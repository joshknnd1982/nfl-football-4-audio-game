"""Trades of the Franchise: the rules as plain functions (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8j, D-070): the situation of a team, the value
rule, the picks that even a trade, the computer teams' search, the player's proposals, the league record of format 5 and the draft that honors traded picks.
The flow on the program rig is test_fr_trade_flow.py.

The hand-worked numbers below use the values of the fixture `values`: the shipped values of SX.8j, set here so that a later calibration moves only
`test_the_shipped_values_are_the_measured_ones` (B-X52), except a margin of 2 rating points (24 for a quarterback, whose trades the cases are built on) and up to 4
trades a week (so that the search's limits have room to be tested).
"""
import copy
import json
import random

import pytest
from drrig import SURNAMES

from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import todo
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import OFFSEASON, SEASON, LeagueError, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5                      # the player's team
CONTENDER, REBUILDER = 4, 9
SHIPPED = {"FR_TRADE_FIRST_WEEK": 4, "FR_TRADE_LAST_WEEK": 9, "FR_TRADE_MIN_GAMES": 3, "FR_TRADE_CONTEND": 2, "FR_TRADE_REBUILD": 2,
           "FR_TRADE_MARGIN": 12, "FR_TRADE_PICKS_MAX": 2, "FR_TRADE_VETERAN_AGE": 28, "FR_TRADE_UPGRADE": 3, "FR_TRADE_SEASON_MAX": 2,
           "FR_TRADE_WEEK_MAX": 1, "FR_TRADE_LIST": 5, "FR_TRADE_NEWS": 2, "FR_TRADE_YOUNG": 25, "FR_TRADE_MONEY_DIVISOR": 20,
           "FR_TRADE_AGE": {"contend": ((24, 80), (29, 100), (32, 100), (99, 80)), "middle": ((24, 100), (29, 100), (32, 80), (99, 55)),
                            "rebuild": ((24, 130), (29, 100), (32, 60), (99, 30))},
           "FR_TRADE_POTENTIAL": {"high": 115, "average": 100, "low": 85},
           "FR_TRADE_PICK_SHARE": {"contend": 70, "middle": 100, "rebuild": 130},
           "FR_TRADE_PICK_VALUE": (48, 38, 29, 19, 10, 3, 1)}


TESTED = dict(SHIPPED, FR_TRADE_MARGIN=2, FR_TRADE_WEEK_MAX=4)


@pytest.fixture(autouse=True)
def values(monkeypatch):
    for name, value in TESTED.items():
        monkeypatch.setattr(T, name, copy.deepcopy(value))


def test_the_shipped_values_are_the_measured_ones():
    """The values of SX.8j (D-070): the window from the NFL's deadline, the margin and the weekly limit of the sweep, the picks' worth measured
    (work/measure_pick_value_sx8j.txt)."""
    import importlib
    shipped = importlib.reload(T)
    for name, value in SHIPPED.items():
        assert getattr(shipped, name) == value, name


def fresh(seed=3, team=TEAM):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def flat_league(seed=3, team=TEAM):
    """A league in which no trade is possible: every player rated 60, 25 years old, average potential, at his market price for two years (nobody is a
    veteran, so no rebuilding team offers anybody). In the season, week 1 (the record's own check holds); the tests pass their own records."""
    league = fresh(seed, team)
    for p in league.players.values():
        p.rating = p.peak = 60
        p.age, p.potential = 25, "average"
        p.salary, p.years = CT.market_salary(p.pos, 60), 2
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    league.stage, league.gtp = SEASON, 1
    return league


def standing():
    out = [2, 2] * D.TEAMS
    out[2 * (CONTENDER - 1)], out[2 * (CONTENDER - 1) + 1] = 3, 1          # 3 and 1: contending
    out[2 * (REBUILDER - 1)], out[2 * (REBUILDER - 1) + 1] = 1, 3          # 1 and 3: rebuilding
    return out


def quarterback(league, team):
    return league.player_at(team, D.PLACES_OF["QB"][0])


def set_player(player, rating, age, potential="average", salary=None, years=2):
    player.rating, player.peak, player.age, player.potential = rating, max(player.peak, rating), age, potential
    player.salary = CT.market_salary(player.pos, rating) if salary is None else salary
    player.years = years
    return player


def scenario(young_rating=62, potential="average"):
    """The contender's young quarterback (age 23) and the rebuilder's veteran (rated 80, age 30): the one trade the search can find."""
    league = flat_league()
    set_player(quarterback(league, CONTENDER), young_rating, 23, potential)
    set_player(quarterback(league, REBUILDER), 80, 30)
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    return league


# ----- the situation of a team -----

@pytest.mark.parametrize("wins, losses, want", [(0, 0, TR.MIDDLE), (2, 0, TR.MIDDLE), (3, 1, TR.CONTEND), (2, 1, TR.MIDDLE), (1, 3, TR.REBUILD),
                                                (1, 2, TR.MIDDLE), (2, 2, TR.MIDDLE), (8, 0, TR.CONTEND), (0, 8, TR.REBUILD), (4, 3, TR.MIDDLE)])
def test_the_situation_of_a_team_comes_from_its_record(wins, losses, want):
    values = [2, 2] * D.TEAMS
    values[0], values[1] = wins, losses
    assert TR.situation(values, 1) == want


# ----- the value rule (hand-worked) -----

