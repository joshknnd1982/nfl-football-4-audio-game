"""rosters.txt layout 2: the real rosters with Madden NFL's positions, read, checked and written (nfl4 only, rule 0.13; CLAUDE.md 0.32, NX-L1, NX-L2,
NX-L8; D-152 to D-156, SR.2). This is inspired by Jim Kitchen.

One module for the file so that the maintainer's script (game/tools/update_rosters.py) and the game's own "get the latest rosters" (NX-L9, SR.6) run
the SAME checks. Facts only: names, teams, positions, numbers, the list a man is on, and the kick and punt return roles. No ratings.

A line of the file:

    T17P01 = QB 18 Caleb Williams          an active player: position, jersey number (or -), name; the file order is the depth order of a position
    T17P56 = PS QB 16 Miller Moss          a practice squad player
    T17P75 = IR TE 85 Cole Kmet            a man on a reserve list (IR, IRD, PUP, NFI, SUS, PSI, ...): on the team, never in a game
    T17KR1 = Zavion Thomas                 the first kick returner (a role of an active man, never a position); PR1 the first punt returner

The positions are the 22 of EA's own Madden NFL 27 pages (D-152): QB HB FB WR TE LT LG C RG RT LEDG REDG DT SAM MIKE WILL CB FS SS K P LS.
`GROUP_OF` maps each to the original's group (RB, OL, DL, LB, S, ...) that the engine still plays until SR.4 (NX-L3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LAYOUT = 2              # the list syntax stays customlists' format 1
TEAMS = 32
MADDEN = ("QB", "HB", "FB", "WR", "TE", "LT", "LG", "C", "RG", "RT", "LEDG", "REDG", "DT", "SAM", "MIKE", "WILL", "CB", "FS", "SS", "K", "P", "LS")
GROUP_OF = {"QB": "QB", "HB": "RB", "FB": "FB", "WR": "WR", "TE": "TE", "LT": "OL", "LG": "OL", "C": "OL", "RG": "OL", "RT": "OL",
            "LEDG": "DL", "REDG": "DL", "DT": "DL", "SAM": "LB", "MIKE": "LB", "WILL": "LB", "CB": "CB", "FS": "S", "SS": "S",
            "K": "K", "P": "P", "LS": "LS"}
SPOKEN = {"QB": "quarterback", "HB": "halfback", "FB": "fullback", "WR": "wide receiver", "TE": "tight end", "LT": "left tackle",
          "LG": "left guard", "C": "center", "RG": "right guard", "RT": "right tackle", "LEDG": "left edge", "REDG": "right edge",
          "DT": "defensive tackle", "SAM": "strong-side linebacker", "MIKE": "middle linebacker", "WILL": "weak-side linebacker",
          "CB": "cornerback", "FS": "free safety", "SS": "strong safety", "K": "kicker", "P": "punter", "LS": "long snapper"}
# How many of a position start (the engine's group order takes the starters of every position first, then the backups tier by tier)
STARTERS = {"WR": 3, "DT": 2, "CB": 2}
ACTIVE, SQUAD = "", "PS"
# The lists a man can be on besides the active roster (the teams' pages' table headings, read raw in SR.1 and SR.2)
RESERVE = {"IR": "injured reserve", "IRD": "injured reserve, designated for return", "PUP": "physically unable to perform",
           "NFI": "non-football injury or illness", "SUS": "suspended", "PSI": "practice squad, injured", "EXM": "exempt",
           "RTD": "reserve, retired", "LFT": "reserve, left the squad", "MIL": "reserve, military", "PSX": "practice squad, exempt"}
STATUSES = (SQUAD,) + tuple(RESERVE)
ROLES = ("KR", "PR")
ACTIVE_MIN, ACTIVE_MAX, SQUAD_MAX = 46, 53, 17          # 2026: 53 from the cut-down, 16 + 1 International Pathway man (SR.2, section 4 of the research)
MUST_HAVE = ("QB", "K", "P", "LS")                       # NX-L8 (on the active roster, else on the practice squad: a warning)
NAME_MAX = 30

_PLAYER_ID = re.compile(r"T(\d{2})P(\d{2,3})")
_ROLE_ID = re.compile(r"T(\d{2})(KR|PR)(\d)")
_VALUE = re.compile(r"^(?:(%s)\s+)?(%s)\s+(\d{1,2}|-)\s+(\S.*)$" % ("|".join(sorted(STATUSES, key=len, reverse=True)),
                                                                   "|".join(sorted(MADDEN, key=len, reverse=True))))
# SR.7 (Q-078, D-167): after the name, optionally "; age N" (his age on the file's date) and "; seasons N" (his NFL seasons before this one). A name has
# no semicolon, so the first semicolon ends it. Facts from nflverse's roster table (birth date, rookie year).
_AGE_PART = re.compile(r"^(?P<name>[^;]*?)\s*(?:;\s*age\s+(?P<age>\d{1,2})\s*)?(?:;\s*seasons\s+(?P<seasons>\d{1,2})\s*)?$", re.IGNORECASE)
AGE_LOW, AGE_HIGH = 18, 50                               # the check's limits of a real player's age (the game then keeps its own 21 to 40)


def split_age(text: str):
    """(name, age or None, seasons or None) of a player's text after the number, or None when a part after a semicolon is not "age N" or "seasons N"."""
    found = _AGE_PART.match(text.strip())
    if found is None:
        return None
    age, seasons = found.group("age"), found.group("seasons")
    return found.group("name").strip(), int(age) if age else None, int(seasons) if seasons else None


