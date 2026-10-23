"""The play menus' W key under stress (S8.3 round 2; nfl4 only, rule 0.13; SZ.7, D-112). This is inspired by Jim Kitchen.

W says which play the playbook would most likely call and draws nothing (test_sz7_likely_key.py). Here: W pressed hundreds of times while every
voice fails, W next to the T key's timeout, and W with a playbook the files no longer have. Nothing raises, nothing is drawn (the rig's source is
strict and empty), the menu still takes its key, and no sentence is said twice in a row that the player did not ask for twice (rule 0.28 (3)).
"""
import pytest
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from test_sz7_likely_key import DEFENSE, ESCAPE, MENU_UNTIL, OFFENSE, W_SENTENCE, first_w, menu, rig_for, texts

from nfl4.extras import playbooks as PB
from nfl4.extras.nfl_rules import NflRules


def all_items(rig, defense):
    state = rig.engine.s
    return list(rig.rules.defense_menu(state) if defense else rig.rules.offense_menu(state, False))


@pytest.mark.parametrize("defense", [False, True])
def test_w_on_every_item_while_every_voice_fails_never_raises_and_draws_nothing(tmp_path, defense):
    rules = NflRules(timeouts_on=False, qb_on=True, offense_book="pro", defense_book="pro")
    rig = rig_for(tmp_path, [ESCAPE], rules=rules, **(DEFENSE if defense else OFFENSE))
    rig.sapi.fail_speak = True
    rig.nvda.available = False
    state = rig.engine.s
    for _ in range(20):
        for item in all_items(rig, defense):
            assert rig.rules.menu_key(state, "w", item) is True


def test_two_hundred_w_presses_then_escape_leave_the_menu_as_it_was(tmp_path):
    rig = rig_for(tmp_path, ["w"] * 200 + [ESCAPE], **OFFENSE)
    mark = len(rig.said)
    menu(rig)
    said = first_w(rig, mark)
    assert len(said) == 200 and len(set(said)) == 1                                   # each press says it once, the same each time


@pytest.mark.parametrize("missing", ["offense", "defense", "both"])
def test_w_with_a_playbook_the_files_no_longer_have_says_something_and_never_raises(tmp_path, missing):
    books = {"offense": ("no such style", "pro"), "defense": ("pro", "no such style"), "both": ("no such style", "no such style")}[missing]
    rules = NflRules(timeouts_on=False, offense_book=books[0], defense_book=books[1])
    for defense in (False, True):
        rig = rig_for(tmp_path / ("d" if defense else "o"), [ESCAPE], rules=rules, **(DEFENSE if defense else OFFENSE))
        mark = len(rig.said)
        for item in all_items(rig, defense):
            assert rig.rules.menu_key(rig.engine.s, "w", item) is True
        assert texts(rig, mark), "W said nothing at all"


def test_w_then_t_then_w_calls_the_timeout_once_and_says_no_sentence_twice_by_itself(tmp_path):
    rules = NflRules(timeouts_on=True, offense_book="pro", defense_book="pro")
    rig = nfl_engine_rig(tmp_path, answers=["w", "t", "w", ESCAPE], rules=rules, extras=dict(left=500, pending=0, running=False), **OFFENSE)
    rig.game.options.settings.game.nx_menu_hints = 3
    mark = len(rig.said)
    run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)
    said = texts(rig, mark)
    x = rig.engine.s.extras
    assert x.called[0] is True and x.timeouts[0] == 2                                  # one timeout, charged once
    assert sum(1 for t in said if "time out called by" in t) == 1
    w = [t for t in said if W_SENTENCE.match(t)]
    assert len(w) == 2                                                                 # W before and W after: two presses, two sentences
    for before, after in zip(said, said[1:]):
        if before == after:
            assert W_SENTENCE.match(before) is None or said.count(before) == 2, before
