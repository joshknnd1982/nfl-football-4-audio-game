"""The independent review of SX.2 (work/review_sx2_findings.md): one test per finding that was fixed (nfl4 only, rule 0.13;
B-X31). This is inspired by Jim Kitchen.

M1  a two-point try after a touchdown that used the last second is played, and the half or game ends after it;
m1  a football.sav cut inside the extras marker still loads the original's values;
m2  no timeout at 0:00 (the period is over);
m3  the clock is "stopped" after a play until between plays says otherwise; F4 at 0:00 says " 0 seconds";
m4  remarks.txt held by another program after Rules went Classic and back keeps the loaded lines, and says so truly;
m5  closing the window at the saved-game question writes football.sav back;
n2  the help and the sentences: time outs only when they are on, the overtime counts, the singular forms.
"""
import random

import pytest

from nfl4.data.customize import Customization
from nfl4.data.files import savedgame
from nfl4.data.files.variant import pack_string
from nfl4.extras import nx_texts as X
from nfl4.extras import timeouts as TO
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nfl4.game.gamestate import SideStats
from nfl4.game.keys import GameQuit
from nfl4.game.outcome import PlayOutcome
from nflrig import nfl_engine_rig
from pagrig import Draws
from randsources import ScriptedRandom
from test_nx_save import a_record, a_save

ENTER, DOWN = 13, 40


# ----- M1 -----

def run_until(engine, step, names):
    seen = []
    while step is not None and step.__name__ not in names:
        seen.append(step.__name__)
        step = step()
    return step, seen


@pytest.mark.parametrize("quarter, ends_with", [(1, "kick_off"), (2, "next_play"), (4, "next_play")])
def test_a_two_point_try_after_a_last_second_touchdown_is_played_then_the_period_ends(tmp_path, quarter, ends_with):
    rig = nfl_engine_rig(tmp_path, answers=[DOWN, ENTER, ENTER, ENTER], quarter=quarter, wisoff=1, defense=2, half=1,
                         yard_line=0, stats={1: SideStats(score=6), 2: SideStats(score=6)},    # SX.13: tied, so the try matters (4-8-2 (c))
                         extras=dict(left=0, period=quarter, unit="H1" if quarter < 3 else "H2",
                                     announced="H1" if quarter < 3 else "H2"))
    rig.rnd.source = random.Random(quarter)
    engine = rig.engine
    step, seen = run_until(engine, engine.extra_point_choice, ("kick_off", "next_play", "period_checks"))
    assert "snap" in seen and "try_result" in seen and "period_checks" not in seen     # the try was snapped and played
    s = engine.s
    assert s.two_point is False and s.score(1) in (6, 8)
    assert step.__name__ == "kick_off"
    following = step()
    if quarter == 1:
        assert following.__name__ != "next_play"                     # quarters 1 and 3: the kick-off comes at 0:00
    else:
        assert following == engine.next_play                         # quarters 2 and 4: no kick-off, the period ends


def test_the_try_is_never_ended_by_the_clock_at_the_snap(tmp_path):
    rig = nfl_engine_rig(tmp_path, two_point=True, extras=dict(left=0))
    assert rig.engine.clock.before_snap() is False


# ----- m1 -----

def test_a_save_cut_inside_the_marker_still_loads_the_original_values():
    marker = pack_string(b"NX-EXTRAS")
    for opening in (2, None):
        plain = savedgame.encode(a_save(opening_receiver=opening))
        for cut in range(1, len(marker)):
            decoded = savedgame.decode(plain + marker[:cut])
            assert decoded.extras is None and decoded.extras_marked and decoded.yard_line == 30, (opening, cut)


# ----- m2 -----

def test_no_timeout_is_called_when_the_period_is_over(tmp_path):
    view = TO.Situation(side=2, quarter=1, left=0, pending=0, running=False, has_ball=True, lead=0, timeouts=3,
                        warning_given=False, own_half=True, yard_line=30, down=1)

    class NoDraw:
        def below(self, n):
            raise AssertionError("no draw at 0:00")

    assert TO.computer_calls(view, NoDraw()) is False
    rig = nfl_engine_rig(tmp_path, quarter=1, wisoff=2, defense=1, half=1, yard_line=30, extras=dict(left=0))
    x = rig.engine.s.extras
    x.plays, x.last_kind, x.last_offense = 1, O.RUN, 2
    rig.rnd.source = ScriptedRandom([], strict=True)
    rig.rules.between_plays(rig.engine.s)
    assert x.timeouts == [3, 3] and rig.said == []


# ----- m3 -----

def test_the_clock_is_stopped_after_a_play_until_between_plays_decides(tmp_path):
    rig = nfl_engine_rig(tmp_path, extras=dict(left=500, pending=0, running=True))
    rig.rnd.source = ScriptedRandom(Draws().below(4, 0).values, strict=True)
    rig.rules.after_outcome(rig.engine.s, PlayOutcome(O.TOUCHDOWN, 1, 1, 1))
    assert rig.rules.extra_situation(rig.engine.s)[0] == " the clock is stopped "


