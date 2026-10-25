"""footbal1.dat: the player's team and the coach's name. This is inspired by Jim Kitchen.

GAME_SPEC 12 (written by ChooseTeam 0x4308e0, read by Form_Load 0x488018 to 0x4882f1): tn1 and tn2 (the player's team:
division 1 to 8, place 1 to 4; Integer Variants), the length of the coach's name (a Long Variant), then one Integer
Variant per character holding its character code (`Asc`). Form_Load opens the file twice: the first read takes only tn1
and treats 0 as "no season" (a new season: coach, team, schedule), the second reads the whole record.

Here a MISSING file is the new season; a file whose first value is 0 is damaged, because the original never writes a 0
there (the rule only guards an empty file the VB runtime made) and a zeroed or emptied file must not silently end a
season (D-047). `decode` raises `FileDamaged` for anything it cannot use. The coach's characters are Latin-1 codes (a typed
name holds letters, digits and spaces only, but a copied original may hold any code from 32 up).
"""
from __future__ import annotations

from dataclasses import dataclass

from ...game.league import DIVISIONS, PLACES
from .variant import FileDamaged, VariantFileError, VariantReader, pack_integer, pack_long

FILE_NAME = "footbal1.dat"
COACH_LIMIT = 100          # the game stores 30 typed characters (G-K5); a copied file may hold more


@dataclass(frozen=True)
class CoachTeam:
    tn1: int
    tn2: int
    coach: str


def encode(tn1: int, tn2: int, coach: str) -> bytes:
    codes = [ord(c) if ord(c) < 256 else ord("?") for c in coach[:COACH_LIMIT]]
    return pack_integer(tn1) + pack_integer(tn2) + pack_long(len(codes)) + b"".join(pack_integer(c) for c in codes)


def decode(raw: bytes) -> CoachTeam:
    try:
        reader = VariantReader(raw)
        tn1 = reader.next_int()
        tn2 = reader.next_int()
        length = reader.next_int()
        if not (1 <= tn1 <= DIVISIONS and 1 <= tn2 <= PLACES):
            raise FileDamaged("the team %d, %d is not one of the 32" % (tn1, tn2))
        if not 1 <= length <= COACH_LIMIT:
            raise FileDamaged("the coach name has %d characters" % length)
        codes = reader.ints(length)
    except FileDamaged:
        raise
    except VariantFileError as exc:
        raise FileDamaged(str(exc)) from exc
    if any(not 32 <= code <= 255 for code in codes):
        raise FileDamaged("the coach name holds a character code outside 32 to 255")
    return CoachTeam(tn1, tn2, "".join(chr(code) for code in codes))
