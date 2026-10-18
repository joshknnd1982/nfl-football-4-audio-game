"""The news of the Franchise: which lines a week's results make, and the lines kept in the league record (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 8.3 (F5, research B11). Rules over the league record, no speech and no files. After weeks 1 to 15 of the regular
season the news of the week is made from the results, the strengths and the streaks, by rules without draws, at most FR_NEWS_MAX
lines, in this order: the player's own streak of FR_STREAK_OWN or more (wins NWY, losses NWZ), the coach's milestone (every
FR_MILESTONE-th win as head coach, NWM), the biggest win of the week (NWB), an upset (NWU), the longest streak of FR_STREAK_LEAGUE or
more of another team (wins NWS, losses NWL) and the closest game that is not already told (NWC). The offseason's news (NWT the
champion, NWR the stars who retire, NWP the player's big improvers, NWD the first pick) is made by its stage. A line is one line of
its pool in news.txt (`news_pools.py`), drawn as the remarks are, filled and kept as markup in `LeagueRecord.news`:

    {"season": s, "week": w (1 to 15, or 16 for the offseason), "pool": "NWB", "markup": "...", "told": 0 or 1}

Ties (the design leaves them open): the first game in the week's order (the results are kept in the order the engine decided them);
for another team's streak the longest, then the lower team number.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ...data import debuglog
from .. import tuning as T
from . import data as D
from . import history
from .league import LeagueError, LeagueRecord, Player
from .news_pools import PLACEHOLDERS, NewsPools, make_line


@dataclass(frozen=True)
class Event:
    """One piece of news before it is a line: the pool, the teams (1 to 32, 0 for none), a number and a score, a player."""
    pool: str
    team: int = 0
    other: int = 0
    n: int = 0
    score: tuple = (0, 0)          # (winner's points, loser's points)
    player: Player | None = None
    rating: int = 0                # NWP: the rating he has now


def week_games(league: LeagueRecord, week: int) -> list:
    """The regular games of the week as (winner, loser, winner score, loser score), in the order the engine decided them."""
    return [(row[2], row[3], row[4], row[5]) for row in league.results if row[0] == 0 and row[1] == week]


def streaks(league: LeagueRecord, week: int) -> dict:
    """team -> (+1 for wins or -1 for losses, games in a row) after the games of weeks 1 to `week`."""
    table = {team: (0, 0) for team in range(1, D.TEAMS + 1)}
    for row in league.results:
        if row[0] != 0 or row[1] > week:
            continue
        for team, sign in ((row[2], 1), (row[3], -1)):
            kind, length = table[team]
            table[team] = (sign, length + 1) if kind == sign else (sign, 1)
    return table


def coach_wins(league: LeagueRecord, week: int) -> int:
    """The coach's regular-season wins through `week` of this season and every season before."""
    own = sum(1 for row in league.results if row[0] == 0 and row[1] <= week and row[2] == league.team)
    return history.career(league).wins + own


OWN_POOLS = ("NWY", "NWZ", "NWM")                  # the player's own news comes first (design 8.3); SX.8j's trades follow it


def week_events(league: LeagueRecord, week: int, cut: bool = True) -> list:
    """The events of the week in the order of the rules, at most FR_NEWS_MAX (design 8.3; `cut` False: all of them, for `with_trades`)."""
    games = week_games(league, week)
    if not games or not 1 <= week <= D.NEWS_LAST_WEEK:
        return []
    own = league.team
    events: list = []
    table = streaks(league, week)
    kind, length = table[own]
    if kind == 1 and length >= T.FR_STREAK_OWN:
        events.append(Event("NWY", team=own, n=length))
    elif kind == -1 and length >= T.FR_STREAK_OWN:
        events.append(Event("NWZ", team=own, n=length))
    if any(winner == own for winner, _l, _ws, _ls in games):
        total = coach_wins(league, week)
        if total > 0 and total % T.FR_MILESTONE == 0:
            events.append(Event("NWM", team=own, n=total))
    told: set = set()
    big = max(range(len(games)), key=lambda i: (games[i][2] - games[i][3], -i))      # the first of equal margins
    winner, loser, ws, ls = games[big]
    events.append(Event("NWB", team=winner, other=loser, n=ws - ls, score=(ws, ls)))
    told.add(big)
    if len(league.sums) == D.TEAMS:
        gaps = [(league.sums[games[i][1] - 1] - league.sums[games[i][0] - 1], i) for i in range(len(games))]
        gaps = [(gap, i) for gap, i in gaps if gap >= T.FR_UPSET_GAP * D.WEIGHT_SUM]
        if gaps:
            _gap, i = max(gaps, key=lambda g: (g[0], -g[1]))
            winner, loser, ws, ls = games[i]
            events.append(Event("NWU", team=winner, other=loser, n=ws - ls, score=(ws, ls)))
            told.add(i)
    best = None
    for team in range(1, D.TEAMS + 1):
        kind, length = table[team]
        if team != own and length >= T.FR_STREAK_LEAGUE and (best is None or length > best[1]):
            best = (team, length, kind)
    if best is not None:
        events.append(Event("NWS" if best[2] == 1 else "NWL", team=best[0], n=best[1]))
    rest = [i for i in range(len(games)) if i not in told]
    if rest:
        close = min(rest, key=lambda i: (games[i][2] - games[i][3], i))
        winner, loser, ws, ls = games[close]
        events.append(Event("NWC", team=winner, other=loser, n=ws - ls, score=(ws, ls)))
    return events[:T.FR_NEWS_MAX] if cut else events


