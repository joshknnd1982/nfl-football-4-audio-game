"""The play menus as data (GAME_SPEC 4.15; nfl4 hook H3). This is inspired by Jim Kitchen.

CODE (lifted) pag: the item texts are filled by the set-up GoSub (L1e0(1 to 8) and L3cc(1 to 7), 0x4540d2 to 0x454498);
the keys are read at 0x43df19 (offense) and 0x43eb04 (defense). An item has its spoken text, the digit that makes it the
current item and its action: ("play", n) starts play n, ("save", 0) saves the game. Up and Down move through the items
and wrap, a digit 1 to the number of items makes that item current, Enter takes it. Classic is exactly the original's
lists; during a two-point try the offense list is items 1 to 5 (the original's bounds at 0x43e2db and 0x43e498).

NFL_EXTRAS_DESIGN 3 H3: one function builds the lists, and the extras (a playbook, more items) pass other lists through
the Rules object; the menu code never changes for them. Letter keys are not used in Classic.
"""
from __future__ import annotations

from typing import NamedTuple

from .setup import DEFENSE_ITEMS, OFFENSE_ITEMS

PLAY, SAVE = "play", "save"


class MenuItem(NamedTuple):
    text: str               # what say5 speaks, e.g. " 1. Line Plunge "
    digit: int              # the digit key that makes it current
    action: tuple[str, int]  # (PLAY, play number) or (SAVE, 0)


def offense_menu(two_point_try: bool = False) -> list[MenuItem]:
    """Items 1 to 8 (7 plays and Save Game); during a two-point try items 1 to 5."""
    items = [MenuItem(text, n, (PLAY, n)) for n, text in enumerate(OFFENSE_ITEMS[:7], start=1)]
    items.append(MenuItem(OFFENSE_ITEMS[7], 8, (SAVE, 0)))
    return items[:5] if two_point_try else items


def defense_menu() -> list[MenuItem]:
    """Items 1 to 7 (6 defenses and Save Game)."""
    items = [MenuItem(text, n, (PLAY, n)) for n, text in enumerate(DEFENSE_ITEMS[:6], start=1)]
    items.append(MenuItem(DEFENSE_ITEMS[6], 7, (SAVE, 0)))
    return items
