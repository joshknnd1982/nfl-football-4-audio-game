"""The typed prompts and the season's questions on the virtual-clock rig. This is inspired by Jim Kitchen.

GAME_SPEC 4.9 to 4.12 and 8.2 (CODE (lifted) getter p_429d10, ccn p_428f60, cqn p_429510, GetCoach p_4311a0, ChooseTeam
p_4308e0, Getqbs p_4314d0, SayScedual p_42eba0), D-022 items 1 and 2, G-K5 (30 characters), D-025, A-06, A-18. The
expected speech, keys and draws below were written from the lifted lines (addresses in game/prompts.py).
"""
import random

import pytest

from gamerig import Rig
from nfl4.game import prompt_texts as T
from nfl4.game.gamestate import GameState
from nfl4.game.playoffs import TeamRef
from nfl4.game.prompts import ccn, cqn
from nfl4.speech.roles import ANNOUNCER
from randsources import ScriptedRandom, value_for

ENTER, ESC, UP, DOWN, TAB, SHIFT, BACKSPACE, F1, F8 = 13, 27, 38, 40, 9, 16, 8, 112, 119
KEYPAD_1, KEYPAD_2 = 97, 98


def said(rig):
    return [text for text, _, _ in rig.said]


class Store:
    def __init__(self):
        self.calls = []

    def write_coach_and_team(self, tn1, tn2, coach):
        self.calls.append(("team", tn1, tn2, coach))

    def write_schedule(self, schedule):
        self.calls.append(("schedule", list(schedule)))

    def append_quarterback(self, name):
        self.calls.append(("quarterback", name))


def rig_with(answers, coach="Kim", **kwargs):
    rig = Rig(answers, **kwargs)
    rig.game.season.coach = coach
    rig.store = rig.game.setup_store = Store()
    return rig


# ----- ccn and cqn -----

@pytest.mark.parametrize("typed, coach, quarterback", [
    ("", "coach", ""), ("a", "coach", ""),                  # fewer than 2 characters typed
    ("ab", "ab", "ab"), ("Jo Bob", "Jo Bob", "Jo Bob"),     # the case and the spaces as typed
    ("a!", "coach", ""),                                    # 1 character left
    ("  ", "coach", ""), ("! !", "coach", ""),              # only spaces left
    (" a", " a", " a"), ("a b", "a b", "a b"),              # no trimming
    ("O'Neil", "ONeil", "ONeil"), ("café 9", "caf 9", "caf 9"),   # other characters removed
    ("x\x1b%y", "xy", "xy"),                                # what the original's Escape and Up arrow typed
])
def test_ccn_and_cqn_keep_letters_digits_and_spaces_with_their_defaults(typed, coach, quarterback):
    assert ccn(typed) == coach
    assert cqn(typed) == quarterback


# ----- getter -----

def test_getter_speaks_the_prompt_echoes_each_key_and_returns_on_enter():
    rig = rig_with(["b", "o", "b", ENTER])
    assert rig.game.getter(" Type ") == "bob"
    assert rig.said == [(" Type ", ANNOUNCER, 0), ("b", ANNOUNCER, 0), ("o", ANNOUNCER, 0), ("b", ANNOUNCER, 0)]


def test_shift_makes_the_next_key_upper_case_whatever_it_types():
    # the original: g2 = UCase$(g2) for the key after Shift; the window's own character does not decide the case
    rig = rig_with([SHIFT, "j", "o", SHIFT, "1", "B", ENTER])
    assert rig.game.getter(" Type ") == "Jo1b"
    assert said(rig)[1:] == ["J", "o", "1", "b"]


def test_backspace_speaks_the_character_it_removes_and_does_nothing_on_an_empty_text():
    rig = rig_with([BACKSPACE, "a", "b", BACKSPACE, "c", ENTER])
    assert rig.game.getter(" Type ") == "ac"
    assert said(rig)[1:] == ["a", "b", "b", "c"]


def test_f1_speaks_the_prompt_again_and_empties_the_text():
    rig = rig_with(["a", F1, "b", "c", ENTER])
    assert rig.game.getter(" Type ") == "bc"
    assert said(rig) == [" Type ", "a", " Type ", "b", "c"]


