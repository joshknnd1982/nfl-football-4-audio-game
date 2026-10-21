"""The catalog's defense menus in the game, the kick defense, the personnel and the model against the computer's offense (nfl4 only,
rule 0.13; NX-P2 to NX-P8, NX-H1; NFL_PLAYS_DESIGN 0 Q-P13, 2 and 7; PX SX.10d, D-094). This is inspired by Jim Kitchen.

The menus of extras/plays/play_menus.py (side D) reach the player through the engine's menu loop and the H3 hooks, as the offense's did in
SX.10c: the original's six calls first with their digits, Enter on a call is the playbook's pick, Right opens a call's lists, Left and
Backspace go back, F, A, M, O, P Kick Defense on fourth down, plus and minus, D. The player's call is played by the outcome models against
the computer's offense (its style's play or a stand-in), with the defense's personnel matched to the offense's.
"""
import random

import pytest

from nfl4.extras import defense_flow as DF
from nfl4.extras import nx_texts as X
from nfl4.extras import playbooks as PB
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import calling as K
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import descriptions as DS
from nfl4.extras.plays import personnel
from nfl4.extras.plays import play_menus as PM
from nfl4.extras.state import ExtrasRecord
from nfl4.game import menus
from nfl4.game import phrases as P
from nfl4.game.rules import CLASSIC
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps

ENTER, ESCAPE, UP, DOWN, BACKSPACE, LEFT, RIGHT = 13, 27, 38, 40, 8, 37, 39
PLUS_MAIN, MINUS_PAD = 187, 109
SELECT_D = " Kim" + P.SELECT_DEFENSE
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=2, defense=1, half=2, yard_line=30, down=1, to_go=10, quarter=1)
TOP = [" 1. Goal Line ", " 2. Short Run ", " 3. Long Run ", " 4. Blitz ", " 5. Short Pass ", " 6. Long Pass ", " 7. More Plays ",
       " 8. Formation and Tempo ", " 9. Save Game "]


def rig_for(tmp_path, answers=(), defense="pressure", timeouts_on=False, extras=None, **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=timeouts_on, offense_book="classic", defense_book=defense)
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, extras=extras, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def items_of(rig):
    return [i.text for i in rig.rules.defense_menu(rig.engine.s)]


def the_menu(rig, draws=None):
    return run_steps(rig, rig.engine.defense_menu, draws or Draws(), until=MENU_UNTIL)


# ----- which menu -----

def test_a_defense_playbook_gives_the_catalogs_six_calls_more_plays_and_formation(tmp_path):
    rig = rig_for(tmp_path)
    assert items_of(rig) == TOP
    items = rig.rules.defense_menu(rig.engine.s)
    assert [i.digit for i in items][:9] == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert items[6].letter == "m" and items[7].letter == "o" and items[8].letter == "s"
    assert items[0].action == ("pd:pick", 1) and items[5].action == ("pd:pick", 6)


def test_the_classic_playbook_and_classic_keep_the_originals_six_calls(tmp_path):
    rig = rig_for(tmp_path, defense="classic")
    assert items_of(rig) == [" 1. Goal Line ", " 2. Short Run ", " 3. Long Run ", " 4. Blitz ", " 5. Short Pass ", " 6. Long Pass ",
                             " 7. Save Game "]
    assert rig.rules.defense.active(rig.engine.s) is False
    assert CLASSIC.special_kick(rig.engine.s, "punt") is None and CLASSIC.defense_menu(rig.engine.s) == menus.defense_menu()


def test_on_fourth_down_p_opens_the_kick_defense(tmp_path):
    rig = rig_for(tmp_path, down=4)
    items = rig.rules.defense_menu(rig.engine.s)
    kick = [i for i in items if i.letter == "p"]
    assert kick and kick[0].text == " 8. Kick Defense " and kick[0].action == ("pd:open", "kg04")
    first = rig_for(tmp_path / "first")
    assert "p" not in [i.letter for i in first.rules.defense_menu(first.engine.s)]


