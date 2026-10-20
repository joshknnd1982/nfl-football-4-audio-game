"""SX.14 (CLAUDE.md 0.23, playbook 7.17, NX-S1 to NX-S8, D-086): the start-up choice. This is inspired by Jim Kitchen.

After the welcome, when anything is saved the program says one sentence about each save and asks what to do; the first item is what the
original did, so Enter alone does it; nothing is loaded, deleted or replaced without a key; a delete asks again (starting at no) and moves the
file to the backup, a restore brings it back; the save is kept until its game ends; a damaged or old save is named and never touched.
"""
import pytest

from nfl4.data.files.shelf import Entry
from nfl4.game import program_texts as P
from nfl4.game import prompt_texts as T
from nfl4.game import save_texts as S
from programrig import said
from savesrig import (DOWN, ENTER, EXIT, a_saved, games, menu_rig, played, run_until_a_key_is_missing, saved_game)

SENTENCE_GAME = "You have a saved game: the Bengals lead the Jets 14 to 10 in the third quarter"


def asked(rig):
    return [t for t in said(rig) if t == S.MENU_PROMPT]


def items(rig):
    """The menu items as the player hears them, in the order they were first spoken."""
    heard = []
    for text in said(rig):
        if "This is week" in text:
            break                                                           # the original's main menu begins: its items are not this menu's
        if text.startswith(" ") and text[1:2].isdigit() and text[2:4] == ". " and text not in heard:
            heard.append(text)
    return heard


def item(number, label):
    return " %d. %s " % (number, label)


def damaged_entry(slot=1):
    return Entry("game", slot, "football.sav", "damaged", "the file ends inside a record", None, {}, 5.0)


# ----- NX-S1: the sentences and the first item -----

def test_nothing_saved_and_no_season_asks_nothing_and_the_original_flow_goes_on(tmp_path):
    rig = menu_rig(tmp_path, [], preset=None)
    run_until_a_key_is_missing(rig)
    assert asked(rig) == []
    assert any(T.ENTER_COACH in t for t in said(rig))                    # the original's set-up of a new season


def test_a_season_alone_is_a_question_whose_first_item_continues_it(tmp_path):
    rig = menu_rig(tmp_path, [ENTER] + EXIT)
    rig.run()
    spoken = said(rig)
    assert asked(rig) == [S.MENU_PROMPT]
    assert any(t.startswith(" You have a season in progress: coach Kim of the ") and "week 1, 4 wins and 1 loss" in t for t in spoken)
    assert items(rig)[0] == item(1, S.CONTINUE_SEASON) and rig.plays == []
    assert any(t.startswith(" This is week") for t in spoken) and P.CHOICES[1] in spoken     # then the original's main menu


def test_a_saved_game_is_said_in_one_sentence_and_enter_continues_it(tmp_path):
    rig = menu_rig(tmp_path, [ENTER], outcomes=[saved_game()])
    record = a_saved()
    rig.store.shelf.write_slot(1, record)
    rig.run()
    sentence = next(t for t in said(rig) if t.startswith(" You have a saved game"))
    assert SENTENCE_GAME in sentence and "The Bengals have the ball." in sentence and "It is week 1." in sentence
    assert "about 6 minutes left" in sentence and sentence.rstrip().endswith(".")
    assert items(rig)[0] == item(1, S.CONTINUE_GAME)
    assert rig.plays[0]["saved"] is record                                # Enter alone did what the original did
    assert games(rig) == [(1, 14)]                                         # and the save is still there (it was saved again, not deleted)


def test_the_saved_game_the_original_would_have_played_is_first_with_the_season_after_it(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, ENTER] + EXIT)
    rig.store.shelf.write_slot(1, a_saved())
    rig.run()
    assert items(rig)[:2] == [item(1, S.CONTINUE_GAME), item(2, S.CONTINUE_SEASON)]
    assert rig.plays == [] and games(rig) == [(1, 14)]                       # item 2 (the season) was chosen: the saved game waits, untouched


