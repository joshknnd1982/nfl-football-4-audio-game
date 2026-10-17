"""Re-signing, the talks and the franchise tag of the Franchise: the rules as plain functions (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8h,
D-067), and the league record that holds the stage in progress (format 3). The stage on the program rig is test_fr_resign_flow.py.
"""
import copy
import json
import random

import pytest
from drrig import SURNAMES

from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging, resign
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import OFFSEASON, LeagueError, LeagueRecord, NewerFormat, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5



@pytest.fixture(autouse=True)
def cap_alone_decides(monkeypatch):
    """The staff's payroll target (FR_RESIGN_TARGET, SX.8i) is out of the way in these tests, which are about the cap and the talks; it has its own tests."""
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 1.0)

def fresh(seed=3, team=TEAM):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def expire(league, team, places):
    """The contracts of these places of the team ran out (the year turned and nothing signed them again)."""
    players = [league.player_at(team, index) for index in places]
    for player in players:
        player.years = 0
    return players


def at_stage_seven(league, resign_record=None):
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, D.STAGE_CONTRACTS, 0, [8, 8] * 32
    league.resign = resign_record
    return league


def history_of(league, team, wins, finish):
    allwins, allfinish = [8] * D.TEAMS, [D.FINISH_MISSED] * D.TEAMS
    allwins[team - 1], allfinish[team - 1] = wins, finish
    league.history = [{"season": league.season, "wins": allwins, "finish": allfinish}]


# ----- the mood (a rule of last season) -----

def test_the_mood_is_happy_after_many_wins_or_a_playoff_win_unhappy_after_few_wins_else_content():
    league = fresh()
    for wins, finish, want in ((11, D.FINISH_MISSED, resign.HAPPY), (16, D.FINISH_MISSED, resign.HAPPY), (8, D.FINISH_DIVISION, resign.HAPPY),
                               (8, D.FINISH_CHAMPION, resign.HAPPY), (10, D.FINISH_MISSED, resign.CONTENT), (9, D.FINISH_WILD_CARD, resign.CONTENT),
                               (6, D.FINISH_MISSED, resign.CONTENT), (5, D.FINISH_MISSED, resign.UNHAPPY), (0, D.FINISH_MISSED, resign.UNHAPPY)):
        history_of(league, TEAM, wins, finish)
        assert resign.mood(league, TEAM) == want, (wins, finish)


def test_the_mood_is_the_teams_own_and_content_without_a_history():
    league = fresh()
    assert resign.mood(league, TEAM) == resign.CONTENT
    history_of(league, TEAM, 14, D.FINISH_CHAMPION)
    assert resign.mood(league, TEAM) == resign.HAPPY and resign.mood(league, TEAM + 1) == resign.CONTENT
    league.history.append({"season": 2, "wins": [3] * D.TEAMS, "finish": [0] * D.TEAMS})
    assert resign.mood(league, TEAM) == resign.UNHAPPY                          # the last season counts, not the one before


# ----- the price a player asks, what he accepts, and the talk -----

def test_a_player_asks_the_market_price_for_the_length_of_his_age():
    league = fresh()
    for player in league.active_of(TEAM):
        player.seasons = 6
        assert resign.asking(player) == (CT.market_salary(player.pos, player.rating), CT.years_for_age(player.age))


def test_a_player_with_fewer_than_three_seasons_has_only_the_exclusive_rights_of_his_team_the_minimum_for_one_year():
    league = fresh()
    player = league.player_at(TEAM, 33)
    player.rating = 90
    assert T.FR_EXCLUSIVE_SEASONS == 3                                                  # research B3: fewer than 3 seasons
    for seasons, least in ((0, 9), (1, 10), (2, 11)):                                   # research B4's table, the minimum of his seasons
        player.seasons = seasons
        assert resign.asking(player) == (least, 1) == (CT.min_salary(seasons), 1)
    player.seasons = 3
    assert resign.asking(player) == CT.market_contract(player) and resign.asking(player)[0] > T.FR_MIN_SALARY


