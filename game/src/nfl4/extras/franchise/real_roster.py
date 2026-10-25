"""The Franchise's real roster: a new franchise of exactly the men of rosters.txt, the conversion of an older league, the depth charts and the player's
choice of who starts (nfl4 only, rule 0.13; CLAUDE.md 0.30 and 0.32, NX-L3, NX-L4, NX-L5, NX-L7, NX-L11; NFL_FRANCHISE_DESIGN 21.3 to 21.6 and 21.13;
D-159, D-160, D-161). This is inspired by Jim Kitchen.

THE BRIDGE (D-161). SR.4 builds the model and SR.5 moves every Franchise block onto it. Until then a team is still stored as the original's 34 places and a
bench (status "reserve"), because the cut, the draft, signings, trades, injuries and the rest read and write places; the chart is kept in step with them:

* `make_real` (a new franchise): the league's drawn places become the view of each team's real chart (roster_model.make_view, one man one place): the
  drawn rating, potential and age of a place go to the man the view puts there (so the starters get exactly the draws 0.16 gave its places); every other
  active man is on the bench, the squad's men on the practice squad, the reserve lists' men have status "list" (on the team, never in a game). Nothing is
  made up and nobody is left off: an empty back place stays empty (a team with three backs runs with three), a 3-4 team's spare edge men fill its backer
  places, a team with no active kicker signs its squad's kicker to the 53 (a game-day man: GAME_DAY_EXTRA).
* `sync_chart` (every save): each team's chart holds every man of its active roster at his own position, the men of the places first in place order, then
  the others in their earlier chart order, then by rating; the return roles keep their order.
* `refresh_view(team)` (the player's choice of a starter, NX-L11): the team's places are made again from its chart, as a new franchise's were.
* `convert` (a league of format 17 or older, once, when it is opened): every man his real position and number by his name in rosters.txt (else by the
  conversion table), a league without benches (format 16 or older) its teams' missing real men at once, the charts, and `league.converted` for the sentence.

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

ON_ROSTER = ("active", "reserve")


# ----- the shape of the new values -----

def check_player(p) -> None:
    from .league import LeagueError
    if not isinstance(p.position, str) or (p.position and p.position not in RM.MADDEN):
        raise LeagueError("player %d has the position %r" % (p.id, p.position))
    if not isinstance(p.number, str) or not (p.number == "-" or (p.number.isdigit() and len(p.number) <= 2)):
        raise LeagueError("player %d has the number %r" % (p.id, p.number))
    if p.roster_list not in ("", RF.SQUAD) + tuple(RF.RESERVE):
        raise LeagueError("player %d is on the list %r" % (p.id, p.roster_list))


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


# ----- positions -----

def team_counts(league, team: int) -> dict:
    have: dict = {}
    for p in league.players.values():
        if p.team == team and p.position and p.status in ON_ROSTER:
            have[p.position] = have.get(p.position, 0) + 1
    return have


def give_positions(league, real=None) -> int:
    """Every man without a real position gets one: the conversion table (roster_model.convert_word) against his team's mix, in player ID order. His
    list follows his status. Returns how many got a position."""
    counts: dict = {}
    given = 0
    for p in sorted(league.players.values(), key=lambda p: p.id):
        if p.status == "practice":
            p.roster_list = RF.SQUAD
        elif p.status != "list":
            p.roster_list = ""
        if p.position:
            continue
        team = p.team if p.status in ON_ROSTER + ("practice", "list") else 0
        if team not in counts:
            counts[team] = team_counts(league, team) if team else {}
        p.position = RM.convert_word(p.pos, counts[team]) or RM.WORD_POSITIONS.get(p.pos, ("WR",))[0]
        if team:
            counts[team][p.position] = counts[team].get(p.position, 0) + 1
        given += 1
    return given


def group_of(position: str) -> str:
    return RM.GROUP.get(position, "")


# ----- the chart -----

def sync_chart(league) -> None:
    """SR.4's bridge (D-161): each team's chart is made again from its active roster: every man at his own position once, the men of the places first in
    place order, then the others in their earlier chart order, then the best rating first (the lower ID of equals). The roles keep the men still on the
    team in their order, and a man of a return place who is in neither role joins the kick returners."""
    give_positions(league)
    members: dict = {}
    for p in league.players.values():
        if p.status in ON_ROSTER and 1 <= p.team <= D.TEAMS:
            members.setdefault(p.team, []).append(p)
    charts = []
    for team in range(1, D.TEAMS + 1):
        previous = league.chart[team - 1] if isinstance(league.chart, list) and len(league.chart) == D.TEAMS and isinstance(league.chart[team - 1], dict) else {}
        placed = {pid: i for i, pid in enumerate(league.rosters[team - 1]) if pid}
        chart: dict = {}
        for position in RM.MADDEN:
            before = {pid: n for n, pid in enumerate(previous.get(position, ()))}
            men = [p for p in members.get(team, ()) if p.position == position]
            men.sort(key=lambda p: (0, placed[p.id], 0, 0) if p.id in placed and placed[p.id] not in D.PLACES_OF["RET"]
                     else (1, before.get(p.id, 10 ** 6), -p.rating, p.id))
            chart[position] = [p.id for p in men]
        on_team = {p.id for p in members.get(team, ())}
        for role in RM.ROLES:
            chart[role] = [pid for pid in previous.get(role, ()) if pid in on_team]
        for index in D.PLACES_OF["RET"]:
            pid = league.rosters[team - 1][index]
            if pid and pid not in chart["KR"] and pid not in chart["PR"]:
                chart["KR"].append(pid)
        charts.append(chart)
    league.chart = charts


def chart_view(league, team: int, fit=None):
    """The view of the team's chart (roster_model.View of player IDs), one man one place (the bridge)."""
    chart = league.chart[team - 1]
    positions = {pos: list(chart.get(pos, ())) for pos in RM.MADDEN}
    roles = {role: list(chart.get(role, ())) for role in RM.ROLES}
    squad: dict = {}
    for p in sorted((p for p in league.players.values() if p.status == "practice" and p.team == team), key=lambda p: (-p.rating, p.id)):
        squad.setdefault(p.position, []).append(p.id)
    return RM.make_view(positions, roles, fit=fit, squad=squad, distinct=True)