def test_the_digits_and_f1_work_like_the_originals_menus(tmp_path):
    rig = menu_rig(tmp_path, ["2", 112, ENTER] + EXIT)
    rig.store.shelf.write_slot(1, a_saved())
    rig.run()
    spoken = said(rig)
    sentence = next(t for t in spoken if t.startswith(" You have a saved game"))
    assert spoken.count(sentence) == 2 and spoken.count(S.MENU_PROMPT) == 2        # F1 said it all again, with the item kept
    assert rig.plays == []                                                  # "2" took the season


def test_the_game_that_was_not_finished_is_offered_first_when_it_is_newer_than_the_saved_game(tmp_path):
    rig = menu_rig(tmp_path, [ENTER], outcomes=[saved_game()])
    rig.store.shelf.write_slot(1, a_saved(own=7))
    newer = a_saved(own=21, quarter=4)
    rig.store.shelf.write_auto(newer)
    rig.run()
    spoken = said(rig)
    assert any(t.startswith(" You have a game that was not finished: the Bengals lead the Jets 21 to 10 in the fourth quarter") for t in spoken)
    assert items(rig)[0] == item(1, S.CONTINUE_AUTO) and rig.plays[0]["saved"] is newer


def test_a_saved_game_newer_than_the_automatic_save_is_first(tmp_path):
    rig = menu_rig(tmp_path, [ENTER], outcomes=[saved_game()])
    rig.store.shelf.write_auto(a_saved(own=21))
    chosen = a_saved(own=28)
    rig.store.shelf.write_slot(2, chosen)
    rig.run()
    assert items(rig)[0] == item(1, S.CONTINUE_GAME) and rig.plays[0]["saved"] is chosen


def test_several_saved_games_are_each_a_sentence_and_one_item_opens_the_list(tmp_path):
    rig = menu_rig(tmp_path, ["2", ENTER, ENTER], outcomes=[saved_game()])
    first, second = a_saved(own=7), a_saved(own=35)
    rig.store.shelf.write_slot(1, first)
    rig.store.shelf.write_slot(3, second)
    rig.run()
    spoken = said(rig)
    assert sum(t.startswith(" You have a saved game in slot") for t in spoken) == 2
    assert items(rig)[1] == item(2, S.CHOOSE_ANOTHER)
    assert any(t.startswith(" 1. slot 1, Bengals and Jets, week 1, saved") for t in spoken)
    assert rig.plays[0]["saved"] is first                                  # the list's first line was taken


def test_the_list_can_be_left_with_its_last_item_and_nothing_is_loaded(tmp_path):
    rig = menu_rig(tmp_path, ["2", ENTER, "3", ENTER, DOWN, DOWN, ENTER] + EXIT)
    rig.store.shelf.write_slot(1, a_saved(own=7))
    rig.store.shelf.write_slot(3, a_saved(own=35))
    rig.run()
    assert " 3. %s " % S.LIST_BACK in said(rig) and rig.plays == []


# ----- NX-S8: damaged and old saves are named, never loaded and never removed -----

def test_a_damaged_save_is_named_not_loaded_and_the_menu_offers_to_delete_it(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, DOWN, ENTER, ENTER, ENTER] + EXIT)           # delete the damaged one, answer no, continue the season
    rig.store.shelf.slots[1] = damaged_entry()
    rig.run()
    spoken = said(rig)
    assert " The saved game is damaged and cannot be played. " in spoken
    assert items(rig)[:3] == [item(1, S.CONTINUE_SEASON), item(2, S.NEW_GAME), item(3, S.DELETE_DAMAGED)]
    assert rig.plays == [] and 1 in rig.store.shelf.slots and rig.store.shelf.backup is None


def test_deleting_a_damaged_save_moves_it_to_the_backup(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, DOWN, ENTER, "y", ENTER] + EXIT)
    rig.store.shelf.slots[1] = damaged_entry()
    rig.run()
    assert S.WAS_DELETED in said(rig) and rig.store.shelf.slots == {} and rig.store.shelf.backup is not None


