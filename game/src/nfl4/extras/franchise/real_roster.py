"""The Franchise's real roster: a team is its depth chart on Madden NFL's 22 positions; the original's 34 places are a view made from it (nfl4 only, rule
0.13; CLAUDE.md 0.30 and 0.32, NX-L3 to NX-L7, NX-L11; NFL_FRANCHISE_DESIGN 21.3 to 21.7 and 21.13; D-159, D-160, D-161, D-164). This is inspired by
Jim Kitchen.

SR.5 (D-164): the CHART is the team. Every block of the Franchise that adds a man to a team or takes one off (the cut, the draft, signings, trades, the
practice squads, retirements, re-signing) says so here (`join`, `leave`, `refresh_view`), and the team's 34 places (`LeagueRecord.rosters`, `Player.place`)
are made again from its chart at once: they are never stored (league.sav format 19). A man of the active roster without a place is the team's "bench" in
the old words (`LeagueRecord.bench`): he is an active man the game day does not use, never a status of his own (the status "reserve" of D-149 is gone).

* `refresh_view(team)`: the chart cleaned (every active man of the team once, at his own position; nobody else), each position in the staff's order (the
  best rating first, the chart's order among equals; on the player's own team the men he put first, `LeagueRecord.depth["order"]`, keep their places),
  the return roles kept to men still there, then the 34 places from `roster_model.make_view` (one man one place, Q-082). A team with no active kicker or
  punter signs its practice squad's (a game-day man becomes a man of the 53, 21.7 (7)). The draft's rookies wait outside the chart until the cut.
* `join` / `leave`: a man comes onto or goes off a team's roster (his status, team and list are the caller's), then the view.
* `make_real` (a new franchise): every man of rosters.txt on his team, at his position, number and list, nobody made up, nobody left off; the drawn
  values of 0.16 go to the men the view puts in the places, then each position's best rating goes to its real starter (`starters_first`, no draw).
* `from_places` (a league of format 18 or older, before its first check): the places and the bench of the older file become the chart.
* `convert` (format 17 or older, once, when the store opens it): every man his real position and number by his name in rosters.txt, a league without
  benches its teams' missing real men, the charts again.

Plain rules: no speech, no files, no draw.
"""
from __future__ import annotations

import logging

from ...data import debuglog
from .. import roster_file as RF
from .. import roster_model as RM
from .. import tuning as T
from . import data as D

log = logging.getLogger("nfl4.extras")

ON_ROSTER = ("active",)


# ----- the shape of the new values -----

def check_player(p) -> None:
    from .league import LeagueError
    if not isinstance(p.position, str) or (p.position and p.position not in RM.MADDEN):
        raise LeagueError("player %d has the position %r" % (p.id, p.position))
    if not isinstance(p.number, str) or not (p.number == "-" or (p.number.isdigit() and len(p.number) <= 2)):
        raise LeagueError("player %d has the number %r" % (p.id, p.number))
    if p.roster_list not in ("", RF.SQUAD) + tuple(RF.RESERVE):
        raise LeagueError("player %d is on the list %r" % (p.id, p.roster_list))
    if p.position and p.pos != RM.GROUP[p.position]:
        raise LeagueError("player %d is a %s in the group %r" % (p.id, p.position, p.pos))


def check_charts(league, whole) -> None:
    from .league import LeagueError
    charts = league.chart
    if not isinstance(charts, list) or len(charts) != D.TEAMS:
        raise LeagueError("the depth charts are %r" % (type(charts).__name__,))
    for team, chart in enumerate(charts, start=1):
        if not isinstance(chart, dict):
            raise LeagueError("the depth chart of team %d is %r" % (team, type(chart).__name__))
        for key, ids in chart.items():
            if key not in RM.MADDEN and key not in RM.ROLES:
                raise LeagueError("the depth chart of team %d has %r" % (team, key))
            if not isinstance(ids, list) or len(ids) > 120:
                raise LeagueError("the depth chart of team %d at %s is %r" % (team, key, type(ids).__name__))
            for pid in ids:
                whole(pid, 1, 10 ** 9, "a man of a depth chart")
    if not isinstance(league.roster_version, str) or len(league.roster_version) > 120 or not isinstance(league.roster_offer, str) \
            or len(league.roster_offer) > 120:
        raise LeagueError("the rosters' version is %r" % (league.roster_version,))


def check_teams(league, waiting) -> None:
    """SR.5: every active man of a team (the draft's rookies apart) is in its chart exactly once, at his own position; the roles hold men of the team; no
    team carries more than the camp's limit (FR_CAMP_MAX; the cut brings it to 53)."""
    from .league import LeagueError
    members: dict = {}
    for p in league.players.values():
        if p.status in ON_ROSTER and p.id not in waiting:
            if isinstance(p.team, bool) or not isinstance(p.team, int) or not 1 <= p.team <= D.TEAMS:
                raise LeagueError("active player %d has the team %r" % (p.id, p.team))
            members.setdefault(p.team, {})[p.id] = p.position
    for team in range(1, D.TEAMS + 1):
        chart = league.chart[team - 1]
        positions = members.get(team, {})
        problems = RM.check_chart({k: v for k, v in chart.items() if k in RM.MADDEN}, positions)
        if problems:
            raise LeagueError("the depth chart of team %d: %s" % (team, problems[0]))
        for role in RM.ROLES:
            for pid in chart.get(role, ()):
                if pid not in positions:
                    raise LeagueError("the %s of team %d is player %d, who is not on the team" % (role, team, pid))
        if len(positions) > T.FR_CAMP_MAX:
            raise LeagueError("team %d has %d players on its roster" % (team, len(positions)))


