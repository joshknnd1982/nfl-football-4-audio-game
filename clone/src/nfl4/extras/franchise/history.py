"""History and records of a Franchise: what is kept per season, the coach's career, the league records, the spoken lines and
history.txt (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 9. The results of the current season come from H14 (`game_played`) into `LeagueRecord.results`; at stage 1
of the offseason `build_entry` turns them, with the final records, into one entry of `LeagueRecord.history`, and the results
are dropped. An entry is plain data (JSON): teams are numbers 1 to 32; the words are made here from `nx_texts` and the names the
caller gives (`Words`), so a renamed team is renamed in the speech and in history.txt too (the league stores numbers, never names).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .. import nx_texts as X
from . import data as D
from .league import LeagueError, LeagueRecord


# ----- one season's entry -----

def build_entry(league: LeagueRecord) -> dict:
    """The entry of the season that just ended, from `league.results` and `league.records` (call at stage 1, before the
    results are dropped)."""
    wins = [league.records[2 * t] for t in range(D.TEAMS)]
    losses = [league.records[2 * t + 1] for t in range(D.TEAMS)]
    finish = [D.FINISH_MISSED] * D.TEAMS
    champion = runner_up = 0
    playoff = [[0, 0] for _ in range(D.TEAMS)]
    streak_now = [0] * D.TEAMS
    streak_best: list | None = None
    top_points: list | None = None
    big_win: list | None = None
    for code, _, winner, loser, ws, ls in league.results:
        stage = D.CODE_STAGE[code]
        if stage != D.REGULAR:
            playoff[winner - 1][0] += 1
            playoff[loser - 1][1] += 1
            finish[loser - 1] = D.LOST_IN[stage]
            if finish[winner - 1] == D.FINISH_MISSED:
                finish[winner - 1] = D.FINISH_WILD_CARD       # in the play-offs at least: raised by the round it loses in
            if stage == D.SUPER_BOWL:
                finish[winner - 1] = D.FINISH_CHAMPION
                champion, runner_up = winner, loser
        streak_now[winner - 1] += 1
        streak_now[loser - 1] = 0
        if streak_best is None or streak_now[winner - 1] > streak_best[1]:
            streak_best = [winner, streak_now[winner - 1]]
        if top_points is None or ws > top_points[2]:
            top_points = [winner, loser, ws, ls]
        if big_win is None or ws - ls > big_win[2] - big_win[3]:
            big_win = [winner, loser, ws, ls]
    if champion == 0:                                          # a season whose Super Bowl was not recorded: the best record
        ranked = sorted(range(1, D.TEAMS + 1), key=lambda t: (-wins[t - 1], t))
        champion, runner_up = ranked[0], ranked[1]
    best = max(range(1, D.TEAMS + 1), key=lambda t: (wins[t - 1], -t))
    worst = min(range(1, D.TEAMS + 1), key=lambda t: (wins[t - 1], t))
    return {"season": league.season, "team": league.team, "coach": league.coach, "champion": champion, "runner_up": runner_up,
            "wins": wins, "losses": losses, "finish": finish, "playoff": playoff[league.team - 1], "best": best, "worst": worst,
            "top_points": top_points, "big_win": big_win, "streak": streak_best}


def check_entry(entry, whole) -> None:
    """The values of one history entry in range (LeagueError otherwise)."""
    if not isinstance(entry, dict):
        raise LeagueError("a history entry is %r" % (type(entry).__name__,))
    for key in ("season", "team", "coach", "champion", "runner_up", "wins", "losses", "finish", "playoff", "best", "worst",
                "top_points", "big_win", "streak"):
        if key not in entry:
            raise LeagueError("a history entry lacks %s" % key)
    whole(entry["season"], 1, D.MAX_SEASONS, "a history season")
    whole(entry["team"], 1, D.TEAMS, "a history team")
    whole(entry["champion"], 1, D.TEAMS, "the champion")
    whole(entry["runner_up"], 1, D.TEAMS, "the runner-up")
    whole(entry["best"], 1, D.TEAMS, "the best record")
    whole(entry["worst"], 1, D.TEAMS, "the worst record")
    if not isinstance(entry["coach"], str) or not 1 <= len(entry["coach"]) <= 60:
        raise LeagueError("a history coach is %r" % (entry["coach"],))
    for key, high in (("wins", 20), ("losses", 20), ("finish", D.FINISH_CHAMPION)):
        values = entry[key]
        if not isinstance(values, list) or len(values) != D.TEAMS:
            raise LeagueError("a history %s is %r" % (key, values))
        for value in values:
            whole(value, 0, high, "a history " + key)
    playoff = entry["playoff"]
    if not isinstance(playoff, list) or len(playoff) != 2:
        raise LeagueError("a history play-off record is %r" % (playoff,))
    for value in playoff:
        whole(value, 0, 4, "a history play-off record")
    for key, size in (("top_points", 4), ("big_win", 4), ("streak", 2)):
        value = entry[key]
        if value is None:
            continue
        if not isinstance(value, list) or len(value) != size:
            raise LeagueError("a history %s is %r" % (key, value))
        for number in value:
            whole(number, 0, 200, "a history " + key)
        for team in (value[0], value[1]) if size == 4 else (value[0],):
            whole(team, 1, D.TEAMS, "a history " + key)


# ----- the coach's career and the league's records -----

@dataclass(frozen=True)
class Career:
    seasons: int
    wins: int
    losses: int
    playoff_wins: int
    playoff_losses: int
    playoff_seasons: int
    super_bowls: int


def career(league: LeagueRecord) -> Career:
    seasons = wins = losses = pw = pl = playoffs = titles = 0
    for entry in league.history:
        t = entry["team"] - 1
        seasons += 1
        wins += entry["wins"][t]
        losses += entry["losses"][t]
        pw += entry["playoff"][0]
        pl += entry["playoff"][1]
        if entry["finish"][t] > D.FINISH_MISSED:
            playoffs += 1
        if entry["finish"][t] == D.FINISH_CHAMPION:
            titles += 1
    return Career(seasons, wins, losses, pw, pl, playoffs, titles)


@dataclass(frozen=True)
class Records:
    """The league records (None: nothing yet). Each is (team, ...) with the season; the first of equal values keeps it."""
    most_wins: tuple | None             # (team, wins, season)
    most_points: tuple | None           # (team, opponent, points, season)
    biggest_win: tuple | None           # (team, opponent, winner score, loser score, season)
    longest_streak: tuple | None        # (team, games, season)


def league_records(league: LeagueRecord) -> Records:
    most_wins = most_points = biggest = streak = None
    for entry in league.history:
        season = entry["season"]
        for team in range(1, D.TEAMS + 1):
            if most_wins is None or entry["wins"][team - 1] > most_wins[1]:
                most_wins = (team, entry["wins"][team - 1], season)
        top = entry["top_points"]
        if top is not None and (most_points is None or top[2] > most_points[2]):
            most_points = (top[0], top[1], top[2], season)
        big = entry["big_win"]
        if big is not None and (biggest is None or big[2] - big[3] > biggest[2] - biggest[3]):
            biggest = (big[0], big[1], big[2], big[3], season)
        run = entry["streak"]
        if run is not None and (streak is None or run[1] > streak[1]):
            streak = (run[0], run[1], season)
    return Records(most_wins, most_points, biggest, streak)


def retired_stars(league: LeagueRecord) -> list:
    """The kept retired players, newest retirement first (then the highest peak)."""
    stars = [p for p in league.players.values() if p.status == "retired" and p.peak >= D.STAR_PEAK]
    return sorted(stars, key=lambda p: (-p.left, -p.peak, p.id))


# ----- the words -----

class Words:
    """Names and texts for the speech and history.txt: `team_name(t)` the nickname of team 1 to 32 (the player's teams.txt)."""

    def __init__(self, team_name: Callable[[int], str]):
        self.team_name = team_name

    def finish(self, code: int) -> str:
        return X.text(D.FINISH_TEXT[code])

    def position(self, position: str) -> str:
        return X.text(D.POSITION_TEXT[position])

    def group(self, position: str) -> str:
        return X.text(D.GROUP_TEXT[position])

    def score(self, winner: int, loser: int) -> str:
        return " %d to %d " % (winner, loser)

    def potential(self, potential: str) -> str:
        return X.text(D.POTENTIAL_TEXT[potential])

    def player(self, player) -> str:
        """NXL-31: a player in a list (SX.8b: the rating and the potential are spoken)."""
        return X.text("NXL-31", player=player.name, position=self.position(player.pos), r=player.rating, a=player.age,
                      potential=self.potential(player.potential))


def team_rating_text(league: LeagueRecord) -> str:
    """NXF-09: the player's team's rating (the weighted mean of its 34 players) and its number among the 32 (design 4.4)."""
    return X.text("NXF-09", r=league.strength(league.team), k=league.rank_of(league.team))


def team_rating_lines(league: LeagueRecord, words: Words) -> list:
    """NXL-40 for the 32 teams by rank, the best first (the team ratings item of F9)."""
    return [X.text("NXL-40", k=rank, team=words.team_name(team), r=league.strength(team))
            for rank, team in enumerate(league.ranking(), start=1)]


def _top_to_bottom(entries: list) -> list:
    return list(reversed(entries))


def champions_lines(league: LeagueRecord, words: Words) -> list:
    """NXG-10 per season, newest first."""
    return [X.text("NXG-10", n=e["season"], champion=words.team_name(e["champion"]), runner_up=words.team_name(e["runner_up"]))
            for e in _top_to_bottom(league.history)]


def record_line(league: LeagueRecord) -> str:
    c = career(league)
    return X.text("NXG-11", n=c.seasons, w=c.wins, l=c.losses, p=c.playoff_seasons, s=c.super_bowls)


def season_lines(league: LeagueRecord, words: Words) -> list:
    """NXG-12 per season, newest first."""
    lines = []
    for e in _top_to_bottom(league.history):
        t = e["team"] - 1
        lines.append(X.text("NXG-12", n=e["season"], w=e["wins"][t], l=e["losses"][t], finish=words.finish(e["finish"][t]),
                            champion=words.team_name(e["champion"]), best=words.team_name(e["best"]),
                            worst=words.team_name(e["worst"])))
    return lines


def record_lines(league: LeagueRecord, words: Words) -> list:
    """NXG-13 to NXG-16 (the records that exist)."""
    r = league_records(league)
    lines = []
    if r.most_wins is not None:
        lines.append(X.text("NXG-13", team=words.team_name(r.most_wins[0]), w=r.most_wins[1], n=r.most_wins[2]))
    if r.most_points is not None:
        lines.append(X.text("NXG-14", team=words.team_name(r.most_points[0]), p=r.most_points[2],
                            other=words.team_name(r.most_points[1]), n=r.most_points[3]))
    if r.biggest_win is not None:
        lines.append(X.text("NXG-15", team=words.team_name(r.biggest_win[0]), other=words.team_name(r.biggest_win[1]),
                            score=words.score(r.biggest_win[2], r.biggest_win[3]).strip(), n=r.biggest_win[4]))
    if r.longest_streak is not None:
        lines.append(X.text("NXG-16", team=words.team_name(r.longest_streak[0]), k=r.longest_streak[1], n=r.longest_streak[2]))
    return lines


def retired_lines(league: LeagueRecord, words: Words) -> list:
    return [X.text("NXG-17", player=p.name, position=words.position(p.pos), team=words.team_name(p.team), n=p.seasons,
                   r=p.peak, s=p.left) for p in retired_stars(league)]


# ----- history.txt (design 9.3) -----

def history_text(league: LeagueRecord, words: Words) -> str:
    """The text of history.txt, one fact per line, a blank line between parts. Written whole; never read back."""
    c = career(league)
    out = ["Franchise history: coach %s, the %s." % (league.coach, words.team_name(league.team)),
           ("Written by NFL Football 4 after season %d." % league.history[-1]["season"] if league.history
            else "Written by NFL Football 4 before the first season."), "",
           "Your record",
           "%d seasons, %d wins and %d losses. Play-offs %d times. Super Bowls won: %d." %
           (c.seasons, c.wins, c.losses, c.playoff_seasons, c.super_bowls)]
    for e in _top_to_bottom(league.history):
        t = e["team"] - 1
        out += ["", "Season %d" % e["season"],
                "Champion: %s. Runner-up: %s." % (words.team_name(e["champion"]), words.team_name(e["runner_up"])),
                "Your team: %d and %d, %s." % (e["wins"][t], e["losses"][t], words.finish(e["finish"][t])),
                "Best record: %s, %d and %d. Worst record: %s, %d and %d." %
                (words.team_name(e["best"]), e["wins"][e["best"] - 1], e["losses"][e["best"] - 1],
                 words.team_name(e["worst"]), e["wins"][e["worst"] - 1], e["losses"][e["worst"] - 1])]
    r = league_records(league)
    if any(value is not None for value in (r.most_wins, r.most_points, r.biggest_win, r.longest_streak)):
        out += ["", "League records"]
        if r.most_wins is not None:
            out.append("Most wins in a season: %s, %d, season %d." % (words.team_name(r.most_wins[0]), r.most_wins[1], r.most_wins[2]))
        if r.most_points is not None:
            out.append("Most points in a game: %s, %d against %s, season %d." %
                       (words.team_name(r.most_points[0]), r.most_points[2], words.team_name(r.most_points[1]), r.most_points[3]))
        if r.biggest_win is not None:
            out.append("The biggest win: %s over %s, %d to %d, season %d." %
                       (words.team_name(r.biggest_win[0]), words.team_name(r.biggest_win[1]), r.biggest_win[2], r.biggest_win[3],
                        r.biggest_win[4]))
        if r.longest_streak is not None:
            out.append("The longest winning streak: %s, %d games, season %d." %
                       (words.team_name(r.longest_streak[0]), r.longest_streak[1], r.longest_streak[2]))
    stars = retired_stars(league)
    if stars:
        out += ["", "Retired stars"]
        for p in stars:
            out.append("%s, %s, %s, %d seasons, best rating %d, retired after season %d." %
                       (p.name, words.position(p.pos), words.team_name(p.team), p.seasons, p.peak, p.left))
    return "\n".join(out) + "\n"
