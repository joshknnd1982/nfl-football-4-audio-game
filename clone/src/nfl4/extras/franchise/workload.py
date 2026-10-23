"""Who carries the ball and how much he carries: the weighted ball carrier, the season's carries and games, the workload rule (nfl4 only, rule 0.13). This
is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8o (research B2, B7's LATER items, INJ-3, D-076). FRANCHISE ONLY: the engine reaches these rules only through the Franchise's
H8 object (`ratings.FranchiseModifiers.carrier_weights`, read by NflRules' H17 `draw_carrier`) and the Franchise's injuries (`injuries.after_games`,
`injury_flow.GameInjuries`); every other game draws the original's `rnd(6)`. Plain rules, no speech, no files; the only draws are the carrier's (one
`below(total)` when the weights differ) and the workload's (one `below(10000)`), made with the one GameRandom handed in.

    carry_weight / weights / draw       the weighted draw of the ball carrier: equal weights are the original's rnd(6) itself (N2: a league of equal
                                        ratings, and every game outside a franchise)
    rated_table / expected_carries      a game the engine does not play: the team's FR_WORKLOAD_RUNS running plays shared by the same weights
    place_weights                       the week's game part of the injuries: the backs' and the receivers' places weighted by the same shares
    count_games / add_carries           the season's games a player played his own place and his carries (`LeagueRecord.usage`, league.sav format 10)
    extra_percent / carry_chance / game_chance   the workload rule: a running back's chance as the ball carrier rises with his carries of the season

`LeagueRecord.usage`: {"season": s, "games": {"<player ID>": games}, "carries": {"<player ID>": tenths of a carry}}, the season s's counts (set again at stage 6).
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D
from .ratings import step

RUN, PASS = "run", "pass"
GROUP_OF_KIND = {RUN: "RB", PASS: "WR"}
KEYS = ("season", "games", "carries")
MAX_CARRIES = 20_000                     # tenths: a bound for the whole-file check (a season of 20 games of 100 carries)


def empty(season: int = 0) -> dict:
    return {"season": season, "games": {}, "carries": {}}


# ----- the weighted ball carrier -----

def kind_of(offense_play: int) -> str | None:
    """Which group carries the play: the backs on a run (plays 1 and 2), the receivers on a pass (3 to 5); None for a kick or a quarterback run."""
    if offense_play in (1, 2):
        return RUN
    if offense_play in (3, 4, 5):
        return PASS
    return None


def carry_weight(rating: int) -> int:
    base, per, cap = T.FR_CARRY_WEIGHT
    return base + step(rating - D.RATING_NEUTRAL, per, cap)


def weights(ratings: list) -> list:
    return [carry_weight(rating) for rating in ratings]


def even(values: list) -> bool:
    return all(value == values[0] for value in values)


def draw(rnd, values: list) -> int:
    """The carrier 1 to 6: the original's rnd(6) when every weight is the same, else one `below(total)` over the weights."""
    if even(values):
        return rnd(6)
    roll = rnd.below(sum(values))
    for number, value in enumerate(values, start=1):
        if roll < value:
            return number
        roll -= value
    raise AssertionError("the carry weights")


# ----- a game the engine does not play -----

def rated_table(league, team: int, table: list) -> list:
    """The ratings a game would read: the lineup `table` with the morale of every player who plays his own place (people.with_morale)."""
    from . import people
    return people.with_morale(league, team, table) if people.has_morale(league) else table


def group_shares(table: list, position: str) -> list:
    """(identity, weight) of the group's places in the lineup `table`, in place order."""
    return [(table[i][0], carry_weight(table[i][2])) for i in D.PLACES_OF[position]]


def expected_carries(table: list) -> dict:
    """identity -> tenths of a carry: the team's FR_WORKLOAD_RUNS running plays of a game shared by the backs' carry weights (a man who plays two places
    gets both shares; a stand-in is left out)."""
    shares = group_shares(table, "RB")
    total = sum(weight for _identity, weight in shares)
    out: dict = {}
    for identity, weight in shares:
        if isinstance(identity, int):
            out[identity] = out.get(identity, 0) + (2 * T.FR_WORKLOAD_RUNS * weight + total) // (2 * total)
    return out