def test_a_veteran_never_asks_for_less_than_the_minimum_of_his_seasons_even_when_his_rating_is_worth_less():
    league = fresh()
    player = league.player_at(TEAM, 0)
    player.rating, player.seasons = 41, 11                                              # the market price of a 41 is 9 + a little: under the 1.3 million of 7 seasons or more
    assert CT.market_contract(player)[0] < CT.min_salary(11) == 13
    assert resign.asking(player)[0] == 13
    player.rating, player.seasons = 90, 11                                              # a good player asks his market price
    assert resign.asking(player) == CT.market_contract(player) and resign.asking(player)[0] > 13
    talk = resign.Talk.start(league.player_at(TEAM, 0), resign.HAPPY)
    assert talk.ask >= talk.least == 13 and talk.floor >= 13


def test_a_talk_with_a_player_who_has_exclusive_rights_never_goes_under_the_minimum_whatever_his_mood():
    league = fresh()
    player = league.player_at(TEAM, 0)
    player.seasons = 1
    for how in resign.MOODS:
        talk = resign.Talk.start(player, how)
        least = CT.min_salary(1)
        assert least == 10 > T.FR_MIN_SALARY
        assert (talk.ask, talk.years, talk.floor, talk.least) == (least, 1, least, least)
        assert talk.offer_less() == (resign.ACCEPTED, least)                         # even an offer for less is the minimum of his seasons, not the flat 0.9 million


@pytest.mark.parametrize("salary, how, floor", [(100, resign.HAPPY, 90), (100, resign.CONTENT, 96), (100, resign.UNHAPPY, 100),
                                                (99, resign.CONTENT, 95), (101, resign.CONTENT, 97), (10, resign.HAPPY, 9), (9, resign.HAPPY, 9)])
def test_the_floor_is_the_least_his_mood_accepts_rounded_half_up_and_never_under_the_minimum(salary, how, floor):
    assert resign.floor_salary(salary, how) == floor


def test_a_happy_players_floor_is_exactly_the_offer_for_less_at_every_price():
    assert T.FR_MOOD_SLACK[resign.HAPPY] == T.FR_OFFER_LESS
    for salary in range(T.FR_MIN_SALARY, T.FR_MAX_SALARY + 1):
        assert resign.floor_salary(salary, resign.HAPPY) == resign.lower_offer(salary)


@pytest.mark.parametrize("salary, lower", [(100, 90), (105, 95), (124, 112), (10, 9), (9, 9), (12, 11)])
def test_offering_less_is_ten_percent_under_rounded_half_up_and_never_under_the_minimum(salary, lower):
    assert resign.lower_offer(salary) == lower


def test_a_happy_player_signs_at_the_lower_offer_at_once():
    talk = resign.Talk(100, 3, resign.floor_salary(100, resign.HAPPY))
    assert talk.offer_less() == (resign.ACCEPTED, 90) and talk.round == 1


def test_a_content_player_counters_halfway_to_his_floor_twice_and_ends_the_talk_in_the_last_round():
    talk = resign.Talk(100, 3, resign.floor_salary(100, resign.CONTENT))
    assert talk.floor == 96
    assert talk.offer_less() == (resign.COUNTER, 98) and (talk.ask, talk.round) == (98, 2)
    assert talk.offer_less() == (resign.COUNTER, 97) and (talk.ask, talk.round) == (97, 3)
    assert talk.offer_less() == (resign.ENDED, 0)                                    # round 3 failed: he leaves
    assert talk.years == 3                                                           # and no round ever changed the length


def test_the_counter_is_halfway_to_the_floor_rounded_up_so_an_odd_sum_goes_to_the_higher_price():
    talk = resign.Talk(101, 3, 96)
    assert talk.offer_less() == (resign.COUNTER, 99)                                 # (101 + 96) / 2 = 98.5 rounded up
    talk = resign.Talk(100, 3, 95)
    assert talk.offer_less() == (resign.COUNTER, 98)                                 # 97.5 rounded up
    talk = resign.Talk(100, 3, 100)
    assert talk.offer_less() == (resign.COUNTER, 100)                                # nothing to come down to


def test_an_unhappy_player_never_comes_down_and_leaves_after_the_third_offer():
    talk = resign.Talk(100, 2, resign.floor_salary(100, resign.UNHAPPY))
    assert [talk.offer_less() for _ in range(3)] == [(resign.COUNTER, 100), (resign.COUNTER, 100), (resign.ENDED, 0)]


