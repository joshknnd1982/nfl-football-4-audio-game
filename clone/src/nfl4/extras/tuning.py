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

# ----- quarterback runs, design 7 (SX.5) -----
# The rows of the three plays and the scramble, one entry per defense call (Goal Line, Short Run, Long Run, Blitz, Short Pass,
# Long Pass; design 7.1, start values): the fewest and the most yards (both ends included, uniform whole numbers), then the
# chances. Yards are drawn like the original's runs: Int(Rnd * (most - fewest + 1)) + fewest.
QB_ROWS = {
    "sneak": ((0, 2), (0, 3), (1, 4), (-1, 3), (1, 4), (1, 5)),
    "keeper": ((-2, 6), (-3, 5), (-4, 3), (-3, 15), (3, 12), (4, 14)),
    "draw": ((-1, 3), (-2, 3), (1, 6), (4, 16), (2, 9), (3, 12)),
}
QB_SCRAMBLE_YARDS = (1, 14)           # the scramble has one row for every defense call: mean 7.5 (NFL 7.67)
QB_FUMBLE_ODDS = {"sneak": 100, "keeper": 90, "draw": 90, "scramble": 200}     # a fumble lost: 1 in this many
QB_OUT_OF_BOUNDS = {"sneak": 0, "keeper": 12, "draw": 5, "scramble": 34}       # percent of the runs that go out of bounds
QB_SOUND = {"sneak": 1, "keeper": 3, "draw": 3, "scramble": 2}                 # the original's PlayTackle numbers (foot4 to foot6)
QB_SCRAMBLE_FROM_SACK = 22            # percent: the original's sack becomes a scramble (design 7.1; one draw below(100) < this)
QB_SCRAMBLE_FROM_INCOMPLETE = 6       # percent: the original's incompletion (before the throw sentence) becomes a scramble
LIVE_SCRAMBLE = (5, 9)                # the live time of a scramble (design 5.1); a sneak, keeper or draw takes a run's LIVE_RUN
QB_SLIDE_MIN_YARDS = 8                # a keeper, draw or scramble that gained this many yards and did not score may slide ...
QB_SLIDE_ONE_IN = 2                   # ... with this chance (1 in 2, one draw rnd(2) = 1)
QB_SLIDE_CUT = (0, 2)                 # a slide cuts the gain by 0 to 2 yards (design 7.3)
QB_LATE_HIT_ONE_IN = 40               # a late hit on the slider (P18) with chance 1 in 40 of the slides, penalties on
QB_COMPUTER_SNEAK = (1, 2)            # the computer: third or fourth and 1 or 2: a sneak with chance 1 in 2 (design 7.4)
QB_COMPUTER_SHORT = 2                 # "short" yardage: this many yards to go or fewer
QB_COMPUTER_OTHER_ONE_IN = 150        # downs 1 to 3 otherwise: one draw rnd(this): 1 a keeper, 2 a draw (design 7.4)

# ----- the ruling model, challenges and booth reviews, design 6 (SX.6) -----
# The ruling on the field is what the engine narrated. A play with a reviewable aspect (design 6.1, extras/review.py) draws once,
# `below(1000)`, over its categories: the wrong windows first, then the close ones. (wrong, close) per 1000 eligible plays:
RULING_RATES = {"catch": (6, 17),         # a completion called incomplete or the reverse: 0.6 and 1.7 percent of the passes
                "fumble": (80, 135),      # a fumble called down before the fumble: 8 and 13.5 percent of the fumbles
                "down": (2, 0),           # a tackle called a fumble, the reverse: 0.2 percent of the runs and the catches
                "goal": (60, 135),        # a run or catch within 2 yards of the goal line, called on the wrong side
                "line": (30, 100),        #   within 1 yard of the line to gain
                "boundary": (5, 17)}      # a catch called out of bounds or in bounds
BOOTH_PLAY_WRONG_FACTOR = 2               # a play of the replay official's own (a score, a turnover, a failed fourth down, the last
#                                           two minutes, overtime: 15-1-2) is wrong this many times as often (the wrong windows
#                                           only): the ball is on the line there and every ruling is seen by the booth, which is why
#                                           the NFL's booth reviews change the ruling 74 to 78 percent of the time (design 6.2)
GOAL_REACH = 2                            # the goal line category: the ball ends within this many yards of it
LINE_REACH = 1                            # the line to gain category: the ball ends within this many yards of it
RULING_CLEAR_PERCENT = 85                 # a wrong ruling shows as clear and obvious on the replay with this chance (15-2-1)
HINT_STRONG_PERCENT = 70                  # after a wrong ruling the announcer hints (pool CHS) with this chance ...
HINT_CLOSE_PERCENT = 50                   # ... after a close one (pool CHC)
BOOTH_CLOSE_PERCENT = 14                  # the replay official reviews a close ruling of a play of his own with this chance
#                                           (a wrong one always: he "initiates when there is doubt", design 6.2)
COMPUTER_CHALLENGE_STRONG_PERCENT = 80    # the computer's coach throws the flag after a strong hint with this chance ...
COMPUTER_CHALLENGE_CLOSE_PERCENT = 30     # ... after a close-call hint
# SX.6 calibration (D-053, work/calibrate_review_sx6.py): the design's start values (the close rates 10, 80, 0, 80, 60 and 10, no
# factor for a booth play, the booth's chance on a close ruling 7 percent, the computer's flag after a strong hint 70 percent)
# gave, in 200 games with both sides played by the computer, 0.198 coach challenges per team per game (NFL 0.24 to 0.28) that
# changed the ruling 53.2 percent of the time (NFL 38 to 52), and 0.32 replay official reviews a game (NFL about 0.65) that changed it
# 82.8 percent (NFL 74 to 78). The two targets share the rates, so two knobs were found: the replay official's plays (a score, a
# turnover, a failed fourth down, the last two minutes, overtime: the NFL's booth finds the ruling wrong 74 to 78 percent of the time
# it stops the game) have their wrong windows doubled, and the close rates are 1.7 times the design's (more rulings that were right but
# close, which are what the coaches lose on); the booth's chance on a close ruling is 14 percent and the computer's flag after a
# strong hint 80 percent. Result in 3,000 games (before the review's fixes): 0.274 coach challenges per team per game, 48.1 percent
# changed the ruling, 76 / 21 / 3 percent of the team-games with 0 / 1 / 2 challenges (NFL 77 / 21 / 2), 0.681 reviews a game, 74.7
# percent changed. Final, in 10,000 games on the code after the independent review's fixes (work/calibrate_review_sx6_10000.txt):
# 0.270 coach challenges per team per game, 51.0 percent changed the ruling, 76.4 / 20.4 / 3.0 / 0.2 percent of the team-games with
# 0 / 1 / 2 / 3 challenges (NFL 77 / 21 / 2 / 0.3), 0.682 reviews a game, 74.5 percent changed; 3.65 charged time outs per team per
# game (SX.2 had 3.76: a lost challenge is a time out and a coach keeps one in hand for a flag).
REVIEW_PAUSE = 2.0                        # seconds: the referee under the hood (design 6.4), then two rady pauses
REVIEW_REMARK_ONE_IN = 2                  # a remark of RVR or RVC after a review with chance 1 in 2 (comments on)