def test_t_d_and_s_are_never_letters_of_the_defense_menus_and_each_level_has_unique_letters(tmp_path):
    rig = rig_for(tmp_path, down=4, timeouts_on=True, extras=dict(again=["", "D017"]))
    flow, s = rig.rules.defense, rig.engine.s
    rig.rules.offense.favourites = ((), ("D017",))
    for go in (lambda: None, lambda: flow.menus.enter(PM.Item("", -1, "", (PM.MORE, 0))),
               lambda: flow.menus.enter(PM.Item("", -1, "", (PM.FAVOURITES, 0))),
               lambda: flow.menus.enter(PM.Item("", -1, "", (PM.SETTINGS, 0)))):
        flow.reset()
        go()
        letters = [i.letter for i in rig.rules.defense_menu(s) if i.letter]
        assert "t" not in letters and "d" not in letters and len(letters) == len(set(letters)), letters
    for group in C.GROUPS:
        if group.side == "D" or group.key == "kg04":
            flow.menus._open(group.key, PM.TOP)
            assert "t" not in [i.letter for i in rig.rules.defense_menu(s) if i.letter]


# ----- the keys -----

def test_right_opens_a_calls_lists_with_their_heading_and_left_goes_back(tmp_path):
    rig = rig_for(tmp_path, answers=["5", RIGHT, RIGHT, LEFT, ESCAPE])
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    said = texts(rig, mark)
    assert X.text("NXB-H13", list="Zone Coverages", n=1, m=2) in said and X.text("NXB-H13", list="Man Coverages", n=2, m=2) in said
    assert said[-2:] == [SELECT_D, " 1. Goal Line "]


def test_enter_on_a_call_of_a_list_calls_it_and_the_engine_gets_the_originals_call(tmp_path):
    rig = rig_for(tmp_path, answers=["6", RIGHT, "3", ENTER])
    assert the_menu(rig) == "defense_chosen"
    third = PM.concepts_of("dg09", rig.rules.defense.context(rig.engine.s))[2]
    assert rig.rules.defense.called == third.id and rig.engine.s.defense_play == 6 == third.family


def test_enter_on_one_of_the_six_calls_is_the_styles_pick_said_before_the_snap(tmp_path):
    # SX.10e (D-095): the pick is the calling's weights over the family's calls for the style and the offense's situation, one draw
    rig = rig_for(tmp_path, answers=["4", ENTER])
    s, books = rig.engine.s, rig.rules.books
    family = [c for g in PM.family_groups("D", 4) for c in PM.concepts_of(g, rig.rules.defense.context(s)) if c.side == "D"]
    weights = K.defense_weights(family, "pressure", books.own_plays("pressure", "D"), books.call_situation(s))
    assert {i for i, _w in weights} <= {c.id for c in family} and len(weights) > 5
    assert the_menu(rig, Draws().below(sum(w for _i, w in weights), 0)) == "defense_chosen"
    pick = weights[0][0]
    assert rig.rules.defense.called == pick and rig.engine.s.defense_play == 4
    assert X.text("NXB-H15", name=PB.DEFAULT_TABLE.name(pick)) in texts(rig)


def test_the_kick_defense_is_set_said_kept_and_the_menu_goes_back_to_its_top(tmp_path):
    rig = rig_for(tmp_path, down=4, answers=["p", ENTER, "3", ENTER, ESCAPE])
    mark = len(rig.said)
    assert the_menu(rig) == "concede"
    x = rig.engine.s.extras
    assert x.kick_defense == "K033" and X.text("NXB-J22", name="Punt Block") in texts(rig, mark)
    assert rig.rules.defense.called == "" and texts(rig, mark)[-2:] == [SELECT_D, " 1. Goal Line "]
    back = ExtrasRecord.from_json(x.to_json())
    assert back.kick_defense == "K033"
    rig.rules.kicks.set_kick_defense(rig.engine.s, "K031")
    assert x.kick_defense == ""                            # the return is the default and is kept as ""


