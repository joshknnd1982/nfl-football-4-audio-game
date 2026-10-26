"""The league record of a Franchise: 32 teams of 34 players, the current season and the history (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 4 and 10.1. Plain data and rules, no reference to the game, the speech or the files, so the record can be
copied and written whole. A team is its number 1 to 32 (T01 to T32, `game.league.League.team_id`); the season's engine speaks
of a team as a division 1 to 8 and a place 1 to 4, `team_ref` and `team_index` turn one into the other. A player is a `Player`;
a team's roster is a list of 34 player IDs in the order of the original's slots (`data.PLACES`), 0 for an empty place.

`check` is the whole-file check of design 10.1 with the part that fits the stage the record says it is in (B-X49): a record
written in the middle of an offseason has empty places and is not damage, a record in the season must be whole.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from ...game.setup import Roster
from .. import tuning as T
from . import data as D
from . import first_names as FN

log = logging.getLogger("nfl4.extras")

SEASON, OFFSEASON, DRAFT = "season", "offseason", "draft"
STATUSES = ("active", "retired", "released", "free", "practice", "list")
# SR.4 (D-161): "list", a man of a team on one of its real reserve lists (injured reserve and the like, Player.roster_list): on the team, never in a game
# SR.5 (D-164): the status "reserve" of D-149 (the bench) is gone: a man of the team's roster is "active", in a place of the view or not
ON_TEAM = ("active",)                # a player of a team's roster (its chart; the draft's rookies wait outside it for the cut)
# D-136: "practice", a player of a practice squad (practice.py)      # SX.8h: "free", a player whose contract ended and who was not signed again


class LeagueError(ValueError):
    """A record that cannot be used: damage, never clamped silently."""


class NewerFormat(LeagueError):
    """A record saved by a newer version of the game: left alone, not damage (design 10.1)."""


def team_ref(team: int) -> tuple[int, int]:
    """(division 1 to 8, place 1 to 4) of team 1 to 32."""
    return (team - 1) // 4 + 1, (team - 1) % 4 + 1


def team_index(division: int, place: int) -> int:
    return (division - 1) * 4 + place


@dataclass
class Player:
    id: int
    name: str
    pos: str
    rating: int
    potential: str
    age: int
    seasons: int
    peak: int
    drafted: list | None = None          # [season, round, pick] or None
    points: int = 0                      # development points of this season (design 8.2)
    status: str = "active"
    left: int = 0                        # the season he retired or was released
    team: int = 0                        # 1 to 32 while active
    place: int = -1                      # his index in the team's roster while active
    salary: int = 0                      # the contract (SX.8g, format 2): tenths of a million dollars, 0 for a retired or released player
    years: int = 0                       # the seasons left on it, the coming one included
    # SR.4 (format 18, D-161, NX-L2): his real position (one of roster_model.MADDEN; `pos` stays the group word of the Franchise's tables and places
    # until SR.5), his jersey number ("-" for none) and his list ("" the active roster, "PS" the practice squad, a reserve list code of roster_file.RESERVE)
    position: str = ""
    number: str = "-"
    roster_list: str = ""

    def to_list(self) -> list:
        return [self.id, self.name, self.pos, self.rating, self.potential, self.age, self.seasons, self.peak, self.drafted,
                self.points, self.status, self.left, self.team, self.place, self.salary, self.years, self.position, self.number, self.roster_list]

    @classmethod
    def from_list(cls, row, contracts: bool = True) -> "Player":
        """A player from a row of the file: 19 values in format 18, 16 in formats 2 to 17 (a test's downgraded file may keep 19), 14 (no contract)
        in format 1."""
        if not isinstance(row, list) or len(row) not in ((16, 19) if contracts else (14,)):
            raise LeagueError("a player is %r" % (row,))
        return cls(*row)


@dataclass
class LeagueRecord:
    league_id: str = ""
    season: int = 1
    stage: str = SEASON
    stage_no: int = 0                    # OFFSEASON: the number of the stage to run next (D.STAGES keys)
    pick_no: int = 0                     # DRAFT: the next pick (SX.8d)
    coach: str = "coach"
    team: int = 1                        # the player's team
    rosters: list = field(default_factory=lambda: [[0] * D.PLACE_COUNT for _ in range(D.TEAMS)])
    players: dict = field(default_factory=dict)
    next_id: int = 1
    # the current season (the SeasonState values the store keeps in step)
    gtp: int = 1
    schedule: list = field(default_factory=list)       # [division, team, flag] per week
    records: list = field(default_factory=lambda: [0] * 64)   # footbal3.dat's 64 values
    ties: list = field(default_factory=lambda: [0] * D.TEAMS)  # footbal6.dat's 32 values: the season's ties (SX.12, format 11)
    pairings: list = field(default_factory=list)       # footbal4.dat's values
    byes: list = field(default_factory=list)           # footbal5.dat's values
    results: list = field(default_factory=list)        # [stage code, week, winner team, loser team, winner score, loser score]
    sums: list = field(default_factory=list)           # the 32 exact strengths at the start of the season (SX.8b)
    history: list = field(default_factory=list)        # one dict per finished season (history.py)
    told: list = field(default_factory=lambda: [0, 0])  # [season, week] whose season line (NXF-08) was told
    prepared: list = field(default_factory=lambda: [0, 0])  # [season, week] whose preparation (SX.8e: points, news, items) was made
    todo: list = field(default_factory=list)           # the waiting items (SX.8e)
    news: list = field(default_factory=list)           # the season's news (SX.8e)
    news_recent: dict = field(default_factory=dict)    # per news pool, the IDs spoken last (SX.8e)
    draft: dict | None = None                          # the draft in progress (SX.8d)
    dead: list = field(default_factory=lambda: [0] * D.TEAMS)   # per team, the dead money of the cap year (SX.8g, format 2)
    resign: dict | None = None                         # the stage of the expiring contracts in progress (SX.8h, format 3): see resign.py
    market: dict | None = None                         # the stage of free agency in progress (SX.8i, format 4): see market.py
    trades: dict = field(default_factory=lambda: {"picks": [], "log": []})   # the season's trades and the traded picks of the coming draft (SX.8j, format 5): see trades.py
    injuries: dict = field(default_factory=lambda: {"hurt": [], "stand_ins": [], "report": None, "chosen": []})   # the season's injuries (SX.8k, format 6; "chosen" D-143, format 15): see injuries.py
    staff: dict | None = None                          # the head coaches, the coordinators and the stage "the staff" in progress (SX.8l, format 7): see staff.py
    comp: list = field(default_factory=list)           # the compensatory picks awarded for a coming draft (SX.8m, format 8): see comp.py
    future_picks: list = field(default_factory=list)   # the first-round picks owed for the draft after the coming one (SX.8m, format 8): see tags.py
    tags: dict = field(default_factory=lambda: {"history": {}, "open": None, "sheet": None})   # the non-exclusive tag (SX.8m, format 8): see tags.py
    people: dict = field(default_factory=lambda: {"morale": {}, "begun": 0, "holdouts": [], "pending": [], "demands": [], "goal": None, "verdict": None})   # SX.8n, format 9: see people.py
    honors: dict = field(default_factory=lambda: {"awards": [], "hall": []})   # SX.8o, format 10: the awards and the hall of fame (honors.py)
    usage: dict = field(default_factory=lambda: {"season": 0, "games": {}, "carries": {}})   # SX.8o, format 10: the season's games and carries (workload.py)
    practice: dict = field(default_factory=lambda: {"season": 0, "elevations": {}})   # D-136, format 14: practice.py
    depth: dict = field(default_factory=lambda: {"order": {}, "key": {}})   # NX-D3, NX-D4, format 16: the player's depth chart and key players (depth.py)
    calendar: dict | None = None                       # SZ.8, format 12: {"label": str, "weeks": [[[visitor, home], ...], ...]} the real calendar of this season; None: the original's 16 weeks
    cut_deciding: bool = field(default=False, repr=False, compare=False)   # D-130: the roster cut's plans are made and not yet applied (never saved)
    # D-149 (NX-B2b): the league carries the 53-man roster, a bench of up to 19 a team (reserves.py): the program's store sets it on every league it opens or
    # makes, so a league of format 16 or older carries benches from its next cut; never saved. False (the older tests' leagues, made without the store): the
    # cut releases every man over the 34 places and the cap is FR_CAP, as before.
    reserves_on: bool = field(default=False, repr=False, compare=False)
    # SR.4 (format 18, D-161, design 21.6): each team's depth chart on the 22 positions ({position: [player ids], "KR": [...], "PR": [...]}; real_roster.py),
    # the VERSION of the rosters.txt the league was made from or brought up to, and the VERSION whose offer of the newer rosters was answered (SR.6)
    chart: list = field(default_factory=lambda: [{} for _ in range(D.TEAMS)])
    roster_version: str = ""
    roster_offer: str = ""
    loaded_format: int = field(default=0, repr=False, compare=False)      # the format the file was read from (0: made in memory); never saved
    converted: dict | None = field(default=None, repr=False, compare=False)   # what real_roster.convert did when the league was opened (SR.6 says it)

    # ----- the calendar (SZ.8) -----

    @property
    def regular_weeks(self) -> int:
        """Weeks of this season's regular season: the calendar's, else the original's 16."""
        return len(self.calendar["weeks"]) if self.calendar else D.REGULAR_WEEKS

    @property
    def last_prepared_week(self) -> int:
        """The last regular week that has a preparation after it: 15 of the original's 16, 17 of the calendar's 18 (the last game has none, and the play-offs have
        no to-do list). The news, the injuries of the games and the morale count the weeks 1 to this one."""
        return self.regular_weeks - 1

    def games_before(self, week: int) -> int:
        """The regular-season games the whole league has played before this week (the results the record must hold)."""
        if not self.calendar:
            return 16 * max(0, min(week, D.REGULAR_WEEKS + 1) - 1)
        return sum(len(games) for games in self.calendar["weeks"][:max(0, min(week, self.regular_weeks + 1) - 1)])

    def team_games_before(self, team: int, week: int) -> int:
        """The games a team has played before this week: one for each earlier week, except the week of its bye."""
        if not self.calendar:
            return max(0, min(week, D.REGULAR_WEEKS + 1) - 1)
        return sum(1 for games in self.calendar["weeks"][:max(0, min(week, self.regular_weeks + 1) - 1)] if any(team in game for game in games))

    def has_bye(self, team: int, week: int) -> bool:
        """The team has its bye in this week of the calendar (never in a league without one)."""
        if not self.calendar or not 1 <= week <= self.regular_weeks:
            return False
        return not any(team in game for game in self.calendar["weeks"][week - 1])

    # ----- the teams -----

    def roster_ids(self, team: int) -> list:
        return self.rosters[team - 1]

    def player_at(self, team: int, index: int) -> Player | None:
        pid = self.rosters[team - 1][index]
        return self.players.get(pid) if pid else None

    def active_of(self, team: int) -> list:
        """The team's 34 places: a Player or None."""
        return [self.players.get(pid) if pid else None for pid in self.rosters[team - 1]]

    def group_of(self, team: int, position: str) -> list:
        """The players of one position group, in place order (None for an empty place)."""
        return [self.player_at(team, i) for i in D.PLACES_OF[position]]

    def bench(self, team: int, position: str | None = None) -> list:
        """The men of the team's active roster who have no place in the view (SR.5: no status of their own; the draft's rookies apart), of one group or
        all, each group in its chart's order (the staff's: the best first), the groups in D.BENCH_ORDER."""
        order = {pos: n for n, pos in enumerate(D.BENCH_ORDER)}
        chart = self.chart[team - 1] if isinstance(self.chart, list) and len(self.chart) == D.TEAMS and isinstance(self.chart[team - 1], dict) else {}
        found = []
        for key, ids in chart.items():                    # (the chart holds every man of the roster once; real_roster.refresh_view keeps it so)
            if key in ("KR", "PR"):
                continue
            for n, pid in enumerate(ids):
                p = self.players.get(pid)
                if p is not None and p.status == "active" and p.team == team and p.place < 0 and (position is None or p.pos == position):
                    found.append((order.get(p.pos, 99), n, -p.rating, p.id, p))
        return [row[-1] for row in sorted(found, key=lambda row: row[:4])]

    def strength_sum(self, team: int) -> int:
        """The weighted sum of the 34 ratings (design 4.4); an empty place counts as the lowest rating. SR.4 (design 21.7 (8)): an empty BACK place
        counts for nothing and the sum is scaled back to the whole weight (a team with three backs is not weaker for the places that carry nothing);
        with every place filled it is the plain sum, as before."""
        total = weight = 0
        for index, pid in enumerate(self.rosters[team - 1]):
            player = self.players.get(pid) if pid else None
            if player is None and index in D.BACK_PLACES:
                continue
            w = D.WEIGHT[D.POSITION_OF_PLACE[index]]
            total += w * (player.rating if player is not None else D.RATING_MIN)
            weight += w
        if weight == D.WEIGHT_SUM or weight == 0:
            return total
        return (total * D.WEIGHT_SUM + weight // 2) // weight

    def waiting_rookies(self, team: int) -> list:
        """The team's rookies waiting for the cut (stages 4 and 5): drafted, active, without a place, in pick order."""
        if not self.draft:
            return []
        rows = self.draft["picks"] + self.draft.get("undrafted", [])          # SX.8m: and the undrafted free agents in camp
        return [self.players[pid] for t, _, pid in rows if t == team and pid in self.players]

    def rookie_range(self, player: Player) -> tuple:
        """(low end, high end) of the spoken range of a rookie waiting for the cut."""
        for _, index, pid in self.draft["picks"] + self.draft.get("undrafted", []):
            if pid == player.id:
                low = self.draft["class"][index][5]
                return low, low + D.RANGE_SPAN
        raise LeagueError("player %d is no rookie of this draft" % player.id)

    def has_empty_place(self) -> bool:
        """A place of a team waits for a man (stages 2 to 5 of an offseason). SR.4: an empty BACK place is the real roster's (a team with three backs
        has no fourth, design 21.4 (2)), never a wait."""
        return any(pid == 0 for roster in self.rosters for index, pid in enumerate(roster) if index not in D.BACK_PLACES)

    def team_men(self, team: int) -> list:
        """SR.4 (design 21.6): the men of the team's active roster (its places, its bench, its rookies waiting for the cut), by player ID."""
        return sorted((p for p in self.players.values() if p.team == team and p.status == "active"), key=lambda p: p.id)

    def cover_place(self, team: int, index: int):
        """SR.4 (design 21.4 (7)): the nearest filled back place to an empty one (the lower of two equally near), or None when the team has no back."""
        roster = self.rosters[team - 1]
        places = D.BACK_PLACES
        for distance in range(1, len(places)):
            for other in (index - distance, index + distance):
                if other in places and roster[other]:
                    return other
        return None

    def shown_sums(self) -> list:
        """The 32 sums the player is told of (the rating, the rank): the exact sums of the rosters, except while places are empty
        (stages 2 to 5 of an offseason), when the strength is not used (design 4.4, review finding 4 of SX.8c) and the sums kept at
        the start of the season stand in."""
        if self.sums and (self.has_empty_place() or not self.must_be_whole()):     # SR.5: the view fills the places in every stage now
            return list(self.sums)
        return [self.strength_sum(team) for team in range(1, D.TEAMS + 1)]

    def strength(self, team: int) -> int:
        """The spoken rating: the weighted mean rounded half up, integers only."""
        return (self.shown_sums()[team - 1] + D.WEIGHT_SUM // 2) // D.WEIGHT_SUM

    def ranking(self) -> list:
        """The teams 1 to 32 best first by the exact sum, ties by team order (design 4.4)."""
        sums = self.shown_sums()
        return sorted(range(1, D.TEAMS + 1), key=lambda team: (-sums[team - 1], team))

    def rank_of(self, team: int) -> int:
        return self.ranking().index(team) + 1

    # ----- a roster for a game (H7) -----

    def roster_for_game(self, team: int) -> Roster:
        """The team's players as the game's Roster: the names by section, the ratings keyed (section heading, number), the
        quarterback's name. Every place must be filled (the season and stage 1 are)."""
        sections: dict[str, list] = {heading: [] for heading, _, _ in D.PLACES}
        ratings: dict = {}
        quarterback = ""
        for index, (heading, number, _) in enumerate(D.PLACES):
            player = self.player_at(team, index)
            if player is None and index in D.BACK_PLACES:          # SR.4: an empty back place plays as its cover (no share: usage.without_repeats)
                cover = self.cover_place(team, index)
                player = self.player_at(team, cover) if cover is not None else None
            if player is None:
                raise LeagueError("team %d has an empty place %d" % (team, index))
            ratings[(heading, number)] = player.rating
            if heading == "Quarterback:":
                quarterback = player.name
            else:
                sections[heading].append(player.name)
        roster = Roster(sections["Running Backs:"], sections["Receivers:"], sections["Defensive Players:"],
                        sections["Special Teams Players:"], sections["Kickers:"], quarterback=quarterback)
        roster.ratings = ratings
        roster.empty = [(D.PLACES[i][0], D.PLACES[i][1]) for i in D.BACK_PLACES if not self.rosters[team - 1][i]]     # SR.4: no share
        return roster

    # ----- the record in a file -----

    def to_json(self) -> str:
        """SR.5 (format 19): the charts are the teams; the places are the view of them, not saved (a player row's place is -1)."""
        rows = []
        for pid in sorted(self.players):
            row = self.players[pid].to_list()
            row[13] = -1
            rows.append(row)
        data = {"format": D.FORMAT, "game": D.GAME_MARKER, "league_id": self.league_id, "season": self.season,
                "stage": self.stage, "stage_no": self.stage_no, "pick_no": self.pick_no, "coach": self.coach,
                "team": self.team,
                "players": rows, "next_id": self.next_id,
                "gtp": self.gtp, "schedule": self.schedule, "records": self.records, "pairings": self.pairings,
                "byes": self.byes, "results": self.results, "sums": self.sums, "history": self.history, "told": self.told,
                "prepared": self.prepared, "todo": self.todo, "news": self.news, "news_recent": self.news_recent, "draft": self.draft,
                "dead": self.dead, "resign": self.resign, "market": self.market, "trades": self.trades,
                "injuries": self.injuries, "staff": self.staff, "comp": self.comp, "future_picks": self.future_picks, "tags": self.tags,
                "people": self.people, "honors": self.honors, "usage": self.usage, "ties": self.ties, "calendar": self.calendar,
                "practice": self.practice, "depth": self.depth,
                "chart": self.chart, "roster_version": self.roster_version, "roster_offer": self.roster_offer}
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "LeagueRecord":
        """The record a file holds; LeagueError when it is not a whole record (NewerFormat for a higher format)."""
        try:
            data = json.loads(text)
        except (ValueError, TypeError, RecursionError) as exc:
            raise LeagueError("the franchise file is not JSON: %s" % exc) from exc
        if not isinstance(data, dict):
            raise LeagueError("the franchise file is not a record")
        version = data.get("format")
        if isinstance(version, int) and not isinstance(version, bool) and version > D.FORMAT:
            raise NewerFormat("format %d" % version)
        if isinstance(version, bool) or version not in range(D.OLDEST_FORMAT, D.FORMAT + 1) or data.get("game") != D.GAME_MARKER:
            raise LeagueError("the franchise file has format %r and game %r" % (version, data.get("game")))
        record = cls()
        try:
            record.league_id = data["league_id"]
            record.season, record.stage = data["season"], data["stage"]
            record.stage_no, record.pick_no = data["stage_no"], data["pick_no"]
            record.coach, record.team = data["coach"], data["team"]
            if version < 19:
                record.rosters = data["rosters"]                    # SR.5: a file of format 18 or older stores its places (from_places reads them)
            rows = data["players"]
            if not isinstance(rows, list):
                raise LeagueError("the players are %r" % (type(rows).__name__,))
            record.players = {}
            for row in rows:
                player = Player.from_list(row, contracts=version >= 2)
                record.players[player.id] = player
            record.next_id = data["next_id"]
            record.gtp, record.schedule, record.records = data["gtp"], data["schedule"], data["records"]
            record.pairings, record.byes, record.results = data["pairings"], data["byes"], data["results"]
            record.sums, record.history, record.told = data["sums"], data["history"], data["told"]
            record.todo, record.news, record.news_recent = data["todo"], data["news"], data["news_recent"]
            record.prepared = data.get("prepared", [0, 0])         # a league.sav of SX.8a to SX.8d has none: its week is not prepared
            record.draft = data["draft"]
            if version >= 2:
                record.dead = data["dead"]
            if version >= 3:
                record.resign = data["resign"]
            if version >= 4:
                record.market = data["market"]
            if version >= 5:
                record.trades = data["trades"]
            if version >= 6:
                record.injuries = data["injuries"]
                if version < 15 and isinstance(record.injuries, dict) and "chosen" not in record.injuries:
                    record.injuries["chosen"] = []                  # D-143: a file of format 14 or older has no choice of who starts (the staff's rule)
            if version >= 7:
                record.staff = data["staff"]
            if version >= 8:
                record.comp, record.future_picks, record.tags = data["comp"], data["future_picks"], data["tags"]
            if version >= 9:
                record.people = data["people"]                      # SX.8n; a file of format 8 or older: nobody has a morale, nobody held out (the default)
            if version >= 10:
                record.honors, record.usage = data["honors"], data["usage"]     # SX.8o; a file of format 9 or older: no award and nobody in the hall yet,
                #                                                                   no game or carry counted this season (the defaults: a migration with no draw)
            if version >= 11:
                record.ties = data["ties"]                          # SX.12; a file of format 10 or older: no team has a tie (the default)
            if version >= 12:
                record.calendar = data["calendar"]                  # SZ.8; a file of format 11 or older: the original's 16 weeks (the default)
            if version >= 14:
                record.practice = data["practice"]                  # D-136; a file of format 13 or older: no squads yet (formed below in its season)
            if version >= 16:
                record.depth = data["depth"]                        # NX-D3; a file of format 15 or older: the staff's order and the starters (the default)
            if version >= 18:
                record.chart = data["chart"]                        # SR.4; a file of format 17 or older: no chart yet (real_roster.convert makes it)
                record.roster_version, record.roster_offer = data["roster_version"], data["roster_offer"]
            record.loaded_format = version
        except KeyError as exc:
            raise LeagueError("the franchise file lacks %s" % exc) from exc
        except TypeError as exc:
            raise LeagueError("a player of the franchise file is not a record: %s" % exc) from exc
        from . import real_roster
        try:
            if version < 19:
                from . import draft
                draft.migrate_class(record)                     # SR.5: a draft in progress, its prospects' positions (a rookie waiting keeps his)
                real_roster.from_places(record, version)        # SR.5: the stored places and bench become the chart (after their own check)
            if not isinstance(record.chart, list) or len(record.chart) != D.TEAMS or not all(isinstance(c, dict) for c in record.chart):
                raise LeagueError("the depth charts are %r" % (type(record.chart).__name__,))
            for p in record.players.values():
                if not isinstance(p, Player) or not isinstance(p.team, int) or isinstance(p.team, bool) or not isinstance(p.status, str):
                    raise LeagueError("a player of the franchise file is not a record")
                if p.status == "active" and not 1 <= p.team <= D.TEAMS:
                    raise LeagueError("active player %r has the team %r" % (p.id, p.team))
                if p.position and p.position not in real_roster.RM.MADDEN:
                    raise LeagueError("player %r has the position %r" % (p.id, p.position))
                if not p.position and p.status in ("active", "practice", "list"):
                    real_roster.give_positions(record)
            if version >= 19:                                   # the file's charts as written: damage is refused, never cleaned silently
                def whole(value, low, high, what):
                    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                        raise LeagueError("%s is %r" % (what, value))
                real_roster.check_charts(record, whole)
                from . import draft as draft_rules
                real_roster.check_teams(record, draft_rules.check_draft(record, whole))     # (a damaged draft is told as itself first)
            real_roster.refresh_all(record)                     # SR.5: the 34 places of every team, made from its chart
        except (TypeError, AttributeError, KeyError, IndexError) as exc:
            raise LeagueError("the franchise's rosters are not whole: %r" % (exc,)) from exc
        if version < 12:                                                 # SZ.8: the offseason's news lines were week 16; 16 is a regular week of the calendar now
            for line in record.news if isinstance(record.news, list) else ():
                if isinstance(line, dict) and line.get("week") == 16:
                    line["week"] = D.NEWS_OFFSEASON
        if version < 5 and isinstance(record.draft, dict) and isinstance(record.draft.get("order"), list) and "owners" not in record.draft:
            # a draft saved before SX.8j has no owners: every pick is the team's of the draft order (no trade moved one), the migration of format 5
            # (made first: the check of every older format reads the owners of a draft in progress)
            order = record.draft["order"]
            record.draft["owners"] = [order[i % len(order)] for i in range(D.DRAFT_PICKS)] if order else []
        if version < 8:
            # a file of format 7 or older (SX.8m, the migration of format 8): no compensatory pick was ever awarded and no tag history kept (`comp`,
            # `future_picks` and `tags` keep their empty defaults); a market in progress has no moves recorded and a draft in progress no compensatory picks
            if isinstance(record.market, dict) and "moves" not in record.market:
                record.market["moves"] = []
            if isinstance(record.draft, dict) and "comp" not in record.draft:
                record.draft["comp"] = []
            if isinstance(record.draft, dict) and "undrafted" not in record.draft:
                record.draft["undrafted"] = []
        if version < 7:
            # a file of format 6 or older has no staff: a new league's staff (no draw), made before any check, which reads the staff (the migration of format 7)
            from . import staff as staff_rules
            staff_rules.migrate(record)
        if version < 2:
            record.check(contracts=False)                      # a format-1 file is whole as it was; then it gets its contracts (a migration, no draw)
            from . import contracts
            contracts.migrate(record)
        # a format-2 file has no stage of expiring contracts in progress, a format-3 file no market in progress and a format-4 file no trades (`resign` and
        # `market` None, `trades` empty, from the dataclass defaults): nothing to migrate but a draft's owners (below). A league written before the stage of free agency existed and saved in the middle of the offseason is
        # at a stage number of its own list, so it goes on at that stage (the market is simply not held for it)
        record.check()
        if version < 13:
            give_first_names(record, skip_team=record.team)    # D-131: a league of 0.12.0 or older has bare drawn surnames (once; no draw)
        if version < 14 and record.stage == SEASON:
            from . import practice
            practice.form(record)                               # D-136: a league in its season gets its practice squads at once (no draw)
            record.check()
        return record

    # ----- the whole-file check, by stage (design 10.1, B-X49) -----

    def must_be_whole(self) -> bool:
        """The stages in which every place of every team is filled: the season, stage 1 and stage 6 on."""
        if self.stage == SEASON:
            return True
        return self.stage == OFFSEASON and self.stage_no in (D.STAGE_REVIEW, D.STAGE_STAFF, D.STAGE_NEW_SEASON)

    def check(self, contracts: bool = True) -> None:
        """LeagueError (with what is wrong) unless the record is usable at the stage it says it is in. `contracts` is False only for a
        format-1 file that has not been migrated yet."""
        def whole(value, low, high, what):
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise LeagueError("%s is %r" % (what, value))

        def ints(values, count, low, high, what):
            if not isinstance(values, list) or (count is not None and len(values) != count):
                raise LeagueError("%s is %r" % (what, values if len(str(values)) < 60 else str(values)[:60]))
            for value in values:
                whole(value, low, high, what)

        if not isinstance(self.league_id, str) or not 1 <= len(self.league_id) <= 40:
            raise LeagueError("the league ID is %r" % (self.league_id,))
        whole(self.season, 1, D.MAX_SEASONS, "the season")
        if self.stage not in (SEASON, OFFSEASON, DRAFT):
            raise LeagueError("the stage is %r" % (self.stage,))
        whole(self.stage_no, 0, D.STAGE_MAX, "the stage number")
        whole(self.pick_no, 0, 400, "the pick")
        if self.stage == OFFSEASON and self.stage_no not in {number for number, _ in D.STAGES}:
            raise LeagueError("the offseason stage %r is not one of this version's" % (self.stage_no,))
        if not isinstance(self.coach, str) or not 1 <= len(self.coach) <= 60:
            raise LeagueError("the coach is %r" % (self.coach,))
        whole(self.team, 1, D.TEAMS, "the player's team")
        self._check_players(whole)
        from . import draft
        waiting = draft.check_draft(self, whole)               # the rookies waiting for the cut (stages 4 and 5 only)
        self._check_rosters(whole, waiting)
        if contracts:
            from . import contracts as contract_rules
            contract_rules.check_contracts(self, whole)         # SX.8g: every contract is in range (the rules are the simulation's CP1 to CP5)
        self._check_history(whole)
        from . import news, todo
        todo.check_items(self, whole)                       # the to-do list (SX.8e: each item's kind, week, state and values)
        news.check_entries(self, whole)                     # and the news with its history of lines told last
        ints(self.told, 2, 0, D.MAX_SEASONS, "the told mark")
        ints(self.prepared, 2, 0, D.MAX_SEASONS, "the prepared mark")
        if self.sums:
            ints(self.sums, D.TEAMS, 0, 78 * 99, "the strengths")
        if self.draft is not None and not isinstance(self.draft, dict):
            raise LeagueError("the draft is %r" % (type(self.draft).__name__,))
        from . import resign as resign_rules
        resign_rules.check_resign(self, whole)                 # SX.8h: the stage of the expiring contracts in progress
        from . import market as market_rules
        market_rules.check_market(self, whole)                 # SX.8i: the stage of free agency in progress
        from . import trades as trade_rules
        trade_rules.check_trades(self, whole)                  # SX.8j: the season's trades and the traded picks of the coming draft
        from . import injuries as injury_rules
        injury_rules.check_injuries(self, whole)               # SX.8k: the season's injuries, the stand-ins and the week's report
        from . import staff as staff_rules
        staff_rules.check_staff(self, whole)                   # SX.8l: the head coaches, the coordinators and the stage of the staff in progress
        from . import comp as comp_rules, tags as tag_rules
        comp_rules.check_comp(self, whole)                     # SX.8m: the compensatory picks awarded for a coming draft
        tag_rules.check_tags(self, whole)                      # SX.8m: the non-exclusive tag and the first-round picks owed
        from . import people as people_rules
        people_rules.check_people(self, whole)                 # SX.8n: the morale, the camp's holdouts, the trade demands, the game goal
        from . import honors as honor_rules, workload as workload_rules
        honor_rules.check_honors(self, whole)                  # SX.8o: the awards and the hall of fame
        workload_rules.check_usage(self, whole)                # SX.8o: the season's games and carries
        from . import practice as practice_rules
        practice_rules.check(self, whole)                      # D-136: the practice squads
        from . import depth as depth_rules
        depth_rules.check(self, whole)                         # NX-D3, NX-D4: the player's depth chart and key players
        self._check_results(whole)
        self._check_season(whole, ints)

    def _check_players(self, whole) -> None:
        if not isinstance(self.players, dict):
            raise LeagueError("the players are not a table")
        whole(self.next_id, 1, 10 ** 9, "the next player ID")
        for pid, p in self.players.items():
            whole(p.id, 1, 10 ** 9, "a player ID")
            if p.id != pid or p.id >= self.next_id:
                raise LeagueError("player ID %r is out of order" % (p.id,))
            if not isinstance(p.name, str) or not 1 <= len(p.name) <= 40 or any(ord(c) < 32 for c in p.name):
                raise LeagueError("player %d has the name %r" % (p.id, p.name))
            if p.pos not in D.ALL_POSITIONS or p.potential not in D.POTENTIALS or p.status not in STATUSES:
                raise LeagueError("player %d has position %r, potential %r, status %r" % (p.id, p.pos, p.potential, p.status))
            from .real_roster import check_player
            check_player(p)                                            # SR.4: the position, the number, the list
            if p.status == "list" and (isinstance(p.team, bool) or not isinstance(p.team, int) or not 1 <= p.team <= D.TEAMS or p.place != -1):
                raise LeagueError("player %d on a reserve list has team %r and place %r" % (p.id, p.team, p.place))
            whole(p.rating, D.RATING_MIN, D.RATING_MAX, "the rating of player %d" % p.id)
            whole(p.peak, D.RATING_MIN, D.RATING_MAX, "the peak of player %d" % p.id)
            whole(p.age, D.AGE_MIN, D.AGE_MAX, "the age of player %d" % p.id)
            whole(p.seasons, 0, 99, "the seasons of player %d" % p.id)
            whole(p.points, 0, 3, "the development points of player %d" % p.id)
            whole(p.left, 0, D.MAX_SEASONS, "the leaving season of player %d" % p.id)
            if p.drafted is not None:
                if not isinstance(p.drafted, list) or len(p.drafted) != 3:
                    raise LeagueError("player %d was drafted %r" % (p.id, p.drafted))
                whole(p.drafted[0], 1, D.MAX_SEASONS, "the draft season")
                whole(p.drafted[1], 1, 7, "the draft round")
                whole(p.drafted[2], 1, 400, "the draft pick")

    def _check_rosters(self, whole, waiting=frozenset()) -> None:
        """SR.5 (D-164): the charts are the teams (real_roster.check_teams: every active man once at his own position, the roles on the team, at most
        the camp's limit); the places are their view in memory: a place holds an active man of the team with that place, of a group the place may hold,
        in no other place, never a rookie waiting for the cut; in the stages that must be whole only an empty BACK place is allowed (design 21.4 (2))."""
        from . import real_roster
        real_roster.check_charts(self, whole)
        real_roster.check_teams(self, waiting)
        if not isinstance(self.rosters, list) or len(self.rosters) != D.TEAMS:
            raise LeagueError("the league has %r rosters" % (len(self.rosters) if isinstance(self.rosters, list) else None))
        placed: set = set()
        for team, roster in enumerate(self.rosters, start=1):
            if not isinstance(roster, list) or len(roster) != D.PLACE_COUNT:
                raise LeagueError("team %d has a roster of %r" % (team, len(roster) if isinstance(roster, list) else None))
            for index, pid in enumerate(roster):
                whole(pid, 0, 10 ** 9, "a place of team %d" % team)
                if pid == 0:
                    if self.must_be_whole() and index not in D.BACK_PLACES:
                        raise LeagueError("team %d has an empty place %d" % (team, index))
                    continue
                player = self.players.get(pid)
                if player is None or player.status != "active" or player.team != team or player.place != index or pid in waiting:
                    raise LeagueError("place %d of team %d holds player %d, who is not active there" % (index, team, pid))
                if pid in placed:
                    raise LeagueError("player %d is in two places" % pid)
                group = D.POSITION_OF_PLACE[index]
                if player.pos != group and player.pos not in D.PLACE_COVERS.get(group, ()):    # a 3-4 edge man at linebacker, a returner
                    raise LeagueError("player %d plays %s in a %s place" % (pid, player.pos, group))
                placed.add(pid)
        for pid, player in self.players.items():
            if player.place >= 0 and pid not in placed:
                raise LeagueError("player %d has the place %d but holds none" % (pid, player.place))

    def _check_history(self, whole) -> None:
        if not isinstance(self.history, list) or len(self.history) > D.MAX_HISTORY:
            raise LeagueError("the history is %r" % (type(self.history).__name__,))
        previous = 0
        for entry in self.history:
            from . import history
            history.check_entry(entry, whole)
            if entry["season"] <= previous:
                raise LeagueError("the history seasons are out of order at %r" % (entry["season"],))
            previous = entry["season"]

    def _check_results(self, whole) -> None:
        if not isinstance(self.results, list) or len(self.results) > D.MAX_RESULTS:
            raise LeagueError("the season's results are %r" % (type(self.results).__name__,))
        for row in self.results:
            if not isinstance(row, list) or len(row) != 6:
                raise LeagueError("a result is %r" % (row,))
            whole(row[0], 0, 4, "a result's round")
            whole(row[1], 1, D.MAX_REGULAR_WEEKS + 4, "a result's week")
            whole(row[2], 1, D.TEAMS, "a result's winner")
            whole(row[3], 1, D.TEAMS, "a result's loser")
            whole(row[4], 0, 200, "a result's score")
            whole(row[5], 0, 200, "a result's score")
            if row[2] == row[3]:
                raise LeagueError("a team played itself: %r" % (row,))
            if row[4] == row[5] and row[0] != 0:                   # SX.12: equal scores are a tie, only in a regular week (16-1-4 (d))
                raise LeagueError("a tied play-off game: %r" % (row,))

    def _check_season(self, whole, ints) -> None:
        in_season = self.stage == SEASON
        at_review = self.stage == OFFSEASON and self.stage_no == D.STAGE_REVIEW
        if not (in_season or at_review):
            return                                         # stages 2 to 6 of an offseason: the season is over, the next not made
        self._check_calendar(whole)
        regular = self.regular_weeks
        whole(self.gtp, 0, regular + 4, "the week")           # 0: the season is over (the engine writes it when the player is out)
        if self.schedule:
            if not isinstance(self.schedule, list) or len(self.schedule) != regular:
                raise LeagueError("the schedule holds %r weeks" % (len(self.schedule) if isinstance(self.schedule, list) else None))
            for week, entry in enumerate(self.schedule, start=1):
                if not isinstance(entry, list) or len(entry) != 3:
                    raise LeagueError("a schedule week is %r" % (entry,))
                if self.calendar and entry == [0, 0, 0]:             # the bye week of the calendar (and only where the calendar says so)
                    if not self.has_bye(self.team, week):
                        raise LeagueError("week %d of the schedule is a bye but the calendar has the team's game there" % week)
                    continue
                whole(entry[0], 1, 8, "a schedule division")
                whole(entry[1], 1, 4, "a schedule team")
                whole(entry[2], 1, 2, "a schedule flag")
                if self.calendar and self.has_bye(self.team, week):
                    raise LeagueError("week %d of the schedule has a game but the calendar gives the team its bye" % week)
        elif in_season and self.gtp != 1:
            raise LeagueError("the season has no schedule")          # week 1 may be written before makes has made one
        ints(self.records, 64, 0, 20, "the records")
        ints(self.ties, D.TEAMS, 0, 17, "the ties")
        for team in range(D.TEAMS):
            weeks = self.team_games_before(team + 1, regular + 1 if self.gtp == 0 or self.gtp > regular else self.gtp)
            if self.records[2 * team] + self.records[2 * team + 1] + self.ties[team] != weeks:
                raise LeagueError("team %d has %d wins and %d losses and %d ties after %d games" %
                                  (team + 1, self.records[2 * team], self.records[2 * team + 1], self.ties[team], weeks))
        if not isinstance(self.pairings, list) or len(self.pairings) > 24 or len(self.pairings) % 4:      # 24: the N. F. L.'s six wild card games (D-129)
            raise LeagueError("the pairings hold %r values" % (len(self.pairings) if isinstance(self.pairings, list) else None))
        for index, value in enumerate(self.pairings):
            whole(value, 1, 8 if index % 2 == 0 else 4, "a pairing value")
        if not isinstance(self.byes, list) or len(self.byes) > 8 or len(self.byes) % 2:
            raise LeagueError("the byes hold %r values" % (len(self.byes) if isinstance(self.byes, list) else None))
        for index, value in enumerate(self.byes):
            whole(value, 1, 8 if index % 2 == 0 else 4, "a bye value")
        if in_season and self.gtp > 0:                       # the games of the coming round (finding 3 of the SX.8a review)
            real = self.real_bracket()                       # D-129: the N. F. L.'s 14 teams (2 byes, 6 wild card games) on the real calendar
            games = {1: 6 if real else 4, 2: 4, 3: 2, 4: 1}.get(self.gtp - regular, 0)     # round 1 is the wild card week: 17 in the original, the calendar's 19
            if len(self.pairings) != 4 * games:
                raise LeagueError("week %d has %d play-off games, not %d" % (self.gtp, len(self.pairings) // 4, games))
            byes = 4 if real else 8
            if self.gtp - regular in (1, 2) and len(self.byes) != byes:
                raise LeagueError("week %d has %d teams with a bye, not %d" % (self.gtp, len(self.byes) // 2, byes // 2))

    def real_bracket(self) -> bool:
        """The season's play-offs are the N. F. L.'s 14 teams (D-129): a season on the real calendar whose byes, once written, are the two seeds 1
        (a league saved in the play-offs by version 0.12.1, with the original's four, finishes the bracket it began)."""
        return bool(self.calendar) and len(self.byes) != 8

    def _check_calendar(self, whole) -> None:
        """The calendar of the season, when there is one: a label and the weeks of (visitor, home) games, every team once at most in a week, 17 games and
        one bye for every team, the same teams in a week never twice. Only a whole calendar is kept; a damaged one is a damaged file."""
        if self.calendar is None:
            return
        calendar = self.calendar
        if not isinstance(calendar, dict) or set(calendar) != {"label", "weeks"} or not isinstance(calendar["label"], str) or len(calendar["label"]) > 120:
            raise LeagueError("the calendar is %r" % (type(calendar).__name__,))
        weeks = calendar["weeks"]
        if not isinstance(weeks, list) or len(weeks) != 18:
            raise LeagueError("the calendar holds %r weeks" % (len(weeks) if isinstance(weeks, list) else None))
        played = [0] * (D.TEAMS + 1)
        for number, games in enumerate(weeks, start=1):
            if not isinstance(games, list) or not 1 <= len(games) <= 16:
                raise LeagueError("week %d of the calendar holds %r games" % (number, len(games) if isinstance(games, list) else None))
            seen: set = set()
            for game in games:
                if not isinstance(game, list) or len(game) != 2:
                    raise LeagueError("a game of the calendar is %r" % (game,))
                for team in game:
                    whole(team, 1, D.TEAMS, "a team of the calendar")
                    if team in seen:
                        raise LeagueError("team %d plays twice in week %d of the calendar" % (team, number))
                    seen.add(team)
                    played[team] += 1
                if game[0] == game[1]:
                    raise LeagueError("a team plays itself in week %d of the calendar" % number)
        if any(played[team] != 17 for team in range(1, D.TEAMS + 1)):
            raise LeagueError("the calendar gives the teams %r games, not 17" % (sorted({played[team] for team in range(1, D.TEAMS + 1)}),))


# ----- a new league (design 4.5, 12.1) -----

def draw_name(rnd, surnames: list, used: set) -> str:
    """rnd(1708) again while an active player of the league has the name (bounded, G-D1: then the first free name in the
    pool's order, then any name). The new league, the fill and (SX.8d) the draft class name their players with it."""
    def scan() -> int:
        for number, name in enumerate(surnames, start=1):
            if name not in used:
                return number
        return 1

    if used.issuperset(surnames):
        # D-149: a league of 53-man rosters can hold more made-up men than the pool has surnames. Every redraw would fail (10,000 draws, then the
        # first of the pool): one draw gives a surname in use, as the fallback does, without the wasted draws. A league of 34 places never gets here.
        return surnames[rnd(len(surnames)) - 1]
    number = rnd.redraw(lambda: rnd(len(surnames)), lambda n: surnames[n - 1] not in used, scan, "a franchise player's name")
    return surnames[number - 1]


_SHIPPED_SURNAMES: frozenset | None = None


def _shipped_surnames() -> frozenset:
    """The original's surnames (the ones with a space are told from a real or a full name by this list); empty when the file cannot be read."""
    global _SHIPPED_SURNAMES
    if _SHIPPED_SURNAMES is None:
        try:
            from ...game.names import load_surnames
            _SHIPPED_SURNAMES = frozenset(load_surnames())
        except (OSError, ValueError, UnicodeError):
            log.warning("first names: the original surnames could not be read; only one-word names get a first name")
            _SHIPPED_SURNAMES = frozenset()
    return _SHIPPED_SURNAMES


def give_first_names(league: "LeagueRecord", skip_team: int | None = None) -> int:
    """D-131, the migration of format 13: every made-up player of the league (players, the draft class in progress, the stand-ins) whose name
    is a bare drawn surname gets his first name (first_names.full_name: no draw); a real player's name and a full name are left. The players
    of `skip_team` (the player's own team: footplay.txt's names and his renames are his) are left too. Returns how many changed."""
    surnames = _shipped_surnames()
    lid = league.league_id
    changed = 0
    for player in league.players.values():
        if player.team != skip_team and FN.needs_first_name(player.name, surnames):
            player.name = FN.full_name(lid, player.name)
            changed += 1
    draft = league.draft
    if isinstance(draft, dict) and isinstance(draft.get("class"), list):
        for row in draft["class"]:
            if isinstance(row, list) and len(row) > 1 and FN.needs_first_name(row[1], surnames):
                row[1] = FN.full_name(lid, row[1])
                changed += 1
    injuries = league.injuries
    if isinstance(injuries, dict) and isinstance(injuries.get("stand_ins"), list):
        for row in injuries["stand_ins"]:
            if isinstance(row, list) and len(row) > 2 and FN.needs_first_name(row[2], surnames):
                row[2] = FN.full_name(lid, row[2])
                changed += 1
    if changed:
        log.info("first names: %d made-up players of franchise %s got a first name (D-131)", changed, lid)
    return changed


def _clamp(value: int) -> int:
    return max(D.RATING_MIN, min(D.RATING_MAX, value))


def draw_potential(rnd) -> str:
    roll = rnd.below(100)
    high, average = T.FR_POTENTIAL_SHARES
    return "high" if roll < high else "average" if roll < average else "low"


def use_real_names(league: "LeagueRecord", real, own_team: int, given: list | None) -> int:
    """SX.11 (NX-N5): the names the new league drew are replaced by the real players of the 32 teams, place by place (`real.places`), after
    all the draws, so a league has exactly the ratings, ages and draws it has with the original's names. The player's own team keeps the
    names of `given` (his footplay.txt is his); a real name another player of the league already has stays with the first, and the place
    keeps its drawn surname. Returns how many players got a real name."""
    assigned: set = set()
    if given:
        assigned |= {name.casefold() for name in given if name}
    count = 0
    for t in range(1, D.TEAMS + 1):
        for index, name in enumerate(real.places(t)):
            if not name or (t == own_team and given is not None and given[index] is not None) or name.casefold() in assigned:
                continue
            player = league.player_at(t, index)
            if player is None:
                continue
            player.name = name
            assigned.add(name.casefold())
            count += 1
    return count


def new_league(rnd, surnames: list, coach: str, team: int, league_id: str, own_names: Roster | None = None, team_styles=None,
               real=None) -> LeagueRecord:
    """A new league (design 4.5): the player's team first, with the 33 names of `own_names` when it is a complete roster (and
    its quarterback when it names one), then T01 to T32 without it; every other value is drawn, in the order of design 12.1. `team_styles`: the
    playbooks' assignment of the 32 teams the coordinators start with (SX.8l; None: the built-in one). `real` (SX.11): the real names
    (extras.real_names.RealNames) the players and the other teams' head coaches get; None: the drawn surnames, as before."""
    if team_styles is None:
        from ..playbook_data import TEAM_STYLES as team_styles
    league = LeagueRecord(league_id=league_id, season=1, stage=SEASON, coach=coach, team=team)
    used: set = set()
    given: list | None = None
    if own_names is not None and own_names.is_complete():
        given = own_names.names() + [own_names.quarterback or None]
    for t in [team] + [other for other in range(1, D.TEAMS + 1) if other != team]:
        level = rnd.below(T.FR_TEAM_LEVEL_SPAN) + T.FR_TEAM_LEVEL_LOW
        own = t == team and given is not None
        for index, (_, _, position) in enumerate(D.PLACES):
            if own and given[index] is not None:
                name = given[index]
            else:
                name = draw_name(rnd, surnames, used)
            used.add(name)
            if not (own and given[index] is not None):
                name = FN.full_name(league_id, name)            # D-131: a drawn player has a first name too (no draw)
            rating = _clamp(T.FR_RATING_BASE + rnd.below(T.FR_RATING_DRAW) + rnd.below(T.FR_RATING_DRAW) + level)
            potential = draw_potential(rnd)
            base, first, second, third = T.FR_START_AGE
            age = base + rnd.below(first) + rnd.below(second) + rnd.below(third)
            if position in ("K", "P"):
                age += rnd.below(T.FR_START_AGE_KICKER)
            age = max(D.AGE_MIN, min(D.AGE_MAX, age))
            player = Player(league.next_id, name, position, rating, potential, age, max(0, age - 22), rating, None, 0,
                            "active", 0, t, index)
            league.players[player.id] = player
            league.rosters[t - 1][index] = player.id
            league.next_id += 1
    from . import real_roster
    made = False
    if real is not None:
        made = bool(real_roster.make_real(league, real, [team] + [other for other in range(1, D.TEAMS + 1) if other != team]))
        if not made:
            use_real_names(league, real, team, given)           # SX.11: the real players, after the draws (an older rosters.txt of the player's)
        # SR.4 (NX-L4): a layout-2 rosters.txt makes every team its real roster, the player's too (his footplay.txt names were the real ones)
    if not made:
        real_roster.from_places(league, D.FORMAT)               # SR.5: the drawn places become the charts (an older rosters.txt, or no real names)
        if real is not None:
            real_roster.starters_first(league)                  # NX-D2, NX-D3: each position's best drawn rating to its real starter (no draw)
    real_roster.refresh_all(league)                             # SR.5: the 34 places are the view of the charts
    from . import contracts
    contracts.give_initial_contracts(league)                    # SX.8g: the market price of each player; no draw
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    from . import staff
    if real is None:
        staff.new_staff(league, surnames, team_styles)          # SX.8l: the head coaches and the coordinators, the goals of season 1; no draw
    else:
        staff.new_staff(league, surnames, team_styles, real)    # SX.11: the other teams' head coaches are the real ones
    return league
