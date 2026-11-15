"""Substitutions during a game, the program's part: the U key of the play menus, the lists it speaks, and the lineup it gives the engine (nfl4 only,
rule 0.13; GitHub issue 14, D-229). This is inspired by Jim Kitchen.

The rules are `subs.py`. Here:

* `SubsFlow.menu` (U in the player's offense or defense menu, the N. F. L. rules): a short list in the original's style. Its items: put all your
  backups in for the rest of the game; put your starters back in (when anything is changed); then the groups of places (quarterback, running backs,
  receivers, defensive linemen, linebackers, cornerbacks, safeties, kick and punt returners, kicker, punter), each said with who plays there now.
  Enter on a group lists its places and their men; Enter on a place lists who may come in there (the lineup's men of the position, then the bench's);
  Enter on a man asks for how long: the next play only, or the rest of the game. Escape goes back one list; from the first it goes back to the play
  menu, which says its current item. D says what the position of a place or of a man does (rule 0.25). T calls a time out as anywhere in a game.
* `SubsFlow.ensure` (the play menus, the kick-off and the end of every play): a next-play substitution ends after the play it was made for (a foul
  before the snap keeps it, the down is played again), and the lineup the engine plays is made again when anything changed.
* A quick game or a season: the base is the player's side's 34 names as the set-up made them (taken again whenever the game gave the roster other
  names), its men's positions from the real rosters (the player's depth charts laid over them), its bench the other active men of the real roster.
  A franchise game: `franchise_apply` is called by the injuries' `refresh` of the player's side (franchise/injury_flow.GameInjuries), so a man who is
  hurt leaves the lineup at once and every place keeps the identity, the rating and the injury draws of the man who really plays it.

The tester's answers on issue 14 (2026-11-15, rule 0.41; D-234 to D-236):
* "All backups in" also puts the backup returners in (Q-087): `spares` gives the team's returners in their order (the real roles KR1, PR1, KR2,
  PR2 ...; a franchise game's fit men only).
* Packages by formation (Q-086) and for the kicks (Q-097, D-241: the kick-off, kick return, punt, punt return and field goal teams;
  `kick_package` at the kick-off and the kicked try, `before_snap` at a punt and a field goal): the top list's last item, "Formation and kick
  packages", lists the offense's formations, the defense's packages and the kicks' teams, each
  with how many men are set; Enter on one lists the groups as they play in it, then the places and the men as for a substitution, with no question
  of how long: the man comes in for every play called in that formation. "Clear this package" ends it. `before_snap` (NflRules.before_snap, the
  play called) lays the package of the called play's formation over the lineup; `ensure` takes it off again between plays and at a kick.
* The computer rests its starters (Q-085): `rest` (NflRules.between_plays and the kick-off) puts the computer side's backups in when it leads by a
  lot late in the game and its starters back when the lead shrinks (subs.rest_due), with one sentence each; the record is
  ExtrasRecord.computer_rest (Save Game keeps it).

Nothing here draws: a game where the player substitutes nobody is the very same game (its record stays None).
"""
from __future__ import annotations

import logging

from ..data import debuglog
from ..game.rules import MENU_QUIET, MENU_REFRESH, TIMEOUT_GRANTED
from . import nx_texts as X
from . import roster_model as RM
from . import subs as S
from .plays import catalog as C
from .plays import personnel
from .plays.play_menus import SETTING_VALUE_TEXT
from .qb_runs import to_goal

log = logging.getLogger("nfl4.extras")

KEY_ENTER, KEY_ESCAPE, KEY_UP, KEY_DOWN, KEY_HOME, KEY_END = "13", "27", "38", "40", "36", "35"
KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
GROUP_WORDS = {"QB": "NXL-03", "RB": "NXL-11", "WR": "NXL-12", "DL": "NXL-14", "LB": "NXL-15", "CB": "NXL-16", "S": "NXL-17", "RET": "NXL-86",
               "K": "NXL-09", "P": "NXL-10"}
