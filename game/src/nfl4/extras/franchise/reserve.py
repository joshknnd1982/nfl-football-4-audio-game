"""The player's injured reserve in the Franchise: placing a hurt man on the list, designating him to return, activating him (nfl4 only, rule 0.13; rule
0.40, D-216). This is inspired by Jim Kitchen.

A tester (2026-11-06), made the owner's own: "Add injured reserved to franchise mode. Include the ability to bring people off injured reserve including
activations." The N. F. L.'s rules (tuning FR_IR_..., SRC-SECONDARY, read 2026-11-06): a man on injured reserve leaves the 53 (his place is free for a
signing) and misses at least FR_IR_MIN_GAMES of his team's games; to bring him back the club DESIGNATES him to return, which opens his practice window
(once FR_IR_DESIGNATE_AFTER games are missed), and ACTIVATES him within FR_IR_WINDOW_WEEKS weeks, or he stays on the list for the rest of the season; a
club has FR_IR_RETURNS designations in a regular season and FR_IR_PLAYOFF_RETURNS more in the play-offs, one man at most FR_IR_MAN_RETURNS.

Only the player's own team is moved here: the computer teams keep the men their real rosters put on a list and the staff's rule for the hurt (the weekly
draws, the stand-ins), so nothing a computer team does or draws changes (a fingerprint of a season where the player chooses nothing stays the same). A man
of the real rosters who is on injured reserve when a franchise begins counts as placed before week 1. Everyone on a list comes back at the roster cut
(real_roster.return_lists), and the record is a matter of the season (injuries.end_of_season clears it).

The record, `LeagueRecord.injuries["reserve"]` (league.sav format 21):

    {"placed": [[player id, week placed, week designated (0: not yet), ended (0 or 1)], ...], "returns": [[player id, week designated], ...]}

Plain rules: no speech, no files, no draw. The caller (reserve_flow.py) asks, confirms, writes league.sav, then says what was done.
"""
from __future__ import annotations

from .. import roster_file as RF
from .. import tuning as T
from . import data as D
from . import injuries
from .league import SEASON, LeagueError

ON_IR = ("IR", "IRD")                 # the real roster's codes: injured reserve, and designated for return (roster_file.RESERVE)
OTHER_LISTS = ("PUP", "NFI")          # physically unable to perform and non-football injury: activated after the same four games, no designation
MAX_WEEK = D.MAX_REGULAR_WEEKS + 4    # the last week a row may name: the regular season and the four rounds of the play-offs


def empty() -> dict:
    return {"placed": [], "returns": []}


def record(league) -> dict:
    """The season's record (made when an older file or an older test's league has none)."""
    found = league.injuries.get("reserve")
    if not isinstance(found, dict):
        found = league.injuries["reserve"] = empty()
    return found


def in_season(league) -> bool:
    return league.stage == SEASON and 1 <= league.gtp <= league.regular_weeks + 4


def row_of(league, pid: int):
    for row in record(league)["placed"]:
        if row[0] == pid:
            return row
    return None


def on_list(league, team: int | None = None) -> list:
    """The team's men on injured reserve or the PUP and NFI lists, the best first."""
    team = league.team if team is None else team
    return sorted((p for p in league.players.values() if p.status == "list" and p.team == team and p.roster_list in ON_IR + OTHER_LISTS),
                  key=lambda p: (-p.rating, p.id))


def team_games(league, team: int, start: int, week: int) -> int:
    """The team's games from week `start` up to (not with) week `week`: its byes do not count; a week of the play-offs counts as a game."""
    regular = league.regular_weeks
    games = league.team_games_before(team, min(week, regular + 1)) - league.team_games_before(team, min(max(start, 1), regular + 1))
    return max(0, games + max(0, week - max(start, regular + 1)))


def placed_week(league, player) -> int:
    row = row_of(league, player.id)
    return row[1] if row is not None else 1                 # a man of the real rosters on a list from the start: placed before week 1


def missed(league, player, week: int) -> int:
    return team_games(league, player.team, placed_week(league, player), week)


def designated_week(league, player) -> int:
    row = row_of(league, player.id)
    return row[2] if row is not None else 0


def window_left(league, player, week: int) -> int:
    """The weeks left in his practice window (0: none open)."""
    start = designated_week(league, player)
    if not start:
        return 0
    return max(0, T.FR_IR_WINDOW_WEEKS - (week - start))