def test_a_veterans_worth_and_value_in_each_situation():
    league = flat_league()
    qb = set_player(quarterback(league, 1), 80, 30)                       # 12 x (80 - 55) = 300: the fill's middle of a small group is 55
    assert TR.worth(qb) == 300
    assert (TR.player_value(qb, TR.CONTEND), TR.player_value(qb, TR.MIDDLE), TR.player_value(qb, TR.REBUILD)) == (300, 240, 180)
    old = set_player(quarterback(league, 2), 80, 34)
    assert (TR.player_value(old, TR.CONTEND), TR.player_value(old, TR.MIDDLE), TR.player_value(old, TR.REBUILD)) == (240, 165, 90)


def test_youth_and_potential_count_for_a_young_player():
    league = flat_league()
    qb = set_player(quarterback(league, 1), 70, 23, "high")              # 12 x 15 = 180
    assert TR.player_value(qb, TR.REBUILD) == 180 * 130 // 100 * 115 // 100 == 269
    assert TR.player_value(qb, TR.CONTEND) == 180 * 80 // 100 * 115 // 100 == 165
    qb.age = 26                                                            # past FR_TRADE_YOUNG: the potential no longer counts
    assert TR.player_value(qb, TR.REBUILD) == 180


def test_a_contract_under_his_market_price_adds_value_and_one_over_it_takes_it_away_the_same_size():
    league = flat_league()
    market = CT.market_salary("QB", 80)
    cheap = set_player(quarterback(league, 1), 80, 30, salary=market - 50, years=2)       # 50 tenths a year for 2 years: 100 / 20 = 5 points
    dear = set_player(quarterback(league, 2), 80, 30, salary=market + 50, years=2)
    assert TR.player_value(cheap, TR.CONTEND) == 305 and TR.player_value(dear, TR.CONTEND) == 295
    dear.salary = market + 59                                              # 118 / 20 rounds toward zero: 5, not 6
    assert TR.player_value(dear, TR.CONTEND) == 295


def test_a_player_worth_less_than_his_replacement_has_no_value_but_his_contract():
    league = flat_league()
    back = league.player_at(1, D.PLACES_OF["RB"][0])
    set_player(back, 45, 28)                                               # 2 x (45 - 50) < 0
    assert TR.worth(back) == -10 and TR.player_value(back, TR.MIDDLE) == 0
    back.salary = CT.market_salary("RB", 45) - 40
    assert TR.player_value(back, TR.MIDDLE) == 4                            # 40 x 2 / 20


@pytest.mark.parametrize("how, want", [(TR.CONTEND, (33, 26, 20, 13, 7, 2, 0)), (TR.MIDDLE, (48, 38, 29, 19, 10, 3, 1)),
                                       (TR.REBUILD, (62, 49, 37, 24, 13, 3, 1))])
def test_a_picks_value_by_round_and_situation(how, want):
    assert tuple(TR.pick_value(r, how) for r in range(1, 8)) == want


# ----- the picks that even a trade -----

def test_cover_takes_the_cheapest_pick_that_is_enough():
    picks = [(r, 7) for r in range(1, 8)]
    assert TR.cover(0, picks, TR.MIDDLE) == ()
    assert TR.cover(-5, picks, TR.MIDDLE) == ()
    assert TR.cover(10, picks, TR.MIDDLE) == ((5, 7),)                     # round 5 is worth 10: the cheapest that is enough
    assert TR.cover(11, picks, TR.MIDDLE) == ((4, 7),)
    assert TR.cover(48, picks, TR.MIDDLE) == ((1, 7),)


def test_cover_adds_a_second_pick_and_gives_up_past_the_limit():
    picks = [(r, 7) for r in range(1, 8)]
    assert TR.cover(60, picks, TR.MIDDLE) == ((1, 7), (4, 7))              # round 1 (48), then the cheapest for the 12 left: round 4 (19)
    assert TR.cover(86, picks, TR.MIDDLE) == ((1, 7), (2, 7))
    assert TR.cover(87, picks, TR.MIDDLE) is None                          # two picks at most
    assert TR.cover(30, [(6, 7), (7, 7)], TR.MIDDLE) is None
    assert TR.cover(30, [], TR.MIDDLE) is None


# ----- the computer teams' agreement -----

def test_build_with_no_picks_when_both_teams_gain_the_margin():
    league = scenario(young_rating=70, potential="high")
    how = TR.situations(standing())
    trade = TR.build(league, CONTENDER, REBUILDER, quarterback(league, CONTENDER), quarterback(league, REBUILDER), how)
    assert trade == TR.Trade(CONTENDER, REBUILDER, quarterback(league, CONTENDER).id, quarterback(league, REBUILDER).id)
    assert TR.gain(league, trade, CONTENDER, TR.CONTEND) == 300 - 165 and TR.gain(league, trade, REBUILDER, TR.REBUILD) == 269 - 180


def test_build_adds_the_contenders_picks_when_the_rebuilder_would_lose():
    league = scenario()
    how = TR.situations(standing())
    trade = TR.build(league, CONTENDER, REBUILDER, quarterback(league, CONTENDER), quarterback(league, REBUILDER), how)
    # the margin of a quarterback is 2 x 12 = 24; the rebuilder: the young quarterback 12 x 7 x 130 percent = 109, the veteran 180: short by 24 + 71 = 95;
    # round 1 (62 for a rebuilder), then the cheapest for the 33 left, round 3 (37)
    assert TR.margin_of("QB") == 24 and TR.margin_of("DL") == 4
    assert trade.picks_a == ((1, CONTENDER), (3, CONTENDER)) and trade.picks_b == ()
    assert TR.gain(league, trade, REBUILDER, TR.REBUILD) == 109 - 180 + 62 + 37 == 28
    assert TR.gain(league, trade, CONTENDER, TR.CONTEND) == 300 - 67 - 33 - 20 == 180


