"""The playbooks beside the settings, the F9 items, the saved game and the added help (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN
10.4, 12.1, 12.2, 12.3; PX SX.7). This is inspired by Jim Kitchen.
"""
import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras import playbook_data as D
from nfl4.extras import rules_menu as RM
from nfl4.extras.nfl_rules import NflRules, is_nfl, rules_from_settings
from nfl4.extras.state import ExtrasRecord
from nfl4.game.gamestate import GameState
from nfl4.game.rules import CLASSIC
from nflrig import nfl_engine_rig
from test_nx_save import a_record, a_save
from test_nx_settings import LEFT, NEXT_GAME, rules_menu
from test_functions import rig_for


RIGHT = 39


# ----- the settings -----

def test_the_teams_playbook_is_the_default_and_the_lines_are_in_the_file_and_its_header():
    # SX.10e (D-095, Q-035): a new player plays the team's playbook, every play of the catalog (D-083); Classic is one setting away
    game = Settings.defaults().game
    assert (game.nx_offense_playbook, game.nx_defense_playbook, game.nx_playbook_chosen) == ("team", "team", False)
    lines = settingsfile.render(Settings.defaults()).splitlines()
    assert "nx_offense_playbook = team" in lines and "nx_defense_playbook = team" in lines and "nx_playbook_chosen = no" in lines
    for name in ("nx_offense_playbook", "nx_defense_playbook", "nx_playbook_chosen"):
        assert name in settingsfile.HEADER


@pytest.mark.parametrize("choice", D.PLAYBOOK_CHOICES)
def test_every_choice_is_read_and_written_back(choice):
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_offense_playbook = %s\nnx_defense_playbook = %s\n"
                                            "nx_playbook_chosen = yes\n" % (choice.upper(), choice))
    assert problems == [] and settings.game.nx_offense_playbook == choice == settings.game.nx_defense_playbook
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert problems == [] and again.game == settings.game


def test_a_classic_the_player_never_chose_becomes_the_teams_playbook_once_and_a_chosen_one_stays():
    # SX.10e: a file from before SX.10e says classic (the old default) and has no nx_playbook_chosen: read as team, once; the next file
    # written says team; a style the player chose stays whatever the line says
    old = settingsfile.HEADER + "nx_offense_playbook = classic\nnx_defense_playbook = air\n"
    settings, problems = settingsfile.parse(old)
    assert problems == [] and (settings.game.nx_offense_playbook, settings.game.nx_defense_playbook) == ("team", "air")
    assert "nx_offense_playbook = team" in settingsfile.render(settings).splitlines()
    kept, _ = settingsfile.parse(old + "nx_playbook_chosen = yes\n")
    assert (kept.game.nx_offense_playbook, kept.game.nx_defense_playbook) == ("classic", "air")


def test_a_playbook_value_that_is_not_a_choice_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_offense_playbook = wing t\nnx_defense_playbook =\n")
    assert len(problems) == 2 and settings.game.nx_offense_playbook == "team" == settings.game.nx_defense_playbook


def test_the_programs_rules_carry_the_players_books_and_the_computers_team_style(tmp_path):
    settings = Settings.defaults()
    settings.game.rules = "nfl"
    settings.game.nx_offense_playbook, settings.game.nx_defense_playbook = "west", "team"
    rules = rules_from_settings(settings.game)
    assert is_nfl(rules) and (rules.offense_book, rules.defense_book, rules.playbooks_on) == ("west", "team", True)
    again = rules.for_game()
    assert (again.offense_book, again.defense_book, again.playbooks_on) == ("west", "team", True)
    classic = Settings.defaults().game
    classic.rules = "classic"
    assert rules_from_settings(classic) is CLASSIC
    plain = NflRules()                                                  # made by hand: Classic plays, no style for the computer
    assert (plain.offense_book, plain.defense_book, plain.playbooks_on) == ("classic", "classic", False)


# ----- the F9 items -----

@pytest.fixture
def rig(tmp_path):
    return rig_for(tmp_path, [])


def test_the_playbook_items_say_their_value_and_that_it_is_used_with_the_nfl_rules_while_rules_is_classic(rig):
    spoken = rules_menu(rig, ["8", "9"])
    assert spoken[1] == "Offense playbook: Team playbook used with the N. F. L. rules "         # SX.10e: the default
    assert spoken[2] == "Defense playbook: Team playbook used with the N. F. L. rules "


def test_enter_and_right_go_forward_through_the_playbooks_and_left_goes_back(rig):
    spoken = rules_menu(rig, ["8", RIGHT, RIGHT, LEFT, LEFT, LEFT])
    assert spoken[2] == "Offense playbook: Pro Style used with the N. F. L. rules "
    assert spoken[3] == "Offense playbook: West Coast used with the N. F. L. rules "
    assert spoken[4] == "Offense playbook: Pro Style used with the N. F. L. rules "
    assert spoken[5] == "Offense playbook: Team playbook used with the N. F. L. rules "
    assert spoken[6] == "Offense playbook: Classic used with the N. F. L. rules "
    game = rig.game.options.settings.game
    assert game.nx_offense_playbook == "classic" and game.nx_playbook_chosen and rig.saves.count == 5


