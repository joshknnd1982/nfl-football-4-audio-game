"""penalties.txt: the player's part of the foul table (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

CUSTOMIZABLE_CONTENT 13 (L14), CLAUDE.md 0.12, playbook 7.9, design 9.2. One line per foul of extras/fouls_2026.py, its ID and
its spoken name, `P08 = holding`; optional settings after a semicolon: `P08 = holding; off` (the foul is never called) or
`P08 = holding; weight 50` (its chance in percent of the default, 0 to 200). The yards, the spots and the enforcement are the
NFL's rules (extras/rules_2026.py, extras/penalties.py) and are not in the file: a player chooses which fouls happen, how
often and how they are named, never the rules. The F9 Rules menu's Penalties switch turns all of them off. The file is one
more list of data/customlists.py (the same format and healing) and is read only while the Rules setting is the N. F. L.
rules (data/customize.py EXTRA_SPECS).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import fouls_2026 as F
from . import nx_texts as X

ID_PATTERN = re.compile(r"P(\d{1,2})", re.IGNORECASE)
WEIGHT_MAX = 200
NOTES = (
    "These are the fouls the officials call with the N. F. L. rules. The game reads this file only when the Rules setting "
    "of the F9 menu is N. F. L. rules.",
    "Each line is an ID, an equals sign and the name the announcer says. Change a name to have it said your way.",
    "After the name a semicolon and off switch a foul off: P08 = holding; off. The officials never call it then.",
    "Or a semicolon and a weight from 0 to 200 changes how often it is called, in percent: P08 = holding; weight 50 is "
    "half as often.",
    "The yards and the rules of each penalty are the N. F. L.'s and cannot be changed here. Delete a line to get the "
    "original back.",
    "A name has 1 to 30 characters, with no comma and no semicolon. The Penalties item of the F9 Rules menu switches all "
    "fouls off.",
)


def canonical(entry_id: str) -> str | None:
    """P8, p08 and P08 are "P08"; None for an ID that is not a foul of the table."""
    match = ID_PATTERN.fullmatch(entry_id.strip())
    if match is None:
        return None
    key = "P%02d" % int(match.group(1))
    return key if key in F.BY_ID else None


@dataclass(frozen=True)
class FoulTable:
    names: dict = field(default_factory=dict)      # ID -> the spoken name
    weights: dict = field(default_factory=dict)    # ID -> percent of the default rate, 0 (off) to 200

    def name(self, foul_id: str) -> str:
        return self.names.get(foul_id) or X.text(F.name_id(foul_id))

    def percent(self, foul_id: str) -> int:
        return self.weights.get(foul_id, 100)


DEFAULT_TABLE = FoulTable({i: X.text(F.name_id(i)) for i in F.IDS}, {i: 100 for i in F.IDS})


def default_entries() -> list[tuple[str, str]]:
    return [(i, X.text(F.name_id(i))) for i in F.IDS]


def _name_problem(name: str) -> str | None:
    from ..data.customize import name_problem          # the limits of every list's names (CUSTOMIZABLE_CONTENT 10)
    return name_problem(name)


def parse_value(value: str) -> tuple[str, int | None, list[str]]:
    """(the name, the percent or None for the default, the problems) of one line's value."""
    parts = [part.strip() for part in value.split(";")]
    name, options = parts[0], parts[1:]
    percent: int | None = None
    off = False
    problems: list[str] = []
    for option in options:
        words = option.casefold().split()
        if not words:
            continue
        if words == ["off"]:
            off = True                             # off wins over a weight, wherever it stands
        elif words == ["on"]:
            continue
        elif words[0] == "weight" and len(words) == 2 and words[1].isdigit() and int(words[1]) <= WEIGHT_MAX:
            percent = int(words[1])
        else:
            problems.append("'%s' is not off or a weight from 0 to %d, it is ignored" % (option[:30], WEIGHT_MAX))
    return name, 0 if off else percent, problems


def table_of(entries, problems) -> FoulTable:
    """The foul table for the player's entries; `problems` (data.customlists.Problems) gets the plain-word problems: an ID
    that is not a foul, a second line for an ID, a name the limits refuse (the original name is used) and a setting that is
    not understood (ignored)."""
    names = dict(DEFAULT_TABLE.names)
    weights = dict(DEFAULT_TABLE.weights)
    seen: set[str] = set()
    for entry in entries:
        key = canonical(entry.id)
        if key is None:
            problems.add("line %d" % entry.line, "the ID %s is not a foul of this game (P01 to P33), the line is ignored"
                         % entry.id)
            continue
        if key in seen:
            problems.add(key, "this ID is there twice, the first line is used")
            continue
        seen.add(key)
        name, percent, option_problems = parse_value(entry.value)
        for reason in option_problems:
            problems.add(key, reason)
        if name:
            reason = _name_problem(name)
            if reason:
                problems.add(key, "%s, the original name is used" % reason)
            else:
                names[key] = name
        else:
            problems.add(key, "the line has no name, the original name is used")
        if percent is not None:
            weights[key] = percent
    return FoulTable(names, weights)
