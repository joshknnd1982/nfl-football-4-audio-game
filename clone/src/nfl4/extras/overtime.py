"""The 2026 overtime of the N. F. L. rules mode: who has had the ball, when the next score wins, when the game is decided (nfl4 only,
rule 0.13). This is inspired by Jim Kitchen.

Rule 16 of the 2026 book (printed pages 64 to 66; NFL_RULES_RESEARCH Part 7; SX.12, D-096). Classic keeps the original's sudden death:
none of this is ever called there. The record lives in the game's ExtrasRecord (H5), so Save Game keeps it:

    ot_phase     ""        no overtime yet (or a game saved before SX.12: read as sudden death, the rule it was played under)
                 "first"   the first team's initial possession: from the receivers' opening kick-off to the end of their drive
                 "second"  the first team scored; the second team's initial possession (16-1-5 (c): the kick-off after the score is its
                           opportunity to possess, even when the kickers recover it)
                 "sudden"  both teams have had the ball (or the first did not score): the next score by any method wins (16-1-3 (c))
                 "over"    the game is decided
    ot_first     the side that received the overtime's first kick-off (A); the other side is B
    ot_base      the score of each side when overtime began (the game was tied)
    ot_kicked    A scored and kicked off: the kick is B's opportunity
    ot_told      the sentence that the next score wins was said
    ot_receiver  the side that received the kick-off of the last period that began with a toss (the play-offs' third period, 16-1-4 (e))
    ot_toss      a toss is due before the next kick-off (the play-offs' fifth period, 16-1-4 (i))

The engine asks through four hooks (game/rules.py H22): `points_end_game` after points are scored (a touchdown before its try too),
`possession_ends_game` after a change of possession, `between_plays` (H10) as a safety net for a kick the kickers kept, and the period
end; every answer is computed here from the scores and who has the ball, with no draw and no spoken word (the sentences are the callers').
"""
from __future__ import annotations

from . import rules_2026 as R

NONE, FIRST, SECOND, SUDDEN, OVER = "", "first", "second", "sudden", "over"
PHASES = (NONE, FIRST, SECOND, SUDDEN, OVER)

# what the engine does when a play-off overtime period ends without a winner (16-1-4)
SAME_BALL, KICK_OFF, COIN_TOSS = "same ball", "kick off", "coin toss"


def other(side: int) -> int:
    return 2 if side == 1 else 1


def in_overtime(state) -> bool:
    return state.quarter >= 5


def points(x, state, side: int) -> int:
    """The side's points in overtime."""
    return state.score(side) - x.ot_base


def begin(x, state, receiver: int) -> None:
    """The overtime's first kick-off (16-1-3 (a)): the receivers are A, their drive is the first possession."""
    x.ot_phase, x.ot_first, x.ot_receiver = FIRST, receiver, receiver
    x.ot_base = state.score(1)
    x.ot_kicked = x.ot_told = x.ot_toss = False


def at_kickoff(x, state, kicking_side: int) -> None:
    """H4: a kick-off in overtime. The first one starts the possession rule; a kick by A after its score is B's opportunity
    (16-1-5 (c)); the kick of a period that began with a toss records its receiver (16-1-4 (e))."""
    if not in_overtime(state):
        return
    receiver = other(kicking_side)
    if x.ot_phase == NONE:
        begin(x, state, receiver)
        return
    if x.ot_toss:
        x.ot_toss, x.ot_receiver = False, receiver
    if x.ot_phase == FIRST and kicking_side == x.ot_first and points(x, state, x.ot_first) > 0:
        x.ot_kicked = True


def _settle(x) -> None:
    """The kick after A's score was B's opportunity: from then on the phase is SECOND, whatever happened on the kick."""
    if x.ot_phase == FIRST and x.ot_kicked:
        x.ot_phase = SECOND


def _sudden(x) -> None:
    x.ot_phase = SUDDEN


def after_points(x, state, touchdown_by: int | None = None) -> bool:
    """After points were scored in overtime: a touchdown's six before its try (`touchdown_by` the side that scored it), or any points
    whose play is over (a field goal, a safety, a try, two points for the defense on a try). True when the game is decided."""
    if not in_overtime(state):
        return False
    _settle(x)
    if x.ot_phase in (NONE, SUDDEN, OVER):         # sudden death (and a game saved before SX.12): any points decide it
        x.ot_phase = OVER
        return True
    a, b = x.ot_first, other(x.ot_first)
    pa, pb = points(x, state, a), points(x, state, b)
    if x.ot_phase == FIRST:
        if pb > 0 and pa == 0:                     # B scored on A's initial possession: a safety (16-1-3 (a)), or a defensive score
            x.ot_phase = OVER                      # after which A's possession had ended without points (16-1-3 (c))
            return True
        return False                               # A scored: its try is played, then it kicks off to B
    # SECOND: B's initial possession; any points end it (a score by B, or by A's defense)
    if touchdown_by is not None:
        if touchdown_by == a or pb > pa:           # A's defense scored, or B went ahead: decided, no try (4-8-2 (c))
            x.ot_phase = OVER
            return True
        return False                               # B tied it or is still behind: the try is played
    if pa != pb:                                   # 16-1-3 (b): after both possessions the side ahead wins
        x.ot_phase = OVER
        return True
    _sudden(x)                                     # tied after both: the next score wins (16-1-3 (c))
    return False


