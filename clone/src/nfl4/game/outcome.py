"""The record of one play's result (nfl4 hook H2). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 3 H2: a play is (1) choose, (2) `before_snap`, (3) snap, resolve and narrate exactly as the original
(GAME_SPEC 5.8 to 5.10, every draw, sentence, sound and pause in its order) up to the NARRATION END POINT of its kind of
result, which yields this record, (4) `after_outcome(outcome)`, (5) apply (5.11 and 5.12). The end points, where the
engine calls the hook:
* a run, pass or sack that ends in the field of play: after the gain, loss or no-gain sentence of 5.11 item 3, before the
  downs (a two-point try: before its result);
* a touchdown: after the run countdown or the catch sentence, before " TOUCH DOWN" (a two-point try: before its result);
* a safety: after the tackle or sack sentence and foot5, before " in the end zone for a safety";
* an interception or a fumble: after its sentence and sound, before the turnover spot and the possession sentence;
* a field goal: after its result sentence, foot12, the log flag and foot11, before the points (" is way to short": after
  that sentence, before the possession sentence);
* a punt: after its last sentence and foot11 (and " IT IS A TOUCH BACK"), before the possession sentence;
* a kick-off: a touch back after its sentence, foot11 and the crowd ramp, before the position sentence; a return like a
  run in the field of play.
The speech, sounds and pauses up to the end point are not replayed from the record: they have happened. In Classic the
hook returns the record unchanged and the engine goes on as the original does.
"""
from __future__ import annotations

from dataclasses import dataclass

RUN, PASS_COMPLETE, PASS_INCOMPLETE, SACK = "run", "pass complete", "pass incomplete", "sack"
INTERCEPTION, FUMBLE = "interception", "fumble"
FIELD_GOAL_GOOD, FIELD_GOAL_MISSED, FIELD_GOAL_SHORT = "field goal good", "field goal missed", "field goal short"
PUNT, KICKOFF_RETURN, KICKOFF_TOUCH_BACK = "punt", "kick-off return", "kick-off touch back"
TOUCHDOWN, SAFETY_KIND, TWO_POINT_TRY = "touchdown", "safety", "two-point try"


@dataclass
class PlayOutcome:
    kind: str
    offense: int                       # the side with the ball at the snap (wisoff)
    offense_play: int                  # L1d4 (0 for a kick-off)
    defense_play: int                  # L1c4
    yards: int = 0                     # L32c
    carrier: int = 0                   # L408 (the returner's number for a kick-off)
    defender1: int = 0                 # L578
    defender2: int = 0                 # L664
    turnover: bool = False
    score: str | None = None           # "touchdown", "field goal", "safety", "two-point" or None
    spot_before: tuple[int, int] = (0, 0)    # (half, yard line) at the snap
    two_point_try: bool = False
    # the ruling fields that only the extras fill (NFL_EXTRAS_DESIGN 6.1); empty in Classic
    ruling: object = None
    # what the engine does next when the extras took over the end of the play (game/rules.py NEXT_DOWN and the others;
    # SX.3, an accepted penalty); None in Classic: the engine goes on as the original
    then: str | None = None