# ----- who is on a team -----

def waiting_ids(league) -> set:
    """The draft's rookies and the undrafted in camp, who wait outside the chart for the cut (stages 4 and 5)."""
    data = league.draft
    if not isinstance(data, dict):
        return set()
    out = set()
    for key in ("picks", "undrafted"):
        rows = data.get(key)
        for row in rows if isinstance(rows, list) else ():
            if isinstance(row, list) and len(row) == 3 and isinstance(row[2], int):
                out.add(row[2])
    return out


def members(league, team: int, waiting=None) -> list:
    """The men of the team's active roster (the draft's rookies apart), by player ID (the players' table is kept in ID order: new IDs are added at its
    end and a read file lists them sorted)."""
    waiting = waiting_ids(league) if waiting is None else waiting
    return [p for p in league.players.values() if p.team == team and p.status == "active" and p.id not in waiting]


def roster_count(league, team: int, waiting=None) -> int:
    return len(members(league, team, waiting))


def room(league, team: int) -> int:
    """How many more men the team's 53 takes now (the draft's rookies apart: the cut decides them)."""
    return max(0, D.ROSTER_MAX - roster_count(league, team))


def family_count(league, team: int, group: str, waiting=None) -> int:
    return sum(1 for p in members(league, team, waiting) if p.pos == group)


def counts_by_group(men) -> dict:
    out: dict = {}
    for p in men:
        out[p.pos] = out.get(p.pos, 0) + 1
    return out


def short_groups(league, team: int, gone=(), come=(), waiting=None) -> list:
    """The groups the team would hold fewer of than the family minimums (T.FR_FAMILY_MIN) once `gone` leave and `come` join; [] when none."""
    gone_ids = {p.id for p in gone}
    men = [p for p in members(league, team, waiting) if p.id not in gone_ids] + list(come)
    have = counts_by_group(men)
    return [group for group, least in T.FR_FAMILY_MIN.items() if have.get(group, 0) < least]


def breaks_minimum(league, team: int, gone=(), come=(), waiting=None) -> bool:
    """A move that leaves the team short of a family minimum it holds now (a team already short is not made shorter)."""
    before = counts_by_group(members(league, team, waiting))
    gone_ids = {p.id for p in gone}
    after = counts_by_group([p for p in members(league, team, waiting) if p.id not in gone_ids] + list(come))
    return any(after.get(group, 0) < least and after.get(group, 0) < before.get(group, 0) for group, least in T.FR_FAMILY_MIN.items())


# ----- the chart and the view -----

def _blank_chart() -> dict:
    chart = {position: [] for position in RM.MADDEN}
    chart.update({role: [] for role in RM.ROLES})
    return chart


def order_position(league, team: int, position: str, ids: list, new=frozenset(), strict: bool = False) -> list:
    """The staff's order of a position, slot by slot from the top (D-170): the man the chart's order puts in a slot (the real order of rosters.txt, then
    the staff's earlier choices) keeps it unless a man below him is at least FR_DEPTH_HOLD rating points better, and then the best such man takes it
    (the ratings are the game's own, so a point or two never takes a real starter's job); a man in `new` (he joined the chart now: signed, traded,
    back from a list) needs FR_DEPTH_HOLD_NEW points, as a staff starts the clearly better man it brought in; `strict` (the staff's full order, F9's
    reset) puts the best rating first, the chart's order among equals; on the player's own team the men he put first (his order of
    the position, NX-D3, NX-L11) keep their places at the top."""
    players = league.players
    index = {pid: n for n, pid in enumerate(ids)}
    first: list = []
    if team == league.team:
        for pid in (league.depth or {}).get("order", {}).get(position, ()):
            if pid in index and pid not in first:
                first.append(pid)
    chosen = set(first)
    hold = T.FR_DEPTH_HOLD.get(position, T.FR_DEPTH_HOLD["*"])
    if strict:
        return first + sorted((pid for pid in ids if pid not in chosen), key=lambda pid: (-players[pid].rating, index[pid]))
    left = [pid for pid in ids if pid not in chosen]          # the chart's order
    rest: list = []
    while left:                                               # slot by slot from the top: the man there keeps it unless a man below is clearly better
        keeper = left[0]
        floor = players[keeper].rating
        better = [pid for pid in left[1:] if players[pid].rating >= floor + (T.FR_DEPTH_HOLD_NEW if pid in new else hold)]
        if keeper in new:                                     # a newcomer at the top of the order holds nothing yet: the best man of the rest takes it
            better = [pid for pid in left[1:] if players[pid].rating > floor]
        take = max(better, key=lambda pid: (players[pid].rating, -left.index(pid))) if better else keeper
        rest.append(take)
        left.remove(take)
    return first + rest