def test_build_says_no_when_two_picks_cannot_make_it_up():
    league = scenario(young_rating=56)
    how = TR.situations(standing())
    assert TR.build(league, CONTENDER, REBUILDER, quarterback(league, CONTENDER), quarterback(league, REBUILDER), how) is None


def test_build_says_no_when_the_picks_would_take_the_payer_under_the_margin():
    """The contender gains 48 - 9 = 39 before the picks; the rebuilder is short by 24 + 13 = 37, which round 3 makes up (37 for it), and round 3 costs the
    contender 20: 19, under the margin of 24, so no trade (the mutation check of SX.8j: a build that does not check after the picks)."""
    league = flat_league()
    set_player(quarterback(league, CONTENDER), 56, 23)
    set_player(quarterback(league, REBUILDER), 59, 30)
    how = TR.situations(standing())
    plain = TR.Trade(CONTENDER, REBUILDER, quarterback(league, CONTENDER).id, quarterback(league, REBUILDER).id)
    assert TR.gain(league, plain, CONTENDER, TR.CONTEND) == 39 and TR.gain(league, plain, REBUILDER, TR.REBUILD) == -13
    assert TR.build(league, CONTENDER, REBUILDER, quarterback(league, CONTENDER), quarterback(league, REBUILDER), how) is None


def test_the_potential_counts_up_to_and_with_the_last_young_age():
    league = flat_league()
    qb = set_player(quarterback(league, 1), 70, T.FR_TRADE_YOUNG, "high")    # 25: still young
    assert TR.player_value(qb, TR.MIDDLE) == 180 * 115 // 100
    qb.age = T.FR_TRADE_YOUNG + 1
    assert TR.player_value(qb, TR.MIDDLE) == 180


# ----- why a trade cannot be made -----

def test_the_reasons_a_trade_cannot_be_made():
    league = scenario()
    a, b = quarterback(league, CONTENDER), quarterback(league, REBUILDER)
    good = TR.Trade(CONTENDER, REBUILDER, a.id, b.id, ((1, CONTENDER),), ())
    assert TR.problems(league, good, 5) is None
    assert TR.problems(league, good, 10) == "outside the trade window"
    assert TR.problems(league, good, 0) == "outside the trade window"
    league.stage = OFFSEASON
    assert TR.problems(league, good, 5) == "outside the trade window"
    league.stage = SEASON
    back = league.player_at(REBUILDER, D.PLACES_OF["RB"][0])
    assert TR.problems(league, TR.Trade(CONTENDER, REBUILDER, a.id, back.id), 5) == "players of different positions"
    assert TR.problems(league, TR.Trade(CONTENDER, CONTENDER, a.id, b.id), 5) == "the teams"
    assert TR.problems(league, TR.Trade(REBUILDER, CONTENDER, a.id, b.id), 5) == "a player who is not on his team"
    assert TR.problems(league, TR.Trade(CONTENDER, REBUILDER, a.id, b.id, ((1, REBUILDER),), ()), 5) == "a pick the team does not own"
    assert TR.problems(league, TR.Trade(CONTENDER, REBUILDER, a.id, b.id, ((1, CONTENDER), (2, CONTENDER), (3, CONTENDER)), ()), 5) == "too many picks"
    assert TR.problems(league, TR.Trade(CONTENDER, REBUILDER, a.id, b.id, ((1, CONTENDER), (1, CONTENDER)), ()), 5) == "too many picks"
    league.trades["log"].append([4, 1, 2, b.id, 1, [], [], TR.KIND_COMPUTER])
    assert TR.problems(league, good, 5) == "a player traded already this season"


def test_a_trade_that_would_put_a_team_over_the_cap_cannot_be_made_and_one_just_under_it_can():
    league = scenario()
    a, b = quarterback(league, CONTENDER), quarterback(league, REBUILDER)
    trade = TR.Trade(CONTENDER, REBUILDER, a.id, b.id)
    for player in league.active_of(CONTENDER):                            # the contender's other contracts rise until the trade fills its cap exactly
        need = T.FR_CAP - TR.cap_after(league, trade, CONTENDER)
        if player is not a and need > 0:
            player.salary += min(need, T.FR_MAX_SALARY - player.salary)
    assert TR.cap_after(league, trade, CONTENDER) == T.FR_CAP == CT.cap_used(league, CONTENDER) - a.salary + b.salary
    assert TR.problems(league, trade, 5) is None
    b.salary += 1                                                         # one tenth of a million more: over the cap
    assert TR.problems(league, trade, 5) == "over the cap"


# ----- a trade made -----

