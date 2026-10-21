"""Timeouts of the N. F. L. rules mode: how many, when they renew, and when the computer calls one (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 6.3 (NX1, built in SX.2), the rules table extras/rules_2026.py and the start values of extras/tuning.py.
A team has three charged timeouts in each half (4-5-1 Item 1, no carry-over); in overtime two in the one regular-season
period (16-1-3 (e); SX.12) and three for each pair of play-off periods (16-1-4 (g)). A team
calls at most one in a dead-ball period (4-5-1 Item 3). The menus refuse a request with none left, so it is never a foul.

The computer's rules (design 6.3, checked in H10 after every play in this order; the first that applies decides):
1. none when it has none, or when it would leave none and a challenge is still possible for it (before the two-minute
   warning of its half, quarters 1 to 4), unless rule 3 or 4 applies (SX.6: `challenge_possible`);
2. first half after the warning: the side with the ball next calls one when the clock runs, the pending runoff is more
   than 10 seconds and it is on its own 30 or beyond; the defense calls one when the clock runs and the offense is inside
   its own 35 on third down or later;
3. fourth quarter, trailing or tied: on offense when the clock runs and under 2:00 (tied) or 5:00 (trailing) are left; on
   defense when trailing, the clock runs and under 5:00 + 40 seconds for each timeout it holds are left;
4. overtime: like rule 2 in the last 2:00 of the period;
5. a leading computer team never calls one in the fourth quarter;
6. quarters 1 and 3: a side with three timeouts calls one with chance 1 in 80 (the league's "operational" timeouts).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..game.gamestate import own_half
from . import rules_2026 as R
from . import tuning as T


def unit_for(period: int, postseason: bool) -> str:
    """The span that shares one set of timeouts: H1 (quarters 1 and 2), H2 (3 and 4), OT<n> per regular-season overtime
    period, OTP<k> per pair of play-off overtime periods."""
    if period <= 2:
        return "H1"
    if period <= 4:
        return "H2"
    number = period - 4
    if postseason:
        return "OTP%d" % ((number + 1) // 2)
    return "OT%d" % number


def count_for(unit: str) -> int:
    if unit.startswith("OTP"):
        return R.OT_POST_TIMEOUTS
    if unit.startswith("OT"):
        return R.OT_REGULAR_TIMEOUTS
    return R.TIMEOUTS_PER_HALF


def enter_unit(record, period: int) -> bool:
    """A new period begins: a new half or overtime unit gives every team its timeouts again. True when it renewed them."""
    unit = unit_for(period, record.postseason)
    if unit == record.unit:
        return False
    record.unit = unit
    count = count_for(unit)
    record.timeouts = [count, count]
    record.called = [False, False]
    return True


def refusal(record, side: int, called=None) -> str | None:
    """Why a request is refused (the menu says so; the rules ignore such a request, 4-5-1 Item 3), or None: "none" when the
    team has none left, "called" when it already called one in this dead-ball period. `called` is the record's `called` as it was
    before the snap took the dead-ball period away (the T key during the snap count, SX.2b)."""
    if record.timeouts_of(side) <= 0:
        return "none"
    if (record.called_by(side) if called is None else called[side - 1]):
        return "called"
    return None


def charge(record, side: int) -> None:
    """A granted timeout is charged: one fewer left, one more used in the game, called in this dead-ball period."""
    record.timeouts[side - 1] -= 1
    record.used[side - 1] += 1
    record.called[side - 1] = True


@dataclass(frozen=True)
class Situation:
    """What the computer's rules read about one side after a play (before the next snap)."""
    side: int
    quarter: int
    left: int                 # seconds left in the period
    pending: int              # the runoff that would run before the snap
    running: bool
    has_ball: bool            # this side snaps next
    lead: int                 # its score minus the other's
    timeouts: int
    warning_given: bool       # in this period
    own_half: bool            # the ball is in the half of the side that has it
    yard_line: int            # the ball's distance to the goal line of the half it is in
    down: int
    challenges: int = 0       # the challenges it may still throw (SX.6; 0 when the Replay challenges switch is off)


def challenges_left(record, side: int) -> int:
    """The challenges a team may still throw (15-1-1 (f)): two in the game, a third once at least one of them changed the
    ruling, never a fourth. Whether it has a time out in hand is a separate condition (15-1-1 (d))."""
    limit = R.CHALLENGES_MAX if record.chal_won[side - 1] >= R.CHALLENGE_THIRD_AFTER_WINS else R.CHALLENGES_PER_GAME
    return max(0, limit - record.chal_used[side - 1])


def situation(state, record, side: int) -> Situation:
    other = 2 if side == 1 else 1
    return Situation(side, state.quarter, record.left, record.pending, record.running, state.wisoff == side,
                     state.score(side) - state.score(other), record.timeouts_of(side), record.warning_given,
                     state.half == own_half(state.wisoff), state.yard_line, state.down,
                     challenges_left(record, side) if record.challenges_on else 0)


def challenge_possible(view: Situation) -> bool:
    """Rule 1's challenge clause (design 6.3, NX2): a coach keeps a time out for a challenge until the two-minute warning of
    the half (quarters 1 and 3, and quarters 2 and 4 before it) while it has a challenge left. After the warning, and in
    overtime, a play is the replay official's (15-1-2) and nothing is kept."""
    if view.challenges <= 0 or view.quarter > 4:
        return False
    return view.quarter in (1, 3) or not view.warning_given


def _rule2(view: Situation) -> bool:
    """The end of a half (or of an overtime period): the side with the ball saves time in a drive, the defense saves time
    to get the ball back after a punt."""
    if not view.running:
        return False
    if view.has_ball:
        in_drive = not view.own_half or view.yard_line >= T.RULE2_DRIVE_FROM
        return view.pending > T.RULE2_PENDING_OVER and in_drive
    return view.own_half and view.yard_line < T.RULE2_DEFENSE_INSIDE and view.down >= T.RULE2_DEFENSE_DOWN


def _rule3(view: Situation) -> bool:
    if view.quarter != 4 or view.lead > 0 or not view.running:
        return False
    if view.has_ball:
        return view.left < (T.RULE3_TIED if view.lead == 0 else T.RULE3_TRAILING)
    return view.lead < 0 and view.left < T.RULE3_DEFENSE_BASE + T.RULE3_DEFENSE_PER_TIMEOUT * view.timeouts


def _rule4(view: Situation) -> bool:
    return view.quarter >= 5 and view.left <= T.RULE4_LAST and _rule2(view)


def computer_calls(view: Situation, rnd) -> bool:
    """Rules 1 to 6 for one side; rule 6 draws one number (`rnd.below(80)`), and only when it is reached."""
    if view.timeouts <= 0 or view.left <= 0:
        return False                                                      # rule 1 (and a period that is over)
    rule3, rule4 = _rule3(view), _rule4(view)
    if view.timeouts == 1 and challenge_possible(view) and not (rule3 or rule4):
        return False                                                      # rule 1: one kept for a challenge
    if view.quarter == 2 and view.warning_given and _rule2(view):
        return True                                                       # rule 2
    if rule3:
        return True                                                       # rule 3
    if rule4:
        return True                                                       # rule 4
    if view.quarter == 4 and view.lead > 0:
        return False                                                      # rule 5
    if view.quarter in (1, 3) and view.timeouts == R.TIMEOUTS_PER_HALF:
        return rnd.below(T.RULE6_CHANCE) == 0                              # rule 6
    return False
