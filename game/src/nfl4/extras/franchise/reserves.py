"""The bench of a franchise team: the players of its 53 who have none of the 34 places (nfl4 only, rule 0.13; NX-B2b, D-149). This is inspired by Jim
Kitchen.

The owner (2026-10-24, NX-B2): "it should be using the current 53 man rosters for each team." The design is spec/NFL_EXTRA_FEATURES section 19.1 (Q-071):

* A bench player is a Player with status "reserve", his team and no place (-1). A team is its 34 places and a bench of up to MAX (19) men, so 53 in all;
  the practice squad (practice.py) stays apart. The offensive linemen (OL) and the long snapper (LS) are on a bench only: the game plays no place of theirs.
* A bench player plays no snap and adds nothing to a strength (`LeagueRecord.strength_sum` counts the 34 places, so every band and calibration of the games
  holds); he is paid (contracts.team_players), he ages, develops, retires, is signed again or let go, traded and released like a man of the places.
* When a man of the places is hurt, the staff's choice for his place is the best fit man of the bench of his position, at his own rating but never above the
  hurt man's (no injury is a gain); a hurt quarterback's place goes to the backup quarterback before any stand-in (injuries.lineup).
* The roster cut (draft.plan_cut, draft.apply_cut) keeps 53: the 34 places by rating as before, then the bench by `bench_order` (a backup quarterback, the
  long snapper and five linemen first, then one backup of each group, then the rest by the cut's keep value); the draft's rookies and the undrafted join
  the bench first; a free agent signs to an open place or to the bench.
* `real_reserves`: a new franchise of the real players puts every other man of a team's real 53 (rosters.txt) on its bench, with no draw: a hash of the
  league's ID and the name gives a rating below the team's places of his position, an age and a potential, and his contract is the market price.
* A league of format 16 or older has nobody on a bench; its next cut fills the benches. `LeagueRecord.reserves_on` (the store sets it) switches the rules
  on; the older tests' leagues keep it off and play exactly as before.

Plain rules: no speech, no files, no draw.
"""
from __future__ import annotations

import logging

from ...data import debuglog
from .. import tuning as T
from . import data as D

log = logging.getLogger("nfl4.extras")

STATUS = "reserve"
MAX = D.RESERVE_MAX
# the real roster's positions in the Franchise's groups (a returner's RET line repeats a man of his own position: it is not a man of its own)
REAL_GROUP = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "WR", "DL": "DL", "LB": "LB", "CB": "CB", "S": "S", "K": "K", "P": "P",
              "OL": "OL", "LS": "LS"}
# the men a bench keeps first at the cut (a team needs them most): a backup quarterback, the long snapper, five linemen, then one backup of each group
COVER_FIRST = (("QB", 1), ("LS", 1), ("OL", 5), ("RB", 1), ("WR", 1), ("DL", 1), ("LB", 1), ("CB", 1), ("S", 1))
NEVER_TRIMMED = ("QB", "LS")       # a new franchise that has more real men than the bench holds leaves out the deepest men of its largest groups, never these


def on(league) -> bool:
    return bool(getattr(league, "reserves_on", False))


def count(league, team: int) -> int:
    return sum(1 for p in league.players.values() if p.status == STATUS and p.team == team)


def filled(league, team: int) -> int:
    return sum(1 for pid in league.rosters[team - 1] if pid)


def room(league, team: int) -> int:
    """How many more men the team's 53 takes (0 when the league carries no benches). SR.4: the places and the bench together, so a team of the real
    roster whose view leaves back places empty has a longer bench (with every place filled it is MAX less the bench, as before)."""
    return max(0, D.ROSTER_MAX - filled(league, team) - count(league, team)) if on(league) else 0


def slots(league) -> int:
    """The men a team carries under contract besides its practice squad: the 34 places, and the bench when the league carries one."""
    return D.PLACE_COUNT + (MAX if on(league) else 0)


# ----- moving a man between the places and the bench -----

def to_bench(league, player) -> None:
    """The man leaves his place (if he has one) for his team's bench."""
    if player.place >= 0 and player.status == "active":
        league.rosters[player.team - 1][player.place] = 0
    player.status, player.place = STATUS, -1


def to_place(league, player, index: int) -> None:
    """The man of the team takes the place `index` (the caller has freed it)."""
    league.rosters[player.team - 1][index] = player.id
    player.status, player.place = "active", index


def open_index(league, team: int, position: str):
    roster = league.rosters[team - 1]
    return next((i for i in D.PLACES_OF.get(position, ()) if not roster[i]), None)


