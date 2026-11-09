"""GitHub issue 11 (D-224): a timeout called while the holder says " hike! " before a field goal is granted before the snap (nfl4 only,
rule 0.13; owner rule 0.22, playbook 7.16). This is inspired by Jim Kitchen.

The tester (0.16.21, JAWS) pressed T 0.17 s after the holder's " hike! " began, to ice the kicker. The kick had been made live before the
word was said, so the key was only kept: the 56-yard field goal was good and the timeout was charged after it, before the kick-off. Now the
word is still the snap count: a T while it is said cuts it, the timeout is called and the kick is withdrawn; the kick is live once the word
has been said. The same snap count (pag_kicks.kicksnap) is used by the punt and the kicked try, so they are tested too. A scrimmage play
keeps its live moment at " Hike! " (the hike sound and the play noise start with it), as before.
"""
from pathlib import Path

import pytest

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import phrases as P
from nfl4.game.pag import PlayWithdrawn
from pagrig import Draws
from randsources import ScriptedRandom
from test_nx_tkey import ENTER, OUT, T_KEY, called, check, drive, scene, script, stop_at, texts, Stop


def kick_count() -> Draws:
    """kicksnap with the fewest draws: " hut 1 ", its pause, no " hut 2 ", one " hut" (no "!"), its pause, the pause before " hike! "."""
    return Draws().rady().rnd(3, 2).rnd(3, 1).rnd(3, 1).rady().rady()


def press_t_while_saying(rig, text: str):
    """The player presses T while `text` is being said: the window thread posts the key during the speech wait, so the wait ends and the
    game thread takes the key at once (Speakers._speak services it before anything else is said)."""
    speech = rig.game.speech
    original = speech.say
    pressed = {"n": 0}

    def say(said, *args, **kwargs):
        result = original(said, *args, **kwargs)
        if said == text and pressed["n"] == 0:
            pressed["n"] += 1
            rig.keys.post(T_KEY)
            rig.keys.post_char("t")
        return result
    speech.say = say
    return pressed


def stop_index_after(rig, text: str) -> bool:
    """A stop of the speech came after `text` was sent (the word was cut by the key)."""
    events = rig.sapi.events
    spoken = [i for i, (kind, value) in enumerate(events) if kind == "speak" and value == text]
    return bool(spoken) and any(kind == "stop" for kind, _ in events[spoken[-1] + 1:])


def test_t_while_the_holder_says_hike_ices_the_kicker_the_field_goal_is_withdrawn(tmp_path):
    """The tester's moment: the timeout is called before the snap, the kick is not made, the menu comes again from its top."""
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20)
    draws = Draws().rady().extend(kick_count()).below(6, 1)          # the set-up's pause, the snap count, then u (the clock's runoff)
    script(rig, draws)
    pressed = press_t_while_saying(rig, P.KICK_HIKE)
    engine = rig.engine
    step, names = drive(engine, engine.snap)
    check(rig, draws)
    assert pressed["n"] == 1
    assert names == ["snap", "field_goal", "withdrawn"] and step == engine.play_menu
    said = texts(rig)
    assert P.KICK_HIKE in said and OUT in said and said.index(P.KICK_HIKE) < said.index(OUT)
    assert P.SNAP_IS_GOOD not in said and P.HOLD_IS_GOOD not in said and P.KICK_IS_UP not in said
    assert stop_index_after(rig, P.KICK_HIKE)                         # the word was cut at once
    x = engine.s.extras
    assert (x.timeouts, x.used, x.called) == ([2, 3], [1, 0], [True, False])
    assert (x.left, x.pending, x.running) == (496, 0, False)          # the runoff the snap took is given back, as in the snap count
    assert not engine.t_live and not rig.rules.timeout_kept
    assert (rig.game.qorp, rig.game.ptf) == (1, 0)                    # the punter's voice and the speech log's flag do not stay on
    assert not rig.sounds.play_noise_running()


def test_t_while_the_holder_says_hike_on_a_2026_field_goal_is_withdrawn_too(tmp_path):
    """The tester played the N. F. L. rules with the team's playbook: the kicks of 2026 (pag_kicks26.field_goal_2026)."""
    rules = NflRules(timeouts_on=True, offense_book="team", defense_book="team", playbooks_on=True)   # the tester's settings
    rig = scene(tmp_path, rules=rules, offense_play=6, defense_play=1, yard_line=20)
    rig.rnd.source = ScriptedRandom([], seed=11)                      # the 2026 kick's own draws are not planned here
    taken = []
    original = rig.engine.field_goal_2026
    rig.engine.field_goal_2026 = lambda plan: taken.append(plan) or original(plan)
    press_t_while_saying(rig, P.KICK_HIKE)
    engine = rig.engine
    step, names = drive(engine, engine.snap)
    assert taken and taken[0].what == "field goal"
    assert names == ["snap", "field_goal", "withdrawn"] and step == engine.play_menu
    said = texts(rig)
    assert OUT in said and P.SNAP_IS_GOOD not in said
    assert called(rig) == [1, 0] and not engine.t_live and not rules.timeout_kept


