"""The player's depth chart and his players for the key downs and moments in a franchise (nfl4 only, rule 0.13; NX-D3, NX-D4, D-147). This is inspired
by Jim Kitchen.

`LeagueRecord.depth` (league.sav format 16): {"order": {group: [player ids]}, "key": {situation: {role: player id}}}, the player's own team only. The order
lists the men he put first in a group of places (the others follow by rating, as the staff orders every team: `aging.place_by_rating`), so a trade, a
signing, an injury or the cut keeps his order for the men still there. Plain rules, no speech, no files, no draw.
"""
from __future__ import annotations

from ..depth_chart import ROLES, SITUATIONS
from . import data as D
from .league import LeagueError

GROUPS = ("RB", "WR", "DL", "LB", "CB", "S", "RET", "K", "P")     # the franchise's groups of places a player may order (the quarterback has one)


def empty() -> dict:
    return {"order": {}, "key": {}}


def player_order(league, position: str, players: list) -> list:
    """The group's players with the men the player put first in his order, then the others as given (by rating)."""
    wanted = (league.depth or {}).get("order", {}).get(position, [])
    if not wanted:
        return players
    by_id = {p.id: p for p in players}
    first = [by_id[pid] for pid in wanted if pid in by_id]
    return first + [p for p in players if p not in first]


def group_of(league, position: str) -> list:
    return [p for p in league.group_of(league.team, position) if p is not None]


def put_first(league, position: str, pid: int) -> list:
    """The player makes `pid` the first of his group: the order becomes he, then the group's others as they stand; the places follow at once. Returns
    the group's new order (players)."""
    current = group_of(league, position)
    if pid not in [p.id for p in current]:
        raise LeagueError("player %r is not in the group %s of the player's team" % (pid, position))
    order = [pid] + [p.id for p in current if p.id != pid]
    league.depth.setdefault("order", {})[position] = order
    roster = league.rosters[league.team - 1]
    places = D.PLACES_OF[position]
    players = [league.players[i] for i in order]
    for index, player in zip(places, players):
        roster[index] = player.id
        player.place = index
    if len(league.sums) == D.TEAMS:
        league.sums[league.team - 1] = league.strength_sum(league.team)
    return players


def reset(league) -> None:
    """The staff's order again for every group (the best first) and no key players."""
    league.depth = empty()
    from .aging import place_by_rating
    place_by_rating(league, league.team)


def set_key(league, situation: str, role: str, pid: int | None) -> None:
    keys = league.depth.setdefault("key", {})
    if pid is None:
        keys.get(situation, {}).pop(role, None)
        if situation in keys and not keys[situation]:
            del keys[situation]
        return
    keys.setdefault(situation, {})[role] = pid


def real_starters_first(league) -> int:
    """A new franchise of the real players: in each group of each team the best drawn rating goes to the real starter, the next to the next man of the
    depth chart (the ratings of the group are only given to other men, no draw; age, potential and contract follow later). Returns how many groups moved."""
    moved = 0
    for team in range(1, D.TEAMS + 1):
        for position, places in D.PLACES_OF.items():
            players = [league.player_at(team, i) for i in places]
            players = [p for p in players if p is not None]
            values = sorted(((p.rating, p.peak, p.potential) for p in players), key=lambda v: -v[0])
            if [p.rating for p in players] == [v[0] for v in values]:
                continue
            for player, (rating, peak, potential) in zip(players, values):
                player.rating, player.peak, player.potential = rating, max(peak, rating), potential
            moved += 1
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)] if league.sums else league.sums
    return moved


def check(league, whole) -> None:
    depth = league.depth
    if not isinstance(depth, dict) or set(depth) != {"order", "key"} or not isinstance(depth["order"], dict) or not isinstance(depth["key"], dict):
        raise LeagueError("the depth chart is %r" % (type(depth).__name__,))
    for position, order in depth["order"].items():
        if position not in GROUPS or not isinstance(order, list) or len(order) > len(D.PLACES_OF[position]) + 20:
            raise LeagueError("a depth chart group is %r" % (position,))
        for pid in order:
            whole(pid, 1, 10 ** 9, "a player of the depth chart")
    for situation, roles in depth["key"].items():
        if situation not in SITUATIONS or not isinstance(roles, dict):
            raise LeagueError("a key situation is %r" % (situation,))
        for role, pid in roles.items():
            if role not in ROLES:
                raise LeagueError("a key role is %r" % (role,))
            whole(pid, 1, 10 ** 9, "a key player")
