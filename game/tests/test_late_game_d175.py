"""The late-game calibration (nfl4 only, rule 0.13; D-175, Q-037): the computer's fourth down in the fourth quarter of a game that plays
the catalog (calling.fourth_down_call through hook H25), and its try when a touchdown leaves it one point behind (the kick that ties).
Classic and a side that plays the original's plays keep the original's rule, with its draws. This is inspired by Jim Kitchen."""
import pytest

import nflrig
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import calling as K
from nfl4.game.rules import CLASSIC

MIN = 60


# ----- the coaches' chart (a rule, no draw): concrete cases that must hold whatever the aggregates say (B-P56) -----

@pytest.mark.parametrize("left, lead, to_goal, to_go, call", [
    (2 * MIN, -3, 30, 8, "kick"),          # behind 3 late in reach: the field goal ties
    (30, -1, 2, 2, "kick"),                # behind 1 at the 2 with 30 seconds: the field goal wins
    (2 * MIN, -3, 60, 8, "go"),            # behind 3, out of reach, two minutes: never the punt
    (4 * MIN + 30, -3, 70, 8, "punt"),     # behind 3 with four and a half minutes, deep in its own end, long: the punt
    (4 * MIN + 30, -3, 45, 6, "go"),       # the same from the other half: go
    (MIN, -7, 20, 6, "go"),                # a touchdown is needed: no field goal
    (4 * MIN, -5, 25, 6, "kick"),          # behind 5 with four minutes in reach, long: the kick makes it a 2-point game
    (2 * MIN + 30, -5, 25, 6, "go"),       # the same with two and a half minutes: go
    (3 * MIN, -10, 20, 7, "kick"),         # two scores behind: the kick makes it one score
    (2 * MIN, -14, 20, 7, "go"),           # two touchdowns behind: go
    (7 * MIN, -12, 40, 3, "go"),           # two scores behind in the last eight minutes, the other half: go
    (MIN, 0, 30, 6, "kick"),               # tied late in reach: the kick
    (MIN, 0, 70, 6, "punt"),               # tied late in its own end: the punt
    (3 * MIN, 4, 65, 3, "punt"),           # ahead: the punt
    (3 * MIN, 4, 30, 3, "kick"),           # ahead in reach: the kick
    (10 * MIN, -3, 60, 4, "punt"),         # early in the quarter: the ordinary choice
    (10 * MIN, -3, 45, 1, "go"),           # fourth and 1 in the other half
    (10 * MIN, 0, 2, 1, "go"),             # fourth and goal at the 2, tied: go for the touchdown
    (10 * MIN, 7, 2, 1, "kick"),           # ahead: the sure field goal
])
def test_the_fourth_quarter_chart(left, lead, to_goal, to_go, call):
    assert K.fourth_down_call(left, lead, to_goal, to_go) == call


def test_behind_late_the_computer_never_punts_in_the_last_three_minutes():
    for lead in range(-30, 0):
        for to_goal in range(1, 100):
            for to_go in (1, 5, 15):
                assert K.fourth_down_call(K.ALL_IN_SECONDS, lead, to_goal, to_go) != "punt"


def test_a_field_goal_is_never_tried_beyond_the_reach():
    for left in (900, 400, 250, 100, 10):
        for lead in range(-20, 21):
            for to_goal in range(K.LAST_KICK_REACH + 1, 100):
                assert K.fourth_down_call(left, lead, to_goal, 4) != "kick"


def test_ahead_the_computer_never_goes_for_it_outside_fourth_and_short():
    for left in (900, 400, 250, 100):
        for to_goal in range(1, 100):
            assert K.fourth_down_call(left, 3, to_goal, K.SHORT_GO + 1) != "go"


# ----- the try: one point behind after the touchdown, the kick that ties -----

def test_one_point_behind_after_the_touchdown_the_computer_kicks_to_tie_in_the_fourth_quarter():
    assert -1 not in K.TWO_POINT_CHART and -8 not in K.TWO_POINT_CHART and -2 in K.TWO_POINT_CHART
    assert K.goes_for_two(4, -1, None, left=60) is False         # no draw in the chart's time
    assert K.goes_for_two(4, -8, None, left=300) is False


