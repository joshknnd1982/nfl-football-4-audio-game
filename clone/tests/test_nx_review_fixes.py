"""The fixes of the independent review of SX.6 (work/review_sx6_findings.md): one test per finding that was fixed (nfl4 only, rule 0.13;
B-X31). This is inspired by Jim Kitchen.

1  a time out called before a won challenge keeps the clock stopped and keeps its signal time;
2  a reversal keeps the fact that the play went out of bounds, unless the corrected play cannot have;
3  (the games' test: test_nx_review_games.py) every reversal, the computer's too, has its corrected end point;
4  a throw-away has no catch to rule on;
5  the Challenge item is made again after a time out or a lost challenge;
6  a lost challenge is the time out of its dead-ball period;
8  the last play of a quarter is not challenged by anybody;
9  the sentences of a review are not in the replay list of F2;
10 the hint does not depend on F8 (decided, D-053); 14 a plain pass is asked about its catch;
15 the record refuses a third challenge without a win; 7 the switch Time outs off keeps the time outs of the challenges (decided).
Every number is worked out from the rule next to it (B-X38).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import review as RV
from nfl4.extras.state import ExtrasRecord
from nfl4.game.rules import REVIEWED_FIELD, REVIEWED_FUMBLE
from pagrig import Draws, run_steps
from test_nx_review_computer import computer_scene
from test_nx_review_flows import (CLOSE, ENTER, ESCAPE, FUMBLE, LINE_SHORT, NO, RUN, SELECT, WRONG, YES, at_the_menu, first_pass,
                                  the_menu)
from test_nx_review_plays import COMPLETE, INCOMPLETE, TD, pending, reversed_scene, rule, scene, texts


def timeout_scene(tmp_path, answers, extras=None, ruling=None):
    """Third and 5 from the 30 with the time outs on: the run of 4 is ruled short of the line (the ruling's draws), the Jets draw
    their rule 6 (one in 140: not now), the next play's menu comes."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, timeouts_on=True, answers=answers, extras=extras)
    d = first_pass(ruling or WRONG()).below(140, 99)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    at_the_menu(rig)
    return rig


# ----- 1: a time out, then a won challenge -----

def test_a_time_out_called_before_a_won_challenge_keeps_the_clock_stopped_and_the_seconds_it_ran(tmp_path):
    """900 on the clock, the run of 4 is charged its 4 seconds (896) and R = 30 is pending; the player calls a time out (the signal
    time u = 3 + 1 = 4 seconds of the 30 run: 892, the clock is stopped), then wins the challenge: the 4 seconds of the ruled play
    are given back (896), the corrected play takes its own 4 (892) and NO runoff is drawn: the stopped clock stays stopped to the
    snap, and the time out is gone for good (2 left, used 1)."""
    rig = timeout_scene(tmp_path, ["t", "c", ENTER, "y", ENTER])
    x = rig.engine.s.extras
    assert (x.left, x.pending, x.running) == (900 - 4, 30, True)
    d = Draws().below(6, 1).rady().rady()                           # the time out's u, the referee's two pauses
    d.below(4, 0).rnd(4, 1).below(140, 99)                          # the corrected play: L, the banter, the Jets' rule 6; no runoff
    assert the_menu(rig, d) == "next_play"
    assert (x.chal_used, x.chal_won, x.timeouts, x.used, x.called) == ([1, 0], [1, 0], [2, 3], [1, 0], [True, False])
    assert (x.left, x.pending, x.running) == (900 - 4 - 4, 0, False)
    assert (rig.engine.s.down, rig.engine.s.to_go) == (1, 10)       # the first down the run of 5 made


# ----- 2: out of bounds -----

def test_a_reversal_keeps_the_fact_that_the_run_went_out_of_bounds_so_the_clock_stays_stopped_in_the_late_window(tmp_path):
    """The fourth quarter with 4:00 left (the last 5:00: a runner out of bounds stops the clock until the snap, 4-3-2): the run of 4
    ended out of bounds and was ruled short of the line; the challenge makes it 5 yards. The corrected play ended out of bounds as
    well: the clock is stopped (no runoff drawn), not running for 30 seconds."""
    rig, then = reversed_scene(tmp_path, RUN, 10, booth=False, yards=4, down=3, to_go=5, quarter=4,
                               extras={"period": 4, "left": 240, "out_of_bounds": True})
    assert then == REVIEWED_FIELD
    x = rig.engine.s.extras
    assert x.out_of_bounds is True
    assert run_steps(rig, rig.engine.gain_and_end, Draws().below(4, 0).rnd(4, 1)) == "next_play"
    assert (x.pending, x.running) == (0, False)


@pytest.mark.parametrize("kind, value, kwargs, then, cleared", [
    # a run called down that fumbled: nothing ended at the side line
    (RUN, 0, dict(yards=3, down=1, to_go=10), REVIEWED_FUMBLE, True),
    # a catch ruled in bounds that was out: the pass was incomplete
    (COMPLETE, 3, dict(yards=8, down=1, to_go=10, offense_play=4, defense_play=5), REVIEWED_FIELD, True),
    # a run short of the line that made it: the same run, the same side line
    (RUN, 10, dict(yards=4, down=3, to_go=5), REVIEWED_FIELD, False)])
def test_a_reversal_clears_the_out_of_bounds_fact_only_when_the_corrected_play_cannot_have_it(tmp_path, kind, value, kwargs, then,
                                                                                               cleared):
    rig, got = reversed_scene(tmp_path, kind, value, booth=False, extras={"out_of_bounds": True}, **kwargs)
    assert got == then
    assert rig.engine.s.extras.out_of_bounds is (not cleared)


# ----- 4: a throw-away -----

def test_a_throw_away_has_no_catch_to_rule_on_and_any_other_incompletion_has(tmp_path):
    """The sentence of the passer throwing the ball away (NXP-21) is the grounding foul's play: no receiver, no draw."""
    away = X.text("NXP-21", quarterback="Starr")
    rig, record = scene(tmp_path, INCOMPLETE, offense_play=4, defense_play=5, down=2, to_go=7, sentence=away)
    assert rule(rig, record, Draws()) is None and pending(rig) is None          # no draw at all (a strict source)
    rig, record = scene(tmp_path / "other", INCOMPLETE, offense_play=4, defense_play=5, down=2, to_go=7)
    rule(rig, record, Draws().below(1000, 999))                                  # a plain ruling on the catch
    assert (pending(rig).primary.category, pending(rig).primary.ruled) == ("catch", RV.INCOMPLETE)


# ----- 5 and 6: the item and the time out of a lost challenge -----

def test_the_challenge_item_is_made_again_after_the_last_time_out_and_the_letter_says_why(tmp_path):
    """One time out left: the menu has the Challenge item (8) and Time Out (9). The player takes the time out (u = 4); the menu
    starts again without the item and C says that a time out is needed (NXR-11)."""
    rig = timeout_scene(tmp_path, ["t", "c", ESCAPE], extras={"timeouts": [1, 3]})
    mark = len(rig.said)
    assert the_menu(rig, Draws().below(6, 1)) == "concede"
    assert texts(rig, mark) == [SELECT, " 1. Line Plunge ", X.text("NXT-01", team="Bengals"), X.text("NXT-10"),
                                SELECT, " 1. Line Plunge ", X.text("NXR-11"), " 1. Line Plunge "]
    assert [i.text for i in rig.rules.offense_menu(rig.engine.s, False)][-2:] == [" 8. Time Out ", " 9. Save Game "]


def test_a_lost_challenge_is_the_time_out_of_its_dead_ball_period_and_a_second_one_is_refused(tmp_path):
    """The ruling was right but close: the review confirms it, the Bengals lose a time out (2 left, used 1) and cannot call
    another in this dead-ball period (4-5-1 Item 3): T at the menu says so (NXT-05) and nothing is charged."""
    rig = timeout_scene(tmp_path, ["c", ENTER, "y", ENTER, "t", ESCAPE], ruling=CLOSE())
    mark = len(rig.said)
    assert the_menu(rig, Draws().rady().rady()) == "concede"
    assert texts(rig, mark) == [
        SELECT, " 1. Line Plunge ", " 8. Challenge the Ruling ",
        " Kim do you wish to challenge the ruling that " + LINE_SHORT + "? ",
        " you have 2 challenges and 3 time outs left. a time out is lost if the ruling stands. ", NO, YES,
        X.text("NXR-04"), X.text("NXR-07"), " the Bengals lose a time out. ",
        SELECT, " 1. Line Plunge ", X.text("NXT-05"), SELECT, " 1. Line Plunge "]
    x = rig.engine.s.extras
    assert (x.timeouts, x.used, x.called) == ([2, 3], [1, 0], [True, False])


# ----- 8: the last play of a quarter -----

def test_the_computer_does_not_challenge_the_play_that_used_the_last_second_of_the_quarter(tmp_path):
    """4 seconds left in the first quarter, the run takes its 4 (the clock says 0:00: the quarter is over): the ruling is wrong, the
    announcer hints strongly, and still no flag is thrown (the draw 0 would have thrown it); the player's coach would be refused
    as well (the item is never offered at the next menu, which is in the second quarter)."""
    rig, d = computer_scene(tmp_path, Draws().below(1000, 10).below(100, 0).below(100, 0), extras={"left": 4})
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    x = rig.engine.s.extras
    assert x.left == 0 and x.chal_used == [0, 0]
    ruling = pending(rig)
    assert ruling.wrong and ruling.hint == "strong" and ruling.left_after == 0
    assert rig.rules.review.refusal(rig.engine.s, 2) == "nothing" and rig.rules.review.refusal(rig.engine.s, 1) == "nothing"


# ----- 9: F2 -----

def test_the_sentences_of_a_review_are_spoken_and_logged_but_not_kept_for_the_instant_replay(tmp_path):
    """First and 5 from the 5: the replay official reverses a touchdown (the corrected play is 4 yards): F2's list holds the
    original's sentences of the corrected play and none of the review's (N2.6)."""
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5)
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 99).rady().rady().below(4, 0).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.touchdown_reached, d) == "next_play"
    said = texts(rig)
    assert X.text("NXR-04") in said and X.text("NXR-05") in said and " the runner was short of the goal line. " in said
    kept = list(rig.game.replay)
    assert " There is a gain of 4 yards on the play" in kept
    for text in (X.text("NXR-08"), X.text("NXR-04"), X.text("NXR-05"), " the runner was short of the goal line. "):
        assert text not in kept, text