def clean_chart(league, team: int, waiting=None) -> dict:
    """The team's chart with every man of its active roster once at his own position (a man not there yet joins the end of his position), each position
    in the staff's order, the roles kept to the men still on the team."""
    men = members(league, team, waiting)
    position_of = {p.id: p.position for p in men}
    old = league.chart[team - 1] if isinstance(league.chart, list) and len(league.chart) == D.TEAMS and isinstance(league.chart[team - 1], dict) else {}
    chart = _blank_chart()
    for position in RM.MADDEN:
        for pid in old.get(position, ()):
            if position_of.get(pid) == position and pid not in chart[position]:
                chart[position].append(pid)
    present = {pid for position in RM.MADDEN for pid in chart[position]}
    new = set()
    for p in men:
        if p.id not in present:
            if p.position not in RM.MADDEN:
                give_positions(league)
            chart[p.position].append(p.id)
            new.add(p.id)
    for position in RM.MADDEN:
        chart[position] = order_position(league, team, position, chart[position], new)
    for role in RM.ROLES:
        seen: list = []
        for pid in old.get(role, ()):
            if pid in position_of and pid not in seen:
                seen.append(pid)
        chart[role] = seen
    if team == league.team:
        _drop_left(league, position_of, chart, old)
    if not isinstance(league.chart, list) or len(league.chart) != D.TEAMS:
        league.chart = [{} for _ in range(D.TEAMS)]
    league.chart[team - 1] = chart
    return chart


def _drop_left(league, position_of: dict, chart: dict, old: dict) -> None:
    """SR.6 (design 21.13): a man the player chose who is no longer on the team (traded, released, retired, a new roster) leaves his order; when he was a
    starter (one of the first STARTERS of the position, or the first returner) the loss is kept in `depth["dropped"]` as [id, position, slot] and told
    once by the lineup and the roster (`told_dropped`)."""
    depth = league.depth if isinstance(league.depth, dict) else None
    if depth is None:
        return
    order = depth.get("order")
    if not isinstance(order, dict):
        return
    for key in list(order):
        ids = order[key]
        if not isinstance(ids, list):
            continue
        starters = RM.STARTERS.get(key, 1) if key in RM.MADDEN else 1
        for slot, pid in enumerate(ids):
            if pid in position_of or slot >= starters:
                continue
            row = [pid, key, slot]
            kept = depth.setdefault("dropped", [])
            if row not in kept and len(kept) < 200:
                kept.append(row)
        order[key] = [pid for pid in ids if pid in position_of]
        if not order[key]:
            del order[key]


def told_dropped(league) -> list:
    """SR.6: [(player id, key, slot, the man who starts there now or None)] of the starters the player chose who left, each once; the record is cleared.
    The man is the one on the chart at that slot now (a position) or the first of the role."""
    depth = league.depth if isinstance(league.depth, dict) else {}
    rows = depth.pop("dropped", []) if isinstance(depth, dict) else []
    chart = league.chart[league.team - 1] if isinstance(league.chart, list) and len(league.chart) == D.TEAMS else {}
    out = []
    for pid, key, slot in rows:
        ids = chart.get(key, []) if isinstance(chart, dict) else []
        out.append((pid, key, slot, ids[slot] if slot < len(ids) else None))
    return out


def squad_chart(league, team: int) -> dict:
    squad: dict = {}
    for p in sorted((p for p in league.players.values() if p.status == "practice" and p.team == team), key=lambda p: (-p.rating, p.id)):
        squad.setdefault(p.position, []).append(p.id)
    return squad


def chart_view(league, team: int, fit=None):
    """The view of the team's chart (roster_model.View of player IDs), one man one place."""
    chart = league.chart[team - 1]
    positions = {pos: list(chart.get(pos, ())) for pos in RM.MADDEN}
    roles = {role: list(chart.get(role, ())) for role in RM.ROLES}
    return RM.make_view(positions, roles, fit=fit, squad=squad_chart(league, team), distinct=True)


def refresh_view(league, team: int, waiting=None) -> None:
    """The team's chart cleaned and ordered, then its 34 places made from it (design 21.4, 21.6): the view's men take the places (`Player.place`), every
    other man of the active roster has none. A squad kicker or punter the view needs is signed to the 53 (21.7 (7)). Changes no draw."""
    waiting = waiting_ids(league) if waiting is None else waiting
    clean_chart(league, team, waiting)
    view = chart_view(league, team)
    if view.elevated:
        from . import contracts as CT
        for pid in view.elevated:
            man = league.players[pid]
            man.status, man.roster_list, man.place = "active", "", -1
            CT.sign(man, CT.min_salary(man.seasons), 1)
            league.practice["elevations"].pop(str(pid), None)
            debuglog.event("franchise", "must_have_promoted", team=team, player=pid, position=man.position)     # rule 0.15 (design 21.11)
        clean_chart(league, team, waiting)
        view = chart_view(league, team)
    if not isinstance(league.rosters, list) or len(league.rosters) != D.TEAMS:
        league.rosters = [[0] * D.PLACE_COUNT for _ in range(D.TEAMS)]
    roster = [0] * D.PLACE_COUNT
    for p in members(league, team, waiting):
        p.place = -1
    for index, pid in enumerate(view.places):
        if pid:
            roster[index] = pid
            league.players[pid].place = index
    league.rosters[team - 1] = roster


def refresh_all(league) -> None:
    waiting = waiting_ids(league)
    for team in range(1, D.TEAMS + 1):
        refresh_view(league, team, waiting)


