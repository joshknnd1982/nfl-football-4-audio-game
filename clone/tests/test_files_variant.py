"""The Variant record reader and writer (data/files/variant.py). This is inspired by Jim Kitchen.

GAME_SPEC 12: VB6 writes a Variant to a Binary file as its two-byte type word and then the value; the clone writes Integer,
Long, Single and Double and reads those and the few others a copied file could hold.
"""
import struct

import pytest

from nfl4.data.files import variant as v


def test_the_written_layout_is_the_type_word_then_the_value():
    assert v.pack_integer(300) == struct.pack("<Hh", 2, 300)
    assert v.pack_long(70000) == struct.pack("<Hi", 3, 70000)
    assert v.pack_single(1.5) == struct.pack("<Hf", 4, 1.5)
    assert v.pack_double(0.1) == struct.pack("<Hd", 5, 0.1)
    assert len(v.pack_integer(1)) == 4 and len(v.pack_single(1)) == 6      # the 12 and 18 bytes of a footbal2.dat record


def test_pack_number_takes_the_smallest_exact_type():
    assert v.pack_number(7) == v.pack_integer(7)
    assert v.pack_number(-32768) == v.pack_integer(-32768)
    assert v.pack_number(32768) == v.pack_long(32768)
    assert v.pack_number(2.5) == v.pack_single(2.5)
    assert v.pack_number(100.0) == v.pack_single(100.0)
    assert v.pack_number(0.1) == v.pack_double(0.1)               # a Single cannot hold 0.1 exactly
    assert v.pack_number(True) == v.pack_integer(1)


def test_every_number_comes_back_as_it_went_in():
    values = [0, 1, -1, 32767, -32768, 40000, -2147483648, 2147483647, 1.5, 100.0, 0.1, 3.14159, 1e300]
    assert v.unpack_numbers(v.pack_numbers(values)) == values


def test_values_that_do_not_fit_or_are_not_numbers_are_refused():
    with pytest.raises(v.VariantFileError):
        v.pack_integer(32768)
    with pytest.raises(v.VariantFileError):
        v.pack_long(2 ** 31)
    for bad in (float("nan"), float("inf")):
        with pytest.raises(v.VariantFileError):
            v.pack_number(bad)


def test_the_reader_accepts_every_type_a_get_could_read():
    raw = (struct.pack("<H", 0) + struct.pack("<Hh", 2, -5) + struct.pack("<Hi", 3, 123456) + struct.pack("<Hf", 4, 0.5)
           + struct.pack("<Hd", 5, 2.25) + struct.pack("<Hq", 6, 12500) + struct.pack("<Hd", 7, 36526.0)
           + struct.pack("<Hh", 11, -1) + struct.pack("<HB", 17, 200))
    assert v.unpack_numbers(raw) == [0, -5, 123456, 0.5, 2.25, 1.25, 36526.0, -1, 200]


def test_next_int_accepts_a_whole_single_and_refuses_a_fraction():
    reader = v.VariantReader(v.pack_single(3.0) + v.pack_single(3.5) + v.pack_integer(4))
    assert reader.next_int() == 3
    with pytest.raises(v.VariantFileError):
        reader.next_int()
    assert reader.next_int() == 4 and reader.at_end


def test_a_file_that_ends_inside_a_record_is_refused():
    whole = v.pack_long(7)
    for cut in range(1, len(whole)):
        with pytest.raises(v.VariantFileError):
            v.unpack_numbers(whole[:cut])
    with pytest.raises(v.VariantFileError):
        v.VariantReader(b"").next()


def test_an_unknown_type_word_is_refused_with_its_place():
    with pytest.raises(v.VariantFileError, match="unknown Variant type 8 at byte 4"):
        v.unpack_numbers(v.pack_integer(1) + struct.pack("<H", 8) + b"xx")


def test_ints_reads_the_count_asked_for_and_stops():
    reader = v.VariantReader(v.pack_numbers([1, 2, 3, 4]))
    assert reader.ints(3) == [1, 2, 3] and not reader.at_end and reader.position == 12
    with pytest.raises(v.VariantFileError):
        reader.ints(2)


def test_random_bytes_never_raise_anything_but_the_files_own_error():
    import random
    rng = random.Random(7)
    for _ in range(500):
        junk = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 40)))
        try:
            v.unpack_numbers(junk)
        except v.VariantFileError:
            pass
