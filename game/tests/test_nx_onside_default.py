"""The onside question at every kick (nfl4 only, rule 0.13; N4.1 as amended by D-085, PX SX.2b, gap G26-2). This is inspired by Jim Kitchen.

The owner, playing the game: "I did not see onside kicks in there. My version of the game must follow current 2026 nfl rules." The 2026 rule
(6-1-6) lets the kicking team declare an onside kick at any free kick, so the player's team is asked at EVERY kick-off and safety kick: the
setting's default is "always"; a file that says "sensible" and was never chosen by the player (the old default) moves once; "sensible" stays
a choice of the player's own, remembered by `nx_onside_question_chosen`.
"""
import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras.nfl_rules import is_nfl, rules_from_settings
from nfl4.game.rules import NORMAL_KICKOFF
from test_nx_onside import NO, QUESTION, game, texts

ENTER = 13


def test_a_new_player_is_asked_at_every_kick():
    settings = Settings.defaults()
    assert settings.game.nx_onside_question == "always" and settings.game.nx_onside_question_chosen is False
    assert settings.game.rules == "nfl"
    rules = rules_from_settings(settings.game)
    assert is_nfl(rules) and rules.onside_on and rules.onside_always


def test_a_file_from_before_the_change_with_sensible_moves_once():
    old = settingsfile.HEADER + "nx_onside = on\nnx_onside_question = sensible\n"
    settings, problems = settingsfile.parse(old)
    assert problems == [] and settings.game.nx_onside_question == "always" and settings.game.nx_onside_question_chosen is False
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert problems == [] and again.game.nx_onside_question == "always"                  # written back as the new default


def test_a_player_who_chose_sensible_keeps_it():
    chosen = settingsfile.HEADER + "nx_onside_question = sensible\nnx_onside_question_chosen = yes\n"
    settings, problems = settingsfile.parse(chosen)
    assert problems == [] and settings.game.nx_onside_question == "sensible" and settings.game.nx_onside_question_chosen is True
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert problems == [] and again.game.nx_onside_question == "sensible" and again.game.nx_onside_question_chosen is True
    assert rules_from_settings(again.game).onside_always is False


def test_a_bad_chosen_value_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_onside_question_chosen = maybe\n")
    assert len(problems) == 1 and settings.game.nx_onside_question_chosen is False


@pytest.mark.parametrize("quarter,scores,left", [(1, (0, 0), 900), (2, (14, 3), 700), (3, (3, 14), 600), (4, (21, 7), 800),
                                                 (4, (10, 17), 100), (5, (10, 10), 300)])
def test_the_players_team_is_asked_at_every_kick_off(tmp_path, quarter, scores, left):
    """Any quarter, any score, any time: the 2026 rule has no condition."""
    rig = game(tmp_path, answers=[ENTER], always=True, quarter=quarter, scores=scores, left=left)
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == [QUESTION, NO]


def test_the_players_team_is_asked_at_a_safety_kick_too(tmp_path):
    rig = game(tmp_path, answers=[ENTER], always=True, quarter=2, scores=(7, 0), extras=dict(safety_kick=True))
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == [QUESTION, NO] and rig.engine.s.extras.kick_from == 20


def test_the_computer_is_never_asked(tmp_path):
    rig = game(tmp_path, answers=[], always=True, quarter=2, scores=(7, 0))
    rig.engine.s.defense, rig.engine.s.wisoff = 2, 1                  # the Jets kick: no question, the computer's rules decide
    assert rig.rules.before_kickoff(rig.engine.s, 2) == NORMAL_KICKOFF
    assert texts(rig) == []


def test_the_players_own_sensible_choice_asks_only_when_it_makes_sense(tmp_path):
    rig = game(tmp_path, answers=[], always=False, quarter=1, scores=(0, 0))
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == []
