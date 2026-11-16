"""GitHub issue 11, the tester's answer on overtime (nfl4 only, rule 0.13; rule 0.41, rule 0.42 (4); Q-098, D-243). This is inspired by Jim Kitchen.

Asked on 2026-11-15 (comment 6903396896) and answered by Dennisl123 the same day, "1 b." (comment 6903652500): in the last two minutes of
overtime too, a T pressed during a play is kept and the time out is called as soon as the play ends, as in the last two minutes of each half
(D-242). Overtime's last two minutes are those of a period with a two-minute warning: the regular season's one period (16-1-3 (e)) and every
second play-off period (16-1-4); the first and third play-off periods end like the first and third quarters, so there a T during a play is still
not kept (D-233). The key changes no draw: only whether a time out is charged after the play.
"""
from pathlib import Path

import pytest
from test_issue11_14_followups import LATE, OUT, T_KEY, scene

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.game.rules import TIMEOUT_GRANTED, TIMEOUT_KEPT
from randsources import ScriptedRandom


def end_of_play(tmp_path, quarter, left, period, postseason=False, seed=7):
    """A running play of the player's offense ends (H10, between_plays) after a T pressed while it was live."""
    rig = scene(tmp_path, quarter=quarter, extras=dict(plays=1, handled=0, last_offense=1, last_kind="run", running=True, pending=0,
                                                       left=left, period=period, postseason=postseason))
    rig.rnd.source = ScriptedRandom([], seed=seed, strict=False)
    engine, rules = rig.engine, rig.rules
    engine.go_live()
    rig.keys.post(T_KEY)
    rig.keys.pump()
    rules.after_play = True
    rules.between_plays(engine.s)
    return rig


@pytest.mark.parametrize("left,period,postseason", [(120, 5, False), (60, 5, False), (1, 5, False), (90, 6, True), (30, 8, True)])
def test_in_the_last_two_minutes_of_overtime_the_time_out_is_called_when_the_play_ends(tmp_path, left, period, postseason):
    rig = end_of_play(tmp_path, 5, left, period, postseason)
    said = [t for t, _, _ in rig.said]
    assert OUT in said and LATE not in said and list(rig.engine.s.extras.used) == [1, 0]


@pytest.mark.parametrize("left,period,postseason", [(121, 5, False), (500, 5, False), (60, 5, True), (90, 7, True), (121, 6, True)])
def test_earlier_in_overtime_and_in_a_first_or_third_play_off_period_it_is_still_not_kept(tmp_path, left, period, postseason):
    rig = end_of_play(tmp_path, 5, left, period, postseason)
    said = [t for t, _, _ in rig.said]
    assert OUT not in said and said.count(LATE) == 1 and list(rig.engine.s.extras.used) == [0, 0]


def test_late_in_half_reads_the_period():
    class S:
        def __init__(self, quarter, left, period, postseason=False):
            self.quarter = quarter
            self.extras = type("X", (), dict(left=left, period=period, postseason=postseason))()
    assert NflRules.late_in_half(S(5, 120, 5)) and not NflRules.late_in_half(S(5, 121, 5))
    assert NflRules.late_in_half(S(5, 10, 6, True)) and not NflRules.late_in_half(S(5, 10, 5, True))
    assert NflRules.late_in_half(S(4, 120, 4)) and not NflRules.late_in_half(S(3, 10, 3)) and not NflRules.late_in_half(S(5, -1, 5))


def test_the_run_out_question_in_overtime_says_the_time_out_comes_when_the_play_ends(tmp_path):
    rig = scene(tmp_path, answers=["t", 13], returner=1, quarter=5, extras=dict(left=90, period=5))
    rig.engine.t_live = True
    rig.rnd.source = ScriptedRandom([], seed=5, strict=False)
    assert rig.engine.run_it_out() == rig.engine.kick_return
    said = [t for t, _, _ in rig.said]
    assert said.count(X.text("NXT-18")) == 1 and X.text("NXT-15") not in said
    assert rig.rules.grant_kept_timeout(rig.engine.s) == TIMEOUT_GRANTED and list(rig.engine.s.extras.used) == [1, 0]


def test_the_overtime_key_logs_why(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig", quarter=5, extras=dict(left=100, period=5))
    assert rig.rules.timeout_key(rig.engine.s, True) == TIMEOUT_KEPT and not rig.rules.timeout_late
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if "timeout_key" in line]
    assert len(lines) == 1 and "last two minutes of overtime" in lines[0], lines
