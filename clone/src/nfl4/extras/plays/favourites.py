"""favourites.txt: the player's favourite plays of each side (nfl4 only, rule 0.13; design `spec/NFL_PLAYS_DESIGN.md` 2.5; built in
SX.10b, read by the game from SX.10c). This is inspired by Jim Kitchen.

A list file of data/customlists.py (the same header, notes, healing and damaged copies as every customize list, playbook 7.9),
in the folder `playbooks` of the customize folder:

    OF01 = O027      the first offense favourite (Mesh Crossers); OF01 to OF10
    DF01 = D017      the first defense favourite; DF01 to DF10

The game writes it when the player adds or takes off a favourite (the plus and minus keys in a list); the player may edit it
too. A line that is not understood, a play that does not exist or is of the other side, a place past ten and a play twice are
problems (one spoken summary, the details in the log) and are left out; the file is never refused for them.
"""
from __future__ import annotations

import os
import re

from ...data import customlists as cl
from ...data.customize import GAME, PLAYBOOKS_FOLDER
from ...data.healing import write_text_atomic
from . import catalog as C
from .play_menus import FAVOURITES_MAX

FILE_NAME, KIND = "favourites.txt", "favourite plays"
PLACE = re.compile(r"([OD])F(\d{2})$")
NOTES = (
    "These are your favourite plays. The game reads this file only when the Rules setting of the F9 menu is N. F. L. rules.",
    "The game writes it when you press plus on a play in a play list, and takes a play off when you press minus.",
    "OF01 to OF10 are offense plays and DF01 to DF10 defense calls: OF01 = O027 puts Mesh Crossers first. The play IDs are the "
    "ones in plays.txt.",
    "Delete a line to take a play off. A line the game does not understand is left out and said once.",
)


def text_of(offense: tuple = (), defense: tuple = ()) -> str:
    entries = [("OF%02d" % n, pid) for n, pid in enumerate(offense[:FAVOURITES_MAX], start=1)]
    entries += [("DF%02d" % n, pid) for n, pid in enumerate(defense[:FAVOURITES_MAX], start=1)]
    return cl.render_list(GAME, KIND, NOTES, entries)


def list_file(customize_folder: str) -> cl.ListFile:
    return cl.ListFile(os.path.join(customize_folder, PLAYBOOKS_FOLDER), FILE_NAME, GAME, KIND, text_of)


def parse(entries, problems: cl.Problems) -> tuple[tuple, tuple]:
    """(offense favourites, defense favourites) of the file's entries; what is wrong goes to `problems` and is left out. The Customize
    layer (data/customize.py, SX.10c) and `read` both use it."""
    places: dict[str, dict[int, str]] = {"O": {}, "D": {}}
    seen: set[str] = set()
    for entry in entries:
        match = PLACE.match(entry.id)
        if match is None:
            problems.add(entry.id, "the ID is not OF01 to OF10 or DF01 to DF10")
            continue
        side, number = match.group(1), int(match.group(2))
        play_id = entry.value.strip().upper()
        concept = C.BY_ID.get(play_id)
        if not 1 <= number <= FAVOURITES_MAX:
            problems.add(entry.id, "there are ten places on each side")
        elif concept is None or concept.side != side:
            problems.add(entry.id, "%s is not a play of the %s" % (entry.value, "offense" if side == "O" else "defense"))
        elif number in places[side]:
            problems.add(entry.id, "the place is written twice; the first line counts")
        elif play_id in seen:
            problems.add(entry.id, "%s is a favourite already" % play_id)
        else:
            places[side][number] = play_id
            seen.add(play_id)
    offense = tuple(places["O"][n] for n in sorted(places["O"]))
    defense = tuple(places["D"][n] for n in sorted(places["D"]))
    return offense, defense


def read(customize_folder: str) -> tuple[tuple, tuple, cl.ListLoad, cl.Problems]:
    """(offense favourites, defense favourites, how the file loaded, its problems); never raises."""
    load = list_file(customize_folder).load()
    problems = cl.Problems(FILE_NAME)
    offense = defense = ()
    if load.parsed is not None:
        for line, why in load.parsed.bad_lines:
            problems.add("line %d" % line, why)
        offense, defense = parse(load.parsed.entries, problems)
    return offense, defense, load, problems


def write(customize_folder: str, offense: tuple, defense: tuple) -> bool:
    """The whole file again, in one step (a crash never leaves half a file)."""
    return write_text_atomic(list_file(customize_folder).path, text_of(tuple(offense), tuple(defense)))
