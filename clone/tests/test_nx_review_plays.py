"""Replay challenges and booth reviews in the play engine: every ruling of design 6.1 reversed, confirmed and left standing, the
player's challenge from the menu, the computer's flag, the refusals, the limits, the clock and the statistics (nfl4 only, rule
0.13; NFL_EXTRAS_DESIGN 6 and 15; PX SX.6). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source (Draws, tests/pagrig.py) in the order of the design as built and every expected
number and text is worked out from the rule next to it, never from a run of the game (B-X38): the window of a draw from the
rates of design 6.1, the yards of a truth from the row of the play, the ball from the spot of the snap, the clock from the live
time. The scenes start at the narration end point of a play that has just been told (the ball moved, the original's statistics
counted), so the hooks run exactly as they do in a game. Penalties are off here (the flagged play is tested through `rule`).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import review as RV
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.rules import REVIEWED_FIELD, REVIEWED_FUMBLE, REVIEWED_TOUCHDOWN
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps, sounds_played
from randsources import ScriptedRandom

TD, FUMBLE, RUN, COMPLETE, INCOMPLETE = O.TOUCHDOWN, O.FUMBLE, O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE
ENTER, UP, DOWN, F1 = 13, 38, 40, 112
START = {"gain_and_end": "gain_and_end", TD: "touchdown_reached", FUMBLE: "reviewed_fumble"}


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def scene(tmp_path, kind, yards=0, spot=(2, 30), offense_play=1, defense_play=3, down=2, to_go=7, quarter=1, comments=False,
          answers=(), extras=None, timeouts_on=False, auto_sides=(2,), sentence=" tackle string ", qb_run="", **state):
    """The engine at the narration end point of a play of side 1 that has just been told: `kind` (RUN, COMPLETE, INCOMPLETE, TD
    or FUMBLE; a TD or FUMBLE is of a run for the plays 1, 2 and 8 to 10 and of a catch for 3 to 5), the ball moved from `spot`,
    the statistics as the narration counted them. Returns (rig, the PlayOutcome record of the play)."""
    rules = NflRules(timeouts_on=timeouts_on, challenges_on=True, auto_sides=auto_sides)
    fields = dict(wisoff=1, defense=2, down=down, to_go=to_go, quarter=quarter, offense_play=offense_play,
                  defense_play=defense_play)
    fields.update(state)
    rig = nfl_engine_rig(tmp_path, answers=answers, comments=comments, rules=rules, extras=extras, **fields)
    rig.game.pause_log = []
    engine, s = rig.engine, rig.engine.s
    engine._spot_before = spot
    run = offense_play <= 2 or offense_play >= 8 or bool(qb_run)
    s.result_kind = (RUN if run else COMPLETE) if kind in (TD, FUMBLE) else kind
    s.play_kind = 1 if run else 2
    s.yards = 0 if kind == FUMBLE else yards
    s.tackle_sentence = sentence
    mine = s.stats[1]
    if not run:
        mine.pass_attempts = 1
    if kind == RUN or (kind == TD and run):
        mine.running_plays, mine.running_yards = 1, yards
    if kind == COMPLETE or (kind == TD and not run) or (kind == FUMBLE and not run):
        mine.completions = 1
        mine.passing_yards = yards if kind != FUMBLE else 0
    if kind == FUMBLE:
        mine.fumbles_lost = 1
        s.fumble_flag = True
        s.text = P.THE_BALL_IS_NOW
        s.half, s.yard_line = spot
    else:
        s.half, s.yard_line = RV.moved(spot, 1, yards)
    record = O.PlayOutcome(kind, 1, offense_play, defense_play, yards=s.yards, spot_before=spot, qb_run=qb_run)
    return rig, record


def feed(rig, draws: Draws) -> None:
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []


def used_up(rig, draws: Draws) -> None:
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert rig.rnd.source.left == 0


def rule(rig, record, draws: Draws, flags=()):
    """review.rule at the end point (what NflRules.after_outcome calls, after the live time and the fouls), with exactly these
    draws. The clock is as it was before the live time (`left_before`)."""
    s = rig.engine.s
    board = RV.capture(s)
    feed(rig, draws)
    then = rig.rules.review.rule(s, record, board, s.extras.left, list(flags))
    used_up(rig, draws)
    return then


def pending(rig):
    return rig.rules.review.pending


def throw(rig, draws: Draws, side=1):
    """A challenge thrown without the menu: the review, the cost, the reversal."""
    feed(rig, draws)
    then = rig.rules.review.throw(rig.engine.s, side, pending(rig))
    used_up(rig, draws)
    return then


# ----- the draw: the windows of design 6.1 -----

@pytest.mark.parametrize("value, what, category, ruled", [
    (0, "wrong", "line", RV.SHORT_OF_LINE), (29, "wrong", "line", RV.SHORT_OF_LINE),
    (30, "wrong", "down", RV.DOWN_BEFORE), (31, "wrong", "down", RV.DOWN_BEFORE),
    (32, "close", "line", RV.SHORT_OF_LINE), (131, "close", "line", RV.SHORT_OF_LINE),
    (132, "plain", "line", RV.SHORT_OF_LINE), (999, "plain", "line", RV.SHORT_OF_LINE)])
def test_the_windows_of_the_draw_are_the_wrong_rates_first_then_the_close_ones(tmp_path, value, what, category, ruled):
    """A run from the 30 that ends 1 yard short of the line (third and 5, 4 yards) has two aspects, the line to gain (wrong 30,
    close 100 per 1000) and the tackle (wrong 2, close 0). The wrong windows are 0 to 29 (line) and 30 to 31 (tackle), the close
    ones 32 to 131 (the line; the tackle's is empty), anything from 132 on is a plain ruling (design 6.1, calibrated close rate)."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5)
    d = Draws().below(1000, value)
    if what == "wrong":
        d.below(100, 99).below(100, 99)                              # not clear and obvious, no hint heard
    elif what == "close":
        d.below(100, 99)                                             # no hint heard
    assert rule(rig, record, d) is None                              # a coach's play: nothing happens until a flag
    ruling = pending(rig)
    assert (ruling.primary.category, ruling.primary.ruled) == (category, ruled)
    assert (ruling.wrong, ruling.close) == (what == "wrong", what == "close")
    assert (ruling.truth is not None) is (what == "wrong") and ruling.clear is False and ruling.hint == ""


def test_a_close_ruling_is_right_and_is_not_reversed_and_a_plain_one_has_nothing_to_hint(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5)
    assert rule(rig, record, Draws().below(1000, 40).below(100, 10)) is None      # close (32 to 91), the hint 10 < 50
    ruling = pending(rig)
    assert (ruling.close, ruling.wrong, ruling.hint, ruling.truth) == (True, False, "close", None)
    rig, record = scene(tmp_path / "plain", RUN, yards=4, down=3, to_go=5)
    assert rule(rig, record, Draws().below(1000, 500)) is None                    # plain: no more draws
    ruling = pending(rig)
    assert (ruling.close, ruling.wrong, ruling.hint) == (False, False, "")


def test_a_play_with_nothing_to_review_draws_nothing_and_leaves_no_ruling(tmp_path):
    rig, record = scene(tmp_path, O.SACK, yards=-6)
    assert rule(rig, record, Draws()) is None and pending(rig) is None
    rig, record = scene(tmp_path / "two", RUN, yards=4, down=3, to_go=5)
    record.two_point_try = True
    assert rule(rig, record, Draws()) is None and pending(rig) is None


def test_the_hint_chance_is_70_after_a_wrong_ruling_and_50_after_a_close_one(tmp_path):
    for value, hint in ((69, "strong"), (70, "")):
        rig, record = scene(tmp_path / ("w%d" % value), RUN, yards=4, down=3, to_go=5)
        rule(rig, record, Draws().below(1000, 5).below(100, 0).below(100, value))
        assert pending(rig).hint == hint
    for value, hint in ((49, "close"), (50, "")):
        rig, record = scene(tmp_path / ("c%d" % value), RUN, yards=4, down=3, to_go=5)
        rule(rig, record, Draws().below(1000, 50).below(100, value))
        assert pending(rig).hint == hint


def test_a_wrong_ruling_is_clear_and_obvious_with_85_percent(tmp_path):
    for value, clear in ((84, True), (85, False)):
        rig, record = scene(tmp_path / ("c%d" % value), RUN, yards=4, down=3, to_go=5)
        rule(rig, record, Draws().below(1000, 5).below(100, value).below(100, 99))
        assert pending(rig).clear is clear


def test_the_hint_is_a_remark_of_pool_chs_or_chc_when_the_comments_are_on_and_silent_with_f8(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, comments=True)
    rule(rig, record, Draws().below(1000, 5).below(100, 0).below(100, 0).rnd(4, 3))        # CHS03
    assert texts(rig) == [" the replay on the big screen does not agree with that call. "]
    assert rig.engine.s.extras.recent == {"CHS": ["CHS03"]}
    rig, record = scene(tmp_path / "close", RUN, yards=4, down=3, to_go=5, comments=True)
    rule(rig, record, Draws().below(1000, 50).below(100, 0).rnd(3, 2))                     # CHC02, no booth for a coach's play
    assert texts(rig) == [" Ghip, that could have gone either way. "]
    rig, record = scene(tmp_path / "off", RUN, yards=4, down=3, to_go=5, comments=False)  # F8: nothing said, the hint still exists
    rule(rig, record, Draws().below(1000, 5).below(100, 0).below(100, 0))
    assert texts(rig) == [] and pending(rig).hint == "strong"


# ----- every wrong ruling reversed: the truth, the ball, the statistics, the next step -----

def reversed_scene(tmp_path, kind, value, truth_draws=None, booth=True, **kwargs):
    """A wrong ruling hit by `value` that the replay shows clearly, reviewed by the replay official (a booth play) or thrown by
    the player's flag (a coach's play). Returns (rig, the step that applies the corrected result)."""
    rig, record = scene(tmp_path, kind, **kwargs)
    d = Draws().below(1000, value)
    for item in (truth_draws.items if truth_draws is not None else []):
        d.items.append(item)
    d.below(100, 0).below(100, 99)                                                # clear, no hint
    if booth:
        then = rule(rig, record, d.rady().rady())                                 # the replay official's two pauses
    else:
        assert rule(rig, record, d) is None
        then = throw(rig, Draws().rady().rady())
    return rig, then


def test_a_touchdown_that_was_short_of_the_goal_line_is_a_run_to_the_one(tmp_path):
    """First and 5 from the 5: the run of 5 reached the goal line as ruled; the truth is 4 yards, the ball on the 1."""
    rig, then = reversed_scene(tmp_path, TD, 10, yards=5, spot=(1, 5), down=1, to_go=5)
    s, x = rig.engine.s, rig.engine.s.extras
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.half, s.yard_line, s.down, s.to_go) == (4, RUN, 1, 1, 1, 5)
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 4)
    assert rig.rules.review.replaying is True and pending(rig) is None and x.left == 900     # no live time was charged yet
    assert texts(rig) == [" the replay official has stopped the game to review the play. ",
                          " the referee is going under the hood to look at the play. ",
                          " after further review, the ruling on the field is reversed. ",
                          " the runner was short of the goal line. "]
    assert "foot11" in sounds_played(rig)                                                   # the referee's whistle


