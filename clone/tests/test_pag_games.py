"""Whole games of pag on a seeded source: the invariants of GAP_REGISTER G-C1, the pause sites, the safety nets, the
hooks in Classic, and the pass outcome odds. This is inspired by Jim Kitchen.

S8.1 runs the 10,000-game property test; here a smaller number of games checks the same properties in every suite run:
yard line 1 to 50, down 1 to 4 and yards to go 1 or more at every next play, scores made of 6, 1, 2, 3 and 2, every
period ends after its drawn number of counted plays (Q14), a tie after four quarters goes to overtime, every game ends
with a winner; the pause sites are all in work/pause_table_s43.txt; no redraw runs out of tries (G-D1), the play noise
never reaches a key wait (G-A2), the replay list stays far below the original's 501 places (B-P41).
"""
import random
import re

import pytest

from nfl4.game import pag as pag_module
from nfl4.game.outcome import FIELD_GOAL_GOOD
from nfl4.game.rules import ClassicRules
from pagrig import Draws, engine_rig, make_rig, play, run_steps
from specfiles import GAME_ROOT

ENTER, ESCAPE, DOWN, F1, F2, F3, F4 = 13, 27, 40, 112, 113, 114, 115
GAMES = 30


def lively_policy(rig, seed):
    """Enter, digits, Down, now and then F1 to F4 or Escape (answered "no"); never Save Game."""
    rng = random.Random(seed)

    def policy(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Save Game "):
            return DOWN
        if "concede" in last:
            return "n"
        roll = rng.random()
        if roll < 0.45:
            return ENTER
        if roll < 0.80:
            return str(rng.randint(1, 6))
        if roll < 0.93:
            return DOWN
        if roll < 0.98:
            return rng.choice((F1, F2, F3, F4))
        return ESCAPE
    return policy


class SpyEngine(pag_module.PlayEngine):
    """Records the state at every next-play step and every score change."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.steps = []

    def next_play(self):
        s = self.s
        self.steps.append((s.quarter, s.counter, s.half, s.yard_line, s.down, s.to_go, s.score(1), s.score(2)))
        return super().next_play()


def spy_game(tmp_path, seed, rules=None):
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = lively_policy(rig, seed + 1000)
    rig.game.pause_log = []
    original = pag_module.PlayEngine
    pag_module.PlayEngine = SpyEngine
    engines = []
    try:
        real_init = SpyEngine.__init__

        def init(self, *args, **kwargs):
            real_init(self, *args, **kwargs)
            engines.append(self)
        SpyEngine.__init__ = init
        result = play(rig, rules=rules)
    finally:
        pag_module.PlayEngine = original
        SpyEngine.__init__ = real_init
    return rig, engines[0], result


@pytest.fixture(scope="module")
def games(tmp_path_factory):
    return [spy_game(tmp_path_factory.mktemp("game%d" % seed), seed) for seed in range(GAMES)]


def test_every_game_ends_with_a_winner_and_the_engine_never_needed_a_safety_net(games):
    for rig, engine, result in games:
        assert result.scores is not None and result.scores[0] != result.scores[1] and not result.saved
        assert rig.rnd.fallbacks == 0
        assert engine.noise_net == 0
        assert rig.game.replay_longest < 200


def test_the_ball_down_and_distance_are_valid_at_every_next_play(games):
    for _, engine, _ in games:
        for quarter, counter, half, yard, down, to_go, _, _ in engine.steps:
            assert half in (1, 2) and 1 <= yard <= 50 and 1 <= down <= 4 and to_go >= 1, engine.steps[-1]


def test_scores_change_only_by_the_values_of_football(games):
    for _, engine, _ in games:
        previous = (0, 0)
        for step in engine.steps:
            for side in (0, 1):
                change = step[6 + side] - previous[side]
                assert change in (0, 2, 3, 6, 7, 8), change             # a touchdown with its try counts as one play
            previous = step[6:8]


def test_every_period_lasts_its_drawn_number_of_counted_plays_q14(games):
    checked = 0
    for _, engine, result in games:
        plays = engine.s.plays
        by_quarter = {}
        for quarter, *_ in engine.steps:
            by_quarter[quarter] = by_quarter.get(quarter, 0) + 1
        for quarter, expected in ((1, plays[0] - 1), (2, plays[1] - 1), (3, plays[2])):
            assert by_quarter[quarter] == expected
            checked += 1
        if engine.s.overtime == 0:
            assert by_quarter[4] == plays[3] - 1
    assert checked == 3 * GAMES


def test_a_tie_after_regulation_always_went_to_overtime(games):
    for _, engine, _ in games:
        if engine.s.overtime:
            assert any(step[0] == 5 for step in engine.steps)


def pause_table_sites():
    path = GAME_ROOT / "work" / "pause_table_s43.txt"
    if not path.exists():
        pytest.skip("work/pause_table_s43.txt is not in this copy")
    sites = set()
    for line in path.read_text(encoding="utf-8").split("\n"):
        match = re.match(r"^(pag|kicksnap|inrep)\s+([0-9a-f]+) ", line)
        if match:
            sites.add(int(match.group(2), 16))
    return sites


def test_every_pause_of_a_game_is_a_site_of_the_pause_table_and_every_site_is_reached(games):
    table = pause_table_sites()
    assert len(table) == 51                                         # pag 45, kicksnap 5, inrep 1
    used = set()
    for rig, _, _ in games:
        sites = {site for site, _ in rig.game.pause_log}
        assert None not in sites and sites <= table, sites - table
        used |= sites
    # the 30 games reach all 51 (the concede bleeps' pause through the policy's Escape; 0x43b9d9 is every start's dy)
    assert used == table, sorted(hex(s) for s in table - used)


def test_the_hooks_are_called_in_classic_and_change_nothing(tmp_path):
    class SpyRules(ClassicRules):
        def __init__(self):
            self.calls = {}

        def _count(self, name):
            self.calls[name] = self.calls.get(name, 0) + 1

        def before_snap(self, *a):
            self._count("before_snap")
            return super().before_snap(*a)

        def after_outcome(self, state, outcome):
            self._count("after_outcome")
            return super().after_outcome(state, outcome)

        def offense_menu(self, *a):
            self._count("offense_menu")
            return super().offense_menu(*a)

        def defense_menu(self, *a):
            self._count("defense_menu")
            return super().defense_menu(*a)

        def before_kickoff(self, *a):
            self._count("before_kickoff")
            return super().before_kickoff(*a)

        def between_plays(self, *a):
            self._count("between_plays")
            return super().between_plays(*a)

        def extra_stats_lines(self, *a):
            self._count("extra_stats_lines")
            return super().extra_stats_lines(*a)

        def extra_situation(self, *a):
            self._count("extra_situation")
            return super().extra_situation(*a)

    rig_a, engine_a, result_a = spy_game(tmp_path / "a", 7)
    spy = SpyRules()
    rig_b, engine_b, result_b = spy_game(tmp_path / "b", 7, rules=spy)
    assert result_a == result_b and rig_a.said == rig_b.said
    assert [(e.slot, e.action, e.sound_id, e.volume) for e in rig_a.slot_log] == \
           [(e.slot, e.action, e.sound_id, e.volume) for e in rig_b.slot_log]
    assert rig_a.game.pause_log == rig_b.game.pause_log
    assert set(spy.calls) == {"before_snap", "after_outcome", "offense_menu", "defense_menu", "before_kickoff",
                              "between_plays", "extra_stats_lines", "extra_situation"}
    assert spy.calls["after_outcome"] == len(engine_b.outcomes) >= spy.calls["before_snap"]


def test_the_pass_outcome_odds_long_pass_against_long_pass(tmp_path):
    """Sack 25 %, then an interception 1 in (30 - 3) with the count reset, else complete 30 %; a fumble 1 in 50 after a
    sack or a catch. 3,000 plays on a seeded source; chi-square with 4 degrees of freedom below 18.47 (p = 0.001)."""
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)
    rig.keys.fast = True
    rig.sounds.sleep = lambda seconds: rig.clock.sleep(0.02)
    rig.rnd.source = random.Random(12)
    engine = rig.engine
    counts = {"sack": 0, "interception": 0, "incomplete": 0, "complete": 0, "fumble": 0}
    n = 3000
    for _ in range(n):
        s = engine.s
        s.wisoff, s.defense, s.half, s.yard_line, s.down, s.to_go = 1, 2, 2, 30, 1, 10
        s.offense_play, s.defense_play = 5, 6
        s.stats[1].interception_count = 0
        before = (s.stats[1].sacked, s.stats[1].intercepted, s.stats[1].completions, s.stats[1].fumbles_lost)
        step = engine.snap
        while step.__name__ not in ("next_play", "play_menu", "touchdown"):
            step = step()
        after = (s.stats[1].sacked, s.stats[1].intercepted, s.stats[1].completions, s.stats[1].fumbles_lost)
        if after[3] > before[3]:
            counts["fumble"] += 1
        elif after[0] > before[0]:
            counts["sack"] += 1
        elif after[1] > before[1]:
            counts["interception"] += 1
        elif after[2] > before[2]:
            counts["complete"] += 1
        else:
            counts["incomplete"] += 1
    not_sack = 0.75
    p_int = not_sack / 27
    p_complete_raw = not_sack * 26 / 27 * 0.30
    expected = {"sack": 0.25 * 49 / 50, "interception": p_int, "incomplete": not_sack * 26 / 27 * 0.70,
                "complete": p_complete_raw * 49 / 50, "fumble": (0.25 + p_complete_raw) / 50}
    assert abs(sum(expected.values()) - 1) < 1e-9
    chi2 = sum((counts[k] - n * p) ** 2 / (n * p) for k, p in expected.items())
    assert chi2 < 18.47, (counts, chi2)


def test_field_goals_of_a_whole_season_of_games_were_kicked(games):
    kinds = [o.kind for _, engine, _ in games for o in engine.outcomes]
    assert kinds.count(FIELD_GOAL_GOOD) > 0
