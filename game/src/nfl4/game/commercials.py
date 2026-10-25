"""The player's commercials: the files, the folder and the order they play in. This is inspired by Jim Kitchen.

Owner rule 0.14 (2026-10-16), playbook 7.7.1, CUSTOMIZABLE_CONTENT 15. The original has no commercials and the game ships
none. The player puts sound files (any name, any format the sound layer reads) in the commercials folder in the per-user
data; a file in the folder itself may play at any break, a file in a subfolder named for a break plays only there:

    commercials\\quarter, commercials\\two-minute-warning, commercials\\halftime, commercials\\final

The Sounds menu setting (off by default) says how often one plays; GameSounds.commercial plays it. The order is a shuffle
(none repeats until all have played) drawn from this object's OWN random generator, so the game's draws, seeds, saved games
and replays are the same with commercials on or off.
"""
from __future__ import annotations

import logging
import os
import random
from typing import Callable

from ..audio.wavdata import DECODER_EXTENSIONS

log = logging.getLogger("nfl4.game")

BREAKS = ("quarter", "two-minute-warning", "halftime", "final")
NOTE_NAME = "About commercials.txt"

NOTE_TEXT = """About commercials. NFL Football 4 comes with no commercials. This folder is yours.

Put sound files here (wav, ogg, flac or mp3, any name, any length) and turn commercials on in the Sounds menu (F9, Sounds,
Commercials; the setting is off until you change it). A commercial then plays at a break of the game, after the break has
been spoken, and any key skips it. They play in a shuffled order, and none repeats until all have been played.

A file in this folder can play at any break. A file in one of these folders plays only at that break:
  quarter              the end of the first and the third quarter
  two-minute-warning   the two minute warning
  halftime             half time, before the second half kicks off
  final                the end of the game, after the final score

Only your own files belong here. The game gives you none and takes none. If a file cannot be read the game skips it.
You can delete this note; the game makes it again.
"""


class Commercials:
    def __init__(self, folder: str, rng: random.Random | None = None):
        self.folder = folder
        self.rng = rng if rng is not None else random.Random()     # its own: never the game's (7.7.1)
        self._bags: dict[str, list[str]] = {}
        self._last: dict[str, str] = {}
        self.ensure()

    # ----- the folder (playbook 7.10: recreated when it is missing, never an error) -----

    def ensure(self) -> bool:
        """Make the folder, the four break folders and the note when they are missing. False when that cannot be done."""
        try:
            os.makedirs(self.folder, exist_ok=True)
            for name in BREAKS:
                os.makedirs(os.path.join(self.folder, name), exist_ok=True)
            note = os.path.join(self.folder, NOTE_NAME)
            if not os.path.exists(note):
                with open(note, "w", encoding="utf-8", newline="\r\n") as handle:
                    handle.write(NOTE_TEXT)
            return True
        except OSError:
            log.warning("could not make the commercials folder %s", self.folder, exc_info=True)
            return False

    def refresh(self) -> None:
        """The Sounds menu's reload: make what is missing and start the shuffles again."""
        self.ensure()
        self._bags.clear()

    # ----- the files -----

    def candidates(self, break_name: str) -> list[str]:
        """The full paths a break may play: the files in the folder itself, then the files in the break's own folder."""
        found: list[str] = []
        for folder in (self.folder, os.path.join(self.folder, break_name)):
            try:
                names = sorted(os.listdir(folder), key=str.lower)
            except OSError as exc:
                log.debug("commercials folder %s cannot be listed (%s)", folder, exc)
                continue
            for name in names:
                path = os.path.join(folder, name)
                if name.lower().endswith(DECODER_EXTENSIONS) and os.path.isfile(path):
                    found.append(path)
        return found

    def count(self) -> int:
        """How many commercial files the folders hold (each file counted once)."""
        seen = set()
        for name in BREAKS:
            seen.update(path.lower() for path in self.candidates(name))
        return len(seen)

    def choose(self, break_name: str) -> str | None:
        """The next commercial for this break, or None when there is none. A shuffled bag per break: every file is used
        once before any is used again, and the first of a new bag is never the last one played."""
        available = self.candidates(break_name)
        if not available:
            self._bags.pop(break_name, None)
            return None
        bag = [path for path in self._bags.get(break_name, []) if path in available]
        if not bag:
            bag = list(available)
            self.rng.shuffle(bag)
            last = self._last.get(break_name)
            if len(bag) > 1 and bag[-1] == last:        # pop() takes the end: do not repeat the file just played
                bag[0], bag[-1] = bag[-1], bag[0]
        path = bag.pop()
        self._bags[break_name] = bag
        self._last[break_name] = path
        return path
