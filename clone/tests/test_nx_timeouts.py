"""Timeouts of the N. F. L. rules mode: the counts, the units, the refusals and the computer's six rules, alone and in the
engine on a strict scripted source (nfl4 only, rule 0.13; NFL_EXTRA_FEATURES NX1, NFL_EXTRAS_DESIGN 6.3, PX SX.2). This is
inspired by Jim Kitchen.

The scripted end-of-half tests are NX1's done-when: a trailing computer team with timeouts uses them the NFL way (to stop a
running clock late in the fourth quarter, on offense and on defense), a leading one never does, the first half's last two
minutes save time in a drive, and quarters 1 and 3 have the rare "operational" timeout.
"""
import pytest

from nfl4.extras import timeouts as TO
from nfl4.extras import tuning as T
from nfl4.extras.state import ExtrasRecord
from nfl4.game import outcome as O
from nflrig import nfl_engine_rig
from pagrig import Draws
from randsources import ScriptedRandom


def view(**fields):
    values = dict(side=2, quarter=4, left=200, pending=30, running=True, has_ball=True, lead=-3, timeouts=3,
                  warning_given=True, own_half=True, yard_line=30, down=1)
    values.update(fields)
    return TO.Situation(**values)


class NoDraw:
    def below(self, n):
        raise AssertionError("no draw was planned")


# ----- the counts and the units (design 4, rules 4-5-1, 16-3-e, 16-4-g) -----

@pytest.mark.parametrize("period, postseason, unit, count", [
    (1, False, "H1", 3), (2, True, "H1", 3), (3, False, "H2", 3), (4, True, "H2", 3), (5, False, "OT1", 2),
    (6, False, "OT2", 2), (5, True, "OTP1", 3), (6, True, "OTP1", 3), (7, True, "OTP2", 3), (8, True, "OTP2", 3)])
def test_the_unit_that_shares_timeouts_and_its_count(period, postseason, unit, count):
    assert TO.unit_for(period, postseason) == unit
    assert TO.count_for(unit) == count


def test_a_new_half_renews_the_timeouts_a_new_quarter_of_the_same_half_does_not():
    record = ExtrasRecord()
    record.timeouts = [0, 1]
    assert TO.enter_unit(record, 2) is False and record.timeouts == [0, 1]
    assert TO.enter_unit(record, 3) is True and record.timeouts == [3, 3] and record.unit == "H2"
    record.called = [True, False]
    assert TO.enter_unit(record, 5) is True and record.timeouts == [2, 2] and record.called == [False, False]


def test_a_request_is_refused_with_none_left_or_a_second_in_one_dead_ball_period():
    record = ExtrasRecord()
    assert TO.refusal(record, 1) is None
    TO.charge(record, 1)
    assert record.timeouts == [2, 3] and record.used == [1, 0] and record.called == [True, False]
    assert TO.refusal(record, 1) == "called"
    record.called = [False, False]
    record.timeouts = [0, 3]
    assert TO.refusal(record, 1) == "none"
    assert TO.refusal(record, 2) is None


# ----- the computer's rules, alone -----

def test_rule_1_none_left_means_no_timeout():
    assert TO.computer_calls(view(timeouts=0), NoDraw()) is False


def test_rule_1_keeps_a_timeout_for_a_challenge_only_when_a_challenge_is_possible_which_is_never_before_sx6():
    assert TO.challenge_possible(view()) is False
    assert TO.computer_calls(view(quarter=4, timeouts=1, lead=-3, has_ball=True, left=100), NoDraw()) is True


@pytest.mark.parametrize("fields, calls", [
    (dict(quarter=2, warning_given=True, has_ball=True, pending=13, own_half=True, yard_line=30), True),
    (dict(quarter=2, warning_given=True, has_ball=True, pending=12, own_half=True, yard_line=30), False),
    (dict(quarter=2, warning_given=True, has_ball=True, pending=20, own_half=True, yard_line=29), False),
    (dict(quarter=2, warning_given=True, has_ball=True, pending=20, own_half=False, yard_line=10), True),
    (dict(quarter=2, warning_given=False, has_ball=True, pending=20, own_half=False, yard_line=10), False),
    (dict(quarter=2, warning_given=True, has_ball=True, pending=20, running=False, own_half=False), False),
    (dict(quarter=2, warning_given=True, has_ball=False, own_half=True, yard_line=34, down=3), True),
    (dict(quarter=2, warning_given=True, has_ball=False, own_half=True, yard_line=35, down=4), False),
    (dict(quarter=2, warning_given=True, has_ball=False, own_half=True, yard_line=20, down=2), False),
    (dict(quarter=2, warning_given=True, has_ball=False, own_half=False, yard_line=20, down=3), False)])
