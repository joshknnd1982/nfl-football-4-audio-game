"""A franchise in progress brought up to newer real rosters: the other 31 teams only, when the player says yes (nfl4 only, rule 0.13; CLAUDE.md 0.32,
NX-L9; NFL_FRANCHISE_DESIGN 21.10 "WHAT IT CHANGES"; SR.6). This is inspired by Jim Kitchen.

A franchise keeps its own league when the game gets newer rosters (its history is the player's), so the newer file is OFFERED once when a league made
from older rosters is opened (rosters_flow.offer). This module is the rules of that offer and of the update, with no speech, no files and NO DRAW:

* `version_of(real)`: the VERSION line of rosters.txt (RealNames.roster_version); `league_version` is a league's own, where the label "season 2026, as of
  2026-10-22" that SR.4 and SR.5 wrote (coaches.txt's line, not the rosters') counts as the rosters the game ships, so no league is offered the very
  rosters it was made from.
* `offer_due(league, real)`: the version to offer, or "": a league of the real rosters older than the game's file whose offer of that file was not
  answered (`roster_offer`). `allowed(league)`: never inside the draft, the roster cut, the market, the re-signing or an open tag (the offer waits).
* `update(league, real, known)`: design 21.10 points 1 to 4. Only the 31 computer teams change; the player's team (`league.team`) and every man of it
  are never touched. Each man of a computer team's lines in the file: already there -> the file's position, number and list; on another computer team ->
  he moves with his contract; on the player's team -> he stays with the player and the computer team does without him; a free agent of the league (free,
  released or retired) -> he signs at the market price; not in the league -> he joins with the bench rule's rating and hashed age
  (real_roster.bench_rating, bench_age) at the market price. A man of a computer team the file does not have on that team: a real man the file has
  nowhere (released in reality) becomes a free agent with no dead money (the league did not choose it); a man the league made (drafted, undrafted, made
  up) stays. Then a team over 53 goes to 53 by the staff's cut rule (draft.keep_plan, no dead money either), a practice squad over its limits sends its
  league-made men first, and the charts are made again: the file's men in the file's order, then the others, which the staff's rule then orders by
  rating (the file's order among equals, as every computer chart is kept since SR.5). Men move only through real_roster.join and leave.
"""
from __future__ import annotations

import logging
import re

from ...data import debuglog
from .. import roster_file as RF
from .. import roster_model as RM
from .. import tuning as T
from . import contracts as CT
from . import data as D
from . import practice
from . import real_roster as RR

log = logging.getLogger("nfl4.extras")

