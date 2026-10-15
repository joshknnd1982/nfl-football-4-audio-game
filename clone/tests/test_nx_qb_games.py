"""Whole seeded games with the quarterback runs on, both sides played by the computer (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 7
and 15; PX SX.5). This is inspired by Jim Kitchen.

The properties that must hold in every game, whatever the dice: the statistics equal the events (a penalty may erase a run,
never add one), no run that scored slid, no slide left fewer than 6 yards, a sneak never slid and never went out of bounds,
the clock never goes negative and every period ends at 0, the extras record is valid at the end, no redraw ran out, and the
play noise was never left looping. The numbers of the calibration (10,000 games) are in work/calibrate_qb_sx5.py.
"""
import pytest

from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nflrig import RecordingRules, sim_game

SEEDS = range(1, 13)


@pytest.fixture(scope="module")
def games(tmp_path_factory):
    out = {}
    for seed in SEEDS:
        rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True)
        rig, engine, rules, result = sim_game(tmp_path_factory.mktemp("g%d" % seed), seed, rules=rules)
        out[seed] = (rig, engine, rules, result)
    return out


def test_the_games_have_quarterback_runs_of_every_kind(games):
    kinds = {e[2] for _, _, rules, _ in games.values() for e in rules.qb.events}
    assert kinds == {"sneak", "keeper", "draw", "scramble"}


def test_the_statistics_equal_the_events_less_the_runs_a_penalty_erased(games):
    for seed, (rig, engine, rules, result) in games.items():
        x = engine.s.extras
        for side in (1, 2):
            events = [e for e in rules.qb.events if e[1] == side]
            assert x.qb_runs[side - 1] <= len(events), seed
        erased = len(rules.qb.events) - sum(x.qb_runs)
        accepted_erasing = [e for e in rules.penalty.events if e[1] in ("accepted", "major", "offset")]
        assert 0 <= erased <= len(accepted_erasing), (seed, erased)


def test_every_event_obeys_the_rules_of_the_run(games):
    for seed, (rig, engine, rules, result) in games.items():
        for quarter, side, kind, yards, slid, down, to_go, outcome_kind, try_ in rules.qb.events:
            assert kind in ("sneak", "keeper", "draw", "scramble")
            assert not (kind == "sneak" and slid), seed
            if slid:
                assert yards >= 6, (seed, yards)                              # 8 or more, cut by at most 2
            if kind != "scramble" and not try_:
                assert 1 <= down <= 4
            if outcome_kind == O.TOUCHDOWN:
                assert not slid, seed                                          # a run that scored never slides
        assert rules.qb.eligible >= len(rules.qb.slides)
        assert rules.qb.late_hits <= len(rules.qb.slides)


def test_a_scramble_replaces_a_pass_and_is_counted_as_a_run_not_a_pass(games):
    for seed, (rig, engine, rules, result) in games.items():
        scrambles = [o for o in engine.outcomes if o.qb_run == "scramble"]
        assert all(o.offense_play in (3, 4, 5) for o in scrambles), seed
        assert all(o.kind in (O.RUN, O.TOUCHDOWN, O.SAFETY_KIND, O.TWO_POINT_TRY, O.FUMBLE) for o in scrambles), seed
        designed = [o for o in engine.outcomes if o.qb_run in ("sneak", "keeper", "draw")]
        assert all(o.offense_play in (8, 9, 10) for o in designed), seed


def test_the_clocks_the_records_and_the_games_are_sound(games):
    for seed, (rig, engine, rules, result) in games.items():
        engine.s.extras.check()
        assert all(left >= 0 for _, left, _ in rules.lefts), seed
        assert all(left == 0 for _, _, left in rules.periods), seed
        assert rig.rnd.fallbacks == 0 and engine.noise_net == 0, seed
        assert result.scores is not None and result.scores[0] != result.scores[1], seed
        assert engine.s.qb_run == "" and not engine.s.slid


def test_a_game_with_the_switch_off_has_no_quarterback_run_at_all(tmp_path):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=False)
    rig, engine, rules, result = sim_game(tmp_path, 3, rules=rules)
    assert rules.qb.events == [] and engine.s.extras.qb_runs == [0, 0]
    assert not [o for o in engine.outcomes if o.qb_run or o.offense_play >= 8]
    assert isinstance(rules, NflRules)


# ----- games played through the menus by a player who runs the quarterback -----

def player_policy(rig, seed):
    """Enter, the digits 1 to 9 and 0 (so the three runs are chosen often), Down, T, F1 to F4, Escape answered no, A and D at
    a penalty's question; never Save Game."""
    import random
    rng = random.Random(seed)

    def policy(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Save Game "):
            return 40
        if "concede" in last:
            return "n"
        roll = rng.random()
        if roll < 0.35:
            return 13
        if roll < 0.80:
            return str(rng.choice("123456789000"))
        if roll < 0.88:
            return "t"
        if roll < 0.94:
            return rng.choice(("a", "d"))
        if roll < 0.99:
            return rng.choice((112, 113, 114, 115))
        return 27
    return policy


@pytest.mark.parametrize("seed", range(5))
def test_a_whole_game_through_the_menus_with_the_players_sneaks_keepers_and_draws(tmp_path, seed):
    import random
    from pagrig import make_rig, play
    rig = make_rig(tmp_path, rng=random.Random(700 + seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = player_policy(rig, 800 + seed)
    program_rules = RecordingRules(auto_sides=(2,), penalties_on=True, onside_on=True, qb_on=True)
    result = play(rig, rules=program_rules)
    assert result.scores is not None and result.scores[0] != result.scores[1]
    assert rig.rnd.fallbacks == 0
    said = [t for t, _, _ in rig.said]
    assert " 8. Quarterback Sneak " in said and " 10. Quarterback Draw " in said
    engine_rules = program_rules.used
    assert engine_rules is not None
    x = engine_rules.state.extras
    x.check()
    assert x.qb_on and x.qb_runs[0] >= 1                      # the player ran the quarterback at least once
    assert sum(x.qb_runs) <= len(engine_rules.qb.events)
