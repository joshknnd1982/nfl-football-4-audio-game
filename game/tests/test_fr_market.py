"""Free agency of the Franchise: the rules as plain functions (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8i, D-068), and the league record that holds the
stage in progress (format 4). The stage on the program rig is test_fr_market_flow.py.
"""
import copy
import json
import random

import pytest
from drrig import SURNAMES

from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import market as M
from nfl4.extras.franchise import resign
from nfl4.extras.franchise.league import OFFSEASON, LeagueError, LeagueRecord, NewerFormat, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5


def fresh(seed=3, team=TEAM):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def make_free(league, team, index):
    """The player of this place was not signed again: a free agent of this offseason, no contract, no place (what `resign.let_go` does)."""
    player = league.player_at(team, index)
    resign.let_go(league, player)
    return player


def retire(league, team, index):
    """The place is empty because its player retired."""
    player = league.player_at(team, index)
    league.rosters[team - 1][index] = 0
    player.status, player.left, player.place = "retired", league.season, -1
    CT.leave(player)
    return player


def at_stage_eight(league, market=None):
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, D.STAGE_FREE_AGENCY, 0, [8, 8] * 32
    league.market = market
    return league


def market_league(seed=3, free=((2, 0), (3, 6), (7, 33), (9, 12), (11, 18)), empty_for=()):
    """A league at the start of free agency: these places were freed (their players are free agents) and these (team, place)s are empty because of a retirement."""
    league = fresh(seed)
    players = [make_free(league, team, index) for team, index in free]
    for team, index in empty_for:
        retire(league, team, index)
    at_stage_eight(league)
    return league, players


def with_rating(player, rating, seasons=6, age=26):
    player.rating, player.peak, player.seasons, player.age = rating, max(player.peak, rating), seasons, age
    return player


def open_group(league, team, position, count=1):
    """The first `count` places of the team's group are empty (retired)."""
    for index in D.PLACES_OF[position][:count]:
        if league.rosters[team - 1][index]:
            retire(league, team, index)


def squeeze(league, team, left):
    """Raise the salaries of the team's players until the room under the cap is exactly `left` (each up to the maximum salary)."""
    for pid in league.rosters[team - 1]:
        need = M.room(league, team) - left
        if need <= 0:
            break
        if pid:
            player = league.players[pid]
            player.salary += min(need, T.FR_MAX_SALARY - player.salary)
    assert M.room(league, team) == left


# ----- the minimum salary by seasons, the pool and the price -----

@pytest.mark.parametrize("seasons, least", [(0, 9), (1, 10), (2, 11), (3, 11), (4, 12), (6, 12), (7, 13), (20, 13)])
def test_the_minimum_salary_follows_the_nfl_table_by_seasons(seasons, least):
    assert CT.min_salary(seasons) == least and least >= T.FR_MIN_SALARY


def test_exclusive_rights_ask_the_minimum_of_the_seasons_for_one_year():
    league = fresh()
    player = league.player_at(TEAM, 33)
    player.rating = 90
    for seasons, least in ((0, 9), (1, 10), (2, 11)):
        player.seasons = seasons
        assert resign.asking(player) == (least, 1)


def test_the_pool_is_the_free_agents_of_this_offseason_best_first_and_no_one_else():
    league, free = market_league()
    stale = league.player_at(4, 0)
    resign.let_go(league, stale)
    stale.left = league.season - 1                                  # a star of an earlier offseason, kept for history
    retired = retire(league, 6, 3)
    order = M.pool(league)
    assert {p.id for p in order} == {p.id for p in free}
    assert stale not in order and retired not in order
    assert order == sorted(order, key=resign.value)
    assert all(p.status == "free" and p.left == league.season for p in order)


