"""Calibration values of the extras, each with its target (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 2 P4: the numbers marked "start value" in the design live here. A build session changes one only with a
recorded seeded simulation (DECISIONS.md). All ranges are whole seconds or whole percents, both ends included, drawn with
the one GameRandom (design 15).

SX.2 (the clock and the timeouts): the values below are the design's start values unless a line says what the
calibration of SX.2 (work/calibrate_clock_sx2.py, D-049) changed and why.
"""
from __future__ import annotations

# ----- the live time of a play, design 5.1 (seconds, low and high) -----
LIVE_RUN = (4, 7)                     # a run (or a keeper), in bounds or out of bounds
LIVE_PASS_COMPLETE = (5, 8)
LIVE_PASS_INCOMPLETE = (3, 7)         # the NFL's incomplete snap to snap: 3, 5, 7 at the 10th, 50th, 90th percentile
LIVE_SACK = (4, 8)
LIVE_TURNOVER = (5, 10)               # an interception or a fumble
LIVE_PUNT = (8, 12)
LIVE_FIELD_GOAL = (3, 5)              # never more than rules_2026.FIELD_GOAL_MAX_CLOCK
KICKOFF_RETURN_BASE = 3               # a return costs 3 + (return yards \ 10) + 0 to 3; a touch back costs 0 (4-3-1)
KICKOFF_RETURN_EXTRA = (0, 3)

# ----- out of bounds, design 5.2 (percent of the plays that end in the field of play) -----
OUT_OF_BOUNDS_RUN = 8                 # runs (play-by-play data 2024 to 2026, Part 9)
OUT_OF_BOUNDS_PASS_COMPLETE = 21      # completions

# ----- the runoff until the next snap, design 5.3 -----
RUNOFF_NORMAL = (30, 40)              # SX.2 calibration (D-049): 27 to 37 gave 25.1 seconds per counted play (band 26
#                                       to 30, 1,000 games); 3 seconds more, still within the 40-second play clock (4-6)
RUNOFF_HURRY = (12, 20)
RUNOFF_MILK = (37, 39)
READY_SIGNAL_CUT = (2, 5)             # a stop that restarts on the ready signal shortens the runoff
HURRY_SNAP_MIN = 6                    # a hurry-up offense snaps before time runs out when at least this many seconds are left
HURRY_FIRST_HALF = 120                # the offense hurries in the last 2:00 of the first half,
HURRY_TRAILING = 300                  # a trailing offense in the last 5:00 of the fourth quarter,
HURRY_TIED = 120                      # a tied one in its last 2:00,
HURRY_OVERTIME = 120                  # and every offense in the last 2:00 of an overtime period
MILK_LEADING = 480                    # a leading offense in the last 8:00 of the fourth quarter

# ----- what the computer reads through H1, design 5.6 -----
SECONDS_PER_PLAY = 38                 # plays_left = time left / 38, rounded up, at least 1
LAST_PLAY_RUNNING = 38                # "the last play of the period": at most 38 seconds with the clock running,
LAST_PLAY_STOPPED = 8                 # or at most 8 with it stopped

# ----- timeouts, design 6.3 -----
TIMEOUT_SIGNAL = (3, 8)               # u: the seconds of the pending runoff that run before a timeout is granted
TIMEOUT_REMARK_CHANCE = 3             # a remark of pool TO with chance 1 in 3 after a granted timeout
# the computer's rules (design 6.3, checked in H10 in this order)
RULE2_PENDING_OVER = 12               # rule 2: first half after the warning, the pending runoff is more than 12 seconds
#                                       (start value 10; SX.2: 1.87 timeouts per team in quarter 2, target 1.7),
RULE2_DRIVE_FROM = 30                 #   the side with the ball is on its own 30 or beyond;
RULE2_DEFENSE_INSIDE = 35             #   the defense: the offense inside its own 35
RULE2_DEFENSE_DOWN = 3                #   on third down or later
RULE3_TIED = 120                      # rule 3: fourth quarter, on offense when tied and under 2:00,
RULE3_TRAILING = 300                  #   or trailing and under 5:00;
RULE3_DEFENSE_BASE = 300              #   on defense when trailing and under 5:00 + 40 seconds for each timeout it holds
RULE3_DEFENSE_PER_TIMEOUT = 60        # start value 40; SX.2: 1.50 timeouts per team in quarter 4, target 1.7
RULE4_LAST = 120                      # rule 4: overtime, like rule 2 in the last 2:00 of the period
RULE6_CHANCE = 140                    # rule 6: quarters 1 and 3, a side with three timeouts calls one with chance 1 in 140
#                                       (start value 80; SX.2: 0.32 per team in quarters 1 and 3, target 0.2)

