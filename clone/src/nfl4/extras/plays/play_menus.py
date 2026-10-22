"""The spoken play menus of the N. F. L. rules mode in the original's style (nfl4 only, rule 0.13; NX-P4, NX-P7; design
`spec/NFL_PLAYS_DESIGN.md` section 2). This is inspired by Jim Kitchen.

Pure: no speech, no keys, no draw. `PlayMenus` gives the items of the level the player is in and answers what Enter, Right and
Left do; the engine's menu loop (game/pag.py `_menu`) keeps the original's keys: Up and Down move and wrap, a digit or a letter
makes an item the current one, Enter takes it, F1 to F4 as always, Escape concedes. SX.10c connects it through the H3 hooks
(`offense_menu`, `menu_action`, `menu_back`) and one new hook for the Right key.

The top level is the original's menu: Line Plunge, End Run, Screen Pass, Short Pass, Long Pass, Field Goal and Punt keep their
digits 1 to 7 and Enter on a play family calls the playbook's pick of that family for the down and distance (design 2.2), so
the usual call is the original's two keys. Right on a family opens its first list of plays, Right in a list goes to the
family's next list, Left or Backspace goes back. After the original's items come the letters: F favourites, A the last play
again, M more plays, K kneel and P spike (only when they help, design 2.7), O formation and tempo; NflRules then adds Challenge
(C), Time Out and Save Game (S) as now. T is never an item's letter (CLAUDE.md 0.22).
"""
from __future__ import annotations

from typing import NamedTuple

from ...game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
from . import catalog as C
from . import descriptions as D

PICK, KICK, OPEN, CALL, MORE, FAVOURITES, AGAIN, FIND, BACK, SETTINGS, SETTING = (
    "pick", "kick", "open", "call", "more", "favourites", "again", "find", "back", "settings", "setting")
FAVOURITES_MAX = 10
TOP, LIST, MORE_LEVEL, FAV_LEVEL, FOUND, SETTINGS_LEVEL = "top", "list", "more", "favourites", "found", "settings"
LETTERS = {MORE: "m", FAVOURITES: "f", AGAIN: "a", SETTINGS: "o", FIND: "n", BACK: "b", "kneel": "k", "spike": "p",
           "kick_defense": "p"}
RESERVED = ("t", "s", "c", "d")     # T calls a time out anywhere; S Save Game and C Challenge are NflRules' tail; D describes the
                                    # current item (NX-P8, D-091; built in SX.10b2)
# the menu words of spec/strings_nx.tsv (added in SX.10b)
TEXT = {MORE: "NXB-50", FAVOURITES: "NXB-51", AGAIN: "NXB-52", FIND: "NXB-53", SETTINGS: "NXB-54", "find_prompt": "NXB-56",
        "no_match": "NXB-57", "fav_added": "NXB-58", "fav_removed": "NXB-59", "fav_full": "NXB-60", "list_of": "NXB-61",
        BACK: "NXB-10"}
SETTING_TEXT = {"formation": "NXB-62", "personnel": "NXB-63", "motion": "NXB-64", "side": "NXB-65", "tempo": "NXB-66",
                "protection": "NXB-67", "defense_personnel": "NXB-68", "coverage_shade": "NXB-69"}
OFFENSE_SETTINGS = ("formation", "personnel", "motion", "side", "tempo", "protection")
DEFENSE_SETTINGS = ("defense_personnel", "coverage_shade")
# every value of catalog.SETTINGS has a spoken row: NXB-70 to NXB-99, then NXB-A00 on, in the order of the dict
SETTING_VALUE_TEXT: dict = {}
_n = 70
for _name, _values in C.SETTINGS.items():
    for _value in _values:
        if (_name, _value) not in SETTING_VALUE_TEXT:
            SETTING_VALUE_TEXT[(_name, _value)] = "NXB-%02d" % _n if _n < 100 else "NXB-A%02d" % (_n - 100)
            _n += 1
QB_ITEMS = ((8, "NXM-01"), (9, "NXM-02"), (10, "NXM-03"))     # the SX.5 items: 8 sneak, 9 keeper, 0 draw
QB_GROUP = "og13"
KICK_LIST = {6: "kg03", 7: "kg02"}       # Right on Field Goal or Punt: its kinds and fakes