def update_sum(league, team: int) -> None:
    if len(league.sums) == D.TEAMS:
        league.sums[team - 1] = league.strength_sum(team)


def join(league, team: int, player, refresh: bool = True) -> None:
    """A man joins the team's active roster (a free agent, a squad man promoted, a man traded or tagged away): his team, status and list; he takes his place
    on his position's chart by the staff's order; the view follows."""
    old = player.team if player.status in ON_ROSTER and isinstance(player.team, int) and 1 <= player.team <= D.TEAMS else 0
    if old and player.place >= 0 and isinstance(league.rosters, list) and len(league.rosters) == D.TEAMS:
        league.rosters[old - 1][player.place] = 0
    player.team, player.status, player.roster_list, player.place = team, "active", "", -1
    player.left, player.points = 0, 0
    if not player.position:
        give_positions(league)
    if refresh:
        if old and old != team:
            refresh_view(league, old)                       # a man traded or signed away: his old team's chart and view too
        refresh_view(league, team)


def leave(league, player, status: str, refresh: bool = True) -> None:
    """A man leaves his team's active roster (released, let go, retired, to the practice squad, traded): his new status, no place; the team's chart and view
    follow. The caller sets his team and his contract."""
    team = player.team
    if 1 <= team <= D.TEAMS and player.place >= 0 and isinstance(league.rosters, list) and len(league.rosters) == D.TEAMS:
        league.rosters[team - 1][player.place] = 0
    player.status, player.place = status, -1
    if refresh and 1 <= team <= D.TEAMS:
        refresh_view(league, team)


def starters_first(league, teams=None) -> int:
    """A new franchise (no draw): in each position of each team the best drawn rating goes to the first man of the chart, the next to the next man (the
    rating, the peak and the potential move together), so the staff's order is the real chart's. Returns how many positions changed."""
    moved = 0
    for team in teams or range(1, D.TEAMS + 1):
        chart = league.chart[team - 1]
        for position in RM.MADDEN:
            men = [league.players[pid] for pid in chart.get(position, ())]
            values = sorted(((p.rating, p.peak, p.potential) for p in men), key=lambda v: -v[0])
            if [p.rating for p in men] == [v[0] for v in values]:
                continue
            for man, (rating, peak, potential) in zip(men, values):
                man.rating, man.peak, man.potential = rating, max(peak, rating), potential
            moved += 1
    return moved


# ----- the cut's last resort and the reserve lists (design 21.3, 21.7 (1), Q-079) -----

SMALL_FAMILIES = ("QB", "K", "P", "LS")         # the families of one starter: the fill's rookie is rated as for a small group (FR_FILL_RATING_SMALL)


def fill_needs(league, rnd, surnames: list) -> list:
    """After the cut: a family a team still holds fewer of than its minimum (T.FR_FAMILY_MIN) gets an undrafted rookie for each man missing, the
    position of the family the team is shortest of against the league's mix, in team order and the families' order, the name, the rating and the
    potential drawn as the old fill drew them (a name `rnd(len(surnames))` again while in use, the rating base + `below(span)`, the potential
    `below(100)`), on the minimum for FR_FILL_YEARS. The cut kept room for them (draft.keep_plan). Returns the men made."""
    from . import first_names as FN
    from .draft import free_number
    from .league import Player, draw_name
    used = FN.name_keys(league.league_id, (p.name for p in league.players.values() if p.status in ("active", "practice")))
    high, average = T.FR_ROOKIE_POTENTIAL_SHARES
    made: list = []
    for team in range(1, D.TEAMS + 1):
        men = members(league, team)
        have = counts_by_group(men)
        positions = team_counts(league, team)
        for group in D.GROUPS:
            while have.get(group, 0) < T.FR_FAMILY_MIN[group]:
                position = RM.convert_word(group, positions) or RM.WORD_POSITIONS[group][0]
                name = draw_name(rnd, surnames, used)
                used.add(name)
                base, span = T.FR_FILL_RATING_SMALL if group in SMALL_FAMILIES else T.FR_FILL_RATING
                rating = max(D.RATING_MIN, min(D.RATING_MAX, base + rnd.below(span)))
                roll = rnd.below(100)
                potential = "high" if roll < high else "average" if roll < average else "low"
                player = Player(league.next_id, FN.full_name(league.league_id, name), group, rating, potential, D.AGE_MIN + 1, 0, rating, None, 0,
                                "active", 0, team, -1, T.FR_MIN_SALARY, T.FR_FILL_YEARS, position=position,
                                number=free_number(league, team, position))
                league.players[player.id] = player
                league.next_id += 1
                made.append(player)
                have[group] = have.get(group, 0) + 1
                positions[position] = positions.get(position, 0) + 1
        refresh_view(league, team)
    if made:
        debuglog.event("franchise", "cut_filled", season=league.season, made=len(made))               # rule 0.15
    return made


def return_lists(league) -> int:
    """Q-079 (accepted default, design 21.12): at the roster cut every man of a team's real reserve list (injured reserve, PUP, NFI, suspended...) comes back
    to its roster, before the cut decides, on the market price (his own contract ran with the list). Returns how many came back."""
    from . import contracts as CT
    back = 0
    for p in sorted(league.players.values(), key=lambda p: p.id):
        if p.status == "list" and 1 <= p.team <= D.TEAMS:
            p.status, p.roster_list, p.place = "active", "", -1
            if not CT.running(p):
                CT.sign(p, *CT.market_contract(p))
            back += 1
    if back:
        refresh_all(league)
        debuglog.event("franchise", "reserve_lists_returned", season=league.season, players=back)       # rule 0.15
    return back


