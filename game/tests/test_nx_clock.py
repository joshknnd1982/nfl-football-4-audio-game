"""The real clock of the N. F. L. rules mode: the rules table, the live times, the runoff, the warning, the snap (nfl4 only,
rule 0.13; NFL_EXTRAS_DESIGN 4 and 5, PX SX.2). This is inspired by Jim Kitchen.

Rule tests against extras/rules_2026.py and extras/tuning.py, and the clock object on a strict scripted source (every draw
planned by hand: an unplanned, unused or wrongly sized draw fails).
"""
import pytest

from nfl4.extras import clock as C
from nfl4.extras import rules_2026 as R
from nfl4.extras import tuning as T
from nfl4.extras.state import ExtrasRecord
from nfl4.game import outcome as O
from nfl4.game.gamestate import GameState
from nfl4.game.outcome import PlayOutcome
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, below_value


class SayClock:
    def __init__(self):
        self.said = []

    def say_clock(self, text):
        self.said.append(text)


def strict(*pairs):
    """A GameRandom whose draws are Int(Rnd * n) = k for each (n, k), in order, and nothing else."""
    rnd = GameRandom(ScriptedRandom([below_value(n, k) for n, k in pairs], strict=True))
    rnd.trace = []
    return rnd


def done(rnd, *sizes):
    assert rnd.trace == list(sizes)
    assert rnd.source.left == 0


def make_clock(quarter=1, left=900, **extras):
    state = GameState()
    state.quarter = quarter
    state.extras = ExtrasRecord(left=left, period=min(quarter, 5), **extras)
    return C.NflPeriodClock(SayClock(), state), state


def record(kind, **fields):
    values = dict(offense=1, offense_play=1, defense_play=1)
    values.update(fields)
    return PlayOutcome(kind, **values)


# ----- the rules table (design 4) -----

def test_the_rules_table_holds_the_2026_rulebook_numbers():
    assert R.YEAR == 2026
    assert R.QUARTER_SECONDS == 900 and R.WARNING_SECONDS == 120 and R.WARNING_QUARTERS == (2, 4)
    assert R.OT_REGULAR_PERIOD_SECONDS == 600 and R.OT_POST_PERIOD_SECONDS == 900
    assert R.TIMEOUTS_PER_HALF == 3 and R.OT_REGULAR_TIMEOUTS == 2 and R.OT_POST_TIMEOUTS == 3
    assert R.FIELD_GOAL_MAX_CLOCK == 5 and R.TRY_UNTIMED
    assert R.LATE_FIRST_HALF_SECONDS == 120 and R.FIVE_MINUTE_RULE_SECONDS == 300 and R.PLAY_CLOCK == 40


def test_every_runoff_range_fits_the_play_clock_and_every_range_is_ordered():
    for low, high in (T.RUNOFF_NORMAL, T.RUNOFF_HURRY, T.RUNOFF_MILK, T.LIVE_RUN, T.LIVE_PASS_COMPLETE,
                      T.LIVE_PASS_INCOMPLETE, T.LIVE_SACK, T.LIVE_TURNOVER, T.LIVE_PUNT, T.LIVE_FIELD_GOAL,
                      T.READY_SIGNAL_CUT, T.TIMEOUT_SIGNAL, T.KICKOFF_RETURN_EXTRA):
        assert 0 <= low <= high
    for _, high in (T.RUNOFF_NORMAL, T.RUNOFF_HURRY, T.RUNOFF_MILK):
        assert high <= R.PLAY_CLOCK
    assert T.LIVE_FIELD_GOAL[1] <= R.FIELD_GOAL_MAX_CLOCK


@pytest.mark.parametrize("period, postseason, seconds", [(1, False, 900), (4, True, 900), (5, False, 600),
                                                          (6, False, 600), (5, True, 900), (7, True, 900)])
def test_period_lengths(period, postseason, seconds):
    assert C.period_seconds(period, postseason) == seconds


@pytest.mark.parametrize("period, postseason, warned", [(1, False, False), (2, False, True), (3, True, False),
                                                         (4, True, True), (5, False, True), (6, False, True),
                                                         (5, True, False), (6, True, True), (7, True, False),
                                                         (8, True, True)])
def test_warning_periods(period, postseason, warned):
    assert C.is_warning_period(period, postseason) is warned


