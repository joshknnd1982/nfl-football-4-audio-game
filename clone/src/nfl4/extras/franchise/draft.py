"""The draft, the roster cut and the fill of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 7 (F3, N6.5). Plain rules over the league record, no speech and no files, so the offseason's stages and the
calibration's fast run use the very same code (the speech and the questions are `draft_flow.py`).

    make_class / draft_order           the class (the only draws of stage 4) and the order of the picks (no draw)
    Draft                              the draft in progress: the value of a prospect for a team (`best_for`, `ranked_for`: no draw, one code path
                                       for the computer's picks and the staff's list, invariant I7), the picks, the rookies waiting for the cut
    keep_order / plan_cut / apply_cut  the roster cut of every team (no draw): the staff's releases, the player's own choice, the places
    check_draft                        the whole-file check of a draft record (league.py calls it)

A drafted rookie is an ACTIVE player with `place` -1 (waiting) until the cut: the roster lists keep their 34 places, and the group's
count plus the rookies waiting for it is what the need bonus and the cut look at. The draft record (`LeagueRecord.draft`) is a plain dict,
{"class": [[pos, name, true rating, potential, age, low end of the range] ...], "order": [32 teams], "picks": [[team, prospect index,
player ID] ...], "staff_all": 0 or 1}; it lives from the class (the start of stage 4) to the end of stage 5, when the cut applies.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import tuning as T
from . import contracts
from . import data as D
from .league import LeagueError, LeagueRecord, Player, draw_name

SURPLUS_POSITIONS = ("K", "P", "RET")        # design 7.3: a prospect of these needs an open place to be worth a pick


@dataclass(frozen=True)
class Prospect:
    """One player of the class. The spoken range is `low` to `high`; the true rating is known to the team only from the cut on."""
    index: int
    pos: str
    name: str
    true: int
    potential: str
    age: int
    low: int

    @property
    def middle(self) -> int:
        return self.low + D.RANGE_MIDDLE

    @property
    def high(self) -> int:
        return self.low + D.RANGE_SPAN

    @classmethod
    def from_row(cls, index: int, row: list) -> "Prospect":
        return cls(index, *row)

    def to_row(self) -> list:
        return [self.pos, self.name, self.true, self.potential, self.age, self.low]


# ----- the class (stage 4's draws, design 12 item 6) -----

def make_class(league: LeagueRecord, rnd, surnames: list) -> list:
    """The class of this draft: for each prospect in order the position `below(sum of the weights)`, the name (`rnd(len(surnames))`
    again while an active player or a prospect of this class has it: design 7.4), the true rating `below(15)` twice, the potential
    `below(100)`, the age `below(3)` and the scouting offset `below(7)`. Nothing of the league is changed."""
    weights = T.FR_CLASS_WEIGHTS
    total = sum(weight for _, weight in weights)
    used = {player.name for player in league.players.values() if player.status == "active"}
    base, span = T.FR_ROOKIE_RATING
    high, average = T.FR_ROOKIE_POTENTIAL_SHARES
    age_base, age_span = T.FR_ROOKIE_AGE
    prospects = []
    for index in range(T.FR_CLASS_SIZE):
        roll = rnd.below(total)
        for position, weight in weights:
            if roll < weight:
                break
            roll -= weight
        name = draw_name(rnd, surnames, used)
        used.add(name)
        true = max(D.RATING_MIN, min(D.RATING_MAX, base + rnd.below(span) + rnd.below(span)))
        chance = rnd.below(100)
        potential = "high" if chance < high else "average" if chance < average else "low"
        age = age_base + rnd.below(age_span)
        offset = rnd.below(T.FR_SCOUT_SPAN)
        prospects.append(Prospect(index, position, name, true, potential, age, true - offset))
    return prospects


def draft_order(sums: list, wins: list, finish: list) -> list:
    """The 32 teams in the order they pick, in every round (design 7.2, NFL draft rules): the teams that missed the play-offs first, then
    the play-off teams by the round they lost in (wild card, division, conference championship, the Super Bowl loser, the champion
    last); inside a group fewer wins first, then the lower exact strength first, then the team order. No draw."""
    if len(sums) != D.TEAMS:
        sums = [0] * D.TEAMS
    return sorted(range(1, D.TEAMS + 1), key=lambda t: (finish[t - 1], wins[t - 1], sums[t - 1], t))


def order_of(league: LeagueRecord) -> list:
    """The order from the season that just ended: its history entry (wins and finish) and the exact strengths of that season, which
    the record keeps until stage 6 (the rosters do not change during a season)."""
    entry = league.history[-1] if league.history and league.history[-1]["season"] == league.season else None
    if entry is not None:
        wins, finish = entry["wins"], entry["finish"]
    else:                                                      # no entry (a record made by hand): the records, nobody in the play-offs
        wins, finish = [league.records[2 * t] for t in range(D.TEAMS)], [D.FINISH_MISSED] * D.TEAMS
    return draft_order(league.sums, wins, finish)


# ----- the prospects still to be taken, by position -----

class Board:
    """The undrafted prospects of each position, best first by (middle + potential bonus, lower number first), so that the best choice for
    a team is found without looking at all of them (`Draft.best_for` stops a position's list as soon as nothing after can win)."""

    def __init__(self, prospects: list, taken: set):
        self.base = {p.index: p.middle + T.FR_DRAFT_POTENTIAL[p.potential] for p in prospects}
        self.by_pos = {position: [] for position in D.POSITIONS}
        for p in prospects:
            if p.index not in taken:
                self.by_pos[p.pos].append(p)
        for available in self.by_pos.values():
            available.sort(key=lambda p: (-self.base[p.index], p.index))

    def remove(self, prospect: Prospect) -> None:
        self.by_pos[prospect.pos].remove(prospect)

    def available(self) -> list:
        return [p for available in self.by_pos.values() for p in available]


# ----- the draft in progress -----

class Draft:
    """The draft record of a league with the helpers a pick needs. `create` makes a new one (the class, the order, no pick yet); the
    constructor reads one that is in the record (a resumed draft). Every change goes into `league.draft` as it is made."""

    def __init__(self, league: LeagueRecord):
        if league.draft is None:
            raise LeagueError("there is no draft in progress")
        self.league = league
        self.data = league.draft
        self.prospects = [Prospect.from_row(i, row) for i, row in enumerate(self.data["class"])]
        self.order = self.data["order"]
        self.picks = self.data["picks"]
        self.board = Board(self.prospects, {row[1] for row in self.picks})
        self.rookies: dict = {}                                 # team -> its rookies waiting for the cut, in pick order
        self.middle_of: dict = {}                               # player ID -> the middle of his spoken range
        for team, index, pid in self.picks:
            self.rookies.setdefault(team, []).append(league.players[pid])
            self.middle_of[pid] = self.prospects[index].middle

    @classmethod
    def create(cls, league: LeagueRecord, rnd, surnames: list) -> "Draft":
        prospects = make_class(league, rnd, surnames)
        league.draft = {"class": [p.to_row() for p in prospects], "order": order_of(league), "picks": [], "staff_all": 0}
        league.pick_no = 1
        return cls(league)

    # ----- where the draft stands -----

    @property
    def staff_all(self) -> bool:
        return bool(self.data["staff_all"])

    def let_the_staff_pick_the_rest(self) -> None:
        self.data["staff_all"] = 1

    @property
    def done(self) -> bool:
        return len(self.picks) >= D.DRAFT_PICKS

    def slot(self, overall: int) -> tuple:
        """(round 1 to 7, the pick in the round 1 to 32, the team) of pick number `overall` (1 to 224)."""
        index = overall - 1
        return index // D.TEAMS + 1, index % D.TEAMS + 1, self.order[index % D.TEAMS]

    def next_slot(self) -> tuple:
        return self.slot(len(self.picks) + 1)

    def place_in_round(self, team: int) -> int:
        """The pick of a team in every round (1 to 32)."""
        return self.order.index(team) + 1

    # ----- what a team needs -----

    def needs(self, team: int) -> dict:
        """For each position group of the team: (open, lowest). A group has an open place when its places outnumber the players it
        has left plus the rookies drafted into it; a group of one place counts as open also when its best player (a rookie by the
        middle of his range) is under `FR_DRAFT_WEAK`. `lowest` is the rating of the weakest player who would hold a place: the lowest
        rating the group knows (the incumbents' true ratings, the rookies' middles) while the group has an open place, and once the
        rookies make it full the place-count'th best, so that a prospect counts as better only when he would take a place (a team
        that has drafted its quarterback does not want a fourth one, D-059). None for an empty group."""
        league = self.league
        roster = league.rosters[team - 1]
        rookies = self.rookies.get(team, ())
        needs = {}
        for position in D.POSITIONS:
            places = D.PLACES_OF[position]
            known = [league.players[roster[i]].rating for i in places if roster[i]]
            known += [self.middle_of[r.id] for r in rookies if r.pos == position]
            is_open = len(known) < len(places) or (len(places) == 1 and max(known) < T.FR_DRAFT_WEAK)
            starters = sorted(known, reverse=True)[:len(places)]
            needs[position] = (is_open, starters[-1] if starters else None)
        return needs

    def value(self, prospect: Prospect, needs: dict) -> int:
        """What the prospect is worth to a team with these needs (design 7.3): the middle of the range, the potential bonus, and the
        need bonuses, all added."""
        is_open, lowest = needs[prospect.pos]
        points = self.board.base[prospect.index]
        if is_open:
            points += T.FR_DRAFT_VALUE["need_quarterback" if prospect.pos == "QB" else "need"]
        elif prospect.pos in SURPLUS_POSITIONS:
            points += T.FR_DRAFT_VALUE["surplus"]
        if lowest is not None and prospect.middle > lowest:
            points += T.FR_DRAFT_VALUE["better"]
        return points

    def ranked_for(self, team: int) -> list:
        """Every prospect still available, the most valuable to the team first, equal values by the lower number. The staff's list is
        its first five; `hear more prospects` walks all of it."""
        needs = self.needs(team)
        return sorted(self.board.available(), key=lambda p: (-self.value(p, needs), p.index))

    def best_for(self, team: int) -> Prospect | None:
        """The first of `ranked_for`, found without ranking everyone: in each position's list (best base first) nothing after a prospect
        can beat the best found once its base plus the position's bonuses falls under it."""
        needs = self.needs(team)
        better = max(0, T.FR_DRAFT_VALUE["better"])
        best_key, best = None, None
        for position, available in self.board.by_pos.items():
            if not available:
                continue
            is_open, lowest = needs[position]
            extra = (T.FR_DRAFT_VALUE["need_quarterback" if position == "QB" else "need"] if is_open
                     else T.FR_DRAFT_VALUE["surplus"] if position in SURPLUS_POSITIONS else 0)
            for prospect in available:
                base = self.board.base[prospect.index]
                if best_key is not None and base + extra + better < best_key[0]:
                    break
                points = base + extra + (better if lowest is not None and prospect.middle > lowest else 0)
                key = (points, -prospect.index)
                if best_key is None or key > best_key:
                    best_key, best = key, prospect
        return best

    # ----- a pick -----

    def make_pick(self, team: int, prospect: Prospect) -> Player:
        """The team takes the prospect: he becomes a player of the league (a new ID, drafted [season, round, pick in the round]) who
        waits, active and unplaced, for the cut. League.sav is written by the caller."""
        league = self.league
        if self.done:
            raise LeagueError("the draft is over")
        overall = len(self.picks) + 1
        round_no, in_round, expected = self.slot(overall)
        if team != expected:
            raise LeagueError("pick %d is the team %d's, not the team %d's" % (overall, expected, team))
        if prospect.index in {row[1] for row in self.picks}:
            raise LeagueError("%s was taken already" % prospect.name)
        player = Player(league.next_id, prospect.name, prospect.pos, prospect.true, prospect.potential, prospect.age, 0,
                        prospect.true, [league.season, round_no, in_round], 0, "active", 0, team, -1,
                        contracts.rookie_salary(overall), T.FR_ROOKIE_YEARS)      # SX.8g: the scale of his pick, four years
        league.next_id += 1
        league.players[player.id] = player
        self.picks.append([team, prospect.index, player.id])
        self.board.remove(prospect)
        self.rookies.setdefault(team, []).append(player)
        self.middle_of[player.id] = prospect.middle
        league.pick_no = len(self.picks) + 1
        return player

    # ----- the ranges the player is told (until the cut) -----

    def range_of(self, player: Player) -> tuple:
        """(low end, high end) of a rookie waiting for the cut."""
        low = self.middle_of[player.id] - D.RANGE_MIDDLE
        return low, low + D.RANGE_SPAN


def open_places(draft: Draft, team: int) -> list:
    """The positions with open places and how many, in the roster menu's order: [(position, count)]."""
    league = draft.league
    roster = league.rosters[team - 1]
    rookies = draft.rookies.get(team, ())
    out = []
    for position in D.ROSTER_ORDER:
        places = D.PLACES_OF[position]
        have = sum(1 for i in places if roster[i]) + sum(1 for r in rookies if r.pos == position)
        if have < len(places):
            out.append((position, len(places) - have))
    return out


# ----- the roster cut (stage 5, design 7.6; no draw) -----

def keep_value(player: Player) -> int:
    """Rating plus the youth bonus (age `FR_KEEP_YOUTH_AGE` or less: high potential +4, average +2)."""
    return player.rating + (T.FR_KEEP_YOUTH[player.potential] if player.age <= T.FR_KEEP_YOUTH_AGE else 0)


def keep_order(players: list) -> list:
    """The players best to keep first; equal values to the younger, then to the lower ID."""
    return sorted(players, key=lambda p: (-keep_value(p), p.age, p.id))


def waiting_by_team(league: LeagueRecord) -> dict:
    """The rookies waiting for the cut, by team: the active players who have no place."""
    waiting: dict = {}
    for player in league.players.values():
        if player.status == "active" and player.place < 0:
            waiting.setdefault(player.team, []).append(player)
    return waiting


def group_players(league: LeagueRecord, team: int, position: str, waiting: dict) -> list:
    """The team's players of one group: those in its places and the rookies waiting for it."""
    roster = league.rosters[team - 1]
    players = [league.players[roster[i]] for i in D.PLACES_OF[position] if roster[i]]
    return players + [w for w in waiting.get(team, ()) if w.pos == position]


def surplus(league: LeagueRecord, team: int, waiting: dict) -> dict:
    """position -> how many players the team has over the group's places (only the groups that have any)."""
    out = {}
    for position in D.POSITIONS:
        over = len(group_players(league, team, position, waiting)) - D.GROUP_SIZE[position]
        if over > 0:
            out[position] = over
    return out


def release_order(players: list) -> list:
    """The players worst to keep first: the order of the staff's releases, and of the player's own choice (the staff's choices first)."""
    return list(reversed(keep_order(players)))


def floor_releases(kept: list, position: str) -> list:
    """The players of a group of one or two places who are under the cut's floor (`FR_CUT_FLOOR`): one weak player is the whole group,
    so he is released although the group is not over its places, and the fill puts an undrafted rookie of 50 or more in his place
    (invariant I5, D-059). `kept` are the players who stay by the count. The worst to keep first."""
    if D.GROUP_SIZE[position] > D.CUT_FLOOR_GROUP_MAX:
        return []
    return [player for player in release_order(kept) if player.rating < T.FR_CUT_FLOOR]


def plan_cut(league: LeagueRecord, team: int, waiting: dict) -> list:
    """The players the staff releases from the team: in each group (in the roster menu's order) the surplus, the worst to keep first,
    then the players of a small group who are under the floor."""
    released = []
    for position in D.ROSTER_ORDER:
        players = group_players(league, team, position, waiting)
        over = len(players) - D.GROUP_SIZE[position]
        cut = release_order(players)[:over] if over > 0 else []
        gone = {player.id for player in cut}
        released += cut + floor_releases([player for player in players if player.id not in gone], position)
    return released


def staff_cut(league: LeagueRecord, team: int, waiting: dict) -> list:
    """All the staff releases from a team: the cut (`plan_cut`) and, when the team would be over the cap after it and the fill, the
    players who save the most for what they give (`contracts.cap_releases`, SX.8g). The computer's teams and the fast run use this."""
    released = plan_cut(league, team, waiting)
    return released + contracts.cap_releases(league, team, waiting, released)


def apply_cut(league: LeagueRecord, releases: dict, waiting: dict) -> int:
    """Every team's cut: `releases` is team -> the players it releases. The released leave (status released, the season they left, the
    dead money of their contracts charged to the team: SX.8g); the rest of each group take its places best first, the rookies among
    them (their true rating is known now); a group with fewer players than places keeps its empty places last. Returns the number
    released."""
    count = 0
    for team in range(1, D.TEAMS + 1):
        gone = {player.id for player in releases.get(team, ())}
        roster = league.rosters[team - 1]
        for position in D.POSITIONS:
            places = D.PLACES_OF[position]
            players = group_players(league, team, position, waiting)
            kept = sorted((p for p in players if p.id not in gone), key=lambda p: (-p.rating, p.id))
            if len(kept) > len(places):
                raise ValueError("the %s group of team %d keeps %d players for %d places" % (position, team, len(kept), len(places)))
            for player in players:
                if player.id in gone:
                    contracts.release(league, player)               # before the status: the dead money is charged to his team
                    player.status, player.left, player.place, player.points = "released", league.season, -1, 0
                    count += 1
            for index, player in zip(places, kept):
                roster[index] = player.id
                player.place = index
            for index in places[len(kept):]:
                roster[index] = 0
    return count


# ----- the whole-file check of a draft record (league.py) -----

def check_draft(league: LeagueRecord, whole) -> set:
    """LeagueError unless the draft record is whole; returns the IDs of the rookies waiting for the cut. Allowed only in stages 4 and 5."""
    data = league.draft
    if data is None:
        if league.pick_no != 0:
            raise LeagueError("pick %d but no draft" % league.pick_no)
        return set()
    from .league import OFFSEASON
    if league.stage != OFFSEASON or league.stage_no not in (D.STAGE_DRAFT, D.STAGE_CUT):
        raise LeagueError("a draft in stage %r %r" % (league.stage, league.stage_no))
    if not isinstance(data, dict) or set(data) != {"class", "order", "picks", "staff_all"}:
        raise LeagueError("the draft holds %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    rows = data["class"]
    if not isinstance(rows, list) or len(rows) != T.FR_CLASS_SIZE:
        raise LeagueError("the class holds %r prospects, not %d" % (len(rows) if isinstance(rows, list) else rows, T.FR_CLASS_SIZE))
    youngest, span = T.FR_ROOKIE_AGE
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise LeagueError("a prospect is %r" % (row,))
        position, name, true, potential, age, low = row
        if position not in D.POSITIONS or potential not in D.POTENTIALS:
            raise LeagueError("a prospect is %r" % (row,))
        if not isinstance(name, str) or not 1 <= len(name) <= 40 or any(ord(c) < 32 for c in name):
            raise LeagueError("a prospect has the name %r" % (name,))
        whole(true, D.RATING_MIN, D.RATING_MAX, "a prospect's rating")
        whole(age, youngest, youngest + span - 1, "a prospect's age")
        whole(low, D.RATING_MIN, D.RATING_MAX, "a prospect's low end")
        if not low <= true <= low + D.RANGE_SPAN:
            raise LeagueError("a prospect rated %d has the range %d to %d" % (true, low, low + D.RANGE_SPAN))
    order = data["order"]
    if not isinstance(order, list) or sorted(order) != list(range(1, D.TEAMS + 1)) or any(isinstance(t, bool) for t in order):
        raise LeagueError("the draft order is %r" % (order,))
    if data["staff_all"] not in (0, 1) or isinstance(data["staff_all"], bool):
        raise LeagueError("staff_all is %r" % (data["staff_all"],))
    picks = data["picks"]
    if not isinstance(picks, list) or len(picks) > D.DRAFT_PICKS:
        raise LeagueError("the draft holds %r picks" % (len(picks) if isinstance(picks, list) else picks,))
    waiting: set = set()
    taken: set = set()
    per_team: dict = {}
    for number, row in enumerate(picks):
        if not isinstance(row, list) or len(row) != 3:
            raise LeagueError("a pick is %r" % (row,))
        team, index, pid = row
        whole(team, 1, D.TEAMS, "a pick's team")
        whole(index, 0, len(rows) - 1, "a pick's prospect")
        whole(pid, 1, 10 ** 9, "a pick's player")
        if team != order[number % D.TEAMS] or index in taken or pid in waiting:
            raise LeagueError("pick %d is %r, out of order or twice" % (number + 1, row))
        player = league.players.get(pid)
        if (player is None or player.status != "active" or player.place != -1 or player.team != team
                or player.drafted != [league.season, number // D.TEAMS + 1, number % D.TEAMS + 1]):
            raise LeagueError("pick %d is player %d, who is not a rookie waiting for the cut" % (number + 1, pid))
        prospect = rows[index]
        if (player.name, player.pos, player.rating, player.potential, player.age) != (prospect[1], prospect[0], prospect[2], prospect[3], prospect[4]):
            raise LeagueError("pick %d is not the prospect %d" % (number + 1, index))
        taken.add(index)
        waiting.add(pid)
        per_team[team] = per_team.get(team, 0) + 1
        if per_team[team] > D.MAX_ROOKIES:
            raise LeagueError("team %d has %d rookies" % (team, per_team[team]))
    if league.pick_no != len(picks) + 1:
        raise LeagueError("the next pick is %d after %d picks" % (league.pick_no, len(picks)))
    if league.stage_no == D.STAGE_CUT and len(picks) != D.DRAFT_PICKS:
        raise LeagueError("the cut after %d picks of %d" % (len(picks), D.DRAFT_PICKS))
    return waiting
