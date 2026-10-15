"""The one random function of the game, and the bounded redraws. This is inspired by Jim Kitchen.

GAP_REGISTER G-D2 (D-013): the original reseeds VB's Rnd from the clock and draws `Int(Rnd * N) + k`. The clone has ONE
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
from typing import Callable, TypeVar

log = logging.getLogger("nfl4.game")

REDRAW_LIMIT = 10_000   # G-D1

T = TypeVar("T")


class GameRandom:
    """source: anything with random() giving 0 <= x < 1 (random.Random in the game, a seeded one or a scripted one in
    tests). None = a generator seeded from the operating system (D-013)."""

    def __init__(self, source=None):
        self.source = source if source is not None else random.Random()
        self.redraw_limit = REDRAW_LIMIT
        self.fallbacks = 0          # how often a redraw ran out of tries (a test asserts it stays 0 on the real data)
        # S7.3b: when a list, every draw appends its size n (Int(Rnd * n)) or 0 (a bare Rnd), so a test can compare the
        # sizes of a whole game's draws with the lifted lines and with a recorded game (the golden transcript).
        self.trace: list[int] | None = None

    def _next(self) -> float:
        x = self.source.random()
        if not 0.0 <= x < 1.0:
            raise ValueError("a random source gave %r, which is not below 1 and not negative" % (x,))
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

    def __call__(self, n: int) -> int:
        """Int(Rnd * n) + 1: 1 to n."""
        return self.below(n) + 1

    def redraw(self, draw: Callable[[], T], accept: Callable[[T], bool], scan: Callable[[], T], what: str) -> T:
        """`draw` again until `accept` takes the value (the original's loop), at most `redraw_limit` times. Then `scan`
        gives the first valid candidate (it may raise when there is none)."""
        for _ in range(self.redraw_limit):
            value = draw()
            if accept(value):
                return value
        self.fallbacks += 1
        log.warning("%s: no valid draw in %d tries, taking the first valid candidate (G-D1)", what, self.redraw_limit)
        return scan()