def test_keypad_digits_type_digits_and_keys_that_type_nothing_are_ignored_d022():
    rig = rig_with(["a", KEYPAD_1, UP, ESC, TAB, KEYPAD_2, ENTER])
    assert rig.game.getter(" Type ") == "a12"
    assert said(rig) == [" Type ", "a", "1", "2"]


def test_a_typed_name_stores_30_characters_and_echoes_the_rest_g_k5():
    letters = list("abcdefghijklmnopqrstuvwxyzabcdefghi")       # 35
    rig = rig_with(letters + [ENTER])
    assert rig.game.getter(" Type ") == "".join(letters[:30])
    assert said(rig)[1:] == letters


def test_a_global_key_while_typing_runs_its_menu_and_the_name_starts_again():
    rig = rig_with(["a", F8, "b", "c", ENTER])
    assert rig.game.getter(" Type ") == "bc"
    assert said(rig) == [" Type ", "a", T.COMMENTS_OFF, " Type ", "b", "c"]
    assert rig.game.comtog == 1


# ----- GetCoach (4.9) -----

def test_the_coach_name_is_typed_and_confirmed():
    rig = rig_with(["k", "i", "m", ENTER, ENTER], coach="coach")
    assert rig.game.get_coach() == "kim" and rig.game.season.coach == "kim"
    assert said(rig) == [T.ENTER_COACH, "k", "i", "m", " is, kim, correct for the name of your coach? ", " yes "]
    assert [(text, role) for text, role, _ in rig.said][-2:] == [(" is, kim, correct for the name of your coach? ",
                                                                  ANNOUNCER), (" yes ", ANNOUNCER)]


def test_no_asks_the_name_again_and_y_accepts():
    rig = rig_with(["k", "i", ENTER, DOWN, ENTER, "j", "o", ENTER, "y"])
    assert rig.game.get_coach() == "jo"
    assert said(rig) == [T.ENTER_COACH, "k", "i", " is, ki, correct for the name of your coach? ", " yes ", " no ",
                         T.ENTER_COACH, "j", "o", " is, jo, correct for the name of your coach? ", " yes ", "y"]


def test_f1_and_other_keys_ask_again_with_yes_and_n_asks_the_name_again():
    rig = rig_with(["k", "i", ENTER, UP, F1, "z", "n", "l", "u", ENTER, ENTER])
    assert rig.game.get_coach() == "lu"
    question = " is, ki, correct for the name of your coach? "
    assert said(rig) == [T.ENTER_COACH, "k", "i", question, " yes ", " no ", question, " yes ", "z", question,
                         " yes ", "n", T.ENTER_COACH, "l", "u", " is, lu, correct for the name of your coach? ",
                         " yes "]


def test_a_name_of_one_letter_is_coach():
    rig = rig_with(["k", ENTER, ENTER])
    assert rig.game.get_coach() == "coach"


# ----- ChooseTeam (4.10) -----

def choose(answers):
    rig = rig_with(answers)
    rig.game.choose_team()
    return rig


def test_enter_takes_the_first_team_and_writes_footbal1():
    rig = choose([ENTER, ENTER])
    assert (rig.game.season.tn1, rig.game.season.tn2) == (1, 1)
    assert said(rig) == [" Kim choose your team ", "Bengals", " Kim your team is the Bengals. Is this correct? ",
                         " yes "]
    assert rig.store.calls == [("team", 1, 1, "Kim")]


@pytest.mark.parametrize("keys, team, place", [
    ([DOWN] * 4, "Bills", (2, 1)),                 # place first, then the division (0x430bd2)
    ([UP], "Saints", (8, 4)),                      # from the first team back to the last (0x430b70)
    ([UP, DOWN], "Bengals", (1, 1)),               # from the last forward to the first (0x430c86)
    ([DOWN] * 31, "Saints", (8, 4)),
])
def test_up_and_down_walk_the_32_teams_and_wrap(keys, team, place):
    rig = choose(keys + [ENTER, ENTER])
    assert (rig.game.season.tn1, rig.game.season.tn2) == place
    assert said(rig)[-3] == team


def test_any_other_key_while_browsing_starts_the_choice_again_f1_without_an_echo():
    rig = choose([DOWN, "x", DOWN, F1, ENTER, ENTER])
    assert said(rig) == [" Kim choose your team ", "Bengals", "Browns", "x", " Kim choose your team ", "Bengals",
                         "Browns", " Kim choose your team ", "Bengals",
                         " Kim your team is the Bengals. Is this correct? ", " yes "]


