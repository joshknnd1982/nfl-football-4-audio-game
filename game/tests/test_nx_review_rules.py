"""The ruling model, the booth's reviews and the coaches' challenges, their rules as plain functions (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 6.1, 6.2, 6.4; NFL_RULES_RESEARCH Part 3; PX SX.6). This is inspired by Jim Kitchen.

Every expected number is worked out from the rule or the design next to it, never from a run of the code (B-X38): the
distances to the goal line from the spot, the windows of the draw from the rates of design 6.1, the challenges a team may
still throw from 15-1-1 (f). The flows through the engine are in tests/test_nx_review_plays.py.
"""
import json

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import review as RV
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.state import ExtrasRecord
from nfl4.extras.timeouts import Situation, challenge_possible, challenges_left
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.gamestate import GameState, SideStats
from nfl4.game.playtables import PASSES, RUNS
from nflrig import nfl_engine_rig
from pagrig import Draws
from randsources import ScriptedRandom

TD, FUMBLE, RUN, COMPLETE, INCOMPLETE = O.TOUCHDOWN, O.FUMBLE, O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE


def outcome(kind=RUN, yards=0, offense=1, offense_play=1, defense_play=3, spot=(2, 30), qb_run="", two_point=False):
    return O.PlayOutcome(kind, offense, offense_play, defense_play, yards=yards, spot_before=spot, qb_run=qb_run,
                         two_point_try=two_point)


def state_of(down=3, to_go=5, result_kind=RUN, tackle_sentence=" tackle string ", quarter=1, offense=1):
    s = GameState(wisoff=offense, defense=3 - offense, down=down, to_go=to_go, quarter=quarter)
    s.result_kind, s.tackle_sentence = result_kind, tackle_sentence
    return s


def cats(found):
    return [(c.category, c.ruled, c.corrected, c.against, c.how) for c in found]


# ----- the distance to the goal line -----

@pytest.mark.parametrize("offense, spot, distance", [(1, (2, 30), 70), (1, (1, 5), 5), (2, (1, 30), 70), (2, (2, 8), 8),
                                                     (1, (2, 50), 50), (1, (1, 50), 50)])
def test_the_distance_to_the_goal_line_from_the_spot_of_the_snap(offense, spot, distance):
    """Side 1 defends half 2 and attacks half 1 (and the other way round): the yard line is the distance to the goal line of
    the half the ball is in, so on the offense's own half the goal line it attacks is 100 minus that."""
    assert RV.goal_distance(outcome(offense=offense, spot=spot)) == distance


# ----- which aspects a play has (design 6.1) -----

def test_a_run_one_yard_short_of_the_line_to_gain_may_have_been_a_first_down_and_the_call_went_against_the_offense():
    found = RV.candidates(state_of(down=3, to_go=5), outcome(RUN, yards=4), ExtrasRecord())
    assert cats(found) == [("line", RV.SHORT_OF_LINE, RV.MADE_THE_LINE, 1, "line_made"),
                           ("down", RV.DOWN_BEFORE, RV.FUMBLED, 2, "fumble")]


@pytest.mark.parametrize("yards", [5, 6])
def test_a_first_down_by_at_most_one_yard_may_have_been_short_and_the_call_went_against_the_defense(yards):
    found = RV.candidates(state_of(down=3, to_go=5), outcome(RUN, yards=yards), ExtrasRecord())
    assert cats(found)[0] == ("line", RV.MADE_THE_LINE, RV.SHORT_OF_LINE, 2, "line_short")


@pytest.mark.parametrize("yards", [3, 7, 20, -2])
def test_a_play_farther_than_a_yard_from_the_line_to_gain_has_no_line_aspect(yards):
    found = RV.candidates(state_of(down=3, to_go=5), outcome(RUN, yards=yards), ExtrasRecord())
    assert [c.category for c in found] == ["down"]


def test_goal_to_go_the_line_to_gain_is_the_goal_line_so_there_is_no_line_aspect():
    """d = 5 from the 5, 5 to go: the first down line is the goal line (15-3-7 has nothing to measure)."""
    s = state_of(down=3, to_go=5)
    assert [c.category for c in RV.candidates(s, outcome(RUN, yards=4, spot=(1, 5)), ExtrasRecord())] == ["goal", "down"]