def test_a_run_short_of_the_goal_line_that_crossed_it_is_a_touchdown(tmp_path):
    """From the 5 a run of 4 ended on the 1: 4 plus 1 is the 5 yards to the goal line, so the truth is a touchdown of 5."""
    rig, then = reversed_scene(tmp_path, RUN, 10, booth=False, yards=4, spot=(1, 5), down=2, to_go=5)
    s = rig.engine.s
    assert then == REVIEWED_TOUCHDOWN
    assert (s.yards, s.result_kind, s.half, s.yard_line) == (5, RUN, 1, 0)
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 5)
    assert texts(rig)[-2:] == [" after further review, the ruling on the field is reversed. ", " the runner crossed the goal line. "]


def test_a_first_down_that_was_one_yard_short_is_a_run_one_yard_less(tmp_path):
    """Third and 5, a run of 5 ruled a first down: the line to gain window is 0 to 29; the truth is 4 yards (15-3-7)."""
    rig, then = reversed_scene(tmp_path, RUN, 10, booth=False, yards=5, down=3, to_go=5)
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.half, s.yard_line, s.down, s.to_go) == (4, RUN, 2, 34, 3, 5)
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 4)
    assert texts(rig)[-1] == " the runner was short of the first down. "


def test_a_run_short_of_the_line_that_made_it_is_a_run_one_yard_more(tmp_path):
    rig, then = reversed_scene(tmp_path, RUN, 10, booth=False, yards=4, down=3, to_go=5)
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.half, s.yard_line) == (5, 2, 35)
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 5)
    assert texts(rig)[-1] == " the runner made the first down. "