def place_weights(table: list) -> list:
    """The 34 places' weights of the week's game part (FR_INJ_GAME_WEIGHT): a back's or a receiver's place by its share of the group's carries (equal
    weights: the table's own numbers exactly), every other place as it is."""
    out = [T.FR_INJ_GAME_WEIGHT[D.POSITION_OF_PLACE[i]] for i in range(D.PLACE_COUNT)]
    for position in ("RB", "WR"):
        shares = group_shares(table, position)
        total = sum(weight for _identity, weight in shares)
        whole = T.FR_INJ_GAME_WEIGHT[position] * len(shares)
        for index, (_identity, weight) in zip(D.PLACES_OF[position], shares):
            out[index] = whole * weight // total
    return out


# ----- the season's counts -----

def ensure(league) -> dict:
    usage = league.usage
    if usage["season"] != league.season:
        league.usage = usage = empty(league.season)
    return usage


def count_games(league, week: int, staff: bool = True) -> None:
    """The game of `week` (1 to 16, or the calendar's 18) counts for every player who played his own place in it (people.played_ids: the week's lineup);
    a team on its bye played no game."""
    from . import people
    if not 1 <= week <= league.regular_weeks:
        return
    games = ensure(league)["games"]
    for team in range(1, D.TEAMS + 1):
        if league.has_bye(team, week):
            continue
        for pid in people.played_ids(league, team, week, staff or team != league.team):
            key = str(pid)
            games[key] = games.get(key, 0) + 1


def games_of(league, pid: int) -> int:
    usage = league.usage
    return usage["games"].get(str(pid), 0) if usage["season"] == league.season else 0


def add_carries(league, pid: int, tenths: int) -> None:
    if tenths <= 0:
        return
    carries = ensure(league)["carries"]
    key = str(pid)
    carries[key] = min(MAX_CARRIES, carries.get(key, 0) + tenths)


def carries_of(league, pid: int) -> int:
    usage = league.usage
    return usage["carries"].get(str(pid), 0) if usage["season"] == league.season else 0


# ----- the workload rule (INJ-3) -----

def extra_percent(league, pid: int) -> int:
    """The percent a running back's chance as the ball carrier rises by his carries of the season (0 under FR_WORKLOAD_FREE, at most FR_WORKLOAD_MAX)."""
    player = league.players.get(pid)
    if player is None or player.pos != "RB":
        return 0
    over = carries_of(league, pid) - T.FR_WORKLOAD_FREE
    if over < T.FR_WORKLOAD_PER:
        return 0
    return min(T.FR_WORKLOAD_MAX, over // T.FR_WORKLOAD_PER * T.FR_WORKLOAD_PCT)


def carry_chance(extra: int) -> int:
    """Ten-thousandths: the more chance of one carry of a game the engine plays (the ball carrier's part of FR_INJ_PLAY, raised by `extra` percent)."""
    return T.FR_INJ_PLAY * (100 - T.FR_INJ_TACKLER) * extra // 10000


def game_chance(tenths: int, extra: int) -> int:
    """Ten-thousandths: the same over the `tenths` carries of a game the engine does not play (one draw a game)."""
    return min(9999, tenths * T.FR_INJ_PLAY * (100 - T.FR_INJ_TACKLER) * extra // 100000)


# ----- stage 6 and the whole-file check -----

def new_season(league) -> None:
    league.usage = empty(league.season)


def check_usage(league, whole) -> None:
    from .league import LeagueError
    usage = league.usage
    if not isinstance(usage, dict) or set(usage) != set(KEYS):
        raise LeagueError("the usage is %r" % (sorted(usage) if isinstance(usage, dict) else type(usage).__name__,))
    whole(usage["season"], 0, D.MAX_SEASONS, "the season of the usage")
    for name, high in (("games", D.MAX_REGULAR_WEEKS), ("carries", MAX_CARRIES)):
        table = usage[name]
        if not isinstance(table, dict) or len(table) > 4 * D.TEAMS * D.PLACE_COUNT:
            raise LeagueError("the %s are %r" % (name, type(table).__name__))
        for key, value in table.items():
            if not isinstance(key, str) or not key.isascii() or not key.isdigit() or key != str(int(key)) or int(key) not in league.players:
                raise LeagueError("the %s of %r, who is not in the league" % (name, key))
            whole(value, 1, high, "a player's " + name)
