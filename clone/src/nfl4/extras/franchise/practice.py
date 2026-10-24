"""The practice squads of the Franchise (nfl4 only, rule 0.13; the owner's request 2026-10-23: "The practice squad is not added in franchise mode.
You must add this into the game, too."; D-136). This is inspired by Jim Kitchen.

The NFL's practice squad (research 2026-10-23, SRC-SECONDARY: si.com, fantasynerds.com, hogshaven.com, dallascowboys.com; the NFL's own operations
page could not be read, so every number here is tagged UNVERIFIED until the owner or a later session checks it there): up to 16 players (17 with an
International Pathway player, not modelled), at most 6 of them veterans (more than two accrued seasons); a player may be elevated to the game-day
roster 3 times in a regular season (any number in the play-offs), at most 2 elevations a game, and he goes back to the squad after the game; a
practice squad player is paid by the week: 13,750 dollars for two or fewer seasons, 18,350 to 22,850 for a veteran (2026); sources differ on the cap,
the game counts the salaries against it (the 2020 CBA's rule as most sources state it).

How the game models it (rules only: no speech, no files, no draw, so the program and a fast run call the same code):

* A practice squad player is a Player with status "practice", his team, no place (-1), a one-season contract of PRACTICE_SALARY (young) or
  PRACTICE_SALARY_VETERAN (tenths of a million: 18 weeks of the weekly pay), counted in the team's cap.
* `form(league)`, at the roster cut (stage 5, after the cut and the fill): each team takes, team by team in a turn that changes each season, the best
  of the players cut this offseason that it may still sign (its own cut players first), until SIZE or the veterans' limit; the player's team the same
  (the staff's rule; F9, Franchise, practice squad changes it).
* `elevate(league, team, position)`: when an injury leaves a group with nobody fit, the team's best squad player of the position (a returner's place:
  a running back, then a receiver, then a cornerback of the squad) with elevations left plays as the stand-in instead of a made-up player. The week's
  stand-in draw is still made (so the league's draws stay the same) and its name is not used. `count_week(league, week)` charges one elevation a
  regular-season week for every squad player standing in.
* `dissolve(league)`: when the season is over (the season in review, stage 1) every squad player becomes a free agent of the offseason ("released",
  the season he left), as the NFL's practice squad contracts end with the season.
* `promote`, `sign_to_squad`, `release_from_squad`: the player's own moves in F9 (practice_flow.py), with their checks (`promote_problem` and the rest).

    league.practice = {"season": s, "elevations": {"<player id>": n}}     (league.sav format 14; an older file gets it empty, and a league in its
                                                                          season gets its squads at once from the players cut this offseason)
"""
from __future__ import annotations

from .. import nx_texts as X
from .. import tuning as T
from . import contracts as CT
from . import data as D
from . import injuries

STATUS = "practice"
SIZE = 16                     # UNVERIFIED (SRC-SECONDARY): 16, or 17 with an International Pathway player (not modelled)
VETERANS = 6                  # UNVERIFIED (SRC-SECONDARY): at most six players with more than two accrued seasons
VETERAN_SEASONS = 3           # a veteran has three or more seasons (more than two)
ELEVATIONS = 3                # UNVERIFIED (SRC-SECONDARY, the 2022 rule): three elevations a player in a regular season; the play-offs have no limit
PER_GAME = 2                  # UNVERIFIED (SRC-SECONDARY): two elevations a team in one game
PRACTICE_SALARY = 2           # tenths of a million: 13,750 dollars x 18 weeks = 0.25 million (2026, SRC-SECONDARY)
PRACTICE_SALARY_VETERAN = 4   # 18,350 to 22,850 dollars x 18 weeks = 0.33 to 0.41 million
RETURN_COVER = ("RB", "WR", "CB")     # a returner's place is stood in for by a squad back, then a receiver, then a cornerback


