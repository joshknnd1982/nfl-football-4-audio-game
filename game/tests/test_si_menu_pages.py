"""S-I (2026-11-06, D-211, fixesforgames B-W46): Page Up and Page Down in the F9 menus and the text pages. This is inspired by Jim Kitchen.

The owner's run of 0.16.16 (nfl4-20261106-160342.log): in F9, Speech settings the brackets only said the current item again, because the F9
menus (SpokenMenu) and the text pages (TextPages) had no Page Up or Page Down, although F5, F6 and README_keys said that Page Up and Page Down
move ten items in the F9 menus. Now they move ten, stopping at the ends, as the lists (ListPicker) always did, and the brackets of rule 0.38
with them; F1 of these menus says the keys.
"""
from gamerig import Rig

from nfl4.game import extra_texts as words
from nfl4.game.keys import KEY_END, KEY_HOME, KEY_PAGE_DOWN, KEY_PAGE_UP
from nfl4.game.spoken_menu import Item, SpokenMenu, TextPages

OPEN_BRACKET, CLOSE_BRACKET, SEMICOLON, APOSTROPHE = 219, 221, 186, 222
ENTER, ESC, F1, DOWN = 13, 27, 112, 40


def menu_choice(answers, count=25):
    """The index Enter is pressed on in a menu of `count` items, and what the menu said."""
    chosen = []
    items = [Item(label=(lambda i=i: "item %d" % (i + 1)), enter=(lambda i=i: chosen.append(i) or "")) for i in range(count)]
    rig = Rig(answers=list(answers) + [ENTER, ESC])
    SpokenMenu(rig.speech, rig.keys, "Speech settings", items).run()
    return chosen[0], [text for text, _, _ in rig.said]


def test_page_down_and_page_up_move_ten_items_of_an_f9_menu_and_stop_at_the_ends():
    assert menu_choice([KEY_PAGE_DOWN])[0] == 10
    assert menu_choice([KEY_PAGE_DOWN, KEY_PAGE_DOWN, KEY_PAGE_DOWN])[0] == 24          # stops at the last item
    assert menu_choice([KEY_PAGE_DOWN, KEY_PAGE_DOWN, KEY_PAGE_UP])[0] == 10
    assert menu_choice([KEY_PAGE_UP])[0] == 0                                           # stops at the first item
    assert menu_choice([DOWN, DOWN, KEY_PAGE_DOWN])[0] == 12
    assert menu_choice([KEY_PAGE_DOWN], count=12)[0] == 10                              # Speech settings has 12 items today
    assert menu_choice([KEY_PAGE_DOWN, KEY_PAGE_DOWN], count=12)[0] == 11


def test_each_move_says_the_item_it_lands_on():
    _, said = menu_choice([KEY_PAGE_DOWN, KEY_PAGE_UP])
    assert said[1:3] == ["item 11", "item 1"]


def test_the_brackets_do_in_an_f9_menu_what_page_up_and_page_down_do():
    assert menu_choice([CLOSE_BRACKET, CLOSE_BRACKET, OPEN_BRACKET]) == menu_choice([KEY_PAGE_DOWN, KEY_PAGE_DOWN, KEY_PAGE_UP])
    assert menu_choice([APOSTROPHE, SEMICOLON, CLOSE_BRACKET])[0] == menu_choice([KEY_END, KEY_HOME, KEY_PAGE_DOWN])[0] == 10


def pages_said(answers, count=25):
    rig = Rig(answers=list(answers) + [ESC])
    TextPages(rig.speech, rig.keys, "About", tuple("line %d" % (i + 1) for i in range(count))).run()
    return [text for text, _, _ in rig.said][count + 2:]          # after the title, the lines and the help read at the start


def test_the_text_pages_move_ten_lines_with_page_down_and_page_up_and_the_brackets():
    assert pages_said([KEY_PAGE_DOWN, KEY_PAGE_DOWN, KEY_PAGE_DOWN, KEY_PAGE_UP]) == ["line 11", "line 21", "line 25", "line 15"]
    assert pages_said([CLOSE_BRACKET, OPEN_BRACKET, OPEN_BRACKET]) == ["line 11", "line 1", "line 1"]


def test_f1_of_the_menus_and_the_pages_names_the_keys():
    for text in (words.MENU_HELP, words.PAGES_HELP, words.LIST_HELP):
        assert "Page Up and Page Down move ten" in text and "Home and End jump to the ends" in text
    _, said = menu_choice([F1])
    assert words.MENU_HELP in said
