"""Whole seeded games with the replay challenges on, both sides played by the computer, and games through the menus by a player who
challenges (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 6 and 15; PX SX.6). This is inspired by Jim Kitchen.

The properties that must hold in every game, whatever the dice: never more than three challenges a team, a third only after a
success, a challenge only with a time out in hand and only on a play a coach may challenge, the replay official only on plays
that are his, every reversal tells its play again once, the statistics stay whole after the takings back, the clock never goes
negative and every period ends at 0, the extras record is valid at the end, no redraw ran out and the play noise was never left
looping. The numbers of the calibration (10,000 games) are in work/calibrate_review_sx6.py.
"""
import random

import pytest

from nfl4.extras import review as RV
from nfl4.game import outcome as O
from nflrig import RecordingRules, sim_game
from pagrig import make_rig, play

SEEDS = range(1, 21)


def all_on(**kwargs):
    return RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, **kwargs)


@pytest.fixture(scope="module")
def games(tmp_path_factory):
    out = {}
    for seed in SEEDS:
        rig, engine, rules, result = sim_game(tmp_path_factory.mktemp("g%d" % seed), seed, rules=all_on())
        out[seed] = (rig, engine, rules, result)
    return out


def test_the_games_have_booth_reviews_and_coach_challenges_reversed_and_confirmed(games):
    """(A wrong ruling that the replay does not show clearly is 15 percent of the wrong ones: the scenes of
    test_nx_review_flows.py have it; twenty games may not.)"""
    events = [e for _, _, rules, _ in games.values() for e in rules.review.events]
    assert {e[1] for e in events} == {"booth", "coach"}
    assert {RV.REVERSED, RV.CONFIRMED} <= {e[5] for e in events} <= {RV.REVERSED, RV.STANDS, RV.CONFIRMED}
    assert {e[1] for e in events if e[5] == RV.REVERSED} == {"booth", "coach"}


def test_never_more_than_three_challenges_a_team_and_a_third_only_after_a_success(games):
    for seed, (rig, engine, rules, result) in games.items():
        x = engine.s.extras
        for side in (1, 2):
            mine = [e for e in rules.review.events if e[1] == "coach" and e[2] == side]
            assert len(mine) == x.chal_used[side - 1] <= 3, seed
            assert sum(1 for e in mine if e[5] == RV.REVERSED) == x.chal_won[side - 1], seed
            for number, event in enumerate(mine, start=1):
                if number == 3:
                    assert any(earlier[5] == RV.REVERSED for earlier in mine[:2]), (seed, "a third without a success")


def test_a_challenge_has_a_time_out_in_hand_and_is_for_a_play_a_coach_may_challenge(games):
    for seed, (rig, engine, rules, result) in games.items():
        for quarter, who, side, category, wrong, outcome, ruled, reason, timeouts in rules.review.events:
            if who == "coach":
                assert reason == "" and timeouts >= 1 and quarter <= 4, (seed, quarter, reason, timeouts)
            else:
                assert reason in ("booth", "warning", "overtime"), (seed, reason)


def test_a_review_that_did_not_reverse_costs_the_coach_a_time_out_and_a_reversal_costs_nothing(games):
    for seed, (rig, engine, rules, result) in games.items():
        x = engine.s.extras
        lost = [sum(1 for e in rules.review.events if e[1] == "coach" and e[2] == side and e[5] != RV.REVERSED)
                for side in (1, 2)]
        assert [x.chal_used[i] - x.chal_won[i] for i in (0, 1)] == lost, seed
        for side in (1, 2):
            assert x.timeouts[side - 1] >= 0 and x.used[side - 1] >= lost[side - 1], seed


def test_a_booth_reversal_is_followed_by_the_corrected_end_point_of_the_same_play_and_that_is_not_ruled_again(games):
    """The booth's reversal marks the record of the ruled play (`then`); a coach's comes later, from the menu or H10, so its
    record is not marked. The next record is the same play (the side, the plays, the spot) with nothing taken over."""
    for seed, (rig, engine, rules, result) in games.items():
        booth = [e for e in rules.review.events if e[1] == "booth" and e[5] == RV.REVERSED]
        superseded = [i for i, o in enumerate(engine.outcomes) if o.then and o.then.startswith("reviewed")]
        assert len(superseded) == len(booth), seed
        for i in superseded:
            first, again = engine.outcomes[i], engine.outcomes[i + 1]
            assert (again.offense, again.offense_play, again.defense_play, again.spot_before) == (
                first.offense, first.offense_play, first.defense_play, first.spot_before), seed
            assert again.then is None and again.kind in (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.TOUCHDOWN, O.FUMBLE)
        assert not rules.review.replaying, seed