@pytest.mark.parametrize("yards, goal", [(4, True), (3, True), (2, False), (0, False)])
def test_a_run_that_ends_within_two_yards_of_the_goal_line_may_have_crossed_it(yards, goal):
    """d = 5: a run of 4 ends 1 short, of 3 ends 2 short (GOAL_REACH 2), of 2 ends 3 short."""
    found = RV.candidates(state_of(down=2, to_go=5), outcome(RUN, yards=yards, spot=(1, 5)), ExtrasRecord())
    assert ("goal" in [c.category for c in found]) is goal
    if goal:
        assert cats(found)[0] == ("goal", RV.SHORT_OF_GOAL, RV.CROSSED_GOAL, 1, "touchdown")


@pytest.mark.parametrize("yards, goal", [(5, True), (6, True), (7, True), (8, False), (30, False)])
def test_a_touchdown_by_at_most_two_yards_may_have_been_short_and_the_call_went_against_the_defense(yards, goal):
    s = state_of(down=1, to_go=5, result_kind=RUN)
    found = RV.candidates(s, outcome(TD, yards=yards, spot=(1, 5)), ExtrasRecord())
    assert cats(found) == ([("goal", RV.CROSSED_GOAL, RV.SHORT_OF_GOAL, 2, "short")] if goal else [])


def test_a_touchdown_pass_is_a_goal_line_play_too_and_a_kick_off_return_is_not():
    s = state_of(down=1, to_go=10, result_kind=COMPLETE)
    assert RV.candidates(s, outcome(TD, yards=20, offense_play=4, spot=(1, 20)), ExtrasRecord())[0].category == "goal"
    assert RV.candidates(s, outcome(TD, yards=20, offense_play=0, spot=(1, 20)), ExtrasRecord()) == []


def test_a_fumble_lost_may_have_been_a_runner_down_before_the_fumble_and_the_call_went_against_the_offense():
    found = RV.candidates(state_of(result_kind=RUN), outcome(FUMBLE), ExtrasRecord())
    assert cats(found) == [("fumble", RV.FUMBLED, RV.DOWN_BEFORE, 1, "down")]
    assert RV.candidates(state_of(result_kind=O.SACK), outcome(FUMBLE), ExtrasRecord()) == []     # a sack's fumble: not modeled


def test_a_completion_may_have_been_incomplete_and_an_incompletion_a_catch():
    complete = RV.candidates(state_of(result_kind=COMPLETE), outcome(COMPLETE, yards=12, offense_play=4), ExtrasRecord())
    assert cats(complete)[-1] == ("catch", RV.COMPLETE, RV.INCOMPLETE, 2, "incomplete")
    incomplete = RV.candidates(state_of(result_kind=INCOMPLETE, tackle_sentence=" Rec1 drops the ball "),
                               outcome(INCOMPLETE, offense_play=4), ExtrasRecord())
    assert cats(incomplete) == [("catch", RV.INCOMPLETE, RV.COMPLETE, 1, "complete")]


def test_a_catch_at_the_side_line_is_a_boundary_play_not_a_catch_play():
    out_of_bounds = ExtrasRecord(out_of_bounds=True)
    found = RV.candidates(state_of(result_kind=COMPLETE), outcome(COMPLETE, yards=12, offense_play=4), out_of_bounds)
    assert cats(found)[-1] == ("boundary", RV.IN_BOUNDS, RV.OUT_OF_BOUNDS, 2, "incomplete")
    assert "catch" not in [c.category for c in found]
    sentence = " Rec1" + P.OUT_OF_BOUNDS
    found = RV.candidates(state_of(result_kind=INCOMPLETE, tackle_sentence=sentence), outcome(INCOMPLETE, offense_play=4),
                          ExtrasRecord())
    assert cats(found) == [("boundary", RV.OUT_OF_BOUNDS, RV.IN_BOUNDS, 1, "complete")]


def test_the_aspects_of_a_play_are_in_the_order_of_the_priority_of_design_6_1():
    """The goal line, the line to gain, the fumble, the tackle, the catch, the side line."""
    assert RV.PRIORITY == ("goal", "line", "fumble", "down", "catch", "boundary")
    s = state_of(down=3, to_go=4, result_kind=COMPLETE)           # from the 5: 4 yards end 1 short of the goal line and make the 4
    found = RV.candidates(s, outcome(COMPLETE, yards=4, offense_play=4, spot=(1, 5)), ExtrasRecord())
    assert [c.category for c in found] == ["goal", "line", "down", "catch"]
    s = state_of(down=3, to_go=5, result_kind=COMPLETE)           # goal to go: the line to gain is the goal line
    found = RV.candidates(s, outcome(COMPLETE, yards=4, offense_play=4, spot=(1, 5)), ExtrasRecord())
    assert [c.category for c in found] == ["goal", "down", "catch"]
    s = state_of(down=3, to_go=4, result_kind=COMPLETE)           # in the open field: 4 yards make the 4
    found = RV.candidates(s, outcome(COMPLETE, yards=4, offense_play=4, spot=(2, 30)), ExtrasRecord())
    assert [c.category for c in found] == ["line", "down", "catch"]


