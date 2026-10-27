"""Whole games with the N. F. L. rules: the property tests of C8 for the clock and the timeouts, the calibration bands on a
smaller sample, and games played through the menus by a seeded player who also calls timeouts (nfl4 only, rule 0.13;
NFL_EXTRA_FEATURES C2, C8, NX1; NFL_EXTRAS_DESIGN 5.7, 6.3; PX SX.2). This is inspired by Jim Kitchen.

The 10,000-game run of design 5.7 is work/calibrate_clock_sx2.py (its report: work/calibrate_clock_sx2_10000.txt); here 60
seeded games in every suite run check the same properties.
"""
import random
import statistics

import pytest

from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.timeouts import count_for
from nflrig import RecordingRules, sim_game
from pagrig import make_rig, play

GAMES = 60
ENTER, ESCAPE, DOWN, F1, F2, F3, F4 = 13, 27, 40, 112, 113, 114, 115


@pytest.fixture(scope="module")
def games(tmp_path_factory):
    return [sim_game(tmp_path_factory.mktemp("nx%d" % seed), seed) for seed in range(100, 100 + GAMES)]


def test_every_game_ends_with_a_winner_and_no_safety_net_was_needed(games):
    for rig, engine, rules, result in games:
        assert result.scores is not None
        # a level score only as the regular season's tie after its one overtime period (16-1-3 (d)); NX-D2's usage draws gave seed 144 one
        assert result.scores[0] != result.scores[1] or (engine.s.overtime >= 1 and not engine.s.extras.postseason)
        assert rig.rnd.fallbacks == 0 and engine.noise_net == 0


def test_every_period_ends_when_the_clock_reaches_zero_and_the_clock_is_never_negative(games):
    for _, engine, rules, _ in games:
        regulation = [p for p in rules.periods if p[0] <= 4]
        # the rig records a period end at period_checks; a touchdown on the last play of the fourth quarter whose try cannot change the
        # result has no try and goes straight to the end of the game (SX.13), past that hook (seeds 105 and 156 since BC.2's draws, D-180)
        walk_off = engine.outcomes[-1].score == "touchdown" and engine.s.extras.left == 0 and len(regulation) == 3
        assert len(regulation) == 4 or walk_off
        assert all(left == 0 for _, _, left in rules.periods)
        assert all(left >= 0 and pending >= 0 for _, left, pending in rules.lefts)


def test_one_two_minute_warning_in_the_second_and_fourth_quarter_and_never_in_the_first_and_third(games):
    for _, _, rules, _ in games:
        quarters = [q for q, _ in rules.warnings]
        assert quarters.count(2) == 1 and quarters.count(4) == 1
        assert 1 not in quarters and 3 not in quarters
        assert all(0 < left <= 120 for _, left in rules.warnings)


def test_never_more_timeouts_than_the_rules_allow_and_never_two_in_one_dead_ball_period(games):
    for _, _, rules, _ in games:
        per_unit = {}
        for quarter, side, left, remaining, unit in rules.timeouts:
            per_unit[(unit, side)] = per_unit.get((unit, side), 0) + 1
            assert remaining >= 0
        assert all(n <= count_for(unit) for (unit, _), n in per_unit.items())
        assert len(rules.dead_balls) == len(set(rules.dead_balls))


def test_the_extras_record_is_valid_at_the_end_and_the_timeouts_used_add_up(games):
    for _, engine, rules, _ in games:
        x = engine.s.extras
        x.check()
        assert sum(x.used) == len(rules.timeouts)


def test_the_statistics_say_the_timeouts_used(games):
    rig, engine, _, _ = games[0]
    said = [t for t, _, _ in rig.said]
    assert said.count(" Time Outs Used") >= 4                        # after every quarter and at the end


