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
from ...data.files.shelf import AUTO_FILE, ORPHAN, OK, STALE, SaveShelf
from ...data.healing import FileInUse
from ...game.gamestate import SavedGame
from ...game.playoffs import PlayoffState
from ...game.schedule import Calendar, ScheduleEntry
from ...game.season import SeasonState
from ...game.setup import Roster
from ...game.standings import Records
from .. import nx_texts as X
from . import data as D
from . import history
from .files import TMP

BEFORE_FORMAT_18 = ".before-format-18"     # SR.4: the copy of a league of format 17 or older, kept when it is converted (design 21.6 item 1)
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
        self.practice_squads = True             # D-136: the practice squads are formed at the new season (False: the older tests' leagues)
        self.reserves = True                    # D-149 (NX-B2b): every league opened or made carries the 53-man roster, its benches (False: the older tests' leagues)
        self.real_names_of = None               # 2026-10-23: a callable that gives the program's real names (flow.franchise), for fix_real_backs
        self.real_calendar = True               # SZ.8: a season plays the league's real calendar (fixtures.py); False (the tests of the original's 16 weeks): the original's `makes`
        self.unwritable = False
        self.keep_old = False                   # the old franchise could not be archived: the new league is never written over it
        self.season_current = False             # SZ.8: the Game's SeasonState holds this league's season (loaded, or made by the engine or the set-up); until then `sync` copies nothing
        self._notices: list = []
        self.shelf = SaveShelf(files)           # SX.14: the franchise's saved games (three slots, the automatic save, the backup)
        self._write_notice_given = False
        self.slot = 1                           # D-173: which of the three franchise slots this store's folder is (flow.franchise_peek sets it)

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
            self._benches()
            self._fix_backs()
            self._convert(D.LEAGUE_FILE)
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
            self._benches()
            self._fix_backs()
            self._convert(D.PREVIOUS_FILE)
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

    def _benches(self) -> None:
        """D-149, SR.5: every league carries the 53-man roster (its chart); logged with the size of the rosters (rule 0.15)."""
        if self.league is not None:
            self.league.reserves_on = True
            from . import real_roster
            debuglog.event("franchise", "rosters", players=sum(real_roster.roster_count(self.league, t) for t in range(1, D.TEAMS + 1)))

    def _convert(self, name: str) -> None:
        """SR.4 (NX-L7, design 21.6): a league of format 17 or older, once: the file is kept as league.sav.before-format-18, then every man gets his
        real position and number by his name, a league without benches its teams' missing real men, the depth charts (real_roster.convert). Saved
        at the next save; `league.converted` tells SR.6's sentence what was done. A failure never costs the player his franchise (it is logged)."""
        league = self.league
        if league is None or not league.loaded_format or league.loaded_format >= 18:      # SR.5: a league of format 18 has its positions already
            return
        try:
            self.files.copy(name, D.LEAGUE_FILE + BEFORE_FORMAT_18)
            real = self.real_names_of() if self.real_names_of is not None else None
            from . import real_roster
            real_roster.convert(league, real)
        except Exception:
            log.exception("the franchise could not be brought to the real rosters' positions")

    @staticmethod
    def _mend_charts(league) -> None:
        """SR.5 (D-164): every team's chart and places made again from its roster before a write (real_roster.refresh_all), so a path that changed a
        man's team or status without real_roster.join or leave can never write a broken file; when a chart's men had to change it is logged (rule 0.15:
        the log names the path to mend)."""
        from . import real_roster
        before = [sorted(pid for key, ids in chart.items() if key not in ("KR", "PR") for pid in ids) if isinstance(chart, dict) else None
                  for chart in (league.chart if isinstance(league.chart, list) else [])]
        real_roster.refresh_all(league)
        after = [sorted(pid for key, ids in chart.items() if key not in ("KR", "PR") for pid in ids) for chart in league.chart]
        changed = [team for team, (a, b) in enumerate(zip(before, after), start=1) if a != b]
        if changed:
            debuglog.event("franchise", "chart_mended", logging.WARNING, teams=changed, stage=league.stage, stage_no=league.stage_no)

    def _fix_backs(self) -> None:
        """SR.5 (NX-L5, NX-L7): nothing to rename any more. A real man of an older league whom the old fill put at another position gets his real position
        back by his name (real_roster.convert), never a made-up name; the renames of 2026-10-23 and NX-D1 (fix_real_backs, fix_real_positions) are gone."""
        return None

    @property
    def exists(self) -> bool:
        return self.league is not None

    # ----- the three steps of a write -----

    def bind(self, season: SeasonState) -> None:
        self.season = season
        self.season_current = False

    def unbind(self) -> None:
        self.season = None
        self.season_current = False

    def sync(self) -> None:
        """The season values of the Game's SeasonState go into the record (only while a season is being played, and only once the state holds this league's season:
        at the start-up menu the store is bound but the state still has its defaults, and a save there (an F9 trade, a signing) would have written week 1 of team 1
        over the league, SZ.8 review)."""
        league, season = self.league, self.season
        if league is None or season is None or league.stage != SEASON or not self.season_current:
            return
        league.coach = season.coach
        league.team = team_index(season.tn1, season.tn2)
        league.gtp = season.gtp
        league.schedule = [[e.division, e.team, e.flag] for e in season.schedule]
        league.calendar = None if season.calendar is None else {"label": season.calendar.label, "weeks": season.calendar.to_rows()}      # SZ.8
        league.records = season.records.as_file_values()
        league.ties = season.records.tie_values()          # SX.12: the ties of the 2026 overtime
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
        weeks = league.regular_weeks
        if gtp <= weeks:
            return regular == league.games_before(gtp) and playoff == 0 and not league.pairings
        real = league.real_bracket()                             # D-129: the N. F. L.'s six wild card games and two byes
        rounds = {1: (6, 0), 2: (4, 6), 3: (2, 10), 4: (1, 12)} if real else {1: (4, 0), 2: (4, 4), 3: (2, 8), 4: (1, 10)}
        if gtp - weeks not in rounds:
            return False
        games, played = rounds[gtp - weeks]
        return (regular == league.games_before(weeks + 1) and playoff == played and len(league.pairings) == 4 * games
                and (gtp - weeks > 2 or len(league.byes) == (4 if real else 8)))

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
            self._mend_charts(league)
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
        for source, pattern in self._companions():
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
        return True

    def create(self, league: LeagueRecord) -> bool:
        """The new league replaces the franchise (which `archive_current` kept); league.sav and history.txt are written."""
        archived = self.archive_current()
        self.league = league
        if self.reserves:
            league.reserves_on = True              # D-149
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

    def current_mark(self) -> dict | None:
        """The league, season and week a franchise game is saved in (design 10.2); None while the franchise is not in a season."""
        league = self.league
        if league is None or league.stage != SEASON:
            return None
        return {"league": league.league_id, "season": league.season, "week": league.gtp}

    def classify(self, entry) -> tuple[str, str]:
        """Which saves of the franchise folder can be continued (SX.14, NX-S8): the ones marked with this league's season and week.
        Nothing is set aside here any more; the start-up menu names a save that cannot be played and only the player moves it."""
        mark = self.current_mark()
        if mark is None:
            return ORPHAN, "the franchise is not in a season"
        if self._saved_value(entry.saved) != mark:
            return STALE, "it belongs to another week of the franchise"
        return OK, ""

    def has_saved_game(self) -> bool:
        """A saved game of this league's season and week is there (design 10.2)."""
        return any(entry.playable for entry in self.shelf.scan(self.classify))

    def _notice_text(self, text: str) -> None:
        if text not in self._notices:
            self._notices.append(text)

    @staticmethod
    def _saved_value(saved: SavedGame):
        from ..state import ExtrasRecord
        if saved is None or saved.extras is None:
            return None
        try:
            return ExtrasRecord.from_json(saved.extras).franchise
        except ValueError as exc:
            log.warning("the extras of a saved game cannot be read (%s)", exc)
            return None

    def _marked(self, saved: SavedGame) -> SavedGame:
        """The saved game with the extras record's franchise value (the league, season and week it belongs to)."""
        mark = self.current_mark()
        if saved.extras is not None and mark is not None:
            from ..state import ExtrasRecord
            try:
                record = ExtrasRecord.from_json(saved.extras)
                record.franchise = mark
                return dataclasses.replace(saved, extras=record.to_json())
            except ValueError:
                log.warning("the extras of the franchise game cannot be marked: it is saved without the mark")
        return saved

    def save_game(self, saved: SavedGame, slot: int | None = None) -> bool:
        """Save Game in a franchise: a slot of the franchise folder (slot 1 is football.sav) with the extras record's franchise value."""
        if self.league is None or not self.available:
            return False
        if not self.shelf.write_slot(slot or 1, self._marked(saved)):
            self._write_failed()
            return False
        return True

    def autosave(self, saved: SavedGame) -> bool:
        """The automatic save of a franchise game (NX-S4), marked like a saved game."""
        if self.league is None or not self.available:
            return False
        if not self.shelf.write_auto(self._marked(saved)):
            self._write_failed()
            return False
        return True

    # ----- the player's own choices at the start (NX-S1, NX-S2): delete and restore -----

    def delete_franchise(self) -> bool:
        """The franchise moves to the backup (old\\league-1.sav and its companions, the three newest kept) and there is none until a new one
        is made or this one is restored. False when it could not be moved: nothing is lost."""
        if self.league is None:
            return True
        if not self.archive_current():
            return False
        debuglog.event("save", "franchise_delete")
        return True

    def deleted_exists(self) -> bool:
        return self.league is None and self.files.exists(D.OLD_FOLDER + "/" + "league-1.sav")

    def restore_deleted(self) -> bool:
        """The franchise deleted last comes back (old\\league-1.sav and its companions), the older copies move up one. False when a
        franchise is there now, none was deleted, or it could not be moved."""
        if not self.deleted_exists():
            return False
        return self.restore_backup(1)

    # ----- D-173 (the owner 2026-10-26: "the backups fail to restore"): every kept copy, into any empty slot -----

    def backup_numbers(self) -> list:
        """The numbers of the kept copies in old\\ (1 the newest), whether or not a franchise is in this slot now."""
        return [n for n in range(1, D.OLD_COPIES + 1) if self.files.exists(D.OLD_FOLDER + "/" + "league-%d.sav" % n)]

    def peek_backup(self, number: int):
        """The kept copy's league (a LeagueRecord) for its summary, or None when it cannot be read."""
        state, record = self._read(D.OLD_FOLDER + "/" + "league-%d.sav" % number)
        return record if state == "ok" else None

    def restore_backup(self, number: int, target: "FranchiseStore | None" = None) -> bool:
        """Kept copy `number` of this slot becomes the franchise of `target` (this store, or another slot's), which must be empty; the
        copies after it move up one. Every file of the copy moves (league.sav, history.txt, its saved games). False when the target holds a
        franchise, the copy is not there, or a file could not be moved (what moved stays where it went, and the log says which)."""
        target = target if target is not None else self
        old = D.OLD_FOLDER + "/"
        if not target.opened:
            target.open(False)
        if target.league is not None or not self.files.exists(old + "league-%d.sav" % number):
            debuglog.event("save", "franchise_restore_refused", slot=getattr(self, "slot", 1), copy=number,
                           target=getattr(target, "slot", 1), target_full=target.league is not None)
            return False
        for name, pattern in self._companions():
            source = old + pattern % number
            if not self.files.exists(source):
                continue
            if target is self:
                moved = self.files.move(source, name)
            else:
                data = self.files.read(source)
                moved = data is not None and target.files.write(name, data)
                if moved:
                    self.files.remove(source)
            if not moved:
                debuglog.event("save", "franchise_restore_failed", file=name, copy=number)
                return False
        for _name, pattern in self._companions():
            for later in range(number + 1, D.OLD_COPIES + 1):
                if self.files.exists(old + pattern % later):
                    self.files.move(old + pattern % later, old + pattern % (later - 1))
        target.files.remove(D.PREVIOUS_FILE)            # the copy is whole; an older slot's previous file must never heal over it
        target.opened, target.problem, target.league = False, "", None
        target.open(True)
        debuglog.event("save", "franchise_restore", slot=getattr(self, "slot", 1), copy=number, target=getattr(target, "slot", 1),
                       ok=target.league is not None)
        return target.league is not None

    @staticmethod
    def _companions() -> tuple:
        """(the file in the franchise folder, its name pattern in old\\) for everything a franchise is."""
        return ((D.LEAGUE_FILE, "league-%d.sav"), (D.HISTORY_FILE, "history-%d.txt"), (D.SAVED_FILE, "football-%d.sav"),
                ("football2.sav", "football2-%d.sav"), ("football3.sav", "football3-%d.sav"), (AUTO_FILE, "autosave-%d.sav"))

    def load_season(self, season: SeasonState) -> bool:
        """The record's season goes into the Game's SeasonState (the franchise is in use and in the season)."""
        league = self.league
        if league is None or league.stage != SEASON:
            return False
        season.coach = league.coach
        debuglog.add_typed(season.coach)
        season.tn1, season.tn2 = (league.team - 1) // 4 + 1, (league.team - 1) % 4 + 1
        season.schedule = [ScheduleEntry(*entry) for entry in league.schedule]
        season.calendar = Calendar.from_rows(league.calendar["label"], league.calendar["weeks"]) if league.calendar else None      # SZ.8
        self.season_current = True
        season.gtp = league.gtp
        loaded = Records.from_file_values(league.records)
        loaded.set_tie_values(league.ties)                 # SX.12
        loaded.copy_into(season.records)
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
        self.season_current = True              # (the engine wrote: its state is the season)
        self.save()

    def write_gtp(self, gtp) -> None:
        self.season_current = True
        self.save()

    def write_pairings(self, pairings) -> None:
        self.season_current = True
        self.save()

    def write_byes(self, byes) -> None:
        self.season_current = True
        self.save()

    # ----- SetupStore -----

    def write_coach_and_team(self, tn1: int, tn2: int, coach: str) -> None:
        if self.creating or self.league is None:
            self.pending = (tn1, tn2, coach)
            return
        self.season_current = True
        self.save()

    def make_season_schedule(self, season: SeasonState, rnd):
        """SZ.8 (Game.make_schedule asks the setup store first): this season's real calendar and the player's team's schedule in it, or None when the Franchise
        plays the original's random 16 weeks (the setting for the tests, no calendar file that passes its check, no league yet). The calendar goes into the
        Game's SeasonState (the record takes it at the next sync) and no random number is drawn."""
        from . import fixtures
        league = self.league
        if league is None or not self.real_calendar:
            return None
        calendar = fixtures.for_season(league.season)
        if calendar is None:
            # S8.3 round 2: the README promises the real calendar, so a missing or damaged file is told once (said at the next week line), not only logged
            debuglog.event("franchise", "calendar_missing", logging.INFO, season=league.season, year=fixtures.year_of(league.season),
                           path=fixtures.shipped_path(fixtures.year_of(league.season)))
            self._notice("NXF-46")
            return None
        season.calendar = calendar
        season.schedule = calendar.entries_of(team_index(season.tn1, season.tn2))
        debuglog.event("franchise", "calendar", season=league.season, label=calendar.label, weeks=calendar.length,
                       byes=[week for week, entry in enumerate(season.schedule, start=1) if entry.is_bye])
        return season.schedule

    def write_schedule(self, schedule) -> None:
        self.season_current = True              # (the set-up of a season made it: the state is the season)
        self.save()

    def append_quarterback(self, name: str) -> None:
        return None                              # the quarterback of a franchise team is a player of the league
