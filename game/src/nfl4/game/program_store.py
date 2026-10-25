"""What the program's start-up and week loop read from and write to the player's files. This is inspired by Jim Kitchen.

GAME_SPEC 3 and 12 (Form_Load reads football.sav, footbal0.dat, footbal1.dat to footbal5.dat, football.gtp and footplay.txt
and opens footballlog.txt). S7.4b only needs the SHAPE of the files, as the earlier sessions did for SeasonStore (the
engine's writes) and SetupStore (the set-up's writes): a `ProgramStore` is the read side and the few extra writes of the
program itself. S7.5 implements it over the real files in `data/files/store.py` (`FileProgramStore`: the original's value
order, GAME_SPEC 12, D-024 item 4, which app.py hands to the Game); `MemoryProgramStore` keeps everything for one run, so
a season, a saved game and the log live exactly as long as the process, and the first start is shown once: the tests'
store.

The reads happen once, at the start (`load_season`); the week loop then works on the Game's `SeasonState`, which the engine
keeps in step with the files through the SeasonStore (the original re-reads football.gtp, footbal2.dat and footbal3.dat at
every pass of its week loop, and those values are what the state holds).

SX.14 (CLAUDE.md 0.23, playbook 7.17): the saved games are kept by a `shelf` (data/files/shelf.py: three slots, the automatic save and
the backup), and nothing deletes one when it is loaded. The season has its own peek, delete and restore here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..data.files.shelf import AUTO_FILE, OK, SLOT_FILE, SLOTS, Entry
from .gamestate import SavedGame
from .season import SeasonState
from .setup import Roster


@dataclass
class SeasonPeek:
    """A season in progress, as the files hold it before it is loaded (the start-up menu's sentence about it)."""
    coach: str
    tn1: int
    tn2: int
    gtp: int
    wins: int
    losses: int


class ProgramStore(Protocol):
    def first_run(self) -> bool: ...                             # footbal0.dat missing: the welcome and the voice choice
    def has_saved_game(self) -> bool: ...                        # a saved game that can be continued is there (SavedGame = 1)
    def load_season(self, season: SeasonState) -> bool: ...      # footbal1.dat first value not 0: the season continues
    def open_log(self, fresh: bool) -> None: ...                 # footballlog.txt: Output (fresh) or Append
    def player_names(self) -> Roster | None: ...                 # footplay.txt read and valid (pag's gpn)
    def save_game(self, saved: SavedGame, slot: int | None = None) -> bool | None: ...   # a slot written (Save Game); False = it could not be
    def write_player_names(self, roster: Roster) -> object: ...  # footplay.txt written after pag drew the player's names
    def log_line(self, text: str) -> None: ...                   # footballlog.txt: one line (Print #3), the Game's log_sink
    def delete_season_files(self) -> None: ...                   # the season's end: footbal1 to 5, football.gtp, footplay.txt
    # SX.14 (rule 0.23): the saved games and the season the player chooses among at the start
    shelf: object                                                # the keeper of the slots, the automatic save and the backup
    def classify(self, entry: Entry) -> tuple[str, str]: ...     # (status, reason) of a save that decodes: ok, stale, orphan
    def autosave(self, saved: SavedGame) -> bool: ...            # the automatic save, whole
    def season_peek(self) -> SeasonPeek | None: ...              # the season in the files, before it is loaded
    def delete_season(self) -> bool: ...                         # the season moves to the backup
    def restore_season(self) -> bool: ...                        # and comes back, when no season is there
    def season_deleted(self) -> bool: ...                        # a deleted season is in the backup


class MemoryShelf:
    """The shelf's calls over entries kept in memory (the tests' store): no file, no encoding, so a test may put any object in a slot."""

    def __init__(self):
        self.slots: dict[int, Entry] = {}
        self.auto: Entry | None = None
        self.backup: Entry | None = None
        self.finished: list[Entry] = []
        self.clock = 1_000_000_000.0

    def _entry(self, kind, slot, name, saved) -> Entry:
        self.clock += 1.0
        info = {}
        if getattr(saved, "info", None):
            import json
            info = json.loads(saved.info)
        info.update({"slot": slot, "auto": kind == "auto", "t": self.clock})
        return Entry(kind, slot, name, OK, "", saved, info, self.clock)

    def scan(self, classify=None) -> list[Entry]:
        found = [self.slots[slot] for slot in SLOTS if slot in self.slots] + ([self.auto] if self.auto is not None else [])
        if classify is not None:
            for entry in found:
                if entry.saved is not None and entry.status == OK:
                    entry.status, entry.reason = classify(entry)
        return found

    def deleted(self) -> Entry | None:
        return self.backup

    def write_slot(self, slot: int, saved) -> bool:
        self.slots[slot] = self._entry("game", slot, SLOT_FILE[slot], saved)
        return True

    def write_auto(self, saved) -> bool:
        self.auto = self._entry("auto", None, AUTO_FILE, saved)
        return True

    def remove_auto(self, why: str) -> None:
        self.auto = None

    def delete(self, entry: Entry, why: str = "") -> bool:
        self.backup = entry
        if entry.is_auto:
            self.auto = None
        else:
            self.slots.pop(entry.slot, None)
        return True

    def restore(self) -> int | None:
        if self.backup is None:
            return None
        wanted = self.backup.info.get("slot")
        order = ([wanted] if wanted in SLOTS else []) + [slot for slot in SLOTS if slot != wanted]
        slot = next((s for s in order if s not in self.slots), None)
        if slot is None:
            return None
        entry, self.backup = self.backup, None
        entry.slot, entry.kind, entry.name = slot, "game", SLOT_FILE[slot]
        self.slots[slot] = entry
        return slot

    def retire(self, entries, why: str) -> int:
        moved = 0
        for entry in entries:
            if entry.is_auto:
                self.auto = None
            elif self.slots.get(entry.slot) is entry or entry.slot in self.slots:
                self.finished.insert(0, self.slots.pop(entry.slot))
                moved += 1
        return moved


class MemoryProgramStore:
    """Everything in memory for one run (the S7.4b program, the tests). `first` says whether this start shows the welcome."""

    def __init__(self, first: bool = False):
        self.first = first
        self.shelf = MemoryShelf()
        self.names: Roster | None = None
        self.season_exists = False
        self.season_backup = False
        self.peek: SeasonPeek | None = None      # a test sets it to give the start-up menu a season to speak about
        self.log_opened: list[bool] = []         # the `fresh` of every open_log (the original opens it once per run)
        self.deleted = 0                         # how many times the season files were deleted
        self.log_lines: list[str] = []           # what the Game logged (Print #3)

    @property
    def saved(self):
        """Slot 1's saved game (the original's football.sav), or None: what the tests of the original's flow look at."""
        entry = self.shelf.slots.get(1)
        return entry.saved if entry is not None else None

    @saved.setter
    def saved(self, value) -> None:
        if value is None:
            self.shelf.slots.pop(1, None)
        else:
            self.shelf.write_slot(1, value)

    def first_run(self) -> bool:
        return self.first

    def has_saved_game(self) -> bool:
        return any(entry.playable for entry in self.shelf.scan(self.classify))

    def classify(self, entry: Entry) -> tuple[str, str]:
        return OK, ""

    def load_season(self, season: SeasonState) -> bool:
        return self.season_exists

    def open_log(self, fresh: bool) -> None:
        self.log_opened.append(fresh)

    def player_names(self) -> Roster | None:
        return self.names

    def save_game(self, saved: SavedGame, slot: int | None = None) -> bool:
        self.shelf.write_slot(slot or 1, saved)
        return True

    def autosave(self, saved: SavedGame) -> bool:
        return self.shelf.write_auto(saved)

    def write_player_names(self, roster: Roster) -> None:
        self.names = roster

    def log_line(self, text: str) -> None:
        self.log_lines.append(text)

    def delete_season_files(self) -> None:
        self.deleted += 1
        self.season_exists = False

    def season_peek(self) -> SeasonPeek | None:
        return self.peek if self.season_exists else None

    def delete_season(self) -> bool:
        self.season_exists, self.season_backup = False, True
        return True

    def restore_season(self) -> bool:
        if self.season_exists or not self.season_backup:
            return False
        self.season_exists, self.season_backup = True, False
        return True

    def season_deleted(self) -> bool:
        return self.season_backup