def empty() -> dict:
    return {"season": 0, "elevations": {}}


def veteran(player) -> bool:
    return player.seasons >= VETERAN_SEASONS


def salary_of(player) -> int:
    return PRACTICE_SALARY_VETERAN if veteran(player) else PRACTICE_SALARY


def squad(league, team: int) -> list:
    """The team's practice squad, the best first (rating, then the lower ID)."""
    return sorted((p for p in league.players.values() if p.status == STATUS and p.team == team), key=lambda p: (-p.rating, p.id))


def elevations(league, player) -> int:
    return int(league.practice["elevations"].get(str(player.id), 0))


def can_take(league, team: int, player) -> bool:
    """The squad of `team` has room for `player` (the size, the veterans' limit and the cap)."""
    members = squad(league, team)
    if len(members) >= SIZE:
        return False
    if CT.cap_used(league, team) + salary_of(player) > T.FR_CAP:
        return False
    return not veteran(player) or sum(1 for p in members if veteran(p)) < VETERANS


def _join(league, team: int, player) -> None:
    player.status, player.team, player.place, player.left, player.points = STATUS, team, -1, 0, 0
    player.salary, player.years = salary_of(player), 1
    league.practice["elevations"].pop(str(player.id), None)


def candidates(league) -> list:
    """The players a squad may sign at the cut: the players released or let go in this offseason (status "released" or "free", the season just
    over or this one), the best first."""
    season = league.season
    return sorted((p for p in league.players.values() if p.status in ("released", "free") and p.left in (season, season - 1)
                   and p.age <= T.FR_PRACTICE_MAX_AGE),
                  key=lambda p: (-p.rating, p.id))


def form(league) -> int:
    """Every team's practice squad at the roster cut (no draw): each team in turn (the turn starts with a team that changes each season) takes the best
    candidate it may sign, preferring the players it cut itself, until every squad is full or nobody is left. Returns how many joined."""
    pool = candidates(league)
    if not pool:
        return top_up(league)
    own = {}
    for p in pool:
        own.setdefault(p.team, []).append(p)
    joined, taken = 0, set()
    start = (league.season - 1) % D.TEAMS
    order = [(start + k) % D.TEAMS + 1 for k in range(D.TEAMS)]
    while True:
        moved = False
        for team in order:
            if len(squad(league, team)) >= SIZE:
                continue
            choice = next((p for p in own.get(team, []) if p.id not in taken and can_take(league, team, p)), None)
            if choice is None:
                choice = next((p for p in pool if p.id not in taken and can_take(league, team, p)), None)
            if choice is None:
                continue
            taken.add(choice.id)
            _join(league, team, choice)
            joined += 1
            moved = True
        if not moved:
            break
    league.practice["season"] = league.season
    return joined + top_up(league)                     # the places nobody let go could fill: young made-up players


TEMPLATE = (("QB", 1), ("RB", 2), ("WR", 3), ("DL", 3), ("LB", 3), ("CB", 2), ("S", 2))     # 16 places of a squad filled with young players
REAL_GROUP = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "WR", "DL": "DL", "LB": "LB", "CB": "CB", "S": "S", "K": "K", "P": "P"}   # NX-B2


