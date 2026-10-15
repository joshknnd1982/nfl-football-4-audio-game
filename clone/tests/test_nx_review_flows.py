"""Booth reviews and challenges through the engine and its menus: the plays told again after a reversal, the player's question at the
play menu, the lost time out, the refusals with their reasons, the computer's flag, the limits (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 6.2, 6.4, 15; PX SX.6). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source in the order of the design as built and every number and text is worked out from
the rule next to it (B-X38). The scenes (tests/test_nx_review_plays.py `scene`) start at the narration end point of a play that has
just been told; the first part runs the end of the play (`gain_and_end` or `touchdown_reached`: the ruling, the apply step, the
position and down sentences, the computer's clock), the second the next play menu with the keys of the player.
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import review as RV
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.speech.roles import ANNOUNCER
from pagrig import Draws, run_steps, sounds_played
from test_nx_review_plays import COMPLETE, ENTER, FUMBLE, INCOMPLETE, RUN, TD, feed, rule, scene, texts, used_up

ESCAPE, DOWN, UP, F1 = 27, 40, 38, 112
MENU_UNTIL = ("next_play", "play_menu", "kick_off", "finish", "concede", "offense_chosen", "defense_chosen", "save_game")
SELECT = " Kim" + P.SELECT_OFFENSE
LINE_SHORT = "the runner was short of the first down"          # what a coach challenges when the run of 4 on third and 5 is "short"
NO, YES = X.text("NXO-A01"), X.text("NXO-A02")


def tail(d: Draws, live=4, banter=1, runoff=0) -> Draws:
    """What follows a play that keeps the ball and the clock running: its live time L (a run 4 to 7 is `below(4)`: the draw 0 is 4
    seconds), the banter draw 1 in 4 at the position, then, between plays, the runoff R = 30 to 40 (`below(11)`)."""
    return d.below(live, 0).rnd(4, banter).below(11, runoff)


def first_pass(ruling: Draws, live=4, banter=1, runoff=0) -> Draws:
    """The end point of a play whose ruling is drawn (design 15 as built): its live time L first (the clock is charged before the
    ruling, so a reversal can go back to the time before it), then the ruling's draws, then the banter draw and the runoff."""
    d = Draws().below(live, 0)
    d.extend(ruling)
    return d.rnd(4, banter).below(11, runoff)


def at_the_menu(rig):
    """The next-play step and the period checks: the counter grows and the play menu comes."""
    assert run_steps(rig, rig.engine.next_play, Draws(), until=("play_menu",)) == "play_menu"


def the_menu(rig, draws: Draws, step="offense_menu"):
    return run_steps(rig, getattr(rig.engine, step), draws, until=MENU_UNTIL)


def line_scene(tmp_path, ruling_draws: Draws, **kwargs):
    """Third and 5 from the 30: the run of 4 is ruled short of the line (fourth and 1) and the end of the play is run with the
    ruling's draws (design 6.1: the aspects are the line to gain, wrong 0 to 29 and close 32 to 91, and the tackle, wrong 30 to 31).
    Returns the rig at the next-play step."""
    rig, record = scene(tmp_path, RUN, yards=4, down=3, to_go=5, **kwargs)
    assert run_steps(rig, rig.engine.gain_and_end, first_pass(ruling_draws)) == "next_play"
    assert texts(rig) == [" There is a gain of 4 yards on the play", " it's your ball on your 34yard line",
                          " it's fourth down and 1yard to go"]
    return rig


WRONG = lambda: Draws().below(1000, 10).below(100, 0).below(100, 99)             # the line to gain wrong and clear, no hint
CLOSE = lambda: Draws().below(1000, 40).below(100, 99)                           # the line to gain right but close, no hint
UNCLEAR = lambda: Draws().below(1000, 10).below(100, 85).below(100, 99)          # wrong but not clear and obvious (85 or more)


# ----- a booth review, from the end of the play to the next one -----

