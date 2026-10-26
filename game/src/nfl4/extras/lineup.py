"""The starting lineup and the choice of who starts, at every real position (nfl4 only, rule 0.13; CLAUDE.md 0.30, 0.24, 0.25; NX-L11, D-160; NFL_FRANCHISE_DESIGN
21.13). This is inspired by Jim Kitchen.

The owner (2026-10-25): "Claude must add the ability for the user to choose who starts from the current rosters." Two backends give the same questions to the
speech, so a quick game or a season (the team's setting `nx_depth`, laid over the real rosters) and a franchise (the league's depth chart) are heard the same
way:

* `slots()` the lineup's lines: QB, HB, FB (when the team has one), WR 1 to 3, TE, the five linemen, LEDG, DT 1 and 2, REDG, SAM, MIKE, WILL, CB 1 and 2, FS, SS,
  K, P, LS, then the kick and punt returners (design 21.13);
* `candidates(key)` who may be chosen: every active man of the position, then the men of his family who can move there (the other side or role), then the
  practice squad's men of the position; for a return role every active man who may return;
* `choose(key, man, slot)` makes him the starter and says it in one sentence. The man who was there takes the chosen man's old place on the chart; a squad man
  is an elevation (quick game: two a game) or, in a franchise, a signing first (practice_flow).

The speech is `menu_items`, `lineup_picker` and `choose_flow`; D (rule 0.25) describes the position the menu is on. No draw anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..data import debuglog
from ..game.spoken_menu import Item, ListPicker
from . import depth_chart as DC
from . import nx_texts as X
from . import roster_file as RF
from . import roster_model as RM

MULTI = {"WR": 3, "DT": 2, "CB": 2}               # the positions that start more than one man (roster_file.STARTERS)
LINEUP = (("QB", 0), ("HB", 0), ("FB", 0), ("WR", 0), ("WR", 1), ("WR", 2), ("TE", 0), ("LT", 0), ("LG", 0), ("C", 0), ("RG", 0), ("RT", 0),
          ("LEDG", 0), ("DT", 0), ("DT", 1), ("REDG", 0), ("SAM", 0), ("MIKE", 0), ("WILL", 0), ("CB", 0), ("CB", 1), ("FS", 0), ("SS", 0),
          ("K", 0), ("P", 0), ("LS", 0), ("KR", 0), ("PR", 0))
KEYS = tuple(RM.MADDEN) + tuple(RM.ROLES)           # the 22 positions and the two roles, the order of the menu and of the descriptions
ROLE_TEXT = {"KR": "NXL-82", "PR": "NXL-83"}
DESCRIPTION = {key: "NXM-L%d" % (40 + n) for n, key in enumerate(KEYS)}


class LineupError(Exception):
    """A choice the rules refuse; the text is the sentence to say."""

    def __init__(self, text: str):
        super().__init__(text)
        self.text = text


@dataclass(frozen=True)
class Man:
    key: object                 # a player id (franchise) or the written name (quick game)
    name: str                   # as spoken
    position: str               # one of the 22
    number: str = "-"
    rating: int | None = None
    age: int | None = None
    squad: bool = False         # on the practice squad (or brought up from it for the next game)


# ----- the words -----

def word(key: str) -> str:
    """A position's (or a role's) singular word."""
    return X.text(ROLE_TEXT[key]) if key in ROLE_TEXT else RF.SPOKEN[key]


def label(key: str, slot: int = 0) -> str:
    """The lineup's name of a place: "left tackle", "wide receiver 2" (a position that starts several men numbers them)."""
    if key in MULTI:
        return X.text("NXM-L36", position=word(key), n=slot + 1)
    return word(key)


def describe(key: str) -> str:
    """Rule 0.25: the plain description of a position or role."""
    return X.text(DESCRIPTION[key]).strip() if key in DESCRIPTION else ""


def starters_of(key: str) -> int:
    return 1 if key in RM.ROLES else RF.STARTERS.get(key, 1)


def man_line(man: Man, current: bool = False) -> str:
    """A man in a list of candidates: his name and own position, his rating and age when the program knows them, and whether he starts now or is on the squad."""
    line = X.text("NXM-L79", player=man.name, position=RF.SPOKEN[man.position]).strip()
    if man.rating is not None:
        line += X.text("NXM-L80", r=man.rating, a=man.age).rstrip()
    if man.number != "-":
        line += X.text("NXM-L05", number=man.number).rstrip()
    if man.squad:
        line += X.text("NXM-L66").rstrip()
    if current:
        line += X.text("NXM-L65").rstrip()
    return line + ". "


