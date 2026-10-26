"""The real roster as a team: its depth chart on Madden NFL's 22 positions, and the engine's 34 places made from it (nfl4 only, rule 0.13; CLAUDE.md
0.30 and 0.32, NX-L3, NX-L4, NX-L5, NX-L11; NFL_FRANCHISE_DESIGN 21.3, 21.4, 21.6 (2) and 21.13; D-159, D-160, D-161). This is inspired by Jim Kitchen.

Plain rules: no speech, no files, no draw, nothing of the Franchise. A man is any key (a player ID in a franchise, a written name in a quick game); the
caller says each man's position. Classic never reaches this module: it keeps the original's places, groups and names.

* THE CHART: {position: [men, starter first]} for the 22 positions, and the return roles {"KR": [men], "PR": [men]} (a role of a man of any position).
* THE VIEW (design 21.4): the 34 places of the original's sections, made for each game from the chart, the men who will not play skipped:
  6 backs (the halfbacks, then the fullbacks), 6 receivers (WR1, WR2, WR3, TE1, WR4, TE2, WR5, TE3, ...), 17 defenders (6 line: LEDG1, REDG1, DT1, DT2,
  then the second tier; 5 backers: SAM1, MIKE1, WILL1, then the second tier; 4 corners; 2 safeties: FS1, SS1, FS2, SS2), 2 returners, the kicker,
  the punter, the quarterback. A man is in one place at most. A back or receiver place with nobody of the family is EMPTY (None: the usage share of an
  empty place is 0, `cover` names a man for the original's uniform draws). A defense place the family cannot fill takes the best spare man of the
  nearest family, who keeps his own position (a 3-4 team's edge men at linebacker). A team with no active kicker or punter plays its practice squad's
  (a game-day elevation); with none there, the punter kicks or the kicker punts.
* `convert_word`: an older league's group word (RB, WR, DL, OL, ...) to the position of its family the team is shortest of against the league's mix.
"""
from __future__ import annotations

from . import roster_file as RF

MADDEN = RF.MADDEN
ROLES = RF.ROLES
STARTERS = RF.STARTERS

# the families of the 22 positions (design 21.3): a man changes position only inside his family
FAMILIES = (("QB", ("QB",)), ("backs", ("HB", "FB")), ("receivers", ("WR", "TE")), ("offensive line", ("LT", "LG", "C", "RG", "RT")),
            ("defensive line", ("LEDG", "REDG", "DT")), ("backers", ("SAM", "MIKE", "WILL")), ("corners", ("CB",)), ("safeties", ("FS", "SS")),
            ("K", ("K",)), ("P", ("P",)), ("LS", ("LS",)))
FAMILY_POSITIONS = dict(FAMILIES)
FAMILY = {position: family for family, positions in FAMILIES for position in positions}
# the Franchise's group word of each position (the rows of its tuning tables and its 34 places until SR.5 moves every block to the positions: D-161)
GROUP = {"QB": "QB", "HB": "RB", "FB": "RB", "WR": "WR", "TE": "WR", "LT": "OL", "LG": "OL", "C": "OL", "RG": "OL", "RT": "OL",
         "LEDG": "DL", "REDG": "DL", "DT": "DL", "SAM": "LB", "MIKE": "LB", "WILL": "LB", "CB": "CB", "FS": "S", "SS": "S",
         "K": "K", "P": "P", "LS": "LS"}
# the men a position may take a starter from besides its own (NX-L11 1: the other side or role of the family; never another family)
SAME_FAMILY_MOVES = {"LT": ("RT",), "RT": ("LT",), "LG": ("RG",), "RG": ("LG",), "C": (), "LEDG": ("REDG",), "REDG": ("LEDG",), "DT": (),
                     "SAM": ("MIKE", "WILL"), "MIKE": ("SAM", "WILL"), "WILL": ("SAM", "MIKE"), "FS": ("SS",), "SS": ("FS",),
                     "HB": ("FB",), "FB": ("HB",), "WR": (), "TE": (), "QB": (), "CB": (), "K": (), "P": (), "LS": ()}

# the league's active men by position (design 21.1, the shipped rosters.txt of 2026-10-25, SRC-OFFICIAL): the mix the conversion compares with
LEAGUE_MIX = {"QB": 86, "HB": 105, "FB": 13, "WR": 174, "TE": 119, "LT": 61, "LG": 62, "C": 62, "RG": 54, "RT": 54, "LEDG": 77, "REDG": 75, "DT": 172,
              "SAM": 22, "MIKE": 66, "WILL": 63, "CB": 180, "FS": 75, "SS": 71, "K": 31, "P": 32, "LS": 32}
