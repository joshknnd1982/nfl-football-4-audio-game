"""The news lines of the Franchise: the pools of news.txt (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 8.3 and 15, CUSTOMIZABLE_CONTENT 13 L16, CLAUDE.md 0.12, playbook 7.9. The news is customizable commentary:
the defaults are the lines of spec/STRINGS_NX.md (extras/nx_texts.py, generated, never typed), twelve pools with permanent IDs (a
pool's letters and a number: NWB01), a player's line with the same ID replaces the default, `NWB02 = off` switches it off, a new
number adds a line (NWB05 and up). A line uses the markup of banter.txt and the placeholders of its pool in angle brackets; an
unknown placeholder is spoken as written and counted as a problem. [name] and [opponent quarterback] are NOT allowed in a news line
(the news is told between games, where there is no game's list of banter names and no opponent quarterback): a line with either is a
bad line, its default is used (a new ID is left out) and one problem is counted.

The draw is the remarks' (`remarks.pick`): one line of the pool that is on, with equal chances, never one of the last three told of
that pool when more than three are on; the history is in the league record. A pool with every line off is never told. F8 (comments
off) does not silence the news (it is information the player can read again, not commentary).

A line is made when its news is made, not when it is spoken: placeholders are filled and [one of: ...] is drawn, so what the league
record keeps is plain markup that only `[sound ...]`, `[pause]`, `[bleep]`, `[then]` and `[faster]` remain in.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping

from ...game.banter_markup import NameRef, OneOf, OppQbRef, Speak, Text, choice_sizes, parse_markup, to_markup
from .. import nx_texts
from .. import remarks as R
from ..state import RECENT_REMARKS
from . import data as D

log = logging.getLogger("nfl4.extras")

POOLS = D.NEWS_POOLS
_FOR_GAME = ("<team>", "<other>", "<n>", "<score>", "<coach>")
PLACEHOLDERS = {"NWB": _FOR_GAME, "NWU": _FOR_GAME, "NWC": _FOR_GAME,
                "NWS": ("<team>", "<n>", "<coach>"), "NWL": ("<team>", "<n>", "<coach>"),
                "NWY": ("<coach>", "<n>", "<team>"), "NWZ": ("<coach>", "<n>", "<team>"), "NWM": ("<coach>", "<n>", "<team>"),
                "NWT": ("<team>", "<n>", "<coach>"),
                "NWR": ("<player>", "<position>", "<team>", "<coach>"),
                "NWD": ("<team>", "<player>", "<position>", "<coach>"),
                "NWP": ("<player>", "<position>", "<r>", "<coach>", "<team>"),
                "NWK": ("<team>", "<cap>", "<coach>"),
                "NWX": ("<team>", "<other>", "<player>", "<position>", "<coach>"),      # SX.8j: a trade of two other teams
                "NWJ": ("<team>", "<player>", "<position>", "<n>", "<coach>")}          # SX.8k: another team's player out for up to <n> weeks
MAX_NUMBER = 9999
Remark = R.Remark


def news_id(pool: str, number: int) -> str:
    return "%s%02d" % (pool, number)


def parse_id(entry_id: str) -> tuple[str, int] | None:
    """NWB1, nwb01 and NWB01 are ("NWB", 1); None for anything that is not a news ID of a pool this game has."""
    match = R.ID_PATTERN.fullmatch(entry_id)
    if match is None:
        return None
    pool, number = match.group(1).upper(), int(match.group(2))
    if pool not in POOLS or not 1 <= number <= MAX_NUMBER:
        return None
    return pool, number


def _builtin(line_id: str) -> Remark:
    pool, number = parse_id(line_id)
    pieces = (Speak((Text(nx_texts.TEXTS[line_id]),)),)
    return Remark(line_id, pool, number, pieces, to_markup(pieces), True)


DEFAULT_LINES: dict[str, tuple[Remark, ...]] = {pool: tuple(_builtin(line_id) for line_id in nx_texts.REMARK_POOLS[pool])
                                                for pool in POOLS}
DEFAULT_MARKUP: dict[str, str] = {r.id: r.markup for lines in DEFAULT_LINES.values() for r in lines}


class NewsPools:
    """The lines that are on, per pool, in the order of their numbers."""

    def __init__(self, pools: Mapping[str, tuple[Remark, ...]] | None = None):
        source = pools if pools is not None else DEFAULT_LINES
        self.pools: dict[str, tuple[Remark, ...]] = {pool: tuple(sorted(source.get(pool, ()), key=lambda r: r.number))
                                                     for pool in POOLS}

    def lines(self, pool: str) -> tuple[Remark, ...]:
        return self.pools.get(pool, ())

    @property
    def size(self) -> int:
        return sum(len(lines) for lines in self.pools.values())


DEFAULT_POOLS = NewsPools()


def _forbidden(pieces: tuple) -> bool:
    """A reference to the banter names or to the opponent's quarterback anywhere in the line."""
    for piece in pieces:
        if isinstance(piece, Speak):
            for item in piece.items:
                if isinstance(item, (NameRef, OppQbRef)):
                    return True
                if isinstance(item, OneOf) and any(isinstance(sub, (NameRef, OppQbRef)) for option in item.options for sub in option):
                    return True
    return False


