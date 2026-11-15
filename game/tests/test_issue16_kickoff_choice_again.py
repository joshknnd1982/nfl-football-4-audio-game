"""GitHub issue 16 (D-230): a time out the player calls by T after he chose his kick-off and before the kick withdraws the kick he chose,
and the kick-off menu (or the onside question) is asked again (nfl4 only, rule 0.13; owner rule 0.22, playbook 7.16). This is inspired by
Jim Kitchen.

The tester (1.0.1, JAWS, a franchise game) chose Deep Kick in "choose your kick off", pressed T while "Dominic Zvada is set to kick it off"
was said, the time out was granted, and the deep kick was made with no new choice. His words: "expected result you have the option to pick
the type of kick. actual result it uses the kick you picked before the timeout." A field goal, a punt and the try already went back to their
menu (SZ.6, D-111, D-224, D-225); the kick-off now does too. The computer's kick-off and a kick made again after a foul keep their kick.
"""
from pathlib import Path

import pytest

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import model as M
from nfl4.game import phrases as P
from nfl4.game.pag import PlayWithdrawn
from nfl4.game.rules import CLASSIC, KICKOFF_2026, NORMAL_KICKOFF, ONSIDE_KICKOFF
from pagrig import Draws
from test_nx_tkey import ENTER, T_KEY, called, check, press_t_at, scene, script, texts

KICKING = dict(wisoff=2, defense=1, half=1, yard_line=0, quarter=1)
QUIET = dict(left=900, pending=0, running=False)
OUT = " time out called by the Bengals. "


def rules_2026():
    return NflRules(timeouts_on=True, auto_sides=(2,), onside_on=True, offense_book="west", defense_book="pressure")


def rules_onside_question():
    return NflRules(timeouts_on=True, auto_sides=(2,), onside_on=True, onside_always=True)


def menu_prompt():
    return X.text("NXB-J01", coach="Kim")


def back_deep(rig) -> str:
    engine = rig.engine
    return " " + engine.returner(2, 1) + P.AND + engine.returner(2, 2) + P.KICKOFF_BACK_DEEP


def given_touchback(rig):
    rig.rules.kickoff_result = lambda *a: M.KickResult("touchback", 35)


def test_the_testers_moment_deep_kick_chosen_t_in_the_set_up_and_the_menu_comes_again(tmp_path):
    """Deep Kick (Enter), T in the set-up: the time out is called, the deep kick is withdrawn, the menu comes again; 2 and Enter: the short
    kick is made. Who is back deep is said once (SZ.6); the kicker's sentence comes again before the new kick."""
    rig = scene(tmp_path, answers=[ENTER, "2", ENTER], rules=rules_2026(), extras=dict(QUIET), **KICKING)
    engine = rig.engine
    script(rig, Draws())
    press_t_at(rig, "dy", 1)                                    # the pause after who is back deep: before " ... is set to kick it off "
    step = engine.kick_off()
    assert step == engine.kickoff_2026 and engine.s.extras.kick_call == "K001"
    assert engine.t_back == engine.kickoff_again
    with pytest.raises(PlayWithdrawn) as caught:
        step()
    assert caught.value.back == engine.kickoff_again and called(rig) == [1, 0]
    step = engine.withdrawn(caught.value)
    assert step == engine.kickoff_again
    step = step()
    assert step == engine.kickoff_2026 and engine.s.extras.kick_call == "K002"     # the short kick he chose the second time
    check(rig, Draws())
    said = texts(rig)
    first, again = said.index(menu_prompt()), len(said) - 1 - said[::-1].index(menu_prompt())
    assert first < said.index(OUT) < again                     # the menu, the time out, the menu again
    assert said[again:] == [menu_prompt(), " 1. Deep Kick ", " 2. Short Kick "]
    given_touchback(rig)
    rig.rnd.source = __import__("random").Random(5)
    mark = len(rig.said)
    step()
    later = texts(rig, mark)
    assert back_deep(rig) not in later and texts(rig).count(back_deep(rig)) == 1  # SZ.6: who is back deep is not said twice
    assert any("set to kick it off" in t or P.READY_TO_KICK_OFF in t for t in later)
    assert P.KICKOFF_UP not in later                             # the short kick's sentence, not the deep kick's
    assert called(rig) == [1, 0]                                # one time out, the kick was made


def test_the_onside_kick_chosen_and_withdrawn_is_not_counted_and_the_deep_kick_can_be_chosen_instead(tmp_path):
    rig = scene(tmp_path, answers=["4", ENTER, ENTER], rules=rules_2026(), extras=dict(QUIET), **KICKING)
    engine = rig.engine
    script(rig, Draws())
    step = engine.kick_off()
    assert step == engine.onside_kick and engine.t_back == engine.kickoff_again
    say4 = rig.game.say4

    def post_t(text, *args, **kwargs):                         # T while the onside line-up is said, before the kick is made
        if text == X.text("NXO-03", receiving_team="Jets"):
            rig.keys.post(T_KEY)
            rig.keys.post_char("t")
        return say4(text, *args, **kwargs)
    rig.game.say4 = post_t
    with pytest.raises(PlayWithdrawn) as caught:
        step()
    rig.game.say4 = say4
    assert caught.value.back == engine.kickoff_again and called(rig) == [1, 0]
    assert engine.s.extras.onside_tried == [0, 0]               # a kick withdrawn was never tried
    step = engine.withdrawn(caught.value)()
    assert step == engine.kickoff_2026 and engine.s.extras.kick_call == "K001" and engine.s.extras.kick_kind == NORMAL_KICKOFF
    check(rig, Draws())


