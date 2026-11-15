"""GitHub issue 11, the tester's answer to Q-089 (D-233; nfl4 only, rule 0.13; owner rule 0.22 as the tester chose it). This is inspired by Jim
Kitchen.

The question (issue 11, comment 6901661631): should T at a scrimmage play's "Hike!" stop the play before the snap, as at a kick? The answer
(Dennisl123, comment 6901992315): "A with an acception. You wouldn't want a timeout most likely after the play is over." So the ball stays live
from the quarterback's "Hike!" (choice a), and the exception: a T pressed once the ball is live is no longer kept and granted when the play ends.
No time out is charged, the clock after the play is what it would be without the key (the same draws), and the end of the play says so once
(NXT-17). In the run-out question of a kick-off (the ball is live) the key says NXT-15 at once and nothing more after the play. A T in a pause
between periods (the ball is not in play) is still kept for the next menu and granted there. The log line timeout_key says "late".
"""
from pathlib import Path

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.game.rules import TIMEOUT_GRANTED, TIMEOUT_LATE
from nflrig import nfl_engine_rig
from randsources import ScriptedRandom

ENTER, T_KEY = 13, 84
STATE = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)
OUT = " time out called by the Bengals. "
LATE = X.text("NXT-17")


def scene(tmp_path, answers=(), extras=None, **state):
    fields = dict(STATE)
    fields.update(state)
    base = dict(left=500, pending=0, running=False)
    base.update(extras or {})
    return nfl_engine_rig(tmp_path, answers=answers, extras=base, **fields)


def texts(rig):
    return [t for t, _, _ in rig.said]


def called(rig):
    return list(rig.engine.s.extras.used)


def end_of_play(tmp_path, press: bool, seed: int = 7):
    """A running play of the player's offense in the second quarter ends (H10, between_plays): with or without a T pressed while it was live.
    Returns (the rig, the draws of H10, the clock left)."""
    rig = scene(tmp_path / ("t" if press else "none"), quarter=2,
                extras=dict(plays=1, handled=0, last_offense=1, last_kind="run", running=True, pending=0))
    rig.rnd.source = ScriptedRandom([], seed=seed, strict=False)
    rig.rnd.trace = []
    engine, rules = rig.engine, rig.rules
    engine.go_live()
    if press:
        rig.keys.post(T_KEY)
        rig.keys.pump()
    rules.after_play = True
    rules.between_plays(engine.s)
    x = engine.s.extras
    return rig, list(rig.rnd.trace), (x.left, x.pending, x.running)


def test_t_after_the_snap_is_not_granted_and_the_end_of_the_play_says_so_once(tmp_path):
    rig, _trace, _left = end_of_play(tmp_path, press=True)
    said = texts(rig)
    assert said.count(LATE) == 1 and OUT not in said
    assert called(rig) == [0, 0] and rig.engine.s.extras.timeouts == [3, 3]
    assert not rig.rules.timeout_kept and not rig.rules.timeout_late


def test_the_clock_after_the_play_is_the_same_as_without_the_key(tmp_path):
    """The late key draws nothing and stops nothing: the runoff and every draw of H10 are those of the same play with no T."""
    _rig, trace_t, left_t = end_of_play(tmp_path, press=True)
    _rig2, trace, left = end_of_play(tmp_path, press=False)
    assert trace_t == trace and left_t == left
    rig, _trace, _left = end_of_play(tmp_path / "again", press=True)
    x = rig.engine.s.extras
    assert x.running or x.pending > 0                                # the clock was not stopped by a time out


def test_the_next_menu_says_nothing_more_and_a_new_t_there_calls_the_time_out(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER])
    rig.rnd.source = ScriptedRandom([], seed=3, strict=False)
    engine = rig.engine
    engine.go_live()
    rig.keys.post(T_KEY)
    rig.keys.pump()
    engine.dead_ball()                                               # the play is over: the late key is told here, once
    engine.offense_menu()                                            # T in the menu: the time out is called now, as anywhere
    said = texts(rig)
    assert said.count(LATE) == 1 and said.index(LATE) < said.index(OUT) and called(rig) == [1, 0]


def test_the_run_out_question_says_it_at_once_and_not_again_after_the_play(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER], returner=1)
    rig.engine.t_live = True
    rig.rnd.source = ScriptedRandom([], strict=True)
    assert rig.engine.run_it_out() == rig.engine.kick_return
    rig.engine.dead_ball()
    said = texts(rig)
    assert said.count(X.text("NXT-15")) == 1 and LATE not in said and OUT not in said and called(rig) == [0, 0]


def test_the_sentences_are_plain_and_short():
    assert X.text("NXT-15").strip() == "the ball is live, so no time out is taken."
    assert X.text("NXT-17").strip() == "your time out came after the snap, so none was taken."


def test_a_t_in_a_pause_between_periods_is_still_kept_and_granted(tmp_path):
    """Not a live play: the ball is not in play, so the request still waits for the next menu (where="a pause between periods")."""
    rig = scene(tmp_path)
    rules, s = rig.rules, rig.engine.s
    rules.timeout_key(s, True, None, None, "a pause between periods")
    assert rules.timeout_kept and not rules.timeout_late
    assert rules.grant_kept_timeout(s) == TIMEOUT_GRANTED and called(rig) == [1, 0] and LATE not in texts(rig)


def test_the_log_line_says_late(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig")
    rules, s = rig.rules, rig.engine.s
    rules.timeout_key(s, True)
    assert rules.grant_kept_timeout(s) == TIMEOUT_LATE
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if "timeout_key" in line]
    assert len(lines) == 2 and all("late" in line for line in lines), lines
    assert "live play" in lines[0] and "after the snap" in lines[1]


def test_the_key_help_says_a_late_t_is_not_kept():
    from nfl4.game import key_list
    row = [r for r in key_list.ROWS if r.id == "timeout"][0]
    assert "is not kept for after the play" in row.what and "granted when the play ends" not in row.what
