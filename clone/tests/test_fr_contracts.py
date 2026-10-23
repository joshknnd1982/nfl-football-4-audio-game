"""Contracts and the salary cap of the Franchise: the price rules, the cap rule of the roster cut, the year that turns, the migration of a
format-1 league and the damage matrix of the new values (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8g, D-066). Rules only, no speech:
the stage and the menus are test_fr_cap_flow.py.
"""
import copy
import json
import random

import pytest
from drrig import SURNAMES
from test_fr_cut_flow import cut_league

from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise.league import LeagueError, LeagueRecord, NewerFormat, Player, new_league
from nfl4.game.rnd import GameRandom


def fresh(seed=3, team=5):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def rnd(seed=1):
    return GameRandom(random.Random(seed))


# ----- the three price rules -----

def test_the_market_price_is_the_minimum_at_the_bottom_of_the_scale_and_follows_the_position_and_the_rating():
    pinned = {"QB": [9, 21, 59, 121, 209, 280, 280], "RB": [9, 12, 24, 42, 69, 102, 139], "DL": [9, 14, 29, 54, 89, 134, 183],
              "K": [9, 11, 17, 27, 42, 61, 81], "P": [9, 10, 15, 24, 35, 50, 67], "RET": [9, 10, 15, 24, 35, 50, 67]}
    for position, row in pinned.items():
        assert [CT.market_salary(position, r) for r in (40, 50, 60, 70, 80, 90, 99)] == row, position
    for position in D.POSITIONS:
        prices = [CT.market_salary(position, r) for r in range(D.RATING_MIN, D.RATING_MAX + 1)]
        assert prices == sorted(prices) and prices[0] == T.FR_MIN_SALARY and max(prices) <= T.FR_MAX_SALARY
    assert CT.market_salary("QB", 80) > CT.market_salary("DL", 80) > CT.market_salary("WR", 80) > CT.market_salary("S", 80) > \
        CT.market_salary("K", 80) > CT.market_salary("P", 80)


def test_the_rookie_scale_runs_in_straight_lines_between_its_points_and_never_rises_with_the_pick():
    assert [CT.rookie_salary(p) for p in (1, 2, 10, 32, 33, 64, 100, 128, 160, 192, 223, 224)] == [77, 75, 62, 26, 26, 17, 13, 11, 10, 10, 9, 9]
    scale = [CT.rookie_salary(p) for p in range(1, D.DRAFT_PICKS + 1)]
    assert scale == sorted(scale, reverse=True) and scale[0] == 77 and scale[-1] == T.FR_MIN_SALARY
    for pick, pay in T.FR_ROOKIE_SCALE:
        assert CT.rookie_salary(pick) == pay                                       # every point of the scale is hit exactly
    assert CT.rookie_salary(0) == 77 and CT.rookie_salary(999) == T.FR_MIN_SALARY      # outside the draft the ends hold


def test_the_length_of_a_new_contract_falls_with_age_and_is_never_under_a_year():
    assert [(a, CT.years_for_age(a)) for a in (21, 27, 28, 29, 30, 31, 32, 40)] == [(21, 4), (27, 4), (28, 3), (29, 3), (30, 2), (31, 2), (32, 1), (40, 1)]
    lengths = [CT.years_for_age(a) for a in range(D.AGE_MIN, D.AGE_MAX + 1)]
    assert lengths == sorted(lengths, reverse=True) and min(lengths) == 1


def test_dead_money_is_a_share_of_the_salary_for_every_year_left_rounded_half_up():
    player = Player(1, "A", "RB", 70, "average", 25, 3, 70, None, 0, "active", 0, 1, 0, 40, 3)
    assert CT.dead_money(player) == (40 * 3 * T.FR_DEAD_SHARE + 50) // 100 == 30
    player.salary, player.years = 9, 2
    assert CT.dead_money(player) == 5                                              # 4.5 goes up
    player.salary, player.years = 9, 1
    assert CT.dead_money(player) == 2                                              # 2.25 goes down


def test_an_amount_is_said_in_millions_with_a_tenth_only_when_there_is_one():
    assert [CT.millions(u) for u in (0, 9, 10, 124, 1932, 2000)] == ["0", "0.9", "1", "12.4", "193.2", "200"]


