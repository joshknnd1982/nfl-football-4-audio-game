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
import os
import random
import time
from typing import Callable

from ..audio.engine import Audio
from ..audio.ids import foot_id
from ..audio.pools import POOLS, Member
from ..audio.output import (EXTRA_SLOT, SLOT_AMBIENT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE, SLOT_NOISE, SLOT_ONESHOT,
                            SLOT_TACKLE)
from ..data.settings import AudioSettings
from . import extra_texts as words
from .keys import KeyInput
from .rnd import REDRAW_LIMIT

log = logging.getLogger("nfl4.game")

RAMP_STEP = 100          # hundredths of a decibel per step of the crowd 2 ramps
RAMP_PAUSE = 0.1         # dy(0.1) after every step
TACKLE_WAIT = 2.5        # PlayTackle's dy(2.5)
CELEBRATION_PAUSE = 0.4  # playcel's dy(0.4) before its foot12
MIN_CELEBRATION_FREQ = 8000
AMBIENT_FIRST = 5.0      # getkey2: st4 = Timer + 5
AMBIENT_LEVELS = {8: -250, 9: -1200}   # PlayRan's levels of foot8 and foot9; foot10 is panned (see play_ran)
ADDED_AMBIENT_LEVEL = -1200            # a member the player added (rule 0.14): foot9's level, centered (D-068)
COMMERCIAL_EVERY = {"off": 0, "every": 1, "second": 2, "third": 3}   # the Sounds menu setting (rule 0.14, D-068)
COMMERCIAL_ATTEMPTS = 5                # files tried at one break before it goes without


