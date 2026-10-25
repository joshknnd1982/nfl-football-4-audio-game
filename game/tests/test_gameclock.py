"""The made-up game clock (sgc). This is inspired by Jim Kitchen.

GAME_SPEC 5.3 (CODE (lifted) p_42bfc0; constants checked in the assembly), D-039 (the arithmetic is Single, TESTED against
the automation library, tests/oleauto.py). Texts are the exact strings of the original (strings 675, 705, 728, 732, s25, s29,
s41, 738, 749, 772).
"""
import random

import pytest

import oleauto
from nfl4.game.gameclock import COUNTDOWN_AT_WARNING, QuarterClock, quarter_word
from nfl4.game.rnd import GameRandom
from nfl4.game.vbnum import int_of, single, str_
from randsources import ScriptedRandom, below_value
from specfiles import original_strings


class NoJitter(GameRandom):
    """j = Int(Rnd * spread) - low is 0 for all three spreads the clock uses (30 with 15, 18 with 9, 10 with 5)."""

    def below(self, n):
        return n // 2


def jitter(spread, j):
    """The Rnd value that makes `Int(Rnd * spread) - low` equal j."""
    low = {30: 15, 18: 9, 10: 5}[spread]
    return below_value(spread, low + j)


def advance(clock, played, total, quarter, values=()):
    source = ScriptedRandom(values, strict=True)
    text = clock.advance(played, total, quarter, GameRandom(source))
    assert source.left == 0, "a scripted draw was not used"
    return text


# ----- the sentence -----

def test_the_texts_are_strings_of_the_original():
    strings = original_strings()
    for text in (" remaining in the ", " quarter. ", " minute", " second", "s", "first", "second", "third", "fourth",
                 "over time"):
        assert text in strings, text


def test_hand_checked_first_quarter_time():
    """total 30, played 10: pct = Int(20 * 100 / 30) = 66, m = 66 * 15 / 100 = 9.9, minutes 9; Int(9.9 * 100) is 989 in a
    Single (990 in a Double), so the seconds are Int(89 * 60 / 100) = 53 before the jitter (checked with the library)."""
    clock = QuarterClock()
    text = advance(clock, 10, 30, 1, [jitter(30, 0)])
    assert (clock.mins, clock.secs) == (9, 53)
    assert text == " 9 minutes  53 seconds remaining in the first quarter. "


def test_the_first_acceptable_jitter_is_taken_and_a_negative_result_is_drawn_again():
    clock = QuarterClock()
    # total 36, played 25: left 11, pct = 30, m = 30 * 15 / 100 = 4.5, mins 4, L54 = 450, secs = 30; j = -15 gives 15 (ok)
    assert advance(clock, 25, 36, 1, [jitter(30, -15)]).startswith(" 4 minutes  15 seconds")
    # total 30, played 29: left 1, pct = 3, m = 0.45, minutes 0, L54 = 45 (a Single 0.45 * 100 rounds to 45.0), seconds
    # Int(45 * 60 / 100) = 27; j = +14 makes 41
    clock = QuarterClock()
    assert advance(clock, 29, 30, 1, [jitter(30, 14)]) == "   41 seconds remaining in the first quarter. "
    # a base of 0 seconds (total 30, played 30: left 0, pct 0) with two draws below zero: drawn again until 0 or more
    clock = QuarterClock()
    text = advance(clock, 30, 30, 1, [jitter(30, -15), jitter(30, -1), jitter(30, 2)])
    assert clock.secs == 2 and clock.mins == 0                       # -15 and -1 were below 0: drawn again; 0 + 2 = 2
    assert text == "   2 seconds remaining in the first quarter. "


def test_the_sentence_forms_for_every_combination_of_minutes_and_seconds():
    clock = QuarterClock()
    clock.oldtime = 7                                                # the same play counter again: no computation, no draw
    cases = [
        (12, 0, " 12 minutes remaining in the first quarter. "),
        (1, 0, " 1 minute remaining in the first quarter. "),
        (1, 1, " 1 minute  1 second remaining in the first quarter. "),
        (2, 2, " 2 minutes  2 seconds remaining in the first quarter. "),
        (0, 1, "   1 second remaining in the first quarter. "),
        (0, 30, "   30 seconds remaining in the first quarter. "),
        (0, 0, "  remaining in the first quarter. "),                 # " " and then " remaining": two spaces
        (15, 0, " 15 minutes remaining in the first quarter. "),
    ]
    for mins, secs, expected in cases:
        clock.mins, clock.secs = mins, secs
        assert advance(clock, 7, 30, 1) == expected


def test_the_same_play_counter_gives_the_same_time_again_with_no_draw():
    clock = QuarterClock()
    first = advance(clock, 12, 31, 1, [jitter(30, 3)])
    again = advance(clock, 12, 31, 1)                                # strict: any draw would fail
    assert again == first
    different = advance(clock, 13, 31, 1, [jitter(30, 0)])
    assert different != first and clock.oldtime == 13