def test_an_amount_below_zero_is_said_with_a_minus_and_its_own_size_not_rounded_the_wrong_way():
    assert [CT.millions(u) for u in (-1, -10, -67, -124, -9)] == ["-0.1", "-1", "-6.7", "-12.4", "-0.9"]


def test_the_cap_is_the_nfls_scaled_to_34_places_and_the_scale_leaves_room_under_it():
    assert T.FR_CAP == round(3012 * 34 / 53) == 1932                                # 301.2 million x 34 / 53, in tenths of a million
    assert 34 * T.FR_MIN_SALARY < T.FR_CAP and 14 <= T.FR_MAX_SALARY * 100 // T.FR_CAP <= 15      # a top salary is about 14.5 percent of the cap
    assert CT.rookie_salary(1) < T.FR_MAX_SALARY


# ----- a new league -----

def test_a_new_league_has_a_contract_for_every_player_that_is_the_market_price_and_a_length_of_his_age():
    league = fresh()
    market = {t: sum(CT.market_salary(p.pos, p.rating) for p in league.active_of(t)) for t in range(1, D.TEAMS + 1)}
    assert any(total <= T.FR_CAP for total in market.values())
    for player in league.players.values():
        if market[player.team] <= T.FR_CAP:
            assert player.salary == CT.market_salary(player.pos, player.rating)
        else:                                                                        # a team that would start over the cap is lowered by one share
            assert T.FR_MIN_SALARY <= player.salary <= CT.market_salary(player.pos, player.rating)
        assert 1 <= player.years <= CT.years_for_age(player.age) and player.years == 1 + player.id % CT.years_for_age(player.age)
    assert league.dead == [0] * D.TEAMS
    assert all(CT.cap_used(league, t) <= T.FR_CAP for t in range(1, D.TEAMS + 1))
    league.check()                                                                  # and the league record accepts them


def test_the_contracts_of_a_league_are_the_same_for_the_same_seed_and_the_rules_take_no_random_source():
    import inspect
    assert fresh(seed=9).to_json() == fresh(seed=9).to_json() != fresh(seed=10).to_json()
    for rule in (CT.give_initial_contracts, CT.migrate, CT.turn_the_year, CT.initial_contract, CT.fit_to_cap, CT.cap_releases):
        assert "rnd" not in inspect.signature(rule).parameters and "source" not in inspect.signature(rule).parameters


def test_a_team_that_would_start_over_the_cap_is_lowered_by_one_share_and_the_others_are_not_touched():
    league = fresh()
    for player in league.active_of(3):
        player.rating = 99
        player.salary = CT.market_salary(player.pos, 99)
    others = {pid: p.salary for pid, p in league.players.items() if p.team != 3}
    assert CT.cap_used(league, 3) > T.FR_CAP
    assert CT.fit_to_cap(league) == 1
    assert T.FR_CAP - 34 < CT.cap_used(league, 3) <= T.FR_CAP                        # the sum fits and nothing is wasted by more than a tenth a player
    team = sorted(league.active_of(3), key=lambda p: p.id)
    assert all(p.salary >= T.FR_MIN_SALARY for p in team)
    assert {pid: p.salary for pid, p in league.players.items() if p.team != 3} == others
    assert CT.fit_to_cap(league) == 0                                                # and it is done


# ----- the year turns (stage 2) -----

def test_the_year_turns_a_year_off_every_contract_the_expired_ones_wait_with_no_years_and_the_dead_money_gone():
    league = fresh()
    league.dead[4] = 77
    ending = next(p for p in league.active_of(2) if p.years == 1)
    running = next(p for p in league.active_of(2) if p.years == 3 and p.age + 1 <= 27)
    before = (running.salary, running.years)
    before_ending = ending.salary
    aging.apply_aging(league, [])
    assert league.dead == [0] * D.TEAMS
    assert (running.salary, running.years) == (before[0], before[1] - 1)             # a year less, the same salary
    assert ending.years == 0 and ending.salary == before_ending                      # the contract ran out: no years, the last salary kept (the tag's raise)
    assert not CT.running(ending) and CT.payroll(league, 2) == sum(p.salary for p in league.active_of(2) if p.years > 0)
    assert all(0 <= p.years <= CT.years_for_age(p.age) for p in league.players.values() if p.status == "active")


def test_a_player_who_retires_leaves_no_contract_and_costs_no_dead_money():
    league = fresh()
    player = league.player_at(1, 0)
    aging.apply_aging(league, [player])
    assert player.status == "retired" and player.salary == 0 and player.years == 0
    assert league.dead == [0] * D.TEAMS