def test_the_ask_only_comes_down_and_never_under_the_floor_over_every_price_and_mood():
    for how in resign.MOODS:
        for salary in range(T.FR_MIN_SALARY, T.FR_MAX_SALARY + 1):
            talk = resign.Talk(salary, 2, resign.floor_salary(salary, how))
            asks = [talk.ask]
            for _ in range(T.FR_TALK_ROUNDS + 1):
                result, value = talk.offer_less()
                if result == resign.ACCEPTED:
                    assert talk.floor <= value <= talk.ask
                    break
                if result == resign.ENDED:
                    break
                asks.append(talk.ask)
            assert asks == sorted(asks, reverse=True) and min(asks) >= talk.floor
            assert talk.round <= T.FR_TALK_ROUNDS


def test_a_talk_of_one_round_is_the_last_round_at_once(monkeypatch):
    monkeypatch.setattr(T, "FR_TALK_ROUNDS", 1)
    talk = resign.Talk(100, 3, resign.floor_salary(100, resign.CONTENT))
    assert talk.offer_less() == (resign.ENDED, 0)


# ----- the franchise tag -----

def test_the_tag_pays_the_average_of_the_five_highest_running_salaries_at_the_position():
    league = fresh()
    backs = [p for p in league.players.values() if p.pos == "RB"]
    for player, salary in zip(backs, (200, 180, 160, 140, 120, 110, 100)):
        player.salary, player.years = salary, 2
    for other in backs[7:]:
        other.salary, other.years = 40, 1
    other = backs[0]                                                                 # a contract that ran out, the highest of the position: it does not count
    other.years = 0
    target = backs[6]
    target.years = 0
    assert resign.tag_salary(league, target) == (180 + 160 + 140 + 120 + 110 + 2) // 5 == 142        # the five highest that run, rounded half up
    other.years = 2
    assert resign.tag_salary(league, target) == (200 + 180 + 160 + 140 + 120) // 5 == 160              # with his contract running it would count


def test_the_tag_average_leaves_out_every_contract_that_ran_out_not_only_his_own():
    league = fresh()
    backs = [p for p in league.players.values() if p.pos == "RB"]
    for player, salary in zip(backs, (200, 180, 160, 140, 120, 100, 80)):
        player.salary, player.years = salary, 2
    for other in backs[7:]:
        other.salary, other.years = 40, 1
    backs[0].years = 0                                                               # another back, with the highest salary, has no contract either
    backs[-1].years = 0
    assert resign.tag_salary(league, backs[-1]) == (180 + 160 + 140 + 120 + 100) // 5 == 140


def test_the_tag_is_at_least_a_raise_of_his_last_salary_and_his_market_price_and_never_over_the_maximum():
    league = fresh()
    kicker = next(p for p in league.players.values() if p.pos == "K")
    for other in league.players.values():
        if other.pos == "K" and other is not kicker:
            other.salary, other.years = T.FR_MIN_SALARY, 1
    kicker.years = 0
    kicker.salary = 60
    assert resign.tag_salary(league, kicker) == max(72, CT.market_salary("K", kicker.rating))          # 120 percent of 60; the others earn the minimum
    kicker.salary = T.FR_MAX_SALARY
    assert resign.tag_salary(league, kicker) == T.FR_MAX_SALARY


def test_the_tag_with_fewer_than_five_salaries_at_the_position_uses_the_ones_there_are():
    league = fresh()
    for player in league.players.values():
        if player.pos == "P":
            player.status = "retired"
    other = Player_of(league, "P")
    other.salary, other.years = 100, 2
    punter = Player_of(league, "P")
    punter.salary = 10
    assert CT.market_salary("P", punter.rating) < 100
    assert resign.tag_salary(league, punter) == 100                                  # the only running salary at the position is the average


def Player_of(league, position):
    from nfl4.extras.franchise.league import Player
    player = Player(league.next_id, "Solo", position, 70, "average", 27, 5, 70, None, 0, "active", 0, 1, -1, 40, 0)
    league.players[player.id] = player
    league.next_id += 1
    return player


# ----- the room under the cap -----

def test_the_room_is_the_cap_less_the_running_contracts_the_dead_money_and_the_minimum_for_every_other_place():
    assert resign.room_after(0, 0, 0) == T.FR_CAP - T.FR_RESIGN_RESERVE - T.FR_MIN_SALARY * 33
    assert resign.room_after(1000, 20, 100) == T.FR_CAP - T.FR_RESIGN_RESERVE - 100 - 1000 - T.FR_MIN_SALARY * 13
    assert resign.room_after(0, 33, 0) == T.FR_CAP - T.FR_RESIGN_RESERVE                       # the last place may take the whole room


