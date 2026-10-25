"""SX.14 (CLAUDE.md 0.23, playbook 7.17, NX-S4 to NX-S6): Save Game asks for a place and then whether to quit or keep playing, and the play menu
writes the automatic save. This is inspired by Jim Kitchen.

The engine is in the middle of a game at its play menu (tests/pagrig.py); the save questions are the program's `SaveUi` over a memory store.
Enter at every question does what the original did: the game is saved (in slot 1) and the program ends.
"""
import json

from nfl4.game import save_texts as S
from nfl4.game.program_store import MemoryProgramStore
from nfl4.game.save_menu import SaveUi
from pagrig import Draws, engine_rig, run_steps, texts
from savesrig import a_saved

ENTER, ESCAPE, UP, DOWN = 13, 27, 38, 40


class FakeProgram:
    def __init__(self, rig):
        self.g = rig.game
        self.store = MemoryProgramStore()
        self.slot_in_use = None


def save_rig(tmp_path, answers, **state):
    fields = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=2, counter=9)
    fields.update(state)
    rig = engine_rig(tmp_path, answers=answers, **fields)
    rig.program = FakeProgram(rig)
    rig.engine.save_ui = SaveUi(rig.program)
    rig.engine.save_sink = rig.program.store.save_game
    rig.engine.autosave_sink = rig.program.store.autosave
    rig.engine.game_on = True
    return rig


def go(rig, until=("never",)):
    return run_steps(rig, rig.engine.offense_menu, Draws(), until=until)


def test_enter_at_every_question_saves_in_slot_one_and_quits_as_the_original_did(tmp_path):
    rig = save_rig(tmp_path, [UP, ENTER, ENTER, ENTER])
    assert go(rig) is None
    spoken = texts(rig)
    assert S.SLOT_QUESTION in spoken and " Game Saved " in spoken and (S.SAVED_IN_SLOT % 1 + S.QUIT_OR_KEEP) in spoken
    assert rig.engine.result.saved and list(rig.program.store.shelf.slots) == [1]
    record = rig.program.store.shelf.slots[1].saved
    info = json.loads(record.info)
    assert (info["own"], info["opp"], info["week"], record.quarter, record.counter) == ("Bengals", "Jets", 1, 2, 9)
    assert record.resume is None                                      # a saved game by hand is not a replay of the draws


def test_keep_playing_goes_back_to_the_same_play_menu_and_the_game_is_not_over(tmp_path):
    rig = save_rig(tmp_path, [UP, ENTER, ENTER, DOWN, ENTER, ENTER])
    assert go(rig, until=("offense_chosen",)) == "offense_chosen"
    assert not rig.engine.result.saved and rig.engine.game_on and 1 in rig.program.store.shelf.slots
    assert rig.program.slot_in_use == 1
    spoken = texts(rig)
    assert spoken.count(" Kim select the play for your off fence ") == 2


def test_the_places_name_what_they_hold_and_the_games_own_place_is_first(tmp_path):
    rig = save_rig(tmp_path, [UP, ENTER, ENTER, ENTER])
    rig.program.store.shelf.write_slot(2, a_saved(own=3))
    rig.program.slot_in_use = 2
    go(rig)
    spoken = texts(rig)
    first = next(t for t in spoken if t.startswith(" 1. slot 2, holds"))
    assert S.SLOT_CURRENT in first and "Bengals and Jets" in first
    assert list(rig.program.store.shelf.slots) == [2] and rig.engine.result.saved           # Enter on the game's own place replaced it without a question


def test_another_games_place_is_replaced_only_after_a_yes(tmp_path):
    rig = save_rig(tmp_path, [UP, ENTER, "3", ENTER, ENTER, ESCAPE, ENTER])             # slot 3 (all are full): no (Enter), the places again, Escape
    rig.program.store.shelf.write_slot(1, a_saved(own=3))
    rig.program.store.shelf.write_slot(3, a_saved(own=5))
    rig.program.store.shelf.write_slot(2, a_saved(own=4))
    go_to = go(rig, until=("offense_chosen",))
    assert go_to == "offense_chosen"
    assert S.SLOT_REPLACE_QUESTION % 3 in texts(rig) and S.SAVE_CANCELLED in texts(rig)
    assert {slot: entry.saved.stats[1].score for slot, entry in rig.program.store.shelf.slots.items()} == {1: 3, 2: 4, 3: 5}


def test_a_yes_replaces_the_other_game(tmp_path):
    rig = save_rig(tmp_path, [UP, ENTER, "3", ENTER, "y", ENTER])
    rig.engine.s.stats[1].score = 99
    rig.program.store.shelf.write_slot(1, a_saved(own=3))
    rig.program.store.shelf.write_slot(2, a_saved(own=4))
    rig.program.store.shelf.write_slot(3, a_saved(own=5))
    go(rig)
    assert rig.program.store.shelf.slots[3].saved.stats[1].score == 99 and rig.engine.result.saved
    assert rig.program.store.shelf.slots[1].saved.stats[1].score == 3


def test_escape_at_the_places_saves_nothing_and_the_game_goes_on(tmp_path):
    rig = save_rig(tmp_path, [UP, ENTER, ESCAPE, ENTER])
    assert go(rig, until=("offense_chosen",)) == "offense_chosen"
    assert rig.program.store.shelf.slots == {} and not rig.engine.result.saved and rig.engine.game_on
    assert S.SAVE_CANCELLED in texts(rig)


def test_the_play_menu_writes_the_automatic_save_whole_with_the_summary_and_the_resume_state(tmp_path):
    rig = save_rig(tmp_path, [ENTER])
    run_steps(rig, rig.engine.play_menu, Draws(), until=("offense_chosen",))
    auto = rig.program.store.shelf.auto
    assert auto is not None and auto.info["auto"] is True and auto.saved.quarter == 2
    assert json.loads(auto.saved.resume)["v"] == 1 and json.loads(auto.saved.info)["opp"] == "Jets"
    assert rig.rnd.draws == 0                                         # the save drew no number


def test_no_automatic_save_before_the_game_is_on_or_when_the_sink_fails(tmp_path):
    rig = save_rig(tmp_path, [ENTER])
    rig.engine.game_on = False
    run_steps(rig, rig.engine.play_menu, Draws(), until=("offense_chosen",))
    assert rig.program.store.shelf.auto is None
    broken = save_rig(tmp_path / "b", [ENTER])
    broken.engine.autosave_sink = lambda record: 1 / 0
    assert run_steps(broken, broken.engine.play_menu, Draws(), until=("offense_chosen",)) == "offense_chosen"      # the game is never stopped for it
