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
from dataclasses import dataclass, field

from ...game.setup import Roster
from .. import tuning as T
from . import data as D

SEASON, OFFSEASON, DRAFT = "season", "offseason", "draft"
STATUSES = ("active", "retired", "released", "free")      # SX.8h: "free", a player whose contract ended and who was not signed again


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

    def to_list(self) -> list:
        return [self.id, self.name, self.pos, self.rating, self.potential, self.age, self.seasons, self.peak, self.drafted,
                self.points, self.status, self.left, self.team, self.place, self.salary, self.years]

    @classmethod
    def from_list(cls, row, contracts: bool = True) -> "Player":
        """A player from a row of the file: 16 values in format 2, 14 (no contract) in format 1."""
        if not isinstance(row, list) or len(row) != (16 if contracts else 14):
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
    injuries: dict = field(default_factory=lambda: {"hurt": [], "stand_ins": [], "report": None})   # the season's injuries (SX.8k, format 6): see injuries.py
    staff: dict | None = None                          # the head coaches, the coordinators and the stage "the staff" in progress (SX.8l, format 7): see staff.py

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

    def strength_sum(self, team: int) -> int:
        """The weighted sum of the 34 ratings (design 4.4); an empty place counts as the lowest rating."""
        total = 0
        for index, pid in enumerate(self.rosters[team - 1]):
            player = self.players.get(pid) if pid else None
            total += D.WEIGHT[D.POSITION_OF_PLACE[index]] * (player.rating if player is not None else D.RATING_MIN)
        return total

    def waiting_rookies(self, team: int) -> list:
        """The team's rookies waiting for the cut (stages 4 and 5): drafted, active, without a place, in pick order."""
        if not self.draft:
            return []
        return [self.players[pid] for t, _, pid in self.draft["picks"] if t == team and pid in self.players]

    def rookie_range(self, player: Player) -> tuple:
        """(low end, high end) of the spoken range of a rookie waiting for the cut."""
        for _, index, pid in self.draft["picks"]:
            if pid == player.id:
                low = self.draft["class"][index][5]
                return low, low + D.RANGE_SPAN
        raise LeagueError("player %d is no rookie of this draft" % player.id)

    def has_empty_place(self) -> bool:
        return any(pid == 0 for roster in self.rosters for pid in roster)

    def shown_sums(self) -> list:
        """The 32 sums the player is told of (the rating, the rank): the exact sums of the rosters, except while places are empty
        (stages 2 to 5 of an offseason), when the strength is not used (design 4.4, review finding 4 of SX.8c) and the sums kept at
        the start of the season stand in."""
        if self.sums and self.has_empty_place():
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
        return roster

    # ----- the record in a file -----

    def to_json(self) -> str:
        data = {"format": D.FORMAT, "game": D.GAME_MARKER, "league_id": self.league_id, "season": self.season,
                "stage": self.stage, "stage_no": self.stage_no, "pick_no": self.pick_no, "coach": self.coach,
                "team": self.team, "rosters": self.rosters,
                "players": [self.players[pid].to_list() for pid in sorted(self.players)], "next_id": self.next_id,
                "gtp": self.gtp, "schedule": self.schedule, "records": self.records, "pairings": self.pairings,
                "byes": self.byes, "results": self.results, "sums": self.sums, "history": self.history, "told": self.told,
                "prepared": self.prepared, "todo": self.todo, "news": self.news, "news_recent": self.news_recent, "draft": self.draft,
                "dead": self.dead, "resign": self.resign, "market": self.market, "trades": self.trades,
                "injuries": self.injuries, "staff": self.staff}
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
            record.rosters = data["rosters"]
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
            if version >= 7:
                record.staff = data["staff"]
        except KeyError as exc:
            raise LeagueError("the franchise file lacks %s" % exc) from exc
        except TypeError as exc:
            raise LeagueError("a player of the franchise file is not a record: %s" % exc) from exc
        if version < 5 and isinstance(record.draft, dict) and isinstance(record.draft.get("order"), list) and "owners" not in record.draft:
            # a draft saved before SX.8j has no owners: every pick is the team's of the draft order (no trade moved one), the migration of format 5
            # (made first: the check of every older format reads the owners of a draft in progress)
            order = record.draft["order"]
            record.draft["owners"] = [order[i % len(order)] for i in range(D.DRAFT_PICKS)] if order else []
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
            if p.pos not in D.POSITIONS or p.potential not in D.POTENTIALS or p.status not in STATUSES:
                raise LeagueError("player %d has position %r, potential %r, status %r" % (p.id, p.pos, p.potential, p.status))
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
        if not isinstance(self.rosters, list) or len(self.rosters) != D.TEAMS:
            raise LeagueError("the league has %r rosters" % (len(self.rosters) if isinstance(self.rosters, list) else None))
        placed: set = set()
        for team, roster in enumerate(self.rosters, start=1):
            if not isinstance(roster, list) or len(roster) != D.PLACE_COUNT:
                raise LeagueError("team %d has a roster of %r" % (team, len(roster) if isinstance(roster, list) else None))
            for index, pid in enumerate(roster):
                whole(pid, 0, 10 ** 9, "a place of team %d" % team)
                if pid == 0:
                    if self.must_be_whole():
                        raise LeagueError("team %d has an empty place %d" % (team, index))
                    continue
                player = self.players.get(pid)
                if player is None or player.status != "active" or player.team != team or player.place != index:
                    raise LeagueError("place %d of team %d holds player %d, who is not active there" % (index, team, pid))
                if pid in placed:
                    raise LeagueError("player %d is in two places" % pid)
                if player.pos != D.POSITION_OF_PLACE[index]:
                    raise LeagueError("player %d plays %s in a %s place" % (pid, player.pos, D.POSITION_OF_PLACE[index]))
                placed.add(pid)
        for pid, player in self.players.items():
            if (player.status == "active") != (pid in placed or pid in waiting):
                raise LeagueError("player %d is %s but %s" % (pid, player.status, "placed" if pid in placed else "not placed"))

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
            whole(row[1], 1, 20, "a result's week")
            whole(row[2], 1, D.TEAMS, "a result's winner")
            whole(row[3], 1, D.TEAMS, "a result's loser")
            whole(row[4], 0, 200, "a result's score")
            whole(row[5], 0, 200, "a result's score")
            if row[2] == row[3]:
                raise LeagueError("a team played itself: %r" % (row,))

    def _check_season(self, whole, ints) -> None:
        in_season = self.stage == SEASON
        at_review = self.stage == OFFSEASON and self.stage_no == D.STAGE_REVIEW
        if not (in_season or at_review):
            return                                         # stages 2 to 6 of an offseason: the season is over, the next not made
        whole(self.gtp, 0, 20, "the week")                    # 0: the season is over (the engine writes it when the player is out)
        if self.schedule:
            if not isinstance(self.schedule, list) or len(self.schedule) != 16:
                raise LeagueError("the schedule holds %r weeks" % (len(self.schedule) if isinstance(self.schedule, list) else None))
            for entry in self.schedule:
                if not isinstance(entry, list) or len(entry) != 3:
                    raise LeagueError("a schedule week is %r" % (entry,))
                whole(entry[0], 1, 8, "a schedule division")
                whole(entry[1], 1, 4, "a schedule team")
                whole(entry[2], 1, 2, "a schedule flag")
        elif in_season and self.gtp != 1:
            raise LeagueError("the season has no schedule")          # week 1 may be written before makes has made one
        ints(self.records, 64, 0, 20, "the records")
        weeks = 16 if self.gtp == 0 or self.gtp > 16 else self.gtp - 1
        for team in range(D.TEAMS):
            if self.records[2 * team] + self.records[2 * team + 1] != weeks:
                raise LeagueError("team %d has %d wins and %d losses after %d weeks" %
                                  (team + 1, self.records[2 * team], self.records[2 * team + 1], weeks))
        if not isinstance(self.pairings, list) or len(self.pairings) > 16 or len(self.pairings) % 4:
            raise LeagueError("the pairings hold %r values" % (len(self.pairings) if isinstance(self.pairings, list) else None))
        for index, value in enumerate(self.pairings):
            whole(value, 1, 8 if index % 2 == 0 else 4, "a pairing value")
        if not isinstance(self.byes, list) or len(self.byes) > 8 or len(self.byes) % 2:
            raise LeagueError("the byes hold %r values" % (len(self.byes) if isinstance(self.byes, list) else None))
        for index, value in enumerate(self.byes):
            whole(value, 1, 8 if index % 2 == 0 else 4, "a bye value")
        if in_season and self.gtp > 0:                       # the games of the coming round (finding 3 of the SX.8a review)
            games = {17: 4, 18: 4, 19: 2, 20: 1}.get(self.gtp, 0)
            if len(self.pairings) != 4 * games:
                raise LeagueError("week %d has %d play-off games, not %d" % (self.gtp, len(self.pairings) // 4, games))
            if self.gtp in (17, 18) and len(self.byes) != 8:
                raise LeagueError("week %d has %d teams with a bye, not 4" % (self.gtp, len(self.byes) // 2))


# ----- a new league (design 4.5, 12.1) -----

def draw_name(rnd, surnames: list, used: set) -> str:
    """rnd(1708) again while an active player of the league has the name (bounded, G-D1: then the first free name in the
    pool's order, then any name). The new league, the fill and (SX.8d) the draft class name their players with it."""
    def scan() -> int:
        for number, name in enumerate(surnames, start=1):
            if name not in used:
                return number
        return 1

    number = rnd.redraw(lambda: rnd(len(surnames)), lambda n: surnames[n - 1] not in used, scan, "a franchise player's name")
    return surnames[number - 1]


def _clamp(value: int) -> int:
    return max(D.RATING_MIN, min(D.RATING_MAX, value))


def draw_potential(rnd) -> str:
    roll = rnd.below(100)
    high, average = T.FR_POTENTIAL_SHARES
    return "high" if roll < high else "average" if roll < average else "low"


def new_league(rnd, surnames: list, coach: str, team: int, league_id: str, own_names: Roster | None = None, team_styles=None) -> LeagueRecord:
    """A new league (design 4.5): the player's team first, with the 33 names of `own_names` when it is a complete roster (and
    its quarterback when it names one), then T01 to T32 without it; every other value is drawn, in the order of design 12.1. `team_styles`: the
    playbooks' assignment of the 32 teams the coordinators start with (SX.8l; None: the built-in one)."""
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
    from . import contracts
    contracts.give_initial_contracts(league)                    # SX.8g: the market price of each player; no draw
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    from . import staff
    staff.new_staff(league, surnames, team_styles)              # SX.8l: the head coaches and the coordinators, the goals of season 1; no draw
    return league
