"""A team's place in its league and what it does to the computer's games (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 5.2. The computer's games have no teams in the original: a regular week draws two indices into a 32-entry
score table and the higher index wins; a play-off game is a coin. The Franchise lets strength move both by a bounded amount:

    shift(team)                      a team's score index moves this many places (sign-symmetric, at most FR_SHIFT_MAX)
    playoff_per_mille(visitor, home) the chance that the visitor wins a play-off game, 250 to 750 per mille (500: the original's coin)

The team's place is z = (its exact strength sum - the mean of the 32 sums) / max(the standard deviation of the 32 sums, FR_SPREAD_FLOOR),
taken from the sums kept at the start of the season, so the effect of being the best or the worst team lasts while the rosters even out
over the years. No float is used in a rule the tests compare: the sums are whole numbers, the standard deviation is compared by
squares, and a rounded half up value is counted from one integer square root (`rounded`), so the rule is sign-symmetric by
construction (a team below the mean gets exactly the negative of the shift of a team as far above it) and every league of 32 equal
sums (all 70s included) has z = 0 and the original's results.
"""
from __future__ import annotations

from math import isqrt

from .. import tuning as T
from . import data as D


class LeaguePlace:
    """The 32 sums of a season, ready to answer the shift of a team and the lean of a game."""

    def __init__(self, sums):
        sums = list(sums)
        if len(sums) != D.TEAMS:
            raise ValueError("a league has %d teams, not %d sums" % (D.TEAMS, len(sums)))
        n = len(sums)
        total = sum(sums)
        # d = n times the distance from the mean: a whole number. sd_d (n times the standard deviation) squared is sum(d^2) / n, so
        # the squared spread in use is `spread_sq` / n with the floor counted in the same units
        self.d = [n * s - total for s in sums]
        floor_d = T.FR_SPREAD_FLOOR * n
        self.spread_sq = max(sum(x * x for x in self.d), n * floor_d * floor_d)
        self.n = n

    def rounded(self, delta: int, per_sd: int) -> int:
        """sign(delta) * round_half_up(|delta| / sd_d * per_sd), whole numbers only: with t = 2 * |delta| * per_sd, twice the value
        squared is n * t^2 / spread_sq, and round_half_up(v) = (floor(2 v) + 1) // 2 with floor(2 v) from an integer square root."""
        if delta == 0:
            return 0
        t = 2 * abs(delta) * per_sd
        magnitude = (isqrt(self.n * t * t // self.spread_sq) + 1) // 2
        return magnitude if delta > 0 else -magnitude

    def shift(self, team: int) -> int:
        """How many places team 1 to 32's score index moves (design 5.2): in -FR_SHIFT_MAX to +FR_SHIFT_MAX."""
        value = self.rounded(self.d[team - 1], T.FR_SHIFT_PER_SD)
        return max(-T.FR_SHIFT_MAX, min(T.FR_SHIFT_MAX, value))

    def playoff_per_mille(self, visitor: int, home: int) -> int:
        """The chance that the visitor wins a play-off game, per mille: 500 plus the lean of the gap in standard deviations."""
        lean = self.rounded(self.d[visitor - 1] - self.d[home - 1], T.FR_PLAYOFF_PER_SD)
        return max(D.PLAYOFF_CHANCE_MIN, min(D.PLAYOFF_CHANCE_MAX, 500 + lean))

    def index(self, team: int, index: int) -> int:
        """The index into the score table (1 to 32) after the team's shift."""
        return max(1, min(D.SCORE_TABLE_SIZE, index + self.shift(team)))