class GameSounds:
    def __init__(self, audio: Audio, keys: KeyInput, settings: AudioSettings, rng=None,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep):
        self.audio = audio
        self.keys = keys
        self.settings = settings
        self.rng = rng if rng is not None else random.Random()
        self.clock = clock
        self.sleep = sleep
        self.commercials = None  # game.commercials.Commercials: the player's commercial files (rule 0.14), None in the tests
        self.announce: Callable[[str], None] | None = None   # speaks a sentence and waits for it (set by the Game)
        self._commercial_breaks = 0   # the breaks seen while the setting is on, for "every second / third break"
        self.crwd1 = -1200       # crowd 1's base level: -1200 in the menus (Form_Load), -100 during a game (pag)
        self.st4 = 0.0           # PlayRan: no ambient sound starts before this time
        # NX-M1, NX-M2 (D-148, the owner 2026-10-24: "remove the startup music and touchdown celebration sounds, allowing the user to insert their
        # own sounds"): True while the owner's own mode is in use (the N. F. L. rules; set by the Game and the program). Then the original's music
        # (foot0) and celebration sounds (foot15 to foot24, playcel's foot12) are not played: the slots `music` and `celebration` play the player's
        # file (sounds folder), else a developer's file of that name in the program's sounds_nx, else nothing, with the same random draws.
        self.own_mode: Callable[[], bool] = lambda: False

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

    # ----- NX-M1, NX-M2: the music and celebration slots -----

    def slot_files(self, name: str) -> list:
        """The files of a slot: the player's (sounds folder) first, then the developer's (the program's sounds_nx), as the stadium's families
        are found (extras/stadium.family); [] when there is none or the folders cannot be read."""
        try:
            from ..extras import stadium
            return stadium.family(name, (stadium.player_folder(), stadium.shipped_folder()))
        except Exception as exc:                      # a slot never stops the game
            log.debug("the %s slot could not be read: %s", name, exc)
            return []

    def music_file(self) -> str | None:
        files = self.slot_files("music")
        return files[0] if files else None

    def intro_name(self) -> str:
        """What the start's loop is, for the log (rule 0.15): the original's foot0, the music slot's file, or the empty slot (NX-M1)."""
        if not self._own():
            return "intro foot0"
        path = self.music_file()
        return "music " + os.path.basename(path) if path else "music slot empty (no file, nothing plays)"

    def _own(self) -> bool:
        try:
            return bool(self.own_mode())
        except Exception:
            return False

    def intro(self) -> None:
        """Form_Load: clk, foot0 once at 0 + wavol, waited to its end, then looped at the same level until the first
        announcement stops it (stop_oneshot). NX-M1: in the owner's mode the music slot's file instead, else nothing."""
        if self._own():
            self.keys.clk()
            path = self.music_file()
            if path is not None:
                self.audio.play_file(SLOT_ONESHOT, path, self.wavol, loop=True)       # looped until the welcome stops it (rule 0.21)
            return
        self.keys.clk()
        self.audio.play(SLOT_ONESHOT, foot_id(0), self.wavol)
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)
        self.audio.play(SLOT_ONESHOT, foot_id(0), self.wavol, loop=True)

    def loop_foot0(self) -> None:
        """ChangeVoice (F12): foot0 looped at wavol while a voice loads; stop_oneshot ends it. NX-M1: the music slot's file, else nothing."""
        if self._own():
            path = self.music_file()
            if path is not None:
                self.audio.play_file(SLOT_ONESHOT, path, self.wavol, loop=True)
            return
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

    def crowd2_level(self) -> int:
        """Crowd 2's level now (GetVolume: base + wavol), which adjvol reads before its ramp to put it back (S7.4a)."""
        return int(self.audio.volume(SLOT_CROWD2))

    def set_crowd_levels(self, crowd1: int, crowd2: int | None = None) -> None:
        """SetVolume of crowd 1 (and crowd 2) to levels that already hold wavol (adjvol's sound step, F11)."""
        self.audio.set_volume(SLOT_CROWD1, int(crowd1))
        if crowd2 is not None:
            self.audio.set_volume(SLOT_CROWD2, int(crowd2))

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

    # SY.3: the N. F. L. rules' whistles. The stadium (extras/stadium.py) installs `whistle_hook` while a game with its sounds is played: asked at
    # every whistle (PlayTackle(8)) with the context the caller named (`whistle_context`: "quarter", "final", "twominute", "timeout", "penalty",
    # "review", or None), it answers the path of a pea whistle, or None for the original's foot11. The wait of 2.5 s is the original's either way.
    whistle_hook = None
    whistle_context = None

    def play_tackle(self, n: int) -> None:
        """PlayTackle(n), n = 1, 2, 3 or 8: foot(n + 3) once at -1500 + wavol (a second tackle within the first one's
        length cuts it), the play noise stops, then 2.5 s pass whatever the sound's length (keys do not shorten it)."""
        alternative = None
        if n == 8 and self.whistle_hook is not None:
            try:
                alternative = self.whistle_hook(self.whistle_context)
            except Exception as exc:
                log.warning("the whistle could not be chosen: %s", exc)
            self.whistle_context = None
        if alternative:
            self.audio.play_file(SLOT_TACKLE, alternative, -1500 + self.wavol)
        else:
            self.audio.play(SLOT_TACKLE, foot_id(int(n) + 3), -1500 + self.wavol)
        self.audio.stop(SLOT_NOISE)
        self.keys.dy(TACKLE_WAIT)

    # ----- the one-shot slot: play, play2, the celebration -----

    def play(self, n, v: int) -> None:
        """play(n, v): clk, foot<n> once at v + wavol, waited to its end (a key does not stop it), stop. NX-M1: foot0, the original's music, is the
        music slot's file in the owner's mode (the exit, the halftime show), else nothing."""
        if int(n) == 0 and self._own():
            self.keys.clk()
            path = self.music_file()
            if path is not None:
                self.play_file(path)
            return
        self.keys.clk()
        self.audio.play(SLOT_ONESHOT, foot_id(int(n)), int(v) + self.wavol)
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)

    def play_file(self, path: str, limit: float | None = None) -> None:
        """The banter's [sound file] (D-048): clk, the player's file once at wavol and its own rate on the one-shot slot,
        waited to its end (a key does not stop it, like play), stop. A file that cannot be used plays nothing and nothing
        waits for it. `limit`: the most seconds to wait (the banter caps the sounds of one line, so a line of long files
        cannot hold the game for minutes); the sound is stopped then."""
        self.keys.clk()
        self.audio.play_file(SLOT_ONESHOT, path, self.wavol)
        end = None if limit is None else self.clock() + limit
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT) and (end is None or self.clock() < end))
        self.audio.stop(SLOT_ONESHOT)

    def play_effect(self, path: str, level: int = 0, slot: int = EXTRA_SLOT) -> None:
        """A stadium sound of the N. F. L. rules (SY.2, extras/stadium.py): the file once on the extra channel, `level` hundredths of a
        decibel under the sound volume. Nothing waits for it, no key stops it, no random number is drawn; a file that cannot be used plays
        nothing (the library logs it)."""
        try:
            self.audio.play_file(slot, path, int(level) + self.wavol)
        except Exception as exc:
            log.warning("a stadium sound could not be played: %s", exc)

    def play2(self, stem: str) -> None:
        """play2(stem): clk, <stem>.wav once at wavol and the file's own rate, until it ends or a key comes (the key is
        left in g for the caller, who clears it), stop."""
        self.keys.clk()
        if stem == "foot0" and self._own():           # NX-M1: the volume demo is the music slot's file, else the officials' whistle
            path = self.music_file() or next(iter(self.slot_files("whistle")), None)
            if path is not None:
                self.audio.play_file(SLOT_ONESHOT, path, self.wavol)
                self._wait_while(lambda: self.keys.code_text == "" and self.audio.busy(SLOT_ONESHOT))
                self.audio.stop(SLOT_ONESHOT)
            return
        self.audio.play(SLOT_ONESHOT, stem, self.wavol)
        self._wait_while(lambda: self.keys.code_text == "" and self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)

    def _members(self, pool_name: str) -> list[Member]:
        """What the pool draws from (audio/pools.py): the original members plus the player's added files. Without a library
        (a fake audio) the original's list."""
        library = getattr(self.audio, "library", None)
        if library is None or not hasattr(library, "pool_members"):
            return [Member(foot_id(n), None, n) for n in POOLS[pool_name].originals]
        return library.pool_members(pool_name)

    def celebration_sound(self) -> None:
        """One celebration sound (playcel, halftime, superbowl, finplay17): a member of the celebration pool (foot15 to
        foot24 and the player's added celebration<N> files) at -300 + wavol, frequency = own rate + 100 x k with
        k = Int(Rnd * 40) - 20 drawn again while 0, at least 8000 Hz, waited, stop. The draw is Int(Rnd * count) with the
        pool's count, 10 while nothing is added, so the original's draws are unchanged (rule 0.14, D-068)."""
        members = self._members("celebration")
        silent = False
        if self._own():                             # NX-M2: the player's added files and the developer's, never foot15 to foot24
            own = [m for m in members if m.added]
            same = lambda path: os.path.normcase(os.path.abspath(path))      # noqa: E731  (the player's file is in both lists once)
            known = {same(m.path) for m in own}
            own += [Member(None, path, 1000 + n) for n, path in enumerate(self.slot_files("celebration")) if same(path) not in known]
            silent = not own
            members = own if own else members       # silent: the original's count for the draws, nothing played
        index = int(self._rnd() * max(len(members), 1))
        if not members:
            return                                  # every member switched off: nothing to play (7.7.1)
        if silent:
            for _ in range(REDRAW_LIMIT):           # the same pitch draws as the original, so a seeded game is the same game
                if int(self._rnd() * 40) - 20 != 0:
                    break
            return
        member = members[min(index, len(members) - 1)]
        rate = self.audio.member_rate(member) or 0
        for _ in range(REDRAW_LIMIT):           # G-D1: the original's loop has no bound; a stuck source must end
            k = int(self._rnd() * 40) - 20
            if k != 0:
                break
        else:
            log.warning("celebration pitch: no draw other than 0 in %d tries, taking +100 Hz (G-D1)", REDRAW_LIMIT)
            k = 1
        freq = max(MIN_CELEBRATION_FREQ, rate + 100 * k)
        self.audio.play_member(SLOT_ONESHOT, member, -300 + self.wavol, freq=freq)
        self._wait_while(lambda: self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)

    def celebration_run(self) -> None:
        """8 to 15 celebration sounds (Int(Rnd * 8) + 8 of them, each waited): the run of playcel, of the Super Bowl
        presentation (superbowl: twice when the player's team won, once when the opponent won) and of finplay17's Super
        Bowl (S7.3c; the Rnd calls at 0x484bab, 0x48541f and 0x483f73). Like the other sound procedures it draws a bare
        Rnd (S7.2), so the draw trace records size 0 for these draws (the golden transcript holds the same sizes)."""
        for _ in range(int(self._rnd() * 8) + 8):
            self.celebration_sound()

    def playcel(self) -> None:
        """The touchdown celebration: c2uf, 8 to 15 celebration sounds (Int(Rnd * 8) + 8), 0.4 s, play(12, -500), c2df."""
        self.c2uf()
        self.celebration_run()
        if self._own():                             # NX-M2: no closing foot12 and no pause after a celebration that is the slot's
            self.c2df()
            return
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
        """PlayRan, called on every pass of getkey2: nothing while the ambient slot plays or before st4; else one member of
        the ambient pool: foot8 (-250), foot9 (-1200) or foot10 (pan (Int(Rnd * 30) - 15) * 100, level -2900 + |pan|), or a
        file the player added (-1200, centered), + wavol, once, not waited; then st4 = now + Rnd * 7 + 3 (3 to 10 s). The
        draw is Int(Rnd * count), 3 while nothing is added (rule 0.14)."""
        if self.audio.busy(SLOT_AMBIENT) or self.clock() < self.st4:
            return
        members = self._members("ambient")
        index = int(self._rnd() * max(len(members), 1))
        if members:
            member = members[min(index, len(members) - 1)]
            pan = 0
            if member.added:
                base = ADDED_AMBIENT_LEVEL
            elif member.number == 10:
                pan = (int(self._rnd() * 30) - 15) * 100
                base = -2900 + abs(pan)
            else:
                base = AMBIENT_LEVELS[member.number]
            self.audio.play_member(SLOT_AMBIENT, member, base + self.wavol, pan=pan)
        self.st4 = self.clock() + (self._rnd() * 7 + 3)

    # ----- commercials (owner rule 0.14, playbook 7.7.1, game/commercials.py) -----

    def commercial(self, break_name: str) -> None:
        """A break of the game (the quarter, the two minute warning, half time, the end): when the player turned commercials
        on and put sound files in the commercials folder, the sentence "Commercial", then one of them, until it ends or a key
        comes (that key is not passed on). Draws come from the commercials' own random object, never the game's, and nothing
        is kept in a save, so the game is the same with commercials on or off. With the setting off, a missing or empty
        folder or no usable file: nothing happens and nothing waits."""
        every = COMMERCIAL_EVERY.get(getattr(self.settings, "commercials", "off"), 0)
        if every == 0 or self.commercials is None:
            return
        self._commercial_breaks += 1
        if self._commercial_breaks % every:
            return
        path = None
        for _ in range(COMMERCIAL_ATTEMPTS):
            wanted = self.commercials.choose(break_name)
            if wanted is None:
                return
            if self.audio.library.pick_file(wanted).sound is not None:
                path = wanted
                break
        if path is None:
            return
        if self.announce is not None:
            self.announce(words.COMMERCIAL_CUE)
        self.keys.clk()
        self.audio.play_file(SLOT_ONESHOT, path, self.wavol)
        self._wait_while(lambda: self.keys.code_text == "" and self.audio.busy(SLOT_ONESHOT))
        self.audio.stop(SLOT_ONESHOT)
        self.keys.clk()                              # the key that skipped it goes no further

    # ----- the exit -----

    def exit_beep(self) -> None:
        """One of the exit's two Beeps (SOUND_DESIGN 4 step 3): the player's beep_exit file, the Windows default sound, or the
        generated blip."""
        self.audio.beep_exit()

    def stop_all(self) -> None:
        """Every slot and the extra channel stop (the exit releases the DirectSound objects, SOUND_DESIGN 4 step 1)."""
        self.audio.stop_all()
