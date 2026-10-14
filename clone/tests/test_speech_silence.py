"""Silence at the ends of rendered speech is cut (owner bug 2026-10-13: "a long silence before the sounds").
This is inspired by Jim Kitchen's Brain.

Some voices end every utterance with half a second of digital silence (FlexVoice2 Bill: 0.66 s after a 1.9 s prompt).
The game waits for "the speech is done", so that silence delayed the first sound of every playback.
"""
import array
import math

from nfl4.speech.waveout import KEEP_LEAD_SECONDS, KEEP_TAIL_SECONDS, trim_silence

from test_sapi_render import FakePlayer, FakeStream, RenderVoice, make

RATE = 44100


def tone(seconds, level=8000):
    n = int(seconds * RATE)
    return array.array("h", (int(level * math.sin(i * 0.3)) for i in range(n)))


def pcm(*parts):
    out = array.array("h")
    for part in parts:
        out.extend(part)
    return out.tobytes()


def silence(seconds):
    return array.array("h", [0] * int(seconds * RATE))


def seconds(data):
    return len(data) / 2 / RATE


def test_trailing_silence_is_cut_down_to_a_short_natural_tail():
    data = pcm(tone(1.0), silence(0.66))
    trimmed = trim_silence(data, RATE)
    assert abs(seconds(trimmed) - (1.0 + KEEP_TAIL_SECONDS)) < 0.01


def test_leading_silence_is_cut_down_to_a_few_milliseconds():
    data = pcm(silence(0.4), tone(1.0))
    trimmed = trim_silence(data, RATE)
    assert abs(seconds(trimmed) - (KEEP_LEAD_SECONDS + 1.0)) < 0.01


def test_quiet_noise_in_the_silence_counts_as_silence_but_speech_does_not():
    noise = array.array("h", [(-1) ** i * 40 for i in range(int(0.5 * RATE))])
    loud_gap = pcm(tone(0.3), silence(0.2), tone(0.3))             # a pause inside the speech is kept whole
    trimmed = trim_silence(pcm(tone(0.3), silence(0.2), tone(0.3), noise), RATE)
    assert abs(seconds(trimmed) - (0.8 + KEEP_TAIL_SECONDS)) < 0.01
    assert trim_silence(loud_gap, RATE) == loud_gap


def test_audio_that_is_silent_from_end_to_end_is_returned_unchanged():
    data = pcm(silence(0.5))
    assert trim_silence(data, RATE) == data                         # a voice at volume zero keeps its timing
    assert trim_silence(b"", RATE) == b""


def test_an_odd_number_of_bytes_is_not_16_bit_audio_and_is_left_alone():
    data = pcm(tone(0.2), silence(0.3)) + b"\x01"
    assert trim_silence(data, RATE) == data


def test_the_backend_plays_the_trimmed_audio_so_the_wait_ends_with_the_sound():
    class TailVoice(RenderVoice):
        def WaitUntilDone(self, ms):
            done = super().WaitUntilDone(ms)
            if done and self.AudioOutputStream is not None and self.AudioOutputStream.data:
                self.AudioOutputStream.data = pcm(tone(0.5)) + pcm(silence(0.66))
            return done

    b, voice, player = make(voice=TailVoice(), player=FakePlayer(play_seconds=0.0))
    try:
        b.speak("Press the space bar to stop")
        b.wait_until_done()
        assert player.blocks and abs(seconds(player.blocks[0]) - (0.5 + KEEP_TAIL_SECONDS)) < 0.01
    finally:
        b.close()
