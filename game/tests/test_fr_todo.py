"""The to-do list of the Franchise: its items, their answers, the computer teams' extra work, the game plan and the check of the list
in league.sav (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 8.1 and 8.2 (SX.8e). The rules are plain functions over the league record (`extras/franchise/todo.py`), so the
tests build a league, shape a team's players and call them; nothing is drawn. The week's flow on the program rig is
tests/test_fr_week.py.
"""
import importlib.util
import os
import random

import pytest

from drrig import SURNAMES
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import todo
from nfl4.extras.franchise.league import LeagueError, new_league
from nfl4.extras.playbook_data import BOOK_KEYS, STYLES
from nfl4.game.rnd import GameRandom

STYLE_KEYS = {s.key for s in STYLES}
TEAM = 5


def a_league(seed=3, team=TEAM):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def shape(league, team, specs):
    """Make the team's players old and low (no candidate), then give the first players of its roster the listed
    (age, potential, rating, points). Returns those players."""
    players = [p for p in league.active_of(team)]
    for p in players:
        p.age, p.potential, p.points = 30, "low", 0
    chosen = []
    for player, (age, potential, rating, points) in zip(players, specs):
        player.age, player.potential, player.rating, player.points = age, potential, rating, points
        chosen.append(player)
    return chosen


def whole(value, low, high, what):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise LeagueError("%s is %r" % (what, value))


# ----- who can take the point -----

def test_the_two_candidates_are_the_highest_potential_then_the_youngest_then_the_best_rated_then_the_lower_id():
    league = a_league()
    a, b, c, d, e = shape(league, TEAM, [(24, "average", 70, 0), (22, "average", 65, 0), (23, "high", 60, 0), (23, "high", 66, 0),
                                         (23, "high", 66, 0)])
    assert d.id < e.id
    assert [p.id for p in todo.candidates(league, TEAM)] == [d.id, e.id]      # high potential first; of age 23 the rating 66, then the ID
    c.age = 21
    assert [p.id for p in todo.candidates(league, TEAM)] == [c.id, d.id]      # the youngest of the high potentials goes first
    c.potential = "average"
    assert [p.id for p in todo.candidates(league, TEAM)] == [d.id, e.id]
    d.potential = e.potential = "average"
    assert [p.id for p in todo.candidates(league, TEAM)] == [c.id, b.id]      # average potential: age 21, then age 22


def test_age_potential_and_points_decide_who_is_a_candidate():
    league = a_league()
    old, low, full, ok = shape(league, TEAM, [(25, "high", 80, 0), (22, "low", 80, 0), (22, "high", 80, T.FR_EXTRA_WORK_POINTS),
                                              (T.FR_EXTRA_WORK_AGE, "average", 50, T.FR_EXTRA_WORK_POINTS - 1)])
    assert not todo.is_candidate(old) and not todo.is_candidate(low) and not todo.is_candidate(full) and todo.is_candidate(ok)
    assert todo.candidates(league, TEAM) == []                      # one candidate is not two


def test_a_team_with_fewer_than_two_candidates_has_none():
    league = a_league()
    shape(league, TEAM, [(22, "high", 70, 0)])
    assert todo.candidates(league, TEAM) == []
    shape(league, TEAM, [(22, "high", 70, 0), (22, "average", 70, 0)])
    assert len(todo.candidates(league, TEAM)) == 2


def test_a_released_or_retired_player_is_not_a_candidate():
    league = a_league()
    first, second = shape(league, TEAM, [(22, "high", 70, 0), (22, "high", 69, 0)])
    first.status = "retired"
    assert not todo.is_candidate(first) and todo.candidates(league, TEAM) == []


# ----- the computer teams -----

def every_team_has_two(league):
    for team in range(1, D.TEAMS + 1):
        shape(league, team, [(22, "high", 70, 0), (23, "average", 70, 0)])


