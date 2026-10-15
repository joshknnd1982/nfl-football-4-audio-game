"""footbal4.dat: the play-off pairings of the coming round. This is inspired by Jim Kitchen.

GAME_SPEC 12: records of four Integer Variants: division and place of the first team (the visitor), then of the second
(the home team). Written by pog and finplay17 after each round (the original deletes the file first, k4, because a
Binary write does not shorten an existing file; the clone replaces it whole), read by the week loop (this week's
opponent), SayScedual, pog and finplay17. 4 records after week 16 and after the wild card week, 2 after the division week,
1 after the championship week.
"""
from __future__ import annotations

from ...game.playoffs import Pairing, PlayoffState
from ...game.league import DIVISIONS, PLACES
from .variant import FileDamaged, VariantFileError, VariantReader, pack_integer

FILE_NAME = "footbal4.dat"
GAMES_AFTER_WEEK = {17: 4, 18: 4, 19: 2, 20: 1}      # the games of the coming round, by the week counter


def encode(pairings: list[Pairing]) -> bytes:
    return b"".join(pack_integer(value) for visitor, home in pairings for value in (*visitor, *home))


def _checked(values: list[int]) -> None:
    for i in range(0, len(values), 2):
        if not (1 <= values[i] <= DIVISIONS and 1 <= values[i + 1] <= PLACES):
            raise FileDamaged("the team %d, %d is not one of the 32" % (values[i], values[i + 1]))


def decode(raw: bytes) -> list[Pairing]:
    try:
        reader = VariantReader(raw)
        values = []
        while not reader.at_end:
            values.append(reader.next_int())
        if len(values) % 4:
            raise FileDamaged("the file holds %d values, not whole games" % len(values))
        _checked(values)
        return PlayoffState.pairings_from_values(values)
    except FileDamaged:
        raise
    except (VariantFileError, ValueError) as exc:
        raise FileDamaged(str(exc)) from exc