def test_the_replay_official_reverses_a_touchdown_that_was_short_and_the_play_goes_on_from_the_one(tmp_path):
    """First and 5 from the 5: the run of 5 is ruled a touchdown, the window of the goal line (wrong 60 per 1000) is hit by 10,
    the replay shows it clearly (0 is below 85), no hint (99 is not below 70). The replay official stops the game (a touchdown is
    his, 15-1-2), the referee goes under the hood (two pauses), the ruling is reversed and the corrected play is told: 4 yards, the
    ball on the 1, second and goal. The corrected end point is not ruled again: there is no second draw of 1000."""
    rig, record = scene(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5)
    d = tail(Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 99).rady().rady())   # L of the ruled play, the ruling
    assert run_steps(rig, rig.engine.touchdown_reached, d) == "next_play"
    assert rig.said == [
        (X.text("NXR-08"), ANNOUNCER, 0), (X.text("NXR-04"), ANNOUNCER, 0), (X.text("NXR-05"), ANNOUNCER, 0),
        (" the runner was short of the goal line. ", ANNOUNCER, 0), (" There is a gain of 4 yards on the play", ANNOUNCER, 0),
        (" it's your ball on my 1yard line", ANNOUNCER, 0), (" it's second down and goal to go", ANNOUNCER, 0)]
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.half, s.yard_line, s.down, s.to_go, s.wisoff) == (1, 1, 2, 1, 1)
    assert (s.stats[1].running_plays, s.stats[1].running_yards, s.stats[1].first_downs, s.stats[1].score) == (1, 4, 0, 0)
    assert [(o.kind, o.yards, o.then) for o in rig.engine.outcomes] == [(O.TOUCHDOWN, 5, "reviewed field play"),
                                                                        (O.RUN, 4, None)]
    assert x.left == 900 - 4 and (x.pending, x.running) == (30, True)      # the first L given back, L of the corrected play, R = 30
    assert x.chal_used == [0, 0] and x.timeouts == [3, 3]                   # a booth review costs nobody anything
    assert rig.rules.review.events == [(1, "booth", 0, "goal", True, "reversed", RV.CROSSED_GOAL, "booth", 0)]
    assert sounds_played(rig).count("foot11") == 1                          # the referee's whistle


def test_a_reversal_that_creates_a_touchdown_goes_on_at_the_touchdown_step_and_scores_six(tmp_path):
    """Third and goal from the 5, after the two-minute warning (a play of the replay official, 15-1-2 (a)): a catch of 4 is ruled
    short of the goal line, the goal line window 0 to 59 is hit by 10. The truth is 5 yards (design 6.1) and the engine goes on at
    the touchdown step: its live time (a catch 5 to 8 seconds: `below(4)`, 5), the touchdown, the celebration, the pause."""
    rig, record = scene(tmp_path, COMPLETE, yards=4, spot=(1, 5), offense_play=4, defense_play=5, down=3, to_go=5, quarter=2,
                        extras={"warning_given": True, "period": 2, "left": 100})
    d = Draws().below(4, 0).below(1000, 10).below(100, 0).below(100, 99).rady().rady().below(4, 0).celebration(8).rady()
    until = ("extra_point_choice", "extra_point", "next_play")
    assert run_steps(rig, rig.engine.gain_and_end, d, until=until) == "extra_point_choice"
    assert texts(rig) == [" There is a gain of 4 yards on the play", X.text("NXR-08"), X.text("NXR-04"), X.text("NXR-05"),
                          " the runner crossed the goal line. ", P.TOUCH_DOWN]       # the catch as ruled, the review, the score
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.stats[1].score, s.stats[1].completions, s.stats[1].passing_yards, s.stats[1].pass_attempts) == (6, 1, 5, 1)
    assert x.left == 100 - 5 and s.quarter == 2


# ----- the player's challenge at the play menu -----

def test_a_challenge_that_wins_gives_the_first_down_and_costs_nothing(tmp_path):
    """The line to gain window 0 to 29 is hit by 10, the replay will show it (0 is below 85), no hint. The run of 4 on third and 5
    is ruled short, so it is fourth and 1. At the next menu the player presses C (the item is 8, before Save Game: only now),
    answers yes, and the referee finds the first down: 5 yards, first and 10 on the 35. No time out is lost, one challenge used
    and won, the clock has its live time back and the corrected play takes its own."""
    rig = line_scene(tmp_path, WRONG(), answers=["c", ENTER, "y", ENTER])
    x = rig.engine.s.extras
    assert (x.left, x.pending, x.running) == (900 - 4, 30, True)
    at_the_menu(rig)
    mark = len(rig.said)
    d = Draws().rady().rady()
    tail(d)
    assert the_menu(rig, d) == "next_play"
    assert texts(rig, mark) == [
        SELECT, " 1. Line Plunge ", " 8. Challenge the Ruling ",
        " Kim do you wish to challenge the ruling that " + LINE_SHORT + "? ",
        " you have 2 challenges and 3 time outs left. a time out is lost if the ruling stands. ", NO, YES,
        X.text("NXR-04"), X.text("NXR-05"), " the runner made the first down. ",
        " There is a gain of 5 yards on the play", " it's your ball on your 35yard line",
        " it's first down and 10yards to go"]
    s = rig.engine.s
    assert (s.half, s.yard_line, s.down, s.to_go, s.counter) == (2, 35, 1, 10, 1)       # the counter goes back with the board
    assert (s.stats[1].running_plays, s.stats[1].running_yards, s.stats[1].first_downs) == (1, 5, 1)
    assert (x.chal_used, x.chal_won, x.timeouts, x.used) == ([1, 0], [1, 0], [3, 3], [0, 0])
    assert (x.left, x.pending, x.running) == (900 - 4, 30, True)                         # given back 4, then 4 again
    assert rig.rules.review.pending is None
    assert [(o.kind, o.yards) for o in rig.engine.outcomes] == [(O.RUN, 4), (O.RUN, 5)]