# ----- 10, 14: the hint without F8, the plain pass -----

def test_the_computer_hears_the_hint_with_f8_off_and_a_plain_pass_is_asked_about_its_catch(tmp_path):
    """Decided (D-053): the hint is a fact of the play; F8 only mutes the announcer, so the Jets' flag follows a strong hint
    with the comments switched off too (these scenes have F8 on: nothing is said, nothing is drawn for a remark)."""
    rig, d = computer_scene(tmp_path / "f8", Draws().below(1000, 10).below(100, 0).below(100, 0))
    d.below(100, 0).rady().rady().below(4, 0).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert rig.engine.s.extras.chal_used == [0, 1] and rig.game.comtog == 1
    rig, record = scene(tmp_path / "pass", COMPLETE, yards=8, offense_play=4, defense_play=5, down=1, to_go=10)
    rule(rig, record, Draws().below(1000, 999))
    assert (pending(rig).primary.category, pending(rig).primary.ruled) == ("catch", RV.COMPLETE)
    rig, record = scene(tmp_path / "run", RUN, yards=3, down=1, to_go=10)
    rule(rig, record, Draws().below(1000, 999))
    assert (pending(rig).primary.category, pending(rig).primary.ruled) == ("down", RV.DOWN_BEFORE)


# ----- 15, 7: the record, the switch -----

