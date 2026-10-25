"""football.gtp: the week counter. This is inspired by Jim Kitchen.

GAME_SPEC 12: one Integer Variant, gtp: 1 to 16 the regular weeks, 17 wild card, 18 division, 19 division
championship, 20 Super Bowl week, 0 the season is over (the original's exit then deletes the season files). Written 1 at
a new season, then by pog after every call, and 0 by finplay17.
"""
from __future__ import annotations

import struct

from .variant import VT_EMPTY, FileDamaged, VariantFileError, VariantReader, pack_integer

FILE_NAME = "football.gtp"
LAST_WEEK = 20


def encode(gtp: int) -> bytes:
    return pack_integer(gtp)


def decode(raw: bytes) -> int:
    if len(raw) >= 2 and struct.unpack_from("<H", raw)[0] == VT_EMPTY:
        raise FileDamaged("the week is an Empty Variant (a zeroed file), not a number")    # not a real 0 (D-047)
    try:
        gtp = VariantReader(raw).next_int()
    except VariantFileError as exc:
        raise FileDamaged(str(exc)) from exc
    if not 0 <= gtp <= LAST_WEEK:
        raise FileDamaged("the week %d is not 0 to %d" % (gtp, LAST_WEEK))
    return gtp
