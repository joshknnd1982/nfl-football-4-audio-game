"""The to-do list of the Franchise: its items, their answers and what the answers do (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 8.1 and 8.2 (F5). Rules over the league record, no speech and no files and no draw, so the weekly flow
(`weekly.py`) and the calibration's fast run use the very same code. The list is `LeagueRecord.todo`, plain dicts:

    {"kind": "extra_work", "season": s, "week": w, "state": 0, "players": [id, id]}      T1 extra work (design 8.1, 8.2)
    {"kind": "game_plan",  "season": s, "week": w, "state": 0, "styles": [their offense, their defense, our offense, our defense]}   T2

An item has a deadline: the kick-off of its week's game. `state` is ITEM_NEW (not asked yet), ITEM_LATER (answered "later") or, for
the game plan only, ITEM_SET (taken for this week's game; the game reads it). A new week's list replaces the old one. The kinds are
`data.TODO_KINDS`; a later update (contracts, injuries, coordinators) adds its own.

T1: a point of development is +1 on the player's change at the next progression (aging.plan_development reads `Player.points`), at
most FR_EXTRA_WORK_POINTS (3) a season. Every computer team gives its first candidate the point in the same weeks, in the same code
(`computer_extra_work`), so the player's advantage is only the choice, and the points are rating added to the league every year: the
calibration (C-F4) counts them.
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D
from .league import LeagueError, LeagueRecord, Player


# ----- T1: extra work -----

def is_candidate(player: Player) -> bool:
    """Young (FR_EXTRA_WORK_AGE or less), a high or average potential and fewer than FR_EXTRA_WORK_POINTS points this season."""
    return (player.status == "active" and player.age <= T.FR_EXTRA_WORK_AGE and player.potential != "low"
            and player.points < T.FR_EXTRA_WORK_POINTS)


def candidates(league: LeagueRecord, team: int) -> list:
    """The team's two best candidates (the highest potential, then the youngest, then the highest rating, then the lower ID), or
    none when it has fewer than FR_EXTRA_WORK_CANDIDATES of them (design 8.1 T1)."""
    pool = [p for p in league.active_of(team) if p is not None and is_candidate(p)]
    if len(pool) < T.FR_EXTRA_WORK_CANDIDATES:
        return []
    pool.sort(key=lambda p: (D.POTENTIALS.index(p.potential), p.age, -p.rating, p.id))
    return pool[:2]


def computer_extra_work(league: LeagueRecord, week: int) -> int:
    """In an extra-work week every computer team gives its first candidate the point. Returns how many points were given."""
    if week not in T.FR_EXTRA_WORK_WEEKS:
        return 0
    given = 0
    for team in range(1, D.TEAMS + 1):
        if team == league.team:
            continue
        picked = candidates(league, team)
        if picked:
            picked[0].points += 1
            given += 1
    return given


def extra_work_item(league: LeagueRecord, week: int) -> dict | None:
    """The player's item of this week, or None (not an extra-work week, or fewer than two candidates)."""
    if week not in T.FR_EXTRA_WORK_WEEKS:
        return None
    picked = candidates(league, league.team)
    if not picked:
        return None
    return {"kind": D.TODO_EXTRA_WORK, "season": league.season, "week": week, "state": D.ITEM_NEW, "players": [p.id for p in picked]}


def valid_players(league: LeagueRecord, item: dict) -> list:
    """The players of an extra-work item who can still take the point (active, on the team, not at the season's limit)."""
    players = [league.players.get(pid) for pid in item["players"]]
    return [p for p in players if p is not None and p.team == league.team and is_candidate(p)]


# ----- T2: the game plan -----

def game_plan_item(league: LeagueRecord, week: int, their_offense: str, their_defense: str, offense_book: str, defense_book: str,
                   styles: set) -> dict | None:
    """The item of a regular week when the player's offense or defense playbook setting is not Classic. The staff recommends, for
    each side the player plays a playbook on, the style `tuning.FR_GAME_PLAN` gives for the opponent's style on the other side (the
    keys are Classic or a style of `styles`); a side the player keeps Classic stays Classic."""
    classic = "classic"
    if not 1 <= week <= D.REGULAR_WEEKS or (offense_book == classic and defense_book == classic):
        return None

    def recommended(table: dict, key: str) -> str:
        style = table.get(key, classic)
        return style if style in styles else classic

    ours_o = recommended(T.FR_GAME_PLAN["offense"], their_defense) if offense_book != classic else classic
    ours_d = recommended(T.FR_GAME_PLAN["defense"], their_offense) if defense_book != classic else classic
    return {"kind": D.TODO_GAME_PLAN, "season": league.season, "week": week, "state": D.ITEM_NEW,
            "styles": [their_offense, their_defense, ours_o, ours_d]}