# ----- the playbooks, design 10 (SX.7) -----
# The computer's weighted draw over a style's plays (design 10.4, N5.6): a play's weight (playbook_data.py, styles.txt) times
# the percent of its family in the situation, each in whole percents (100 = no change). One draw, `below(total)`.
PB_SHORT_YARDS = 2                    # "short": this many yards to go or fewer
PB_LONG_YARDS = 8                     # "long": this many yards to go or more
PB_RED_ZONE = 10                      # "red zone": the ball is this many yards from the goal line or closer
PB_LATE_SECONDS = 300                 # "late": the fourth quarter or overtime with this many seconds left or fewer
PB_LATE_MARGIN = 8                    # "trailing" or "leading" late: by at least this many points (a trailing offense needs the
#                                       pass, a leading one the run)
PB_SITUATION_STRENGTH = 100           # percent of the factors below that count (0: the weights alone, the balance test's knob)
PB_DISTANCE_PERCENT = {"short": {1: 150, 2: 100, 3: 60, 4: 80, 5: 50},
                       "long": {1: 60, 2: 60, 3: 140, 4: 120, 5: 140}}
PB_RED_ZONE_PERCENT = {1: 130, 2: 90, 3: 100, 4: 100, 5: 70}
PB_LATE_TRAILING_PERCENT = {1: 50, 2: 50, 3: 100, 4: 140, 5: 160}
PB_LATE_LEADING_PERCENT = {1: 140, 2: 140, 3: 60, 4: 70, 5: 40}
# SX.7 calibration (D-054, work/calibrate_playbooks_sx7.py): the design's start values (the situation's distance counted from the first
# down, uncentered plays) gave Pro Style, the control group, 53 to 55 percent against Classic and Power Run 60; three moves, each from a
# measurement: the plays' own tilts were centered with the expected-yards yardstick of tests/playbook_ev.py, the distance counts from the
# second down, and the family masses and tilts of the styles (playbook_data.py MASS and the tilts) were reset. Result in 10,000 games per
# style against Classic, the side alternating (work/calibrate_playbooks_sx7_10000.txt): Pro Style 51.3, West Coast 50.0, Air Raid 49.9,
# Power Run 52.3, Zone Run 50.8, Option 51.1 and Pressure 52.4 percent, Classic against Classic 50.0 (the error is 0.5; design 10.3's band
# is 45 to 55). PB_SITUATION_STRENGTH stays 100.

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
TARGET_QB_DESIGNED_PER_TEAM_GAME = (1.0, 1.6)   # designed quarterback runs per team per game (NFL 1.29, Part 1.6)
TARGET_QB_DESIGNED_YARDS = (3.2, 4.2)           # their mean yards (NFL 3.66)
TARGET_QB_SCRAMBLE_SHARE = (0.045, 0.065)       # scrambles as a share of the drop-backs (design 7.1: about 5.4 percent)
TARGET_QB_SCRAMBLE_YARDS = (7.0, 8.2)           # their mean yards (NFL 7.67; a slide cuts a little)
TARGET_QB_SHORT_CONVERSION = (0.78, 0.88)       # third or fourth and 1, a designed quarterback run: first down or touchdown
#                                                 (NFL 83.4 percent)
TARGET_PLAYBOOK_WIN = (0.45, 0.55)                      # every style against Classic wins this share of the games (design 10.3)
TARGET_COACH_CHALLENGES_PER_TEAM_GAME = (0.20, 0.32)    # coach challenges per team per game (NFL 0.24 to 0.28, Part 3 section 7)
TARGET_CHALLENGE_REVERSED = (0.38, 0.52)                # the share that changed the ruling (NFL 38 to 52 percent)
TARGET_BOOTH_PER_GAME = (0.50, 0.80)                    # replay official reviews per game, both teams (NFL about 0.65)
TARGET_BOOTH_REVERSED = (0.70, 0.82)                    # the share that changed the ruling (NFL 74 to 78 percent)

# ----- the Franchise (NFL_FRANCHISE_DESIGN, SX.8): start values of a new league, design 4.5; later sessions add theirs here -----
FR_TEAM_LEVEL_LOW, FR_TEAM_LEVEL_SPAN = -2, 5        # a team's level: below(5) - 2, so -2 to +2 (SX.8b: the design's -4 to +4, below(9) - 4, gave a
#                                                      first season whose strengths spread 2.8 points a standard deviation against about 1.4 once the
#                                                      rosters had evened out, so the first season's effect was not the later seasons'; -2 to +2 starts at
#                                                      1.8 and settles at 1.4 to 1.6, work/calibrate_ratings_sx8b_fast_*.txt)
FR_RATING_BASE, FR_RATING_DRAW = 58, 13              # a rating: 58 + below(13) + below(13) + the level (58 to 82 before the level)
FR_POTENTIAL_SHARES = (20, 70)                       # below(100): under 20 high, under 70 average, else low
FR_START_AGE = (21, 5, 5, 4)                         # an age: 21 + below(5) + below(5) + below(4); a kicker or punter below(5) more
FR_START_AGE_KICKER = 5

