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
INFO_MARKER = b"NX-INFO"            # SX.14: the facts of the one-sentence summary (teams, week, date, time left), UTF-8 JSON
RESUME_MARKER = b"NX-RESUME"        # SX.14: what an automatic save keeps so the game goes on with the same draws, UTF-8 JSON
SECTION_FORMAT = 1
_SECTIONS = (EXTRAS_MARKER, INFO_MARKER, RESUME_MARKER)
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
    for marker, text in ((INFO_MARKER, saved.info), (RESUME_MARKER, saved.resume)):
        if text is not None:
            out += pack_string(marker) + pack_integer(SECTION_FORMAT) + pack_string(text.encode("utf-8"))
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
        sections = _sections(reader) if not reader.at_end else {}
    except FileDamaged:
        raise
    except VariantFileError as exc:
        raise FileDamaged(str(exc)) from exc
    name = "".join(chr(code) for code in codes)
    extras = sections.get(EXTRAS_MARKER)
    return SavedGame(wisoff, defense, half, quarter, counter, plays, countdown, stats, yard_line, down, to_go, name, opening,
                     extras, EXTRAS_MARKER in sections, sections.get(INFO_MARKER), sections.get(RESUME_MARKER))


def _sections(reader: VariantReader) -> dict:
    """The sections after the game (nfl4 SX.2 and SX.14): {marker: JSON text, or None when the section's record cannot be used}.
    A file cut inside a marker is read as that marker with no record (its bytes are a beginning of the marker's record); a
    section the clone does not know is a damaged file, as before. The extras section that is followed by something else
    keeps its marker and drops its record (SX.2's rule)."""
    found: dict = {}
    while not reader.at_end:
        rest = reader.raw[reader.position:]
        marker = next((m for m in _SECTIONS if rest.startswith(pack_string(m))), None)
        if marker is None:
            cut = next((m for m in _SECTIONS if len(rest) < len(pack_string(m)) and pack_string(m).startswith(rest)), None)
            if cut is None and EXTRAS_MARKER in found:        # SX.2's rule: more after the extras than the clone knows drops the record
                found[EXTRAS_MARKER] = None
                return found
            if cut is None or cut in found:
                raise FileDamaged("the file holds more than a game")
            found[cut] = None
            return found
        if marker in found:
            raise FileDamaged("the file holds the %s section twice" % marker.decode())
        reader.next_string()
        try:
            version = reader.next_int()
            record = reader.next_string()
            if version != (EXTRAS_FORMAT if marker == EXTRAS_MARKER else SECTION_FORMAT):
                raise VariantFileError("%s is format %r, this game reads another" % (marker.decode(), version))
            found[marker] = record.decode("utf-8")
        except (VariantFileError, UnicodeDecodeError):
            found[marker] = None
            return found
    return found
