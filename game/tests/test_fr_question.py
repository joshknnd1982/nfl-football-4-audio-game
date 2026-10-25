"""FranchiseQuestion: a question inside the program's flow on the original's key wait (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.7, B-W10: every key of the question, the global keys that run at its wait, the paging and the wait with
one item. The Game and its speakers are the rig's (tests/gamerig.py); the keys are scripted and the rig fails the test when the
question waits for a key that was not scripted.
"""
from gamerig import Rig

from nfl4.extras.franchise.question import FranchiseQuestion, ask_yes_no, wait_for_enter

ENTER, ESC, UP, DOWN, F1, F2, F8, PAGE_UP, PAGE_DOWN = 13, 27, 38, 40, 112, 113, 119, 33, 34
ITEMS = ["classic season", "your franchise with the Bengals", "a new franchise"]
SITUATION = " Kim which kind of season do you wish to play "


def ask(answers, items=ITEMS, situation=SITUATION, **kwargs):
    rig = Rig(answers=answers)
    result = FranchiseQuestion(rig.game, situation, items, **kwargs).ask()
    return result, [text for text, _, _ in rig.said], rig


def test_the_situation_and_the_first_item_are_spoken_and_enter_takes_it():
    result, spoken, rig = ask([ENTER])
    assert result == 0 and spoken == [SITUATION, " 1. classic season "] and rig.keys.answers == []


def test_up_and_down_move_and_wrap_and_speak_the_new_item():
    result, spoken, _ = ask([DOWN, DOWN, DOWN, UP, UP, UP, UP, ENTER])
    assert spoken[2:] == [" 2. your franchise with the Bengals ", " 3. a new franchise ", " 1. classic season ",
                          " 3. a new franchise ", " 2. your franchise with the Bengals ", " 1. classic season ",
                          " 3. a new franchise "]
    assert result == 2


def test_the_digits_of_the_main_row_and_the_keypad_take_that_item_as_the_current_one():
    result, spoken, _ = ask(["3", 98, ENTER])                           # the main row 3, the keypad 2 (code 98)
    assert spoken[2:] == [" 3. a new franchise ", " 2. your franchise with the Bengals "] and result == 1


def test_f1_says_the_situation_and_the_current_item_again_with_the_item_kept():
    result, spoken, _ = ask([DOWN, F1, ENTER])
    assert spoken == [SITUATION, " 1. classic season ", " 2. your franchise with the Bengals ", SITUATION,
                      " 2. your franchise with the Bengals "] and result == 1


def test_f2_is_the_instant_replay_of_what_was_spoken():
    _, spoken, _ = ask([F2, ENTER])
    assert " here's the instant rea play " in spoken
    start = spoken.index(" here's the instant rea play ")
    assert spoken[start + 1:] == [SITUATION, " 1. classic season "]


def test_any_other_key_is_echoed_and_the_question_is_said_again_from_the_top_with_the_item_kept():
    result, spoken, _ = ask([DOWN, "x", ENTER])
    assert spoken[:3] == [SITUATION, " 1. classic season ", " 2. your franchise with the Bengals "]
    assert spoken[3:] == ["x", SITUATION, " 2. your franchise with the Bengals "] and result == 1


def test_a_digit_beyond_the_items_is_an_other_key():
    result, spoken, _ = ask(["9", ENTER])
    assert "9" in spoken and spoken.count(SITUATION) == 2 and result == 0


def test_escape_does_not_take_an_item_of_a_question():
    result, spoken, _ = ask([ESC, ENTER])
    assert result == 0 and spoken.count(SITUATION) == 2


def test_a_global_key_runs_at_the_wait_and_hands_back_f1_so_the_question_is_said_again():
    rig = Rig(answers=[F8, ENTER])
    before = rig.game.options.comtog
    result = FranchiseQuestion(rig.game, SITUATION, ITEMS).ask()
    spoken = [text for text, _, _ in rig.said]
    assert result == 0 and rig.game.options.comtog != before            # F8 switched the comments
    assert spoken.count(SITUATION) == 2 and spoken[-1] == " 1. classic season "


# ----- paging: nine items a page, then "more" on the 0, and "Back" on later pages -----

LONG = ["item %d" % n for n in range(1, 13)]


def test_a_long_list_shows_nine_items_then_more_and_a_page_line():
    result, spoken, _ = ask(["0", ENTER, ENTER], items=LONG)
    assert spoken[:3] == [SITUATION, " page 1 of 2. ", " 1. item 1 "]
    assert spoken[3:] == [" 0. more ", " page 2 of 2. ", " 1. item 10 "] and result == 9


def test_page_two_has_back_on_the_zero_and_the_item_numbers_start_again():
    result, spoken, _ = ask([PAGE_DOWN, "3", "0", ENTER, DOWN, ENTER], items=LONG)
    assert spoken[:3] == [SITUATION, " page 1 of 2. ", " 1. item 1 "]
    assert spoken[3:8] == [" page 2 of 2. ", " 1. item 10 ", " 3. item 12 ", " 0. Back ", " page 1 of 2. "]
    assert spoken[8:] == [" 1. item 1 ", " 2. item 2 "] and result == 1


def test_page_up_and_page_down_turn_pages_and_the_edges_stay():
    result, spoken, _ = ask([PAGE_UP, PAGE_DOWN, PAGE_DOWN, PAGE_UP, "1", ENTER], items=LONG)
    assert result == 0 and spoken.count(" page 2 of 2. ") == 1 and spoken.count(" page 1 of 2. ") == 2


def test_a_short_list_has_no_page_line_and_no_more():
    _, spoken, _ = ask([ENTER])
    assert not any("page" in text or "more" in text for text in spoken)


# ----- a wait with one item, and a yes or no question -----

def test_a_stage_wait_speaks_its_lines_without_a_number_and_enter_or_escape_goes_on():
    lines = [" stage 1 of 2. the season in review. ", " press enter to go on. F1 says it again. "]
    for key in (ENTER, ESC):
        rig = Rig(answers=[key])
        wait_for_enter(rig.game, lines)
        assert [text for text, _, _ in rig.said] == lines
    rig = Rig(answers=[F1, ENTER])
    wait_for_enter(rig.game, lines)
    assert [text for text, _, _ in rig.said] == lines + lines


def test_a_yes_or_no_question_starts_where_it_is_told_to_and_up_down_y_and_n_answer():
    for answers, start, expected in (([ENTER], False, False), ([ENTER], True, True), ([UP, ENTER], False, True),
                                     (["y"], False, True), (["n"], True, False), ([DOWN, DOWN, ENTER], True, True)):
        rig = Rig(answers=answers)
        assert ask_yes_no(rig.game, " is it so? ", start_yes=start) is expected, answers
    rig = Rig(answers=[F1, ENTER])
    ask_yes_no(rig.game, " is it so? ", start_yes=False)
    assert [text for text, _, _ in rig.said] == [" is it so? ", " no ", " is it so? ", " no "]