def test_a_trade_swaps_the_players_moves_the_picks_logs_it_and_brings_the_strengths_up_to_date():
    league = scenario()
    a, b = quarterback(league, CONTENDER), quarterback(league, REBUILDER)
    sums = list(league.sums)
    trade = TR.Trade(CONTENDER, REBUILDER, a.id, b.id, ((1, CONTENDER), (2, CONTENDER)), ())
    TR.execute(league, trade, 5, TR.KIND_COMPUTER)
    assert (a.team, b.team) == (REBUILDER, CONTENDER) and quarterback(league, CONTENDER) is b and quarterback(league, REBUILDER) is a
    assert TR.owner(league, 1, CONTENDER) == REBUILDER and TR.owner(league, 2, CONTENDER) == REBUILDER and TR.owner(league, 3, CONTENDER) == CONTENDER   # (the trade made by hand)
    assert TR.picks_of(league, REBUILDER)[:3] == [(1, REBUILDER), (1, CONTENDER), (2, REBUILDER)]
    assert (1, CONTENDER) not in TR.picks_of(league, CONTENDER)
    assert league.trades["log"] == [[5, CONTENDER, REBUILDER, a.id, b.id, [[1, CONTENDER], [2, CONTENDER]], [], TR.KIND_COMPUTER]]
    assert league.sums[CONTENDER - 1] == sums[CONTENDER - 1] + 12 * (80 - 62) == league.strength_sum(CONTENDER)
    assert league.sums[REBUILDER - 1] == sums[REBUILDER - 1] - 12 * 18 and league.sums[0] == sums[0]
    assert TR.traded_this_season(league) == {a.id, b.id} and TR.trades_of(league, CONTENDER) == 1 and TR.trades_of(league, 1) == 0
    league.check()                                                        # every place filled, each player in one place of his position
    again = LeagueRecord.from_json(league.to_json())
    assert again.trades == league.trades and again.to_json() == league.to_json()


def test_a_pick_traded_back_to_its_team_leaves_the_table():
    league = flat_league()
    TR.move_pick(league, (3, 7), 12)
    assert league.trades["picks"] == [[3, 7, 12]] and TR.owner(league, 3, 7) == 12
    TR.move_pick(league, (3, 7), 20)
    assert league.trades["picks"] == [[3, 7, 20]]
    TR.move_pick(league, (3, 7), 7)
    assert league.trades["picks"] == [] and TR.owner(league, 3, 7) == 7


def test_a_trade_puts_the_better_player_first_in_his_new_group():
    league = flat_league()
    giver = league.player_at(REBUILDER, D.PLACES_OF["DL"][5])               # the sixth lineman of the rebuilder, a veteran rated 75
    set_player(giver, 75, 30)
    taker = league.player_at(CONTENDER, D.PLACES_OF["DL"][2])
    TR.execute(league, TR.Trade(CONTENDER, REBUILDER, taker.id, giver.id), 5, TR.KIND_COMPUTER)
    assert league.player_at(CONTENDER, D.PLACES_OF["DL"][0]) is giver and giver.place == D.PLACES_OF["DL"][0]
    league.check()


# ----- the search: the computer teams' trades of a week -----

def test_the_search_finds_the_one_possible_trade():
    league = scenario()
    found = TR.search(league, 5, standing())
    a, b = quarterback(league, CONTENDER), quarterback(league, REBUILDER)
    assert found == [TR.Trade(CONTENDER, REBUILDER, a.id, b.id, ((1, CONTENDER), (3, CONTENDER)), ())]
    assert a.team == CONTENDER                                            # the search changes nothing


def test_the_search_finds_nothing_in_a_league_without_veterans_and_outside_its_weeks():
    assert TR.search(flat_league(), 5, standing()) == []
    league = scenario()
    assert TR.search(league, 3, standing()) == [] and TR.search(league, 10, standing()) == []
    assert TR.search(league, 4, standing()) and TR.search(league, 9, standing())
    league.stage = OFFSEASON
    assert TR.search(league, 5, standing()) == []


def test_the_search_needs_a_contender_and_a_rebuilder():
    league = scenario()
    assert TR.search(league, 5, [2, 2] * D.TEAMS) == []                     # everybody middle
    both_contend = standing()
    both_contend[2 * (REBUILDER - 1)], both_contend[2 * (REBUILDER - 1) + 1] = 3, 1
    assert TR.search(league, 5, both_contend) == []


def test_the_search_wants_a_real_upgrade_and_a_veteran():
    league = scenario()
    quarterback(league, CONTENDER).rating = 78                             # 80 is only 2 better
    assert TR.search(league, 5, standing()) == []
    league = scenario()
    quarterback(league, REBUILDER).age = 27                                # not a veteran
    assert TR.search(league, 5, standing()) == []
    league = scenario()                                                    # the same trade by value, its veteran one year under the veteran's age
    T.FR_TRADE_VETERAN_AGE = 31
    assert TR.search(league, 5, standing()) == []
    T.FR_TRADE_VETERAN_AGE = 30
    assert len(TR.search(league, 5, standing())) == 1


def test_a_team_at_its_season_limit_and_a_player_traded_already_are_left_out():
    league = scenario()
    for k in range(T.FR_TRADE_SEASON_MAX):
        league.trades["log"].append([4, CONTENDER, 20 + k, league.player_at(20 + k, 0).id, league.player_at(CONTENDER, 0).id, [], [], 0])
    assert TR.search(league, 5, standing()) == []
    league = scenario()
    league.trades["log"].append([4, REBUILDER, 20, quarterback(league, REBUILDER).id, league.player_at(20, 33).id, [], [], 0])
    assert TR.search(league, 5, standing()) == []