def ended(league, player, week: int) -> bool:
    """He stays on injured reserve for the rest of the season: his window closed without an activation."""
    row = row_of(league, player.id)
    return row is not None and (row[3] == 1 or (row[2] > 0 and window_left(league, player, week) == 0))


def returns_used(league) -> int:
    return len(record(league)["returns"])


def returns_allowed(league, week: int) -> int:
    return T.FR_IR_RETURNS + (T.FR_IR_PLAYOFF_RETURNS if week > league.regular_weeks else 0)


def returns_left(league, week: int) -> int:
    return max(0, returns_allowed(league, week) - returns_used(league))


def man_returns(league, pid: int) -> int:
    return sum(1 for row in record(league)["returns"] if row[0] == pid)


# ----- what can be done (a short reason for the tests and the log, or None) -----

def place_problem(league, player, week: int) -> str | None:
    from . import real_roster
    if not in_season(league):
        return "outside the season"
    if player is None or player.team != league.team or player.status != "active" or player.id in real_roster.waiting_ids(league):
        return "not a man of your active roster"
    if injuries.healthy(league, player.id, week):
        return "not hurt"
    if real_roster.breaks_minimum(league, player.team, gone=[player]):
        return "too few of his family left"
    return None


def designate_problem(league, player, week: int) -> str | None:
    if not in_season(league):
        return "outside the season"
    if player is None or player.team != league.team or player.status != "list" or player.roster_list not in ON_IR:
        return "not on injured reserve"
    if ended(league, player, week):
        return "out for the season"
    if designated_week(league, player):
        return "designated already"
    if missed(league, player, week) < T.FR_IR_DESIGNATE_AFTER:
        return "too early"
    if returns_left(league, week) <= 0:
        return "no returns left"
    if man_returns(league, player.id) >= T.FR_IR_MAN_RETURNS:
        return "he returned twice"
    return None


def activate_problem(league, player, week: int, release=None) -> str | None:
    from . import real_roster
    if not in_season(league):
        return "outside the season"
    if player is None or player.team != league.team or player.status != "list" or player.roster_list not in ON_IR + OTHER_LISTS:
        return "not on a reserve list"
    if player.roster_list in ON_IR:
        if ended(league, player, week):
            return "out for the season"
        if not designated_week(league, player):
            return "not designated"
    if missed(league, player, week) < T.FR_IR_MIN_GAMES:
        return "too early"
    if not injuries.healthy(league, player.id, week):
        return "still hurt"
    if real_roster.room(league, player.team) <= 0:
        if release is None:
            return "no room"
        if release.team != player.team or release.status != "active" or release.id in real_roster.waiting_ids(league):
            return "a release who is not a man of the roster"
        if not injuries.healthy(league, release.id, week):
            return "a release who is hurt"
        if real_roster.breaks_minimum(league, player.team, gone=[release], come=[player]):
            return "too few of his family left"
    elif release is not None:
        return "a release with room"
    return None


def releasable(league, player, week: int) -> list:
    """The men the player may release to make room for `player` (healthy men of his active roster, the family minimums kept), the lowest rated first."""
    from . import real_roster
    waiting = real_roster.waiting_ids(league)
    men = [p for p in league.team_men(player.team) if p.id not in waiting and injuries.healthy(league, p.id, week)]
    return sorted((p for p in men if not real_roster.breaks_minimum(league, player.team, gone=[p], come=[player], waiting=waiting)),
                  key=lambda p: (p.rating, p.id))


# ----- the moves -----

def _forget(league, pid: int) -> None:
    """A man who leaves the 53 leaves no question about him and no choice of who starts in his place."""
    league.injuries["chosen"] = [row for row in league.injuries["chosen"] if pid not in row]
    league.todo[:] = [item for item in league.todo if not (item["kind"] in (D.TODO_INJURY, D.TODO_LINEUP) and item.get("player") == pid)]


def _sums(league, team: int) -> None:
    if len(league.sums) == D.TEAMS:
        league.sums[team - 1] = league.strength_sum(team)


def place(league, player, week: int) -> None:
    """He goes on injured reserve: off the 53 (status "list", code IR), his injury runs on; the chart and the view follow."""
    from . import real_roster
    problem = place_problem(league, player, week)
    if problem is not None:
        raise LeagueError("cannot place %d on injured reserve: %s" % (player.id, problem))
    real_roster.leave(league, player, "list")
    player.roster_list = "IR"
    rows = [row for row in record(league)["placed"] if row[0] != player.id]
    rows.append([player.id, week, 0, 0])
    record(league)["placed"] = rows
    _forget(league, player.id)
    _sums(league, player.team)


