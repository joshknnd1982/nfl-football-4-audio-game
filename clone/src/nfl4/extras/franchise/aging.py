"""Aging, retirement, progression and regression of the Franchise's players (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 6 and 8.2 (F2, N6.4). Plain rules over the league record, no speech and no files, so the offseason's stages
and the calibration's fast run use the very same code. A stage PLANS first (the draws are made, nothing is changed, so the spoken
lines can name the old and the new values), then APPLIES the plan and saves, then speaks (design 3.3 item 4, B-X51: a stage is
idempotent until its save, and the league the player may open in F9 at the wait is the changed one).

    plan_retirements / apply_aging     stage 2: everybody a year older, then the retirements (6.1, 6.3)
    plan_development / apply_development   stage 3: progression and regression, the development points go back to 0 (6.2, 8.2)
    retire_chance, base_change         the two rules as plain functions of numbers (the property tests read them)
    place_by_rating, fill_places       the places of a group in rating order; the fill of the empty places with undrafted rookies (stage 5)
    drop_the_unkept                    the retired and released players history does not need are dropped (design 4.3)

League order is team 1 to 32, then the order of the team's 34 places (design 6.2): the order of the draws. All numbers are data in
`extras\\tuning.py` (the `FR_` names) and `data.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import tuning as T
from . import contracts
from . import data as D
from .league import LeagueRecord, Player, draw_name


def league_order(league: LeagueRecord):
    """The active players, team 1 to 32 and each team's places in order."""
    players = league.players
    for roster in league.rosters:
        for pid in roster:
            if pid:
                yield players[pid]


def aged(player: Player) -> int:
    """The age he will have once everybody is a year older (at most the oldest age of the scale)."""
    return min(D.AGE_MAX, player.age + 1)


# ----- the two rules as functions of numbers -----

def retire_chance(age: int, rating: int) -> int:
    """The chance, per mille, that a player of this age (after the year's aging) and rating retires (design 6.3). Nothing under 30
    (invariant I1), 1000 at the oldest age (no draw is made for it), else (age - 29) per year less the rating's points over 70."""
    if age < D.RETIRE_FROM_AGE:
        return 0
    if age >= D.AGE_MAX:
        return D.RETIRE_DRAW
    chance = (age - 29) * T.FR_RETIRE_PER_YEAR - (rating - D.RATING_NEUTRAL) * T.FR_RETIRE_PER_POINT
    return max(0, min(D.RETIRE_DRAW, chance))


def base_change(position: str, age: int, potential: str) -> int:
    """The yearly change before the spread and the development points (design 6.2): growth before the position's window by
    potential, little in it, and a decline that deepens by the year after it whatever the potential."""
    first, last = T.FR_PEAK[position]
    level = D.POTENTIALS.index(potential)               # high 0, average 1, low 2
    if age < first:
        return T.FR_GROWTH[level]
    if age <= last:
        return T.FR_IN_WINDOW[level]
    years = age - last                                  # 1 the first year after the window
    return -T.FR_DECLINE[min(years, len(T.FR_DECLINE)) - 1]


def clamp_rating(value: int) -> int:
    return max(D.RATING_MIN, min(D.RATING_MAX, value))


# ----- stage 2: aging and retirement -----

def plan_retirements(league: LeagueRecord, rnd) -> list:
    """The players who retire this offseason, in league order. One draw `below(1000)` for each player who will be 30 to 39 (the
    ones who will be 40 retire without a draw, the ones under 30 neither retire nor draw). Nothing is changed."""
    retiring = []
    for player in league_order(league):
        age = aged(player)
        if age >= D.AGE_MAX:
            retiring.append(player)
        elif age >= D.RETIRE_FROM_AGE and rnd.below(D.RETIRE_DRAW) < retire_chance(age, player.rating):
            retiring.append(player)
    return retiring


def apply_aging(league: LeagueRecord, retiring: list) -> None:
    """Everybody active is a year older with a season more (at most the scale's ends), then the retiring players leave their
    places: retired, the season he retired after, the team he last played for kept (history names it). Then the cap year turns
    (SX.8g, `contracts.turn_the_year`): a year off every contract, the dead money gone; a contract that runs out is left with 0 years
    for stage 7 (SX.8h, `resign.py`) to settle."""
    for player in list(league_order(league)):
        player.age = aged(player)
        player.seasons = min(99, player.seasons + 1)
    for player in retiring:
        league.rosters[player.team - 1][player.place] = 0
        player.status, player.left, player.place, player.points = "retired", league.season, -1, 0     # points are of no use now
        contracts.leave(player)
    contracts.turn_the_year(league)