def test_the_search_takes_the_trade_its_contender_gains_most_from_and_one_trade_a_team_a_week():
    league = scenario()
    second = 13                                                            # another rebuilder with a better, older veteran quarterback
    set_player(quarterback(league, second), 84, 33)
    values = standing()
    values[2 * (second - 1)], values[2 * (second - 1) + 1] = 0, 4
    found = TR.search(league, 5, values)
    assert len(found) == 1 and found[0].b == second and found[0].give_b == quarterback(league, second).id
    # the second rebuilder values its 33-year-old at 30 percent (104): it is short by 24 - (109 - 104) = 19, which round 4 makes up (24 for it)
    assert found[0].picks_a == ((4, CONTENDER),)
    assert TR.gain(league, found[0], CONTENDER, TR.CONTEND) == 348 * 80 // 100 - 67 - 13 == 198 > 180       # more than the first rebuilder's trade


def test_a_contender_takes_its_best_trade_with_a_rebuilder_not_the_first_one_found():
    """Two trades with the same rebuilder: running backs come first in the order of the positions (a gain of 18 value, 9 rating points of a back) and quarterbacks
    later (15 rating points of a quarterback): the quarterbacks' trade is taken (the mutation check of SX.8j: the first trade found)."""
    league = scenario()
    young_back = league.player_at(CONTENDER, D.PLACES_OF["RB"][0])
    old_back = league.player_at(REBUILDER, D.PLACES_OF["RB"][0])
    set_player(young_back, 70, 23)
    set_player(old_back, 75, 30)
    found = TR.search(league, 5, standing())
    assert [(t.give_a, t.give_b) for t in found] == [(quarterback(league, CONTENDER).id, quarterback(league, REBUILDER).id)]
    back_trade = TR.build(league, CONTENDER, REBUILDER, young_back, old_back, TR.situations(standing()))
    assert back_trade is not None and TR.points(TR.gain(league, back_trade, CONTENDER, TR.CONTEND), "RB") < TR.points(TR.gain(league, found[0], CONTENDER, TR.CONTEND), "QB")


def test_trades_of_different_positions_are_compared_by_rating_points_of_the_position_not_by_value():
    """A back's trade worth 31 value is 15.5 rating points of a back (weight 2); the quarterbacks' 180 is 15 of a quarterback (weight 12): the back's trade is
    taken although its value is smaller (the mutation check of SX.8j: a gain compared in plain value)."""
    league = scenario()
    young_back = league.player_at(CONTENDER, D.PLACES_OF["RB"][0])
    old_back = league.player_at(REBUILDER, D.PLACES_OF["RB"][0])
    set_player(young_back, 60, 23)
    set_player(old_back, 80, 30)
    (found,) = TR.search(league, 5, standing())
    assert (found.give_a, found.give_b, found.picks_a) == (young_back.id, old_back.id, ((4, CONTENDER),))
    assert TR.gain(league, found, CONTENDER, TR.CONTEND) == 44 - 13 and TR.points(31, "RB") == 15500 > TR.points(180, "QB") == 15000


def test_the_weeks_trades_do_not_depend_on_each_other_and_at_most_the_weeks_number_are_made():
    league = scenario()
    # four more pairs, each a contender with a young quarterback and a rebuilder with a veteran, so the search has five trades to make
    values = standing()
    pairs = [(14, 15), (16, 17), (18, 19), (21, 22)]
    for contender, rebuilder in pairs:
        set_player(quarterback(league, contender), 62, 23)
        set_player(quarterback(league, rebuilder), 80, 30)
        values[2 * (contender - 1)], values[2 * (contender - 1) + 1] = 3, 1
        values[2 * (rebuilder - 1)], values[2 * (rebuilder - 1) + 1] = 1, 3
    found = TR.search(league, 5, values)
    assert len(found) == T.FR_TRADE_WEEK_MAX
    teams = [t for trade in found for t in (trade.a, trade.b)]
    assert len(teams) == len(set(teams))                                   # a team takes one trade a week
    step = copy.deepcopy(league)
    for trade in found:                                                    # made one after the other, each is still what it was
        assert TR.problems(step, trade, 5) is None
        TR.execute(step, trade, 5, TR.KIND_COMPUTER)


def test_the_order_of_the_search_turns_with_the_week_and_the_season():
    firsts = {TR.rotation(season, week)[0] for season in range(1, 9) for week in range(4, 10)}
    assert len(firsts) >= 24
    assert sorted(TR.rotation(3, 7)) == list(range(1, D.TEAMS + 1))


def test_week_makes_the_trades_of_two_computer_teams_and_offers_the_players_one():
    league = scenario()
    made, offers = TR.week(league, 5, standing())
    assert len(made) == 1 and offers == [] and quarterback(league, CONTENDER).rating == 80
    league = scenario()
    league.team = REBUILDER                                                # the player's team is the rebuilder: the trade waits for his answer
    made, offers = TR.week(league, 5, standing())
    assert made == [] and len(offers) == 1 and quarterback(league, CONTENDER).rating == 62
    league.team = 0                                                        # the fast run has no player's team
    made, offers = TR.week(copy.deepcopy(scenario()), 5, standing())
    assert len(made) == 1