# ----- the ratings' bounded effect, design 5.1 and 5.2 (SX.8b; the history of every move is below) -----
# In a game the player plays: step(x, per, cap) = sign(x) * min(cap, |x| // per) of the gap d between the offense's rating (the
# ball carrier's, or two thirds quarterback and one third receiver) and the defense's (the two tacklers' mean), added to the playbook's
# Mod and clamped to the playbooks' bounds (playbook_data.BOUNDS). Each pair is (per, cap).
FR_YARD_STEP = (4, 1)             # yards low and high together, up or down (design start value (12, 1))
FR_SACK_STEP = (2, 3)             # the sack percent (the other way: a better offense is sacked less) (design (6, 3))
FR_COMP_STEP = (2, 3)             # the catch percent (design (6, 3))
FR_FUM_STEP = (3, 3)              # the fumble denominator (a better offense fumbles less) (design (8, 3))
FR_TEAM_EDGE = (5, 2)             # numerator and denominator: 5 / 2 = 2.5 TIMES the two teams' strength gap, in rating points of the weighted
#                                   mean (design 4.4), is added to every play's gap d (design start value: none; added in SX.8b, D-057)
FR_KICK_STEP = (5, 5)             # the field goal's odds around 70, from the kicker's rating around 70
FR_PUNT_STEP = (8, 3)             # the shortest punt around 25 yards, from the punter's rating around 70
# In the computer's games: the team's place in its league (z, the exact strength against the league's mean and spread) moves the
# index into the score table, and leans the play-off coin.
FR_SHIFT_MAX = 10                 # most places a team's score index moves (design start value 6)
FR_SHIFT_PER_SD = 5               # places per standard deviation of the league's strengths (design start value 3)
FR_SPREAD_FLOOR = 78              # the least spread counted, in the weighted sum (78 is one rating point of strength)
FR_PLAYOFF_PER_SD = 150           # per mille of lean of the play-off coin per standard deviation of the gap between the teams (design 60)
# SX.8b calibration (D-057; the reports are work/calibrate_ratings_sx8b_*.txt, the scripts work/calibrate_ratings_sx8b.py,
# work/sim_league_sx8b.py and work/regular_week_share_sx8b.py). The design's start values gave a win spread of 2.36 to 2.41 wins a
# season in the fast run (500 leagues of 20 seasons; target 2.6 to 3.4, the NFL's 3.0 a season;
# work/calibrate_ratings_sx8b_fast_500x20_design_values.txt), because the lean of the computer's games is the whole of the spread
# (z has a spread of 1 by construction, so wins vary by sqrt(4 + 256 c^2) for a lean c of the win share per standard deviation):
# 5 places a standard deviation (10 at most) gives a mean win spread over the 500 leagues of 2.82 to 2.88 in each of the 20 seasons
# (a single league's season varies, 2.1 to 3.8: wins of 16 games are noisy; work/calibrate_ratings_sx8b_fast_500x20.txt).
# The played games could not follow: with the design's steps the stronger team won 0.51 to 0.53 of the games at gaps of 1.3 to 3.6
# rating points where the regular week gives 0.62 to 0.77 (work/calibrate_ratings_sx8b_played_2000_design_values.txt). Finer steps
# (the caps, 1 yard and 3 points, are the design's) and a team edge (every play's gap counts 2.5 times the two TEAMS' strength
# gap as well, so the signal is not lost in the noise of the individual players, which saturate the caps) bring them within 0.03
# of it at the spreads of seasons 1, 5 and 10: the stronger team won 0.666, 0.672 and 0.701 at one standard deviation (the
# regular week 0.672) and 0.760, 0.769 and 0.792 at two (0.769) in 10,000 games a gap (work/calibrate_ratings_sx8b_played_10000.txt).
# Centering (C-F3), 10,000 games a line: points a game +0.87 percent with the Classic playbooks and +0.94 percent with the styles,
# yards a play -0.01 and +0.19 percent (work/calibrate_ratings_sx8b_centering_10000.txt). The play-off lean is set to the regular
# week's share (0.67 at 1 standard deviation, 0.77 at 2; the lean is capped at 0.75).

# ----- aging, retirement, progression and regression, design 6 and 8.2 (SX.8c; the history of every move is below) -----
# Retirement (stage 2, after everybody is a year older): a player of 30 or more draws below(1000) against
# r = clamp((age - 29) * FR_RETIRE_PER_YEAR - (rating - 70) * FR_RETIRE_PER_POINT, 0, 1000); at 40 he retires without a draw.
FR_RETIRE_PER_YEAR = 110          # per mille of retirement chance for each year of age over 29
FR_RETIRE_PER_POINT = 6           # per mille taken off for each rating point over 70 (and put on for each under it)
# Progression and regression (stage 3): change = base(position, age, potential) + below(5) - 2 + the development points.
FR_PEAK = {"RB": (24, 28), "WR": (25, 29), "QB": (24, 30), "DL": (25, 29), "LB": (25, 29), "CB": (25, 28), "S": (25, 29),
           "RET": (24, 28), "K": (24, 34), "P": (24, 34)}     # the first and the last age of a group's peak window
#                                 (design start values: RB 24-27, QB 26-32, RET 24-27, K and P 26-34; see the history below)
FR_GROWTH = (4, 2, 1)             # before the window, by potential (high, average, low) (design start value (5, 3, 1))
# FR_IN_WINDOW and FR_PROGRESS_NOISE are design RULES (6.2 gives them no start-value mark), not calibration knobs; FR_DECLINE is a start value
FR_IN_WINDOW = (1, 0, 0)          # in the window, by potential
FR_DECLINE = (2, 3, 4, 5, 6, 6)   # after the window: the k-th year after it takes this many points, whatever the potential
FR_PROGRESS_NOISE = (5, -2)       # below(5) - 2: the yearly spread, -2 to +2
# The fill of an empty place with an undrafted rookie (design 7.6; stage 5 since SX.8d, a stand-in at the end of stage 3 in SX.8c):
# rating base + below(span) in a group of three places or more, the second pair in a group of one or two.
FR_FILL_RATING = (45, 11)
FR_FILL_RATING_SMALL = (50, 11)
FR_ROOKIE_POTENTIAL_SHARES = (25, 75)       # below(100): under 25 high, under 75 average, else low
# SX.8c calibration (D-058; the reports are work/calibrate_aging_sx8c_fast_*.txt, the scripts work/sim_league_sx8c.py and
# work/calibrate_aging_sx8c.py, the sweeps work/calibrate_aging_sx8c_sweeps/). The fast run (500 leagues x 20 seasons, the real stages 2
# and 3, stand-ins for the draft, the cut and the four weeks of extra work) at the design's start values drifted: the league's mean
# rating rose to 72.0 by season 12 (band 68 to 72) and the quarterbacks' mean to 76 to 78.7 (band 64 to 76; 58 percent of the league-
# seasons outside it, single leagues up to 84) (work/calibrate_aging_sx8c_fast_500x20_design_values.txt). Two causes, each moved by its
# own knob: (1) the growth before the window was too fast for the rookies the draft brings (a class of 46 to 74, mean 60): (4, 2, 1) in
# place of (5, 3, 1) holds the mean rating at 69.1 to 70.8; (2) a position whose window starts late grows for more years before it
# peaks (nobody develops before 22: rookies join after the development stage), so the quarterbacks (window 26 to 32, four years of
# growth) peaked about five points above a running back (two years): the quarterbacks' window now starts at 24 (two years of growth)
# and still ends at 32, so a quarterback in his early thirties holds as research B6 says, and the running backs' and returners' windows
# end at 28 (their mean was 67 to 68 and single leagues went down to 62). FR_PEAK is not in the knob list design 16 gives SX.8f; it is
# moved here by decision D-058, which changes design 6.2's windows. The result over 10,000 league-seasons: the mean over the leagues
# is inside its band in every one of the 20 seasons (mean rating 69.1 to 70.8, mean age 25.8 to 26.8, every group 67.0 to 73.8), the
# win spread 2.81 to 2.88 (C-F1 holds), no single league-season has a mean rating or a mean age outside its band, and 11.2 percent of
# the league-seasons have one group mean outside 64 to 76 (the kickers 5.4 percent, the punters 4.4, the quarterbacks 2.0, the
# returners 0.2): the single-place groups follow a cohort and the stand-in cut's ratchet; the retirement values were tried
# (work/calibrate_aging_sx8c_sweeps/) and left at the design's (110, 6) because a rule that is right is not moved to meet an aggregate
# (B-P56): SX.8d's real cut and SX.8f's per-run invariant are where the tails are settled. (SX.8c: its build alone did not keep these
# bands, because until the draft existed stage 3 filled every empty place with an undrafted rookie rated 45 to 60 and the mean fell from
# 69 to 55 in ten seasons; the calibration ran a stand-in draft and cut. SX.8d replaced the stand-ins: see the draft group below.)

