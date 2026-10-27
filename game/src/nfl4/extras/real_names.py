"""The real head coaches and rosters of the 32 teams, and how they are said (nfl4 only, rule 0.13; CLAUDE.md 0.19, NX-N1 to NX-N7). This is inspired by Jim Kitchen.

SX.11 (D-098). The player types no name: with the N. F. L. rules the coach of the team the player chooses, the players of both teams and the two
quarterbacks come from three customization files (playbook 7.9, 7.10), shipped as the built-in values in `assets/data` and copied to the player's
customize folder:

    coaches.txt       VERSION = season 2026, as of 2026-10-22      T01 = Zac Taylor      (one head coach for each of T01 to T32)
    rosters.txt       T01P01 = QB 9 Joe Burrow                      (a team's players in depth order, then its returners as RET)
                      T01P70 = PS WR 14 Jordan Moore                (since 2026-10-24, NX-B2: the practice squad; OL and LS are on the active roster)
    respellings.txt   R001 = Jr. => Junior                          (how the voice says a written name or a word of it)
    free_agents.txt   F001 = WR 32 Tyreek Hill                      (NX-B3: the real free agents a new franchise starts with: position, age, name)

Facts only: names, teams, positions and numbers (no ratings, no photographs, no logos); the numbers are kept in the file and are never spoken.
A team's lines in the player's rosters.txt replace that team's built-in lines as a whole (a new season is a new file, an old player must not come
back from the built-in copy); a coach, the VERSION line and a respelling replace the built-in one with the same ID. Nothing here raises: a line the
rules refuse is a problem (one spoken summary per file) and the built-in value is used.

The 53-man file (2026-10-24, D-144, NX-B2; "it should be using the current 53 man rosters for each team"): every player of the active 53, the offensive
linemen (OL) and the long snapper (LS) too, then the practice squad, each line marked PS. The game plays no OL or LS place and no practice squad player:
`_assemble`, `quarterback` and the quarterbacks' list read the active players of the positions the game plays, exactly as with the older file, so a game
draws and names the same with either file; the Franchise reads the practice squads (`squad`). An older file (the player's own) is read as it always was; the list syntax is the same (format 1).

Layout 2 (SR.2, D-152, NX-L1 and NX-L2; extras/roster_file.py): the positions are Madden NFL's 22 (QB HB FB WR TE LT LG C RG RT LEDG REDG DT SAM MIKE
WILL CB FS SS K P LS), a line may start with a list (PS, or a reserve list such as IR), and the return roles are lines of their own (T17KR1 = a name).
Until SR.4 builds the real roster model the engine still plays the original's groups: `RealPlayer.pos` is the group (HB is RB, LT is OL, LEDG is DL,
SAM is LB, FS is S) and `RealPlayer.madden` keeps the real position; a team's active men are put in the order its groups take them (the starters of
every position first, roster_file.group_order), its returners become RET lines after the active roster as in format 1, and the men of a reserve
list are kept apart in `RealNames.reserves` (on the team, never in a game). A format-1 file is read as it always was.

`RealNames.roster(team, fallback)` makes the 33 names of the set-up (the original's sections: 6 running backs, 6 receivers, 17 defensive players,
2 returners, 2 kickers) from a team's real players; a place with no real player keeps the name of `fallback` (the names the original's draw has made,
so the draws of a game are the same with or without real names). `places(team)` is the same for the Franchise's 34 places.
"""
from __future__ import annotations

import dataclasses
import logging
import os
import re
from dataclasses import dataclass

from ..data import customlists as cl
from ..data import paths
from ..game.setup import COUNTS, Roster
from . import roster_file as RF
from .franchise import data as D

log = logging.getLogger("nfl4.extras")

GAME = "NFL Football 4"
COACHES, ROSTERS, RESPELLINGS = "coaches", "rosters", "respellings"
FREE_AGENTS = "freeagents"            # NX-B3 (D-145): free_agents.txt
NFL_SURNAMES = "nflsurnames"          # NX-L12 (D-163, D-164): nfl_surnames.txt, the real NFL players' last names of the made-up players
FILE_NAMES = {COACHES: "coaches.txt", ROSTERS: "rosters.txt", RESPELLINGS: "respellings.txt", FREE_AGENTS: "free_agents.txt",
              NFL_SURNAMES: "nfl_surnames.txt"}
