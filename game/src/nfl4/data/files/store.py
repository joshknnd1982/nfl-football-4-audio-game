"""The real files: `FileProgramStore` is the ProgramStore, the SeasonStore and the SetupStore over the player's folders.
This is inspired by Jim Kitchen.

GAME_SPEC 3 step 7 to 9 and 12, D-024 (items 3 to 5), D-027 item 3, D-029 item 5, D-046 item 2, GAP_REGISTER G-S10, G-F3 to
G-F5 and G-F8, playbook 7.10. Where the files live: the season files (footbal1.dat to footbal5.dat, football.gtp), the
saved game football.sav and the speech log footballlog.txt in the data folder (`paths.user_data_dir()`); footplay.txt
and, after a season, footplay.previous.txt in its `customize` folder (the player edits it, CUSTOMIZABLE_CONTENT 6 and 10).
The program never reads or writes the original's Documents\\kitchensinc.

What each caller uses:
* `game/program.py` (ProgramStore): `first_run`, `has_saved_game`, `load_season`, `open_log`, `player_names`,
  `take_saved_game`, `save_game`, `delete_season_files`;
* `game/season_engine.py` (SeasonStore): `write_records`, `write_gtp`, `write_pairings`, `write_byes`, called at the moments
  and in the order the original writes them (tests/seasonrig.py's RecordingStore proves the order);
* `game/prompts.py` (SetupStore): `write_coach_and_team`, `write_schedule`, `append_quarterback`;
* `game/pag.py`: `write_player_names` (the 33 names pag drew, the original's write at 0x455908 to 0x456f0b);
* the Game: `log_line` (its `log_sink`, Print #3) and `take_notices` (spoken once, like every notice source).

Healing (D-024 item 5, G-F5, playbook 7.10), all decided at the START, when the store is made, so that the notices come
with the start-up notices and `has_saved_game` and `load_season` are plain answers:
* a missing footbal1.dat is a new season (the first start) and nothing is said; season files left behind without it are
  removed quietly; a week of 0 in football.gtp (a season that ended and was not cleaned up) is cleaned up quietly;
* a season file that cannot be used (a missing one that the week needs, one that is cut short, a value outside its range,
  a pairing round without the player's team) is copied to <name>.damagedN (three kept), every season file is removed, one
  notice says so and a new season begins; the player's footplay.txt stays;
* a football.sav that cannot be used, or that belongs to no season, is copied the same way, removed, one notice;
* footplay.txt: see `player_names`; an unreadable file is never a reason to stop;
* a file that is held by another program is not damaged: it is left alone and the game goes on from memory;
* a folder that cannot be written is told once and the game goes on (nothing is kept).
Files are written whole through a temporary file and a rename, so a crash never leaves half a file.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field

from ...data import debuglog
from ...game.gamestate import SavedGame
from ...game.playoffs import Pairing, TeamRef
from ...game.schedule import ScheduleEntry
from ...game.season import SeasonState
from ...game.setup import Roster
from ...game.standings import Records
from ..healing import (read_bytes, read_player_text, save_damaged_copy, write_bytes_atomic,
                       write_text_atomic)
from . import (byesfile, coachteam, pairingsfile, playernames, recordsfile, savedgame, schedulefile, speechlog,
               tiesfile, weekfile)
from . import shelf as shelf_module
from .shelf import ORPHAN, OK, STALE, SaveShelf
from .variant import FileDamaged

log = logging.getLogger("nfl4.data")

SEASON_FILES = (coachteam.FILE_NAME, schedulefile.FILE_NAME, weekfile.FILE_NAME, recordsfile.FILE_NAME,
                pairingsfile.FILE_NAME, byesfile.FILE_NAME, tiesfile.FILE_NAME)      # footbal6.dat: the ties (SX.12; only with a tie)
SEASON_BACKUP = os.path.join(shelf_module.BACKUP_FOLDER, "season")      # SX.14: the season the player deleted last
SAVED_NAME = savedgame.FILE_NAME
LOG_NAME = speechlog.FILE_NAME

# The texts the game adds (CLONE texts, GAP_REGISTER section 8; S8.2 listens to them)
SEASON_DAMAGED = " The season files could not be read and were set aside. A new season begins. "
SAVED_DAMAGED = " The saved game could not be read and was set aside. "                                # G-F5
NAMES_REPAIRED = " The file footplay.txt had a problem. The part that was wrong got new random names, and a copy of the file was saved. "
NAMES_REPLACED = " The file footplay.txt could not be read. It was replaced with new random names, and a copy was saved. "
UNWRITABLE = " The game could not write its files, so the season and the saved game will not be kept. "
LOCKED = " The season files are in use by another program. A new season starts this time, and it will not be kept. "


@dataclass
class LoadedSeason:
    """What the season files held at the start, checked as a whole."""
    team: coachteam.CoachTeam
    schedule: list[ScheduleEntry]
    gtp: int
    records: Records
    pairings: list[Pairing] = field(default_factory=list)
    byes: list[TeamRef] = field(default_factory=list)


class FileProgramStore:
    def __init__(self, data_dir: str, customize_dir: str | None = None, first: bool = False):
        self.data_dir = data_dir
        self.customize_dir = customize_dir if customize_dir is not None else os.path.join(data_dir, "customize")
        self.first = first
        self.speech_log = speechlog.SpeechLog(os.path.join(data_dir, LOG_NAME))
        self._notices: list[str] = []
        self._season: LoadedSeason | None = None
        self._week: int | None = None          # SX.14: the week of the season in the files (None: no season); the saved games are judged by it
        from ...extras.franchise.files import DiskFiles
        self.shelf = SaveShelf(DiskFiles(data_dir))      # SX.14: the slots, the automatic save and the backup of deleted ones
        self._own_division: int | None = None
        self._write_notice_given = False
        self._hold_writes = False              # the season files are locked by another program: write nothing this run
        self._hold_names = False               # footplay.txt could not be opened: do not write over it this run
        self._reading: str | None = None       # the season file being read
        self._start()

    # ----- paths and small helpers -----

    def path(self, name: str) -> str:
        return os.path.join(self.data_dir, name)

    @property
    def names_path(self) -> str:
        return os.path.join(self.customize_dir, playernames.FILE_NAME)

    @property
    def previous_names_path(self) -> str:
        return os.path.join(self.customize_dir, playernames.PREVIOUS_NAME)

    def take_notices(self) -> list[str]:
        notices, self._notices = self._notices, []
        return notices

    def _notice(self, text: str) -> None:
        if text not in self._notices:
            self._notices.append(text)

    def _remove(self, path: str) -> None:
        try:
            os.remove(path)
        except FileNotFoundError:
            log.debug("%s was not there to delete", path)
        except OSError:
            log.exception("could not delete %s", path)

    def _write(self, path: str, build) -> bool:
        """Write the bytes `build()` makes; never raises (a value that cannot be encoded is a failed write too)."""
        if self._hold_writes:
            return False
        try:
            data = build()
        except Exception:
            log.exception("could not encode %s", path)
            self._write_failed(path)
            return False
        if write_bytes_atomic(path, data):
            return True
        self._write_failed(path)
        return False

    def _write_text(self, path: str, build) -> bool:
        if self._hold_names or self._hold_writes:
            return False
        try:
            ok = write_text_atomic(path, build())
        except Exception:                       # a name the file cannot hold (a lone surrogate)
            log.exception("could not write %s", path)
            ok = False
        if not ok:
            self._write_failed(path)
        return ok

    def _write_failed(self, path: str) -> None:
        log.warning("could not write %s: the game goes on without keeping it", path)
        if not self._write_notice_given:
            self._write_notice_given = True
            self._notice(UNWRITABLE)

    def _set_aside(self, path: str, why: str) -> None:
        """A copy of a damaged file (<name>.damagedN, three kept), then the file is removed."""
        log.warning("%s is damaged (%s); a copy is kept", path, why)
        if os.path.exists(path):
            save_damaged_copy(path)
            self._remove(path)

    # ----- the start: the season and the saved game, checked once -----

    def _start(self) -> None:
        try:
            self._season = self._read_season()
        except Exception:                      # whatever goes wrong, the game starts a new season (7.10)
            log.exception("reading the season files failed")
            self._season = None
        self._week = self._season.gtp if self._season is not None else None
        # SX.14 (NX-S8): a saved game that cannot be used is no longer set aside here. It stays where it is, the start-up menu
        # names it, and only the player's choice moves it (to the backup); `classify` says which saves can be continued

    def _read_required(self, name: str) -> bytes:
        self._reading = self.path(name)
        try:
            return read_bytes(self._reading)
        except FileNotFoundError:
            raise FileDamaged("%s is missing" % name) from None
        except ValueError as exc:
            raise FileDamaged("%s: %s" % (name, exc)) from exc

    def _read_season(self) -> LoadedSeason | None:
        first_path = self.path(coachteam.FILE_NAME)
        self._reading = first_path
        if not os.path.exists(first_path):
            self._set_aside_season_files()          # files left behind without a season: kept as copies, then removed
            return None
        try:
            team = coachteam.decode(self._read_required(coachteam.FILE_NAME))
            schedule = schedulefile.decode(self._read_required(schedulefile.FILE_NAME))
            gtp = weekfile.decode(self._read_required(weekfile.FILE_NAME))
            if gtp == 0:                                        # the season ended and the program stopped before the cleanup
                self.delete_season_files()
                return None
            records = Records()
            records_path = self.path(recordsfile.FILE_NAME)
            if os.path.exists(records_path):
                records = recordsfile.decode(self._read_required(recordsfile.FILE_NAME))
            elif gtp >= 2:
                raise FileDamaged("%s is missing in week %d" % (recordsfile.FILE_NAME, gtp))
            if os.path.exists(self.path(tiesfile.FILE_NAME)):      # SX.12: the ties of the N. F. L. rules (no file: none)
                records.set_tie_values(tiesfile.decode(self._read_required(tiesfile.FILE_NAME)))
            loaded = LoadedSeason(team, schedule, gtp, records)
            if gtp >= 17:
                self._read_playoffs(loaded)
            self._own_division = team.tn1
            return loaded
        except OSError:                                         # held by another program, or any read error: not damage
            log.warning("a season file could not be read: a new season starts this time and nothing is kept", exc_info=True)
            self._hold_writes = True
            self._notice(LOCKED)
            return None
        except FileDamaged as exc:
            self._season_damaged(str(exc))
            return None

    def _read_playoffs(self, loaded: LoadedSeason) -> None:
        loaded.pairings = pairingsfile.decode(self._read_required(pairingsfile.FILE_NAME))
        if len(loaded.pairings) != pairingsfile.GAMES_AFTER_WEEK[loaded.gtp]:
            raise FileDamaged("%s holds %d games in week %d" % (pairingsfile.FILE_NAME, len(loaded.pairings), loaded.gtp))
        own = TeamRef(loaded.team.tn1, loaded.team.tn2)
        if not any(own in pairing for pairing in loaded.pairings):
            raise FileDamaged("the player's team is in none of the play-off games")
        if loaded.gtp <= 18 or os.path.exists(self.path(byesfile.FILE_NAME)):   # the wild card and division rounds need the byes;
            loaded.byes = byesfile.decode(self._read_required(byesfile.FILE_NAME))   # the file stays until the season ends

    def _season_damaged(self, why: str) -> None:
        log.warning("the season is unusable: %s", why)
        self._set_aside_season_files()
        self._notice(SEASON_DAMAGED)

    def _set_aside_season_files(self) -> None:
        """A copy of every season file that is there (the mid-season state may be worth looking at), then they go."""
        for name in SEASON_FILES:
            path = self.path(name)
            if os.path.exists(path):
                save_damaged_copy(path)
        self._remove_season_files()

    def _remove_season_files(self) -> None:
        for name in SEASON_FILES:
            self._remove(self.path(name))

    def classify(self, entry) -> tuple[str, str]:
        """Which saves of the data folder can be continued (SX.14): one of this season's week (a file of the original has no week
        and counts as this week's, as before), while a season is there."""
        if self._hold_writes:                                   # the season could not be read: the save stays, and cannot be played this time
            return ORPHAN, "the season files are in use by another program"
        if self._week is None or not 1 <= self._week <= weekfile.LAST_WEEK:
            return ORPHAN, "it belongs to no season"            # it disagrees with football.gtp (G-F5)
        week = entry.info.get("week")
        if isinstance(week, int) and week != self._week:
            return STALE, "it is from week %d and the season is in week %d" % (week, self._week)
        return OK, ""

    # ----- ProgramStore -----

    def first_run(self) -> bool:
        return self.first

    def has_saved_game(self) -> bool:
        return any(entry.playable for entry in self.shelf.scan(self.classify))

    def season_peek(self):
        """The season the files hold, before it is loaded, for the start-up menu's sentence (None: no season, or already loaded)."""
        from ...game.program_store import SeasonPeek
        loaded = self._season
        if loaded is None:
            return None
        wins, losses = loaded.records.record(loaded.team.tn1, loaded.team.tn2)
        return SeasonPeek(loaded.team.coach, loaded.team.tn1, loaded.team.tn2, loaded.gtp, wins, losses)

    def season_deleted(self) -> bool:
        return os.path.exists(self._backup_path(coachteam.FILE_NAME))

    def _backup_path(self, name: str) -> str:
        return os.path.join(self.data_dir, SEASON_BACKUP, name)

    def _season_names(self) -> list[tuple[str, str]]:
        """(the file, its place in the backup) of everything a season is: the six season files and the player's footplay.txt."""
        names = [(self.path(name), self._backup_path(name)) for name in SEASON_FILES]
        names.append((self.names_path, self._backup_path(playernames.FILE_NAME)))
        # the saved games of the season go with it (they hold no opponent: they need their season), and come back with it
        names += [(self.path(name), self._backup_path(name)) for name in (*shelf_module.SLOT_FILE.values(), shelf_module.AUTO_FILE)]
        return names

    def delete_season(self) -> bool:
        """The season moves to the backup folder (the one before it there is replaced) and the next start is a new season. False
        when a file could not be moved: everything moved so far is put back, so the season is never half deleted."""
        if self._hold_writes or self._hold_names:
            return False
        done: list[tuple[str, str]] = []
        try:
            for _source, target in self._season_names():
                self._remove(target)
            os.makedirs(os.path.join(self.data_dir, SEASON_BACKUP), exist_ok=True)
            for source, target in self._season_names():
                if os.path.exists(source):
                    os.replace(source, target)
                    done.append((source, target))
        except OSError:
            log.exception("the season could not be moved to the backup: it is put back")
            for source, target in reversed(done):
                try:
                    os.replace(target, source)
                except OSError:
                    log.exception("could not put %s back", source)
            return False
        debuglog.event("save", "season_delete", files=len(done))
        self._season, self._week = None, None
        return True

    def restore_season(self) -> bool:
        """The deleted season comes back, when there is no season now. False when there is one, none was deleted, or it could not be moved."""
        if not self.season_deleted() or os.path.exists(self.path(coachteam.FILE_NAME)):
            return False
        done: list[tuple[str, str]] = []
        try:
            os.makedirs(self.customize_dir, exist_ok=True)
            for source, target in self._season_names():
                if os.path.exists(target) and not os.path.exists(source):
                    os.replace(target, source)
                    done.append((source, target))
        except OSError:
            log.exception("the season could not be restored: it is put back in the backup")
            for source, target in reversed(done):
                try:
                    os.replace(source, target)
                except OSError:
                    log.exception("could not put %s back", target)
            return False
        debuglog.event("save", "season_restore", files=len(done))
        try:
            self._season = self._read_season()
        except Exception:
            log.exception("reading the restored season failed")
            self._season = None
        self._week = self._season.gtp if self._season is not None else None
        return self._season is not None

    def load_season(self, season: SeasonState) -> bool:
        loaded, self._season = self._season, None
        if loaded is None:
            return False
        season.coach = loaded.team.coach
        debuglog.add_typed(season.coach)          # the coach's name was typed once; the debug log hides it in every launch
        season.tn1, season.tn2 = loaded.team.tn1, loaded.team.tn2
        season.schedule = list(loaded.schedule)
        season.gtp = loaded.gtp
        loaded.records.copy_into(season.records)            # wins, losses and (SX.12) ties
        season.playoffs.pairings[:] = loaded.pairings
        season.playoffs.byes[:] = loaded.byes
        return True

    def open_log(self, fresh: bool) -> None:
        self.speech_log.open(fresh)

    def log_line(self, text: str) -> None:
        self.speech_log.line(text)

    def close(self) -> None:
        self.speech_log.close()

    def player_names(self) -> Roster | None:
        """footplay.txt read for pag (gpn): None when it is missing or unusable (pag draws all 33 names and writes the
        file); a Roster with only the good sections filled when part of it is wrong (pag draws the rest, keeps the good
        names and the quarterback, and writes the repaired file); a complete Roster otherwise. A copy of a file with a
        problem is kept and one notice is given (D-025 d, 7.10)."""
        path = self.names_path
        if not os.path.exists(path):
            return None
        try:
            text = read_player_text(path)
        except OSError:                                         # held by another program: never write over it this run
            log.warning("%s could not be read: new names this game, and the file is left alone", path, exc_info=True)
            self._hold_names = True
            return None
        except ValueError as exc:
            self._set_aside(path, str(exc))
            self._notice(NAMES_REPLACED)
            return None
        parsed = playernames.parse(text)
        if parsed.sound:
            return parsed.roster
        for problem in parsed.problems:
            log.warning("%s: %s", path, problem)
        save_damaged_copy(path)
        if not parsed.usable:
            self._notice(NAMES_REPLACED)
            return parsed.roster if parsed.roster.quarterback else None     # a quarterback who was typed is not asked twice
        self._notice(NAMES_REPAIRED)
        return parsed.roster

    def current_player_names(self) -> Roster | None:
        """footplay.txt as a roster when it is whole, else None; it only reads (no notice, no copy, nothing written): the
        Franchise (nfl4 only, SX.8a) names a new league's first team with it and never writes the file (design 3.6)."""
        path = self.names_path
        if not os.path.exists(path):
            return None
        try:
            parsed = playernames.parse(read_player_text(path))
        except (OSError, ValueError):
            return None
        return parsed.roster if parsed.sound else None

    def previous_player_names(self) -> Roster | None:
        """footplay.previous.txt (kept when a classic season ends) as a roster when it is whole, else None. It reads only: no
        notice, no copy, nothing written. The Franchise (nfl4 only, SX.8a) uses it to name a new league's first team."""
        path = self.previous_names_path
        if not os.path.exists(path):
            return None
        try:
            parsed = playernames.parse(read_player_text(path))
        except (OSError, ValueError):
            return None
        return parsed.roster if parsed.sound else None

    def write_player_names(self, roster: Roster) -> bool:
        """The original's write of footplay.txt after pag drew the names (0x455908 to 0x456f0b)."""
        return self._write_text(self.names_path, lambda: playernames.format_roster(roster))

    def save_game(self, saved: SavedGame, slot: int | None = None) -> bool:
        """Save Game (SX.14: one of the three slots; slot 1 is the original's football.sav). The original's pag deleted the file as it
        loaded it (Kill, 0x43afa4); the game keeps it until its game ends (NX-S3), so nothing here reads and removes."""
        if self._hold_writes:
            return False
        if self.shelf.write_slot(slot or 1, saved):
            return True
        self._write_failed(self.path(SAVED_NAME))
        return False

    def autosave(self, saved: SavedGame) -> bool:
        """The automatic save (NX-S4): whole, quiet; a failure is told once and the game goes on."""
        if self._hold_writes:
            return False
        if self.shelf.write_auto(saved):
            return True
        self._write_failed(self.path(shelf_module.AUTO_FILE))
        return False

    def delete_season_files(self) -> None:
        """The season's end (GAME_SPEC 3 step 9): footbal1.dat to footbal5.dat, football.gtp and footplay.txt go; the
        names are first kept as footplay.previous.txt, replaced at each season end (G-F4, Q55). Never fails."""
        if self._hold_writes:                                   # the real season is locked: this run's is not its end
            log.warning("the season files are in use: nothing is deleted")
            self._season = None
            return
        names = self.names_path
        keep_names = True
        if os.path.exists(names) and not self._hold_names:
            try:
                os.makedirs(self.customize_dir, exist_ok=True)
                shutil.copyfile(names, self.previous_names_path)
            except OSError:
                log.exception("could not keep %s as %s: the names stay where they are", names, self.previous_names_path)
                keep_names = False
        self._remove_season_files()
        if keep_names and not self._hold_names:
            self._remove(names)
        self._season = None
        self._week = None

    # ----- SeasonStore -----

    def write_records(self, records: Records) -> None:
        self._write(self.path(recordsfile.FILE_NAME), lambda: recordsfile.encode(records))
        if records.any_ties():                              # SX.12: footbal6.dat only while a team has a tie (Classic never)
            self._write(self.path(tiesfile.FILE_NAME), lambda: tiesfile.encode(records))
        elif os.path.exists(self.path(tiesfile.FILE_NAME)):
            self._remove(self.path(tiesfile.FILE_NAME))

    def write_gtp(self, gtp: int) -> None:
        self._week = gtp if gtp else None                      # SX.14: the week the saved games are judged by
        self._write(self.path(weekfile.FILE_NAME), lambda: weekfile.encode(gtp))

    def write_pairings(self, pairings: list[Pairing]) -> None:
        self._write(self.path(pairingsfile.FILE_NAME), lambda: pairingsfile.encode(pairings))

    def write_byes(self, byes: list[TeamRef]) -> None:
        self._write(self.path(byesfile.FILE_NAME), lambda: byesfile.encode(byes))

    # ----- SetupStore -----

    def write_coach_and_team(self, tn1: int, tn2: int, coach: str) -> None:
        self._own_division = tn1
        self._write(self.path(coachteam.FILE_NAME), lambda: coachteam.encode(tn1, tn2, coach))

    def write_schedule(self, schedule: list[ScheduleEntry]) -> None:
        self._write(self.path(schedulefile.FILE_NAME), lambda: schedulefile.encode(schedule, self._own_division))

    def append_quarterback(self, name: str) -> None:
        """Getqbs's append (0x431978 to 0x4319ba): the heading and the name at the end of footplay.txt."""
        try:
            text = read_player_text(self.names_path)
        except (OSError, ValueError):
            text = ""
        self._write_text(self.names_path, lambda: playernames.with_quarterback(text, name))
