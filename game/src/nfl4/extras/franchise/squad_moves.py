"""Teams sign practice squad players to their rosters, other teams' too, and every team protects four squad men a week (nfl4 only, rule 0.13; S-E2,
Q-067, D-162, D-174, D-200). This is inspired by Jim Kitchen.

The NFL's rules (settled 2026-11-06, spec/NFL_EXTRA_FEATURES section 23, NX-T4):
* SRC-OFFICIAL (the 2020 CBA, Article 33 Section 6, its text as overthecap.com hosts it): a club may sign another club's practice squad player to its
  53-player Active/Inactive List (never to its own practice squad: SRC-SECONDARY, the 2026 squad guides); it counts him there for three games and pays
  him at least three weeks of the active list's minimum.
* SRC-OFFICIAL (Article 33 Section 2(b)): a squad player may not sign with his club's next opponent later than 4 p.m. New York time on the sixth day
  before the game (the tenth with a bye). The weekly step runs inside those six days, so a team never signs a man of the squad of the team it plays this
  week.
* SRC-OFFICIAL (buccaneers.com, a club's own page, 2020) and SRC-SECONDARY (fantasynerds.com 2026-08-30: still in force): every club may protect up to
  four practice squad players a week, from Tuesday 4 p.m. ET through its game; protected men cannot be signed away; a man may be protected every week.
  Not modelled: the hours between a club's game and Tuesday 4 p.m., when nobody is protected (the player's protections hold all week, D-200).
* UNVERIFIED: how often teams do it (no count was found); the game's rule below is measured in the soaks (D-200).

How the game models it (rules only: no speech, no files, NO DRAW, so the league's random draws stay the same):

* `protected_ids(league, team)`: a computer team protects its four best squad men; the player's team the four best too until he chooses his own
  (`league.practice["protected"]`, None for the staff's choice, else his list, kept from week to week until he changes it).
* `week_signings(league, week)`: in the preparation of weeks 2 to the last regular week, after the week's injuries and trades, every computer team (in a
  turn that changes each week) whose family is short for the coming weeks (fewer men of it able to play than FR_FAMILY_MIN, counting a man out for
  FR_SQUAD_SIGN_OUT games or more as gone) signs ONE squad man of that family to its roster: its own best, or another team's best unprotected man when he
  is better by FR_SQUAD_POACH_EDGE or more (never of the squad of the team it plays this week, never a man standing in for his team this week). A full
  53 releases its worst man to keep of a family that stays at its minimum; the cap must allow it. A computer team that lost a squad man signs the best
  free agent of his family the squad may take (`practice.can_take`).
* `sign_up(league, team, player, release)`: the one move of a squad man onto a team's roster (his own team's or another's), for the minimum, one season.
* `league.practice["signings"]`: the season's rows [week, from team, to team, player id], for the player's report and F9's list.
"""
from __future__ import annotations

from ...data import debuglog
from .. import tuning as T
from . import contracts as CT
from . import data as D
from . import injuries
from . import practice as P

PROTECT = 4                   # SRC-OFFICIAL (a club's page) and SRC-SECONDARY (2026): four protected squad men a club a week
SIGNINGS_MAX = 2000           # the check's bound on a season's rows


# ----- the protections -----

def protected_ids(league, team: int) -> set:
    """The squad men of `team` other teams cannot sign this week."""
    members = P.squad(league, team)
    chosen = league.practice.get("protected")
    if team == league.team and chosen is not None:
        ids = {p.id for p in members}
        return {pid for pid in chosen if pid in ids}
    return {p.id for p in members[:PROTECT]}


def staff_protects(league) -> bool:
    return league.practice.get("protected") is None


def set_protected(league, player, on: bool) -> str | None:
    """The player protects (`on`) or unprotects one of his squad men. Returns a short reason when it cannot be done, else None. The first change turns
    the staff's four into his own list."""
    if player is None or player.status != P.STATUS or player.team != league.team:
        return "not a player of the practice squad"
    current = sorted(protected_ids(league, league.team))
    if on:
        if player.id in current:
            league.practice["protected"] = current          # his choice now: the staff's four are kept as his own
            return None
        if len(current) >= PROTECT:
            return "four protected"
        current.append(player.id)
    else:
        current = [pid for pid in current if pid != player.id]
    league.practice["protected"] = sorted(current)
    return None


# ----- who may be signed -----

def next_opponent(league, team: int, week: int) -> int:
    """The team `team` plays in `week` (0: none known, or its bye). The calendar knows every game; a league of the original's 16 weeks only the player's."""
    if league.calendar:
        weeks = league.calendar["weeks"]
        if 1 <= week <= len(weeks):
            for game in weeks[week - 1]:
                if team in game:
                    return game[1] if game[0] == team else game[0]
        return 0
    if team == league.team and isinstance(league.schedule, list) and 1 <= week <= len(league.schedule):
        entry = league.schedule[week - 1]
        if isinstance(entry, list) and len(entry) == 3 and entry[0]:
            from .league import team_index
            return team_index(entry[0], entry[1])
    return 0