KINDS = (COACHES, ROSTERS, RESPELLINGS, FREE_AGENTS, NFL_SURNAMES)
TEAMS = 32
POSITIONS = ("QB", "RB", "FB", "WR", "TE", "DL", "LB", "CB", "S", "K", "P", "RET", "OL", "LS")      # OL and LS: the 53-man file (NX-B2), no place in a game
SQUAD_MARK = "PS"                     # the 53-man file: a practice squad player's line starts with it
NAME_MIN, NAME_MAX = 1, 30

_COACH_ID = re.compile(r"T(\d{1,2})", re.IGNORECASE)
_PLAYER_ID = re.compile(r"T(\d{1,2})P(\d{1,3})", re.IGNORECASE)
_ALL_POSITIONS = tuple(sorted(set(POSITIONS) | set(RF.MADDEN), key=len, reverse=True))       # format 1's words and layout 2's positions
_PLAYER_VALUE = re.compile(r"^(?:(%s)\s+)?(%s)\s+(\d{1,2}|-)\s+(.+)$" % ("|".join(sorted(RF.STATUSES, key=len, reverse=True)), "|".join(_ALL_POSITIONS)),
                           re.IGNORECASE)
_ROLE_ID = re.compile(r"T(\d{1,2})(KR|PR)(\d)", re.IGNORECASE)
_RESPELL_ID = re.compile(r"R(\d{1,4})", re.IGNORECASE)
_FREE_ID = re.compile(r"F(\d{1,4})", re.IGNORECASE)
_SURNAME_ID = re.compile(r"S(\d{1,5})", re.IGNORECASE)
# D-185: a free agent's position is one of the 22 of a real roster (HB, LT, LEDG, MIKE, FS, ...) or an older family word (RB, OL, DL, LB, S); the longer
# words first so that C does not take the start of CB
FREE_POSITIONS = tuple(sorted({p for p in POSITIONS if p != "RET"} | {"HB", "LT", "LG", "C", "RG", "RT", "LEDG", "REDG", "DT", "SAM", "MIKE", "WILL",
                                                                     "FS", "SS"}, key=lambda p: (-len(p), p)))
_FREE_VALUE = re.compile(r"^(%s)\s+(\d{1,2}|-)\s+(.+)$" % "|".join(FREE_POSITIONS), re.IGNORECASE)
_ARROW = "=>"



def name_problem(name: str) -> str | None:
    """None when the name passes the game's limits (CUSTOMIZABLE_CONTENT 10), else the plain reason."""
    if not NAME_MIN <= len(name) <= NAME_MAX:
        return "a name has %d to %d characters" % (NAME_MIN, NAME_MAX)
    if "," in name or ";" in name:
        return "a name cannot have a comma or a semicolon"
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return "a name cannot have a control character"
    if not any(c.isalpha() for c in name):
        return "a name needs at least one letter"
    return None


@dataclass(frozen=True)
class RealPlayer:
    pos: str
    number: str          # digits, or "-" when the player has none; kept for the file, never spoken
    name: str
    squad: bool = False  # the 53-man file: a player of the practice squad (no place in a game; the Franchise's squad)
    madden: str = ""     # layout 2: the real position (roster_file.MADDEN); "" for a format-1 line of a group word
    status: str = ""     # layout 2: "" active, "PS" the practice squad, or a reserve list (IR, PUP, ...): then the man is in RealNames.reserves
    age: int | None = None       # SR.7 (D-167): his real age on the file's date, None when the line gives none
    seasons: int | None = None   # SR.7: his NFL seasons before this one, None when the line gives none


@dataclass(frozen=True)
class RealFreeAgent:
    """NX-B3: a real free agent of free_agents.txt (facts only: no rating)."""
    pos: str
    age: int | None      # None when no source gave it
    name: str


