"""The non-exclusive franchise tag and its offer sheet (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8m (research B3, D-073). Plain rules over the league record, no speech, no files and no draw. The NFL (operations.nfl.com, franchise
tags, SRC-OFFICIAL): a player of the non-exclusive tag is paid one year at the higher of the position's cap percentage average or 120 percent of his prior
salary and may negotiate with other clubs; his club may match an offer sheet, else it is entitled to two first-round picks; the exclusive tag pays the higher of
the average of the five largest salaries at the position or the non-exclusive amount.

    record_history / cap_average     the position's average of its highest salaries, kept for `FR_TAG_HISTORY` seasons (the cap is a constant, so the
                                     average of those averages is the cap percentage average)
    nonexclusive_salary              the price of the non-exclusive tag (`resign.tag_salary` is the exclusive one and is never under it)
    offer_sheet                      the computer team that offers for the tagged player at stage 8, and its contract, or None (one code path: the same rule
                                     for every team, as the trades' value rule)
    should_match / match / let_go    the staff's recommendation, and the two answers: keep him at the offer, or let him go for two first-round picks
    check_tags / check_future        the whole-file checks of `league.tags` and `league.future_picks`

Only the player's team uses a tag (the computer teams never do: D-067), so the fast run has none; the rule a computer team makes a sheet by is tested on
strict leagues. `league.tags` is {"history": {position: [averages, oldest first]}, "open": [player, season] while a non-exclusive tag waits for stage 8,
"sheet": [team, salary, years] while the player decides}. `league.future_picks` holds the first-round picks owed for the draft after the coming one,
[draft season, round, original team, owner]; stage 6 moves them into the trades' table of the coming draft.
"""
from __future__ import annotations

import dataclasses

from .. import tuning as T
from . import contracts as CT
from . import data as D

KEYS = ("history", "open", "sheet")


def empty() -> dict:
    return {"history": {}, "open": None, "sheet": None}


# ----- the prices -----