# ----- penalties, design 9 (SX.3) -----
PENALTY_RATE_SCALE = 1.2              # every rate of extras/fouls_2026.py is multiplied by this (the calibration of SX.3;
#                                       start value 1.0: 11.15 accepted fouls per game in 40 games; 1.24: 13.28 in 1,000;
#                                       band 12.0 to 13.6, target 12.8)
GROUNDING_PER_10000_SACKS = 170       # intentional grounding in place of a sack (design 9.2 P15). Start value 833 (1 in 12)
#                                       gave 1.03 groundings per game: the original's engine sacks about 12 times a game
#                                       (the NFL about 4.8); 170 aims at the NFL's 0.21 per game (Part 8)
DPI_LONG_FACTOR = 3                   # pass interference is three times as likely on a Long Pass as on a Short Pass,
DPI_SCREEN_FACTOR = 0                 #   never on a Screen Pass (design 9.2 P12)
ICT_SCREEN_FACTOR = 0                 # illegal contact never on a Screen Pass (P11)
RPS_BLITZ_FACTOR = 2                  # roughing the passer twice as likely against a Blitz (P14)
IDP_SCREEN_FACTOR = 3                 # ineligible receiver down field three times as likely on a Screen (P16)
SECOND_FOUL_CHANCE = 40               # after a foul, a foul by the other team too with chance 1 in 40 (design 9.1)
PENALTY_REMARK_CHANCE = 3             # a remark of pool PN with chance 1 in 3 after an accepted penalty (comments on)
# the spots that are drawn (design 9.1: "then, for a spot foul, its spot"), in yards from the line of scrimmage
DPI_DEPTH_SHORT = (5, 15)             # pass interference on a Short Pass: the depth of the throw
DPI_DEPTH_LONG = (15, 40)             #   on a Long Pass
RUN_FOUL_BEHIND = 2                   # a foul by the offense on a run: from 2 yards behind the line to the end of the run
GROUNDING_DROP = (5, 9)               # intentional grounding: the passer is 5 to 9 yards behind the line
RETURN_FOUL_REACH = 25                # a foul by the receivers on a kick-off return: within 25 yards behind its end
# the computer's choice (design 9.3): field positions within this many yards count as equal, then the down decides.
# SX.3: 3 gives 8.0 percent of the choices declined over 10,000 games (Part 8: 12 to 13, a plausibility check). 5 was
# tried (9.9 percent in 1,000 games) and not kept: it accepts an offside after a 9-yard gain (first and 5 over second and
# 1), which coaches decline; the clone's shortfall comes from the play mix (D-050)
FIELD_POSITION_TOLERANCE = 3

# ----- onside kicks, design 8 (SX.4) -----
LIVE_ONSIDE = (3, 5)                  # the clock's cost of an onside kick that is not returned (design 5.1); a return costs
#                                       the kick-off return's formula
ONSIDE_DISTANCE = (8, 14)             # the kick goes this far (2024 and 2025: mean 10.4, 10th to 90th percentile 7 to 14)
ONSIDE_RECOVERY_PERCENT = 8           # the kicking team recovers it: 8 of 113 declared kicks of 2024 to 2026 (7.1 percent), 2018
#                                       to 2023 8.7 percent (Part 9 section 4)
ONSIDE_RETURN_IN_100 = 4              # of the kicks the kicking team does not recover, the receivers pick it up and run with
#                                       this chance (design 8.3: 1 in 25) ...
ONSIDE_TOUCHDOWN_IN_100 = 1           # ... and 1 of those 100 failures is a touchdown (counted inside the 4)
ONSIDE_RETURN_YARDS = (5, 44)         # a return that does not score (never to the goal line: capped at the spot, design 8.3)
ONSIDE_REMARK_CHANCE = 3              # a remark of pool ON with chance 1 in 3 when a kick is declared (comments on)
# the player's question (design 8.2): the player's team trails in the third or fourth quarter, or leads by one score late
ONSIDE_LATE_SECONDS = 300             # "late": the last 5:00 of the fourth quarter
ONSIDE_LATE_LEAD = (1, 8)             # "one score": leads by 1 to 8 points
# the computer's declaration (design 8.4, start values): (trails by at least, at most, time left more than, at most,
# chance `a in b`), the first rule that fits decides, one draw `rnd(b) <= a`; never otherwise, never outside the fourth quarter
ONSIDE_COMPUTER_RULES = ((1, 999, 0, 120, 9, 10),      # any deficit with 2:00 or less: 9 in 10
                         (9, 999, 120, 300, 6, 10),    # 9 or more down with 2:00 to 5:00: 6 in 10
                         (9, 999, 300, 600, 1, 4))     # 9 or more down with 5:00 to 10:00: 1 in 4
