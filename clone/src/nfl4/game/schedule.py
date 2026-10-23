"""The schedule maker. This is inspired by Jim Kitchen.

GAME_SPEC 5.1 (CODE (lifted) `makes` p_42fa70; the constants and the picks were checked in the assembly): runs at a new
season and when the player rejects the schedule in week 1. 16 weeks, each with the opponent's division and place and a
flag (1 or 2; 8 weeks of each; "home" or "away" as the original's sentences use them, 4.11). Every draw is
`Int(Rnd * N) + 1` in the original's order, so a scripted random source reproduces any schedule:

1. All 16 weeks are emptied.
2. The six division games: for each of the three other teams of the player's division in place order (1 to 4 without
   the player's own), twice (flag 1, then flag 2): draw a week 1 to 16 until it is free and not 1 or 2 weeks away from the
   week placed just before (`last`; it starts at 0, so the first draw can never be week 1 or 2).
3. The ten free weeks in week order: draw a division 1 to 8 until it is not the player's, then a place 1 to 4, and both
   again until that team is not yet on the schedule; draw the flag 1 or 2 until the count of that flag among these ten
   games is below 5. Result: eight weeks of each flag, ten different opponents outside the division.

The numbers of the division games are Integer Variants and the others Single Variants in the original; that only matters
for the byte layout of footbal2.dat (GAME_SPEC 12, S7.5). G-D1: every redraw is bounded (rnd.redraw); the fallback
candidates keep the rules, so a schedule made after the bound still satisfies them.
"""
from __future__ import annotations

from dataclasses import dataclass

from .league import DIVISIONS, PLACES
from .rnd import GameRandom

WEEKS = 16
FLAG_LIMIT = 5      # the free weeks give each flag at most five of the ten games
BYE = (0, 0, 0)     # a calendar's week in which the team does not play: the entry's three values (nfl4's Franchise only)


@dataclass(frozen=True)
class ScheduleEntry:
    division: int   # the opponent's division tn3 (1 to 8)
    team: int       # the opponent's place tn4 (1 to 4)
    flag: int       # vtrnt's value for the week: 1 or 2 (4.11: flag 1 "A verses the B" with A the opponent)

    @property
    def is_bye(self) -> bool:
        """A week of a calendar in which the team does not play (BYE: the three values are 0; nfl4's Franchise only)."""
        return self.division == 0


def team_number(division: int, place: int) -> int:
    """The team 1 to 32 of a division 1 to 8 and a place 1 to 4 (T01 to T32 in the order of teams.txt)."""
    return (division - 1) * PLACES + place


def team_pair(team: int) -> tuple[int, int]:
    """(division, place) of the team 1 to 32."""
    return (team - 1) // PLACES + 1, (team - 1) % PLACES + 1


@dataclass(frozen=True)
class Calendar:
    """A season whose every game is known before it is played (nfl4's Franchise, the real NFL calendar: 18 weeks, 17 games for each team, one bye
    week). `weeks[w - 1]` holds the games of week w as (visiting team, home team) with the teams as numbers 1 to 32. The original has no such thing:
    its 16 weeks come from `make_schedule` and its other games are drawn week by week among the teams that have not played. A season with a calendar
    ends its regular season after `length` weeks, so the play-off weeks follow it (SeasonState.regular_weeks)."""
    label: str
    weeks: tuple

    @property
    def length(self) -> int:
        return len(self.weeks)

    def games(self, week: int) -> tuple:
        return self.weeks[week - 1]

    def game_of(self, week: int, team: int):
        """The (visitor, home) game of the team in the week, or None when it has its bye."""
        for game in self.weeks[week - 1]:
            if team in game:
                return game
        return None

    def entries_of(self, team: int) -> list[ScheduleEntry]:
        """The team's schedule: one entry for each week, the opponent's division and place and the flag (1: the team is at home, the original's meaning
        of "the opponent first"; 2: away), or BYE for the week without a game."""
        out = []
        for week in range(1, self.length + 1):
            game = self.game_of(week, team)
            if game is None:
                out.append(ScheduleEntry(*BYE))
                continue
            visitor, home = game
            opponent = visitor if home == team else home
            out.append(ScheduleEntry(*team_pair(opponent), 1 if home == team else 2))
        return out

    def to_rows(self) -> list:
        return [[[visitor, home] for visitor, home in week] for week in self.weeks]

    @classmethod
    def from_rows(cls, label: str, rows) -> "Calendar":
        return cls(label, tuple(tuple((int(v), int(h)) for v, h in week) for week in rows))


def make_schedule(rnd: GameRandom, own_division: int, own_team: int) -> list[ScheduleEntry]:
    """The 16 weeks of a new schedule for the team (own_division, own_team), as `makes` makes them."""
    division = [0] * (WEEKS + 1)        # L8c(week + 17): 0 = the week is free
    team = [0] * (WEEKS + 1)            # L8c(week + 34)
    flag = [0] * (WEEKS + 1)            # L8c(week + 51)

    # --- the six division games ---
    last = 0                            # Lcc: Empty at first, counts as 0
    for rival in range(1, PLACES + 1):
        if rival == own_team:
            continue
        for game_flag in (1, 2):
            def acceptable(week: int, last=last) -> bool:
                return division[week] == 0 and abs(week - last) not in (1, 2)

            def first_acceptable(last=last) -> int:
                for week in range(1, WEEKS + 1):
                    if acceptable(week, last):
                        return week
                for week in range(1, WEEKS + 1):        # no week leaves room: any free week
                    if division[week] == 0:
                        return week
                raise RuntimeError("no free week for a division game")

            week = rnd.redraw(lambda: rnd(WEEKS), acceptable, first_acceptable, "division game week")
            last = week
            division[week], team[week], flag[week] = own_division, rival, game_flag

    # --- the ten free weeks, in week order ---
    ones = twos = 0                     # Ldc and L68: how often each flag was used in these ten
    for week in range(1, WEEKS + 1):
        if division[week] != 0:
            continue

        def draw_opponent() -> tuple[int, int]:
            drawn_division = rnd.redraw(lambda: rnd(DIVISIONS), lambda d: d != own_division,
                                        lambda: next(d for d in range(1, DIVISIONS + 1) if d != own_division),
                                        "opponent division")
            return drawn_division, rnd(PLACES)

        def not_yet_scheduled(pair: tuple[int, int]) -> bool:
            return not any(division[w] == pair[0] and team[w] == pair[1] for w in range(1, WEEKS + 1))

        def first_unscheduled() -> tuple[int, int]:
            for d in range(1, DIVISIONS + 1):
                if d == own_division:
                    continue
                for t in range(1, PLACES + 1):
                    if not_yet_scheduled((d, t)):
                        return d, t
            raise RuntimeError("every team is already on the schedule")

        opponent = rnd.redraw(draw_opponent, not_yet_scheduled, first_unscheduled, "opponent team")

        def flag_free(value: int) -> bool:
            return not ((value == 1 and ones == FLAG_LIMIT) or (value == 2 and twos == FLAG_LIMIT))

        game_flag = rnd.redraw(lambda: rnd(2), flag_free, lambda: 1 if ones < FLAG_LIMIT else 2, "home or away flag")
        if game_flag == 1:
            ones += 1
        else:
            twos += 1
        division[week], team[week], flag[week] = opponent[0], opponent[1], game_flag

    return [ScheduleEntry(division[w], team[w], flag[w]) for w in range(1, WEEKS + 1)]
