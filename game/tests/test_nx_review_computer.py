"""The computer's flag between the plays, the remarks after a review, the last second of a half, the statistics and the help
(nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 6.2, 6.4, 15; PX SX.6). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source in the order of the design as built; every number and text is worked out from
the rule next to it (B-X38). The scene is third and 5 from the 30: the run of 5 is ruled a first down, which went against the
defense, the computer's side (line to gain window: wrong 0 to 29, close 32 to 91 per 1000, design 6.1).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import review as RV
from nfl4.game import phrases as P
from pagrig import Draws, run_steps
from test_nx_review_plays import FUMBLE, RUN, TD, feed, rule, scene, texts, throw, used_up

FLAG = " the Jets have thrown the red flag. they are challenging the ruling that the runner made the first down. "
FIRST_DOWN = [" There is a gain of 5 yards on the play", " it's your ball on your 35yard line", " it's first down and 10yards to go"]


def computer_scene(tmp_path, ruling: Draws, **kwargs):
    """The first part of the end of the play: the ruling's draws, the live time (a run 4 to 7 seconds: the draw 0 is 4), the
    banter draw 1 in 4 (1: none)."""
    kwargs.setdefault("yards", 5)
    rig, record = scene(tmp_path, RUN, down=3, to_go=5, **kwargs)
    d = Draws().below(4, 0)
    d.extend(ruling)
    return rig, d.rnd(4, 1)


def test_the_computer_throws_the_flag_after_a_strong_hint_and_the_review_reverses_the_ruling(tmp_path):
    """The hint was heard (0 is below 70) and the flag chance is 80 percent (0 is below it). The pauses of the review, then the
    corrected play (4 yards: fourth and 1) is told again with its live time, the banter draw and the runoff."""
    rig, d = computer_scene(tmp_path, Draws().below(1000, 10).below(100, 0).below(100, 0))
    d.below(100, 0).rady().rady().below(4, 0).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig) == FIRST_DOWN + [
        FLAG, X.text("NXR-04"), X.text("NXR-05"), " the runner was short of the first down. ",
        " There is a gain of 4 yards on the play", " it's your ball on your 34yard line", " it's fourth down and 1yard to go"]
    x, s = rig.engine.s.extras, rig.engine.s
    assert (x.chal_used, x.chal_won, x.timeouts, x.used) == ([0, 1], [0, 1], [3, 3], [0, 0])
    assert (s.down, s.to_go, s.stats[1].first_downs) == (4, 1, 0)
    assert x.left == 900 - 4 and rig.rules.review.pending is None
    assert rig.rules.review.events == [(1, "coach", 2, "line", True, "reversed", RV.MADE_THE_LINE, "", 3)]


def test_the_computer_throws_the_flag_after_a_close_call_hint_with_30_percent_and_may_lose(tmp_path):
    """The ruling was right but close (40), the hint is the close-call kind (0 is below 50), the flag draw 29 is below 30: the
    review confirms the call, the Jets lose a time out, and the play goes on as it was (the runoff is drawn; the time out the
    lost challenge charged is their one of this dead-ball period, so their own time out rule draws nothing, finding 6)."""
    rig, d = computer_scene(tmp_path, Draws().below(1000, 40).below(100, 0))
    d.below(100, 29).rady().rady().below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig)[3:] == [FLAG, X.text("NXR-04"), X.text("NXR-07"), " the Jets lose a time out. "]
    x = rig.engine.s.extras
    assert (x.chal_used, x.chal_won, x.timeouts, x.used) == ([0, 1], [0, 0], [3, 2], [0, 1])
    assert (x.pending, x.running) == (30, True)


def test_a_close_call_hint_needs_a_draw_below_30_and_a_wrong_ruling_without_a_hint_is_never_challenged(tmp_path):
    rig, d = computer_scene(tmp_path, Draws().below(1000, 40).below(100, 0))
    d.below(100, 30).below(11, 0)                                       # 30 is not below 30
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig)[3:] == [] and rig.engine.s.extras.chal_used == [0, 0]
    rig, d = computer_scene(tmp_path / "nohint", Draws().below(1000, 10).below(100, 0).below(100, 99))   # wrong, no hint
    d.below(11, 0)                                                      # no draw for a flag at all
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert rig.engine.s.extras.chal_used == [0, 0] and rig.rules.review.pending.wrong is True


def test_the_computer_does_not_throw_the_flag_for_the_player(tmp_path):
    """The run of 4 ruled short is against the offense, the player's side: the computer (side 2) leaves it alone."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5)
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 0).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert rig.engine.s.extras.chal_used == [0, 0] and rig.rules.review.pending.hint == "strong"