def join(league, team: int, player) -> str:
    """A man who signs with the team (a free agent, a squad player): the first open place of his position, else the bench (the caller has checked that
    one of them has room). Returns "place" or "bench"."""
    player.team, player.left, player.points = team, 0, 0
    index = open_index(league, team, player.pos)
    if index is not None:
        to_place(league, player, index)
        return "place"
    player.status, player.place = STATUS, -1
    return "bench"


def can_join(league, team: int, position: str) -> bool:
    """The team has an open place of the position, or room on its bench. SR.4: with the 53-man roster only while the team has fewer than 53 (an empty
    back place of the real roster is no open spot of a full team)."""
    if on(league):
        return room(league, team) > 0
    return open_index(league, team, position) is not None


def swap(league, starter, backup) -> None:
    """The bench man takes the place of the man in it, who goes to the bench (the player's own move: the depth chart, the quarterbacks)."""
    index = starter.place
    to_bench(league, starter)
    to_place(league, backup, index)


# ----- the cut: who stays on the bench -----

def bench_order(players: list, keep_order) -> list:
    """The men best to keep on a bench first: COVER_FIRST's men (the best of each, by `keep_order`), then every other man by `keep_order`."""
    ranked = keep_order(players)
    first: list = []
    for position, wanted in COVER_FIRST:
        first += [p for p in ranked if p.pos == position][:wanted]
    chosen = {p.id for p in first}
    return first + [p for p in ranked if p.id not in chosen]


# ----- the real 53 of a new franchise -----

def _mix(*parts) -> int:
    from .signings import _mix as mix
    return mix(*parts)


def _trim(placed_count: dict, extra: list, limit: int) -> list:
    """`extra` (in depth order) cut to `limit` men: again and again the deepest man of the group with the most men on the team (its places and its bench;
    equal counts: the later group of D.BENCH_ORDER), never a quarterback or the long snapper (while another group has a man to give)."""
    extra = list(extra)
    order = {pos: n for n, pos in enumerate(D.BENCH_ORDER)}
    while len(extra) > limit:
        totals: dict = {}
        for _rp, position, _name in extra:
            totals[position] = totals.get(position, 0) + 1
        groups = [pos for pos in totals if pos not in NEVER_TRIMMED] or list(totals)
        largest = max(groups, key=lambda pos: (totals[pos] + placed_count.get(pos, 0), order.get(pos, 0)))
        last = max(i for i, row in enumerate(extra) if row[1] == largest)
        extra.pop(last)
    return extra


def real_reserves(league, real) -> int:
    """A new franchise of the real players (NX-B2b): every man of a team's real 53 (the active roster of rosters.txt) who has none of its 34 places joins its
    bench, up to MAX (`_trim` leaves out the deepest men of the largest groups when a team has more), in his group's depth order, once each (a name the
    league already has stays with the first). No draw: a hash of the league's ID, the team and the name gives the rating (the first man 1 to 4 under the
    weakest place of his group, each next man 1 or 2 lower; the line and the snapper FR_RESERVE_RATING), the age (FR_RESERVE_AGE) and the potential; the
    contract is the market price (contracts.initial_contract). Switches the league's benches on. Returns how many joined."""
    from . import contracts as CT
    from .league import Player
    league.reserves_on = True
    if real is None or not hasattr(real, "active"):
        return 0
    known = {p.name.casefold() for p in league.players.values()}
    joined = 0
    base, span = T.FR_RESERVE_RATING
    age_base, age_span = T.FR_RESERVE_AGE
    for team in range(1, D.TEAMS + 1):
        placed = [p for p in league.active_of(team) if p is not None]
        placed_count: dict = {}
        weakest: dict = {}
        for p in placed:
            placed_count[p.pos] = placed_count.get(p.pos, 0) + 1
            weakest[p.pos] = min(weakest.get(p.pos, D.RATING_MAX + 1), p.rating)
        extra, seen = [], set()
        for rp in real.active(team):
            position = REAL_GROUP.get(rp.pos)
            name = real.spoken(rp.name)
            key = name.casefold()
            if position is None or key in known or key in seen:
                continue
            seen.add(key)
            extra.append((rp, position, name))
        extra = _trim(placed_count, extra, room(league, team))
        previous: dict = {}                              # position -> the rating of the man above on this bench
        for rp, position, name in extra:
            h = _mix(league.league_id, "bench", team, rp.name)
            if position not in previous:
                rating = weakest[position] - 1 - h % 4 if position in weakest else base + h % span
            else:
                rating = previous[position] - 1 - (h >> 4) % 2
            rating = max(D.RATING_MIN, min(D.RATING_MAX, rating))
            previous[position] = rating
            age = max(D.AGE_MIN, min(D.AGE_MAX, age_base + (h >> 8) % age_span))
            if age <= 25:
                potential = "high" if (h >> 16) % 5 == 0 else "average"
            else:
                potential = "average" if (h >> 16) % 2 else "low"
            player = Player(league.next_id, name, position, rating, potential, age, max(0, age - 22), rating, None, 0, STATUS, 0, team, -1)
            CT.sign(player, *CT.initial_contract(player))
            league.players[player.id] = player
            league.next_id += 1
            known.add(name.casefold())
            joined += 1
    CT.fit_to_cap(league)
    debuglog.event("franchise", "benches_formed", real=joined, teams=sum(1 for t in range(1, D.TEAMS + 1) if count(league, t)))   # rule 0.15
    return joined


