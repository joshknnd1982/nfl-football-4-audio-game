"""The draft, the roster cut and the fill of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 7 (F3, N6.5). Plain rules over the league record, no speech and no files, so the offseason's stages and the
calibration's fast run use the very same code (the speech and the questions are `draft_flow.py`).

    make_class / draft_order           the class (the only draws of stage 4) and the order of the picks (no draw)
    Draft                              the draft in progress: the value of a prospect for a team (`best_for`, `ranked_for`: no draw, one code path
                                       for the computer's picks and the staff's list, invariant I7), the picks, the rookies waiting for the cut
    keep_order / plan_cut / apply_cut  the roster cut of every team (no draw): the staff's releases, the player's own choice, the places
    check_draft                        the whole-file check of a draft record (league.py calls it)

A drafted rookie is an ACTIVE player with `place` -1 who waits OUTSIDE the chart until the cut (real_roster.waiting_ids): the team's family count plus
the rookies waiting for it is what the need bonus and the cut look at (SR.5, D-164: by family, against FR_ROSTER_TARGET and FR_GROUP_STARTERS, in place
of the 34 places' groups). The draft record (`LeagueRecord.draft`) is a plain dict,
{"class": [[group, name, true rating, potential, age, low end of the range, position] ...], "order": [32 teams], "picks": [[team, prospect index,
player ID] ...], "staff_all": 0 or 1, "owners": [the team that makes each of the 224 picks], "comp": [[round, team] of the compensatory picks]}; it lives from the class (the start of stage 4) to the end of
stage 5, when the cut applies. SX.8j: a pick may have changed hands in a trade of the season (`trades.py`); the draft makes the owners its own when it is
created (`owners`, pick by pick) and the trades' table of picks starts empty again. SX.8m: the compensatory picks awarded a year before (`comp.py`) sit at
the end of rounds 3 to 7 (`sequence`: every round's 32 picks, then its compensatory picks), so a draft has 224 picks or more; a compensatory pick is "pick 33"
and on of its round, paid by the rookie scale of its place in the whole draft.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import tuning as T
from . import contracts
from . import data as D
from . import first_names as FN
from .league import LeagueError, LeagueRecord, Player, draw_name

SURPLUS_POSITIONS = ("K", "P", "LS")         # design 7.3: a prospect of these needs an open spot to be worth a pick (SR.5: the snapper, no returner)


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
    position: str = ""                       # SR.5: his position of the 22 (`pos` is its family's word)

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
        return [self.pos, self.name, self.true, self.potential, self.age, self.low, self.position]


# ----- the class (stage 4's draws, design 12 item 6) -----

def class_size(comp_count: int) -> int:
    """The prospects of a class: `FR_CLASS_SIZE` (the 224 picks and a choice at the last ones) and one more for every compensatory pick (SX.8m), so the
    prospects nobody drafts, the undrafted free agents of the cut, are as many whatever the draft's count."""
    return T.FR_CLASS_SIZE + comp_count


def make_class(league: LeagueRecord, rnd, surnames: list, comp_count: int = 0) -> list:
    """The class of this draft: for each prospect in order the position `below(sum of the weights)` (SR.5: the 22 positions by the league's mix,
    FR_CLASS_POSITIONS), the name (`rnd(len(surnames))` again while an active player or a prospect of this class has it: design 7.4; NX-L12: the
    surnames are real NFL players' in the N. F. L. rules), the true rating `below(15)` twice, the potential `below(100)`, the age `below(3)` and the
    scouting offset `below(7)`. Nothing of the league is changed."""
    from .. import roster_model as RM
    weights = T.FR_CLASS_POSITIONS
    total = sum(weight for _, weight in weights)
    used = FN.name_keys(league.league_id, (player.name for player in league.players.values() if player.status == "active"))   # D-131
    base, span = T.FR_ROOKIE_RATING
    high, average = T.FR_ROOKIE_POTENTIAL_SHARES
    age_base, age_span = T.FR_ROOKIE_AGE
    prospects = []
    for index in range(class_size(comp_count)):
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
        prospects.append(Prospect(index, RM.GROUP[position], FN.full_name(league.league_id, name), true, potential, age, true - offset, position))
    return prospects


