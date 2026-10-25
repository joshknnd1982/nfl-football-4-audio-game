"""The defense's personnel against the offense's (nfl4 only, rule 0.13; NX-P4, design section 0 Q-P13; built in SX.10d, D-094). This is
inspired by Jim Kitchen.

Pure: no speech, no state, no draw. A defense call of the catalog carries its own package (its defensive backs and its box). Q-P13: by
default the defense's personnel follows the offense's (nickel, five defensive backs, against three receivers; base, four, against two backs
or two tight ends; dime, six, against four or five receivers; heavy, three, at the goal line), the player may override it in Formation and
Tempo (Defensive Personnel), and the computer matches the same way. `adjust` gives the call the model plays: its defensive backs those of the
package, its box one man lighter for each back more than the call's own and one heavier for each back fewer, never more than one man
either way and always 5 to 8 (the box is what the run and pass models read, design 4.7), and the Coverage Shade setting's press or off in
place of the call's own (UNVERIFIED shapes: a mismatch is about one man in the box; SX.10e measures the balance).
"""
from __future__ import annotations

from . import catalog as C

MATCH, BOOK = "match", "book"
GOAL_LINE_YARDS = 3                 # within this many yards of the goal a heavy offense (one receiver or none) meets the heavy package
PACKAGE_BACKS = {                   # the defensive backs of each value of the Defensive Personnel setting (catalog.SETTINGS)
    "base 4-3": 4, "base 3-4": 4, "nickel 4-2-5": 5, "nickel 3-3-5": 5, "nickel 2-4-5": 5, "big nickel": 5,
    "dime 4-1-6": 6, "dime 3-2-6": 6, "quarter": 7, "2-5": 6, "heavy": 3,
}
SHADES = ("press", "off")


def receivers(personnel: str) -> int:
    """The wide receivers of an offense's personnel ("11" is one back, one tight end: three receivers)."""
    if len(personnel) != 2 or not personnel.isdigit():
        return 3
    return max(0, 5 - int(personnel[0]) - int(personnel[1]))


def matched_backs(personnel: str, to_goal: int) -> int:
    """Q-P13: the defensive backs that match the offense's personnel."""
    wide = receivers(personnel)
    if to_goal <= GOAL_LINE_YARDS and wide <= 1:
        return 3
    if wide <= 2:
        return 4
    if wide == 3:
        return 5
    return 6


def adjust(call: C.Call, personnel: str, to_goal: int, setting: str = MATCH, shade: str = BOOK) -> C.Call:
    """The call as it is played: the package's defensive backs, the box moved by at most one man, the shade's press or off."""
    backs = matched_backs(personnel, to_goal) if setting in (MATCH, "", None) else PACKAGE_BACKS.get(setting, call.backs)
    box = call.box + max(-1, min(1, call.backs - backs))
    box = max(5, min(8, box))
    tags = call.tags
    if shade in SHADES:
        tags = tuple(t for t in tags if t not in SHADES) + (shade,)
    return call._replace(backs=backs, box=box, tags=tags)


def offense_personnel(concept: C.Concept, settings: dict) -> str:
    """The offense's personnel for a play: the Personnel setting of Formation and Tempo when the player set one, else the play's own."""
    value = settings.get("personnel", BOOK) if settings else BOOK
    return concept.personnel if value == BOOK else value