# ----- the draft, the roster cut and the fill, design 7 (SX.8d; the history of every move is below) -----
# The draft class (made at the start of stage 4): FR_CLASS_SIZE prospects; each one's position by below(sum of the weights), the true rating
# base + below(span) + below(span), the potential from FR_ROOKIE_POTENTIAL_SHARES (above), the age base + below(span), and the scouting
# offset below(FR_SCOUT_SPAN), which places the true rating inside the spoken range (low end = true - offset, high end = low end + 6).
FR_CLASS_SIZE = 260
FR_CLASS_WEIGHTS = (("RB", 6), ("WR", 6), ("QB", 2), ("DL", 6), ("LB", 5), ("CB", 4), ("S", 2), ("RET", 2), ("K", 1), ("P", 1))
FR_ROOKIE_RATING = (46, 15)                  # 46 + below(15) + below(15): 46 to 74, mean 60
FR_ROOKIE_AGE = (21, 3)                      # 21 + below(3)
FR_SCOUT_SPAN = 7                            # the offset below(7): the true rating lies 0 to 6 above the low end of the spoken range
# What a team's pick values (design 7.3): the middle of the range + the potential bonus + the need bonus, its parts added.
FR_DRAFT_POTENTIAL = {"high": 5, "average": 0, "low": -4}
FR_DRAFT_VALUE = {"need": 8, "need_quarterback": 12, "better": 3, "surplus": -10}   # an open place; the same for a quarterback; the
#                                            prospect's middle beats the group's lowest rating; a K, P or RET for a group with no open place
FR_DRAFT_WEAK = 60                           # a group of one place counts as open also when its best player is under this rating
# The roster cut (design 7.6): a player's keep value = rating + this bonus when he is FR_KEEP_YOUTH_AGE or younger.
FR_KEEP_YOUTH = {"high": 4, "average": 2, "low": 0}
FR_KEEP_YOUTH_AGE = 24
# In a group of one or two places (quarterback, kicker, punter, safeties, returners) one weak player is the whole group, so a player under this
# rating is released at the cut even with no surplus, and the fill (rated 50 or more there) takes his place: invariant I5 (D-059).
FR_CUT_FLOOR = 50
# SX.8d calibration (D-059; the reports are work/calibrate_draft_sx8d_fast_500x20.txt and ..._build_alone.txt, the scripts
# work/sim_league_sx8d.py and work/calibrate_draft_sx8d.py, the whole-program run work/build_alone_sx8d.py). The design's start values were
# kept: not one of the draft values above moved. Two additions, each from a measurement of the first run (20 leagues x 20 seasons): (1) in
# 6.5 percent of the league-seasons some team had a position group with a mean under 50 (invariant I5): kickers and punters whose only
# candidate was a late-round prospect rated 46 to 49, and returners left at 42 to 47 by the decline; the fill (rated 50 to 60 in a group of
# one or two places) is better than they are but only fills EMPTY places, so a player under FR_CUT_FLOOR in a group of one or two places is
# released at the cut and the fill takes his place; (2) the "beats the group's lowest rating" bonus counts the weakest player who would
# hold a place (the place-count'th best of the group's players and drafted rookies), so a team that drafted a quarterback does not draft a
# fourth. Result over 10,000 league-seasons of the fast run with the real draft, cut and fill (the only stand-in left, SX.8e's four weeks of
# extra work, on): the MEAN over the leagues is inside its band in every one of the 20 seasons (rating 69.2 to 70.8, age 25.8 to 26.7, every
# group 67.2 to 73.9, win spread 2.81 to 2.87); no single league-season has a mean rating or age outside its band; no team group is under 50
# (lowest 50.0); one group's mean leaves 64 to 76 in 10.3 percent of the single league-seasons (kickers 4.3, punters 5.0, quarterbacks 1.7:
# the single-place groups move as a cohort, B-P74; left to SX.8f's per-run I8b); a player who left had played 4.91 seasons (C-F5: 3 to 7); the
# picks of round 1 are rated 76.3 at 25 (at least 72) and the picks of round 7 65.0 (at most 66), counted over the picks still active at 25,
# of whom 0.8 percent (round 1) to 95.4 percent (round 7) had left before 25 (C-F6). THE BUILD ALONE (nothing gives a development point
# until SX.8e) is inside the same bands as a mean over the leagues: rating 68.5 to 70.0, age 25.8 to 26.7, every group 66.5 to 72.8, win
# spread 2.79 to 2.88; 15 of the 10,000 single league-seasons have a mean rating just under 68 and 1.6 percent a group outside 64 to 76
# (work/calibrate_draft_sx8d_fast_500x20_build_alone.txt); the picks of round 1 are rated 74.3 at 25 and those of round 7 64.6.

# ----- the to-do list and the news, design 8 (SX.8e; the history of every move is below) -----
# T1 extra work (design 8.1): in these weeks of the regular season a team with at least FR_EXTRA_WORK_CANDIDATES players aged
# FR_EXTRA_WORK_AGE or less, of high or average potential and with fewer than FR_EXTRA_WORK_POINTS development points, gives one of
# them a point. The player is asked; every computer team gives its first candidate the point (the same code, `franchise/todo.py`).
FR_EXTRA_WORK_WEEKS = (2, 6, 10, 14)
FR_EXTRA_WORK_AGE = 24
FR_EXTRA_WORK_CANDIDATES = 2
FR_EXTRA_WORK_POINTS = 3
# T2 the game plan (design 8.1): the style the staff recommends for each opponent style (and Classic), worked out once by
# work/make_game_plan_sx8e.py with the expected-yards yardstick of tests/playbook_ev.py and frozen here (report:
# work/make_game_plan_sx8e.txt). "offense" is keyed by the opponent's DEFENSE style, "defense" by the opponent's OFFENSE style.
FR_GAME_PLAN = {
    "offense": {"classic": "west", "pro": "west", "west": "west", "air": "west", "power": "west", "zone": "west", "option": "west", "pressure": "west"},
    "defense": {"classic": "power", "pro": "option", "west": "pressure", "air": "option", "power": "power", "zone": "option", "option": "option", "pressure": "pressure"},
}
# The news (design 8.3): at most FR_NEWS_MAX lines a week, in the order of the rules; the player's streak from FR_STREAK_OWN, another
# team's from FR_STREAK_LEAGUE, every FR_MILESTONE-th win as head coach; an upset is a win by a team whose rating (the weighted mean,
# design 4.4) is FR_UPSET_GAP or more points under the loser's.
FR_NEWS_MAX = 4
FR_STREAK_OWN = 3
FR_STREAK_LEAGUE = 4
FR_MILESTONE = 10
FR_UPSET_GAP = 3                  # design 8.3 gives 4 as a fixed number (no start-value mark); moved by decision D-060, see below
# SX.8e calibration (D-060; the report is work/calibrate_todo_sx8e_fast_500x20.txt, the scripts work/sim_league_sx8e.py and
# work/calibrate_todo_sx8e.py). THE REAL EXTRA-WORK ITEM (todo.computer_extra_work, in its week for every team) in the fast run's loop
# leaves C-F4 as the SX.8d report had it with the stand-in, season by season (the item is the same rule): the MEAN over the 500 leagues is
# inside its band in every one of the 20 seasons (rating 69.2 to 70.8, age 25.8 to 26.7, every group 67.2 to 73.9, win spread 2.81 to 2.87),
# 127.5 of the 128 points a season are given (a team with fewer than two candidates gives none), and no value of the aging, the draft or the
# extra work moved. ONE value of the news moved: at the design's FR_UPSET_GAP of 4 rating points an upset is told in 8.0 percent of the
# weeks (the strengths' standard deviation settles near 1.3, so a gap of 4 is three standard deviations between two teams); at 3 it is
# 26.0 percent (at 5, 2.0 percent). Three is the first gap at which an upset is news about one week in four; the lines a week are
# 3.13 at the gap of 4 and 3.27 at 3, and the cut at FR_NEWS_MAX takes lines away in 6.9 percent of the weeks (2.7 at the gap of 4).

