"""footbal6.dat: the ties of the 32 teams (nfl4 only, rule 0.13; SX.12, D-096). This is inspired by Jim Kitchen.

The original has no ties: its overtime ends on a score, so footbal3.dat holds only wins and losses (GAME_SPEC 12) and keeps its 64
values. The N. F. L. rules mode's regular-season overtime can end tied (Rule 16, 16-1-3 (d)), and a team's ties live here: for
division 1 to 8, for place 1 to 4, one Integer Variant (32 values, 128 bytes), in the same form as footbal3.dat. The store writes it
with footbal3.dat only while some team has a tie and removes it otherwise, so a Classic season (and every season without a tie) has
the original's files exactly. A missing file means no ties: a season saved before SX.12 loads with none.
"""
from __future__ import annotations

from ...game.standings import Records
from .variant import FileDamaged, VariantFileError, VariantReader, pack_integer

FILE_NAME = "footbal6.dat"
VALUES = 32
LIMIT = 16           # a season has 16 regular weeks


def encode(records: Records) -> bytes:
    return b"".join(pack_integer(value) for value in records.tie_values())


def decode(raw: bytes) -> list[int]:
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
        raise FileDamaged("a tie count is outside 0 to %d" % LIMIT)
    return values
