"""The playbooks in use: the table the player's files change, the bounded modifiers, the H8 door (nfl4 only, rule 0.13; NX5). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 10.3 and 3 (H8). `Table` is the catalog's names and switches, the seven styles and the teams' assignment, as the
built-in data (extras/playbook_data.py) and the player's files (plays.txt, styles.txt, team_styles.txt; extras/playbook_list.py)
make them. The engine never sees any of it: it reads the outcome tables through `PlaybookModifiers`, which Classic replaces by
NEUTRAL, and which changes a row only by the combined `Mod` of the two plays that were called, clamped to `BOUNDS` (design 10.3).

    combined(table, off, defense, family, call)   the Mod of an offense play and a defense play, bounded
    PlaybookModifiers                             the H8 object of a game with N. F. L. rules: unchanged rows when no play
                                                  of a playbook is armed
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..game.playtables import FUMBLE_ODDS, Modifiers, PassEntry, QBRunEntry, RunEntry
from . import nx_texts as X
from . import playbook_data as D

CLASSIC = D.CLASSIC_KEY
MOD_FIELDS = D.MOD_NAMES


def clamp(mod: D.Mod) -> D.Mod:
    """Every component within its bound (design 10.3)."""
    return D.Mod(*(max(-limit, min(limit, value)) for value, limit in zip(mod, D.BOUNDS)))


@dataclass(frozen=True)
class StyleBook:
    """One style as it is in use: its plays (the enabled ones with their weights) and its tilts by ID (OB1 to OB3, OP1 to OP3,
    DB1 to DB3, DP1 to DP3: offense or defense, bonus or penalty, the number)."""
    key: str
    code: str
    name_id: str
    offense: dict
    defense: dict
    tilts: dict
    qb_percent: int = 100

    def tilts_of(self, side: str) -> list[D.Tilt]:
        return [tilt for tilt_id, tilt in self.tilts.items() if tilt_id[0] == side]


def style_book(style: D.Style) -> StyleBook:
    tilts = {}
    for name, tilt_list in (("OB", style.off_bonus), ("OP", style.off_penalty), ("DB", style.def_bonus),
                            ("DP", style.def_penalty)):
        for number, tilt in enumerate(tilt_list, start=1):
            tilts["%s%d" % (name, number)] = tilt
    return StyleBook(style.key, style.code, style.name_id, dict(style.offense), dict(style.defense), tilts, style.qb_percent)


@dataclass(frozen=True)
class Table:
    names: dict            # play ID -> the spoken name (plays.txt)
    disabled: frozenset    # play IDs switched off in plays.txt
    styles: dict           # style key -> StyleBook (styles.txt)
    teams: tuple           # 32 pairs (offense, defense): a style key or "classic" (team_styles.txt)

    def name(self, play_id: str) -> str:
        return self.names.get(play_id) or X.text(D.PLAYS[play_id].name_id)

    def style_name(self, key: str) -> str:
        if key == CLASSIC:
            return X.text("NXM-27")
        return X.text(self.styles[key].name_id) if key in self.styles else X.text("NXM-27")

    def usable(self, key: str, side: str) -> list[tuple[D.Play, int]]:
        """The plays of a style's offense ("O") or defense ("D") that are on, in the order of their IDs: (play, weight)."""
        book = self.styles.get(key)
        if book is None:
            return []
        members = book.offense if side == "O" else book.defense
        return [(D.PLAYS[pid], weight) for pid, weight in sorted(members.items())
                if weight > 0 and pid in D.PLAYS and pid not in self.disabled]

    def team_style(self, team_index: int, side: str) -> str:
        """The style key of the team (0 to 31) for its offense ("O") or defense ("D"); "classic" for a number out of range."""
        if not 0 <= team_index < len(self.teams):
            return CLASSIC
        return self.teams[team_index][0 if side == "O" else 1]


