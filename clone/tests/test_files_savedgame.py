"""football.sav: the saved game (data/files/savedgame.py). This is inspired by Jim Kitchen.

GAME_SPEC 12: 36 Variant values and the opponent quarterback's name in the original's order, then the clone's one added value
(the side that received the opening kick-off, D-027 item 3). A file of the original, without it, is accepted.
"""
import struct

import pytest

from nfl4.data.files import savedgame, variant
from nfl4.game.gamestate import SavedGame, SideStats

Damaged = variant.FileDamaged


def a_game(name="Namath", opening=1, countdown=71.5):
    own = SideStats(pass_attempts=12, completions=7, passing_yards=88, sacked=1, intercepted=2, running_plays=9,
                    running_yards=41, fumbles_lost=0, first_downs=6, score=10)
    opponent = SideStats(pass_attempts=20, completions=11, passing_yards=130, sacked=3, intercepted=0, running_plays=14,
                         running_yards=60, fumbles_lost=1, first_downs=9, score=17)
    return SavedGame(2, 1, 1, 3, 12, [31, 32, 33, 34, 35], countdown, {1: own, 2: opponent}, 40, 2, 6, name, opening)


def test_the_values_are_in_the_originals_order_and_the_name_is_a_long_then_codes():
    raw = savedgame.encode(a_game())
    values = variant.unpack_numbers(raw)
    assert values[:11] == [2, 1, 1, 3, 12, 31, 32, 33, 34, 35, 71.5]
    assert values[11:31] == [12, 20, 7, 11, 88, 130, 1, 3, 2, 0, 9, 14, 41, 60, 0, 1, 6, 9, 10, 17]    # own, opponent each
    assert values[31:36] == [40, 1, 2, 6, 6]            # yard line, Lcc again, down, yards to go, the name's length
    assert [chr(c) for c in values[36:42]] == list("Namath") and values[42] == 1              # the clone's extra value
    assert [struct.unpack_from("<H", raw, at)[0] for at in (0, 4)] == [2, 2]            # Integer records, 4 bytes each


def test_the_length_of_the_name_is_stored_as_a_long():
    raw = savedgame.encode(a_game(name="Ab"))
    reader = variant.VariantReader(raw)
    for _ in range(35):
        reader.next()
    assert struct.unpack_from("<H", raw, reader.position)[0] == 3                              # VT_LONG


def test_a_saved_game_comes_back_whole():
    saved = a_game()
    assert savedgame.decode(savedgame.encode(saved)) == saved
    for name in ("", "Martínez", "O'Brien", 'Jones"', "Van Zyl"):
        assert savedgame.decode(savedgame.encode(a_game(name=name))).opponent_quarterback == name


def test_a_file_of_the_original_has_no_extra_value_and_reads_as_none():
    saved = a_game(opening=None)
    raw = savedgame.encode(saved)
    assert len(raw) == len(savedgame.encode(a_game())) - 4
    assert savedgame.decode(raw).opening_receiver is None


def test_the_clock_is_kept_exactly_as_a_single_or_a_double():
    for countdown in (100, 100.0, 71.5, 33.33333333333333, 0.1, 0):
        assert savedgame.decode(savedgame.encode(a_game(countdown=countdown))).countdown == countdown


def test_integers_longs_singles_and_doubles_of_a_copied_file_all_read():
    saved = a_game()
    values = variant.unpack_numbers(savedgame.encode(saved))
    as_singles = b"".join(variant.pack_single(x) if i not in (35,) else variant.pack_long(x)
                          for i, x in enumerate(values[:36])) + b"".join(variant.pack_double(c) for c in values[36:])
    assert savedgame.decode(as_singles) == saved


def test_the_values_a_game_cannot_have_are_refused():
    base = variant.unpack_numbers(savedgame.encode(a_game()))
    # (index in the file, a value no game can hold): the side, the half, the quarter, the counter, a quarter's plays, the
    # clock, a statistic, the yard line, the second half, the down, yards to go, the name's length
    for index, bad in [(0, 3), (1, 0), (2, 5), (3, 6), (4, 201), (5, 0), (10, -1), (10, 5000), (11, 100000), (31, 51),
                       (32, 9), (33, 5), (34, 0), (34, 101), (35, 5000), (35, -2)]:
        values = list(base)
        values[index] = bad
        raw = b"".join(variant.pack_number(x) for x in values)
        with pytest.raises(Damaged):
            savedgame.decode(raw)


def test_a_file_cut_anywhere_is_refused_or_is_a_shorter_valid_name_never_another_error():
    raw = savedgame.encode(a_game())
    refused = 0
    for cut in range(len(raw)):
        try:
            savedgame.decode(raw[:cut])
        except Damaged:
            refused += 1
    assert refused == len(raw) - 1        # only the cut before the clone's extra value is a whole file (an original's)


def test_extra_records_after_the_extra_value_are_refused():
    with pytest.raises(Damaged):
        savedgame.decode(savedgame.encode(a_game()) + variant.pack_integer(1))
    with pytest.raises(Damaged):
        savedgame.decode(savedgame.encode(a_game(opening=None)) + variant.pack_integer(3))   # a side that does not exist


def test_empty_and_random_bytes_are_damaged():
    import random
    with pytest.raises(Damaged):
        savedgame.decode(b"")
    rng = random.Random(3)
    for _ in range(300):
        try:
            savedgame.decode(bytes(rng.randrange(256) for _ in range(rng.randrange(0, 200))))
        except Damaged:
            pass


def test_a_play_counter_of_0_is_a_game_saved_at_the_start_of_quarter_3_or_of_overtime():
    saved = a_game()
    saved.counter = 0
    assert savedgame.decode(savedgame.encode(saved)).counter == 0
