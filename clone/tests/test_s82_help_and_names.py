"""S8.2 (owner, 2026-10-20): the key help names every key the clone adds, F1 says where the help is, and no sentence the game speaks
names the original's author as the game's maker. This is inspired by Jim Kitchen.

CLAUDE.md 0.17 (the key help) and 0.18 (the author's name), playbook 7.13, fixesforgames B-K9 and B-S27. The wording of the exit
sentence is the owner's own: "thank you for playing nfl football by Josh Kennedy, inspired by Jim Kitchen".
"""
import re

from nfl4.game import extra_texts as words
from nfl4.game import help_texts as H
from nfl4.game import program_texts as P
from nfl4.game import prompt_texts, texts
from programrig import DOWN, ENTER, F1, F5, preset_season, program_rig, said

EXIT = [DOWN, DOWN, DOWN, ENTER]


def menu_speech(rig):
    spoken = said(rig)
    start = next(i for i, t in enumerate(spoken) if t.startswith(" Today's game is"))
    return spoken[start:spoken.index(texts.THANK_YOU)]


# ----- 0.18: the author's name -----

def test_the_exit_sentence_is_the_owners_words():
    assert texts.THANK_YOU.strip() == "Thank you for playing N. F. L. football by Josh Kennedy, inspired by Jim Kitchen."


def test_the_week_line_names_the_clones_author():
    assert P.OF_FOOTBALL == " of Josh Kennedy's N. F. L. football "
    assert H.JIMS_GAME_PIECE not in H.TERMINOLOGY and H.JOSHS_GAME_PIECE in H.TERMINOLOGY


def test_no_spoken_text_of_the_game_names_jim_as_the_maker():
    """Every text constant with "Jim" in it is either the original's (kept under an ORIGINAL name for STRINGS.md and the tests) or a
    sentence that says "inspired by Jim Kitchen" / "Jim Kitchen's original games"; none says "Jim's N. F. L. football" or "By Jim Kitchen"
    as the game's owner."""
    allowed_original = {"OF_JIMS_FOOTBALL", "LOG_TITLE_ORIGINAL", "THANK_YOU_ORIGINAL", "CONTACT", "JIMS_GAME_PIECE", "TERMINOLOGY_ORIGINAL"}
    bad = []
    for module in (texts, P, prompt_texts, words):
        for name, value in vars(module).items():
            if isinstance(value, str) and "Jim" in value and name not in allowed_original:
                if re.search(r"Jim's N\. ?F\. ?L|By Jim Kitchen|by Jim Kitchen(?!\.)", value) and "inspired by Jim Kitchen" not in value:
                    bad.append((module.__name__, name))
    assert bad == []
    assert "Jim's" not in H.TERMINOLOGY and "Jim's" not in H.GAME_INSTRUCTIONS and "Jim's" not in H.FOOTBALL_INSTRUCTIONS
    assert "Jim" not in H.SPECIAL_KEYS


# ----- 0.17: the key help -----

def test_f5_lists_f9_in_a_classic_program(tmp_path):
    rig = program_rig(tmp_path, [DOWN, F5, DOWN, DOWN, ENTER], preset=preset_season(gtp=2)).run()
    spoken = said(rig)
    assert words.KEYS_ADDED_F9 in spoken and spoken.index(H.SPECIAL_KEYS) + 1 == spoken.index(words.KEYS_ADDED_F9)
    assert "F9." in words.KEYS_ADDED_F9 and "added functions" in words.KEYS_ADDED_F9


def test_f1_in_the_main_menu_repeats_then_names_the_help_keys_once(tmp_path):
    rig = program_rig(tmp_path, [DOWN, F1, DOWN, DOWN, ENTER], preset=preset_season(gtp=2))
    rig.keys.hint_enabled = True
    rig.run()
    speech = menu_speech(rig)
    assert speech.count(words.F1_HELP_HINT) == 1
    at = speech.index(words.F1_HELP_HINT)
    assert speech[at - 1] == " 2. see schedule " and speech[at + 1] == " 3. see standings "     # after the repeated prompt, before the next key's answer
    for key in ("F5", "F6", "F7", "F9"):
        assert key in words.F1_HELP_HINT


def test_a_key_that_is_not_f1_brings_no_hint_and_neither_does_the_hand_back_of_f5(tmp_path):
    rig = program_rig(tmp_path, [DOWN, F5, DOWN, DOWN, ENTER], preset=preset_season(gtp=2))
    rig.keys.hint_enabled = True
    rig.run()
    assert words.F1_HELP_HINT not in said(rig)
    rig = program_rig(tmp_path, [DOWN, DOWN, DOWN, ENTER], preset=preset_season(gtp=2))
    rig.keys.hint_enabled = True
    rig.run()
    assert words.F1_HELP_HINT not in said(rig)


def test_an_f1_that_a_later_key_wait_finds_too_late_brings_no_hint(tmp_path):
    from nfl4.game.keys import KeyInput
    clock = [0.0]
    keys = KeyInput(clock=lambda: clock[0], sleep=lambda s: None)
    said_hints = []
    keys.f1_hint = lambda: said_hints.append(clock[0])
    keys.post(112)
    keys.pump()
    clock[0] = 10.0                                                  # the wait comes ten seconds after the key
    keys._say_f1_hint()
    assert said_hints == []
    keys.post(112)
    keys.pump()
    keys._say_f1_hint()
    keys._say_f1_hint()                                              # once per press
    assert said_hints == [10.0]
