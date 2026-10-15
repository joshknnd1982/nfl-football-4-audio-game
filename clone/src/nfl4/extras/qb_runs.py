"""Quarterback runs of the N. F. L. rules mode (nfl4 only, rule 0.13; NX3, built in SX.5). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 7, NFL_RULES_RESEARCH Part 4 (3-27: a quarterback who holds a live ball is a runner, his rushes count as
rushing and a loss behind the line on a designed run is a rush, not a sack; 7-2-1 (d): a runner who slides is down at once;
12-2-8 (d): a late hit on a slider is unnecessary roughness, 15 yards and an automatic first down; 12-1-4: the sneak and the
push are legal in 2026). The rules as plain functions (no speech, no keys; the draws are named): `row`, `computer_play`,
`to_goal`. `QbFlow` is the game's part: NflRules (extras/nfl_rules.py) owns one per game and calls it from the hooks.

    entry(state, scramble)           H8: the QBRunEntry of the play against the defense call (no draw)
    narrate(state, entry, d1, d2)    the start sentence of pool QB (keeper and draw, never one of the last three: its draws),
                                     the keeper's direction `below(4) + 4`, the run sentence and the tackle sentence
    scramble_from_sack(state)        the original's sack becomes a scramble: one `below(100)` against 22 percent
    scramble_from_incomplete(state)  the original's incompletion becomes a scramble: one `below(100)` against 6 percent
    slide(state)                     a gain of 8 or more yards that did not score: `rnd(2) == 1` slides, `below(3)` yards are
                                     cut, the tackle sentence is the slide, the whistle; with penalties on `below(40)` is a late hit
    computer_offense(state)          the computer's offense: a sneak with chance 1 in 2 on third or fourth and 1 or 2 (`rnd(2)`),
                                     else on downs 1 to 3 one draw `rnd(150)`: 1 a keeper, 2 a draw
    count(state, outcome)            the statistics line and the events of the calibration

The order of the draws of a designed run (design 15, as built): the snap's own, the start sentence (pool QB: `rnd(size)`,
redrawn while it is one of the last three, a name and the choices only when the line has them), the direction, the fumble
`rnd(odds)`, the yards, then the slide. A scramble: the sack or the completion draw of the original, the scramble draw, then
the same from the run sentence on.
"""
from __future__ import annotations

import logging

from ..game import outcome as O
from ..game import phrases as P
from ..game.gamestate import own_half
from ..game.playtables import QB_DRAW, QB_KEEPER, QB_SNEAK, QBRunEntry
from ..game.setup import RUN_DIRECTIONS
from . import nx_texts as X
from . import remarks
from . import tuning as T

log = logging.getLogger("nfl4.extras")

SNEAK, KEEPER, DRAW, SCRAMBLE_KEY = "sneak", "keeper", "draw", "scramble"
KINDS = {QB_SNEAK: SNEAK, QB_KEEPER: KEEPER, QB_DRAW: DRAW}
DESIGNED = (SNEAK, KEEPER, DRAW)
COUNTED_KINDS = (O.RUN, O.TOUCHDOWN, O.SAFETY_KIND, O.TWO_POINT_TRY)   # a fumbled run is not counted as a run (Q60)


# ----- the rules, as plain functions -----

def row(key: str, defense_play: int) -> tuple[int, int]:
    """The fewest and the most yards of the play against a defense call (1 to 6)."""
    if key == SCRAMBLE_KEY:
        return T.QB_SCRAMBLE_YARDS
    return T.QB_ROWS[key][defense_play - 1]


def make_entry(key: str, defense_play: int) -> QBRunEntry:
    low, high = row(key, defense_play)
    return QBRunEntry(key, 4 if key == KEEPER else None, T.QB_SOUND[key], low, high + 1, T.QB_FUMBLE_ODDS[key])


def to_goal(state) -> int:
    """The yards from the line of scrimmage to the defense's goal line (a gain of at least this many scores)."""
    return 100 - state.yard_line if state.half == own_half(state.wisoff) else state.yard_line


