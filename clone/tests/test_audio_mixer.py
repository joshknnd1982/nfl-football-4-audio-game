"""The real pygame mixer, on SDL's silent dummy driver (no sound reaches the speakers): logic only.
This is inspired by Jim Kitchen.

fixesforgames B-A2: the dummy driver's timing is not trustworthy, so these tests check what plays where, loops, cuts,
levels and threads; the timing is measured on the real device at volume 0 (test_audio_realdevice.py) and the mixed
output itself with SDL's disk driver (test_audio_disk.py).
"""
import random
import threading
import time

import pytest

from nfl4.audio.engine import Audio
from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import (CHANNELS, EXTRA_SLOT, SLOT_COUNT, SLOT_CROWD2, SLOT_NOISE, SLOT_ONESHOT, SLOT_TACKLE,
                               OutputError, PygameOutput, split_gain)
from nfl4.audio.render import MIX_RATE, level_gain
from nfl4.data.settings import AudioSettings

pytestmark = pytest.mark.mixer


class NoBeep:
    def beep(self):
        return False


@pytest.fixture
def audio(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    lib = SoundLibrary(shipped_sounds_dir(), str(tmp_path))
    a = Audio(lib, AudioSettings(), beeper=NoBeep())
    assert a.ok, a.error
    yield a
    a.close()


def busy_time(audio, slot, limit=1.0):
    start = time.perf_counter()
    while audio.busy(slot) and time.perf_counter() - start < limit:
        time.sleep(0.0005)
    return time.perf_counter() - start


def test_mixer_format_and_eight_channels(audio):
    import pygame
    assert pygame.mixer.get_init() == (MIX_RATE, -16, 2)
    assert pygame.mixer.get_num_channels() == CHANNELS == 9      # 8: the crowd's reactions (2026-10-23)


def test_the_seven_slots_and_the_extra_channel_play_at_once(audio):
    for slot in range(CHANNELS):
        audio.play(slot, "snd_foot1", -1200, loop=True)
    assert all(audio.busy(slot) for slot in range(CHANNELS))
    audio.stop_all()
    assert not any(audio.busy(slot) for slot in range(CHANNELS))


def test_stop_takes_effect_at_once(audio):
    audio.play(SLOT_TACKLE, "snd_foot4", -1500)
    assert audio.busy(SLOT_TACKLE)
    audio.stop(SLOT_TACKLE)
    assert not audio.busy(SLOT_TACKLE)


def test_a_new_sound_in_a_busy_slot_replaces_it(audio):
    import pygame
    audio.play(SLOT_TACKLE, "snd_foot4", -1500)
    first = pygame.mixer.Channel(SLOT_TACKLE).get_sound()
    audio.play(SLOT_TACKLE, "snd_foot12", -1500)
    second = pygame.mixer.Channel(SLOT_TACKLE).get_sound()
    assert second is not first and second.get_length() == pytest.approx(0.4, abs=0.001)
    assert busy_time(audio, SLOT_TACKLE, limit=3.0) < 3.0     # the short one ends, not foot4's 4.3 s (timing: real device)


def test_a_loop_keeps_playing_past_its_length_until_stopped(audio):
    audio.play(SLOT_NOISE, "snd_foot13", -2750, loop=True)                # 0.366 s per pass
    time.sleep(0.9)
    assert audio.busy(SLOT_NOISE)
    audio.stop(SLOT_NOISE)
    assert not audio.busy(SLOT_NOISE)


def test_a_level_change_reaches_the_playing_sound_without_restarting_it(audio):
    import pygame
    audio.play(SLOT_CROWD2, "snd_foot2", -1200, loop=True)
    sound = pygame.mixer.Channel(SLOT_CROWD2).get_sound()
    chunk, _ = split_gain(level_gain(-1200))
    assert sound.get_volume() == pytest.approx(chunk / 128)
    audio.set_volume(SLOT_CROWD2, 0)
    assert pygame.mixer.Channel(SLOT_CROWD2).get_sound() is sound and sound.get_volume() == 1.0
    audio.set_volume(SLOT_CROWD2, -600)
    assert sound.get_volume() == pytest.approx(split_gain(level_gain(-600))[0] / 128)


def test_split_gain_reaches_any_level_closely():
    """Chunk volume (128 steps) times the panning effect (255 steps): within half a percent down to -50 dB; below
    that the product of two whole numbers is the limit, still within 1 dB at -79 dB, the quietest the game sets."""
    import math
    for hundredths in range(0, -7901, -50):           # -2900 + wavol -5000: foot10 centered at the lowest volume
        want = level_gain(hundredths)
        chunk, effect = split_gain(want)
        got = chunk / 128 * effect / 255
        assert 0 <= chunk <= 128 and 0 <= effect <= 255
        if hundredths >= -5000:
            assert got == pytest.approx(want, rel=0.005), hundredths
        else:
            assert abs(20 * math.log10(got / want)) < 1.0, hundredths
    assert split_gain(1.0) == (128, 255) and split_gain(0.0) == (0, 0) and split_gain(2.0) == (128, 255)


def test_master_volume_zero_makes_every_sound_silent(audio):
    audio.output.volume = 0.0
    audio.play(SLOT_ONESHOT, "snd_foot0", 0)
    import pygame
    assert pygame.mixer.Channel(SLOT_ONESHOT).get_sound().get_volume() == 0.0
    assert audio.busy(SLOT_ONESHOT)                                       # it still takes its time


def test_playing_from_another_thread(audio):
    done = []

    def worker():
        audio.play(SLOT_ONESHOT, "snd_foot12", -1000)
        done.append(audio.busy(SLOT_ONESHOT))
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(2)
    assert done == [True]


def test_exit_beep_blip_plays_on_the_extra_channel(audio):
    assert audio.beep_exit()
    assert audio.busy(EXTRA_SLOT) and not any(audio.busy(s) for s in range(SLOT_COUNT))
    import pygame
    assert pygame.mixer.Channel(EXTRA_SLOT).get_sound().get_length() == pytest.approx(0.080, abs=0.001)
    assert busy_time(audio, EXTRA_SLOT, limit=2.0) < 2.0       # it ends (its timing: the real device, B-A2)


def test_many_starts_on_seven_slots_never_fail(audio):
    """Random restarts and level changes on every slot for a second, as a busy game would make them."""
    rng = random.Random(7)
    ids = [f"snd_foot{n}" for n in range(26)]
    end = time.perf_counter() + 1.0
    starts = 0
    while time.perf_counter() < end:
        slot = rng.randrange(SLOT_COUNT)
        if rng.random() < 0.3:
            audio.set_volume(slot, rng.randrange(-5000, 1, 100))
        else:
            audio.play(slot, rng.choice(ids), rng.randrange(-5000, 1, 100), pan=rng.randrange(-1500, 1401, 100),
                       freq=None if rng.random() < 0.5 else rng.randrange(8000, 46001, 100), loop=rng.random() < 0.2)
            starts += 1
        time.sleep(0.002)
    assert starts > 100
    audio.stop_all()
    assert not any(audio.busy(slot) for slot in range(CHANNELS))


def test_buffer_size_falls_back_when_the_first_is_refused(monkeypatch):
    import pygame
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    real_init = pygame.mixer.init
    calls = []

    def picky(*args, **kwargs):
        calls.append(kwargs.get("buffer"))
        if kwargs.get("buffer") == 256:
            raise pygame.error("buffer refused")
        return real_init(*args, **kwargs)

    monkeypatch.setattr(pygame.mixer, "init", picky)
    output = PygameOutput(256)
    try:
        assert calls[:2] == [256, 512] and output.buffer == 512
    finally:
        output.close()


def test_mixer_that_will_not_start_raises_outputerror(monkeypatch):
    import pygame
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setattr(pygame.mixer, "init", lambda *a, **k: (_ for _ in ()).throw(pygame.error("no device")))
    with pytest.raises(OutputError, match="no device"):
        PygameOutput(256)