@pytest.mark.parametrize("offense_play", [0, 6, 7])
def test_kicks_and_kick_offs_have_no_ruling(offense_play):
    assert RV.candidates(state_of(), outcome(RUN, yards=4, offense_play=offense_play), ExtrasRecord()) == []


@pytest.mark.parametrize("kind", [O.SACK, O.INTERCEPTION, O.SAFETY_KIND, O.PUNT, O.KICKOFF_RETURN, O.FIELD_GOAL_GOOD,
                                  O.FIELD_GOAL_MISSED, O.KICKOFF_TOUCH_BACK, O.ONSIDE_KICK])
def test_only_a_run_a_catch_an_incompletion_a_touchdown_and_a_fumble_have_a_ruling(kind):
    assert RV.candidates(state_of(), outcome(kind, yards=4), ExtrasRecord()) == []


def test_a_two_point_try_has_no_ruling():
    assert RV.candidates(state_of(result_kind=RUN), outcome(TD, yards=2, spot=(1, 2), two_point=True), ExtrasRecord()) == []


def test_the_quarterbacks_runs_have_the_running_aspects_and_a_scramble_is_never_a_catch():
    keeper = RV.candidates(state_of(down=3, to_go=5), outcome(RUN, yards=4, offense_play=9, qb_run="keeper"), ExtrasRecord())
    assert [c.category for c in keeper] == ["line", "down"]
    scramble = RV.candidates(state_of(down=3, to_go=5), outcome(RUN, yards=4, offense_play=4, qb_run="scramble"),
                             ExtrasRecord())
    assert [c.category for c in scramble] == ["line", "down"]


@pytest.mark.parametrize("category, wrong, close", [("catch", 6, 17), ("fumble", 80, 135), ("down", 2, 0), ("goal", 60, 135),
                                                    ("line", 30, 100), ("boundary", 5, 17)])
def test_the_rates_are_design_6_1_per_thousand_with_the_close_rates_of_the_calibration(category, wrong, close):
    """The wrong rates are the design's: 0.6 percent of the passes, 8 percent of the fumbles, 0.2 percent of the runs and the
    catches, 6 percent at the goal line, 3 percent at the line to gain, 0.5 percent at the side line (design 6.1). The close
    rates are the design's 10, 80, 0, 80, 60 and 10 times 1.7 (SX.6 calibration, tuning.py: more rulings that were right but
    close, which is what holds the coaches' reversals at the NFL's 38 to 52 percent)."""
    assert T.RULING_RATES[category] == (wrong, close)
    candidate = RV._make(category, RV.COMPLETE, RV.INCOMPLETE, 2, "incomplete")
    assert (candidate.wrong, candidate.close) == (wrong, close)
    assert T.BOOTH_PLAY_WRONG_FACTOR == 2


# ----- who may challenge (15-1-2) -----

def test_the_replay_official_has_overtime_then_the_plays_after_the_warning_then_scores_turnovers_and_a_failed_fourth_down():
    record = ExtrasRecord()
    s = state_of(down=2, to_go=5)
    assert RV.booth_reason(s, outcome(RUN, yards=4), record) == ""
    assert RV.booth_reason(s, outcome(TD, yards=5), record) == "booth"
    assert RV.booth_reason(s, outcome(FUMBLE), record) == "booth"
    record.warning_given = True
    assert RV.booth_reason(s, outcome(RUN, yards=4), record) == "warning"
    assert RV.booth_reason(state_of(quarter=5), outcome(RUN, yards=4), record) == "overtime"        # overtime before the warning


@pytest.mark.parametrize("kind, yards, reason", [(RUN, 4, "booth"), (INCOMPLETE, 0, "booth"), (COMPLETE, 4, "booth"),
                                                 (RUN, 5, ""), (COMPLETE, 9, ""), (RUN, 6, "")])