def migrate_class(league: LeagueRecord) -> None:
    """SR.5 (format 19): a draft in progress of an older file: each prospect gets his position (the conversion table's first of his group word; a returner
    a receiver), his group word follows it, and a rookie he became takes the same (no draw)."""
    from .. import roster_model as RM
    data = league.draft
    if not isinstance(data, dict) or not isinstance(data.get("class"), list):
        return
    for row in data["class"]:
        if isinstance(row, list) and len(row) == 6 and isinstance(row[0], str):
            position = RM.WORD_POSITIONS.get(row[0], ("WR",))[0]
            row[0] = RM.GROUP[position]
            row.append(position)
    for key in ("picks", "undrafted"):
        for pick in data.get(key, ()) if isinstance(data.get(key), list) else ():
            if isinstance(pick, list) and len(pick) == 3 and isinstance(pick[1], int) and 0 <= pick[1] < len(data["class"]):
                player = league.players.get(pick[2]) if isinstance(pick[2], int) else None
                row = data["class"][pick[1]]
                if player is not None and isinstance(row, list) and len(row) == 7:
                    player.position, player.pos = row[6], row[0]


def draft_order(sums: list, wins: list, finish: list) -> list:
    """The 32 teams in the order they pick, in every round (design 7.2, NFL draft rules): the teams that missed the play-offs first, then
    the play-off teams by the round they lost in (wild card, division, conference championship, the Super Bowl loser, the champion
    last); inside a group fewer wins first, then the lower exact strength first, then the team order. No draw."""
    if len(sums) != D.TEAMS:
        sums = [0] * D.TEAMS
    return sorted(range(1, D.TEAMS + 1), key=lambda t: (finish[t - 1], wins[t - 1], sums[t - 1], t))


def order_of(league: LeagueRecord) -> list:
    """The order from the season that just ended: its history entry (wins and finish) and the exact strengths the record keeps until stage 6:
    the strengths the teams ENDED the season with (a trade of the season brings the two teams' sums up to date, SX.8j), so a team that traded for
    veterans picks as the stronger team it became."""
    entry = league.history[-1] if league.history and league.history[-1]["season"] == league.season else None
    if entry is not None:
        wins, finish, ties = entry["wins"], entry["finish"], entry.get("ties") or [0] * D.TEAMS
    else:                                                      # no entry (a record made by hand): the records, nobody in the play-offs
        wins, finish, ties = [league.records[2 * t] for t in range(D.TEAMS)], [D.FINISH_MISSED] * D.TEAMS, list(league.ties)
    # SX.12: a tie is half a win (twice the wins plus the ties orders the teams as the wins do when nobody has a tie)
    return draft_order(league.sums, [2 * w + t for w, t in zip(wins, ties)], finish)


# ----- the prospects still to be taken, by position -----

