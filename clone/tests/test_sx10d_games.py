"""The catalog's defense and the kicks of 2026 in whole games (nfl4 only, rule 0.13; NX-P1 to NX-P8, NX-R7; NFL_PLAYS_DESIGN 2, 4.9 and 7;
PX SX.10d, D-094). This is inspired by Jim Kitchen.

Whole seeded games with a playbook on both of the player's sides: the computer plays both teams, and side 1's offense calls a catalog play
of the family the computer's draw gave, its defense a catalog call of the family drawn; every kick is a kick of 2026. The games end as the
original's games end, with the scores the statistics hold, every kind of kick happens, the extras' record stays valid, and the kicks come
out near the 2024 to 2026 numbers (a loose check: SX.10e measures the bands).
"""
import random

import pytest

from nfl4.extras import offense_flow as OF
from nfl4.extras.plays import catalog as C
import nflrig


class BothSidesSim(nflrig.SimEngine):
    """Both sides by the computer; side 1 calls catalog plays on offense (SX.10c's CatalogSim) and catalog calls on defense (SX.10d)."""

    def __init__(self, *args, picker_seed=7, **kwargs):
        super().__init__(*args, **kwargs)
        self.picker = random.Random(picker_seed)

    def offense_menu(self):
        step = super().offense_menu()
        s = self.s
        if s.offense_play in (6, 7):
            return step
        pool = [c for c in C.OFFENSE if OF.engine_family(c) == s.offense_play and c.kind not in ("kneel", "spike")]
        concept = self.picker.choice(pool or [c for c in C.OFFENSE if c.kind not in ("kneel", "spike")])
        self.rules.offense.called = concept.id
        s.offense_play = OF.engine_family(concept)
        return step

    def defense_menu(self):
        step = super().defense_menu()
        pool = [c for c in C.DEFENSE if c.family == self.s.defense_play]
        self.rules.defense.called = self.picker.choice(pool).id
        if self.picker.random() < 0.2:
            self.s.extras.kick_defense = self.picker.choice(("", "K032", "K033", "K034", "K035", "K036"))
        return step


def both_sides_game(tmp_path, seed):
    rig = nflrig.make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2)
    rules = nflrig.RecordingRules(qb_on=True, penalties_on=True, challenges_on=True, onside_on=True, playbooks_on=True)
    rules.forced = (("west", "pressure"), ("pro", "pro"))
    engine = BothSidesSim(rig.game, rules, quarterback_names=lambda state: nflrig.QUARTERBACKS, picker_seed=seed)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, engine, rules, result


@pytest.mark.parametrize("seed", range(11, 19))
def test_whole_games_with_the_catalogs_defense_and_the_kicks_of_2026_end_and_their_scores_are_the_statistics(tmp_path, seed):
    rig, engine, rules, result = both_sides_game(tmp_path, seed)
    s = engine.s
    assert result.scores == (s.score(1), s.score(2))
    assert engine.noise_net == 0 and rig.rnd.fallbacks == 0
    s.extras.check()
    assert rules.kicks.on(s)
    defended = rules.defense.events
    assert len(defended) > 20 and all(call.startswith("D") and play.startswith("O") for play, call, *_rest in defended)
    assert all(3 <= backs <= 7 and 5 <= box <= 8 for *_x, backs, box in defended)
    kinds = {what for what, *_rest in rules.kicks.events}
    assert {"kickoff", "punt"} <= kinds, kinds
    assert rules.offense.result is None


def test_the_kicks_of_2026_come_out_near_the_leagues_numbers_over_eight_games(tmp_path):
    events, points = [], []
    for seed in range(11, 19):
        _rig, _engine, rules, result = both_sides_game(tmp_path / str(seed), seed)
        events += rules.kicks.events
        points += list(result.scores)
    tries = [kind for what, _side, _c, kind, _n in events if what == "extra point"]
    goals = [kind for what, _side, _c, kind, _n in events if what == "field goal"]
    kickoffs = [kind for what, _side, _c, kind, _n in events if what == "kickoff"]
    punts = [kind for what, _side, _c, kind, _n in events if what == "punt"]
    assert tries and sum(k == "good" for k in tries) / len(tries) >= 0.8, tries
    assert goals and 0.4 <= sum(k == "made" for k in goals) / len(goals) <= 1.0, goals
    assert kickoffs and sum(k == "touchback" for k in kickoffs) / len(kickoffs) <= 0.45, kickoffs
    assert punts and any(k == "returned" for k in punts) and any(k in ("fair_catch", "downed", "out_of_bounds", "touchback")
                                                               for k in punts)
    assert 5 <= sum(points) / len(points) <= 45, points


def test_the_same_seed_is_the_same_game(tmp_path):
    first = both_sides_game(tmp_path / "a", 21)
    second = both_sides_game(tmp_path / "b", 21)
    assert first[3].scores == second[3].scores and first[2].kicks.events == second[2].kicks.events
    assert first[2].defense.events == second[2].defense.events
