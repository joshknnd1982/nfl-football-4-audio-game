"""The announcer's banter: which line, which name, and how it is spoken (GAME_SPEC 5.13). This is inspired by Jim Kitchen.

CODE (lifted) pag's GoSub 0x45915e, read in full (S3.5; the 142 lines are data, game/banter_lines.py). One call:
1. comments off (comtog = 1, F8): nothing at all;
2. when all 142 lines were used in this game nothing (cannot happen in a game); else the count L7dc grows by one;
3. n = Int(Rnd * 142) + 1 drawn again while it is one of the lines used in this game (bounded, G-D1); it is recorded;
4. L778 = Int(Rnd * 58) + 1 picks the name of the 58-name list; rady;
5. the texts of line n (lines 101 and 110 draw their second text: Int(Rnd * 5) + 1, Int(Rnd * 3) + 1);
6. clk, the first text with say (line 113 one rate step faster), foot13 after the first text of lines 69, 72, 75 (twice),
   83 and 140, clk, the second text with say when there is one, clk.
The history of used lines lives for one game and is not saved (Q37). S7.7 lets the player change, switch off and add
lines (banter.txt, D-035); the draw rule stays this one for the whole pool.
"""
from __future__ import annotations

from .banter_lines import LINES, NAME, OPPONENT_QB, BanterLine
from .gamestate import GameState

NAME_LIST_SIZE = 58
BLEEP_SOUND = 13


def line_texts(line: BanterLine, name: str, opponent_qb: str, alternative: int | None) -> tuple[str, str]:
    """The first and second text of a line with its name inserted (the same name in both texts)."""
    first = line.first.replace(NAME, name).replace(OPPONENT_QB, opponent_qb)
    second = line.second if not line.alternatives else line.alternatives[alternative - 1]
    second = second.replace(NAME, name).replace(OPPONENT_QB, opponent_qb)
    return first, second


def speak_banter(game, state: GameState) -> None:
    """The GoSub at 0x45915e."""
    if game.comtog == 1:
        return
    lines = LINES
    if len(state.banter_used) == len(lines):
        return
    rnd = game.rnd
    used = list(state.banter_used)
    number = rnd.redraw(lambda: rnd(len(lines)), lambda n: n not in used,
                        lambda: next(n for n in range(1, len(lines) + 1) if n not in used), "banter line")
    state.banter_used.append(number)
    name_index = rnd(NAME_LIST_SIZE)
    game.rady()
    line = lines[number - 1]
    alternative = rnd(len(line.alternatives)) if line.alternatives else None
    names = state.banter_names
    name = names[name_index - 1] if name_index <= len(names) else ""
    first, second = line_texts(line, name, state.quarterbacks.get(2, ""), alternative)
    game.keys.clk()
    game.say(first, rate_step=line.rate_step)
    for _ in range(line.bleeps):
        game.sounds.play(BLEEP_SOUND, 0)
    game.keys.clk()
    if second != "":
        game.say(second)
    game.keys.clk()