def standing_in(league, team: int) -> set:
    """The names of the team's squad men who stand in for an injured group this week (an elevation: never signed away that week)."""
    return {row[2] for row in league.injuries["stand_ins"] if row[0] == team}


def week_protections(league) -> dict:
    """Every team's protected squad men as they stand now: the week's list (the NFL's clubs name theirs on Tuesday for the whole week, so a squad that
    changes during the week's signings does not change who is protected; a man who joined a squad after it is not protected that week)."""
    return {team: protected_ids(league, team) for team in range(1, D.TEAMS + 1)}


def signable(league, team: int, week: int, family: str | None = None, protections: dict | None = None) -> list:
    """The squad men of OTHER teams that `team` may sign to its roster this week, the best first: not protected (`protections`, the week's list, else
    the list as it stands now), not standing in for their team, not of the squad of the team `team` plays this week."""
    opponent = next_opponent(league, team, week)
    squads: dict = {}
    for p in league.players.values():                     # every squad in one pass, each the best first (practice.squad's order)
        if p.status == P.STATUS and 1 <= p.team <= D.TEAMS:
            squads.setdefault(p.team, []).append(p)
    standing: dict = {}
    for row in league.injuries["stand_ins"]:
        standing.setdefault(row[0], set()).add(row[2])
    chosen = league.practice.get("protected")
    out = []
    for other, members in squads.items():
        if other in (team, opponent):
            continue
        members.sort(key=lambda p: (-p.rating, p.id))
        if protections is not None:
            blocked = protections.get(other, set())
        elif other == league.team and chosen is not None:
            blocked = set(chosen)
        else:
            blocked = {p.id for p in members[:PROTECT]}
        for p in members:
            if (family is None or p.pos == family) and p.id not in blocked and p.name not in standing.get(other, ()):
                out.append(p)
    return sorted(out, key=lambda p: (-p.rating, p.id))


# ----- a team's need -----

def able(league, team: int, family: str, week: int) -> int:
    """The men of the family on the team's roster who can play in the coming weeks (a man out for FR_SQUAD_SIGN_OUT games or more counts as gone)."""
    from . import real_roster
    known = injuries.rows(league)
    count = 0
    for p in real_roster.members(league, team):
        if p.pos != family:
            continue
        row = known.get(p.id)
        if row is not None and injuries.left(row, week) >= T.FR_SQUAD_SIGN_OUT:
            continue
        count += 1
    return count


def need_of(league, team: int, week: int) -> str | None:
    """The family the team is shortest of (below FR_FAMILY_MIN for the coming weeks), the most short first, then D.GROUPS' order; None when none is."""
    best, short = None, 0
    for family in D.GROUPS:
        least = T.FR_FAMILY_MIN.get(family, 0)
        gap = least - able(league, team, family, week)
        if gap > short:
            best, short = family, gap
    return best


def release_for(league, team: int, week: int, family: str):
    """The man a full roster releases to make room for a man of `family`: the worst to keep (draft.release_order) of the men of the other families who
    have no place in this week's view (the bench) and whose family has nobody hurt, so the week's lineup and its stand-ins, already settled, never
    miss him; his family keeps its minimum without him. None when nobody may go. (The soak of 2026-11-06 found the first rule, any healthy man,
    releasing a team's only fit safety after the week's stand-ins were made.)"""
    from . import draft
    from . import real_roster
    roster = real_roster.members(league, team)
    hurt = {p.pos for p in roster if not injuries.healthy(league, p.id, week)}
    men = [p for p in roster if p.pos != family and p.pos not in hurt and p.place < 0]
    for p in draft.release_order(men):
        if able(league, team, p.pos, week) - 1 >= T.FR_FAMILY_MIN.get(p.pos, 0):
            return p
    return None


def cap_allows(league, team: int, player, release) -> bool:
    used = CT.cap_used(league, team) + CT.min_salary(player.seasons)
    if player.team == team:
        used -= player.salary                             # his own squad's pay ends when he signs
    if release is not None:
        used += CT.dead_money(release) - (release.salary if CT.running(release) else 0)
    return used <= CT.cap_of(league)


# ----- the move -----

def sign_up(league, team: int, player, release=None) -> tuple:
    """The squad man signs to `team`'s roster for the minimum (one season); `release`, a man of `team`, is let go first (a free agent of the season). His
    old team's stand-in rows and elevations of him end. Returns (the salary, the dead money)."""
    from . import real_roster
    from . import signings as S
    old = player.team
    dead = 0
    if release is not None:
        dead = CT.release(league, release)
        release.left, release.points = league.season, 0
        real_roster.leave(league, release, "free", refresh=False)
        release.team = 0
        S._forget(league, release.id)
    rows = league.injuries["stand_ins"]
    rows[:] = [row for row in rows if not (row[0] == old and row[2] == player.name)]
    league.practice["elevations"].pop(str(player.id), None)
    salary = CT.min_salary(player.seasons)
    real_roster.join(league, team, player, refresh=False)
    CT.sign(player, salary, 1)
    real_roster.refresh_view(league, team)
    if len(league.sums) == D.TEAMS:
        league.sums[team - 1] = league.strength_sum(team)
    return salary, dead


