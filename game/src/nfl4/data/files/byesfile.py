"""footbal5.dat: the four teams with a bye in the wild card round. This is inspired by Jim Kitchen.

GAME_SPEC 12: four pairs of Integer Variants (division, place): A. F. C. D3, A. F. C. D4, N. F. C. D3, N. F. C. D4.
Written once by pog after week 16 (deleted first when it exists), read by pog and finplay17.
"""
from __future__ import annotations

from ...game.league import DIVISIONS, PLACES
from ...game.playoffs import PlayoffState, TeamRef
from .variant import FileDamaged, VariantFileError, VariantReader, pack_integer

FILE_NAME = "footbal5.dat"
TEAMS = 4


def encode(byes: list[TeamRef]) -> bytes:
    return b"".join(pack_integer(value) for team in byes for value in team)


def decode(raw: bytes) -> list[TeamRef]:
    try:
        reader = VariantReader(raw)
        values = []
        while not reader.at_end:
            values.append(reader.next_int())
        if len(values) != 2 * TEAMS:
            raise FileDamaged("the file holds %d values, not %d teams" % (len(values), TEAMS))
        for i in range(0, len(values), 2):
            if not (1 <= values[i] <= DIVISIONS and 1 <= values[i + 1] <= PLACES):
                raise FileDamaged("the team %d, %d is not one of the 32" % (values[i], values[i + 1]))
        return PlayoffState.byes_from_values(values)
    except FileDamaged:
        raise
    except (VariantFileError, ValueError) as exc:
        raise FileDamaged(str(exc)) from exc
