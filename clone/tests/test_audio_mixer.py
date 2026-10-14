"""The real pygame mixer, on SDL's silent dummy driver (no sound reaches the speakers).
This is inspired by Jim Kitchen's Brain.

The dummy driver consumes audio at the real rate, so end-of-sound timing here is the mixer's own.
"""
import random
import threading
import time

import pytest

from nfl4.audio.engine import Audio
from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import BEEP_SLOT, PygameOutput, OutputError
from nfl4.audio.render import MIX_RATE
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


def test_mixer_format_and_channels(audio):
    import pygame
    assert pygame.mixer.get_init() == (MIX_RATE, -16, 2)
    assert pygame.mixer.get_num_channels() == 10


@pytest.mark.parametrize("number,offset", [(36, -2000), (21, 1900), (8, 1900), (13, -2000), (1, 100)])
def test_end_of_sound_is_seen_close_to_the_computed_length(audio, number, offset):
    """GAME_SPEC 5.4: the slot starts its next sound when the buffer reports stopped."""
    pick = audio.library.pick_number(number)
    expected = audio.play(0, pick, pick.rate + offset, 0)
    heard = busy_time(audio, 0)
    # SDL's dummy driver paces itself with coarse sleeps, so only a loose bound is reliable here;
    # tools/audio_selfcheck.py measures the exact lag on the real device at volume 0 (silent).
    assert expected * 0.75 - 0.01 <= heard <= expected + 0.06, (number, expected, heard)


def test_nine_slots_and_the_beep_channel_play_at_once(audio):
    pick = audio.library.pick_number(36)
    for slot in range(9):
        audio.play(slot, pick, pick.rate, 0)
    audio.output.play(BEEP_SLOT, bytes(4410 * 4))
    assert sum(audio.busy(s) for s in range(10)) == 10
    audio.stop_all()
    assert sum(audio.busy(s) for s in range(9)) == 0 and audio.busy(BEEP_SLOT)


def test_stop_takes_effect_at_once(audio):
    pick = audio.library.pick_number(36)
    audio.play(2, pick, pick.rate - 2000, 0)
    start = time.perf_counter()
    audio.stop(2)
    assert not audio.busy(2) and time.perf_counter() - start < 0.01     # the 10 ms key rule (DECISIONS P5)


def test_a_new_sound_in_a_busy_slot_replaces_it(audio):
    long_pick, short_pick = audio.library.pick_number(36), audio.library.pick_number(8)
    audio.play(0, long_pick, long_pick.rate - 2000, 0)
    seconds = audio.play(0, short_pick, short_pick.rate + 1900, 0)
    assert busy_time(audio, 0) < seconds + 0.045                        # not the 324 ms of the first


def test_playing_from_another_thread(audio):
    pick = audio.library.pick_number(9)
    seen = {}

    def run():
        seen["seconds"] = audio.play(1, pick, pick.rate + 100, 300)
        seen["busy"] = audio.busy(1)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(2)
    assert seen["busy"] and seen["seconds"] > 0.05


def test_exit_beep_blip_plays_on_its_own_channel(audio):
    assert audio.beep_exit()
    assert audio.busy(BEEP_SLOT) and not any(audio.busy(s) for s in range(9))
    assert busy_time(audio, BEEP_SLOT) == pytest.approx(0.080, abs=0.045)


def test_the_slot_loop_keeps_nine_slots_going_without_gaps(audio):
    """A rough version of GAME_SPEC 5.4 over the real mixer: restart a slot as soon as it stops."""
    rng = random.Random(7)
    starts = [0] * 9
    last_end = [None] * 9
    gaps = []
    pool = audio.library.pool_size()
    end = time.perf_counter() + 1.2
    while time.perf_counter() < end:
        for slot in range(9):
            if not audio.busy(slot):
                now = time.perf_counter()
                if last_end[slot] is not None:
                    gaps.append(now - last_end[slot])
                pick = audio.library.pick_number(rng.randint(1, pool))
                freq = pick.rate + rng.choice([r for r in range(-20, 20) if r]) * 100
                seconds = audio.play(slot, pick, freq, rng.randint(-100, 99) * 10)
                last_end[slot] = now + seconds
                starts[slot] += 1
        time.sleep(0.001)
    assert min(starts) >= 3 and len(gaps) > 20
    late = [g for g in gaps if g > 0.05]
    assert len(late) <= len(gaps) * 0.05                                # nearly every restart within 50 ms of the end


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
