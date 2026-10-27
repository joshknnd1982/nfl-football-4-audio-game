"""The quarterback runs of the N. F. L. rules mode outside the plays themselves: the rows of the table, the menus and their
keys, the settings and the Rules menu, the remark pool QB and remarks.txt, the statistics, the help, the saved record and
Classic's no-ops (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 7, 10.4, 12; PX SX.5). This is inspired by Jim Kitchen.

Every expected number is worked out from the rule next to it, never from a run of the game (B-X38).
"""
from fractions import Fraction

import pytest

from nfl4.data import customlists as cl
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras import qb_runs as QB
from nfl4.extras import remarks as RM
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules, is_nfl, rules_from_settings
from nfl4.extras.state import ExtrasRecord
from nfl4.game import menus
from nfl4.game.playtables import QB_DRAW, QB_KEEPER, QB_SNEAK, QBRunEntry
from nfl4.extras.classic_radio import ClassicRadioRules
from nfl4.game.rules import CLASSIC, SCRAMBLE, ClassicRules
from nflrig import nfl_engine_rig
from pagrig import engine_rig
from randsources import ScriptedRandom

ENTER, F1, F2 = 13, 112, 113
GAME = "NFL Football 4"
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def rig_for(tmp_path, answers=(), qb_on=True, timeouts_on=True, comments=False, **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=timeouts_on, qb_on=qb_on)
    return nfl_engine_rig(tmp_path, answers=answers, comments=comments, rules=rules, **fields)


# ----- the rows of the table (design 7.1) -----

DESIGN_ROWS = {   # the design's table, call by call: Goal Line, Short Run, Long Run, Blitz, Short Pass, Long Pass
    "sneak": ((0, 2), (0, 3), (1, 4), (-1, 3), (1, 4), (1, 5)),
    "keeper": ((-2, 6), (-3, 5), (-4, 3), (-3, 15), (3, 12), (4, 14)),
    "draw": ((-1, 3), (-2, 3), (1, 6), (4, 16), (2, 9), (3, 12)),
}


def test_the_rows_are_the_designs_table_of_7_1():
    assert T.QB_ROWS == DESIGN_ROWS
    assert T.QB_SCRAMBLE_YARDS == (1, 14)
    assert T.QB_FUMBLE_ODDS == {"sneak": 100, "keeper": 90, "draw": 90, "scramble": 200}
    assert T.QB_OUT_OF_BOUNDS == {"sneak": 0, "keeper": 12, "draw": 5, "scramble": 34}


@pytest.mark.parametrize("kind", ["sneak", "keeper", "draw"])
@pytest.mark.parametrize("call", [1, 2, 3, 4, 5, 6])
def test_an_entry_is_a_row_with_one_more_than_the_most_yards(kind, call):
    low, high = DESIGN_ROWS[kind][call - 1]
    entry = QB.make_entry(kind, call)
    assert entry == QBRunEntry(kind, 4 if kind == "keeper" else None, T.QB_SOUND[kind], low, high + 1, T.QB_FUMBLE_ODDS[kind])


@pytest.mark.parametrize("call", [1, 2, 3, 4, 5, 6])
def test_the_scramble_has_one_row_for_every_defense_call(call):
    assert QB.make_entry("scramble", call) == QBRunEntry("scramble", None, 2, 1, 15, 200)


def test_the_scramble_gains_7_and_a_half_yards_on_average_and_the_rows_are_worked_out_by_hand():
    entry = QB.make_entry("scramble", 1)
    assert Fraction(sum(range(entry.low, entry.high)), entry.high - entry.low) == Fraction(15, 2)     # (1 + 14) / 2
    # the sneak on third or fourth and 1 against each call: the share of its yards that are 1 or more
    shares = []
    for low, high in DESIGN_ROWS["sneak"]:
        yards = list(range(low, high + 1))
        shares.append(Fraction(sum(1 for y in yards if y >= 1), len(yards)))
    assert shares == [Fraction(2, 3), Fraction(3, 4), 1, Fraction(3, 5), 1, 1]
    converted = sum(shares) / 6 * Fraction(99, 100)                                                   # the 1 in 100 fumble
    low, high = T.TARGET_QB_SHORT_CONVERSION
    assert Fraction(78, 100) <= converted <= Fraction(88, 100) and low <= float(converted) <= high    # 82.8 percent


def test_the_designed_rows_average_inside_the_target_when_every_call_is_equally_likely():
    means = {k: sum(Fraction(lo + hi, 2) for lo, hi in rows) / 6 for k, rows in DESIGN_ROWS.items()}
    assert means["sneak"] == Fraction(23, 12) and means["keeper"] == Fraction(25, 6) and means["draw"] == Fraction(14, 3)


