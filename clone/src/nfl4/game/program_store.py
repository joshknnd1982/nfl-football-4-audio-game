"""What the program's start-up and week loop read from and write to the player's files. This is inspired by Jim Kitchen.

GAME_SPEC 3 and 12 (Form_Load reads football.sav, footbal0.dat, footbal1.dat to footbal5.dat, football.gtp and footplay.txt
and opens footballlog.txt). S7.4b only needs the SHAPE of the files, as the earlier sessions did for SeasonStore (the
engine's writes) and SetupStore (the set-up's writes): a `ProgramStore` is the read side and the few extra writes of the
program itself. S7.5 implements it over the real files (the original's value order, GAME_SPEC 12, D-024 item 4);
until then the program runs on `MemoryProgramStore`, which keeps everything for one run, so a season, a saved game and the
log live exactly as long as the process, and the first start is shown once.

The reads happen once, at the start (`load_season`); the week loop then works on the Game's `SeasonState`, which the engine
keeps in step with the files through the SeasonStore (the original re-reads football.gtp, footbal2.dat and footbal3.dat at
every pass of its week loop, and those values are what the state holds).
"""
from __future__ import annotations

from typing import Protocol

from .gamestate import SavedGame
from .season import SeasonState
from .setup import Roster


class ProgramStore(Protocol):
    def first_run(self) -> bool: ...                             # footbal0.dat missing: the welcome and the voice choice
    def has_saved_game(self) -> bool: ...                        # football.sav is there (SavedGame = 1)
    def load_season(self, season: SeasonState) -> bool: ...      # footbal1.dat first value not 0: the season continues
    def open_log(self, fresh: bool) -> None: ...                 # footballlog.txt: Output (fresh) or Append
    def player_names(self) -> Roster | None: ...                 # footplay.txt read and valid (pag's gpn)
    def take_saved_game(self) -> SavedGame | None: ...           # football.sav read, then deleted (pag)
    def save_game(self, saved: SavedGame) -> None: ...           # football.sav written (Save Game)
    def delete_season_files(self) -> None: ...                   # the season's end: footbal1 to 5, football.gtp, footplay.txt


class MemoryProgramStore:
    """Everything in memory for one run (the S7.4b program, the tests). `first` says whether this start shows the welcome."""

    def __init__(self, first: bool = False):
        self.first = first
        self.saved: SavedGame | None = None
        self.names: Roster | None = None
        self.season_exists = False
        self.log_opened: list[bool] = []         # the `fresh` of every open_log (the original opens it once per run)
        self.deleted = 0                         # how many times the season files were deleted

    def first_run(self) -> bool:
        return self.first

    def has_saved_game(self) -> bool:
        return self.saved is not None

    def load_season(self, season: SeasonState) -> bool:
        return self.season_exists

    def open_log(self, fresh: bool) -> None:
        self.log_opened.append(fresh)

    def player_names(self) -> Roster | None:
        return self.names

    def take_saved_game(self) -> SavedGame | None:
        saved, self.saved = self.saved, None
        return saved

    def save_game(self, saved: SavedGame) -> None:
        self.saved = saved

    def delete_season_files(self) -> None:
        self.deleted += 1
        self.season_exists = False
