"""The franchise's files: league.sav with its backup and healing, football.sav, history.txt, and the three store protocols over
them (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.1, 10.1 and 10.2. `FranchiseStore` is what the program swaps in for the classic `FileProgramStore` while
the franchise is in use: it is the ProgramStore (`game/program_store.py`), the SeasonStore (the engine's writes) and the
SetupStore (the set-up's writes) over ONE record, the `LeagueRecord`. Every write the season engine makes, every set-up write and
every stage of the offseason ends in `save()`, which writes the whole record in the three steps of `files.py`, so at any moment
league.sav or league.previous.sav is whole (invariant I10). The classic season's files are never touched; the log, the first-run
flag and the player's names (footplay.txt, read once to name a new league's first team) are the classic store's.

Healing (design 10.1, playbook 7.10), decided once in `open()`: a damaged league.sav falls back to league.previous.sav with the
damaged file kept as league.sav.damagedN; a franchise that cannot be read is set aside and a classic season begins (the franchise
is never made again silently); a newer format, a file held by another program and an unwritable folder have their own notices.
"""
from __future__ import annotations

import dataclasses
import logging

from ...data import debuglog
from ...data.files import savedgame
from ...data.healing import FileInUse
from ...game.gamestate import SavedGame
from ...game.playoffs import PlayoffState
from ...game.schedule import ScheduleEntry
from ...game.season import SeasonState
from ...game.setup import Roster
from ...game.standings import Records
from .. import nx_texts as X
from . import data as D
from . import history
from .files import TMP
from .league import SEASON, LeagueError, LeagueRecord, NewerFormat, team_index

log = logging.getLogger("nfl4.data")

SAVED_DAMAGED = " The saved game could not be read and was set aside. "      # the classic store's own text (G-F5)