def test_the_computer_teams_give_their_first_candidate_a_point_in_the_four_weeks_and_never_the_players_team():
    league = a_league()
    every_team_has_two(league)
    assert T.FR_EXTRA_WORK_WEEKS == (2, 6, 10, 14)
    firsts = {t: todo.candidates(league, t)[0] for t in range(1, D.TEAMS + 1)}
    assert todo.computer_extra_work(league, 2) == D.TEAMS - 1
    for team, player in firsts.items():
        assert player.points == (0 if team == TEAM else 1)
    for week in (1, 3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 16):
        assert todo.computer_extra_work(league, week) == 0, week
    assert sum(p.points for p in league.players.values()) == D.TEAMS - 1


def test_a_team_stops_at_three_points_a_season_and_a_team_without_two_candidates_gives_none():
    league = a_league()
    every_team_has_two(league)
    for week in T.FR_EXTRA_WORK_WEEKS:
        todo.computer_extra_work(league, week)
    other = 1 if TEAM != 1 else 2
    first, second = league.active_of(other)[0], league.active_of(other)[1]
    assert (first.points, second.points) == (3, 0)                  # the fourth week: one candidate is left, so no point
    assert todo.candidates(league, other) == []


def test_the_candidates_come_from_the_same_rule_for_the_player_and_the_computer():
    league = a_league()
    every_team_has_two(league)
    item = todo.extra_work_item(league, 6)
    assert item["players"] == [p.id for p in todo.candidates(league, TEAM)]
    assert todo.extra_work_item(league, 5) is None and todo.extra_work_item(league, 17) is None


def test_no_item_when_the_players_team_has_fewer_than_two_candidates():
    league = a_league()
    shape(league, TEAM, [(22, "high", 70, 0)])
    assert todo.extra_work_item(league, 2) is None


# ----- answering -----

def extra_work_league():
    league = a_league()
    shape(league, TEAM, [(22, "high", 70, 0), (23, "average", 70, 0)])
    item = todo.extra_work_item(league, 2)
    league.todo.append(item)
    return league, item


def test_the_first_answer_gives_the_first_candidate_a_point_and_the_item_goes():
    league, item = extra_work_league()
    first, second = (league.players[pid] for pid in item["players"])
    assert todo.answer_count(league, item) == 3
    assert todo.apply_answer(league, item, 0) is first
    assert (first.points, second.points) == (1, 0) and league.todo == []


def test_the_second_answer_gives_the_second_candidate_the_point():
    league, item = extra_work_league()
    first, second = (league.players[pid] for pid in item["players"])
    assert todo.apply_answer(league, item, 1) is second
    assert (first.points, second.points) == (0, 1)


def test_nobody_this_week_is_the_last_answer_gives_no_point_and_the_item_goes():
    league, item = extra_work_league()
    assert todo.is_do_nothing(league, item, 2) and not todo.is_do_nothing(league, item, 0)
    assert todo.apply_answer(league, item, 2) is None
    assert sum(p.points for p in league.players.values()) == 0 and league.todo == []


def test_a_candidate_who_cannot_take_the_point_any_more_is_not_offered():
    league, item = extra_work_league()
    first, second = (league.players[pid] for pid in item["players"])
    first.points = T.FR_EXTRA_WORK_POINTS
    assert todo.valid_players(league, item) == [second] and todo.answer_count(league, item) == 2
    assert todo.apply_answer(league, item, 0) is second
    league2, item2 = extra_work_league()
    league2.players[item2["players"][0]].team = TEAM + 1             # traded away
    assert [p.id for p in todo.valid_players(league2, item2)] == [item2["players"][1]]


def test_later_keeps_the_item_on_the_list_and_it_stays_waiting():
    league, item = extra_work_league()
    todo.put_off(item)
    assert item["state"] == D.ITEM_LATER and todo.waiting(league) == [item] and todo.waiting(league, include_later=False) == []
    assert sum(p.points for p in league.players.values()) == 0


def test_the_kick_off_closes_what_is_waiting_without_a_point_and_keeps_a_game_plan_that_was_set():
    league, item = extra_work_league()
    plan = todo.game_plan_item(league, 2, "air", "zone", "pro", "classic", STYLE_KEYS)
    league.todo.append(plan)
    todo.apply_answer(league, plan, 0)
    todo.put_off(item)
    assert todo.close_unanswered(league) == 1
    assert league.todo == [plan] and plan["state"] == D.ITEM_SET
    assert sum(p.points for p in league.players.values()) == 0


