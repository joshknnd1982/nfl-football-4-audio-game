"""Pitch and pan rendering. This is inspired by Jim Kitchen."""
import audioop
import math
import os
from array import array

import pytest

from nfl4.audio.render import (MIX_RATE, channel_peak, frames_of, level_gain, output_frames, pan_gains,
                                render_stereo, resample, usable_frequency)
from nfl4.audio.wavdata import load_sound_file
from nfl4.data import paths
from wavmaker import floats, sampled, sine

SHIPPED = os.path.join(paths.program_dir(), "assets", "sounds")


def tone(freq, seconds, rate, amp=0.5):
    return sampled(sine(freq, seconds, rate, amp), rate)


def dominant_hz(samples):
    """Pitch of a clean tone from its rising zero crossings (a sine has one per cycle)."""
    rising = sum(1 for a, b in zip(samples, samples[1:]) if a < 0 <= b)
    return rising * MIX_RATE / len(samples)


def left_samples(pcm):
    every = array("h")
    every.frombytes(pcm)
    return every[0::2]


def test_pan_gains_attenuate_only_the_far_channel_by_pan_over_100_db():
    assert pan_gains(0) == (1.0, 1.0)
    left, right = pan_gains(750)                     # GAME_SPEC 5.5 / DECISIONS P5
    assert right == 1.0 and left == pytest.approx(10 ** (-7.5 / 20))
    left, right = pan_gains(-750)
    assert left == 1.0 and right == pytest.approx(10 ** (-7.5 / 20))
    assert pan_gains(-1000)[1] == pytest.approx(10 ** (-10 / 20))   # mode 4 extreme: 10 dB
    assert pan_gains(99999) == pan_gains(10000)                      # clamped to DirectSound's range
    assert pan_gains(10000)[0] == pytest.approx(1e-5)                # full right: left is 100 dB down


def test_pan_table_gains_are_the_documented_decibel_steps():
    table = [-750, -600, -450, -300, -150, 0, 150, 300, 450, 600, 750]
    for p in table:
        near, far = sorted(pan_gains(p), reverse=True)
        assert near == 1.0
        assert 20 * math.log10(far) == pytest.approx(-abs(p) / 100)


def test_usable_frequency_range_is_directsounds():
    assert not usable_frequency(99) and usable_frequency(100)
    assert usable_frequency(200_000) and not usable_frequency(200_001)
    assert not usable_frequency(0) and not usable_frequency(-500)


def test_real_lengths_at_the_pitch_extremes_match_the_spec():
    """WAV_EVENT_MAP 2 and 4: the celebration sounds play at their own rate + 100 x k (k -20 to 19, not 0), at least
    8000 Hz: foot21 (44,100 Hz, 87 ms) is shortest at 46,000 Hz, foot19 (8,363 Hz) longest at the 8,000 Hz floor."""
    f21 = load_sound_file(os.path.join(SHIPPED, "foot21.wav"))
    f19 = load_sound_file(os.path.join(SHIPPED, "foot19.wav"))
    assert f21.rate == 44100 and f19.rate == 8363
    assert f21.seconds == pytest.approx(0.087, abs=0.001)
    assert output_frames(f21.frames, f21.rate + 1900) / MIX_RATE == pytest.approx(0.087 * 44100 / 46000, abs=0.0005)
    assert output_frames(f19.frames, 8000) / MIX_RATE == pytest.approx(f19.seconds * 8363 / 8000, abs=0.0001)


def test_level_gain_is_hundredths_of_a_decibel():
    """D-023: amplitude = 10 ^ (v / 2000); 0 and above is the file unchanged, -10000 and below is silence."""
    assert level_gain(0) == 1.0 and level_gain(250) == 1.0
    assert level_gain(-600) == pytest.approx(10 ** (-6 / 20))
    assert level_gain(-1200) == pytest.approx(0.2512, abs=0.0001)
    assert level_gain(-2750) == pytest.approx(0.0422, abs=0.0001)
    assert level_gain(-7900) == pytest.approx(10 ** (-79 / 20))         # the quietest the game sets: -2900 - 5000
    assert level_gain(-10000) == 0.0 and level_gain(-12000) == 0.0


def test_pitch_changes_by_the_frequency_ratio():
    source = tone(1000, 0.2, 11025)
    for new_freq in (11025 - 2000, 11025 + 1900):
        pcm = render_stereo(source, new_freq, 0, 1.0)
        assert dominant_hz(left_samples(pcm)) == pytest.approx(1000 * new_freq / 11025, rel=0.02)