def test_two_computers_each_throw_their_own_flag(tmp_path):
    """With both sides by the computer (the calibration's) side 1's coach challenges the run of 4 ruled short: the corrected run
    is 5 yards and a first down."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, auto_sides=(1, 2))
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 0).rnd(4, 1)
    d.below(100, 0).rady().rady().below(4, 0).rnd(4, 1).below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig)[3:] == [
        " the Bengals have thrown the red flag. they are challenging the ruling that the runner was short of the first down. ",
        X.text("NXR-04"), X.text("NXR-05"), " the runner made the first down. ", " There is a gain of 5 yards on the play",
        " it's your ball on your 35yard line", " it's first down and 10yards to go"]
    x = rig.engine.s.extras
    assert (x.chal_used, x.chal_won) == ([1, 0], [1, 0])


def test_a_fourth_down_conversion_that_the_review_takes_back_turns_the_ball_over_on_downs(tmp_path):
    """Fourth and 5: the run of 5 is ruled a first down (a coach's play: only a failed fourth down is the replay official's). The
    computer's flag finds it was 4 yards: the corrected play is a failed fourth down and the engine goes on at the possession
    sentence of the original's turnover on downs, with the first down the ruling had counted gone."""
    rig, record = scene(tmp_path, RUN, yards=5, down=4, to_go=5)
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 0).rnd(4, 1)
    d.below(100, 0).rady().rady().below(4, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d, until=("possession",)) == "possession"
    assert texts(rig) == FIRST_DOWN + [FLAG, X.text("NXR-04"), X.text("NXR-05"), " the runner was short of the first down. ",
                                       " There is a gain of 4 yards on the play"]
    s = rig.engine.s
    assert (s.down, s.downs_flag, s.text, s.stats[1].first_downs) == (5, True, P.TURNED_OVER_ON_DOWNS, 0)
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 4)


@pytest.mark.parametrize("extras", [{"chal_used": [0, 2]}, {"timeouts": [3, 0]}])
def test_the_computer_cannot_challenge_without_a_challenge_or_a_time_out_and_draws_nothing_for_it(tmp_path, extras):
    rig, d = computer_scene(tmp_path, Draws().below(1000, 10).below(100, 0).below(100, 0), extras=extras)
    d.below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert texts(rig)[3:] == []


def test_a_computer_with_one_time_out_and_a_challenge_left_keeps_it_before_the_warning_and_draws_nothing(tmp_path):
    """Rule 1 of design 6.3 (SX.6): the last time out is kept for a challenge until the two-minute warning of the half; after the
    warning rule 2 may call it (the second quarter, the offense inside its own 35 on third down, the clock running)."""
    from nfl4.extras import timeouts as TO
    before = TO.Situation(2, 2, 100, 20, True, False, -7, 1, False, True, 30, 3, 2)
    assert TO.challenge_possible(before) is True
    assert TO.computer_calls(before, None) is False                       # rnd is None: a draw would raise
    after = TO.Situation(2, 2, 100, 20, True, False, -7, 1, True, True, 30, 3, 2)
    assert TO.challenge_possible(after) is False
    assert TO.computer_calls(after, None) is True                         # rule 2: the defense stops the clock after a punt


# ----- the remarks after a review (pools RVR and RVC) -----

def test_a_remark_of_pool_rvr_follows_a_reversal_with_chance_one_in_two_when_the_comments_are_on(tmp_path):
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5, comments=True)
    rule(rig, record, Draws().below(1000, 10).below(100, 0).below(100, 99).rady().rady().rnd(2, 1).rnd(3, 2))
    assert texts(rig)[-2:] == [" the runner was short of the goal line. ", " the replay showed it clearly, Gus Delgado. "]
    rig, record = scene(tmp_path / "no", TD, yards=5, spot=(1, 5), down=1, to_go=5, comments=True)
    rule(rig, record, Draws().below(1000, 10).below(100, 0).below(100, 99).rady().rady().rnd(2, 2))    # 2 is not 1: none
    assert texts(rig)[-1] == " the runner was short of the goal line. "


