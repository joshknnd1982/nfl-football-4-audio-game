"""F9, Franchise, your roster by positions (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 21.8, NX-L6, NX-L11; SR.6). This is inspired by Jim Kitchen.

The roster is one list that is heard position by position, in the order of the 22 positions of Madden NFL (quarterbacks, halfbacks, fullbacks, wide receivers,
tight ends, the five linemen, the edge men, tackles, linebackers, cornerbacks, safeties, kicker, punter, long snapper), then the practice squad, the reserve lists
(injured reserve and the like) and the draft's rookies who wait for the cut. A heading says its count ("Quarterbacks, 3."), then each man in his chart order:

    name, position, depth (starter, second, third ...; kick returner and punt returner after it), number, rating, age, potential, contract, tag, morale and word.

Keys (rule 0.24; never T, which calls a timeout in a game, rule 0.22): Up and Down go man by man; Left and Right, Page Up and Page Down go position by position;
Home and End go to the first and the last; a letter goes to the next position that starts with it (E: the tight ends); Enter opens the man's items (make him
the starter, the kick or punt returner, change his name); F1 says the keys; Escape goes back. A man is always said by his own position ("T.J. Watt, left edge"),
whatever place he plays in a game. Plain rules are real_roster.py and lineup.py; this module speaks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from ...game.keys import KEY_DOWN, KEY_END, KEY_ENTER, KEY_ESCAPE, KEY_F1, KEY_HOME, KEY_LEFT, KEY_PAGE_DOWN, KEY_PAGE_UP, KEY_RIGHT, KEY_UP, typed_character
from ...game.spoken_menu import Item, SpokenMenu, _Speaker
from .. import lineup as L
from .. import nx_texts as X
from .. import roster_file as RF
from .. import roster_model as RM
from . import data as D

ORDINALS = ["NXM-L%02d" % n for n in range(10, 20)]
HEADINGS = {key: "NXL-%d" % (60 + n) for n, key in enumerate(RM.MADDEN)}


class _Done(Exception):
    """An item of a man was taken: the menu of his items ends and the sentence is said."""

    def __init__(self, text):
        super().__init__("done")
        self.text = text


@dataclass
class Section:
    key: str                                  # a position of the 22, "squad", a reserve list's code or "rookies"
    heading: str
    men: list = field(default_factory=list)   # Players
    letter: str = ""


def letter_of(heading: str, key: str) -> str:
    """The letter that goes to a heading: its first letter, except T (the timeout key) and the tight ends, who are E."""
    if key == "TE":
        return "e"
    first = heading.strip()[:1].lower()
    return "" if first == "t" else first


# ----- the sections and the lines -----

def sections_of(g, store) -> list:
    league = store.league
    team = league.team
    chart = league.chart[team - 1]
    out = []
    for key in RM.MADDEN:
        heading = X.text(HEADINGS[key])
        men = [league.players[pid] for pid in chart.get(key, ()) if pid in league.players and league.players[pid].status == "active"]
        out.append(Section(key, heading, men, letter_of(heading, key)))
    squad = sorted((p for p in league.players.values() if p.status == "practice" and p.team == team), key=lambda p: (-p.rating, p.id))
    heading = X.text("NXL-84")
    out.append(Section("squad", heading, squad, letter_of(heading, "squad")))
    for code, name in RF.RESERVE.items():
        men = sorted((p for p in league.players.values() if p.status == "list" and p.team == team and p.roster_list == code), key=lambda p: (-p.rating, p.id))
        if men:
            out.append(Section(code, name, men, letter_of(name, code)))
    rookies = league.waiting_rookies(team) if league.draft is not None else []
    if rookies:
        heading = X.text("NXL-85")
        out.append(Section("rookies", heading, list(rookies), letter_of(heading, "rookies")))
    return out


def depth_word(section: Section, index: int) -> str:
    if index < RF.STARTERS.get(section.key, 1):
        return X.text(ORDINALS[0])
    return X.text(ORDINALS[index]) if index < len(ORDINALS) else X.text("NXM-L20", n=index + 1)


def name_in_team(league, player) -> str:
    """The man's name; two men of one name on the team are told apart by their numbers (design 21.8)."""
    key = player.name.casefold()
    if any(p.id != player.id and p.team == player.team and p.status in ("active", "practice", "list") and p.name.casefold() == key
           for p in league.players.values()):
        return X.text("NXM-L82", player=player.name, number=player.number).strip()
    return player.name