def real_squads(league, real) -> int:
    """NX-B2 (the owner 2026-10-24: "it should be using the current 53 man rosters for each team"): a new franchise's practice squads are each team's real
    squad (the PS lines of rosters.txt), in the file's order, up to SIZE, the offensive linemen and long snappers left out (the Franchise has no place for
    them yet). No real rating or age: a hash of the league's ID and the name gives a rating in FR_PRACTICE_RATING and an age of 22 to 25 (rookies and
    second-year men, so the veterans' limit holds), as the made-up young players have. No draw. `top_up` fills what is left. Returns how many joined."""
    from .league import Player
    from .signings import _mix
    if real is None or not hasattr(real, "squad"):
        return 0
    known = {p.name.casefold() for p in league.players.values()}
    base, span = T.FR_PRACTICE_RATING
    joined = 0
    for team in range(1, D.TEAMS + 1):
        for agent in real.squad(team):
            position = REAL_GROUP.get(agent.pos)
            name = real.spoken(agent.name)
            if position is None or name.casefold() in known or len(squad(league, team)) >= SIZE:
                continue
            h = _mix(league.league_id, "real practice squad", team, agent.name)
            seasons = (h >> 8) % 2
            age = 22 + seasons + (h >> 12) % 3
            rating = max(D.RATING_MIN, min(D.RATING_MAX, base + h % span))
            if CT.cap_used(league, team) + PRACTICE_SALARY > T.FR_CAP:
                break
            player = Player(league.next_id, name, position, rating, "average", age, seasons, rating, None, 0, STATUS, 0, team, -1, PRACTICE_SALARY, 1)
            league.players[player.id] = player
            league.next_id += 1
            known.add(name.casefold())
            joined += 1
    league.practice["season"] = league.season
    return joined


def top_up(league, surnames: list | None = None) -> int:
    """Every squad short of SIZE is filled with made-up young players (rookies and second-year men, rated FR_PRACTICE_RATING, no veterans), made
    WITHOUT a draw from a hash of the league's ID, the season, the team and the place (the free agents' rule, signings.py), so a new franchise has
    its squads from week 1 and a reloaded league has the same men. They take positions the squad has fewest of by TEMPLATE. Returns how many."""
    from .league import Player
    from . import first_names as FN
    from .signings import _mix
    if surnames is None:
        from ...game.names import load_surnames
        surnames = load_surnames()
    used = FN.name_keys(league.league_id, (p.name for p in league.players.values() if p.status in ("active", STATUS, "free")))
    made = 0
    base, span = T.FR_PRACTICE_RATING
    for team in range(1, D.TEAMS + 1):
        members = squad(league, team)
        have = {pos: sum(1 for p in members if p.pos == pos) for pos, _n in TEMPLATE}
        wanted = [pos for pos, n in TEMPLATE for _ in range(max(0, n - have.get(pos, 0)))]
        for index, position in enumerate(wanted[:max(0, SIZE - len(members))]):
            h = _mix(league.league_id, "practice", league.season, team, position, index)
            start = (h >> 20) % len(surnames)
            surname = next((surnames[(start + k) % len(surnames)] for k in range(len(surnames))
                            if surnames[(start + k) % len(surnames)] not in used), surnames[start])
            used.add(surname)
            seasons = (h >> 8) % 2
            age = 22 + seasons + (h >> 12) % 2
            rating = max(D.RATING_MIN, min(D.RATING_MAX, base + h % span))
            player = Player(league.next_id, FN.full_name(league.league_id, surname), position, rating, "average", age, seasons, rating,
                            None, 0, STATUS, 0, team, -1, PRACTICE_SALARY, 1)
            if CT.cap_used(league, team) + PRACTICE_SALARY > T.FR_CAP:
                break
            league.players[player.id] = player
            league.next_id += 1
            made += 1
    league.practice["season"] = league.season
    return made


def dissolve(league) -> int:
    """The season is over: every squad player is a free agent of the offseason (released this season, no team, no contract)."""
    count = 0
    for p in league.players.values():
        if p.status == STATUS:
            p.status, p.left, p.team, p.place, p.salary, p.years = "released", league.season, 0, -1, 0, 0
            count += 1
    league.practice = empty()
    return count


# ----- the elevations (the stand-ins of injuries.py) -----

def playoffs(league, week: int) -> bool:
    return week > league.regular_weeks


def eligible(league, team: int, position: str, week: int, exclude=()) -> list:
    """The squad players who may stand in for the group `position` this week, the best first."""
    wanted = RETURN_COVER if position == "RET" else (position,)
    out = []
    for pos in wanted:
        for p in squad(league, team):
            if p.pos == pos and p.name not in exclude and (playoffs(league, week) or elevations(league, p) < ELEVATIONS):
                out.append(p)
    return out