def test_a_failed_fourth_down_is_the_booths_and_its_reversal_gives_the_first_down_back(tmp_path):
    """Fourth and 5, a catch of 4 (a turnover on downs as ruled): the replay official reviews it (15-1-2 (e)), the window of the
    line to gain is 0 to 29 and the truth is a catch of 5."""
    rig, then = reversed_scene(tmp_path, COMPLETE, 10, yards=4, offense_play=4, defense_play=5, down=4, to_go=5)
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.stats[1].completions, s.stats[1].passing_yards) == (5, COMPLETE, 1, 5)
    assert texts(rig)[0] == " the replay official has stopped the game to review the play. "


def test_a_fumble_lost_that_was_a_runner_down_before_it_is_a_run_with_the_yards_of_the_plays_row(tmp_path):
    """Line Plunge against Long Run (1, 3): 0 to 6 yards (RunEntry(0, 7)); the draw 4 gives 4; the ball is on the 34."""
    rig, then = reversed_scene(tmp_path, FUMBLE, 10, truth_draws=Draws().below(7, 4), booth=True, spot=(2, 30), down=2,
                               to_go=7)
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.half, s.yard_line, s.fumble_flag) == (4, RUN, 2, 34, False)
    assert (s.stats[1].fumbles_lost, s.stats[1].running_plays, s.stats[1].running_yards) == (0, 1, 4)
    assert texts(rig)[-1] == " the runner was down before the fumble. "