def test_an_offer_the_staff_accepts_leaves_the_league_the_fast_run_makes_one_code_path():
    """Research G: the computer teams' trades never depend on how the player watches. The same week with the player's team in the trade and the staff
    accepting its offer gives the league the fast run (no player's team) gives: the same rosters, picks and strengths; only the log's kind says who agreed."""
    by_staff = scenario()
    by_staff.team = REBUILDER
    _made, (offer,) = TR.week(by_staff, 5, standing())
    by_staff.todo.append(todo.trade_item(by_staff, 5, offer))
    todo.apply_answer(by_staff, by_staff.todo[0], 0)
    unwatched = scenario()
    unwatched.team = 0
    made, offers = TR.week(unwatched, 5, standing())
    assert offers == [] and made == [offer]
    assert by_staff.rosters == unwatched.rosters and by_staff.sums == unwatched.sums and by_staff.trades["picks"] == unwatched.trades["picks"]
    assert [row[:7] for row in by_staff.trades["log"]] == [row[:7] for row in unwatched.trades["log"]]
    assert (by_staff.trades["log"][0][7], unwatched.trades["log"][0][7]) == (TR.KIND_OFFER, TR.KIND_COMPUTER)


def test_the_rebuilder_offers_its_best_veteran_of_a_position():
    """Two veteran linemen of the rebuilder (80 and 75, both 30): the search trades for the better one (the mutation check: the worst veteran)."""
    league = flat_league()
    better = set_player(league.player_at(REBUILDER, D.PLACES_OF["DL"][0]), 80, 30)
    worse = set_player(league.player_at(REBUILDER, D.PLACES_OF["DL"][1]), 75, 30)
    set_player(league.player_at(CONTENDER, D.PLACES_OF["DL"][0]), 66, 23, "high")
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    found = TR.search(league, 5, standing())
    assert [t.give_b for t in found] == [better.id] and worse.team == REBUILDER


# ----- the news of trades (NWX) -----

def test_the_news_of_a_trade_names_the_better_player_and_the_team_he_left():
    from nfl4.extras.franchise import news
    league = scenario()
    trade = TR.Trade(CONTENDER, REBUILDER, quarterback(league, CONTENDER).id, quarterback(league, REBUILDER).id)
    (event,) = news.trade_events(league, [trade])
    assert (event.pool, event.team, event.other, event.player) == ("NWX", REBUILDER, CONTENDER, quarterback(league, REBUILDER))
    reverse = TR.Trade(REBUILDER, CONTENDER, quarterback(league, REBUILDER).id, quarterback(league, CONTENDER).id)
    (again,) = news.trade_events(league, [reverse])
    assert (again.team, again.other, again.player) == (REBUILDER, CONTENDER, quarterback(league, REBUILDER))


def test_at_most_the_news_number_of_trades_is_told_the_best_player_first():
    from nfl4.extras.franchise import news
    league = flat_league()
    made = []
    for k, (a, b, rating) in enumerate(((1, 2, 70), (3, 4, 85), (5, 6, 78))):
        star = set_player(league.player_at(b, D.PLACES_OF["WR"][k]), rating, 30)
        made.append(TR.Trade(a, b, league.player_at(a, D.PLACES_OF["WR"][k]).id, star.id))
    events = news.trade_events(league, made)
    assert T.FR_TRADE_NEWS == 2 and [e.player.rating for e in events] == [85, 78] and [e.team for e in events] == [4, 6]


def test_the_trades_take_their_place_after_his_own_news_and_inside_the_weeks_limit():
    from nfl4.extras.franchise import news
    own, big, upset, close = news.Event("NWY", 1, n=3), news.Event("NWB", 2, 3), news.Event("NWU", 4, 5), news.Event("NWC", 6, 7)
    trade_a, trade_b = news.Event("NWX", 8, 9), news.Event("NWX", 10, 11)
    assert news.with_trades([own, big, upset, close], [trade_a, trade_b]) == [own, trade_a, trade_b, big]
    assert news.with_trades([big, upset, close], [trade_a]) == [trade_a, big, upset, close]
    assert news.with_trades([own, big, upset, close], []) == [own, big, upset, close]
    assert len(news.with_trades([own, big, upset, close, close], [trade_a, trade_b])) == T.FR_NEWS_MAX


# ----- the player's proposals -----

def test_the_block_offers_are_the_teams_that_gain_with_their_picks_added_best_first():
    league = scenario(young_rating=70, potential="high")
    league.team = CONTENDER
    young = quarterback(league, CONTENDER)
    offers = TR.block_offers(league, CONTENDER, young, standing(), 5)
    assert len(offers) == T.FR_TRADE_LIST and [value for _t, value in offers] == sorted((value for _t, value in offers), reverse=True)
    trade, value = offers[0]
    # the rebuilder gains 269 - 180 = 89; round 1 (62 for it) leaves 27, over the margin of 24; round 2 to 5 would each leave less than 24;
    # round 6 (3) leaves 24: two picks, the most a side adds
    assert trade.b == REBUILDER and trade.picks_b == ((1, REBUILDER), (6, REBUILDER)) and trade.picks_a == ()
    assert value == 300 - 165 + 33 + 2
    for other, gain_for_him in offers[1:]:                                 # every other team's quarterback (60, 25) is worth less to him than his own
        assert other.b != REBUILDER and gain_for_him < 0 and TR.gain(league, other, other.b, TR.MIDDLE) >= TR.margin_of("QB")


def test_nobody_offers_for_a_player_traded_this_season():
    league = scenario(young_rating=70, potential="high")
    young = quarterback(league, CONTENDER)
    league.trades["log"].append([4, CONTENDER, 20, young.id, league.player_at(20, 33).id, [], [], 0])
    assert TR.block_offers(league, CONTENDER, young, standing(), 5) == []