def test_every_reversal_the_computers_too_has_exactly_one_corrected_end_point(games):
    """Review finding 3: the rig dropped the step a computer's won challenge answers, so only the booth's reversals were proven.
    A reversal sets the corrected end point and the hook counts it once: as many as there were reversals, coach or booth."""
    coach_reversals = 0
    for seed, (rig, engine, rules, result) in games.items():
        reversals = [e for e in rules.review.events if e[5] == RV.REVERSED]
        assert rules.review.corrected == len(reversals), seed
        coach_reversals += sum(1 for e in reversals if e[1] == "coach")
    assert coach_reversals >= 1                                  # (the twenty seeded games have three of them)


def test_the_statistics_stay_whole_after_the_takings_back(games):
    for seed, (rig, engine, rules, result) in games.items():
        for side in (1, 2):
            stats = engine.s.stats[side]
            assert min(stats.pass_attempts, stats.completions, stats.sacked, stats.intercepted, stats.running_plays,
                       stats.fumbles_lost, stats.first_downs, stats.score) >= 0, (seed, side)
            assert stats.completions <= stats.pass_attempts, (seed, side)
        x = engine.s.extras
        assert min(x.qb_runs) >= 0 and sum(x.qb_runs) <= len(rules.qb.events), seed


def test_the_clocks_the_records_and_the_games_are_sound(games):
    for seed, (rig, engine, rules, result) in games.items():
        engine.s.extras.check()
        assert all(left >= 0 for _, left, _ in rules.lefts), seed
        assert all(left == 0 for _, _, left in rules.periods), seed
        assert rig.rnd.fallbacks == 0 and engine.noise_net == 0, seed
        assert result.scores is not None and result.scores[0] != result.scores[1], seed
        assert engine.s.extras.challenges_on is True


def test_a_play_with_a_flag_was_never_ruled(games):
    for seed, (rig, engine, rules, result) in games.items():
        assert len(rules.review.rulings) <= len(engine.outcomes), seed
        assert all(wrong or close or hint == "" for _, _, wrong, close, hint, _ in rules.review.rulings), seed


def test_a_game_with_the_switch_off_has_no_ruling_at_all(tmp_path):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=False)
    rig, engine, rules, result = sim_game(tmp_path, 3, rules=rules)
    assert rules.review.rulings == [] and rules.review.events == []
    assert engine.s.extras.chal_used == [0, 0] and engine.s.extras.challenges_on is False
    assert not [o for o in engine.outcomes if o.then and o.then.startswith("reviewed")]


# ----- games played through the menus by a player who challenges -----

def player_policy(rig, seed):
    """Enter, the digits (the plays), C and Y or N (the challenge and its question), T, F1 to F4, Escape answered no, A and D at a
    penalty's question; never Save Game."""
    rng = random.Random(seed)

    def policy(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Save Game "):
            return 40
        if "concede" in last:
            return "n"
        roll = rng.random()
        if roll < 0.30:
            return 13
        if roll < 0.55:
            return str(rng.choice("123456789000"))
        if roll < 0.75:
            return "c"
        if roll < 0.83:
            return rng.choice(("y", "n"))
        if roll < 0.89:
            return "t"
        if roll < 0.94:
            return rng.choice(("a", "d"))
        if roll < 0.99:
            return rng.choice((112, 113, 114, 115))
        return 27
    return policy


@pytest.mark.parametrize("seed", range(6))
def test_a_whole_game_through_the_menus_with_the_players_challenges(tmp_path, seed):
    rig = make_rig(tmp_path, rng=random.Random(900 + seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = player_policy(rig, 950 + seed)
    program_rules = RecordingRules(auto_sides=(2,), penalties_on=True, onside_on=True, qb_on=True, challenges_on=True)
    result = play(rig, rules=program_rules)
    assert result.scores is not None and result.scores[0] != result.scores[1]
    assert rig.rnd.fallbacks == 0
    engine_rules = program_rules.used
    assert engine_rules is not None
    x = engine_rules.state.extras
    x.check()
    assert x.challenges_on and 0 <= x.chal_used[0] <= 3 and 0 <= x.chal_used[1] <= 3
    assert all(left >= 0 for _, left, _ in engine_rules.lefts)
    for quarter, who, side, category, wrong, outcome, ruled, reason, timeouts in engine_rules.review.events:
        assert reason == "" or who == "booth"