def test_a_free_agent_asks_what_he_asked_in_stage_seven_and_less_every_round_he_stays():
    league, free = market_league()
    player = with_rating(free[0], 70)
    salary, years = resign.asking(player)
    assert M.price(player, 1) == (salary, years)
    assert M.price(player, 2) == ((salary * 90 + 50) // 100, years)
    assert M.price(player, 3) == ((salary * 80 + 50) // 100, years)
    assert M.price(player, 3)[0] < M.price(player, 2)[0] < M.price(player, 1)[0]


def test_the_falling_price_never_goes_under_the_minimum_of_his_seasons():
    league, free = market_league()
    for seasons in (0, 1, 2, 5, 9):
        player = with_rating(free[0], 41, seasons=seasons)
        for number in (1, 2, 3):
            assert M.price(player, number)[0] >= CT.min_salary(seasons)
    player = with_rating(free[0], 41, seasons=9)
    assert M.price(player, 3)[0] == CT.min_salary(9)


def test_offering_more_is_ten_percent_over_rounded_half_up_and_never_over_the_maximum():
    assert T.FR_FA_OFFER_MORE == 10
    for salary, want in ((100, 110), (105, 116), (9, 10), (124, 136), (260, 280), (280, 280)):
        assert M.more(salary) == min(T.FR_MAX_SALARY, want)


# ----- what a team can still sign -----

def test_open_places_are_the_empty_places_by_position_in_the_rosters_order():
    league, _ = market_league(free=((2, 0), (2, 1)), empty_for=((2, 33), (2, 22)))          # two running backs, the quarterback, a linebacker
    assert M.open_places(league, 2) == [("QB", 1), ("RB", 2), ("LB", 1)]
    assert M.open_places(league, 1) == []
    assert M.filled(league, 2, "RB") == D.GROUP_SIZE["RB"] - 2 and M.filled(league, 2, "QB") == 0


def test_the_room_is_the_cap_room_of_stage_seven_less_the_reserve_for_the_rookies(monkeypatch):
    league, _ = market_league()
    assert M.room(league, 2) == resign.room(league, 2) - T.FR_FA_RESERVE
    monkeypatch.setattr(T, "FR_FA_RESERVE", 40)
    assert M.room(league, 2) == resign.room(league, 2) - 40


def test_the_fit_is_two_for_the_best_of_the_group_one_for_a_better_than_the_weakest_and_zero_otherwise():
    league, free = market_league(free=((2, 0),))
    team = 2
    group = [league.player_at(team, i) for i in D.PLACES_OF["RB"] if league.rosters[team - 1][i]]
    for k, p in enumerate(group):
        p.rating = 60 + 3 * k
    candidate = free[0]                                              # a running back
    assert candidate.pos == "RB"
    best, weakest = max(p.rating for p in group), min(p.rating for p in group)
    assert M.fit_level(league, team, with_rating(candidate, best + 1)) == 2
    assert M.fit_level(league, team, with_rating(candidate, best)) == 1
    assert M.fit_level(league, team, with_rating(candidate, weakest + 1)) == 1
    assert M.fit_level(league, team, with_rating(candidate, weakest)) == 0
    assert M.fit_level(league, team, with_rating(candidate, weakest - 5)) == 0


def test_a_group_with_no_player_left_fits_the_free_agent_as_its_best():
    league = fresh()
    stray = with_rating(make_free(league, 3, D.PLACES_OF["K"][0]), 55)
    open_group(league, 2, "K", D.GROUP_SIZE["K"])
    assert [league.rosters[1][i] for i in D.PLACES_OF["K"]] == [0] * D.GROUP_SIZE["K"]
    assert M.fit_level(league, 2, stray) == 2


def test_the_score_is_the_salary_raised_by_the_fit():
    league, free = market_league()
    player = with_rating(free[0], 99)                                # better than anybody: fit 2 at any team
    assert M.score(league, 2, player, 100) == 100 * (100 + T.FR_FA_FIT[2])
    assert M.score(league, 2, player, 101) > M.score(league, 2, player, 100)


def test_the_numbers_of_the_market_are_the_calibrated_ones():
    assert (T.FR_FA_ROUNDS, T.FR_FA_PRICE_DROP, T.FR_FA_MIN_RATING, T.FR_FA_CHASE, T.FR_FA_FIT, T.FR_FA_OFFER_MORE, T.FR_FA_OFFERS, T.FR_FA_LIST,
            T.FR_FA_RESERVE) == (3, 10, 60, 2, (0, 2, 4), 10, 5, 5, 0)
    assert T.FR_RESIGN_TARGET == 0.62                                  # the share of the cap the staff keeps its contracts under: the supply of the market (Q-031)
    assert T.FR_MIN_SALARY_BY_SEASONS == ((0, 9), (1, 10), (2, 11), (3, 11), (6, 12), (99, 13))


def test_a_team_chases_one_more_free_agent_for_each_open_place_in_every_later_round():
    league, pool, _ = one_open("QB")
    free = M.by_position(M.pool(league))
    assert [M.chase(r) for r in (1, 2, 3)] == [2, 3, 4]
    assert [len(M.team_bids(league, 2, r, free)) for r in (1, 2, 3)] == [2, 3, 4]
    assert [b.player for b in M.team_bids(league, 2, 3, free)] == [p.id for p in pool]


def test_the_fit_raises_the_score_by_zero_two_or_four_percent_of_the_salary():
    league, free = market_league(free=((2, 0),))
    team = 2
    group = [league.player_at(team, i) for i in D.PLACES_OF["RB"] if league.rosters[team - 1][i]]
    for k, p in enumerate(group):
        p.rating = 60 + 3 * k
    candidate = free[0]
    best, weakest = max(p.rating for p in group), min(p.rating for p in group)
    assert M.score(league, team, with_rating(candidate, weakest), 100) == 10000
    assert M.score(league, team, with_rating(candidate, weakest + 1), 100) == 10200
    assert M.score(league, team, with_rating(candidate, best + 1), 100) == 10400


# ----- a team's offers -----

def one_open(position, rating=70, team=2):
    """A league in which `team` has one open place at `position` and four other teams each lost a player of that position to the market (the free agents rated
    `rating`, `rating` - 2 ...). Returns the league, the free agents and the teams they came from."""
    league = fresh()
    retire(league, team, D.PLACES_OF[position][0])
    origins = [t for t in range(1, D.TEAMS + 1) if t != team][:4]
    pool = [with_rating(make_free(league, t, D.PLACES_OF[position][0]), rating - 2 * k) for k, t in enumerate(origins)]
    at_stage_eight(league)
    return league, pool, origins


def test_a_team_with_an_open_place_chases_two_of_the_best_free_agents_of_the_position_at_the_price():
    league, pool, _ = one_open("QB")
    bids = M.team_bids(league, 2, 1, M.by_position(M.pool(league)))
    qbs = [p for p in M.pool(league) if p.pos == "QB" and p.rating >= T.FR_FA_MIN_RATING]
    assert len(qbs) == 4
    assert [b.player for b in bids] == [p.id for p in qbs[:T.FR_FA_CHASE]] == [pool[0].id, pool[1].id]
    for bid, player in zip(bids, qbs):
        assert (bid.team, bid.salary, bid.years) == (2, *M.price(player, 1))
        assert bid.score == M.score(league, 2, player, bid.salary)


def test_a_team_offers_only_for_a_position_with_an_open_place_and_a_full_team_offers_nothing():
    league, pool, origins = one_open("QB")
    bids = M.computer_bids(league, 1)
    assert {b.team for b in bids} == {2} | set(origins)             # the origins each have the one open place of the player they lost
    for bid in bids:
        assert league.players[bid.player].pos == "QB" and M.filled(league, bid.team, "QB") == 0
    full = fresh()
    at_stage_eight(full)
    assert M.computer_bids(full, 1) == []


def test_a_team_offers_nothing_to_a_player_rated_under_the_minimum_rating():
    league, pool, _ = one_open("QB", rating=T.FR_FA_MIN_RATING + 3)
    assert min(p.rating for p in pool) < T.FR_FA_MIN_RATING <= max(p.rating for p in pool)
    bids = M.team_bids(league, 2, 1, M.by_position(M.pool(league)))
    assert bids and all(league.players[b.player].rating >= T.FR_FA_MIN_RATING for b in bids)
    low, _, _ = one_open("QB", rating=T.FR_FA_MIN_RATING - 1)
    assert M.team_bids(low, 2, 1, M.by_position(M.pool(low))) == []


def test_a_team_offers_only_what_it_can_pay():
    league, pool, _ = one_open("QB")
    prices = [M.price(p, 1)[0] for p in pool]                       # the dearer the better player: 121, 107, 93, 81
    assert prices == sorted(prices, reverse=True) and len(set(prices)) == 4
    squeeze(league, 2, prices[1])                                    # room for the second best, not for the best
    bids = M.team_bids(league, 2, 1, M.by_position(M.pool(league)))
    assert [b.player for b in bids] == [pool[1].id, pool[2].id]      # it chases the next two it can pay
    squeeze(league, 2, prices[3] - 1)
    assert M.team_bids(league, 2, 1, M.by_position(M.pool(league))) == []


def test_the_offers_change_nothing_and_are_the_same_every_time():
    league, pool, _ = one_open("QB")
    before = league.to_json()
    assert M.computer_bids(league, 1) == M.computer_bids(league, 1) and league.to_json() == before


def test_the_offers_skip_the_teams_asked_to_be_skipped():
    league, pool, origins = one_open("QB")
    assert M.computer_bids(league, 1, skip=(2, *origins)) == []
    assert {b.team for b in M.computer_bids(league, 1, skip=origins)} == {2}


def test_an_offer_chases_as_many_free_agents_as_the_open_places_times_the_chase():
    league = fresh()
    for index in D.PLACES_OF["WR"][:2]:
        retire(league, 2, index)
    for t in (3, 4, 5, 6, 7, 8):
        with_rating(make_free(league, t, D.PLACES_OF["WR"][0]), 72)
    at_stage_eight(league)
    wr = M.team_bids(league, 2, 1, M.by_position(M.pool(league)))
    assert len(wr) == 2 * T.FR_FA_CHASE


# ----- the judgement of a round -----

def bid(league, team, player, salary=None, years=None):
    price = M.price(player, 1)
    return M.make_bid(league, team, player, price[0] if salary is None else salary, price[1] if years is None else years)


def test_the_highest_score_wins_the_free_agent():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    open_group(league, 2, player.pos)
    open_group(league, 3, player.pos)
    low, high = bid(league, 2, player), bid(league, 3, player, salary=M.price(player, 1)[0] + 40)
    assert high.score > low.score
    result = M.resolve(league, [low, high], 1)
    assert result.signed == [(player, high)] and player.team == 3 and result.decisions[0].winner == high and result.decisions[0].ranked == [high, low]
    assert result.decisions[0].passed == []                          # the lower offer was not passed over for want of a place or money: it simply lost


def test_equal_scores_are_told_apart_by_the_fixed_rule_that_favors_no_team():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    for team in (2, 3, 4):
        for index in D.PLACES_OF[player.pos]:
            if league.rosters[team - 1][index]:
                league.players[league.rosters[team - 1][index]].rating = 60        # the same group at the three teams, so the same fit
        open_group(league, team, player.pos)
    bids = [bid(league, team, player) for team in (2, 3, 4)]
    assert len({b.score for b in bids}) == 1
    expected = min((2, 3, 4), key=lambda team: (team * (1 + player.id % 36)) % 37)          # the queue: the team number times a multiplier of his ID, modulo 37
    result = M.resolve(league, bids, 1)
    assert result.signed[0][1].team == expected
    for pid in range(1, 80):
        assert len({M.tie_key(t, pid) for t in range(1, D.TEAMS + 1)}) == D.TEAMS      # no two teams share a key for one player
    assert {min(range(1, D.TEAMS + 1), key=lambda t: M.tie_key(t, pid)) for pid in range(1, 400)} == set(range(1, D.TEAMS + 1))     # every team is first for some player
    for first in (1, 5, 9, 29):                                                         # neighbours (division mates) are ahead of each other about half the time
        ahead = sum(M.tie_key(first, pid) < M.tie_key(first + 1, pid) for pid in range(1, 1001))
        assert 400 < ahead < 600, (first, ahead)


def test_a_better_fit_beats_the_same_money():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    for index in D.PLACES_OF[player.pos]:
        for team, rating in ((2, 80), (3, 60)):
            if league.rosters[team - 1][index]:
                league.players[league.rosters[team - 1][index]].rating = rating     # team 2 has a good player at the position, team 3 a poor one
    open_group(league, 2, player.pos)
    open_group(league, 3, player.pos)
    a, b = bid(league, 2, player), bid(league, 3, player)
    assert a.salary == b.salary and b.score > a.score
    assert M.resolve(league, [a, b], 1).signed[0][1].team == 3


def test_the_winner_who_can_no_longer_afford_him_loses_to_the_next_offer():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    open_group(league, 2, player.pos)
    open_group(league, 3, player.pos)
    rich, poor = bid(league, 2, player, salary=M.price(player, 1)[0] + 40), bid(league, 3, player)
    assert rich.score > poor.score
    squeeze(league, 2, rich.salary - 1)                             # one tenth short of its own offer when the offers are judged
    result = M.resolve(league, [rich, poor], 1)
    assert result.signed[0][1].team == 3 and result.decisions[0].passed == [rich] and player.team == 3


def test_a_team_signs_the_best_of_two_players_it_bid_on_and_the_second_lapses_when_its_place_is_filled():
    league = fresh()
    open_group(league, 2, "QB")
    first = with_rating(make_free(league, 3, D.PLACES_OF["QB"][0]), 85)
    second = with_rating(make_free(league, 4, D.PLACES_OF["QB"][0]), 70)
    at_stage_eight(league)
    result = M.resolve(league, [bid(league, 2, second), bid(league, 2, first)], 1)
    assert [p.id for p, _ in result.signed] == [first.id]            # the best player is judged first
    assert second.status == "free" and result.decisions[1].winner is None and result.decisions[1].passed[0].team == 2


def test_the_free_agents_are_judged_in_the_order_of_their_value_whatever_the_order_of_the_offers():
    league = fresh()
    for team in (2, 3):
        open_group(league, team, "QB")
    star = with_rating(make_free(league, 7, D.PLACES_OF["QB"][0]), 90)
    other = with_rating(make_free(league, 8, D.PLACES_OF["QB"][0]), 65)
    at_stage_eight(league)
    bids = [bid(league, 2, other), bid(league, 3, other), bid(league, 2, star)]
    result = M.resolve(league, bids, 1)
    assert [p.id for p, _ in result.signed] == [star.id, other.id] and result.signed[0][1].team == 2 and result.signed[1][1].team == 3


def test_a_signed_player_joins_the_first_empty_place_of_his_position_on_the_contract_of_the_offer():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    open_group(league, 2, player.pos, 2)
    offer = bid(league, 2, player, salary=M.price(player, 1)[0] + 3)
    M.resolve(league, [offer], 1)
    assert (player.status, player.team, player.left, player.points) == ("active", 2, 0, 0)
    assert (player.salary, player.years) == (offer.salary, offer.years) and league.rosters[1][player.place] == player.id
    assert player.place in D.PLACES_OF[player.pos]
    group = [league.players[league.rosters[1][i]].rating for i in D.PLACES_OF[player.pos] if league.rosters[1][i]]
    assert group == sorted(group, reverse=True)                      # the places are put in rating order, an empty place last
    assert player not in M.pool(league)


def test_a_round_signs_nobody_without_offers_and_leaves_the_league_as_it_was():
    league, free = market_league()
    before = league.to_json()
    result = M.resolve(league, [], 1)
    assert result.signed == [] and result.decisions == [] and league.to_json() == before


def test_a_player_who_is_not_free_cannot_be_signed_again():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    open_group(league, 2, player.pos)
    open_group(league, 3, player.pos)
    M.resolve(league, [bid(league, 2, player)], 1)
    assert not M.can_sign(league, M.make_bid(league, 3, player, 50, 2))


def test_a_price_that_exactly_fills_the_room_is_signed_and_one_tenth_more_is_not():
    for extra, signed in ((0, True), (1, False)):
        league, free = market_league(free=((9, 12),))
        player = with_rating(free[0], 75)
        open_group(league, 2, player.pos)
        offer = bid(league, 2, player)
        squeeze(league, 2, offer.salary - extra)                    # the room is exactly his price (or a tenth short)
        assert M.can_sign(league, offer) is signed
        assert bool(M.resolve(league, [offer], 1).signed) is signed


def test_a_team_cannot_sign_a_player_into_a_group_that_is_full():
    league, free = market_league(free=((9, 12),))
    player = with_rating(free[0], 75)
    assert M.filled(league, 2, player.pos) == D.GROUP_SIZE[player.pos]
    assert not M.can_sign(league, bid(league, 2, player))


# ----- an independent worked-out judgement (the best offer wins, research G) -----

def oracle(league, bids):
    """Who signs whom, worked out again from the raw numbers (not from `market.can_sign` or `resign.room`): the free agents in the order of the value over the
    replacement rating, each to the highest score among the offers whose team has an empty place at his position and the room under the cap."""
    def replacement(position):
        base, span = T.FR_FILL_RATING if D.GROUP_SIZE[position] >= 3 else T.FR_FILL_RATING_SMALL
        return base + span // 2
    empty, payroll, count = {}, {}, {}
    for team in range(1, D.TEAMS + 1):
        for position in D.POSITIONS:
            empty[team, position] = sum(1 for i in D.PLACES_OF[position] if league.rosters[team - 1][i] == 0)
        placed = [league.players[pid] for pid in league.rosters[team - 1] if pid]
        payroll[team] = sum(p.salary for p in placed if p.years > 0)
        count[team] = len(placed)
    by_player = {}
    for b in bids:
        by_player.setdefault(b.player, []).append(b)

    def value_key(pid):
        p = league.players[pid]
        return (-D.WEIGHT[p.pos] * (p.rating - replacement(p.pos)), -p.rating, p.id)
    signed = []
    for pid in sorted(by_player, key=value_key):
        p = league.players[pid]
        for b in sorted(by_player[pid], key=lambda b: (-b.score, (b.team * (1 + pid % 36)) % 37)):
            room = T.FR_CAP - T.FR_RESIGN_RESERVE - T.FR_FA_RESERVE - league.dead[b.team - 1] - payroll[b.team] - T.FR_MIN_SALARY * (D.PLACE_COUNT - count[b.team] - 1)
            if empty[b.team, p.pos] > 0 and b.salary <= room:
                empty[b.team, p.pos] -= 1
                payroll[b.team] += b.salary
                count[b.team] += 1
                signed.append((pid, b.team, b.salary))
                break
    return signed


@pytest.mark.parametrize("seed", range(1, 13))
def test_the_best_offer_wins_in_random_markets_as_an_independent_oracle_says(seed):
    rng = random.Random(seed)
    league = fresh(seed)
    for _ in range(70):
        team, index = rng.randrange(1, D.TEAMS + 1), rng.randrange(D.PLACE_COUNT)
        if league.player_at(team, index) is not None:
            (make_free if rng.random() < 0.7 else retire)(league, team, index)
    at_stage_eight(league)
    extra = []
    for player in M.pool(league)[:15]:                              # the player's team offers more, less, the same for a few
        salary = M.price(player, 1)[0] + rng.choice((-3, 0, 4, 12))
        extra.append(M.make_bid(league, TEAM, player, max(T.FR_MIN_SALARY, salary), M.price(player, 1)[1]))
    bids = M.computer_bids(league, 1, skip=(TEAM,)) + extra
    want = oracle(league, bids)
    result = M.resolve(copy.deepcopy(league), bids, 1)
    assert [(p.id, b.team, b.salary) for p, b in result.signed] == want
    assert len(want) > 3


# ----- the whole market -----

@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_the_whole_market_keeps_every_team_under_the_cap_and_every_group_within_its_places(seed):
    rng = random.Random(seed)
    league = fresh(seed)
    for _ in range(120):
        team, index = rng.randrange(1, D.TEAMS + 1), rng.randrange(D.PLACE_COUNT)
        if league.player_at(team, index) is not None:
            (make_free if rng.random() < 0.6 else retire)(league, team, index)
    at_stage_eight(league)
    active_before = sum(1 for p in league.players.values() if p.status == "active")
    rounds = M.run_market(league)
    signed = [p for r in rounds for p, _ in r.signed]
    assert len(signed) == len({p.id for p in signed}) > 0
    assert sum(1 for p in league.players.values() if p.status == "active") == active_before + len(signed)
    for team in range(1, D.TEAMS + 1):
        assert CT.cap_used(league, team) <= T.FR_CAP
        for position in D.POSITIONS:
            assert M.filled(league, team, position) <= D.GROUP_SIZE[position]
    for player in league.players.values():
        if player.status == "free":
            assert (player.salary, player.years, player.place) == (0, 0, -1)
        if player.status == "active":
            assert D.POSITION_OF_PLACE[player.place] == player.pos and league.rosters[player.team - 1][player.place] == player.id
    for player in signed:
        assert 1 <= player.years <= CT.years_for_age(player.age) and CT.min_salary(player.seasons) <= player.salary <= T.FR_MAX_SALARY
    league.check()


def test_the_whole_market_is_the_same_every_time():
    def run():
        league = fresh(5)
        for team in range(2, 12):
            make_free(league, team, team % D.PLACE_COUNT)
        at_stage_eight(league)
        M.run_market(league)
        return league.to_json()
    assert run() == run()


def test_the_price_falls_between_rounds_so_a_free_agent_nobody_could_afford_at_first_is_signed_later():
    league = fresh()
    open_group(league, 2, "QB")
    player = with_rating(make_free(league, 3, D.PLACES_OF["QB"][0]), 80)
    at_stage_eight(league)
    price1, price3 = M.price(player, 1)[0], M.price(player, 3)[0]
    assert price3 < price1
    squeeze(league, 3, 0)                                            # his own team cannot pay him in any round
    squeeze(league, 2, price3)                                       # team 2 can pay the round-3 price, not the round-1 or the round-2 price
    assert M.price(player, 2)[0] > price3
    rounds = M.run_market(league)
    assert [len(r.signed) for r in rounds] == [0, 0, 1]
    assert player.status == "active" and player.team == 2 and player.salary == price3


# ----- the record of the stage in progress -----

def stage_record(**change):
    data = M.begin()
    data.update(change)
    return data


def test_a_market_in_progress_round_trips_through_the_file_and_is_format_four():
    league, free = market_league()
    league.market = stage_record(round=2, offers=[[free[0].id, 40], [free[1].id, 55]], signed=1, lost=2)
    data = json.loads(league.to_json())
    assert data["format"] == D.FORMAT == 18 and data["market"] == league.market      # (format 12 since SZ.8: the market is format 4's)
    again = LeagueRecord.from_json(league.to_json())
    assert again.market == league.market and again.to_json() == league.to_json()


def test_a_format_three_file_loads_with_no_market_and_the_next_save_is_format_four():
    league, _ = market_league()
    data = json.loads(league.to_json())
    del data["market"]
    data["format"] = 3
    again = LeagueRecord.from_json(json.dumps(data))
    assert again.market is None and json.loads(again.to_json())["format"] == D.FORMAT


def test_a_format_four_file_without_the_market_is_damage_and_a_newer_format_is_left_alone():
    league, _ = market_league()
    data = json.loads(league.to_json())
    del data["market"]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))
    data["format"] = D.FORMAT + 1
    with pytest.raises(NewerFormat):
        LeagueRecord.from_json(json.dumps(data))