def test_the_room_of_a_league_counts_only_the_contracts_that_run():
    league = fresh()
    base = resign.room(league, TEAM)
    assert base == resign.room_after(CT.payroll(league, TEAM), 34, 0)                           # all 34 places hold a running contract
    player = expire(league, TEAM, [3])[0]
    assert resign.running_count(league, TEAM) == 33
    assert resign.running_payroll(league, TEAM) == CT.payroll(league, TEAM) == sum(p.salary for p in league.active_of(TEAM) if p is not player)
    assert resign.room(league, TEAM) == base + player.salary - T.FR_MIN_SALARY                  # his old salary is room again, less the minimum his place will cost
    league.dead[TEAM - 1] = 33
    assert resign.room(league, TEAM) == base + player.salary - T.FR_MIN_SALARY - 33


# ----- the staff's and the computer's rule -----

def team_with(expiring_ratings, filler_salary=None, team=3, positions=None):
    """A league in which the team's players at the first places have no years left, with these ratings; every other contract runs."""
    league = fresh(team=team)
    players = []
    for index, rating in enumerate(expiring_ratings):
        player = league.player_at(team, index if positions is None else positions[index])
        player.rating, player.peak = rating, max(player.peak, rating)
        player.years, player.seasons = 0, max(player.seasons, 8)                      # (a young player has the exclusive rights: the minimum for a year)
        players.append(player)
    if filler_salary is not None:
        for player in league.active_of(team):
            if player.years > 0:
                player.salary = filler_salary
    return league, players


def test_the_staff_signs_the_valuable_first_at_the_market_price_for_the_length_of_the_age_and_lets_the_weak_go():
    league, players = team_with([85, 70, 41], positions=[33, 0, 7])                 # a quarterback, a running back and a receiver
    qb, back, receiver = players
    plan = resign.plan_team(league, 3)
    assert [(p.id, s, y) for p, s, y in plan.signed] == [(qb.id, CT.market_salary("QB", 85), CT.years_for_age(qb.age)),
                                                         (back.id, CT.market_salary("RB", 70), CT.years_for_age(back.age))]
    assert [p.id for p in plan.gone] == [receiver.id]                              # 41 is under the rookie of the fill plus the margin
    assert not resign.worth_keeping(receiver) and resign.worth_keeping(qb)
    assert qb.years == 0 and back.years == 0                                         # planning changes nothing
    resign.apply_plan(league, plan)
    assert (qb.years, back.years) == (CT.years_for_age(qb.age), CT.years_for_age(back.age)) and qb.status == back.status == "active"
    assert receiver.status == "free" and receiver.team == 3 and receiver.place == -1 and receiver.left == league.season
    assert (receiver.salary, receiver.years) == (0, 0) and league.rosters[2][7] == 0
    assert league.dead == [0] * D.TEAMS                                              # a contract that ran out costs no dead money


def test_the_staff_signs_a_worthy_young_player_for_the_minimum_for_one_year_and_lets_a_weak_one_go():
    league, players = team_with([70, 70, 41], positions=[0, 7, 8])
    good, also, weak = players
    for player in players:
        player.seasons = 1
    plan = resign.plan_team(league, 3)
    assert [(p.id, s, y) for p, s, y in plan.signed] == [(good.id, CT.min_salary(1), 1), (also.id, CT.min_salary(1), 1)] and CT.min_salary(1) == 10
    assert [p.id for p in plan.gone] == [weak.id]
    resign.apply_plan(league, plan)
    assert (good.salary, good.years) == (CT.min_salary(1), 1)


def test_a_player_is_worth_keeping_from_the_draft_classes_mean_rating_in_every_group():
    league = fresh()
    assert T.FR_RESIGN_MIN_RATING == 60 == 46 + 14                                    # the mean true rating of the draft class (FR_ROOKIE_RATING)
    back, kicker = league.player_at(1, 0), league.player_at(1, 31)
    assert (back.pos, kicker.pos) == ("RB", "K")
    assert CT.replacement_rating("RB") == 50 and CT.replacement_rating("K") == 55          # the fill's middle: 45 + 11 // 2 and 50 + 11 // 2
    for player in (back, kicker):                                                    # a kicker is judged as a back: the draft's supply for him is as thin as the fill's
        for rating, ok in ((59, False), (60, True), (80, True)):
            player.rating = rating
            assert resign.worth_keeping(player) is ok