def test_a_catch_fumbled_and_ruled_lost_keeps_the_catch_when_the_runner_was_down(tmp_path):
    """Short Pass against Long Run (4, 3): 5 to 14 yards (PassEntry(5, 15)); the draw 2 gives 7."""
    rig, then = reversed_scene(tmp_path, FUMBLE, 10, truth_draws=Draws().below(10, 2), offense_play=4, defense_play=3)
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.fumble_flag) == (7, COMPLETE, False)
    assert (s.stats[1].fumbles_lost, s.stats[1].completions, s.stats[1].passing_yards) == (0, 1, 7)


def test_a_tackle_that_was_a_fumble_turns_the_ball_over_and_is_not_a_run(tmp_path):
    """A run of 4 from the 30 ruled down: the tackle window is 30 to 31 behind the line aspect's 0 to 29 (third and 5, 4 yards
    gives both); the truth is a fumble lost at the spot of the snap."""
    rig, then = reversed_scene(tmp_path, RUN, 31, booth=False, yards=4, down=3, to_go=5)
    s = rig.engine.s
    assert then == REVIEWED_FUMBLE
    assert (s.yards, s.fumble_flag, s.half, s.yard_line) == (0, True, 2, 30)
    assert (s.stats[1].fumbles_lost, s.stats[1].running_plays, s.stats[1].running_yards) == (1, 0, 0)
    assert texts(rig)[-1] == " the ball was fumbled. "


