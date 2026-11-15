"""Substitutions during a game: who plays for the player's team, for the next play or for the rest of the game (nfl4 only, rule 0.13; CLAUDE.md
0.30, 0.24; GitHub issue 14, D-229). This is inspired by Jim Kitchen.

The tester's words (issue 14, 2026-11-14): "Add an option to sub players in for either a play or for the rest of the game. Example I might want to put
all backups in if winning by a large amount. I might want to put a particular player in for a play these in game options should be added."

The rules part (no speech, no files, NO DRAW). The game plays a team as its 34 places (franchise/data.PLACES: 6 backs, 6 receivers, 17 defenders,
2 returners, the kicker, the punter, the quarterback); the starters are the first places of each position and get the most of the usage draws
(extras/usage.py). A substitution only changes WHO holds a place; every draw of the game is made as before, so a game where the player substitutes
nobody is the very same game.

* `effective(base, bench, record)` the 34 men as they play now: the base lineup (the game's own: the depth chart, the injuries of a franchise game),
  then "backups in" when it is on, then the substitutions for the rest of the game, then those for the next play, in the order they were made;
* backups in: for every position the starters (roster_file.STARTERS: three wide receivers, two defensive tackles, two cornerbacks, one of every other
  position) go to the end of the position's depth order and the men behind them take their places, the bench's men of that position too; the
  returners, the kicker and the punter stay (a team rests its starters, not its kickers);
* one man in at one place: a man who holds another place of the offense or the defense changes places with the man there (no man plays two places);
  a man of the bench takes the place and the man there goes to the bench. A returner's place takes any man who may return kicks, and he keeps his
  own place too, as the game day's returners always have. A man who can no longer play (hurt in a franchise game) leaves the list: his place goes
  back to the lineup's man.
* the record, `ExtrasRecord.subs` (Save Game keeps it): {"backups": bool, "game": [[place, man], ...], "play": [[place, man], ...], "at": n,
  "packages": {formation: [[place, man], ...]}}; a man is a franchise player's id or, in a quick game or a season, his spoken name; "play" holds for
  the play that starts after `at` plays of the game. A record saved before the packages (1.0.2) has no "packages": it loads as none.
* the tester's answers on issue 14 (2026-11-15, rule 0.41): Q-087 b (D-234), "All backups in" puts the backup returners in too (the kicker and the
  punter stay): the team's next kick and punt returners (`spares`, the roles KR2, PR2 ... in turn), else the men who may return kicks in the lineup
  as it is with the backups in; Q-086 b (D-235), packages by formation: the men the player set for a formation come in for every play called in it
  (`effective(..., formation=...)`), after the substitutions for the rest of the game and before those for the next play; Q-085 b (D-236): the
  computer's side rests its starters (`backups_in` on its lineup) when it leads by a lot late in the game (`rest_due`).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import roster_file as RF
from . import roster_model as RM

PLACE_COUNT = 34
BACKS, RECEIVERS, LINE, BACKERS, CORNERS, SAFETIES = RM.BACKS, RM.RECEIVERS, RM.LINE, RM.BACKERS, RM.CORNERS, RM.SAFETIES
RETURNERS, KICKER, PUNTER, QUARTERBACK = tuple(RM.RETURNERS), RM.KICKER, RM.PUNTER, RM.QUARTERBACK
FIELD = tuple(range(0, 29)) + (QUARTERBACK,)              # the places of the offense and the defense: one man, one place
# the groups of places the menu lists, in its order, and the franchise's group word of each (franchise/data.POSITIONS)
GROUPS = (("QB", (QUARTERBACK,)), ("RB", tuple(BACKS)), ("WR", tuple(RECEIVERS)), ("DL", tuple(LINE)), ("LB", tuple(BACKERS)),
          ("CB", tuple(CORNERS)), ("S", tuple(SAFETIES)), ("RET", RETURNERS), ("K", (KICKER,)), ("P", (PUNTER,)))
GROUP_OF_PLACE = {place: group for group, places in GROUPS for place in places}
SECTIONS = (tuple(BACKS), tuple(RECEIVERS), tuple(range(12, 29)), RETURNERS)
# backups in: the starters of a position (a group word when nothing more is known of the men: a game without real names)
GROUP_STARTERS = {"QB": 1, "RB": 1, "WR": 4, "DL": 4, "LB": 3, "CB": 2, "S": 2}
NOT_RESTED = frozenset(("K", "P", "LS"))
GROUP_MARK = "*"                                        # a position known only as a group: "*WR"
LIST_MAX = 34                                           # a record's lists (a saved game edited by hand is refused, never half used)
# Q-086 (D-235): the formations a package is set for. The offense's: the formation the play is lined up in (the Formation setting of Formation and
# Tempo, else the play's own; catalog.SETTINGS["formation"] without "book"; "other" is the old and trick formations: wildcat, wishbone, victory
# and the like); the defense's: its package of defensive backs as played (personnel.adjust: 3 heavy at the goal line, 4 base, 5 nickel, 6 dime,
# 7 quarter). A play of the original's menus (no catalog call) has no formation: no package plays.
OFFENSE_FORMATIONS = ("under_center", "shotgun", "pistol", "singleback", "i_form", "split_backs", "empty", "heavy", "other")
DEFENSE_PACKAGES = ("heavy", "base", "nickel", "dime", "quarter")
PACKAGE_OF_BACKS = {3: "heavy", 4: "base", 5: "nickel", 6: "dime", 7: "quarter"}
PACKAGES = tuple("O:" + f for f in OFFENSE_FORMATIONS) + tuple("D:" + p for p in DEFENSE_PACKAGES)
# Q-085 (D-236): the computer rests its starters in the fourth quarter (never in overtime) when it leads by REST_LEAD with REST_LEFT seconds or less
# left, or by REST_LEAD_ANY at any time of the quarter; its starters come back when the lead falls under BACK_LEAD (UNVERIFIED: a common
# reading of NFL coaching, "three scores late"; measured by the calibration soak of D-236).
REST_QUARTER, REST_LEAD, REST_LEFT, REST_LEAD_ANY, BACK_LEAD = 4, 21, 600, 28, 14
# Q-087 (D-234): the men a backup returner is found among when the team's own returners are used up: backs, receivers and defensive backs (the
# coverage men a real team returns kicks with; roster_model.make_view's order), never a lineman or a linebacker
RETURN_GROUPS = frozenset(("RB", "WR", "CB", "S"))


@dataclass(frozen=True)
class Man:
    key: object                 # a franchise player's id (int) or the spoken name (str); None for a place nobody can be moved from (a stand-in)
    name: str                   # as spoken
    position: str = ""          # one of roster_model.MADDEN, else a group word (RB, WR, DL, ...), "" when unknown
    rating: object = None       # the franchise's rating of the place (None in a quick game)
    row: object = None          # the franchise's row (identity, name, rating) of a man who cannot be moved

    @property
    def movable(self) -> bool:
        return self.key is not None


def new_record() -> dict:
    return {"backups": False, "game": [], "play": [], "at": 0, "packages": {}}


def is_empty(record) -> bool:
    """Nothing is changed and no package is set: the base lineup plays."""
    return not record or (not changed_now(record) and not any(record.get("packages", {}).values()))


def changed_now(record) -> bool:
    """Backups in, or a substitution for the rest of the game or the next play (the packages are standing choices, not changes: "Starters back
    in" keeps them)."""
    return bool(record) and bool(record.get("backups") or record.get("game") or record.get("play"))


def package_rows(record, formation) -> list:
    if not record or not formation:
        return []
    return list(record.get("packages", {}).get(formation, ()))


def rest_due(resting: bool, quarter: int, overtime: bool, lead: int, left: int) -> bool:
    """Q-085 (D-236): whether the computer's side rests its starters now (`resting`: it does already). No draw."""
    if overtime or quarter != REST_QUARTER:
        return False
    if resting:
        return lead >= BACK_LEAD
    return lead >= REST_LEAD_ANY or (lead >= REST_LEAD and left <= REST_LEFT)


def group_of(position: str) -> str:
    """The group word of a position (TE is a receiver, FS a safety); a group word known only as a group ("*WR": a game without real names, an older
    league's man) is its own."""
    if position.startswith(GROUP_MARK):
        return position[len(GROUP_MARK):]
    return RM.GROUP.get(position, position)


def group_position(group: str) -> str:
    """The position of a man known only by his group (never one of the 22: the six receivers of a game without real names are not three wide
    receivers and so on)."""
    return GROUP_MARK + group


def may_play(place: int, place_position: str, man: Man) -> bool:
    """`man` may be put in at `place` whose man plays `place_position`: a returner's place takes any man who returns kicks (never a quarterback,
    a kicker, a lineman or the snapper); the kicker's and the punter's places take a kicker or a punter; any other place a man of the position or of
    the other side or role of its family (roster_model.may_start_at: a halfback for a fullback, a free safety for a strong safety, any linebacker),
    and when either position is not one of the 22 (a game without real names) a man of the same group."""
    if not man.movable:
        return False
    if place in RETURNERS:
        return man.position not in RM.RETURN_NEVER and group_of(man.position) not in ("QB", "K", "P", "OL", "LS")
    if place in (KICKER, PUNTER):
        return group_of(man.position) in ("K", "P")
    if place_position in RM.MADDEN and man.position in RM.MADDEN:
        return RM.may_start_at(place_position, man.position)
    return group_of(place_position) == group_of(man.position) != ""


def starters(position: str) -> int:
    if position in RM.MADDEN:
        return RF.STARTERS.get(position, 1)
    return GROUP_STARTERS.get(group_of(position), 1)


def place_position(table: list, place: int) -> str:
    """The position a place is played at: its man's own position; the group of the place when its man has none."""
    man = table[place]
    if man is not None and man.position:
        return man.position
    group = GROUP_OF_PLACE.get(place, "")
    return group_position("RB" if group == "RET" else group)


def field_place_of(table: list, key) -> int | None:
    """The place of the offense or the defense the man holds, or None (on the bench, or a returner only)."""
    for place in FIELD:
        man = table[place]
        if man is not None and man.movable and man.key == key:
            return place
    return None


def pool_of(base: list, bench: list) -> dict:
    """{key: Man} of every man who can be put in: the lineup's men and the bench's (one entry each)."""
    pool: dict = {}
    for man in list(base) + list(bench):
        if man is not None and man.movable and man.key not in pool:
            pool[man.key] = man
    return pool


def backups_in(table: list, bench: list, spares=()) -> list:
    """Every position's starters to the end of its order, the men behind them (the bench's too) in their places, and the backup returners in the
    two return places (see the module's text; `spares`: the team's returners in their order, as Men)."""
    out = list(table)
    in_table = {man.key for man in table if man is not None and man.movable}
    positions: list = []
    places_of: dict = {}
    for place in FIELD:
        man = table[place]
        if man is None or not man.movable or not man.position or group_of(man.position) in NOT_RESTED:
            continue
        if man.position not in places_of:
            positions.append(man.position)
            places_of[man.position] = []
        places_of[man.position].append(place)
    for position in positions:
        places = places_of[position]
        men = [table[p] for p in places] + [m for m in bench if m.movable and m.position == position and m.key not in in_table]
        count = min(starters(position), len(men))
        order = men[count:] + men[:count]
        for place, man in zip(places, order):
            out[place] = man
    return backup_returners(out, bench, spares)


def backup_returners(table: list, bench: list, spares=()) -> list:
    """Q-087 (D-234): the two return places get men who are not the returners now: the team's next returners (`spares`, in their order), then
    the backs, receivers and defensive backs of the lineup as it plays now (the backups who came in first, in place order), then the bench's. A place keeps
    its man when nobody else may return there."""
    out = list(table)
    now = {out[p].key for p in RETURNERS if out[p] is not None and out[p].movable}
    taken: set = set()
    for place in RETURNERS:
        position = place_position(out, place)
        order = [m for m in spares if m is not None] + [m for m, _where in candidates(out, bench, place)
                                                         if group_of(m.position) in RETURN_GROUPS]
        for man in order:
            if man.movable and man.key not in now and man.key not in taken and may_play(place, position, man):
                out[place] = man
                taken.add(man.key)
                break
    return out


def put(table: list, place: int, man: Man) -> list:
    """`man` in at `place` (see the module's text)."""
    out = list(table)
    if place in RETURNERS:
        other = RETURNERS[1] if place == RETURNERS[0] else RETURNERS[0]
        if out[other] is not None and out[other].movable and out[other].key == man.key:
            out[other] = out[place]
        out[place] = man
        return out
    if place in (KICKER, PUNTER):
        out[place] = man
        return out
    where = field_place_of(out, man.key)
    if where is not None:
        out[where] = out[place]
    out[place] = man
    return out


def effective(base: list, bench: list, record, empty=(), formation=None, spares=()) -> tuple[list, list]:
    """(the 34 men as they play now, the substitutions that were left out: [(list name, place, key)]). `empty`: the places that have nobody (the real
    roster's empty back places, franchise injuries.EMPTY): never moved, their names are the nearest filled place's of the section again.
    `formation`: the formation of the play called now (PACKAGES; None between plays and at a kick): its package plays after the substitutions for
    the rest of the game. `spares`: the team's returners in their order (keys), for "backups in"."""
    table = list(base)
    dropped: list = []
    if is_empty(record) or (not changed_now(record) and not package_rows(record, formation)):
        return table, dropped
    pool = pool_of(base, bench)
    empty = set(empty)
    if record.get("backups"):
        table = backups_in(table, [m for m in bench if m.movable], [pool[k] for k in spares if k in pool])
    lists = (("game", record.get("game", ())), ("package", package_rows(record, formation)), ("play", record.get("play", ())))
    for kind, rows in lists:
        for place, key in rows:
            man = pool.get(key)
            if man is None or not 0 <= place < PLACE_COUNT or place in empty:
                dropped.append((kind, place, key))
                continue
            table = put(table, place, man)
    for place in sorted(empty):
        cover = cover_of(table, place, empty)
        if cover is not None:
            table[place] = cover
    return table, dropped


def cover_of(table: list, place: int, empty) -> Man | None:
    """The man of the nearest filled place of the same section (nearest first, the lower of two equally near): roster_model.View.cover's rule."""
    for section in SECTIONS:
        if place in section:
            for distance in range(1, len(section)):
                for other in (place - distance, place + distance):
                    if other in section and other not in empty and table[other] is not None:
                        return table[other]
    return None


def candidates(table: list, bench: list, place: int, empty=()) -> list:
    """The men who may be put in at `place`, as (Man, the place he holds now or None): the lineup's men who may play there in place order (the
    offense and the defense first, then the returners, the kicker and the punter), then the bench's in its order; the man already there is left out."""
    current = table[place]
    position = place_position(table, place)
    seen = set()
    out = []
    if current is not None and current.movable:
        seen.add(current.key)
    for index in FIELD + RETURNERS + (KICKER, PUNTER):
        man = table[index]
        if index in empty or man is None or man.key in seen or not may_play(place, position, man):
            continue
        seen.add(man.key)
        out.append((man, index))
    for man in bench:
        if man.key in seen or not may_play(place, position, man):
            continue
        seen.add(man.key)
        out.append((man, None))
    # the man's own position first (a halfback before a fullback at a halfback's place), each part in its order
    own = [c for c in out if c[0].position == position]
    return own + [c for c in out if c[0].position != position]


# ----- the record -----

def check_record(record) -> None:
    """A saved record's shape and ranges (ExtrasRecord.check): ValueError when it is not a whole, sensible record. A record without "packages"
    (saved by 1.0.2) is mended: none."""
    if isinstance(record, dict) and set(record) == {"backups", "game", "play", "at"}:
        record["packages"] = {}
    if not isinstance(record, dict) or set(record) != {"backups", "game", "play", "at", "packages"}:
        raise ValueError("the substitutions are %r" % (record,))
    packages = record["packages"]
    if not isinstance(packages, dict) or any(key not in PACKAGES for key in packages):
        raise ValueError("the packages are %r" % (packages,))
    for rows in packages.values():
        check_rows(rows)
    if not isinstance(record["backups"], bool):
        raise ValueError("the backups switch is %r" % (record["backups"],))
    at = record["at"]
    if isinstance(at, bool) or not isinstance(at, int) or not 0 <= at <= 100000:
        raise ValueError("the play of the substitutions is %r" % (at,))
    for kind in ("game", "play"):
        check_rows(record[kind])


def check_rows(rows) -> None:
    if not isinstance(rows, list) or len(rows) > LIST_MAX:
        raise ValueError("the substitutions are %r" % (rows,))
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("a substitution is %r" % (row,))
        place, key = row
        if isinstance(place, bool) or not isinstance(place, int) or not 0 <= place < PLACE_COUNT:
            raise ValueError("a substitution's place is %r" % (place,))
        if isinstance(key, bool) or not (isinstance(key, int) and 1 <= key <= 10 ** 9 or isinstance(key, str) and 1 <= len(key) <= 40
                                         and not any(ord(c) < 32 for c in key)):
            raise ValueError("a substitution's player is %r" % (key,))


def add(record: dict, kind: str, place: int, key) -> None:
    """A substitution of `kind` ("game" or "play"). A later one for the same place replaces the earlier of its kind; one for the rest of the game
    also ends a next-play one at that place (the player's newer word)."""
    rows = [row for row in record[kind] if row[0] != place]
    rows.append([place, key])
    record[kind] = rows[-LIST_MAX:]
    if kind == "game":
        record["play"] = [row for row in record["play"] if row[0] != place]


def add_package(record: dict, formation: str, place: int, key) -> None:
    """Q-086 (D-235): `key` comes in at `place` for every play called in `formation`; a later one for the same place replaces it."""
    packages = record.setdefault("packages", {})
    rows = [row for row in packages.get(formation, []) if row[0] != place]
    rows.append([place, key])
    packages[formation] = rows[-LIST_MAX:]


def clear_package(record: dict, formation: str) -> None:
    record.setdefault("packages", {}).pop(formation, None)