PLACE_WORDS = {"QB": "NXL-03", "RB": "NXL-01", "WR": "NXL-02", "DL": "NXL-04", "LB": "NXL-05", "CB": "NXL-06", "S": "NXL-07", "RET": "NXL-08",
               "K": "NXL-09", "P": "NXL-10"}
# the position whose plain description D says for a man or a place known only by its group (a game without real names)
DESCRIBE_GROUP = {"QB": "QB", "RB": "HB", "WR": "WR", "DL": "DT", "LB": "MIKE", "CB": "CB", "S": "FS", "K": "K", "P": "P"}
SECTION_ATTRIBUTES = (("running_backs", 6), ("receivers", 6), ("defense", 17), ("special_teams", 2), ("kickers", 2))
EMPTY_HEADINGS = {"Running Backs:": 0, "Receivers:": 6}
# Q-086 (D-235): the spoken name of each package (the offense's formations are the Formation setting's own words)
PACKAGE_WORDS = {"O:other": "NXB-U21", "D:heavy": "NXB-U22", "D:base": "NXB-U23", "D:nickel": "NXB-U24", "D:dime": "NXB-U25",
                 "D:quarter": "NXB-U26",
                 # Q-097 (D-241): the kicks' teams
                 "K:kickoff": "NXB-U36", "K:kick_return": "NXB-U37", "K:punt": "NXB-U38", "K:punt_return": "NXB-U39", "K:field_goal": "NXB-U40"}
FIELD_GOAL_PLAY, PUNT_PLAY = 6, 7                 # the original's offense plays of the field goal and the punt (pag_scrimmage.snap)