def test_ask_names_the_picks_the_other_team_wants_or_says_no():
    league = scenario()
    league.team = CONTENDER
    young, veteran = quarterback(league, CONTENDER), quarterback(league, REBUILDER)
    trade = TR.ask(league, CONTENDER, young, veteran, standing(), 5)
    assert trade == TR.Trade(CONTENDER, REBUILDER, young.id, veteran.id, ((1, CONTENDER), (3, CONTENDER)), ())
    young.rating = 56
    assert TR.ask(league, CONTENDER, young, veteran, standing(), 5) is None
    back = league.player_at(CONTENDER, D.PLACES_OF["RB"][0])
    assert TR.ask(league, CONTENDER, back, veteran, standing(), 5) is None   # not the same position
    assert TR.ask(league, CONTENDER, young, veteran, standing(), 10) is None  # after the deadline


def test_ask_needs_no_picks_when_the_other_team_gains_anyway():
    league = scenario(young_rating=70, potential="high")
    young, veteran = quarterback(league, CONTENDER), quarterback(league, REBUILDER)
    assert TR.ask(league, CONTENDER, young, veteran, standing(), 5) == TR.Trade(CONTENDER, REBUILDER, young.id, veteran.id)


# ----- the to-do item of an offer -----

def test_an_offers_item_makes_the_trade_on_its_first_answer_and_nothing_on_its_second():
    league = scenario()
    league.team = REBUILDER
    _made, (offer,) = TR.week(league, 5, standing())
    item = todo.trade_item(league, 5, offer)
    league.todo.append(item)
    assert todo.answer_count(league, item) == 2 and todo.is_do_nothing(league, item, 1)
    copy_league = copy.deepcopy(league)
    assert todo.apply_answer(copy_league, copy_league.todo[0], 1) is None
    assert copy_league.todo == [] and quarterback(copy_league, REBUILDER).rating == 80
    made = todo.apply_answer(league, item, 0)
    assert made == offer and league.todo == [] and quarterback(league, REBUILDER).rating == 62
    assert league.trades["log"][0][7] == TR.KIND_OFFER


def test_an_offer_that_can_no_longer_be_made_makes_nothing():
    league = scenario()
    league.team = REBUILDER
    _made, (offer,) = TR.week(league, 5, standing())
    item = todo.trade_item(league, 5, offer)
    league.todo.append(item)
    quarterback(league, CONTENDER).salary += T.FR_CAP                      # the rebuilder would be over the cap now
    assert todo.apply_answer(league, item, 0) is None and league.trades["log"] == [] and league.todo == []


@pytest.mark.parametrize("mutate", [
    lambda t: t.update(trade=[1, 1, 5, 6, [], []]), lambda t: t.update(trade=[1, 2, 5, 6, [[1, 1]] * 3, []]),
    lambda t: t.update(trade=[1, 2, 5, 6, [[8, 1]], []]), lambda t: t.update(trade=[1, 2, 5]), lambda t: t.update(state=D.ITEM_SET),
    lambda t: t.update(trade=[0, 2, 5, 6, [], []]), lambda t: t.update(trade=[1, 2, 5, 6, [[1]], []]), lambda t: t.pop("trade"),
    lambda t: t.update(trade=[1, 2] + t["trade"][2:]), lambda t: t.update(trade=t["trade"][:2] + [999999] + t["trade"][3:]),
    lambda t: t.update(trade=t["trade"][:3] + [999998] + t["trade"][4:])])
def test_a_damaged_offer_item_is_refused(mutate):
    league = scenario()                                                    # the player's team is 5
    item = {"kind": D.TODO_TRADE, "season": 1, "week": 5, "state": D.ITEM_NEW,
            "trade": [5, 2, quarterback(league, 5).id, quarterback(league, 2).id, [], []]}
    league.todo.append(item)
    LeagueRecord.from_json(league.to_json())
    mutate(item)
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


# ----- the league record: format 5, its check and the migration -----

def test_format_five_round_trips_the_trades_and_a_format_four_file_loads_with_none():
    league = scenario()
    TR.execute(league, TR.search(league, 5, standing())[0], 5, TR.KIND_COMPUTER)
    data = json.loads(league.to_json())
    assert data["format"] == D.FORMAT == 9 and data["trades"] == league.trades     # (format 9 since SX.8n: the trades are format 5's)
    again = LeagueRecord.from_json(league.to_json())
    assert again.trades == league.trades and again.to_json() == league.to_json()
    old = json.loads(fresh().to_json())
    del old["trades"]
    old["format"] = 4
    loaded = LeagueRecord.from_json(json.dumps(old))
    assert loaded.trades == {"picks": [], "log": []} and json.loads(loaded.to_json())["format"] == D.FORMAT       # (9 since SX.8n)


def test_a_format_five_file_without_its_trades_is_damage():
    data = json.loads(fresh().to_json())
    del data["trades"]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


@pytest.mark.parametrize("mutate", [
    lambda l: setattr(l, "trades", None), lambda l: setattr(l, "trades", {"picks": []}), lambda l: l.trades.update(extra=1),
    lambda l: l.trades.update(picks=[[1, 3, 3]]), lambda l: l.trades.update(picks=[[8, 3, 4]]), lambda l: l.trades.update(picks=[[1, 3, 4], [1, 3, 5]]),
    lambda l: l.trades.update(picks=[[1, 3]]), lambda l: l.trades.update(picks=[[1, 33, 4]]), lambda l: l.trades.update(log=[[5, 1, 1, 1, 2, [], [], 0]]),
    lambda l: l.trades.update(log=[[10, 1, 2, 1, 2, [], [], 0]]), lambda l: l.trades.update(log=[[5, 1, 2, 999999, 2, [], [], 0]]),
    lambda l: l.trades.update(log=[[5, 1, 2, 1, 2, [], [], 4]]), lambda l: l.trades.update(log=[[5, 1, 2, 1, 2, [[1, 1]] * 3, [], 0]]),
    lambda l: l.trades.update(log=[[5, 1, 2, 1, 2, [[9, 1]], [], 0]]), lambda l: l.trades.update(log=[[5, 1, 2, 1, 2, [], []]]),
    lambda l: l.trades.update(log="x")])
