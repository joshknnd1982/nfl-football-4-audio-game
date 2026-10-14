"""The audio layer the game logic uses, with a silent timed output. This is inspired by Jim Kitchen's Brain."""
import audioop

import pytest

from nfl4.audio import engine
from nfl4.audio.engine import Audio
from nfl4.audio.library import Pick, SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import BEEP_SLOT, TimedOutput
from nfl4.audio.render import MIX_RATE, channel_peak, frames_of
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
from nfl4.audio.tonegen import GENERATED_SOUNDS, generated, synthesize, write_wav, Segment
from nfl4.audio.wavdata import Sampled, load_sound_file
from nfl4.data.settings import AudioSettings
from wavmaker import floats, sine, write


def peak(pcm):
    """Largest absolute sample of rendered stereo sound."""
    return audioop.max(pcm, 2)


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
    audio = Audio(lib, AudioSettings(), output=output, beeper=beeper)
    return audio, output, clock, lib, beeper, tmp_path


def test_play_returns_the_real_length_and_the_slot_is_busy_until_then(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(36)                                       # 5,564 Hz, 1,155 bytes of 8-bit
    seconds = audio.play(0, pick, pick.rate - 2000, 0)
    assert seconds == pytest.approx(0.324, abs=0.001)               # GAME_SPEC 5.3
    assert audio.busy(0)
    clock.now += seconds - 0.001
    assert audio.busy(0)
    clock.now += 0.002
    assert not audio.busy(0)


def test_stop_and_stop_all_touch_only_the_nine_slots(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(9)
    for slot in range(9):
        audio.play(slot, pick, pick.rate + 100, 0)
    audio.play(BEEP_SLOT, pick, pick.rate + 100, 0)
    assert all(audio.busy(s) for s in range(9))                      # nine at once
    audio.stop(3)
    assert not audio.busy(3) and audio.busy(4)
    audio.stop_all()
    assert not any(audio.busy(s) for s in range(9))
    assert audio.busy(BEEP_SLOT)


def test_a_new_sound_replaces_the_slots_old_one(rig):
    audio, output, clock, lib, *_ = rig
    long_pick, short_pick = lib.pick_number(36), lib.pick_number(8)
    audio.play(0, long_pick, long_pick.rate, 0)
    audio.play(0, short_pick, short_pick.rate, 0)
    clock.now += 0.05
    assert not audio.busy(0)                                         # the long one was cut, not left running


def test_frequency_outside_directsound_range_plays_at_the_files_own_rate(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(8)                                        # 44,100 Hz, 178 frames
    own = audio.play(0, pick, None, 0)
    assert own == pytest.approx(pick.sound.frames / pick.rate, abs=0.0001)
    assert audio.play(0, pick, 50, 0) == pytest.approx(own)          # too low: SetFrequency would fail
    assert audio.play(0, pick, 300_000, 0) == pytest.approx(own)
    assert audio.play(0, pick, -2000, 0) == pytest.approx(own)       # negative walks happen after bad wavs


def test_nothing_playable_plays_nothing(rig):
    audio, output, clock, lib, *_ = rig
    before = len(output.played)
    assert audio.play(0, Pick("brain99", None, None, "none"), 11025, 0) == 0.0
    assert len(output.played) == before and not audio.busy(0)


def test_effects_volume_and_sound_trim_scale_the_level(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(9)
    audio.play(0, pick, pick.rate + 100, 0)
    full = peak(output.played[-1][1])
    audio.settings.effects_volume = 50
    audio.play(0, pick, pick.rate + 100, 0)
    assert peak(output.played[-1][1]) == pytest.approx(full / 2, abs=2)
    trimmed = Pick(pick.sound_id, pick.sound, pick.size, pick.source, pick.path, volume=0.5)
    audio.play(0, trimmed, pick.rate + 100, 0)
    assert peak(output.played[-1][1]) == pytest.approx(full / 4, abs=2)
    audio.settings.effects_volume = 0
    audio.play(0, pick, pick.rate + 100, 0)
    assert not any(output.played[-1][1])


def test_default_volume_leaves_the_file_unchanged(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(21)
    audio.play(0, pick, pick.rate + 1, 0)
    assert peak(output.played[-1][1]) == pytest.approx(pick.sound.peak * 32767 / 32768, abs=6)   # integer resampling: a few steps of 32,768


def test_pan_reaches_the_output(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(9)
    audio.play(0, pick, pick.rate + 100, -750)
    pcm = output.played[-1][1]
    assert channel_peak(pcm, 1) == pytest.approx(channel_peak(pcm, 0) * 10 ** (-7.5 / 20), rel=0.02)


def test_silent_wav_brain7_plays_as_a_silent_sound_of_its_length(rig):
    audio, output, clock, lib, *_ = rig
    pick = lib.pick_number(7)
    seconds = audio.play(0, pick, pick.rate, 0)
    assert seconds == pytest.approx(0.049, abs=0.001) and not any(output.played[-1][1])
    assert audio.busy(0)                                             # silent but it takes its time


def test_exit_beep_uses_the_system_sound_first(rig):
    audio, output, clock, lib, beeper, _ = rig
    assert audio.beep_exit() is True
    assert beeper.calls == 1 and output.played == []


def test_exit_beep_falls_back_to_the_generated_blip(rig):
    audio, output, clock, lib, beeper, _ = rig
    beeper.works = False
    assert audio.beep_exit() is True
    slot, pcm = output.played[-1]
    assert slot == BEEP_SLOT and frames_of(pcm) == pytest.approx(0.080 * MIX_RATE, abs=2)
    assert audio.busy(BEEP_SLOT)


def test_exit_beep_player_file_replaces_both(rig):
    audio, output, clock, lib, beeper, tmp_path = rig
    write(tmp_path / "player" / "beep_exit.wav", sine(500, 0.05, 22050), rate=22050)
    audio.refresh()
    audio.beep_exit()
    assert beeper.calls == 0 and output.played[-1][0] == BEEP_SLOT
    assert frames_of(output.played[-1][1]) == pytest.approx(0.05 * MIX_RATE, abs=2)


def test_exit_beep_switched_off_is_silent_and_skips_the_system_sound(rig):
    audio, output, clock, lib, beeper, tmp_path = rig
    (tmp_path / "player" / FILE_NAME).write_text(DEFAULT_TEXT + "beep_exit = off\n", encoding="utf-8")
    audio.refresh()
    audio.beep_exit()
    assert beeper.calls == 0 and not any(output.played[-1][1])


def test_system_beeper_calls_messagebeep_zero(monkeypatch):
    import winsound
    seen = []
    monkeypatch.setattr(winsound, "MessageBeep", lambda kind=0: seen.append(kind))
    assert engine.SystemBeeper().beep() is True and seen == [0]
    monkeypatch.setattr(winsound, "MessageBeep", lambda kind=0: (_ for _ in ()).throw(RuntimeError("no")))
    assert engine.SystemBeeper().beep() is False


def test_no_sound_device_means_silent_running_not_a_crash(tmp_path, monkeypatch):
    def broken(buffer):
        raise engine.OutputError("no device")
    monkeypatch.setattr(engine, "PygameOutput", broken)
    audio = Audio(SoundLibrary(shipped_sounds_dir(), str(tmp_path)), AudioSettings(), beeper=FakeBeeper())
    assert audio.ok is False and "no device" in audio.error
    pick = audio.library.pick_number(9)
    seconds = audio.play(0, pick, pick.rate + 100, 0)
    assert seconds > 0 and audio.busy(0)                             # timing still works for the game logic
    audio.close()


def test_unexpected_start_up_failure_is_also_caught(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "PygameOutput", lambda buffer: (_ for _ in ()).throw(ValueError("odd")))
    audio = Audio(SoundLibrary(shipped_sounds_dir(), str(tmp_path)), AudioSettings(), beeper=FakeBeeper())
    assert not audio.ok


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
    assert set(GENERATED_SOUNDS) == {"beep_exit"}


def test_generated_sound_exports_to_a_playable_wav(tmp_path):
    path = tmp_path / "beep.wav"
    write_wav(str(path), generated("beep_exit"))
    again = load_sound_file(str(path))
    assert again.rate == 44100 and again.frames == generated("beep_exit").frames
    assert again.pcm == generated("beep_exit").pcm and again.channels == 1