# ----- the 20-season simulation, design 16 SX.8f (the history of every move is here) -----
# SX.8f (D-061; the reports are work/simulate_franchise_sx8f_fast_100x20.txt, _fast_500x20.txt and _full_5x20.txt, the scripts work/simulate_franchise_sx8f.py
# and work/full_sx8f.py, the sweeps work/sweep_sx8f_log.txt). At the values SX.8e left, 100 leagues x 20 seasons failed three invariants: I11 (49 of 100
# leagues had a team among the three weakest more than 5 seasons in a row, the longest 10), I8b (236 of 2,000 league-seasons had a group's mean outside 64 to
# 76: kickers 112, punters 107, quarterbacks 41, all above) and I8's spread (136 below 1.0). TWO WINDOWS MOVED (FR_PEAK is not in design 16's list of knobs
# for SX.8f; D-058 moved it too, and D-061 says so): (1) the kicker's and the punter's windows start at 24 (the design's 26): the rule of D-058 again, a
# window that starts late grows for more years (a kicker drafted at 21 to 23 grew until 26, four to five years against the two of a running back) and the
# selection of the cut and of the retirements, which keep the good ones, lifted the group's mean to 73.7; with 24 it settles at 68.2 to 70.9 (the end, 34, is
# the research's). (2) The quarterback's window ends at 30 (the design's 32, D-058 kept 32): the quarterbacks' mean drifted up to 72.2 and a league's
# quarterbacks sat over 76 for up to 7 seasons in a row (the "quarterbacks at 77 to 81" that I8b was written for); with 30 the longest stretch is 5 seasons and
# the mean 70.1 to 72.9. A quarterback still holds to 30 and declines from 31 (-2, -3, -4); research B6's "early thirties" is 31 and 32 there.
# TRIED AND NOT KEPT (each in the sweep log): a weak mark of the draft that is higher for the quarterback (75 or 78): it seemed to cut the leagues with a long
# streak from 49 to 14 percent, but the independent review showed why: with the mark above the rookies' middles a team that had drafted a quarterback still
# counted the place open and drafted a second and a third (4 quarterbacks in round 1 a draft, 35 percent of them released at the cut, 29 percent of the
# round-1 picks made by a team whose quarterback was rated 70 or more); with the rule corrected (the need bonus only for a prospect who would take the
# place) the gain was gone (27 to 40 percent), so FR_DRAFT_WEAK stays the design's 60 and the draft's code is the committed one; also not kept: the retirement
# per year 150 (the leagues with a long streak 14 to 9 percent, but a rule that is right is not moved to meet an aggregate, B-P56), the youth bonus of the cut
# 8/4, the team level -1..+1, the draft's need values, a wider spread of the rookies' ratings with and without a lower growth (the quarterbacks' mean over 76
# in 20 to 60 percent of the league-seasons), a longer decline, a noisier progression, shorter windows for the others.
# THE BANDS THAT CANNOT BE MET BY THE LISTED KNOBS (restated by decision D-061 for the core; SX.8p measures the whole Franchise against the design's again):
# I11's "no team among the three weakest more than 5 seasons in a row": 41 percent of the leagues are over it, the longest 10; the cause is measured (the lag-1
# correlation of a team's strength is 0.74, the quarterback is 52 percent of the variance of the exact sums, only retirement and the draft change a roster), so
# the core is judged by the chance that a team in the bottom three is there again next season (0.48; by luck 0.094; allowed 0.55) and a streak of at most 10;
# the spread of the 32 strengths (the design's 1.0 as the lower edge) is 0.8 for the core: the mean over the runs is 1.13 to 1.77 in every season, each run's
# mean 1.00 to 1.49, 0.6 percent of the single run-seasons are under 0.8 (the lowest 0.67), no run stays outside for more than a quarter of its seasons.
# Result over 500 leagues x 20 seasons: I1, I3, I4, I5, I9, I10, I12 hold in every run-season; mean rating 68.3 to 71.3 and mean age 25.6 to 27.0 in every
# run-season; C-F1 2.83 (2.80 to 2.87 in each season, 2.64 to 3.02 in each league); every strength 60 to 80.