def test_a_save_of_a_week_that_is_over_is_named_and_cannot_be_continued(tmp_path):
    rig = menu_rig(tmp_path, [ENTER] + EXIT)
    rig.store.classify = lambda entry: ("stale", "it is from week 3") if entry.info.get("week") == 3 else ("ok", "")
    rig.store.shelf.write_slot(1, a_saved(week=3))
    rig.run()
    assert " The saved game is from a week that is over, so it cannot be played. " in said(rig)
    assert rig.plays == [] and items(rig)[0] == item(1, S.CONTINUE_SEASON) and games(rig) == [(1, 14)]


# ----- NX-S2: delete asks again, starts at no, goes to the backup; restore brings it back -----

def test_delete_asks_again_starting_at_no_and_enter_deletes_nothing(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, DOWN, DOWN, ENTER, ENTER, DOWN, ENTER] + EXIT)      # delete the game, Enter = no, then the season
    rig.store.shelf.write_slot(1, a_saved())
    rig.run()
    spoken = said(rig)
    assert items(rig)[3] == item(4, S.DELETE_GAME)
    question = next(t for t in spoken if t.startswith(" Delete ") and "kept in the backup" in t)
    assert "Bengals and Jets" in question and " no " in spoken
    assert games(rig) == [(1, 14)] and rig.store.shelf.backup is None and S.WAS_DELETED not in spoken


def test_yes_moves_the_save_to_the_backup_and_the_menu_offers_to_restore_it(tmp_path):
    answers = [DOWN, DOWN, DOWN, ENTER, "y"] + [DOWN, DOWN, DOWN, ENTER] + [DOWN, ENTER]     # delete (yes); restore (item 4); the season
    rig = menu_rig(tmp_path, answers + EXIT)
    rig.store.shelf.write_slot(1, a_saved(own=17))
    rig.run()
    spoken = said(rig)
    assert S.WAS_DELETED in spoken and item(4, S.RESTORE_GAME) in spoken
    assert (S.WAS_RESTORED % 1) in spoken and games(rig) == [(1, 17)]            # restored to its own slot


def test_a_restore_when_every_slot_is_full_changes_nothing(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, DOWN, ENTER] + EXIT)           # the season; before that the restore item is tried below
    shelf = rig.store.shelf
    for slot in (1, 2, 3):
        shelf.write_slot(slot, a_saved(own=slot))
    shelf.backup = shelf.slots.pop(2)
    shelf.write_slot(2, a_saved(own=22))
    rig.keys.answers[:0] = [38, ENTER]                              # Up wraps to the last item: the restore
    rig.run()
    assert S.EVERY_SLOT_FULL in said(rig) and shelf.backup is not None and sorted(games(rig)) == [(1, 1), (2, 22), (3, 3)]


def test_delete_the_season_asks_again_and_its_yes_leaves_the_season_in_the_backup(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, DOWN, ENTER, "y", DOWN, DOWN, ENTER])        # items: continue, new, delete the season; then "start a new game" is next
    run_until_a_key_is_missing(rig)
    spoken = said(rig)
    assert S.DELETE_QUESTION_SEASON in spoken and S.WAS_DELETED in spoken
    assert rig.store.preset is None and rig.store.backup_preset is not None


# ----- NX-S3: the save is kept until its game ends -----

def test_a_loaded_game_that_is_played_out_moves_its_save_to_the_backup_and_says_so(tmp_path):
    rig = menu_rig(tmp_path, [ENTER, ENTER] + EXIT, outcomes=[played()])
    rig.store.shelf.write_slot(1, a_saved())
    rig.store.shelf.write_auto(a_saved(own=21))
    rig.run()
    assert S.GAME_OVER_SAVES_MOVED in said(rig)
    assert rig.store.shelf.slots == {} and rig.store.shelf.auto is None and len(rig.store.shelf.finished) == 1


def test_a_loaded_game_that_is_saved_again_keeps_every_save(tmp_path):
    rig = menu_rig(tmp_path, [ENTER], outcomes=[saved_game()])
    rig.store.shelf.write_slot(1, a_saved())
    rig.run()
    assert S.GAME_OVER_SAVES_MOVED not in said(rig) and games(rig) == [(1, 14)]