def test_the_question_f1_speaks_the_answer_only_and_no_starts_again():
    rig = choose([ENTER, F1, DOWN, ENTER, DOWN, ENTER, "q", "y"])
    question = " Kim your team is the Bengals. Is this correct? "
    assert said(rig) == [" Kim choose your team ", "Bengals", question, " yes ", " yes ", " no ",
                         " Kim choose your team ", "Bengals", "Browns",
                         " Kim your team is the Browns. Is this correct? ", " yes ", "q",
                         " Kim your team is the Browns. Is this correct? ", " yes ", "y"]
    assert rig.store.calls == [("team", 1, 2, "Kim")]


def test_n_at_the_question_starts_the_choice_again():
    rig = choose([ENTER, "n", ENTER, ENTER])
    assert said(rig)[4:6] == ["n", " Kim choose your team "]
    assert rig.store.calls == [("team", 1, 1, "Kim")]


# ----- Getqbs (4.12) -----

def qb_rig(answers, draws=()):
    rig = rig_with(answers, rng=ScriptedRandom(draws, strict=True))
    season = rig.game.season
    season.tn3, season.tn4 = 2, 3                          # this week's opponent: the Jets
    return rig


def test_first_game_the_own_name_is_typed_and_written_the_opponents_drawn():
    rig = qb_rig(["s", "m", "i", "t", "h", ENTER, ENTER, ENTER, ENTER], [value_for(1708, 11)])
    pool = rig.game.pool
    drawn = pool.name(11)
    state = GameState()
    assert rig.game.getqbs(state) == ("smith", drawn)
    assert said(rig) == [" Kim enter the name of your quarter back or press enter ", "s", "m", "i", "t", "h",
                         " is, smith, correct for the name of your quarter back? ", " yes ",
                         " enter the name of the Jets quarter back or press enter ",
                         " is, %s, correct for the name of the Jets quarter back? " % drawn, " yes "]
    assert rig.store.calls == [("quarterback", "smith")]
    assert pool.name(1439) == "" and pool.name(11) == ""   # Smith (every entry, any case) and the drawn slot
    assert rig.rnd.source.left == 0


def test_a_drawn_slot_that_is_blank_is_drawn_again_and_no_draws_again():
    draws = [value_for(1708, 10), value_for(1708, 11), value_for(1708, 12)]
    rig = qb_rig([ENTER, "n", ENTER, ENTER], draws)
    pool = rig.game.pool
    pool.blank(10)
    names = pool.name(11), pool.name(12)
    state = GameState()
    state.gpn, state.quarterbacks = 1, {2: "Saved"}
    own, opponent = rig.game.getqbs(state, saved=False, own_from_file="Starr")
    assert (own, opponent) == ("Starr", names[1])          # footplay.txt read: only the opponent is asked
    assert said(rig)[:4] == [" enter the name of the Jets quarter back or press enter ",
                             " is, %s, correct for the name of the Jets quarter back? " % names[0], " yes ", "n"]
    assert pool.name(11) == names[0] and pool.name(12) == ""   # the refused name stays in the pool
    assert rig.store.calls == []


def test_a_loaded_game_with_footplay_txt_asks_nothing():
    rig = qb_rig([])
    state = GameState()
    state.gpn, state.quarterbacks = 1, {2: "Unitas"}
    assert rig.game.getqbs(state, saved=True, own_from_file="Starr") == ("Starr", "Unitas")
    assert rig.said == []


def test_a_loaded_game_without_footplay_txt_asks_both_and_the_answer_replaces_the_saved_name_a18():
    rig = qb_rig(["b", "o", ENTER, ENTER, "c", "y", ENTER, ENTER])
    state = GameState()
    state.quarterbacks = {2: "Unitas"}
    assert rig.game.getqbs(state, saved=True) == ("bo", "cy")
    assert rig.store.calls == [("quarterback", "bo")]


def test_the_typed_quarterback_prompt_runs_inside_a_game(tmp_path):
    from pagrig import make_rig
    rig = make_rig(tmp_path, rng=random.Random(4), fast=True)
    rig.game.setup_store = store = Store()
    result = rig.game.play_game()                           # no names handed in: Getqbs asks, Enter takes defaults
    assert result.scores is not None
    lines = said(rig)
    assert lines[0] == " Kim enter the name of your quarter back or press enter "
    own = [line for line in lines if line.endswith(", correct for the name of your quarter back? ")]
    opponent = [line for line in lines if line.endswith(", correct for the name of the Jets quarter back? ")]
    assert len(own) == 1 and len(opponent) == 1
    assert store.calls == [("quarterback", own[0][len(" is, "):-len(T.OWN_QUARTERBACK_CORRECT)])]