def test_a_failed_fourth_down_is_the_replay_officials_and_a_converted_one_a_coachs(kind, yards, reason):
    """Fourth and 5 (15-1-2 (e): the offense failed to reach the line to gain on fourth down)."""
    assert RV.booth_reason(state_of(down=4, to_go=5), outcome(kind, yards=yards), ExtrasRecord()) == reason


# ----- the statistics, the ball, the challenges -----

def test_the_statistics_of_a_result_are_counted_and_taken_back_the_way_the_original_counts_them():
    stats = SideStats()
    RV.tally(stats, "run", True, 7, +1)
    assert (stats.running_plays, stats.running_yards) == (1, 7)
    RV.tally(stats, "complete", False, 12, +1)
    assert (stats.completions, stats.passing_yards) == (1, 12)
    RV.tally(stats, "incomplete", False, 0, +1)                     # the attempt was counted at the throw: nothing here
    assert (stats.completions, stats.passing_yards, stats.pass_attempts) == (1, 12, 0)
    RV.tally(stats, "fumble", True, 0, +1)                          # a fumbled run is not a running play (Q60)
    assert (stats.fumbles_lost, stats.completions, stats.running_plays) == (1, 1, 1)
    RV.tally(stats, "fumble", False, 0, +1)                         # a fumbled catch: the catch was counted before the test
    assert (stats.fumbles_lost, stats.completions) == (2, 2)
    for result, run, yards in (("run", True, 7), ("complete", False, 12), ("fumble", True, 0), ("fumble", False, 0)):
        RV.tally(stats, result, run, yards, -1)
    assert stats == SideStats()


@pytest.mark.parametrize("offense, spot, yards, expected", [(1, (2, 30), 25, (1, 45)), (1, (1, 5), 4, (1, 1)),
                                                            (1, (2, 40), 15, (1, 45)), (2, (1, 30), 25, (2, 45)),
                                                            (2, (2, 8), 5, (2, 3)), (1, (2, 30), -4, (2, 26)),
                                                            (1, (2, 40), 10, (1, 50)), (1, (1, 5), 5, (1, 0))])
def test_the_ball_moves_as_the_original_moves_it(offense, spot, yards, expected):
    assert RV.moved(spot, offense, yards) == expected


@pytest.mark.parametrize("used, won, left", [(0, 0, 2), (1, 0, 1), (2, 0, 0), (1, 1, 2), (2, 1, 1), (3, 1, 0), (2, 2, 1),
                                             (3, 3, 0), (4, 2, 0)])
def test_two_challenges_a_game_a_third_after_a_success_never_a_fourth(used, won, left):
    """15-1-1 (f), the 2024 amendment: at least ONE success earns a third; a team that won both has not earned a fourth."""
    record = ExtrasRecord(challenges_on=True)
    record.chal_used, record.chal_won = [used, 0], [won, 0]
    assert challenges_left(record, 1) == left
    assert challenges_left(record, 2) == 2                           # the other side has its own count


@pytest.mark.parametrize("quarter, warning_given, challenges, kept", [(1, False, 2, True), (3, False, 1, True), (2, False, 2, True),
                                                                      (2, True, 2, False), (4, False, 1, True), (4, True, 2, False),
                                                                      (5, False, 2, False), (1, False, 0, False)])
def test_the_computer_keeps_a_time_out_for_a_challenge_until_the_warning_of_the_half(quarter, warning_given, challenges, kept):
    view = Situation(1, quarter, 600, 0, False, True, 0, 1, warning_given, True, 30, 1, challenges)
    assert challenge_possible(view) is kept


# ----- the board a reversal goes back to -----

def test_the_board_is_put_back_field_by_field_with_the_statistics_and_the_quarterback_counts():
    s = state_of(down=2, to_go=6)
    s.extras = ExtrasRecord(qb_on=True)
    s.extras.qb_runs, s.extras.qb_yards = [1, 0], [5, 0]
    s.stats[1].running_yards = 40
    board = RV.capture(s)
    s.down, s.to_go, s.yard_line, s.half, s.wisoff, s.counter = 3, 1, 41, 1, 2, 9
    s.stats[1].running_yards = 99
    s.extras.qb_runs, s.extras.qb_yards = [2, 0], [9, 0]
    RV.restore(s, board)
    assert (s.down, s.to_go, s.wisoff, s.counter) == (2, 6, 1, 1)
    assert s.stats[1].running_yards == 40
    assert (s.extras.qb_runs, s.extras.qb_yards) == ([1, 0], [5, 0])
    board.stats[1].running_yards = 7                                  # the board keeps its own copy: restoring twice is the same
    s.stats[1].running_yards = 99
    RV.restore(s, board)
    assert s.stats[1].running_yards == 7


