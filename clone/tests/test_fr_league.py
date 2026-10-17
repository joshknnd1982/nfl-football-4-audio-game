"""The league record of a Franchise: creation, the strength, the roster for a game and the whole-file check by stage (nfl4 only,
rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 4, 10.1 and 12 (the draws of a new league), SX.8a. The creation invariants are the ones the 20-season runs of
SX.8f check after every offseason: every place filled, ratings 40 to 99, ages 21 to 40, no name twice among the active.
"""
import copy
import random

import pytest

from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import (OFFSEASON, SEASON, LeagueError, LeagueRecord, NewerFormat, Player, new_league,
                                          team_index, team_ref)
from nfl4.game.names import load_surnames
from nfl4.game.rnd import GameRandom
from nfl4.game.setup import Roster

SURNAMES = load_surnames()


def make(seed=1, team=5, own=None, trace=False):
    rnd = GameRandom(random.Random(seed))
    if trace:
        rnd.trace = []
    return new_league(rnd, SURNAMES, "Kim", team, "20260101-000000", own), rnd


def complete_roster(prefix="Own"):
    names = ["%s%02d" % (prefix, i) for i in range(1, 34)]
    return Roster(names[0:6], names[6:12], names[12:29], names[29:31], names[31:33], quarterback="Quincy")


# ----- the places -----

def test_a_team_has_34_places_in_the_originals_order_with_a_position_each():
    assert D.PLACE_COUNT == 34 and len(D.PLACES) == 34
    assert D.GROUP_SIZE == {"RB": 6, "WR": 6, "QB": 1, "DL": 6, "LB": 5, "CB": 4, "S": 2, "RET": 2, "K": 1, "P": 1}
    assert D.PLACES[0] == ("Running Backs:", 1, "RB") and D.PLACES[6] == ("Receivers:", 1, "WR")
    assert D.PLACES[12] == ("Defensive Players:", 1, "DL") and D.PLACES[28] == ("Defensive Players:", 17, "S")
    assert D.PLACES[29] == ("Special Teams Players:", 1, "RET") and D.PLACES[31] == ("Kickers:", 1, "K")
    assert D.PLACES[32] == ("Kickers:", 2, "P") and D.PLACES[33] == ("Quarterback:", 1, "QB")
    assert D.WEIGHT_SUM == 78                                          # design 4.4


def test_team_numbers_and_the_engines_division_and_place_turn_into_each_other():
    assert team_ref(1) == (1, 1) and team_ref(4) == (1, 4) and team_ref(5) == (2, 1) and team_ref(32) == (8, 4)
    assert all(team_index(*team_ref(t)) == t for t in range(1, 33))


# ----- a new league -----

def test_a_new_league_has_32_full_teams_with_every_value_in_range():
    league, _ = make()
    league.check()
    assert len(league.players) == 32 * 34 == 1088 and league.next_id == 1089
    for team in range(1, 33):
        assert all(pid for pid in league.rosters[team - 1])
        for index, player in enumerate(league.active_of(team)):
            assert player.pos == D.POSITION_OF_PLACE[index] and player.team == team and player.place == index
            assert D.RATING_MIN <= player.rating <= D.RATING_MAX and player.peak == player.rating
            assert 21 <= player.age <= (36 if player.pos in ("K", "P") else 32)
            assert player.seasons == max(0, player.age - 22) and player.potential in D.POTENTIALS


def test_no_name_is_used_twice_among_the_active_players_while_free_names_exist():
    league, _ = make()
    names = [p.name for p in league.players.values()]
    assert len(set(names)) == len(names)


def test_the_league_is_not_all_alike_there_is_a_spread_of_strengths():
    league, _ = make()
    sums = [league.strength_sum(t) for t in range(1, 33)]
    assert max(sums) > min(sums) and league.sums == sums
    ratings = [p.rating for p in league.players.values()]
    assert 66 <= sum(ratings) / len(ratings) <= 74                      # the mean rating is about 70 (design 4.5)


def test_the_same_seed_makes_the_same_league_and_another_seed_another():
    a, _ = make(7)
    b, _ = make(7)
    c, _ = make(8)
    assert a.to_json() == b.to_json() and a.to_json() != c.to_json()


def test_the_players_team_is_made_first_with_the_names_of_the_file_and_its_quarterback():
    own = complete_roster()
    league, _ = make(team=9, own=own)
    names = [p.name for p in league.active_of(9)]
    assert names == own.names() + ["Quincy"]
    first_ids = [league.rosters[8][i] for i in range(34)]
    assert first_ids == list(range(1, 35))                              # the player's team got the first IDs
    others = [p.name for t in range(1, 33) if t != 9 for p in league.active_of(t)]
    assert not set(others) & set(names)                                 # nobody else has a name of the file