def lineup_line(backend, key: str, slot: int) -> str:
    """One line of the lineup: the place, then its starter and his number."""
    place = label(key, slot)
    found = backend.starters(key)
    man = found[slot] if slot < len(found) else None
    if man is None:
        fill = backend.fill(key, slot)                 # S8.2: a man of another position plays there (B-P189)
        if fill is not None:
            man, own, how = fill
            if how == "squad":
                return X.text("NXM-L88" if man.number != "-" else "NXM-L89", position=place, player=man.name, number=man.number)
            return X.text("NXM-L86" if man.number != "-" else "NXM-L87", position=place, player=man.name, number=man.number,
                          old=RF.SPOKEN[own])
        squad = backend.squad_men(key)
        if squad:
            return X.text("NXM-L35", position=place, player=squad[0].name)
        return X.text("NXM-L34", position=place)
    if man.number != "-":
        return X.text("NXM-L32", position=place, player=man.name, number=man.number)
    return X.text("NXM-L33", position=place, player=man.name)


def result_text(backend, key: str, man: Man, slot: int, old_position: str, before) -> str:
    """The sentence after a choice."""
    place = label(key, slot)
    if before is not None and before == man.key and not man.squad:
        return X.text("NXM-L72", player=man.name)
    if key in RM.ROLES:
        return X.text("NXM-L71", player=man.name, position=word(key))
    if man.squad:
        return backend.squad_text(man, key)
    if old_position != key:
        return X.text("NXM-L70", player=man.name, old=RF.SPOKEN[old_position], new=RF.SPOKEN[key])
    if key in MULTI:
        return X.text("NXM-L69", player=man.name, position=word(key), n=slot + 1)
    return X.text("NXM-L68", player=man.name, position=place)


# ----- the choice -----

def choose_flow(speech, keys, backend, key: str, slot: int = 0) -> str | None:
    """The list of the men who may start at the place; Enter makes one the starter. Returns the sentence to say, or None when the player left with Escape."""
    busy = backend.busy()
    if busy:
        return busy
    candidates = backend.candidates(key)
    if not candidates:
        return X.text("NXM-L77", position=word(key))
    current = backend.starters(key)
    now = current[slot].key if slot < len(current) else None
    if now is None:
        fill = backend.fill(key, slot)                 # the man who fills in is where the list starts, said as starting now
        now = fill[0].key if fill is not None else None
    start = next((i for i, man in enumerate(candidates) if man.key == now), 0)
    lines = [man_line(man, man.key == now) for man in candidates]
    if key in RM.ROLES:
        title = X.text("NXM-L39", position=word(key))
    elif key in MULTI:
        title = X.text("NXM-L38", position=word(key), n=slot + 1)
    else:
        title = X.text("NXM-L37", position=word(key))
    picked = ListPicker(speech, keys, title, len(lines), lambda i: lines[i], start=start).run()
    if picked is None:
        return None
    man = candidates[picked]
    try:
        text = backend.choose(key, man, slot)
    except LineupError as exc:
        return exc.text
    return text


# ----- the menus -----

def lineup_picker(speech, keys, backend, team_name: str) -> None:
    """F9, Rules, Depth charts, Starting lineup: one list of the lines of LINEUP; Enter opens the place's choice; D describes the place."""
    slots = backend.slots()

    def name(i: int) -> str:
        return lineup_line(backend, *slots[i])

    def enter(i: int):
        return choose_flow(speech, keys, backend, *slots[i])

    def on_key(char: str, i: int):
        return describe(slots[i][0]) if char == "d" else None
    ListPicker(speech, keys, X.text("NXM-L31", team=team_name), len(slots), name, on_enter=enter, close_on_enter=False, on_key=on_key).run()


def position_items(speech, keys, backend, first_label) -> tuple:
    """The items of the depth chart menu below the lineup: the 22 positions and the two returners, each with its first man (`first_label(key)` says it).
    Returns (items, the key of each item), the second for the D key."""
    items, order = [], []
    for key in KEYS:
        if key in MULTI:
            items.append(Item(lambda key=key: first_label(key), enter=lambda key=key: _slot_flow(speech, keys, backend, key)))
        else:
            items.append(Item(lambda key=key: first_label(key), enter=lambda key=key: choose_flow(speech, keys, backend, key, 0)))
        order.append(key)
    return items, order


def _slot_flow(speech, keys, backend, key: str):
    """A position that starts several men: which of them is being chosen."""
    lines = [lineup_line(backend, key, slot) for slot in range(MULTI[key])]
    picked = ListPicker(speech, keys, X.text("NXL-%d" % (60 + RM.MADDEN.index(key))), len(lines), lambda i: lines[i]).run()
    if picked is None:
        return None
    return choose_flow(speech, keys, backend, key, picked)