def record(league, week: int, old: int, team: int, player) -> None:
    league.practice["signings"].append([week, old, team, player.id])


def refill(league, team: int, family: str, surnames=None, real=None) -> object | None:
    """A computer team's squad that lost a man signs the best free agent of his family it may take (the staff's age limit of the cut too). When the
    season's pool has nobody of the family yet and `surnames` is given, the pool is made first (signings.ensure_pool: the real free agents of a franchise's
    first season, then made-up veterans; no draw), as the player's first look at the free agents makes it. No draw."""
    from . import signings as S
    if surnames is not None and not S.pool_of(league, family):
        S.ensure_pool(league, surnames, real)
    for p in S.pool_of(league, family):
        if p.age <= T.FR_PRACTICE_MAX_AGE and P.can_take(league, team, p):
            P._join(league, team, p)
            return p
    return None


def week_signings(league, week: int, surnames=None, real=None) -> list:
    """The computer teams' squad signings of `week` (weeks 2 to the last regular week, once, in the week's preparation). Returns the rows made.
    `surnames` and `real` let a squad's refill make the season's free-agent pool when nobody has looked at it yet (`refill`)."""
    from .league import SEASON
    if league.stage != SEASON or not 2 <= week <= league.regular_weeks or league.practice["season"] != league.season:
        return []
    made = []
    protections = week_protections(league)                      # the week's lists, fixed before the first signing
    start = (league.season * 7 + week) % D.TEAMS                # a turn that changes each week (no draw)
    for k in range(D.TEAMS):
        team = (start + k) % D.TEAMS + 1
        if team == league.team:
            continue
        family = need_of(league, team, week)
        if family is None:
            continue
        standing = standing_in(league, team)                     # a man standing in this week stays where the week's lineup put him
        own = next((p for p in P.squad(league, team) if p.pos == family and p.name not in standing), None)
        other = next(iter(signable(league, team, week, family, protections)), None)
        choice = own
        if other is not None and (own is None or other.rating >= own.rating + T.FR_SQUAD_POACH_EDGE):
            choice = other
        if choice is None:
            continue
        from . import real_roster
        release = None if real_roster.room(league, team) > 0 else release_for(league, team, week, family)
        if real_roster.room(league, team) <= 0 and release is None:
            continue
        if not cap_allows(league, team, choice, release):
            continue
        old = choice.team
        salary, dead = sign_up(league, team, choice, release)
        record(league, week, old, team, choice)
        refilled = refill(league, old, family, surnames, real) if old != league.team else None     # the player's squad is his to fill
        debuglog.event("franchise", "squad_signed", week=week, season=league.season, team=team, player=choice.id, position=choice.position or choice.pos,
                       rating=choice.rating, from_team=old, own=old == team, released=release.id if release is not None else None, salary=salary,
                       dead_money=dead, refilled=refilled.id if refilled is not None else None)          # rule 0.15
        made.append([week, old, team, choice.id])
    return made


def taken_from_player(league, rows: list) -> list:
    """The rows of `rows` in which another team signed a man of the player's squad."""
    return [row for row in rows if row[1] == league.team and row[2] != league.team]


# ----- the record -----

def check(league, whole) -> None:
    """LeagueError unless the protections and the season's rows are whole (called by practice.check)."""
    from .league import LeagueError
    chosen = league.practice["protected"]
    if chosen is not None:
        if not isinstance(chosen, list) or len(chosen) > PROTECT or len(set(chosen)) != len(chosen):
            raise LeagueError("the protected squad players are %r" % (chosen,))
        for pid in chosen:
            whole(pid, 1, 10 ** 9, "a protected squad player")
            if pid not in league.players:
                raise LeagueError("a protected squad player %r is not in the league" % (pid,))
    rows = league.practice["signings"]
    if not isinstance(rows, list) or len(rows) > SIGNINGS_MAX:
        raise LeagueError("the squad signings are %r" % (type(rows).__name__,))
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a squad signing is %r" % (row,))
        whole(row[0], 1, 30, "a squad signing's week")
        whole(row[1], 1, D.TEAMS, "a squad signing's team")
        whole(row[2], 1, D.TEAMS, "a squad signing's team")
        whole(row[3], 1, 10 ** 9, "a squad signing's player")
        if row[3] not in league.players:
            raise LeagueError("a squad signing of player %r, who is not in the league" % (row[3],))