# ----- the truth of a wrong ruling (one draw for its yards at most) -----

def rules_rig(tmp_path):
    rules = NflRules(timeouts_on=False, challenges_on=True)
    rig = nfl_engine_rig(tmp_path, rules=rules, wisoff=1, defense=2, half=2, yard_line=30, down=2, to_go=5)
    return rig, rules


def truth(rig, rules, how, outcome_, draws=None, **state):
    for name, value in state.items():
        setattr(rig.engine.s, name, value)
    source = ScriptedRandom((draws or Draws()).values, strict=True)
    rig.rnd.source = source
    rig.rnd.trace = []
    candidate = RV.Candidate("catch", RV.COMPLETE, RV.INCOMPLETE, 2, how, 0, 0)
    result = rules.review.make_truth(candidate, rig.engine.s, outcome_)
    assert rig.rnd.trace == (draws or Draws()).sizes and source.left == 0
    return result


@pytest.mark.parametrize("how, kind, yards, expected", [("short", RUN, 5, ("field", RUN, 4)),
                                                        ("touchdown", RUN, 3, ("touchdown", RUN, 5)),
                                                        ("line_short", RUN, 6, ("field", RUN, 4)),
                                                        ("line_made", RUN, 4, ("field", RUN, 5)),
                                                        ("fumble", RUN, 4, ("fumble", RUN, 0)),
                                                        ("incomplete", COMPLETE, 12, ("field", INCOMPLETE, 0))])
def test_a_truth_without_a_draw(tmp_path, how, kind, yards, expected):
    """From the 25 yard line of the other half (d = 25 - 20 = 5 in the first two rows) with 5 to go: a touchdown was 5 yards,
    a ball short of the goal line 4, a first down 5 and one short of it 4 (design 6.1)."""
    rig, rules = rules_rig(tmp_path)
    spot = (1, 5) if how in ("short", "touchdown") else (2, 30)
    play = outcome(kind, yards=yards, offense_play=1 if kind == RUN else 4, spot=spot)
    got = truth(rig, rules, how, play, to_go=5)
    assert (got.kind, got.result_kind, got.yards) == expected


def test_a_pass_complete_truth_for_an_incompletion_draws_the_yards_of_the_plays_own_row(tmp_path):
    """Short Pass against Short Pass (4, 5): 1 to 9 yards (PassEntry(1, 10, ...): Int(Rnd * 9) + 1); the draw 6 gives 7."""
    assert PASSES[(4, 5)].low == 1 and PASSES[(4, 5)].high == 10
    rig, rules = rules_rig(tmp_path)
    play = outcome(INCOMPLETE, offense_play=4, defense_play=5, spot=(2, 30))
    got = truth(rig, rules, "complete", play, Draws().below(9, 6))
    assert (got.kind, got.result_kind, got.yards) == ("field", COMPLETE, 7)


def test_a_runner_who_was_down_before_the_fumble_gains_the_yards_of_the_runs_row(tmp_path):
    """Line Plunge against Short Run (1, 2): -1 to 4 (RunEntry(-1, 5)): Int(Rnd * 6) - 1; the draw 4 gives 3."""
    assert (RUNS[(1, 2)].low, RUNS[(1, 2)].high) == (-1, 5)
    rig, rules = rules_rig(tmp_path)
    play = outcome(FUMBLE, offense_play=1, defense_play=2, spot=(2, 30))
    got = truth(rig, rules, "down", play, Draws().below(6, 4), result_kind=RUN)
    assert (got.kind, got.result_kind, got.yards) == ("field", RUN, 3)


def test_the_truth_that_reaches_the_goal_line_is_a_touchdown(tmp_path):
    rig, rules = rules_rig(tmp_path)
    play = outcome(INCOMPLETE, offense_play=4, defense_play=5, spot=(1, 7))            # 7 from the goal line
    got = truth(rig, rules, "complete", play, Draws().below(9, 8))                    # 8 + 1 = 9 yards
    assert (got.kind, got.result_kind, got.yards) == ("touchdown", COMPLETE, 9)
    got = truth(rig, rules, "complete", play, Draws().below(9, 5))                    # 6 yards: still 1 short
    assert (got.kind, got.yards) == ("field", 6)


