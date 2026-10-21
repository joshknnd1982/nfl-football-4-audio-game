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
    original and Lb0(place*9 + division + 90) losses. ties[d - 1][p - 1] (nfl4 only, SX.12, D-096): the N. F. L. rules mode's
    regular-season overtime can end tied (16-1-3 (d)); the original's games never do, so in Classic every tie stays 0, footbal3.dat
    keeps its 64 values and the ties live in footbal6.dat (data/files/tiesfile.py), written only when a team has one."""
    wins: list[list[int]] = field(default_factory=lambda: [[0] * PLACES for _ in range(DIVISIONS)])
    losses: list[list[int]] = field(default_factory=lambda: [[0] * PLACES for _ in range(DIVISIONS)])
    ties: list[list[int]] = field(default_factory=lambda: [[0] * PLACES for _ in range(DIVISIONS)])

    def reset(self) -> None:
        for d in range(DIVISIONS):
            for p in range(PLACES):
                self.wins[d][p] = 0
                self.losses[d][p] = 0
                self.ties[d][p] = 0

    def win(self, division: int, place: int) -> None:
        self.wins[division - 1][place - 1] += 1

    def loss(self, division: int, place: int) -> None:
        self.losses[division - 1][place - 1] += 1

    def tie(self, division: int, place: int) -> None:
        self.ties[division - 1][place - 1] += 1

    def record(self, division: int, place: int) -> tuple[int, int]:
        return self.wins[division - 1][place - 1], self.losses[division - 1][place - 1]

    def ties_of(self, division: int, place: int) -> int:
        return self.ties[division - 1][place - 1]

    def any_ties(self) -> bool:
        return any(value for row in self.ties for value in row)

    def tie_values(self) -> list[int]:
        """The 32 values of footbal6.dat: division 1 to 8, place 1 to 4."""
        return [self.ties[d][p] for d in range(DIVISIONS) for p in range(PLACES)]

    def set_tie_values(self, values) -> None:
        values = [int(v) for v in values]
        if len(values) != DIVISIONS * PLACES:
            raise ValueError("footbal6.dat holds %d values, not %d" % (len(values), DIVISIONS * PLACES))
        for d in range(DIVISIONS):
            self.ties[d][:] = values[d * PLACES:(d + 1) * PLACES]

    def copy_into(self, other: "Records") -> None:
        """Every count into `other`, in place (the season's records are shared by the engine and the stores)."""
        for d in range(DIVISIONS):
            other.wins[d][:] = self.wins[d]
            other.losses[d][:] = self.losses[d]
            other.ties[d][:] = self.ties[d]

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


def half_losses(losses: int, ties: int) -> int:
    """The sort key of the original's loss order with ties (SX.12): a tie counts half a loss (the NFL's percentage, wins plus half the
    ties over the games, orders teams with as many games the same way). Without ties it is twice the losses: the original's order."""
    return 2 * losses + ties


def half_wins(wins: int, ties: int) -> int:
    """Twice the wins plus the ties: the original's win order (the seeds, Q43's "as many wins") with a tie as half a win (SX.12)."""
    return 2 * wins + ties


def standings_order(division: int, league: League, records: Records) -> list[tuple[str, int, int]]:
    """The division's four teams (name, wins, losses) as SayStand puts them: an insertion sort on losses, fewest first,
    written as the original's two loops (no swap when the next team has the same or more losses). A tie counts half a loss (SX.12;
    no team of a Classic season has one)."""
    rows = [(league.team(division, p), records.wins[division - 1][p - 1], records.losses[division - 1][p - 1],
             records.ties[division - 1][p - 1]) for p in range(1, PLACES + 1)]
    for outer in range(1, PLACES):               # L90 = 1 to 3
        for inner in range(outer, 0, -1):        # Ld0 = L90 down to 1
            if half_losses(rows[inner][2], rows[inner][3]) >= half_losses(rows[inner - 1][2], rows[inner - 1][3]):
                break
            rows[inner - 1], rows[inner] = rows[inner], rows[inner - 1]
    return [row[:3] for row in rows]


def standings_ties(division: int, league: League, records: Records) -> list[int]:
    """The ties of the four teams in `standings_order`'s order (the same sort)."""
    rows = [(records.losses[division - 1][p - 1], records.ties[division - 1][p - 1]) for p in range(1, PLACES + 1)]
    for outer in range(1, PLACES):
        for inner in range(outer, 0, -1):
            if half_losses(*rows[inner]) >= half_losses(*rows[inner - 1]):
                break
            rows[inner - 1], rows[inner] = rows[inner], rows[inner - 1]
    return [ties for _, ties in rows]


def ties_words(ties: int) -> str:
    """"and 1 tie" or "and 2 ties" (nfl4 only: NXC-13, NXC-14; SX.12); never asked for 0."""
    from ..extras import nx_texts as X
    return X.text("NXC-13" if ties == 1 else "NXC-14", n=ties)


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
        ties = standings_ties(division, league, records)
        lines = [" " + name + " " + trim(str_(wins)) + AND + trim(str_(losses)) + (", " + ties_words(tied) if tied else "") + END
                 for (name, wins, losses), tied in zip(standings_order(division, league, records), ties)]
        divisions.append((league.division_text(division), lines))
    return StandingsSpeech(HEADING + trim(str_(week)), divisions)
