"""The announcer's banter: which line, which name, and how it is spoken (GAME_SPEC 5.13). This is inspired by Jim Kitchen.

CODE (lifted) pag's GoSub 0x45915e, read in full (S3.5; the 142 lines are data, game/banter_lines.py). One call:
1. comments off (comtog = 1, F8): nothing at all;
2. when all the lines of the pool were used in this game nothing (cannot happen in a game with the original's 142); else the
   count L7dc grows by one;
3. n = Int(Rnd * 142) + 1 drawn again while it is one of the lines used in this game (bounded, G-D1); it is recorded;
4. L778 = Int(Rnd * 58) + 1 picks the name of the 58-name list; rady;
5. the texts of line n (lines 101 and 110 draw their second text: Int(Rnd * 5) + 1, Int(Rnd * 3) + 1);
6. clk, the first text with say (line 113 one rate step faster), foot13 after the first text of lines 69, 72, 75 (twice),
   83 and 140, clk, the second text with say when there is one, clk.
The history of used lines lives for one game and is not saved (Q37).

S7.7 (D-035, D-048): the pool is `game.banter_pool`, the 142 original lines plus the player's (banter.txt, game/banter_pool.py:
a line replaced, switched off or added), each a sequence of pieces (game/banter_markup.py). The draw rule is this one for the
whole pool: the pool's size takes the place of 142 and the lines are told apart by their numbers (B001 to B142 are the
original's own numbers, so with the original lines the draws are the same sizes and the same lines as before). The draws of the
[one of:] choices of a line come where the original draws the second text of lines 101 and 110, in line order. F8's
comments-off silences every line, the player's too. The groups of a line (a spoken part and the sounds and pauses that follow
it) keep the original's three clk (before the line, after each group, and after the second group even when there is none).
"""
from __future__ import annotations

import logging
import os

from .banter_lines import NAME, OPPONENT_QB, BanterLine
from .banter_markup import Bleep, Pause, Sound, Speak, choice_sizes, speak_text
from .gamestate import GameState

log = logging.getLogger("nfl4.game")

NAME_LIST_SIZE = 58
BLEEP_SOUND = 13


def line_texts(line: BanterLine, name: str, opponent_qb: str, alternative: int | None) -> tuple[str, str]:
    """The first and second text of an original line with its name inserted (the same name in both texts)."""
    first = line.first.replace(NAME, name).replace(OPPONENT_QB, opponent_qb)
    second = line.second if not line.alternatives else line.alternatives[alternative - 1]
    second = second.replace(NAME, name).replace(OPPONENT_QB, opponent_qb)
    return first, second


def groups_of(pieces: tuple) -> list[list]:
    """A group is a spoken part and the sounds and pauses after it; sounds before the first part belong to the first group."""
    groups: list[list] = [[]]
    for piece in pieces:
        if isinstance(piece, Speak) and any(isinstance(p, Speak) for p in groups[-1]):
            groups.append([])
        groups[-1].append(piece)
    return groups


def speak_banter(game, state: GameState) -> None:
    """The GoSub at 0x45915e."""
    if game.comtog == 1:
        return
    lines = game.banter_pool.lines
    used = list(state.banter_used)
    if not lines or all(line.number in used for line in lines):
        return
    rnd = game.rnd
    index = rnd.redraw(lambda: rnd(len(lines)), lambda n: lines[n - 1].number not in used,
                       lambda: next(n for n in range(1, len(lines) + 1) if lines[n - 1].number not in used), "banter line")
    line = lines[index - 1]
    state.banter_used.append(line.number)
    name_index = rnd(NAME_LIST_SIZE)
    game.rady(0x459497)
    choices = [rnd(size) for size in choice_sizes(line.pieces)]
    names = state.banter_names
    name = names[name_index - 1] if name_index <= len(names) else ""
    play_line(game, line.pieces, name, state.quarterbacks.get(2, ""), choices)


def play_line(game, pieces: tuple, name: str, opponent_qb: str, choices: list[int]) -> None:
    """Step 6: clk, then each group (its part said and waited, its sounds played and waited), clk after each."""
    keys = game.keys
    keys.clk()
    groups = groups_of(pieces)
    remaining = iter(choices)
    for group in groups:
        for piece in group:
            if isinstance(piece, Speak):
                text = speak_text(piece, name, opponent_qb, remaining)
                if text.strip() != "":
                    game.say(text, rate_step=1 if piece.faster else 0)
            elif isinstance(piece, Bleep):
                game.sounds.play(BLEEP_SOUND, 0)
            elif isinstance(piece, Sound):
                play_player_sound(game, piece.file)
            elif isinstance(piece, Pause):
                if piece.seconds is None:
                    game.rady()
                else:
                    game.dy(piece.seconds)
        keys.clk()
    if len(groups) == 1:
        keys.clk()


def play_player_sound(game, file_name: str) -> None:
    """[sound file]: the player's file from customize\\sounds, played like the bleep. A file that cannot be used is skipped
    (the library logs it and gives its one spoken notice) and the rest of the line is said."""
    folder = getattr(game, "banter_sounds_dir", None)
    if not folder:
        log.warning("banter sound %s skipped: there is no folder for the player's sounds", file_name)
        return
    game.sounds.play_file(os.path.join(folder, file_name))