def test_length_scales_inversely_with_frequency():
    source = tone(500, 0.1, 22050)
    assert output_frames(source.frames, 22050) == pytest.approx(0.1 * MIX_RATE, abs=2)
    assert len(resample(source, 22050 * 2)) // 2 == pytest.approx(0.05 * MIX_RATE, abs=2)
    assert len(resample(source, 11025)) // 2 == pytest.approx(0.2 * MIX_RATE, abs=2)


def test_the_rendered_length_is_exactly_the_computed_length_at_any_pitch():
    for freq in (100, 441, 4000, 9125, 22050, 88200, 200_000):
        for frames in (1, 2, 3, 178, 881):
            source = sampled([0.25] * frames, 8000)
            assert frames_of(render_stereo(source, freq, 0, 1.0)) == output_frames(frames, freq), (freq, frames)


def test_level_is_kept_at_full_volume_and_scales_with_volume():
    source = tone(500, 0.1, 22050, amp=0.5)
    full = render_stereo(source, 22050 - 100, 0, 1.0)
    assert 16000 < audioop.max(full, 2) <= 16384
    half = render_stereo(source, 22050 - 100, 0, 0.5)
    assert audioop.max(half, 2) == pytest.approx(audioop.max(full, 2) / 2, abs=2)
    assert not any(render_stereo(source, 22050, 0, 0.0))


def test_loud_boost_clips_without_wrapping():
    source = tone(500, 0.05, 22050, amp=0.9)
    boosted = array("h")
    boosted.frombytes(render_stereo(source, 22050, 0, 2.0))
    assert max(boosted) == 32767 and min(boosted) == -32768
    left = boosted[0::2]
    assert max(abs(b - a) for a, b in zip(left, left[1:])) < 20000     # no wrap-around jumps


def test_pan_shows_in_channel_levels():
    source = tone(500, 0.1, 22050)
    pcm = render_stereo(source, 22050 - 100, 600, 1.0)         # right: left is 6 dB down
    assert channel_peak(pcm, 0) / channel_peak(pcm, 1) == pytest.approx(10 ** (-6 / 20), rel=0.02)
    pcm = render_stereo(source, 22050 - 100, -1000, 1.0)
    assert channel_peak(pcm, 1) / channel_peak(pcm, 0) == pytest.approx(10 ** (-10 / 20), rel=0.02)


def test_stereo_source_pans_as_balance():
    source = sampled([(0.5, -0.5)] * 2000, 22050, channels=2)
    every = array("h")
    every.frombytes(render_stereo(source, 22050, 0, 1.0))
    assert every[200] > 0 > every[201]                                  # frame 100: left positive, right negative


def test_stereo_source_pan_attenuates_the_far_channel():
    source = sampled([(0.5, 0.5)] * 2000, 22050, channels=2)
    pcm = render_stereo(source, 22050, 600, 1.0)
    assert channel_peak(pcm, 0) / channel_peak(pcm, 1) == pytest.approx(10 ** (-6 / 20), rel=0.02)


def test_single_frame_and_extreme_frequencies_do_not_fail():
    one = sampled([0.5], 8000)
    assert frames_of(render_stereo(one, 8000, 0, 1.0)) >= 1
    assert frames_of(render_stereo(tone(500, 0.01, 8000), 100, 0, 1.0)) > 0
    assert frames_of(render_stereo(tone(500, 0.01, 8000), 200_000, 0, 1.0)) > 0


def test_the_last_sample_is_held_not_dropped():
    """The float version held the final sample while its position ran past the end."""
    source = sampled([0.0, 0.5, 0.5, 0.5], 8000)
    left = left_samples(render_stereo(source, 8000, 0, 1.0))
    assert left[-1] == pytest.approx(0.5 * 32767, abs=2)
    left = left_samples(render_stereo(source, 1000, 0, 1.0))             # slowed down: the end is held
    assert left[-1] == pytest.approx(0.5 * 32767, abs=2)


def test_every_shipped_wav_renders_at_both_extremes_without_gaining_level():
    """All 26 files, 7 formats (B-A13), at their own rate and at the celebration extremes (floor 8000 Hz), with the
    extreme pans of foot10: exact lengths, never louder than the file."""
    for number in range(26):
        sound = load_sound_file(os.path.join(SHIPPED, f"foot{number}.wav"))
        for freq in (sound.rate, max(8000, sound.rate - 2000), sound.rate + 1900):
            for pan in (0, -1500, 1400):
                pcm = render_stereo(sound, freq, pan, 1.0)
                assert frames_of(pcm) == output_frames(sound.frames, freq), (number, freq)
                assert audioop.max(pcm, 2) <= sound.peak + 2, (number, freq, pan)