def default_table() -> Table:
    styles = {s.key: style_book(s) for s in D.STYLES}
    return Table({pid: X.text(play.name_id) for pid, play in D.PLAYS.items()}, frozenset(), styles, tuple(D.TEAM_STYLES))


DEFAULT_TABLE = default_table()


# ----- the modifiers -----

def play_mod(play: D.Play, calls: int) -> D.Mod:
    """The play's own tilt against one family of the opponent (`calls`)."""
    total = D.ZERO
    for rule in play.rules:
        if calls in rule.vs:
            total = total.plus(rule.mod)
    return total


def style_mod(book: StyleBook | None, side: str, family: int, calls: int) -> D.Mod:
    total = D.ZERO
    if book is None:
        return total
    for tilt in book.tilts_of(side):
        if family in tilt.families and calls in tilt.vs:
            total = total.plus(tilt.mod)
    return total


def side_mod(book: StyleBook | None, play: D.Play | None, calls: int) -> D.Mod:
    """One side's mod against the opponent's family `calls`: the play's tilt plus its style's, bounded."""
    if play is None:
        return D.ZERO
    return clamp(play_mod(play, calls).plus(style_mod(book, play.side, play.family, calls)))


def combined(table: Table, off_style: str, offense: D.Play | None, def_style: str, defense: D.Play | None,
             offense_family: int, defense_family: int) -> D.Mod:
    """The mod of the pair of plays on the row of (offense family, defense family): the offense play's and the defense play's,
    each against the other's family, added and bounded again (a row never moves more than design 10.3 allows)."""
    off = side_mod(table.styles.get(off_style), offense, defense_family)
    de = side_mod(table.styles.get(def_style), defense, offense_family)
    return clamp(off.plus(de))


class PlaybookModifiers(Modifiers):
    """H8 with a playbook: while `mod` is armed (before the snap, from the two plays that were called) the rows move by it."""

    def __init__(self):
        self.mod: D.Mod | None = None

    def arm(self, mod: D.Mod | None) -> None:
        self.mod = mod if mod is not None and any(mod) else None

    def bind(self, state) -> None:
        """The game's state, given once per game (`NflRules.period_clock`). The playbooks do not read it; the Franchise's
        ratings do (extras/franchise/ratings.py)."""
        return None

    def mod_for(self, kind: str) -> D.Mod | None:
        """The Mod in force for a read of the table of `kind` ("run", "pass", "qb" or "fumble"): the armed playbook Mod. The
        Franchise adds its ratings Mod to it and clamps the sum to the same bounds (design 5.1)."""
        return self.mod

    def run(self, offense: int, defense: int, entry: RunEntry) -> RunEntry:
        m = self.mod_for("run")
        if m is None:
            return entry
        low, high = entry.low + m.ylo, entry.high + m.yhi
        return entry._replace(low=low, high=max(high, low + 1))

    def pass_(self, offense: int, defense: int, entry: PassEntry) -> PassEntry:
        m = self.mod_for("pass")
        if m is None:
            return entry
        low, high = entry.low + m.ylo, entry.high + m.yhi
        return entry._replace(low=low, high=max(high, low + 1), sack=max(0, min(100, entry.sack + m.sack)),
                              complete=max(1, min(100, entry.complete + m.comp)))

    def qb_run(self, entry: QBRunEntry) -> QBRunEntry:
        m = self.mod_for("qb")
        if m is None:
            return entry
        low, high = entry.low + m.ylo, entry.high + m.yhi
        return entry._replace(low=low, high=max(high, low + 1), fumble=max(2, entry.fumble + m.fum))

    def fumble_odds(self, side: int) -> int:
        m = self.mod_for("fumble")
        return FUMBLE_ODDS if m is None else max(2, FUMBLE_ODDS + m.fum)


@dataclass
class Pending:
    """The plays called for the play now being made (the catalog IDs), cleared at every play's end."""
    offense: str = ""
    defense: str = ""

    def clear(self) -> None:
        self.offense = self.defense = ""