@pytest.mark.parametrize("half, yard_line, wisoff, expected", [
    (2, 30, 1, 70),          # the Bengals on their own 30 (half 2 is theirs): 70 yards to go
    (1, 3, 1, 3),            # on the Jets' 3
    (1, 30, 2, 70),          # the Jets on their own 30 (half 1)
    (2, 5, 2, 5),            # the Jets on the Bengals' 5
])
def test_the_distance_to_the_goal_line(half, yard_line, wisoff, expected):
    from types import SimpleNamespace
    assert QB.to_goal(SimpleNamespace(half=half, yard_line=yard_line, wisoff=wisoff)) == expected


# ----- the menu (design 10.4) -----

def test_the_offense_menu_has_the_three_runs_before_time_out_and_save_game(tmp_path):
    rig = rig_for(tmp_path)
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.text for i in items] == [" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ",
                                       " 5. Long Pass ", " 6. Field Goal ", " 7. Punt ", " 8. Quarterback Sneak ",
                                       " 9. Quarterback Keeper ", " 10. Quarterback Draw ", " 11. Time Out ",
                                       " 12. Save Game "]
    assert [i.digit for i in items[:10]] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]       # the key 0 is item 10
    assert [i.action for i in items[7:10]] == [(menus.PLAY, 8), (menus.PLAY, 9), (menus.PLAY, 10)]
    assert (items[10].letter, items[11].letter) == ("", "s") and all(i.letter == "" for i in items[:10])


def test_with_time_outs_off_save_game_is_item_11(tmp_path):
    rig = rig_for(tmp_path, timeouts_on=False)
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.text for i in items][-3:] == [" 9. Quarterback Keeper ", " 10. Quarterback Draw ", " 11. Save Game "]
    assert items[-1].letter == "s" and items[-1].action == (menus.SAVE, 0)


def test_with_quarterback_runs_off_the_menu_is_the_one_of_time_outs(tmp_path):
    rig = rig_for(tmp_path, qb_on=False)
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.text for i in items][6:] == [" 7. Punt ", " 8. Time Out ", " 9. Save Game "]


def test_the_defense_menu_and_the_two_point_try_have_no_quarterback_runs(tmp_path):
    rig = rig_for(tmp_path)
    s = rig.engine.s
    assert [i.text for i in rig.rules.defense_menu(s)] == [" 1. Goal Line ", " 2. Short Run ", " 3. Long Run ", " 4. Blitz ",
                                                          " 5. Short Pass ", " 6. Long Pass ", " 7. Time Out ",
                                                          " 8. Save Game "]
    assert rig.rules.offense_menu(s, True) == menus.offense_menu(True)               # the try: the original's items 1 to 5


@pytest.mark.parametrize("key, play", [("8", QB_SNEAK), ("9", QB_KEEPER), ("0", QB_DRAW), (104, QB_SNEAK), (105, QB_KEEPER),
                                       (96, QB_DRAW)])
def test_the_keys_8_9_and_0_and_the_keypad_choose_the_runs(tmp_path, key, play):
    rig = rig_for(tmp_path, answers=[key, ENTER], timeouts_on=False)
    assert rig.engine.offense_menu() == rig.engine.offense_chosen
    assert rig.engine.s.offense_play == play
    said = texts(rig)
    assert said[2] == {QB_SNEAK: " 8. Quarterback Sneak ", QB_KEEPER: " 9. Quarterback Keeper ",
                       QB_DRAW: " 10. Quarterback Draw "}[play]


def test_the_key_1_still_chooses_item_1_not_item_11(tmp_path):
    rig = rig_for(tmp_path, answers=["1", ENTER])
    assert rig.engine.offense_menu() == rig.engine.offense_chosen and rig.engine.s.offense_play == 1


def test_the_key_0_in_a_classic_menu_is_only_echoed_as_before(tmp_path):
    rig = engine_rig(tmp_path, answers=["0", ENTER], wisoff=1, defense=2, half=2, yard_line=30)
    assert rig.engine.offense_menu() == rig.engine.offense_chosen and rig.engine.s.offense_play == 1
    assert texts(rig)[-1] == " 1. Line Plunge "


# ----- Classic: the hooks answer nothing and never draw -----