def test_a_released_player_costs_dead_money_to_his_team_and_has_no_contract_after():
    league = fresh()
    player = league.player_at(6, 0)
    player.salary, player.years = 40, 3
    assert CT.release(league, player) == 30
    assert league.dead[5] == 30 and player.salary == 0 and player.years == 0
    other = league.player_at(6, 1)
    other.salary, other.years = 12, 2
    CT.release(league, other)
    assert league.dead[5] == 30 + 6 and sum(league.dead) == 36


# ----- the draft and the cut -----

def test_a_drafted_rookie_has_the_scale_of_his_pick_for_four_years_and_an_undrafted_one_the_minimum_for_three():
    league = cut_league()
    rows = league.draft["picks"]
    assert len(rows) == D.DRAFT_PICKS
    for number, (team, _index, pid) in enumerate(rows, start=1):
        player = league.players[pid]
        assert (player.salary, player.years) == (CT.rookie_salary(number), T.FR_ROOKIE_YEARS), number
        assert CT.draft_overall(player) == number
    start = league.next_id
    for index in (0, 1):
        league.rosters[4][index] = 0                                                  # two empty places on the player's team
    filled = aging.fill_places(league, rnd(), SURNAMES)
    assert filled == 2
    new = [p for p in league.players.values() if p.id >= start]
    assert len(new) == 2 and all((p.salary, p.years) == (T.FR_MIN_SALARY, T.FR_FILL_YEARS) for p in new)


def test_the_cut_charges_the_dead_money_of_every_release_to_its_team_and_ends_the_contract():
    league = cut_league()
    waiting = DR.waiting_by_team(league)
    plans = {t: DR.plan_cut(league, t, waiting) for t in range(1, D.TEAMS + 1)}
    expected = [sum(CT.dead_money(p) for p in plans[t]) for t in range(1, D.TEAMS + 1)]
    assert sum(expected) > 0 and league.dead == [0] * D.TEAMS
    DR.apply_cut(league, plans, waiting)
    assert league.dead == expected
    assert all(p.salary == 0 and p.years == 0 for released in plans.values() for p in released)


def test_the_cap_after_the_cut_and_the_fill_is_exactly_what_the_team_then_uses():
    league = cut_league()
    waiting = DR.waiting_by_team(league)
    plans = {t: DR.staff_cut(league, t, waiting) for t in range(1, D.TEAMS + 1)}
    predicted = {t: CT.cap_after_cut(league, t, waiting, plans[t]) for t in plans}
    DR.apply_cut(league, plans, waiting)
    aging.fill_places(league, rnd(), SURNAMES)
    league.draft = None
    assert all(CT.cap_used(league, t) == predicted[t] for t in plans)
    assert all(CT.cap_used(league, t) <= T.FR_CAP for t in plans)                    # the staff's list leaves every team under the cap


# ----- the cap rule of the cut -----

def over_the_cap(team=1):
    """A league whose team is 448 tenths over the cap with every player on a one-year contract (so a release costs little dead money) and a
    different rating for every place, so the staff's order is one order."""
    league = fresh()
    for index, player in enumerate(league.active_of(team)):
        player.salary, player.years, player.rating = 70, 1, 50 + index
    return league


def test_a_team_under_the_cap_after_the_cut_releases_nobody_for_it():
    league = fresh()
    assert CT.cap_over(league, 1, {}, []) < 0 and CT.cap_releases(league, 1, {}, []) == []


