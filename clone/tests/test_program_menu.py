"""The week line, today's game and the main menu on the virtual-clock rig. This is inspired by Jim Kitchen.

GAME_SPEC 3 step 7 and 4 (main menu) (CODE (lifted) Form_Load p_486990 0x488314 to 0x489d6c; keys 0x489af1 to 0x489d31), Q32,
D-022. The expected speech was written from the lifted lines (addresses in game/program.py): the menu says
" <coach> select " and then the current choice only; Up and Down wrap; a digit sets the choice; F1 and any hot-key menu repeat
everything from the week text (the choice kept); any other key is echoed and the choice starts at 1 again.
"""
import pytest

from nfl4.game import help_texts as H
from nfl4.game.playoffs import TeamRef
from programrig import DOWN, ENTER, ESC, F1, F5, UP, preset_season, program_rig, said

EXIT = [DOWN, DOWN, DOWN, ENTER]
SELECT = " Kim select "
CHOICE = {1: " 1. play game ", 2: " 2. see schedule ", 3: " 3. see standings ", 4: " 4. exit game "}


def menu_speech(rig):
    """The speech of the main menu only: from the first "Today's game" on, up to the thank-you."""
    spoken = said(rig)
    start = next(i for i, t in enumerate(spoken) if t.startswith(" Today's game is"))
    end = spoken.index(" Thank you for playing N. F. L. football version 4 By Jim Kitchen ")
    return spoken[start:end]


def week_with_flag(flag, team=(1, 1), seed=5):
    """The first week of the seeded schedule whose flag (vtrnt) is `flag`, and that week's opponent as a (division, team)."""
    from nfl4.game.rnd import GameRandom
    from nfl4.game.schedule import make_schedule
    import random
    schedule = make_schedule(GameRandom(random.Random(seed)), *team)
    week = next(i for i, e in enumerate(schedule, start=1) if e.flag == flag)
    return week, (schedule[week - 1].division, schedule[week - 1].team)


# ----- the week line and today's game -----

def test_the_week_line_has_str_numbers_and_the_log_gets_the_trimmed_one(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season(gtp=12))
    lines = []
    rig.game.log_sink = lines.append
    rig.run()
    spoken = said(rig)
    assert spoken[1:3] == [" This is week  12 of Jim's N. F. L. football ", " "]       # Str$(12) = " 12"; the synchronous " "
    assert " This is week #12 of Jim's N. F. L. football " in lines


@pytest.mark.parametrize("flag", [1, 2])
def test_todays_game_names_the_opponent_first_only_when_the_flag_is_1(tmp_path, flag):
    # vtrnt = 1: <opponent> <wins> and <losses> verses the <player's team> <wins> and <losses>; else the other way round
    week, (division, place) = week_with_flag(flag)

    def preset(season):
        preset_season(gtp=week)(season)
        season.records.wins[0][0], season.records.losses[0][0] = 2, 7            # the Bengals (the player) 2 and 7
        season.records.wins[division - 1][place - 1], season.records.losses[division - 1][place - 1] = 5, 3
    rig = program_rig(tmp_path, EXIT, preset=preset).run()
    opponent = rig.game.league.team(division, place)
    sentence = [t for t in said(rig) if t.startswith(" Today's game is")][0]
    own, other = "Bengals 2 and  7", "%s 5 and  3" % opponent
    first, second = (other, own) if flag == 1 else (own, other)
    assert sentence == " Today's game is %s verses the %s" % (first, second)
    assert rig.game.season.vtrnt == flag


def test_the_numbers_of_todays_game_are_str_numbers_with_a_space_in_front(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season(gtp=1)).run()
    sentence = [t for t in said(rig) if t.startswith(" Today's game is")][0]
    assert "0 and  0" in sentence and sentence.count(" verses the ") == 1 and not sentence.endswith(" ")


def test_a_play_off_week_says_this_is_the_then_the_week_name_in_the_menu_text(tmp_path):
    def preset(season):
        preset_season(gtp=18)(season)
        season.playoffs.pairings = [(TeamRef(1, 1), TeamRef(3, 2)), (TeamRef(2, 1), TeamRef(4, 4))]
    rig = program_rig(tmp_path, EXIT, preset=preset)
    lines = []
    rig.game.log_sink = lines.append
    rig.run()
    spoken = said(rig)
    assert spoken[1:3] == [" This is the ", " "]                                      # 0x488884, the synchronous " "
    assert spoken[3] == " division play off week of Jim's N. F. L. football "         # say2(L118) in the menu
    assert spoken[4].startswith(" Today's game is") and spoken[5] == SELECT
    assert rig.game.season.vtrnt == 2 and (rig.game.season.tn3, rig.game.season.tn4) == (3, 2)   # the player is the visitor
    # gtp 18 is not week 1: the log is appended to (an empty line first, 0x488454), then 0x488adf to 0x488b96, then today's block
    assert lines[:5] == ["", "", "#18", " division play off week", ""]
    assert lines[5] == "" and lines[6].startswith(" Today's game is") and lines[7] == ""


def test_a_week_of_the_regular_season_has_no_week_text_in_the_menu(tmp_path):
    rig = program_rig(tmp_path, [F1] + EXIT, preset=preset_season(gtp=2)).run()
    spoken = said(rig)
    # F1 speaks again from the top: today's game, then the select line (no week text in a regular week, L118 = "")
    first_today = next(i for i, t in enumerate(spoken) if t.startswith(" Today's game is"))
    assert spoken[first_today + 1: first_today + 3] == [SELECT, CHOICE[1]]
    assert spoken[first_today + 3].startswith(" Today's game is")


