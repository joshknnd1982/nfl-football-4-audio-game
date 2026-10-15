"""football.sav: the saved game. This is inspired by Jim Kitchen.

GAME_SPEC 12 (written by Save Game at 0x45f655 with Put, read by pag at 0x43afa4 in the same order, then closed and
deleted with Kill). Every value is a Variant (a reader accepts any number type, D-024 item 4), in this order:

     1 wisoff (the side on offense)          2 L504 (the other side)          3 Lcc (the half: 1 the opponent's, 2 the player's)
     4 the quarter (5 = overtime)            5 the play counter               6 to 10 the plays of quarters 1 to 4 and overtime
    11 CountDown                            12 to 31 ten statistics, each the player's value then the opponent's:
         pass attempts, completions, passing yards, times sacked, times intercepted, running plays, running yards,
         fumbles lost, first downs, scores
    32 the yard line                        33 Lcc again (written twice; the second read wins)   34 the down   35 yards to go
    36 the length of the opponent quarterback's name (a Long), then one Integer per letter (its character code)

and, added by the clone (D-027 item 3, Q28), one more Integer after the name: the side that received the opening
kick-off. An original's file stops after the name and is accepted (the original's own rule then applies); a clone's file
stays readable by the original, which reads only its own 36 values and the name.

nfl4 only (rule 0.13, NFL_EXTRAS_DESIGN 12.3, PX SX.2): a game played with the N. F. L. rules adds three more Variants: the
String "NX-EXTRAS", the Integer 1 (the format) and one String with the extras record as UTF-8 JSON. A marker with another
format number, or a record that is not UTF-8, keeps the marker and drops the record (the extras then start from their start
values with one notice, C10); everything before it still loads. A Classic game writes none of it.

`decode` raises `FileDamaged` for a file that is short, holds a value outside what a game can have, or has a name that is
not text. Nothing here reads the disk.
"""
from __future__ import annotations

import math

from ...game.gamestate import SavedGame, SideStats
from .variant import (VT_STRING, FileDamaged, VariantFileError, VariantReader, pack_integer, pack_long, pack_number,
                      pack_string)

FILE_NAME = "football.sav"
EXTRAS_MARKER = b"NX-EXTRAS"
EXTRAS_FORMAT = 1
STATISTICS = ("pass_attempts", "completions", "passing_yards", "sacked", "intercepted", "running_plays", "running_yards",
              "fumbles_lost", "first_downs", "score")
NAME_LIMIT = 200           # a name is at most 30 typed characters (G-K5) or a pool surname; the bound keeps junk out


def encode(saved: SavedGame) -> bytes:
    out = bytearray()
    out += pack_integer(saved.wisoff) + pack_integer(saved.defense) + pack_integer(saved.half)
    out += pack_integer(saved.quarter) + pack_integer(saved.counter)
    out += b"".join(pack_integer(plays) for plays in saved.plays[:5])
    out += pack_number(saved.countdown)
    for field in STATISTICS:
        out += pack_number(getattr(saved.stats[1], field)) + pack_number(getattr(saved.stats[2], field))
    out += pack_integer(saved.yard_line) + pack_integer(saved.half) + pack_integer(saved.down) + pack_integer(saved.to_go)
    codes = [ord(c) if ord(c) < 256 else ord("?") for c in saved.opponent_quarterback[:NAME_LIMIT]]
    out += pack_long(len(codes)) + b"".join(pack_integer(c) for c in codes)
    if saved.opening_receiver is not None:
        out += pack_integer(saved.opening_receiver)
    if saved.extras is not None:
        out += pack_string(EXTRAS_MARKER) + pack_integer(EXTRAS_FORMAT) + pack_string(saved.extras.encode("utf-8"))
    return bytes(out)


def _within(value, low, high, what):
    if not low <= value <= high:
        raise FileDamaged("%s is %s, not %s to %s" % (what, value, low, high))
    return value


def decode(raw: bytes) -> SavedGame:
    try:
        reader = VariantReader(raw)
        wisoff = _within(reader.next_int(), 1, 2, "the side on offense")
        defense = _within(reader.next_int(), 1, 2, "the defending side")
        half = _within(reader.next_int(), 1, 2, "the half")
        quarter = _within(reader.next_int(), 1, 5, "the quarter")
        counter = _within(reader.next_int(), 0, 200, "the play counter")      # 0 at the start of quarter 3 and of overtime
        plays = [_within(reader.next_int(), 1, 99, "the plays of a quarter") for _ in range(5)]
        countdown = reader.next()
        if not (isinstance(countdown, (int, float)) and math.isfinite(countdown) and 0 <= countdown <= 1000):
            raise FileDamaged("CountDown is %r" % (countdown,))
        stats = {1: SideStats(), 2: SideStats()}
        for field in STATISTICS:
            for side in (1, 2):
                setattr(stats[side], field, _within(reader.next_int(), -9999, 99999, field))
        yard_line = _within(reader.next_int(), 0, 50, "the yard line")
        _within(reader.next_int(), 1, 2, "the half, written a second time")
        down = _within(reader.next_int(), 1, 4, "the down")
        to_go = _within(reader.next_int(), 1, 100, "the yards to go")
        length = _within(reader.next_int(), 0, NAME_LIMIT, "the length of the quarterback's name")
        codes = reader.ints(length)
        if any(not 0 <= code <= 255 for code in codes):
            raise FileDamaged("the quarterback's name holds a character code outside 0 to 255")
        opening = None
        if not reader.at_end and reader.raw[reader.position] != VT_STRING:     # a String's type word begins with 8
            opening = _within(reader.next_int(), 1, 2, "the side that received the opening kick-off")
        extras, marked = None, False
        if not reader.at_end:
            extras, marked = _extras(reader)
    except FileDamaged:
        raise
    except VariantFileError as exc:
        raise FileDamaged(str(exc)) from exc
    name = "".join(chr(code) for code in codes)
    return SavedGame(wisoff, defense, half, quarter, counter, plays, countdown, stats, yard_line, down, to_go, name, opening,
                     extras, marked)


def _extras(reader: VariantReader) -> tuple[str | None, bool]:
    """The extras section (nfl4 SX.2): (the JSON text, True), or (None, True) for a marker whose record cannot be used,
    including a file cut inside the marker itself (its bytes are then a beginning of the marker's record). Anything else
    after the game is a damaged file, as before."""
    marker = pack_string(EXTRAS_MARKER)
    rest = reader.raw[reader.position:]
    if len(rest) < len(marker) and marker.startswith(rest):
        return None, True
    if not rest.startswith(marker):
        raise FileDamaged("the file holds more than a game")
    reader.next_string()
    try:
        version = reader.next_int()
        record = reader.next_string()
        if not reader.at_end:
            raise VariantFileError("the file holds more after the extras")
        if version != EXTRAS_FORMAT:
            raise VariantFileError("the extras are format %r, this game reads format %d" % (version, EXTRAS_FORMAT))
        return record.decode("utf-8"), True
    except (VariantFileError, UnicodeDecodeError):
        return None, True