# the conversion table of design 21.6 (2): an older group word, and the positions it may become (one: always that one)
WORD_POSITIONS = {"QB": ("QB",), "RB": ("HB",), "FB": ("FB",), "WR": ("WR",), "TE": ("TE",), "OL": ("LT", "LG", "C", "RG", "RT"),
                  "DL": ("LEDG", "REDG", "DT"), "LB": ("SAM", "MIKE", "WILL"), "CB": ("CB",), "S": ("FS", "SS"), "K": ("K",), "P": ("P",),
                  "LS": ("LS",), "RET": ("WR", "CB")}
for _p in MADDEN:
    WORD_POSITIONS.setdefault(_p, (_p,))

# the 34 places (franchise.data.PLACES' order): 0-5 backs, 6-11 receivers, 12-28 defense (12-17 line, 18-22 backers, 23-26 corners, 27-28 safeties),
# 29-30 returners, 31 kicker, 32 punter, 33 quarterback
BACKS, RECEIVERS, LINE, BACKERS, CORNERS, SAFETIES = range(0, 6), range(6, 12), range(12, 18), range(18, 23), range(23, 27), range(27, 29)
RETURNERS, KICKER, PUNTER, QUARTERBACK = range(29, 31), 31, 32, 33
PLACE_COUNT = 34
SECTIONS = (BACKS, RECEIVERS, range(12, 29), RETURNERS)
# the nearest families a short defense section borrows from, in order (design 21.4 (4))
COVER_FROM = {"backers": (("LEDG", "REDG"), ("DT",)), "corners": (("FS", "SS"),), "safeties": (("CB",),), "defensive line": (("SAM", "MIKE", "WILL"),)}
RETURN_NEVER = frozenset(("QB", "K", "P", "LS", "LT", "LG", "C", "RG", "RT"))     # never a returner, whatever the roles say (SR.6: nor a lineman)
RETURN_FALLBACK =(("HB", "FB"), ("WR", "TE"), ("CB",))           # who returns when the roles name fewer than two fit men (today's rule)


def family_of(position: str) -> str:
    return FAMILY.get(position, "")


def may_start_at(position: str, man_position: str) -> bool:
    """NX-L11: a man of this position may be made the starter at `position` (his own, or the other side or role of his family)."""
    return man_position == position or man_position in SAME_FAMILY_MOVES.get(position, ())


def convert_word(word: str, have: dict) -> str:
    """Design 21.6 (2): the position an older league's group word becomes, the one of its candidates the team has fewest of against the league's
    mix (have[p] / LEAGUE_MIX[p] smallest; ties to the first in the 22's order). `have` counts the team's men by position (it is not changed)."""
    candidates = WORD_POSITIONS.get(word.upper() if isinstance(word, str) else "", ())
    if not candidates:
        return ""
    best = candidates[0]
    for position in candidates[1:]:
        if have.get(position, 0) * LEAGUE_MIX[best] < have.get(best, 0) * LEAGUE_MIX[position]:
            best = position
    return best


def ordered_positions(men: list, position_of) -> dict:
    """{position: [men in the given order]} of the 22 (every position present, empty lists too)."""
    chart = {position: [] for position in MADDEN}
    for man in men:
        position = position_of(man)
        if position in chart:
            chart[position].append(man)
    return chart


def put_first(order: list, man, slot: int = 0) -> list:
    """NX-L11 (design 21.13): `man` takes the slot (0 the starter, 1 the second starter of a position that starts more than one); the man who was there
    takes the chosen man's old place, so nobody leaves the chart. A man not in the order is put in the slot and the others move down one."""
    out = list(order)
    slot = max(0, min(slot, len(out)))
    if man in out:
        old = out.index(man)
        if old == slot:
            return out
        if slot < len(out):
            out[old], out[slot] = out[slot], man
        return out
    out.insert(slot, man)
    return out


def with_names_first(order: list, names: list, key=lambda man: man) -> list:
    """The named men first (in the order named, by casefolded key), then the others in their order (a name not in the order is left out)."""
    by_key = {str(key(man)).casefold(): man for man in order}
    first = []
    for name in names:
        man = by_key.get(str(name).casefold())
        if man is not None and man not in first:
            first.append(man)
    return first + [man for man in order if man not in first]


# ----- the view -----

