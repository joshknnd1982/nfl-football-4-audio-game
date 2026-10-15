"""Whole games with the N. F. L. rules and the penalties on: the properties of C8, the calibration bands on a smaller sample,
and games played through the menus by a seeded player who answers the accept-or-decline prompts (nfl4 only, rule 0.13;
NFL_EXTRA_FEATURES C8, NX7; NFL_EXTRAS_DESIGN 9; PX SX.3). This is inspired by Jim Kitchen.

The 10,000-game run of NX7's done-when is work/calibrate_penalties_sx3.py (its report: work/calibrate_penalties_sx3_10000.txt);
here 40 seeded games in every suite run check the same properties.
"""
import random
import statistics

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nflrig import RecordingRules, sim_game
from pagrig import make_rig, play

GAMES = 40
ACCEPTED = ("accepted", "major", "on the try")
ENTER, ESCAPE, DOWN, F1, F2, F3, F4 = 13, 27, 40, 112, 113, 114, 115


@pytest.fixture(scope="module")
def games(tmp_path_factory):
    out = []
    for seed in range(300, 300 + GAMES):
        rules = RecordingRules(penalties_on=True)
        out.append(sim_game(tmp_path_factory.mktemp("px%d" % seed), seed, rules=rules))
    return out


def test_every_game_ends_with_a_winner_and_no_safety_net_was_needed(games):
    for rig, engine, rules, result in games:
        assert result.scores is not None and result.scores[0] != result.scores[1]
        assert rig.rnd.fallbacks == 0 and engine.noise_net == 0


def test_every_period_still_ends_at_zero_with_no_negative_clock(games):
    for _, engine, rules, _ in games:
        assert len([p for p in rules.periods if p[0] <= 4]) == 4
        assert all(left == 0 for _, _, left in rules.periods)
        assert all(left >= 0 and pending >= 0 for _, left, pending in rules.lefts)


def test_the_record_is_valid_and_the_statistics_count_every_accepted_penalty(games):
    for _, engine, rules, _ in games:
        x = engine.s.extras
        x.check()
        accepted = [e for e in rules.penalty.events if e[1] in ACCEPTED]
        assert x.flags == [sum(1 for e in accepted if e[3] == side) for side in (1, 2)]
        assert sum(x.flag_yards) == sum(e[4] for e in accepted)
        assert not x.extension and x.foul_clock in ("", "live", "pre", "runoff")


def test_the_sample_falls_near_the_nfl_rates(games):
    per_game = [sum(1 for e in rules.penalty.events if e[1] in ACCEPTED) for _, _, rules, _ in games]
    mean = statistics.mean(per_game)
    low, high = T.TARGET_ACCEPTED_FOULS_PER_GAME
    assert low - 1.5 <= mean <= high + 1.5, mean                      # 40 games: about 0.6 of sampling error
    events = [e for _, _, rules, _ in games for e in rules.penalty.events]
    assert any(e[1] == "declined" for e in events) and any(e[1] == "offset" for e in events)
    pre = sum(1 for e in events if e[1] in ACCEPTED and e[5]) / sum(1 for e in events if e[1] in ACCEPTED)
    assert 0.2 <= pre <= 0.5, pre


def test_the_statistics_say_the_penalties(games):
    rig = games[0][0]
    said = [t for t, _, _ in rig.said]
    assert said.count(X.text("NXS-01")) >= 4 and said.count(X.text("NXS-02")) >= 4


def test_a_foul_before_the_snap_is_not_a_counted_play(games):
    """The play counter grows by one at every counted play and never at a foul before the snap: within a period the
    counters of the counted plays follow each other with no gap."""
    pre_snap = 0
    for _, engine, rules, _ in games:
        pre_snap += sum(1 for e in rules.penalty.events if e[5])
        for (q1, c1), (q2, c2) in zip(engine.steps, engine.steps[1:]):
            if q1 == q2:
                assert c2 == c1 + 1, (q1, c1, c2)
    assert pre_snap > 0


# ----- games through the menus -----

def player_policy(rig, seed):
    """Enter, digits, Down, F1 to F4, A and D at a penalty prompt, Escape answered no; never Save Game."""
    rng = random.Random(seed)

    def policy(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Save Game "):
            return DOWN
        if "concede" in last:
            return "n"
        if last in (X.text("NXP-A01"), X.text("NXP-A02"), X.text("NXP-A03"), X.text("NXP-A04")):
            roll = rng.random()
            if roll < 0.5:
                return ENTER
            return rng.choice(("a", "d", DOWN, F1, F3, F4, 97, "x"))
        roll = rng.random()
        if roll < 0.45:
            return ENTER
        if roll < 0.80:
            return str(rng.randint(1, 6))
        if roll < 0.90:
            return DOWN
        if roll < 0.99:
            return rng.choice((F1, F2, F3, F4))
        return ESCAPE
    return policy


@pytest.mark.parametrize("seed", range(5))
def test_a_whole_game_through_the_menus_with_the_players_penalty_choices(tmp_path, seed):
    rig = make_rig(tmp_path, rng=random.Random(700 + seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = player_policy(rig, 800 + seed)
    program_rules = RecordingRules(auto_sides=(2,), penalties_on=True)
    result = play(rig, rules=program_rules)
    rules = program_rules.used                                       # the game's own object (for_game)
    assert result.scores is not None and result.scores[0] != result.scores[1]
    assert rig.rnd.fallbacks == 0
    said = [t for t, _, _ in rig.said]
    assert X.text("NXP-01") in said
    x = rules.state.extras
    x.check()
    accepted = [e for e in rules.penalty.events if e[1] in ACCEPTED]
    assert x.flags == [sum(1 for e in accepted if e[3] == side) for side in (1, 2)]


def test_a_game_with_penalties_off_never_calls_a_foul(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(91), fast=True, vtrnt=2)
    rig.keys.policy = player_policy(rig, 92)
    program_rules = RecordingRules(auto_sides=(2,), penalties_on=False)
    result = play(rig, rules=program_rules)
    rules = program_rules.used
    assert result.scores is not None and rules.state.extras.flags == [0, 0]
    said = [t for t, _, _ in rig.said]
    assert X.text("NXP-01") not in said and rules.penalty.events == []
    assert X.text("NXS-01") not in said