@dataclass
class Man:
    pos: str            # one of MADDEN
    number: str         # digits or "-"
    name: str
    status: str = ""    # ACTIVE, SQUAD or a RESERVE kind
    age: int | None = None       # SR.7: his age on the file's date, None when the sources give none
    seasons: int | None = None   # SR.7: his NFL seasons before this one (0: a rookie), None when unknown


@dataclass
class Team:
    men: list = field(default_factory=list)                       # Man, in file order (actives in depth order by position, then the squad, then reserves)
    roles: dict = field(default_factory=lambda: {"KR": [], "PR": []})

    def active(self):
        return [m for m in self.men if m.status == ACTIVE]

    def squad(self):
        return [m for m in self.men if m.status == SQUAD]

    def reserves(self):
        return [m for m in self.men if m.status not in (ACTIVE, SQUAD)]


def name_problem(name: str) -> str | None:
    if not 1 <= len(name) <= NAME_MAX:
        return "a name has 1 to %d characters" % NAME_MAX
    if "," in name or ";" in name or "=" in name:
        return "a name cannot have a comma, a semicolon or an equals sign"
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return "a name cannot have a control character"
    if not any(c.isalpha() for c in name):
        return "a name needs at least one letter"
    return None


def parse(text: str):
    """(version, {team: Team}, problems) of a layout-2 text. Strict: every line that is not a comment, blank, the VERSION, a player or a role is a problem."""
    version, teams, problems = "", {}, []
    rows: dict[int, list] = {}
    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            problems.append("line %d has no equals sign" % number)
            continue
        ident, value = (part.strip() for part in line.split("=", 1))
        if ident.upper() == "VERSION":
            version = value
            continue
        player, role = _PLAYER_ID.fullmatch(ident), _ROLE_ID.fullmatch(ident)
        if player:
            team = int(player.group(1))
            parts = _VALUE.match(value)
            if not 1 <= team <= TEAMS or parts is None:
                problems.append("line %d (%s) is not a player of layout 2" % (number, ident))
                continue
            split = split_age(parts.group(4))
            if split is None:
                problems.append("line %d (%s): after the name only \"; age N\" and \"; seasons N\" may follow" % (number, ident))
                continue
            name, age, seasons = split
            reason = name_problem(name)
            if reason:
                problems.append("line %d (%s): %s" % (number, ident, reason))
                continue
            rows.setdefault(team, []).append((int(player.group(2)), Man(parts.group(2), parts.group(3), name, parts.group(1) or ACTIVE, age, seasons)))
        elif role:
            team = int(role.group(1))
            if not 1 <= team <= TEAMS:
                problems.append("line %d (%s) is not a team" % (number, ident))
                continue
            teams.setdefault(team, Team()).roles[role.group(2)].append((int(role.group(3)), value))
        else:
            problems.append("line %d: %s is not a player or a role ID" % (number, ident))
    for team, men in rows.items():
        teams.setdefault(team, Team()).men = [m for _, m in sorted(men, key=lambda r: r[0])]
    for team in teams.values():
        team.roles = {r: [name for _, name in sorted(team.roles.get(r, []))] for r in ROLES}
    return version, teams, problems