def test_a_team_over_the_cap_releases_in_the_staffs_order_until_the_cap_is_met_and_no_more():
    league = over_the_cap()
    over = CT.cap_over(league, 1, {}, [])
    assert over == 34 * 70 - T.FR_CAP == 448
    extra = CT.cap_releases(league, 1, {}, [])
    saved = 70 - T.FR_MIN_SALARY - CT.dead_money(league.player_at(1, 0))            # a release saves the salary less the minimum and the dead money
    assert saved == 43 and len(extra) == -(-over // saved) == 11
    assert CT.cap_over(league, 1, {}, extra) <= 0 < CT.cap_over(league, 1, {}, extra[:-1])      # the last one was needed
    assert [CT.release_value(p) for p in extra] == sorted(CT.release_value(p) for p in extra)       # the staff's order
    assert extra == CT.cap_candidates(league, 1, {}, [])[:len(extra)]
    predicted = CT.cap_after_cut(league, 1, {}, extra)
    DR.apply_cut(league, {1: extra}, {})
    aging.fill_places(league, rnd(), SURNAMES)
    assert CT.cap_used(league, 1) == predicted <= T.FR_CAP


def exactly_at_the_cap(offset=0):
    """Team 1 uses the cap plus `offset` tenths of a million after the cut and the fill (raising salaries one by one)."""
    league = fresh()
    todo = T.FR_CAP + offset - CT.cap_after_cut(league, 1, {}, [])
    assert todo > 0
    for player in league.active_of(1):
        step = min(todo, T.FR_MAX_SALARY - player.salary)
        player.salary += step
        todo -= step
    assert todo == 0
    return league


def test_a_team_exactly_at_the_cap_releases_nobody_and_one_tenth_over_releases_one_player():
    league = exactly_at_the_cap()
    assert CT.cap_over(league, 1, {}, []) == 0 and CT.cap_releases(league, 1, {}, []) == []
    over = exactly_at_the_cap(offset=1)
    assert CT.cap_over(over, 1, {}, []) == 1
    extra = CT.cap_releases(over, 1, {}, [])
    assert len(extra) == 1 and CT.cap_over(over, 1, {}, extra) <= 0


def test_the_staff_lets_go_first_of_those_who_give_least_for_what_they_cost():
    league = over_the_cap()
    candidates = CT.cap_candidates(league, 1, {}, [])
    assert candidates == sorted(candidates, key=CT.release_value) and len(candidates) == 34
    assert CT.release_value(candidates[0]) < CT.release_value(candidates[-1])
    cheap_and_poor = league.player_at(1, 2)
    cheap_and_poor.rating = 45                                                       # worse than any replacement: nothing is lost by releasing him
    assert cheap_and_poor in CT.cap_candidates(league, 1, {}, [])[:2]                # with the one player of exactly his replacement's rating
    assert CT.release_value(cheap_and_poor)[0] == 0                                 # no better than his replacement: before everybody else
    worse_and_dearer = league.player_at(1, 3)
    worse_and_dearer.rating, worse_and_dearer.salary = 44, 75
    first = CT.cap_candidates(league, 1, {}, [])
    assert first[0] is worse_and_dearer and cheap_and_poor in first[:3]       # of such players the one who saves most goes first


def test_the_position_counts_in_the_staffs_order_the_part_of_the_strength_it_is():
    """The same pay and the same rating over the replacement: a kicker's release costs the team less strength than a quarterback's."""
    league = fresh()
    kicker, quarterback = league.player_at(1, D.PLACES_OF["K"][0]), league.player_at(1, D.PLACES_OF["QB"][0])
    for player in (kicker, quarterback):
        player.salary, player.years = 60, 1
    kicker.rating = CT.replacement_rating("K") + 10
    quarterback.rating = CT.replacement_rating("QB") + 10
    assert D.WEIGHT["QB"] > D.WEIGHT["K"] and CT.release_value(kicker) < CT.release_value(quarterback)
    kicker.rating += 30                                                              # a kicker much better than his replacement is worth more
    assert CT.release_value(kicker) > CT.release_value(quarterback)


def test_a_player_whose_release_saves_nothing_is_never_a_candidate_and_the_search_ends_when_nobody_saves():
    league = fresh()
    for player in league.active_of(1):
        player.salary, player.years = 100, 4                                          # dead money = the whole salary: a release saves nothing
    assert CT.cap_over(league, 1, {}, []) > 0
    assert CT.cap_candidates(league, 1, {}, []) == [] and CT.cap_releases(league, 1, {}, []) == []
    for player in league.active_of(1)[:3]:
        player.salary = T.FR_MIN_SALARY
    assert all(p.salary > T.FR_MIN_SALARY for p in CT.cap_candidates(league, 1, {}, []))


def test_the_dead_money_a_team_already_holds_counts_in_what_it_uses_after_the_cut():
    league = fresh()
    base = CT.cap_after_cut(league, 1, {}, [])
    league.dead[0] = 60
    assert CT.cap_after_cut(league, 1, {}, []) == base + 60
    assert CT.cap_over(league, 1, {}, []) == CT.cap_used(league, 1) - T.FR_CAP


def test_the_cuts_own_list_is_counted_before_the_cap_rule_looks_at_the_team():
    league = cut_league()
    waiting = DR.waiting_by_team(league)
    cut = DR.plan_cut(league, 5, waiting)
    assert cut and CT.cap_after_cut(league, 5, waiting, cut) != CT.cap_after_cut(league, 5, waiting, [])
    for player in DR.group_players(league, 5, "QB", waiting):
        player.salary, player.years = T.FR_MAX_SALARY, 1
    extra = CT.cap_releases(league, 5, waiting, cut)
    assert not set(p.id for p in extra) & set(p.id for p in cut)                     # nobody is released twice


# ----- a format-1 league -----

def as_format_one(league):
    data = json.loads(league.to_json())
    data["format"] = 1
    del data["dead"], data["resign"], data["market"], data["trades"], data["injuries"], data["staff"]   # what formats 2 to 7 added (SX.8j review: a draft of format 1 has no owners)
    del data["comp"], data["future_picks"], data["tags"]                                               # and format 8 (SX.8m)
    if isinstance(data["draft"], dict):
        del data["draft"]["owners"], data["draft"]["comp"], data["draft"]["undrafted"]
    data["players"] = [row[:14] for row in data["players"]]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def test_a_format_one_file_still_loads_and_gets_its_contracts_by_the_rules_with_no_draw():
    league = fresh()
    young = [league.player_at(2, 0), league.player_at(2, 1), league.player_at(2, 2)]
    young[0].drafted, young[0].seasons = [1, 1, 5], 1                                 # pick 5 of round 1, one season played
    young[1].drafted, young[1].seasons = [1, 3, 9], 3                                 # pick 73, three seasons played
    young[2].drafted, young[2].seasons = [1, 2, 1], 4                                 # four seasons played: his rookie contract is over
    gone = Player(league.next_id, "Gone", "RB", 60, "low", 33, 11, 80, None, 0, "retired", 1, 7, -1)
    league.players[gone.id] = gone
    league.next_id += 1
    text = as_format_one(league)
    assert '"format":1' in text and "dead" not in text
    loaded = LeagueRecord.from_json(text)
    assert (young_of := loaded.players[young[0].id]).salary == CT.rookie_salary(5) and young_of.years == 3
    assert (loaded.players[young[1].id].salary, loaded.players[young[1].id].years) == (CT.rookie_salary(64 + 9), 1)
    old = loaded.players[young[2].id]
    assert (old.salary, old.years) == (CT.market_salary(old.pos, old.rating), 1 + old.id % CT.years_for_age(old.age))
    assert (loaded.players[gone.id].salary, loaded.players[gone.id].years) == (0, 0)
    assert loaded.dead == [0] * D.TEAMS
    market = {t: sum(CT.market_salary(p.pos, p.rating) for p in league.active_of(t)) for t in range(1, D.TEAMS + 1)}
    for player in loaded.players.values():
        if player.status == "active" and player.id not in {y.id for y in young}:
            assert 1 <= player.years <= CT.years_for_age(player.age)
            if market[player.team] <= T.FR_CAP:
                assert player.salary == CT.market_salary(player.pos, player.rating)
    assert all(CT.cap_used(loaded, t) <= T.FR_CAP for t in range(1, D.TEAMS + 1))
    assert json.loads(loaded.to_json())["format"] == D.FORMAT == 12                    # the next save is format 11 (SX.12)
    again = LeagueRecord.from_json(text)
    assert again.to_json() == loaded.to_json()                                        # a migration draws nothing: the same file, the same answer
    assert LeagueRecord.from_json(loaded.to_json()).to_json() == loaded.to_json()


def test_a_format_one_team_that_would_be_over_the_cap_is_lowered_when_it_is_read():
    league = fresh()
    for player in league.active_of(8):
        player.rating = 99
    loaded = LeagueRecord.from_json(as_format_one(league))
    assert CT.cap_used(loaded, 8) <= T.FR_CAP and CT.cap_used(loaded, 7) == CT.cap_used(league, 7)
    assert all(p.salary >= T.FR_MIN_SALARY for p in loaded.active_of(8))


def test_a_format_one_team_over_the_cap_keeps_the_scale_of_its_rookies_and_the_lowering_falls_on_the_others():
    league = fresh()
    for player in league.active_of(4):
        player.rating = 99
    rookie = league.player_at(4, 0)
    rookie.drafted, rookie.seasons = [1, 1, 1], 1
    loaded = LeagueRecord.from_json(as_format_one(league))
    assert (loaded.players[rookie.id].salary, loaded.players[rookie.id].years) == (CT.rookie_salary(1), 3)
    assert CT.cap_used(loaded, 4) <= T.FR_CAP
    assert all(loaded.players[p.id].salary <= CT.market_salary(p.pos, p.rating) for p in league.active_of(4) if p.id != rookie.id)


def test_a_format_one_league_in_an_offseason_with_waiting_rookies_gets_their_scale_too():
    league = cut_league()
    text = as_format_one(league)
    loaded = LeagueRecord.from_json(text)
    for number, (_team, _index, pid) in enumerate(loaded.draft["picks"], start=1):
        assert (loaded.players[pid].salary, loaded.players[pid].years) == (CT.rookie_salary(number), T.FR_ROOKIE_YEARS)
    assert loaded.draft is not None and len(loaded.draft["picks"]) == D.DRAFT_PICKS and loaded.stage_no == D.STAGE_CUT


# ----- the damage matrix of the new values -----

def damaged(change):
    data = json.loads(fresh().to_json())
    change(data)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def row_change(index, value):
    def change(data):
        data["players"][0][index] = value
    return change


@pytest.mark.parametrize("change", [
    row_change(14, T.FR_MIN_SALARY - 1), row_change(14, T.FR_MAX_SALARY + 1), row_change(14, -5), row_change(14, True), row_change(14, 12.5),
    row_change(14, "12"), row_change(14, None), row_change(15, 0), row_change(15, 5), row_change(15, -1), row_change(15, False),
    row_change(15, 2.0), row_change(15, "2"), row_change(15, None),
    lambda data: data["players"][0].pop(),                                              # a format-2 row of 15 values
    lambda data: data["players"][0].__delitem__(slice(14, 16)),                         # and one of 14 (a format-1 row in a format-2 file)
    lambda data: data["players"][0].append(0),                                          # and one of 17
    lambda data: data.pop("dead"),
    lambda data: data.__setitem__("dead", [0] * 31),
    lambda data: data.__setitem__("dead", [0] * 33),
    lambda data: data.__setitem__("dead", "none"),
    lambda data: data.__setitem__("dead", None),
    lambda data: data["dead"].__setitem__(3, -1),
    lambda data: data["dead"].__setitem__(3, D.MAX_DEAD + 1),
    lambda data: data["dead"].__setitem__(3, 1.5),
    lambda data: data["dead"].__setitem__(3, True),
    lambda data: data["dead"].__setitem__(3, "7"),
])
def test_a_contract_or_dead_money_out_of_range_or_of_the_wrong_kind_is_damage(change):
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(damaged(change))


def test_a_released_or_retired_player_with_a_contract_out_of_range_is_damage():
    league = fresh()
    gone = Player(league.next_id, "Gone", "RB", 60, "low", 33, 11, 80, None, 0, "retired", 1, 7, -1, T.FR_MAX_SALARY + 1, 0)
    league.players[gone.id] = gone
    league.next_id += 1
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())
    gone.salary, gone.years = 0, 5
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_formats_other_than_one_to_three_are_damage_or_newer():
    text = fresh().to_json()
    for version in (0, -1, True, 1.5, "2", None):
        with pytest.raises(LeagueError) as raised:
            LeagueRecord.from_json(text.replace('"format":12', '"format":%s' % json.dumps(version), 1))
        assert not isinstance(raised.value, NewerFormat)
    with pytest.raises(NewerFormat):
        LeagueRecord.from_json(text.replace('"format":12', '"format":13', 1))


def test_a_format_one_file_with_a_contract_column_is_damage_like_any_row_of_the_wrong_length():
    text = fresh().to_json().replace('"format":12', '"format":1', 1)
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(text)


def test_the_league_record_round_trips_with_its_contracts_and_dead_money():
    league = fresh()
    league.dead[9] = 123
    player = league.player_at(4, 3)
    player.salary, player.years = 77, 2
    again = LeagueRecord.from_json(league.to_json())
    assert again.dead[9] == 123 and (again.players[player.id].salary, again.players[player.id].years) == (77, 2)
    assert again.to_json() == league.to_json() and copy.copy(again).dead == again.dead