class View:
    """The 34 places of one team for one game (or for the Franchise's places at full health): `places[i]` a man or None (an empty place), and how
    each was found (for the debug log, design 21.11)."""

    def __init__(self):
        self.places = [None] * PLACE_COUNT
        self.covered = {}                 # place -> the position of the man of another family who fills it
        self.elevated = []                # practice squad men who play this game (a kicker or a punter)
        self.empty = []                   # the empty places

    def men(self) -> list:
        return [man for man in self.places if man is not None]

    def cover(self, index: int):
        """The man of the nearest filled place of the same section (nearest first, the lower place of two equally near), or None; never used for a
        filled place."""
        for section in SECTIONS:
            if index in section:
                for distance in range(1, len(section)):
                    for other in (index - distance, index + distance):
                        if other in section and self.places[other] is not None:
                            return self.places[other]
        return None

    def names(self, name_of) -> list:
        """The 34 names, an empty place's the cover's (the original's uniform draws name him; its usage share is 0 because it repeats a man)."""
        out = []
        for index, man in enumerate(self.places):
            if man is None:
                man = self.cover(index)
            out.append(name_of(man) if man is not None else "")
        return out


def make_view(chart: dict, roles: dict | None = None, fit=None, squad: dict | None = None, distinct: bool = False) -> View:
    """Design 21.4: the 34 places from a chart. `fit(man)` is False for a man who will not play (None: everyone plays); `squad` is the practice
    squad's chart, used only for a missing kicker or punter (an elevation); `distinct`: no man in two places (the returners, the kicker who
    punts). Adds no draw."""
    fit = fit or (lambda man: True)
    view = View()
    used: set = set()

    def ready(position) -> list:
        return [m for m in chart.get(position, ()) if fit(m) and id_of(m) not in used]

    def place(index, man) -> None:
        view.places[index] = man
        used.add(id_of(man))

    # quarterback, kicker, punter
    for index, position in ((QUARTERBACK, "QB"), (KICKER, "K"), (PUNTER, "P")):
        men = ready(position)
        if men:
            place(index, men[0])
    for index, position in ((KICKER, "K"), (PUNTER, "P")):
        if view.places[index] is None and squad:
            men = [m for m in squad.get(position, ()) if fit(m) and id_of(m) not in used]
            if men:
                place(index, men[0])
                view.elevated.append(men[0])
    if not distinct:
        if view.places[KICKER] is None and view.places[PUNTER] is not None:
            view.places[KICKER] = view.places[PUNTER]      # the punter kicks (the day's emergency)
        elif view.places[PUNTER] is None and view.places[KICKER] is not None:
            view.places[PUNTER] = view.places[KICKER]
    # backs: every halfback, then the fullbacks
    for index, man in zip(BACKS, ready("HB") + ready("FB")):
        place(index, man)
    # receivers: WR1, WR2, WR3, TE1, WR4, TE2, WR5, TE3, ...
    wide, tight, mixed = ready("WR"), ready("TE"), []
    while wide or tight:
        for _ in range(3 if not mixed else 1):
            if wide:
                mixed.append(wide.pop(0))
        if tight:
            mixed.append(tight.pop(0))
    for index, man in zip(RECEIVERS, mixed):
        place(index, man)
    # the defense, each section from its own family first, by tiers (the starters of every position, then the second tier, ...)
    sections = (("defensive line", LINE, ("LEDG", "REDG", "DT")), ("backers", BACKERS, ("SAM", "MIKE", "WILL")), ("corners", CORNERS, ("CB",)),
                ("safeties", SAFETIES, ("FS", "SS")))
    for _family, places, positions in sections:
        for index, man in zip(places, tiers(ready, positions)):
            place(index, man)
    for family, places, _positions in sections:
        for index in places:
            if view.places[index] is not None:
                continue
            for borrow in COVER_FROM.get(family, ()):
                spare = tiers(ready, borrow)
                if spare:
                    place(index, spare[0])
                    view.covered[index] = position_of_in(chart, spare[0])
                    break
    # returners: the roles' men in turn (KR1, PR1, KR2, PR2, ...), the two different; then the spare backs, receivers and corners. A returner
    # may also hold his place of the offense or the defense (a team's third receiver returns punts) unless `distinct` (the Franchise's places
    # until SR.5: one man, one place, D-161)
    roles = roles or {}
    turns = []
    for i in range(max((len(roles.get(r, ())) for r in ROLES), default=0)):
        for role in ROLES:
            if i < len(roles.get(role, ())):
                turns.append(roles[role][i])
    known = {id_of(m) for p in MADDEN for m in chart.get(p, ())}
    def may_return(man) -> bool:
        return RETURN_NEVER.isdisjoint({position_of_in(chart, man)})

    returners = [m for m in turns if fit(m) and id_of(m) in known and (not distinct or id_of(m) not in used) and may_return(m)]
    wide, tight = ready("WR"), ready("TE")
    for group in (ready("HB") + ready("FB"), wide + tight, ready("CB")):
        returners += group
    seen: list = []
    for man in returners:
        if id_of(man) not in {id_of(s) for s in seen}:
            seen.append(man)
    if len(seen) < len(RETURNERS):
        # SR.5: a Franchise team with every back, receiver and corner in a place (a small roster after injuries or a thin offseason) returns kicks
        # with a spare safety, then a spare backer (a real team's coverage men); never the quarterback, the kickers or the snapper
        for man in tiers(ready, ("FS", "SS")) + tiers(ready, ("SAM", "MIKE", "WILL")) + tiers(ready, ("LEDG", "REDG", "DT")):
            if id_of(man) not in {id_of(s) for s in seen}:
                seen.append(man)
    for index, man in zip(RETURNERS, seen):
        view.places[index] = man
        used.add(id_of(man))
    view.empty = [i for i in range(PLACE_COUNT) if view.places[i] is None]
    return view


