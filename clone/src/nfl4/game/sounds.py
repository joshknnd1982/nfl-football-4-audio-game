"""The original's sound procedures. This is inspired by Jim Kitchen.

WAV_EVENT_MAP 4 (CODE, read from the lifted procedures crowd1, crowd2, c2uh, c2uf, c2dh, c2df, MakeHike, PlayHike,
MakePlayNoise, PlayNoise, PlayTackle, play, play2, playcel, PlayRan and the intro of Form_Load): every procedure here
does what its original does, in the same order, on the same slot, at the same level (base + wavol, hundredths of a
decibel), with the same waits. D-023: the +1 Hz is not reproduced, c2uh's empty ramp is (a quirk the player hears as
"no ramp"), PlayTackle waits 2.5 s, play waits to the end and play2 stops on a key. The random draws keep the ranges of
their lifted lines (GAP_REGISTER G-D2); `rng` is the game's generator (its random() is VB's Rnd: 0 <= x < 1).

The game logic (S7.3) and the menus (S7.4) call these; they never touch a slot themselves.
"""
from __future__ import annotations

import logging
import random
import time
from typing import Callable

from ..audio.engine import Audio
from ..audio.ids import foot_id
from ..audio.output import (SLOT_AMBIENT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE, SLOT_NOISE, SLOT_ONESHOT,
                            SLOT_TACKLE)
from ..data.settings import AudioSettings
from .keys import KeyInput
from .rnd import REDRAW_LIMIT

log = logging.getLogger("nfl4.game")

RAMP_STEP = 100          # hundredths of a decibel per step of the crowd 2 ramps
RAMP_PAUSE = 0.1         # dy(0.1) after every step
TACKLE_WAIT = 2.5        # PlayTackle's dy(2.5)
CELEBRATION_PAUSE = 0.4  # playcel's dy(0.4) before its foot12
MIN_CELEBRATION_FREQ = 8000
AMBIENT_FIRST = 5.0      # getkey2: st4 = Timer + 5