# ----- positions -----

def team_counts(league, team: int) -> dict:
    have: dict = {}
    for p in league.players.values():
        if p.team == team and p.position and p.status in ON_ROSTER:
            have[p.position] = have.get(p.position, 0) + 1
    return have


def give_positions(league, real=None) -> int:
    """Every man without a real position gets one: the conversion table (roster_model.convert_word) against his team's mix, in player ID order. His
    group word follows his position (SR.5: `pos` is his family's word, never RET) and his list his status. Returns how many got a position."""
    counts: dict = {}
    given = 0
    for p in sorted(league.players.values(), key=lambda p: p.id):
        if p.status == "practice":
            p.roster_list = RF.SQUAD
        elif p.status != "list":
            p.roster_list = ""
        if not p.position:
            team = p.team if p.status in ON_ROSTER + ("practice", "list", "reserve") else 0
            if team not in counts:
                counts[team] = team_counts(league, team) if team else {}
            p.position = RM.convert_word(p.pos, counts[team]) or RM.WORD_POSITIONS.get(p.pos, ("WR",))[0]
            if team:
                counts[team][p.position] = counts[team].get(p.position, 0) + 1
            given += 1
        p.pos = RM.GROUP[p.position]
    return given


def group_of(position: str) -> str:
    return RM.GROUP.get(position, "")


# ----- the player's choice of who starts (NX-L11) -----

def choose_starter(league, position: str, pid: int, slot: int = 0) -> list:
    """NX-L11 (D-160, design 21.13): the player makes `pid` the starter at `position` of his own team (`slot` 1 for the second of the three receivers,
    two tackles or two corners). He must be a man of the team's active roster whose position is that one or the other side or role of its family (a man
    moved takes the new position and keeps his family); for "KR" or "PR" any man of the active roster. The man who was there takes his old place on the
    chart. His order is kept (`depth["order"]`, the men he put first) and the places follow at once. Returns the position's new order (IDs)."""
    from .league import LeagueError
    team = league.team
    man = league.players.get(pid)
    if man is None or man.team != team or man.status not in ON_ROSTER or pid in waiting_ids(league):
        raise LeagueError("player %r is not on the active roster of the player's team" % (pid,))
    chart = clean_chart(league, team)
    orders = league.depth.setdefault("order", {})
    if position in RM.ROLES:
        if man.position in RM.RETURN_NEVER:
            raise LeagueError("a %s cannot return kicks" % man.position)
        chart[position] = RM.put_first(chart[position], pid, slot)
        orders[position] = list(chart[position][:slot + 1])         # SR.6: his choice is kept, so a loss is told (_drop_left)
    else:
        if position not in RM.MADDEN or not RM.may_start_at(position, man.position):
            raise LeagueError("a %s cannot start at %s" % (man.position, position))
        if man.position != position:
            chart[man.position] = [i for i in chart[man.position] if i != pid]
            orders[man.position] = [i for i in orders.get(man.position, ()) if i != pid]
            man.position = position
            man.pos = RM.GROUP[position]
        kept = len([i for i in orders.get(position, ()) if i in chart[position]])
        chart[position] = RM.put_first(chart[position], pid, slot)
        orders[position] = list(chart[position][:max(slot + 1, kept)])    # the men he set, down to the slot he chose, keep their places
    refresh_view(league, team)
    update_sum(league, team)
    debuglog.event("franchise", "starter_chosen", team=team, position=position, player=pid, slot=slot, mode="franchise")   # rule 0.15
    return list(league.chart[team - 1][position])


# ----- the men of the file -----

def _mix(*parts) -> int:
    from .signings import _mix as mix
    return mix(*parts)


def bench_rating(league, team: int, group: str, name: str, weakest: dict, previous: dict) -> int:
    """D-149's bench rule (no draw): the first man of a group 1 to 4 under the weakest man of its places, each next one 1 or 2 lower; the line and the
    snapper FR_RESERVE_RATING."""
    base, span = T.FR_RESERVE_RATING
    h = _mix(league.league_id, "bench", team, name)
    if group not in previous:
        rating = weakest[group] - 1 - h % 4 if group in weakest else base + h % span
    else:
        rating = previous[group] - 1 - (h >> 4) % 2
    rating = max(D.RATING_MIN, min(D.RATING_MAX, rating))
    previous[group] = rating
    return rating


def bench_age(league, team: int, name: str) -> tuple:
    h = _mix(league.league_id, "bench", team, name)
    age_base, age_span = T.FR_RESERVE_AGE
    age = max(D.AGE_MIN, min(D.AGE_MAX, age_base + (h >> 8) % age_span))
    if age <= 25:
        potential = "high" if (h >> 16) % 5 == 0 else "average"
    else:
        potential = "average" if (h >> 16) % 2 else "low"
    return age, potential