def test_the_onside_question_is_asked_again_after_a_time_out_with_the_classic_playbook(tmp_path):
    """SX.4's question (no 2026 kicks): "no" (Enter), T in the set-up, the question again, "y" and Enter: the onside kick."""
    rig = scene(tmp_path, answers=[ENTER, "y", ENTER], rules=rules_onside_question(), extras=dict(QUIET), **KICKING)
    engine = rig.engine
    script(rig, Draws())
    press_t_at(rig, "dy", 1)
    with pytest.raises(PlayWithdrawn) as caught:
        engine.kick_off()
    assert caught.value.back == engine.kickoff_again and called(rig) == [1, 0]
    step = engine.withdrawn(caught.value)()
    assert step == engine.onside_kick and engine.s.extras.kick_kind == ONSIDE_KICKOFF
    question = " Kim do you wish to try an onside kick "
    assert texts(rig).count(question) == 2
    check(rig, Draws())


def test_the_safety_kick_asked_again_still_offers_the_safety_punt_from_the_20(tmp_path):
    rig = scene(tmp_path, answers=["5", ENTER, "5", ENTER], rules=rules_2026(), extras=dict(QUIET, safety_kick=True), **KICKING)
    engine, x = rig.engine, rig.engine.s.extras
    script(rig, Draws())
    assert rig.rules.before_kickoff(engine.s, 1) == KICKOFF_2026 and x.kick_call == "K027" and x.kick_from == 20
    assert rig.rules.kickoff_again(engine.s, 1) == KICKOFF_2026 and x.kick_call == "K027" and x.kick_from == 20
    check(rig, Draws())


def test_no_choice_asked_no_choice_again_the_computers_kick_a_kick_made_again_and_classic(tmp_path):
    rig = scene(tmp_path, rules=rules_2026(), extras=dict(QUIET), **dict(KICKING, wisoff=1, defense=2))
    rig.rnd.source = __import__("random").Random(1)
    rig.rules.before_kickoff(rig.engine.s, 2)                   # the computer's kick: no menu
    assert not rig.rules.kickoff_chosen(rig.engine.s)
    mine = scene(tmp_path / "again", answers=[ENTER], rules=rules_2026(), extras=dict(QUIET), **KICKING)
    script(mine, Draws())
    mine.rules.before_kickoff(mine.engine.s, 1)
    assert mine.rules.kickoff_chosen(mine.engine.s)
    mine.engine.s.extras.kick_again = True                      # a foul: the kick is made again with its call, nothing asked
    mine.rules.before_kickoff(mine.engine.s, 1)
    assert not mine.rules.kickoff_chosen(mine.engine.s)
    off = scene(tmp_path / "off", answers=[ENTER], rules=NflRules(timeouts_on=False, auto_sides=(2,), offense_book="west",
                                                                   defense_book="pressure"), extras=dict(QUIET), **KICKING)
    script(off, Draws())
    off.rules.before_kickoff(off.engine.s, 1)
    assert not off.rules.kickoff_chosen(off.engine.s)            # no timeouts in this game: nothing to ask again for
    assert CLASSIC.kickoff_chosen(off.engine.s) is False


def test_the_computers_kick_off_still_goes_on_after_the_players_time_out(tmp_path):
    """The player receives: his time out in the set-up is granted and the computer's kick is made as it was (its draws do not change)."""
    rig = scene(tmp_path, rules=rules_2026(), extras=dict(QUIET), **dict(KICKING, wisoff=1, defense=2))
    engine = rig.engine
    rig.rnd.source = __import__("random").Random(2)
    step = engine.kick_off()
    call = engine.s.extras.kick_call
    assert engine.t_back is None
    press_t_at(rig, "dy", 1)
    given_touchback(rig)
    step()                                                     # no PlayWithdrawn: the kick goes on
    assert called(rig) == [1, 0] and engine.s.extras.kick_call == call


def test_the_log_says_the_kick_was_withdrawn_and_chosen_again(tmp_path):
    """The lines that would have shown the bug: play_withdrawn back=kickoff_again, and kickoff_again with the new kick."""
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig", answers=[ENTER, "3", ENTER], rules=rules_2026(), extras=dict(QUIET), **KICKING)
    engine = rig.engine
    script(rig, Draws())
    press_t_at(rig, "dy", 1)
    step = engine.kick_off()
    with pytest.raises(PlayWithdrawn) as caught:
        step()
    engine.withdrawn(caught.value)()
    debuglog.flush(30)
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    withdrawn = [line for line in lines if " play_withdrawn " in line]
    again = [line for line in lines if " kickoff_again " in line]
    assert len(withdrawn) == 1 and "back=kickoff_again" in withdrawn[0]
    assert len(again) == 1 and "call=K003" in again[0] and "spot=35" in again[0]


def test_a_second_t_before_the_same_kick_is_refused_and_the_kick_goes_on(tmp_path):
    """One time out per team in one dead-ball period (NFL 4-5-1, SX.13): the kick chosen again is made after a refused second T."""
    rig = scene(tmp_path, answers=[ENTER, "3", ENTER], rules=rules_2026(), extras=dict(QUIET), **KICKING)
    engine = rig.engine
    script(rig, Draws())
    press_t_at(rig, "dy", 1)
    step = engine.kick_off()
    with pytest.raises(PlayWithdrawn) as caught:
        step()
    step = engine.withdrawn(caught.value)()
    assert step == engine.kickoff_2026 and engine.s.extras.kick_call == "K003"
    press_t_at(rig, "dy", 1)                                   # the pause of the new set-up (a new count): the second T
    given_touchback(rig)
    rig.rnd.source = __import__("random").Random(4)
    step()                                                     # no PlayWithdrawn: refused, the squib kick is made
    assert called(rig) == [1, 0] and X.text("NXT-05") in texts(rig)