def test_a_new_weeks_list_replaces_the_old_one():
    league, item = extra_work_league()
    todo.drop_old(league, 2)
    assert league.todo == [item]
    todo.drop_old(league, 3)
    assert league.todo == []
    league2, item2 = extra_work_league()
    league2.season = 2
    todo.drop_old(league2, 2)                                        # the same week of another season
    assert league2.todo == []


# ----- the game plan -----

def test_no_game_plan_item_when_both_playbooks_are_classic_or_in_the_play_offs():
    league = a_league()
    assert todo.game_plan_item(league, 3, "air", "zone", "classic", "classic", STYLE_KEYS) is None
    assert todo.game_plan_item(league, 17, "air", "zone", "pro", "pro", STYLE_KEYS) is None
    assert todo.game_plan_item(league, 0, "air", "zone", "pro", "pro", STYLE_KEYS) is None
    assert todo.game_plan_item(league, 16, "air", "zone", "pro", "classic", STYLE_KEYS) is not None


def test_the_staff_recommends_by_the_frozen_table_for_each_side_the_player_plays_a_playbook_on():
    league = a_league()
    item = todo.game_plan_item(league, 3, "pressure", "option", "team", "pro", STYLE_KEYS)
    assert item["kind"] == D.TODO_GAME_PLAN and item["state"] == D.ITEM_NEW
    assert item["styles"] == ["pressure", "option", T.FR_GAME_PLAN["offense"]["option"], T.FR_GAME_PLAN["defense"]["pressure"]]
    only_offense = todo.game_plan_item(league, 3, "pressure", "option", "pro", "classic", STYLE_KEYS)
    assert only_offense["styles"][3] == "classic"                    # a side the player keeps Classic stays Classic
    only_defense = todo.game_plan_item(league, 3, "pressure", "option", "classic", "air", STYLE_KEYS)
    assert only_defense["styles"][2] == "classic" and only_defense["styles"][3] == T.FR_GAME_PLAN["defense"]["pressure"]


def test_each_side_reads_the_opponents_other_side_in_the_table(monkeypatch):
    # the frozen table is West Coast on offense against everything, so a table with distinct answers shows which key each side reads
    monkeypatch.setattr(T, "FR_GAME_PLAN", {"offense": {"classic": "air", "zone": "power", "option": "zone"},
                                            "defense": {"classic": "pro", "zone": "west", "option": "air"}})
    league = a_league()
    item = todo.game_plan_item(league, 3, "zone", "option", "pro", "pro", STYLE_KEYS)
    assert item["styles"] == ["zone", "option", "zone", "west"]            # our offense by their defense, our defense by their offense


def test_a_style_the_game_does_not_have_falls_back_to_classic_and_an_opponent_that_plays_classic_has_a_plan():
    league = a_league()
    item = todo.game_plan_item(league, 3, "classic", "classic", "pro", "pro", {"pro"})
    assert item["styles"][2:] == ["classic", "classic"]              # west and power are not in the set
    full = todo.game_plan_item(league, 3, "classic", "classic", "pro", "pro", STYLE_KEYS)
    assert full["styles"][2:] == [T.FR_GAME_PLAN["offense"]["classic"], T.FR_GAME_PLAN["defense"]["classic"]]


def test_the_frozen_plan_names_a_style_or_classic_for_every_opponent_style():
    keys = {"classic"} | STYLE_KEYS
    for side in ("offense", "defense"):
        assert set(T.FR_GAME_PLAN[side]) == keys
        assert set(T.FR_GAME_PLAN[side].values()) <= STYLE_KEYS


