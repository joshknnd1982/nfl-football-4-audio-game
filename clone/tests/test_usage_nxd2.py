"""NX-D2 (the owner's second report of 2026-10-24, D-147, CLAUDE.md 0.30): the starters play the most, like Madden's depth chart (nfl4 only, rule 0.13).

With the N. F. L. rules the ball carrier, the receiver and the two tacklers are drawn through the usage shares of extras/tuning.py, one below(total)
draw each (the count of random numbers is the original's); Classic keeps the original's even rnd(6) and rnd(17).
"""
import random

import pytest

from nfl4.extras import tuning as T
from nfl4.extras import usage
from nfl4.game.rnd import GameRandom
from nfl4.game.rules import ClassicRules

N = 20000


def rnd(seed=7):
    return GameRandom(random.Random(seed))


def shares_of(draws, size):
    return [draws.count(k) / len(draws) for k in range(1, size + 1)]


@pytest.mark.parametrize("table", [T.USAGE_RUN, T.USAGE_PASS, T.USAGE_TACKLE])
def test_the_draws_follow_the_shares(table):
    r = rnd()
    draws = [usage.weighted_place(r, list(table)) for _ in range(N)]
    for got, want in zip(shares_of(draws, len(table)), table):
        assert abs(got - want / sum(table)) < 0.012


def test_the_starters_get_most_of_the_plays():
    assert T.USAGE_RUN[0] > 2 * T.USAGE_RUN[1] and T.USAGE_RUN[4] == T.USAGE_RUN[5] == 0
    assert T.USAGE_PASS[0] == max(T.USAGE_PASS) and T.USAGE_PASS[4] + T.USAGE_PASS[5] < T.USAGE_PASS[0]
    starters = [0, 1, 2, 3, 6, 7, 8, 11, 12, 15, 16]                      # four linemen, three linebackers, two corners, two safeties
    assert sum(T.USAGE_TACKLE[i] for i in starters) >= 80 and sum(T.USAGE_TACKLE) == 100
    assert sum(T.USAGE_RUN) == sum(T.USAGE_PASS) == 100


def test_one_draw_a_pick_as_the_original():
    traced = rnd()
    traced.trace = []
    usage.weighted_place(traced, list(T.USAGE_RUN))
    assert traced.trace == [100]                                          # one number of the source, as rnd(6) was


def test_two_tacklers_are_two_men_by_the_shares():
    r = rnd(3)
    pairs = [usage.defenders(r) for _ in range(N)]
    assert all(a != b for a, b in pairs)
    firsts = shares_of([a for a, _ in pairs], 17)
    assert abs(firsts[6] - T.USAGE_TACKLE[6] / 100) < 0.012               # the first linebacker
    assert firsts[5] < 0.02 and firsts[10] < 0.02                         # the sixth lineman and the fifth linebacker seldom


def test_classic_keeps_the_original_even_draws():
    a, b = rnd(5), rnd(5)
    classic = ClassicRules().draw_defenders(None, a)
    first = b(17)
    second = b.redraw(lambda: b(17), lambda d: d != first, lambda: 2 if first == 1 else 1, "second defender")
    assert classic == (first, second)


def test_a_key_player_takes_his_share():
    weights = usage.with_key_player(list(T.USAGE_PASS), 4)                 # the first tight end on a key down
    assert abs(weights[3] / sum(weights) - T.KEY_PLAYER_SHARE / 100) < 1e-9
    rest = [w for i, w in enumerate(weights) if i != 3]
    others = [w for i, w in enumerate(T.USAGE_PASS) if i != 3]
    assert [x / sum(rest) for x in rest] == pytest.approx([x / sum(others) for x in others])
    assert usage.with_key_player(list(T.USAGE_RUN), None) == list(T.USAGE_RUN)


def test_a_franchise_multiplies_the_shares_by_its_rating_weights():
    assert usage.combine([60, 40], [3, 5]) == [180, 200] and usage.combine([60, 40], None) == [60, 40]