def top_average(league, position: str) -> int:
    """The average of the `FR_TAG_TOP` highest salaries at the position among the contracts that run (rounded half up), 0 when there are none."""
    top = sorted((p.salary for p in league.players.values() if p.status == "active" and p.pos == position and CT.running(p)),
                 reverse=True)[:T.FR_TAG_TOP]
    return (sum(top) + len(top) // 2) // len(top) if top else 0


def record_history(league) -> None:
    """Stage 7 begins (before anybody is signed again): every position's average of its highest salaries joins its history; the oldest beyond
    `FR_TAG_HISTORY` seasons is dropped."""
    history = league.tags["history"]
    for position in D.POSITIONS:
        values = list(history.get(position, [])) + [top_average(league, position)]
        history[position] = values[-T.FR_TAG_HISTORY:]


def cap_average(league, position: str) -> int:
    """The position's cap percentage average: the mean of its kept averages (rounded half up); the average of now when none is kept (a league older than this rule)."""
    values = league.tags["history"].get(position) or [top_average(league, position)]
    return (sum(values) + len(values) // 2) // len(values)


def nonexclusive_salary(league, player) -> int:
    """One year at the position's cap percentage average, or `FR_TAG_RAISE` percent of his last salary, or his market price, whichever is most, never over
    the maximum."""
    raised = (player.salary * T.FR_TAG_RAISE + 50) // 100
    return min(T.FR_MAX_SALARY, max(cap_average(league, player.pos), raised, CT.market_salary(player.pos, player.rating)))


# ----- the offer sheet (stage 8) -----

def tagged(league):
    """The player of the non-exclusive tag waiting for stage 8, or None."""
    data = league.tags.get("open")
    return league.players.get(data[0]) if data else None


def sheet_value(player, salary: int, years: int, how: str) -> int:
    from . import trades
    return trades.player_value(dataclasses.replace(player, salary=salary, years=years), how)


def picks_value(how: str) -> int:
    from . import trades
    return T.FR_TAG_SHEET_PICKS * trades.pick_value(1, how)


def owns_both_firsts(league, team: int) -> bool:
    """The team owns its first-round pick of the coming draft and owes none of the draft after it."""
    from . import trades
    return trades.owner(league, 1, team) == team and not any(row[2] == team and row[1] == 1 for row in league.future_picks)


def offer_sheet(league):
    """(team, salary, years) of the offer sheet for the tagged player, or None: among the other teams with an empty place at his position, the room under
    the cap for his market price (the length of his age), both of their first-round picks, and a value of him at that contract of at least the two picks'
    (each by the team's situation), the team that values him most, equal values by the market's tie rule; the offer pays at least his tag. No draw; nothing
    is changed."""
    from . import market, real_roster, trades
    player = tagged(league)
    if player is None:
        return None
    price, years = CT.market_contract(player)
    salary = max(price, player.salary)           # an offer sheet pays at least his tag (the review of SX.8m: at the market price it was always a pay cut)
    best = None
    for team in range(1, D.TEAMS + 1):
        if team == player.team:
            continue
        if real_roster.room(league, team) <= 0 or salary > market.room(league, team):          # SR.5: a spot on the 53
            continue
        if not owns_both_firsts(league, team):
            continue
        how = trades.situation(league.records, team)
        value = sheet_value(player, salary, years, how)
        if value < picks_value(how):
            continue
        key = (-value, market.tie_key(team, player.id))
        if best is None or key < best[0]:
            best = (key, team)
    return None if best is None else (best[1], salary, years)


def can_match(league, player, salary: int) -> bool:
    """His team can keep him at the offer: the offer pays him no more than the tag, or its cap with the offer in place of the tag's salary stays under it."""
    return salary <= player.salary or CT.cap_used(league, player.team) - player.salary + salary <= CT.cap_of(league)


def should_match(league, player, salary: int, years: int) -> bool:
    """The staff's recommendation: match when the team can and he is worth at least the two picks to it (its situation)."""
    from . import trades
    how = trades.situation(league.records, player.team)
    return can_match(league, player, salary) and sheet_value(player, salary, years, how) >= picks_value(how)


def match(league, player, salary: int, years: int) -> None:
    CT.sign(player, salary, years)


def let_go(league, player, team: int, salary: int, years: int) -> None:
    """He joins the team of the sheet on its contract, in its first empty place of his position (else its bench, D-149); his team gets that team's first-round
    pick of the coming draft and of the draft after it (`future_picks`)."""
    from . import real_roster, trades
    old = player.team
    real_roster.join(league, team, player)               # SR.5: onto the other team's chart; both teams' places are made again
    CT.sign(player, salary, years)
    trades.move_pick(league, (1, team), old)
    league.future_picks.append([league.season + 1, 1, team, old])


def close(league) -> None:
    league.tags["open"] = None
    league.tags["sheet"] = None


def move_future(league) -> None:
    """Stage 6, the new season: the picks owed for this season's draft join the trades' table of the coming draft."""
    from . import trades
    due = [row for row in league.future_picks if row[0] == league.season]
    league.future_picks = [row for row in league.future_picks if row[0] != league.season]
    for _season, round_no, original, owner in due:
        trades.move_pick(league, (round_no, original), owner)


# ----- the whole-file checks -----

def check_tags(league, whole) -> None:
    from .league import OFFSEASON, LeagueError
    data = league.tags
    if not isinstance(data, dict) or set(data) != set(KEYS):
        raise LeagueError("the tags hold %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    history = data["history"]
    if not isinstance(history, dict) or any(key not in D.POSITIONS for key in history):
        raise LeagueError("the tags' history is %r" % (type(history).__name__,))
    for values in history.values():
        if not isinstance(values, list) or len(values) > T.FR_TAG_HISTORY:
            raise LeagueError("a position's history of salaries is %r" % (values,))
        for value in values:
            whole(value, 0, T.FR_MAX_SALARY, "an average of the highest salaries")
    opened = data["open"]
    if opened is not None:
        if not isinstance(opened, list) or len(opened) != 2:
            raise LeagueError("the non-exclusive tag is %r" % (opened,))
        whole(opened[1], league.season, league.season, "the season of the non-exclusive tag")
        player = league.players.get(opened[0]) if isinstance(opened[0], int) and not isinstance(opened[0], bool) else None
        if (league.stage != OFFSEASON or league.stage_no not in (D.STAGE_CONTRACTS, D.STAGE_FREE_AGENCY) or player is None or player.status != "active"
                or player.team != league.team or player.years != 1):
            raise LeagueError("the non-exclusive tag of player %r does not fit stage %r %r" % (opened[0], league.stage, league.stage_no))
    sheet = data["sheet"]
    if sheet is not None:
        if opened is None or league.stage_no != D.STAGE_FREE_AGENCY or not isinstance(sheet, list) or len(sheet) != 3:
            raise LeagueError("an offer sheet %r without a tagged player at free agency" % (sheet,))
        whole(sheet[0], 1, D.TEAMS, "the team of an offer sheet")
        whole(sheet[1], T.FR_MIN_SALARY, T.FR_MAX_SALARY, "the salary of an offer sheet")
        whole(sheet[2], 1, max(years for _age, years in T.FR_CONTRACT_YEARS), "the years of an offer sheet")
        if sheet[0] == league.team:
            raise LeagueError("an offer sheet of the player's own team")
    check_future(league, whole)


def check_future(league, whole) -> None:
    from .league import LeagueError
    rows = league.future_picks
    if not isinstance(rows, list) or len(rows) > D.TEAMS * D.DRAFT_ROUNDS:       # RC (D-197): every round of the draft after the coming one
        raise LeagueError("the picks owed are %r" % (type(rows).__name__ if not isinstance(rows, list) else len(rows),))
    seen: set = set()
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a pick owed is %r" % (row,))
        whole(row[0], league.season + 1, league.season + 1, "the draft of a pick owed")
        whole(row[1], 1, D.DRAFT_ROUNDS, "the round of a pick owed")
        whole(row[2], 1, D.TEAMS, "the team of a pick owed")
        whole(row[3], 1, D.TEAMS, "the owner of a pick owed")
        if row[2] == row[3] or (row[0], row[1], row[2]) in seen:
            raise LeagueError("the pick owed %r is listed twice or with its own team" % (row,))
        seen.add((row[0], row[1], row[2]))
