"""Random sources for the game logic tests (GAP_REGISTER G-D2). This is inspired by Jim Kitchen.

`GameRandom` takes any object with random() (0 <= x < 1). A SCRIPTED source gives chosen numbers in order, so a test can
force one situation of the original (a rejected draw, a table row, a branch); when the script is used up it either raises
(a draw the test did not plan is a failure, `strict`) or goes on with a seeded generator (B-X1: a source stuck on one
value can loop forever, so the default is a seeded real generator behind the script).

`value_for(n, k)` is the Rnd value whose `Int(Rnd * n) + 1` is k (1 to n); `below_value(n, k)` the one whose
`Int(Rnd * n)` is k (0 to n - 1). `draws(...)` builds a script from (n, k) pairs.
"""
import random


def value_for(n: int, k: int) -> float:
    """The middle of the bucket of k in rnd(n) = Int(Rnd * n) + 1."""
    assert 1 <= k <= n, (n, k)
    return (k - 1 + 0.5) / n


def below_value(n: int, k: int) -> float:
    """The middle of the bucket of k in Int(Rnd * n), k = 0 to n - 1."""
    assert 0 <= k < n, (n, k)
    return (k + 0.5) / n


def draws(*pairs) -> list[float]:
    """A script from (n, k) pairs meaning rnd(n) = k."""
    return [value_for(n, k) for n, k in pairs]


class ScriptedRandom:
    def __init__(self, values=(), seed=5, strict=False):
        self.values = list(values)
        self.rest = random.Random(seed)
        self.strict = strict
        self.drawn = 0

    def random(self) -> float:
        self.drawn += 1
        if self.values:
            return self.values.pop(0)
        if self.strict:
            raise AssertionError("the game drew a random number the test did not script (draw %d)" % self.drawn)
        return self.rest.random()

    @property
    def left(self) -> int:
        return len(self.values)


class StuckRandom:
    """Always the same number: every redraw loop must end through its bound (G-D1)."""

    def __init__(self, value=0.0):
        self.value = value
        self.drawn = 0

    def random(self) -> float:
        self.drawn += 1
        return self.value