def at_possession(x, state) -> bool:
    """A change of possession, or a new drive after a kick (the ball is `state.wisoff`'s). True when the game is decided."""
    if not in_overtime(state) or x.ot_phase in (NONE, SUDDEN, OVER):
        return x.ot_phase == OVER and in_overtime(state)
    _settle(x)
    a, b = x.ot_first, other(x.ot_first)
    pa, pb = points(x, state, a), points(x, state, b)
    if x.ot_phase == FIRST:
        if state.wisoff == b and pa == 0:          # A's initial possession ended without a score: the next score wins (16-1-3 (c))
            _sudden(x)
        return False
    if state.wisoff == a:                          # B's initial possession ended (a punt, a turnover, downs, a missed kick), or A kept
        if pa != pb:                               # its own kick-off: B had its opportunity (16-1-5 (c)); the side ahead wins
            x.ot_phase = OVER
            return True
        _sudden(x)
    return False


def kickers_kept_punt(x, state, kicking_side: int) -> None:
    """A punt the receivers muffed and the kickers recovered (16-1-5 (c)): it was the receivers' opportunity to possess. When the first team
    punted on its initial possession without points, both teams have now had theirs: the next score wins. (The second team keeping its own
    muffed punt goes on as its possession: a reading, Q-038.)"""
    if not in_overtime(state):
        return
    _settle(x)
    if x.ot_phase == FIRST and kicking_side == x.ot_first and points(x, state, x.ot_first) == 0:
        _sudden(x)


def decided(x, state) -> bool:
    return in_overtime(state) and x.ot_phase == OVER


def sudden_news(x, state) -> bool:
    """True once, when the sentence that the next score wins is due (said at the next kick-off or before the next play)."""
    if in_overtime(state) and x.ot_phase == SUDDEN and not x.ot_told:
        x.ot_told = True
        return True
    return False


def second_possession_trailing(x, state, side: int) -> int:
    """How far `side` trails while it has its initial possession as the second team (0 when it does not): the computer's fourth down
    then never punts (a punt ends the game) and kicks a field goal only when it ties."""
    _settle(x)
    if not in_overtime(state) or x.ot_phase != SECOND or side == x.ot_first:
        return 0
    return max(0, points(x, state, x.ot_first) - points(x, state, side))


def period_end(x, state) -> str | None:
    """A play-off overtime period ended without a winner (16-1-4 (d)): what the next period starts with. None in the regular season (one
    period, 16-1-3 (d)): the game ends, as a tie when the score is level."""
    if not x.postseason:
        return None
    period = state.overtime + 1                    # the overtime number of the period that begins
    if period % R.OT_POST_NEW_TOSS_AFTER == 1:     # 5, 9, ...: another toss (16-1-4 (i))
        x.ot_toss = True
        return COIN_TOSS
    if period % R.OT_POST_NEW_TOSS_AFTER == R.OT_POST_LOSER_CHOOSES_PERIOD:     # 3, 7, ...: a new kick-off (16-1-4 (e))
        if x.ot_phase in (FIRST, SECOND):          # an initial possession has not ended: it goes on (16-1-4 (d))
            return SAME_BALL
        return KICK_OFF
    return SAME_BALL                               # 2, 4, ...: the ball, the down and the distance stay (4-2-3)


def third_period_receiver(x) -> int:
    """16-1-4 (e): at the third period the captain who lost the toss has the first choice; the clone gives it as its second half does:
    the side that kicked off at the start of the last tossed period receives."""
    return other(x.ot_receiver)


def check(x, whole) -> None:
    """The overtime values of a saved record (ExtrasRecord.check)."""
    if x.ot_phase not in PHASES:
        raise ValueError("the overtime phase is %r" % (x.ot_phase,))
    whole(x.ot_first, 0 if x.ot_phase == NONE else 1, 2, "the overtime's first team")
    whole(x.ot_receiver, 0 if x.ot_phase == NONE else 1, 2, "the overtime's receiver")
    whole(x.ot_base, 0, 9999, "the score when overtime began")
    for name in ("ot_kicked", "ot_told", "ot_toss"):
        if not isinstance(getattr(x, name), bool):
            raise ValueError("%s is %r" % (name, getattr(x, name)))