# ----- the menu's keys -----

def test_the_menu_says_the_select_line_then_only_the_current_choice(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season()).run()
    assert menu_speech(rig)[1:] == [SELECT, CHOICE[1], CHOICE[2], CHOICE[3], CHOICE[4]]


def test_up_from_the_first_choice_wraps_to_the_exit_and_down_from_the_last_to_the_first(tmp_path):
    rig = program_rig(tmp_path, [UP, DOWN, UP, ENTER], preset=preset_season()).run()
    assert menu_speech(rig)[2:] == [CHOICE[1], CHOICE[4], CHOICE[1], CHOICE[4]]
    assert rig.keys.answers == [] and said(rig)[-2].startswith(" Thank you")


@pytest.mark.parametrize("key, choice", [("1", 1), ("2", 2), ("3", 3), ("4", 4), (97, 1), (98, 2), (99, 3), (100, 4)])
def test_a_digit_sets_the_choice_the_keypad_too_q32(tmp_path, key, choice):
    # the keypad's keys 1 to 4 are the key codes 97 to 100: the original typed the letters a to d there, the clone takes digits
    rig = program_rig(tmp_path, [key, "4", ENTER], preset=preset_season()).run()
    assert menu_speech(rig)[1:] == [SELECT, CHOICE[1], CHOICE[choice], CHOICE[4]]


@pytest.mark.parametrize("keypad", [96, 101, 102, 103, 104, 105])
def test_the_keypad_s_0_and_5_to_9_are_any_other_key_and_never_a_choice(tmp_path, keypad):
    # found by the independent review of S7.4b: they once gave choice 5 to 9 and a KeyError; the original tests "1" to "4" only
    rig = program_rig(tmp_path, [keypad, DOWN, DOWN, DOWN, ENTER], preset=preset_season(gtp=2)).run()
    speech = menu_speech(rig)
    echo = chr(keypad).lower()                                                     # the original typed ` and the letters e to i
    assert speech[1:] == [SELECT, CHOICE[1], echo, speech[0], SELECT, CHOICE[1], CHOICE[2], CHOICE[3], CHOICE[4]]


def test_f1_says_everything_again_from_the_top_with_the_choice_kept(tmp_path):
    rig = program_rig(tmp_path, [DOWN, F1, DOWN, DOWN, ENTER], preset=preset_season(gtp=2)).run()
    speech = menu_speech(rig)
    today = speech[0]
    assert speech[1:] == [SELECT, CHOICE[1], CHOICE[2],           # first pass
                          today, SELECT, CHOICE[2],               # F1: from the top, choice 2 kept
                          CHOICE[3], CHOICE[4]]


def test_any_other_key_is_echoed_and_the_choice_starts_at_one_again(tmp_path):
    rig = program_rig(tmp_path, [DOWN, "a", DOWN, DOWN, DOWN, ENTER], preset=preset_season(gtp=2)).run()
    speech = menu_speech(rig)
    today = speech[0]
    assert speech[1:] == [SELECT, CHOICE[1], CHOICE[2],           # first pass, choice 2
                          "a",                                    # saykey: the key's character g2
                          today, SELECT, CHOICE[1],               # from the top (L_489857), choice 1 again
                          CHOICE[2], CHOICE[3], CHOICE[4]]


def test_escape_does_not_leave_the_main_menu_and_is_not_echoed(tmp_path):
    rig = program_rig(tmp_path, [ESC] + EXIT, preset=preset_season(gtp=2)).run()
    speech = menu_speech(rig)
    assert speech[0].startswith(" Today's game is") and speech.count(SELECT) == 2
    assert "\x1b" not in "".join(speech)                           # saykey sends no control character


def test_a_hot_key_menu_in_the_menu_repeats_from_the_top_with_the_choice_kept(tmp_path):
    rig = program_rig(tmp_path, [DOWN, F5, DOWN, DOWN, ENTER], preset=preset_season(gtp=2)).run()
    speech = menu_speech(rig)
    today = speech[0]
    after_f5 = speech.index(H.SPECIAL_KEYS)
    assert speech[after_f5 + 1:after_f5 + 4] == [today, SELECT, CHOICE[2]]


# ----- choices 2 and 3 return to the week line (0x48a8df, 0x48a930) -----

def test_see_schedule_returns_to_the_week_line_and_the_menu(tmp_path):
    rig = program_rig(tmp_path, [DOWN, ENTER] + EXIT, preset=preset_season(gtp=3)).run()
    spoken = said(rig)
    week = " This is week  3 of Jim's N. F. L. football "
    assert spoken.count(week) == 2                                  # the week line again, as the original (GAME_SPEC 3 step 7)
    assert " Bengals schedual. " in spoken
    assert spoken.index(" Bengals schedual. ") < len(spoken) - spoken[::-1].index(week)


def test_see_standings_returns_to_the_week_line_and_the_menu(tmp_path):
    rig = program_rig(tmp_path, [DOWN, DOWN, ENTER] + EXIT, preset=preset_season(gtp=3)).run()
    spoken = said(rig)
    week = " This is week  3 of Jim's N. F. L. football "
    assert spoken.count(week) == 2
    assert " Standings after week number 2" in spoken


def test_the_log_is_not_opened_again_when_the_week_line_comes_back(tmp_path):
    rig = program_rig(tmp_path, [DOWN, DOWN, ENTER] + EXIT, preset=preset_season(gtp=3)).run()
    assert [c for c in rig.store.calls if isinstance(c, tuple)] == [("open_log", False)]       # L7c: once per run
