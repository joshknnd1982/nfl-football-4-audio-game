"""The records, the standings order and the SayStand speech. This is inspired by Jim Kitchen.

GAME_SPEC 5.2 (CODE (lifted) SayStand p_42ce40; the sort checked in the assembly at 0x42da3b), S5.2 audit finding A-11 (the
exact heading). The speech goes through the rig: say2, asynchronous, the announcer, the replay list, the log.
"""
import random

import pytest

from gamerig import Rig
from nfl4.game.league import DIVISIONS, PLACES, League
from nfl4.game.standings import Records, standings_order, standings_speech
from nfl4.speech.roles import ANNOUNCER
from specfiles import original_strings


def records_with(rows):
    """rows: {division: [(wins, losses) x 4]}"""
    records = Records()
    for division, teams in rows.items():
        for place, (wins, losses) in enumerate(teams, start=1):
            records.wins[division - 1][place - 1] = wins
            records.losses[division - 1][place - 1] = losses
    return records


def test_a_division_is_ordered_by_fewest_losses_only_and_equal_losses_keep_the_leagues_order():
    league = League()
    records = records_with({1: [(0, 5), (9, 3), (1, 3), (2, 0)]})
    assert standings_order(1, league, records) == [("Steelers", 2, 0), ("Browns", 9, 3), ("Ravens", 1, 3),
                                                   ("Bengals", 0, 5)]
    # wins are ignored: 15 wins and 0 wins with the same losses keep the league's order (Browns before Ravens above)
    even = records_with({1: [(0, 4), (15, 4), (3, 4), (8, 4)]})
    assert [name for name, _, _ in standings_order(1, league, even)] == ["Bengals", "Browns", "Ravens", "Steelers"]


def test_the_sort_equals_a_stable_sort_on_losses_for_any_records():
    league = League()
    rng = random.Random(14)
    for _ in range(2000):
        records = Records()
        for d in range(DIVISIONS):
            for p in range(PLACES):
                records.wins[d][p] = rng.randrange(0, 17)
                records.losses[d][p] = rng.randrange(0, 5)
        division = rng.randrange(1, DIVISIONS + 1)
        want = sorted(((league.team(division, p), records.wins[division - 1][p - 1], records.losses[division - 1][p - 1])
                       for p in range(1, PLACES + 1)), key=lambda team: team[2])
        assert standings_order(division, league, records) == want


def test_the_speech_is_the_heading_then_each_division_and_its_four_teams_with_the_exact_texts():
    league = League()
    records = records_with({1: [(1, 2), (3, 0), (0, 3), (2, 1)], 8: [(16, 0), (0, 16), (7, 7), (7, 7)]})
    speech = standings_speech(league, records, 4)
    assert speech.heading == " Standings after week number 3"                # trimmed number, no space at the end
    assert len(speech.divisions) == 8
    division, lines = speech.divisions[0]
    assert division == " A. F. C. North. "
    assert lines == [" Browns 3, and 0. ", " Steelers 2, and 1. ", " Bengals 1, and 2. ", " Ravens 0, and 3. "]
    division, lines = speech.divisions[7]
    assert division == " N. F. C. South. "
    assert lines == [" Buccaneers 16, and 0. ", " Panthers 7, and 7. ", " Saints 7, and 7. ", " Falcons 0, and 16. "]
    # the 7 and 7 teams keep the league's order: Panthers (place 3) before Saints (place 4)


def test_the_week_number_is_gtp_minus_one_at_most_16_and_nothing_is_said_outside_1_to_17():
    league, records = League(), Records()
    assert standings_speech(league, records, 0) is None and standings_speech(league, records, -3) is None
    assert standings_speech(league, records, 18) is None and standings_speech(league, records, 20) is None
    assert standings_speech(league, records, 1).heading == " Standings after week number 0"
    assert standings_speech(league, records, 2).heading == " Standings after week number 1"
    assert standings_speech(league, records, 16).heading == " Standings after week number 15"
    assert standings_speech(league, records, 17).heading == " Standings after week number 16"


def test_the_texts_are_strings_of_the_original():
    strings = original_strings()
    for text in (" Standings after week number ", ", and ", ". ", " A. F. C. North. ", " N. F. C. South. "):
        assert text in strings, text


def test_the_records_round_trip_through_the_64_values_of_footbal3_dat():
    records = records_with({1: [(1, 2), (3, 4), (5, 6), (7, 8)], 8: [(9, 10), (11, 12), (13, 14), (15, 16)]})
    values = records.as_file_values()
    assert len(values) == 64 and values[:8] == [1, 2, 3, 4, 5, 6, 7, 8] and values[-2:] == [15, 16]
    assert Records.from_file_values(values) == records
    with pytest.raises(ValueError):
        Records.from_file_values(values[:63])
    records.win(2, 3)
    records.loss(2, 3)
    assert records.record(2, 3) == (1, 1)
    records.reset()
    assert records.as_file_values() == [0] * 64


# ----- the speaking: Game.say_stand on the rig -----

def test_say_stand_speaks_with_say2_logs_the_lines_and_clears_the_key_twice():
    rig = Rig()
    game = rig.game
    log = []
    game.log_sink = log.append
    game.season.gtp = 3
    game.season.records.wins[0][1] = 2
    game.season.records.losses[0][0] = 1
    clk_calls = []
    original_clk = rig.keys.clk
    rig.keys.clk = lambda: (clk_calls.append(len(rig.said)), original_clk())
    game.say_stand()
    assert clk_calls == [0, 0]                                          # the original clears the key twice, before speaking
    texts = [text for text, _, _ in rig.said]
    assert texts[0] == " Standings after week number 2"
    assert texts[1] == " A. F. C. North. " and texts[2] == " Browns 2, and 0. "
    assert len(texts) == 1 + 8 * 5 and all(role == ANNOUNCER for _, role, _ in rig.said)
    assert [kind for kind, _ in rig.sapi.events if kind != "speak"] == []   # say2: asynchronous, no wait, no stop
    assert game.ptf == 0                                                # set to 1 for the speech and back to 0
    expected_log = texts[:1]
    for division in range(8):
        expected_log += texts[1 + 5 * division:6 + 5 * division] + [""]       # the division's lines, then an empty line
    assert log == expected_log
    assert game.replay == texts                                         # say2 keeps every line for the replay


def test_say_stand_says_nothing_but_still_clears_the_key_once_when_the_season_is_not_in_a_week():
    for gtp in (0, 18, 20):
        rig = Rig()
        calls = []
        original_clk = rig.keys.clk
        rig.keys.clk = lambda: (calls.append(1), original_clk())
        rig.game.season.gtp = gtp
        rig.game.say_stand()
        assert rig.said == [] and len(calls) == 1 and rig.game.ptf == 0 and rig.game.replay == []