def test_a_challenge_that_loses_costs_a_time_out_and_the_item_then_says_there_is_nothing_to_challenge(tmp_path):
    """The ruling was right but close (the close window 32 to 91 is hit by 40): the review confirms it, the Bengals lose a time
    out (15-1-1 (e)), and a second C on the same play is refused: a review looked at every aspect already (15-2-2)."""
    rig = line_scene(tmp_path, CLOSE(), answers=["c", ENTER, "y", ENTER, "c", ENTER, ESCAPE])
    at_the_menu(rig)
    mark = len(rig.said)
    assert the_menu(rig, Draws().rady().rady()) == "concede"
    assert texts(rig, mark) == [
        SELECT, " 1. Line Plunge ", " 8. Challenge the Ruling ",
        " Kim do you wish to challenge the ruling that " + LINE_SHORT + "? ",
        " you have 2 challenges and 3 time outs left. a time out is lost if the ruling stands. ", NO, YES,
        X.text("NXR-04"), X.text("NXR-07"), " the Bengals lose a time out. ",
        SELECT, " 1. Line Plunge ", " 8. Challenge the Ruling ", X.text("NXR-15"), " 8. Challenge the Ruling "]
    x, s = rig.engine.s.extras, rig.engine.s
    assert (x.chal_used, x.chal_won, x.timeouts, x.used) == ([1, 0], [0, 0], [2, 3], [1, 0])
    assert (s.down, s.to_go, s.yard_line) == (4, 1, 34)                                  # nothing changed
    assert rig.rules.review.pending.challenged is True


def test_a_wrong_ruling_that_the_replay_does_not_show_clearly_stands_and_costs_the_time_out(tmp_path):
    """Wrong, but the evidence is not clear and obvious (85 is not below 85, 15-2-1): the ruling stands, the time out is lost."""
    rig = line_scene(tmp_path, UNCLEAR(), answers=["c", ENTER, "y", ENTER, ESCAPE])
    at_the_menu(rig)
    mark = len(rig.said)
    assert the_menu(rig, Draws().rady().rady()) == "concede"
    assert texts(rig, mark)[7:10] == [X.text("NXR-04"), X.text("NXR-06"), " the Bengals lose a time out. "]
    x = rig.engine.s.extras
    assert (x.chal_used, x.chal_won, x.timeouts) == ([1, 0], [0, 0], [2, 3])
    assert rig.rules.review.pending.wrong is True


def test_answering_no_at_the_question_costs_nothing_and_the_challenge_stays_possible(tmp_path):
    rig = line_scene(tmp_path, WRONG(), answers=["c", ENTER, ENTER, "c", ESCAPE])
    at_the_menu(rig)
    mark = len(rig.said)
    assert the_menu(rig, Draws()) == "concede"
    spoken = texts(rig, mark)
    assert spoken.count(" Kim do you wish to challenge the ruling that " + LINE_SHORT + "? ") == 1      # asked once: Enter is no
    assert X.text("NXR-04") not in spoken
    assert spoken[5:9] == [NO, SELECT, " 1. Line Plunge ", " 8. Challenge the Ruling "]    # the menu starts again, the item is there
    x = rig.engine.s.extras
    assert (x.chal_used, x.timeouts) == ([0, 0], [3, 3]) and rig.rules.review.pending.challenged is False


def test_the_keys_at_the_question_are_up_down_y_n_enter_and_f1_and_any_other_key_asks_again_with_the_answer_kept(tmp_path):
    rig = line_scene(tmp_path, WRONG(), answers=["c", ENTER, DOWN, "x", F1, UP, "y", "n", ENTER, ESCAPE])
    at_the_menu(rig)
    mark = len(rig.said)
    assert the_menu(rig, Draws()) == "concede"
    spoken = texts(rig, mark)
    question = " Kim do you wish to challenge the ruling that " + LINE_SHORT + "? "
    assert spoken.count(question) == 3                                                 # at the start, after x, after F1
    first = spoken.index(question)
    answers = [t for t in spoken[first:] if t in (NO, YES)]
    assert answers == [NO, YES, YES, YES, NO, YES, NO]    # no; Down: yes; x asks again (yes kept); F1 again; Up: no; y; n
    assert rig.engine.s.extras.chal_used == [0, 0]


@pytest.mark.parametrize("n, m, status", [(2, 3, "NXR-02"), (1, 3, "NXR-17"), (2, 1, "NXR-18"), (1, 1, "NXR-19")])
def test_the_question_says_one_challenge_and_one_time_out_in_the_singular(tmp_path, n, m, status):
    """A team with one challenge used and none won has 1 left; with 2 used and one won has 1 (the third)."""
    used, won = (0, 0) if n == 2 else (1, 0)
    rig = line_scene(tmp_path, WRONG(), answers=["c", ENTER, ENTER, ESCAPE],
                     extras={"chal_used": [used, 0], "chal_won": [won, 0], "timeouts": [m, 3]})
    at_the_menu(rig)
    mark = len(rig.said)
    the_menu(rig, Draws())
    assert X.text(status, n=n, m=m) in texts(rig, mark)
