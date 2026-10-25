"""Visual Basic 6 Variant records in a binary file: the reader and the writer. This is inspired by Jim Kitchen.

GAME_SPEC 12 and D-024 item 4: the original writes every value of its binary files with `Put #n, , aVariant` and reads
it with `Get`. VB writes a Variant to a Binary file as its two-byte type word followed by the value, so a file is a
plain run of such records and the game reads and writes the same layout, which lets a player copy a season or a
saved game across from the original (and back).

* Written by the game: Integer (type 2, two bytes), Long (type 3, four bytes), Single (type 4, four bytes) and, for a
  number a Single cannot hold exactly, Double (type 5, eight bytes).
* Read tolerantly (the original's `Get` takes whatever type the file holds): Empty (0, no value bytes, counts as 0),
  Integer, Long, Single, Double, Currency (6, eight bytes in ten-thousandths), Date (7, a Double), Boolean (11, two
  bytes) and Byte (17, one byte). Any other type word, or a file that ends inside a record, is a `VariantFileError`:
  the caller decides what a damaged file means (the game never raises it any further, playbook 7.10).

Nothing here touches the disk; `files/store.py` reads and writes the bytes.
"""
from __future__ import annotations

import math
import struct
from typing import Iterable

VT_EMPTY, VT_INTEGER, VT_LONG, VT_SINGLE, VT_DOUBLE = 0, 2, 3, 4, 5
VT_CURRENCY, VT_DATE, VT_BOOLEAN, VT_BYTE = 6, 7, 11, 17
VT_STRING = 8               # a String Variant: its type word, a two-byte length, the bytes (nfl4 SX.2: football.sav's extras)
STRING_LIMIT = 65535

INTEGER_RANGE = (-32768, 32767)
LONG_RANGE = (-2147483648, 2147483647)

# type word -> (struct format of the value, scale divisor); Empty has no value bytes
_READ = {
    VT_INTEGER: ("<h", 1), VT_LONG: ("<i", 1), VT_SINGLE: ("<f", 1), VT_DOUBLE: ("<d", 1),
    VT_CURRENCY: ("<q", 10000), VT_DATE: ("<d", 1), VT_BOOLEAN: ("<h", 1), VT_BYTE: ("<B", 1),
}


class VariantFileError(ValueError):
    """The bytes are not a run of Variant records: an unknown type word, a record cut short, or a value that is not what
    the caller asked for (a fraction where a whole number belongs, not a number)."""


class FileDamaged(VariantFileError):
    """The records parse but the values are not what the game can use (a team number of 9, a week of 31, 15 games in a
    schedule of 16): the file is damaged for the game's purposes."""


def _fits(value: int, bounds: tuple[int, int]) -> bool:
    return bounds[0] <= value <= bounds[1]


def pack_integer(value: int) -> bytes:
    if not _fits(int(value), INTEGER_RANGE):
        raise VariantFileError("%r does not fit an Integer" % (value,))
    return struct.pack("<Hh", VT_INTEGER, int(value))


def pack_long(value: int) -> bytes:
    if not _fits(int(value), LONG_RANGE):
        raise VariantFileError("%r does not fit a Long" % (value,))
    return struct.pack("<Hi", VT_LONG, int(value))


def pack_single(value: float) -> bytes:
    """A Single record (the original stores the ten non-division games of footbal2.dat and the drawn yards as Singles)."""
    return struct.pack("<Hf", VT_SINGLE, float(value))


def pack_double(value: float) -> bytes:
    return struct.pack("<Hd", VT_DOUBLE, float(value))


def pack_number(value: int | float) -> bytes:
    """The smallest type that keeps the value exactly: a whole number is an Integer, else a Long; a fraction is a Single
    when the Single reads back as the same number, else a Double."""
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, int):
        return pack_integer(value) if _fits(value, INTEGER_RANGE) else pack_long(value)
    if not math.isfinite(value):
        raise VariantFileError("%r is not a number a file can hold" % (value,))
    try:
        if struct.unpack("<f", struct.pack("<f", value))[0] == value:
            return pack_single(value)
    except OverflowError:
        pass            # too large for a single: stored as a double, which is the original's rule for such a value
    return pack_double(value)