def test_a_player_is_let_go_when_the_cap_has_no_room_for_his_price_even_if_he_is_worth_it():
    league, players = team_with([85, 70], filler_salary=55, positions=[33, 0])      # 32 running contracts of 5.5 million
    qb, back = players
    assert resign.room(league, 3) < CT.market_salary("QB", 85)
    plan = resign.plan_team(league, 3)
    assert [p.id for p in plan.gone] == [qb.id] and [p.id for p, _, _ in plan.signed] == [back.id]      # the cheaper one still fits
    resign.apply_plan(league, plan)
    assert CT.cap_used(league, 3) <= T.FR_CAP


def test_the_room_shrinks_with_every_signing_so_a_team_that_began_under_the_cap_never_ends_over_it():
    league, players = team_with([85] * 10, positions=list(range(10)), filler_salary=60)         # ten backs and receivers rated 85, each of whom fits alone
    asks = [resign.asking(p)[0] for p in players]
    assert min(asks) > 80 and sum(asks) + 24 * 60 > T.FR_CAP and T.FR_CAP - 24 * 60 - 9 * T.FR_MIN_SALARY > max(asks)      # all fit one by one, not together
    plan = resign.plan_team(league, 3)
    # worked out by hand: the room starts at the cap less 24 contracts of 6.0 million less the minimum for 9 other places, and falls by each price
    room, count, expected = T.FR_CAP - 24 * 60 - T.FR_MIN_SALARY * 9, 0, []
    for player in sorted(players, key=resign.value):
        price = resign.asking(player)[0]
        if price <= room:
            expected.append(player.id)
            room -= price
            room += T.FR_MIN_SALARY                       # one more place has a contract: its minimum is no longer reserved
    assert 0 < len(expected) < 10
    assert [p.id for p, _, _ in plan.signed] == expected and len(plan.gone) == 10 - len(expected)
    resign.apply_plan(league, plan)
    assert CT.cap_used(league, 3) <= T.FR_CAP


def test_a_price_that_exactly_fills_the_room_is_signed_and_one_tenth_more_is_not():
    for extra, signed in ((0, True), (1, False)):
        league, (qb,) = team_with([85], positions=[33])
        ask = resign.asking(qb)[0]
        filler = next(p for p in league.active_of(3) if p.years > 0)
        filler.salary = 60
        filler.salary += (T.FR_CAP - ask + extra) - resign.running_payroll(league, 3)          # the room is exactly his price (or a tenth short)
        assert resign.room(league, 3) == ask - extra and T.FR_MIN_SALARY <= filler.salary <= T.FR_MAX_SALARY
        plan = resign.plan_team(league, 3)
        assert bool(plan.signed) is signed and bool(plan.gone) is not signed
        if signed:
            resign.apply_plan(league, plan)
            assert CT.cap_used(league, 3) == T.FR_CAP                                      # exactly at the cap, not over it


def test_planning_draws_nothing_and_is_the_same_twice():
    league, _ = team_with([85, 70, 60, 50], positions=[33, 0, 7, 12])
    first = resign.plan_team(league, 3)
    second = resign.plan_team(copy.deepcopy(league), 3)
    assert [(p.id, s, y) for p, s, y in first.signed] == [(p.id, s, y) for p, s, y in second.signed]
    assert [p.id for p in first.gone] == [p.id for p in second.gone]


def test_the_order_of_value_is_the_part_of_the_strength_a_player_gives_over_his_replacement():
    league, players = team_with([75, 75, 90, 60], positions=[33, 8, 14, 21])         # a quarterback, a receiver, a cornerback, a returner
    qb = players[0]
    ordered = resign.expiring(league, 3)
    keys = [resign.value(p) for p in ordered]
    assert keys == sorted(keys) and len(ordered) == 4
    assert ordered[0].id == qb.id                                                    # the quarterback's weight of 12 beats a 90-rated cornerback's 2


