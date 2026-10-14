"""The audio layer: the original's DirectSound calls on seven slots, with a silent timed output and a slot log.
This is inspired by Jim Kitchen.

WAV_EVENT_MAP 1, 3, 4; GAP_REGISTER G-A1 (a new sound in a slot stops that slot's sound, different slots mix, one extra
channel), G-A4 (no device), D-023 (volume, pan, frequency without the +1 Hz).
"""
import audioop
import os

import pytest

from nfl4.audio import engine
from nfl4.audio.engine import NO_SOUND_NOTICE, Audio, SlotEvent
from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import (CHANNELS, EXTRA_SLOT, SLOT_AMBIENT, SLOT_COUNT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE,
                               SLOT_NOISE, SLOT_ONESHOT, SLOT_TACKLE, TimedOutput)
from nfl4.audio.render import MIX_RATE, channel_peak, frames_of, level_gain
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
from nfl4.audio.tonegen import GENERATED_SOUNDS, Segment, generated, synthesize, write_wav
from nfl4.audio.wavdata import load_sound_file
from nfl4.data.settings import AudioSettings
from wavmaker import floats, sine, write


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class FakeBeeper:
    def __init__(self, works=True):
        self.works = works
        self.calls = 0

    def beep(self):
        self.calls += 1
        return self.works


@pytest.fixture
def rig(tmp_path):
    clock = Clock()
    output = TimedOutput(clock)
    lib = SoundLibrary(shipped_sounds_dir(), str(tmp_path / "player"))
    beeper = FakeBeeper()
    log = []
    audio = Audio(lib, AudioSettings(), output=output, beeper=beeper, clock=clock, slot_log=log)
    return audio, output, clock, lib, beeper, tmp_path, log


def test_the_seven_original_slots_and_the_extra_channel():
    assert (SLOT_ONESHOT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE, SLOT_AMBIENT, SLOT_TACKLE, SLOT_NOISE) == tuple(range(7))
    assert SLOT_COUNT == 7 and EXTRA_SLOT == 7 and CHANNELS == 8 and Audio.SLOTS == 7


def test_play_returns_the_real_length_and_the_slot_is_busy_until_then(rig):
    audio, output, clock, lib, *_ , log = rig
    seconds = audio.play(SLOT_TACKLE, "snd_foot6", -1500)              # 2,930 ms at its own 22,050 Hz
    assert seconds == pytest.approx(2.930, abs=0.001)
    assert audio.busy(SLOT_TACKLE)
    clock.now += seconds - 0.001
    assert audio.busy(SLOT_TACKLE)
    clock.now += 0.002
    assert not audio.busy(SLOT_TACKLE)
    assert log == [SlotEvent(100.0, SLOT_TACKLE, "play", "snd_foot6", -1500, 22050, 0, False, "original")]


def test_a_new_sound_in_a_slot_stops_that_slots_sound(rig):
    """G-A1: PlayTackle within the first tackle's length cuts it; the slot plays only the new one."""
    audio, output, clock, lib, *_, log = rig
    audio.play(SLOT_TACKLE, "snd_foot4", -1500)                       # 4.3 s
    clock.now += 2.5
    seconds = audio.play(SLOT_TACKLE, "snd_foot11", -1500)            # 1.95 s, starts at 2.5 s
    clock.now += seconds + 0.001
    assert not audio.busy(SLOT_TACKLE)                                # the first one would still run until 4.3 s
    assert [e.sound_id for e in log if e.action == "play"] == ["snd_foot4", "snd_foot11"]


def test_different_slots_mix(rig):
    audio, output, clock, *_ = rig
    audio.play(SLOT_CROWD1, "snd_foot1", -1200, loop=True)
    audio.play(SLOT_CROWD2, "snd_foot2", -1200, loop=True)
    audio.play(SLOT_HIKE, "snd_foot3", -1600)
    audio.play(SLOT_NOISE, "snd_foot14", -2750, loop=True)
    audio.play(SLOT_TACKLE, "snd_foot5", -1500)
    audio.play(SLOT_AMBIENT, "snd_foot8", -250)
    audio.play(SLOT_ONESHOT, "snd_foot7", -1500)
    assert all(audio.busy(slot) for slot in range(SLOT_COUNT))
    assert not audio.busy(EXTRA_SLOT)