class Board:
    """The undrafted prospects of each position, best first by (middle + potential bonus, lower number first), so that the best choice for
    a team is found without looking at all of them (`Draft.best_for` stops a position's list as soon as nothing after can win)."""

    def __init__(self, prospects: list, taken: set):
        self.base = {p.index: p.middle + T.FR_DRAFT_POTENTIAL[p.potential] for p in prospects}
        self.by_pos = {position: [] for position in D.GROUPS}
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
        self.owners = self.data["owners"]
        self.comp = self.data["comp"]
        self.sequence = sequence(self.owners, self.comp)        # (round, the pick in the round, the team) of every pick, in order
        self.board = Board(self.prospects, {row[1] for row in self.picks} | {row[1] for row in self.data["undrafted"]})
        self.rookies: dict = {}                                 # team -> its rookies waiting for the cut, in pick order
        self.middle_of: dict = {}                               # player ID -> the middle of his spoken range
        for team, index, pid in self.picks + self.data["undrafted"]:      # SX.8m: the undrafted free agents wait for the cut too
            self.rookies.setdefault(team, []).append(league.players[pid])
            self.middle_of[pid] = self.prospects[index].middle

    @classmethod
    def create(cls, league: LeagueRecord, rnd, surnames: list) -> "Draft":
        from . import comp
        comp_count = sum(1 for row in league.comp if row[0] == league.season)
        prospects = make_class(league, rnd, surnames, comp_count)
        order = order_of(league)
        league.draft = {"class": [p.to_row() for p in prospects], "order": order, "picks": [], "staff_all": 0, "owners": owners_of(league, order),
                        "comp": comp.for_draft(league, order), "undrafted": []}
        league.trades["picks"] = []                             # SX.8j: the traded picks are the draft's now
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
        return len(self.picks) >= len(self.sequence)

    def slot(self, overall: int) -> tuple:
        """(round 1 to 7, the pick in the round, the team) of pick number `overall` (1 to the draft's count; a compensatory pick is 33 and on of its round)."""
        return self.sequence[overall - 1]

    @property
    def total(self) -> int:
        return len(self.sequence)

    def next_slot(self) -> tuple:
        return self.slot(len(self.picks) + 1)

    def place_in_round(self, team: int) -> int:
        """The pick of a team in every round (1 to 32) by the draft order (its own picks)."""
        return self.order.index(team) + 1

    def picks_of(self, team: int) -> list:
        """The picks the team makes in this draft: (round, the pick in the round), in draft order (SX.8j: traded picks included, its own traded away left out)."""
        return [(r, k) for r, k, owner in self.sequence if owner == team]

    def own_picks_only(self, team: int) -> bool:
        """The team makes exactly its own pick in every round (no trade moved one of them; its compensatory picks are told apart, SX.8m)."""
        place = self.place_in_round(team)
        return [(r, k) for r, k in self.picks_of(team) if k <= D.TEAMS] == [(r, place) for r in range(1, D.DRAFT_ROUNDS + 1)]

    def comp_picks_of(self, team: int) -> list:
        """The team's compensatory picks in this draft: (round, the pick in the round)."""
        return [(r, k) for r, k, owner in self.sequence if owner == team and k > D.TEAMS]

    # ----- what a team needs -----

    def needs(self, team: int) -> dict:
        """For each family of the team (SR.5, D-164): (open, lowest). A family is open when the team holds fewer than its roster target
        (FR_ROSTER_TARGET: the real league's mean) counting the rookies drafted into it, or when its weakest starter (a rookie by the middle of his
        range) is under `FR_DRAFT_WEAK`. `lowest` is the rating of the family's weakest starter
        (FR_GROUP_STARTERS of them: the incumbents' true ratings, the rookies' middles), so a prospect counts as better only when he would start
        (a team that has drafted its quarterback does not want a fourth one, D-059). None for an empty family."""
        from . import real_roster
        league = self.league
        rookies = self.rookies.get(team, ())
        mine = {r.id for r in rookies}
        men = [p for p in real_roster.members(league, team) if p.id not in mine]
        needs = {}
        for group in D.GROUPS:
            known = [p.rating for p in men if p.pos == group]
            known += [self.middle_of[r.id] for r in rookies if r.pos == group]
            starting = T.FR_GROUP_STARTERS[group]
            starters = sorted(known, reverse=True)[:starting]
            # under the target, or a starter under FR_DRAFT_WEAK (SR.5: every family, as the one-place groups were: a weak starter is a need)
            is_open = len(known) < T.FR_ROSTER_TARGET[group] or (group not in D.RESERVE_POSITIONS and len(starters) == starting
                                                                  and starters[-1] < T.FR_DRAFT_WEAK)    # (the line and the snapper play no place)
            needs[group] = (is_open, starters[-1] if starters else None)
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
                        contracts.rookie_salary(contracts.pick_number(round_no, in_round)), T.FR_ROOKIE_YEARS,      # SX.8g: the scale of his pick, four years
                        position=prospect.position, number=free_number(league, team, prospect.position))
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


def sequence(owners: list, comp: list) -> list:
    """(round, the pick in the round, the team) of every pick of a draft: each round's 32 picks by `owners`, then its compensatory picks in their order."""
    out = []
    for round_no in range(1, D.DRAFT_ROUNDS + 1):
        out += [(round_no, k + 1, owners[(round_no - 1) * D.TEAMS + k]) for k in range(D.TEAMS)]
        extra = [team for r, team in comp if r == round_no]
        out += [(round_no, D.TEAMS + i + 1, team) for i, team in enumerate(extra)]
    return out