def test_overtime_keeps_the_charts_two_point_try_one_point_behind():
    """D-175: the coaches' figures are the fourth quarter's; in overtime the kick that ties made too many games end tied (14.0 percent of
    overtime games against the league's 5.9), so the second team one point behind goes for two as SX.12 measured."""
    assert K.TWO_POINT_CHART_OVERTIME == frozenset((-10, -8, -5, -2, -1, 1, 2, 4, 5, 7))
    assert K.goes_for_two(5, -1, None) is True and K.goes_for_two(5, 0, None) is False


# ----- the hook -----

def test_classic_answers_the_hook_none():
    class State:
        quarter, down, wisoff = 4, 4, 2
    assert CLASSIC.late_fourth_down(State()) is None


def quarter_four(tmp_path, books, **fields):
    rig = nflrig.nfl_engine_rig(tmp_path, rules=NflRules(offense_book=books, defense_book=books, playbooks_on=True))
    s = rig.engine.s
    s.wisoff, s.defense, s.quarter, s.down = 2, 1, 4, 4
    for name, value in fields.items():
        setattr(s, name, value)
    rig.rules.books.resolve(rig.game, s)
    return rig, s


def test_a_side_that_plays_the_original_plays_keeps_the_original_rule(tmp_path):
    rig, s = quarter_four(tmp_path, "classic")
    assert rig.rules.late_fourth_down(s) is None                # strict source: no draw


def test_the_computer_behind_late_goes_for_it_from_its_own_half(tmp_path):
    rig, s = quarter_four(tmp_path, "team", half=1, yard_line=30, to_go=8)   # the computer's own 30 (side 2 defends half 1)
    s.extras.left = 100
    s.stats[1].score, s.stats[2].score = 17, 10                  # the computer is 7 behind
    assert rig.rules.late_fourth_down(s) == "go"


def test_whole_games_never_punt_behind_in_the_last_three_minutes(tmp_path):
    """Seeded games, both sides by the computer with their team playbooks: every fourth down of the fourth quarter follows the chart (a
    property of the rule, not of one seed's score)."""
    from nfl4.extras.playbook_data import TEAM_STYLES
    from nfl4.game.pag_kicks26 import to_goal
    seen = []

    class Watched(nflrig.SimEngine):
        def snap(self):
            s = self.s
            if s.quarter == 4 and s.down == 4 and not s.two_point and not self.clock.is_last_play():   # the last play: its own rule
                lead = s.score(s.wisoff) - s.score(3 - s.wisoff)
                seen.append((s.extras.left, lead, to_goal(s), s.to_go, s.offense_play))
            return super().snap()

    real = nflrig.SimEngine
    nflrig.SimEngine = Watched
    try:
        for seed in range(1, 13):
            rules = nflrig.RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
            rules.forced = (TEAM_STYLES[(seed + 5) % 32], TEAM_STYLES[seed % 32])
            nflrig.sim_game(tmp_path / ("g%d" % seed), seed, rules=rules)
    finally:
        nflrig.SimEngine = real
    assert len(seen) > 20
    assert sum(1 for left, lead, *_rest in seen if lead < 0 and left <= K.ALL_IN_SECONDS) >= 3     # the rule was asked late
    for left, lead, goal, to_go, play in seen:
        if lead < 0 and left <= K.ALL_IN_SECONDS:
            assert play != 7, (left, lead, goal, to_go)
        if play == 6:
            assert goal <= K.LAST_KICK_REACH, (left, lead, goal, to_go)


def test_the_engine_kicks_and_punts_on_the_hook_with_no_draw_and_goes_with_the_original_s_draw(tmp_path):
    rig, s = quarter_four(tmp_path, "team", half=2, yard_line=20, to_go=6)   # the player's 20
    s.extras.left = 100
    s.stats[1].score, s.stats[2].score = 10, 7                   # the computer 3 behind: the kick
    rig.rnd.trace = []
    step = rig.engine._fourth_down_rule()
    assert step.__name__ == "snap" and s.offense_play == 6 and rig.rnd.trace == []
    s.stats[1].score = 7                                         # tied, its own 30: the punt
    s.half, s.yard_line = 1, 30
    step = rig.engine._fourth_down_rule()
    assert step.__name__ == "snap" and s.offense_play == 7 and rig.rnd.trace == []
