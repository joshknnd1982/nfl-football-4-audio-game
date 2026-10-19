"""The awards of a season and the hall of fame of a Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8o (research B11's LATER item, D-076). Plain rules over the league record, no speech, no files and NO DRAW, so stage 1 of the
program's offseason (`offseason.stage_review`) and the calibration's fast run call the very same functions. Every number is data in `extras\\tuning.py`.

NO STATISTICS MODEL (D-076): the computer's games are the original's score table, with no plays and so no player statistics (research C); an invented box
score would be fiction, and the player's own games would have real numbers where the other 15 games of a week have none. So an award reads only what every
team has, by one rule: the players' ratings, the games each played his own place (`workload.count_games`, every week, every team), his team's wins and the
play-offs. A player's value is WEIGHT x (rating - FR_AWARD_BASE) x games / 16 + FR_AWARD_WIN x his team's wins (at least FR_AWARD_MIN_GAMES games); the awards after the first count every position alike (the weight of a back). A season whose games were counted from a later week on (a league of an older format, migrated in the middle of a season) scales the 16 and the least games to the weeks counted (the most games any player has):

    mvp    the most valuable player: the highest value among the players of the twelve play-off teams
    opoy   offensive player of the year: the highest value of a running back or a receiver (the quarterbacks have the most valuable player)
    dpoy   defensive player of the year: a lineman, linebacker, cornerback or safety
    roy    rookie of the year: a player in his first season, offense or defense (not a kicker or a punter)
    coy    coach of the year: the head coach whose team won the most games over what its rank lets expect (FR_COACH_EXPECT, measured on the ranks at the
           season's start; the rank is of the league's sums, which a trade of the season brings up to date, so a team that traded in a star is
           expected to win as its new roster lets it: the review of SX.8o)

Equal values: the higher rating, then the lower player ID (a coach: more wins, then the team order).

THE HALL OF FAME: at every stage 1 a kept player (retired, released or a free agent who left) whose last season is FR_HOF_WAIT or more seasons before is a
candidate; his hall value is his peak + his seasons + the points of his awards (FR_HOF_AWARD_POINTS). Those at FR_HOF_BAR or more enter, the highest
value first (equal: the higher peak, the lower ID), at most FR_HOF_CLASS a season. A player who won an award or entered the hall is kept in the league
record for good (`keeps`, read by `aging.drop_the_unkept`).

`LeagueRecord.honors` (league.sav format 10):
    {"awards": [[season, award, player id (0 for the coach), name, position ("" for the coach), team], ...],
     "hall": [[player id, season he entered], ...]}
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D

AWARDS = ("mvp", "opoy", "dpoy", "roy", "coy")
AWARD_TEXT = {"mvp": "NXG-A01", "opoy": "NXG-A02", "dpoy": "NXG-A03", "roy": "NXG-A04", "coy": "NXG-A05"}
OFFENSE = ("RB", "WR")
DEFENSE = ("DL", "LB", "CB", "S")
KEYS = ("awards", "hall")
MAX_AWARDS = len(AWARDS) * D.MAX_HISTORY
MAX_HALL = 4000


def empty() -> dict:
    return {"awards": [], "hall": []}


# ----- the awards -----

def value(player, games: int, wins: int, weighted: bool = True, weeks: int = D.REGULAR_WEEKS) -> int:
    """A player's season value: the position's weight (design 4.4; `weighted` False: every position as a back's, 2) x his rating over FR_AWARD_BASE x his
    share of the season's games (`weeks`: the weeks counted, 16 in a whole season), plus FR_AWARD_WIN a win of his team."""
    weight = D.WEIGHT[player.pos] if weighted else D.WEIGHT["RB"]
    return weight * max(0, player.rating - T.FR_AWARD_BASE) * games // weeks + T.FR_AWARD_WIN * wins


def weeks_counted(league) -> int:
    """The weeks of the season whose games were counted: the most games any player has (16 in a whole season; fewer only in a league migrated from an
    older format in the middle of a season)."""
    games = league.usage["games"].values() if league.usage["season"] == league.season else ()
    return max(games, default=0)


def least_games(weeks: int) -> int:
    """FR_AWARD_MIN_GAMES of 16, scaled to the weeks counted (rounded up)."""
    return (T.FR_AWARD_MIN_GAMES * weeks + D.REGULAR_WEEKS - 1) // D.REGULAR_WEEKS


def candidates(league, wins: list, weighted: bool = True) -> list:
    """(value, player) of every placed player of the season who played FR_AWARD_MIN_GAMES games or more (scaled to the weeks counted)."""
    from . import workload
    out = []
    weeks = weeks_counted(league)
    if weeks == 0:
        return out
    least = least_games(weeks)
    for team in range(1, D.TEAMS + 1):
        for player in league.active_of(team):
            if player is None:
                continue
            games = workload.games_of(league, player.id)
            if games >= least:
                out.append((value(player, games, wins[team - 1], weighted, weeks), player))
    return out


def best(pool: list):
    """The winner of a list of (value, player): the highest value, then the higher rating, then the lower ID; None for an empty list."""
    if not pool:
        return None
    return min(pool, key=lambda item: (-item[0], -item[1].rating, item[1].id))[1]


def expected_wins(rank: int) -> int:
    """Tenths of a win: what a team of this rank at the season's start wins (FR_COACH_EXPECT, by bands of four ranks)."""
    return T.FR_COACH_EXPECT[min(len(T.FR_COACH_EXPECT) - 1, (rank - 1) // 4)]


def coach_of_the_year(league, wins: list) -> int:
    """The team whose head coach is coach of the year: the most wins over the expected of its rank (league.sums: the season's start, brought up to date
    by a trade), then more wins, then the team order."""
    sums = league.sums if len(league.sums) == D.TEAMS else [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    ranked = sorted(range(1, D.TEAMS + 1), key=lambda t: (-sums[t - 1], t))
    rank = {team: number for number, team in enumerate(ranked, start=1)}
    return min(range(1, D.TEAMS + 1), key=lambda t: (-(10 * wins[t - 1] - expected_wins(rank[t])), -wins[t - 1], t))


def coach_name(league, team: int) -> str:
    if team == league.team:
        return league.coach
    staff = getattr(league, "staff", None)
    return staff["coaches"][team - 1]["name"] if staff else "coach"


def season_awards(league, wins: list, finish: list) -> list:
    """The rows of the season's awards (wins and finish of the 32 teams, as stage 1's entry has them); no row for an award nobody qualifies for."""
    pool = candidates(league, wins)
    plain = {p.id: v for v, p in candidates(league, wins, weighted=False)}     # the other awards: every position alike
    playoff = {team for team in range(1, D.TEAMS + 1) if finish[team - 1] > D.FINISH_MISSED}
    rows = []

    def row(award, player):
        if player is not None:
            rows.append([league.season, award, player.id, player.name, player.pos, player.team])

    mvp = best([(v, p) for v, p in pool if p.team in playoff])
    row("mvp", mvp)
    row("opoy", best([(plain[p.id], p) for _v, p in pool if p.pos in OFFENSE and p is not mvp]))
    row("dpoy", best([(plain[p.id], p) for _v, p in pool if p.pos in DEFENSE and p is not mvp]))
    row("roy", best([(plain[p.id], p) for _v, p in pool if p.seasons == 0 and p.pos not in ("K", "P")]))
    team = coach_of_the_year(league, wins)
    rows.append([league.season, "coy", 0, coach_name(league, team), "", team])
    return rows


def award_points(league, pid: int) -> int:
    return sum(T.FR_HOF_AWARD_POINTS.get(row[1], 0) for row in league.honors["awards"] if row[2] == pid)


def awards_of(league, pid: int) -> list:
    return [row for row in league.honors["awards"] if row[2] == pid]


# ----- the hall of fame -----

def in_hall(league, pid: int) -> bool:
    return any(row[0] == pid for row in league.honors["hall"])


def hall_value(league, player) -> int:
    return player.peak + player.seasons + award_points(league, player.id)


def hall_candidates(league) -> list:
    """The kept players who left the league FR_HOF_WAIT or more seasons before this one and are not in the hall, by hall value (the highest first)."""
    out = []
    for player in league.players.values():
        if player.status == "active" or player.left == 0 or league.season - player.left < T.FR_HOF_WAIT or in_hall(league, player.id):
            continue
        if player.peak < D.STAR_PEAK and not awards_of(league, player.id):
            continue                       # the kept players of every team alike (the player's own team keeps all of its players for history)
        out.append(player)
    return sorted(out, key=lambda p: (-hall_value(league, p), -p.peak, p.id))


def hall_class(league) -> list:
    """This season's class: the candidates at FR_HOF_BAR or more, at most FR_HOF_CLASS."""
    return [p for p in hall_candidates(league) if hall_value(league, p) >= T.FR_HOF_BAR][:T.FR_HOF_CLASS]


def stage_one(league, wins: list, finish: list) -> tuple:
    """Stage 1's honors, worked out without changing anything: (the award rows, the players of the hall's class). The awards of this season count for
    the class (a player who left five seasons ago cannot have won one now)."""
    return season_awards(league, wins, finish), hall_class(league)


def apply(league, rows: list, inducted: list) -> None:
    """The season's awards and the hall's class join the record (after stage 1's wait)."""
    league.honors["awards"].extend(rows)
    league.honors["hall"].extend([p.id, league.season] for p in inducted)


def keeps(league) -> set:
    """The players the record keeps for good: every award winner and every member of the hall."""
    return {row[2] for row in league.honors["awards"] if row[2]} | {row[0] for row in league.honors["hall"]}


def hall_members(league) -> list:
    """The hall's members as players, the newest class first, in the order they entered within a class (the highest hall value first)."""
    rows = sorted(league.honors["hall"], key=lambda row: -row[1])           # a stable sort keeps the entry order within a season
    return [(league.players[row[0]], row[1]) for row in rows if row[0] in league.players]


# ----- the whole-file check -----

def check_honors(league, whole) -> None:
    from .league import LeagueError
    data = league.honors
    if not isinstance(data, dict) or set(data) != set(KEYS):
        raise LeagueError("the honors are %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    awards, hall = data["awards"], data["hall"]
    if not isinstance(awards, list) or len(awards) > MAX_AWARDS or not isinstance(hall, list) or len(hall) > MAX_HALL:
        raise LeagueError("the honors' lists are too long or not lists")
    seen = set()
    for row in awards:
        if not isinstance(row, list) or len(row) != 6 or row[1] not in AWARDS:
            raise LeagueError("an award is %r" % (row,))
        whole(row[0], 1, D.MAX_SEASONS, "an award's season")
        if (row[0], row[1]) in seen:
            raise LeagueError("the award %r of season %r twice" % (row[1], row[0]))
        seen.add((row[0], row[1]))
        whole(row[5], 1, D.TEAMS, "an award's team")
        if not isinstance(row[3], str) or not 1 <= len(row[3]) <= 60 or any(ord(c) < 32 for c in row[3]):
            raise LeagueError("an award's name is %r" % (row[3],))
        if row[1] == "coy":
            whole(row[2], 0, 0, "a coach's award's player")             # a whole 0 (not False, not 0.0: the review)
            if row[4] != "":
                raise LeagueError("a coach's award is %r" % (row,))
        else:
            whole(row[2], 1, 10 ** 9, "an award's player")
            if row[4] not in D.POSITIONS or row[2] not in league.players:
                raise LeagueError("the award of player %r, who is not in the league" % (row[2],))
        if row[0] >= league.season and not (row[0] == league.season and league.stage != "season"):
            raise LeagueError("an award of season %r before it ended" % (row[0],))
    members = set()
    for row in hall:
        if not isinstance(row, list) or len(row) != 2:
            raise LeagueError("a member of the hall is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "a member of the hall")
        whole(row[1], 1, D.MAX_SEASONS, "the season he entered the hall")
        player = league.players.get(row[0])
        if player is None or player.status == "active" or row[0] in members:
            raise LeagueError("the member %r of the hall is not a former player of the league, or is there twice" % (row[0],))
        members.add(row[0])
