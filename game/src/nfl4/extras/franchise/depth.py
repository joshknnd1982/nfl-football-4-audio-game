"""The player's depth chart and his players for the key downs and moments in a franchise (nfl4 only, rule 0.13; NX-D3, NX-D4, D-147). This is inspired
by Jim Kitchen.

`LeagueRecord.depth` (league.sav format 16): {"order": {group: [player ids]}, "key": {situation: {role: player id}}}, the player's own team only. The order
lists the men he put first in a group of places (the others follow by rating, as the staff orders every team: `aging.place_by_rating`), so a trade, a
signing, an injury or the cut keeps his order for the men still there. Plain rules, no speech, no files, no draw.

SR.5 (format 19, D-164): the order is by POSITION of the 22 and the roles KR and PR ({"LT": [ids], "KR": [ids], ...}): the men he put first of each
position's chart (real_roster.order_position keeps them on top). The F9 items of the older groups (running backs, wide receivers, ...) still work: a man
put first of his group is put first of his own position, and the group's list is the family's men in the view's order, then the rest of the chart.
"""
from __future__ import annotations

from ..depth_chart import ROLES, SITUATIONS
from ..roster_model import MADDEN
from .league import LeagueError

GROUPS = ("RB", "WR", "DL", "LB", "CB", "S", "RET", "K", "P")     # the franchise's groups of places a player may order (the quarterback has one)
KEYS = tuple(MADDEN) + ("KR", "PR")    # SR.5: the order's keys (format 19)


def empty() -> dict:
    return {"order": {}, "key": {}}


def player_order(league, position: str, players: list) -> list:
    """The group's players with the men the player put first in his order (of their own positions), then the others as given (by rating)."""
    order = (league.depth or {}).get("order", {})
    wanted = list(order.get(position, []))
    for key, ids in order.items():
        if key not in GROUPS:
            wanted += [pid for pid in ids if pid not in wanted]
    if not wanted:
        return players
    by_id = {p.id: p for p in players}
    first = [by_id[pid] for pid in wanted if pid in by_id]
    return first + [p for p in players if p not in first]


def group_of(league, position: str) -> list:
    return [p for p in league.group_of(league.team, position) if p is not None]


def chart_of(league, position: str) -> list:
    """The depth chart of a group (the F9 items of the older groups): the men of its places in order, then the other men of the family on the roster
    (the returners: the men of the return places, then the roles' others)."""
    if position == "RET":
        chart = league.chart[league.team - 1]
        first = group_of(league, "RET")
        seen = {p.id for p in first}
        rest = [league.players[pid] for role in ("KR", "PR") for pid in chart.get(role, ()) if pid in league.players and pid not in seen]
        return first + [p for n, p in enumerate(rest) if p.id not in {q.id for q in rest[:n]}]
    return group_of(league, position) + league.bench(league.team, position)


def put_first(league, position: str, pid: int) -> list:
    """The player makes `pid` the first of his group (an older F9 item): he is put first of his own position's chart (for the returners: the first kick
    returner), and his order is kept (`real_roster.choose_starter`); the places follow at once. Returns the group's new order (players)."""
    from . import real_roster
    current = chart_of(league, position)
    if pid not in [p.id for p in current]:
        raise LeagueError("player %r is not in the group %s of the player's team" % (pid, position))
    man = league.players[pid]
    real_roster.choose_starter(league, "KR" if position == "RET" else man.position, pid, 0)
    return chart_of(league, position)


def reset(league) -> None:
    """The staff's order again for every position (the best first) and no key players."""
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


def check(league, whole) -> None:
    depth = league.depth
    if not isinstance(depth, dict) or set(depth) not in ({"order", "key"}, {"order", "key", "dropped"}) or not isinstance(depth["order"], dict)             or not isinstance(depth["key"], dict):
        raise LeagueError("the depth chart is %r" % (type(depth).__name__,))
    dropped = depth.get("dropped", [])                       # SR.6: the starters the player chose who left the team, told once ([id, position, slot])
    if not isinstance(dropped, list) or len(dropped) > 200:
        raise LeagueError("the dropped starters are %r" % (type(dropped).__name__,))
    for row in dropped:
        if not isinstance(row, list) or len(row) != 3 or row[1] not in KEYS or not isinstance(row[0], int) or isinstance(row[0], bool)                 or not isinstance(row[2], int) or isinstance(row[2], bool) or not 0 <= row[2] <= 5:
            raise LeagueError("a dropped starter is %r" % (row,))
    for position, order in depth["order"].items():
        if position not in KEYS or not isinstance(order, list) or len(order) > 120:
            raise LeagueError("a depth chart position is %r" % (position,))
        for pid in order:
            whole(pid, 1, 10 ** 9, "a player of the depth chart")
    for situation, roles in depth["key"].items():
        if situation not in SITUATIONS or not isinstance(roles, dict):
            raise LeagueError("a key situation is %r" % (situation,))
        for role, pid in roles.items():
            if role not in ROLES:
                raise LeagueError("a key role is %r" % (role,))
            whole(pid, 1, 10 ** 9, "a key player")