def test_f4_at_zero_says_zero_seconds(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4, extras=dict(left=0, period=4))
    rig.engine.clock.speak()
    assert rig.said[-1][0] == "  0 seconds remaining in the fourth quarter. "


# ----- m4 -----

def test_remarks_held_after_a_classic_round_trip_keep_the_loaded_lines(tmp_path):
    import os
    from filedamage import holding
    from nfl4.game.banter_markup import Speak, Text
    folder = str(tmp_path / "customize")
    os.makedirs(folder)
    with open(os.path.join(folder, "remarks.txt"), "w", encoding="utf-8") as handle:
        handle.write("# NFL Football 4 remarks, format 1.\nTO01 = mine\n")
    custom = Customization(folder, extras=True)
    custom.take_notices()
    custom.use_extras(False)
    assert custom.snapshot.remarks.lines("TO")[0].pieces == (Speak((Text("mine"),)),)      # BC.3: Classic keeps remarks.txt in use
    with holding(os.path.join(folder, "remarks.txt")):
        custom.use_extras(True)                                         # and the switch back does not read it again
        notices = custom.take_notices()
        held = custom.reload()
    assert custom.snapshot.remarks.lines("TO")[0].pieces == (Speak((Text("mine"),)),)
    assert notices == [] and " The file remarks.txt is in use by another program. The remarks you already had stay in use. " in held


def test_remarks_held_the_first_time_say_the_originals_are_used(tmp_path):
    import os
    from filedamage import holding
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)                                 # the file exists
    with holding(os.path.join(folder, "remarks.txt")):
        custom = Customization(folder)                                  # BC.3: Classic reads remarks.txt too
    assert custom.take_notices() == [" The file remarks.txt is in use by another program. The original remarks are used "
                                     "this time. "]


# ----- m5 -----

def test_closing_the_window_at_the_saved_game_question_writes_the_save_back(tmp_path, monkeypatch):
    from nfl4.extras import saved as saved_module
    from programrig import preset_season, program_rig
    rig = program_rig(tmp_path, [], preset=preset_season())
    record = a_save(extras=a_record().to_json(), extras_marked=True)
    rig.store.saved = record

    def closed(game, question):
        raise GameQuit()
    monkeypatch.setattr(saved_module, "ask_yes_no", closed)
    with pytest.raises(GameQuit):
        rig.run()
    assert rig.store.saved is record


# ----- n2 -----

def test_the_help_speaks_of_time_outs_only_when_they_are_on_and_says_the_overtime_counts(tmp_path):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False))
    for key in ("116", "117", "118"):
        assert not any("time out" in line.lower() for line in rig.rules.extra_help(key))
    assert "two in an over time period" in X.text("NXH-05") and "more in over time" not in X.text("NXH-05")
    rig = nfl_engine_rig(tmp_path / "on")
    from nflrig import feature_help
    assert feature_help(rig.rules, "116") == [X.text("NXH-02"), X.text("NXH-01")]


def test_one_time_out_and_one_second_are_said_in_the_singular(tmp_path):
    rig = nfl_engine_rig(tmp_path, extras=dict(timeouts=[1, 2]))
    assert rig.rules.extra_situation(rig.engine.s)[1] == " you have 1 time out left, and the Jets have 2. "
    rig = nfl_engine_rig(tmp_path / "b", answers=["t", ENTER], wisoff=1, defense=2, half=2, yard_line=30,
                         extras=dict(left=500, timeouts=[2, 3]))
    rig.rnd.source = ScriptedRandom([], strict=True)
    rig.engine.offense_menu()
    assert " you have 1 time out left. " in [t for t, _, _ in rig.said]
    rig = nfl_engine_rig(tmp_path / "c", quarter=1, wisoff=1, defense=2, half=2, yard_line=30, extras=dict(left=1))
    x = rig.engine.s.extras
    x.plays, x.last_kind, x.last_offense = 1, O.RUN, 1
    rig.rnd.source = ScriptedRandom(Draws().below(11, 0).below(140, 3).values, strict=True)
    rig.rules.between_plays(rig.engine.s)
    assert rig.said[-1][0] == " the clock is running with 1 second left. "


def test_a_play_off_overtime_pair_says_its_time_outs_are_for_two_periods(tmp_path):
    rig = nfl_engine_rig(tmp_path, gtp=18, quarter=5, extras=dict(unit="OTP1", announced="H2", timeouts=[3, 3]))
    rig.rules.before_kickoff(rig.engine.s, 2)
    assert rig.said[-1][0] == " each team has 3 time outs for these two periods. "