# ----- contracts and the salary cap, design 17 SX.8g (D-066; the history of every move is below) -----
# A salary is a whole number of tenths of a million dollars (124 is 12.4 million), the same unit for the cap, a payroll and dead money.
# THE CAP (research F2's choice, D-066): the NFL's 2026 cap of 301.2 million dollars a club is for 53 players; this league has 34 places, so the cap
# is SCALED by 34/53 (193.2 million), which keeps the cap per place at the NFL's 5.7 million (the league uses about 78 percent of it once it has turned
# over, so a player is paid 4.4 million on the average). The other choice, the real cap with a fixed charge for the
# 19 unnamed players, was not taken: it would make a number the player cannot see in the roster the biggest part of every cap sum. The cap is a
# constant for the whole franchise: the NFL's growth is not copied (research G: "cap value inflating by a compounding multiplier"), the
# salary scale below is a constant too, and the 20-season check holds the league's payroll in a band (no drift).
FR_CAP = 1932                     # 301.2 million x 34 / 53 = 193.2 million
FR_MIN_SALARY = 9                 # 0.9 million: the NFL's 2026 minimum for a rookie, 0.885, up to the next tenth (research B4)
FR_MAX_SALARY = 280               # 28 million: about 14.5 percent of the cap, the size of the NFL's top franchise tag (research F2)
# The market price of a player: the minimum + (rating - 40) squared x the position's pay in percent / FR_PAY_DIVISOR, at most the maximum.
# The pay of a position follows, roughly, how much it matters (design 4.4's weights): the quarterback most (two and a half times a lineman, three
# times a receiver), the kicker, the punter and the returners least (the NFL pays a kicker far less than a back, so the kicker is paid less than his
# weight of 4 suggests).
FR_PAY = {"QB": 300, "RB": 90, "WR": 100, "DL": 120, "LB": 100, "CB": 100, "S": 80, "RET": 40, "K": 50, "P": 40}
FR_PAY_DIVISOR = 2400
# A drafted rookie's salary is fixed by his pick (research B3: the NFL's wage scale is unknown, so the league invents one that keeps its
# shape: the first pick earns about three times the 32nd, who earns about three times the last): straight lines between these (pick, salary)
# points. Four years for a drafted rookie, three for an undrafted one (the fill of the roster cut); a rookie contract has no fifth-year
# option (research B3).
FR_ROOKIE_SCALE = ((1, 77), (32, 26), (64, 17), (96, 13), (128, 11), (224, 9))
FR_ROOKIE_YEARS = 4
FR_FILL_YEARS = 3
# The length of a new contract by the player's age (the first row whose age is not under his): research G, "a maximum contract length by age".
FR_CONTRACT_YEARS = ((27, 4), (29, 3), (31, 2), (99, 1))
# Releasing a player costs dead money against the cap of the season that follows: this percent of his salary for every year he had left
# (research B3: one simple rule, no restructures, no proration).
FR_DEAD_SHARE = 25
# SX.8g calibration (D-066; the reports are work/simulate_franchise_sx8f_fast_500x20_sx8g.txt, _full_5x20_sx8g.txt and _fast_500x20_sx8g_cap_off.txt,
# the divisor was swept with work/probe_cap_sx8g.py). Only FR_PAY_DIVISOR and the shape of the rookie scale moved while it was found: with the divisor
# 2200 and a quadratic rookie scale from 7.7 million the league used 0.89 to 0.95 of the cap and the cap rule of the cut released players in 17 percent of
# the team-offseasons; the final scale (straight lines, the 32nd pick 2.6 million) and 2400 give the league's mean cap use 0.834 in season 1, 0.700 in season 7
# and 0.77 to 0.79 from season 11 (a new league is all market prices, a league that has turned over is a third rookie contracts and 2.7 percent dead money),
# the fullest team 1.000, and the cap rule releases 441 players in 341 of 320,000 team-offseasons (0.1 percent): the cap almost never binds, so the free
# agency of SX.8i is where it will (SX.8p measures it again). Contracts alone change nothing else: with FR_CAP so large that it never binds the 500-league season
# table is identical to SX.8f's.

# ----- re-signing, the talks and the franchise tag, design 17 SX.8h (D-067; the history of every move is below) -----
# A player whose contract has run out (years left 0 after the year turned in stage 2) is either signed again at the market price of his
# position, rating and age for the length of his age, or he is a free agent (status "free"). The staff and the computer's teams sign by value
# under the cap, the player is asked about his own players (a short talk, at most FR_TALK_ROUNDS rounds, the player's mood decides what he
# accepts) or the staff does it when the setting says so. Every number is data; nothing is drawn.
FR_RESIGN_MIN_RATING = 60        # the staff and the computer's teams sign a player again only when he is rated at least this: the draft class's mean true rating
#                                   (FR_ROOKIE_RATING 46 + 14), because the draft that follows replaces a weaker veteran at the cut and his release costs dead money
#                                   (a margin over the fill's middle, 3 then 10, was tried: it asked 65 of a kicker or punter, whose draft supply is thin, and the kicker group's
#                                   mean fell under 62 in the 2,000-league run)
FR_RESIGN_RESERVE = 0             # tenths of a million left under the cap when signing, for the rookies of the draft (0: the cap rule of the cut is the net)
FR_EXCLUSIVE_SEASONS = 3          # a player with fewer seasons in the league than this asks the minimum for one year (research B3: exclusive rights)
FR_TALK_ROUNDS = 3                # a talk ends after this many rounds (research B3)
FR_OFFER_LESS = 10                # "offer less" is this many percent under the present price
FR_MOOD_SLACK = {"happy": 10, "content": 4, "unhappy": 0}     # the most percent under his price he accepts, by his mood
FR_MOOD_WINS = (11, 5)            # a team's players are happy after this many regular-season wins (or after reaching the division round: a win or a bye), unhappy after this few or fewer
FR_TAG_TOP = 5                    # the franchise tag pays the average of this many highest salaries at the position (research B3) ...
FR_TAG_RAISE = 120                # ... or this percent of the player's last salary, whichever is more (and never less than his market price)
# SX.8h calibration (D-067; the reports are work/simulate_franchise_sx8f_fast_500x20_sx8h.txt, _fast_2000x20_sx8h_2000.txt, _full_5x20_sx8h.txt, the stand-in baseline
# ..._sx8h_standin.txt (everybody signed again at the market price after the development: SX.8g's behaviour at the new timing) and the sweep ..._sx8h_margin<m>.txt).
# 251 contracts run out in a league-offseason (23 percent of the 1,088 players); the staff signs 93.5 percent again and lets 6.5 percent (16 players, mean rating 56.9,
# none rated 80 or more) go; none for want of room under the cap, which (mean use 0.77) does not bind before free agency. HOW THE MINIMUM RATING WAS FOUND: the first rule
# was a margin over the fill's middle rating (3 points): it let 1.0 percent go, and 14.6 percent of the cut's releases had been signed again in the same offseason (17.6
# percent of the dead money, the independent review). A margin of 10 (the draft class's mean over the fill's) halved that and let 9.6 percent go, but asked 65 of a kicker
# or punter, whose supply from the draft is as thin as the fill's: the kickers' league mean fell under 62 in the 2,000-league run; a margin of 14 broke the floor of a group (I5).
# So the rule is one number for every group, the class's mean true rating, 60. The league as SX.8g left it is unchanged within the sampling error (persistence of the bottom
# three 0.478, spread 1.12 to 1.77, quarterbacks 70.09 to 72.79, cap use 0.686 to 0.834, careers 4.90, dead money 1,487 against 1,683); the stage changes the player's decisions,
# not the league's health. THE SUPPLY OF FREE AGENTS IS THIN (Q-031: 16 a league-offseason, none rated 80): SX.8i's market must make its own (FR_RESIGN_MIN_RATING and
# FR_RESIGN_RESERVE are the knobs this stage offers it). The mood of a player is a rule of last season's record only (FR_MOOD_WINS), and FR_MOOD_SLACK equals FR_OFFER_LESS
# for a happy player on purpose: his floor is exactly the offer for less.