class Item(NamedTuple):
    text_id: str            # the row of the name (or a raw text for the original's items: "=Line Plunge")
    digit: int              # 1 to 9, 0 for the tenth, -1 none
    letter: str
    action: tuple
    extra: str = ""         # a second text said after the first (the play of "Again", a setting's value)


class Context(NamedTuple):
    side: str = "O"                 # O offense, D defense
    two_point: bool = False
    qb_on: bool = True
    kneel_helps: bool = False
    spike_helps: bool = False
    fourth_down: bool = False
    last_call: str = ""             # the concept called last by the player on this side
    favourites: tuple = ()
    usable: frozenset | None = None     # the concept IDs the playbook allows (None: all of the catalog)


def offense_family_items() -> list:
    return [OFFENSE_ITEMS[n - 1].strip()[3:] for n in range(1, 8)]


def defense_family_items() -> list:
    return [DEFENSE_ITEMS[n - 1].strip()[3:] for n in range(1, 7)]


def place(position: int) -> int:
    """The digit of an item by its place (1 to 9, the tenth is 0, later items have none)."""
    return position % 10 if position <= 10 else -1


def concepts_of(group: str, context: Context) -> list[C.Concept]:
    """The plays said in one list: its own and those it lists again (`also`), usable, in catalog order, at most ten."""
    out = [c for c in C.CATALOG if (c.group == group or group in c.also) and not set(c.situations) & ASKED]
    if not context.two_point:                  # a kick team's try play (the swinging gate) only on a try
        out = [c for c in out if not (c.side == "K" and "two_point" in c.situations)]
    if context.usable is not None:
        out = [c for c in out if c.id in context.usable]
    if context.two_point:
        out = [c for c in out if "clock" not in c.situations]
    return out[:C.MAX_PER_GROUP]


ASKED = {"try", "fair_catch"}       # chosen by their own question (the try's kick, the fair catch kick), never from a list


def kickoff_items(safety: bool = False) -> list[Item]:
    """The 2026 kick-off menu (design 2.6, G26-1, SX.10d): the deep kick first so Enter keeps the original's pace, then the short
    kick into the landing zone, the squib and the declared onside kick; after a safety the punt from the 20 too (RB26 11-5-2)."""
    ids = ["K001", "K002", "K003", "K004"] + (["K027"] if safety else [])
    return [Item(C.BY_ID[i].text_id, place(n), "", (CALL, i)) for n, i in enumerate(ids, start=1)]


def family_groups(side: str, family: int) -> list[str]:
    groups = [g for g in C.GROUPS if g.side == side and g.family == family]
    return [g.key for g in sorted(groups, key=lambda g: g.order)]


def more_groups(side: str) -> list[str]:
    if side == "O":
        return [g.key for g in C.GROUPS if g.side == "O" and g.family == 0]
    # SZ.5 (D-110, a player's e-mail of 2026-10-22: "no other plays are listed on defense"): More Plays on defense lists EVERY list of calls so the
    # 89 calls are found in one place: the situation defenses and the kick defense first, where they always were (keys 1 and 2), then the lists
    # that Right opens from each of the six calls, in the order Right goes through them
    groups = sorted((g for g in C.GROUPS if g.side == "D" and g.family), key=lambda g: (g.family, g.order))
    return ["dg11", "kg04"] + [g.key for g in groups]