def test_a_format_two_file_still_loads_with_no_market():
    league = fresh()
    data = json.loads(league.to_json())
    del data["market"], data["resign"]
    data["format"] = 2
    assert LeagueRecord.from_json(json.dumps(data)).market is None


@pytest.mark.parametrize("mutate", [
    lambda l, d, f: d.update(round=0), lambda l, d, f: d.update(round=T.FR_FA_ROUNDS + 1), lambda l, d, f: d.update(round=True),
    lambda l, d, f: d.update(offers=[[f[0].id, 40]] * 2), lambda l, d, f: d.update(offers=[[999999, 40]]),
    lambda l, d, f: d.update(offers=[[f[0].id, 1]]), lambda l, d, f: d.update(offers=[[f[0].id, T.FR_MAX_SALARY + 1]]),
    lambda l, d, f: d.update(offers=[[f[0].id]]), lambda l, d, f: d.update(offers="x"),
    lambda l, d, f: d.update(offers=[[f[k].id, 40] for k in range(T.FR_FA_OFFERS)] + [[f[T.FR_FA_OFFERS].id, 40]]),
    lambda l, d, f: d.update(signed=-1), lambda l, d, f: d.update(lost=10 ** 6), lambda l, d, f: d.update(staff=2),
    lambda l, d, f: d.pop("staff"), lambda l, d, f: d.update(extra=1),
    lambda l, d, f: setattr(l.players[f[0].id], "left", l.season - 1) or d.update(offers=[[f[0].id, 40]])])
