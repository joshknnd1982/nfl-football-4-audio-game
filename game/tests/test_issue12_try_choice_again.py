"""GitHub issue 12 (D-225): after a penalty or a timeout on the player's two-point try, the choice of the kick or the two-point try is asked
again (nfl4 only, rule 0.13; NFL 2026 rule 11-3-1, SRC-OFFICIAL). This is inspired by Jim Kitchen.

The tester (0.16.23, JAWS) chose the two-point try; the Packers' illegal shift flag on his successful sneak was accepted, the referee said
"the try will be played again from the 7 yard line", and the game went straight to the play menu. A timeout before the snap of the try did
the same. Rule 11-3-1: "the offensive team may change its choice ... if there is a penalty or charged timeout by either team." Now both go
back to the choice, which starts on the two-point try (Enter keeps it, from the spot the penalty set); Up or Down gives the kick. The
computer's own try that a penalty makes it play again goes to the player's defense menu (before, the player's offense menu came).
"""
from pathlib import Path

import pytest

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.game import phrases as P
from nfl4.game.pag import PlayWithdrawn
from nfl4.game.rules import TRY_AGAIN
from pagrig import Draws
from test_nx_penalties import game, script as pen_script, check as pen_check, value_of
from test_nx_penalty_review import DEAD
from test_nx_tkey import ENTER, OUT, UP, called, drive, press_t_at, scene, script, check, texts

CHOICE = "extra_point_choice"


def test_the_testers_moment_a_penalty_on_the_two_point_try_asks_the_choice_again(tmp_path):
    """The try is played again after an accepted foul: the next step is the choice, not the play menu; Enter keeps the two-point try
    from the spot the penalty set (the 7)."""
    rig = game(tmp_path, answers=[ENTER], half=1, yard_line=2, two_point=True, offense_play=1, defense_play=2)
    draws = Draws().below(10000, value_of(rig, DEAD, "P01")).rnd(12, 1).rnd(4, 1).rnd(10, 1)
    pen_script(rig, draws)
    engine = rig.engine
    step = engine.snap()
    pen_check(rig, draws)
    assert step == engine.try_again and engine.s.yard_line == 7 and engine.s.two_point
    assert step() == engine.extra_point_choice
    start = len(rig.said)
    assert engine.extra_point_choice() == engine.offense_menu
    said = [t for t, _, _ in rig.said[start:]]
    assert said[:2] == [" " + engine.coach + P.SELECT, P.TRY_FOR_TWO]          # the choice starts on the try he had chosen
    assert engine.s.two_point and engine.s.yard_line == 7                      # the spot the penalty set, not the 2 again


def test_after_a_penalty_the_player_may_kick_instead(tmp_path):
    rig = scene(tmp_path, answers=[UP, ENTER], two_point=True, yard_line=7, extras=dict(pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    engine.s.try_good = True
    assert engine.extra_point_choice() == engine.extra_point
    said = texts(rig)
    assert said[:3] == [" Kim" + P.SELECT, P.TRY_FOR_TWO, P.KICK_FOR_EXTRA_POINT]
    assert not engine.s.two_point and not engine.s.try_good
    assert engine.t_back == engine.extra_point_choice                         # a timeout before that kick asks the choice again too
    assert rig.rules.try_due                                                   # the try's down is still to come (SX.13)


def test_the_continuation_of_a_try_played_again_is_the_choice_for_the_player_and_the_defense_menu_for_the_computer(tmp_path):
    rig = game(tmp_path, two_point=True, yard_line=7)
    engine = rig.engine
    assert engine.continuation(TRY_AGAIN) == engine.try_again
    assert engine.try_again() == engine.extra_point_choice
    other = game(tmp_path / "computer", wisoff=2, defense=1, two_point=True, yard_line=7)
    assert other.engine.try_again() == other.engine.defense_menu


def test_t_in_the_two_point_menu_goes_back_to_the_choice(tmp_path):
    rig = scene(tmp_path, answers=["t", UP, ENTER], two_point=True, yard_line=2, extras=dict(pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    engine.t_choice = (5, 2)                                                   # left over from the touchdown's play: never restored
    engine.s.previous_play, engine.s.repeats = 1, 0
    step, names = drive(engine, engine.offense_menu, stop=(CHOICE,))
    assert names == ["offense_menu", "withdrawn"] and step == engine.extra_point_choice
    assert (engine.s.previous_play, engine.s.repeats) == (1, 0)
    assert step() == engine.extra_point                                        # Up: the kick
    said = texts(rig)
    assert OUT in said and said[-3:] == [" Kim" + P.SELECT, P.TRY_FOR_TWO, P.KICK_FOR_EXTRA_POINT]
    assert called(rig) == [1, 0] and not engine.s.two_point


def test_t_in_the_snap_count_of_the_two_point_try_goes_back_to_the_choice(tmp_path):
    rig = scene(tmp_path, offense_play=1, defense_play=1, two_point=True, yard_line=2, extras=dict(pending=0, running=False))
    draws = Draws().rnd(4, 1).rnd(10, 1)                                       # the huddle is said, the pause before " hut 1 "
    script(rig, draws)
    press_t_at(rig, "dy", 1)
    engine = rig.engine
    with pytest.raises(PlayWithdrawn) as caught:
        engine.snap()
    check(rig, draws)
    assert caught.value.back == engine.extra_point_choice and called(rig) == [1, 0]
    assert P.HIKE not in texts(rig)


def test_a_timeout_at_0_00_after_the_kick_was_chosen_instead_is_still_granted(tmp_path):
    """The touchdown came as the half ran out; the try's down is still to come whichever try is chosen (SX.13, 4-5-1)."""
    rig = scene(tmp_path, answers=[UP, ENTER], two_point=True, yard_line=7, extras=dict(left=0, pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    rig.rules.try_due = False                                                  # the two-point snap had ended the dead-ball period
    assert engine.extra_point_choice() == engine.extra_point and not engine.s.two_point
    draws = Draws().rady()
    script(rig, draws)
    press_t_at(rig, "rady", 1)
    with pytest.raises(PlayWithdrawn) as caught:
        engine.extra_point()
    assert caught.value.back == engine.extra_point_choice and called(rig) == [1, 0]
    assert X.text("NXT-16") not in texts(rig)


def test_the_first_choice_after_a_touchdown_is_unchanged(tmp_path):
    """No penalty, no timeout: the kick first, and the two-point try from the 2, as the original."""
    rig = scene(tmp_path, answers=[UP, ENTER], yard_line=30, extras=dict(pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    assert engine.extra_point_choice() == engine.offense_menu
    assert texts(rig)[:3] == [" Kim" + P.SELECT, P.KICK_FOR_EXTRA_POINT, P.TRY_FOR_TWO]
    assert engine.s.two_point and engine.s.yard_line == 2


def test_the_log_says_the_try_was_played_again_and_what_was_chosen(tmp_path):
    """The lines that would have shown the bug: try_again when a penalty makes the try be played again, try_choice_again with the
    choice and the spot."""
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig", answers=[ENTER], two_point=True, yard_line=7, extras=dict(pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    assert engine.continuation(TRY_AGAIN)() == engine.extra_point_choice
    engine.extra_point_choice()
    debuglog.flush(30)
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    again = [line for line in lines if " try_again " in line]
    chosen = [line for line in lines if "try_choice_again" in line]
    assert len(again) == 1 and "yard_line=7" in again[0]
    assert len(chosen) == 1 and "choice=two" in chosen[0] and "yard_line=7" in chosen[0]
