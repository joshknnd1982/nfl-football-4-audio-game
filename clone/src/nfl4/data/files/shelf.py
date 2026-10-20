"""The saved games of one folder: three slots, the automatic save, the backup of a deleted one. This is inspired by Jim Kitchen.

CLAUDE.md 0.23, playbook 7.17, NX-S1 to NX-S8 (D-086). The original read football.sav at the start and deleted it as it loaded it (Kill),
so a crash after the load lost the game and the player had no say. A `SaveShelf` is the new keeper of the files of one folder (the
program's data folder for a classic season, the franchise's folder for a franchise); it knows nothing of the game's rules, the speech or
the season, only these files:

    football.sav, football2.sav, football3.sav   the three slots (slot 1 is the original's file, so a saved game of the original is slot 1)
    autosave.sav                                 the game in progress, written at safe points (game/pag.py), the same format
    backup\\deleted-game.sav                      the saved game the player deleted last (one level); restore brings it back
    backup\\finished-1.sav to finished-3.sav      the saves of a game that ended, kept three deep, never offered again

Every write is whole through a temporary file and a rename (`files.write`), so a crash never leaves half a save. Nothing here deletes a
save without a call from the player's choice: `delete` and `retire` MOVE the file, and the debug log writes every save, load, delete,
restore and retirement with the file and the reason. The facts of the one-sentence summary are the file's own `info` section (teams,
week, date); a file of the original has none and shows its score, quarter and the file's date.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import time
from dataclasses import dataclass, field

from ...data import debuglog
from ...game.gamestate import SavedGame
from ..healing import FileInUse
from . import savedgame
from .variant import FileDamaged

log = logging.getLogger("nfl4.data")

SLOTS = (1, 2, 3)
SLOT_FILE = {1: savedgame.FILE_NAME, 2: "football2.sav", 3: "football3.sav"}
AUTO_FILE = "autosave.sav"
BACKUP_FOLDER = "backup"
DELETED_FILE = BACKUP_FOLDER + "/deleted-game.sav"
FINISHED_PATTERN = BACKUP_FOLDER + "/finished-%d.sav"
FINISHED_COPIES = 3

OK, DAMAGED, HELD, STALE, ORPHAN = "ok", "damaged", "held", "stale", "orphan"


@dataclass
class Entry:
    """One save file as the shelf found it. `status`: ok (can be continued), damaged (named, never loaded), held (another program has
    it open), stale (it belongs to a week that is over), orphan (it belongs to no season); `reason` says why in words for the log."""
    kind: str                               # "game" (a slot) or "auto" (the automatic save)
    slot: int | None
    name: str
    status: str = OK
    reason: str = ""
    saved: SavedGame | None = None
    info: dict = field(default_factory=dict)
    stamp: float = 0.0                      # when it was saved (seconds since 1970): the info's, else the file's

    @property
    def playable(self) -> bool:
        return self.status == OK

    @property
    def is_auto(self) -> bool:
        return self.kind == "auto"


def parse_info(text: str | None) -> dict:
    if not text:
        return {}
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        return {}
    return data if isinstance(data, dict) else {}


class SaveShelf:
    def __init__(self, files, clock=time.time):
        self.files = files
        self.clock = clock

    # ----- reading -----

    def _read(self, kind: str, slot: int | None, name: str, classify=None) -> Entry | None:
        if not self.files.exists(name):
            return None
        entry = Entry(kind, slot, name)
        try:
            raw = self.files.read(name)
        except FileInUse as exc:
            entry.status, entry.reason = HELD, "in use by another program (%s)" % exc
            return entry
        except ValueError as exc:
            entry.status, entry.reason = DAMAGED, str(exc)
            return entry
        if raw is None:
            return None
        try:
            entry.saved = savedgame.decode(raw)
        except (FileDamaged, ValueError) as exc:
            entry.status, entry.reason = DAMAGED, str(exc)
            return entry
        entry.info = parse_info(entry.saved.info)
        entry.stamp = float(entry.info.get("t") or 0) or self.files.mtime(name)
        if classify is not None:
            entry.status, entry.reason = classify(entry)
        return entry

    def scan(self, classify=None) -> list[Entry]:
        """Every save file there is: the slots in order, then the automatic save. `classify(entry) -> (status, reason)` is the owner's
        check of a save that decodes (a week that is over, no season to belong to); without it every readable save is ok."""
        found = [self._read("game", slot, SLOT_FILE[slot], classify) for slot in SLOTS]
        found.append(self._read("auto", None, AUTO_FILE, classify))
        entries = [entry for entry in found if entry is not None]
        debuglog.event("save", "scan", saves=[(e.name, e.status) for e in entries])
        return entries

    def deleted(self) -> Entry | None:
        """The save the player deleted last, as the backup holds it (no checks of the owner: it is not played from there)."""
        return self._read("game", None, DELETED_FILE) if self.files.exists(DELETED_FILE) else None

    # ----- writing -----

    def _stamped(self, saved: SavedGame, slot: int | None, auto: bool) -> SavedGame:
        if saved.info is None:                  # a save made without a summary (a bare sink, the tests') stays as it was: the file's date serves
            return saved
        info = parse_info(saved.info)
        info.update({"t": round(self.clock(), 3), "slot": slot, "auto": auto})
        return dataclasses.replace(saved, info=json.dumps(info, sort_keys=True, separators=(",", ":")))

    def _write(self, name: str, saved: SavedGame, what: str, **fields) -> bool:
        try:
            data = savedgame.encode(saved)
        except Exception:
            log.exception("could not encode the %s", what)
            debuglog.event("save", "write_failed", logging.WARNING, file=name, why="could not be encoded")
            return False
        ok = self.files.write(name, data)
        debuglog.event("save", "write" if ok else "write_failed", logging.INFO if ok else logging.WARNING, file=name, what=what,
                       bytes=len(data), **fields)
        return ok

    def write_slot(self, slot: int, saved: SavedGame) -> bool:
        return self._write(SLOT_FILE[slot], self._stamped(saved, slot, False), "saved game", slot=slot)

    def write_auto(self, saved: SavedGame) -> bool:
        return self._write(AUTO_FILE, self._stamped(saved, None, True), "automatic save")

    def remove_auto(self, why: str) -> None:
        if self.files.exists(AUTO_FILE):
            self.files.remove(AUTO_FILE)
            debuglog.event("save", "auto_removed", file=AUTO_FILE, why=why)

    # ----- the backup -----

    def delete(self, entry: Entry, why: str = "the player deleted it") -> bool:
        """The save moves to the backup (the one before it there is replaced: one level). False when it could not be moved."""
        if self.files.exists(DELETED_FILE):
            self.files.remove(DELETED_FILE)
        moved = self.files.move(entry.name, DELETED_FILE)
        debuglog.event("save", "delete" if moved else "delete_failed", logging.INFO if moved else logging.WARNING, file=entry.name,
                       status=entry.status, why=why)
        return moved

    def restore(self) -> int | None:
        """The deleted save goes back to the slot it came from when that is free, else the first free slot. The slot it went to,
        or None when there is nothing to restore, every slot is taken, or it could not be moved."""
        if not self.files.exists(DELETED_FILE):
            return None
        held = self.deleted()
        wanted = parse_info(held.saved.info if held is not None and held.saved is not None else None).get("slot")
        order = ([wanted] if wanted in SLOTS else []) + [slot for slot in SLOTS if slot != wanted]
        slot = next((s for s in order if not self.files.exists(SLOT_FILE[s])), None)
        if slot is None:
            debuglog.event("save", "restore_refused", logging.INFO, why="every slot holds a game")
            return None
        if not self.files.move(DELETED_FILE, SLOT_FILE[slot]):
            debuglog.event("save", "restore_failed", logging.WARNING, slot=slot)
            return None
        debuglog.event("save", "restore", file=SLOT_FILE[slot], slot=slot)
        return slot

    def retire(self, entries: list[Entry], why: str) -> int:
        """The saves of a game that ended: moved to the backup's finished-1.sav (the older ones shift, the oldest of three goes), never
        offered again. The automatic save is simply removed (it only duplicates a game that is over)."""
        moved = 0
        for entry in entries:
            if entry.is_auto:
                self.remove_auto(why)
                continue
            if not self.files.exists(entry.name):
                continue
            self.files.remove(FINISHED_PATTERN % FINISHED_COPIES)
            for number in range(FINISHED_COPIES - 1, 0, -1):
                if self.files.exists(FINISHED_PATTERN % number):
                    self.files.move(FINISHED_PATTERN % number, FINISHED_PATTERN % (number + 1))
            if self.files.move(entry.name, FINISHED_PATTERN % 1):
                moved += 1
                debuglog.event("save", "retire", file=entry.name, why=why)
            else:
                debuglog.event("save", "retire_failed", logging.WARNING, file=entry.name)
        return moved
