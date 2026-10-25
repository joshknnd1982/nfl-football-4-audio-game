"""The plain descriptions of every play, item, list and setting (nfl4 only, rule 0.13; NX-P8, D-091, CLAUDE.md 0.25). This is inspired by
Jim Kitchen.

Pure: no speech, no keys. The texts are rows of spec/strings_nx.tsv (nx_texts.py), one or two plain sentences of at most 35 words for a
person who has never watched football; the D key of a play menu says the one of the current item (extras.nfl_rules.NflRules.menu_key,
play_menus.PlayMenus.describe), F7 says the original's items in Classic (game/hotkeys.py), and game/PLAYS_GUIDE.md is made from them
(guide.py). The row ids follow the design's scheme (spec/NFL_PLAYS_DESIGN.md 3):

    offense play   O001 to O099 NXY-R01 to R99, O100 on NXY-S00 on     defense call   D001 on NXZ-R01 on
    special teams  K001 to K036 NXB-D01 to D36                        the original's items and the menu words NXB-E01 on
    the lists      NXB-F01 on (the order of catalog.GROUPS)           the settings   NXB-G01 to G08
"""
from __future__ import annotations

from ...game import menus
from .. import nx_texts as X
from . import catalog as C

QB_PLAYS = {8: "O046", 9: "O047", 10: "O048"}          # the offense items 8, 9 and 0 (playtables QB_SNEAK, QB_KEEPER, QB_DRAW)
OFFENSE_ITEM_ROWS = {n: "NXB-E%02d" % n for n in range(1, 8)}      # Line Plunge ... Punt
DEFENSE_ITEM_ROWS = {n: "NXB-E%02d" % (10 + n) for n in range(1, 7)}    # Goal Line ... Long Pass
WORD_ROWS = {"back": "NXB-E17", "more": "NXB-E18", "favourites": "NXB-E19", "again": "NXB-E20", "find": "NXB-E21", "settings": "NXB-E22",
             "timeout": "NXB-E23", "challenge": "NXB-E24", menus.SAVE: "NXB-E25"}
DEFENSE_MORE_ROW = "NXB-G09"
PLAYBOOK_GROUP_ROWS = {n: "NXB-E%02d" % (26 + n) for n in range(1, 8)}        # the groups of SX.7's playbook menu (NXB-01 to NXB-07)
SETTING_NAMES = ("formation", "personnel", "motion", "side", "tempo", "protection", "defense_personnel", "coverage_shade")
SETTING_ROWS = {name: "NXB-G%02d" % n for n, name in enumerate(SETTING_NAMES, start=1)}
LIST_ROWS = {group.key: "NXB-F%02d" % n for n, group in enumerate(C.GROUPS, start=1)}
# the F7 words the descriptions use (rows NXH-48 to NXH-51), the words of the offense's settings and clock plays (NXH-52 to NXH-55,
# SX.10c) and of the kicks of 2026 and the defense's personnel (NXH-59 to NXH-61, SX.10d), said after the football words in the N. F. L.
# rules mode
F7_WORD_ROWS = ("NXH-48", "NXH-49", "NXH-50", "NXH-51", "NXH-52", "NXH-53", "NXH-54", "NXH-55", "NXH-59", "NXH-60", "NXH-61")


def play_row(play_id: str) -> str:
    """The row of a catalog play's description."""
    number = int(play_id[1:])
    if play_id[0] == "K":
        return "NXB-D%02d" % number
    letter = "Y" if play_id[0] == "O" else "Z"
    return "NX%s-R%02d" % (letter, number) if number < 100 else "NX%s-S%02d" % (letter, number - 100)


def text(row: str) -> str:
    """A description as it is said (no spaces at the ends)."""
    return X.text(row).strip()


def action_row(on_offense: bool, action: tuple) -> str | None:
    """The row for an item of the live play menus (extras SX.7 playbooks, the tail items): the action is the item's own
    (menus.PLAY n, an obook or dbook play, a group, Back, the timeout, the challenge, Save Game). None when it has none."""
    kind, value = action
    if kind == menus.PLAY:
        if on_offense:
            if value in QB_PLAYS:
                return play_row(QB_PLAYS[value])
            return OFFENSE_ITEM_ROWS.get(value)
        return DEFENSE_ITEM_ROWS.get(value)
    if kind == "obook":
        return play_row("O%03d" % value)
    if kind == "dbook":
        return play_row("D%03d" % value)
    if kind == "ogroup":
        return PLAYBOOK_GROUP_ROWS.get(value)
    if kind == "dgroup":
        return DEFENSE_ITEM_ROWS.get(value)
    if kind in ("back", "timeout", "challenge", menus.SAVE):
        return WORD_ROWS[kind]
    return None


def menu_item_row(side: str, action: tuple, fourth_down_kick: bool = False) -> str | None:
    """The row for an item of extras.plays.play_menus (its action kinds: call, pick, kick, open, more, favourites, again, find, back,
    settings, setting)."""
    kind, value = action
    if kind == "call":
        return play_row(value)
    if kind == "pick":
        if side == "O":
            return play_row(QB_PLAYS[value]) if value in QB_PLAYS else OFFENSE_ITEM_ROWS.get(value)
        return DEFENSE_ITEM_ROWS.get(value)
    if kind == "kick":
        return OFFENSE_ITEM_ROWS.get(value)
    if kind == "open":
        return LIST_ROWS.get(value)
    if kind == "more" and side == "D":
        return DEFENSE_MORE_ROW                      # SZ.5: on defense More Plays holds every list of calls
    if kind in ("more", "favourites", "again", "find", "back", "settings"):
        return WORD_ROWS[kind]
    if kind == "setting":
        return SETTING_ROWS.get(value)
    return None


def all_rows() -> list[str]:
    """Every description row there is, in the order of the guide: the items, the lists with their plays, the settings."""
    rows = [OFFENSE_ITEM_ROWS[n] for n in sorted(OFFENSE_ITEM_ROWS)] + [DEFENSE_ITEM_ROWS[n] for n in sorted(DEFENSE_ITEM_ROWS)]
    rows += list(WORD_ROWS.values()) + [DEFENSE_MORE_ROW] + list(PLAYBOOK_GROUP_ROWS.values()) + list(LIST_ROWS.values())
    rows += [play_row(c.id) for c in C.CATALOG] + list(SETTING_ROWS.values()) + list(F7_WORD_ROWS)
    return rows


def classic_f7_lines() -> list[str]:
    """Classic's F7 addition: the original's own items, each with its description, after the original's football words (and nothing
    else; the keys of Classic stay the original's). The words of the descriptions are the original's F7 words only (a test)."""
    from ...game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
    offense = " ".join("%s: %s" % (OFFENSE_ITEMS[n - 1].strip()[3:], text(OFFENSE_ITEM_ROWS[n])) for n in range(1, 8))
    defense = " ".join("%s: %s" % (DEFENSE_ITEMS[n - 1].strip()[3:], text(DEFENSE_ITEM_ROWS[n])) for n in range(1, 7))
    save = "Save Game: " + text(WORD_ROWS[menus.SAVE])
    return [" The offense plays. " + offense + " " + save + " ", " The defense plays. " + defense + " " + save + " "]
