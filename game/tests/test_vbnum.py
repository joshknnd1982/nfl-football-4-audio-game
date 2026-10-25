"""Visual Basic's Str$, Int, Trim$ and the Single rounding the clock needs. This is inspired by Jim Kitchen.

GAME_SPEC 15 (the doubled spaces of Str$, GAP_REGISTER G-S3), 5.3 and D-039 (the clock's Variants are Singles).
"""
import math
import struct

from nfl4.game.vbnum import int_of, rtrim, single, str_, trim


def test_str_puts_a_space_before_a_number_that_is_not_negative_and_a_minus_before_a_negative_one():
    assert [str_(n) for n in (0, 1, 9, 10, 123456)] == [" 0", " 1", " 9", " 10", " 123456"]
    assert [str_(n) for n in (-1, -20)] == ["-1", "-20"]
    assert str_(7.0) == " 7" and str_(-7.0) == "-7" and str_(0.0) == " 0"          # whole singles and doubles print whole


def test_str_of_a_fraction_keeps_the_sign_rule():
    assert str_(2.5) == " 2.5" and str_(-2.5) == "-2.5"


def test_the_doubled_space_of_the_originals_sentences_comes_from_str():
    assert " game number " + str_(1) == " game number  1"                         # GAP_REGISTER G-S3
    assert " it's your ball on my " + str_(30) == " it's your ball on my  30"


def test_trim_and_rtrim_remove_only_spaces():
    assert trim("  a b  ") == "a b" and rtrim("  a b  ") == "  a b"
    assert trim("\ta ") == "\ta" and rtrim("a\t") == "a\t"                           # a tab is not a space to Trim$


def test_int_is_a_floor_also_below_zero():
    assert [int_of(x) for x in (0.0, 0.99, 1.0, 9.999999, -0.5, -1.0, -1.5)] == [0, 0, 1, 9, -1, -1, -2]


def test_single_rounds_like_a_32_bit_float():
    for x in (0.1, 4.35, 9.9, 1.2, 123456.789):
        assert single(x) == struct.unpack("<f", struct.pack("<f", x))[0]
    assert single(0.5) == 0.5 and single(0.25) == 0.25                               # exact binary fractions stay
    assert single(16777217.0) == 16777216.0                                          # 2 ** 24 + 1 needs 25 bits
    assert math.isinf(single(1e39)) and single(-1e39) == -math.inf


def test_the_reason_for_single_in_the_clock_two_cases():
    assert int(4.35 * 100) == 434                                                    # a Double: 434.99999999999994
    assert int_of(single(single(4.35) * 100)) == 435                                 # a Single: 435.0
    assert int(9.9 * 100) == 990 and int_of(single(single(9.9) * 100)) == 989        # the other way round
