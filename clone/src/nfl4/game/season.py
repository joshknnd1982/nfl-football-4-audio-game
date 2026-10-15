"""The state of a season. This is inspired by Jim Kitchen.

GAME_SPEC 3 (the week loop), 5.1, 5.2, 12: what the original keeps between games in form variables and in the files
footbal1.dat (the coach and the team), footbal2.dat (the schedule), footbal3.dat (the records), football.gtp (the week
counter gtp) and, for the play-offs, footbal4.dat and footbal5.dat (S7.3c adds them). S7.3a holds the frame; S7.5
reads and writes the files and keeps this object in step with them.

* tn1, tn2 = the player's team (division 1 to 8, place 1 to 4); tn3, tn4 = this week's opponent; vtrnt = the week's flag.
* gtp = the week counter: 1 to 16 the regular season, 17 wild card week, 18 division play-off week, 19 division
  championship week, 20 Super Bowl week; 0 = the season is over.
* coach = the typed coach name ("coach" by default, GAME_SPEC 8.2).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .playoffs import PlayoffState, TeamRef
from .rnd import GameRandom
from .schedule import WEEKS, ScheduleEntry, make_schedule
from .standings import Records

WEEK_WILD_CARD, WEEK_DIVISION, WEEK_CHAMPIONSHIP, WEEK_SUPER_BOWL = 17, 18, 19, 20
DEFAULT_COACH = "coach"


@dataclass
class SeasonState:
    coach: str = DEFAULT_COACH
    tn1: int = 1                      # the player's division
    tn2: int = 1                      # the player's place in it
    tn3: int = 1                      # this week's opponent: division
    tn4: int = 1                      # this week's opponent: place
    vtrnt: int = 1                    # the week's flag (the third value of the schedule's week)
    gtp: int = 1                      # the week counter
    schedule: list[ScheduleEntry] = field(default_factory=list)
    records: Records = field(default_factory=Records)
    playoffs: PlayoffState = field(default_factory=PlayoffState)    # footbal4.dat and footbal5.dat (S7.3c)

    def choose_team(self, division: int, place: int) -> None:
        self.tn1, self.tn2 = division, place

    @property
    def own_team(self) -> TeamRef:
        return TeamRef(self.tn1, self.tn2)

    @property
    def opponent_team(self) -> TeamRef:
        return TeamRef(self.tn3, self.tn4)

    def make_schedule(self, rnd: GameRandom) -> list[ScheduleEntry]:
        """`makes`: a new schedule for the chosen team (a new season, and when the player rejects the schedule in week 1)."""
        self.schedule = make_schedule(rnd, self.tn1, self.tn2)
        return self.schedule

    def reset_for_new_season(self) -> None:
        """What the original's next START gives (it ends after every game, GAME_SPEC 3 step 7): the default coach, the
        first team, week 1, no schedule, all records 0, no play-off pairings or byes. The clone calls this when a season is
        over and the program goes on (GAP_REGISTER G-F3); the objects stay the same, the engine holds no copy."""
        self.coach = DEFAULT_COACH
        self.tn1 = self.tn2 = self.tn3 = self.tn4 = 1
        self.vtrnt = 1
        self.gtp = 1
        self.schedule = []
        self.records.reset()
        self.playoffs.clear()

    def set_week_opponent(self) -> ScheduleEntry | None:
        """The week loop reads footbal2.dat's first gtp records and keeps the last: tn3, tn4 = the opponent and vtrnt =
        the flag (GAME_SPEC 3 step 7b). Only for the regular season (gtp 1 to 16)."""
        if not 1 <= self.gtp <= WEEKS or len(self.schedule) < self.gtp:
            return None
        entry = self.schedule[self.gtp - 1]
        self.tn3, self.tn4, self.vtrnt = entry.division, entry.team, entry.flag
        return entry

    def set_playoff_opponent(self) -> bool:
        """The week loop's step 7c for gtp 17 to 20 (GAME_SPEC 3): this week's opponent is the other team of the player's
        game in footbal4.dat (tn3, tn4) with vtrnt = 2 when the player is the visitor, 1 when the player is the home team.
        When no record has the player's team the three values stay as they were (cannot happen in normal play: a team
        that is out gets the remaining rounds at once). Returns whether the player's game was found."""
        found = self.playoffs.opponent_of(self.own_team)
        if found is None:
            return False
        opponent, self.vtrnt = found
        self.tn3, self.tn4 = opponent.division, opponent.place
        return True