# ----- stage 3: progression and regression -----

@dataclass(frozen=True)
class Change:
    """One player's new rating (the old one is still on the player until `apply_development`)."""
    player: Player
    new: int

    @property
    def delta(self) -> int:
        return self.new - self.player.rating


def plan_development(league: LeagueRecord, rnd) -> list:
    """The new rating of every active player, in league order: base + below(5) - 2 + his development points, kept in 40 to 99.
    One draw for each player. Nothing is changed."""
    span, low = T.FR_PROGRESS_NOISE
    plan = []
    for player in league_order(league):
        change = base_change(player.pos, player.age, player.potential) + rnd.below(span) + low + player.points
        plan.append(Change(player, clamp_rating(player.rating + change)))
    return plan


def apply_development(plan: list) -> None:
    for change in plan:
        player = change.player
        player.rating = change.new
        player.peak = max(player.peak, change.new)
        player.points = 0


@dataclass(frozen=True)
class DevelopmentSummary:
    """What the player's team heard in stage 3: counts, the most improved and the biggest drop (None when there is none)."""
    improved: int
    declined: int
    same: int
    best: Change | None
    worst: Change | None


def summarize(plan: list, team: int) -> DevelopmentSummary:
    """The team's changes: the first of equal ones in the roster's order is named (design 6.2 names no tie rule)."""
    own = [change for change in plan if change.player.team == team]
    improved = [c for c in own if c.delta > 0]
    declined = [c for c in own if c.delta < 0]
    best = max(improved, key=lambda c: c.delta) if improved else None          # max keeps the first of equals
    worst = min(declined, key=lambda c: c.delta) if declined else None
    return DevelopmentSummary(len(improved), len(declined), len(own) - len(improved) - len(declined), best, worst)


# ----- the places -----

def place_by_rating(league: LeagueRecord, team: int | None = None) -> None:
    """In each group the best player takes the first place (design 7.6: the order does not change play, it makes the roster
    speech start with the best); equal ratings keep the lower ID first. A group with an empty place keeps it last."""
    for t in ([team] if team else range(1, D.TEAMS + 1)):
        roster = league.rosters[t - 1]
        for position, places in D.PLACES_OF.items():
            players = sorted((league.players[roster[i]] for i in places if roster[i]), key=lambda p: (-p.rating, p.id))
            for index, player in zip(places, players):
                roster[index] = player.id
                player.place = index
            for index in places[len(players):]:
                roster[index] = 0


def fill_places(league: LeagueRecord, rnd, surnames: list) -> int:
    """The fill of the roster cut (design 7.6, stage 5): every empty place gets an undrafted rookie, in team order and place order,
    the name, the rating, the potential as design 12 item 6 draws them for the fill. Returns how many. The places are then put in
    rating order. (SX.8c used it as a stand-in at the end of stage 3, before the draft existed.)"""
    used = {player.name for player in league.players.values() if player.status == "active"}
    high, average = T.FR_ROOKIE_POTENTIAL_SHARES
    count = 0
    for team in range(1, D.TEAMS + 1):
        roster = league.rosters[team - 1]
        for index, pid in enumerate(roster):
            if pid:
                continue
            position = D.POSITION_OF_PLACE[index]
            name = draw_name(rnd, surnames, used)
            used.add(name)
            base, span = T.FR_FILL_RATING if D.GROUP_SIZE[position] >= 3 else T.FR_FILL_RATING_SMALL
            rating = clamp_rating(base + rnd.below(span))
            roll = rnd.below(100)
            potential = "high" if roll < high else "average" if roll < average else "low"
            player = Player(league.next_id, name, position, rating, potential, D.AGE_MIN + 1, 0, rating, None, 0, "active", 0,
                            team, index, T.FR_MIN_SALARY, T.FR_FILL_YEARS)       # SX.8g: an undrafted rookie signs for the minimum
            league.players[player.id] = player
            roster[index] = player.id
            league.next_id += 1
            count += 1
    place_by_rating(league)
    return count


def drop_the_unkept(league: LeagueRecord) -> int:
    """Retired and released players history does not need are dropped at the end of the offseason (design 4.3): the player's own
    team's and every star (a peak of `STAR_PEAK` or more) stay. Player IDs are never reused. Returns how many were dropped."""
    gone = [pid for pid, p in league.players.items()
            if p.status != "active" and p.team != league.team and p.peak < D.STAR_PEAK]
    for pid in gone:
        del league.players[pid]
    return len(gone)
