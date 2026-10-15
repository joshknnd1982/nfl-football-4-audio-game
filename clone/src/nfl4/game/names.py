"""The surname pool the rosters and the default quarterback names are drawn from. This is inspired by Jim Kitchen.

GAME_SPEC 11, 5.5 and 4.12 (CODE (lifted) SetPlayerNames, pag's set-up GoSub, Getqbs): 1,708 surnames in one array
(spec\\SURNAMES.tsv, kept as clone\\assets\\data\\surnames.txt, D-026). A draw is `Int(Rnd * 1708) + 1` and is drawn again
while that slot is blank; a used name is BLANKED so the next draws cannot meet it (drawing without replacement). Two
different ways to blank by name exist in the original and both are kept:

* names read from footplay.txt (pag's set-up): the FIRST slot that equals the name exactly (case sensitive) is blanked,
  a name that is not in the pool (a typed one) blanks nothing (`blank_exact`);
* a typed or accepted quarterback name (Getqbs): EVERY slot that equals it ignoring case is blanked (`blank_matching`).

S7.7 loads the player's surnames.txt (renaming only: the count stays 1,708, CUSTOMIZABLE_CONTENT 5) into the same class.
G-D1: the redraw is bounded; with every slot blank (cannot happen with the original data, which needs 70 names of
1,708) the pool is refilled from its original list and a warning is logged.
"""
from __future__ import annotations

import logging
import os

from ..data import paths
from .rnd import GameRandom

log = logging.getLogger("nfl4.game")

POOL_SIZE = 1708


def shipped_surnames_path() -> str:
    return os.path.join(paths.program_dir(), "assets", "data", "surnames.txt")


def load_surnames(path: str | None = None) -> list[str]:
    """The original surnames in the original's order (UTF-8, one per line)."""
    with open(path or shipped_surnames_path(), "r", encoding="utf-8") as fh:
        names = fh.read().split("\n")
    if names and names[-1] == "":
        names.pop()
    return names


class NamePool:
    def __init__(self, rnd: GameRandom, names: list[str] | None = None):
        self.rnd = rnd
        self.original = list(names) if names is not None else load_surnames()
        if len(self.original) != POOL_SIZE:
            raise ValueError("the surname pool has %d names, not %d" % (len(self.original), POOL_SIZE))
        self.slots = list(self.original)       # "" = used (blanked)

    @property
    def size(self) -> int:
        return len(self.slots)

    def name(self, slot: int) -> str:
        """Me.m278(slot), slots 1 to 1,708."""
        return self.slots[slot - 1]

    def replace_names(self, names: list[str]) -> None:
        """The player reloaded surnames.txt (S7.7): the names change, the used (blank) slots stay blank, so a name already
        drawn is not drawn again and a game in progress keeps its roster (its names are copies)."""
        if len(names) != POOL_SIZE:
            raise ValueError("the surname pool has %d names, not %d" % (len(names), POOL_SIZE))
        self.original = list(names)
        self.slots = [new if old != "" else "" for old, new in zip(self.slots, names)]

    def available(self) -> int:
        return sum(1 for name in self.slots if name != "")

    def draw_slot(self) -> int:
        """`Lbc = Int(Rnd * 1708) + 1` drawn again while the slot is blank. The slot is not blanked here."""

        def refill() -> int:
            log.warning("every surname of the pool is used: the pool is filled again (G-D1)")
            self.slots = list(self.original)
            return 1

        def first_free() -> int:
            for number, name in enumerate(self.slots, start=1):
                if name != "":
                    return number
            return refill()

        return self.rnd.redraw(lambda: self.rnd(self.size), lambda slot: self.slots[slot - 1] != "", first_free,
                               "surname draw")

    def blank(self, slot: int) -> None:
        self.slots[slot - 1] = ""

    def take(self) -> str:
        """The set-up's draw: a free slot, its name, the slot blanked."""
        slot = self.draw_slot()
        name = self.slots[slot - 1]
        self.slots[slot - 1] = ""
        return name

    def blank_exact(self, name: str) -> bool:
        """footplay.txt names: the first slot equal to `name` (case sensitive) is blanked. True when one was."""
        for index, slot_name in enumerate(self.slots):
            if slot_name == name:
                self.slots[index] = ""
                return True
        return False

    def blank_matching(self, name: str) -> int:
        """Getqbs: every slot equal to `name` ignoring case is blanked (LCase$ on both sides). Returns how many."""
        wanted = name.lower()
        count = 0
        for index, slot_name in enumerate(self.slots):
            if slot_name.lower() == wanted:
                self.slots[index] = ""
                count += 1
        return count