def test_the_sample_falls_in_the_calibration_bands(games):
    plays = {q: [] for q in (1, 2, 3, 4)}
    for _, engine, _, _ in games:
        counts = {}
        for quarter, _ in engine.steps:
            counts[quarter] = counts.get(quarter, 0) + 1
        for q in plays:
            plays[q].append(counts.get(q, 0))
    mean = statistics.mean(n for q in plays for n in plays[q])
    low, high = T.TARGET_PLAYS_PER_QUARTER
    assert low <= mean <= high, mean
    extra = (statistics.mean(plays[2] + plays[4]) - statistics.mean(plays[1] + plays[3]))
    assert T.TARGET_LATE_QUARTER_EXTRA[0] - 1 <= extra <= T.TARGET_LATE_QUARTER_EXTRA[1] + 1, extra
    per_team = statistics.mean(len(rules.timeouts) for _, _, rules, _ in games) / 2
    assert 3.0 <= per_team <= 4.7, per_team


def test_quarters_two_and_four_use_most_of_the_timeouts(games):
    by_quarter = {}
    for _, _, rules, _ in games:
        for quarter, *_ in rules.timeouts:
            by_quarter[quarter] = by_quarter.get(quarter, 0) + 1
    assert by_quarter.get(2, 0) + by_quarter.get(4, 0) > 3 * (by_quarter.get(1, 0) + by_quarter.get(3, 0))


# ----- games played through the menus -----

def player_policy(rig, seed):
    """Enter, digits, Down, now and then T (which calls a time out at once), F1 to F4, Escape answered no; never Save Game."""
    rng = random.Random(seed)

    def policy(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Save Game "):
            return DOWN
        if "concede" in last:
            return "n"
        if last.endswith("Time Out ") and rng.random() < 0.6:
            return ENTER
        roll = rng.random()
        if roll < 0.40:
            return ENTER
        if roll < 0.75:
            return str(rng.randint(1, 6))
        if roll < 0.85:
            return "t"
        if roll < 0.93:
            return DOWN
        if roll < 0.99:
            return rng.choice((F1, F2, F3, F4))
        return ESCAPE
    return policy


@pytest.mark.parametrize("seed", range(6))
def test_a_whole_game_through_the_menus_with_the_players_timeouts(tmp_path, seed):
    rig = make_rig(tmp_path, rng=random.Random(500 + seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = player_policy(rig, 900 + seed)
    program_rules = RecordingRules(auto_sides=(2,))
    result = play(rig, rules=program_rules)
    rules = program_rules.used                    # the game's own object (SX.3: before, the checks read an unused one)
    assert rules is not None and rules.state is not None
    assert result.scores is not None and result.scores[0] != result.scores[1]
    assert rig.rnd.fallbacks == 0
    said = [t for t, _, _ in rig.said]
    assert rules.state.extras.used[0] >= 1                # the player's own timeouts: the T key of the policy calls them (SX.2b, rule 0.22)
    assert sum(rules.state.extras.used) == len(rules.timeouts)
    per_unit = {}
    for quarter, side, left, remaining, unit in rules.timeouts:
        per_unit[(unit, side)] = per_unit.get((unit, side), 0) + 1
    assert all(n <= count_for(unit) for (unit, _), n in per_unit.items())
    assert len(rules.dead_balls) == len(set(rules.dead_balls))


def test_a_game_with_timeouts_off_never_offers_or_calls_one(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(77), fast=True, vtrnt=2)
    rig.keys.policy = player_policy(rig, 78)
    program_rules = RecordingRules(timeouts_on=False, auto_sides=(2,))
    result = play(rig, rules=program_rules)
    rules = program_rules.used
    assert result.scores is not None
    said = [t for t, _, _ in rig.said]
    assert not any("Time Out" in t or "time out" in t for t in said)
    assert rules.timeouts == [] and rules.state.extras.used == [0, 0]


def test_the_program_rules_object_is_not_used_for_a_game_itself(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(3), fast=True, vtrnt=2)
    program_rules = NflRules()
    rig.game.rules = program_rules
    rig.keys.policy = player_policy(rig, 4)
    play(rig)
    assert program_rules.state is None and program_rules.game is None     # for_game made the game's own object