def refresh_view(league, team: int) -> None:
    """The team's 34 places made again from its chart at full health (design 21.6): the view's men take the places, every other man of the active roster
    the bench. A squad kicker the view needs is signed to the 53 (a game-day man). Only in a stage where every place is filled (the season, stages 1, 9
    and 6), never with rookies waiting for the cut."""
    view = chart_view(league, team)
    roster = league.rosters[team - 1]
    for pid in view.elevated:
        man = league.players[pid]
        man.status, man.roster_list = "active", ""
        from . import contracts as CT
        CT.sign(man, *CT.initial_contract(man))
    on_view = set()
    for index, pid in enumerate(view.places):
        roster[index] = pid or 0
        if pid:
            on_view.add(pid)
            man = league.players[pid]
            man.status, man.place = "active", index
    for p in league.players.values():
        if p.team == team and p.status in ON_ROSTER and p.id not in on_view:
            p.status, p.place = "reserve", -1
    if len(league.sums) == D.TEAMS:
        league.sums[team - 1] = league.strength_sum(team)


def choose_starter(league, position: str, pid: int, slot: int = 0) -> list:
    """NX-L11 (D-160, design 21.13): the player makes `pid` the starter at `position` of his own team (`slot` 1 for the second of the three receivers,
    two tackles or two corners). He must be a man of the team's active roster whose position is that one or the other side or role of its family (a man
    moved takes the new position and keeps his family); for "KR" or "PR" any man of the active roster. The man who was there takes his old place on the
    chart. The places follow at once when the league is in a stage of whole places. Returns the position's new order (IDs)."""
    from .league import LeagueError
    team = league.team
    man = league.players.get(pid)
    if man is None or man.team != team or man.status not in ON_ROSTER:
        raise LeagueError("player %r is not on the active roster of the player's team" % (pid,))
    sync_chart(league)
    chart = league.chart[team - 1]
    if position in RM.ROLES:
        chart[position] = RM.put_first(chart[position], pid, slot)
        order = chart[position]
    else:
        if position not in RM.MADDEN or not RM.may_start_at(position, man.position):
            raise LeagueError("a %s cannot start at %s" % (man.position, position))
        if man.position != position:
            chart[man.position] = [i for i in chart[man.position] if i != pid]
            man.position = position
        chart[position] = RM.put_first(chart[position], pid, slot)
        order = chart[position]
    if league.must_be_whole() and not league.draft:
        refresh_view(league, team)
        from . import depth
        for group, places in D.PLACES_OF.items():          # the bridge: the places' order is the player's (aging.place_by_rating keeps it)
            if places and group in depth.GROUPS:
                league.depth.setdefault("order", {})[group] = [league.rosters[team - 1][i] for i in places if league.rosters[team - 1][i]]
    debuglog.event("franchise", "starter_chosen", team=team, position=position, player=pid, slot=slot, mode="franchise")   # rule 0.15
    return list(order)


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


