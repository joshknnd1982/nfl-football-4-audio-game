"""F9, Rules, Commentator: choose the color commentator's name (nfl4 only, rule 0.13; SZ.1, D-106). This is inspired by Jim Kitchen.

A list of the default (Ghip), well-known sports podcasters (extras/commentators.py) and the last item, which lets the player type a name
of their own with the original's typed prompt (F1 says the prompt again, Backspace removes the last character, Enter ends). Up and Down
move, typing letters jumps to a name, Enter chooses, Escape goes back with no change. The name is the setting `nx_commentator`; it is
used from the next game, like every other rule (a game in progress keeps what it began with).

    label(settings)        "Commentator: Ghip" (+ " used with the N. F. L. rules" while Rules is Classic): the Rules menu's item
    pick(game, speech, keys, settings)   True when the name changed (the caller saves and applies it)
    step(settings, direction)            Left and Right on the item: the next or the previous name of the list, True when it changed
"""
from __future__ import annotations

from ..data import debuglog
from ..game import prompts as P
from ..game.spoken_menu import ListPicker
from . import commentators
from . import nx_texts as X

NFL = "nfl"


def label(settings) -> str:
    text = X.text("NXM-39") + ": " + commentators.name_of(settings)
    if getattr(settings, "rules", NFL) != NFL:
        text += X.text("NXM-22")
    return text


def item_name(kind: str, name: str) -> str:
    if kind == "default":
        return X.text("NXM-45", name=name)
    if kind == "own":
        return X.text("NXM-46", name=name)
    if kind == "type":
        return X.text("NXM-42")
    return name


def search(items):
    """The best match for typed letters: a name that starts with them, else a word of a name that starts with them, else a name that has them."""
    def find(text: str) -> int | None:
        wanted = " ".join(text.lower().split())
        if not wanted:
            return None
        names = [(kind, name.lower()) for kind, name in items if kind != "type"]
        for test in (lambda n: n.startswith(wanted), lambda n: any(w.startswith(wanted) for w in n.split()), lambda n: wanted in n):
            for index, (kind, name) in enumerate(names):
                if test(name):
                    return index
        return None
    return find


def pick(game, speech, keys, settings) -> bool:
    items = commentators.choices(commentators.name_of(settings))
    current = commentators.name_of(settings)
    start = next((i for i, (kind, name) in enumerate(items) if kind != "type" and name == current), 0)
    chosen = ListPicker(speech, keys, X.text("NXM-40"), len(items), lambda i: item_name(*items[i]), search=search(items), start=start,
                        help_text=X.text("NXM-41")).run()
    if chosen is None:
        return False
    kind, name = items[chosen]
    if kind == "type":
        from .franchise import rename
        typed = rename.typed(game, speech, keys, X.text("NXM-43"))
        name = commentators.clean(P.cqn(typed))
        if not name:
            speech.say_async(X.text("NXM-44"))
            return False
    if name == current:
        return False
    settings.nx_commentator = name
    debuglog.event("setting", "change", name="nx_commentator", value=name)
    return True


def step(settings, direction: int) -> bool:
    """Left and Right on the item: the next or the previous name of the list, going around (the item that types a name is not a step)."""
    names = [name for kind, name in commentators.choices(commentators.name_of(settings)) if kind != "type"]
    current = commentators.name_of(settings)
    index = names.index(current) if current in names else 0
    settings.nx_commentator = names[(index + (1 if direction >= 0 else -1)) % len(names)]
    return True
