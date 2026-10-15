"""The announcer's remarks of the extras: the pools of remarks.txt (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

CUSTOMIZABLE_CONTENT 13 (L13), CLAUDE.md 0.12, playbook 7.9, D-042. Every pool is customizable commentary: the defaults are the
lines of spec/STRINGS_NX.md (extras/nx_texts.py, generated, never typed), each with a permanent ID; a player's line with the
same ID replaces it, `TO03 = off` switches it off, a new number adds a line (TO06 and up). A line uses the markup of banter.txt
(game/banter_markup.py: [sound file], [pause], [bleep], [one of: a | b], [name], [opponent quarterback], [then], [faster]) and
the placeholders of its pool in angle brackets (the TO pool: <team>, <coach>, <quarterback>); an unknown placeholder is spoken
as it is written and counted as a problem when the file is read.

The draw (design 6.3, CUSTOMIZABLE_CONTENT 13): one line of the pool's lines that are on, with equal chances, never one of the
last three spoken in this game when the pool has more than three lines on (`Int(Rnd * size) + 1`, drawn again while it is one
of them; bounded, G-D1); a line with [name] draws a name of the banter's list after it, a line with [one of:] its choices
after that. F8 (comments off) silences the pools of commentary before any draw. A pool with no line on says nothing.

Built so far: TO (SX.2). Each later session adds its pool to POOLS_BUILT and its placeholders to PLACEHOLDERS.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Mapping

from ..game.banter import NAME_LIST_SIZE, play_line
from ..game.banter_markup import NameRef, OneOf, Speak, Text, choice_sizes, parse_markup, to_markup
from . import nx_texts
from .state import RECENT_REMARKS

log = logging.getLogger("nfl4.extras")

POOLS_BUILT = ("TO",)                                    # the pools whose feature exists (SX.2: the timeout remarks)
COMMENTARY_POOLS = frozenset(("TO", "CHS", "CHC", "RVR", "RVC", "ON", "PN"))   # F8 silences these; QB is play-by-play
PLACEHOLDERS = {"TO": ("<team>", "<coach>", "<quarterback>")}
ID_PATTERN = re.compile(r"([A-Z]{2,3})(\d{1,4})", re.IGNORECASE)
MAX_NUMBER = 9999
_PLACEHOLDER = re.compile(r"<[^<>]{1,30}>")


def remark_id(pool: str, number: int) -> str:
    return "%s%02d" % (pool, number)


def parse_id(entry_id: str) -> tuple[str, int] | None:
    """TO3, to03 and TO03 are ("TO", 3); None for anything that is not a remark ID of a pool this game has."""
    match = ID_PATTERN.fullmatch(entry_id)
    if match is None:
        return None
    pool, number = match.group(1).upper(), int(match.group(2))
    if pool not in POOLS_BUILT or not 1 <= number <= MAX_NUMBER:
        return None
    return pool, number


@dataclass(frozen=True)
class Remark:
    id: str
    pool: str
    number: int
    pieces: tuple
    markup: str
    builtin: bool                  # a default line: its text keeps the exact spaces of STRINGS_NX


def _builtin(remark_id_text: str) -> Remark:
    parsed = parse_id(remark_id_text)
    if parsed is None:
        raise ValueError("%s is not a remark of a built pool" % remark_id_text)
    pieces = (Speak((Text(nx_texts.TEXTS[remark_id_text]),)),)
    return Remark(remark_id_text, parsed[0], parsed[1], pieces, to_markup(pieces), True)


DEFAULT_REMARKS: dict[str, tuple[Remark, ...]] = {
    pool: tuple(_builtin(rid) for rid in nx_texts.REMARK_POOLS[pool]) for pool in POOLS_BUILT}
DEFAULT_MARKUP: dict[str, str] = {r.id: r.markup for lines in DEFAULT_REMARKS.values() for r in lines}


class RemarkPools:
    """The lines that are on, per pool, in the order of their numbers."""

    def __init__(self, pools: Mapping[str, tuple[Remark, ...]] | None = None):
        source = pools if pools is not None else DEFAULT_REMARKS
        self.pools: dict[str, tuple[Remark, ...]] = {
            pool: tuple(sorted(source.get(pool, ()), key=lambda r: r.number)) for pool in POOLS_BUILT}

    def lines(self, pool: str) -> tuple[Remark, ...]:
        return self.pools.get(pool, ())

    @property
    def size(self) -> int:
        return sum(len(lines) for lines in self.pools.values())


DEFAULT_POOLS = RemarkPools()


def _texts_of(pieces: tuple) -> list[str]:
    out = []
    for piece in pieces:
        if isinstance(piece, Speak):
            for item in piece.items:
                if isinstance(item, Text):
                    out.append(item.text)
                elif isinstance(item, OneOf):
                    out.extend(sub.text for option in item.options for sub in option if isinstance(sub, Text))
    return out


def build_pools(overrides: Mapping[str, str | None], problems) -> RemarkPools:
    """The pools for the player's entries: `overrides` maps a canonical ID (TO03) to the markup, or to None for `off`.
    `problems` gets the plain-word problems (data.customlists.Problems): a bad line keeps the default (or is left out when it
    is a new ID); an unknown placeholder is a problem and is spoken as written."""
    lines: dict[str, Remark] = {r.id: r for pool in DEFAULT_REMARKS.values() for r in pool}
    for key in sorted(overrides):
        value = overrides[key]
        pool, number = parse_id(key)
        if value is None:
            lines.pop(key, None)
            continue
        original = DEFAULT_MARKUP.get(key)
        if original is not None and value == original:
            continue                                            # the default, unchanged: its exact spaces stay
        parsed = parse_markup(value)
        for reason in parsed.problems:
            problems.add(key, reason)
        if parsed.pieces is None:
            problems.add(key, "the line is left out" if original is None else "the original line is used")
            continue
        known = PLACEHOLDERS.get(pool, ())
        unknown = sorted({p for text in _texts_of(parsed.pieces) for p in _PLACEHOLDER.findall(text) if p not in known})
        if unknown:
            problems.add(key, "%s is not known in this pool and is spoken as written (known: %s)"
                         % (", ".join(unknown), ", ".join(known) or "none"))
        lines[key] = Remark(key, pool, number, parsed.pieces, to_markup(parsed.pieces), False)
    grouped: dict[str, list[Remark]] = {pool: [] for pool in POOLS_BUILT}
    for remark in lines.values():
        grouped[remark.pool].append(remark)
    return RemarkPools({pool: tuple(items) for pool, items in grouped.items()})


# ----- the draw and the line -----

def _fill(text: str, values: Mapping[str, str]) -> str:
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    return text


def _filled(pieces: tuple, values: Mapping[str, str]) -> tuple:
    """The pieces with the pool's placeholders replaced in every text, the choices of [one of:] too."""
    out = []
    for piece in pieces:
        if not isinstance(piece, Speak):
            out.append(piece)
            continue
        items = []
        for item in piece.items:
            if isinstance(item, Text):
                items.append(Text(_fill(item.text, values)))
            elif isinstance(item, OneOf):
                items.append(OneOf(tuple(tuple(Text(_fill(sub.text, values)) if isinstance(sub, Text) else sub
                                                for sub in option) for option in item.options)))
            else:
                items.append(item)
        out.append(Speak(tuple(items), piece.faster))
    return tuple(out)


