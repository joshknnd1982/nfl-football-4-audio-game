"""The rules table nfl_rules_2026: the NFL's own numbers, each with its rule (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 4 (P3: rules are data). Every value is SRC-OFFICIAL from the 2026 rulebook (spec/NFL_RULES_RESEARCH.md
Part 1 and Part 2) unless marked; a citation is Rule-Section-Article. These numbers never move in a calibration: the values
a build session tunes are in extras/tuning.py. A later rule year is a new module chosen by one setting value. SX.2 wrote
the groups it uses (clock and periods, timeouts); each later session adds the group of its feature.
"""
from __future__ import annotations

YEAR = 2026

# ----- clock and periods -----
QUARTER_SECONDS = 900                  # 4-1: four periods of 15 minutes
WARNING_SECONDS = 120                  # 3-41: the two-minute warning
WARNING_QUARTERS = (2, 4)              # 3-41: the second and fourth periods; an automatic timeout charged to nobody, 4-4(h)
OT_REGULAR_PERIOD_SECONDS = 600        # 16-3: one period of 10 minutes in the regular season
OT_POST_PERIOD_SECONDS = 900           # 16-4: periods of 15 minutes in the play-offs
# overtime warnings (SRC-SECONDARY practice, Part 1.2 default): at 2:00 of every regular-season overtime period, and of
# play-off overtime periods 2 and 4 (the clone's sudden-death periods go on: every second one)
OT_POST_WARNING_EVERY = 2
LATE_FIRST_HALF_SECONDS = 120          # 4-3-2: in the last 2:00 of the first half a runner out of bounds stops the clock
FIVE_MINUTE_RULE_SECONDS = 300         # 4-3-2(a)(3), 4-3-2(e)(2): the last 5:00 of the second half; overtime alike (Part 1.5)
PLAY_CLOCK = 40                        # 4-6: bounds the runoff ranges only
FIELD_GOAL_MAX_CLOCK = 5               # 11-4-2 Note 5: a field goal attempt runs at most 5 seconds off
TRY_UNTIMED = True                     # 4-3-2(h), 11-3-1: the extra point and the two-point try take no time

# ----- timeouts -----
TIMEOUTS_PER_HALF = 3                  # 4-5-1 Item 1: three charged timeouts each half, no carry-over
OT_REGULAR_TIMEOUTS = 2                # 16-3-e: two in the regular-season period (the clone: again at every new period)
OT_POST_TIMEOUTS = 3                   # 16-4-g: three per pair of play-off overtime periods (SRC-SECONDARY reading)
ONE_CHARGED_TIMEOUT_PER_DEAD_BALL = True   # 4-5-1 Item 3
# A request with no timeout left is ignored (4-5-1 Item 3): the clone's menu refuses it with a sentence and never grants
# it, so the delay-of-game foul for a granted excess timeout and the foul of 4-5-1 Item 4 cannot arise (design 4).

# ----- penalties (SX.3; the fouls themselves are extras/fouls_2026.py; NFL_RULES_RESEARCH Part 6) -----
HALF_DISTANCE = True                   # 14-2-1: never more than half the distance from the spot of enforcement to the
#                                        offender's goal line; not for the spot fouls (pass interference, 8-5) nor for
#                                        intentional grounding at the spot of the pass (8-2-1). The clone has whole yards
#                                        only: the ball moves half the distance rounded down, so it stays on the 1 (Part
#                                        1.5 default: never on or behind the goal line)
NO_AUTOMATIC_FIRST_DOWN = ("DOF", "ENC", "NZI", "DOG", "DOD", "ILS", "EXT", "RNK", "DTM", "DIF")
#                                        14-1-2 Item 5: offside, encroachment, neutral zone infraction, delay of game,
#                                        illegal substitution, excess timeout, running into the kicker, more than 11 at the
#                                        snap or in the formation, the defense's illegal formation on a scrimmage kick; every
#                                        other foul by the defense gives a first down
FIRST_DOWN_ONLY_PAST_THE_LINE = True   # 14-1-2 Item 4: a foul by the offense gives a first down only when the ball ends
#                                        beyond the line to gain (Part 1.5 default for the ball exactly on it)
DPI_GOAL_LINE_SPOT = 1                 # 8-5: pass interference in the end zone is a first down on the 1 (halfway to the
#                                        goal line when the previous spot is inside the 2)
GROUNDING_YARDS = 10                   # 8-2-1: loss of down and 10 from the previous spot, or at the spot of the pass when
#                                        that is worse for the offense; a safety when the passer is in his own end zone
RUNOFF_SECONDS = 10                    # 4-7-1: an offense foul that stops a running clock after the two-minute warning of
#                                        either half: ten seconds off, the defense may take the yards only; never against
#                                        the defense (4-5-4 Note 9); the clock then starts on the ready signal (4-3-2 (g))
NO_RUNOFF_FOULS = ("DOG",)             # 4-7-1 does not list delay of game (Part 6 5.3, Part 1.5 default: no run off)
PLAY_CLOCK_AFTER_PENALTY = 25          # 4-6-2 (e), 4-6-3: after a penalty the play clock is 25; it bounds the runoff
RUNOFF_PLAY_CLOCK = 30                 # 4-6-3 (c): after a ten-second run off the play clock is 30
UNTIMED_DOWN = True                   # 4-8-2 (a): an accepted foul by the defense on the last play of a half gives the
#                                        offense one untimed down
ONE_PENALTY_PER_TEAM = True            # 14-1-3: the offended team chooses one penalty of a multiple foul
DOUBLE_FOUL_REPLAY = True              # 14-5-1: fouls by both teams offset and the down is played again (no choice);
MAJOR_AGAINST_MINOR = 15               # Exception 1: a 15-yard foul against a 5-yard foul with no automatic first down,
#                                        loss of down or run off is enforced alone
