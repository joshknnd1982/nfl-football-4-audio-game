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
FR_PEAK = {"RB": (24, 28), "WR": (25, 29), "QB": (24, 32), "DL": (25, 29), "LB": (25, 29), "CB": (25, 28), "S": (25, 29),
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
# SX.8f (D-061; the reports are work/simulate_franchise_sx8f_fast_100x20.txt and _500x20.txt, _full_5x20.txt, the scripts work/simulate_franchise_sx8f.py
# and work/full_sx8f.py, the sweeps work/sweep_sx8f_log.txt). At the values SX.8e left, 100 leagues x 20 seasons failed three invariants: I11 (49 of 100
# leagues had a team among the three weakest more than 5 seasons in a row, the longest 10), I8b (236 of 2,000 league-seasons had a group's mean outside 64 to
# 76: kickers 112, punters 107, quarterbacks 41, all above) and I8's spread (136 below 1.0). TWO VALUES MOVED, nothing else:
# (1) FR_DRAFT_WEAK became a number for each group of one place, the quarterback's 75 (the design's single 60 stays for the kicker and the punter). The
# quarterback carries half of a team's strength (52 percent of the variance of the exact sums; the lag-1 correlation of a team's strength is 0.80, of its
# quarterback's part 0.83), so a team keeps a weak quarterback for years; with 75 a team whose best quarterback is under 75 counts the place as open, so the
# staff drafts a replacement every year and the cut keeps the better of the two (round 1: 14 percent of the picks are quarterbacks, the NFL drafts 3 to 5 a
# year). The single number raised for all three (78) did the same for the quarterback but put kickers and punters in round 1 (4 percent of the picks) and
# released half of them at the cut: football nonsense, so the mark is per group. (2) The kicker's and the punter's windows start at 24 (the design's 26): the
# rule of D-058 again (a window that starts late grows for more years: a kicker drafted at 21 to 23 grew until 26, four to five years against the two of a
# running back, and the selection of the cut and of the retirements, which keep the good ones, lifted the group's mean to 73.7; with 24 it settles at 68.2
# to 70.7). The end of the window (34) is the research's. Tried and NOT kept (each in the sweep log): the retirement per year 150 (the streak share 14 to 9
# percent, a rule that is right is not moved, B-P56), the youth bonus of the cut 8/4, the team level -1..+1, the draft's need values, a wider spread of the
# rookies' ratings (FR_ROOKIE_RATING (42, 19): the quarterbacks' mean over 76 in 20 percent of the league-seasons), a lower growth, longer decline, noisier
# progression. Result over 500 leagues x 20 seasons: I1, I3, I4, I5, I9, I10 and I12 hold in every run-season; the mean rating 68.3 to 71.4 and the mean age
# 25.6 to 26.9 in every run-season; C-F1 2.84 (2.82 to 2.87 in each season, 2.66 to 3.03 in each league); the spread of the strengths 1.37 to 1.77 by season
# (1.1 percent of the run-seasons under 1.0, the lowest 0.74); every group's mean 64 to 76 in 99.4 percent of the run-seasons or better (the quarterbacks'
# 0.6 percent above, the punters' 0.2 percent, the kickers' 0.1 percent; none beyond 3 points); every strength 60 to 80; 77 of 500 leagues (15 percent) still
# have a team among the three weakest more than 5 seasons in a row, the longest streak 7. THE BAND OF I11 IS CHANGED BY DECISION to 8: no value inside the
# listed knobs reaches 5 (the best, 7 percent of the leagues, bought the same with the retirement and youth rules moved), because the only things that change
# a roster in the core are retirement and the draft (the lag-1 correlation of a team's strength is 0.73 at the final values); free agency and trades
# (SX.8g, SX.8j) are the real equalizers. The owner's playtest should listen for a franchise whose own team sits at the bottom for many seasons.