def _has_name(pieces: tuple) -> bool:
    for piece in pieces:
        if isinstance(piece, Speak):
            for item in piece.items:
                if isinstance(item, NameRef):
                    return True
                if isinstance(item, OneOf) and any(isinstance(sub, NameRef) for option in item.options for sub in option):
                    return True
    return False


def pick(pool_lines: tuple[Remark, ...], recent: list[str], rnd) -> Remark | None:
    """One line, never one of the last three spoken when the pool has more than three (G-D1 bounds the redraw)."""
    if not pool_lines:
        return None
    size = len(pool_lines)
    if size <= RECENT_REMARKS:
        return pool_lines[rnd(size) - 1]
    index = rnd.redraw(lambda: rnd(size), lambda n: pool_lines[n - 1].id not in recent,
                       lambda: next(n for n in range(1, size + 1) if pool_lines[n - 1].id not in recent), "remark line")
    return pool_lines[index - 1]


def say_remark(game, state, record, pool: str, values: Mapping[str, str]) -> Remark | None:
    """Draw and say one remark of `pool` (F8 silences the commentary pools before any draw). Returns the line said."""
    if pool in COMMENTARY_POOLS and game.comtog == 1:
        return None
    pools = getattr(game, "remark_pools", None) or DEFAULT_POOLS
    recent = list(record.recent.get(pool, []))
    remark = pick(pools.lines(pool), recent, game.rnd)
    if remark is None:
        return None
    record.recent[pool] = (recent + [remark.id])[-RECENT_REMARKS:]
    name = ""
    if _has_name(remark.pieces):
        names = state.banter_names
        index = game.rnd(NAME_LIST_SIZE)
        name = names[index - 1] if index <= len(names) else ""
    pieces = _filled(remark.pieces, values)
    choices = [game.rnd(size) for size in choice_sizes(pieces)]
    play_line(game, pieces, name, state.quarterbacks.get(2, ""), choices)
    return remark


# ----- remarks.txt -----

NOTES = (
    "These are the announcer's remarks of the N. F. L. rules. The game reads this file only when the Rules setting of the F9 "
    "menu is N. F. L. rules.",
    "Each line is an ID, an equals sign and the remark. The letters of the ID say the pool: TO are the remarks after a time out.",
    "Change a line to say something else. Write TO03 = off to switch a line off. Delete a line to get the original back.",
    "Add your own lines with a new number in a pool, TO06 and up. A remark is chosen by chance, never one of the last three.",
    "In a line, <team> is the team that called the time out, <coach> is your name and <quarterback> that team's quarterback.",
    "The words in square brackets of banter.txt work here too: [sound my laugh.wav], [pause], [bleep], [one of: a | b].",
    "A line has at most 500 characters and 20 parts. The F8 key switches all comments off, these too.",
)


def default_entries() -> list[tuple[str, str]]:
    return [(r.id, r.markup) for pool in POOLS_BUILT for r in DEFAULT_REMARKS[pool]]


def overrides_of(entries, problems) -> dict[str, str | None]:
    """The player's entries of remarks.txt by canonical ID; a non-remark ID, a second line for an ID and an empty value are
    problems (the default stays)."""
    overrides: dict[str, str | None] = {}
    for entry in entries:
        parsed = parse_id(entry.id)
        if parsed is None:
            problems.add("line %d" % entry.line, "the ID %s is not a remark ID (%s and a number), the line is ignored"
                         % (entry.id, ", ".join(POOLS_BUILT)))
            continue
        key = remark_id(*parsed)
        if key in overrides:
            problems.add(key, "this ID is there twice, the first line is used")
            continue
        if entry.value.casefold() == "off":
            overrides[key] = None
        elif entry.value == "":
            problems.add(key, "the line has no text (write off to switch a line off), the original is used")
        else:
            overrides[key] = entry.value
    return overrides