# ----- the backends -----

class Backend:
    """What the two backends have in common."""
    team_name = ""

    def slots(self) -> list:
        """The lines of the lineup: (key, slot); a fullback only when the team has one."""
        have_fb = bool(self.men_at("FB")) or bool(self.squad_men("FB"))
        return [slot for slot in LINEUP if slot[0] != "FB" or have_fb]

    def busy(self) -> str | None:
        return None

    def fill(self, key: str, slot: int = 0):
        """S8.2 (B-P189): (man, his own position, how) of a lineup place with no man of its own position, or None (roster_model.fill_ins)."""
        if key in RM.ROLES:
            return None
        chart = {position: self.men_at(position) for position in RM.MADDEN}
        squad = {position: self.squad_men(position) for position in ("K", "P")}
        return RM.fill_ins(chart, squad, LINEUP).get((key, slot))

    def squad_text(self, man: Man, key: str) -> str:
        return X.text("NXM-L68", player=man.name, position=label(key))

    def notices(self) -> list:
        return []


class QuickBackend(Backend):
    """A quick game or a season: the player's `nx_depth` laid over the real rosters of any of the 32 teams (extras/depth_chart.py)."""

    def __init__(self, game, team: int, team_name: str):
        self.game = game
        self.team = team
        self.team_name = team_name

    @property
    def real(self):
        return self.game.real_names

    def _lines(self) -> dict:
        return {p.name: p for p in self.real.rosters[self.team - 1] if p.pos != "RET"}

    def _man(self, written: str, squad: bool = False) -> Man:
        p = self._lines()[written]
        return Man(written, self.real.spoken(written), p.madden, p.number, None, None, squad or p.squad)

    def _brought(self) -> set:
        from . import quarterbacks
        depth = DC.parse_depth(self.game.options.settings.game.nx_depth)
        return {n.casefold() for n in DC.elevated_names(depth, quarterbacks.base_names(self.game), self.team)}

    def _chart(self) -> tuple:
        return self.real.chart(self.team)

    def men_at(self, key: str) -> list:
        chart, _roles, _squad = self._chart()
        brought = self._brought()
        return [self._man(n, n.casefold() in brought) for n in chart.get(key, ())]

    def squad_men(self, key: str) -> list:
        _chart, _roles, squad = self._chart()
        return [self._man(n, True) for n in squad.get(key, ())]

    def starters(self, key: str) -> list:
        if key in RM.ROLES:
            _chart, roles, _squad = self._chart()
            return [self._man(n) for n in roles.get(key, ())[:1]]
        return self.men_at(key)[:starters_of(key)]

    def candidates(self, key: str) -> list:
        chart, roles, squad = self._chart()
        if key in RM.ROLES:
            first = [self._man(n) for n in roles.get(key, ())]
            seen = {m.key for m in first}
            rest = [self._man(n) for position in RM.MADDEN if position not in RM.RETURN_NEVER for n in chart.get(position, ()) if n not in seen]
            return first + rest
        out = self.men_at(key)
        for other in RM.SAME_FAMILY_MOVES.get(key, ()):
            out += self.men_at(other)
        return out + self.squad_men(key)

    def choose(self, key: str, man: Man, slot: int) -> str:
        from . import quarterbacks
        settings = self.game.options.settings.game
        current = self.starters(key)
        before = current[slot].key if slot < len(current) else None
        old_position = man.position
        try:
            depth = DC.choose_starter(DC.parse_depth(settings.nx_depth), self.real, self.team, key, man.key, slot,
                                      base=quarterbacks.base_names(self.game))
        except DC.ElevationLimit:
            return X.text("NXM-L74")
        except ValueError:
            return X.text("NXM-L76", player=man.name, position=label(key, slot))
        settings.nx_depth = DC.render_depth(depth)
        self.game.options.save()
        quarterbacks.apply(self.game)                      # the next game uses the new order
        debuglog.event("extras", "starter_chosen", team=self.team, position=key, player=man.key, slot=slot, mode="quick",
                       squad=man.squad)                                                        # rule 0.15
        return result_text(self, key, man, slot, old_position, before)

    def squad_text(self, man: Man, key: str) -> str:
        return X.text("NXM-L73", player=man.name, position=label(key))

    def notices(self) -> list:
        """A starter the player chose who is no longer on the team's active roster (a new rosters.txt): one sentence each; the entry is dropped."""
        settings = self.game.options.settings.game
        depth = DC.parse_depth(settings.nx_depth)
        entries = depth.get(self.team, {})
        if not entries or not self.real.is_layout2(self.team):
            return []
        chart, roles, _squad = self._chart()
        active = {n.casefold() for position in RM.MADDEN for n in chart.get(position, ())}
        from . import quarterbacks
        base = quarterbacks.base_names(self.game)
        told = []
        for key in KEYS:
            names = entries.get(key)
            if not names:
                continue
            for slot, written in enumerate(names[:starters_of(key)]):
                if written.casefold() in active or written.casefold() in {n.casefold() for n in DC.elevated_names(depth, base, self.team)}:
                    continue
                now = (roles.get(key, ()) if key in RM.ROLES else chart.get(key, ()))
                new = now[slot] if slot < len(now) else None
                told.append(X.text("NXM-L75", old=self.real.spoken(written), new=self.real.spoken(new), position=word(key)) if new else
                            X.text("NXM-L78", old=self.real.spoken(written), position=word(key)))
        if told:
            cleaned = {key: [n for n in names if n.casefold() in active] for key, names in entries.items()}
            depth[self.team] = {key: names for key, names in cleaned.items() if names}
            if not depth[self.team]:
                del depth[self.team]
            settings.nx_depth = DC.render_depth(depth)
            self.game.options.save()
            from . import quarterbacks as Q
            Q.apply(self.game)
            debuglog.event("extras", "starter_dropped", team=self.team, count=len(told))                # rule 0.15
        return told