def test_a_fresh_clock_treats_play_counter_0_as_the_old_time_and_computes_nothing():
    """oldtime starts Empty, which equals 0 (GAME_SPEC 5.3; Q28: the counter starts at 1 so it only matters at 0)."""
    clock = QuarterClock()
    assert advance(clock, 0, 30, 1) == "  remaining in the first quarter. "
    assert (clock.mins, clock.secs, clock.oldtime) == (0, 0, 0)


def test_the_start_of_an_overtime_period_speaks_its_full_time_when_f4_was_never_pressed_since_counter_0_q6():
    """Q6 / D-025 (b), not reproduced: the original says " remaining in the over time quarter." with no time (or repeats the
    last time pressed at counter 0); the game speaks 15 minutes, and draws nothing for it."""
    clock = QuarterClock()
    assert advance(clock, 0, 30, 5) == " 15 minutes remaining in the over time quarter. "
    assert (clock.mins, clock.secs, clock.oldtime) == (15, 0, 0)
    clock = QuarterClock()
    clock.oldtime, clock.mins, clock.secs = 0, 4, 12                  # last pressed at counter 0 with another time left over
    assert advance(clock, 0, 30, 6) == " 15 minutes remaining in the over time quarter. "


def test_an_overtime_period_after_f4_was_pressed_later_is_computed_as_the_original_does_and_the_rest_is_kept_q6():
    clock = QuarterClock()
    clock.oldtime = 12                                                  # F4 was pressed at counter 12 of the last period
    text = advance(clock, 0, 30, 5, [jitter(30, 7)])                    # played 0 is not oldtime: computed (one seconds draw)
    assert text.startswith(" 15 minutes") and (clock.mins, clock.oldtime) == (15, 0)
    from nfl4.game.gameclock import clock_sentence                      # a clock at the very end of a quarter gives no seconds (kept)
    assert clock_sentence(2, 0, "second") == " 2 minutes remaining in the second quarter. "
    assert clock_sentence(0, 0, "fourth") == "  remaining in the fourth quarter. "


def test_the_third_quarter_starts_at_15_minutes_and_the_counter_0_is_forced_to_it():
    clock = QuarterClock()
    assert advance(clock, 0, 33, 3) == " 15 minutes remaining in the third quarter. "
    clock = QuarterClock()
    clock.oldtime = 5
    text = advance(clock, 0, 33, 3, [jitter(30, 7)])                 # played 0 is not oldtime: computed, then overridden
    assert text == " 15 minutes remaining in the third quarter. " and (clock.mins, clock.secs) == (15, 0)
    assert clock.oldtime == 0


def test_every_quarter_word_and_the_overtime_word():
    assert [quarter_word(q) for q in (1, 2, 3, 4)] == ["first", "second", "third", "fourth"]
    assert {quarter_word(q) for q in range(5, 11)} == {"over time"}
    for bad in (0, 11, -1):
        with pytest.raises(ValueError):
            quarter_word(bad)


# ----- the two-minute warning -----

def test_the_countdown_grows_by_the_warning_length_on_every_call_inside_5_plus_w_plays():
    clock = QuarterClock()
    clock.set_warnings(6, 5, 5)                                      # M2W = 6
    assert clock.countdown == 100
    advance(clock, 25, 34, 2, [jitter(18, 0)])                       # left 9 < 11: CountDown 106, spread 18
    assert clock.countdown == 106 and (clock.mins, clock.secs) == (3, 40)
    advance(clock, 26, 34, 2, [jitter(18, 0)])                       # left 8 < 11 again: 112 (it accumulates)
    assert clock.countdown == 112
    advance(clock, 20, 34, 2, [jitter(30, 0)])                       # left 14: no change, the normal spread
    assert clock.countdown == 112


def test_inside_w_plays_the_countdown_is_set_to_125_170_or_215_and_the_spread_is_ten():
    for w, constant in ((5, 125), (6, 170), (7, 215)):
        clock = QuarterClock()
        clock.set_warnings(w, w, w)
        advance(clock, 34 - w, 34, 2, [jitter(10, 0)])
        assert clock.countdown == constant == COUNTDOWN_AT_WARNING[w]
    # quarter 4, W = 5, total 30, played 27: left 3, pct 10, m = 10 * 15 / 125 = 1.2, minutes 1, Int(1.2 * 100) = 120
    # in a Single, seconds Int(20 * 60 / 100) = 12 (hand-checked, and by the library in the test below)
    clock = QuarterClock()
    clock.set_warnings(7, 5, 7)
    text = advance(clock, 27, 30, 4, [jitter(10, 0)])
    assert text == " 1 minute  12 seconds remaining in the fourth quarter. "
    # quarter 2, W = 6, total 34, played 31: left 3, pct 8, m = 8 * 15 / 170, minutes 0, 70 hundredths, 42 seconds
    clock = QuarterClock()
    clock.set_warnings(6, 5, 7)
    text = advance(clock, 31, 34, 2, [jitter(10, 4)])                # j = +4: 46 seconds
    assert text == "   46 seconds remaining in the second quarter. "