class FranchiseStore:
    def __init__(self, files, classic=None):
        self.files = files
        self.classic = classic                  # the classic ProgramStore: the log, the first-run flag, footplay.txt's names
        self.league: LeagueRecord | None = None
        self.opened = False
        self.available = True                   # False: a file held by another program or saved by a newer version
        self.force_classic = False              # the franchise set as the kind could not be used: nx_season_kind -> classic
        self.problem = ""                       # what open() found: "", "healed", "damaged", "missing", "held", "newer"
        self.season: SeasonState | None = None  # the Game's SeasonState while this store is in use (bind)
        self.pending: tuple[int, int, str] | None = None     # (tn1, tn2, coach) chosen before the league is made
        self.creating = False                   # a new franchise is being made: the set-up writes wait for the league
        self.words: history.Words | None = None
        self.staff_setting = lambda: False      # SX.8k: whether the staff handles the to-do list (mode.activate gives the setting)
        self.game_injuries = None               # SX.8k: the injuries of the player's game in progress (injury_flow.GameInjuries), until its result
        self.strict = False                     # tests: a record that fails its own check raises instead of being refused
        self.unwritable = False
        self.keep_old = False                   # the old franchise could not be archived: the new league is never written over it
        self._notices: list = []
        self._saved_ok = False
        self._write_notice_given = False

    # ----- notices -----

    def take_notices(self) -> list:
        notices, self._notices = self._notices, []
        return notices

    def _notice(self, text_id: str) -> None:
        text = X.text(text_id)
        if text not in self._notices:
            self._notices.append(text)

    # ----- opening: the healing of design 10.1 -----

    def _read(self, name: str):
        """(state, record): "ok", "missing", "damaged", "held" or "newer"."""
        try:
            raw = self.files.read(name)
        except FileInUse:
            return "held", None
        except ValueError:
            return "damaged", None
        if raw is None:
            return "missing", None
        try:
            return "ok", LeagueRecord.from_json(raw.decode("utf-8"))
        except NewerFormat:
            return "newer", None
        except Exception:                       # LeagueError, UnicodeError, anything a damaged file makes the parser raise
            log.warning("%s is damaged", name, exc_info=True)
            return "damaged", None

    def open(self, kind_is_franchise: bool) -> None:
        """Read the franchise folder once (a stale league.sav.tmp is the rest of a write that did not finish: deleted unread).
        Sets `league` (None: there is no usable franchise), `available`, `force_classic` and the start-up notices."""
        if self.opened:
            return
        self.opened = True
        self.files.remove(D.LEAGUE_FILE + TMP)
        sav_state, sav = self._read(D.LEAGUE_FILE)
        prev_state, prev = self._read(D.PREVIOUS_FILE)
        if "held" in (sav_state, prev_state):
            self.available, self.problem = False, "held"
            self._notice("NXF-35")
            return
        if sav_state == "newer":
            self.available, self.problem, self.force_classic = False, "newer", kind_is_franchise
            self._notice("NXF-34")
            return
        if sav_state == "ok":
            self.league = sav
            return
        if prev_state == "ok":
            if sav_state == "damaged":
                self.files.set_aside(D.LEAGUE_FILE)
                self._notice("NXF-30")
                self.problem = "damaged"
            else:
                self._notice("NXF-36")
                self.problem = "missing"
            self.league = prev
            self.save()                          # the copy is league.sav again
            return
        damaged = [name for name, state in ((D.LEAGUE_FILE, sav_state), (D.PREVIOUS_FILE, prev_state)) if state == "damaged"]
        if damaged:
            for name in damaged:
                self.files.set_aside(name)
            self.problem, self.force_classic = "damaged", kind_is_franchise
            self._notice("NXF-31")
            return
        if kind_is_franchise:                    # nothing there although the setting says there is a franchise
            self.problem, self.force_classic = "missing", True
            self._notice("NXF-37")

    @property
    def exists(self) -> bool:
        return self.league is not None

    # ----- the three steps of a write -----

    def bind(self, season: SeasonState) -> None:
        self.season = season

    def unbind(self) -> None:
        self.season = None

    def sync(self) -> None:
        """The season values of the Game's SeasonState go into the record (only while a season is being played)."""
        league, season = self.league, self.season
        if league is None or season is None or league.stage != SEASON:
            return
        league.coach = season.coach
        league.team = team_index(season.tn1, season.tn2)
        league.gtp = season.gtp
        league.schedule = [[e.division, e.team, e.flag] for e in season.schedule]
        league.records = season.records.as_file_values()
        league.pairings = season.playoffs.pairing_values()
        league.byes = season.playoffs.bye_values()

    def engine_consistent(self) -> bool:
        """The season engine changes the week before a round and writes the next round's pairings before it changes the week
        back (and finplay17 writes whole rounds without the player): a state saved there could not be resumed (review finding 1
        of SX.8a). A state is saved only when the week, the records, the pairings and the results the record holds agree."""
        league = self.league
        gtp = league.gtp
        if gtp == 0:
            return True
        regular = sum(1 for row in league.results if row[0] == 0)
        playoff = len(league.results) - regular
        if gtp <= 16:
            return regular == 16 * (gtp - 1) and playoff == 0 and not league.pairings
        games, played = {17: (4, 0), 18: (4, 4), 19: (2, 8), 20: (1, 10)}[gtp]
        return (regular == 256 and playoff == played and len(league.pairings) == 4 * games
                and (gtp > 18 or len(league.byes) == 8))

    def save(self) -> bool:
        """league.sav, whole: the new text to the temporary file, the present file copied to league.previous.sav, the
        temporary file renamed. False when it could not be written (the franchise then plays on from memory)."""
        league = self.league
        if league is None or not self.available or self.keep_old:
            return False
        self.sync()
        if self.season is not None and league.stage == SEASON and not self.engine_consistent():
            return True                          # the engine is between two of its own writes: the file keeps the last whole state
        try:
            league.check()
            data = league.to_json().encode("utf-8")
        except Exception:
            if self.strict:
                raise
            log.exception("the franchise record is not whole: it is not written")
            self._write_failed()
            return False
        if not self.files.write_tmp(D.LEAGUE_FILE, data):
            self._write_failed()
            return False
        if self.files.exists(D.LEAGUE_FILE):
            self.files.copy(D.LEAGUE_FILE, D.PREVIOUS_FILE)
        if not self.files.commit(D.LEAGUE_FILE):
            self._write_failed()
            return False
        debuglog.event("franchise", "saved", season=league.season, stage=league.stage, stage_no=league.stage_no, bytes=len(data))
        return True

    def _write_failed(self) -> None:
        self.unwritable = True
        if not self._write_notice_given:
            self._write_notice_given = True
            self._notice("NXF-32")

    def write_history(self) -> bool:
        """history.txt, rewritten whole from the record (never read back)."""
        if self.league is None or self.words is None or not self.available:
            return False
        return self.files.write_text(D.HISTORY_FILE, history.history_text(self.league, self.words))

    # ----- a new franchise and the old ones -----

    def archive_current(self) -> bool:
        """The present franchise is kept as a copy: league.sav, history.txt and its saved game move to old\\league-1.sav,
        old\\history-1.txt and old\\football-1.sav; an older copy 1 becomes 2, 2 becomes 3 and 3 is deleted. league.sav is moved
        FIRST, to a place of its own, and when it cannot be moved nothing is deleted and False is answered (review finding 2)."""
        if self.league is None:
            return True
        old = D.OLD_FOLDER + "/"
        if self.files.exists(D.LEAGUE_FILE) and not self.files.move(D.LEAGUE_FILE, old + "league-0.sav"):
            return False
        pairs = ((D.LEAGUE_FILE, "league-%d.sav"), (D.HISTORY_FILE, "history-%d.txt"), (D.SAVED_FILE, "football-%d.sav"))
        for source, pattern in pairs:
            self.files.remove(old + pattern % D.OLD_COPIES)
            for number in range(D.OLD_COPIES - 1, 0, -1):
                if self.files.exists(old + pattern % number):
                    self.files.move(old + pattern % number, old + pattern % (number + 1))
            if source == D.LEAGUE_FILE:
                if self.files.exists(old + "league-0.sav"):
                    self.files.move(old + "league-0.sav", old + pattern % 1)
            elif self.files.exists(source):
                self.files.move(source, old + pattern % 1)
        self.files.remove(D.PREVIOUS_FILE)
        self.files.remove(D.LEAGUE_FILE + TMP)
        self.league = None
        self._saved_ok = False
        return True

    def create(self, league: LeagueRecord) -> bool:
        """The new league replaces the franchise (which `archive_current` kept); league.sav and history.txt are written."""
        archived = self.archive_current()
        self.league = league
        self.pending, self.creating = None, False
        if not archived:                         # the old franchise could not be kept: it stays where it is, the new one is in memory
            self.keep_old = True
            self._write_failed()
            return False
        ok = self.save()
        self.write_history()
        return ok

    # ----- ProgramStore -----

    def first_run(self) -> bool:
        return False

    def has_saved_game(self) -> bool:
        """The franchise's own football.sav, which must belong to this league's season and week (design 10.2)."""
        self._saved_ok = False
        league = self.league
        if league is None or league.stage != SEASON or not self.files.exists(D.SAVED_FILE):
            return False
        try:
            raw = self.files.read(D.SAVED_FILE)
        except FileInUse as exc:
            log.warning("the franchise's saved game is held by another program (%s)", exc)
            return False
        except ValueError:
            raw = None
        saved = None
        if raw is not None:
            try:
                saved = savedgame.decode(raw)
            except Exception:
                saved = None
        if saved is None:
            self.files.set_aside(D.SAVED_FILE)
            self._notice_text(SAVED_DAMAGED)
            return False
        if self._saved_value(saved) != {"league": league.league_id, "season": league.season, "week": league.gtp}:
            self.files.set_aside(D.SAVED_FILE)
            self._notice("NXF-33")
            return False
        self._saved_ok = True
        return True

    def _notice_text(self, text: str) -> None:
        if text not in self._notices:
            self._notices.append(text)

    @staticmethod
    def _saved_value(saved: SavedGame):
        from ..state import ExtrasRecord
        if saved.extras is None:
            return None
        try:
            return ExtrasRecord.from_json(saved.extras).franchise
        except ValueError as exc:
            log.warning("the extras of a saved game cannot be read (%s)", exc)
            return None

    def take_saved_game(self) -> SavedGame | None:
        self._saved_ok = False
        try:
            raw = self.files.read(D.SAVED_FILE)
        except (FileInUse, ValueError):
            return None
        if raw is None:
            return None
        try:
            saved = savedgame.decode(raw)
        except Exception:
            self.files.set_aside(D.SAVED_FILE)
            self._notice_text(SAVED_DAMAGED)
            return None
        self.files.remove(D.SAVED_FILE)
        return saved

    def save_game(self, saved: SavedGame) -> bool:
        """Save Game in a franchise: football.sav in the franchise folder with the extras record's franchise value."""
        league = self.league
        if league is None or not self.available:
            return False
        if saved.extras is not None:
            from ..state import ExtrasRecord
            try:
                record = ExtrasRecord.from_json(saved.extras)
                record.franchise = {"league": league.league_id, "season": league.season, "week": league.gtp}
                saved = dataclasses.replace(saved, extras=record.to_json())
            except ValueError:
                log.warning("the extras of the franchise game cannot be marked: it is saved without the mark")
        try:
            data = savedgame.encode(saved)
        except Exception:
            log.exception("could not encode the saved game")
            self._write_failed()
            return False
        if not self.files.write(D.SAVED_FILE, data):
            self._write_failed()
            return False
        return True

    def load_season(self, season: SeasonState) -> bool:
        """The record's season goes into the Game's SeasonState (the franchise is in use and in the season)."""
        league = self.league
        if league is None or league.stage != SEASON:
            return False
        season.coach = league.coach
        debuglog.add_typed(season.coach)
        season.tn1, season.tn2 = (league.team - 1) // 4 + 1, (league.team - 1) % 4 + 1
        season.schedule = [ScheduleEntry(*entry) for entry in league.schedule]
        season.gtp = league.gtp
        loaded = Records.from_file_values(league.records)
        for d in range(len(season.records.wins)):
            season.records.wins[d][:] = loaded.wins[d]
            season.records.losses[d][:] = loaded.losses[d]
        season.playoffs.pairings[:] = PlayoffState.pairings_from_values(league.pairings)
        season.playoffs.byes[:] = PlayoffState.byes_from_values(league.byes)
        return True

    def open_log(self, fresh: bool) -> None:
        if self.classic is not None:
            self.classic.open_log(fresh)

    def log_line(self, text: str) -> None:
        if self.classic is not None:
            self.classic.log_line(text)

    def player_names(self) -> Roster | None:
        league = self.league
        if league is None or league.stage != SEASON:
            return None
        from .injury_flow import lineup_roster
        return lineup_roster(league, league.team, league.gtp, self.staff_setting())      # SX.8k: the week's lineup (the hurt are not in it)

    def write_player_names(self, roster: Roster) -> None:
        return None                              # the franchise's players are the league's (footplay.txt is the classic season's)

    def delete_season_files(self) -> None:
        return None                              # a franchise's season ends in its offseason, written stage by stage

    def close(self) -> None:
        return None

    # ----- SeasonStore -----

    def write_records(self, records) -> None:
        self.save()

    def write_gtp(self, gtp) -> None:
        self.save()

    def write_pairings(self, pairings) -> None:
        self.save()

    def write_byes(self, byes) -> None:
        self.save()

    # ----- SetupStore -----

    def write_coach_and_team(self, tn1: int, tn2: int, coach: str) -> None:
        if self.creating or self.league is None:
            self.pending = (tn1, tn2, coach)
            return
        self.save()

    def write_schedule(self, schedule) -> None:
        self.save()

    def append_quarterback(self, name: str) -> None:
        return None                              # the quarterback of a franchise team is a player of the league