def test_a_damaged_trades_record_is_refused(mutate):
    league = flat_league()
    mutate(league)
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_the_season_end_keeps_the_picks_and_drops_the_log():
    league = scenario()
    TR.execute(league, TR.search(league, 5, standing())[0], 5, TR.KIND_COMPUTER)
    picks = list(league.trades["picks"])
    TR.new_season(league)
    assert league.trades == {"picks": picks, "log": []}


# ----- the draft honors the traded picks -----

def draft_ready(league):
    """The league at the start of stage 4 (the season's history entry the draft order reads)."""
    league.stage, league.stage_no, league.gtp = OFFSEASON, D.STAGE_DRAFT, 0
    league.history = [{"season": league.season, "team": league.team, "coach": "Kim", "champion": 1, "runner_up": 2, "wins": [8] * D.TEAMS,
                       "losses": [8] * D.TEAMS, "finish": [0] * D.TEAMS, "playoff": [0, 0], "best": 1, "worst": 2, "top_points": None,
                       "big_win": None, "streak": None}]
    return league


def test_the_draft_makes_the_traded_picks_its_owners_and_empties_the_table():
    league = scenario()
    TR.execute(league, TR.search(league, 5, standing())[0], 5, TR.KIND_COMPUTER)
    draft_ready(league)
    draft = DR.Draft.create(league, GameRandom(random.Random(5)), SURNAMES)
    order = league.draft["order"]
    place = order.index(CONTENDER)
    assert draft.owners[place] == REBUILDER and draft.owners[D.TEAMS + place] == CONTENDER and draft.owners[2 * D.TEAMS + place] == REBUILDER
    assert league.trades["picks"] == []
    assert draft.picks_of(REBUILDER)[:3] == [(1, order.index(REBUILDER) + 1), (1, place + 1), (2, order.index(REBUILDER) + 1)]
    assert len(draft.picks_of(REBUILDER)) == 9 and len(draft.picks_of(CONTENDER)) == 5
    assert not draft.own_picks_only(CONTENDER) and not draft.own_picks_only(REBUILDER) and draft.own_picks_only(1)
    while not draft.done:
        _round, _pick, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    assert len(league.waiting_rookies(REBUILDER)) == 9 and len(league.waiting_rookies(CONTENDER)) == 5
    assert [row[0] for row in league.draft["picks"]] == draft.owners
    league.check()
    assert LeagueRecord.from_json(league.to_json()).draft == league.draft


def test_a_pick_made_by_the_wrong_team_is_refused():
    league = scenario()
    TR.execute(league, TR.search(league, 5, standing())[0], 5, TR.KIND_COMPUTER)
    draft_ready(league)
    draft = DR.Draft.create(league, GameRandom(random.Random(5)), SURNAMES)
    with pytest.raises(LeagueError):
        place = league.draft["order"].index(CONTENDER)
        while len(draft.picks) < place:
            _round, _pick, team = draft.next_slot()
            draft.make_pick(team, draft.best_for(team))
        draft.make_pick(CONTENDER, draft.best_for(CONTENDER))              # the contender's first pick is the rebuilder's now


@pytest.mark.parametrize("mutate", [lambda d: d.pop("owners"), lambda d: d.update(owners=[1] * 223), lambda d: d.update(owners=[0] * 224),
                                    lambda d: d.update(owners=["1"] * 224)])
def test_a_draft_record_with_damaged_owners_is_refused(mutate):
    league = draft_ready(flat_league())
    league.stage, league.gtp = OFFSEASON, 0
    DR.Draft.create(league, GameRandom(random.Random(5)), SURNAMES)
    LeagueRecord.from_json(league.to_json())
    mutate(league.draft)
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_a_draft_saved_by_format_four_gets_the_owners_of_the_draft_order():
    league = draft_ready(flat_league())
    draft = DR.Draft.create(league, GameRandom(random.Random(5)), SURNAMES)
    for _ in range(40):
        _round, _pick, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    data = json.loads(league.to_json())
    order = data["draft"]["order"]
    del data["draft"]["owners"], data["draft"]["comp"], data["draft"]["undrafted"], data["trades"]     # (what formats 5 to 8 added to a draft)
    del data["comp"], data["future_picks"], data["tags"]
    data["format"] = 4
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.draft["owners"] == [order[i % D.TEAMS] for i in range(D.DRAFT_PICKS)]
    loaded.staff = league.staff                    # SX.8l: a format-4 file gets a new league's staff (the migration of format 7); the rest is the file's
    assert loaded.to_json() == league.to_json()


def test_traded_picks_while_a_draft_is_in_progress_are_damage():
    league = draft_ready(flat_league())
    DR.Draft.create(league, GameRandom(random.Random(5)), SURNAMES)
    league.trades["picks"] = [[1, 3, 4]]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())
