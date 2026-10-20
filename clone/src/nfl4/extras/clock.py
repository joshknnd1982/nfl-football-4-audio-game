"""The real game clock of the N. F. L. rules mode (nfl4 only, rule 0.13; C2, hook H1). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 5 (built in SX.2). Every period has a clock in whole seconds. A play costs its live time L (drawn at its
narration end point, H2 step 4: `play_time`) and, when the clock keeps running after it, a runoff R until the next snap
(drawn between plays, H10: `runoff`). R is not applied at once: it is kept PENDING and applied at the snap (`before_snap`),
so the play menu and the computer's decisions can still stop it with a timeout (`stop_for_timeout` uses only u seconds of
it). Two things stop the clock at the end of the play instead: when L crosses 2:00 of a warning period the warning follows
the play, and when R would cross it the clock stops at exactly 2:00 and the warning follows (3-41).

`NflPeriodClock` answers the calls of the classic engine's period clock (game/periodclock.py) from seconds:
    plays_left()    the time left / 38, rounded up, at least 1 (design 5.6: 5.7's thresholds keep their meaning)
    played()        the counter of counted plays in the period, as Classic
    is_last_play()  at most 38 seconds left with the clock running, at most 8 with it stopped
    period_over()   the clock is at 0
    warning_zone(), warning_due()   the two-minute warning is to be given now; warning_given() after it was said
    speak()         F4: the real time with the original's sentence (" 3 minutes 12 seconds remaining in the ...")
    after_play()    the counter grows (the next-play step); the time was taken at the narration end point
    start_period()  a new quarter or overtime period: the full time, the clock stopped, the timeouts of a new half
    before_snap()   the pending runoff runs; True when it ran the period out (the period ends before the snap)
The engine reads them in the same places as the counter clock, so 5.6 and 5.7 need no change.
"""
from __future__ import annotations

import math

from ..game import outcome as O
from ..game.gameclock import PLURAL, QUARTER_END, REMAINING_IN_THE, SECOND, clock_sentence, quarter_word
from ..game.vbnum import str_
from . import rules_2026 as R
from . import timeouts
from . import tuning as T

HURRY, MILK, NORMAL = "hurry-up", "milk", "normal"


# ----- the rules of time, as plain functions (design 4 and 5) -----

def period_seconds(period: int, postseason: bool) -> int:
    """Quarters 1 to 4: 15 minutes (4-1); an overtime period: 10 minutes, 15 in the play-offs (16-3, 16-4)."""
    if period <= 4:
        return R.QUARTER_SECONDS
    return R.OT_POST_PERIOD_SECONDS if postseason else R.OT_REGULAR_PERIOD_SECONDS


def is_warning_period(period: int, postseason: bool) -> bool:
    """3-41: the second and fourth quarters; overtime by practice: every regular-season period, every second play-off
    period."""
    if period <= 4:
        return period in R.WARNING_QUARTERS
    if not postseason:
        return True
    return (period - 4) % R.OT_POST_WARNING_EVERY == 0


def late_window(quarter: int, left: int) -> bool:
    """A runner or receiver out of bounds stops the clock until the snap: the last 2:00 of the first half, the last 5:00 of
    the second half, all of overtime (4-3-2); before them the clock restarts on the ready signal."""
    if quarter >= 5:
        return True
    if quarter == 2:
        return left <= R.LATE_FIRST_HALF_SECONDS
    if quarter == 4:
        return left <= R.FIVE_MINUTE_RULE_SECONDS
    return False


def tempo(quarter: int, left: int, lead: int) -> str:
    """The tempo of the offense that snaps next (design 5.3); `lead` is its score minus the other side's."""
    if quarter == 2 and left <= T.HURRY_FIRST_HALF:
        return HURRY
    if quarter == 4 and lead < 0 and left <= T.HURRY_TRAILING:
        return HURRY
    if quarter == 4 and lead == 0 and left <= T.HURRY_TIED:
        return HURRY
    if quarter >= 5 and left <= T.HURRY_OVERTIME:
        return HURRY
    if quarter == 4 and lead > 0 and left <= T.MILK_LEADING:
        return MILK
    return NORMAL


RUNOFF = {NORMAL: T.RUNOFF_NORMAL, HURRY: T.RUNOFF_HURRY, MILK: T.RUNOFF_MILK}

# the clock keeps running after these plays when they end in bounds and the same side keeps the ball (design 5.2 list A)
RUNNING_KINDS = (O.RUN, O.PASS_COMPLETE, O.SACK)
LIVE_TIMES = {O.RUN: T.LIVE_RUN, O.PASS_COMPLETE: T.LIVE_PASS_COMPLETE, O.PASS_INCOMPLETE: T.LIVE_PASS_INCOMPLETE,
              O.SACK: T.LIVE_SACK, O.INTERCEPTION: T.LIVE_TURNOVER, O.FUMBLE: T.LIVE_TURNOVER, O.PUNT: T.LIVE_PUNT,
              O.FIELD_GOAL_GOOD: T.LIVE_FIELD_GOAL, O.FIELD_GOAL_MISSED: T.LIVE_FIELD_GOAL,
              O.FIELD_GOAL_SHORT: T.LIVE_FIELD_GOAL, O.ONSIDE_KICK: T.LIVE_ONSIDE}