# ----- free agency, design 17 SX.8i (D-068; the history of every move is below) -----
# The minimum salary by the seasons a player has played (research B4, the NFL's 2026 table: 0 seasons 0.885 million, 1 season 1.005, 2 1.075, 3 1.145, 4 to 6 1.215,
# 7 or more 1.3), in tenths of a million rounded: (the most seasons the row is for, the minimum). The first row whose seasons are not under the player's applies.
# It is the exclusive-rights price of stage 7 (a player with fewer than FR_EXCLUSIVE_SEASONS seasons) and the floor of a free agent's falling price.
FR_MIN_SALARY_BY_SEASONS = ((0, 9), (1, 10), (2, 11), (3, 11), (6, 12), (99, 13))
# The market: FR_FA_ROUNDS rounds (research B4: 3 to 5); in each round every team places its offers, then they are all judged together, the best player first
# (the player with the best value over his replacement, `resign.value`). A free agent who is not signed in a round asks FR_FA_PRICE_DROP percent of his stage-7 price less for every round he stays
# (the market cools: 90 and 80 percent), never under his minimum. A team bids only for a position with an open place (no stacking, no release to make room), for a player rated at least
# FR_FA_MIN_RATING, at his price, and for at most FR_FA_CHASE players for each open place in the first round and one more in every later round (it chases a second when the first goes elsewhere,
# and looks further down the list when its choices have gone: `market.chase`). The score of an offer is the salary
# raised by the fit of the player to the group (FR_FA_FIT percent: 0 when he would not be better than the group's weakest, 1 when he would, 2 when he would be its best);
# the highest score wins, equal scores are told apart by a rule that favors no team (`market.tie_key`: a multiplier from his ID, modulo 37, orders the teams). The player's
# "offer more" is FR_FA_OFFER_MORE percent over the price. The player places at most FR_FA_OFFERS offers in a round; the staff's list holds FR_FA_LIST players.
FR_RESIGN_TARGET = 0.62           # the share of the cap the staff keeps the coming season's contracts under when it signs players again (stage 7); the players that do not
#                                   fit go to the market (Q-031: the supply of free agents). 1.0: the cap alone decides (SX.8h). Found by a sweep, see the history below.
FR_FA_ROUNDS = 3
FR_FA_PRICE_DROP = 10
FR_FA_MIN_RATING = 60
FR_FA_CHASE = 2
FR_FA_FIT = (0, 2, 4)
FR_FA_OFFER_MORE = 10
FR_FA_OFFERS = 5
FR_FA_LIST = 5
FR_FA_RESERVE = 0                 # tenths of a million left under the cap for the draft's rookies when a team signs a free agent (0: the cap rule of the cut is the net)
# SX.8i calibration (D-069; the reports are work/simulate_franchise_sx8f_fast_500x20_sx8i.txt, _fast_2000x20_sx8i_2000.txt, _fast_100x20_sx8i_cap1450.txt and _full_5x20_sx8i.txt, the
# sweeps work/sweep_market_sx8i_a.txt, _b.txt and _c.txt, the probe work/probe_market_sx8i.py). THE SUPPLY (Q-031): at SX.8h's rule the market had 16 players a league-offseason, mean
# rating 56.9, none rated 80. The one lever that makes a supply without a random draw is a payroll target of the staff when it signs players again (FR_RESIGN_TARGET): a sweep
# over the share of the cap gave, per league-offseason (64 leagues x 10 seasons, the neutral tie rule): 1.00: 16 free agents, no star; 0.74: 39 (0.34 stars rated 80 or more); 0.70: 57
# (0.9); 0.66: 84 (1.9); 0.62: 117 (4.0); 0.58: 150 (6.4); the persistence of the bottom three 0.52, 0.49, 0.48, 0.44, 0.39, 0.33. 0.62 is the first share at which the market is worth
# hearing (about 4 free agents for each team and about 6 stars) and the league's health stays inside the bands of the core. The first sweep (work/sweep_market_sx8i_a.txt) broke
# ties in favor of the team that was weaker last season and found a persistence of 0.03 to 0.11: a rule that favors a side is a parity machine, so equal scores are now told apart by
# a fixed rule that favors no team (tie_key: a multiplier from the player's ID, modulo 37; the review found that "team plus ID" put each team ahead of its neighbour in 31 of 32 ties). The fit
# changes nothing but the order of the fit levels (all the computer's offers are at one price), so its percentages are only data (0, 2, 4 and 0, 1, 2 give the same leagues,
# work/sweep_market_sx8i_c.txt). The chase grows by one for every later round (2, 3, 4): with a flat chase 29 free agents rated 60 or more a league-offseason left the market although a team
# had an open place and the room for them (the review), and 45 of 130 were left; with the growing chase 26.5 are left and 80 percent of the market is signed, at the price of more
# churn (the cut releases 3.7 market signings of 133 and the dead money rises from 1,235 to 1,402 tenths). WHAT THE MARKET DOES TO THE LEAGUE, said plainly (2,000 leagues x 20 seasons
# against SX.8h's report; the same runs with FR_RESIGN_TARGET 1.0, which is SX.8h's behaviour with a market that has nobody to sell, differ in the same way in 200 leagues): the
# persistence of the bottom three falls from 0.478 to 0.363 (the design wants it lower); THE SPREAD OF THE 32 STRENGTHS FALLS: from season 4 it is 0.95 to 1.12 (the core had about 1.1 to 1.4),
# below the design's lower edge of 1.0 in the seasons 4 to 8 and 4.9 percent of the run-seasons are under the core's relaxed 0.8; the win spread falls from 2.83 to 2.79 and 4 of 2,000 runs
# have a mean under 2.6 (lowest 2.58) where none had (lowest 2.62): the payroll target takes players from the teams with high payrolls (a progressive tax: the strong teams) and the fit
# sends free agents to the teams where they would be the best of the group (the weak ones), so the market is a little parity. C-F1 per run is therefore judged by a share of the runs
# (simulate_franchise_sx8f.py WIN_TAIL_SHARE and WIN_HARD, decision D-069) and SX.8p must bring the design's spread and win-spread bands back (the levers are outside this stage: the
# lean and the ratings' spread of SX.8b). The other numbers: every invariant holds in every run-season (I1 to I5, CP1 to CP5, RS1 to RS4, FA1 to FA8, I8 rating 68.30 to 71.45), 130
# free agents a league-offseason (mean rating 67.4, 6.4 rated 80 or more) for 196 open places, 104 signed (mean rating 69.5, every star), 26.5 left; 52 percent of the 252 contracts
# that run out are not signed again; the quarterbacks' league mean 70.04 to 72.83, careers 4.91, the mean cap use 0.689 to 0.833. THE CAP: at the league's use of 0.75 the room decided 4 of 45
# million offers; need (an empty place), not money, limits a team, so "the cap now binding" is true of the rules and of a STRESS RUN with a cap of 1450 (25 percent lower,
# work/simulate_franchise_sx8f_fast_100x20_sx8i_cap1450.txt: cap use 0.81 to 0.99, the room decided thousands of offers and the cap rule of the cut fired in 2,600 of 64,000 team-offseasons), in
# which every research-G invariant (CP1, FA2, FA5 and the others) still holds and only CP4's band of the cap use and the mean rating move, as they should, not of the shipped game.