def real_age(man, age: int, seasons: int) -> tuple:
    """SR.7 (Q-078, D-167): (age, seasons) of a man of rosters.txt: his real age (within the game's AGE_MIN to AGE_MAX) and his real NFL seasons when the
    file gives them, else the `age` and `seasons` the game made (a draw or the hash). No draw either way."""
    if getattr(man, "age", None) is None:
        return age, seasons
    age = max(D.AGE_MIN, min(D.AGE_MAX, man.age))
    if getattr(man, "seasons", None) is not None:
        seasons = man.seasons
    return age, max(0, min(seasons, age - 21))


def cap_squad_veterans(men: list) -> None:
    """SR.7: a real practice squad has at most six veterans by ACCRUED seasons, which the data does not give (calendar seasons count up to ten a squad):
    the six most experienced men keep their seasons, the others count as at most two (practice.VETERAN_SEASONS - 1). No draw."""
    from . import practice
    ordered = sorted(men, key=lambda p: -p.seasons)
    for p in ordered[practice.VETERANS:]:
        p.seasons = min(p.seasons, practice.VETERAN_SEASONS - 1)


def file_teams(real) -> dict:
    """{team: roster_file.Team} of a layout-2 RealNames (the spoken names), or {} when the names are not layout 2."""
    if real is None or not hasattr(real, "is_layout2") or not all(real.is_layout2(t) for t in range(1, D.TEAMS + 1)):
        return {}
    out = {}
    for team in range(1, D.TEAMS + 1):
        lines = real.rosters[team - 1]
        men = [RF.Man(p.madden or RM.WORD_POSITIONS.get(p.pos, ("WR",))[0], p.number, real.spoken(p.name), p.status if p.squad else "",
                      getattr(p, "age", None), getattr(p, "seasons", None))
               for p in lines if p.pos != "RET"]
        men += [RF.Man(p.madden or RM.WORD_POSITIONS.get(p.pos, ("WR",))[0], p.number, real.spoken(p.name), p.status or "IR",
                       getattr(p, "age", None), getattr(p, "seasons", None))
                for p in real.reserve(team)]
        given = real.roles[team - 1] if getattr(real, "roles", None) and isinstance(real.roles[team - 1], dict) and real.roles[team - 1] else None
        if given:
            roles = {role: [real.spoken(n) for n in given.get(role, ())] for role in RF.ROLES}
        else:
            roles = {"KR": [real.spoken(p.name) for p in lines if p.pos == "RET" and not p.squad], "PR": []}
        out[team] = RF.Team(men, roles)
    return out


def make_real(league, real, drawn_team_order: list) -> int:
    """NX-L4 (design 21.5): the new league's drawn places (made in `drawn_team_order`, the draws of 0.16) become the real teams of rosters.txt. Returns the
    number of real men in the league, or 0 when `real` is not a layout-2 file (the caller keeps the older names)."""
    from . import contracts as CT
    from . import practice
    from .league import Player
    teams = file_teams(real)
    if not teams:
        return 0
    total = 0
    for team in range(1, D.TEAMS + 1):
        file_team = teams[team]
        drawn = [league.players[pid] for pid in league.rosters[team - 1]]
        active = file_team.active()
        keys = list(range(len(active)))                      # the view works on the men's index in the file's active list
        chart = RM.ordered_positions(keys, lambda k: active[k].pos)
        by_name = {m.name.casefold(): k for k, m in enumerate(active)}
        roles = {role: [by_name[n.casefold()] for n in file_team.roles.get(role, ()) if n.casefold() in by_name] for role in RF.ROLES}
        squad_men = file_team.squad()
        squad_keys = [("PS", i) for i in range(len(squad_men))]
        squad_chart = RM.ordered_positions(squad_keys, lambda k: squad_men[k[1]].pos)
        view = RM.make_view(chart, roles, squad=squad_chart, distinct=True)
        ids_of: dict = {}
        roster = league.rosters[team - 1]
        for index, key in enumerate(view.places):
            player = drawn[index]
            if key is None:
                del league.players[player.id]                # an empty back place: its draws are made and dropped
                roster[index] = 0
                continue
            man = active[key] if not isinstance(key, tuple) else squad_men[key[1]]
            player.name, player.position, player.number, player.roster_list = man.name, man.pos, man.number, ""
            player.pos = group_of(man.pos)
            player.age, player.seasons = real_age(man, player.age, player.seasons)       # SR.7: the place's drawn rating and potential, his real age
            ids_of[key] = player.id
        weakest: dict = {}
        for pid in roster:
            if pid:
                p = league.players[pid]
                weakest[p.pos] = min(weakest.get(p.pos, D.RATING_MAX + 1), p.rating)
        previous: dict = {}

        def join_file(man, status: str, roster_list: str) -> "Player":
            group = group_of(man.pos)
            if status == "practice":
                h = _mix(league.league_id, "real practice squad", team, man.name)
                base, span = T.FR_PRACTICE_RATING
                seasons = (h >> 8) % 2
                age, rating, potential = 22 + seasons + (h >> 12) % 3, max(D.RATING_MIN, min(D.RATING_MAX, base + h % span)), "average"
            else:
                rating = bench_rating(league, team, group, man.name, weakest, previous)
                age, potential = bench_age(league, team, man.name)
                seasons = max(0, age - 22)
            age, seasons = real_age(man, age, seasons)                                    # SR.7 (D-167)
            player = Player(league.next_id, man.name, group, rating, potential, age, seasons, rating, None, 0, status, 0, team, -1,
                            position=man.pos, number=man.number, roster_list=roster_list)
            if status == "active":
                CT.sign(player, *CT.initial_contract(player))
            elif status == "practice":
                player.salary, player.years = practice.PRACTICE_SALARY, 1
            league.players[player.id] = player
            league.next_id += 1
            return player

        for key, man in enumerate(active):
            if key not in ids_of:
                ids_of[key] = join_file(man, "active", "").id
        squad_players = []
        for i, man in enumerate(squad_men):
            if ("PS", i) not in ids_of:
                squad_players.append(join_file(man, "practice", RF.SQUAD))
        cap_squad_veterans(squad_players)
        for man in file_team.reserves():
            join_file(man, "list", man.status)
        chart_ids = {position: [ids_of[k] for k in chart[position]] for position in RM.MADDEN}
        for k in view.elevated:                              # the squad's kicker signed to the 53 heads his position's chart
            p = league.players[ids_of[k]]
            chart_ids[p.position] = [p.id] + chart_ids[p.position]
        for role in RF.ROLES:
            chart_ids[role] = [ids_of[k] for k in roles[role]]
        league.chart[team - 1] = chart_ids
        total += len(active) + len(squad_men) + len(file_team.reserves())
        if view.empty or view.covered or view.elevated:
            debuglog.event("franchise", "roster_view", logging.DEBUG, team=team, empty=view.empty, covered=sorted(view.covered.items()),
                           elevated=len(view.elevated))      # design 21.11 (rule 0.15)
    league.roster_version = getattr(real, "roster_version", "") or getattr(real, "version", "") or ""
    league.practice["season"] = league.season
    league.reserves_on = True
    starters_first(league)                                   # each position's best drawn rating to its real starter (no draw)
    debuglog.event("franchise", "real_rosters_made", men=total, version=league.roster_version)       # rule 0.15
    return total