# ----- the line and the snapper (the draft makes none) -----

LINE_WANTED = (("LS", 1), ("OL", 5))      # what a bench keeps at least, the snapper first (bench_order keeps them first too)


def line_missing(players: list) -> int:
    """How many men of LINE_WANTED the bench would still lack with these men on it (the cut keeps room for them)."""
    return sum(max(0, wanted - sum(1 for p in players if p.pos == position)) for position, wanted in LINE_WANTED)


def fill_line(league, surnames: list | None = None) -> int:
    """At the roster cut, after the fill: the draft and the market make no lineman and no snapper (the game plays no place of theirs), so a bench short of
    LINE_WANTED gets young made-up men of those positions while it has room and the cap allows the minimum, made WITHOUT a draw from a hash of the league's
    ID, the season, the team and the place (the practice squads' rule, practice.top_up), rated FR_FILL_RATING_SMALL as the fill's rookies of a small group,
    on the fill's contract. Nothing in a league without benches. Returns how many were made."""
    from . import contracts as CT
    from . import first_names as FN
    from .league import Player
    if not on(league):
        return 0
    if surnames is None:
        from ...game.names import load_surnames
        surnames = load_surnames()
    used = FN.name_keys(league.league_id, (p.name for p in league.players.values() if p.status in ("active", STATUS, "practice", "free")))
    base, span = T.FR_FILL_RATING_SMALL
    made = 0
    for team in range(1, D.TEAMS + 1):
        for position, wanted in LINE_WANTED:
            for index in range(len(league.bench(team, position)), wanted):
                if room(league, team) <= 0 or CT.cap_used(league, team) + T.FR_MIN_SALARY > CT.cap_of(league):
                    break
                h = _mix(league.league_id, "line", league.season, team, position, index)
                start = (h >> 20) % len(surnames)
                surname = next((surnames[(start + k) % len(surnames)] for k in range(len(surnames))
                                if surnames[(start + k) % len(surnames)] not in used), surnames[start])
                used.add(surname)
                rating = max(D.RATING_MIN, min(D.RATING_MAX, base + h % span))
                player = Player(league.next_id, FN.full_name(league.league_id, surname), position, rating, "average", D.AGE_MIN + 1, 0, rating,
                                None, 0, STATUS, 0, team, -1, T.FR_MIN_SALARY, T.FR_FILL_YEARS)
                league.players[player.id] = player
                league.next_id += 1
                made += 1
    if made:
        debuglog.event("franchise", "bench_line_filled", season=league.season, made=made)        # rule 0.15
    return made


# ----- the whole-file check -----

def check(league, whole) -> None:
    """LeagueError unless every bench man has a team and no place, and no bench holds more than MAX."""
    from .league import LeagueError
    counts = [0] * D.TEAMS
    for p in league.players.values():
        if p.status != STATUS:
            continue
        if isinstance(p.team, bool) or not isinstance(p.team, int) or not 1 <= p.team <= D.TEAMS or p.place != -1:
            raise LeagueError("bench player %d has team %r and place %r" % (p.id, p.team, p.place))
        counts[p.team - 1] += 1
    for team in range(1, D.TEAMS + 1):                    # SR.4: the places and the bench, the 53 and the game day's two (a squad kicker signed)
        if counts[team - 1] + filled(league, team) > D.ROSTER_MAX + D.GAME_DAY_EXTRA:
            raise LeagueError("team %d has %d players on its 53" % (team, counts[team - 1] + filled(league, team)))
