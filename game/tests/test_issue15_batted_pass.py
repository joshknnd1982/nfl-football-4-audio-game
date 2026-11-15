"""GitHub issue 15 (a tester, 2026-11-15, on 1.0.1: "still putting defense players in for computer teams. It is still putting defensive players in
on offense for computer teams."), fixed in S-D (D-231). This is inspired by Jim Kitchen.

His log (a franchise game, Vikings at Bears) had one wrong man: while the Bears had the ball, " Tyrique Stevenson Senior bats it right back at Caleb
Williams! ", and Stevenson is a Bears cornerback. It is the original's quirk Q56: of its nine incomplete passes, " <defender> bats it right back at
<quarterback> " names defensive player L578 of the side ON OFFENSE (Me.m370(wisoff, L578), pag 0x44cc09), the passer's own team's defender, for
either team. Classic keeps it (the exact original, its golden transcript); the N. F. L. rules name the defense's man. Only the side changes: the
same draw, the same pause, the same result."""
import random
import re

import pytest

from nfl4.extras.nfl_rules import NflRules
from pagrig import Draws, engine_rig, make_rig
from randsources import ScriptedRandom

BATS = re.compile(r"^\s*(?P<who>.+?) bats it right back at (?P<qb>\S+)\s*$")


def incomplete(tmp_path, rules, wisoff, number=6, defender1=3):
    """The engine's incomplete pass `number` (6: bats it back, 5: batted down) with side `wisoff` on offense; returns its sentence."""
    rig = engine_rig(tmp_path, offense_play=4, defense_play=5)
    engine = rig.engine
    if rules is not None:
        engine.rules = rules
    s = engine.s
    s.wisoff, s.defense = wisoff, 3 - wisoff
    s.carrier, s.defender1 = 1, defender1
    d = Draws().rnd(9, number).below(4, 2)                   # the incompletion; the pause (2 + 4) / 9
    rig.rnd.source = ScriptedRandom(d.values, strict=True)
    rig.rnd.trace = []
    engine.incomplete()
    assert rig.rnd.trace == d.sizes                          # the same draws in both modes
    return s.tackle_sentence


@pytest.mark.parametrize("wisoff, defender, qb", [(1, "ODef3", "Starr"), (2, "Def3", "Unitas")])
def test_the_nfl_rules_name_the_defenses_man_for_either_team(tmp_path, wisoff, defender, qb):
    assert incomplete(tmp_path, NflRules(), wisoff) == " %s bats it right back at %s " % (defender, qb)


@pytest.mark.parametrize("wisoff, defender, qb", [(1, "Def3", "Starr"), (2, "ODef3", "Unitas")])
def test_classic_keeps_the_originals_q56(tmp_path, wisoff, defender, qb):
    assert incomplete(tmp_path, None, wisoff) == " %s bats it right back at %s " % (defender, qb)


@pytest.mark.parametrize("rules", [None, NflRules()])
def test_batted_down_was_always_the_defenses_man(tmp_path, rules):
    assert incomplete(tmp_path, rules, 2, number=5, defender1=7) == " it is batted down by Def7 "


def whole_game(tmp_path, seed):
    """A game of the N. F. L. rules, both teams by the computer, plain calls (the engine's own words); returns the engine and what was said."""
    from nflrig import QUARTERBACKS, RecordingRules, SimEngine
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
    rig.game.options.settings.game.nx_play_calls = "plain"
    rig.game.comtog_source = lambda: 1
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    try:
        engine.run()
    finally:
        rig.game.play_engine = None
    return engine, [t for t, _r, _s in rig.said]


def test_whole_games_never_name_the_offenses_own_defender_at_a_batted_pass(tmp_path):
    seen = 0
    for seed in range(1500, 1512):
        engine, said = whole_game(tmp_path / str(seed), seed)
        s = engine.s
        side_of_qb = {qb: side for side, qb in s.quarterbacks.items()}
        for text in said:
            m = BATS.match(text)
            if not m or m.group("qb") not in side_of_qb:
                continue
            offense = side_of_qb[m.group("qb")]
            assert m.group("who") in s.rosters[3 - offense].defense, text
            assert m.group("who") not in s.rosters[offense].defense, text
            seen += 1
    assert seen >= 2                                          # the sentence came, for real, in these games