def test_classic_has_no_quarterback_runs_and_its_hooks_draw_nothing(tmp_path):
    rig = engine_rig(tmp_path, wisoff=1, defense=2)
    rig.rnd.source = ScriptedRandom([], strict=True)
    rules = rig.engine.rules
    assert rules is CLASSIC and isinstance(rules, ClassicRules)
    assert rules.instead_of_sack(rig.engine.s) is None and rules.instead_of_incompletion(rig.engine.s) is False
    assert rules.computer_offense(rig.engine.s) is None
    for call in (lambda: rules.qb_entry(rig.engine.s), lambda: rules.qb_narrate(rig.engine.s, None, "", ""),
                 lambda: rules.qb_slide(rig.engine.s)):
        with pytest.raises(RuntimeError, match="Classic"):
            call()
    assert SCRAMBLE == "scramble"
    s = rig.engine.s
    for play, ran in ((0, True), (1, True), (2, True), (3, False), (4, False), (5, False)):   # runs and kick-off returns
        s.offense_play = play
        assert rig.engine.ran() is ran
    s.offense_play, s.qb_run = 4, "scramble"                # a pass play that became a scramble is a run for its end
    assert rig.engine.ran() is True


def test_a_classic_game_never_has_a_quarterback_state(tmp_path):
    rig = engine_rig(tmp_path)
    s = rig.engine.s
    assert (s.qb_run, s.slid) == ("", False) and s.extras is None


# ----- the settings -----

def test_the_settings_read_and_write_the_quarterback_runs_line():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_qb_runs = off\n")
    assert problems == [] and settings.game.nx_qb_runs is False
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert problems == [] and again.game == settings.game
    assert "nx_qb_runs = off" in settingsfile.render(settings).splitlines()
    assert Settings.defaults().game.nx_qb_runs is True
    assert "nx_qb_runs" in settingsfile.HEADER


def test_a_bad_quarterback_runs_value_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_qb_runs = sometimes\n")
    assert len(problems) == 1 and settings.game.nx_qb_runs is True


def test_the_programs_rules_follow_the_quarterback_runs_setting():
    settings = Settings.defaults()
    settings.game.rules = "nfl"
    rules = rules_from_settings(settings.game)
    assert is_nfl(rules) and rules.qb_on is True
    settings.game.nx_qb_runs = False
    rules = rules_from_settings(settings.game)
    assert rules.qb_on is False and rules.for_game().qb_on is False
    settings.game.rules = "classic"
    assert isinstance(rules_from_settings(settings.game), ClassicRadioRules)


def test_a_rules_object_made_by_hand_has_no_quarterback_runs():
    assert NflRules().qb_on is False


# ----- the remark pool QB and remarks.txt -----

def entries_of(text):
    return cl.parse_list(cl.render_list(GAME, "remarks", RM.NOTES, []) + text, GAME, "remarks").entries


def pools_of(text):
    problems = cl.Problems("remarks.txt")
    return RM.build_pools(RM.overrides_of(entries_of(text), problems), problems), problems


def test_the_default_pool_is_the_five_lines_of_strings_nx():
    lines = RM.DEFAULT_POOLS.lines("QB")
    assert [r.id for r in lines] == ["QB01", "QB02", "QB03", "QB04", "QB05"] == list(X.REMARK_POOLS["QB"])
    assert [X.TEXTS[r.id] for r in lines] == [
        " <quarterback> keeps the ball ", " <quarterback> fakes the hand off and keeps it ",
        " <quarterback> pulls the ball down and runs ", " <quarterback> rolls out and takes off ",
        " <quarterback> drops back, then takes off "]
    assert all(X.SPEAKERS[r.id] == "say4" for r in lines)                            # play-by-play, not commentary


def test_a_line_of_the_pool_is_changed_switched_off_or_added_with_its_placeholders():
    pools, problems = pools_of("QB02 = <quarterback> hides the ball [bleep]\nQB03 = off\nQB06 = <team> are fooled [pause]\n"
                               "QB07 = <score> is nothing\n")
    ids = [r.id for r in pools.lines("QB")]
    assert ids == ["QB01", "QB02", "QB04", "QB05", "QB06", "QB07"]
    assert problems.count == 1 and "<score>" in problems.messages[0]                # an unknown placeholder is counted


def test_the_ids_of_the_pool_are_remark_ids_and_the_notes_tell_the_player():
    assert RM.parse_id("qb3") == ("QB", 3) and RM.parse_id("QB0") is None and RM.parse_id("QX01") is None
    notes = " ".join(RM.NOTES)
    assert "QB" in notes and "F8" in notes