# ----- trades, design 17 SX.8j (D-070; the history of every move is below) -----
# A trade swaps two players of the SAME position between two teams (so every place stays filled in the season), with up to FR_TRADE_PICKS_MAX picks of the
# coming draft added by the side that must give more. The value of a player to a team is his worth over the rookie who would replace him (the position's weight
# times the rating over the fill's middle rating, `resign.value`'s unit), weighted by his age and the team's situation (FR_TRADE_AGE), by his potential while he is
# young (FR_TRADE_POTENTIAL), plus what his contract saves against his market price (FR_TRADE_MONEY_DIVISOR); a pick is worth FR_TRADE_PICK_VALUE[round] weighted by the
# team's situation (FR_TRADE_PICK_SHARE). A computer team agrees when what it gets is worth at least FR_TRADE_MARGIN rating points of the position more to it than
# what it gives (times the position's weight: `trades.margin_of`) (research B5).
# THE WINDOW: the NFL's 2026 deadline is 4 p.m. on 2026-11-10, the day after week 9 of 18 (research F2; nfl.com important dates): half the season. Half of 16 is 8 games played,
# so the window closes at the kick-off of week FR_TRADE_LAST_WEEK = 9 (design 17 said "week 10 of 16" before it was worked out). The computer teams look for trades in the
# preparations of the weeks FR_TRADE_FIRST_WEEK to FR_TRADE_LAST_WEEK (after 3 to 8 games: before that a record says nothing about a team's situation).
FR_TRADE_FIRST_WEEK = 4
FR_TRADE_LAST_WEEK = 9
# START VALUES that no measurement has moved (the SX.8j review's note; the playtest and SX.8p may): FR_TRADE_MIN_GAMES, FR_TRADE_CONTEND, FR_TRADE_REBUILD,
# FR_TRADE_VETERAN_AGE, FR_TRADE_UPGRADE, FR_TRADE_AGE, FR_TRADE_POTENTIAL, FR_TRADE_MONEY_DIVISOR, FR_TRADE_PICK_SHARE, FR_TRADE_SEASON_MAX, FR_TRADE_PICKS_MAX.
# MEASURED: FR_TRADE_PICK_VALUE (work/measure_pick_value_sx8j.txt); SWEPT: FR_TRADE_MARGIN and FR_TRADE_WEEK_MAX (the history below).
FR_TRADE_MIN_GAMES = 3            # a team's situation needs this many games played; before it every team is "middle"
FR_TRADE_CONTEND = 2              # a team that has won at least this many more games than it lost is contending
FR_TRADE_REBUILD = 2              # a team that has lost at least this many more games than it won is rebuilding
FR_TRADE_MARGIN = 12              # a computer team agrees only when it gains at least this many rating points of the position (in value: times its weight)
FR_TRADE_PICKS_MAX = 2            # picks one side may add to a trade
FR_TRADE_VETERAN_AGE = 28         # a rebuilding team offers its players of this age or more (the trade block)
FR_TRADE_UPGRADE = 3              # a contending team trades for a player rated at least this much over the one it gives
FR_TRADE_SEASON_MAX = 2           # a computer team starts at most this many trades a season
FR_TRADE_WEEK_MAX = 1             # at most this many trades between computer teams in a week
FR_TRADE_LIST = 5                 # the offers the player hears for a player he puts on the block
FR_TRADE_NEWS = 2                 # the trades of a week told in the news (the most valuable first)
# the age weight of a player's value in percent, by the team's situation: (the oldest age of the row, percent)
FR_TRADE_AGE = {"contend": ((24, 80), (29, 100), (32, 100), (99, 80)),
                "middle": ((24, 100), (29, 100), (32, 80), (99, 55)),
                "rebuild": ((24, 130), (29, 100), (32, 60), (99, 30))}
FR_TRADE_YOUNG = 25               # the potential counts for a player of this age or less ...
FR_TRADE_POTENTIAL = {"high": 115, "average": 100, "low": 85}     # ... in percent
FR_TRADE_MONEY_DIVISOR = 20       # tenths of a million saved against his market price (for every year left) per point of value
FR_TRADE_PICK_SHARE = {"contend": 70, "middle": 100, "rebuild": 130}   # a pick's value in percent, by the team's situation
FR_TRADE_PICK_VALUE = (48, 38, 29, 19, 10, 3, 1)       # round 1 to 7, measured in SX.8j (see below)
# SX.8j calibration (D-070; the reports are work/simulate_franchise_sx8f_fast_500x20_sx8j.txt, _fast_2000x20_sx8j_2000.txt, _fast_500x20_sx8j_off.txt (trades off) and
# _full_5x20_sx8j.txt, the sweeps work/sweep_trades_sx8j.py, the measurement work/measure_pick_value_sx8j.txt). THE PICKS: a pick is worth what the player it becomes is
# worth to a team in the situation "middle" (trades.player_value) at the start of his first and second season, 0 when the cut released him, the mean of the two, over 200
# leagues x 12 seasons of the fast run without trades: (41.9, 53.7) (34.4, 41.1) (26.6, 31.1) (18.2, 20.3) (9.5, 9.9) (3.6, 3.3) (1.0, 0.9) -> (48, 38, 29, 19, 10, 3, 1);
# the start values (60, 35, 22, 15, 10, 6, 4) were a guess. THE MARGIN AND THE COUNT (48 leagues x 20 seasons each): a flat margin in value points (the first build,
# 10 and then 30) let quarterbacks alone through (11 of 12 trades in a small whole-program run at 30: a margin of 30 is 2.5 rating points of a quarterback and 15 of a
# lineman), so the margin is rating points of the position times its weight (trades.margin_of). With 4 trades a week allowed the count stayed at 22 a league-season for
# margins 3 to 6 (the week's limit bound, not the margin; 10: 13, 14: 2.9); "a few a year" (research B5) is reached by ONE computer trade a week (FR_TRADE_WEEK_MAX 1):
# 6.0 trades a league-season at a margin of 5 or 8 (one in EVERY week of the window). THE INDEPENDENT REVIEW found that the first search gave the week's one trade to the
# first contender of the turned order (a team's number decided: 101 to 193 trades a team in 40 x 20), so the search now keeps the best trade of every pair of a contender
# and a rebuilder and the week takes them the greatest gain first (in rating points of the position); and that a fixed trade a week is no "few a year": with the new
# search a margin of 12 gives 4.3 trades a league-season and leaves about three in ten window weeks without a trade (8: 6.0 in every week, 16: 1.1, 20: 0.1), so the margin
# is 12 (quarterbacks 0.3 percent of the trades: a trade of quarterbacks rarely gains a contender 12 points of the position at the price a rebuilder asks).
# WHAT THE TRADES DO, said plainly (500 leagues x 20 seasons, work/simulate_franchise_sx8f_fast_500x20_sx8j.txt, against the same leagues with trades off, _sx8j_off.txt,
# whose season table is SX.8i's to the digit): the contenders get the rebuilders' veterans, so the spread of the 32 strengths rises by 0.125 on the average inside a season
# and the win spread from 2.79 to 2.88; C-F1 per run holds again without D-069's share (no run outside 2.6 to 3.4, the lowest 2.70); the spread at the start of the seasons
# from season 4 is 0.96 to 1.17 (the design's 1.0: under it in seasons 4 to 8, by 0.04 at most); the persistence of the bottom three is 0.370 against 0.362 without trades
# (the rebuilders get young players and picks, the contenders players who will decline: the two nearly cancel), the longest streak 9; the position groups and the cap use do
# not move (I8b and CP4 hold as before). SX.8p must still bring the spread to the design's band from the first seasons on.
