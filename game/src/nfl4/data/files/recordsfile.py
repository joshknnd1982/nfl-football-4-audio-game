"""footbal3.dat: the wins and losses of the 32 teams. This is inspired by Jim Kitchen.

GAME_SPEC 12: for division 1 to 8, for place 1 to 4: wins, then losses; 64 Integer Variants (256 bytes), written by pog
after every regular week. A missing file means 0 and 0 for everybody (week 1 of every season: nothing has written it yet).
"""
from __future__ import annotations

from ...game.standings import Records
from .variant import FileDamaged, VariantFileError, VariantReader, pack_integer

FILE_NAME = "footbal3.dat"
VALUES = 64
LIMIT = 99           # a season has 16 games; the bound only keeps a junk file out


def encode(records: Records) -> bytes:
    return b"".join(pack_integer(value) for value in records.as_file_values())


def decode(raw: bytes) -> Records:
    try:
        reader = VariantReader(raw)
        values = reader.ints(VALUES)
        if not reader.at_end:
            raise FileDamaged("the file holds more than %d values" % VALUES)
    except FileDamaged:
        raise
    except VariantFileError as exc:
        raise FileDamaged(str(exc)) from exc
    if any(not 0 <= value <= LIMIT for value in values):
        raise FileDamaged("a win or loss count is outside 0 to %d" % LIMIT)
    return Records.from_file_values(values)