def file_teams(real) -> dict:
    """{team: roster_file.Team} of a layout-2 RealNames (the spoken names), or {} when the names are not layout 2."""
    if real is None or not hasattr(real, "is_layout2") or not all(real.is_layout2(t) for t in range(1, D.TEAMS + 1)):
        return {}
    out = {}
    for team in range(1, D.TEAMS + 1):
        lines = real.rosters[team - 1]
        men = [RF.Man(p.madden or RM.WORD_POSITIONS.get(p.pos, ("WR",))[0], p.number, real.spoken(p.name), p.status if p.squad else "")
               for p in lines if p.pos != "RET"]
        men += [RF.Man(p.madden or RM.WORD_POSITIONS.get(p.pos, ("WR",))[0], p.number, real.spoken(p.name), p.status or "IR")
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
            ids_of[key] = player.id
        weakest: dict = {}
        for pid in roster:
            if pid:
                p = league.players[pid]
                weakest[p.pos] = min(weakest.get(p.pos, D.RATING_MAX + 1), p.rating)
        previous: dict = {}

        def join(man, status: str, roster_list: str) -> "Player":
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
            player = Player(league.next_id, man.name, group, rating, potential, age, seasons, rating, None, 0, status, 0, team, -1,
                            position=man.pos, number=man.number, roster_list=roster_list)
            if status == "reserve":
                CT.sign(player, *CT.initial_contract(player))
            elif status == "practice":
                player.salary, player.years = practice.PRACTICE_SALARY, 1
            league.players[player.id] = player
            league.next_id += 1
            return player

        for key, man in enumerate(active):
            if key not in ids_of:
                ids_of[key] = join(man, "reserve", "").id
        for i, man in enumerate(squad_men):
            if ("PS", i) not in ids_of:
                join(man, "practice", RF.SQUAD)
        for man in file_team.reserves():
            join(man, "list", man.status)
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
    league.roster_version = getattr(real, "version", "") or ""
    league.practice["season"] = league.season
    league.reserves_on = True
    debuglog.event("franchise", "real_rosters_made", men=total, version=league.roster_version)       # rule 0.15
    return total


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
            room = D.ROSTER_MAX - sum(1 for p in league.players.values() if p.team == team and p.status in ON_ROSTER)
            weakest: dict = {}
            for p in league.active_of(team):
                if p is not None:
                    weakest[p.pos] = min(weakest.get(p.pos, D.RATING_MAX + 1), p.rating)
            previous: dict = {}
            active = [m for m in teams[team].active() if m.name.casefold() not in known]
            active.sort(key=lambda m: order.get(m.pos, 9))
            for man in active[:max(0, room)]:
                group = group_of(man.pos)
                rating = bench_rating(league, team, group, man.name, weakest, previous)
                age, potential = bench_age(league, team, man.name)
                player = Player(league.next_id, man.name, group, rating, potential, age, max(0, age - 22), rating, None, 0, "reserve", 0, team, -1,
                                position=man.pos, number=man.number)
                CT.sign(player, *CT.initial_contract(player))
                league.players[player.id] = player
                league.next_id += 1
                known.add(man.name.casefold())
                joined += 1
        if joined:
            league.reserves_on = True
    sync_chart(league)
    if teams and not league.roster_version:
        league.roster_version = getattr(real, "version", "") or ""
    done = {"from": league.loaded_format, "positions": named, "joined": joined}
    league.converted = done
    debuglog.event("franchise", "league_converted", **done)                                          # rule 0.15
    return done