def test_the_booth_never_says_rvc03_that_a_time_out_was_wasted_and_a_lost_challenge_may(tmp_path):
    """RVC has three lines; after a booth review the draw is over the two that are not RVC03 (`rnd(2)`), after a lost challenge
    over all three (`rnd(3)`)."""
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5, comments=True)
    rule(rig, record, Draws().below(1000, 150).below(100, 99).below(100, 13).rady().rady().rnd(2, 1).rnd(2, 2))
    assert texts(rig)[-2:] == [X.text("NXR-07"), " not enough there to change the call. "]
    assert rig.engine.s.extras.recent == {"RVC": ["RVC02"]}
    rig, record = scene(tmp_path / "lost", RUN, yards=4, down=3, to_go=5, comments=True)
    rule(rig, record, Draws().below(1000, 40).below(100, 99))
    assert throw(rig, Draws().rady().rady().rnd(2, 1).rnd(3, 3)) is None
    assert texts(rig)[-3:] == [X.text("NXR-07"), " the Bengals lose a time out. ", " that is a time out wasted, Gus Delgado. "]


@pytest.mark.parametrize("value, what", [(0, "wrong"), (119, "wrong"), (120, "close"), (254, "close"), (255, "plain")])
def test_a_play_of_the_replay_officials_is_wrong_twice_as_often_in_the_wrong_windows_only(tmp_path, value, what):
    """A touchdown has the goal line aspect (wrong 60, close 135 per 1000): as a booth play the wrong window is 0 to 119 and the
    close one 120 to 254 (the close window is not doubled); a coach's play (the second scene) has 0 to 59 and 60 to 194."""
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5)
    d = Draws().below(1000, value)
    if what == "wrong":
        d.below(100, 0).below(100, 99).rady().rady()             # clear, no hint, the replay official reviews it
    elif what == "close":
        d.below(100, 99).below(100, 99)                          # no hint, the booth's 14 percent not met
    rule(rig, record, d)                                         # (a reversal clears the pending ruling: read the list)
    quarter, category, wrong, close, hint, reason = rig.rules.review.rulings[-1]
    assert (wrong, close, reason) == (what == "wrong", what == "close", "booth")
    rig, record = scene(tmp_path / "coach", RUN, yards=4, spot=(1, 5), down=2, to_go=5)        # the same aspect, a coach's play
    d = Draws().below(1000, value)
    coach_what = "wrong" if value < 60 else "close" if value < 195 else "plain"
    if coach_what == "wrong":
        d.below(100, 99).below(100, 99)
    elif coach_what == "close":
        d.below(100, 99)
    assert rule(rig, record, d) is None
    assert rig.rules.review.pending.wrong is (coach_what == "wrong")


@pytest.mark.parametrize("hint_draw, flags", [(79, True), (80, False)])
def test_the_computer_throws_the_flag_after_a_strong_hint_with_chance_80_percent(tmp_path, hint_draw, flags):
    rig, d = computer_scene(tmp_path, Draws().below(1000, 10).below(100, 0).below(100, 0))
    d.below(100, hint_draw)
    if flags:
        d.rady().rady().below(4, 0).rnd(4, 1)
    d.below(11, 0)
    assert run_steps(rig, rig.engine.gain_and_end, d) == "next_play"
    assert (rig.engine.s.extras.chal_used == [0, 1]) is flags


def test_a_booth_review_of_a_close_ruling_has_a_14_percent_chance(tmp_path):
    for value, reviewed in ((13, True), (14, False)):
        rig, record = scene(tmp_path / ("v%d" % value), TD, yards=5, spot=(1, 5), down=1, to_go=5)
        d = Draws().below(1000, 150).below(100, 99).below(100, value)
        if reviewed:
            d.rady().rady()
        assert rule(rig, record, d) is None
        assert bool(texts(rig)) is reviewed
        assert [e[1] for e in rig.rules.review.events] == (["booth"] if reviewed else [])