def test_rule_2_the_end_of_the_first_half(fields, calls):
    assert TO.computer_calls(view(**fields), NoDraw()) is calls


@pytest.mark.parametrize("fields, calls", [
    (dict(has_ball=True, lead=-1, left=299), True), (dict(has_ball=True, lead=-1, left=300), False),
    (dict(has_ball=True, lead=0, left=119), True), (dict(has_ball=True, lead=0, left=200), False),
    (dict(has_ball=True, lead=-8, left=100, running=False), False),
    (dict(has_ball=False, lead=-4, left=479, timeouts=3), True), (dict(has_ball=False, lead=-4, left=480, timeouts=3), False),
    (dict(has_ball=False, lead=-4, left=359, timeouts=1), True), (dict(has_ball=False, lead=-4, left=360, timeouts=1), False),
    (dict(has_ball=False, lead=0, left=100), False)])
def test_rule_3_the_fourth_quarter_trailing_or_tied(fields, calls):
    assert TO.computer_calls(view(quarter=4, **fields), NoDraw()) is calls


def test_rule_4_overtime_saves_time_in_its_last_two_minutes():
    assert TO.computer_calls(view(quarter=5, left=110, has_ball=True, pending=15, own_half=False), NoDraw()) is True
    assert TO.computer_calls(view(quarter=5, left=130, has_ball=True, pending=15, own_half=False), NoDraw()) is False


def test_rule_5_a_leading_team_never_calls_one_in_the_fourth_quarter():
    for has_ball in (True, False):
        assert TO.computer_calls(view(quarter=4, lead=1, left=20, has_ball=has_ball), NoDraw()) is False


def test_rule_6_the_operational_timeout_of_quarters_1_and_3_draws_once_and_only_with_three_left():
    class Draw:
        def __init__(self, value):
            self.value, self.sizes = value, []

        def below(self, n):
            self.sizes.append(n)
            return self.value

    for quarter in (1, 3):
        hit, miss = Draw(0), Draw(1)
        assert TO.computer_calls(view(quarter=quarter, timeouts=3), hit) is True
        assert TO.computer_calls(view(quarter=quarter, timeouts=3), miss) is False
        assert hit.sizes == [T.RULE6_CHANCE] and miss.sizes == [T.RULE6_CHANCE]
    assert TO.computer_calls(view(quarter=1, timeouts=2), NoDraw()) is False
    assert TO.computer_calls(view(quarter=2, timeouts=3, warning_given=False), NoDraw()) is False


# ----- in the engine, between plays (H10), on a strict source -----

def between(rig, draws: Draws):
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []
    start = len(rig.said)
    rig.rules.between_plays(rig.engine.s)
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert rig.rnd.source.left == 0
    return [text for text, _, _ in rig.said[start:]]


def after_run(rig, offense):
    x = rig.engine.s.extras
    x.plays += 1
    x.last_kind, x.last_offense, x.last_two_point = O.RUN, offense, False


def stats(**score):
    from nfl4.game.gamestate import SideStats
    return {1: SideStats(score=score.get("own", 0)), 2: SideStats(score=score.get("opponent", 0))}


def test_a_trailing_computer_offense_stops_the_clock_in_the_last_five_minutes(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4, wisoff=2, defense=1, half=1, yard_line=35, down=2, to_go=4,
                         stats=stats(own=14, opponent=10), extras=dict(left=180, period=4, unit="H2"))
    after_run(rig, 2)
    said = between(rig, Draws().below(9, 4).below(6, 2))     # hurry-up runoff 16, then u = 5
    x = rig.engine.s.extras
    assert said == [" time out called by the Jets. ", " they have 2 time outs left. "]
    assert x.timeouts == [3, 2] and x.used == [0, 1] and x.left == 175 and x.pending == 0 and not x.running
    assert [e.sound_id for e in rig.slot_log if e.action == "play"][-1] == "snd_foot11"


def test_a_trailing_computer_defense_uses_its_timeouts_to_get_the_ball_back(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4, wisoff=1, defense=2, half=2, yard_line=40, down=1, to_go=10,
                         stats=stats(own=17, opponent=10), extras=dict(left=400, period=4, unit="H2"))
    after_run(rig, 1)
    said = between(rig, Draws().below(3, 1).below(6, 5))     # the leading offense milks the clock (38), u = 8
    x = rig.engine.s.extras
    assert said == [" time out called by the Jets. ", " they have 2 time outs left. "]
    assert x.left == 392 and x.timeouts == [3, 2]