def man_line(g, store, section: Section, index: int) -> str:
    """One man of the roster, spoken (design 21.8)."""
    from . import people_flow
    league, words = store.league, store.words
    p = section.men[index]
    if section.key == "rookies":
        low, high = league.rookie_range(p)
        return words.prospect_line(p.name, p.position or p.pos, low, high, p.age, p.potential)
    name = name_in_team(league, p)
    word = words.position_for(p)
    if section.key == "squad":
        where = X.text("NXM-L06", position=word)
    elif section.key in RF.RESERVE:
        where = X.text("NXM-L23", position=word, list=RF.RESERVE[section.key])
    else:
        depth = depth_word(section, index)
        chart = league.chart[league.team - 1]
        if chart.get("KR", [None])[:1] == [p.id]:
            depth += X.text("NXM-L21").rstrip()
        if chart.get("PR", [None])[:1] == [p.id]:
            depth += X.text("NXM-L22").rstrip()
        where = X.text("NXM-L04", position=word, depth=depth)
    if p.number != "-":
        where += X.text("NXM-L05", number=p.number).rstrip()
    line = X.text("NXL-33", player=name, position=where, r=p.rating, a=p.age, potential=words.potential(p.potential), contract=words.contract(p))
    return line + people_flow.roster_words(words, league, p)


# ----- the list -----

class PositionList(_Speaker):
    """The roster: sections of men. `build()` gives the sections again after a change (the list keeps the man's place); `line(section, index)` speaks a man;
    `enter(section, index)` is Enter on a man and returns the text to say, or None."""
    kind = "list"

    def __init__(self, speech, keys, title: str, build: Callable[[], list], line: Callable, enter: Callable, help_text: str):
        super().__init__(speech, keys)
        self.title = title
        self.build = build
        self.line = line
        self.enter = enter
        self.help_text = help_text
        self.sections = build()
        self.s = 0
        self.i = 0

    def _count(self, s: int) -> int:
        return len(self.sections[s].men)

    def _first(self, s: int) -> str:
        """A position reached: its heading, then its first man (or nothing when it has none)."""
        section = self.sections[s]
        text = X.text("NXM-L01", heading=section.heading, n=len(section.men))
        return text + (self.line(section, 0) if section.men else "")

    def _here(self) -> str:
        """The man the list is on; his heading before him when he is the first of his position."""
        section = self.sections[self.s]
        if not section.men:
            return self._first(self.s)
        return (self._first(self.s) if self.i == 0 else self.line(section, self.i))

    def _step(self, step: int) -> None:
        """Up (-1) or Down (+1) by man, going on to the next position; empty positions are heard as their heading and pass on at the next key."""
        s, i = self.s, self.i
        total = len(self.sections)
        i += step
        while True:
            if 0 <= i < self._count(s):
                break
            s = (s + step) % total
            i = 0 if step > 0 else max(0, self._count(s) - 1)
            if self._count(s) == 0:
                break
        self.s, self.i = s, i

    def _section(self, step: int) -> None:
        self.s = (self.s + step) % len(self.sections)
        self.i = 0

    def _rebuild(self, keep) -> None:
        """After a change: the sections again, the list on the same man if he is still there, else on the same position."""
        old_key = self.sections[self.s].key
        self.sections = self.build()
        for s, section in enumerate(self.sections):
            if section.key == old_key:
                self.s = s
                break
        section = self.sections[self.s]
        found = next((n for n, p in enumerate(section.men) if p.id == keep), None)
        self.i = found if found is not None else max(0, min(self.i, len(section.men) - 1))

    def _run(self) -> None:
        self.say(self.title + " " + self._first(0))
        while True:
            code = self.keys.read_key()
            if code == KEY_ESCAPE:
                self.leave()
                return
            if code in (KEY_UP, KEY_DOWN):
                self._step(1 if code == KEY_DOWN else -1)
                self.say(self._here())
            elif code in (KEY_LEFT, KEY_PAGE_UP):
                self._section(-1)
                self.say(self._first(self.s))
            elif code in (KEY_RIGHT, KEY_PAGE_DOWN):
                self._section(1)
                self.say(self._first(self.s))
            elif code == KEY_HOME:
                self.s, self.i = 0, 0
                self.say(self._first(0))
            elif code == KEY_END:
                self.s = len(self.sections) - 1
                self.i = max(0, self._count(self.s) - 1)
                self.say(self._here())
            elif code == KEY_ENTER:
                section = self.sections[self.s]
                if not section.men:
                    self.say(self._first(self.s))
                    continue
                keep = section.men[self.i].id
                text = self.enter(section, self.i)
                self._rebuild(keep)
                self.say(text if text else self._here())
            elif code == KEY_F1:
                self.say(self.help_text)
            else:
                char = typed_character(code) if isinstance(code, int) else ""
                if char and char != " ":
                    total = len(self.sections)
                    found = next((n for n in ((self.s + k) % total for k in range(1, total + 1)) if self.sections[n].letter == char), None)
                    if found is not None:
                        self.s, self.i = found, 0
                        self.say(self._first(found))
                        continue
                self.say(self._here())