@dataclass(frozen=True)
class RealNames:
    version: str
    coaches: tuple                      # 32 names ("" when a team has none)
    rosters: tuple                      # 32 tuples of RealPlayer, in file order
    respellings: tuple                  # ((ID, written, spoken), ...) in the order of the IDs
    free_agents: tuple = ()             # NX-B3: ((ID, RealFreeAgent), ...) in the order of the IDs
    reserves: tuple = ()                # layout 2: 32 tuples of RealPlayer on a reserve list (injured reserve and the like), never in a game
    roles: tuple = ()                   # layout 2 (SR.4): 32 dicts {"KR": [names], "PR": [names]}, the return roles in order (the player's choice laid over)
    surnames: tuple = ()                # NX-L12: ((ID, last name), ...) of nfl_surnames.txt in the order of the IDs
    # SR.6 (NX-L9, design 21.10): the VERSION line of rosters.txt ("season 2026, as of 2026-10-25"). `version` above is coaches.txt's line, which the
    # leagues of SR.4 and SR.5 took as their roster_version; the offer of newer rosters compares leagues with this one (franchise/roster_update.py)
    roster_version: str = ""

    def surname_pool(self) -> list:
        """NX-L12: the last names of real NFL players the made-up players take ([] when the file gives none)."""
        return [name for _ident, name in self.surnames]

    def real_full_names(self) -> frozenset:
        """NX-L12: the casefolded full names of the real men of the files (the rosters, their lists, the free agents): no made-up man takes one."""
        written = [p.name for roster in self.rosters for p in roster] + [p.name for team in self.reserves for p in team]
        written += [agent.name for _ident, agent in self.free_agents]
        return frozenset(n.casefold() for name in written for n in (name, self.spoken(name)))     # as written and as the league says it

    def reserve(self, team: int) -> list:
        """The team's men on a reserve list (layout 2), in file order; [] for a format-1 file."""
        return list(self.reserves[team - 1]) if self.reserves and 1 <= team <= TEAMS else []

    # ----- how a name is said -----

    def spoken(self, name: str) -> str:
        """The name as the voice should say it: every respelling whose written text is a whole word (or words) of the name, the longest
        written text first."""
        result = name
        for _, written, said in sorted(self.respellings, key=lambda row: -len(row[1])):
            result = re.sub(r"(?<!\S)%s(?!\S)" % re.escape(written), said.replace("\\", "\\\\"), result)
        return result

    # ----- the coaches -----

    def has_coaches(self) -> bool:
        return any(self.coaches)

    def coach(self, team: int) -> str:
        """The spoken name of team 1 to 32's head coach ("" when there is none)."""
        return self.spoken(self.coaches[team - 1]) if 1 <= team <= TEAMS and self.coaches[team - 1] else ""

    def public_names(self) -> frozenset:
        """Every real man's and head coach's name, as written and as spoken (casefolded): public facts the debug log never hides."""
        coaches = [c for c in self.coaches if c]
        return self.real_full_names() | frozenset(n.casefold() for c in coaches for n in (c, self.spoken(c)))

    def coach_choices(self) -> list:
        """(team, spoken name) of every team that has a coach, in the teams' order."""
        return [(team, self.coach(team)) for team in range(1, TEAMS + 1) if self.coaches[team - 1]]

    # ----- the players -----

    def has_players(self, team: int) -> bool:
        return 1 <= team <= TEAMS and bool(self.rosters[team - 1])

    def quarterback(self, team: int) -> str:
        """The spoken name of the team's first quarterback ("" when it has none); never a practice squad player."""
        for player in self.rosters[team - 1] if 1 <= team <= TEAMS else ():
            if player.pos == "QB" and not player.squad:
                return self.spoken(player.name)
        return ""

    def active(self, team: int) -> list:
        """The team's players of the active roster (the 53, not the practice squad), in file order."""
        return [player for player in self.rosters[team - 1] if not player.squad] if 1 <= team <= TEAMS else []

    def squad(self, team: int) -> list:
        """The team's practice squad players (the 53-man file), in file order; [] for an older file."""
        return [player for player in self.rosters[team - 1] if player.squad] if 1 <= team <= TEAMS else []

    def is_layout2(self, team: int) -> bool:
        """The team's lines carry the real positions (rosters.txt layout 2, SR.2): the view of the real roster plays them (SR.4)."""
        return 1 <= team <= TEAMS and any(p.madden for p in self.rosters[team - 1])

    def chart(self, team: int) -> tuple:
        """SR.4 (design 21.3, NX-L3): (the depth chart {position: [written names]} of the team's active men in line order, the return roles
        {"KR": [names in turn], "PR": []}, the practice squad's chart) of a layout-2 team. The order of the lines is the file's, with the player's
        chosen starters and depth charts laid over it (quarterbacks.with_starters, depth_chart.with_depth)."""
        from . import roster_model as RM
        lines = self.rosters[team - 1]
        active = [p for p in lines if not p.squad and p.pos != "RET"]
        squad = [p for p in lines if p.squad]
        position = {p.name: (p.madden or RM.WORD_POSITIONS.get(p.pos, ("",))[0]) for p in active + squad}
        chart = RM.ordered_positions([p.name for p in active], position.get)
        squad_chart = RM.ordered_positions([p.name for p in squad], position.get)
        given = self.roles[team - 1] if self.roles and isinstance(self.roles[team - 1], dict) else None
        if given:
            roles = {r: [n for n in given.get(r, ()) if n in position] for r in RM.ROLES}
        else:
            roles = {"KR": [p.name for p in lines if p.pos == "RET" and not p.squad], "PR": []}
        return chart, roles, squad_chart

    def view(self, team: int):
        """SR.4 (design 21.4): the engine's 34 places of a layout-2 team at full health (roster_model.View, the written names)."""
        from . import roster_model as RM
        chart, roles, squad = self.chart(team)
        return RM.make_view(chart, roles, squad=squad)

    def _assemble(self, team: int) -> dict:
        """The sections of a team's real players: lists of names, None where the team has no player for the place."""
        if self.is_layout2(team):
            return self._assemble_view(team)
        by: dict[str, list] = {pos: [] for pos in POSITIONS}
        for player in self.rosters[team - 1]:
            if not player.squad:                                 # NX-B2: the practice squad has no place in a game (OL and LS are never taken)
                by[player.pos].append(player.name)
        used: set[str] = set()

        def free(names):
            return [n for n in names if n.casefold() not in used]

        def take(names, count):
            out = []
            for name in names:
                if len(out) == count:
                    break
                if name.casefold() not in used:
                    used.add(name.casefold())
                    out.append(name)
            return out

        kickers = [(take(by["K"], 1) or [None])[0], (take(by["P"], 1) or [None])[0]]
        # the running backs and fullbacks first (tester, 2026-10-23: "wrong position players are still playing at running back"): a returner is
        # listed again as RET with the name of his RB line, so taking the returners first cost 23 teams' backs one of their real backs
        # NX-D1 (D-147, the owner 2026-10-24: "A backup quarterback should not be playing wide receiver"): every place takes only players of its own
        # position, in depth order; a place the team has no more real players for stays None, so the set-up keeps the draw's name there (a made-up
        # player of that position). The returners come last: the chart's returners not already in a place, then the backs, receivers and cornerbacks
        # left over (a returner is a role of those positions), else made-up. Before: the returners were taken first and a short group was filled
        # from other positions (the Bears' backup quarterback at receiver, linebackers at defensive line, safeties at cornerback).
        backs = take(by["RB"] + by["FB"], COUNTS[0])
        wide, tight = list(by["WR"]), list(by["TE"])
        mixed = []                                               # WR1, WR2, WR3, TE1, WR4, TE2, WR5, TE3, ...
        while wide or tight:
            for _ in range(3 if not mixed else 1):
                if wide:
                    mixed.append(wide.pop(0))
            if tight:
                mixed.append(tight.pop(0))
        receivers = take(mixed, COUNTS[1])
        defenders = {pos: take(by[pos], count) for pos, count in (("DL", 6), ("LB", 5), ("CB", 4), ("S", 2))}
        returners = take(by["RET"], COUNTS[3])
        if len(returners) < COUNTS[3]:
            returners += take(free(by["RB"] + by["FB"]) + free(mixed) + free(by["CB"]), COUNTS[3] - len(returners))
        defense = []
        for pos, count in (("DL", 6), ("LB", 5), ("CB", 4), ("S", 2)):
            defense += defenders[pos] + [None] * (count - len(defenders[pos]))
        quarterback = (by["QB"] or [""])[0]

        def pad(names, count):
            return list(names[:count]) + [None] * (count - len(names))

        return {"running_backs": pad(backs, COUNTS[0]), "receivers": pad(receivers, COUNTS[1]), "defense": pad(defense, COUNTS[2]),
                "special_teams": pad(returners, COUNTS[3]), "kickers": pad(kickers, COUNTS[4]), "quarterback": quarterback}

    def _assemble_view(self, team: int) -> dict:
        """SR.4 (NX-L3, design 21.4 and 21.5): the sections from the view of the team's chart. An empty place (a team with three backs has no fourth)
        takes the name of the nearest filled place of its section, so the original's uniform draws name a real man of the team and the usage draw
        gives the repeated name no share (usage.without_repeats); a section with nobody at all keeps None (the drawn name stands in for that game)."""
        from . import roster_model as RM
        view = self.view(team)
        names = []
        for index, man in enumerate(view.places):
            man = man if man is not None else view.cover(index)
            names.append(man)
        if view.empty or view.covered or view.elevated:
            from ..data import debuglog
            debuglog.event("names", "roster_view", logging.DEBUG, team=team, empty=view.empty, covered=sorted(view.covered.items()),
                           elevated=view.elevated)                       # design 21.11 (rule 0.15)
        return {"running_backs": names[0:6], "receivers": names[6:12], "defense": names[12:29], "special_teams": names[29:31],
                "kickers": [names[RM.KICKER], names[RM.PUNTER]], "quarterback": names[RM.QUARTERBACK] or ""}

    def roster(self, team: int, fallback: Roster | None = None) -> Roster | None:
        """The 33 names of the set-up from a team's real players, spoken forms; a place with no real player keeps `fallback`'s name (the one
        the draw made). None when the team has no players. The quarterback is not set (Getqbs asks for him, with `quarterback` as its default)."""
        if not self.has_players(team):
            return None
        sections = self._assemble(team)
        result = Roster()
        if self.is_layout2(team):                       # SR.4: the view's empty places (their cover's name, no share of the usage draw)
            view = self.view(team)
            result.empty = [(("Running Backs:", "Receivers:")[i >= 6], i % 6 + 1) for i in view.empty if i < 12]
        for attribute, count in zip(("running_backs", "receivers", "defense", "special_teams", "kickers"), COUNTS):
            drawn = getattr(fallback, attribute) if fallback is not None else []
            names = []
            for index in range(count):
                real = sections[attribute][index]
                names.append(self.spoken(real) if real else self.last_resort(drawn[index] if index < len(drawn) else "player"))
            getattr(result, attribute).extend(names)
        return result

    def last_resort(self, drawn: str) -> str:
        """NX-L12 (D-164): the name of a place no real man of the team can play (a family with nobody, design 21.4 (8)): the draw made the original's
        surname as ever (the same draws); the name said is a real NFL player's last name chosen from it (no draw) with a first name of the game's list
        that makes no real player's full name."""
        pool = self.surname_pool()
        if not pool or not drawn:
            return drawn
        import zlib
        from .franchise import first_names as FN
        surname = pool[zlib.crc32(drawn.encode("utf-8", "surrogatepass")) % len(pool)]
        return FN.full_name("quick game", surname)

    def places(self, team: int) -> list:
        """The names of the Franchise's 34 places (franchise.data.PLACES: the sections, then the quarterback) from a team's real players, spoken
        forms; None where the team has no player for the place (the league keeps the name it drew)."""
        if not self.has_players(team):
            return [None] * D.PLACE_COUNT
        sections = self._assemble(team)
        headings = {"Running Backs:": "running_backs", "Receivers:": "receivers", "Defensive Players:": "defense",
                    "Special Teams Players:": "special_teams", "Kickers:": "kickers"}
        out = []
        for heading, number, position in D.PLACES:
            if heading == "Quarterback:":
                name = sections["quarterback"]
            else:
                name = sections[headings[heading]][number - 1]
            out.append(self.spoken(name) if name else None)
        return out


