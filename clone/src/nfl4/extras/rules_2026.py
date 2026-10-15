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
