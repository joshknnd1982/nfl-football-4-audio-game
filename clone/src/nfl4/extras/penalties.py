"""Penalty enforcement of the N. F. L. rules mode as plain functions (nfl4 only, rule 0.13; NX7). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 9.3 and 9.4, the 2026 rulebook through NFL_RULES_RESEARCH Part 6 (the citations are on the lines). No
speech, no keys, no random numbers: the caller (extras/penalty_flow.py) draws the foul and its spot, these functions say
what accepting and what declining it would give, which the computer prefers, and how a situation is said.

Positions are yards from the goal line of a named side ("its own goal line"): 0 is that goal line, 100 the other. A `Down`
is the down at the snap from the offense's view (on a kick-off the receivers are the offense and the return starts at 0).
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..game import outcome as O
from . import fouls_2026 as F
from . import nx_texts as X
from . import rules_2026 as R
from . import tuning as T

# what a result is
NEW_DOWN = "new down"                     # `ball` snaps next from `los`, `down` and `to_go`
TOUCHDOWN, FIELD_GOAL, SAFETY = "touchdown", "field goal", "safety"
TURNOVER = "turnover"                     # the interception or the fumble stands (its spot is the engine's draw, Q31)
TRY_GOOD, TRY_FAILS, TRY_AGAIN = "try good", "try fails", "try again"
REPLAY_KICK = "kick again"                # offsetting fouls on a kick-off: the kick is made again
PLAY_STANDS = "play stands"               # double fouls after the play: they offset and the down counts (14-4-9 Item 2)

# how the offended team may answer (design 9.3)
CHOICE = "choice"                         # accept or decline
AUTO_ACCEPT = "accepted"                  # a dead-ball foul before the snap: declining would only replay the same down
AUTO_DECLINE = "declined"                 # the score stands; accepting could only take it away
ON_THE_TRY = "on the try"                 # a personal foul by the defense on a touchdown: the score stands, the yards go
#                                           to the try (14-2-3)


def other(side: int) -> int:
    return 2 if side == 1 else 1


@dataclass(frozen=True)
class Down:
    offense: int
    los: int
    down: int = 1
    to_go: int = 10
    two_point: bool = False

    @property
    def line_to_gain(self) -> int:
        return min(100, self.los + self.to_go)


@dataclass(frozen=True)
class PlayFacts:
    """What the play did, at its narration end point (H2)."""
    kind: str                     # the outcome kind of the play behind the result (RUN, PASS_COMPLETE, ..., PUNT)
    end: int = 0                  # where the ball became dead, offense's view (a field play, a kick-off return)
    score: str | None = None      # "touchdown", "field goal", "safety", "two-point"
    turnover: bool = False        # an interception or a fumble (the opponent has the ball)
    receivers_spot: int = 0       # a punt: where the receivers get the ball, their view
    offense_play: int = 0         # the plays chosen (the multipliers of design 9.2)
    defense_play: int = 0


@dataclass(frozen=True)
class Result:
    kind: str
    ball: int = 0                 # NEW_DOWN: the side with the ball next; a score: the side that scored
    los: int = 0                  # NEW_DOWN, TRY_AGAIN: from `ball`'s own goal line
    down: int = 1
    to_go: int = 10
    new_series: bool = False      # a new first down for `ball`
    points: tuple = (0, 0)        # side 1, side 2
    yards: int = 0                # an accepted penalty: the yards it moved the ball (the statistics)
    notes: tuple = ()             # the sentences after an accepted penalty: NXP-09, NXP-10, NXP-11, NXP-14
    keeps_play: bool = False      # the play's own result stands under the penalty (statistics kept)
    play_first_down: bool = False     # the play itself made a first down (kept: counted as the original counts it)
    penalty_first_down: bool = False  # the penalty gave the first down
    erased_score: str | None = None   # the score this accepted penalty takes away (the situation says so)
    untimed: bool = False         # one more untimed down (4-8-2 (a))
    pieces: tuple = ()            # situation pieces said before the result (NXP-S05, S07, S08, S09)


# ----- the yards -----

def offender_side(foul: F.Foul, down: Down) -> int:
    return down.offense if foul.offense_side else other(down.offense)


def half_distance(to_goal: int, yards: int) -> tuple[int, bool]:
    """14-2-1: the yards a distance penalty moves the ball from a spot `to_goal` yards from the offender's goal line:
    never more than half that distance (rounded down in whole yards, so the ball never reaches the goal line). Returns
    (yards moved, whether the half-distance rule cut it)."""
    half = max(0, to_goal) // 2
    if yards > half:
        return half, True
    return yards, False


def move(spot: int, yards: int, by_offense: bool) -> tuple[int, int, bool]:
    """The new spot (offense's view) after a distance penalty from `spot`: back toward the offense's goal for a foul by the
    offense, forward for a foul by the defense. Returns (new spot, yards moved, halved)."""
    if by_offense:
        moved, halved = half_distance(spot, yards)
        return spot - moved, moved, halved
    moved, halved = half_distance(100 - spot, yards)
    return spot + moved, moved, halved


# ----- the play's own result (what declining keeps) -----

def play_result(down: Down, play: PlayFacts) -> Result:
    """What the engine does with the play when there is no penalty (GAME_SPEC 5.11, 5.12)."""
    offense, defense = down.offense, other(down.offense)
    if down.two_point:
        return Result(TRY_GOOD, offense, points=_points(offense, 2)) if play.score == "two-point" else Result(TRY_FAILS)
    if play.kind == O.ONSIDE_KICK:                # SX.4: the kicking team kept it (`turnover`), or the receivers have it
        if play.turnover:
            return Result(NEW_DOWN, defense, 100 - play.end, new_series=True)
        return Result(NEW_DOWN, offense, play.end, new_series=True)
    if play.score == "touchdown":
        return Result(TOUCHDOWN, offense, points=_points(offense, 6))
    if play.score == "field goal":
        return Result(FIELD_GOAL, offense, points=_points(offense, 3))
    if play.score == "safety":
        return Result(SAFETY, defense, points=_points(defense, 2))
    if play.turnover:
        return Result(TURNOVER, defense, pieces=(turnover_piece(play.kind),))
    if play.kind == O.FIELD_GOAL_MISSED:             # SX.10d (G26-7): the kicks of 2026 give the spot of the kick or the 20
        return Result(NEW_DOWN, defense, play.receivers_spot or 100 - down.los, new_series=True)
    if play.kind == O.PUNT:
        return Result(NEW_DOWN, defense, play.receivers_spot, new_series=True)
    if play.kind in (O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK):
        return Result(NEW_DOWN, offense, play.end, new_series=True, play_first_down=play.kind == O.KICKOFF_RETURN)
    gained = play.end - down.los
    to_go = down.to_go - gained
    if to_go < 1:
        return Result(NEW_DOWN, offense, play.end, new_series=True, play_first_down=True)
    if down.down + 1 >= 5:
        return Result(NEW_DOWN, defense, 100 - play.end, new_series=True)          # turned over on downs
    return Result(NEW_DOWN, offense, play.end, down.down + 1, to_go)


def _points(side: int, value: int) -> tuple:
    return (value, 0) if side == 1 else (0, value)


# ----- accepting: the enforcement (design 9.4) -----

def enforcement_spot(foul: F.Foul, down: Down, play: PlayFacts, foul_spot: int | None) -> int:
    """Where a foul that erases the play is enforced from (offense's view)."""
    if foul.spot == F.THREE_AND_ONE and play.kind == O.RUN and not play.turnover:
        # 14-3-6: a foul by the offense behind the end of the run is enforced from its spot; behind the line of
        # scrimmage, or when the run ended behind it, from the previous spot
        if foul_spot is None or play.end <= down.los or foul_spot < down.los:
            return down.los
        return min(foul_spot, play.end, 100)
    if foul.spot == F.DEAD_BALL and not play.turnover and play.kind in (O.RUN, O.PASS_COMPLETE, O.SACK):
        return max(play.end, down.los)            # a defense foul behind the line: from the previous spot (14-3-6)
    if foul.spot == F.BETTER_OF and play.kind == O.PASS_COMPLETE and not play.turnover:
        return max(play.end, down.los)            # 14-4-5 (d): the previous or the dead ball spot, the better
    return down.los


def accept(foul: F.Foul, down: Down, play: PlayFacts | None, foul_spot: int | None = None) -> Result:
    """The result of accepting `foul` (play None: a foul before the snap)."""
    by_offense = foul.offense_side
    if play is not None and play.kind == O.ONSIDE_KICK:
        return _accept_on_onside(foul, down, play)
    if play is not None and play.kind in (O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK):
        return _accept_on_kickoff(foul, down, play, foul_spot)
    if foul.spot == F.CATCH_SPOT and play is not None:
        return _accept_catch_interference(foul, down, play)
    if F.AFTER in foul.phases:
        return _accept_after(foul, down, play)
    if foul.spot == F.PASS_SPOT:
        return _accept_grounding(foul, down, foul_spot)
    if foul.spot == F.SPOT_OF_FOUL and foul.yards == 0:
        return _accept_pass_interference(foul, down, foul_spot)
    spot = down.los if play is None else enforcement_spot(foul, down, play, foul_spot)
    new, moved, halved = move(spot, foul.yards, by_offense)
    keeps = play is not None and spot != down.los and not by_offense and not play.turnover and play.score is None
    erased = _erased_score(play)
    result = _downs_after(foul, down, new, moved, halved)
    if keeps:                                     # enforced from the end of the play: the play's yards stand
        result = replace(result, keeps_play=True)
    return replace(result, erased_score=erased)


def _erased_score(play: PlayFacts | None) -> str | None:
    if play is None or play.score in (None, "safety"):
        return None
    return play.score


def _downs_after(foul: F.Foul, down: Down, new: int, moved: int, halved: bool, loss_of_down: bool = False) -> Result:
    """14-1-2: the number of the down and the line to gain after a penalty that replaces the play."""
    notes = (X.text("NXP-11"),) if halved else ()
    offense = down.offense
    if down.two_point:                            # 11-3-3: the try is played again from the new spot, or fails
        if loss_of_down:
            return Result(TRY_FAILS, offense, yards=moved, notes=(X.text("NXP-10"),) + notes)
        return Result(TRY_AGAIN, offense, new, yards=moved, notes=notes)
    if foul.automatic_first_down:                 # Item 5: a foul by the defense, first and 10
        return Result(NEW_DOWN, offense, new, new_series=True, penalty_first_down=True, yards=moved,
                      notes=(X.text("NXP-09"),) + notes)
    line = down.line_to_gain
    to_go = line - new
    if foul.offense_side:
        if loss_of_down:                          # Item 2: a combination penalty
            next_down = down.down + 1
            notes = (X.text("NXP-10"),) + notes
            if next_down >= 5:                    # on fourth down the ball goes over, the yards enforced too
                return Result(NEW_DOWN, other(offense), 100 - new, new_series=True, yards=moved, notes=notes)
            if new > line:
                return Result(NEW_DOWN, offense, new, new_series=True, penalty_first_down=True, yards=moved, notes=notes)
            return Result(NEW_DOWN, offense, new, next_down, max(1, to_go), yards=moved, notes=notes)
        if new > line and R.FIRST_DOWN_ONLY_PAST_THE_LINE:    # Item 4 (only beyond the line)
            return Result(NEW_DOWN, offense, new, new_series=True, penalty_first_down=True, yards=moved, notes=notes)
        # exactly on the line: not a first down (Part 1.5 default); the clone has no inches, so 1 to go
        return Result(NEW_DOWN, offense, new, down.down, max(1, to_go), yards=moved, notes=notes)
    if to_go <= 0:                                # Item 5's exceptions: a first down only on or past the line
        return Result(NEW_DOWN, offense, new, new_series=True, penalty_first_down=True, yards=moved, notes=notes)
    return Result(NEW_DOWN, offense, new, down.down, to_go, yards=moved, notes=notes)


def _accept_pass_interference(foul: F.Foul, down: Down, foul_spot: int | None) -> Result:
    """8-5: a first down at the spot of the foul, with no half-distance limit; in the end zone on the 1, or halfway to the
    goal line when the previous spot is inside the 2. On a try: the try again from the spot (the 1 in the end zone)."""
    spot = down.los if foul_spot is None else foul_spot
    if spot >= 100:
        spot = 100 - R.DPI_GOAL_LINE_SPOT
        if down.los >= 100 - 2:
            spot = max(down.los, down.los + (100 - down.los) // 2)
    spot = max(spot, down.los)
    if down.two_point:
        return Result(TRY_AGAIN, down.offense, spot, yards=spot - down.los)
    return Result(NEW_DOWN, down.offense, spot, new_series=True, penalty_first_down=True, yards=spot - down.los,
                  notes=(X.text("NXP-09"),))


def _accept_grounding(foul: F.Foul, down: Down, pass_spot: int | None) -> Result:
    """8-2-1: loss of down and 10 yards from the previous spot (half the distance applies there), or loss of down at the
    spot of the pass when that is worse for the offense; a safety when the passer was in his own end zone."""
    spot_of_pass = down.los if pass_spot is None else pass_spot
    if spot_of_pass == 0:
        spot_of_pass = 1                          # on the goal line, not wholly in the end zone: no safety, the 1
    if spot_of_pass < 0 and not down.two_point:
        defense = other(down.offense)
        return Result(SAFETY, defense, points=_points(defense, 2), notes=(X.text("NXP-10"),))
    from_previous, moved, halved = move(down.los, foul.yards, True)
    new = from_previous
    if 0 < spot_of_pass < from_previous:
        new, halved = spot_of_pass, False
    return _downs_after(foul, down, new, down.los - new, halved, loss_of_down=True)


def _accept_after(foul: F.Foul, down: Down, play: PlayFacts) -> Result:
    """14-4-9: a foul after the play is enforced from the succeeding spot and the down counts: the play's result stands and
    the yards are added. By the defense: an automatic first down. By the offense: after a first down on the play, first
    and 10 from the new spot (Item 1), else the down after the play with the yards added to the distance."""
    first = play_result(down, play)
    by_offense = foul.offense_side
    new, moved, halved = move(first.los, foul.yards, by_offense)
    notes = (X.text("NXP-11"),) if halved else ()
    if not by_offense:
        return Result(NEW_DOWN, first.ball, new, new_series=True, penalty_first_down=not first.new_series, yards=moved,
                      notes=(X.text("NXP-09"),) + notes, keeps_play=True, play_first_down=first.play_first_down)
    if first.new_series:
        return Result(NEW_DOWN, first.ball, new, new_series=True, yards=moved, notes=notes, keeps_play=True,
                      play_first_down=first.play_first_down)
    return Result(NEW_DOWN, first.ball, new, first.down, first.to_go + moved, yards=moved, notes=notes, keeps_play=True)


def _accept_catch_interference(foul: F.Foul, down: Down, play: PlayFacts) -> Result:
    """Kick catch interference on a punt (10-1-1, SX.10d): the kicking team hindered the catch. The receivers get the ball 15 yards beyond
    where they got it (their view; half the distance near the goal line, 14-2-1) with a first down; the punt itself stands."""
    spot = min(99, max(1, play.receivers_spot))
    new, moved, halved = move(spot, foul.yards, False)
    return Result(NEW_DOWN, other(down.offense), new, new_series=True, yards=moved, keeps_play=True,
                  notes=(X.text("NXP-11"),) if halved else ())


def _accept_on_kickoff(foul: F.Foul, down: Down, play: PlayFacts, foul_spot: int | None) -> Result:
    """A kick-off (the receivers are the offense): a foul by the kicking team, the yards from the dead ball spot (14-4-7's
    option, the receivers keep the ball); a foul by the receivers on the return, from the spot of the foul (three and one
    after they have the ball, 14-4-7), the return's score erased."""
    end = play.end
    if foul.offense_side:
        spot = end if foul_spot is None else min(foul_spot, end, 99)
        new, moved, halved = move(spot, foul.yards, True)
        return Result(NEW_DOWN, down.offense, new, new_series=True, yards=moved, erased_score=_erased_score(play),
                      notes=(X.text("NXP-11"),) if halved else (), keeps_play=True, play_first_down=True)
    new, moved, halved = move(min(end, 99), foul.yards, False)
    return Result(NEW_DOWN, down.offense, new, new_series=True, yards=moved, keeps_play=True,
                  play_first_down=play.kind == O.KICKOFF_RETURN, notes=(X.text("NXP-11"),) if halved else ())


def _accept_on_onside(foul: F.Foul, down: Down, play: PlayFacts) -> Result:
    """An onside kick (design 8.3; 6-1-6 penalty, 6-2-5, 6-3-1, 14-4-7; the receivers are the offense): a foul by the kicking
    team. When the receivers have the ball, the yards are enforced from the dead ball spot (14-4-7's option when they keep
    possession; the half distance applies). When the kicking team recovered it: offside (P24) loses five yards and the kick
    is made again from there (`yards` says how far back); an illegal touch (P33) gives the receivers the ball at the spot
    (6-2-5 Item 1: "or the receiving team takes possession at the spot of the illegal touch")."""
    if not play.turnover:
        new, moved, halved = move(min(play.end, 99), foul.yards, False)
        return Result(NEW_DOWN, down.offense, new, new_series=True, yards=moved, keeps_play=True,
                      notes=(X.text("NXP-11"),) if halved else ())
    if foul.id == "P24":
        return Result(REPLAY_KICK, down.offense, yards=foul.yards, notes=(X.text("NXP-13"),))
    return Result(NEW_DOWN, down.offense, min(play.end, 99), new_series=True)


def replay_down(down: Down, play: PlayFacts | None) -> Result:
    """Offsetting fouls (14-5-1): the down is played again from the previous spot with the same down and distance; a
    kick-off is made again; a try is tried again."""
    if play is not None and play.kind in (O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK):
        return Result(REPLAY_KICK, down.offense, notes=(X.text("NXP-13"),))
    if down.two_point:
        return Result(TRY_AGAIN, down.offense, down.los)
    return Result(NEW_DOWN, down.offense, down.los, down.down, down.to_go, erased_score=_erased_score(play))


def is_minor(foul: F.Foul) -> bool:
    """14-5-1 Exception 1: a five-yard foul with no automatic first down, no loss of down, no run off and not a spot foul."""
    return foul.yards == 5 and not foul.automatic_first_down and not foul.loss_of_down and foul.spot != F.SPOT_OF_FOUL


def double_foul(first: F.Foul, second: F.Foul, down: Down, play: PlayFacts | None) -> tuple[Result, F.Foul | None]:
    """Fouls by both teams on one down: (the result, the foul enforced or None when they offset). No choice for either
    team (14-5-1). Both after the play: they offset and the play's result stands (14-4-9 Item 2)."""
    if F.AFTER in first.phases and F.AFTER in second.phases:
        return Result(PLAY_STANDS), None
    for major, minor in ((first, second), (second, first)):
        if major.yards == R.MAJOR_AGAINST_MINOR and is_minor(minor):
            new, moved, halved = move(down.los, major.yards, major.offense_side)
            if down.two_point:
                return Result(TRY_AGAIN, down.offense, new, yards=moved), major
            result = _downs_after(major, down, new, moved, halved)
            return replace(result, erased_score=_erased_score(play)), major
    return replay_down(down, play), None


def answers(foul: F.Foul, down: Down, play: PlayFacts | None, foul_spot: int | None = None) -> tuple[str, Result, Result]:
    """(how the offended team may answer, the result of accepting, the result of declining)."""
    if play is None:                              # a dead-ball foul before the snap (design 9.3: no prompt)
        same = Result(NEW_DOWN, down.offense, down.los, down.down, down.to_go)
        if down.two_point:
            same = Result(TRY_AGAIN, down.offense, down.los)
        return AUTO_ACCEPT, accept(foul, down, None), same
    declined = play_result(down, play)
    accepted = accept(foul, down, play, foul_spot)
    if down.two_point and ((declined.kind == TRY_GOOD and not foul.offense_side)
                           or (declined.kind == TRY_FAILS and foul.offense_side and accepted.kind != TRY_FAILS)):
        return AUTO_DECLINE, accepted, declined   # 11-3-3 Items 3 and 4: no try again for the team that fouled
    if play.turnover and foul.offense_side and foul.personal:
        return AUTO_DECLINE, accepted, declined   # 14-4-3 (b): the defense keeps the ball (its yards: not carried, D-050)
    if declined.kind == TOUCHDOWN and not foul.offense_side:
        if foul.personal:
            return ON_THE_TRY, accepted, declined
        if play.kind in (O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK) or enforcement_spot(foul, down, play, foul_spot) >= 100:
            return AUTO_DECLINE, accepted, declined
    return CHOICE, accepted, declined


# ----- the computer's choice (design 9.3; NFL_RULES_RESEARCH Part 6 section 8) -----

def _net_points(result: Result, side: int) -> float:
    if result.kind == TRY_AGAIN:                  # a try still to play: worth more than a failed one, less than a good one
        value = 1.0
        return value if result.ball == side else -value
    return result.points[side - 1] - result.points[other(side) - 1]


def _has_ball(result: Result, side: int) -> int | None:
    """1: `side` has the ball next, 0: the other side, None: a score or a try (the kick-off follows)."""
    if result.kind in (NEW_DOWN,):
        return 1 if result.ball == side else 0
    if result.kind == TURNOVER:
        return 1 if result.ball == side else 0
    return None


def better_for(side: int, a: Result, b: Result) -> Result:
    """The result `side` prefers (a on a tie): points first, then the ball, then a new series, then the field position
    (within FIELD_POSITION_TOLERANCE yards counts as equal), then the down and the distance."""
    pa, pb = _net_points(a, side), _net_points(b, side)
    if pa != pb:
        return a if pa > pb else b
    ha, hb = _has_ball(a, side), _has_ball(b, side)
    if ha is not None and hb is not None and ha != hb:
        return a if ha > hb else b
    if a.kind != NEW_DOWN or b.kind != NEW_DOWN:
        return a
    mine = a.ball == side                         # both have the same side with the ball here
    if a.new_series != b.new_series:
        return (a if a.new_series else b) if mine else (b if a.new_series else a)
    if abs(a.los - b.los) > T.FIELD_POSITION_TOLERANCE:
        return (a if a.los > b.los else b) if mine else (a if a.los < b.los else b)
    if (a.down, a.to_go) != (b.down, b.to_go):
        better_a = (a.down, a.to_go) < (b.down, b.to_go)
        return (a if better_a else b) if mine else (b if better_a else a)
    if a.los != b.los:
        return (a if a.los > b.los else b) if mine else (a if a.los < b.los else b)
    return a


def computer_accepts(side: int, accepted: Result, declined: Result) -> bool:
    return better_for(side, accepted, declined) is accepted


def takes_runoff(side: int, lead: int) -> bool:
    """The ten-second run off (4-7-1): a defense that leads or is tied lets the clock run; one that trails takes the
    yards only."""
    return lead >= 0


# ----- how a result is said (STRINGS_NX NXP-S) -----

ORDINAL_WORDS = {1: "first", 2: "second", 3: "third", 4: "fourth"}


def spot_words(ball: int, los: int, player: int = 1) -> tuple[str, int]:
    """(<side>, <yard>) of the original's position sentence: "your" for the player's own half, "my" for the other, "the"
    at midfield."""
    if los == 50:
        return "the", 50
    in_own_half = los < 50
    owner = ball if in_own_half else other(ball)
    return ("your" if owner == player else "my"), (los if in_own_half else 100 - los)


def distance_word(los: int, to_go: int) -> str:
    """" goal" when the ball is in the other half and the distance reaches the goal line (the engine's rule), else the
    number."""
    if los > 50 and to_go >= 100 - los:
        return "goal"
    return str(to_go)


def situation(result: Result, offense: int, player: int = 1) -> str:
    """The <situation> of NXP-04 and NXP-05 for one result, as the player hears it."""
    parts = []
    if result.erased_score == "touchdown":
        parts.append(X.text("NXP-S05"))
    elif result.erased_score in ("field goal",):
        parts.append(X.text("NXP-S07"))
    kind = result.kind
    if kind == NEW_DOWN:
        side, yard = spot_words(result.ball, result.los, player)
        if result.ball == offense:
            down = 1 if result.new_series else result.down
            to_go = 10 if result.new_series else result.to_go
            parts.append(X.text("NXP-S01", down=ORDINAL_WORDS.get(down, str(down)),
                                distance=distance_word(result.los, to_go), side=side, yard=yard))
        else:
            piece = "NXP-S03" if result.ball == player else "NXP-S02"
            parts.append(X.text(piece, side=side, yard=yard))
    elif kind == TOUCHDOWN:
        parts.append(X.text("NXP-S04"))
    elif kind == FIELD_GOAL:
        parts.append(X.text("NXP-S06"))
    elif kind == SAFETY:
        parts.append(X.text("NXP-S13"))
    elif kind == TURNOVER:
        if not result.pieces:
            parts.append(X.text("NXP-S11"))
    elif kind == TRY_GOOD:
        parts.append(X.text("NXP-S14"))
    elif kind == TRY_FAILS:
        parts.append(X.text("NXP-S15"))
    elif kind == TRY_AGAIN:
        parts.append(X.text("NXP-S16", yard=100 - result.los))
    elif kind == REPLAY_KICK:
        parts.append(X.text("NXP-S17"))
    else:
        parts.append(X.text("NXP-S10"))
    parts.extend(result.pieces)                   # "the fumble stands", "the half ends"
    if result.untimed:
        parts.append(X.text("NXP-S09"))
    return ", ".join(parts)


def turnover_piece(kind: str) -> str:
    """"the interception stands" for an interception, "the fumble stands" for a fumble (whatever play it ended)."""
    return X.text("NXP-S11") if kind == O.INTERCEPTION else X.text("NXP-S12")


__all__ = ["Down", "PlayFacts", "Result", "accept", "answers", "better_for", "computer_accepts", "double_foul",
           "half_distance", "move", "play_result", "replay_down", "situation"]
