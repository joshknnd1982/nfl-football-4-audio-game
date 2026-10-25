"""The injury texts of the Franchise: the pools of injuries.txt (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRA_FEATURES INJ-5, NFL_FRANCHISE_DESIGN 17 SX.8k, CUSTOMIZABLE_CONTENT 13 L17, CLAUDE.md 0.12, playbook 7.9. The file is made like news.txt
(`news_pools.py`): the defaults are the lines of spec/STRINGS_NX.md (extras/nx_texts.py, generated), each pool has permanent IDs (its letters and a
number: IJA01), a line with the same ID replaces the default, `IJA01 = off` switches it off, a new number adds a line (IJA02 and up). The pools:

* IJA to IJM: the spoken name of each injury kind (tuning FR_INJ_KINDS), said in the injury report (" out with a sprained ankle "). A kind whose
  lines are all off is told without its name. The kinds, their games missed and their shares are data, not the player's file (design 15: balance
  is not a player's file): a line off never changes how often an injury happens.
* IJX: the announcer's line when a player is hurt in a game the player plays (" <player> is hurt on the play and leaves the game. "), with <player>,
  <position> and <team>; the markup of banter.txt works ([sound ...], [pause], [one of: ...]); [name] and [opponent quarterback] do not.

A line is drawn with equal chances (`remarks.pick` with no history: the report and the game say one line at a time, far apart).
"""
from __future__ import annotations

from collections.abc import Mapping

from ...game.banter_markup import parse_markup, to_markup
from .. import nx_texts
from .. import remarks as R
from . import data as D
from . import news_pools as NP

POOLS = D.INJURY_POOLS
PLACEHOLDERS = {pool: () for pool in D.INJURY_KIND_POOLS}
PLACEHOLDERS["IJX"] = ("<player>", "<position>", "<team>")
MAX_NUMBER = 9999
Remark = R.Remark


def injury_id(pool: str, number: int) -> str:
    return "%s%02d" % (pool, number)


def parse_id(entry_id: str) -> tuple[str, int] | None:
    """IJA1, ija01 and IJA01 are ("IJA", 1); None for anything that is not an ID of a pool of injuries.txt."""
    match = R.ID_PATTERN.fullmatch(entry_id)
    if match is None:
        return None
    pool, number = match.group(1).upper(), int(match.group(2))
    if pool not in POOLS or not 1 <= number <= MAX_NUMBER:
        return None
    return pool, number


def _builtin(line_id: str) -> Remark:
    from ...game.banter_markup import Speak, Text
    pool, number = parse_id(line_id)
    pieces = (Speak((Text(nx_texts.TEXTS[line_id]),)),)
    return Remark(line_id, pool, number, pieces, to_markup(pieces), True)


DEFAULT_LINES: dict[str, tuple[Remark, ...]] = {pool: tuple(_builtin(line_id) for line_id in nx_texts.REMARK_POOLS[pool]) for pool in POOLS}
DEFAULT_MARKUP: dict[str, str] = {r.id: r.markup for lines in DEFAULT_LINES.values() for r in lines}


class InjuryPools:
    """The lines that are on, per pool, in the order of their numbers."""

    def __init__(self, pools: Mapping[str, tuple[Remark, ...]] | None = None):
        source = pools if pools is not None else DEFAULT_LINES
        self.pools: dict[str, tuple[Remark, ...]] = {pool: tuple(sorted(source.get(pool, ()), key=lambda r: r.number)) for pool in POOLS}

    def lines(self, pool: str) -> tuple[Remark, ...]:
        return self.pools.get(pool, ())

    @property
    def size(self) -> int:
        return sum(len(lines) for lines in self.pools.values())


DEFAULT_POOLS = InjuryPools()