class PlayMenus:
    """One side's menus in one game: where the player is, and what each key does there."""

    def __init__(self, context: Context = Context()):
        self.context = context
        self.level = TOP
        self.group = ""                 # the open list (LIST level)
        self.parent = TOP               # where Left goes from a list
        self.found: tuple = ()          # the plays a name search found

    def set_context(self, context: Context) -> None:
        self.context = context

    def reset(self) -> None:
        """A play is over or a time out was called: the menu starts at its top again."""
        self.level, self.group, self.parent, self.found = TOP, "", TOP, ()

    # ----- the items of each level -----

    def items(self) -> list[Item]:
        if self.level == LIST:
            return self._list_items(concepts_of(self.group, self.context))
        if self.level == FAV_LEVEL:
            plays = [C.BY_ID[i] for i in self.context.favourites if i in C.BY_ID]
            return self._list_items(plays)
        if self.level == FOUND:
            return self._list_items([C.BY_ID[i] for i in self.found])
        if self.level == MORE_LEVEL:
            items = [Item(C.group_text_id(C.GROUP_BY_KEY[key]), place(n), "", (OPEN, key))
                     for n, key in enumerate(more_groups(self.context.side), start=1)]
            items.append(Item(TEXT[FIND], place(len(items) + 1), LETTERS[FIND], (FIND, 0)))
            items.append(Item(TEXT[BACK], place(len(items) + 1), LETTERS[BACK], (BACK, 0)))
            return items
        if self.level == SETTINGS_LEVEL:
            names = OFFENSE_SETTINGS if self.context.side == "O" else DEFENSE_SETTINGS
            items = [Item(SETTING_TEXT[name], place(n), "", (SETTING, name)) for n, name in enumerate(names, start=1)]
            items.append(Item(TEXT[BACK], place(len(items) + 1), LETTERS[BACK], (BACK, 0)))
            return items
        return self._top()

    def _list_items(self, plays: list[C.Concept]) -> list[Item]:
        items = [Item(p.text_id, place(n), "", (CALL, p.id)) for n, p in enumerate(plays, start=1)]
        items.append(Item(TEXT[BACK], place(len(items) + 1), LETTERS[BACK], (BACK, 0)))
        return items

    def _top(self) -> list[Item]:
        ctx = self.context
        items: list[Item] = []
        if ctx.side == "O":
            names = offense_family_items()
            last = 5 if ctx.two_point else 7
            for n in range(1, last + 1):
                action = (PICK, n) if n <= 5 else (KICK, n)
                items.append(Item("=" + names[n - 1], place(n), "", action))
            if ctx.qb_on and not ctx.two_point:
                for family, text_id in QB_ITEMS:
                    items.append(Item(text_id, place(len(items) + 1), "", (PICK, family)))
        else:
            for n, name in enumerate(defense_family_items(), start=1):
                items.append(Item("=" + name, place(n), "", (PICK, n)))
        if ctx.favourites:
            items.append(Item(TEXT[FAVOURITES], place(len(items) + 1), LETTERS[FAVOURITES], (FAVOURITES, 0)))
        if ctx.last_call in C.BY_ID:
            items.append(Item(TEXT[AGAIN], place(len(items) + 1), LETTERS[AGAIN], (AGAIN, ctx.last_call),
                              C.BY_ID[ctx.last_call].text_id))
        items.append(Item(TEXT[MORE], place(len(items) + 1), LETTERS[MORE], (MORE, 0)))
        if ctx.side == "O" and not ctx.two_point:
            if ctx.kneel_helps:
                items.append(Item(C.BY_ID["O152"].text_id, place(len(items) + 1), LETTERS["kneel"], (CALL, "O152")))
            if ctx.spike_helps:
                items.append(Item(C.BY_ID["O153"].text_id, place(len(items) + 1), LETTERS["spike"], (CALL, "O153")))
        if ctx.side == "D" and ctx.fourth_down:
            items.append(Item(C.group_text_id(C.GROUP_BY_KEY["kg04"]), place(len(items) + 1), LETTERS["kick_defense"],
                              (OPEN, "kg04")))
        items.append(Item(TEXT[SETTINGS], place(len(items) + 1), LETTERS[SETTINGS], (SETTINGS, 0)))
        return items

    # ----- what the keys do -----

    def enter(self, item: Item):
        """Enter on an item. Answers ("call", id) a play is chosen, ("pick", family) the playbook's pick of a family, ("kick", n)
        the original's Field Goal or Punt, ("setting", name) a setting to change, ("find", 0) the typed search, or True: the
        level changed and the menu starts again from its top item."""
        kind, value = item.action
        if kind in (CALL, PICK, KICK, SETTING, FIND):
            return item.action
        if kind == AGAIN:
            return (CALL, value)
        if kind == OPEN:
            self._open(value, self.level)
            return True
        if kind == MORE:
            self.level, self.parent = MORE_LEVEL, TOP
            return True
        if kind == FAVOURITES:
            self.level, self.parent = FAV_LEVEL, TOP
            return True
        if kind == SETTINGS:
            self.level, self.parent = SETTINGS_LEVEL, TOP
            return True
        if kind == BACK:
            return self.back()
        return False

    def _open(self, group: str, parent: str) -> None:
        self.level, self.group, self.parent = LIST, group, parent

    def right(self, item: Item) -> bool:
        """Right: a family's first list from the top; the family's next list from one of its lists (it wraps)."""
        if self.level == TOP:
            kind, value = item.action
            side = self.context.side
            if kind == PICK and value in (8, 9, 10):
                self._open(QB_GROUP, TOP)
                return True
            if kind == PICK:
                groups = family_groups(side, value)
                if groups:
                    self._open(groups[0], TOP)
                    return True
            if kind == KICK and value in KICK_LIST:
                self._open(KICK_LIST[value], TOP)
                return True
            return False
        if self.level == LIST:
            group = C.GROUP_BY_KEY[self.group]
            if group.family:
                groups = family_groups(group.side, group.family)
                self._open(groups[(groups.index(self.group) + 1) % len(groups)], self.parent)
                return True
        return False

    def back(self) -> bool:
        """Left or Backspace (and the Back item): one level up; nothing at the top."""
        if self.level == TOP:
            return False
        if self.level == LIST and self.parent == MORE_LEVEL:
            self.level, self.group, self.parent = MORE_LEVEL, "", TOP
            return True
        self.reset()
        return True

    def search(self, typed: str) -> int:
        """The typed search: the plays whose name has a word starting with the letters (at most ten). The menu shows them as a
        list when there is any; answers how many were found."""
        typed = " ".join(typed.lower().split())
        if not typed:
            return 0
        side = self.context.side
        kick_lists = ("kg02", "kg03") if side == "O" else ("kg04",)    # the kick-offs have their own menu at the kick
        hits = []
        for concept in C.CATALOG:
            if concept.side == "K" and concept.group not in kick_lists:
                continue
            if concept.side not in (side, "K") or set(concept.situations) & ASKED:
                continue
            if concept.side == "K" and "two_point" in concept.situations and not self.context.two_point:
                continue
            if self.context.usable is not None and concept.id not in self.context.usable:
                continue
            name = concept.name.lower()
            words = name.split()
            if name.startswith(typed) or any(" ".join(words[i:]).startswith(typed) for i in range(len(words))):
                hits.append(concept.id)
        self.found = tuple(hits[:C.MAX_PER_GROUP])
        if self.found:
            self.level, self.parent = FOUND, TOP
        return len(hits)

    def describe(self, item: Item) -> str:
        """The row of the plain description of an item (NX-P8, D-091): what the D key says, once per press, with the menu staying on
        the item. Every item of every level has one (a test)."""
        return D.menu_item_row(self.context.side, item.action) or ""

    def heading(self) -> tuple[str, int, int]:
        """The open list's name and its place among its family's lists (said before the first item): (text id, n, m)."""
        if self.level != LIST:
            return "", 0, 0
        group = C.GROUP_BY_KEY[self.group]
        if not group.family:
            return C.group_text_id(group), 0, 0
        groups = family_groups(group.side, group.family)
        return C.group_text_id(group), groups.index(self.group) + 1, len(groups)


def add_favourite(favourites: tuple, play_id: str) -> tuple[tuple, str]:
    """(the new list, the text id to say): a play is added once, at the end, to at most FAVOURITES_MAX."""
    if play_id in favourites:
        return favourites, TEXT["fav_added"]
    if len(favourites) >= FAVOURITES_MAX:
        return favourites, TEXT["fav_full"]
    return favourites + (play_id,), TEXT["fav_added"]


def remove_favourite(favourites: tuple, play_id: str) -> tuple[tuple, str]:
    return tuple(i for i in favourites if i != play_id), TEXT["fav_removed"]
