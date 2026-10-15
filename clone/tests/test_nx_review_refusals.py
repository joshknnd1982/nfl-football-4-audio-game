"""Why a coach may not challenge, the limits of 15-1-1 and the letter C at the play menu (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN
6.4; NFL_RULES_RESEARCH Part 3; PX SX.6). This is inspired by Jim Kitchen.

The item "Challenge the Ruling" is in the menu only while a challenge is allowed; the letter C without the item says why not
(NXR-10 to NXR-15) and the menu goes on at the same item. Every expected reason is worked out from the rule it names.
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import review as RV
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from test_nx_review_plays import ENTER, FUMBLE, RUN, TD, rule, scene, texts

ESCAPE = 27
MENU_UNTIL = ("next_play", "play_menu", "kick_off", "finish", "concede", "offense_chosen", "defense_chosen", "save_game")
SELECT = " Kim" + P.SELECT_OFFENSE


def ruled_plain(tmp_path, kind=RUN, **kwargs):
    """A scene whose play was ruled plain (the draw 999 is past every window): the ruling exists, nothing happens."""
    kwargs.setdefault("yards", 4)
    if kind == RUN:
        kwargs.setdefault("down", 3)
        kwargs.setdefault("to_go", 5)
    rig, record = scene(tmp_path, kind, **kwargs)
    assert rule(rig, record, Draws().below(1000, 999)) is None
    return rig


def say_c(rig):
    mark = len(rig.said)
    assert rig.rules.menu_key(rig.engine.s, "c") is True
    return texts(rig, mark)


def the_menu(rig):
    return run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)


@pytest.mark.parametrize("why, text_id, kwargs", [
    ("overtime", "NXR-13", dict(quarter=5)),
    ("warning", "NXR-12", dict(quarter=2, extras={"warning_given": True, "period": 2})),
    ("none left", "NXR-10", dict(extras={"chal_used": [2, 0]})),
    ("no timeout", "NXR-11", dict(extras={"timeouts": [0, 3]}))])
def test_the_letter_c_says_why_there_is_no_challenge(tmp_path, why, text_id, kwargs):
    rig = ruled_plain(tmp_path, **kwargs)
    s = rig.engine.s
    assert rig.rules.review.refusal(s, 1) == why
    assert RV.REASON_TEXTS[why] == text_id
    assert say_c(rig) == [X.text(text_id)]
    assert not [i for i in rig.rules.offense_menu(s, False) if i.letter == "c"]       # and the menu has no such item


def test_overtime_comes_before_the_warning_in_the_reasons(tmp_path):
    rig = ruled_plain(tmp_path, quarter=5, extras={"warning_given": True, "period": 5})
    assert rig.rules.review.refusal(rig.engine.s, 1) == "overtime"


@pytest.mark.parametrize("kind, kwargs", [(TD, dict(yards=5, spot=(1, 5), down=1, to_go=5)), (FUMBLE, dict()),
                                          (RUN, dict(yards=4, down=4, to_go=5))])
def test_a_score_a_turnover_or_a_failed_fourth_down_is_the_replay_officials_and_the_letter_c_says_so(tmp_path, kind, kwargs):
    rig = ruled_plain(tmp_path, kind, **kwargs)
    assert rig.rules.review.refusal(rig.engine.s, 1) == "booth"
    assert say_c(rig) == [X.text("NXR-14")]


def test_with_no_ruling_a_stale_ruling_another_quarter_or_a_play_already_reviewed_there_is_nothing_to_challenge(tmp_path):
    rig, record = scene(tmp_path / "none", O.SACK, yards=-6)
    assert rule(rig, record, Draws()) is None
    assert say_c(rig) == [X.text("NXR-15")]
    rig = ruled_plain(tmp_path / "stale")
    assert rig.rules.review.refusal(rig.engine.s, 1) is None
    rig.engine.s.extras.plays += 1                                   # a play, a try or a foul before the snap has ended since
    assert say_c(rig) == [X.text("NXR-15")]
    rig = ruled_plain(tmp_path / "quarter")
    rig.engine.s.quarter = 2
    assert say_c(rig) == [X.text("NXR-15")]
    rig = ruled_plain(tmp_path / "reviewed")
    rig.rules.review.pending.challenged = True
    assert say_c(rig) == [X.text("NXR-15")]


def test_another_letter_is_echoed_as_before_and_a_game_with_challenges_off_has_no_item_and_no_reason(tmp_path):
    rig = ruled_plain(tmp_path)
    s = rig.engine.s
    mark = len(rig.said)
    assert rig.rules.menu_key(s, "x") is False and rig.rules.menu_key(s, "") is False
    assert texts(rig, mark) == []
    off = nfl_engine_rig(tmp_path / "off", rules=NflRules(timeouts_on=False), wisoff=1, defense=2, down=3, to_go=5)
    assert [i.text for i in off.rules.offense_menu(off.engine.s, False)] == [
        " 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass ", " 6. Field Goal ",
        " 7. Punt ", " 8. Save Game "]
    assert off.rules.menu_key(off.engine.s, "c") is False


def test_the_letter_c_in_the_menu_loop_says_why_and_the_menu_goes_on_at_the_same_item(tmp_path):
    rig = ruled_plain(tmp_path, quarter=5, answers=["c", ESCAPE])
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    assert texts(rig, mark) == [SELECT, " 1. Line Plunge ", X.text("NXR-13"), " 1. Line Plunge "]


def test_the_two_point_try_menu_has_no_challenge_item_and_c_at_0_00_says_the_reason_and_breaks_nothing(tmp_path):
    """The try after a touchdown is untimed: the menu is the original's items 1 to 5. The clock says 0:00 in the second quarter,
    after the warning (B-X34: every answer a prompt offers at 0:00 of a half): the reason is the warning's (15-1-2 (a))."""
    rig = ruled_plain(tmp_path, TD, yards=5, spot=(1, 5), down=1, to_go=5, quarter=2, two_point=True,
                      extras={"left": 0, "warning_given": True, "period": 2}, answers=["c", ESCAPE])
    assert [i.text for i in rig.rules.offense_menu(rig.engine.s, True)] == [
        " 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass "]
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    assert texts(rig, mark) == [SELECT, " 1. Line Plunge ", X.text("NXR-12"), " 1. Line Plunge "]
    rig.engine.s.extras.check()