def owners_of(league: LeagueRecord, order: list) -> list:
    """The team that makes each of the 224 picks: the team of the draft order, or the team a trade of the season moved that pick to (SX.8j)."""
    from . import trades
    return [trades.owner(league, i // D.TEAMS + 1, order[i % D.TEAMS]) for i in range(D.DRAFT_PICKS)]


def open_places(draft: Draft, team: int) -> list:
    """The families the team holds fewer of than its roster target (FR_ROSTER_TARGET), counting its rookies, and how many, in the roster menu's
    order: [(group, count)]."""
    from . import real_roster
    league = draft.league
    men = real_roster.members(league, team)
    rookies = draft.rookies.get(team, ())
    out = []
    for group in D.ROSTER_ORDER:
        have = sum(1 for p in men if p.pos == group) + sum(1 for r in rookies if r.pos == group)
        if have < T.FR_ROSTER_TARGET[group]:
            out.append((group, T.FR_ROSTER_TARGET[group] - have))
    return out


# the NFL's jersey numbers by position (SRC-OFFICIAL, the 2021 rule 5-1-4 as amended: the numbers a position may wear); a rookie takes the lowest free one
NUMBER_RANGES = {"QB": (1, 19), "K": (1, 19), "P": (1, 19), "HB": (1, 49), "FB": (1, 49), "WR": (1, 49), "TE": (1, 49), "CB": (1, 49), "FS": (1, 49),
                 "SS": (1, 49), "SAM": (1, 59), "MIKE": (1, 59), "WILL": (1, 59), "LEDG": (50, 99), "REDG": (50, 99), "DT": (50, 99),
                 "LT": (50, 79), "LG": (50, 79), "C": (50, 79), "RG": (50, 79), "RT": (50, 79), "LS": (40, 99)}


def free_number(league: LeagueRecord, team: int, position: str) -> str:
    """Design 21.7 (2): the lowest number of the position's range that no man of the team (its roster and its squad) wears; "-" when none is free."""
    if position not in NUMBER_RANGES:
        return "-"
    taken = {p.number for p in league.players.values() if p.team == team and p.status in ("active", "practice", "list")}
    low, high = NUMBER_RANGES[position]
    for number in range(low, high + 1):
        if str(number) not in taken:
            return str(number)
    return "-"


# ----- the roster cut (stage 5, design 7.6; no draw) -----

def keep_value(player: Player) -> int:
    """Rating plus the youth bonus (age `FR_KEEP_YOUTH_AGE` or less: high potential +4, average +2)."""
    return player.rating + (T.FR_KEEP_YOUTH[player.potential] if player.age <= T.FR_KEEP_YOUTH_AGE else 0)


def keep_order(players: list) -> list:
    """The players best to keep first; equal values to the younger, then to the lower ID."""
    return sorted(players, key=lambda p: (-keep_value(p), p.age, p.id))


def waiting_by_team(league: LeagueRecord) -> dict:
    """The rookies waiting for the cut, by team: the draft's picks and the undrafted in camp (real_roster.waiting_ids), in pick order."""
    from . import real_roster
    waiting: dict = {}
    for pid in sorted(real_roster.waiting_ids(league)):
        player = league.players.get(pid)
        if player is not None and player.status == "active":
            waiting.setdefault(player.team, []).append(player)
    return waiting


def group_players(league: LeagueRecord, team: int, position: str, waiting: dict) -> list:
    """The team's players of one family: the men of its chart (the view's first, then the rest in chart order) and the rookies waiting for it."""
    from . import real_roster
    rookies = [w for w in waiting.get(team, ()) if w.pos == position]
    mine = {w.id for w in waiting.get(team, ())}
    men = [p for p in real_roster.members(league, team) if p.pos == position and p.id not in mine]
    men.sort(key=lambda p: (p.place < 0, p.place if p.place >= 0 else 0, -p.rating, p.id))
    return men + rookies


def team_candidates(league: LeagueRecord, team: int, waiting: dict) -> list:
    """Every man the team's cut decides on: its roster and its rookies waiting (each once)."""
    from . import real_roster
    rookies = list(waiting.get(team, ()))
    mine = {p.id for p in rookies}
    return [p for p in real_roster.members(league, team) if p.id not in mine] + rookies


def surplus(league: LeagueRecord, team: int, waiting: dict) -> dict:
    """group -> how many players the team holds over its roster target (only the families that have any)."""
    out = {}
    for group in D.GROUPS:
        over = len(group_players(league, team, group, waiting)) - T.FR_ROSTER_TARGET[group]
        if over > 0:
            out[group] = over
    return out


def release_order(players: list) -> list:
    """The players worst to keep first: the order of the staff's releases, and of the player's own choice (the staff's choices first)."""
    return list(reversed(keep_order(players)))


FLOOR_GROUPS = ("K", "P", "LS")             # SR.5: the families of one man (design 7.6's floor, invariant I5)


def floor_releases(kept: list, position: str) -> list:
    """The players of a family of one man (the kicker, the punter, the snapper) who are under the cut's floor (`FR_CUT_FLOOR`): one weak player is the
    whole family, so he is released although the family is not over its limit, and the fill puts an undrafted rookie of 50 or more in his place
    (invariant I5, D-059). `kept` are the players who stay by the count. The worst to keep first."""
    if position not in FLOOR_GROUPS:
        return []
    return [player for player in release_order(kept) if player.rating < T.FR_CUT_FLOOR]


def keep_plan(players: list, gone=frozenset()) -> list:
    """SR.5 (D-164, design 21.7 (1)): the men the staff keeps of `players` (a team's roster and its rookies), at most D.ROSTER_MAX: the family minimums
    first (FR_FAMILY_MIN: two quarterbacks, the kicker, the punter, the snapper, eight linemen and the rest; each family's best by `keep_order`, a one-man
    family's man under the floor not counted), then every other man by `keep_order` while his family is under its most (FR_FAMILY_MAX). In keep order."""
    ranked = [p for p in keep_order(players) if p.id not in gone]
    floor = {p.id for group in FLOOR_GROUPS for p in floor_releases([q for q in ranked if q.pos == group], group)}
    # room is kept for the men the fill must make (a family with fewer men than its minimum: real_roster.fill_needs), so a team ends the cut at 53
    missing = sum(max(0, least - sum(1 for q in ranked if q.pos == group and q.id not in floor)) for group, least in T.FR_FAMILY_MIN.items())
    limit = D.ROSTER_MAX - missing
    kept: list = []
    held: dict = {}
    for group in D.GROUPS:
        for p in [q for q in ranked if q.pos == group and q.id not in floor][:T.FR_FAMILY_MIN.get(group, 0)]:
            kept.append(p)
            held[group] = held.get(group, 0) + 1
    chosen = {p.id for p in kept}
    for p in ranked:
        if len(kept) >= limit:
            break
        if p.id in chosen or p.id in floor or held.get(p.pos, 0) >= T.FR_FAMILY_MAX.get(p.pos, D.ROSTER_MAX):
            continue
        kept.append(p)
        chosen.add(p.id)
        held[p.pos] = held.get(p.pos, 0) + 1
    return keep_order(kept)


def plan_cut(league: LeagueRecord, team: int, waiting: dict) -> list:
    """The players the staff releases from the team (SR.5, D-164: the cut to 53 of design 21.7 (1)): every man of its roster and its rookies whom
    `keep_plan` does not keep, the worst to keep first."""
    players = team_candidates(league, team, waiting)
    kept = {p.id for p in keep_plan(players)}
    return release_order([p for p in players if p.id not in kept])


def staff_cut(league: LeagueRecord, team: int, waiting: dict) -> list:
    """All the staff releases from a team: the cut (`plan_cut`) and, when the team would be over the cap after it and the fill, the
    players who save the most for what they give (`contracts.cap_releases`, SX.8g). The computer's teams and the fast run use this."""
    released = plan_cut(league, team, waiting)
    return released + contracts.cap_releases(league, team, waiting, released)


def apply_cut(league: LeagueRecord, releases: dict, waiting: dict) -> int:
    """Every team's cut: `releases` is team -> the players it releases. The released leave (status released, the season they left, the
    dead money of their contracts charged to the team: SX.8g); the draft is over (its rookies who stay join their positions' charts, their true
    rating known now) and every team's chart and places are made again (the staff's order: the best first; the player's own order kept, NX-D3).
    Returns the number released."""
    from . import real_roster
    count = 0
    for team in range(1, D.TEAMS + 1):
        for player in releases.get(team, ()):
            if player.status != "active" or player.team != team:
                continue
            if contracts.released_free(player, league):
                contracts.leave(player)                     # SX.8m: an undrafted rookie released at his first cut costs nothing
            else:
                contracts.release(league, player)           # before the status: the dead money is charged to his team
            player.status, player.left, player.place, player.points = "released", league.season, -1, 0
            count += 1
    league.draft = None
    league.pick_no = 0
    real_roster.refresh_all(league)
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
    if not isinstance(data, dict) or set(data) != {"class", "order", "picks", "staff_all", "owners", "comp", "undrafted"}:
        raise LeagueError("the draft holds %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    rows = data["class"]
    size = class_size(len(data["comp"])) if isinstance(data["comp"], list) else T.FR_CLASS_SIZE
    if not isinstance(rows, list) or len(rows) != size:
        raise LeagueError("the class holds %r prospects, not %d" % (len(rows) if isinstance(rows, list) else rows, size))
    youngest, span = T.FR_ROOKIE_AGE
    from .. import roster_model as RM
    for row in rows:
        if not isinstance(row, list) or len(row) != 7:
            raise LeagueError("a prospect is %r" % (row,))
        position, name, true, potential, age, low, real_position = row
        if position not in D.GROUPS or potential not in D.POTENTIALS or real_position not in RM.MADDEN or RM.GROUP[real_position] != position:
            raise LeagueError("a prospect is %r" % (row,))
        if not isinstance(name, str) or not 1 <= len(name) <= 40 or any(ord(c) < 32 for c in name):
            raise LeagueError("a prospect has the name %r" % (name,))
        whole(true, D.RATING_MIN, D.RATING_MAX, "a prospect's rating")
        whole(age, youngest, youngest + span - 1, "a prospect's age")
        whole(low, max(D.RATING_MIN, T.FR_ROOKIE_RATING[0]) - (T.FR_SCOUT_SPAN - 1), D.RATING_MAX, "a prospect's low end")   # (SX.8m: a rookie rated 45 may be "about 39 to 45")
        if not low <= true <= low + D.RANGE_SPAN:
            raise LeagueError("a prospect rated %d has the range %d to %d" % (true, low, low + D.RANGE_SPAN))
    order = data["order"]
    if not isinstance(order, list) or sorted(order) != list(range(1, D.TEAMS + 1)) or any(isinstance(t, bool) for t in order):
        raise LeagueError("the draft order is %r" % (order,))
    if data["staff_all"] not in (0, 1) or isinstance(data["staff_all"], bool):
        raise LeagueError("staff_all is %r" % (data["staff_all"],))
    owners = data["owners"]
    if not isinstance(owners, list) or len(owners) != D.DRAFT_PICKS:
        raise LeagueError("the draft's owners are %r" % (len(owners) if isinstance(owners, list) else owners,))
    for team in owners:
        whole(team, 1, D.TEAMS, "the owner of a pick")
    from . import comp
    comp.check_rows(data["comp"], whole, "the draft's compensatory picks")       # SX.8m
    slots = sequence(owners, data["comp"])
    picks = data["picks"]
    if not isinstance(picks, list) or len(picks) > len(slots):
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
        round_no, in_round, owner = slots[number]
        if team != owner or index in taken or pid in waiting:
            raise LeagueError("pick %d is %r, out of order or twice" % (number + 1, row))
        player = league.players.get(pid)
        if (player is None or player.status != "active" or player.place != -1 or player.team != team
                or player.drafted != [league.season, round_no, in_round]):
            raise LeagueError("pick %d is player %d, who is not a rookie waiting for the cut" % (number + 1, pid))
        prospect = rows[index]
        if (player.name, player.pos, player.rating, player.potential, player.age) != (prospect[1], prospect[0], prospect[2], prospect[3], prospect[4]):
            raise LeagueError("pick %d is not the prospect %d" % (number + 1, index))
        taken.add(index)
        waiting.add(pid)
        per_team[team] = per_team.get(team, 0) + 1
        if per_team[team] > sum(1 for slot in slots if slot[2] == team):
            raise LeagueError("team %d has %d rookies" % (team, per_team[team]))
    from . import undrafted
    waiting |= undrafted.check_undrafted(league, data, whole, taken, len(picks) == len(slots))      # SX.8m: the undrafted free agents in camp
    if league.pick_no != len(picks) + 1:
        raise LeagueError("the next pick is %d after %d picks" % (league.pick_no, len(picks)))
    if league.stage_no == D.STAGE_CUT and len(picks) != len(slots):
        raise LeagueError("the cut after %d picks of %d" % (len(picks), len(slots)))
    return waiting