# ----- the built-in values (the shipped files) -----

def shipped_path(kind: str) -> str:
    return os.path.join(paths.program_dir(), "assets", "data", FILE_NAMES[kind])


def shipped_text(kind: str) -> str:
    """The text of a shipped file, the built-in copy that the player's file starts as. Raises when the asset cannot be read."""
    with open(shipped_path(kind), "r", encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def parse_entries(text: str, kind: str):
    return cl.parse_list(text, GAME, kind)


def build(coach_entries, roster_entries, respell_entries, defaults: "RealNames | None", problems: dict, free_entries=(),
          surname_entries=()) -> "RealNames":
    """The values of the three files. `defaults` is the built-in RealNames (None for the built-in one itself); `problems` maps each kind to
    a customlists.Problems. A bad line keeps the built-in value."""
    base_version = defaults.version if defaults else ""
    base_coaches = list(defaults.coaches) if defaults else [""] * TEAMS
    base_rosters = list(defaults.rosters) if defaults else [()] * TEAMS
    base_respell = {row[0]: row for row in defaults.respellings} if defaults else {}

    version = base_version
    coaches = list(base_coaches)
    seen: set[int] = set()
    bad = problems[COACHES]
    for entry in coach_entries:
        if entry.id == "VERSION":
            version = entry.value or version
            continue
        match = _COACH_ID.fullmatch(entry.id)
        number = int(match.group(1)) if match else 0
        if not 1 <= number <= TEAMS:
            bad.add("line %d" % entry.line, "the ID %s is not a team, T01 to T32, the line is ignored" % entry.id)
        elif number in seen:
            bad.add(entry.id, "this ID is there twice, the first line is used")
        else:
            seen.add(number)
            reason = name_problem(entry.value)
            if reason:
                bad.add(entry.id, "%s, the built-in name is used" % reason)
            else:
                coaches[number - 1] = entry.value

    rosters = list(base_rosters)
    roster_version = defaults.roster_version if defaults else ""
    reserves = list(defaults.reserves) if defaults and defaults.reserves else [()] * TEAMS
    team_roles = list(defaults.roles) if defaults and defaults.roles else [{} for _ in range(TEAMS)]
    lines: dict[int, list] = {}
    roles: dict[int, dict] = {}
    bad = problems[ROSTERS]
    for entry in roster_entries:
        if entry.id == "VERSION":
            roster_version = entry.value or roster_version          # SR.6: the rosters' own date (NX-L9)
            continue
        role = _ROLE_ID.fullmatch(entry.id)
        if role is not None and 1 <= int(role.group(1)) <= TEAMS:
            reason = name_problem(entry.value.strip())
            if reason:
                bad.add(entry.id, "%s, the line is ignored" % reason)
            else:
                roles.setdefault(int(role.group(1)), {}).setdefault(role.group(2).upper(), []).append((int(role.group(3)), entry.value.strip()))
            continue
        match = _PLAYER_ID.fullmatch(entry.id)
        team = int(match.group(1)) if match else 0
        if not 1 <= team <= TEAMS:
            bad.add("line %d" % entry.line, "the ID %s is not a player, like T01P01, the line is ignored" % entry.id)
            continue
        parts = _PLAYER_VALUE.match(entry.value)
        if parts is None:
            bad.add(entry.id, "a player is a position, a number and a name, like QB 9 Joe Burrow, the line is ignored")
            continue
        status = (parts.group(1) or "").upper()
        squad = status == SQUAD_MARK
        code = parts.group(2).upper()
        if status and code == "RET":
            bad.add(entry.id, "a practice squad player is not a returner, the line is ignored")
            continue
        split = RF.split_age(parts.group(4))                 # SR.7 (D-167): "; age N; seasons N" after the name
        if split is None:
            bad.add(entry.id, "after the name only \"; age 24\" and \"; seasons 2\" may follow, the line is ignored")
            continue
        name, age, seasons = split
        reason = name_problem(name)
        if reason:
            bad.add(entry.id, "%s, the line is ignored" % reason)
            continue
        madden = code if code in RF.MADDEN else ""
        lines.setdefault(team, []).append((int(match.group(2)), entry.line, RealPlayer(RF.GROUP_OF.get(code, code), parts.group(3),
                                                                                       name, squad, madden, status, age, seasons)))
    for team, rows in lines.items():
        rows.sort(key=lambda row: (row[0], row[1]))          # by the number of the ID, then by the line: the file's own order is the depth order
        players = [player for _, _, player in rows]
        rosters[team - 1], reserves[team - 1] = _team_lines(players, roles.get(team))
        team_roles[team - 1] = {r: [name for _, name in sorted(roles.get(team, {}).get(r, []))] for r in ("KR", "PR")} if roles.get(team) else {}
    for team, given in roles.items():                         # role lines alone: the returners of a built-in (or earlier) team
        if team not in lines:
            kept = [p for p in rosters[team - 1] if p.pos != "RET" or p.squad]
            rosters[team - 1], _ = _team_lines(kept, given)
            team_roles[team - 1] = {r: [name for _, name in sorted(given.get(r, []))] for r in ("KR", "PR")}

    respell = dict(base_respell)
    bad = problems[RESPELLINGS]
    for entry in respell_entries:
        match = _RESPELL_ID.fullmatch(entry.id)
        if match is None:
            bad.add("line %d" % entry.line, "the ID %s is not a respelling ID, R001 and up, the line is ignored" % entry.id)
        elif entry.value.casefold() == "off":
            respell.pop(entry.id.upper(), None)
        elif _ARROW not in entry.value:
            bad.add(entry.id, "a respelling is the written text, an arrow => and what the voice speaks, the line is ignored")
        else:
            written, said = (part.strip() for part in entry.value.split(_ARROW, 1))
            if not written or not said:
                bad.add(entry.id, "a respelling needs both the written text and what the voice speaks, the line is ignored")
            else:
                respell[entry.id.upper()] = (entry.id.upper(), written, said)
    free = {row[0]: row for row in defaults.free_agents} if defaults else {}
    bad = problems.get(FREE_AGENTS)
    for entry in free_entries:                                    # NX-B3: laid over the built-in list by ID, "off" leaves one out
        if entry.id == "VERSION":
            continue
        match = _FREE_ID.fullmatch(entry.id)
        if match is None:
            bad.add("line %d" % entry.line, "the ID %s is not a free agent ID, F001 and up, the line is ignored" % entry.id)
            continue
        ident = "F%03d" % int(match.group(1))
        if entry.value.casefold() == "off":
            free.pop(ident, None)
            continue
        parts = _FREE_VALUE.match(entry.value)
        if parts is None:
            bad.add(entry.id, "a free agent is a position, an age and a name, like WR 32 Tyreek Hill, the line is ignored")
            continue
        reason = name_problem(parts.group(3).strip())
        if reason:
            bad.add(entry.id, "%s, the line is ignored" % reason)
            continue
        age = int(parts.group(2)) if parts.group(2).isdigit() else None
        free[ident] = (ident, RealFreeAgent(parts.group(1).upper(), age, parts.group(3).strip()))
    surnames = {row[0]: row for row in defaults.surnames} if defaults else {}
    bad = problems.get(NFL_SURNAMES)
    for entry in surname_entries:                                 # NX-L12: laid over the built-in list by ID, "off" leaves one out
        if entry.id == "VERSION":
            continue
        match = _SURNAME_ID.fullmatch(entry.id)
        if match is None:
            if bad is not None:
                bad.add("line %d" % entry.line, "the ID %s is not a surname ID, S00001 and up, the line is ignored" % entry.id)
            continue
        ident = "S%05d" % int(match.group(1))
        if entry.value.casefold() == "off":
            surnames.pop(ident, None)
            continue
        name = entry.value.strip()
        reason = name_problem(name) or (None if len(name) >= 2 else "a last name has at least 2 characters")
        if reason:
            if bad is not None:
                bad.add(entry.id, "%s, the line is ignored" % reason)
            continue
        surnames[ident] = (ident, name)
    built = RealNames(version, tuple(coaches), tuple(rosters), tuple(sorted(respell.values())),
                      tuple(sorted(free.values(), key=lambda row: int(row[0][1:]))), tuple(reserves), tuple(team_roles),
                      tuple(sorted(surnames.values(), key=lambda row: int(row[0][1:]))), roster_version)
    from ..data import debuglog
    debuglog.add_public_source(built.public_names)  # rule 0.15: the real men the game offers are named in the log, never <typed> (read lazily)
    return built


def _team_lines(players: list, roles: "dict | None"):
    """(the team's lines as the engine reads them, its reserve men). Layout 2 (a real position, roles): the active men in the order of the groups,
    the returners as RET lines after them (KR1, PR1, KR2, PR2, ...; each once, the number of his own line), then the practice squad."""
    reserve = tuple(p for p in players if p.status not in ("", SQUAD_MARK))
    playing = [p for p in players if p.status in ("", SQUAD_MARK)]
    real = any(p.madden and p.madden not in POSITIONS for p in playing) or bool(roles)
    if not real:
        return tuple(playing), reserve
    active = [p for p in playing if not p.squad and p.pos != "RET"]
    old_returners = [p for p in playing if not p.squad and p.pos == "RET"]
    squad = [p for p in playing if p.squad]
    if any(p.madden and p.madden not in POSITIONS for p in active):
        men = [RF.Man(p.madden or p.pos, p.number, p.name) for p in active]
        lookup = {id(m): p for m, p in zip(men, active)}
        active = [lookup[id(m)] for m in RF.group_order(men)]
    # SR.4 (D-161): the lent linebacker and the squad kicker moved to the active lines of SR.2 are gone: the view (roster_model.make_view) fills a 3-4
    # team's backer places with its spare edge men and elevates the squad's kicker for the game, each keeping his own position and list
    returners = old_returners
    if roles:
        numbers = {p.name.casefold(): p for p in active}
        ordered = {r: [name for _, name in sorted(roles.get(r, []))] for r in ("KR", "PR")}
        names: list = []
        for i in range(max(len(ordered["KR"]), len(ordered["PR"]))):
            for r in ("KR", "PR"):
                if i < len(ordered[r]) and ordered[r][i].casefold() in numbers and ordered[r][i].casefold() not in {n.casefold() for n in names}:
                    names.append(ordered[r][i])
        returners = [RealPlayer("RET", numbers[n.casefold()].number, numbers[n.casefold()].name) for n in names]   # every role man, in turn (SR.4)
    return tuple(active + returners + squad), reserve


def apply_kind(current: "RealNames", kind: str, entries, problems: "cl.Problems") -> "RealNames":
    """One file's entries laid over `current` (the built-in names at the start of a load): the part of the other two files stays as it is."""
    mine = {k: cl.Problems(FILE_NAMES[k]) for k in FILE_NAMES}
    mine[kind] = problems
    return build(entries if kind == COACHES else [], entries if kind == ROSTERS else [], entries if kind == RESPELLINGS else [],
                 current, mine, entries if kind == FREE_AGENTS else [], entries if kind == NFL_SURNAMES else [])


_DEFAULTS: "RealNames | None | bool" = False        # False: not read yet


def defaults() -> "RealNames | None":
    """The built-in names (the shipped files), read once; None when an asset cannot be read (the game then asks for typed names as the original)."""
    global _DEFAULTS
    if _DEFAULTS is False:
        try:
            problems = {kind: cl.Problems(FILE_NAMES[kind]) for kind in FILE_NAMES}
            parsed = {kind: parse_entries(shipped_text(kind), kind).entries for kind in (COACHES, ROSTERS, RESPELLINGS)}
            try:
                parsed[FREE_AGENTS] = parse_entries(shipped_text(FREE_AGENTS), FREE_AGENTS).entries
            except Exception:                                    # NX-B3: no free agents file never costs the names (made-up free agents, as before)
                log.exception("the shipped free agents file could not be read")
                parsed[FREE_AGENTS] = []
            try:
                parsed[NFL_SURNAMES] = parse_entries(shipped_text(NFL_SURNAMES), NFL_SURNAMES).entries
            except Exception:                                    # NX-L12: no surnames file never costs the names (the original's surnames, as before)
                log.exception("the shipped NFL surnames file could not be read")
                parsed[NFL_SURNAMES] = []
            _DEFAULTS = build(parsed[COACHES], parsed[ROSTERS], parsed[RESPELLINGS], None, problems, parsed[FREE_AGENTS], parsed[NFL_SURNAMES])
            if sum(p.count for p in problems.values()):
                log.warning("the shipped name files have problems: %s", [m for p in problems.values() for m in p.messages][:5])
        except Exception:
            log.exception("the shipped name files could not be read")
            _DEFAULTS = None
    return _DEFAULTS


def reset_defaults_cache() -> None:
    """For the tests: read the shipped files again."""
    global _DEFAULTS
    _DEFAULTS = False