def test_the_computer_spends_its_last_timeout_and_says_none_are_left(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4, wisoff=2, defense=1, half=1, yard_line=35,
                         stats=stats(own=21, opponent=10), extras=dict(left=100, period=4, unit="H2", timeouts=[3, 1]))
    after_run(rig, 2)
    said = between(rig, Draws().below(9, 0).below(6, 0))
    assert said == [" time out called by the Jets. ", " they have no time outs left. "]
    after_run(rig, 2)
    said = between(rig, Draws().below(9, 8))                 # none left: the clock runs, nothing is asked
    assert said == [] and rig.engine.s.extras.running


def test_a_leading_computer_team_lets_the_clock_run(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4, wisoff=2, defense=1, half=1, yard_line=35,
                         stats=stats(own=3, opponent=10), extras=dict(left=200, period=4, unit="H2"))
    after_run(rig, 2)
    said = between(rig, Draws().below(3, 2))                 # milk: 39
    x = rig.engine.s.extras
    assert said == [] and x.running and x.pending == 39 and x.timeouts == [3, 3]


def test_the_first_half_after_the_warning_the_computer_saves_time_in_a_drive(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=2, wisoff=2, defense=1, half=1, yard_line=45, down=1, to_go=10,
                         extras=dict(left=90, period=2, warning_given=True))
    after_run(rig, 2)
    said = between(rig, Draws().below(9, 8).below(6, 0))     # hurry-up 20, more than 12: the timeout, u = 3
    assert said == [" time out called by the Jets. ", " they have 2 time outs left. "]
    assert rig.engine.s.extras.left == 87


def test_the_first_half_before_the_warning_no_timeout_and_a_short_runoff_is_not_worth_one(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=2, wisoff=2, defense=1, half=1, yard_line=45,
                         extras=dict(left=90, period=2, warning_given=True))
    after_run(rig, 2)
    assert between(rig, Draws().below(9, 0)) == []          # 12 seconds: not more than 12
    rig = nfl_engine_rig(tmp_path / "b", quarter=2, wisoff=2, defense=1, half=1, yard_line=45,
                         extras=dict(left=300, period=2))
    after_run(rig, 2)
    assert between(rig, Draws().below(11, 3)) == []         # 5:00 left in quarter 2: the normal tempo, no rule


def test_the_computer_defense_saves_time_when_the_offense_is_deep_on_third_down(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=2, wisoff=1, defense=2, half=2, yard_line=20, down=3, to_go=6,
                         extras=dict(left=100, period=2, warning_given=True))
    after_run(rig, 1)
    said = between(rig, Draws().below(9, 0).below(6, 1))
    assert said == [" time out called by the Jets. ", " they have 2 time outs left. "]


def test_the_operational_timeout_in_quarter_1(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=1, wisoff=2, defense=1, half=1, yard_line=30, extras=dict(left=600))
    after_run(rig, 2)
    said = between(rig, Draws().below(11, 0).below(T.RULE6_CHANCE, 0).below(6, 0))
    assert said == [" time out called by the Jets. ", " they have 2 time outs left. "]
    after_run(rig, 2)
    said = between(rig, Draws().below(11, 0))               # two left now: rule 6 needs three, no draw
    assert said == []


def test_the_players_side_is_never_decided_by_the_computer(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4, wisoff=1, defense=2, half=1, yard_line=30,
                         stats=stats(own=0, opponent=7), extras=dict(left=100, period=4, unit="H2"))
    after_run(rig, 1)
    said = between(rig, Draws().below(9, 3))                # the player trails: hurry-up 15, but no timeout for that side
    assert rig.engine.s.extras.timeouts == [3, 3] and rig.engine.s.extras.pending == 15
    assert said == []


def test_the_clock_running_warning_before_the_menu_when_the_runoff_would_end_the_period(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=1, wisoff=1, defense=2, half=2, yard_line=30, extras=dict(left=25))
    after_run(rig, 1)
    said = between(rig, Draws().below(11, 0).below(T.RULE6_CHANCE, 7))   # 30 seconds pending, 25 left; the Jets' rule 6
    assert said == [" the clock is running with 25 seconds left. "]


def test_between_plays_draws_once_per_play_even_when_the_statistics_say_the_down_again(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=3, wisoff=2, defense=1, half=1, yard_line=30, extras=dict(left=500))
    after_run(rig, 2)
    between(rig, Draws().below(11, 0).below(T.RULE6_CHANCE, 5))
    assert between(rig, Draws()) == []                      # the second call for the same play draws nothing


def test_timeouts_off_means_no_computer_timeout_and_no_draw_for_one(tmp_path):
    from nfl4.extras.nfl_rules import NflRules
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False), quarter=4, wisoff=2, defense=1, half=1,
                         yard_line=35, stats=stats(own=14, opponent=10), extras=dict(left=180, period=4, unit="H2"))
    after_run(rig, 2)
    assert between(rig, Draws().below(9, 4)) == []
    assert rig.engine.s.extras.timeouts == [3, 3]