class FranchiseBackend(Backend):
    """The player's own team of a franchise: the league's depth chart (extras/franchise/real_roster.py); `promote(man)` signs a squad man (the practice
    squad's own questions) and returns (the sentence, True when he is on the roster)."""

    def __init__(self, game, store, promote=None):
        self.game = game
        self.store = store
        self.promote = promote
        self.team_name = store.words.team_name(store.league.team)

    @property
    def league(self):
        return self.store.league

    def _man(self, p, squad: bool = False) -> Man:
        return Man(p.id, p.name, p.position, p.number, p.rating, p.age, squad)

    def busy(self) -> str | None:
        return X.text("NXI-54") if self.game.play_engine is not None else None

    def men_at(self, key: str) -> list:
        league = self.league
        chart = league.chart[league.team - 1]
        return [self._man(league.players[pid]) for pid in chart.get(key, ()) if pid in league.players]

    def squad_men(self, key: str) -> list:
        league = self.league
        found = [p for p in league.players.values() if p.status == "practice" and p.team == league.team and p.position == key]
        return [self._man(p, True) for p in sorted(found, key=lambda p: (-p.rating, p.id))]

    def starters(self, key: str) -> list:
        league = self.league
        if key in RM.ROLES:
            ids = league.chart[league.team - 1].get(key, ())[:1]
            return [self._man(league.players[pid]) for pid in ids if pid in league.players]
        return self.men_at(key)[:starters_of(key)]

    def candidates(self, key: str) -> list:
        league = self.league
        if key in RM.ROLES:
            first = list(league.chart[league.team - 1].get(key, ()))
            rest = [m.key for position in RM.MADDEN if position not in RM.RETURN_NEVER for m in self.men_at(position) if m.key not in first]
            return [self._man(league.players[pid]) for pid in first + rest if pid in league.players]
        out = self.men_at(key)
        for other in RM.SAME_FAMILY_MOVES.get(key, ()):
            out += self.men_at(other)
        return out + self.squad_men(key)

    def choose(self, key: str, man: Man, slot: int) -> str:
        from .franchise import real_roster
        from .franchise.league import LeagueError
        league = self.league
        current = self.starters(key)
        before = current[slot].key if slot < len(current) else None
        old_position = man.position
        signed = ""
        if man.squad:
            if self.promote is None:
                return X.text("NXM-L76", player=man.name, position=label(key, slot))
            signed, ok = self.promote(man)                 # the practice squad's own questions (closed, a release, the contract)
            if not ok:
                return signed
        try:
            real_roster.choose_starter(league, key, man.key, slot)
        except LeagueError:
            return signed + X.text("NXM-L76", player=man.name, position=label(key, slot))
        self.store.save()                                  # written, then told (B-X53)
        return signed + result_text(self, key, Man(man.key, man.name, man.position, man.number, man.rating, man.age, False), slot, old_position,
                                    before if not man.squad else None)

    def notices(self) -> list:
        from .franchise import real_roster
        league = self.league
        told = []
        for pid, key, slot, now in real_roster.told_dropped(league):
            gone = league.players.get(pid)
            old = gone.name if gone is not None else ""
            new = league.players[now].name if now in league.players else None
            told.append(X.text("NXM-L75", old=old, new=new, position=word(key)) if new else X.text("NXM-L78", old=old, position=word(key)))
        if told:
            self.store.save()
            debuglog.event("franchise", "starter_dropped", count=len(told))                              # rule 0.15
        return told
