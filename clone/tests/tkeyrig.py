"""Whole games in which the player's T key is pressed at random moments (nfl4 only, rule 0.13; owner rule 0.22, PX SX.2b). This is inspired by Jim Kitchen.

The real engine with every switch of the N. F. L. rules on, both sides played by the computer (nflrig.SimEngine), on the fast virtual clock.
Before a pause of the play (the pauses pump the keys, as the original's do) the "player" presses T with a small chance. The keys are posted the
way the window thread posts them (KeyInput.post), so the speech is cut at once, the game thread takes the key at its next pump and the engine
decides: a timeout before the snap (the play is withdrawn), a timeout in the dead ball, a request kept during a live play, or a refusal.

`properties(...)` reads one finished game and returns the problems: the limits of N1 (design 6.3) and the new ones of rule 0.22 (never a
timeout while the ball is live, never two by one team in one dead-ball period). Used by tests/test_nx_tkey_games.py and work/tkey_games_sx2b.py.
"""
import random

from nflrig import QUARTERBACKS, RecordingRules, SimEngine
from pagrig import make_rig


class WatchingRules(RecordingRules):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.live_grants = 0
        self.results = []                      # "granted", "refused" or "live kept" of every T key that reached the rules

    def grant(self, state, side):
        engine = self.game.play_engine
        if engine is not None and engine.t_live:
            self.live_grants += 1
        super().grant(state, side)

    def timeout_key(self, state, live, undo=None, called=None):
        result = super().timeout_key(state, live, undo, called)
        self.results.append(("live " if live else "") + result)
        return result


class TKeyEngine(SimEngine):
    def __init__(self, *args, press_in_1000=12, seed=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.press_rng = random.Random(seed * 7919 + 17)
        self.press_in_1000 = press_in_1000
        self.presses = 0
        self.withdrawn_plays = 0

    def _maybe(self):
        if self.game_on and self.press_rng.random() * 1000 < self.press_in_1000:
            self.presses += 1
            self.keys.post(84)
            self.keys.post_char("t")

    def dy(self, seconds, site):
        self._maybe()
        super().dy(seconds, site)

    def rady(self, site):
        self._maybe()
        super().rady(site)

    def withdrawn(self, withdrawal):
        self.withdrawn_plays += 1
        return super().withdrawn(withdrawal)


def sim_t_game(tmp_path, seed, press_in_1000=12):
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
    rules = WatchingRules(timeouts_on=True, auto_sides=(1, 2), penalties_on=True, onside_on=True, onside_always=True, qb_on=True,
                          challenges_on=True, playbooks_on=True)
    engine = TKeyEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS, press_in_1000=press_in_1000, seed=seed)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, engine, rules, result


def properties(rig, engine, rules, result) -> list[str]:
    from nfl4.extras.timeouts import count_for
    used = rules
    problems = []
    if any(left < 0 for _, left, _ in used.lefts):
        problems.append("a negative clock")
    for quarter, counter, left in used.periods:
        if left != 0:
            problems.append("period %d ended at %d seconds" % (quarter, left))
    warned = {}
    for quarter, _ in used.warnings:
        warned[quarter] = warned.get(quarter, 0) + 1
    if any(n > 1 for q, n in warned.items() if q <= 4):
        problems.append("two warnings in one period")
    units = {}
    for quarter, side, left, remaining, unit in used.timeouts:
        units[(unit, side)] = units.get((unit, side), 0) + 1
        if remaining < 0:
            problems.append("a timeout left below 0")
    for (unit, side), n in units.items():
        if n > count_for(unit):
            problems.append("%d timeouts in %s for side %d" % (n, unit, side))
    seen = set()
    for entry in used.dead_balls:
        if entry in seen:
            problems.append("two timeouts by side %d in one dead-ball period (quarter %d, play %d)" % entry)
        seen.add(entry)
    if used.live_grants:
        problems.append("%d timeouts granted while the ball was live" % used.live_grants)
    if rig.rnd.fallbacks:
        problems.append("a redraw ran out")
    if result.scores is None or result.scores[0] == result.scores[1]:
        problems.append("no winner")
    if engine.noise_net:
        problems.append("the play noise safety net acted")
    return problems
