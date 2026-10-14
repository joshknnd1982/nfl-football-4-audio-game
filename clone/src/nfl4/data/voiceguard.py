"""Remember a voice that killed the program, so the next start cannot be killed by it again.
This is inspired by Jim Kitchen's Brain.

A SAPI 5 voice is native code running inside Brain's process. Some voices (SmoothTalker, an emulator of a 1990 DOS
engine) can bring the whole process down, and a crash cannot be caught. If the crashing voice is the saved one, every
later start crashes the same way and the player is locked out (owner bug 2026-10-13).

The guard is a file protocol, written before the dangerous moment and removed after it:
- arm(voice): before a voice is opened (at start, or when the player picks one in F2), `voice_trial.txt` holds its id.
- clear(): once the voice has spoken something to the end, or when the program closes normally, the file is removed.
- recover(): at the next start, a file that is still there means the program died while the voice was in trial: the
  voice is added to `crashed_voices.txt` and Brain starts with the default voice instead, saying so once.
- forget(voice): picking the voice again in F2 is the player asking for another try: it leaves the list.
Every call survives a missing or read-only folder: the guard must never be the thing that stops the game.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

TRIAL_FILE = "voice_trial.txt"
CRASHED_FILE = "crashed_voices.txt"
MAX_LISTED = 50


def voice_label(voice_id: str) -> str:
    """A short name for a voice id (the last part of the registry path), for a spoken notice."""
    return (voice_id or "").replace("/", "\\").rstrip("\\").rsplit("\\", 1)[-1] or "voice"


class VoiceGuard:
    def __init__(self, folder: str):
        self.folder = folder
        self._trial = os.path.join(folder, TRIAL_FILE)
        self._crashed = os.path.join(folder, CRASHED_FILE)

    # ----- the file protocol -----
    def arm(self, voice_id: str | None) -> None:
        if not voice_id:
            self.clear()
            return
        try:
            os.makedirs(self.folder, exist_ok=True)
            with open(self._trial, "w", encoding="utf-8") as handle:
                handle.write(voice_id.strip() + "\n")
        except OSError as exc:
            log.debug("voice trial not recorded: %s", exc)

    def clear(self) -> None:
        try:
            os.remove(self._trial)
        except OSError:
            pass

    def recover(self) -> str | None:
        """A trial that never ended: the voice in it crashed the program. Returns its id (now on the list)."""
        try:
            with open(self._trial, encoding="utf-8", errors="replace") as handle:
                voice_id = handle.readline().strip()
        except OSError:
            return None
        self.clear()
        if not voice_id:
            return None
        log.warning("the voice %s did not survive the last start: it is set aside", voice_id)
        self._write(self.crashed() + [voice_id] if not self.is_crashed(voice_id) else self.crashed())
        return voice_id

    # ----- the list -----
    def crashed(self) -> list[str]:
        try:
            with open(self._crashed, encoding="utf-8", errors="replace") as handle:
                return [line.strip() for line in handle if line.strip()]
        except OSError:
            return []

    def is_crashed(self, voice_id: str | None) -> bool:
        wanted = (voice_id or "").strip().lower()
        return bool(wanted) and any(v.lower() == wanted for v in self.crashed())

    def forget(self, voice_id: str | None) -> None:
        wanted = (voice_id or "").strip().lower()
        remaining = [v for v in self.crashed() if v.lower() != wanted]
        if len(remaining) != len(self.crashed()):
            self._write(remaining)

    def _write(self, ids: list[str]) -> None:
        try:
            os.makedirs(self.folder, exist_ok=True)
            with open(self._crashed, "w", encoding="utf-8") as handle:
                handle.write("\n".join(ids[-MAX_LISTED:]) + ("\n" if ids else ""))
        except OSError as exc:
            log.debug("crashed voices not recorded: %s", exc)
