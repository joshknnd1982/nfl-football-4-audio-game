"""footplay.txt: the player's own 33 roster names and the quarterback. This is inspired by Jim Kitchen.

GAME_SPEC 11 and 12, D-025 d, Q8 and Q36, CUSTOMIZABLE_CONTENT 6 (pag reads it at 0x4544e1 to 0x4558af and writes it at
0x455908 to 0x456f0b; Getqbs appends the quarterback). Plain text, one item per line, in this order: the heading
`Running Backs:` and 6 names, `Receivers:` and 6, `Defensive Players:` and 17, `Special Teams Players:` and 2,
`Kickers:` and 2, then (added by Getqbs after the first game's quarterback question) `Quarterback:` and the name.

The player edits this file, so reading is tolerant and a mistake costs only the part that is wrong (D-025 d: the original
ends with run-time error 9 or 62 on most damaged files, Q36, and the clone does not reproduce that):

* the text is read as UTF-8 with or without a BOM, UTF-16 with a BOM, or the Windows code page (an original's file with an
  accented name), CRLF or LF, blank lines and trailing spaces ignored, headings compared ignoring case;
* the file is split at its headings; a section is good when it holds exactly its number of names and every name is 1 to
  30 characters without a comma, a semicolon or a control character (the limits of every name file, CUSTOMIZABLE_CONTENT
  10); a section that is missing or wrong is left empty in the roster and listed in `problems`, and the game draws new
  random names for it; lines before the first heading and a repeated heading are listed too and otherwise ignored;
* `Quarterback:` holds one name by the same limits, else the quarterback is "" and the game asks for it again.

`parse` never raises for a text; `format_roster` writes what the reader expects (the same headings, counts and order, one
line per item, CRLF) and, when the roster has a quarterback, his section too.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ...game.setup import COUNTS, HEADINGS, QUARTERBACK_HEADING, Roster

FILE_NAME = "footplay.txt"
PREVIOUS_NAME = "footplay.previous.txt"
NAME_MIN, NAME_MAX = 1, 30
_BAD_CHARACTERS = ",;"


def valid_name(name: str) -> bool:
    return (NAME_MIN <= len(name) <= NAME_MAX and not any(c in _BAD_CHARACTERS for c in name)
            and not any(ord(c) < 32 or ord(c) == 127 for c in name))


@dataclass
class ParsedNames:
    roster: Roster
    problems: list[str] = field(default_factory=list)

    @property
    def sound(self) -> bool:
        """Nothing was wrong: every section was there and good (the quarterback may be missing: he is asked once)."""
        return not self.problems and self.roster.is_complete()

    @property
    def usable(self) -> bool:
        """At least one section of the 33 names survived (else the game draws all of them, as for a missing file)."""
        return any(len(names) == count for (_, names), count in zip(self.roster.sections(), COUNTS))


def parse(text: str) -> ParsedNames:
    headings = {heading.casefold(): heading for heading in HEADINGS + (QUARTERBACK_HEADING,)}
    groups: dict[str, list[str]] = {}
    problems: list[str] = []
    current: list[str] | None = None
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        heading = headings.get(line.casefold())
        if heading is not None:
            if heading in groups:
                problems.append("the heading %s is there twice (line %d), the first one is used" % (heading, number))
                current = None
            else:
                groups[heading] = current = []
        elif current is not None:
            current.append(line)
        else:
            problems.append("line %d comes before any heading" % number)
    roster = Roster()
    for heading, count in zip(HEADINGS, COUNTS):
        names = groups.get(heading)
        if names is None:
            problems.append("the section %s is missing" % heading)
        elif len(names) != count:
            problems.append("the section %s holds %d names, not %d" % (heading, len(names), count))
        elif not all(valid_name(name) for name in names):
            bad = next(name for name in names if not valid_name(name))
            problems.append("the section %s holds a name that cannot be used (%r)" % (heading, bad[:40]))
        else:
            target = {"Running Backs:": roster.running_backs, "Receivers:": roster.receivers,
                      "Defensive Players:": roster.defense, "Special Teams Players:": roster.special_teams,
                      "Kickers:": roster.kickers}[heading]
            target.extend(names)
    quarterback = groups.get(QUARTERBACK_HEADING)
    if quarterback is not None:
        if len(quarterback) == 1 and valid_name(quarterback[0]):
            roster.quarterback = quarterback[0]
        else:
            problems.append("the section %s does not hold one usable name" % QUARTERBACK_HEADING)
    return ParsedNames(roster, problems)


def format_roster(roster: Roster) -> str:
    """The file the original writes (pag 0x455953 to 0x456eac) plus, when there is one, the quarterback's section."""
    lines: list[str] = []
    for heading, names in roster.sections():
        lines.append(heading)
        lines.extend(names)
    if roster.quarterback:
        lines.append(QUARTERBACK_HEADING)
        lines.append(roster.quarterback)
    return "\n".join(lines) + "\n"


def with_quarterback(text: str, name: str) -> str:
    """Getqbs's append: the text with its Quarterback section (if any) replaced by the heading and the name."""
    kept: list[str] = []
    for line in text.splitlines():
        if line.strip().casefold() == QUARTERBACK_HEADING.casefold():
            break
        kept.append(line.rstrip())
    while kept and not kept[-1]:
        kept.pop()
    kept += [QUARTERBACK_HEADING, name]
    return "\n".join(kept) + "\n"