def test_a_completion_that_was_not_a_catch_is_an_incompletion_with_no_gain(tmp_path):
    """A catch of 12 ruled complete: the tackle window 0 to 1 and the catch window 2 to 7: the draw 5 hits the catch."""
    rig, then = reversed_scene(tmp_path, COMPLETE, 5, booth=False, yards=12, offense_play=4, defense_play=3)
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.half, s.yard_line) == (0, INCOMPLETE, 2, 30)
    assert (s.stats[1].completions, s.stats[1].passing_yards, s.stats[1].pass_attempts) == (0, 0, 1)
    assert texts(rig)[-1] == " the pass was incomplete. "


def test_an_incompletion_that_was_a_catch_gains_the_yards_of_the_plays_row(tmp_path):
    """Short Pass against Short Pass (4, 5): 1 to 9 yards; the draw 6 gives 7."""
    rig, then = reversed_scene(tmp_path, INCOMPLETE, 3, truth_draws=Draws().below(9, 6), booth=False, offense_play=4,
                               defense_play=5, sentence=" Rec1 drops the ball ")
    s = rig.engine.s
    assert then == REVIEWED_FIELD
    assert (s.yards, s.result_kind, s.half, s.yard_line) == (7, COMPLETE, 2, 37)
    assert (s.stats[1].completions, s.stats[1].passing_yards, s.stats[1].pass_attempts) == (1, 7, 1)
    assert texts(rig)[-1] == " the pass was complete. "


def test_a_catch_that_was_out_of_bounds_and_a_reception_in_bounds_the_other_way_round(tmp_path):
    """A catch of 12 that ended at the side line: the tackle window is 0 to 1 and the side line's 2 to 6 (0.5 percent of the
    passes), so 4 says he was out of bounds when he caught it. The other way round the incompletion that "catches it out of
    bounds" is in bounds: Short Pass against Short Pass gives 1 to 9 yards, the draw 2 gives 3."""
    rig, then = reversed_scene(tmp_path, COMPLETE, 4, booth=False, yards=12, offense_play=4, defense_play=3,
                               extras={"out_of_bounds": True})
    s = rig.engine.s
    assert then == REVIEWED_FIELD and (s.result_kind, s.yards) == (INCOMPLETE, 0)
    assert texts(rig)[-1] == " the receiver was out of bounds. "
    rig, then = reversed_scene(tmp_path / "in", INCOMPLETE, 2, truth_draws=Draws().below(9, 2), booth=False, offense_play=4,
                               defense_play=5, sentence=" Rec1" + P.OUT_OF_BOUNDS)
    s = rig.engine.s
    assert then == REVIEWED_FIELD and (s.result_kind, s.yards) == (COMPLETE, 3)
    assert texts(rig)[-1] == " the receiver was in bounds. "


def test_a_truth_that_reaches_the_goal_line_is_a_touchdown_through_the_touchdown_step(tmp_path):
    """From the 7 an incompletion that was a catch of 9 yards (the draw 8 plus 1): a touchdown."""
    rig, then = reversed_scene(tmp_path, INCOMPLETE, 3, truth_draws=Draws().below(9, 8), booth=False, offense_play=4,
                               defense_play=5, spot=(1, 7), down=2, to_go=7, sentence=" Rec1 drops the ball ")
    s = rig.engine.s
    assert then == REVIEWED_TOUCHDOWN
    assert (s.yards, s.result_kind, s.half, s.yard_line) == (9, COMPLETE, 1, -2)
    assert (s.stats[1].completions, s.stats[1].passing_yards) == (1, 9)