def test_the_frozen_plan_is_what_the_script_with_the_yardstick_works_out():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "work", "make_game_plan_sx8e.py")
    if not os.path.exists(path):
        pytest.skip("the script is not here")
    spec = importlib.util.spec_from_file_location("make_game_plan_sx8e", path)
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    for opponent in ["classic"] + script.STYLES:
        offense = {s: script.offense_value(s, opponent) for s in script.STYLES}
        defense = {s: script.defense_allowed(s, opponent) for s in script.STYLES}
        assert script.best(offense, True) == T.FR_GAME_PLAN["offense"][opponent], opponent
        assert script.best(defense, False) == T.FR_GAME_PLAN["defense"][opponent], opponent


def test_the_plan_is_taken_for_this_weeks_game_only():
    league = a_league()
    item = todo.game_plan_item(league, 3, "air", "zone", "pro", "pro", STYLE_KEYS)
    league.todo.append(item)
    assert todo.plan_of(league, 3) is None                           # not taken yet
    assert todo.apply_answer(league, item, 0) is None
    assert item["state"] == D.ITEM_SET and todo.plan_of(league, 3) == (item["styles"][2], item["styles"][3])
    assert todo.plan_of(league, 4) is None
    league.season = 2
    assert todo.plan_of(league, 3) is None


def test_keeping_your_playbooks_removes_the_game_plan_item():
    league = a_league()
    item = todo.game_plan_item(league, 3, "air", "zone", "pro", "pro", STYLE_KEYS)
    league.todo.append(item)
    assert todo.answer_count(league, item) == 2 and todo.is_do_nothing(league, item, 1)
    todo.apply_answer(league, item, 1)
    assert league.todo == [] and todo.plan_of(league, 3) is None


# ----- the check of the list in league.sav -----

def good_items():
    league, extra = extra_work_league()
    plan = todo.game_plan_item(league, 2, "air", "zone", "pro", "pro", STYLE_KEYS)
    league.todo.append(plan)
    return league, extra, plan


def test_a_list_of_well_formed_items_passes_the_check_and_the_league_round_trips_with_it():
    league, extra, plan = good_items()
    todo.check_items(league, whole)
    from nfl4.extras.franchise.league import LeagueRecord
    again = LeagueRecord.from_json(league.to_json())
    assert again.todo == league.todo


@pytest.mark.parametrize("change", [
    lambda item: item.update(kind="contract"), lambda item: item.update(week=0), lambda item: item.update(week=19),
    lambda item: item.update(season=0), lambda item: item.update(state=3), lambda item: item.update(state=True),
    lambda item: item.update(extra=1), lambda item: item.pop("week"), lambda item: item.update(players=[]),
    lambda item: item.update(players=[1, 2, 3]), lambda item: item.update(players=["a"]), lambda item: item.update(state=D.ITEM_SET),
    lambda item: item.update(players=[item["players"][0], item["players"][0]]),
])
def test_a_damaged_extra_work_item_is_refused(change):
    league, extra, plan = good_items()
    change(extra)
    with pytest.raises(LeagueError):
        todo.check_items(league, whole)


@pytest.mark.parametrize("change", [
    lambda item: item.update(styles=["air", "zone", "west"]), lambda item: item.update(styles=["air", "zone", "west", "nothing"]),
    lambda item: item.update(styles=["air", "zone", "west", 7]), lambda item: item.update(styles="airzonewestpower"),
    lambda item: item.pop("styles"), lambda item: item.update(players=[1]),
])
def test_a_damaged_game_plan_item_is_refused(change):
    league, extra, plan = good_items()
    change(plan)
    with pytest.raises(LeagueError):
        todo.check_items(league, whole)


def test_two_items_of_one_kind_in_one_week_and_a_list_that_is_not_a_list_are_refused():
    league, extra, plan = good_items()
    league.todo.append(dict(extra))
    with pytest.raises(LeagueError):
        todo.check_items(league, whole)
    league.todo = {"kind": "extra_work"}
    with pytest.raises(LeagueError):
        todo.check_items(league, whole)
    league.todo = [extra] * 0 + ["extra"]
    with pytest.raises(LeagueError):
        todo.check_items(league, whole)


def test_every_book_key_of_the_game_is_a_valid_style_in_an_item():
    league, extra, plan = good_items()
    for key in BOOK_KEYS:
        plan["styles"] = [key, key, key, key]
        todo.check_items(league, whole)