def designate(league, player, week: int) -> None:
    """He is designated to return: one of the club's returns, his practice window opens (code IRD)."""
    problem = designate_problem(league, player, week)
    if problem is not None:
        raise LeagueError("cannot designate %d: %s" % (player.id, problem))
    row = row_of(league, player.id)
    if row is None:
        row = [player.id, 1, 0, 0]
        record(league)["placed"].append(row)
    row[2] = week
    record(league)["returns"].append([player.id, week])
    player.roster_list = "IRD"


def new_contract(player) -> tuple | None:
    """(salary, years) of the contract he signs when he comes back, or None when his own runs on (GitHub issue 8, D-220a). A man the real rosters put on a
    list when the franchise began has no contract (his salary is 0, his contract ran with the list), so he comes back on the market price, as the roster
    cut brings every list man back (real_roster.return_lists); a man the player placed keeps his own."""
    from . import contracts as CT
    if CT.running(player) and player.salary >= T.FR_MIN_SALARY:
        return None
    return CT.market_contract(player)


def activate(league, player, week: int, release=None) -> int:
    """He comes back to the 53 (onto his position's chart by the staff's order), on his own contract or on `new_contract`'s; `release` is released first
    when the 53 is full. Returns the dead money."""
    from . import contracts as CT
    from . import real_roster
    problem = activate_problem(league, player, week, release)
    if problem is not None:
        raise LeagueError("cannot activate %d: %s" % (player.id, problem))
    dead = 0
    if release is not None:
        dead = CT.release(league, release)
        release.left, release.points = league.season, 0
        real_roster.leave(league, release, "free", refresh=False)
        release.team = 0
        _forget(league, release.id)
    contract = new_contract(player)
    if contract is not None:
        CT.sign(player, *contract)                          # issue 8: an active man always has a contract (contracts.check_contracts)
    record(league)["placed"] = [row for row in record(league)["placed"] if row[0] != player.id]
    real_roster.join(league, player.team, player)
    _sums(league, player.team)
    return dead


def close_windows(league, week: int) -> list:
    """The men of the player's team whose practice window closed without an activation: marked out for the season (code IR again). Returns them."""
    closed = []
    for row in record(league)["placed"]:
        player = league.players.get(row[0])
        if player is None or row[3] == 1 or not row[2] or player.status != "list":
            continue
        if window_left(league, player, week) == 0:
            row[3] = 1
            player.roster_list = "IR"
            closed.append(player)
    return closed


# ----- the whole-file check (format 21) -----

def check(league, whole) -> None:
    found = league.injuries.get("reserve")
    if not isinstance(found, dict) or set(found) != {"placed", "returns"}:
        raise LeagueError("the injured reserve is %r" % (type(found).__name__,))
    placed, returns = found["placed"], found["returns"]
    if not isinstance(placed, list) or not isinstance(returns, list) or len(placed) > D.ROSTER_MAX * 2 or len(returns) > T.FR_IR_RETURNS + T.FR_IR_PLAYOFF_RETURNS:
        raise LeagueError("the injured reserve's lists are too long or not lists")
    if league.stage != SEASON and (placed or returns):
        raise LeagueError("an injured reserve outside the season")
    seen = set()
    for row in placed:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("an injured reserve row is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "a man on injured reserve")
        whole(row[1], 1, MAX_WEEK, "the week he was placed on injured reserve")
        if row[2] != 0:
            whole(row[2], 1, MAX_WEEK, "the week he was designated to return")
        whole(row[3], 0, 1, "the end of his season on injured reserve")
        player = league.players.get(row[0])
        if row[0] in seen or player is None or player.status != "list" or player.roster_list not in ON_IR:
            raise LeagueError("the man %r of the injured reserve is not on it, or is there twice" % (row[0],))
        seen.add(row[0])
    for row in returns:
        if not isinstance(row, list) or len(row) != 2:
            raise LeagueError("a return from injured reserve is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "a man designated to return")
        whole(row[1], 1, MAX_WEEK, "the week of a designation")
        if row[0] not in league.players:
            raise LeagueError("a return names the unknown player %r" % (row[0],))


__all__ = ["RF"]
