"""Whole seeded games with the T key pressed at random moments keep every limit of the timeouts (nfl4 only, rule 0.13; owner rule 0.22,
PX SX.2b). This is inspired by Jim Kitchen.

The same property check as work/tkey_games_sx2b.py (which runs 10,000 games); here a small sample stays in every suite run. Every N1 limit
(three a half, two in a regular-season overtime period, one per team in a dead-ball period), never a timeout while the ball is live, the
clock never negative, every period at 0, a winner. The keys are posted like the window thread posts them, before the pauses of the play.
"""
import pytest

from tkeyrig import properties, sim_t_game

SEEDS = list(range(1, 13))


@pytest.mark.parametrize("seed", SEEDS)
def test_whole_games_with_t_pressed_at_random_keep_every_limit(tmp_path, seed):
    rig, engine, rules, result = sim_t_game(tmp_path, seed)
    assert properties(rig, engine, rules, result) == []
    assert engine.presses > 0


def test_the_sample_exercises_every_way_a_t_key_can_end(tmp_path):
    seen, withdrawn, granted = set(), 0, 0
    for seed in SEEDS:
        rig, engine, rules, result = sim_t_game(tmp_path / ("s%d" % seed), seed, press_in_1000=25)
        assert properties(rig, engine, rules, result) == []
        seen.update(rules.results)
        withdrawn += engine.withdrawn_plays
        granted += len(rules.timeouts)
    assert {"granted", "refused", "live kept"} <= seen
    assert withdrawn > 0 and granted > 0