def pack_numbers(values: Iterable[int | float]) -> bytes:
    return b"".join(pack_number(value) for value in values)


def pack_string(data: bytes) -> bytes:
    """A String Variant as VB's Put writes one to a Binary file: the type word 8, the length in two bytes, the bytes. The
    the game writes only bytes it can read back (football.sav's extras section, nfl4 SX.2); the original never reads them."""
    if len(data) > STRING_LIMIT:
        raise VariantFileError("a string of %d bytes does not fit a Variant record" % len(data))
    return struct.pack("<HH", VT_STRING, len(data)) + bytes(data)


def _as_whole(value: int | float) -> int:
    if isinstance(value, int):
        return value
    if not math.isfinite(value) or value != int(value):
        raise VariantFileError("%r is not a whole number" % (value,))
    return int(value)


class VariantReader:
    """Reads the records of one file in order. `next()` gives a number, `next_int()` a whole number; running out of
    bytes raises `VariantFileError` (the original's `Get` past the end leaves the variable as it was; the game
    treats that as a damaged file, or as a missing value where the caller says so with `at_end`)."""

    def __init__(self, raw: bytes, position: int = 0):
        self.raw = bytes(raw)
        self.position = position

    @property
    def at_end(self) -> bool:
        return self.position >= len(self.raw)

    def next(self) -> int | float:
        raw, at = self.raw, self.position
        if at + 2 > len(raw):
            raise VariantFileError("the file ends at byte %d, a type word was expected" % at)
        (kind,) = struct.unpack_from("<H", raw, at)
        at += 2
        if kind == VT_EMPTY:
            self.position = at
            return 0
        layout = _READ.get(kind)
        if layout is None:
            raise VariantFileError("unknown Variant type %d at byte %d" % (kind, at - 2))
        form, scale = layout
        size = struct.calcsize(form)
        if at + size > len(raw):
            raise VariantFileError("the file ends inside a type %d value at byte %d" % (kind, at))
        (value,) = struct.unpack_from(form, raw, at)
        self.position = at + size
        if scale != 1:
            return value / scale
        if kind in (VT_SINGLE, VT_DOUBLE, VT_DATE):
            return float(value)
        return int(value)

    def next_int(self) -> int:
        return _as_whole(self.next())

    def peek_type(self) -> int | None:
        """The type word of the next record, or None at the end (the reader does not move)."""
        if self.position + 2 > len(self.raw):
            return None
        return struct.unpack_from("<H", self.raw, self.position)[0]

    def next_string(self) -> bytes:
        """The bytes of the next record, which must be a String Variant (`next` reads numbers only)."""
        raw, at = self.raw, self.position
        if self.peek_type() != VT_STRING:
            raise VariantFileError("a string was expected at byte %d" % at)
        if at + 4 > len(raw):
            raise VariantFileError("the file ends inside a string's length at byte %d" % (at + 2))
        (size,) = struct.unpack_from("<H", raw, at + 2)
        if at + 4 + size > len(raw):
            raise VariantFileError("the file ends inside a string of %d bytes at byte %d" % (size, at + 4))
        self.position = at + 4 + size
        return raw[at + 4:at + 4 + size]

    def ints(self, count: int) -> list[int]:
        return [self.next_int() for _ in range(count)]


def unpack_numbers(raw: bytes) -> list[int | float]:
    """Every record of the file."""
    reader = VariantReader(raw)
    values = []
    while not reader.at_end:
        values.append(reader.next())
    return values


def unpack_ints(raw: bytes) -> list[int]:
    reader = VariantReader(raw)
    values = []
    while not reader.at_end:
        values.append(reader.next_int())
    return values
