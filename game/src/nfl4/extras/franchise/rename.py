"""Renaming a player of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8m (research 1.2's LATER item "renaming a player"; design 17: "renaming a player uses the original's typed prompt from the roster
item"; D-073). F9, franchise, your roster: Enter on one of the player's own players asks for the new name with the ORIGINAL'S typed prompt (`game\\prompts.py`
`getter`: F1 says the prompt again and empties the name, Backspace says and removes the last character, Enter ends,
every other key that types something is echoed and kept, at most `NAME_LIMIT` characters, a keypad key types its digit) and cleans it as the quarterback's
name is cleaned (`cqn`: fewer than two letters or digits give no name); then the original's yes or no question ("is <name> correct?", Up and Down change
the answer, y and n answer). Inside F9 the keys are read as F9 reads them (`KeyInput.read_key`, which runs no global key, design 3.7), so F9 is never opened
inside itself; the spoken words go with `say_async` outside the replay list, as every F9 menu speaks. F9's key reading skips Shift on its own and hands the
character the window typed, so a capital letter is typed with Shift as anywhere else (the original's own Shift step reads key codes, which have no case).

    check_name(league, player, name)   None when the name may be used, else the ID of the sentence that says why not
    rename(league, player, name)        the change (the caller writes league.sav)
    ask(g, speech, keys, store, player, words)   the prompt, the question, the change and the save; returns the sentence to say
"""
from __future__ import annotations

from ...data import debuglog
from ...game import prompt_texts as PT
from ...game import prompts as P
from ...game.keys import KEY_ENTER
from .. import nx_texts as X

KEY_F1, KEY_BACKSPACE, KEY_UP, KEY_DOWN, KEY_ESCAPE = 112, 8, 38, 40, 27


def check_name(league, player, name: str):
    """None when `name` may be the player's new name; else the ID of the sentence that says why not: no name typed (NXU-42), his own name (NXU-43), another
    active player's name (NXU-44: names stay unique among the league's active players, design 7.4), a player waiting for the cut (NXU-45: the draft knows him
    by the name of his prospect until the cut is applied)."""
    if player.place < 0:
        return "NXU-45"
    if not name:
        return "NXU-42"
    key = name.strip().casefold()
    if key == player.name.strip().casefold():
        return "NXU-43"
    taken = {p.name.strip().casefold() for p in league.players.values() if p.status in ("active", "reserve") and p.id != player.id}
    if league.draft is not None:                          # the class of a draft in progress keeps its names too (design 7.4: no duplicate while names are free)
        taken |= {row[1].strip().casefold() for row in league.draft["class"]}
    if key in taken:
        return "NXU-44"
    return None


def rename(league, player, name: str) -> None:
    player.name = name
    debuglog.add_typed(name)


def typed(g, speech, keys, prompt: str) -> str:
    """The original's `getter` with F9's key reading: the typed text. The debug log writes no key and no echoed letter while it
    is typed, and hides the result (playbook 7.11, privacy)."""
    with debuglog.context("typing: rename a player"):
        text = _typed(g, speech, keys, prompt)
    debuglog.add_typed(text)
    debuglog.event("input", "text_entered", chars=len(text), prompt="rename a player")
    return text


def _typed(g, speech, keys, prompt: str) -> str:
    while True:
        speech.stop()
        speech.say_async(prompt)
        text = ""
        while True:
            code = keys.read_key()
            if code == KEY_F1:
                break                                        # the prompt again, the text empty
            if code == KEY_ESCAPE:
                return ""                                    # F9's way back: nothing typed (the original's prompts have no Escape)
            char = None
            if code not in (KEY_BACKSPACE, KEY_ENTER):
                char = g.prompts.typed_character(str(code))
            if code == KEY_BACKSPACE:
                if text:
                    speech.stop()
                    speech.say_async(text[-1])
                    text = text[:-1]
                continue
            if code == KEY_ENTER:
                return text
            if char is None:
                continue
            speech.stop()
            speech.say_async(char)
            if len(text) < P.NAME_LIMIT:
                text += char


def confirmed(speech, keys, question: str) -> bool:
    """The original's yes or no question: yes first; Up and Down change the answer and say it, Enter takes it, y and n answer, F1 or another key asks again."""
    while True:
        answer = True
        speech.stop()
        speech.say_async(question)
        speech.say_async(PT.YES if answer else PT.NO)
        while True:
            code = keys.read_key()
            if code == KEY_ENTER:
                return answer
            if code in (KEY_UP, KEY_DOWN):
                answer = not answer
                speech.stop()
                speech.say_async(PT.YES if answer else PT.NO)
                continue
            if code == KEY_ESCAPE:
                return False
            if keys.char == "y":
                return True
            if keys.char == "n":
                return False
            break


def ask(g, speech, keys, store, player) -> str:
    """F9's renaming of one of the player's own players: returns the sentence to say after it (the new name, or why nothing changed)."""
    league = store.league
    if player.place < 0:
        return X.text("NXU-45", player=player.name)
    name = P.cqn(typed(g, speech, keys, X.text("NXU-40", player=player.name)))
    why = check_name(league, player, name)
    if why is not None:
        return X.text(why, player=player.name)
    if not confirmed(speech, keys, X.text("NXU-41", name=name)):
        return X.text("NXU-42", player=player.name)
    old = player.name
    rename(league, player, name.strip())
    store.save()
    return X.text("NXU-46", player=old, name=name)
