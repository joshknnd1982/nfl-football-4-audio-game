"""The real calendar of a Franchise season: 18 weeks, 17 games for every team, one bye week (nfl4 only, rule 0.13; SZ.8). This is inspired by Jim Kitchen.

A player of the game wrote (2026-10-22) that the Franchise did not play the 2026 schedule. The original has 16 weeks that its `makes` draws for the player's
team, and the other teams meet by chance each week. The Franchise now plays the league's real calendar: `assets/data/schedule_2026.txt` lists the 272 games
of the 2026 regular season, week by week (the facts only: the week, the visiting team, the home team and the date; read from the public nflverse schedule
table, which follows the NFL's release of 2026-05, and checked against the NFL's own announcement of the opener and of a team's last week).

    schedule_2026.txt     W01G01 = T08 T28 2026-09-09        (the visiting team, the home team, the date; T01 to T32 are the IDs of teams.txt)

* The first season of a franchise plays the file of its year (the franchise's season 1 is 2026, `year_of`); a later season plays `schedule_<year>.txt` when
  a version of the game ships one (a new season is a file, not code), else the 2026 calendar with the teams relabeled (`relabel`): the divisions of each
  conference rotate and the places in them turn, so a team meets other opponents each year and every rule of the calendar still holds (the same week
  structure, byes and home games; division games stay division games). That is an approximation, said plainly in the README, not the NFL's rotation.
* `check` is the whole check of a calendar (every team plays 17 games and has one bye, twice against each team of its division, once at home and once
  away, never twice in a week). A file that does not pass is not used: the Franchise then plays the original's random 16 weeks and says so once (NXF-46, S8.3
  round 2: the README promises the real calendar, so a silent fallback broke rule 0.28 (4)); the log's `calendar_missing` line names the file.
  A file with a byte order mark (Notepad's) is read.

No speech, no draw and no file writing here; the league record keeps the calendar of its season (`LeagueRecord.calendar`).
"""
from __future__ import annotations

import logging
import os
import re

from ...data import customlists as cl
from ...data import paths
from ...game.league import DIVISIONS, PLACES, TEAM_COUNT
from ...game.schedule import Calendar, team_number, team_pair

log = logging.getLogger("nfl4.extras")

GAME = "NFL Football 4"
KIND = "schedule"
FIRST_YEAR = 2026
WEEKS, GAMES, DIVISION_GAMES = 18, 17, 6
FILE_NAME = "schedule_%d.txt"
_ID = re.compile(r"W(\d{1,2})G(\d{1,2})", re.IGNORECASE)
_GAME = re.compile(r"^T(\d{1,2})\s+T(\d{1,2})(?:\s+\S+)?$", re.IGNORECASE)


class CalendarError(ValueError):
    """A calendar that cannot be used, with what is wrong in plain words."""


def year_of(season: int) -> int:
    """The real year a franchise's season is played in: season 1 is 2026."""
    return FIRST_YEAR + season - 1


def shipped_path(year: int) -> str:
    return os.path.join(paths.program_dir(), "assets", "data", FILE_NAME % year)


def player_path(year: int) -> str:
    """The player's own copy of a year's calendar (D-128): the customize folder of the data folder, where the menu item "get the latest N. F. L. calendar"
    saves it and where the README tells the player to put one by hand. It is read before the shipped file of the same year."""
    return os.path.join(player_folder(), FILE_NAME % year)


def player_folder() -> str:
    """The folder of the player's own calendars (the tests point it at a folder of their own, conftest.py)."""
    return paths.customize_dir()