def test_a_damaged_kick_defense_or_kick_call_in_a_save_is_refused():
    record = ExtrasRecord()
    for name, bad in (("kick_defense", "K011"), ("kick_defense", "D017"), ("kick_call", "K031"), ("kick_call", 3),
                      ("fair_catch_kick", 1)):
        setattr(record, name, bad)
        with pytest.raises(ValueError):
            ExtrasRecord.from_json(record.to_json())
        setattr(record, name, ExtrasRecord().__dict__[name])
    old = ExtrasRecord.from_json('{"rules_year": %d}' % ExtrasRecord().rules_year)        # a record saved before SX.10d
    assert old.kick_defense == "" and old.kick_call == "" and old.fair_catch_kick is False


def test_plus_and_minus_keep_the_defenses_favourites_in_the_second_half_of_the_file(tmp_path):
    rig = rig_for(tmp_path, answers=["1", RIGHT, PLUS_MAIN, DOWN, PLUS_MAIN, MINUS_PAD, LEFT, ESCAPE])
    rig.rules.offense.favourites = (("O027",), ())
    the_menu(rig)
    first, second = PM.concepts_of("dg01", rig.rules.defense.context(rig.engine.s))[:2]
    assert rig.rules.offense.favourites == (("O027",), (first.id,)) and rig.game.favourite_plays == (("O027",), (first.id,))
    assert second.id not in rig.rules.offense.favourites[1]
    assert " 7. Favourites " in items_of(rig)


def test_d_describes_the_current_item_and_every_item_of_the_defense_menus_has_a_description(tmp_path):
    rig = rig_for(tmp_path, answers=["d", RIGHT, "d", ESCAPE], down=4)
    mark = len(rig.said)
    the_menu(rig)
    said = texts(rig, mark)
    assert DS.text("NXB-E11") in said and DS.text(DS.play_row(PM.concepts_of("dg01", rig.rules.defense.context(rig.engine.s))[0].id)) in said
    flow, s = rig.rules.defense, rig.engine.s
    for level in (PM.TOP, PM.MORE_LEVEL, PM.SETTINGS_LEVEL):
        flow.reset()
        flow.menus.level = level
        for item in rig.rules.defense_menu(s):
            if flow.owns(item.action):
                assert DS.text(flow.describe_row(item.action)), item
    for group in C.GROUPS:
        if group.side == "D" or group.key == "kg04":
            flow.menus._open(group.key, PM.TOP)
            for item in rig.rules.defense_menu(s):
                if flow.owns(item.action):
                    assert DS.text(flow.describe_row(item.action)), item


def test_the_defense_settings_are_personnel_and_shade_and_go_around(tmp_path):
    rig = rig_for(tmp_path, answers=["o", ENTER, ENTER, DOWN, ENTER, ENTER, ESCAPE])
    mark = len(rig.said)
    the_menu(rig)
    x = rig.engine.s.extras
    assert x.play_settings == {"defense_personnel": "base 4-3", "coverage_shade": "off"}
    assert " 1. Defensive Personnel, base 4-3 " in texts(rig, mark) or any("Defensive Personnel" in t for t in texts(rig, mark))


# ----- the personnel (Q-P13) -----

@pytest.mark.parametrize("people, to_goal, backs", [("11", 30, 5), ("12", 30, 4), ("21", 30, 4), ("10", 30, 6), ("00", 30, 6),
                                                    ("22", 2, 3), ("13", 3, 3), ("12", 2, 4), ("11", 1, 5)])
def test_the_matched_defensive_backs_follow_the_offenses_receivers(people, to_goal, backs):
    assert personnel.matched_backs(people, to_goal) == backs