class SubsFlow:
    def __init__(self, rules):
        self.rules = rules
        # a quick game's snapshot of each side: [the game state it belongs to, the 34 names as the game made them, the 34 names this flow wrote
        # last (a roster with other names was made again by the game)]
        self.snap = {1: [None, None, None], 2: [None, None, None]}
        self.formation = None         # Q-086: the formation of the play called now (subs.PACKAGES), None between plays
        self.applied = None           # the formation whose package is in the lineup now

    @property
    def base_names(self):
        return self.snap[1][1]

    @property
    def written(self):
        return self.snap[1][2]

    @property
    def game(self):
        return self.rules.game

    # ----- the record -----

    @staticmethod
    def record(state, make: bool = False):
        extras = getattr(state, "extras", None)
        if extras is None:
            return None
        if getattr(extras, "subs", None) is None and make:
            extras.subs = S.new_record()
        return getattr(extras, "subs", None)

    # ----- the lineup: a quick game -----

    @staticmethod
    def read_names(state, side: int = 1) -> list | None:
        """A side's 34 names in the places' order, or None when its roster is not whole."""
        roster = state.rosters.get(side) if isinstance(getattr(state, "rosters", None), dict) else None
        if roster is None:
            return None
        names = []
        for attribute, count in SECTION_ATTRIBUTES:
            values = getattr(roster, attribute)
            if len(values) != count:
                return None
            names += list(values)
        quarterbacks = state.quarterbacks if isinstance(getattr(state, "quarterbacks", None), dict) else {}
        names.append(quarterbacks.get(side, ""))
        return names

    @staticmethod
    def write_names(state, names: list, side: int = 1) -> None:
        roster = state.rosters[side]
        at = 0
        for attribute, count in SECTION_ATTRIBUTES:
            getattr(roster, attribute)[:] = names[at:at + count]
            at += count
        state.quarterbacks[side] = names[S.QUARTERBACK]

    def real_chart(self, side: int = 1) -> tuple[dict, dict, list] | None:
        """({spoken name: position}, {position: [spoken names in depth order]}, [the returners in turn: KR1, PR1, KR2, PR2 ...]) of a side's team in
        the real rosters (the player's depth charts and starting quarterback laid over his), or None (no real names, or a team that is not one of
        the 32)."""
        g = self.game
        real = getattr(g, "real_names", None)
        season = getattr(g, "season", None)
        if real is None or season is None:
            return None
        division, place = (season.tn1, season.tn2) if side == 1 else (season.tn3, season.tn4)
        if not (1 <= division <= 8 and 1 <= place <= 4):
            return None
        from .franchise.league import team_index
        team = team_index(division, place)
        try:
            if not real.has_players(team):
                return None
            chart, roles, _squad = real.chart(team)
        except Exception as exc:                    # a damaged rosters file: substitutions by place only
            log.warning("substitutions: the real chart of team %d cannot be read: %s", team, exc)
            return None
        positions, order = {}, {}
        for position, written in chart.items():
            spoken = [real.spoken(name) for name in written]
            order[position] = spoken
            for name in spoken:
                positions.setdefault(name.casefold(), position)
        turns = []
        roles = roles or {}
        for i in range(max((len(roles.get(r, ())) for r in RM.ROLES), default=0)):
            for role in RM.ROLES:
                if i < len(roles.get(role, ())):
                    turns.append(real.spoken(roles[role][i]))
        return positions, order, turns

    def quick_lineup(self, state, side: int = 1):
        """(base, bench, empty) of a side in a quick game or a season; None when its roster is not whole."""
        found = self.quick_lineup_and_spares(state, side)
        return found[:3] if found is not None else None

    def quick_lineup_and_spares(self, state, side: int = 1):
        """(base, bench, empty, the returners' keys in turn) of a side in a quick game or a season; None when its roster is not whole."""
        names = self.read_names(state, side)
        if names is None:
            return None
        snap = self.snap[side]
        if snap[0] != id(state) or snap[2] is None or names != snap[2]:
            snap[0], snap[1] = id(state), list(names)       # the game's own names (a loaded game, a new set-up)
        names = snap[1]
        roster = state.rosters[side]
        empty = set()
        for heading, number in getattr(roster, "empty", ()) or ():
            if heading in EMPTY_HEADINGS and 1 <= number <= 6:
                empty.add(EMPTY_HEADINGS[heading] + number - 1)
        seen = set()
        for place in S.FIELD:                       # a name said twice in the offense and defense is a cover of an empty place (SR.4)
            key = names[place].casefold()
            if not names[place] or key in seen:
                empty.add(place)
            seen.add(key)
        chart = self.real_chart(side)
        positions, order, turns = chart if chart is not None else ({}, {}, [])
        real_men = sum(1 for p in S.FIELD if p not in empty and names[p].casefold() in positions)
        if real_men * 2 < len([p for p in S.FIELD if p not in empty]):
            positions, order, turns = {}, {}, []    # the side's names are not the real roster's (the original's names, a season file's own)
        base = []
        for place, name in enumerate(names):
            if place in empty:
                base.append(S.Man(None, name))
                continue
            position = "QB" if place == S.QUARTERBACK else positions.get(name.casefold(), "")
            if not position:
                group = S.GROUP_OF_PLACE[place]
                position = S.group_position("RB" if group == "RET" else group)
            base.append(S.Man(name, name, position))
        in_field = {names[p].casefold() for p in S.FIELD if p not in empty}
        bench, listed = [], set()
        for position in RM.MADDEN:
            for name in order.get(position, ()):
                if name.casefold() in in_field or name.casefold() in listed or position in ("LT", "LG", "C", "RG", "RT", "LS"):
                    continue
                listed.add(name.casefold())
                bench.append(S.Man(name, name, position))
        keys = {man.key.casefold(): man.key for man in list(base) + bench if man.movable}
        spares = [keys[name.casefold()] for name in turns if name.casefold() in keys]
        return base, bench, empty, spares

    # ----- the lineup: a franchise game -----

    def lineup(self, state):
        """(base, bench, empty) of the player's side now; None when there is none to change."""
        injuries = self.rules.game_injuries()
        if injuries is not None:
            found = getattr(injuries, "sub_lineup", None)
            return found if found is not None and found[0] else None
        return self.quick_lineup(state)

    # ----- the engine's lineup -----

    def apply(self, state, why: str, side: int = 1) -> None:
        """Make the engine's lineup of a side again from the record (the player's side) or the rest (the computer's side, Q-085); a franchise game
        through its injuries' refresh."""
        record = self.record(state) if side == 1 else self.rest_record(state)
        formation = self.formation if side == 1 else None
        if side == 1:
            self.applied = self.formation
        injuries = self.rules.game_injuries()
        if injuries is not None:
            if side == 1:
                injuries.sub_formation = formation
            if injuries.state is not None:
                injuries.refresh(side)
            return
        found = self.quick_lineup_and_spares(state, side)
        if found is None:
            return
        base, bench, empty, spares = found
        table, dropped = S.effective(base, bench, record, empty, formation, spares)
        names = [man.name if man is not None else "" for man in table]
        self.write_names(state, names, side)
        snap = self.snap[side]
        snap[2] = list(names)
        debuglog.event("subs", "lineup", side=side, why=why, backups=bool(record and record["backups"]),
                       game=len(record["game"]) if record else 0, play=len(record["play"]) if record else 0, formation=formation,
                       package=len(S.package_rows(record, formation)) or None, dropped=dropped or None,
                       changed=[(p, snap[1][p], names[p]) for p in range(S.PLACE_COUNT) if names[p] != snap[1][p]] or None)

    @staticmethod
    def rest_record(state) -> dict | None:
        """Q-085 (D-236): the computer side's record: all its backups in while it rests its starters, else nothing."""
        if not getattr(getattr(state, "extras", None), "computer_rest", None):
            return None
        record = S.new_record()
        record["backups"] = True
        return record

    def ensure(self, state, why: str) -> None:
        """The play menus, the kick-off and the end of a play: a next-play substitution whose play was run ends; the lineup is made again when the
        record changed or the game gave the roster its own names again (a quick game). Nothing at all while the player changed nothing."""
        record = self.record(state)
        if record is None:
            return
        changed = False
        extras = state.extras
        self.formation = None                        # Q-086: between plays and at a kick no package plays
        if self.applied is not None and S.package_rows(record, self.applied):
            changed = True
        if record["play"] and extras.plays > record["at"]:
            if getattr(extras, "no_snap", False):
                record["at"] = extras.plays          # a foul before the snap: the down is played again with the same men
            else:
                debuglog.event("subs", "next_play_over", places=[row[0] for row in record["play"]], plays=extras.plays)
                record["play"] = []
                changed = True
        if self.rules.game_injuries() is not None:
            if changed:
                self.apply(state, why)
            return
        names = self.read_names(state)
        if changed or (names is not None and names != self.written and not S.is_empty(record)):
            self.apply(state, why)
        self.applied = None

    # ----- Q-086 (D-235): the package of the play called -----

    def formation_of(self, state) -> str | None:
        """The package key (subs.PACKAGES) of the player's play called now: on offense the formation it lines up in, on defense its package of
        defensive backs as played; None for a play of the original's menus (no catalog call). A punt is the punt team's (the player punts) or
        the punt return team's (the computer punts), the player's field goal the field goal team's (Q-097, D-241); the computer's field goal has
        none. No draw."""
        rules = self.rules
        extras = state.extras
        kick = getattr(state, "offense_play", 0)
        if kick == PUNT_PLAY:
            return "K:punt" if state.wisoff == 1 else "K:punt_return"
        if kick == FIELD_GOAL_PLAY:
            return "K:field_goal" if state.wisoff == 1 else None
        settings = getattr(extras, "play_settings", None) or {}
        if state.wisoff == 1:
            concept = C.BY_ID.get(getattr(rules.offense, "called", ""))
            if concept is None or concept.side != "O":
                return None
            chosen = settings.get("formation", "book")
            formation = concept.formation if chosen in ("book", "", None) else chosen
            return "O:" + (formation if formation in S.OFFENSE_FORMATIONS else "other")
        call = C.BY_ID.get(getattr(rules.defense, "called", ""))
        if call is None or call.side != "D":
            return None
        offense = rules.defense.offense_concept(state)
        played = personnel.adjust(call.params, offense.personnel, to_goal(state), settings.get("defense_personnel", personnel.MATCH),
                                  settings.get("coverage_shade", personnel.BOOK))
        return "D:" + S.PACKAGE_OF_BACKS.get(played.backs, "base")

    def before_snap(self, state) -> None:
        """NflRules.before_snap: the plays are called; the package of the player's formation comes in (nothing when he set none)."""
        record = self.record(state)
        if record is None:
            return
        self.formation = self.formation_of(state)
        if S.package_rows(record, self.formation) or (self.applied is not None and S.package_rows(record, self.applied)):
            self.apply(state, "package")
            debuglog.event("subs", "package", formation=self.formation, men=len(S.package_rows(record, self.formation)))

    def kick_package(self, state, key: str | None) -> None:
        """Q-097 (D-241): a kick that is not a snapped play from the menus: the kick-off (the kick-off team or the kick return team, by the side
        that kicks) and the player's kicked try (the field goal team). Its package comes in now; `ensure` takes it off after the play. A punt
        and a field goal come through `before_snap`. Nothing when no package is set."""
        record = self.record(state)
        if record is None or key == self.formation:
            return
        self.formation = key
        if S.package_rows(record, key) or (self.applied is not None and S.package_rows(record, self.applied)):
            self.apply(state, "kick package")
            debuglog.event("subs", "package", formation=key, men=len(S.package_rows(record, key)))

    # ----- Q-085 (D-236): the computer rests its starters -----

    def rest(self, state, why: str) -> None:
        """Between plays and at a kick-off: the computer's side (2) rests its starters when it leads by a lot late in the game, and sends them back
        when the lead shrinks; one sentence each. No draw."""
        extras = getattr(state, "extras", None)
        if extras is None or 2 not in getattr(self.rules, "auto_sides", (2,)):
            return
        resting = bool(getattr(extras, "computer_rest", None))
        lead = state.score(2) - state.score(1)
        due = S.rest_due(resting, state.quarter, getattr(extras, "period", state.quarter) > 4, lead, extras.left)
        if due == resting:
            if resting and self.rules.game_injuries() is None:
                names = self.read_names(state, 2)
                if names is not None and names != self.snap[2][2]:
                    self.apply(state, why, side=2)      # the game gave the roster its own names again
            return
        extras.computer_rest = True if due else None
        self.apply(state, why, side=2)
        team = state.teams.get(2, "") if isinstance(getattr(state, "teams", None), dict) else ""
        self.game.say4(X.text("NXB-U29" if due else "NXB-U30", team=team))
        debuglog.event("subs", "computer_rest" if due else "computer_starters_back", quarter=state.quarter, lead=lead, left=extras.left)

    # ----- the words -----

    @staticmethod
    def position_word(position: str) -> str:
        if position in RM.MADDEN:
            from .lineup import word
            return word(position)
        return ""

    @staticmethod
    def label(place: int) -> str:
        group = S.GROUP_OF_PLACE[place]
        word = X.text(PLACE_WORDS[group])
        places = dict(S.GROUPS)[group]
        if len(places) == 1:
            return word
        return X.text("NXM-L36", position=word, n=places.index(place) + 1)

    def man_text(self, man) -> str:
        word = self.position_word(man.position)
        return X.text("NXB-T05", player=man.name, position=word) if word else man.name

    def place_text(self, table: list, place: int, record) -> str:
        man = table[place]
        name = man.name if man is not None else ""
        word = self.position_word(man.position) if man is not None else ""
        text = X.text("NXB-U07", label=self.label(place), player=name, position=word) if word else X.text("NXB-U06", label=self.label(place), player=name)
        if record and any(row[0] == place for row in record["play"]):
            text += X.text("NXB-U08")
        return text

    @staticmethod
    def describe(position: str) -> str:
        from .lineup import describe
        key = position if position in RM.MADDEN else DESCRIBE_GROUP.get(S.group_of(position), "")
        return describe(key) if key else ""

    # ----- the menus -----

    def menu(self, state):
        """U in the player's play menu."""
        if self.lineup(state) is None:
            debuglog.event("subs", "unavailable")
            return False
        debuglog.event("key", "subs_open", offense=state.wisoff == 1)
        current = 0
        while True:
            base, bench, empty = self.lineup(state)
            record = self.record(state)
            table, _dropped = S.effective(base, bench, record, empty)
            items = []
            if not (record and record["backups"]):
                items.append((("backups", None), X.text("NXB-U02"), ""))
            if S.changed_now(record):
                items.append((("starters", None), X.text("NXB-U03"), ""))
            for group, places in S.GROUPS:
                names = []
                for place in places:
                    man = table[place]
                    if place not in empty and man is not None and man.name and man.name not in names:
                        names.append(man.name)
                if names:
                    items.append((("group", group), X.text("NXB-U04", group=X.text(GROUP_WORDS[group]), list=", ".join(names)), group))
            sets = sum(1 for rows in (record or {}).get("packages", {}).values() if rows)
            items.append((("packages", None), X.text("NXB-U20", n=sets), ""))
            chosen = self.pick(state, X.text("NXB-U01", coach=self.coach()), items, current)
            if chosen is None:
                return MENU_REFRESH
            current, (kind, value) = chosen
            if kind == "backups":
                record = self.record(state, make=True)
                record["backups"], record["game"], record["play"] = True, [], []
                self.apply(state, "backups in")
                debuglog.event("subs", "backups_in")
                self.game.say5(X.text("NXB-U17"))
                current = 0
            elif kind == "starters":
                record = self.record(state, make=True)
                record.update(backups=False, game=[], play=[], at=0)       # the packages stay (D-235): they are standing choices
                self.apply(state, "starters back in")
                debuglog.event("subs", "starters_back")
                self.game.say5(X.text("NXB-U18"))
                current = 0
            elif kind == "packages":
                self.packages_menu(state)
            else:
                self.group_menu(state, value)

    def package_word(self, key: str) -> str:
        if key in PACKAGE_WORDS:
            return X.text(PACKAGE_WORDS[key])
        return X.text(SETTING_VALUE_TEXT[("formation", key[2:])])

    def packages_menu(self, state) -> None:
        """Q-086 (D-235): the offense's formations, then the defense's packages, each with how many men are set."""
        current = 0
        while True:
            record = self.record(state)
            packages = (record or {}).get("packages", {})
            items = []
            for key in S.PACKAGES:
                n = len(packages.get(key, ()))
                items.append((key, X.text("NXB-U27", formation=self.package_word(key), n=n) if n else
                              X.text("NXB-U28", formation=self.package_word(key)), ""))
            chosen = self.pick(state, X.text("NXB-U31"), items, current)
            if chosen is None:
                return
            current, key = chosen
            self.package_menu(state, key)

    def package_menu(self, state, key: str) -> None:
        """One formation's package: the groups as they play in it, and "Clear this package" when men are set."""
        current = 0
        word = self.package_word(key)
        while True:
            base, bench, empty = self.lineup(state)
            record = self.record(state)
            table, _dropped = S.effective(base, bench, self.package_only(record), empty, key)
            items = []
            if S.package_rows(record, key):
                items.append((("clear", None), X.text("NXB-U32"), ""))
            for group, places in S.GROUPS:
                names = []
                for place in places:
                    man = table[place]
                    if place not in empty and man is not None and man.name and man.name not in names:
                        names.append(man.name)
                if names:
                    items.append((("group", group), X.text("NXB-U04", group=X.text(GROUP_WORDS[group]), list=", ".join(names)), group))
            chosen = self.pick(state, X.text("NXB-U33", formation=word), items, min(current, len(items) - 1))
            if chosen is None:
                return
            current, (kind, value) = chosen
            if kind == "clear":
                S.clear_package(self.record(state, make=True), key)
                self.apply(state, "package cleared")
                debuglog.event("subs", "package_cleared", formation=key)
                self.game.say5(X.text("NXB-U34", formation=word))
                current = 0
            else:
                self.group_menu(state, value, package=key)

    @staticmethod
    def package_only(record):
        """The record as a package is edited: the base lineup and the package (the substitutions of now are not part of it)."""
        if not record:
            return record
        return {"backups": False, "game": [], "play": [], "at": 0, "packages": record.get("packages", {})}

    def coach(self) -> str:
        season = getattr(self.game, "season", None)
        return getattr(season, "coach", "") or ""

    def group_menu(self, state, group: str, package=None) -> None:
        current = 0
        while True:
            base, bench, empty = self.lineup(state)
            record = self.record(state)
            if package is None:
                table, _dropped = S.effective(base, bench, record, empty)
            else:
                table, _dropped = S.effective(base, bench, self.package_only(record), empty, package)
            places = [p for p in dict(S.GROUPS)[group] if p not in empty and table[p] is not None]
            if not places:
                return
            items = [(p, self.place_text(table, p, record), S.place_position(table, p)) for p in places]
            chosen = self.pick(state, X.text("NXB-U05"), items, min(current, len(items) - 1))
            if chosen is None:
                return
            current, place = chosen
            self.place_menu(state, place, package)

    def place_menu(self, state, place: int, package=None) -> None:
        base, bench, empty = self.lineup(state)
        record = self.record(state)
        if package is None:
            table, _dropped = S.effective(base, bench, record, empty)
        else:
            table, _dropped = S.effective(base, bench, self.package_only(record), empty, package)
        old = table[place]
        found = S.candidates(table, bench, place, empty)
        if not found:
            self.game.say5(X.text("NXB-U19"))
            return
        items = []
        for man, where in found:
            status = X.text("NXB-U10", label=self.label(where)) if where is not None else X.text("NXB-U11")
            items.append((man, self.man_text(man) + status, man.position))
        chosen = self.pick(state, X.text("NXB-U09", label=self.label(place), player=old.name if old is not None else ""), items, 0)
        if chosen is None:
            return
        man = chosen[1]
        if package is not None:                          # Q-086: a package has no "how long": every play of the formation
            S.add_package(self.record(state, make=True), package, place, man.key)
            self.apply(state, "package")
            debuglog.event("subs", "package_set", formation=package, place=place, player=man.name, out=old.name if old is not None else "",
                           position=man.position)
            self.game.say5(X.text("NXB-U35", player=man.name, old=old.name if old is not None else "", formation=self.package_word(package)))
            return
        how = self.pick(state, X.text("NXB-U12", player=man.name, old=old.name if old is not None else ""),
                        [("play", X.text("NXB-U13"), ""), ("game", X.text("NXB-U14"), "")], 0)
        if how is None:
            return
        kind = how[1]
        record = self.record(state, make=True)
        S.add(record, kind, place, man.key)
        if kind == "play":
            record["at"] = state.extras.plays
        self.apply(state, "substitution")
        debuglog.event("subs", "substitution", place=place, kind=kind, player=man.name, out=old.name if old is not None else "",
                       position=man.position, plays=state.extras.plays)
        self.game.say5(X.text("NXB-U15" if kind == "play" else "NXB-U16", player=man.name, old=old.name if old is not None else ""))

    def pick(self, state, prompt: str, items: list, current: int):
        """The list in the original's style (as the receiver list, choices.Choices.choose): the prompt, then the current item; Up and Down move and go
        around, Home and End, a digit chooses, Enter takes it, Escape leaves (None); D says what the item's position does; F1 says the prompt again
        (and takes back a T key, which calls a time out here as anywhere: a time out leaves the list); F2 to F4 as in a play menu; any other key is
        echoed. `items`: (value, text, position for D). Returns (index, value) or None."""
        g, keys = self.game, self.game.keys
        current = max(0, min(current, len(items) - 1))
        prompt_due = True
        while True:
            if prompt_due:
                keys.clk()
                g.say5(prompt)
                prompt_due = False
            g.say5(" %d. %s " % (current + 1, items[current][1]))
            if g.sounds.play_noise_running():
                g.sounds.stop_play_noise()
            keys.getkey2(g.speech, g.sounds)
            code = keys.code_text
            if code == KEY_ENTER:
                return current, items[current][0]
            if code == KEY_ESCAPE:
                return None
            if code == KEY_UP:
                current = (current - 1) % len(items)
                continue
            if code == KEY_DOWN:
                current = (current + 1) % len(items)
                continue
            if code == KEY_HOME:
                current = 0
                continue
            if code == KEY_END:
                current = len(items) - 1
                continue
            if code == KEY_F1:
                if keys.take_resumed() == TIMEOUT_GRANTED:
                    return None                          # a time out was called: back to the play menu
                prompt_due = True
                continue
            if code == KEY_F2:
                g.inrep()
                prompt_due = True
                continue
            if code == KEY_F3:
                g.say_score(state.score(1), state.score(2))
                continue
            if code == KEY_F4:
                self.rules.clock.speak()
                continue
            keypad = code.isdigit() and 96 <= int(code) <= 105
            char = keys.char.lower() if len(keys.char) == 1 else ""
            digit = int(code) - 96 if keypad else (int(char) if char.isdigit() else -1)
            if 1 <= digit <= len(items):
                current = digit - 1
                continue
            if char == "d" and not keypad:
                text = self.describe(items[current][2])
                if text:
                    debuglog.event("key", "describe_position", position=items[current][2])
                    g.voice_speak(text, wait=False)
                    continue
            g.saykey()
            prompt_due = True


