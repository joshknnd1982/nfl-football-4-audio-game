"""The catalog's offense menus in the game (nfl4 only, rule 0.13; NX-P4, NX-P7, NX-P8, NX-H1; NFL_PLAYS_DESIGN 2 and 7; PX SX.10c, D-093).
This is inspired by Jim Kitchen.

The menus of extras/plays/play_menus.py reach the player through the engine's own menu loop (game/pag.py `_menu`) and the H3 hooks: the
original's items first with their digits, Enter on a family is the playbook's pick, Right opens a family's lists and walks them, Left and
Backspace go back, the letters F, A, M, K, P, O and N, plus and minus for the favourites, D the description, a lone Shift says nothing,
the tail of NflRules (Challenge, Time Out, Save Game) after them. With the Classic playbook and in Classic the menus are the original's.
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import offense_flow as OF
from nfl4.extras import playbooks as PB
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import calling as K
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import descriptions as DS
from nfl4.extras.plays import play_menus as PM
from nfl4.game import menus
from nfl4.game import phrases as P
from nfl4.game.rules import CLASSIC, MENU_QUIET
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps

ENTER, ESCAPE, UP, DOWN, BACKSPACE, LEFT, RIGHT, SHIFT = 13, 27, 38, 40, 8, 37, 39, 16
PLUS_MAIN, PLUS_PAD, MINUS_MAIN, MINUS_PAD, KEYPAD_4 = 187, 107, 189, 109, 100
SELECT = " Kim" + P.SELECT_OFFENSE
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
TOP_WEST = [" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass ", " 6. Field Goal ", " 7. Punt ",
            " 8. More Plays ", " 9. Formation and Tempo ", " 10. Save Game "]


def rig_for(tmp_path, answers=(), offense="west", qb_on=False, timeouts_on=False, extras=None, **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=timeouts_on, qb_on=qb_on, offense_book=offense, defense_book="classic")
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, extras=extras, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def items_of(rig):
    return [i.text for i in rig.rules.offense_menu(rig.engine.s, rig.engine.s.two_point)]


def the_menu(rig, draws=None):
    return run_steps(rig, rig.engine.offense_menu, draws or Draws(), until=MENU_UNTIL)


def name(play_id):
    return PB.DEFAULT_TABLE.name(play_id)


# ----- which menu -----

def test_a_playbook_gives_the_catalogs_top_level_with_the_originals_items_first(tmp_path):
    rig = rig_for(tmp_path)
    assert items_of(rig) == TOP_WEST
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.digit for i in items][:10] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    assert items[7].letter == "m" and items[8].letter == "o" and items[9].letter == "s"
    assert items[0].action == ("pm:pick", 1) and items[5].action == ("pm:kick", 6)


def test_the_team_playbook_uses_the_same_menus_and_classic_keeps_the_originals_items(tmp_path):
    assert items_of(rig_for(tmp_path / "team", offense="team")) == TOP_WEST
    classic = items_of(rig_for(tmp_path / "classic", offense="classic"))
    assert classic[:7] == [" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass ",
                           " 6. Field Goal ", " 7. Punt "] and classic[7:] == [" 8. Save Game "]
    rig = rig_for(tmp_path / "rules", offense="classic")
    assert rig.rules.menu_heading(rig.engine.s) == "" and rig.rules.menu_right(rig.engine.s, rig.rules.offense_menu(rig.engine.s, False)[0]) is False


def test_with_the_quarterback_runs_and_timeouts_on_the_tail_follows_the_letters(tmp_path):
    rig = rig_for(tmp_path, qb_on=True, timeouts_on=True)
    assert items_of(rig) == TOP_WEST[:7] + [" 8. Quarterback Sneak ", " 9. Quarterback Keeper ", " 10. Quarterback Draw ",
                                            " 11. More Plays ", " 12. Formation and Tempo ", " 13. Time Out ", " 14. Save Game "]


def test_classic_rules_answer_the_new_hooks_with_the_original_and_no_draw(tmp_path):
    rig = rig_for(tmp_path)
    s = rig.engine.s
    assert CLASSIC.menu_right(s, None) is False and CLASSIC.menu_heading(s) == ""
    assert CLASSIC.model_play(s) is None and CLASSIC.turnover_return(s) is None
    assert CLASSIC.menu_key(s, "", None, "107") is False


# ----- Enter, Right, Left -----

def test_right_opens_a_familys_lists_with_their_heading_and_left_goes_back(tmp_path):
    rig = rig_for(tmp_path, answers=[RIGHT, RIGHT, LEFT, ESCAPE])
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    said = texts(rig, mark)
    inside, power = name("O001"), name("O002")
    assert said[:2] == [SELECT, TOP_WEST[0]]
    assert said[2] == X.text("NXB-H13", list="Inside Runs", n=1, m=2) and said[3] == " 1. %s " % inside
    assert said[4] == X.text("NXB-H13", list="Power and Gap Runs", n=2, m=2) and said[5] == " 1. %s " % power
    assert said[6:8] == [SELECT, TOP_WEST[0]]


def test_right_wraps_to_the_familys_first_list_and_backspace_goes_up_too(tmp_path):
    rig = rig_for(tmp_path, answers=[RIGHT, RIGHT, RIGHT, BACKSPACE, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    assert X.text("NXB-H13", list="Inside Runs", n=1, m=2) in said[4:]
    assert said[-2:] == [SELECT, TOP_WEST[0]]


def test_enter_on_a_play_of_a_list_calls_it_and_the_engine_gets_its_family(tmp_path):
    rig = rig_for(tmp_path, answers=[RIGHT, "3", ENTER])
    assert the_menu(rig) == "offense_chosen"
    third = PM.concepts_of("og01", rig.rules.offense.context(rig.engine.s))[2]
    assert rig.rules.offense.called == third.id and rig.engine.s.offense_play == OF.engine_family(third) == 1


def test_enter_on_a_family_is_the_playbooks_pick_said_before_the_snap(tmp_path):
    # SX.10e (D-095): the pick is the calling's weights (extras/plays/calling.py) over the family's plays for the style, one draw
    rig = rig_for(tmp_path, answers=[ENTER])
    s, books = rig.engine.s, rig.rules.books
    family = [c for g in PM.family_groups("O", 1) for c in PM.concepts_of(g, rig.rules.offense.context(s))]
    weights = K.offense_weights(family, "west", books.own_plays("west", "O"), books.call_situation(s))
    total = sum(w for _i, w in weights)
    assert {i for i, _w in weights} <= {c.id for c in family} and len(weights) > 5
    assert the_menu(rig, Draws().below(total, 0)) == "offense_chosen"
    pick = weights[0][0]
    assert rig.rules.offense.called == pick and rig.engine.s.offense_play == 1
    assert X.text("NXB-H15", name=name(pick)) in texts(rig)


def test_field_goal_and_punt_stay_the_originals_and_right_opens_nothing_on_them_yet(tmp_path):
    rig = rig_for(tmp_path, answers=["6", ENTER])
    assert the_menu(rig) == "offense_chosen"
    assert rig.engine.s.offense_play == 6 and rig.rules.offense.called == ""
    rig = rig_for(tmp_path / "right", answers=["7", RIGHT, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    assert not [t for t in texts(rig, mark) if "list" in t]


def test_the_quarterback_items_call_the_catalogs_sneak_keeper_and_draw_with_no_draw(tmp_path):
    for digit, play, family in (("8", "O046", 8), ("9", "O047", 9), ("0", "O048", 10)):
        rig = rig_for(tmp_path / digit, answers=[digit, ENTER], qb_on=True)
        assert the_menu(rig) == "offense_chosen"
        assert rig.rules.offense.called == play and rig.engine.s.offense_play == family


def test_more_plays_lists_the_other_lists_and_back(tmp_path):
    rig = rig_for(tmp_path, answers=["m", ENTER, ENTER, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    assert X.text("NXB-H14", list="More Plays") in said
    assert " 1. Play Action " in said
    assert X.text("NXB-H14", list="Play Action") in said


def test_the_quarterback_runs_list_is_empty_of_sneaks_while_that_switch_is_off(tmp_path):
    rig = rig_for(tmp_path)
    usable = rig.rules.offense.usable(rig.engine.s)
    assert not {"O046", "O047", "O048", "O121"} & usable
    on = rig_for(tmp_path / "on", qb_on=True)
    assert {"O046", "O047", "O048", "O121"} <= on.rules.offense.usable(on.engine.s)


# ----- letters, plus and minus, Shift, D -----

def test_t_is_never_a_letter_of_any_level_of_the_offense_menus(tmp_path):
    rig = rig_for(tmp_path, qb_on=True, timeouts_on=True, extras=dict(again=["O027", ""]))
    flow = rig.rules.offense
    flow.favourites = (("O001",), ())
    s = rig.engine.s
    levels = [lambda: None, lambda: flow.menus.enter(PM.Item("", -1, "", (PM.MORE, 0))),
              lambda: flow.menus.enter(PM.Item("", -1, "", (PM.FAVOURITES, 0))),
              lambda: flow.menus.enter(PM.Item("", -1, "", (PM.SETTINGS, 0)))]
    for go in levels:
        flow.reset()
        go()
        letters = [i.letter for i in rig.rules.offense_menu(s, False) if i.letter]
        assert "t" not in letters and "d" not in letters and len(letters) == len(set(letters)), letters
    for group in C.GROUPS:
        if group.side == "O":
            flow.menus._open(group.key, PM.TOP)
            assert "t" not in [i.letter for i in rig.rules.offense_menu(s, False) if i.letter]


def test_plus_adds_the_play_to_the_favourites_and_the_top_offers_them_and_minus_takes_it_off(tmp_path):
    rig = rig_for(tmp_path, answers=[RIGHT, PLUS_MAIN, SHIFT, MINUS_PAD, PLUS_PAD, LEFT, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    assert said.count(X.text("NXB-58")) == 2 and said.count(X.text("NXB-59")) == 1
    flow = rig.rules.offense
    assert flow.favourites[0] == ("O001",) and rig.game.favourite_plays == (("O001",), ())
    assert " 8. Favourites " in items_of(rig)


def test_a_lone_shift_says_nothing_and_the_menu_waits_for_the_next_key(tmp_path):
    rig = rig_for(tmp_path, answers=[SHIFT, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    assert texts(rig, mark) == [SELECT, TOP_WEST[0]]
    s = rig.engine.s
    item = rig.rules.offense_menu(s, False)[0]
    assert rig.rules.menu_key(s, "", item, "16") == MENU_QUIET


def test_a_keypad_digit_whose_character_is_a_letter_is_never_that_letter(tmp_path):
    # keypad 4 is code 100, character "d": with no item 4 (one play, Back and Save Game) it is not D (the description); B-W6
    rig = rig_for(tmp_path)
    flow = rig.rules.offense
    flow.favourites = (("O001",), ())
    flow.menus.enter(PM.Item("", -1, "", (PM.FAVOURITES, 0)))
    rig.keys.answers = [KEYPAD_4, ESCAPE]
    mark = len(rig.said)
    the_menu(rig)
    assert DS.text(DS.play_row("O001")) not in texts(rig, mark)


def test_d_describes_the_current_item_of_the_catalogs_menus(tmp_path):
    rig = rig_for(tmp_path, answers=["d", RIGHT, "d", ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    assert DS.text("NXB-E01") in said and DS.text(DS.play_row("O001")) in said


def test_a_play_is_again_after_it_was_run_and_a_is_its_letter(tmp_path):
    rig = rig_for(tmp_path, extras=dict(again=["O027", ""]))
    items = rig.rules.offense_menu(rig.engine.s, False)
    again = [i for i in items if i.letter == "a"]
    assert again and again[0].text == " 8. %s, %s " % (X.text("NXB-52").strip(), name("O027"))
    rig.keys.answers = ["a", ENTER]
    assert the_menu(rig) == "offense_chosen" and rig.rules.offense.called == "O027"


def test_a_played_catalog_call_becomes_again_and_the_menu_is_at_its_top(tmp_path):
    rig = rig_for(tmp_path)
    flow = rig.rules.offense
    flow.called = "O027"
    from nfl4.game.outcome import PlayOutcome
    outcome = PlayOutcome("pass complete", 1, 4, 5)
    flow.menus._open("og06", PM.TOP)
    flow.finish(rig.engine.s, outcome)
    assert outcome.catalog == "O027" and rig.engine.s.extras.again[0] == "O027" and flow.menus.level == PM.TOP and flow.called == ""


# ----- Formation and Tempo -----

def test_enter_on_a_setting_changes_its_value_and_the_item_says_it(tmp_path):
    rig = rig_for(tmp_path, answers=["o", ENTER, ENTER, ENTER, DOWN, DOWN, DOWN, DOWN, ENTER, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    x = rig.engine.s.extras
    assert x.play_settings == {"formation": "shotgun", "tempo": "no_huddle"}
    assert " 1. Formation, under center " in said and " 1. Formation, shotgun " in said and " 5. Tempo, no huddle " in said


def test_a_setting_goes_around_to_the_playbooks_choice_and_is_then_left_out(tmp_path):
    rig = rig_for(tmp_path)
    flow, s = rig.rules.offense, rig.engine.s
    for _ in C.SETTINGS["side"]:
        flow.change_setting(s, "side")
    assert "side" not in s.extras.play_settings


# ----- kneel and spike -----

def test_kneel_is_offered_when_a_lead_can_run_the_clock_out_and_spike_when_the_clock_runs_late(tmp_path):
    lead = rig_for(tmp_path, quarter=4, down=1, extras=dict(left=100, running=True))
    lead.engine.s.stats[1].score = 7
    letters = [i.letter for i in lead.rules.offense_menu(lead.engine.s, False)]
    assert "k" in letters and "p" in letters
    behind = rig_for(tmp_path / "behind", quarter=4, down=1, extras=dict(left=100, running=False))
    letters = [i.letter for i in behind.rules.offense_menu(behind.engine.s, False)]
    assert "k" not in letters and "p" not in letters
    early = rig_for(tmp_path / "early", quarter=1, down=1, extras=dict(left=100, running=True))
    assert "k" not in [i.letter for i in early.rules.offense_menu(early.engine.s, False)]
    fourth = rig_for(tmp_path / "fourth", quarter=2, down=4, extras=dict(left=60, running=True))
    assert "p" not in [i.letter for i in fourth.rules.offense_menu(fourth.engine.s, False)]


def test_k_calls_the_kneel_and_p_the_spike(tmp_path):
    rig = rig_for(tmp_path, answers=["k", ENTER], quarter=4, extras=dict(left=100, running=True))
    rig.engine.s.stats[1].score = 7
    assert the_menu(rig) == "offense_chosen" and rig.rules.offense.called == "O152" and rig.engine.s.offense_play == 1
    rig = rig_for(tmp_path / "p", answers=["p", ENTER], quarter=2, extras=dict(left=50, running=True))
    assert the_menu(rig) == "offense_chosen" and rig.rules.offense.called == "O153" and rig.engine.s.offense_play == 4


# ----- the search -----

def test_find_a_play_by_name_types_letters_t_included_and_lists_what_it_found(tmp_path):
    rig = rig_for(tmp_path, answers=["m", ENTER, "n", ENTER, "t", "r", "i", "p", ENTER, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    assert X.text("NXB-56") in said
    assert X.text("NXB-H14", list=X.text("NXB-53").strip()) in said
    assert any("Triple Option" in t for t in said)


def test_a_name_nobody_has_says_so_and_the_menu_stays(tmp_path):
    rig = rig_for(tmp_path, answers=["m", ENTER, "n", ENTER, "z", "z", "q", ENTER, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    assert X.text("NXB-57") in texts(rig, mark)


# ----- the try -----

def test_the_try_offers_the_five_families_more_plays_and_the_formation_and_no_tail(tmp_path):
    rig = rig_for(tmp_path, two_point=True, yard_line=2, half=1, timeouts_on=True)
    assert items_of(rig) == [" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass ",
                             " 6. More Plays ", " 7. Formation and Tempo "]


def test_a_withdrawn_play_and_a_kick_off_leave_nothing_called(tmp_path):
    rig = rig_for(tmp_path)
    flow = rig.rules.offense
    flow.called = "O027"
    rig.rules.withdraw_play(rig.engine.s)
    assert flow.called == "" and flow.result is None
    flow.called = "O027"
    rig.keys.answers = [ENTER]                       # SX.10d: the player's 2026 kick-off menu, Enter takes the deep kick
    rig.rules.before_kickoff(rig.engine.s, 1)
    assert flow.called == ""


@pytest.mark.parametrize("level", [PM.TOP, PM.MORE_LEVEL, PM.SETTINGS_LEVEL])
def test_every_item_of_the_offense_menus_has_a_description(tmp_path, level):
    rig = rig_for(tmp_path, qb_on=True, timeouts_on=True)
    flow = rig.rules.offense
    flow.menus.level = level
    for item in rig.rules.offense_menu(rig.engine.s, False):
        if flow.owns(item.action):
            assert flow.describe_row(item.action), item
    for group in C.GROUPS:
        if group.side == "O":
            flow.menus._open(group.key, PM.TOP)
            for item in rig.rules.offense_menu(rig.engine.s, False):
                if flow.owns(item.action):
                    assert DS.text(flow.describe_row(item.action)), item