def elevate(league, team: int, position: str, week: int, exclude=()):
    """The squad player who stands in for the group, or None (a made-up stand-in then plays)."""
    standing = {row[2] for row in league.injuries["stand_ins"] if row[0] == team}
    if sum(1 for row in league.injuries["stand_ins"] if row[0] == team and row[2] in names(league, team)) >= PER_GAME:
        return None
    found = eligible(league, team, position, week, exclude=set(exclude) | standing)
    return found[0] if found else None


def names(league, team: int) -> set:
    return {p.name for p in squad(league, team)}


def stand_in_row(team: int, position: str, player) -> list:
    """The stand-in record of injuries.py for an elevated squad player: his name and his rating (a real player, not the replacement level)."""
    return [team, position, player.name, max(D.RATING_MIN, min(D.RATING_MAX, player.rating))]


def count_week(league, week: int) -> int:
    """Before the games of a regular-season week: one elevation for every squad player standing in for a group that needs him this week. A player
    who has used his three is replaced by the next squad player of the position, or by a made-up stand-in the next time one is made. Returns the
    elevations charged."""
    if playoffs(league, week):
        return 0
    charged = 0
    by_name = {}
    for p in league.players.values():
        if p.status == STATUS:
            by_name[(p.team, p.name)] = p
    for row in list(league.injuries["stand_ins"]):
        player = by_name.get((row[0], row[2]))
        if player is None or not injuries.needs_stand_in(league, row[0], row[1], week):
            continue
        key = str(player.id)
        league.practice["elevations"][key] = league.practice["elevations"].get(key, 0) + 1
        charged += 1
        if league.practice["elevations"][key] >= ELEVATIONS:
            nxt = eligible(league, row[0], row[1], week + 1, exclude={row[2]})
            if nxt:
                row[2], row[3] = nxt[0].name, stand_in_row(row[0], row[1], nxt[0])[3]
    return charged


def report_lines(league, words) -> list:
    """The weekly injury report's lines for the player's own squad players standing in (NXJ-P18): who is elevated, for which group, and the
    elevations he has left in the regular season."""
    team = league.team
    mine = {p.name: p for p in squad(league, team)}
    lines = []
    for row in league.injuries["stand_ins"]:
        player = mine.get(row[2]) if row[0] == team else None
        if player is None:
            continue
        left = None if playoffs(league, league.gtp) else max(0, ELEVATIONS - elevations(league, player))
        lines.append(X.text("NXJ-P18", player=player.name, group=words.group(row[1])) if left is None else
                     X.text("NXJ-P19", player=player.name, group=words.group(row[1]), n=left))
    return lines


# ----- the player's own moves (F9, Franchise, practice squad) -----

def in_window(league) -> bool:
    """The squad can be changed in the regular season and the play-offs (before a kick-off; the menu checks the game in progress)."""
    from .league import SEASON
    return league.stage == SEASON and league.practice["season"] == league.season


def promote_problem(league, player, release, week: int) -> str | None:
    """Why the squad player cannot be signed to the team's roster (a short reason), or None."""
    team = league.team
    if player is None or player.status != STATUS or player.team != team:
        return "not a player of the practice squad"
    from . import signings as S
    if S.open_place(league, team, player.pos):
        if release is not None:
            return "a release with an open place"
    else:
        if release is None:
            return "no place and no release"
        if release.status != "active" or release.team != team or release.pos != player.pos or release.place < 0:
            return "a release who is not a player of the group"
        if not injuries.healthy(league, release.id, week):
            return "a release who is hurt"
    salary = CT.min_salary(player.seasons)
    used = CT.cap_used(league, team) - player.salary + salary
    if release is not None:
        used += CT.dead_money(release) - (release.salary if CT.running(release) else 0)
    if used > T.FR_CAP:
        return "over the cap"
    return None


