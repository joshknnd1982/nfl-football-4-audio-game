"""F9, Rules, Broadcast crew: the radio crew's names (nfl4 only, rule 0.13; SZ.1, D-106; BC.3, D-178, D-189). This is inspired by Jim Kitchen.

The Rules menu's item says the three names ("Broadcast crew: Walt Kessler, Gus Delgado, Nora Banks"); Enter opens a menu of four items, one
per role (the play-by-play announcer, the color analyst, the sideline reporter, the network), each said with its name. Up and Down move,
Escape goes back. On an item, Enter opens the list of names: the made-up default, the name the player last typed (kept when he goes back to
the default: BC.2 lost it), and the item that types a new one with the original's typed prompt (F1 says the prompt again, Backspace removes
the last character, Enter ends); Left and Right go between the default and the typed name without the list. Nobody has to type (rule 0.19).
The names are settings (extras/crew.py); they apply from the next game, like every other rule. Both modes: no " used with the N. F. L. rules ".

    label(settings)              the Rules menu's item
    crew_menu(game, speech, keys, settings, apply)   the four names; apply() saves a change (True when one was made)
    pick(game, speech, keys, settings, role)         one role's list: True when the name changed
"""
from __future__ import annotations

from ..data import debuglog
from ..game import prompts as P
from ..game.spoken_menu import Item, ListPicker, SpokenMenu
from . import crew
from . import nx_texts as X

ROLE_TEXT = {crew.ANNOUNCER: "NXM-59", crew.ANALYST: "NXM-60", crew.SIDELINE: "NXM-61", crew.NETWORK: "NXM-62"}


def label(settings) -> str:
    names = crew.names(settings)
    return X.text("NXM-39") + ": " + ", ".join(names[role] for role in (crew.ANNOUNCER, crew.ANALYST, crew.SIDELINE))


def role_label(settings, role: str) -> str:
    return X.text(ROLE_TEXT[role]) + ": " + crew.name_of(settings, role)


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


def pick(game, speech, keys, settings, role: str = crew.ANALYST) -> bool:
    items = crew.choices(settings, role)
    current = crew.name_of(settings, role)
    start = next((i for i, (kind, name) in enumerate(items) if kind != "type" and name == current), 0)
    chosen = ListPicker(speech, keys, X.text("NXM-40"), len(items), lambda i: item_name(*items[i]), search=search(items), start=start,
                        help_text=X.text("NXM-41")).run()
    if chosen is None:
        return False
    kind, name = items[chosen]
    typed = False
    if kind == "type":
        from .franchise import rename
        raw = rename.typed(game, speech, keys, X.text("NXM-43"))
        name = crew.commentators.clean(P.cqn(raw))       # a retired name typed (Ghip) is a name: choose() makes it the default
        debuglog.event("setting", "crew_typed", role=role, typed=raw, kept=name)   # S8.3 round 2: what was typed and what the cleaning kept
        if not name:
            speech.say_async(X.text("NXM-44"))
            return False
        typed = True
    changed = crew.choose(settings, role, name, typed=typed)
    if changed or typed:
        debuglog.event("setting", "change", name=crew.setting(role), value=crew.name_of(settings, role))
    return changed or typed


def crew_menu(game, speech, keys, settings, apply) -> bool:
    """The four names. True when a name changed (the caller says the item again with the sentence about the next game)."""
    changes = []

    def enter(role):
        def run() -> str:
            if pick(game, speech, keys, settings, role):
                apply()
                changes.append(role)
                return role_label(settings, role) + X.text("NXM-23")
            return role_label(settings, role)
        return run

    def change(role):
        def run(step: int = 1) -> None:
            if crew.step(settings, role, step):
                apply()
                changes.append(role)
        return run

    items = [Item(lambda role=role: role_label(settings, role), enter=enter(role), change=change(role)) for role in crew.ROLES]
    SpokenMenu(speech, keys, X.text("NXM-39"), items, help_text=X.text("NXM-63"), space_enters=True, digits_jump=True).run()
    return bool(changes)