def with_trades(events: list, trade_lines: list) -> list:
    """SX.8j: the week's events with the trades of the week's preparation after the player's own news (his streak, his milestone) and before the games'
    news, at most FR_NEWS_MAX in all (design 8.3's limit holds: a trade takes the place of the closest game, then of a streak, and so on)."""
    own = [event for event in events if event.pool in OWN_POOLS]
    rest = [event for event in events if event.pool not in OWN_POOLS]
    return (own + list(trade_lines) + rest)[:T.FR_NEWS_MAX]


# ----- the offseason's news (made by its stages) -----

def champion_event(season: int, champion: int) -> Event:
    return Event("NWT", team=champion, n=season)


def star_events(retiring: list) -> list:
    """The stars who retire and were named (design 6.3), as the stage names them."""
    return [Event("NWR", team=p.team, player=p) for p in retiring]


def first_pick_event(team: int, player: Player) -> Event:
    return Event("NWD", team=team, player=player)


def cap_event(league: LeagueRecord) -> Event:
    """The team with the most cap space after the roster cut and the fill (equal space to the lower team number), NWK; n is its space."""
    from . import contracts
    team = contracts.cap_ranking(league)[0]
    return Event("NWK", team=team, n=contracts.cap_space(league, team))


def trade_events(league: LeagueRecord, made: list) -> list:
    """NWX (SX.8j): the trades two other teams made in this week's preparation, at most FR_TRADE_NEWS, the one that moved the best player first (equal: the
    order of the search). The line names the better of the two players, the team that traded him away (<team>) and the team he goes to (<other>)."""
    events = []
    for order, trade in enumerate(made):
        first, second = league.players[trade.give_a], league.players[trade.give_b]
        star = first if (first.rating, -first.id) > (second.rating, -second.id) else second
        giver = trade.a if star.id == trade.give_a else trade.b
        events.append(((-star.rating, order), Event("NWX", team=giver, other=trade.other(giver), player=star)))
    events.sort(key=lambda pair: pair[0])
    return [event for _key, event in events[:T.FR_TRADE_NEWS]]


def demand_events(league: LeagueRecord, filed: list) -> list:
    """NWH (SX.8n): the players who asked to be traded this week (people.demands_week's rows [player, team, week, state]), in the order they asked."""
    return [Event("NWH", team=row[1], player=league.players[row[0]]) for row in filed if row[0] in league.players]


def improver_events(changes: list, team: int) -> list:
    """The player's team's players who improved by 5 or more, at most two, the biggest first (equal changes in league order)."""
    own = [c for c in changes if c.player.team == team and c.delta >= 5]
    own.sort(key=lambda c: -c.delta)
    return [Event("NWP", team=team, player=c.player, rating=c.new) for c in own[:2]]


# ----- making the lines -----

def _plain(text: str) -> str:
    """A name goes into markup that is read again: its brackets would make a [word] of it, so they become parentheses."""
    return text.replace("[", "(").replace("]", ")")


