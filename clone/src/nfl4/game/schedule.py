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


@dataclass(frozen=True)
class ScheduleEntry:
    division: int   # the opponent's division tn3 (1 to 8)
    team: int       # the opponent's place tn4 (1 to 4)
    flag: int       # vtrnt's value for the week: 1 or 2 (4.11: flag 1 "A verses the B" with A the opponent)


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
