"""The plays guide for GitHub (game/PLAYS_GUIDE.md), made from the description rows (nfl4 only, rule 0.13; NX-P8, D-091, CLAUDE.md 0.25).
This is inspired by Jim Kitchen.

The same plain sentences the D key says in a play menu, list by list, so a person who has never watched football can read what every play
does before choosing it. Written by `py -3.14 -I game/tools/make_docs.py`; a test requires that the file is exactly this text.
"""
from __future__ import annotations

from ...game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
from .. import nx_texts as X
from . import catalog as C
from . import descriptions as D

SIDE_TITLES = {"O": "Offense: when your team has the ball", "D": "Defense: when the other team has the ball",
               "K": "Special teams: kicks and punts"}


def guide_text() -> str:
    out = ["# Plays guide", "",
           "What every play, menu item, list and setting of the game does, in plain words for a person who has never watched football. "
           "In a play menu of the N. F. L. rules, press D to hear the description of the current item; in Classic, F7 reads the "
           "descriptions of the original's plays. These sentences are the game's own text, and the plays are football ideas named in plain "
           "football words. The README has the full notice about the plays and about trademarks.", "",
           "## The original's plays", "", "Offense menu:", ""]
    out += ["- **%s**: %s" % (OFFENSE_ITEMS[n - 1].strip()[3:], D.text(D.OFFENSE_ITEM_ROWS[n])) for n in range(1, 8)]
    out += ["", "Defense menu:", ""]
    out += ["- **%s**: %s" % (DEFENSE_ITEMS[n - 1].strip()[3:], D.text(D.DEFENSE_ITEM_ROWS[n])) for n in range(1, 7)]
    out += ["", "## Menu words", ""]
    names = {"back": "Back", "more": "More Plays", "favourites": "Favourites", "again": "Again", "find": "Find a Play by Name",
             "settings": "Formation and Tempo", "timeout": "Time Out", "challenge": "Challenge the Ruling", "save": "Save Game"}
    out += ["- **%s**: %s" % (names[key], D.text(row)) for key, row in D.WORD_ROWS.items()]
    out.append("- **More Plays (on defense)**: " + D.text(D.DEFENSE_MORE_ROW))
    out += ["", "## The groups of a playbook menu", "", "With a playbook of the N. F. L. rules, the offense menu starts with these groups; Enter opens one "
            "and Backspace or Left goes back.", ""]
    out += ["- **%s**: %s" % (X.text("NXB-%02d" % n).strip(), D.text(row)) for n, row in D.PLAYBOOK_GROUP_ROWS.items()]
    for side in ("O", "D", "K"):
        out += ["", "## " + SIDE_TITLES[side]]
        for group in C.GROUPS:
            if group.side != side:
                continue
            out += ["", "### " + group.name, "", D.text(D.LIST_ROWS[group.key]), ""]
            out += ["- **%s**: %s" % (c.name, D.text(D.play_row(c.id))) for c in C.CATALOG if c.group == group.key]
    out += ["", "## Settings", ""]
    settings = {"formation": "Formation", "personnel": "Personnel", "motion": "Motion", "side": "Side", "tempo": "Tempo",
                "protection": "Protection", "defense_personnel": "Defensive Personnel", "coverage_shade": "Coverage Shade"}
    out += ["- **%s**: %s" % (settings[name], D.text(row)) for name, row in D.SETTING_ROWS.items()]
    out.append("")
    return "\n".join(out)
