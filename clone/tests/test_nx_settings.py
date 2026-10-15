"""The Rules setting: settings.txt, the F9 Rules menu, the program's rules and the extras' files (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 12.1 and 12.2, NFL_EXTRA_FEATURES C1; PX SX.2). This is inspired by Jim Kitchen.

The menu has the items whose features exist (SX.2: Rules, Time outs, Reset), says " used with the N. F. L. rules " after a
switch while Rules is Classic, saves every change at once and says that it applies from the next game. Classic stays the
default (NQ2) and with it no file of the extras is ever made.
"""
import os

import pytest

from nfl4.data import settingsfile
from nfl4.data.customize import Customization
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules, is_nfl, rules_from_settings
from nfl4.extras.remarks import RemarkPools
from nfl4.game import extra_texts as words
from nfl4.game.rules import CLASSIC
from programrig import DOWN, ENTER, ESC, F1, said
from test_functions import TOP, rig_for

SPACE, LEFT = 32, 37
OPEN = "Rules. 8 items. Press F1 for help. "     # SX.6: Rules, Time outs, Replay challenges, Quarterback runs, Onside kicks,
#                                                  Onside question, Penalties, Reset
NEXT_GAME = X.text("NXM-23")


# ----- settings.txt -----

def test_the_defaults_are_classic_with_timeouts_on():
    settings = Settings.defaults()
    assert settings.game.rules == "classic" and settings.game.nx_timeouts is True
    assert rules_from_settings(settings.game) is CLASSIC


@pytest.mark.parametrize("line, rules", [("rules = nfl", "nfl"), ("rules = classic", "classic"),
                                         ("rules = N. F. L. rules", "nfl"), ("rules = NFL", "nfl")])
def test_the_rules_line_is_read(line, rules):
    settings, problems = settingsfile.parse(settingsfile.HEADER + line + "\n")
    assert settings.game.rules == rules and problems == []


def test_a_bad_rules_or_switch_line_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "rules = madden\nnx_timeouts = maybe\n")
    assert settings.game.rules == "classic" and settings.game.nx_timeouts is True and len(problems) == 2


def test_the_file_is_written_with_both_lines_and_reads_back_the_same():
    settings = Settings.defaults()
    settings.game.rules, settings.game.nx_timeouts = "nfl", False
    text = settingsfile.render(settings)
    assert "rules = nfl\n" in text and "nx_timeouts = off\n" in text
    again, problems = settingsfile.parse(text)
    assert again.game == settings.game and problems == []


def test_the_program_rules_follow_the_setting():
    settings = Settings.defaults()
    settings.game.rules, settings.game.nx_timeouts = "nfl", False
    rules = rules_from_settings(settings.game)
    assert is_nfl(rules) and rules.timeouts_on is False and rules.auto_sides == (2,)


# ----- the F9 Rules menu -----

def rules_menu(rig, keys):
    rig.keys.answers = [DOWN, DOWN, DOWN, ENTER] + keys + [ESC, ESC]
    rig.game.functions.run()
    spoken = said(rig)
    assert spoken[:4] == [TOP + "Speech settings.", "Sounds.", words.CUSTOMIZE_ITEM, "Rules."]
    return spoken[4:]


@pytest.fixture
def rig(tmp_path):
    return rig_for(tmp_path, [])


def test_the_menu_opens_on_rules_classic_and_escape_leaves(rig):
    assert rules_menu(rig, []) == [OPEN + "Rules: Classic", "Rules."]
    assert rig.saves.count == 0 and rig.game.rules is CLASSIC


def test_enter_switches_to_the_nfl_rules_saves_and_says_it_applies_from_the_next_game(rig):
    spoken = rules_menu(rig, [ENTER])
    assert spoken[1] == "Rules: N. F. L. rules" + NEXT_GAME
    assert rig.game.options.settings.game.rules == "nfl" and rig.saves.count == 1 and is_nfl(rig.game.rules)


def test_a_switch_says_used_with_the_nfl_rules_while_rules_is_classic(rig):
    spoken = rules_menu(rig, [DOWN, SPACE, LEFT])
    assert spoken[1] == "Time outs on  used with the N. F. L. rules "
    assert spoken[2] == "Time outs off  used with the N. F. L. rules " + NEXT_GAME
    assert spoken[3] == "Time outs on  used with the N. F. L. rules "
    assert rig.game.options.settings.game.nx_timeouts is True and rig.saves.count == 2


