"""The color commentator's name (nfl4 only, rule 0.13; SZ.1, D-106). This is inspired by Jim Kitchen.

The owner (2026-10-22): "The user should be able to change Ghip's name or pick from among popular sports podcaster names that Claude
researches and puts into the game." The commentator of the radio broadcast (extras/broadcast.py) is Ghip, the name the original's jokes
already use for the person the announcer talks to; F9, Rules, Commentator lists NAMES (well-known sports podcasters, researched in
spec/COMMENTATOR_NAMES.md with their sources) and lets the player type a name of their own. Nobody has to type anything (rule 0.19).

The name is the setting `nx_commentator`. Every default line that said Ghip says `<commentator>` instead (strings_nx.tsv) and the name is
put in when the line is said (extras/remarks.py), so a name chosen in the menu is heard everywhere, in the announcer's questions and
banter too. The names are used descriptively only: the voice and the lines are the game's, not theirs, and they have nothing to do with
this game (the About text says so). The lines never state a fact about the person: they are gentle asides that fit any name.

    DEFAULT       "Ghip"
    NAMES         the researched names, in alphabetical order (typing letters in the list jumps to one)
    clean(name)   a typed or stored name made safe to speak and store, "" when it cannot be used
    choices(current)   the items of the list: the default, the names, the player's own name when it is none of them
"""
from __future__ import annotations

import re
import unicodedata

DEFAULT = "Ghip"
NAME_MAX = 30
# Researched 2026-10-22 from the Edison Research podcast rankings of 2025 and Q1 2026, Spotify's 2025 list of sports podcasts, CastFox's
# 2026 football list and the show listings of the NFL podcasts (spec/COMMENTATOR_NAMES.md has the sources, one by one).
NAMES = (
    "Alan Shearer", "Bill Simmons", "Bucky Brooks", "Chris Long", "Chris Simms", "Chris Wesseling", "Colin Cowherd", "Dan Hanzus",
    "Dan Le Batard", "Dan Patrick", "Daniel Jeremiah", "Danny Kelly", "Gary Lineker", "Gregg Rosenthal", "Jason Kelce", "Kevin Clark",
    "Marc Sessler", "Micah Richards", "Michael Lombardi", "Pablo Torre", "Pat McAfee", "Ray Garvin", "Rich Eisen", "Robert Mays",
    "Ross Tucker", "Ryen Russillo", "Shannon Sharpe", "Travis Kelce",
)
_UNSAFE = re.compile(r"[^A-Za-z0-9 '.\-]")


def clean(name) -> str:
    """The name as it is stored and spoken: letters, digits, spaces, apostrophes, full stops and hyphens, one space between words, at most
    NAME_MAX characters. "" when nothing usable is left (fewer than two characters)."""
    if not isinstance(name, str):
        return ""
    # S8.3 round 2: an accented letter is folded to its plain letter ("José" is "Jose"), not dropped ("Jos"); the voices that cannot say an
    # accent (SX.11's respellings) then still say the name
    folded = "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
    text = " ".join(_UNSAFE.sub("", folded).split())[:NAME_MAX].strip()
    return text if len(text) >= 2 else ""


def choices(current: str) -> list[tuple[str, str]]:
    """The items of the list in F9, Rules, Commentator as (kind, name): the default first, the researched names, the player's own name
    when it is none of them, and last the item that lets the player type one. kind is "default", "name", "own" or "type"."""
    items = [("default", DEFAULT)] + [("name", name) for name in NAMES]
    current = clean(current)
    if current and current != DEFAULT and current not in NAMES:
        items.append(("own", current))
    items.append(("type", ""))
    return items


def name_of(game_settings) -> str:
    """The commentator's name for a game: the setting, or Ghip when it is missing or unusable."""
    return clean(getattr(game_settings, "nx_commentator", DEFAULT)) or DEFAULT
