"""Compensatory picks of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8m (research B4 and F2, D-073). Plain rules, no speech, no files and no draw, so stage 8 of the offseason (`market_flow.py`) and the
calibration's fast run use the very same code.

The NFL's rule (SRC-OFFICIAL, the league's announcements): a club that suffers a net loss of compensatory free agents in the free agency period gets as many
compensatory picks, after offsetting each one lost by each one gained of an equal or higher value; no club gets more than four in a year; the league awards at
most 32; they sit at the end of rounds 3 to 7, by the value of the players lost; they come in the draft of the next year. The formula itself is not published:
here a compensatory free agent is a free agent who signed with ANOTHER team in the market for `FR_COMP_QUALIFY` or more, and his salary is his value.

    moves                   the market's signings as rows [player ID, the team he left, the team he joined, salary] (`market.Round.moves`)
    team_values             the values of the picks one team earns from the moves (the offsetting, the net loss, at most four)
    award                   every team's picks, at most 32 in the league, written into `league.comp` for the NEXT offseason's draft
    for_draft               the picks of this offseason's draft, in their places at the end of their rounds (`draft.Draft.create`)
    check_comp              the whole-file check of `league.comp`

A row of `league.comp` is [the season of the draft, round, team, value]: made at stage 8 of the offseason after season s for the draft of the offseason after
season s + 1, taken by that draft when it is created, and dropped at stage 6 when its season is over.
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D


def qualifies(salary: int) -> bool:
    return salary >= T.FR_COMP_QUALIFY


def round_of(value: int) -> int:
    """The round of a compensatory pick by the value of the player lost: the first row of `FR_COMP_ROUNDS` whose least value it reaches."""
    for least, round_no in T.FR_COMP_ROUNDS:
        if value >= least:
            return round_no
    return D.COMP_LAST_ROUND


def team_values(team: int, moves: list) -> list:
    """The values of the picks the team earns, the highest first: the compensatory free agents it lost to other teams, each offset by one it gained of an
    equal or higher value (a gained one offsets the most valuable lost one it can), the rest limited to the net loss in number (lost minus gained) and to
    `FR_COMP_TEAM_MAX`."""
    lost = sorted((row[3] for row in moves if row[1] == team and row[2] != team and qualifies(row[3])), reverse=True)
    gained = sorted((row[3] for row in moves if row[2] == team and row[1] != team and qualifies(row[3])), reverse=True)
    remaining = list(lost)
    for value in gained:
        offset = [v for v in remaining if v <= value]
        if offset:
            remaining.remove(max(offset))
    allowed = max(0, len(lost) - len(gained))
    return remaining[:min(allowed, T.FR_COMP_TEAM_MAX)]


def tie(team: int, season: int) -> int:
    """Equal values are told apart by a rule that favors no team (the market's: a multiplier picked by the season)."""
    from .market import tie_key
    return tie_key(team, season)


def award(league, moves: list) -> list:
    """Every team's compensatory picks for the draft of the NEXT offseason (season + 1): at most `FR_COMP_TOTAL` in the league, the highest values first.
    Writes them into `league.comp` (rows of earlier awards for other drafts are kept) and returns the new rows, by round and then by value."""
    season = league.season + 1
    earned = [(value, team) for team in range(1, D.TEAMS + 1) for value in team_values(team, moves)]
    earned.sort(key=lambda vt: (-vt[0], tie(vt[1], season)))
    kept = earned[:T.FR_COMP_TOTAL]
    rows = sorted(([season, round_of(value), team, value] for value, team in kept), key=lambda r: (r[1], -r[3], tie(r[2], season)))
    league.comp = [row for row in league.comp if row[0] != season] + rows
    return rows


def of_team(league, team: int, season: int) -> list:
    """The rounds of the team's compensatory picks in the draft of that season, the earliest first."""
    return sorted(row[1] for row in league.comp if row[0] == season and row[2] == team)


def for_draft(league, order: list) -> list:
    """The compensatory picks of the draft being created (the rows of this season), as [round, team] in their places: by round, then the higher value first,
    equal values by the draft order. The rows are taken out of `league.comp` (the draft record holds them now)."""
    rows = [row for row in league.comp if row[0] == league.season]
    rows.sort(key=lambda r: (r[1], -r[3], order.index(r[2]) if r[2] in order else D.TEAMS))
    league.comp = [row for row in league.comp if row[0] != league.season]
    return [[row[1], row[2]] for row in rows]


def drop_past(league) -> None:
    """Stage 6: the rows of drafts that are over are dropped (a row is never older than the season it names)."""
    league.comp = [row for row in league.comp if row[0] >= league.season]


def check_rows(rows, whole, what: str) -> None:
    """[round, team] rows of a draft's compensatory picks: rounds 3 to 7, at most four a team and `FR_COMP_TOTAL` in all."""
    from .league import LeagueError
    if not isinstance(rows, list) or len(rows) > T.FR_COMP_TOTAL:
        raise LeagueError("%s are %r" % (what, rows if not isinstance(rows, list) else len(rows)))
    per_team: dict = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise LeagueError("a compensatory pick is %r" % (row,))
        whole(row[0], D.COMP_FIRST_ROUND, D.COMP_LAST_ROUND, "a compensatory pick's round")
        whole(row[1], 1, D.TEAMS, "a compensatory pick's team")
        per_team[row[1]] = per_team.get(row[1], 0) + 1
        if per_team[row[1]] > T.FR_COMP_TEAM_MAX:
            raise LeagueError("team %d has %d compensatory picks" % (row[1], per_team[row[1]]))


def check_comp(league, whole) -> None:
    """LeagueError (through `whole`) unless `league.comp` holds whole rows for this season's draft or the next one: rounds 3 to 7, at most four a team and
    `FR_COMP_TOTAL` for a draft, none for this season while its draft holds them."""
    from .league import LeagueError
    rows = league.comp
    if not isinstance(rows, list) or len(rows) > 2 * T.FR_COMP_TOTAL:
        raise LeagueError("the compensatory picks are %r" % (type(rows).__name__ if not isinstance(rows, list) else len(rows),))
    by_season: dict = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a compensatory pick awarded is %r" % (row,))
        whole(row[0], league.season, league.season + 1, "the draft of a compensatory pick")
        whole(row[3], 0, T.FR_MAX_SALARY, "the value of a compensatory pick")
        by_season.setdefault(row[0], []).append([row[1], row[2]])
        if row[0] == league.season and league.draft is not None:
            raise LeagueError("a compensatory pick of this draft outside the draft")
    for season, picks in by_season.items():
        check_rows(picks, whole, "the compensatory picks of season %d" % season)