def promote(league, player, release) -> tuple:
    """The squad player signs to the roster for the minimum (one season); the released player, when there is one, is a free agent of the season.
    Returns (the salary, the dead money)."""
    from . import aging
    from . import signings as S
    team = league.team
    roster = league.rosters[team - 1]
    dead = 0
    if release is not None:
        index = release.place
        roster[index] = 0
        dead = CT.release(league, release)
        release.status, release.left, release.place, release.points, release.team = "free", league.season, -1, 0, 0
        S._forget(league, release.id)
    else:
        index = next(i for i in D.PLACES_OF[player.pos] if not roster[i])
    salary = CT.min_salary(player.seasons)
    roster[index] = player.id
    player.status, player.team, player.place, player.left, player.points = "active", team, index, 0, 0
    CT.sign(player, salary, 1)
    league.practice["elevations"].pop(str(player.id), None)
    for row in league.injuries["stand_ins"]:
        if row[0] == team and row[2] == player.name:
            row[2] = ""                                   # placeholder; the next week's settle makes a new stand-in if one is still needed
    league.injuries["stand_ins"][:] = [row for row in league.injuries["stand_ins"] if row[2]]
    aging.place_by_rating(league, team)
    if len(league.sums) == D.TEAMS:
        league.sums[team - 1] = league.strength_sum(team)
    return salary, dead


def sign_problem(league, player) -> str | None:
    """Why a free agent of the season cannot join the player's squad, or None."""
    from . import signings as S
    if player is None or player not in S.pool(league):
        return "not a free agent"
    if not can_take(league, league.team, player):
        return "the practice squad is full" if len(squad(league, league.team)) >= SIZE else "too many veterans"
    if CT.cap_used(league, league.team) + salary_of(player) > T.FR_CAP:
        return "over the cap"
    return None


def sign_to_squad(league, player) -> None:
    _join(league, league.team, player)


def release_from_squad(league, player) -> None:
    """The player leaves the squad: a free agent of this season (he may be signed again)."""
    for row in league.injuries["stand_ins"]:
        if row[0] == player.team and row[2] == player.name:
            row[2] = ""
    league.injuries["stand_ins"][:] = [row for row in league.injuries["stand_ins"] if row[2]]
    player.status, player.left, player.team, player.place, player.salary, player.years = "free", league.season, 0, -1, 0, 0
    league.practice["elevations"].pop(str(player.id), None)


# ----- the whole-file check -----

def check(league, whole) -> None:
    """LeagueError unless the practice record and the squads are whole."""
    from .league import LeagueError
    record = league.practice
    if not isinstance(record, dict) or set(record) != {"season", "elevations"}:
        raise LeagueError("the practice squads are %r" % (record,))
    whole(record["season"], 0, 10000, "the practice squads' season")
    if not isinstance(record["elevations"], dict):
        raise LeagueError("the elevations are %r" % (record["elevations"],))
    for key, value in record["elevations"].items():
        if not (isinstance(key, str) and key.isdigit() and int(key) in league.players):
            raise LeagueError("an elevation of %r" % (key,))
        whole(value, 0, 100, "an elevation count")
    counts, vets = [0] * D.TEAMS, [0] * D.TEAMS
    for p in league.players.values():
        if p.status != STATUS:
            continue
        if not (1 <= p.team <= D.TEAMS) or p.place != -1:
            raise LeagueError("practice squad player %d has team %r and place %r" % (p.id, p.team, p.place))
        counts[p.team - 1] += 1
        vets[p.team - 1] += veteran(p)
    if max(counts) > SIZE or max(vets) > VETERANS + 1:     # +1: a squad player who turned a veteran during the season stays
        raise LeagueError("a practice squad of %d players, %d veterans" % (max(counts), max(vets)))