def test_the_digits_jump_and_reset_brings_the_defaults_back(rig):
    spoken = rules_menu(rig, [ENTER, "2", ENTER, "3", ENTER, "4", ENTER, "5", ENTER, "6", ENTER, "7", ENTER, "8", ENTER,
                              ENTER, "1"])
    assert spoken[2] == "Time outs on "
    assert spoken[3] == "Time outs off " + NEXT_GAME
    assert spoken[4] == "Replay challenges on "
    assert spoken[5] == "Replay challenges off " + NEXT_GAME
    assert spoken[6] == "Quarterback runs on "
    assert spoken[7] == "Quarterback runs off " + NEXT_GAME
    assert spoken[8] == "Onside kicks on "
    assert spoken[9] == "Onside kicks off " + NEXT_GAME
    assert spoken[10] == "Onside question: when it makes sense"
    assert spoken[11] == "Onside question: always" + NEXT_GAME
    assert spoken[12] == "Penalties on "
    assert spoken[13] == "Penalties off " + NEXT_GAME
    assert spoken[14] == X.text("NXM-19")
    defaults = ("Rules: Classic. Time outs on  used with the N. F. L. rules. Replay challenges on  used with the N. F. L."
                " rules. Quarterback runs on  used with the N. F. L."
                " rules. Onside kicks on  used with the N. F. L. rules."
                " Onside question: when it makes sense used with the N. F. L. rules. Penalties on  used with the N. F. L."
                " rules ")
    assert spoken[15] == defaults + NEXT_GAME
    assert spoken[16] == defaults                                       # nothing changed now
    assert spoken[17] == "Rules: Classic"
    game = rig.game.options.settings.game
    assert (game.rules, game.nx_timeouts, game.nx_penalties) == ("classic", True, True) and rig.game.rules is CLASSIC
    assert (game.nx_onside, game.nx_onside_question, game.nx_qb_runs) == (True, "sensible", True)
    assert game.nx_challenges is True


def test_f1_says_the_help_of_the_rules_menu(rig):
    assert rules_menu(rig, [F1])[1] == X.text("NXM-36")


def test_a_change_during_a_game_leaves_the_game_its_rules(rig, tmp_path):
    from nflrig import nfl_engine_rig
    other = nfl_engine_rig(tmp_path / "game")
    rig.game.play_engine = other.engine
    rules_menu(rig, [ENTER])
    assert is_nfl(rig.game.rules) and rig.game.rules is not other.engine.rules
    rig.game.play_engine = None


# ----- the extras' files follow the setting (CUSTOMIZABLE_CONTENT 13) -----

def test_remarks_txt_is_never_made_with_classic_and_is_made_and_used_with_the_nfl_rules(rig, tmp_path):
    folder = str(tmp_path / "customize")
    rig.game.customization = Customization(folder)
    rig.game.apply_customization()
    remarks = os.path.join(folder, "remarks.txt")
    assert not os.path.exists(remarks) and rig.game.remark_pools is None
    rig.game.customization.take_notices()
    assert not os.path.exists(remarks)
    rig.game.options.settings.game.rules = "nfl"
    rig.game.apply_rules_setting()
    assert os.path.isfile(remarks) and isinstance(rig.game.remark_pools, RemarkPools)
    assert open(remarks, encoding="utf-8").readline().strip() == "# NFL Football 4 remarks, format 1."
    rig.game.options.settings.game.rules = "classic"
    rig.game.apply_rules_setting()
    assert rig.game.remark_pools is None and rig.game.rules is CLASSIC
    os.remove(remarks)
    rig.game.customization.take_notices()
    assert not os.path.exists(remarks)                                  # Classic again: it is not made again


def test_a_customization_made_with_the_nfl_rules_reads_remarks_txt_at_once(tmp_path):
    folder = str(tmp_path / "customize")
    custom = Customization(folder, extras=True)
    assert os.path.isfile(os.path.join(folder, "remarks.txt"))
    assert [spec.file_name for spec in custom.specs][-2:] == ["remarks.txt", "penalties.txt"]       # SX.3
    assert os.path.isfile(os.path.join(folder, "penalties.txt"))
    assert custom.take_notices() == []
    assert "remarks.txt: no problems." in custom.check()
    assert "remarks.txt" not in Customization(str(tmp_path / "classic")).check()


def test_the_nfl_program_rules_are_given_to_the_game(tmp_path):
    from pagrig import make_rig
    rig = make_rig(tmp_path)
    rig.game.options.settings.game.rules = "nfl"
    rig.game.apply_rules_setting()
    assert isinstance(rig.game.rules, NflRules) and rig.game.rules.for_game() is not rig.game.rules