@pytest.mark.parametrize("quarter, left, late", [(1, 30, False), (2, 121, False), (2, 120, True), (3, 10, False),
                                                  (4, 301, False), (4, 300, True), (5, 599, False), (5, 300, True)])
def test_the_late_windows_where_out_of_bounds_stops_the_clock_until_the_snap(quarter, left, late):
    assert C.late_window(quarter, left) is late


@pytest.mark.parametrize("quarter, left, lead, pace", [
    (1, 100, -20, C.NORMAL), (2, 121, 0, C.NORMAL), (2, 120, 7, C.HURRY), (3, 60, -3, C.NORMAL),
    (4, 300, -1, C.HURRY), (4, 301, -1, C.NORMAL), (4, 120, 0, C.HURRY), (4, 121, 0, C.NORMAL),
    (4, 480, 3, C.MILK), (4, 481, 3, C.NORMAL), (4, 30, 3, C.MILK), (5, 120, 0, C.HURRY), (5, 121, 0, C.NORMAL)])
def test_the_tempo_of_the_offense(quarter, left, lead, pace):
    assert C.tempo(quarter, left, lead) == pace


# ----- the live time L (design 5.1) -----

@pytest.mark.parametrize("kind, span", [(O.RUN, T.LIVE_RUN), (O.PASS_COMPLETE, T.LIVE_PASS_COMPLETE),
                                        (O.PASS_INCOMPLETE, T.LIVE_PASS_INCOMPLETE), (O.SACK, T.LIVE_SACK),
                                        (O.INTERCEPTION, T.LIVE_TURNOVER), (O.FUMBLE, T.LIVE_TURNOVER),
                                        (O.PUNT, T.LIVE_PUNT), (O.FIELD_GOAL_GOOD, T.LIVE_FIELD_GOAL),
                                        (O.FIELD_GOAL_MISSED, T.LIVE_FIELD_GOAL),
                                        (O.FIELD_GOAL_SHORT, T.LIVE_FIELD_GOAL)])
def test_each_kind_of_play_draws_its_live_time_once_from_its_range(kind, span):
    low, high = span
    for k, expected in ((0, low), (high - low, high)):
        rnd = strict((high - low + 1, k))
        assert C.live_time(record(kind), GameState(), rnd) == expected
        done(rnd, high - low + 1)


def test_a_try_and_a_touch_back_take_no_time_and_draw_nothing():
    rnd = strict()
    assert C.live_time(record(O.TWO_POINT_TRY, two_point_try=True), GameState(), rnd) == 0
    assert C.live_time(record(O.INTERCEPTION, two_point_try=True), GameState(), rnd) == 0
    assert C.live_time(record(O.KICKOFF_TOUCH_BACK, offense_play=0), GameState(), rnd) == 0
    done(rnd)


def test_a_kickoff_return_costs_three_seconds_a_second_per_ten_yards_and_zero_to_three_more():
    rnd = strict((4, 2))
    assert C.live_time(record(O.KICKOFF_RETURN, offense_play=0, yards=37), GameState(), rnd) == 3 + 3 + 2
    done(rnd, 4)


def test_a_touchdown_or_a_safety_takes_the_time_of_the_play_that_made_it():
    state = GameState()
    state.result_kind = O.PASS_COMPLETE
    rnd = strict((4, 3))
    assert C.live_time(record(O.TOUCHDOWN, offense_play=4), state, rnd) == T.LIVE_PASS_COMPLETE[0] + 3
    state.result_kind = O.SACK
    rnd = strict((5, 0))
    assert C.live_time(record(O.SAFETY_KIND, offense_play=5), state, rnd) == T.LIVE_SACK[0]
    rnd = strict((4, 0))                                              # a kick-off returned for a touchdown
    assert C.live_time(record(O.TOUCHDOWN, offense_play=0, yards=101), state, rnd) == 3 + 10
    done(rnd, 4)


def test_a_play_is_completed_when_time_runs_out_and_the_clock_stops_at_zero():
    clock, state = make_clock(quarter=1, left=4)
    rnd = strict((4, 3))
    assert clock.play_time(record(O.RUN), rnd) == 7
    assert state.extras.left == 0 and clock.period_over()
    done(rnd, 4)


