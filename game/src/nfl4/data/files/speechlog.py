"""footballlog.txt: the log of the spoken text. This is inspired by Jim Kitchen.

GAME_SPEC 12 and GAP_REGISTER G-S10: the original opens it once per run (Output, with a title line, when there is no
saved game and gtp = 1, else Append) and each speaker does `Print #3` while the form flag ptf is 1. Nothing reads the
file; it is the player's record of a game. The game keeps those rules and adds two for safety: a file larger than
1 MB is started again (at opening and while it grows), and a write error is logged once and the log is switched off
for the rest of the run (never an error for the player).

`SpeechLog.open(fresh)` and `SpeechLog.line(text)` are the whole interface; `FileProgramStore` hands `line` to the Game as
its `log_sink`. Lines are UTF-8 with CRLF endings, so Notepad shows each on its own line.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger("nfl4.data")

FILE_NAME = "footballlog.txt"
SIZE_CAP = 1_000_000


class SpeechLog:
    def __init__(self, path: str, cap: int = SIZE_CAP):
        self.path = path
        self.cap = cap
        self._handle = None
        self._size = 0
        self._failed = False

    @property
    def is_open(self) -> bool:
        return self._handle is not None

    def open(self, fresh: bool) -> None:
        """Output (a new empty file) when `fresh`, else Append; an existing file over the cap is started again."""
        self.close()
        self._failed = False
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
            mode = "w" if fresh or size > self.cap else "a"
            self._handle = open(self.path, mode, encoding="utf-8", newline="\r\n", buffering=1)
            self._size = 0 if mode == "w" else size
        except OSError:
            self._give_up("could not open %s" % self.path)

    def line(self, text: str) -> None:
        handle = self._handle
        if handle is None:
            return
        try:
            if self._size > self.cap:             # the file grew past the cap during the run: start it again
                handle.close()
                handle = self._handle = open(self.path, "w", encoding="utf-8", newline="\r\n", buffering=1)
                self._size = 0
            handle.write(text + "\n")
            self._size += len(text) + 2
        except (OSError, ValueError):
            self._give_up("could not write %s" % self.path)

    def close(self) -> None:
        handle, self._handle = self._handle, None
        if handle is not None:
            try:
                handle.close()
            except OSError as exc:
                log.debug("footballlog.txt did not close cleanly (%s)", exc)

    def _give_up(self, why: str) -> None:
        if not self._failed:
            log.warning("%s: the speech log is switched off for this run", why, exc_info=True)
        self._failed = True
        self.close()