def test_a_loop_plays_until_it_is_stopped(rig):
    audio, output, clock, *_ , log = rig
    one_pass = audio.play(SLOT_NOISE, "snd_foot14", -2750, loop=True)
    assert one_pass == pytest.approx(2.2, abs=0.001)
    clock.now += 600
    assert audio.busy(SLOT_NOISE)
    audio.stop(SLOT_NOISE)
    assert not audio.busy(SLOT_NOISE)
    assert output.played[-1][3] is True and log[-1] == SlotEvent(clock.now, SLOT_NOISE, "stop")


def test_volume_is_hundredths_of_a_decibel_and_a_playing_loop_can_change(rig):
    audio, output, clock, *_ , log = rig
    audio.play(SLOT_CROWD2, "snd_foot2", -1200, loop=True)
    assert output.gains[SLOT_CROWD2] == pytest.approx(level_gain(-1200)) == pytest.approx(0.2512, abs=0.0001)
    assert audio.volume(SLOT_CROWD2) == -1200
    audio.set_volume(SLOT_CROWD2, -600)
    assert output.gains[SLOT_CROWD2] == pytest.approx(10 ** (-6 / 20)) and audio.volume(SLOT_CROWD2) == -600
    assert audio.busy(SLOT_CROWD2)                                    # the loop goes on at the new level
    assert len(output.played) == 1                                    # not restarted
    assert log[-1] == SlotEvent(clock.now, SLOT_CROWD2, "volume", volume=-600)


def test_a_slot_never_set_reads_full_volume_like_directsound(rig):
    audio, *_ = rig
    assert [audio.volume(slot) for slot in range(CHANNELS)] == [0] * CHANNELS


def test_the_level_is_the_mixers_and_the_samples_stay_unchanged(rig):
    """The volume is applied by the mixer (so ramps work); the rendered samples carry only the player's trim."""
    audio, output, *_ = rig
    audio.play(SLOT_ONESHOT, "snd_foot12", -1000)
    loud = output.played[-1][1]
    audio.play(SLOT_ONESHOT, "snd_foot12", -5000)
    assert output.played[-1][1] == loud
    sound = load_sound_file(os.path.join(shipped_sounds_dir(), "foot12.wav"))
    assert audioop.max(loud, 2) <= sound.peak + 2 and audioop.max(loud, 2) > sound.peak - 400


def test_frequency_none_is_the_files_own_rate_and_a_change_scales_the_length(rig):
    """D-023: no +1 Hz; the celebration's own rate + 100 x k changes the length by the ratio."""
    audio, output, clock, *_ , log = rig
    own = audio.play(SLOT_ONESHOT, "snd_foot15")                      # 44,100 Hz
    assert log[-1].freq == 44100 and own == pytest.approx(0.127, abs=0.001)
    faster = audio.play(SLOT_ONESHOT, "snd_foot15", -300, freq=44100 + 1900)
    assert faster == pytest.approx(own * 44100 / 46000, abs=0.0001) and log[-1].freq == 46000


def test_frequency_outside_directsound_range_plays_at_the_files_own_rate(rig):
    audio, output, clock, *_ , log = rig
    seconds = audio.play(SLOT_ONESHOT, "snd_foot12", 0, freq=50)
    assert seconds == pytest.approx(0.4, abs=0.001) and log[-1].freq == 22050


def test_pan_reaches_the_output_and_the_far_channel_is_attenuated(rig):
    audio, output, *_ = rig
    audio.play(SLOT_AMBIENT, "snd_foot10", -1500, pan=1400)           # right: the left is 14 dB down
    pcm = output.played[-1][1]
    assert channel_peak(pcm, 0) / channel_peak(pcm, 1) == pytest.approx(10 ** (-14 / 20), rel=0.02)
    audio.play(SLOT_AMBIENT, "snd_foot10", -1500, pan=-1500)
    pcm = output.played[-1][1]
    assert channel_peak(pcm, 1) / channel_peak(pcm, 0) == pytest.approx(10 ** (-15 / 20), rel=0.02)