def build_pools(overrides: Mapping[str, str | None], problems) -> InjuryPools:
    """The pools for the player's entries (`overrides`: a canonical ID to the markup, or None for off), as news.txt's: a bad line keeps the default
    (a new ID is left out), an unknown placeholder is a problem and is spoken as written, [name] and [opponent quarterback] are not allowed."""
    lines: dict[str, Remark] = {r.id: r for pool in DEFAULT_LINES.values() for r in pool}
    for key in sorted(overrides):
        value = overrides[key]
        pool, number = parse_id(key)
        if value is None:
            lines.pop(key, None)
            continue
        original = DEFAULT_MARKUP.get(key)
        if original is not None and value == original:
            continue
        parsed = parse_markup(value)
        for reason in parsed.problems:
            problems.add(key, reason)
        if parsed.pieces is None:
            problems.add(key, "the line is left out" if original is None else "the original line is used")
            continue
        if NP._forbidden(parsed.pieces):
            problems.add(key, "[name] and [opponent quarterback] are not known in injuries.txt, %s"
                         % ("the original line is used" if original is not None else "the line is left out"))
            continue
        known = PLACEHOLDERS.get(pool, ())
        unknown = sorted({p for text in R._texts_of(parsed.pieces) for p in R._PLACEHOLDER.findall(text) if p not in known})
        if unknown:
            problems.add(key, "%s is not known in this pool and is spoken as written (known: %s)" % (", ".join(unknown), ", ".join(known) or "none"))
        lines[key] = Remark(key, pool, number, parsed.pieces, to_markup(parsed.pieces), False)
    grouped: dict[str, list[Remark]] = {pool: [] for pool in POOLS}
    for remark in lines.values():
        grouped[remark.pool].append(remark)
    return InjuryPools({pool: tuple(items) for pool, items in grouped.items()})


def make_line(pools: InjuryPools, pool: str, values: Mapping[str, str], rnd) -> str | None:
    """Draw one line of the pool (`rnd(size)`, then one draw for each [one of:]), fill its placeholders: its markup, or None when every line of the
    pool is off."""
    line = R.pick(pools.lines(pool), [], rnd)
    if line is None:
        return None
    pieces = R._filled(line.pieces, values)
    from ...game.banter_markup import choice_sizes
    choices = [rnd(size) for size in choice_sizes(pieces)]
    markup = to_markup(NP._resolved(pieces, choices))
    if parse_markup(markup).pieces is None:                     # filled with long names it is over a line's limit: the first default line
        markup = to_markup(NP._resolved(R._filled(DEFAULT_LINES[pool][0].pieces, values), []))
    return markup


# ----- injuries.txt -----

NOTES = (
    "These are the words the game says about injuries in your franchise. The game reads this file only when the Rules setting of the F9 menu is",
    "N. F. L. rules, and injuries happen only in a franchise, never in a quick game or a classic season. Each line is an ID, an equals sign",
    "and the words. IJA to IJM are the names of the kinds of injury, said in the injury report after the word with (out with a sprained",
    "ankle): IJA a sprained ankle, IJB a hamstring, IJC a knee sprain, IJD a shoulder, IJE a concussion, IJF the ribs, IJG a groin,",
    "IJH a broken hand, IJK a high ankle sprain, IJL a torn knee ligament, IJM the back. IJX is what the announcer says when a player is",
    "hurt in a game you play; there <player> is the player, <position> his position and <team> his team.",
    "Change a line to say something else. Write IJA01 = off to switch a line off; if every line of a kind is off, the report names no",
    "injury for it. Delete a line to get the original back. Add your own lines with a new number, IJA02 and up: one of the lines that are",
    "on is chosen by chance. How often an injury happens and how long it lasts do not depend on this file.",
    "The words in square brackets of banter.txt work here too: [sound my groan.wav], [pause], [bleep], [one of: a | b]. [name] and",
    "[opponent quarterback] do not. A line has at most 500 characters and 20 parts.",
)


def default_entries() -> list[tuple[str, str]]:
    return [(r.id, r.markup) for pool in POOLS for r in DEFAULT_LINES[pool]]


def overrides_of(entries, problems) -> dict[str, str | None]:
    """The player's entries of injuries.txt by canonical ID; a wrong ID, a second line for an ID and an empty value are problems (the default stays)."""
    overrides: dict[str, str | None] = {}
    for entry in entries:
        parsed = parse_id(entry.id)
        if parsed is None:
            problems.add("line %d" % entry.line, "the ID %s is not an injury ID (%s and a number), the line is ignored" % (entry.id, ", ".join(POOLS)))
            continue
        key = injury_id(*parsed)
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
