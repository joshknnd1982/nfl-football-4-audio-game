"""The outcome tables against GAME_SPEC 5.9 and 5.10 (nfl4 hook H8). This is inspired by Jim Kitchen.

The numbers in game/playtables.py were read from the lifted lines (L44, L548, L360, L78c, L4f0 of every entry); the spec's
tables were written from the same lines in S3.4 and checked by script then. Here the two are compared, and the neutral
modifiers (Classic) change nothing.
"""
import re

from nfl4.game import playtables as T
from specfiles import SPEC, read_spec

PLAYS = {"Line Plunge": 1, "End Run": 2, "Screen Pass": 3, "Short Pass": 4, "Long Pass": 5}
DEFENSES = {"Goal Line": 1, "Short Run": 2, "Long Run": 3, "Blitz": 4, "Short Pass": 5, "Long Pass": 6}
SOUND_OF = {"foot4": 1, "foot5": 2, "foot6": 3}


def spec_section_59():
    text = read_spec(SPEC / "GAME_SPEC.md")
    start = text.index("### 5.9 Results of runs and passes")
    return text[start:text.index("### 5.10", start)]


def test_the_twelve_runs_have_the_yards_and_sounds_of_the_spec_table():
    rows = re.findall(r"^\| (Line Plunge|End Run) vs (.+?) \|.*\| (foot\d+), (-?\d+) to (-?\d+) \|$",
                      spec_section_59(), re.MULTILINE)
    assert len(rows) == 12
    for play, defense, sound, low, high in rows:
        entry = T.RUNS[(PLAYS[play], DEFENSES[defense])]
        assert (entry.low, entry.high - 1, entry.sound) == (int(low), int(high), SOUND_OF[sound]), (play, defense)


def test_the_eighteen_passes_have_the_yards_sack_and_completion_of_the_spec_table():
    rows = re.findall(r"^\| (Screen Pass|Short Pass|Long Pass)(?:: [^|]*)? \|(.*)\|$", spec_section_59(), re.MULTILINE)
    assert len(rows) == 3
    for play, cells in rows:
        values = [c.strip() for c in cells.split("|")]
        assert len(values) == 6
        for defense, value in enumerate(values, start=1):
            match = re.fullmatch(r"(-?\d+) to (-?\d+), (\d+), (\d+)", value)
            entry = T.PASSES[(PLAYS[play], defense)]
            assert (entry.low, entry.high - 1, entry.sack, entry.complete) == tuple(int(g) for g in match.groups())


def test_every_pair_has_one_entry_and_the_run_directions_are_the_original_draws():
    assert set(T.RUNS) == {(o, d) for o in (1, 2) for d in range(1, 7)}
    assert set(T.PASSES) == {(o, d) for o in (3, 4, 5) for d in range(1, 7)}
    # Line Plunge draws Int(Rnd * 3) + 1 only where a hole is named; every End Run draws Int(Rnd * 4) + 4
    assert [T.RUNS[(1, d)].direction for d in range(1, 7)] == [None, None, 3, None, 3, 3]
    assert [T.RUNS[(2, d)].direction for d in range(1, 7)] == [4] * 6
    assert (T.SACK.low, T.SACK.high) == (-12, 0)


def test_the_kick_numbers_are_the_original_ones():
    assert (T.FUMBLE_ODDS, T.FUMBLE_NUMBER) == (50, 13)
    assert (T.FIELD_GOAL_DRAWS, T.FIELD_GOAL_ODDS, T.FIELD_GOAL_NEEDED) == (5, 70, 3)
    assert (T.PUNT_ODDS, T.PUNT_SHORTEST) == (35, 25)
    assert (T.RETURN_KIND_ODDS, T.RETURN_RANGES, T.RETURN_RANGE, T.RETURN_SHORTEST) == (8, {6: 90, 2: 10}, 30, 12)
    assert (T.TURNOVER_SPOT_ODDS, T.TURNOVER_SPOT_SHORTEST) == (40, 5)


def test_the_field_goal_chances_of_the_spec_follow_from_five_draws_of_70():
    """GAME_SPEC 5.10: 5: 99.7 %, 10: 97.7 %, 20: 85.5 %, 30: 63.2 %, 35: 50 %, 40: 36.8 %, 49: 16.3 %."""
    from math import comb
    expected = {5: 99.7, 10: 97.7, 20: 85.5, 30: 63.2, 35: 50.0, 40: 36.8, 49: 16.3}
    for line, percent in expected.items():
        p = (70 - line) / 70
        chance = sum(comb(5, k) * p ** k * (1 - p) ** (5 - k) for k in range(3, 6))
        assert round(chance * 100, 1) == percent


def test_neutral_modifiers_change_nothing():
    for pair, entry in T.RUNS.items():
        assert T.NEUTRAL.run(*pair, entry) is entry
    for pair, entry in T.PASSES.items():
        assert T.NEUTRAL.pass_(*pair, entry) is entry
    assert T.NEUTRAL.fumble_odds(1) == 50 and T.NEUTRAL.field_goal_odds(2) == 70 and T.NEUTRAL.punt(1) == (35, 25)