def test_a_whole_league_is_settled_team_by_team_and_the_numbers_are_kept():
    league = fresh()
    for team in range(1, D.TEAMS + 1):
        expire(league, team, (0, 6, 12, 33))
    out = resign.run_teams(league, skip=(TEAM,))
    assert sum(out.signed_by.values()) == out.signed and TEAM not in out.signed_by and len(out.signed_by) == 31
    assert out.signed + len(out.gone) == 31 * 4
    assert all(p.years == 0 for p in league.active_of(TEAM) if p is not None and p.id in {league.player_at(TEAM, i).id for i in (0, 6, 12, 33)})
    assert all(p.years > 0 for team in range(1, D.TEAMS + 1) if team != TEAM for p in league.active_of(team) if p is not None)
    assert all(p.status == "free" for p in out.gone) and all(p.team != 0 for p in out.gone)
    stars = Outcome_with(out.gone).stars()
    assert len(stars) <= D.STARS_NAMED and all(p.rating >= D.FREE_STAR_RATING for p in stars)


def Outcome_with(gone):
    return resign.Outcome(gone=gone)


def test_the_stars_who_are_let_go_are_the_best_rated_first_at_most_three_and_only_from_the_freestar_rating():
    league = fresh()
    gone = []
    for index, rating in enumerate((95, 80, 79, 90, 88, 85)):
        player = league.player_at(1 + index, 12)
        player.rating = rating
        gone.append(player)
    named = resign.Outcome(gone=gone).stars()
    assert [p.rating for p in named] == [95, 90, 88]
    assert [p.rating for p in resign.Outcome(gone=gone[1:3]).stars()] == [80]


def test_the_staff_handles_the_players_team_too_when_it_is_told_to():
    league = fresh()
    expire(league, TEAM, (0, 12, 33))
    state = resign.begin(league, True)
    assert state["pending"] == [] and state["signed"] + state["let_go"] == 3
    assert all(p.years > 0 for p in league.active_of(TEAM) if p is not None)
    other = fresh()
    expire(other, TEAM, (0, 12, 33))
    state = resign.begin(other, False)
    assert len(state["pending"]) == 3 and state["signed"] == state["let_go"] == 0         # nothing is decided for the player
    assert all(other.players[pid].years == 0 and other.players[pid].status == "active" for pid in state["pending"])
    assert state["pending"] == [p.id for p in resign.expiring(other, TEAM)]
    assert set(state) == set(resign.KEYS) and state["tag_used"] == 0


def test_a_star_the_staff_lets_go_from_the_players_own_team_is_not_named_among_the_other_teams_stars():
    league = fresh()
    qb = league.player_at(TEAM, 33)
    qb.rating, qb.years, qb.seasons = 95, 0, 8
    for player in league.active_of(TEAM):
        if player.years > 0:
            player.salary = 60                                                           # no room for a quarterback's price
    state = resign.begin(league, True)
    assert qb.status == "free" and state["let_go"] >= 1 and qb.id not in state["stars"]


def test_begin_counts_the_other_teams_and_names_their_stars():
    league = fresh()
    league.player_at(2, 12).rating = 99
    for team in range(1, D.TEAMS + 1):
        expire(league, team, (12,))
    for index in range(34):
        league.player_at(2, index).salary = T.FR_MAX_SALARY                           # team 2 cannot afford anybody
    state = resign.begin(league, False)
    assert state["league_gone"] >= 1 and 1 <= len(state["stars"]) <= 3
    star = league.players[state["stars"][0]]
    assert star.status == "free" and star.team == 2 and star.rating == 99


# ----- the cap, contract and age invariants over many offseasons -----

def test_twelve_offseasons_by_the_rules_keep_every_contract_in_its_bounds_and_every_team_under_the_cap():
    rnd = GameRandom(random.Random(9))
    league = fresh(seed=9)
    for _ in range(12):
        aging.apply_aging(league, aging.plan_retirements(league, rnd))
        aging.apply_development(aging.plan_development(league, rnd))
        out = resign.run_teams(league)
        assert all(p.years > 0 for p in league.players.values() if p.status == "active")
        assert all(1 <= p.years <= CT.years_for_age(p.age) for p in league.players.values() if p.status == "active")
        assert all(T.FR_MIN_SALARY <= p.salary <= T.FR_MAX_SALARY for p in league.players.values() if p.status == "active")
        assert all(CT.cap_used(league, t) <= T.FR_CAP for t in range(1, D.TEAMS + 1))
        assert all((p.salary, p.years) == (0, 0) for p in out.gone)
        aging.fill_places(league, rnd, SURNAMES)
        aging.drop_the_unkept(league)
        league.season += 1