def test_the_window_closing_in_the_game_loses_no_save(tmp_path):
    from nfl4.game.keys import GameQuit

    def closes(rig):
        raise GameQuit()
    rig = menu_rig(tmp_path, [ENTER], outcomes=[closes])
    rig.store.shelf.write_slot(1, a_saved())
    with pytest.raises(GameQuit):
        rig.run()
    assert games(rig) == [(1, 14)]


# ----- NX-S7: a new game -----

def test_a_new_season_asks_before_it_replaces_the_season_and_keeps_it_in_the_backup(tmp_path):
    # new game (item 2), "no" (Enter) back at the menu; new game, "y", then the same coach and team (Enter), then the main menu
    rig = menu_rig(tmp_path, [DOWN, ENTER, ENTER, DOWN, ENTER, "y", ENTER] + EXIT)
    rig.run()
    spoken = said(rig)
    assert spoken.count(S.REPLACE_SEASON_QUESTION) == 2
    assert any(t.startswith(" Play as coach Kim with the Bengals again?") for t in spoken)
    assert rig.store.backup_preset is not None
    assert rig.game.season.coach == "Kim" and rig.game.season.gtp == 1


def test_a_new_season_takes_nothing_without_a_key(tmp_path):
    rig = menu_rig(tmp_path, [DOWN])
    run_until_a_key_is_missing(rig)
    assert rig.store.preset is not None and rig.store.backup_preset is None


# ----- no path acts without a key -----

SCENARIOS = {
    "a season": lambda rig: None,
    "a saved game": lambda rig: rig.store.shelf.write_slot(1, a_saved()),
    "an automatic save": lambda rig: rig.store.shelf.write_auto(a_saved()),
    "three slots": lambda rig: [rig.store.shelf.write_slot(n, a_saved(own=n)) for n in (1, 2, 3)],
    "a damaged save": lambda rig: rig.store.shelf.slots.__setitem__(1, damaged_entry()),
    "a season and a deleted game": lambda rig: setattr(rig.store.shelf, "backup", a_saved()),
}


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_with_no_key_pressed_nothing_is_loaded_deleted_or_replaced(tmp_path, name):
    rig = menu_rig(tmp_path, [])
    SCENARIOS[name](rig)
    before = (dict(rig.store.shelf.slots), rig.store.shelf.auto, rig.store.shelf.backup, rig.store.preset)
    run_until_a_key_is_missing(rig)
    after = (dict(rig.store.shelf.slots), rig.store.shelf.auto, rig.store.shelf.backup, rig.store.preset)
    assert before == after and rig.plays == [] and rig.store.calls.count("load_season") == 0 and rig.store.deleted == 0
    assert S.MENU_PROMPT in said(rig)


# ----- the keys: F1 with its one help sentence (rule 0.17) and the key list (F5) -----

def test_f1_in_the_start_up_menu_says_it_again_and_then_the_one_help_sentence(tmp_path):
    from nfl4.game import extra_texts as words
    rig = menu_rig(tmp_path, [112, ENTER], outcomes=[saved_game()])
    rig.keys.hint_enabled = True
    rig.store.shelf.write_slot(1, a_saved())
    rig.run()
    spoken = said(rig)
    assert spoken.count(S.MENU_PROMPT) == 2 and spoken.count(words.F1_HELP_HINT) == 1
    assert spoken.index(words.F1_HELP_HINT) > spoken.index(S.MENU_PROMPT, spoken.index(S.MENU_PROMPT) + 1)       # after the second saying, once


def test_the_special_key_list_names_the_saved_game_questions_in_every_mode():
    from nfl4.game import extra_texts as words
    assert "Saved games." in words.KEYS_ADDED_F9 and "Save Game asks for one of three places" in words.KEYS_ADDED_F9
    assert words.KEYS_ADDED_F9.startswith(" F9. added functions")