class GameSounds:
    def __init__(self, audio: Audio, keys: KeyInput, settings: AudioSettings, rng=None,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep):
        self.audio = audio
        self.keys = keys
        self.settings = settings
        self.rng = rng if rng is not None else random.Random()
        self.clock = clock
        self.sleep = sleep
        self.crwd1 = -1200       # crowd 1's base level: -1200 in the menus (Form_Load), -100 during a game (pag)
        self.st4 = 0.0           # PlayRan: no ambient sound starts before this time

    @property
    def wavol(self) -> int:
        """The player's sound volume, added to every level (F11 part 2; settings sound_volume)."""
        return int(self.settings.sound_level)

    def _rnd(self) -> float:
        return self.rng.random()

    def _wait_while(self, playing: Callable[[], bool]) -> None:
        """The original's loop: DoEvents, then test GetStatus (and the key for play2), again and again."""
        while True:
            self.keys.pump()
            if not playing():
                return
            self.sleep(0.001)

    # ----- start-up, the crowd beds and their ramps -----

    def intro(self) -> None:
        """Form_Load: clk, foot0 once at 0 + wavol, waited to its end, then looped at the same level until the first
        announcement stops it (stop_oneshot)."""
        self.keys.clk()
        self.audio.play(SLOT_ONESHOT, foot_id(0), self.wavol)
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)
        self.audio.play(SLOT_ONESHOT, foot_id(0), self.wavol, loop=True)

    def loop_foot0(self) -> None:
        """ChangeVoice (F12): foot0 looped at wavol while a voice loads; stop_oneshot ends it."""
        self.audio.play(SLOT_ONESHOT, foot_id(0), self.wavol, loop=True)

    def stop_oneshot(self) -> None:
        self.audio.stop(SLOT_ONESHOT)

    def crowd1(self) -> None:
        """crowd1: foot1 looping at -1200 + wavol, the file's own rate (no SetFrequency)."""
        self.audio.play(SLOT_CROWD1, foot_id(1), -1200 + self.wavol, loop=True)

    def crowd2(self) -> None:
        """crowd2: foot2 looping at -1200 + wavol, the file's own rate (no SetFrequency)."""
        self.audio.play(SLOT_CROWD2, foot_id(2), -1200 + self.wavol, loop=True)

    def start_crowds(self) -> None:
        """Form_Load's order: crowd1, crwd1 = -1200, crowd2. Also the restart after a game (GAP_REGISTER G-A5)."""
        self.crowd1()
        self.crwd1 = -1200
        self.crowd2()

    def set_crwd1(self, base: int) -> None:
        """crwd1 = base and crowd 1 to base + wavol (pag at the start of a game: -100)."""
        self.crwd1 = int(base)
        self.audio.set_volume(SLOT_CROWD1, self.crwd1 + self.wavol)

    def stop_crowds(self) -> None:
        """The end of a game (pag 0x4608f8, 0x460951): crowd 1 and crowd 2 stop."""
        self.audio.stop(SLOT_CROWD1)
        self.audio.stop(SLOT_CROWD2)

    def _ramp(self, start: int, end: int, step: int) -> None:
        """VB's For v = start To end Step step: SetVolume(v), dy(0.1). No pass when start is already past end."""
        v = start
        while (v <= end) if step > 0 else (v >= end):
            self.audio.set_volume(SLOT_CROWD2, v)
            self.keys.dy(RAMP_PAUSE)
            v += step

    def c2uh(self) -> None:
        """Meant as "up to half": its end is the current level + wavol - 600, always below the start, so the loop never
        runs and the level never changes (quirk kept, D-023; it only reads the level twice)."""
        start = self.audio.volume(SLOT_CROWD2)
        self._ramp(start, start + (-600 + self.wavol), RAMP_STEP)

    def c2uf(self) -> None:
        """Crowd 2 up to full: from its level to wavol in steps of 1 dB, 0.1 s each (from -1200: 13 steps, 1.3 s)."""
        self._ramp(self.audio.volume(SLOT_CROWD2), self.wavol, RAMP_STEP)

    def c2dh(self) -> None:
        """Crowd 2 down to half: to -600 + wavol (from full: 7 steps, 0.7 s)."""
        self._ramp(self.audio.volume(SLOT_CROWD2), -600 + self.wavol, -RAMP_STEP)

    def c2df(self) -> None:
        """Crowd 2 down to its base: to -1200 + wavol."""
        self._ramp(self.audio.volume(SLOT_CROWD2), -1200 + self.wavol, -RAMP_STEP)

    # ----- the play: hike, play noise, tackle -----

    def make_hike(self) -> None:
        """MakeHike (start-up): the hike buffer gets -1600 + wavol; nothing plays."""
        self.audio.set_volume(SLOT_HIKE, -1600 + self.wavol)

    def play_hike(self) -> None:
        """PlayHike: foot3 once from its start at -1600 + wavol, not waited, then PlayNoise."""
        self.audio.play(SLOT_HIKE, foot_id(3), -1600 + self.wavol)
        self.play_noise()

    def make_play_noise(self) -> None:
        """MakePlayNoise (start-up): the play noise buffer gets -2750 + wavol; nothing plays."""
        self.audio.set_volume(SLOT_NOISE, -2750 + self.wavol)

    def play_noise(self) -> None:
        """PlayNoise: foot14 looping at -2750 + wavol until PlayTackle stops it."""
        self.audio.play(SLOT_NOISE, foot_id(14), -2750 + self.wavol, loop=True)

    def stop_play_noise(self) -> None:
        """The clone's stop of the play noise where the original forgets it (" is way to short", Q57, G-A2)."""
        self.audio.stop(SLOT_NOISE)

    def play_noise_running(self) -> bool:
        """True while foot14 loops (GAP_REGISTER G-A2: the engine's safety net looks at it before a key wait)."""
        return self.audio.busy(SLOT_NOISE)

    def halftime(self) -> None:
        """halftime (p_485b80, called by pag at the end of the second quarter): foot0 waited, then the original draws
        Int(Rnd * 10) + 10 and overwrites it with 15 (the draw still costs a random number), 15 celebration sounds,
        foot0 waited."""
        self.play(0, 0)
        int(self._rnd() * 10)
        for _ in range(15):
            self.celebration_sound()
        self.play(0, 0)

    def play_tackle(self, n: int) -> None:
        """PlayTackle(n), n = 1, 2, 3 or 8: foot(n + 3) once at -1500 + wavol (a second tackle within the first one's
        length cuts it), the play noise stops, then 2.5 s pass whatever the sound's length (keys do not shorten it)."""
        self.audio.play(SLOT_TACKLE, foot_id(int(n) + 3), -1500 + self.wavol)
        self.audio.stop(SLOT_NOISE)
        self.keys.dy(TACKLE_WAIT)

    # ----- the one-shot slot: play, play2, the celebration -----

    def play(self, n, v: int) -> None:
        """play(n, v): clk, foot<n> once at v + wavol, waited to its end (a key does not stop it), stop."""
        self.keys.clk()
        self.audio.play(SLOT_ONESHOT, foot_id(int(n)), int(v) + self.wavol)
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)

    def play2(self, stem: str) -> None:
        """play2(stem): clk, <stem>.wav once at wavol and the file's own rate, until it ends or a key comes (the key is
        left in g for the caller, who clears it), stop."""
        self.keys.clk()
        self.audio.play(SLOT_ONESHOT, stem, self.wavol)
        self._wait_while(lambda: self.keys.code_text == "" and self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)

    def celebration_sound(self) -> None:
        """One celebration sound (playcel, halftime, superbowl, finplay17): foot15 to foot24 at -300 + wavol, frequency
        = own rate + 100 x k with k = Int(Rnd * 40) - 20 drawn again while 0, at least 8000 Hz, waited, stop."""
        sound_id = foot_id(int(self._rnd() * 10) + 15)
        rate = self.audio.rate(sound_id) or 0
        for _ in range(REDRAW_LIMIT):           # G-D1: the original's loop has no bound; a stuck source must end
            k = int(self._rnd() * 40) - 20
            if k != 0:
                break
        else:
            log.warning("celebration pitch: no draw other than 0 in %d tries, taking +100 Hz (G-D1)", REDRAW_LIMIT)
            k = 1
        freq = max(MIN_CELEBRATION_FREQ, rate + 100 * k)
        self.audio.play(SLOT_ONESHOT, sound_id, -300 + self.wavol, freq=freq)
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)

    def playcel(self) -> None:
        """The touchdown celebration: c2uf, 8 to 15 celebration sounds (Int(Rnd * 8) + 8), 0.4 s, play(12, -500), c2df."""
        self.c2uf()
        for _ in range(int(self._rnd() * 8) + 8):
            self.celebration_sound()
        self.keys.dy(CELEBRATION_PAUSE)
        self.play(12, -500)
        self.c2df()

    # ----- ambient sounds while getkey2 waits -----

    def load_ambient(self) -> None:
        """pag at the start of every game loads foot9 into the ambient buffer without playing it: the slot is idle."""
        self.audio.stop(SLOT_AMBIENT)

    def start_ambient_wait(self) -> None:
        """getkey2's first line: st4 = Timer + 5 (the first ambient sound comes after 5 s of waiting)."""
        self.st4 = self.clock() + AMBIENT_FIRST

    def play_ran(self) -> None:
        """PlayRan, called on every pass of getkey2: nothing while the ambient slot plays or before st4; else one of
        foot8 (-250), foot9 (-1200) or foot10 (pan (Int(Rnd * 30) - 15) * 100, level -2900 + |pan|), + wavol, once, not
        waited; then st4 = now + Rnd * 7 + 3 (3 to 10 s)."""
        if self.audio.busy(SLOT_AMBIENT) or self.clock() < self.st4:
            return
        choice = int(self._rnd() * 3) + 1
        pan = 0
        if choice == 1:
            sound_id, base = foot_id(8), -250
        elif choice == 2:
            sound_id, base = foot_id(9), -1200
        else:
            pan = (int(self._rnd() * 30) - 15) * 100
            sound_id, base = foot_id(10), -2900 + abs(pan)
        self.audio.play(SLOT_AMBIENT, sound_id, base + self.wavol, pan=pan)
        self.st4 = self.clock() + (self._rnd() * 7 + 3)

    # ----- the exit -----

    def stop_all(self) -> None:
        """Every slot and the extra channel stop (the exit releases the DirectSound objects, SOUND_DESIGN 4 step 1)."""
        self.audio.stop_all()