class QbFlow:
    def __init__(self, rules):
        self.rules = rules
        self.events: list[tuple] = []       # (quarter, side, kind, yards, slid, down, to_go, outcome kind, a try): the tests and
        #                                     the calibration count them; a penalty that took the play away is not taken back
        self.eligible = 0                   # gains of 8 or more yards that did not score (a slide was possible)
        self.slides: list[int] = []         # the yards each slide cut
        self.late_hits = 0                  # slides on which a late hit was drawn (penalties on)

    @property
    def game(self):
        return self.rules.game

    @property
    def rnd(self):
        return self.rules.game.rnd

    # ----- H8 -----

    def entry(self, state, scramble: bool = False) -> QBRunEntry:
        key = SCRAMBLE_KEY if scramble else KINDS[state.offense_play]
        return make_entry(key, state.defense_play)

    def narrate(self, state, entry: QBRunEntry, defender1: str, defender2: str) -> tuple[str, str]:
        """(the run sentence, the tackle sentence); the start sentence of the pool is said here, first (design 7.2)."""
        g = self.game
        qb = state.quarterbacks.get(state.wisoff, "")
        key = entry.key
        if key in (KEEPER, DRAW):
            values = {"<team>": state.teams.get(state.wisoff, ""), "<coach>": g.season.coach, "<quarterback>": qb}
            remarks.say_remark(g, state, state.extras, "QB", values, say=g.say4)
        if key == SNEAK:
            return X.text("NXQ-03", quarterback=qb), P.PILE_UP
        if key == KEEPER:
            direction = RUN_DIRECTIONS[self.rnd.below(4) + 4 - 1]           # Int(Rnd * 4) + 4, as the original's End Run
            return X.text("NXQ-04", quarterback=qb, dir=direction), P.TACKLED_BY + defender1 + " "
        if key == DRAW:
            return X.text("NXQ-05", quarterback=qb), P.BROUGHT_DOWN + P.BY + defender1 + " "
        return X.text("NXQ-01", quarterback=qb), P.CAUGHT_BY + defender1 + " "

    # ----- the scramble (design 7.1) -----

    def scramble_from_sack(self, state) -> bool:
        if not state.extras.qb_on:
            return False
        return self.rnd.below(100) < T.QB_SCRAMBLE_FROM_SACK

    def scramble_from_incomplete(self, state) -> bool:
        if not state.extras.qb_on:
            return False
        return self.rnd.below(100) < T.QB_SCRAMBLE_FROM_INCOMPLETE

    # ----- the slide (design 7.3) -----

    def slide(self, state) -> None:
        """After the yards are drawn: the quarterback slides when he gained at least 8 and did not score, with chance 1 in 2;
        the gain is cut by 0 to 2 yards, no fumble is possible any more (the fumble test came first), the tackle sentence is
        the slide and the sound the whistle (foot11). The clock keeps running (7-2-1 (d)). With penalties on, a late hit on
        the slider (P18, by the defense) with chance 1 in 40 of the slides."""
        if state.yards < T.QB_SLIDE_MIN_YARDS or state.yards >= to_goal(state):
            return
        self.eligible += 1
        if self.rnd(T.QB_SLIDE_ONE_IN) != 1:
            return
        low, high = T.QB_SLIDE_CUT
        cut = self.rnd.below(high - low + 1) + low
        self.slides.append(cut)
        state.yards -= cut
        state.slid = True
        state.tackle_sentence = X.text("NXQ-02", quarterback=state.quarterbacks.get(state.wisoff, ""))
        state.tackle_sound = 8
        if state.extras.penalties_on and self.rules.penalty.slider_hit(state, T.QB_LATE_HIT_ONE_IN):
            self.late_hits += 1

    # ----- the computer's offense (design 7.4) -----

    def computer_offense(self, state) -> None:
        x = state.extras
        if not x.qb_on or state.two_point or state.offense_play not in (1, 2, 3, 4, 5):
            return
        if state.down >= 3 and state.to_go <= T.QB_COMPUTER_SHORT:
            a, b = T.QB_COMPUTER_SNEAK
            if self.rnd(b) <= a:
                state.offense_play = QB_SNEAK
            return
        if state.down <= 3:
            draw = self.rnd(T.QB_COMPUTER_OTHER_ONE_IN)
            if draw == 1:
                state.offense_play = QB_KEEPER
            elif draw == 2:
                state.offense_play = QB_DRAW

    # ----- the statistics (C7, design 7.4) -----

    def count(self, state, outcome) -> None:
        """At the narration end point, before the penalty flow can take the play away: every sneak, keeper, draw and scramble that ended as
        a run counts on its own line besides the running statistics the engine already kept."""
        x = state.extras
        if not x.qb_on or not outcome.qb_run or outcome.kind not in COUNTED_KINDS:
            return
        x.qb_runs[outcome.offense - 1] += 1
        x.qb_yards[outcome.offense - 1] += outcome.yards
        self.events.append((state.quarter, outcome.offense, outcome.qb_run, outcome.yards, outcome.slid, state.down,
                            state.to_go, outcome.kind, bool(outcome.two_point_try)))

    def stats_lines(self, state) -> list[str]:
        x = state.extras
        return [X.text("NXS-08"), "%s %d" % (state.teams.get(1, ""), x.qb_runs[0]),
                "%s %d" % (state.teams.get(2, ""), x.qb_runs[1]),
                X.text("NXS-09"), "%s %d" % (state.teams.get(1, ""), x.qb_yards[0]),
                "%s %d" % (state.teams.get(2, ""), x.qb_yards[1])]