# ----- a franchise game (called by franchise/injury_flow.GameInjuries.refresh for the player's side) -----

def franchise_apply(injuries, table: list, side: int = 1) -> list:
    """The lineup rows (identity, name, rating) of a side with its substitutions: the player's record (side 1) or the computer's rest (side 2,
    Q-085). Keeps (base, bench, empty) of the player's side on `injuries` for the menu. With no record the rows come back unchanged."""
    from .franchise import injuries as I
    from .franchise import data as D
    from .franchise.injury_flow import game_returners
    league = injuries.league
    team = injuries.teams[side - 1]
    out_now = injuries.out(side)
    base, empty, seen = [], set(), set()
    for place, row in enumerate(table):
        identity, name, rating = row
        if isinstance(identity, int) and (place not in S.FIELD or identity not in seen):
            player = league.players.get(identity)
            position = (player.position or S.group_position(player.pos)) if player is not None else ""
            base.append(S.Man(identity, name, position, rating))
            if place in S.FIELD:
                seen.add(identity)
            continue
        if identity == I.EMPTY or (isinstance(identity, int) and place in S.FIELD):
            empty.add(place)                        # an empty back place, or the next man up who plays two places (a cover)
        base.append(S.Man(None, name, S.group_position(identity[1]) if isinstance(identity, tuple) and len(identity) == 2 else "", rating, row))
    in_table = {man.key for man in base if man.movable}
    bench = []
    for player in league.bench(team):
        if player.id in in_table or player.id in out_now or player.team != team or player.status != "active":
            continue
        if not I.plays(league, player, injuries.week, injuries.staff_of(side), out_now):
            continue
        rating = max(D.RATING_MIN, player.rating - I.penalty(league, player.id, injuries.week))
        bench.append(S.Man(player.id, player.name, player.position or S.group_position(player.pos), rating))
    if side == 1:
        injuries.sub_lineup = (base, bench, empty)
        record = getattr(injuries.state.extras, "subs", None) if injuries.state is not None else None
        formation = getattr(injuries, "sub_formation", None)
    else:
        record = SubsFlow.rest_record(injuries.state) if injuries.state is not None else None
        formation = None
    if S.is_empty(record):
        return table
    spares = []
    if record.get("backups"):                           # Q-087: the team's next returners, fit for this game (the first two return now)
        spares = [row[0] for row in game_returners(league, team, injuries.week, injuries.staff_of(side), out_now, count=8)]
    lineup, dropped = S.effective(base, bench, record, empty, formation, spares)
    rows = []
    for place, man in enumerate(lineup):
        if man is not None and man.movable and place not in empty:
            rows.append((man.key, man.name, man.rating))
        elif place in empty and man is not None:
            identity = table[place][0]
            key = identity if identity == I.EMPTY or not man.movable else man.key
            rows.append((key, man.name, table[place][2]))
        else:
            rows.append(man.row if man is not None and man.row is not None else table[place])
    debuglog.event("subs", "franchise_lineup", side=side, formation=formation, backups=record["backups"], game=len(record["game"]), play=len(record["play"]), dropped=dropped or None,
                   changed=[(p, table[p][1], rows[p][1]) for p in range(S.PLACE_COUNT) if rows[p][0] != table[p][0]] or None)
    return rows