def test_a_change_says_it_applies_from_the_next_game_and_is_saved_at_once(rig):
    spoken = rules_menu(rig, ["9", 13])
    assert spoken[2] == "Defense playbook: Pro Style used with the N. F. L. rules " + NEXT_GAME
    game = rig.game.options.settings.game
    assert game.nx_defense_playbook == "pro" and game.nx_playbook_chosen and rig.saves.count == 1


def test_every_value_of_the_menu_has_a_name_in_the_order_of_the_choices():
    names = [RM.playbook_name(choice) for choice in D.PLAYBOOK_CHOICES]
    assert names == ["Classic", "Team playbook", "Pro Style", "West Coast", "Air Raid", "Power Run", "Zone Run", "Option",
                     "Pressure"]
    assert RM.next_playbook("pressure", 1) == "classic" and RM.next_playbook("classic", -1) == "pressure"
    assert RM.next_playbook("nonesuch", 1) == "team"                  # a value that is not a choice counts as the first


def test_reset_brings_the_playbooks_back_to_the_teams(rig):
    rules_menu(rig, ["8", 13, "9", 13, "0", 40, 40, 13])      # SY.1: "0" is Broadcast now; SY.2: Reset is the twelfth item, reached with Down twice
    game = rig.game.options.settings.game
    assert (game.nx_offense_playbook, game.nx_defense_playbook, game.nx_playbook_chosen) == ("team", "team", False)


# ----- the saved game -----

def test_a_record_with_books_goes_to_json_and_back_and_an_older_record_has_classic_books():
    record = a_record(offense_book=["air", "zone"], defense_book=["classic", "pressure"])
    assert ExtrasRecord.from_json(record.to_json()) == record
    older = ExtrasRecord.from_json('{"left": 300}')
    assert older.offense_book == ["classic", "classic"] and older.defense_book == ["classic", "classic"]


@pytest.mark.parametrize("text", ['{"offense_book": ["air"]}', '{"offense_book": "air"}', '{"offense_book": ["air", "wing t"]}',
                                  '{"defense_book": ["team", "air"]}', '{"defense_book": [1, 2]}', '{"offense_book": []}',
                                  '{"defense_book": ["air", "air", "air"]}'])
def test_books_that_are_not_two_known_styles_make_the_record_unusable(text):
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(text)


def test_a_loaded_game_keeps_the_books_it_was_saved_with_not_the_settings(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    state = GameState()
    rules = NflRules(offense_book="zone", defense_book="team", playbooks_on=True)
    rules.period_clock(rig.game, state)
    assert state.extras.offense_book[0] == "zone"
    record = a_record(offense_book=["air", "classic"], defense_book=["power", "power"])
    state.load(a_save(extras=record.to_json(), extras_marked=True))
    assert state.extras.offense_book == ["air", "classic"] and state.extras.defense_book == ["power", "power"]
    state = GameState()
    rules.period_clock(rig.game, state)
    state.load(a_save())                                                # a Classic save: the settings' books stay
    assert state.extras.offense_book[0] == "zone"


def test_a_snapshot_keeps_the_books_for_a_reversal(tmp_path):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(offense_book="air", defense_book="pro"))
    copy = rig.engine.s.snapshot()
    assert copy.extras.offense_book == ["air", "classic"] and copy.extras.defense_book == ["pro", "classic"]


# ----- the added help -----

def test_f5_f6_and_f7_add_the_playbook_lines_only_when_a_playbook_is_in_use(tmp_path):
    plain = nfl_engine_rig(tmp_path / "plain")
    used = nfl_engine_rig(tmp_path / "used", rules=NflRules(offense_book="west"))
    computer = nfl_engine_rig(tmp_path / "computer", rules=NflRules(playbooks_on=True))
    lines = {"116": ["NXH-27"], "117": ["NXH-28", "NXH-29", "NXH-30"], "118": ["NXH-31", "NXH-32", "NXH-33"]}
    for key, ids in lines.items():
        wanted = [X.text(i) for i in ids]
        assert not any(t in plain.rules.extra_help(key) for t in wanted)
        for rig in (used, computer):
            help_ = rig.rules.extra_help(key)
            for i in ids:
                # the line about the menus is for a player whose own books are playbooks, not for one who only meets a style
                assert (X.text(i) in help_) == (i != "NXH-27" or rig is used), (key, i)
    assert X.text("NXH-27") == (" With a playbook, the play menus start with the original's items. Right opens a list of plays, and "
                                "Backspace or Left goes back, and so does the last item, Back, which the letter B. selects. ")   # SX.10d