def test_a_damaged_market_record_is_refused(mutate):
    league, free = market_league(free=((2, 0), (3, 6), (7, 33), (9, 12), (11, 18), (12, 20), (13, 21)))
    data = stage_record()
    mutate(league, data, free)
    league.market = data
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_an_undamaged_market_record_with_the_most_offers_is_accepted():
    league, free = market_league(free=((2, 0), (3, 6), (7, 33), (9, 12), (11, 18), (12, 20)))
    league.market = stage_record(round=T.FR_FA_ROUNDS, offers=[[free[k].id, T.FR_MAX_SALARY] for k in range(T.FR_FA_OFFERS)], signed=3, lost=4, staff=1)
    assert LeagueRecord.from_json(league.to_json()).market == league.market


def test_a_market_is_refused_outside_the_stage_of_free_agency():
    league, _ = market_league()
    league.market = stage_record()
    league.stage_no = D.STAGE_DRAFT
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())
    league.stage, league.stage_no = "season", 0
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_the_offer_of_a_free_agent_who_has_signed_elsewhere_is_refused():
    league, free = market_league()
    player = with_rating(free[0], 75)
    open_group(league, 2, player.pos)
    M.resolve(league, [bid(league, 2, player)], 1)
    league.market = stage_record(offers=[[player.id, 40]])
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_the_list_of_stages_places_free_agency_after_the_expiring_contracts_and_before_the_draft():
    numbers = [n for n, _ in D.STAGES]
    assert numbers == [1, 9, 2, 3, 7, 8, 4, 5, 6] and D.STAGE_MAX == max(numbers) == 9      # (SX.8l: the staff, 9, right after stage 1)
    assert numbers.index(D.STAGE_FREE_AGENCY) == numbers.index(D.STAGE_CONTRACTS) + 1 == numbers.index(D.STAGE_DRAFT) - 1