def test_a_close_call_on_a_booth_play_says_its_hint_first_then_the_booth_decides_with_14_percent(tmp_path):
    """A fumble lost (the booth's): the wrong window is 80 doubled for a play of the replay official's, 0 to 159, and the close
    window 135 more, 160 to 294: 200 is in it. The hint (10 is below 50) is a remark of pool CHC (the draw 3 is CHC03), then the
    booth's chance 99 is not below 14: no review."""
    rig, record = scene(tmp_path, FUMBLE, comments=True)
    assert rule(rig, record, Draws().below(1000, 200).below(100, 10).rnd(3, 3).below(100, 99)) is None
    assert texts(rig) == [" a bang bang play there. "]
    assert rig.rules.review.pending.hint == "close" and rig.rules.review.events == []


# ----- the last second of a half (B-X34) -----

def test_a_reversal_on_the_last_play_of_a_half_runs_the_corrected_play_to_0_00_and_nothing_goes_negative(tmp_path):
    """The second quarter, after the warning, 3 seconds left: a touchdown by the replay official, reversed to a run of 4: its
    live time is 4 seconds, the clock stops at 0:00 (a play is completed, 4-8-1), no runoff and no time out can follow."""
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5, quarter=2,
                        extras={"warning_given": True, "period": 2, "left": 3})
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 99).rady().rady().below(4, 0).rnd(4, 1)
    assert run_steps(rig, rig.engine.touchdown_reached, d) == "next_play"
    x, s = rig.engine.s.extras, rig.engine.s
    assert (x.left, x.pending, x.running) == (0, 0, False)
    assert (s.down, s.to_go, s.yard_line) == (2, 1, 1)
    x.check()


def test_a_reversal_puts_the_clock_back_to_before_the_live_time_and_never_past_the_length_of_the_period(tmp_path):
    """The ruled play was charged 7 seconds from 900; a computer time out used 5 more (its signal time ran off after the play);
    the challenge gives the 7 seconds back and keeps the 5: 900 - 5 (review finding 1). A damaged record that said more than
    the period holds is capped at the period's length (15:00)."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, extras={"left": 900 - 7})
    rule(rig, record, Draws().below(1000, 10).below(100, 0).below(100, 99), before=900)
    rig.engine.s.extras.left = 900 - 7 - 5
    assert throw(rig, Draws().rady().rady()) == "reviewed field play"
    assert rig.engine.s.extras.left == 900 - 5
    rig, record = scene(tmp_path / "cap", RUN, yards=4, down=3, to_go=5)
    rule(rig, record, Draws().below(1000, 10).below(100, 0).below(100, 99))
    rig.rules.review.pending.left_before = 5000
    throw(rig, Draws().rady().rady())
    assert rig.engine.s.extras.left == 900


# ----- the statistics, the help -----

def test_the_quarter_statistics_say_the_challenges_won_and_lost_of_each_side(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, extras={"chal_used": [2, 1], "chal_won": [1, 0]})
    lines = rig.rules.extra_stats_lines(rig.engine.s)
    assert lines == [" Challenges Won", "Bengals 1", "Jets 0", " Challenges Lost", "Bengals 1", "Jets 1"] == [
        X.text("NXS-04"), "Bengals 1", "Jets 0", X.text("NXS-05"), "Bengals 1", "Jets 1"]


def test_the_help_of_f5_f6_and_f7_has_the_challenge_lines_only_when_challenges_are_on(tmp_path):
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5)
    from nflrig import feature_help
    on = {key: feature_help(rig.rules, key) for key in ("116", "117", "118")}
    assert X.text("NXH-23") in on["116"] and X.text("NXH-24") in on["117"] and X.text("NXH-25") in on["117"]
    assert X.text("NXH-26") in on["118"]
    rig.engine.s.extras.challenges_on = False
    off = {key: feature_help(rig.rules, key) for key in ("116", "117", "118")}
    added = {"116": ("NXH-23",), "117": ("NXH-24", "NXH-25"), "118": ("NXH-26",)}
    for key in on:
        assert [t for t in on[key] if t not in off[key]] == [X.text(i) for i in added[key]]
