"""R and L are in the special keys, in the help and in the README (CLAUDE.md 0.24; SZ.3). This is inspired by Jim Kitchen.

The owner (2026-10-22), after playing the receiver and blitzer lists: "this must be documented in special keys and help." They were in all three since
SY.4 and SY.5 (the master list of keys, game/key_list.py); this test pins it for a game with the DEFAULT settings, which is what a player has, and for the
README draft, and says that the keys are not documented when the player's books are the original's (the keys do nothing there).
"""
from pathlib import Path

from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules, rules_from_settings
from nfl4.game import key_list as K

CODE = Path(__file__).resolve().parent.parent


def default_rules():
    settings = Settings.defaults()
    assert settings.game.rules == "nfl"
    return rules_from_settings(settings.game)


def test_a_game_with_the_default_settings_speaks_r_and_l_in_f5_and_f6():
    rules = default_rules()
    f5, f6 = " ".join(rules.extra_help(K.KEY_F5)), rules.extra_help(K.KEY_F6)
    assert K.BY_ID["target"].f5 in f5 and K.BY_ID["blitzer"].f5 in f5
    for key_id in ("target", "blitzer"):
        row = K.BY_ID[key_id]
        assert " %s. %s. %s. " % (row.keys, row.where, row.what[0].upper() + row.what[1:]) in f6
    assert X.TEXTS["NXH-69"] in f6 and "R in the offense menu chooses who your next pass goes to" in X.TEXTS["NXH-69"]


def test_the_readme_keys_draft_has_both_and_says_what_they_do():
    text = (CODE / "README_keys.md").read_text(encoding="utf-8")
    assert "- **R** (N. F. L. rules only): In the offense menu of the N. F. L. rules with a playbook. Chooses who your next pass goes to" in text
    assert "- **L** (N. F. L. rules only): In the defense menu of the N. F. L. rules with a playbook. Chooses who blitzes on your next blitz call" in text


def test_the_keys_are_not_spoken_when_both_books_are_the_originals():
    rules = NflRules(offense_book="classic", defense_book="classic", playbooks_on=False)
    lines = " ".join(rules.extra_help(K.KEY_F5) + rules.extra_help(K.KEY_F6))
    assert "chooses the receiver" not in lines and "Chooses who your next pass goes to" not in lines