def test_a_file_that_is_not_complete_is_not_used_and_a_missing_quarterback_is_drawn():
    partial = complete_roster()
    partial.kickers = ["Only"]
    league, _ = make(team=2, own=partial)
    assert not any(p.name.startswith("Own") for p in league.players.values())
    no_qb = complete_roster()
    no_qb.quarterback = ""
    league, _ = make(team=2, own=no_qb)
    qb = league.player_at(2, 33)
    assert qb.name != "" and not qb.name.startswith("Own") and qb.pos == "QB"
    assert [p.name for p in league.active_of(2)][:33] == no_qb.names()


def test_the_draws_of_a_new_league_come_in_the_order_of_design_12():
    own = complete_roster()
    league, rnd = make(team=1, own=own, trace=True)
    sizes = rnd.trace
    place = [13, 13, 100, 5, 5, 4]
    # the player's team: the level, then for each of the 33 named places the rating, the potential, the age (the 34th, the
    # quarterback, has a name from the file too); kickers and punters draw one more age number
    level = T.FR_TEAM_LEVEL_SPAN                                         # 9 at the design's start values, 5 since SX.8b (D-057); the
    #                                                                      calibrated span itself is pinned by test_fr_ratings.py (CALIBRATED)
    expected = [level]
    for index in range(34):
        expected += place + ([5] if D.POSITION_OF_PLACE[index] in ("K", "P") else [])
    assert sizes[:len(expected)] == expected
    # the next team starts with its level, then the name draw of the first place
    assert sizes[len(expected)] == level and sizes[len(expected) + 1] == 1708


def test_a_names_redraw_is_bounded_when_the_pool_is_used_up():
    rnd = GameRandom(random.Random(1))
    tiny = ["A", "B", "C"]                                              # 1,088 players cannot have 3 different names
    league = new_league(rnd, tiny, "Kim", 1, "20260101-000000")
    league.check()                                                      # a duplicate is allowed only when the pool is used up
    assert len(league.players) == 1088 and rnd.fallbacks > 0


# ----- the strength and the rank (design 4.4) -----

def set_all(league, rating):
    for player in league.players.values():
        player.rating = player.peak = rating


def test_a_team_of_70s_has_strength_70_and_the_weighted_sum_78_times_70():
    league, _ = make()
    set_all(league, 70)
    assert league.strength_sum(3) == 78 * 70 == 5460 and league.strength(3) == 70


def test_the_quarterback_counts_12_and_a_returner_1_in_the_exact_sum():
    league, _ = make()
    set_all(league, 70)
    league.player_at(3, 33).rating = 71
    assert league.strength_sum(3) == 5460 + 12
    league.player_at(3, 29).rating = 69
    assert league.strength_sum(3) == 5460 + 12 - 1


def test_the_rank_is_by_the_exact_sum_with_ties_to_the_lower_team_number():
    league, _ = make()
    set_all(league, 70)
    league.player_at(7, 31).rating = 80                                 # the kicker, weight 4
    league.player_at(20, 31).rating = 80
    league.player_at(2, 33).rating = 60                                 # the quarterback, weight 12
    ranking = league.ranking()
    assert ranking[:2] == [7, 20] and ranking[-1] == 2 and league.rank_of(7) == 1 and league.rank_of(20) == 2
    assert league.rank_of(1) == 3 and league.rank_of(2) == 32


def test_while_places_are_empty_the_rating_and_the_rank_are_those_kept_at_the_start_of_the_season():
    league, _ = make()
    set_all(league, 70)
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    league.sums[8] += 500                                                # team 9 was the best at the start of the season
    assert league.ranking()[0] == 1 and not league.has_empty_place()      # whole rosters: the exact sums rule (all equal: team order)
    pid = league.rosters[2][0]                                            # a running back of team 3 retires
    league.players[pid].status, league.players[pid].place = "retired", -1
    league.rosters[2][0] = 0
    assert league.has_empty_place()
    assert league.ranking()[0] == 9 and league.strength(3) == 70 and league.rank_of(3) == 4    # the kept sums: after 9, 1 and 2
    assert league.strength_sum(3) == 5460 - 2 * 30                       # the exact sum counts the empty place as 40


# ----- the roster for a game (H7) -----

def test_the_roster_for_a_game_has_the_names_by_section_the_ratings_and_the_quarterback():
    league, _ = make()
    roster = league.roster_for_game(5)
    assert roster.is_complete() and roster.quarterback == league.player_at(5, 33).name
    assert roster.running_backs == [league.player_at(5, i).name for i in range(0, 6)]
    assert roster.kickers == [league.player_at(5, 31).name, league.player_at(5, 32).name]
    assert roster.ratings[("Defensive Players:", 14)] == league.player_at(5, 12 + 13).rating
    assert roster.ratings[("Quarterback:", 1)] == league.player_at(5, 33).rating and len(roster.ratings) == 34


# ----- the file and the whole-file check by stage (design 10.1, B-X49) -----

