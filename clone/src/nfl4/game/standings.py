"""Win and loss records and the standings speech. This is inspired by Jim Kitchen.

GAME_SPEC 5.2 (CODE (lifted) SayStand p_42ce40; the sort checked in the assembly at 0x42da3b). The records are 8 divisions
of 4 teams, each with wins and losses; the original reads them from footbal3.dat (64 values: for each division 1 to 8,
each place 1 to 4, wins then losses; all 0 when the file does not exist), S7.5 does the file. SayStand speaks nothing when
gtp (the week counter) is 0 or less or more than 17. N = gtp - 1, at most 16: " Standings after week number N " with
the number trimmed. Then for each division its name, and its four teams in order of LOSSES only, fewest first (the wins
are ignored; an insertion sort that never swaps equal losses, so equal ones keep the order of the league), each as
" <team> <wins>, and <losses>. " with the numbers trimmed.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .league import DIVISIONS, PLACES, League
from .vbnum import str_, trim

HEADING = " Standings after week number "          # string 778
AND = ", and "                                      # string 779
END = ". "                                          # string s38


@dataclass
class Records:
    """wins[d - 1][p - 1] and losses[d - 1][p - 1] for division d, place p. Lb0(place*9 + division + 45) is wins in the
    original and Lb0(place*9 + division + 90) losses."""
    wins: list[list[int]] = field(default_factory=lambda: [[0] * PLACES for _ in range(DIVISIONS)])
    losses: list[list[int]] = field(default_factory=lambda: [[0] * PLACES for _ in range(DIVISIONS)])

    def reset(self) -> None:
        for d in range(DIVISIONS):
            for p in range(PLACES):
                self.wins[d][p] = 0
                self.losses[d][p] = 0

    def win(self, division: int, place: int) -> None:
        self.wins[division - 1][place - 1] += 1

    def loss(self, division: int, place: int) -> None:
        self.losses[division - 1][place - 1] += 1

    def record(self, division: int, place: int) -> tuple[int, int]:
        return self.wins[division - 1][place - 1], self.losses[division - 1][place - 1]

    def as_file_values(self) -> list[int]:
        """The 64 values of footbal3.dat: division 1 to 8, place 1 to 4, wins then losses."""
        values = []
        for d in range(DIVISIONS):
            for p in range(PLACES):
                values.extend((self.wins[d][p], self.losses[d][p]))
        return values

    @classmethod
    def from_file_values(cls, values) -> "Records":
        values = list(values)
        if len(values) != 2 * DIVISIONS * PLACES:
            raise ValueError("footbal3.dat holds %d values, not %d" % (len(values), 2 * DIVISIONS * PLACES))
        records = cls()
        index = 0
        for d in range(DIVISIONS):
            for p in range(PLACES):
                records.wins[d][p], records.losses[d][p] = int(values[index]), int(values[index + 1])
                index += 2
        return records


def standings_order(division: int, league: League, records: Records) -> list[tuple[str, int, int]]:
    """The division's four teams (name, wins, losses) as SayStand puts them: an insertion sort on losses, fewest first,
    written as the original's two loops (no swap when the next team has the same or more losses)."""
    teams = [(league.team(division, p), records.wins[division - 1][p - 1], records.losses[division - 1][p - 1])
             for p in range(1, PLACES + 1)]
    for outer in range(1, PLACES):               # L90 = 1 to 3
        for inner in range(outer, 0, -1):        # Ld0 = L90 down to 1
            if teams[inner][2] >= teams[inner - 1][2]:
                break
            teams[inner - 1], teams[inner] = teams[inner], teams[inner - 1]
    return teams


@dataclass
class StandingsSpeech:
    heading: str
    divisions: list[tuple[str, list[str]]]       # (the division text with its spaces, its four team sentences)


def standings_speech(league: League, records: Records, gtp: int) -> StandingsSpeech | None:
    """What SayStand says, in order, or None when it says nothing (gtp 0 or less, or above 17)."""
    if gtp > 17 or gtp < 1:
        return None
    week = min(gtp - 1, 16)
    divisions = []
    for division in range(1, DIVISIONS + 1):
        lines = [" " + name + " " + trim(str_(wins)) + AND + trim(str_(losses)) + END
                 for name, wins, losses in standings_order(division, league, records)]
        divisions.append((league.division_text(division), lines))
    return StandingsSpeech(HEADING + trim(str_(week)), divisions)