def placeholders(event: Event, league: LeagueRecord, words) -> dict:
    """The values of the placeholders the event's pool knows (`news_pools.PLACEHOLDERS`); another placeholder in a line of the pool is
    left as it is written, which is what the problem count of news.txt says."""
    values = {"<coach>": _plain(league.coach), "<n>": str(event.n)}
    if event.team:
        values["<team>"] = _plain(words.team_name(event.team))
    if event.other:
        values["<other>"] = _plain(words.team_name(event.other))
    if event.score != (0, 0):
        values["<score>"] = words.score(*event.score).strip()
    if event.player is not None:
        values["<player>"] = _plain(event.player.name)
        values["<position>"] = words.position(event.player.pos)
        values["<r>"] = str(event.rating or event.player.rating)
    if event.pool == "NWK":
        values["<cap>"] = words.amount(event.n)
    known = PLACEHOLDERS[event.pool]
    return {placeholder: value for placeholder, value in values.items() if placeholder in known}


def render(league: LeagueRecord, events: list, pools: NewsPools, words, rnd) -> tuple:
    """The lines of the events, in order: ([(pool, markup)], the news history after them). Nothing in the league is changed, so a
    stage that speaks before it saves (stage 1) can draw its line and keep it later. A pool with no line on makes none."""
    recent = {pool: list(ids) for pool, ids in league.news_recent.items()}
    lines = []
    for event in events:
        line = make_line(pools, event.pool, placeholders(event, league, words), recent.setdefault(event.pool, []), rnd)
        # the debug log: one line for each happening of the league (a trade, an injury, a holdout, a pick, a retirement ...)
        debuglog.event("franchise", "news", pool=event.pool, team=event.team or None, other=event.other or None, n=event.n or None,
                       player=getattr(event.player, "id", None), season=league.season, stage=league.stage, told=line is not None)
        if line is not None:
            lines.append((event.pool, line[1]))
    return lines, recent


def keep(league: LeagueRecord, lines: list, recent: dict, week: int) -> list:
    """Put rendered lines into the league record (told 0) with the history they made; returns the new entries."""
    league.news_recent = recent
    made = [{"season": league.season, "week": week, "pool": pool, "markup": markup, "told": 0} for pool, markup in lines]
    league.news.extend(made)
    del league.news[:-D.MAX_NEWS]
    return made


def make_entries(league: LeagueRecord, events: list, pools: NewsPools, words, rnd, week: int) -> list:
    """`render` and `keep` in one step (the weekly news)."""
    lines, recent = render(league, events, pools, words, rnd)
    return keep(league, lines, recent, week)


def untold(league: LeagueRecord) -> list:
    return [entry for entry in league.news if not entry["told"]]


def newest_first(league: LeagueRecord) -> list:
    """The kept lines, the newest week first (by season and week); the lines of one week in the order they were made and told."""
    order = sorted(range(len(league.news)), key=lambda i: (-league.news[i]["season"], -league.news[i]["week"], i))
    return [league.news[i] for i in order]


def drop_for_new_season(league: LeagueRecord) -> None:
    """Stage 6: the finished season's weekly news goes, and the offseason's news before it; the offseason just over stays (design
    8.3: kept for the new season's list)."""
    league.news[:] = [e for e in league.news if e["week"] == D.NEWS_OFFSEASON and e["season"] == league.season]


# ----- the whole-file check -----

_ID = re.compile(r"^[A-Z]{3}\d{1,4}$")


def check_entries(league: LeagueRecord, whole) -> None:
    news = league.news
    if not isinstance(news, list) or len(news) > D.MAX_NEWS:
        raise LeagueError("the news is %r" % (type(news).__name__,))
    for entry in news:
        if not isinstance(entry, dict) or set(entry) != {"season", "week", "pool", "markup", "told"}:
            raise LeagueError("a news line is %r" % (entry,))
        whole(entry["season"], 1, D.MAX_SEASONS, "a news season")
        whole(entry["week"], 1, D.NEWS_OFFSEASON, "a news week")
        whole(entry["told"], 0, 1, "a news told mark")
        if entry["pool"] not in D.NEWS_POOLS:
            raise LeagueError("a news line of the pool %r" % (entry["pool"],))
        markup = entry["markup"]
        if not isinstance(markup, str) or not 1 <= len(markup) <= 2000 or any(ord(c) < 32 for c in markup):
            raise LeagueError("a news line has the text %r" % (markup,))
    recent = league.news_recent
    if not isinstance(recent, dict) or len(recent) > len(D.NEWS_POOLS):
        raise LeagueError("the news history is %r" % (type(recent).__name__,))
    for pool, ids in recent.items():
        if pool not in D.NEWS_POOLS or not isinstance(ids, list) or len(ids) > 3 or any(
                not isinstance(i, str) or not _ID.match(i) for i in ids):
            raise LeagueError("the news history of %r is %r" % (pool, ids))