ON_TEAM = ("active", "practice", "list")          # a man of a team: its 53, its practice squad, a reserve list
OFF_TEAM = ("free", "released", "retired")         # a man the league has on no team
_AS_OF = re.compile(r"as of\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


# ----- versions -----

def date_of(version: str) -> str:
    """"2026-10-25" of "season 2026, as of 2026-10-25" (any date of the line when it has no "as of"); "" when it has none."""
    text = version or ""
    found = _AS_OF.search(text) or _DATE.search(text)
    return found.group(1) if found and found.re is _AS_OF else (found.group(0) if found else "")


def spoken_date(version: str) -> str:
    """The date as the voice says it ("October 25, 2026"), or the version's own words when it has no date."""
    date = date_of(version)
    found = _DATE.fullmatch(date) if date else None
    if found and 1 <= int(found.group(2)) <= 12:
        return "%s %d, %s" % (MONTHS[int(found.group(2)) - 1], int(found.group(3)), found.group(1))
    return (version or "").strip()


def newer(candidate: str, current: str) -> bool:
    """`candidate` is newer than `current`: by their dates when both have one, else when they differ (a player's own VERSION line without a date)."""
    a, b = date_of(candidate), date_of(current)
    if a and b:
        return a > b
    return bool((candidate or "").strip()) and (candidate or "").strip() != (current or "").strip()


def version_of(real) -> str:
    """The VERSION of the game's rosters.txt (the player's copy, else the shipped one); "" without real names."""
    if real is None:
        return ""
    return getattr(real, "roster_version", "") or getattr(real, "version", "") or ""


def league_version(league, real) -> str:
    """The league's roster_version, with SR.4's and SR.5's label (coaches.txt's VERSION, `real.version`) read as the rosters the game ships."""
    mine = getattr(league, "roster_version", "") or ""
    if real is not None and mine and mine == getattr(real, "version", None) and mine != version_of(real):
        from .. import real_names
        shipped = real_names.defaults()
        return version_of(shipped) or mine
    return mine


def is_real(real) -> bool:
    """The names are layout 2 (a team is its real roster): the only rosters a league can be brought up to."""
    return real is not None and hasattr(real, "is_layout2") and all(real.is_layout2(t) for t in range(1, D.TEAMS + 1))


def offer_due(league, real) -> str:
    """The rosters version to offer to this league, or "" (no real names, a league not of the real rosters, not older, or answered already)."""
    if league is None or real is None:
        return ""
    current = version_of(real)
    mine = league_version(league, real)
    if not current or not mine or league.roster_offer == current or not newer(current, mine):
        return ""
    return current if is_real(real) else ""


def allowed(league) -> bool:
    """Design 21.10: never during the draft or the cut (nor the market, the re-signing or an open tag, whose records name the men of the teams); in the
    regular season and the play-offs, and in the other stages of an offseason. The caller checks that no game is being played."""
    from .league import OFFSEASON, SEASON
    if league.stage == SEASON:
        return True
    if league.stage != OFFSEASON or league.stage_no in (D.STAGE_DRAFT, D.STAGE_CUT):
        return False
    if league.draft is not None or league.market is not None or league.resign is not None or league.cut_deciding:
        return False
    tags = league.tags if isinstance(league.tags, dict) else {}
    return not tags.get("open") and not tags.get("sheet")


# ----- who is real -----

def known_real_names(real, extra=()) -> frozenset:
    """The casefolded names of the real men the game knows of: the rosters and free agents now in use, the shipped ones, and `extra` (the names of the
    player's earlier rosters kept as copies). A man of a computer team whose name is here and whom the new file has nowhere was released in reality."""
    from .. import real_names
    names = set(n.casefold() for n in extra)
    for source in (real, real_names.defaults()):
        if source is not None and hasattr(source, "real_full_names"):
            names |= source.real_full_names()
    return frozenset(names)


# ----- the update -----

def _pick(candidates, team: int, own: int, claimed: set):
    """The league's man for a file line of `team`: one of that team first, then one of another computer team, then a free one, then the player's."""
    free = [p for p in candidates if p.id not in claimed]
    for test in (lambda p: p.status in ON_TEAM and p.team == team,
                 lambda p: p.status in ON_TEAM and p.team != own,
                 lambda p: p.status in OFF_TEAM,
                 lambda p: p.status in ON_TEAM and p.team == own):
        found = next((p for p in free if test(p)), None)
        if found is not None:
            return found
    return None


def _drop_records(league, player, team: int) -> None:
    """A man who leaves a team's 53 for good or for a list: his injury and the choice made for it end, a stand-in row naming him on his old team goes,
    his elevations are forgotten (practice.release_from_squad's and signings._forget's steps)."""
    league.injuries["hurt"][:] = [row for row in league.injuries["hurt"] if row[0] != player.id]
    chosen = league.injuries.setdefault("chosen", [])
    chosen[:] = [row for row in chosen if player.id not in row[:2]]
    league.injuries["stand_ins"][:] = [row for row in league.injuries["stand_ins"] if not (row[0] == team and row[2] == player.name)]
    league.practice["elevations"].pop(str(player.id), None)


def _release(league, player) -> None:
    """A free agent of this season with no dead money (design 21.10 (3): the league did not choose it)."""
    from . import signings
    team = player.team
    _drop_records(league, player, team)
    CT.leave(player)
    if player.status == "active":
        RR.leave(league, player, "free", refresh=False)
    player.status, player.team, player.place, player.roster_list = "free", 0, -1, ""
    player.left, player.points = league.season, 0
    signings._forget(league, player.id)


def _place(league, team: int, player, man, target: str) -> bool:
    """The league's man takes the file's line of `team`: position, number, list. Returns True when anything of him changed."""
    before = (player.team, player.status, player.position, player.number, player.roster_list)
    old_team, old_status = player.team, player.status
    player.position, player.pos, player.number = man.pos, RM.GROUP[man.pos], man.number
    if target == "active":
        if old_status != "active" or old_team != team:
            if old_status in ("practice", "list"):
                _drop_records(league, player, old_team)
            RR.join(league, team, player, refresh=False)
            if old_status != "active" or not CT.running(player) or player.salary < T.FR_MIN_SALARY:
                CT.sign(player, *CT.market_contract(player))       # a free man, a squad man or a list man: the market price
    else:
        status, roster_list = ("practice", RF.SQUAD) if target == "practice" else ("list", man.status)
        if (old_status, old_team, player.roster_list) != (status, team, roster_list):
            _drop_records(league, player, old_team)
            if old_status == "active":
                RR.leave(league, player, status, refresh=False)
            player.status, player.team, player.place, player.roster_list = status, team, -1, roster_list
            player.left, player.points = 0, 0
            if status == "practice":
                player.salary, player.years = practice.salary_of(player), 1
    return before != (player.team, player.status, player.position, player.number, player.roster_list)


def _new_man(league, team: int, man, target: str, weakest: dict, previous: dict):
    """A real man the league has never had: the bench rule's rating and hashed age (no draw), a squad man the real squads' rule, the market price."""
    from .league import Player
    group = RM.GROUP[man.pos]
    if target == "practice":
        h = RR._mix(league.league_id, "real practice squad", team, man.name)
        base, span = T.FR_PRACTICE_RATING
        seasons = (h >> 8) % 2
        age, rating, potential = 22 + seasons + (h >> 12) % 3, max(D.RATING_MIN, min(D.RATING_MAX, base + h % span)), "average"
    else:
        rating = RR.bench_rating(league, team, group, man.name, weakest, previous)
        age, potential = RR.bench_age(league, team, man.name)
        seasons = max(0, age - 22)
    status, roster_list = {"active": ("active", ""), "practice": ("practice", RF.SQUAD), "list": ("list", man.status)}[target]
    player = Player(league.next_id, man.name, group, rating, potential, age, seasons, rating, None, 0, status, 0, team, -1,
                    position=man.pos, number=man.number, roster_list=roster_list)
    if status == "active":
        CT.sign(player, *CT.market_contract(player))
    elif status == "practice":
        player.salary, player.years = practice.salary_of(player), 1
    league.players[player.id] = player
    league.next_id += 1
    return player


def _trim_squad(league, team: int, file_names: set) -> int:
    """A practice squad over its limits (practice.check: SIZE + 1 men, VETERANS + 1 veterans) lets its men go, the league's own first, the weakest first."""
    gone = 0
    while True:
        squad = practice.squad(league, team)
        veterans = [p for p in squad if practice.veteran(p)]
        if len(squad) <= practice.SIZE + 1 and len(veterans) <= practice.VETERANS + 1:
            return gone
        pool = veterans if len(veterans) > practice.VETERANS + 1 else squad
        man = min(pool, key=lambda p: (p.name.casefold() in file_names, p.rating, -p.id))
        _release(league, man)
        gone += 1


def update(league, real, known=frozenset()) -> dict:
    """Design 21.10 points 1 to 4 (see the module's text). `known`: known_real_names. Returns the counts for the log; n, the sentence's number, is the
    men a computer team has now that it had not before (moved or joined). Raises LeagueError when `real` is not the real rosters."""
    from . import draft as DR
    from .league import LeagueError
    teams = RR.file_teams(real)
    if not teams:
        raise LeagueError("the rosters are not the real rosters (layout 2)")
    own = league.team
    computer = [t for t in range(1, D.TEAMS + 1) if t != own]
    by_name: dict = {}
    for p in sorted(league.players.values(), key=lambda p: p.id):
        by_name.setdefault(p.name.casefold(), []).append(p)
    weakest: dict = {}
    for t in computer:
        weakest[t] = {}
        for p in league.active_of(t):
            if p is not None:
                weakest[t][p.pos] = min(weakest[t].get(p.pos, D.RATING_MAX + 1), p.rating)
    previous = {t: {} for t in computer}
    was_on = {p.id: p.team for p in league.players.values() if p.status in ON_TEAM and p.team in weakest}
    counts = {"moved": 0, "signed": 0, "joined": 0, "changed": 0, "with_you": 0, "released": 0, "cut": 0, "squad_released": 0}
    claimed: set = set()
    placed = {t: [] for t in computer}                       # the file's men of each team, in the file's order
    for t in computer:
        for man in teams[t].men:
            target = "active" if man.status == RF.ACTIVE else "practice" if man.status == RF.SQUAD else "list"
            player = _pick(by_name.get(man.name.casefold(), ()), t, own, claimed)
            if player is None:
                player = _new_man(league, t, man, target, weakest[t], previous[t])
                counts["joined"] += 1
            elif player.status in ON_TEAM and player.team == own:
                claimed.add(player.id)                       # point 2: he stays with the player; this team does without him
                counts["with_you"] += 1
                continue
            else:
                claimed.add(player.id)
                kind = "changed" if player.status in ON_TEAM and player.team == t else "moved" if player.status in ON_TEAM else "signed"
                if _place(league, t, player, man, target) or kind != "changed":
                    counts[kind] += 1
            placed[t].append(player.id)
    file_names = {t: {m.name.casefold() for m in teams[t].men} for t in teams}
    anywhere = set().union(*file_names.values())
    for t in computer:
        mine = set(placed[t])
        for p in sorted(league.players.values(), key=lambda p: p.id):
            if p.team != t or p.status not in ON_TEAM or p.id in mine:
                continue
            name = p.name.casefold()
            if name in anywhere:
                continue                                     # the file has him (on the player's team, or a namesake): he stays where he is
            if p.drafted is None and name in known:
                _release(league, p)                          # point 3: a real man the file has nowhere, released in reality
                counts["released"] += 1
    for t in computer:
        members = RR.members(league, t)
        if len(members) > D.ROSTER_MAX:
            kept = {p.id for p in DR.keep_plan(members)}
            # keep_plan leaves room for the men the offseason's fill would make (a family under its minimum, a lone kicker under the floor); no fill
            # follows here (it draws), so the best men of such a family whom the plan let go stay instead, within the room it left
            for group, least in T.FR_FAMILY_MIN.items():
                have = sum(1 for p in members if p.id in kept and p.pos == group)
                for p in DR.keep_order([q for q in members if q.pos == group and q.id not in kept]):
                    if have >= least or len(kept) >= D.ROSTER_MAX:
                        break
                    kept.add(p.id)
                    have += 1
            for p in members:
                if p.id not in kept:
                    _release(league, p)
                    counts["cut"] += 1
        counts["squad_released"] += _trim_squad(league, t, file_names[t])
        _chart(league, t, placed[t], teams[t])
        RR.refresh_view(league, t)
        RR.update_sum(league, t)
    version = version_of(real)
    league.roster_version = version
    league.roster_offer = version
    # the sentence's number (rule 0.28 (4): what was done): the men a computer team has now that it did not have before, so a man who signed and
    # was cut again by the same update is not counted
    counts["n"] = sum(1 for p in league.players.values() if p.status in ON_TEAM and p.team in weakest and was_on.get(p.id) != p.team)
    debuglog.event("franchise", "league_rosters_updated", logging.INFO, version=version, **counts)        # rule 0.15 (design 21.11)
    return counts


def _chart(league, team: int, placed: list, file_team) -> None:
    """The team's chart before the staff's rule: each position's men of the file in the file's order, then its other men in their earlier order; the
    return roles of the file for the men of the 53."""
    players = league.players
    old = league.chart[team - 1] if isinstance(league.chart[team - 1], dict) else {}
    active = [pid for pid in placed if players[pid].status == "active" and players[pid].team == team]
    chart: dict = {}
    for position in RM.MADDEN:
        first = [pid for pid in active if players[pid].position == position]
        chart[position] = first + [pid for pid in old.get(position, ()) if pid not in first]
    by_name = {players[pid].name.casefold(): pid for pid in active}
    for role in RM.ROLES:
        chart[role] = [by_name[n.casefold()] for n in file_team.roles.get(role, ()) if n.casefold() in by_name]
    league.chart[team - 1] = chart
