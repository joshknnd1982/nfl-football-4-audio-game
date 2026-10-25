"""The one random function and the bounded redraws. This is inspired by Jim Kitchen.

GAP_REGISTER G-D2 (one function, every draw keeps the range of its lifted line) and G-D1 (every redraw loop is bounded).
"""
import logging
import random

import pytest

from nfl4.game.rnd import REDRAW_LIMIT, GameRandom
from randsources import ScriptedRandom, StuckRandom, below_value, draws, value_for


def test_rnd_is_int_of_rnd_times_n_plus_one_and_below_is_without_the_plus_one():
    for n in (2, 3, 8, 30, 1708):
        for k in (1, n // 2 or 1, n):
            assert GameRandom(ScriptedRandom([value_for(n, k)]))(n) == k
        for k in (0, n - 1):
            assert GameRandom(ScriptedRandom([below_value(n, k)])).below(n) == k


def test_the_edges_of_the_range_never_leave_it():
    assert GameRandom(ScriptedRandom([0.0]))(8) == 1
    assert GameRandom(ScriptedRandom([0.9999999999999999]))(8) == 8
    assert GameRandom(ScriptedRandom([0.9999999999999999])).below(1708) == 1707


def test_random_is_the_rnd_the_sound_procedures_call_and_it_checks_its_source():
    rnd = GameRandom(ScriptedRandom([0.25, 1.0]))
    assert rnd.random() == 0.25
    with pytest.raises(ValueError):
        rnd.random()                           # 1.0 is not below 1
    with pytest.raises(ValueError):
        GameRandom(ScriptedRandom([-0.1])).random()


def test_the_default_source_is_a_real_generator():
    rnd = GameRandom()
    seen = {rnd(6) for _ in range(500)}
    assert seen == {1, 2, 3, 4, 5, 6}


def test_a_seeded_source_repeats_the_same_numbers():
    one = GameRandom(random.Random(7))
    two = GameRandom(random.Random(7))
    assert [one(1708) for _ in range(50)] == [two(1708) for _ in range(50)]


def test_every_bucket_of_the_main_draws_is_hit_about_equally_often():
    """A rough distribution check (a chi-square test with a wide limit) of the draw sizes the game uses most."""
    rnd = GameRandom(random.Random(20261014))
    for n in (2, 3, 8, 30):
        counts = [0] * n
        trials = 4000 * n
        for _ in range(trials):
            counts[rnd(n) - 1] += 1
        expected = trials / n
        chi_square = sum((c - expected) ** 2 / expected for c in counts)
        assert chi_square < 3.5 * (n - 1) + 25, (n, counts)       # far from the 0.001 level, still catches a bias


def test_redraw_takes_the_first_acceptable_value_in_the_order_drawn():
    rnd = GameRandom(ScriptedRandom(draws((16, 1), (16, 2), (16, 9), (16, 12))))
    result = rnd.redraw(lambda: rnd(16), lambda week: week > 5, lambda: 99, "test")
    assert result == 9 and rnd.source.left == 1 and rnd.fallbacks == 0      # the 12 is never drawn


def test_redraw_is_bounded_then_takes_the_scanned_candidate_and_logs_once(caplog):
    stuck = StuckRandom(0.0)
    rnd = GameRandom(stuck)
    with caplog.at_level(logging.WARNING, logger="nfl4.game"):
        result = rnd.redraw(lambda: rnd(16), lambda week: week == 7, lambda: 7, "test loop")
    assert result == 7
    assert stuck.drawn == REDRAW_LIMIT == 10_000
    assert rnd.fallbacks == 1
    assert sum("test loop" in record.message for record in caplog.records) == 1


def test_the_limit_can_be_lowered_for_a_test():
    rnd = GameRandom(StuckRandom(0.5))
    rnd.redraw_limit = 5
    assert rnd.redraw(lambda: rnd(4), lambda v: False, lambda: -1, "x") == -1
    assert rnd.source.drawn == 5