# ----- the staff's payroll target (SX.8i: the players that do not fit go to the market) -----

def target_for(payroll):
    """The FR_RESIGN_TARGET whose payroll in tenths of a million is exactly `payroll`."""
    return (payroll + 0.5) / T.FR_CAP


def test_the_target_payroll_is_the_share_of_the_cap(monkeypatch):
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 0.62)
    assert resign.target_payroll() == int(0.62 * T.FR_CAP) == 1197
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 1.0)
    assert resign.target_payroll() == T.FR_CAP


def test_the_staff_signs_again_only_while_the_payroll_stays_under_the_target_and_lets_the_rest_go_though_the_cap_has_room(monkeypatch):
    league, players = team_with([85, 80, 75], positions=[33, 0, 7])
    qb, back, receiver = players
    payroll = resign.running_payroll(league, 3)
    first, second = resign.asking(qb)[0], resign.asking(back)[0]
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", target_for(payroll + first))             # room for the quarterback and nothing more
    assert resign.room(league, 3) > first + second + resign.asking(receiver)[0]            # the cap alone would sign all three
    plan = resign.plan_team(league, 3)
    assert [p.id for p, _, _ in plan.signed] == [qb.id] and [p.id for p in plan.gone] == [back.id, receiver.id]


def test_a_signing_that_exactly_fills_the_target_is_made_and_one_tenth_more_is_not(monkeypatch):
    for extra, signed in ((0, True), (1, False)):
        league, (qb,) = team_with([85], positions=[33])
        payroll = resign.running_payroll(league, 3)
        monkeypatch.setattr(T, "FR_RESIGN_TARGET", target_for(payroll + resign.asking(qb)[0] - extra))
        assert resign.target_payroll() == payroll + resign.asking(qb)[0] - extra
        plan = resign.plan_team(league, 3)
        assert bool(plan.signed) is signed and bool(plan.gone) is not signed


def test_the_dead_money_counts_against_the_target(monkeypatch):
    league, (qb,) = team_with([85], positions=[33])
    payroll = resign.running_payroll(league, 3)
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", target_for(payroll + resign.asking(qb)[0]))
    assert resign.plan_team(league, 3).signed
    league.dead[2] = 1
    assert not resign.plan_team(league, 3).signed


def test_the_target_holds_the_staff_only_the_players_own_talks_and_room_are_held_to_the_cap(monkeypatch):
    league, (qb,) = team_with([85], positions=[33])
    before = resign.room(league, 3)
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 0.3)
    assert resign.room(league, 3) == before and resign.room(league, 3) >= resign.asking(qb)[0]
    assert not resign.plan_team(league, 3).signed                                    # the staff, held to the target, signs nobody


# ----- the stage in progress in league.sav (format 3, and the newest format) -----

def test_the_stage_in_progress_round_trips_through_the_file():
    league = at_stage_seven(fresh(), None)
    expire(league, TEAM, (0, 12))
    state = resign.begin(league, False)
    league.resign = state
    text = league.to_json()
    assert json.loads(text)["format"] == D.FORMAT and json.loads(text)["resign"] == state
    again = LeagueRecord.from_json(text)
    assert again.resign == state and again.to_json() == text


def test_a_format_two_file_loads_with_no_stage_in_progress_and_the_next_save_is_the_newest_format():
    league = fresh()
    data = json.loads(league.to_json())
    data["format"] = 2
    del data["resign"]
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.resign is None and json.loads(loaded.to_json())["format"] == D.FORMAT
    assert [(p.salary, p.years) for p in loaded.players.values()] == [(p.salary, p.years) for p in league.players.values()]    # a migration changes nothing


def test_a_format_two_file_saved_after_stage_two_has_signed_contracts_and_the_expiring_stage_finds_nobody():
    league = at_stage_seven(fresh())
    league.stage_no = D.STAGE_DEVELOPMENT                                             # the file as SX.8g wrote it after stage 2: the stand-in had signed everybody
    data = json.loads(league.to_json())
    data["format"] = 2
    del data["resign"]
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert resign.expiring(loaded, TEAM) == [] and all(p.years >= 1 for p in loaded.players.values())


def test_a_format_three_file_without_the_resign_key_is_damage():
    data = json.loads(fresh().to_json())
    del data["resign"]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


