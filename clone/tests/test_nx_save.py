"""The extras' section of football.sav and which rules a loaded game is played with (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN
12.3, NFL_EXTRA_FEATURES C1 and C10; PX SX.2). This is inspired by Jim Kitchen.

A Classic save is the S7.5 file byte for byte; a save of the N. F. L. rules adds a marker, a format number and one JSON
string; a damaged or newer record keeps the original's values and starts the extras fresh with one spoken notice; a Classic
program asks once whether to play such a save with the N. F. L. rules.
"""
import json
import random

import pytest

from nfl4.data.files import savedgame
from nfl4.data.files.variant import FileDamaged, pack_integer, pack_string
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.saved import rules_for_saved_game
from nfl4.extras.state import ExtrasRecord
from nfl4.game.gamestate import GameState, SavedGame, SideStats
from nfl4.game.rules import CLASSIC
from nflrig import nfl_engine_rig
from pagrig import make_rig

ENTER, DOWN = 13, 40


def a_save(**fields):
    stats = {1: SideStats(score=7, first_downs=3), 2: SideStats(score=3)}
    values = dict(wisoff=1, defense=2, half=2, quarter=2, counter=10, plays=[33, 34, 35, 30, 31], countdown=100,
                  stats=stats, yard_line=30, down=2, to_go=7, opponent_quarterback="Unitas", opening_receiver=2)
    values.update(fields)
    return SavedGame(**values)


def a_record(**fields):
    record = ExtrasRecord(period=2, left=333, pending=12, running=True, timeouts=[1, 2], used=[2, 1], unit="H1",
                          announced="H1", plays=40, handled=40, recent={"TO": ["TO02"]})
    for name, value in fields.items():
        setattr(record, name, value)
    return record


# ----- the record -----

def test_the_record_goes_to_json_and_back_whole():
    record = a_record()
    again = ExtrasRecord.from_json(record.to_json())
    assert again == record


@pytest.mark.parametrize("text", ["", "not json", "[]", "1", '{"left": -1}', '{"left": 901}', '{"left": 1.5}',
                                  '{"left": true}', '{"timeouts": [3]}', '{"timeouts": [4, 3]}', '{"timeouts": [3, "3"]}',
                                  '{"running": 1}', '{"unit": 5}', '{"recent": {"TO": [1]}}', '{"recent": []}',
                                  '{"rules_year": 2025}', "[" * 5000 + "]" * 5000])
def test_a_record_that_is_not_whole_and_sensible_is_refused(text):
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(text)


def test_unknown_names_in_the_record_are_ignored():
    data = json.loads(a_record().to_json())
    data["a_later_field"] = [1, 2, 3]
    assert ExtrasRecord.from_json(json.dumps(data)) == a_record()


def test_a_fuzz_of_damaged_records_raises_only_value_error():
    rng = random.Random(11)
    base = a_record().to_json()
    for _ in range(400):
        chars = list(base)
        for _ in range(rng.randint(1, 6)):
            at = rng.randrange(len(chars))
            chars[at] = rng.choice('{}[]",:0123456789 truefalsn-.x')
        try:
            ExtrasRecord.from_json("".join(chars)).check()
        except ValueError:
            pass


# ----- the file -----

def test_a_classic_save_is_the_same_bytes_as_before_the_extras():
    plain = savedgame.encode(a_save())
    assert savedgame.decode(plain) == a_save()
    assert b"NX-EXTRAS" not in plain
    assert savedgame.decode(plain).extras_marked is False


def test_a_save_with_the_extras_writes_the_marker_the_format_and_the_record_after_the_original_values():
    record = a_record().to_json()
    raw = savedgame.encode(a_save(extras=record, extras_marked=True))
    plain = savedgame.encode(a_save())
    assert raw.startswith(plain)
    assert raw[len(plain):] == pack_string(b"NX-EXTRAS") + pack_integer(1) + pack_string(record.encode("utf-8"))
    decoded = savedgame.decode(raw)
    assert decoded.extras == record and decoded.extras_marked and decoded.opening_receiver == 2


def test_the_extras_without_the_opening_receiver_still_read():
    record = a_record().to_json()
    decoded = savedgame.decode(savedgame.encode(a_save(opening_receiver=None, extras=record, extras_marked=True)))
    assert decoded.opening_receiver is None and decoded.extras == record


def test_a_newer_format_or_a_record_that_is_not_text_keeps_the_marker_and_drops_the_record():
    plain = savedgame.encode(a_save())
    for tail in (pack_string(b"NX-EXTRAS") + pack_integer(2) + pack_string(b"{}"),
                 pack_string(b"NX-EXTRAS") + pack_integer(1) + pack_string(b"\xff\xfe\x00bad"),
                 pack_string(b"NX-EXTRAS") + pack_integer(1),
                 pack_string(b"NX-EXTRAS") + pack_integer(1) + pack_string(b"{}") + pack_integer(5)):
        decoded = savedgame.decode(plain + tail)
        assert decoded.extras is None and decoded.extras_marked
        assert decoded.yard_line == 30 and decoded.stats[1].score == 7         # the original's values still load


def test_anything_else_after_the_game_is_a_damaged_file_as_before():
    plain = savedgame.encode(a_save())
    for tail in (pack_integer(1), pack_string(b"SOMETHING"), b"\x08\x00\xff\xff"):
        with pytest.raises(FileDamaged):
            savedgame.decode(plain + tail)


# ----- the game state (H5) -----