# ----- SayScedual (4.11) -----

def schedule_rig(answers, gtp, seed=3):
    rig = rig_with(answers, rng=random.Random(seed))
    rig.game.season.gtp = gtp
    rig.game.make_schedule()
    rig.store.calls.clear()
    rig.game.pause_log = []
    return rig


def schedule_lines(rig):
    game = rig.game
    lines = [" Bengals schedual. "]
    for number, entry in enumerate(game.season.schedule, start=1):
        other = game.league.team(entry.division, entry.team)
        first, second = (other, "Bengals") if entry.flag == 1 else ("Bengals", other)
        lines += [" game number %s%d" % (" " if number < 10 else " ", number), " %s verses the %s" % (first, second)]
    return lines


def test_from_week_two_the_schedule_is_spoken_with_its_pauses_and_no_question():
    rig = schedule_rig([], gtp=2)
    rig.game.say_schedule()
    assert said(rig) == schedule_lines(rig)
    assert said(rig)[1] == " game number  1"                 # Str$: two spaces
    assert rig.game.pause_log == [(0x42f30b, 0.1), (0x42f5c6, 0.2)] * 16
    assert len([e for e in rig.sapi.events if e[0] == "wait"]) == 0   # say2 only: nothing waited


def test_before_week_one_the_question_follows_and_enter_on_yes_keeps_the_schedule():
    rig = schedule_rig([ENTER], gtp=1)
    before = list(rig.game.season.schedule)
    rig.game.say_schedule()
    assert said(rig) == schedule_lines(rig) + [" Kim do you like this schedual? yes "]
    assert rig.game.pause_log[-1] == (0x42f673, 0.2)
    assert rig.game.season.schedule == before and rig.store.calls == []


def test_no_makes_a_new_schedule_and_speaks_it_again_f1_repeats_it_unchanged():
    rig = schedule_rig([F1, "n", ENTER], gtp=1)
    first = list(rig.game.season.schedule)
    first_lines = schedule_lines(rig)
    rig.game.say_schedule()
    second_lines = schedule_lines(rig)
    question = " Kim do you like this schedual? yes "
    assert said(rig) == first_lines + [question] + first_lines + [question, "n"] + second_lines + [question]
    assert rig.store.calls == [("schedule", rig.game.season.schedule)]
    assert rig.game.season.schedule != first


def test_up_down_and_tab_toggle_the_answer_and_another_key_speaks_it():
    rig = schedule_rig([UP, TAB, DOWN, "q", ENTER, ENTER], gtp=1)
    rig.game.say_schedule()
    lines = said(rig)
    question = lines.index(" Kim do you like this schedual? yes ")
    assert lines[question + 1:question + 6] == [" no ", " yes ", " no ", "q", " no "]
    assert len(rig.store.calls) == 1                       # Enter on no: a new schedule, then Enter on yes


def test_a_play_off_week_speaks_the_round_in_one_waited_text():
    rig = rig_with([])
    season = rig.game.season
    season.gtp = 17
    season.playoffs.pairings = [(TeamRef(1, 1), TeamRef(5, 2)), (TeamRef(2, 3), TeamRef(6, 3))]
    rig.game.say_schedule()
    text = " games for the Wild card play off week are.  the Bengals verses the Lions.  the Jets verses the Giants. "
    assert said(rig) == [text]
    assert ("wait", "") in rig.sapi.events                 # say4 waits
    assert rig.game.replay == [text]                       # and is kept for F2


def test_a_loaded_game_whose_footplay_txt_lacks_the_quarterback_asks_for_him_but_keeps_the_saved_opponent():
    rig = qb_rig(["s", "m", "i", "t", "h", ENTER, ENTER])
    state = GameState()
    state.gpn, state.quarterbacks = 1, {2: "Unitas"}
    assert rig.game.getqbs(state, saved=True, own_from_file="") == ("smith", "Unitas")
    assert rig.store.calls == [("quarterback", "smith")]
    assert not any("Jets quarter back" in text for text in said(rig))
