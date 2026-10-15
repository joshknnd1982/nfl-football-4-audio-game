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
* a file that is held by another program is not damaged: it is left alone and the clone goes on from memory;
* a folder that cannot be written is told once and the game goes on (nothing is kept).
Files are written whole through a temporary file and a rename, so a crash never leaves half a file.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field

from ...game.gamestate import SavedGame
from ...game.playoffs import Pairing, TeamRef
from ...game.schedule import ScheduleEntry
from ...game.season import SeasonState
from ...game.setup import Roster
from ...game.standings import Records
from ..healing import (read_bytes, read_player_text, save_damaged_copy, write_bytes_atomic,
                       write_text_atomic)
from . import (byesfile, coachteam, pairingsfile, playernames, recordsfile, savedgame, schedulefile, speechlog,
               weekfile)
from .variant import FileDamaged

log = logging.getLogger("nfl4.data")

SEASON_FILES = (coachteam.FILE_NAME, schedulefile.FILE_NAME, weekfile.FILE_NAME, recordsfile.FILE_NAME,
                pairingsfile.FILE_NAME, byesfile.FILE_NAME)
SAVED_NAME = savedgame.FILE_NAME
LOG_NAME = speechlog.FILE_NAME

# The texts the clone adds (CLONE texts, GAP_REGISTER section 8; S8.2 listens to them)
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
        self._saved_ok = False
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
            pass
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
        try:
            self._saved_ok = self._check_saved_game()
        except Exception:
            log.exception("checking the saved game failed")
            self._saved_ok = False

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

    def _check_saved_game(self) -> bool:
        path = self.path(SAVED_NAME)
        if not os.path.exists(path):
            return False
        if self._hold_writes:                                   # the season could not be read: judge nothing, delete nothing
            log.warning("%s is left alone: the season files are in use", path)
            return False
        try:
            savedgame.decode(read_bytes(path))
            if self._season is None or not 1 <= self._season.gtp <= weekfile.LAST_WEEK:
                raise FileDamaged("it belongs to no season")     # it disagrees with football.gtp (G-F5)
            return True
        except OSError:
            log.warning("%s could not be read: no saved game this time", path, exc_info=True)
            return False
        except (FileDamaged, ValueError) as exc:
            self._set_aside(path, str(exc))
            self._notice(SAVED_DAMAGED)
            return False

    # ----- ProgramStore -----

    def first_run(self) -> bool:
        return self.first

    def has_saved_game(self) -> bool:
        return self._saved_ok

    def load_season(self, season: SeasonState) -> bool:
        loaded, self._season = self._season, None
        if loaded is None:
            return False
        season.coach = loaded.team.coach
        season.tn1, season.tn2 = loaded.team.tn1, loaded.team.tn2
        season.schedule = list(loaded.schedule)
        season.gtp = loaded.gtp
        for d in range(len(season.records.wins)):
            season.records.wins[d][:] = loaded.records.wins[d]
            season.records.losses[d][:] = loaded.records.losses[d]
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

    def write_player_names(self, roster: Roster) -> bool:
        """The original's write of footplay.txt after pag drew the names (0x455908 to 0x456f0b)."""
        return self._write_text(self.names_path, lambda: playernames.format_roster(roster))

    def take_saved_game(self) -> SavedGame | None:
        """football.sav read, then deleted (pag 0x43afa4: the saved game exists once)."""
        path = self.path(SAVED_NAME)
        self._saved_ok = False
        if not os.path.exists(path):
            return None
        try:
            saved = savedgame.decode(read_bytes(path))
        except OSError:
            log.warning("%s could not be read", path, exc_info=True)
            return None
        except (FileDamaged, ValueError) as exc:
            self._set_aside(path, str(exc))
            self._notice(SAVED_DAMAGED)
            return None
        self._remove(path)
        return saved

    def save_game(self, saved: SavedGame) -> bool:
        return self._write(self.path(SAVED_NAME), lambda: savedgame.encode(saved))

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

    # ----- SeasonStore -----

    def write_records(self, records: Records) -> None:
        self._write(self.path(recordsfile.FILE_NAME), lambda: recordsfile.encode(records))

    def write_gtp(self, gtp: int) -> None:
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
