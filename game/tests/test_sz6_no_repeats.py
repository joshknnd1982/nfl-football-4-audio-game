"""No sentence is said twice in a row by mistake (CLAUDE.md 0.28 (3); SZ.6, D-111). This is inspired by Jim Kitchen.

A player's e-mail (2026-10-22): "Sometimes it says onside kick twice or he is on for the field goal twice." Found by a probe over whole simulated games:
(1) when the computer declares an onside kick the engine said the declaration ("the Jets will try an onside kick") and the line-up ("the Jets line
up for an onside kick") one after the other, and a remark of the pool ON repeated the hands team just said; (2) a time out called by T during a field
goal's set-up withdraws the kick, and the same kick called again said "<kicker> is in for the field goal attempt" and "<holder> will hold" again.
The original's own repeats (the snap count's "hut", colour calls, the replay key, a question asked again after a wrong key) stay. These tests also play
whole seeded games and fail on a sentence of more than three words said twice in a row.
"""
import re

import pytest

from nfl4.extras import nx_texts as X
from nfl4.game import phrases as P
from nfl4.game.pag import PlayWithdrawn
from nflrig import RecordingRules, sim_game
from pagrig import Draws
from test_nx_tkey import drive, press_t_at, scene, script, texts


def repeats(said):
    """Every pair of sentences of more than three words that are the same, back to back (the original's repeats are not among them)."""
    out = []
    for a, b in zip(said, said[1:]):
        a, b = a.strip(), b.strip()
        if a == b and len(a.split()) > 3:
            out.append(a)
    return out


# ----- the onside kick -----

def test_the_declaration_is_the_line_up_and_the_remark_does_not_repeat_the_hands_team():
    assert X.TEXTS["NXO-09"] != X.TEXTS["NXO-02"]
    assert "hands team" not in X.TEXTS["ON03"] and "hands team" in X.TEXTS["NXO-03"]


# ----- the field goal -----

FG = "is in for the field goal attempt"


def test_a_field_goal_called_again_after_a_time_out_is_set_up_once(tmp_path):
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20)
    engine = rig.engine
    script(rig, Draws().rady().below(6, 1))
    press_t_at(rig, "rady", 1)                                     # the first time the set-up is said and T withdraws the kick
    step, names = drive(engine, engine.snap)
    assert names == ["snap", "field_goal", "withdrawn"] and step == engine.play_menu
    assert len([t for t in texts(rig) if FG in t]) == 1

    class Halt(Exception):
        pass

    def halt(*args, **kwargs):
        raise Halt()
    engine.rady = halt                                             # the second time (T is refused within one dead-ball period): stop at the first pause
    with pytest.raises(Halt):
        drive(engine, engine.snap)
    said = texts(rig)
    assert len([t for t in said if FG in t]) == 1 and len([t for t in said if P.WILL_HOLD.strip() in t]) == 1       # not said again
    assert repeats(said) == []


def test_a_different_spot_or_a_kick_that_ran_is_set_up_again(tmp_path):
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20)
    engine = rig.engine
    engine.setup_heard("field goal")
    engine.withdrawn(PlayWithdrawn(engine.play_menu))
    engine.s.down += 1                                              # another down: the set-up is said
    assert engine.setup_told("field goal") is False
    engine.setup_heard("field goal")
    engine.withdrawn(PlayWithdrawn(engine.play_menu))
    assert engine.setup_told("punt") is False and engine.setup_told("field goal") is False       # consumed once, and by kind
    engine.setup_heard("field goal")
    engine.withdrawn(PlayWithdrawn(engine.play_menu))
    assert engine.setup_told("field goal") is True and engine.setup_told("field goal") is False


def test_the_originals_field_goal_is_unchanged_without_a_time_out(tmp_path):
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20)
    assert rig.engine.setup_told("field goal") is False             # nothing was withdrawn: the original's words, every time


# ----- whole games -----

@pytest.mark.parametrize("seed", [3, 7, 12, 19, 25, 31])
def test_no_sentence_is_said_twice_in_a_row_in_whole_games(tmp_path, seed):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, broadcast_on=True)
    rig, engine, rules, result = sim_game(tmp_path, seed, rules=rules)
    said = [t for t, _, _ in rig.said]
    assert len(said) > 200
    allowed = re.compile(r"^(hut|hike|hut!)\b", re.IGNORECASE)
    assert [r for r in repeats(said) if not allowed.match(r)] == []
