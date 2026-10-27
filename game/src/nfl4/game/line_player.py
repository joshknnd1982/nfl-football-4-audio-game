"""How a customizable line is spoken: its parts said, its sounds played, its pauses waited. This is inspired by Jim Kitchen.

BC.2 (D-178, D-180): the original's banter step (its 142 jokes and its draws) is gone from every mode; what it taught the game about
saying a line stays here, because the remark pools of remarks.txt (extras/remarks.py), the Franchise's weekly lines and its news use
it. A line is a sequence of pieces (game/banter_markup.py). One call:

1. clk, then each group (a spoken part and the sounds and pauses after it), clk after each group, and one more clk when the line
   has a single group (the original's three clk around a line);
2. a spoken part is said with `say` (the announcer's say by default, which waits; a pool may give another speaker);
3. [bleep] plays foot13, the original's bleep (it stays: the original also plays it when the player concedes);
4. [sound file] plays the player's own file from customize\\sounds, at most MAX_LINE_SOUND_SECONDS for the whole line;
5. [pause] waits a random rady, [pause 2] two seconds.

    PLAYER_NAMES   58: the size of the draw of a player's name for [name] (the 58 names of state.player_names)
"""
from __future__ import annotations

import logging
import os

from .banter_markup import Bleep, Pause, Sound, Speak, speak_text

log = logging.getLogger("nfl4.game")

PLAYER_NAMES = 58                 # the running backs, receivers and defenders of both teams (setup.player_names)
BLEEP_SOUND = 13
MAX_LINE_SOUND_SECONDS = 30       # the player's sounds of one line together (like the 30 seconds of pauses)


def groups_of(pieces: tuple) -> list[list]:
    """A group is a spoken part and the sounds and pauses after it; sounds before the first part belong to the first group."""
    groups: list[list] = [[]]
    for piece in pieces:
        if isinstance(piece, Speak) and any(isinstance(p, Speak) for p in groups[-1]):
            groups.append([])
        groups[-1].append(piece)
    return groups


def play_line(game, pieces: tuple, name: str, opponent_qb: str, choices: list[int], say=None) -> None:
    """clk, then each group (its part said and waited, its sounds played and waited), clk after each. `say` is the speaker of the
    parts (the announcer's `say`, which waits and is not replayed, unless a pool gives another: pool QB says its lines with say4, as a
    play-by-play sentence, SX.5)."""
    keys = game.keys
    keys.clk()
    groups = groups_of(pieces)
    remaining = iter(choices)
    sound_left = [MAX_LINE_SOUND_SECONDS]                 # what is left of the 30 seconds of the player's sounds in this line
    for group in groups:
        for piece in group:
            if isinstance(piece, Speak):
                text = speak_text(piece, name, opponent_qb, remaining)
                if text.strip() != "":
                    if say is None:
                        game.say(text, rate_step=1 if piece.faster else 0)
                    else:
                        say(text)
            elif isinstance(piece, Bleep):
                game.sounds.play(BLEEP_SOUND, 0)
            elif isinstance(piece, Sound):
                play_player_sound(game, piece.file, sound_left)
            elif isinstance(piece, Pause):
                if piece.seconds is None:
                    game.rady()
                else:
                    game.dy(piece.seconds)
        keys.clk()
    if len(groups) == 1:
        keys.clk()


def play_player_sound(game, file_name: str, sound_left: list[float]) -> None:
    """[sound file]: the player's file from customize\\sounds, played like the bleep. A file that cannot be used is skipped (the
    library logs it and gives its one spoken notice) and the rest of the line is said. `sound_left` is the seconds of player's sound the
    line may still use (one item list, shared by the line): a longer sound is cut there."""
    folder = getattr(game, "custom_sounds_dir", None)
    if not folder:
        log.warning("line sound %s skipped: there is no folder for the player's sounds", file_name)
        return
    if sound_left[0] <= 0:
        log.warning("line sound %s skipped: the line already used its %d seconds of sound", file_name, MAX_LINE_SOUND_SECONDS)
        return
    started = game.sounds.clock()
    game.sounds.play_file(os.path.join(folder, file_name), limit=sound_left[0])
    sound_left[0] -= game.sounds.clock() - started