def test_a_sound_switched_off_plays_nothing_and_takes_no_time(rig):
    """G-A3, D-038: "off" is not a silence of the sound's length; nothing plays and nothing waits."""
    audio, output, clock, lib, beeper, tmp_path, log = rig
    audio.play(SLOT_ONESHOT, "snd_foot0", 0, loop=True)
    (tmp_path / "player" / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot7 = off\n", encoding="utf-8")
    audio.refresh()
    played = len(output.played)
    assert audio.play(SLOT_ONESHOT, "snd_foot7", -1500) == 0.0
    assert len(output.played) == played and not audio.busy(SLOT_ONESHOT)      # the slot's old sound is stopped too
    assert log[-1].source == "off" and log[-1].sound_id == "snd_foot7"


def test_the_players_trim_is_baked_into_the_samples(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    audio.play(SLOT_ONESHOT, "snd_foot12", 0)
    full = audioop.max(output.played[-1][1], 2)
    (tmp_path / "player" / FILE_NAME).write_text(DEFAULT_TEXT + "foot12 = volume=50\n", encoding="utf-8")
    audio.refresh()
    audio.play(SLOT_ONESHOT, "snd_foot12", 0)
    assert audioop.max(output.played[-1][1], 2) == pytest.approx(full / 2, abs=2)


def test_nothing_playable_plays_nothing_and_stops_the_slot(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    audio.play(SLOT_ONESHOT, "snd_foot0", 0)
    assert audio.play(SLOT_ONESHOT, "no_such_sound", 0) == 0.0
    assert not audio.busy(SLOT_ONESHOT) and log[-1].source == "none"


def test_a_render_is_kept_for_the_next_start_and_dropped_on_reload(rig):
    audio, output, *_ = rig
    audio.play(SLOT_TACKLE, "snd_foot6", -1500)
    audio.play(SLOT_TACKLE, "snd_foot6", -1500)
    assert output.played[-1][1] is output.played[-2][1]
    audio.refresh()
    audio.play(SLOT_TACKLE, "snd_foot6", -1500)
    assert output.played[-1][1] is not output.played[-2][1] and output.played[-1][1] == output.played[-2][1]


def test_stop_all_stops_the_seven_slots_and_the_extra_channel(rig):
    audio, *_ = rig
    for slot in range(CHANNELS):
        audio.play(slot, "snd_foot1", 0, loop=True)
    audio.stop_all()
    assert not any(audio.busy(slot) for slot in range(CHANNELS))


def test_preview_uses_the_extra_channel_only(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    assert audio.preview("snd_foot7") == "original"
    assert audio.busy(EXTRA_SLOT) and not any(audio.busy(s) for s in range(SLOT_COUNT))
    audio.stop_preview()
    assert not audio.busy(EXTRA_SLOT)


# ----- the exit beep (SOUND_DESIGN 4 step 3) -----

def test_exit_beep_uses_the_system_sound_first(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    assert audio.beep_exit() is True
    assert beeper.calls == 1 and output.played == []
    assert log[-1] == SlotEvent(clock.now, EXTRA_SLOT, "play", "beep_exit", source="system")


def test_exit_beep_falls_back_to_the_generated_blip(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    beeper.works = False
    assert audio.beep_exit() is True
    slot, pcm, gain, loop = output.played[-1]
    assert slot == EXTRA_SLOT and frames_of(pcm) == pytest.approx(0.080 * MIX_RATE, abs=2) and gain == 1.0
    assert audio.busy(EXTRA_SLOT) and log[-1].source == "generated"


def test_exit_beep_player_file_replaces_both(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    write(tmp_path / "player" / "beep_exit.wav", sine(500, 0.05, 22050), rate=22050)
    audio.refresh()
    audio.beep_exit()
    assert beeper.calls == 0 and output.played[-1][0] == EXTRA_SLOT
    assert frames_of(output.played[-1][1]) == pytest.approx(0.05 * MIX_RATE, abs=2)


def test_exit_beep_switched_off_is_silent_and_skips_the_system_sound(rig):
    audio, output, clock, lib, beeper, tmp_path, log = rig
    (tmp_path / "player" / FILE_NAME).write_text(DEFAULT_TEXT + "beep_exit = off\n", encoding="utf-8")
    audio.refresh()
    assert audio.beep_exit() is True
    assert beeper.calls == 0 and output.played == [] and not audio.busy(EXTRA_SLOT)


def test_system_beeper_calls_messagebeep_zero(monkeypatch):
    import winsound
    seen = []
    monkeypatch.setattr(winsound, "MessageBeep", lambda kind=0: seen.append(kind))
    assert engine.SystemBeeper().beep() is True and seen == [0]
    monkeypatch.setattr(winsound, "MessageBeep", lambda kind=0: (_ for _ in ()).throw(RuntimeError("no")))
    assert engine.SystemBeeper().beep() is False


# ----- no sound device (G-A4) -----

def test_no_sound_device_means_silent_running_and_one_notice(tmp_path, monkeypatch):
    def broken(buffer):
        raise engine.OutputError("no device")
    monkeypatch.setattr(engine, "PygameOutput", broken)
    audio = Audio(SoundLibrary(shipped_sounds_dir(), str(tmp_path)), AudioSettings(), beeper=FakeBeeper())
    assert audio.ok is False and "no device" in audio.error
    seconds = audio.play(SLOT_TACKLE, "snd_foot6", -1500)
    assert seconds > 0 and audio.busy(SLOT_TACKLE)                     # timing still works for the game logic
    assert audio.take_notices() == [NO_SOUND_NOTICE]
    assert audio.take_notices() == []
    audio.close()


def test_unexpected_start_up_failure_is_also_caught(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "PygameOutput", lambda buffer: (_ for _ in ()).throw(ValueError("odd")))
    audio = Audio(SoundLibrary(shipped_sounds_dir(), str(tmp_path)), AudioSettings(), beeper=FakeBeeper())
    assert not audio.ok and audio.take_notices() == [NO_SOUND_NOTICE]


def test_a_failing_mixer_never_raises_into_the_game(rig):
    audio, output, *_ = rig

    def boom(*args, **kwargs):
        raise RuntimeError("mixer gone")
    for name in ("play", "set_gain", "busy", "stop"):
        setattr(output, name, boom)
    assert audio.play(SLOT_ONESHOT, "snd_foot12", 0) == 0.0
    audio.set_volume(SLOT_CROWD2, -600)
    assert audio.busy(SLOT_CROWD2) is False
    audio.stop(SLOT_CROWD2)
    audio.stop_all()


# ----- generated sounds -----

def test_generated_beep_checks():
    blip = generated("beep_exit")
    data = floats(blip)
    assert blip.rate == 44100 and blip.seconds == pytest.approx(0.080, abs=0.0005)
    assert 0.2 < max(abs(v) for v in data) < 0.5                     # audible, far from clipping
    assert abs(data[0]) < 0.01 and abs(data[-1]) < 0.05              # no click at either end
    middle = data[200:-200]
    crossings = sum(1 for a, b in zip(middle, middle[1:]) if (a < 0) != (b < 0))
    assert crossings / 2 / (len(middle) / MIX_RATE) == pytest.approx(880, rel=0.03)   # main pitch 880 Hz
    assert blip.pcm == generated("beep_exit").pcm                    # deterministic


def test_synthesis_waveforms_sweeps_and_rests():
    segments = (Segment("sine", 440, 880, 50, 0.5), Segment("triangle", 300, 300, 20, 0.0),
                Segment("noise", 0, 0, 20, 0.3), Segment("square", 200, 200, 20, 0.5))
    sound = synthesize(segments)
    assert sound.seconds == pytest.approx(0.110, abs=0.001) and sound.peak <= 0.5 * 32768
    assert not any(sound.samples()[int(0.052 * MIX_RATE):int(0.068 * MIX_RATE)])      # the rest is silent
    with pytest.raises(ValueError):
        synthesize((Segment("flute", 1, 1, 10, 1.0),))
    assert set(GENERATED_SOUNDS) == {"beep_exit"}                    # D-032: the only generated sound


def test_generated_sound_exports_to_a_playable_wav(tmp_path):
    path = tmp_path / "beep.wav"
    write_wav(str(path), generated("beep_exit"))
    again = load_sound_file(str(path))
    assert again.rate == 44100 and again.frames == generated("beep_exit").frames
    assert again.pcm == generated("beep_exit").pcm and again.channels == 1
