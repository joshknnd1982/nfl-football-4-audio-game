"""The pool of banter lines the announcer draws from: the original's 142 plus the player's. This is inspired by Jim Kitchen.

D-035, D-048, CUSTOMIZABLE_CONTENT 12. IDs B001 to B142 are the original lines (built in from game/banter_lines.py, the
table generated from the spec, never typed); a player's line with an original ID replaces it, `B045 = off` switches it off,
an ID above 142 (up to B9999) adds a line. A player's line that is exactly the original's markup is the original (its exact
spaces and structure). The pool is the lines that are ON in the order of their numbers; the draw rule of the original
(GAME_SPEC 5.13, banter.py) applies to the pool as it is.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from .banter_lines import LINES
from .banter_markup import default_pieces, parse_markup, to_markup

ID_PATTERN = re.compile(r"B(\d{1,4})", re.IGNORECASE)
MAX_NUMBER = 9999


def banter_id(number: int) -> str:
    return "B%03d" % number


def banter_number(entry_id: str) -> int | None:
    """B045 or b45 -> 45; None when the text is not a banter ID (or is B0 or above B9999)."""
    match = ID_PATTERN.fullmatch(entry_id)
    if match is None:
        return None
    number = int(match.group(1))
    return number if 1 <= number <= MAX_NUMBER else None


@dataclass(frozen=True)
class Line:
    number: int
    pieces: tuple
    markup: str
    builtin: bool           # the original's line: its pieces keep the exact spaces of the original's texts


def _builtin(line) -> Line:
    pieces = default_pieces(line)
    return Line(line.number, pieces, to_markup(pieces), True)


DEFAULT_LINES: tuple[Line, ...] = tuple(_builtin(line) for line in LINES)
DEFAULT_MARKUP: dict[int, str] = {line.number: line.markup for line in DEFAULT_LINES}


class BanterPool:
    """The lines that are on, in the order of their numbers; `off` lists the original numbers switched off."""

    def __init__(self, lines, off=()):
        self.lines: tuple[Line, ...] = tuple(sorted(lines, key=lambda line: line.number))
        self.off: tuple[int, ...] = tuple(sorted(off))

    @property
    def size(self) -> int:
        return len(self.lines)

    def numbers(self) -> list[int]:
        return [line.number for line in self.lines]


DEFAULT_POOL = BanterPool(DEFAULT_LINES)


def build_pool(overrides: Mapping[int, str | None], problems) -> BanterPool:
    """The pool for the player's entries: `overrides` maps a number to the markup text, or to None for `off`.

    `problems` (data.customlists.Problems, or anything with add(key, text)) gets the plain-word problems: a bad line keeps
    the original (or is left out when it is a new ID); an unknown word in a good line is a problem too, the line is used."""
    lines: dict[int, Line] = {}
    off: list[int] = []
    for line in DEFAULT_LINES:
        if line.number in overrides and overrides[line.number] is None:
            off.append(line.number)
        else:
            lines[line.number] = line
    for number in sorted(overrides):
        value = overrides[number]
        if value is None:
            continue
        original = DEFAULT_MARKUP.get(number)
        if original is not None and value == original:
            continue                                        # the original, unchanged: already in lines
        parsed = parse_markup(value)
        for reason in parsed.problems:
            problems.add(banter_id(number), reason)
        if parsed.pieces is None:
            problems.add(banter_id(number), "the line is left out" if original is None else "the original line is used")
            continue
        lines[number] = Line(number, parsed.pieces, to_markup(parsed.pieces), False)
    return BanterPool(lines.values(), off)