def plan_of(league: LeagueRecord, week: int) -> tuple | None:
    """(offense style, defense style) of the game plan taken for this week's game, or None."""
    for item in league.todo:
        if (item["kind"] == D.TODO_GAME_PLAN and item["state"] == D.ITEM_SET and item["season"] == league.season
                and item["week"] == week):
            return item["styles"][2], item["styles"][3]
    return None


# ----- answering -----

def answer_count(league: LeagueRecord, item: dict) -> int:
    """How many answers an item offers, not counting "later": extra work, its valid players and "nobody this week"; the game
    plan, two."""
    if item["kind"] == D.TODO_EXTRA_WORK:
        return len(valid_players(league, item)) + 1
    return 2


def is_do_nothing(league: LeagueRecord, item: dict, answer: int) -> bool:
    """The last answer of an item is its "do nothing" answer (nobody this week, keep your playbooks)."""
    return answer == answer_count(league, item) - 1


def apply_answer(league: LeagueRecord, item: dict, answer: int) -> Player | None:
    """Take an answer (0 is the staff's recommendation) and finish the item: it leaves the list, except a game plan that was set,
    which stays (state ITEM_SET) until the week is over. Returns the player who got the point, if any."""
    if item["kind"] == D.TODO_EXTRA_WORK:
        valid = valid_players(league, item)
        chosen = valid[answer] if answer < len(valid) else None
        if chosen is not None:
            chosen.points += 1
        league.todo.remove(item)
        return chosen
    if answer == 0:
        item["state"] = D.ITEM_SET
    else:
        league.todo.remove(item)
    return None


def put_off(item: dict) -> None:
    item["state"] = D.ITEM_LATER


def waiting(league: LeagueRecord, include_later: bool = True) -> list:
    """The items still to answer (new ones, and with `include_later` the ones answered later), in the list's order."""
    states = (D.ITEM_NEW, D.ITEM_LATER) if include_later else (D.ITEM_NEW,)
    return [item for item in league.todo if item["state"] in states]


def drop_old(league: LeagueRecord, week: int) -> None:
    """A new week's list replaces the old (an item's deadline was its week's kick-off)."""
    league.todo[:] = [item for item in league.todo if item["season"] == league.season and item["week"] == week]


def close_unanswered(league: LeagueRecord) -> int:
    """The kick-off came: every item still waiting is closed with its "do nothing" answer (design 8.1: nothing is ever decided for
    the player). Returns how many were closed."""
    closed = 0
    for item in list(waiting(league)):
        league.todo.remove(item)
        closed += 1
    return closed


# ----- the whole-file check of the list -----

def check_items(league: LeagueRecord, whole) -> None:
    """Every item well formed, in range, at most one of a kind in a week (LeagueError otherwise: damage, never clamped)."""
    from ..playbook_data import BOOK_KEYS
    items = league.todo
    if not isinstance(items, list) or len(items) > D.MAX_TODO:
        raise LeagueError("the to-do list is %r" % (type(items).__name__,))
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) not in ({"kind", "season", "week", "state", "players"},
                                                            {"kind", "season", "week", "state", "styles"}):
            raise LeagueError("a to-do item is %r" % (item,))
        if item["kind"] not in D.TODO_KINDS:
            raise LeagueError("a to-do item of the kind %r" % (item["kind"],))
        whole(item["season"], 1, D.MAX_SEASONS, "a to-do season")
        whole(item["week"], 1, D.REGULAR_WEEKS, "a to-do week")
        whole(item["state"], D.ITEM_NEW, D.ITEM_SET, "a to-do state")
        if (item["kind"], item["season"], item["week"]) in seen:
            raise LeagueError("two to-do items of one kind in one week: %r" % (item,))
        seen.add((item["kind"], item["season"], item["week"]))
        if item["kind"] == D.TODO_EXTRA_WORK:
            players = item.get("players")
            if "players" not in item or item["state"] == D.ITEM_SET or not isinstance(players, list) or not 1 <= len(players) <= 2:
                raise LeagueError("an extra-work item is %r" % (item,))
            for pid in players:
                whole(pid, 1, 10 ** 9, "an extra-work player")
            if len(set(players)) != len(players):
                raise LeagueError("an extra-work item names a player twice: %r" % (item,))
        else:
            styles = item.get("styles")
            if "styles" not in item or not isinstance(styles, list) or len(styles) != 4 or any(
                    not isinstance(s, str) or s not in BOOK_KEYS for s in styles):
                raise LeagueError("a game-plan item is %r" % (item,))