@pytest.mark.parametrize("change", [
    lambda d: d.pop("tag_used"), lambda d: d.__setitem__("tag_used", 2), lambda d: d.__setitem__("tag_used", True),
    lambda d: d.__setitem__("signed", -1), lambda d: d.__setitem__("let_go", 1.5), lambda d: d.__setitem__("league_gone", "3"),
    lambda d: d.__setitem__("pending", "none"), lambda d: d.__setitem__("pending", [d["pending"][0]] * 2),
    lambda d: d.__setitem__("pending", [999999]), lambda d: d.__setitem__("pending", [True]),
    lambda d: d.__setitem__("stars", [1, 2, 3, 4]), lambda d: d.__setitem__("stars", [d["pending"][0]]),
    lambda d: d.__setitem__("extra", 1),
])
def test_a_damaged_stage_record_is_damage(change):
    league = at_stage_seven(fresh())
    expire(league, TEAM, (0, 12))
    league.resign = resign.begin(league, False)
    data = json.loads(league.to_json())
    change(data["resign"])
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


def test_a_pending_player_must_be_one_of_the_players_own_with_no_years_left():
    league = at_stage_seven(fresh())
    expire(league, TEAM, (0,))
    league.resign = resign.begin(league, False)
    league.resign["pending"].append(league.player_at(TEAM, 5).id)                  # his contract runs
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())
    league.resign["pending"] = [league.player_at(3, 5).id]
    league.player_at(3, 5).years = 0                                                 # another team's player
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_a_stage_record_outside_stage_seven_is_damage():
    league = at_stage_seven(fresh())
    expire(league, TEAM, (0,))
    league.resign = resign.begin(league, False)
    for stage_no in (D.STAGE_DEVELOPMENT, D.STAGE_DRAFT, D.STAGE_CUT):
        league.stage_no = stage_no
        with pytest.raises(LeagueError):
            LeagueRecord.from_json(league.to_json())
    league.stage, league.stage_no = "season", 0
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_a_star_named_must_be_a_free_agent():
    league = at_stage_seven(fresh())
    league.resign = resign.begin(league, False)
    league.resign["stars"] = [league.player_at(2, 3).id]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_no_years_left_is_allowed_only_while_the_stages_that_hold_such_a_player_are_running():
    for stage_no, ok in ((D.STAGE_DEVELOPMENT, True), (D.STAGE_CONTRACTS, True), (D.STAGE_DRAFT, False), (D.STAGE_CUT, False),
                         (D.STAGE_NEW_SEASON, False), (D.STAGE_AGING, False), (D.STAGE_REVIEW, False)):
        league = at_stage_seven(fresh())
        league.stage_no = stage_no
        expire(league, TEAM, (3,))
        if stage_no in (D.STAGE_DRAFT, D.STAGE_CUT):
            league.draft = None
        if ok:
            LeagueRecord.from_json(league.to_json())
        else:
            with pytest.raises(LeagueError):
                LeagueRecord.from_json(league.to_json())
    league = fresh()
    expire(league, TEAM, (3,))
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())                                      # in a season nobody has 0 years


def test_during_the_stage_only_the_pending_players_may_have_no_years_left():
    league = at_stage_seven(fresh())
    expire(league, TEAM, (0,))
    league.resign = resign.begin(league, False)
    LeagueRecord.from_json(league.to_json())                                          # the pending player: fine
    expire(league, 3, (5,))                                                           # a computer team's player left in limbo: damage
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_a_free_agent_has_no_contract_no_place_and_is_a_valid_player_of_the_file():
    league = at_stage_seven(fresh())
    player = expire(league, 3, (4,))[0]
    resign.let_go(league, player)
    assert player.status == "free" and player.place == -1 and (player.salary, player.years) == (0, 0) and player.team == 3
    again = LeagueRecord.from_json(league.to_json())
    assert again.players[player.id].status == "free" and again.rosters[2][4] == 0


def test_the_free_agents_of_other_teams_are_dropped_at_the_new_season_but_the_players_own_stay_for_history():
    league = fresh()
    mine, other = expire(league, TEAM, (3,))[0], expire(league, 3, (4,))[0]
    resign.let_go(league, mine)
    resign.let_go(league, other)
    aging.drop_the_unkept(league)
    assert mine.id in league.players and other.id not in league.players