@pytest.mark.parametrize("used, won, timeouts, allowed", [
    (0, 0, 3, True), (1, 0, 3, True), (2, 0, 3, False),                # two challenges, no third without a success
    (2, 1, 3, True), (3, 1, 3, False),                                 # a third after one success, never a fourth
    (2, 2, 3, True), (3, 3, 3, False),                                 # both won: the third, not a fourth
    (0, 0, 0, False), (2, 1, 0, False), (1, 0, 1, True)])             # a time out must be in hand
def test_two_challenges_a_game_a_third_after_a_success_and_a_time_out_in_hand(tmp_path, used, won, timeouts, allowed):
    """15-1-1 (d) to (f): the item is in the menu only for a team with a challenge left and a time out in hand."""
    rig = ruled_plain(tmp_path, extras={"chal_used": [used, 0], "chal_won": [won, 0], "timeouts": [timeouts, 3]})
    s = rig.engine.s
    assert bool([i for i in rig.rules.offense_menu(s, False) if i.letter == "c"]) is allowed
    assert rig.rules.review.can_challenge(s, 1) is allowed
    assert rig.rules.review.refusal(s, 1) == (None if allowed else ("none left" if timeouts else "no timeout"))


def test_a_third_challenge_after_a_success_is_asked_with_one_challenge_left(tmp_path):
    rig = ruled_plain(tmp_path, answers=["c", ENTER, ENTER, ESCAPE], extras={"chal_used": [2, 0], "chal_won": [1, 0]})
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    assert X.text("NXR-17", m=3) in texts(rig, mark)