def test_the_truth_never_puts_the_ball_in_the_own_end_zone(tmp_path):
    """Line Plunge against the Goal Line call: -3 to 1; from the 2 yard line a loss of 3 would be a safety: it stops at the 1."""
    assert (RUNS[(1, 1)].low, RUNS[(1, 1)].high) == (-3, 2)
    rig, rules = rules_rig(tmp_path)
    play = outcome(FUMBLE, offense_play=1, defense_play=1, spot=(2, 2))               # own 2: d = 98
    got = truth(rig, rules, "down", play, Draws().below(5, 0), result_kind=RUN)
    assert (got.kind, got.yards) == ("field", -1)                                      # 1 - 2 = -1: the ball is on the 1


# ----- the record, the texts -----

def test_the_record_keeps_the_challenges_through_json_and_an_old_record_has_none():
    record = ExtrasRecord(challenges_on=True)
    record.chal_used, record.chal_won = [2, 1], [1, 0]
    again = ExtrasRecord.from_json(record.to_json())
    assert (again.challenges_on, again.chal_used, again.chal_won) == (True, [2, 1], [1, 0])
    data = json.loads(record.to_json())
    for name in ("challenges_on", "chal_used", "chal_won"):
        del data[name]
    old = ExtrasRecord.from_json(json.dumps(data))
    assert (old.challenges_on, old.chal_used, old.chal_won) == (False, [0, 0], [0, 0])


@pytest.mark.parametrize("name, value", [("chal_used", [4, 0]), ("chal_used", [-1, 0]), ("chal_used", [1]),
                                         ("chal_won", [2, 0]),             # more won than thrown
                                         ("challenges_on", "yes")])
def test_a_damaged_challenge_record_is_refused_whole(name, value):
    data = json.loads(ExtrasRecord().to_json())
    data[name] = value
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(json.dumps(data))


def test_the_ten_rulings_the_player_hears_and_the_sentences_around_them():
    pieces = [X.text("NXR-R%02d" % n) for n in range(1, 11)]
    assert pieces == ["the pass was incomplete", "the pass was complete", "the runner was down before the fumble",
                      "the ball was fumbled", "the runner was short of the goal line", "the runner crossed the goal line",
                      "the runner was short of the first down", "the runner made the first down",
                      "the receiver was out of bounds", "the receiver was in bounds"]
    assert (RV.INCOMPLETE, RV.COMPLETE, RV.DOWN_BEFORE, RV.FUMBLED) == tuple("NXR-R%02d" % n for n in (1, 2, 3, 4))
    assert X.text("NXR-16", ruling=pieces[1]) == " the pass was complete. "
    assert X.text("NXR-01", coach="Kim", ruling=pieces[8]) == " Kim do you wish to challenge the ruling that the receiver was out of bounds? "
    assert X.text("NXR-03", team="Jets", ruling=pieces[7]) == (
        " the Jets have thrown the red flag. they are challenging the ruling that the runner made the first down. ")
    assert X.text("NXR-02", n=2, m=3) == " you have 2 challenges and 3 time outs left. a time out is lost if the ruling stands. "
    assert X.text("NXR-17", m=3) == " you have 1 challenge and 3 time outs left. a time out is lost if the ruling stands. "
    assert X.text("NXR-18", n=2) == " you have 2 challenges and 1 time out left. a time out is lost if the ruling stands. "
    assert X.text("NXR-19") == " you have 1 challenge and 1 time out left. a time out is lost if the ruling stands. "
    for text_id in ("NXR-04", "NXR-05", "NXR-06", "NXR-07", "NXR-08", "NXR-09", "NXR-10", "NXR-11", "NXR-12", "NXR-13",
                    "NXR-14", "NXR-15"):
        assert X.TEXTS[text_id].startswith(" ") and X.TEXTS[text_id].endswith(". ")
    assert set(RV.REASON_TEXTS.values()) == {"NXR-10", "NXR-11", "NXR-12", "NXR-13", "NXR-14", "NXR-15"}


def test_the_lines_of_the_four_replay_pools_are_the_defaults_of_strings_nx():
    assert [list(X.REMARK_POOLS[p]) for p in ("CHS", "CHC", "RVR", "RVC")] == [
        ["CHS01", "CHS02", "CHS03", "CHS04"], ["CHC01", "CHC02", "CHC03"], ["RVR01", "RVR02", "RVR03"],
        ["RVC01", "RVC02", "RVC03"]]
