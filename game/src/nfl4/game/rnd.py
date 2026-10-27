"""The one random function of the game, and the bounded redraws. This is inspired by Jim Kitchen.

GAP_REGISTER G-D2 (D-013): the original reseeds VB's Rnd from the clock and draws `Int(Rnd * N) + k`. The game has ONE
generator behind ONE object. `rnd(n)` is Int(Rnd * n) + 1 (1 to n); `rnd.below(n)` is Int(Rnd * n) (0 to n - 1), for the
draws whose lifted line adds another offset (`rnd.below(8) + 30`: 30 to 37); `rnd.random()` is Rnd itself (0 <= x < 1,
what the sound procedures call). Every draw keeps the range and the order of its lifted line, so a scripted source can
force any situation and a seeded one makes whole games repeat.

G-D1: the original has unbounded "draw again while ..." loops. With the original data none can run forever, but a
customized pool or a damaged file might, so every such loop goes through `redraw`: at most REDRAW_LIMIT tries, then the
first valid candidate found by scanning, and one warning in the log.
"""
from __future__ import annotations

import logging
import random
import secrets
from typing import Callable, TypeVar

from ..data import debuglog
from .vbnum import int_of, single

log = logging.getLogger("nfl4.game")

REDRAW_LIMIT = 10_000   # G-D1

T = TypeVar("T")


class GameRandom:
    """source: anything with random() giving 0 <= x < 1 (random.Random in the game, a seeded one or a scripted one in
    tests). None = a generator seeded from the operating system (D-013). The seed is made here and written to the debug log
    (playbook 7.11), so a session can be replayed from its log: the same seed and the same keys give the same draws."""

    def __init__(self, source=None):
        self.seed: int | None = None            # the seed of the generator made here; None for a source the caller gave
        if source is None:
            self.seed = secrets.randbits(64)
            source = random.Random(self.seed)
            debuglog.event("rnd", "seed", seed=self.seed)
        self.source = source
        self.draws = 0                          # how many numbers were drawn (the log says it at every game, season and league start)
        self.redraw_limit = REDRAW_LIMIT
        self.fallbacks = 0          # how often a redraw ran out of tries (a test asserts it stays 0 on the real data)
        # S7.3b: when a list, every draw appends its size n (Int(Rnd * n)) or 0 (a bare Rnd), so a test can compare the
        # sizes of a whole game's draws with the lifted lines and with a recorded game (the golden transcript).
        self.trace: list[int] | None = None

    def _next(self) -> float:
        x = self.source.random()
        if not 0.0 <= x < 1.0:
            raise ValueError("a random source gave %r, which is not below 1 and not negative" % (x,))
        self.draws += 1
        if debuglog.trace_on:                   # the trace level of the debug log: every draw, in order
            debuglog.event("rnd", "draw", debuglog.TRACE, n=self.draws, x="%.15g" % x)
        return x

    def random(self) -> float:
        """Rnd: the next number, 0 <= x < 1."""
        if self.trace is not None:
            self.trace.append(0)
        return self._next()

    def below(self, n: int) -> int:
        """Int(Rnd * n): 0 to n - 1."""
        if self.trace is not None:
            self.trace.append(n)
        return min(int(self._next() * n), n - 1)

    def below_single(self, n: int) -> int:
        """Int(Rnd * n) where n is a Variant (S7.3b, B-P40): the original stores Rnd as a Single Variant and calls
        VarMul and VarInt, so the product is rounded to a Single before Int (pag's yards 0x44da18, the kick-off
        return 0x445cf6, the interception 0x44bc75). A constant n is multiplied on the FPU and needs no rounding
        (`below`). The result is kept below n (a 53-bit source can come closer to 1 than VB's 24-bit Rnd)."""
        if self.trace is not None:
            self.trace.append(n)
        return min(int_of(single(self._next() * n)), n - 1)

    def __call__(self, n: int) -> int:
        """Int(Rnd * n) + 1: 1 to n."""
        return self.below(n) + 1

    def chance_first(self, per_mille: int) -> bool:
        """The Franchise's play-off coin (nfl4 only, NFL_FRANCHISE_DESIGN 5.2 and 13; never called in Classic): ONE number of the
        source, traced as a draw of size 2, true when number * 1000 is below `per_mille`. At 500 it is exactly `rnd(2) == 1` for
        every number (x < 0.5 is Int(x * 2) = 0), so a league of equal teams keeps the original's draws, trace and results (B-P65)."""
        if self.trace is not None:
            self.trace.append(2)
        return self._next() * 1000 < per_mille

    def redraw(self, draw: Callable[[], T], accept: Callable[[T], bool], scan: Callable[[], T], what: str) -> T:
        """`draw` again until `accept` takes the value (the original's loop), at most `redraw_limit` times. Then `scan`
        gives the first valid candidate (it may raise when there is none)."""
        for _ in range(self.redraw_limit):
            value = draw()
            if accept(value):
                return value
        self.fallbacks += 1
        log.warning("%s: no valid draw in %d tries, taking the first valid candidate (G-D1) draws=%d", what, self.redraw_limit,
                    self.draws)
        return scan()

    def mark(self, what: str, **fields) -> None:
        """The debug log's line for the start of a game, season or league: which generator and how many draws so far."""
        debuglog.event("rnd", what, seed=self.seed if self.seed is not None else "given", draws=self.draws, **fields)


def side_seed(rnd, mix: int) -> int:
    """The seed of a side generator for one game (nfl4's radio broadcast and stadium sounds, which never draw from the game's own, G-D2).
    BC.4 (D-191): the program's seed AND the draws the game's generator has made so far, so every game of one program run gets lines of
    its own (with the seed alone every game of a season opened with the same sign-on, crew, reporter's note and analyst's line), while the
    same seed and keys still give the same lines (the log has both). A source a test gave has no seed: the fixed seed of before."""
    seed = getattr(rnd, "seed", None)
    if seed is None:
        return 0x5EED ^ mix
    return ((seed ^ mix) << 32) ^ int(getattr(rnd, "draws", 0))