# ----- an older file: the places and the bench become the chart (format 18 and older) -----

def legacy_check(league, whole, waiting) -> None:
    """The whole-file check of an older file's stored places and bench (formats 2 to 18), before they become the chart: a place holds an active man of
    the team at that place and of a group the place may hold; every active man is placed or waits for the cut; a bench man has a team and no place."""
    from .league import LeagueError
    if not isinstance(league.rosters, list) or len(league.rosters) != D.TEAMS:
        raise LeagueError("the league has %r rosters" % (len(league.rosters) if isinstance(league.rosters, list) else None))
    placed: set = set()
    for team, roster in enumerate(league.rosters, start=1):
        if not isinstance(roster, list) or len(roster) != D.PLACE_COUNT:
            raise LeagueError("team %d has a roster of %r" % (team, len(roster) if isinstance(roster, list) else None))
        for index, pid in enumerate(roster):
            whole(pid, 0, 10 ** 9, "a place of team %d" % team)
            if pid == 0:
                continue
            player = league.players.get(pid)
            if player is None or player.status != "active" or player.team != team or player.place != index:
                raise LeagueError("place %d of team %d holds player %d, who is not active there" % (index, team, pid))
            if pid in placed:
                raise LeagueError("player %d is in two places" % pid)
            group = D.POSITION_OF_PLACE[index]
            if player.pos != group and player.pos not in D.PLACE_COVERS.get(group, ()):
                raise LeagueError("player %d plays %s in a %s place" % (pid, player.pos, group))
            placed.add(pid)
    counts = [0] * D.TEAMS
    for pid, player in league.players.items():
        if (player.status == "active") != (pid in placed or pid in waiting):
            raise LeagueError("player %d is %s but %s" % (pid, player.status, "placed" if pid in placed else "not placed"))
        if player.status == "reserve":
            if isinstance(player.team, bool) or not isinstance(player.team, int) or not 1 <= player.team <= D.TEAMS or player.place != -1:
                raise LeagueError("bench player %d has team %r and place %r" % (player.id, player.team, player.place))
            counts[player.team - 1] += 1
    for team in range(1, D.TEAMS + 1):
        filled = sum(1 for pid in league.rosters[team - 1] if pid)
        if counts[team - 1] + filled > D.ROSTER_MAX + D.GAME_DAY_EXTRA:
            raise LeagueError("team %d has %d players on its 53" % (team, counts[team - 1] + filled))