def test_save_game_in_nfl_mode_writes_the_record_and_loading_it_restores_the_whole_record(tmp_path):
    rig = nfl_engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=30, quarter=2, counter=10,
                         extras=dict(left=333, pending=12, running=True, timeouts=[1, 2], used=[2, 1], period=2))
    kept = []
    rig.engine.save_sink = kept.append
    rig.engine.save_game()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    assert saved.extras_marked
    state = GameState()
    rules = NflRules()
    rules.period_clock(rig.game, state)
    state.load(saved)
    assert state.extras == rig.engine.s.extras


def test_a_classic_save_loaded_with_the_nfl_rules_starts_the_extras_from_their_start_values(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    for quarter, counter, left, given in ((1, 10, 620, False), (2, 30, 60, True), (3, 0, 900, False),
                                          (4, 29, 88, True), (5, 3, 516, False)):
        state = GameState()
        NflRules().period_clock(rig.game, state)
        state.load(a_save(quarter=quarter, counter=counter, opening_receiver=None))
        x = state.extras
        assert (x.left, x.warning_given, x.pending, x.running) == (left, given, 0, False), quarter
        assert x.timeouts == ([2, 2] if quarter == 5 else [3, 3]) and x.announced == x.unit


def test_a_damaged_record_loads_with_the_start_values(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    state = GameState()
    NflRules().period_clock(rig.game, state)
    state.load(a_save(extras='{"left": 5000}', extras_marked=True))
    assert state.extras.left == 900 - 28 * 10 and state.extras.timeouts == [3, 3]


def test_a_classic_game_state_ignores_the_extras_of_a_save():
    state = GameState()
    state.load(a_save(extras=a_record().to_json(), extras_marked=True))
    assert state.extras is None and state.saved(100).extras is None


# ----- which rules a loaded game is played with -----

def program(tmp_path, answers=(), rules=None):
    rig = make_rig(tmp_path, answers=answers)
    if rules is not None:
        rig.game.rules = rules
    return rig


def test_a_classic_program_asks_once_and_yes_plays_the_save_with_the_nfl_rules(tmp_path):
    rig = program(tmp_path, answers=[ENTER])
    rules = rules_for_saved_game(rig.game, a_save(extras=a_record().to_json(), extras_marked=True))
    assert isinstance(rules, NflRules) and rig.game.rules is CLASSIC          # the setting stays Classic
    assert [t for t, _, _ in rig.said] == [X.text("NXM-24"), " yes "]


def test_no_plays_the_save_as_classic(tmp_path):
    rig = program(tmp_path, answers=["n", ENTER])
    assert rules_for_saved_game(rig.game, a_save(extras=a_record().to_json(), extras_marked=True)) is CLASSIC
    assert [t for t, _, _ in rig.said] == [X.text("NXM-24"), " yes ", "n", " no "]


def test_the_question_toggles_with_up_and_down_and_f1_asks_again(tmp_path):
    rig = program(tmp_path, answers=[DOWN, 112, ENTER])
    assert rules_for_saved_game(rig.game, a_save(extras=a_record().to_json(), extras_marked=True)) is CLASSIC
    said = [t for t, _, _ in rig.said]
    assert said == [X.text("NXM-24"), " yes ", " no ", X.text("NXM-24"), " no "]


def test_a_damaged_record_is_said_when_the_nfl_rules_play_it(tmp_path):
    rig = program(tmp_path, rules=NflRules())
    assert rules_for_saved_game(rig.game, a_save(extras=None, extras_marked=True)) is None
    assert [t for t, _, _ in rig.said] == [X.text("NXM-25")]
    rig = program(tmp_path / "b", answers=[ENTER])
    assert isinstance(rules_for_saved_game(rig.game, a_save(extras="{", extras_marked=True)), NflRules)
    assert [t for t, _, _ in rig.said][-1] == X.text("NXM-25")


class SameRules(NflRules):
    """The same object for the game (so the test can read its record after the game)."""

    def for_game(self):
        return self


def test_an_nfl_game_saved_through_the_menu_after_a_timeout_loads_with_its_record(tmp_path):
    import re
    from nfl4.data.files.store import FileProgramStore
    from pagrig import play
    store = FileProgramStore(str(tmp_path / "data"), str(tmp_path / "data" / "customize"))
    rig = make_rig(tmp_path / "a", rng=random.Random(8), fast=True)
    called = []

    def saver(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Time Out ") and not called:
            called.append(1)
            return ENTER
        if last.endswith("Save Game ") and called:
            return ENTER
        if re.match(r"^ \d\. ", last):
            return "s" if called else "t"
        return ENTER
    rig.keys.policy = saver
    first = SameRules()
    result = play(rig, rules=first, save_sink=store.save_game)
    assert result.saved and first.state.extras.used[0] == 1
    saved = store.take_saved_game()
    assert saved.extras_marked and saved.extras is not None
    rig2 = make_rig(tmp_path / "b", rng=random.Random(9), fast=True)
    second = SameRules()
    result = play(rig2, rules=second, saved=saved)
    assert result.scores is not None and second.state.extras.used[0] >= 1      # the game's record came back
    assert " getting saved game " in [t for t, _, _ in rig2.said]


def test_a_save_without_extras_asks_nothing_in_either_mode(tmp_path):
    for rules in (None, NflRules()):
        rig = program(tmp_path / str(rules is None), rules=rules)
        assert rules_for_saved_game(rig.game, a_save()) is None and rig.said == []
