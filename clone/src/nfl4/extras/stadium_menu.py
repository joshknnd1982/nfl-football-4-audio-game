"""F9, Sounds, Stadium and referee sounds: the sounds of the N. F. L. rules that a player can replace (nfl4 only, rule 0.13; SZ.2, D-107).
This is inspired by Jim Kitchen.

The owner (2026-10-22), after hearing the stadium sounds, the referee's microphone and the whistles: "those are good, ensure the user can customize
them by adding custom wav files." The mechanism was there since SY.2 and SY.3 (a file with the same name in the player's sounds folder replaces the
shipped one, a new number adds one, rule 0.14), but a blind player could not find it out from the game. This list says it, sound by sound:

    the plain-word name of the sound, the file name it takes, and whether it is the original, the player's own or several
    Enter plays it at the level it has in the game, and again plays the next one of its family (Sound 2 of 3, your file)
    F1 says how to use your own file; the folder itself is the Sounds menu's "Open the sounds folder"

Nothing here changes the game's draws or any setting; the list only reads the two folders and plays on the extra channel.
"""
from __future__ import annotations

from ..audio.output import EXTRA_SLOT
from ..game import extra_texts as words
from ..game.spoken_menu import ListPicker
from . import nx_texts as X
from . import stadium as ST


def count_text(files: list[str], own: list[str]) -> str:
    if len(files) == 1:
        return X.text("NXM-50") if own else X.text("NXM-49")
    return X.text("NXM-51", n=len(files), m=len(own))


def item_name(name: str, folders: tuple[str, ...] | None = None) -> str:
    folders = folders or (ST.player_folder(), ST.shipped_folder())
    files = ST.family(name, folders)
    own = ST.mine(files, folders[0])
    return X.text("NXM-48", label=X.text(ST.LABEL_IDS[name]), file=name, count=count_text(files, own))


def sounds_list(speech, keys, audio, wavol: int, clock) -> None:
    names = ST.ALL_NAMES
    turn = {name: 0 for name in names}
    library = audio.library
    folders = (library.player_dir, ST.shipped_folder())          # the player's sounds folder is the library's (the Sounds menu's "Open the sounds folder")

    def usable(files: list[str]) -> list[str]:
        return [path for path in files if library.pick_file(path).sound is not None]

    def label(index: int) -> str:
        return item_name(names[index], folders)

    def play(index: int) -> str | None:
        name = names[index]
        files = ST.family(name, folders)
        own = ST.mine(files, folders[0])
        files = usable(files) or ST.family(name, (folders[1],))
        if not files:
            return words.NOTHING_CHANGED
        audio.stop_preview()
        position = turn[name] % len(files)
        turn[name] += 1
        path = files[position]
        audio.play_file(EXTRA_SLOT, path, int(ST.LEVELS.get(name, ST.WHISTLE_LEVEL)) + wavol)
        return words.pool_played(position + 1, len(files), "player" if path in own else "original")

    try:
        ListPicker(speech, keys, X.text("NXM-47"), len(names), label, on_enter=play, close_on_enter=False,
                   help_text=X.text("NXM-52") + X.text("NXM-53"), clock=clock).run()
    finally:
        audio.stop_preview()