def fill_ins(chart: dict, squad: dict | None, places) -> dict:
    """S8.2 (an e-mail report, 2026-10-26: "at some positions it has no one starting"): the man who plays a place of the lineup that no man of its
    own position is left for (a 3-4 team has no strong-side linebacker, many teams no fullback, a team's only kicker is on the practice squad).
    `places` are (position, slot) in the lineup's order; returns {(position, slot): (man, his own position, how)} for those places only, where how is
    "family" (a spare man of the other side or role, then of the rest of the family), "squad" (the practice squad's kicker or punter, brought up for
    game day as make_view does), "kicker" (the punter kicks or the kicker punts, as make_view does) or "cover" (a spare man of the nearest defense
    family, COVER_FROM, as make_view does). A spare man is one behind his own position's starters; each fills one place at most. Never a man of
    another family on offense; nobody when nobody fits. No draw; the chart is not changed (the man keeps his own position)."""
    spare = {p: list(chart.get(p, ()))[STARTERS.get(p, 1):] for p in MADDEN}
    squad = squad or {}
    used: set = set()
    out = {}

    def take(positions):
        for p in positions:
            while spare[p]:
                man = spare[p].pop(0)
                if id_of(man) not in used:
                    return man, p
        return None

    for position, slot in places:
        if position not in FAMILY or slot < len(chart.get(position, ())):
            continue
        found = None
        moves = SAME_FAMILY_MOVES.get(position, ())
        rest = tuple(p for p in FAMILY_POSITIONS[FAMILY[position]] if p != position and p not in moves)
        if position in ("K", "P"):
            men = [m for m in squad.get(position, ()) if id_of(m) not in used]
            if men:
                found = (men[0], position, "squad")
            else:
                other = "P" if position == "K" else "K"
                if chart.get(other):
                    found = (chart[other][0], other, "kicker")
        for positions in (moves, rest):
            if found is None and positions:
                got = take(positions)
                if got:
                    found = (got[0], got[1], "family")
        if found is None:
            for borrow in COVER_FROM.get(FAMILY[position], ()):
                got = take(borrow)
                if got:
                    found = (got[0], got[1], "cover")
                    break
        if found is not None:
            if found[2] != "kicker":
                used.add(id_of(found[0]))
            out[(position, slot)] = found
    return out


def tiers(ready, positions) -> list:
    """The ready men of the positions by tiers: the starters of each position (STARTERS of them), then the second tier, and so on, in the order of the
    positions within a tier."""
    lists = {p: ready(p) for p in positions}
    out = []
    depth = 0
    while any(lists.values()):
        for p in positions:
            size = STARTERS.get(p, 1)
            take, lists[p] = lists[p][:size], lists[p][size:]
            out += take
        depth += 1
    return out


def position_of_in(chart: dict, man) -> str:
    for position, men in chart.items():
        if position in MADDEN and man in men:
            return position
    return ""


def id_of(man):
    return man.casefold() if isinstance(man, str) else man


def bench(chart: dict, view: View) -> list:
    """The active men of the chart who have no place in the view, in the 22's order and chart order."""
    placed = {id_of(m) for m in view.men()}
    return [m for position in MADDEN for m in chart.get(position, ()) if id_of(m) not in placed]


def check_chart(chart: dict, positions: dict) -> list:
    """The problems of a chart: `positions` maps every active man to his position; each must be in the chart exactly once, at his own position."""
    problems = []
    seen: dict = {}
    for position, men in chart.items():
        if position not in MADDEN:
            problems.append("the chart has the position %r" % (position,))
            continue
        for man in men:
            if man in seen:
                problems.append("%r is in the chart twice" % (man,))
            seen[man] = position
            if positions.get(man) != position:
                problems.append("%r is at %s in the chart, his position is %r" % (man, position, positions.get(man)))
    for man in positions:
        if man not in seen:
            problems.append("%r is not in the chart" % (man,))
    return problems