def build_pools(overrides: Mapping[str, str | None], problems) -> NewsPools:
    """The pools for the player's entries: `overrides` maps a canonical ID (NWB02) to the markup, or to None for `off`. `problems`
    gets the plain-word problems (data.customlists.Problems): a bad line keeps the default (or is left out when it is a new ID); an
    unknown placeholder is a problem and is spoken as written."""
    lines: dict[str, Remark] = {r.id: r for pool in DEFAULT_LINES.values() for r in pool}
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
        if _forbidden(parsed.pieces):
            problems.add(key, "[name] and [opponent quarterback] are not known in the news, %s"
                         % ("the original line is used" if original is not None else "the line is left out"))
            continue
        known = PLACEHOLDERS.get(pool, ())
        unknown = sorted({p for text in R._texts_of(parsed.pieces) for p in R._PLACEHOLDER.findall(text) if p not in known})
        if unknown:
            problems.add(key, "%s is not known in this pool and is spoken as written (known: %s)"
                         % (", ".join(unknown), ", ".join(known) or "none"))
        lines[key] = Remark(key, pool, number, parsed.pieces, to_markup(parsed.pieces), False)
    grouped: dict[str, list[Remark]] = {pool: [] for pool in POOLS}
    for remark in lines.values():
        grouped[remark.pool].append(remark)
    return NewsPools({pool: tuple(items) for pool, items in grouped.items()})


# ----- the line a piece of news becomes -----

def _resolved(pieces: tuple, choices: list[int]) -> tuple:
    """The pieces with every [one of: ...] replaced by the option the draw chose (the draws in the order of `choice_sizes`)."""
    chosen = iter(choices)
    out = []
    for piece in pieces:
        if not isinstance(piece, Speak):
            out.append(piece)
            continue
        items: list = []
        for item in piece.items:
            parts = item.options[next(chosen) - 1] if isinstance(item, OneOf) else (item,)
            for part in parts:
                if items and isinstance(part, Text) and isinstance(items[-1], Text):
                    items[-1] = Text(items[-1].text + part.text)
                else:
                    items.append(part)
        out.append(Speak(tuple(items), piece.faster))
    return tuple(out)


def make_line(pools: NewsPools, pool: str, values: Mapping[str, str], recent: list, rnd) -> tuple[str, str] | None:
    """Draw one line of the pool (`rnd(size)`, again while one of the last three; then one draw for each [one of:]), fill the
    placeholders and return (the line's ID, its markup with the choices made); `recent` (the IDs told last of this pool) gets the
    line added. None when the pool has no line on (that kind of news is never told)."""
    lines = pools.lines(pool)
    line = R.pick(lines, recent, rnd)
    if line is None:
        return None
    recent.append(line.id)
    del recent[:-RECENT_REMARKS]
    pieces = R._filled(line.pieces, values)
    choices = [rnd(size) for size in choice_sizes(pieces)]
    markup = to_markup(_resolved(pieces, choices))
    if parse_markup(markup).pieces is None:                 # filled with long names the line is over the limit of a line: the
        fallback = DEFAULT_LINES[pool][0]                   # pool's first default line says it (its text is short)
        markup = to_markup(_resolved(R._filled(fallback.pieces, values), []))
    return line.id, markup


# ----- news.txt -----

NOTES = (
    "These are the lines of the news of your franchise. The game reads this file only when the Rules setting of the F9 menu is N. F. L.",
    "rules. Each line is an ID, an equals sign and the line. The letters of the ID say the kind of news: NWB the biggest win of the",
    "week, NWU an upset, NWC the closest game, NWS another team's winning streak and NWL its losing streak, NWY your winning streak",
    "and NWZ your losing streak, NWM your milestone of wins as a head coach, NWT the champion, NWR a star who retires, NWD the first",
    "pick of the draft, NWP a player of yours who improved a lot, NWK the team with the most room under the salary cap, NWX a trade",
    "between two other teams, NWJ a player of another team who is hurt and out for weeks (<n> is the most weeks he may miss).",
    "Change a line to say something else. Write NWB02 = off to switch a line off. Delete a line to get the original back.",
    "Add your own lines with a new number in a kind, NWB05 and up. A line is chosen by chance, never one of the last three of its kind.",
    "If every line of a kind is off, that kind of news is never told. The F8 key does not switch the news off.",
    "In a line, <team> is the team the news is about, <other> the other team of the game (NWB, NWU and NWC), <n> a number (the points,",
    "the games in a row, your wins or the season), <score> the score as said (24 to 17), <coach> your name; <player> and <position> in",
    "the kinds NWR, NWD, NWP, NWX and NWJ, and <r> (the rating he has now) in NWP only; <cap> (the cap space, said in millions) in NWK only; in",
    "NWX <team> is the team that traded the player away and <other> the team he goes to; in NWM,",
    "NWY, NWZ and NWP <team> is your team. Each kind",
    "knows only the words that belong to it; any other word in angle brackets is said as written. Spell a name the way the voice says it.",
    "The words in square brackets of banter.txt work here too: [sound my laugh.wav], [pause], [bleep], [one of: a | b]. [name] and",
    "[opponent quarterback] do not: the news is told between games. [faster] is not used in the news. A line has at most 500 characters",
    "and 20 parts; if the names filled in make it longer, the first original line of its kind is said instead.",
)


def default_entries() -> list[tuple[str, str]]:
    return [(r.id, r.markup) for pool in POOLS for r in DEFAULT_LINES[pool]]


def overrides_of(entries, problems) -> dict[str, str | None]:
    """The player's entries of news.txt by canonical ID; a non-news ID, a second line for an ID and an empty value are problems
    (the default stays)."""
    overrides: dict[str, str | None] = {}
    for entry in entries:
        parsed = parse_id(entry.id)
        if parsed is None:
            problems.add("line %d" % entry.line, "the ID %s is not a news ID (%s and a number), the line is ignored"
                         % (entry.id, ", ".join(POOLS)))
            continue
        key = news_id(*parsed)
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