# SX.4 calibration (D-051, work/calibrate_onside_sx4.py): the design's start values (1 to 16 down in the last 2:00, 17 or
# more down with 5:00 to 10:00) gave 0.133 kicks a game in 400 games (0.155 expected from the opportunities of the engine's
# own games: 0.72 trailing kick-offs a game in the fourth quarter) against the NFL's 0.19 (2024 and 2025: 102 kicks in 544
# games, 20 of them more than 16 down, 14 with 5:00 to 10:00 left, Part 9 section 4). Two moves, each from those counts: the
# first rule has no upper limit on the deficit (the 17 or more down also try it in the last 2:00) and the third rule starts
# at 9 down (the NFL's 5:00 to 10:00 kicks are not only 17 down). Result in 10,000 games: 0.174 kicks a game (the NFL's
# 0.14 in 2026 to week 5 and 0.19 in 2024 and 2025), 58, 30 and 12 percent of them with up to 2:00, 2:00 to 5:00 and 5:00
# to 10:00 left (NFL 54, 29, 14 and 3 percent with more), the team behind by 1 to 8 only 28 percent of the kicks (NFL 42:
# the engine's games are more often decided by more than a score), 8.2 percent kept (design 8, NFL 6.0 and 9.6).

# ----- a Classic save loaded in N. F. L. rules mode, design 12.3 -----
SAVE_SECONDS_PER_COUNTED_PLAY = 28    # the clock at 15:00 minus 28 seconds per counted play,
SAVE_LEAST_LEFT = 60                  # at least 1:00

# ----- the targets of the calibration (design 4 and 5.7; used only by the tests and the calibration script) -----
TARGET_PLAYS_PER_QUARTER = (29, 36)          # counted plays per regulation quarter (the original's range, C2)
TARGET_LATE_QUARTER_EXTRA = (2, 7)           # quarters 2 and 4 carry this many more than 1 and 3 (NFL about 5)
TARGET_SECONDS_PER_PLAY = (26, 30)           # seconds per counted play
TARGET_TIMEOUTS_PER_TEAM_GAME = 3.85         # charged timeouts per team per game (Part 1.6)
TARGET_TIMEOUTS_Q1_Q3 = 0.2                  # per team in quarter 1 and in quarter 3
TARGET_TIMEOUTS_Q2_Q4 = 1.7                  # per team in quarter 2 and in quarter 4
TARGET_ACCEPTED_FOULS_PER_GAME = (12.0, 13.6)   # both teams (design 4, N7.7: 12.8 plus or minus 0.8, 2024 and 2025)
TARGET_DECLINED_SHARE = (0.10, 0.15)            # of the fouls that offer a choice (Part 8 section 6: 12 to 13 percent;
#                                                 a plausibility check of the computer's rule, not a target it is tuned to)
TARGET_PRE_SNAP_SHARE = (0.30, 0.45)            # of the accepted fouls (Part 8: 37 to 39 percent)
TARGET_ONSIDE_PER_GAME = (0.12, 0.27)           # onside kicks tried per game, both teams (NFL 0.19 in 2024 and 2025, 0.14 in
#                                                 2026 to week 5, Part 9 section 4); all in the fourth quarter by the team behind
TARGET_ONSIDE_RECOVERED = (0.06, 0.10)          # the share the kicking team keeps (6.0 percent 2024, 9.6 percent 2025)