def check(calendar: Calendar) -> None:
    """CalendarError unless the calendar is whole: 18 weeks, 17 games and one bye for every team, each division rival twice (once at home, once away)."""
    if calendar.length != WEEKS:
        raise CalendarError("the calendar has %d weeks, not %d" % (calendar.length, WEEKS))
    games_of = [0] * (TEAM_COUNT + 1)
    home_of = [0] * (TEAM_COUNT + 1)
    meetings: dict = {}
    for number, games in enumerate(calendar.weeks, start=1):
        seen: set = set()
        if not 1 <= len(games) <= TEAM_COUNT // 2:
            raise CalendarError("week %d has %d games" % (number, len(games)))
        for visitor, home in games:
            if visitor == home:
                raise CalendarError("team %d plays itself in week %d" % (visitor, number))
            for team in (visitor, home):
                if not 1 <= team <= TEAM_COUNT:
                    raise CalendarError("week %d names the team %d" % (number, team))
                if team in seen:
                    raise CalendarError("team %d plays twice in week %d" % (team, number))
                seen.add(team)
                games_of[team] += 1
            home_of[home] += 1
            meetings[(visitor, home)] = meetings.get((visitor, home), 0) + 1
    for team in range(1, TEAM_COUNT + 1):
        if games_of[team] != GAMES:
            raise CalendarError("team %d plays %d games, not %d" % (team, games_of[team], GAMES))
        if home_of[team] not in (GAMES // 2, GAMES // 2 + 1):
            raise CalendarError("team %d plays %d games at home" % (team, home_of[team]))
    for division in range(1, DIVISIONS + 1):
        teams = [team_number(division, place) for place in range(1, PLACES + 1)]
        for visitor in teams:
            for home in teams:
                if visitor != home and meetings.get((visitor, home), 0) != 1:
                    raise CalendarError("team %d does not visit team %d once in its division" % (visitor, home))


def parse(text: str) -> Calendar:
    """The calendar a schedule file holds; CalendarError when it is not a whole calendar."""
    try:
        parsed = cl.parse_list(text, GAME, KIND)
    except cl.ListFormatError as exc:
        raise CalendarError(str(exc)) from exc
    if parsed.bad_lines:
        raise CalendarError("line %d: %s" % parsed.bad_lines[0])
    label = ""
    weeks: dict = {}
    for entry in parsed.entries:
        if entry.id == "VERSION":
            label = entry.value
            continue
        found = _ID.fullmatch(entry.id)
        game = _GAME.match(entry.value)
        if found is None or game is None:
            raise CalendarError("line %d: %s = %s is not a game" % (entry.line, entry.id, entry.value))
        week, number = int(found.group(1)), int(found.group(2))
        if not 1 <= week <= WEEKS or not 1 <= number <= TEAM_COUNT // 2:
            raise CalendarError("line %d: %s is out of the calendar" % (entry.line, entry.id))
        if (week, number) in {(w, n) for w, rows in weeks.items() for n, _ in rows}:
            raise CalendarError("line %d: %s is there twice" % (entry.line, entry.id))
        weeks.setdefault(week, []).append((number, (int(game.group(1)), int(game.group(2)))))
    if sorted(weeks) != list(range(1, WEEKS + 1)):
        raise CalendarError("the file holds the weeks %r" % (sorted(weeks),))
    calendar = Calendar(label, tuple(tuple(game for _, game in sorted(weeks[week])) for week in range(1, WEEKS + 1)))
    check(calendar)
    return calendar


def load_file(path: str) -> Calendar:
    # utf-8-sig (S8.3 round 2): a calendar saved by Notepad or another editor starts with a byte order mark, and the program's other text files read it too
    with open(path, "r", encoding="utf-8-sig") as handle:
        return parse(handle.read())


def relabel(calendar: Calendar, shift: int, label: str = "") -> Calendar:
    """The calendar with the teams relabeled for a later season: each conference's four divisions rotate (the A. F. C. forward, the N. F. C. back, so the
    pairs of divisions that meet change) and, every fourth season, the places in every division turn. A relabeling that keeps divisions together keeps
    every rule of the calendar (the same weeks, byes, home games and division games); `check` is run on the result."""
    shift = max(0, shift)
    afc_turn, nfc_turn, place_turn = shift % 4, (-shift) % 4, (shift // 4) % 4

    def moved(team: int) -> int:
        division, place = team_pair(team)
        base, turn = (1, afc_turn) if division <= DIVISIONS // 2 else (DIVISIONS // 2 + 1, nfc_turn)
        return team_number(base + (division - base + turn) % (DIVISIONS // 2), (place - 1 + place_turn) % PLACES + 1)

    weeks = tuple(tuple((moved(visitor), moved(home)) for visitor, home in games) for games in calendar.weeks)
    result = Calendar(label or calendar.label, weeks)
    check(result)
    return result


_cache: dict = {}
NEWEST_YEAR_TRIED = 2100                  # the years a base calendar is looked for (a file of a year after it is never read)


def _read(path: str):
    """The calendar of a file, or None (cached by the file's time; never raises)."""
    try:
        stamp = os.stat(path).st_mtime_ns
    except OSError:
        return None
    key = (path, stamp)
    if key not in _cache:
        try:
            _cache[key] = load_file(path)
        except (OSError, ValueError) as exc:
            log.warning("the calendar file %s cannot be used (%s)", path, exc)
            _cache[key] = None
    return _cache[key]


def _shipped(year: int):
    """The calendar of a year: the player's own file (D-128) when it is whole, else the shipped one, else None (never raises)."""
    return _read(player_path(year)) or _read(shipped_path(year))


def local_years() -> list:
    """The years whose calendar the game has (the player's files and the shipped ones that are whole), the newest last."""
    found = set()
    for folder in (player_folder(), os.path.join(paths.program_dir(), "assets", "data")):
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            match = re.fullmatch(r"schedule_(\d{4})\.txt", name, re.IGNORECASE)
            if match and FIRST_YEAR <= int(match.group(1)) <= NEWEST_YEAR_TRIED:
                found.add(int(match.group(1)))
    return sorted(year for year in found if _shipped(year) is not None)


def for_season(season: int):
    """The calendar a franchise plays in its season `season` (1 is 2026), or None when no calendar can be made: the file of that year (the player's or the
    shipped one), else the newest calendar of an earlier year relabeled by the number of years since (the 2026 one until a newer is shipped or downloaded,
    D-128). None sends the Franchise back to the original's random weeks."""
    year = year_of(season)
    exact = _shipped(year)
    if exact is not None:
        return exact
    earlier = [y for y in local_years() if y < year]
    if not earlier:
        return None
    base_year = earlier[-1]
    base = _shipped(base_year)
    if season <= 1:
        return base
    try:
        return relabel(base, year - base_year, "season %d, the %d calendar with the divisions rotated" % (year, base_year))
    except CalendarError:
        log.exception("the %d calendar could not be relabeled", base_year)
        return None