def draw_between(rnd, low_high: tuple[int, int]) -> int:
    """A uniform whole number low to high: Int(Rnd * (high - low + 1)) + low (one draw)."""
    low, high = low_high
    return rnd.below(high - low + 1) + low


def underlying_kind(outcome, state) -> str:
    """The kind of play behind a touchdown or a safety: the play's own result kind (a run, a catch, a sack or a kick-off
    return), which the engine keeps in the state."""
    if outcome.kind in (O.TOUCHDOWN, O.SAFETY_KIND):
        if outcome.offense_play == 0:
            return O.KICKOFF_RETURN
        return state.result_kind or (O.RUN if outcome.offense_play <= 2 else O.PASS_COMPLETE)
    return outcome.kind


def live_time(outcome, state, rnd) -> int:
    """L of design 5.1 for the play of this record: 0 for a try and a touch back (untimed or never touched), the kick-off
    return's formula, else a draw from the kind's range. One draw at most (two for a return)."""
    if outcome.two_point_try:
        return 0                                                         # 4-3-2(h): the try is untimed
    kind = underlying_kind(outcome, state)
    if kind == O.KICKOFF_TOUCH_BACK:
        return 0                                                         # 4-3-1: the clock starts when the ball is touched
    if kind == O.KICKOFF_RETURN:
        return T.KICKOFF_RETURN_BASE + max(0, outcome.yards) // 10 + draw_between(rnd, T.KICKOFF_RETURN_EXTRA)
    if kind == O.TWO_POINT_TRY:
        return 0
    span = LIVE_TIMES.get(kind)
    if outcome.qb_run == "scramble" and kind == O.RUN:
        span = T.LIVE_SCRAMBLE                                           # SX.5: a pass play that became a run (design 5.1)
    if span is None:
        return 0
    seconds = draw_between(rnd, span)
    if kind in (O.FIELD_GOAL_GOOD, O.FIELD_GOAL_MISSED, O.FIELD_GOAL_SHORT):
        seconds = min(seconds, R.FIELD_GOAL_MAX_CLOCK)
    return seconds