def test_live_time_across_two_minutes_brings_the_warning_after_the_play():
    clock, state = make_clock(quarter=2, left=124)
    clock.play_time(record(O.RUN), strict((4, 3)))                     # 7 seconds: 117 left
    assert state.extras.left == 117 and clock.warning_due() and clock.warning_zone()
    clock.warning_given()
    assert not clock.warning_due() and state.extras.warning_given
    clock.play_time(record(O.RUN), strict((4, 3)))
    assert not clock.warning_due()                                       # once per period


def test_no_warning_in_the_first_and_third_quarters():
    for quarter in (1, 3):
        clock, state = make_clock(quarter=quarter, left=124)
        clock.play_time(record(O.RUN), strict((4, 3)))
        assert not clock.warning_due()


# ----- the runoff R (design 5.3) -----

def test_a_running_clock_keeps_its_runoff_pending_until_the_snap():
    clock, state = make_clock(quarter=1, left=600)
    rnd = strict((11, 5))
    assert clock.runoff(rnd, keeps_running=True, ready_signal=False, lead=0) == T.RUNOFF_NORMAL[0] + 5
    x = state.extras
    assert x.pending == 35 and x.running and x.left == 600
    assert clock.before_snap() is False                               # the snap: the runoff runs
    assert x.left == 565 and x.pending == 0
    done(rnd, 11)


def test_a_stopped_clock_has_no_runoff_and_draws_nothing():
    clock, state = make_clock(quarter=1, left=600)
    rnd = strict()
    assert clock.runoff(rnd, keeps_running=False, ready_signal=False, lead=0) == 0
    assert state.extras.pending == 0 and not state.extras.running
    done(rnd)


def test_a_ready_signal_restart_shortens_the_runoff():
    clock, state = make_clock(quarter=3, left=600)
    rnd = strict((11, 0), (4, 3))
    assert clock.runoff(rnd, True, True, 0) == T.RUNOFF_NORMAL[0] - (T.READY_SIGNAL_CUT[0] + 3)
    done(rnd, 11, 4)


def test_the_hurry_up_and_milk_tempos_draw_their_own_ranges():
    clock, state = make_clock(quarter=4, left=200)
    rnd = strict((9, 8))
    assert clock.runoff(rnd, True, False, lead=-3) == T.RUNOFF_HURRY[1]
    clock, state = make_clock(quarter=4, left=400)
    rnd = strict((3, 0))
    assert clock.runoff(rnd, True, False, lead=3) == T.RUNOFF_MILK[0]
    done(rnd, 3)


def test_a_hurry_up_offense_gets_the_snap_off_with_six_seconds_or_more():
    clock, state = make_clock(quarter=2, left=9)
    rnd = strict((9, 8))                                               # 20 seconds wanted, 9 left
    assert clock.runoff(rnd, True, False, 0) == 8
    assert clock.before_snap() is False and state.extras.left == 1
    clock, state = make_clock(quarter=2, left=5)                       # under 6: the half ends before the snap
    clock.runoff(strict((9, 0)), True, False, 0)
    assert state.extras.pending == 12
    assert clock.before_snap() is True and state.extras.left == 0 and clock.period_over()


def test_a_normal_offense_with_more_runoff_than_time_runs_the_period_out_at_the_snap():
    clock, state = make_clock(quarter=1, left=20)
    clock.runoff(strict((11, 0)), True, False, 0)
    assert state.extras.pending >= state.extras.left
    assert not clock.period_over()                                     # not yet: a timeout can still stop it
    assert clock.before_snap() is True and clock.period_over()


def test_a_runoff_across_two_minutes_stops_the_clock_at_exactly_two_minutes_and_the_warning_follows():
    clock, state = make_clock(quarter=4, left=140, )
    rnd = strict((11, 10))                                             # 40 seconds would cross 2:00
    clock.runoff(rnd, True, False, lead=0)
    x = state.extras
    assert x.left == 120 and x.pending == 0 and not x.running and clock.warning_due()


def test_the_warning_stops_the_clock_so_no_runoff_follows_it():
    clock, state = make_clock(quarter=2, left=115, warning_due=True)
    rnd = strict()
    assert clock.runoff(rnd, True, False, 0) == 0 and not state.extras.running
    done(rnd)


# ----- a timeout stops the clock after u seconds -----