def test_the_default_file_lists_the_pool_in_its_place_between_on_and_pn():
    pools = [e[0][:2] for e in RM.default_entries()]
    # the design's order (CUSTOMIZABLE_CONTENT 13): TO, the replay pools (SX.6: CH, CH, RV, RV), ON, QB, PN
    base = ["TO"] * 5 + ["CH"] * 7 + ["RV"] * 6 + ["ON"] * 3 + ["QB"] * 5 + ["PN"] * 4
    # SY.1: then BN, ASK and the analyst's pools; BC.3: then the radio format's 73 lines (SGN to CLK)
    assert pools[:len(base)] == base and len(pools) == len(base) + 142 + 12 + 158 + 73


# ----- the statistics and the help -----

def test_the_statistics_add_the_quarterback_runs_and_their_yards(tmp_path):
    rig = rig_for(tmp_path, timeouts_on=False)
    rig.engine.s.extras.qb_runs, rig.engine.s.extras.qb_yards = [3, 1], [21, -2]
    lines = rig.rules.extra_stats_lines(rig.engine.s)
    assert lines == [X.text("NXS-08"), "Bengals 3", "Jets 1", X.text("NXS-09"), "Bengals 21", "Jets -2"]
    assert X.text("NXS-08") == " Quarterback Runs" and X.text("NXS-09") == " Quarterback Running Yardage"


def test_without_the_switch_the_statistics_and_the_help_say_nothing_of_quarterback_runs(tmp_path):
    rig = rig_for(tmp_path, timeouts_on=False, qb_on=False)
    assert rig.rules.extra_stats_lines(rig.engine.s) == []
    names = {X.text(i) for i in ("NXH-18", "NXH-19", "NXH-20", "NXH-21")}
    for key in ("116", "117", "118"):
        assert not names & set(rig.rules.extra_help(key))


def test_the_help_of_f5_f6_and_f7_names_the_quarterback_runs_when_they_are_on(tmp_path):
    rig = rig_for(tmp_path, timeouts_on=False)
    from nflrig import feature_help
    assert feature_help(rig.rules, "116")[-1] == X.text("NXH-18")
    assert feature_help(rig.rules, "117")[-2:] == [X.text("NXH-19"), X.text("NXH-20")]
    assert feature_help(rig.rules, "118")[-1] == X.text("NXH-21")
    assert "8 is the quarterback sneak" in X.text("NXH-18") and "0 the draw" in X.text("NXH-18")


# ----- the saved record -----

def test_the_record_keeps_the_quarterback_values_in_json_and_checks_them():
    x = ExtrasRecord(qb_on=True, qb_runs=[4, 2], qb_yards=[17, -3])
    again = ExtrasRecord.from_json(x.to_json())
    assert (again.qb_on, again.qb_runs, again.qb_yards) == (True, [4, 2], [17, -3])


@pytest.mark.parametrize("field, value", [("qb_runs", [1]), ("qb_runs", [-1, 0]), ("qb_runs", "ab"), ("qb_yards", [0, 0, 0]),
                                          ("qb_yards", [1.5, 0]), ("qb_yards", [10 ** 7, 0]), ("qb_on", 1), ("qb_on", "yes")])
def test_a_damaged_quarterback_value_is_refused_whole(field, value):
    x = ExtrasRecord(qb_on=True)
    setattr(x, field, value)
    with pytest.raises(ValueError):
        x.check()


def test_a_record_saved_before_sx5_has_no_quarterback_runs():
    import json
    old = json.loads(ExtrasRecord().to_json())
    for name in ("qb_on", "qb_runs", "qb_yards"):
        del old[name]
    loaded = ExtrasRecord.from_json(json.dumps(old))
    assert (loaded.qb_on, loaded.qb_runs, loaded.qb_yards) == (False, [0, 0], [0, 0])


def test_a_game_made_by_the_rules_object_records_its_switch(tmp_path):
    assert rig_for(tmp_path).engine.s.extras.qb_on is True
    assert rig_for(tmp_path / "off", qb_on=False).engine.s.extras.qb_on is False


def test_save_game_writes_the_quarterback_counts_and_loading_restores_them_and_the_switch(tmp_path):
    from nfl4.data.files import savedgame
    from nfl4.game.gamestate import GameState
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False, qb_on=True), wisoff=1, defense=2, half=2, yard_line=30,
                         quarter=2, counter=10, extras=dict(left=333, qb_runs=[2, 1], qb_yards=[9, -3]))
    kept = []
    rig.engine.save_sink = kept.append
    rig.engine.save_game()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    assert saved.extras_marked
    state = GameState()
    rules = NflRules(timeouts_on=False, qb_on=False)                  # the program's switch is off now: the save keeps its own
    rules.period_clock(rig.game, state)
    state.load(saved)
    assert (state.extras.qb_on, state.extras.qb_runs, state.extras.qb_yards) == (True, [2, 1], [9, -3])
