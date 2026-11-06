"""Owner rule 0.38 (2026-11-06, D-207, fixesforgames B-W44): keys that stand in for Home, End, Page Up and Page Down.
This is inspired by Jim Kitchen.

The owner: "some keyboards like acer laptops do not have home, end, pageup and pagedown. You must implement alternative keys". The open
bracket is Page Up, the close bracket Page Down, the semicolon Home and the apostrophe End, in every menu, list and question, in every
mode; while the player types a name they stay themselves, so typing is not disturbed.
"""
from gamerig import Rig

from nfl4.data import debuglog
from nfl4.extras.franchise.question import FranchiseQuestion
from nfl4.game import key_list as K
from nfl4.game.keys import (ALTERNATIVE_KEYS, KEY_END, KEY_HOME, KEY_PAGE_DOWN, KEY_PAGE_UP, KeyInput, MODIFIER_KEYS, WINDOWS_KEYS)
from nfl4.game.spoken_menu import ListPicker

OPEN_BRACKET, CLOSE_BRACKET, SEMICOLON, APOSTROPHE = 219, 221, 186, 222
ENTER = 13
LONG = ["item %d" % n for n in range(1, 13)]
SITUATION = " Kim which kind of season do you wish to play "


def test_each_missing_key_has_a_plain_key_that_stands_in_for_it():
    assert ALTERNATIVE_KEYS == {OPEN_BRACKET: KEY_PAGE_UP, CLOSE_BRACKET: KEY_PAGE_DOWN, SEMICOLON: KEY_HOME, APOSTROPHE: KEY_END}
    assert not set(ALTERNATIVE_KEYS) & (MODIFIER_KEYS | WINDOWS_KEYS)      # no Ctrl, Shift or Alt is needed, no key of Windows


def test_the_key_layer_hands_the_menus_the_key_it_stands_for():
    keys = KeyInput()
    for code in (OPEN_BRACKET, CLOSE_BRACKET, SEMICOLON, APOSTROPHE):
        keys.post(code)
    assert [keys.read_key() for _ in range(4)] == [KEY_PAGE_UP, KEY_PAGE_DOWN, KEY_HOME, KEY_END]


def test_while_a_name_is_typed_the_four_keys_stay_themselves():
    keys = KeyInput()
    with debuglog.context("typing: the player's name"):
        keys.post(APOSTROPHE)
        keys.post(OPEN_BRACKET)
    keys.post(APOSTROPHE)                                                  # after the name: End again
    assert [keys.read_key() for _ in range(3)] == [APOSTROPHE, OPEN_BRACKET, KEY_END]


def test_the_log_says_which_key_stood_in(monkeypatch):
    seen = []
    monkeypatch.setattr(debuglog, "event", lambda *args, **fields: seen.append((args, fields)))
    KeyInput().post(CLOSE_BRACKET)
    assert seen[0][0][:2] == ("key", "alternative") and seen[0][1]["vk"] == CLOSE_BRACKET and seen[0][1]["as_code"] == KEY_PAGE_DOWN


def ask(answers):
    rig = Rig(answers=answers)
    result = FranchiseQuestion(rig.game, SITUATION, LONG).ask()
    return result, [text for text, _, _ in rig.said]


def test_the_brackets_turn_the_pages_of_a_question_exactly_as_page_up_and_page_down_do():
    with_brackets = ask([OPEN_BRACKET, CLOSE_BRACKET, CLOSE_BRACKET, OPEN_BRACKET, "1", ENTER])
    with_page_keys = ask([KEY_PAGE_UP, KEY_PAGE_DOWN, KEY_PAGE_DOWN, KEY_PAGE_UP, "1", ENTER])
    assert with_brackets == with_page_keys
    assert with_brackets[0] == 0 and with_brackets[1].count(" page 2 of 2. ") == 1


def picker_index(answers):
    rig = Rig(answers=answers + [ENTER])
    return ListPicker(rig.speech, rig.keys, "players", 25, lambda i: "player %d" % (i + 1)).run()


def test_semicolon_and_apostrophe_go_to_the_ends_of_a_list_and_the_brackets_move_ten():
    assert picker_index([APOSTROPHE]) == 24
    assert picker_index([APOSTROPHE, SEMICOLON]) == 0
    assert picker_index([CLOSE_BRACKET, CLOSE_BRACKET]) == 20
    assert picker_index([CLOSE_BRACKET, CLOSE_BRACKET, OPEN_BRACKET]) == 10
    assert picker_index([CLOSE_BRACKET, OPEN_BRACKET]) == picker_index([KEY_PAGE_DOWN, KEY_PAGE_UP]) == 0


def test_the_master_key_list_names_the_four_keys_in_f5_f6_and_the_readme_in_both_modes():
    row = K.BY_ID["laptop_keys"]
    assert row.modes == "all" and row.f5 in K.help_lines(K.KEY_F5, "classic") and row.f5 in K.help_lines(K.KEY_F5, "nfl")
    for word in ("open bracket", "close bracket", "semicolon", "apostrophe"):
        assert word in row.f5 and word in row.what
    assert any(line.startswith(" Open bracket, close bracket, semicolon, apostrophe.") for line in K.help_lines(K.KEY_F6, "classic"))
    assert "**Open bracket, close bracket, semicolon, apostrophe**" in K.readme_text()