def from_places(league, version: int) -> None:
    """A league of format 18 or older, read before its first check: its stored places and bench are checked as they were written (`legacy_check`), then
    the bench men are active men, every man has a position and his family's group word, the chart is made from the places (the men of the places first in
    place order, then the earlier chart's order, then the rating) unless the file has one (format 18), and the player's order by group becomes his order by
    position. No draw."""
    from .league import LeagueError

    def whole(value, low, high, what):
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise LeagueError("%s is %r" % (what, value))

    if not isinstance(league.players, dict):
        raise LeagueError("the players are not a table")
    waiting = waiting_ids(league)
    legacy_check(league, whole, waiting)
    for p in league.players.values():
        if p.status == "reserve":
            p.status = "active"
    places = {pid: (team, index) for team, roster in enumerate(league.rosters, start=1) for index, pid in enumerate(roster) if pid}
    give_positions(league)
    charts = league.chart if version >= 18 and isinstance(league.chart, list) and len(league.chart) == D.TEAMS else None
    out = []
    for team in range(1, D.TEAMS + 1):
        previous = charts[team - 1] if charts is not None and isinstance(charts[team - 1], dict) else {}
        men = [p for p in league.players.values() if p.team == team and p.status in ON_ROSTER and p.id not in waiting]
        chart = _blank_chart()
        for position in RM.MADDEN:
            before = {pid: n for n, pid in enumerate(previous.get(position, ()) if isinstance(previous.get(position), list) else ())}
            group = [p for p in men if p.position == position]
            if before:
                group.sort(key=lambda p: (before.get(p.id, 10 ** 6), -p.rating, p.id))
            else:
                group.sort(key=lambda p: (0, places[p.id][1], 0, 0) if p.id in places and places[p.id][1] not in D.PLACES_OF["RET"]
                           else (1, 10 ** 6, -p.rating, p.id))
            chart[position] = [p.id for p in group]
        on_team = {p.id for p in men}
        for role in RM.ROLES:
            old = previous.get(role, ()) if isinstance(previous.get(role), list) else ()
            chart[role] = [pid for pid in old if pid in on_team]
        for index in D.PLACES_OF["RET"] if version < 18 else ():     # the older file's returners keep returning (a file of 18 has its roles)
            pid = league.rosters[team - 1][index] if isinstance(league.rosters[team - 1], list) else 0
            if pid and pid in on_team and pid not in chart["KR"] and pid not in chart["PR"]:
                chart["KR"].append(pid)
        out.append(chart)
    league.chart = out
    migrate_depth(league)


def migrate_depth(league) -> None:
    """The player's order by group (formats 16 to 18: RB, WR, DL, LB, CB, S, RET, K, P) becomes his order by position (each man under his own
    position; RET under KR)."""
    depth = league.depth if isinstance(league.depth, dict) else {}
    order = depth.get("order") if isinstance(depth.get("order"), dict) else {}
    if all(key in RM.MADDEN or key in RM.ROLES for key in order):
        return
    new: dict = {}
    for key, ids in order.items():
        if not isinstance(ids, list):
            continue
        for pid in ids:
            p = league.players.get(pid) if isinstance(pid, int) else None
            if p is None:
                continue
            target = "KR" if key == "RET" else (key if key in RM.MADDEN or key in RM.ROLES else p.position)
            if target and pid not in new.setdefault(target, []):
                new[target].append(pid)
    depth["order"] = {key: ids for key, ids in new.items() if ids}
    league.depth = depth


# ----- the conversion of an older league (NX-L7, design 21.6) -----

def convert(league, real) -> dict:
    """Once, when a league of format 17 or older is opened: every man his real position and number by his name in the rosters (his own team's line
    first), a league without benches (format 16 or older) its teams' missing real men while a team has fewer than 53 (the quarterbacks first, then the
    kicker, the punter and the snapper, then the file's order; men the league has anywhere are never moved), then the charts. No draw. Returns (and keeps
    in `league.converted`) what was done."""
    from . import contracts as CT
    from .league import Player
    teams = file_teams(real)
    named = 0
    if teams:
        index: dict = {}
        for team, file_team in teams.items():
            for man in file_team.men:
                index.setdefault(man.name.casefold(), []).append((team, man))
        for p in sorted(league.players.values(), key=lambda p: p.id):
            rows = index.get(p.name.casefold())
            if not rows:
                continue
            team, man = next(((t, m) for t, m in rows if t == p.team), rows[0])
            if p.position != man.pos or p.number != man.number:
                named += 1
            p.position, p.number = man.pos, man.number
    give_positions(league)
    joined = 0
    if teams and league.loaded_format and league.loaded_format <= 16:
        known = {p.name.casefold() for p in league.players.values()}
        order = {"QB": 0, "K": 1, "P": 2, "LS": 3}
        for team in range(1, D.TEAMS + 1):
            room_left = D.ROSTER_MAX - sum(1 for p in league.players.values() if p.team == team and p.status in ON_ROSTER)
            weakest: dict = {}
            for p in league.active_of(team):
                if p is not None:
                    weakest[p.pos] = min(weakest.get(p.pos, D.RATING_MAX + 1), p.rating)
            previous: dict = {}
            active = [m for m in teams[team].active() if m.name.casefold() not in known]
            active.sort(key=lambda m: order.get(m.pos, 9))
            for man in active[:max(0, room_left)]:
                group = group_of(man.pos)
                rating = bench_rating(league, team, group, man.name, weakest, previous)
                age, potential = bench_age(league, team, man.name)
                age, seasons = real_age(man, age, max(0, age - 22))                       # SR.7 (D-167): a joining real man's real age
                player = Player(league.next_id, man.name, group, rating, potential, age, seasons, rating, None, 0, "active", 0, team, -1,
                                position=man.pos, number=man.number)
                CT.sign(player, *CT.initial_contract(player))
                league.players[player.id] = player
                league.next_id += 1
                known.add(man.name.casefold())
                joined += 1
    refresh_all(league)
    if teams and not league.roster_version:
        league.roster_version = getattr(real, "roster_version", "") or getattr(real, "version", "") or ""
    done = {"from": league.loaded_format, "positions": named, "joined": joined}
    league.converted = done
    debuglog.event("franchise", "league_converted", **done)                                          # rule 0.15
    return done