def test_the_box_moves_one_man_at_most_and_stays_five_to_eight_and_the_shade_replaces_press_or_off():
    goal_line = C.BY_ID["D001"].params            # 3 backs, a box of 8
    played = personnel.adjust(goal_line, "11", 30)
    assert played.backs == 5 and played.box == 7 and played.coverage == goal_line.coverage
    dime = C.BY_ID["D055"].params                 # 6 backs, a box of 6
    assert personnel.adjust(dime, "21", 30).box == 7 and personnel.adjust(dime, "10", 30).box == 6
    assert personnel.adjust(dime, "11", 30, setting="heavy").backs == 3
    for call in C.DEFENSE:
        for people in ("11", "12", "21", "22", "10", "00", "13"):
            box = personnel.adjust(call.params, people, 30).box
            assert 5 <= box <= 8 and abs(box - call.params.box) <= 1
    press = C.BY_ID["D030"].params
    assert "off" in personnel.adjust(press, "11", 30, shade="off").tags and "press" not in personnel.adjust(press, "11", 30,
                                                                                                         shade="off").tags
    assert personnel.adjust(press, "11", 30).tags == press.tags


def test_the_computers_call_is_matched_to_the_players_personnel(tmp_path):
    rules = NflRules(timeouts_on=False, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules, wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
    s = rig.engine.s
    s.defense_play = 1                                   # the stand-in D002 Goal Line Stack: 3 backs, a box of 8
    _id, call = rules.offense.defense_call(s, C.BY_ID["O027"])          # Mesh Crossers: one back, one tight end
    assert call.backs == 5 and call.box == 7
    s.extras.play_settings["personnel"] = "22"           # the player's two backs, two tight ends at the goal line: the heavy package
    s.half, s.yard_line = 1, 2
    _id, call = rules.offense.defense_call(s, C.BY_ID["O027"])
    assert call.backs == 3 and call.box == 8


# ----- the model against the computer's offense -----

def test_the_players_call_is_played_by_the_model_against_the_computers_stand_in(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    rig.rnd.source = random.Random(4)
    rules.defense.called = "D011"                       # Cover Zero Blitz
    s.offense_play = 3                                   # the computer's Screen Pass: the stand-in Running Back Screen
    result = rules.model_play(s)
    assert result is not None and rules.offense.played == "O017"
    play, call, kind, yards, backs, box = rules.defense.events[-1]
    assert (play, call, kind, yards) == ("O017", "D011", result.kind, result.yards) and backs == 5
    rules.defense.called = ""
    assert rules.model_play(s) is None                   # no call of the catalog: the original's tables


def test_the_computers_style_play_is_used_when_it_has_one_of_the_family(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    rig.rnd.source = random.Random(5)
    rules.defense.called = "D017"
    s.offense_play = 1
    rules.books.offense_id = "O002"                      # an SX.7 style play of Line Plunge
    rules.model_play(s)
    assert rules.defense.events[-1][0] == "O002"
    rules.books.offense_id = "O017"                      # not of the family the engine plays: the stand-in
    s.offense_play = 1
    rules.model_play(s)
    assert rules.defense.events[-1][0] == DF.STAND_INS[1]


def test_a_kick_or_a_try_is_never_played_by_the_defenses_model(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    rules.defense.called = "D017"
    for play in (6, 7):
        s.offense_play = play
        assert rules.model_play(s) is None
    s.offense_play, s.two_point = 1, True
    assert rules.model_play(s) is None


def test_the_call_becomes_again_and_the_menu_is_at_its_top_after_the_play(tmp_path):
    from nfl4.game.outcome import PlayOutcome
    rig = rig_for(tmp_path)
    flow = rig.rules.defense
    flow.called = "D017"
    flow.menus._open("dg07", PM.TOP)
    flow.finish(rig.engine.s, PlayOutcome("run", 2, 1, 5))
    assert rig.engine.s.extras.again[1] == "D017" and flow.called == "" and flow.menus.level == PM.TOP
    items = rig.rules.defense_menu(rig.engine.s)
    again = [i for i in items if i.letter == "a"]
    assert again and again[0].action == ("pd:again", "D017")