def test_a_timeout_uses_three_to_eight_seconds_of_the_pending_runoff():
    clock, state = make_clock(quarter=4, left=100, pending=30, running=True)
    rnd = strict((6, 2))
    assert clock.stop_for_timeout(rnd) == T.TIMEOUT_SIGNAL[0] + 2
    x = state.extras
    assert x.left == 95 and x.pending == 0 and not x.running
    done(rnd, 6)


def test_a_timeout_never_lets_the_period_run_out_and_draws_nothing_when_the_clock_is_stopped():
    clock, state = make_clock(quarter=4, left=4, pending=30, running=True)
    clock.stop_for_timeout(strict((6, 5)))
    assert state.extras.left == 1                                      # called at the menu: one second stays
    clock, state = make_clock(quarter=4, left=50)
    rnd = strict()
    assert clock.stop_for_timeout(rnd) == 0 and state.extras.left == 50
    done(rnd)


# ----- what the computer reads (design 5.6) and F4 -----

@pytest.mark.parametrize("left, running, plays_left, last", [(900, False, 24, False), (266, True, 7, False),
                                                              (229, True, 7, False), (228, True, 6, False),
                                                              (38, True, 1, True),
                                                              (39, True, 2, False), (38, False, 1, False),
                                                              (8, False, 1, True), (1, False, 1, True)])
def test_plays_left_and_the_last_play_read_the_seconds(left, running, plays_left, last):
    clock, state = make_clock(quarter=2, left=left, running=running, pending=30 if running else 0)
    assert clock.plays_left() == plays_left
    assert clock.is_last_play() is last


def test_played_is_still_the_counter_and_after_play_counts():
    clock, state = make_clock(quarter=1, left=500)
    state.counter = 12
    clock.after_play()
    assert clock.played() == 13 and state.extras.left == 500


@pytest.mark.parametrize("quarter, left, text", [               # Str$ numbers keep their space: the original's sentence
    (1, 900, " 15 minutes remaining in the first quarter. "),
    (2, 192, " 3 minutes  12 seconds remaining in the second quarter. "),
    (4, 61, " 1 minute  1 second remaining in the fourth quarter. "),
    (3, 45, "   45 seconds remaining in the third quarter. "),
    (5, 600, " 10 minutes remaining in the over time quarter. ")])
def test_f4_speaks_the_real_time_with_the_original_sentence(quarter, left, text):
    clock, state = make_clock(quarter=quarter, left=left)
    clock.speak()
    assert clock.game.said == [text]


def test_a_new_period_has_its_full_length_a_stopped_clock_and_new_timeouts_only_for_a_new_half():
    clock, state = make_clock(quarter=1, left=0, pending=0, warning_given=True)
    x = state.extras
    x.timeouts, x.unit = [1, 2], "H1"
    clock.start_period(1)                                              # the engine: start_period, then quarter = 2
    state.quarter = 2
    assert x.period == 2 and x.left == 900 and not x.running and not x.warning_given and x.timeouts == [1, 2]
    clock.start_period(0)                                              # quarter 2 ends: the second half
    state.quarter = 3
    assert x.period == 3 and x.unit == "H2" and x.timeouts == [3, 3]
    state.quarter, state.overtime = 5, 1                               # game_end sets quarter 5 first
    clock.start_period(0)
    assert x.period == 5 and x.left == 600 and x.unit == "OT1" and x.timeouts == [2, 2]
    x.timeouts = [0, 1]
    state.overtime = 2
    clock.start_period(0)
    assert x.period == 6 and x.unit == "OT2" and x.timeouts == [2, 2]


def test_play_off_overtime_periods_last_fifteen_minutes_and_share_timeouts_in_pairs():
    clock, state = make_clock(quarter=4, left=0, postseason=True)
    x = state.extras
    x.unit = "H2"
    state.quarter, state.overtime = 5, 1
    clock.start_period(0)
    assert x.left == 900 and x.unit == "OTP1" and x.timeouts == [3, 3]
    x.timeouts = [1, 0]
    state.overtime = 2
    clock.start_period(0)
    assert x.unit == "OTP1" and x.timeouts == [1, 0]                   # periods 1 and 2 share three
    state.overtime = 3
    clock.start_period(0)
    assert x.unit == "OTP2" and x.timeouts == [3, 3]