class NflPeriodClock:
    """H1 from seconds. The values live in the state's ExtrasRecord (H5), so a snapshot or a save holds the clock."""

    def __init__(self, game, state):
        self.game = game
        self.state = state

    @property
    def x(self):
        return self.state.extras

    # ----- what the engine reads (5.6, 5.7) -----

    def plays_left(self) -> int:
        return max(1, math.ceil(self.x.left / T.SECONDS_PER_PLAY))

    def played(self) -> int:
        return self.state.counter

    def is_last_play(self) -> bool:
        x = self.x
        return x.left <= (T.LAST_PLAY_RUNNING if x.running else T.LAST_PLAY_STOPPED)

    def period_over(self) -> bool:
        """The clock is at 0, unless an untimed down is due (an accepted foul by the defense on the last play of a half,
        4-8-2 (a), SX.3)."""
        return self.x.left <= 0 and not self.x.extension

    def warning_zone(self) -> bool:
        return self.x.warning_due and self.x.left > 0

    def warning_due(self) -> bool:
        return self.warning_zone()

    def warning_given(self) -> None:
        """The engine said the warning (game/pag_breaks.py): it is not due again in this period."""
        self.x.warning_due = False
        self.x.warning_given = True

    def speak(self) -> None:
        """F4: the time at the end of the last play, with the original's sentence, then clk and g = F1 (as sgc). The
        original's sentence has no form for no time at all (it says neither minutes nor seconds), so 0:00 (a try or the
        wait after a last-second score) is said with its words as " 0 seconds"."""
        left = self.x.left
        word = quarter_word(min(max(self.state.quarter, 1), 10))
        if left <= 0:
            text = " " + str_(0) + SECOND + PLURAL + REMAINING_IN_THE + word + QUARTER_END
        else:
            text = clock_sentence(left // 60, left % 60, word)
        self.game.say_clock(text)

    def summary_left(self) -> tuple[int, int]:
        """The minutes and seconds left, for the one-sentence summary of a save (SX.14)."""
        left = max(0, self.x.left)
        return left // 60, left % 60

    # ----- what the engine does -----

    def after_play(self, outcome=None) -> None:
        """The next-play step: L738 = L738 + 1 (the counted plays, design 5.7's unit). A foul before the snap ran no play:
        not counted (SX.3)."""
        if self.x.no_snap:
            self.x.no_snap = False
            return
        self.state.counter += 1

    def start_period(self, counter: int) -> None:
        """A new period (the engine calls it before it moves the quarter on, or after it set quarter 5 for overtime)."""
        s, x = self.state, self.x
        s.counter = counter
        x.period = s.quarter + 1 if s.quarter <= 3 else 4 + max(1, s.overtime)
        x.left = period_seconds(x.period, x.postseason)
        x.pending = 0
        x.running = False
        x.warning_due = x.warning_given = False
        x.out_of_bounds = False
        x.called = [False, False]
        x.extension = x.extension_snap = x.no_snap = False
        x.foul_clock = ""
        timeouts.enter_unit(x, x.period)

    def before_snap(self) -> bool:
        """H1 at the snap: the pending runoff runs. True when it ran the period out: the period ends before the snap
        (design 5.4; nobody stopped the clock). A two-point try is untimed (4-3-2(h), 11-3-1): it is played even when the
        touchdown used the last second, and the half or the game ends after it (at the kick-off, H4)."""
        x = self.x
        x.left = max(0, x.left - x.pending)
        x.pending = 0
        x.called = [False, False]                 # a new dead-ball period comes after this play
        x.out_of_bounds = False
        x.extension_snap = False
        if x.extension:                           # SX.3: the untimed down after an accepted foul by the defense on the
            x.extension = False                   # last play of a half (4-8-2 (a)) is played at 0:00
            x.extension_snap = True
            return False
        if self.state.two_point:
            return False
        return x.left <= 0

    def capture(self) -> tuple:
        """What `before_snap` is about to change: the time left, the pending runoff, the timeouts called in this dead-ball period, the
        out-of-bounds mark and the untimed down. A timeout called by the T key during the snap count gives the snap back (restore)."""
        x = self.x
        return x.left, x.pending, x.running, list(x.called), x.out_of_bounds, x.extension, x.extension_snap

    @staticmethod
    def snapped_called(token: tuple) -> list:
        """The timeouts called in the dead-ball period that the snap ended (the T key's refusal reads it, SX.2b)."""
        return token[3]

    def restore(self, token: tuple) -> None:
        x = self.x
        x.left, x.pending, x.running, called, x.out_of_bounds, x.extension, x.extension_snap = token
        x.called = list(called)

    # ----- the extras' own calls -----

    def play_time(self, outcome, rnd) -> int:
        """At the narration end point: L runs (a play is always completed, 4-8-1, so the clock stops at 0). When L takes the
        clock across 2:00 of a warning period, the warning follows this play (3-41)."""
        x = self.x
        seconds = live_time(outcome, self.state, rnd)
        before = x.left
        x.left = max(0, x.left - seconds)
        if self._crosses_warning(before, x.left) and x.left > 0:
            x.warning_due = True
        return seconds

    def _crosses_warning(self, before: int, after: int) -> bool:
        x = self.x
        return (is_warning_period(x.period, x.postseason) and not x.warning_given and not x.warning_due
                and before > R.WARNING_SECONDS >= after)

    def runoff(self, rnd, keeps_running: bool, ready_signal: bool, lead: int, cap: int | None = None) -> int:
        """H10, once per play: R for the side that snaps next, kept pending (design 5.3). Returns R (0: the clock is
        stopped)."""
        x, s = self.x, self.state
        if not keeps_running or x.left <= 0 or x.warning_due:
            x.pending, x.running = 0, False
            return 0
        pace = tempo(s.quarter, x.left, lead)
        seconds = draw_between(rnd, RUNOFF[pace])
        if ready_signal:
            seconds = max(0, seconds - draw_between(rnd, T.READY_SIGNAL_CUT))
        if cap is not None:
            seconds = min(seconds, cap)            # after a penalty the play clock is 25 (4-6-2 (e)): SX.3
        if pace == HURRY and seconds >= x.left >= T.HURRY_SNAP_MIN:
            seconds = x.left - 1                  # the hurry-up offense gets the snap off before time runs out
        x.pending, x.running = seconds, seconds > 0
        if self._crosses_warning(x.left, x.left - seconds):
            x.left = R.WARNING_SECONDS            # the clock stops at exactly 2:00 and the warning follows (3-41)
            x.pending, x.running = 0, False
            x.warning_due = True
        return seconds

    def stop_for_timeout(self, rnd) -> int:
        """A timeout stops a running clock after u seconds of the pending runoff (the time to signal the official), never
        later than one second before the end of the period. Returns the seconds that ran (one draw when it was running)."""
        x = self.x
        if x.pending <= 0:
            x.pending, x.running = 0, False
            return 0
        used = min(draw_between(rnd, T.TIMEOUT_SIGNAL), x.pending, max(0, x.left - 1))
        x.left -= used
        x.pending, x.running = 0, False
        return used
