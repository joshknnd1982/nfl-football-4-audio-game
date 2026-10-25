"""Timing on the real sound device, at volume 0 so nothing is heard (fixesforgames B-A2: the dummy driver's timing is
not trustworthy). This is inspired by Jim Kitchen.

The output's master volume is set to 0 before the first sound: every level is then 0 in the mixer, the device plays
silence, and the mixer still reports each sound's end at the real time. Real threads and the real clock: this file is
one of the files run 30 times per bitness (B-X5). Skipped when no sound device opens.
"""
import threading
import time

import pytest

from nfl4.audio.engine import Audio
from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import SLOT_CROWD2, SLOT_NOISE, SLOT_ONESHOT, SLOT_TACKLE, OutputError, PygameOutput
from nfl4.data.settings import AudioSettings
from nfl4.game.keys import KEY_ENTER, KeyInput
from nfl4.game.sounds import GameSounds

pytestmark = pytest.mark.realaudio


class NoBeep:
    def beep(self):
        return False


@pytest.fixture
def audio(tmp_path, monkeypatch):
    monkeypatch.delenv("SDL_AUDIODRIVER", raising=False)
    try:
        output = PygameOutput(256)
    except OutputError as exc:
        pytest.skip(f"no sound device: {exc}")
    output.volume = 0.0                     # silent: before any sound starts
    a = Audio(SoundLibrary(shipped_sounds_dir(), str(tmp_path)), AudioSettings(), output=output, beeper=NoBeep())
    yield a
    a.close()


def busy_time(audio, slot, limit=5.0):
    start = time.perf_counter()
    while audio.busy(slot) and time.perf_counter() - start < limit:
        time.sleep(0.0005)
    return time.perf_counter() - start


def test_the_device_is_silent(audio):
    import pygame
    audio.play(SLOT_ONESHOT, "snd_foot12", 0)
    assert pygame.mixer.Channel(SLOT_ONESHOT).get_sound().get_volume() == 0.0


@pytest.mark.parametrize("sound_id, freq, seconds", [("snd_foot12", None, 0.400), ("snd_foot7", None, 0.600),
                                                     ("snd_foot13", None, 0.366), ("snd_foot21", 46000, 0.0834)])
def test_the_end_of_a_sound_is_reported_at_its_length(audio, sound_id, freq, seconds):
    computed = audio.play(SLOT_ONESHOT, sound_id, 0, freq=freq)
    assert computed == pytest.approx(seconds, abs=0.001)
    assert busy_time(audio, SLOT_ONESHOT) == pytest.approx(computed, abs=0.030)


def test_play_waits_the_sounds_length_on_the_real_clock(audio):
    keys = KeyInput()
    sounds = GameSounds(audio, keys, audio.settings)
    start = time.perf_counter()
    sounds.play(12, -1000)
    assert time.perf_counter() - start == pytest.approx(0.400, abs=0.040)


def test_play2_ends_at_a_key_from_the_window_thread(audio):
    keys = KeyInput()
    sounds = GameSounds(audio, keys, audio.settings)
    timer = threading.Timer(0.15, keys.post, args=(KEY_ENTER,))
    start = time.perf_counter()
    timer.start()
    sounds.play2("foot0")                                              # 3.4 s if no key came
    elapsed = time.perf_counter() - start
    timer.join()
    assert 0.14 <= elapsed < 0.15 + 0.05                       # the timer keeps its own clock: 0.5 ms early was seen
    assert keys.code_text == str(KEY_ENTER) and not audio.busy(SLOT_ONESHOT)


def test_a_loop_runs_past_its_length_and_a_new_sound_cuts_a_slot(audio):
    audio.play(SLOT_NOISE, "snd_foot13", 0, loop=True)                 # 0.366 s per pass
    audio.play(SLOT_TACKLE, "snd_foot4", 0)                            # 4.3 s
    time.sleep(0.8)
    assert audio.busy(SLOT_NOISE)
    computed = audio.play(SLOT_TACKLE, "snd_foot12", 0)                # cuts foot4
    assert busy_time(audio, SLOT_TACKLE) == pytest.approx(computed, abs=0.030)
    assert audio.busy(SLOT_NOISE)
    audio.stop(SLOT_NOISE)
    assert not audio.busy(SLOT_NOISE)


def test_the_crowd_ramp_takes_its_time_on_the_real_clock_and_keeps_the_loop(audio):
    keys = KeyInput()
    sounds = GameSounds(audio, keys, audio.settings)
    sounds.start_crowds()
    start = time.perf_counter()
    sounds.c2uf()
    assert time.perf_counter() - start == pytest.approx(1.3, abs=0.06)
    assert audio.volume(SLOT_CROWD2) == 0 and audio.busy(SLOT_CROWD2)