def test_the_record_refuses_a_third_challenge_that_no_win_earned():
    ExtrasRecord(chal_used=[3, 2], chal_won=[1, 0]).check()
    ExtrasRecord(chal_used=[2, 0], chal_won=[0, 0]).check()
    for used, won in (([3, 0], [0, 0]), ([4, 0], [3, 0]), ([1, 0], [2, 0])):
        with pytest.raises(ValueError):
            ExtrasRecord(chal_used=used, chal_won=won).check()


def test_with_the_time_outs_switch_off_the_teams_keep_their_time_outs_for_the_challenges(tmp_path):
    """Decided (D-053): the switch takes the Time Out item and the computer's own calls away; a challenge still needs a time out in
    hand and a lost one costs it, so the question says so (the same sentence as with the switch on)."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, timeouts_on=False, extras={"timeouts": [0, 3]})
    rule(rig, record, Draws().below(1000, 999))
    assert rig.rules.review.refusal(rig.engine.s, 1) == "no timeout"
    rig.engine.s.extras.timeouts = [2, 3]
    assert rig.rules.review.refusal(rig.engine.s, 1) is None
    items = [i.text for i in rig.rules.offense_menu(rig.engine.s, False)]
    assert items[-2:] == [" 8. Challenge the Ruling ", " 9. Save Game "] and not [t for t in items if "Time Out" in t]
