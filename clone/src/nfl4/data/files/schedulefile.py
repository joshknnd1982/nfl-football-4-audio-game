"""footbal2.dat: the season's schedule. This is inspired by Jim Kitchen.

GAME_SPEC 12 (written by `makes` 0x42fa70, read by Form_Load and SayScedual): 16 records in week order, each three
Variants: the opponent's division (1 to 8), the opponent's team (1 to 4) and the home flag (1 or 2). The original's six
division games are Integer Variants (12 bytes a record) and the ten others Single Variants (18 bytes a record); the
clone writes the same types and reads any number type. Exactly 16 records are required: fewer is a damaged file (the
original would read what it finds and go on with the old values), and so is anything after the sixteenth.
"""
from __future__ import annotations

from collections import Counter

from ...game.league import DIVISIONS, PLACES
from ...game.schedule import WEEKS, ScheduleEntry
from .variant import FileDamaged, VariantFileError, VariantReader, pack_integer, pack_single

FILE_NAME = "footbal2.dat"


def own_division_of(schedule: list[ScheduleEntry]) -> int | None:
    """The player's division: the six division games are the only ones against one division six times (the ten others
    are ten different teams, at most four in a division)."""
    counts = Counter(entry.division for entry in schedule)
    for division, count in counts.items():
        if count == 6:
            return division
    return None


def encode(schedule: list[ScheduleEntry], own_division: int | None = None) -> bytes:
    if own_division is None:
        own_division = own_division_of(schedule)
    out = bytearray()
    for entry in schedule[:WEEKS]:
        pack = pack_integer if entry.division == own_division else pack_single
        out += pack(entry.division) + pack(entry.team) + pack(entry.flag)
    return bytes(out)


def decode(raw: bytes) -> list[ScheduleEntry]:
    try:
        reader = VariantReader(raw)
        schedule = []
        for _ in range(WEEKS):
            division, team, flag = reader.ints(3)
            if not (1 <= division <= DIVISIONS and 1 <= team <= PLACES and flag in (1, 2)):
                raise FileDamaged("the week %d is %d, %d, %d" % (len(schedule) + 1, division, team, flag))
            schedule.append(ScheduleEntry(division, team, flag))
        if not reader.at_end:
            raise FileDamaged("the file holds more than %d weeks" % WEEKS)
    except FileDamaged:
        raise
    except VariantFileError as exc:
        raise FileDamaged(str(exc)) from exc
    return schedule