def check(teams: dict):
    """(failures, warnings) of a league of 32 teams (D-155, NX-L8). A failure means the file is not to be used."""
    fail, warn = [], []
    if sorted(teams) != list(range(1, TEAMS + 1)):
        fail.append("the file has teams %s, not T01 to T32" % sorted(teams))
    seen_name: dict[str, int] = {}
    for t in sorted(teams):
        team, tag = teams[t], "T%02d" % t
        active, squad = team.active(), team.squad()
        if not ACTIVE_MIN <= len(active) <= ACTIVE_MAX:
            fail.append("%s has %d active men (the limits are %d to %d)" % (tag, len(active), ACTIVE_MIN, ACTIVE_MAX))
        if len(squad) > SQUAD_MAX:
            fail.append("%s has %d men on the practice squad (at most %d)" % (tag, len(squad), SQUAD_MAX))
        for pos in MUST_HAVE:
            if not any(m.pos == pos for m in active):
                (warn if any(m.pos == pos for m in squad) else fail).append(
                    "%s has no %s on the active roster%s" % (tag, SPOKEN[pos], " (one on the practice squad)" if any(m.pos == pos for m in squad) else ""))
        names = {}
        for m in team.men:
            if m.pos not in MADDEN:
                fail.append("%s: %s has the unknown position %s" % (tag, m.name, m.pos))
            if m.status not in (ACTIVE,) + STATUSES:
                fail.append("%s: %s has the unknown list %s" % (tag, m.name, m.status))
            if not (m.number == "-" or (m.number.isdigit() and 0 <= int(m.number) <= 99)):
                fail.append("%s: %s has the number %r" % (tag, m.name, m.number))
            reason = name_problem(m.name)
            if reason:
                fail.append("%s: %r: %s" % (tag, m.name, reason))
            if m.age is not None and not AGE_LOW <= m.age <= AGE_HIGH:
                fail.append("%s: %s has the age %d" % (tag, m.name, m.age))
            if m.seasons is not None and (m.seasons < 0 or (m.age is not None and m.seasons > m.age - AGE_LOW)):
                fail.append("%s: %s has %d seasons at the age %s" % (tag, m.name, m.seasons, m.age))
            k = m.name.casefold()
            if k in names:
                fail.append("%s: %s is on the team twice" % (tag, m.name))
            names[k] = m
            if k in seen_name and seen_name[k] != t:
                warn.append("%s and T%02d both have a man called %s (two men, or one man twice: settle it)" % (tag, seen_name[k], m.name))
            seen_name.setdefault(k, t)
        active_names = {m.name.casefold() for m in active}
        for role in ROLES:
            for name in team.roles.get(role, []):
                if name.casefold() not in active_names:
                    fail.append("%s: the %s %s is not on the active roster" % (tag, role, name))
            if not team.roles.get(role):
                warn.append("%s has no %s" % (tag, role))
    return fail, warn


def group_order(active: list) -> list:
    """The active men in the order the engine's groups take them: within each position the file's depth order, and across the positions of a group
    the starters of each position first, then the second tier, and so on (LEDG1, REDG1, DT1, DT2, LEDG2, ...)."""
    index = {}
    keyed = []
    for i, m in enumerate(active):
        k = index.get(m.pos, 0)
        index[m.pos] = k + 1
        tier = k // STARTERS.get(m.pos, 1) + (1000 if m.pos == "FB" else 0)     # the back places take every halfback first, then the fullbacks (as before)
        keyed.append(((tier, MADDEN.index(m.pos) if m.pos in MADDEN else 99, k, i), m))
    return [m for _, m in sorted(keyed, key=lambda row: row[0])]


HEADER = """# NFL Football 4 rosters, format 1, layout 2: the real positions.
# These are the real players of the 32 teams: each team's active roster of up to 53, then its practice squad, then the men on a reserve list.
# Each line is an ID, an equals sign, the list (none for the active roster; PS the practice squad; IR injured reserve, IRD injured reserve and
# designated for return, PUP physically unable to perform, NFI non-football injury, SUS suspended, PSI practice squad injured), the position,
# the jersey number and the name. The number is a number, or a minus sign when the player has none.
# After the name, "; age 24" is his age on the date of the VERSION line and "; seasons 2" his NFL seasons before this one (0: a rookie); both may
# be left out, and a new franchise then gives him an age of its own. A new franchise gives every other man his real age and seasons.
# The positions are the positions of a real roster: QB quarterback, HB halfback, FB fullback, WR wide receiver, TE tight end, LT left tackle,
# LG left guard, C center, RG right guard, RT right tackle, LEDG left edge, REDG right edge, DT defensive tackle, SAM strong-side linebacker,
# MIKE middle linebacker, WILL weak-side linebacker, CB cornerback, FS free safety, SS strong safety, K kicker, P punter, LS long snapper.
# A position's lines come in depth order: the starter first. A line like T17KR1 = a name gives the team's first kick returner, T17PR1 the first
# punt returner; a returner keeps his own position.
# The game still accepts the older position words (RB, OL, DL, LB, S, RET). If you write lines for a team, they replace the lines of that team.
# A new season: replace the lines of the teams, change the VERSION line, save the file, then choose Reload in the Customize item of the F9 menu.
# A name has 1 to 30 characters, with no comma and no semicolon. Delete the whole file to get the game's players back.
# The names are facts, used descriptively. They are not endorsed by the teams or the league.
# Sources: each team's own roster and depth chart pages, compared with nflverse (CC BY 4.0, github.com/nflverse) and Sleeper's player feed.
"""


def render(version: str, teams: dict) -> str:
    out = [HEADER, "VERSION = %s" % version]
    for t in sorted(teams):
        team = teams[t]
        ordered = team.active() + team.squad() + team.reserves()
        for i, m in enumerate(ordered, start=1):
            mark = (m.status + " ") if m.status else ""
            extra = ("; age %d" % m.age if m.age is not None else "") + ("; seasons %d" % m.seasons if m.seasons is not None else "")
            out.append("T%02dP%02d = %s%s %s %s%s" % (t, i, mark, m.pos, m.number, m.name, extra))
        for role in ROLES:
            for i, name in enumerate(team.roles.get(role, [])[:9], start=1):
                out.append("T%02d%s%d = %s" % (t, role, i, name))
    return "\n".join(out) + "\n"