def test_each_quarter_uses_its_own_warning_length_and_quarters_1_and_3_never_warn():
    clock = QuarterClock()
    clock.set_warnings(5, 6, 7)
    advance(clock, 28, 30, 4, [jitter(10, 0)])                       # left 2 <= M4W 6: 170
    assert clock.countdown == 170
    clock = QuarterClock()
    clock.set_warnings(5, 6, 7)
    advance(clock, 28, 30, 5, [jitter(10, 0)])                       # overtime: M5W 7: 215
    assert clock.countdown == 215
    clock = QuarterClock()
    clock.set_warnings(5, 6, 7)
    advance(clock, 29, 30, 1, [jitter(30, 0)])                       # first quarter: no warning at 1 play left
    assert clock.countdown == 100
    clock = QuarterClock()
    advance(clock, 29, 30, 3, [jitter(30, 0)])                       # third quarter: none either
    assert clock.countdown == 100


def test_start_quarter_resets_the_countdown_to_100():
    clock = QuarterClock()
    clock.set_warnings(5, 5, 5)
    advance(clock, 29, 30, 2, [jitter(10, 0)])
    assert clock.countdown == 125
    clock.start_quarter()
    assert clock.countdown == 100


# ----- the arithmetic types -----

def test_single_rounds_to_32_bits_and_str_puts_the_space_before_numbers_that_are_not_negative():
    assert single(4.35) == 4.349999904632568 and single(0.1) == 0.10000000149011612
    assert single(100000000.0) == 100000000.0 and single(3.4e39) == float("inf")
    assert int_of(2.9) == 2 and int_of(-2.1) == -3
    assert (str_(0), str_(7), str_(12.0), str_(-3)) == (" 0", " 7", " 12", "-3")


@pytest.mark.skipif(not oleauto.available(), reason="the automation library (oleaut32) is Windows only")
def test_the_clocks_numbers_equal_the_automation_librarys_for_every_input_the_game_can_give():
    """total 30 to 37 as a Single, the play counter 0 to total, CountDown as the integers 100, 125, 170, 215 and as the
    Singles 100 + n * W (n up to 3): 3,588 inputs, compared with VarSub, VarMul, VarDiv and VarInt on the same types.
    In a Double the same chain differs in 57 of them (D-039)."""
    clock_values = [(oleauto.VT_I2, cd) for cd in (100, 125, 170, 215)]
    clock_values += [(oleauto.VT_R4, 100 + w * k) for w in (5, 6, 7) for k in (1, 2, 3)]
    checked = 0
    for total in range(30, 38):
        for played in range(0, total + 1):
            for vt, countdown in clock_values:
                clock = QuarterClock()
                clock.oldtime = -1                                   # force the computation (a counter of 0 included)
                clock.countdown = countdown
                clock.advance(played, total, 1, NoJitter())
                _, mins, _, secs = oleauto.clock_chain(total, played, countdown, vt)
                assert (clock.mins, clock.secs) == (mins, secs), (total, played, countdown)
                checked += 1
    assert checked == sum((total + 1) * len(clock_values) for total in range(30, 38)) == 3588


@pytest.mark.skipif(not oleauto.available(), reason="the automation library (oleaut32) is Windows only")
def test_whole_quarters_with_warnings_follow_the_library_play_by_play():
    """Every play of quarters 2, 4 and an overtime period for every total and every W: the CountDown the clock holds after
    each call is fed to the library's chain, which gives the same minutes and seconds."""
    for quarter in (2, 4, 5):
        for w in (5, 6, 7):
            for total in (30, 33, 37):
                clock = QuarterClock()
                clock.set_warnings(w, w, w)
                for played in range(1, total + 1):
                    clock.advance(played, total, quarter, NoJitter())
                    _, mins, _, secs = oleauto.clock_chain(total, played, clock.countdown)
                    assert (clock.mins, clock.secs) == (mins, secs), (quarter, w, total, played)


def test_a_double_chain_would_give_other_seconds_in_some_cases_so_the_single_rule_matters():
    """The reason for the Single rounding, kept as a test: the hand-checked case from the library (total 30, played 10)."""
    left = 20
    pct = int(left * 100 / 30)
    m = pct * 15 / 100
    assert int(m * 100) == 990                                       # a Double: 990, minutes 9, seconds 54 ...
    clock = QuarterClock()
    clock.advance(10, 30, 1, NoJitter())
    assert clock.secs == 53                                          # ... the original (a Single): 989 and 53


def test_the_seeded_clock_always_gives_minutes_and_seconds_in_range():
    rnd = GameRandom(random.Random(3))
    for total in range(30, 38):
        for quarter in (1, 2, 3, 4, 5):
            clock = QuarterClock()
            clock.set_warnings(5, 6, 7)
            for played in range(1, total + 1):
                clock.advance(played, total, quarter, rnd)
                assert 0 <= clock.mins <= 15 and 0 <= clock.secs <= 59
    assert rnd.fallbacks == 0