def test_the_record_round_trips_through_its_text():
    league, _ = make()
    league.stage, league.gtp = SEASON, 1
    league.schedule = [[2, 1, 1]] * 16
    again = LeagueRecord.from_json(league.to_json())
    assert again.to_json() == league.to_json() and again.players.keys() == league.players.keys()


def season_league():
    league, _ = make()
    league.schedule = [[2, 1, 1]] * 16
    return league


def broken(mutate, text_part):
    league = season_league()
    mutate(league)
    with pytest.raises(LeagueError) as excinfo:
        LeagueRecord.from_json(league.to_json())
    assert text_part in str(excinfo.value), str(excinfo.value)


def test_a_value_out_of_range_is_damage_never_clamped():
    broken(lambda l: setattr(l.players[10], "rating", 100), "rating")
    broken(lambda l: setattr(l.players[10], "age", 20), "age")
    broken(lambda l: setattr(l.players[10], "age", 41), "age")
    broken(lambda l: setattr(l.players[10], "potential", "huge"), "potential")
    broken(lambda l: setattr(l.players[10], "points", 4), "points")
    broken(lambda l: setattr(l, "team", 33), "team")
    broken(lambda l: setattr(l, "season", 0), "season")
    broken(lambda l: setattr(l, "gtp", 21), "week")
    broken(lambda l: setattr(l, "league_id", ""), "league ID")


def test_a_place_must_hold_an_active_player_of_that_team_in_that_place_with_that_position():
    def swap_teams(l):
        l.rosters[0][0], l.rosters[1][0] = l.rosters[1][0], l.rosters[0][0]
    broken(swap_teams, "not active there")
    broken(lambda l: l.rosters[0].__setitem__(1, l.rosters[0][0]), "not active there")      # in the wrong place
    broken(lambda l: l.rosters[0].__setitem__(0, 99999), "not active there")                 # a player who does not exist
    broken(lambda l: setattr(l.players[1], "status", "retired"), "")                          # retired but still placed


def test_a_season_needs_every_place_filled_and_a_schedule_and_matching_records():
    broken(lambda l: l.rosters[3].__setitem__(5, 0), "empty place")
    broken(lambda l: setattr(l, "schedule", [[2, 1, 1]] * 15), "schedule")
    broken(lambda l: (setattr(l, "gtp", 3)), "wins and")                                      # week 3: 2 games should be played
    league = season_league()
    league.gtp = 3
    league.records = [1, 1] * 32
    LeagueRecord.from_json(league.to_json())                                                 # 1 and 1 after 2 weeks: whole


def test_a_record_in_an_offseason_stage_with_empty_places_is_not_damage(monkeypatch):
    monkeypatch.setattr(D, "STAGES", ((1, "NXE-11"), (2, "NXE-12"), (3, "NXE-13"), (4, "NXE-14"), (5, "NXE-15"), (6, "NXE-16")))
    league = season_league()
    league.stage, league.gtp, league.records = OFFSEASON, 0, [8, 8] * 32
    for stage_no in (1, 6):
        league.stage_no = stage_no
        LeagueRecord.from_json(league.to_json())
    pid = league.rosters[3][5]
    league.players[pid].status, league.players[pid].team, league.players[pid].place = "retired", 0, -1
    league.rosters[3][5] = 0
    for stage_no in (2, 3, 4, 5):                                     # places may be empty while the offseason is going on
        league.stage_no = stage_no
        LeagueRecord.from_json(league.to_json())
    for stage_no in (1, 6):                                           # but not at stage 1 or stage 6
        league.stage_no = stage_no
        with pytest.raises(LeagueError):
            LeagueRecord.from_json(league.to_json())


def test_an_unknown_stage_number_is_damage_and_a_newer_format_is_not():
    league = season_league()
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, 8, 0, [8, 8] * 32
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())                      # this version has seven stages (numbers 1 to 7): there is no stage 8
    league.stage_no = 0
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())                      # and no stage 0 in an offseason
    text = season_league().to_json().replace('"format":3', '"format":4', 1)
    with pytest.raises(NewerFormat):
        LeagueRecord.from_json(text)


@pytest.mark.parametrize("text", ["", "{", "[]", "null", '{"format":1}', "\x00" * 20, '{"format":1,"game":"other"}'])
def test_text_that_is_not_a_league_is_damage(text):
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(text)


def test_a_player_row_of_the_wrong_shape_is_damage():
    league = season_league()
    data = copy.deepcopy(__import__("json").loads(league.to_json()))
    data["players"][0] = [1, 2, 3]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(__import__("json").dumps(data))
    data = __import__("json").loads(league.to_json())
    data["players"] = "none"
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(__import__("json").dumps(data))


def test_a_player_is_a_list_of_fourteen_values_and_comes_back_equal():
    p = Player(5, "Smith", "QB", 77, "high", 25, 3, 80, [2, 1, 4], 2, "active", 0, 3, 33)
    assert Player.from_list(p.to_list()) == p