# ----- a man's items -----

def man_items(g, speech, keys, store, section: Section, player) -> str | None:
    """Enter on a man: make him a starter (his own position, or the other side or role of his family), the kick or punt returner, or change his name.
    Returns the sentence to say."""
    from . import rename
    league, words = store.league, store.words
    backend = L.FranchiseBackend(g, store)
    man = backend._man(player)
    items: list = []

    def take(key: str, slot: int):
        def act():
            raise _Done(backend.choose(key, man, slot))
        return act

    if section.key in RM.MADDEN:
        chart = league.chart[league.team - 1]
        for target in (player.position,) + tuple(RM.SAME_FAMILY_MOVES.get(player.position, ())):
            for slot in range(L.starters_of(target)):
                if chart.get(target, [None] * (slot + 1))[slot:slot + 1] == [player.id]:
                    continue                                          # he starts there already
                word = RF.SPOKEN[target]
                text = X.text("NXM-L26", n=slot + 1, position=word) if L.starters_of(target) > 1 else X.text("NXM-L25", position=word)
                items.append(Item(lambda text=text: text.strip(), enter=take(target, slot)))
        if player.position not in RM.RETURN_NEVER:
            for role, text_id in (("KR", "NXM-L27"), ("PR", "NXM-L28")):
                if chart.get(role, [None])[:1] != [player.id]:
                    items.append(Item(lambda text_id=text_id: X.text(text_id).strip(), enter=take(role, 0)))

    def rename_him():
        raise _Done(rename.ask(g, speech, keys, store, player))
    items.append(Item(lambda: X.text("NXM-L29").strip(), enter=rename_him))
    title = X.text("NXM-L24", player=name_in_team(league, player), position=words.position_for(player))
    try:
        SpokenMenu(speech, keys, title, items, space_enters=True, digits_jump=True).run()
    except _Done as done:
        return done.text
    return None


def roster_list(g, speech, keys, store) -> None:
    """F9, Franchise, your roster."""
    league = store.league
    told = " ".join(t.strip() for t in L.FranchiseBackend(g, store).notices())            # a starter he chose who left (design 21.13)

    def build() -> list:
        return sections_of(g, store)

    count = sum(1 for p in league.players.values() if p.team == league.team and p.status == "active" and p.id not in set(_waiting(league)))
    title = X.text("NXF-13").rstrip(". ") + "." + X.text("NXM-L02", n=count, m=D.ROSTER_MAX) + (" " + told + " " if told else "")
    PositionList(speech, keys, title, build, lambda section, i: man_line(g, store, section, i),
                 lambda section, i: man_items(g, speech, keys, store, section, section.men[i]), X.text("NXM-L03")).run()


def _waiting(league) -> list:
    from . import real_roster
    return list(real_roster.waiting_ids(league))
