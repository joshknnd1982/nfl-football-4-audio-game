"""The Rules setting: settings.txt, the F9 Rules menu, the program's rules and the extras' files (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 12.1 and 12.2, NFL_EXTRA_FEATURES C1; PX SX.2). This is inspired by Jim Kitchen.

The menu has the items whose features exist (SX.2: Rules, Time outs, Reset), says " used with the N. F. L. rules " after a
switch while Rules is Classic, saves every change at once and says that it applies from the next game. Classic stays the
choice of a settings file that says so, and with it no file of the extras is ever made; a new player's default is the N. F. L. rules
(NQ2, SX.9).
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
OPEN = "Rules. 12 items. Press F1 for help. "    # SX.7: Rules, Time outs, Replay challenges, Quarterback runs, Onside kicks,
#                                                  Onside question, Penalties, Offense playbook, Defense playbook, Reset
NEXT_GAME = X.text("NXM-23")


# ----- settings.txt -----

def test_the_defaults_are_the_nfl_rules_with_timeouts_on():
    settings = Settings.defaults()                 # SX.9: a new player's default (NQ2, D-079)
    assert settings.game.rules == "nfl" and settings.game.nx_timeouts is True
    assert is_nfl(rules_from_settings(settings.game))
    settings.game.rules = "classic"
    assert rules_from_settings(settings.game) is CLASSIC


@pytest.mark.parametrize("line, rules", [("rules = nfl", "nfl"), ("rules = classic", "classic"),
                                         ("rules = N. F. L. rules", "nfl"), ("rules = NFL", "nfl")])
def test_the_rules_line_is_read(line, rules):
    settings, problems = settingsfile.parse(settingsfile.HEADER + line + "\n")
    assert settings.game.rules == rules and problems == []


def test_a_bad_rules_or_switch_line_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "rules = madden\nnx_timeouts = maybe\n")
    assert settings.game.rules == "nfl" and settings.game.nx_timeouts is True and len(problems) == 2


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
                              "9", ENTER, "0", ENTER, DOWN, ENTER, DOWN, ENTER, ENTER, "1"])      # SY.1: "0" is Broadcast, Down is Stadium sounds, Down again Reset
    assert spoken[2] == "Time outs on "
    assert spoken[3] == "Time outs off " + NEXT_GAME
    assert spoken[4] == "Replay challenges on "
    assert spoken[5] == "Replay challenges off " + NEXT_GAME
    assert spoken[6] == "Quarterback runs on "
    assert spoken[7] == "Quarterback runs off " + NEXT_GAME
    assert spoken[8] == "Onside kicks on "
    assert spoken[9] == "Onside kicks off " + NEXT_GAME
    assert spoken[10] == "Onside question: always"                      # SX.2b, D-085: the 2026 rule is the default
    assert spoken[11] == "Onside question: when it makes sense" + NEXT_GAME
    assert spoken[12] == "Penalties on "
    assert spoken[13] == "Penalties off " + NEXT_GAME
    assert spoken[14] == "Offense playbook: Team playbook"              # Rules is on N. F. L. rules now: nothing "used with"
    assert spoken[15] == "Offense playbook: Pro Style" + NEXT_GAME     # SX.10e (D-095): the team's playbook is the default
    assert spoken[16] == "Defense playbook: Team playbook"
    assert spoken[17] == "Defense playbook: Pro Style" + NEXT_GAME
    assert spoken[18] == "Broadcast on "                                  # SY.1: the tenth item
    assert spoken[19] == "Broadcast off " + NEXT_GAME
    assert spoken[20] == "Stadium sounds on "                             # SY.2: the eleventh item
    assert spoken[21] == "Stadium sounds off " + NEXT_GAME
    assert spoken[22] == X.text("NXM-19")
    defaults = ("Rules: N. F. L. rules. Time outs on. Replay challenges on. Quarterback runs on. Onside kicks on."   # SX.9: the default is
                " Onside question: always. Penalties on. Offense playbook: Team playbook. Defense playbook: Team playbook. Broadcast on. Stadium sounds on ")
    assert spoken[23] == defaults + NEXT_GAME
    assert spoken[24] == defaults                                       # nothing changed now
    assert spoken[25] == "Rules: N. F. L. rules"
    game = rig.game.options.settings.game
    assert (game.rules, game.nx_timeouts, game.nx_penalties) == ("nfl", True, True) and is_nfl(rig.game.rules)
    assert (game.nx_onside, game.nx_onside_question, game.nx_qb_runs) == (True, "always", True)
    assert (game.nx_offense_playbook, game.nx_defense_playbook) == ("team", "team")      # SX.10e (D-095): the team's is the default
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
    assert [spec.file_name for spec in custom.specs][-8:-6] == ["remarks.txt", "penalties.txt"]     # SX.3
    assert os.path.isfile(os.path.join(folder, "penalties.txt"))
    assert [spec.file_name for spec in custom.specs][-6:] == ["plays.txt", "styles.txt", "team_styles.txt", "news.txt", "injuries.txt",
                                                             "favourites.txt"]    # SX.7, SX.8e, SX.8k, SX.10c
    assert os.path.isfile(os.path.join(folder, "playbooks", "plays.txt"))
    assert custom.take_notices() == []
    assert "remarks.txt: no problems." in custom.check()
    assert "remarks.txt" not in Customization(str(tmp_path / "classic")).check()


def test_the_nfl_program_rules_are_given_to_the_game(tmp_path):
    from pagrig import make_rig
    rig = make_rig(tmp_path)
    rig.game.options.settings.game.rules = "nfl"
    rig.game.apply_rules_setting()
    assert isinstance(rig.game.rules, NflRules) and rig.game.rules.for_game() is not rig.game.rules


def test_the_players_choice_of_the_onside_question_is_remembered_as_his_own(rig):
    """SX.2b, D-085: "always" is the default; the player's toggle is a choice, marked so that a later read keeps it."""
    game = rig.game.options.settings.game
    assert game.nx_onside_question == "always" and game.nx_onside_question_chosen is False
    rules_menu(rig, [ENTER, "6", ENTER])
    assert game.nx_onside_question == "sensible" and game.nx_onside_question_chosen is True
