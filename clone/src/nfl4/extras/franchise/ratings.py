"""The ratings' bounded effect in a game the player plays (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 5.1. `FranchiseModifiers` is the playbooks' H8 object (`PlaybookModifiers`) that also reads the ratings of the
players in the play, which the Franchise's rosters carry (`Roster.ratings`, H7). The engine draws the ball carrier (or the target)
and the two tacklers BEFORE it reads a row (`pag_scrimmage.snap_draws`), so at the moment a row is read the state names the players:

    a run                        the offense's rating is the carrier's (running back `carrier`)
    a pass (a completion, an incompletion, a sack)    (2 x the quarterback + receiver `carrier` + 1) // 3
    a designed quarterback run   the quarterback's rating (a scramble gets no ratings Mod: it does not pass `qb_run`)
    the defense's rating         (the two tacklers' ratings + 1) // 2

The gap d = offense - defense, plus the team edge (SX.8b, D-057: `FR_TEAM_EDGE` times the two teams' strength gap in rating points,
2.5 times at the calibrated values, so the signal of the teams is not lost in the noise of the players of one play), moves the row by `step(d, per, cap)` (whole numbers, the same size up
and down, zero while |d| is under `per`): the yards (low and high together) by `FR_YARD_STEP`, the sack percent the other way by
`FR_SACK_STEP`, the catch percent by `FR_COMP_STEP`, the fumble denominator by `FR_FUM_STEP`. That Mod is ADDED to the playbook's Mod of the two plays called and
the sum is clamped to the playbooks' bounds again, so a row never moves more than `playbook_data.BOUNDS` allow. A field goal's odds
follow the kicker's rating and a punt's shortest length the punter's. With every rating 70, or no ratings at all (every other game),
the Mod is zero and every number is the original's (design 5.3, C3).
"""
from __future__ import annotations

from .. import playbook_data as PD
from .. import tuning as T
from ..playbooks import PlaybookModifiers, clamp
from ...game.playtables import FIELD_GOAL_ODDS, PUNT_ODDS, PUNT_SHORTEST
from . import data as D

RUN, PASS, QB, FUMBLE = "run", "pass", "qb", "fumble"
RUNNING_BACKS, RECEIVERS, DEFENSE, KICKERS, QUARTERBACK = ("Running Backs:", "Receivers:", "Defensive Players:", "Kickers:",
                                                           "Quarterback:")


def step(x: int, per: int, cap: int) -> int:
    """sign(x) * min(cap, |x| // per): zero while |x| is under `per`, whole numbers, the same size up and down."""
    magnitude = min(cap, abs(x) // per)
    return magnitude if x > 0 else -magnitude


def rating_mod(gap: int) -> PD.Mod:
    """The ratings' Mod for a gap d (offense rating - defense rating): design 5.1."""
    yards = step(gap, *T.FR_YARD_STEP)
    return PD.Mod(yards, yards, -step(gap, *T.FR_SACK_STEP), step(gap, *T.FR_COMP_STEP), step(gap, *T.FR_FUM_STEP))


class FranchiseModifiers(PlaybookModifiers):
    """H8 with playbooks and ratings. Until `bind` gives it the game's state, and whenever the rosters carry no ratings, it is the
    playbooks' object exactly."""

    def __init__(self):
        super().__init__()
        self.state = None

    def bind(self, state) -> None:
        self.state = state

    # ----- what the state says -----

    def _rating(self, side: int, heading: str, number: int) -> int | None:
        roster = self.state.rosters.get(side) if self.state is not None else None
        if roster is None or not roster.ratings:
            return None
        return roster.ratings.get((heading, number), D.RATING_NEUTRAL)

    def team_edge(self, offense_side: int, defense_side: int) -> int:
        """The gap of the two teams' strengths (the weighted sums of design 4.4 over 78: rating points of the weighted mean) times
        `FR_TEAM_EDGE` (a numerator and a denominator: 5 / 2), in whole rating points, rounded half up and the same size up and down. Added to every play's gap: the individual players of a play are a noisy
        sample of their teams, and the bounded Mod saturates on the noise, so the team's strength has to be counted once more
        for the team that is better to win by about what the league's results say (design 5.4 C-F2; D-057)."""
        numerator, denominator = T.FR_TEAM_EDGE
        if numerator == 0:
            return 0
        rosters = self.state.rosters
        sums = []
        for side in (offense_side, defense_side):
            ratings = rosters[side].ratings
            sums.append(sum(weight * ratings.get(key, D.RATING_NEUTRAL) for key, weight in D.WEIGHT_OF_KEY.items()))
        delta = (sums[0] - sums[1]) * numerator
        scale = D.WEIGHT_SUM * denominator
        magnitude = (2 * abs(delta) + scale) // (2 * scale)
        return magnitude if delta > 0 else -magnitude

    def gap(self, kind: str) -> int | None:
        """d = the offense's rating - the defense's for the play now being made (None: no ratings in this game), and the teams' edge."""
        s = self.state
        if s is None:
            return None
        offense_side, defense_side = s.wisoff, s.defense
        if kind == RUN:
            offense = self._rating(offense_side, RUNNING_BACKS, s.carrier)
        elif kind == QB:
            offense = self._rating(offense_side, QUARTERBACK, 1)
        else:
            quarterback = self._rating(offense_side, QUARTERBACK, 1)
            receiver = self._rating(offense_side, RECEIVERS, s.carrier)
            offense = None if quarterback is None else (2 * quarterback + receiver + 1) // 3
        first = self._rating(defense_side, DEFENSE, s.defender1)
        second = self._rating(defense_side, DEFENSE, s.defender2)
        if offense is None or first is None or second is None:
            return None
        return offense - (first + second + 1) // 2 + self.team_edge(offense_side, defense_side)

    def play_kind(self) -> str:
        """The kind of the table the play in progress reads: a run (plays 1 and 2), a quarterback run (8 to 10), else a pass."""
        play = self.state.offense_play
        return RUN if play <= 2 else QB if play >= 8 else PASS

    def mod_for(self, kind: str) -> PD.Mod | None:
        armed = self.mod
        if self.state is None:                              # not bound to a game: the playbooks' object exactly
            return armed
        gap = self.gap(self.play_kind() if kind == FUMBLE else kind)
        if gap is None:
            return armed
        total = clamp((armed or PD.ZERO).plus(rating_mod(gap)))
        return total if any(total) else None

    # ----- the kicks -----

    def _kicker(self, side: int, number: int) -> int | None:
        return self._rating(side, KICKERS, number)

    def field_goal_odds(self, side: int) -> int:
        kicker = self._kicker(side, 1)
        if kicker is None:
            return super().field_goal_odds(side)
        return FIELD_GOAL_ODDS + step(kicker - D.RATING_NEUTRAL, *T.FR_KICK_STEP)

    def punt(self, side: int) -> tuple[int, int]:
        punter = self._kicker(side, 2)
        if punter is None:
            return super().punt(side)
        return PUNT_ODDS, PUNT_SHORTEST + step(punter - D.RATING_NEUTRAL, *T.FR_PUNT_STEP)