def test_t_while_the_punter_says_hike_withdraws_the_punt(tmp_path):
    rig = scene(tmp_path, offense_play=7, defense_play=1, yard_line=30)
    rig.rnd.source = ScriptedRandom([], seed=3)                       # the snap's draws (carrier, tacklers) are not planned here
    press_t_while_saying(rig, P.KICK_HIKE)
    engine = rig.engine
    step, names = drive(engine, engine.snap)
    assert names == ["snap", "punt", "withdrawn"] and step == engine.play_menu
    said = texts(rig)
    assert OUT in said and not any(P.LONG_SNAP in line for line in said)
    assert called(rig) == [1, 0] and not engine.t_live


def test_t_while_the_holder_says_hike_on_the_extra_point_goes_back_to_the_choice(tmp_path):
    rig = scene(tmp_path, answers=[ENTER], extras=dict(pending=0, running=False))
    engine = rig.engine
    script(rig, Draws())
    assert engine.extra_point_choice() == engine.extra_point
    draws = Draws().rady().extend(kick_count())
    script(rig, draws)
    press_t_while_saying(rig, P.KICK_HIKE)
    with pytest.raises(PlayWithdrawn) as caught:
        engine.extra_point()
    check(rig, draws)
    assert caught.value.back == engine.extra_point_choice and called(rig) == [1, 0]
    assert P.SNAP_IS_GOOD not in texts(rig)


@pytest.mark.parametrize("extras,sentence", [(dict(timeouts=[0, 3]), "NXT-04"), (dict(called=[True, False]), "NXT-05")])
def test_a_refused_t_while_hike_is_said_says_one_sentence_and_the_kick_goes_on(tmp_path, extras, sentence):
    """No timeout left, or one already called in this dead-ball period (the word belongs to it): one sentence, then the kick is live."""
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20, extras=dict(pending=0, running=False, **extras))
    draws = kick_count()
    script(rig, draws)
    press_t_while_saying(rig, P.KICK_HIKE)
    engine = rig.engine
    engine.t_back = engine.play_menu
    engine.kicksnap()
    check(rig, draws)
    said = texts(rig)
    assert X.text(sentence) in said and said.index(P.KICK_HIKE) < said.index(X.text(sentence)) and OUT not in said
    assert called(rig) == [0, 0] and engine.t_live and rig.game.qorp == 1


def test_t_once_hike_has_been_said_is_kept_the_kick_is_live(tmp_path):
    """The boundary: T during " the snap is good " (after the word) waits for the end of the play, as before."""
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20, extras=dict(pending=0, running=False))
    draws = Draws().rady().extend(kick_count()).rady()
    script(rig, draws)
    press_t_while_saying(rig, P.SNAP_IS_GOOD)
    stop_at(rig, "rady", 6)                                           # the pause after " the snap is good ": the key has been taken
    engine = rig.engine
    with pytest.raises(Stop):
        drive(engine, engine.snap)
    assert rig.rules.timeout_kept and called(rig) == [0, 0] and engine.t_live


def test_without_t_the_word_is_said_in_full_and_then_the_kick_is_live(tmp_path):
    """The dead-ball period ends after the word (rules.ball_live), and nothing is drawn differently: the snap count's draws are the same."""
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20, extras=dict(pending=0, running=False))
    draws = kick_count()
    script(rig, draws)
    order = []
    original = rig.rules.ball_live
    rig.rules.ball_live = lambda state: order.append(P.KICK_HIKE in texts(rig)) or original(state)
    rig.engine.t_back = rig.engine.play_menu
    rig.engine.kicksnap()
    check(rig, draws)
    assert order == [True] and rig.engine.t_live and rig.engine.t_back is None
    assert not stop_index_after(rig, P.KICK_HIKE)


def test_the_log_names_the_moment_the_ball_became_live(tmp_path):
    """The line that would have shown the bug: the kick's snap is logged after the holder's word, and the T key's line follows it."""
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig", offense_play=6, defense_play=1, yard_line=20, extras=dict(pending=0, running=False))
    draws = kick_count()
    script(rig, draws)
    rig.engine.kicksnap()
    debuglog.flush(30)
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    live = [i for i, line in enumerate(lines) if "ball_live" in line]
    hike = [i for i, line in enumerate(lines) if "hike!" in line]
    assert len(live) == 1 and "the kick's snap" in lines[live[0]] and hike and hike[-1] < live[0]


def test_with_timeouts_off_the_snap_count_is_unchanged_and_t_is_not_armed(tmp_path):
    """Timeouts switched off: T is not armed and the snap count ends with the word, as before."""
    rules = NflRules(timeouts_on=False)
    rig = scene(tmp_path, rules=rules, offense_play=6, defense_play=1, yard_line=20, extras=dict(pending=0, running=False,
                                                                                                timeouts_on=False))
    draws = kick_count()
    script(rig, draws)
    rig.engine.kicksnap()
    check(rig, draws)
    assert texts(rig)[-1] == P.KICK_HIKE and not rig.engine.t_armed
