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

# ----- overtime, SX.12 (Rule 16, extras/overtime.py) -----
OT_KICK_FIRST_PER_MILLE = 700         # the computer that wins the overtime toss kicks off with this chance (one draw): under the format in
#                                       which both teams possess (play-offs since 2022, the regular season since 2025) toss winners chose to
#                                       kick in 14 of 20 games (Yahoo Sports, 2026-09-25; SRC-SECONDARY, a small sample). Classic never draws
#                                       it: the original's computer always receives

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
QB_SCRAMBLE_FROM_INCOMPLETE_MODEL = 12   # SX.10e (D-095): the same for an incompletion of the outcome models (a catalog play): their sacks
#                                        are the league's (SACK_SCALE), so the scrambles the sacks gave the original's engine come from here
#                                        (6 gave 3.6 percent of the drop-backs, band 4.5 to 6.5; measured in work/sx10e)
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
           "RET": (24, 28), "K": (24, 34), "P": (24, 34),
           "OL": (25, 30), "LS": (24, 36)}                    # the first and the last age of a group's peak window (OL, LS: NX-B2b, D-149, the bench only; UNVERIFIED)
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
FR_ROOKIE_RATING = (45, 15)                  # 45 + below(15) + below(15): 45 to 73, mean 59 (SX.8m: 46 to 45, see below)
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
FR_PAY = {"QB": 300, "RB": 90, "WR": 100, "DL": 120, "LB": 100, "CB": 100, "S": 80, "RET": 40, "K": 50, "P": 40,
          "OL": 60, "LS": 20}     # NX-B2b (D-149): a lineman and a snapper play no place of the game, so they are paid as backups (UNVERIFIED first values)
FR_PAY_DIVISOR = 2400
# THE BENCH (NX-B2b, D-149, Q-072): a team of 53 pays 19 more men than the 34 places. FR_CAP stays the cap of the 34 places (the 34/53 share of the
# NFL's 301.2 million); a league that carries benches (reserves.py) plays under FR_CAP + FR_CAP_RESERVES (contracts.cap_of), the bench's payroll at the
# market prices of a new franchise of the real 53 (measured by work/nxb2b/measure_bench_cap.py), so the money the places had is the same as before.
FR_CAP_RESERVES = 540             # 54.0 million: the bench payroll's mean of 320 teams (10 new leagues), 53.4 million, up to the next tenth of 10
#                                   (range 33.4 to 88.4; a team over FR_CAP + this at the start has its salaries over the minimum lowered, contracts.fit_to_cap)
# A bench player of a new franchise of the real 53 has no real rating (facts only): a hash gives it, below the team's places of his position
# (the first man of a group's bench 1 to 4 under its weakest place, each next man 1 or 2 lower) or, for the line and the snapper, from this range.
FR_RESERVE_RATING = (56, 10)      # OL and LS: 56 to 65 (UNVERIFIED first values, the fill's rookies are 45 to 55)
FR_RESERVE_AGE = (23, 9)          # 23 to 31
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
# SZ.8 (D-120): free agents the player signs in the regular season (F9, Franchise, free agents; `signings.py`). The pool is the veterans nobody signed: FR_FA_SEASON_PER_GROUP of
# every position group, made without a draw from the league's ID, the season, the week and the group (so a reloaded league has the same ones), rated FR_FA_SEASON_RATING (the base
# and the span: 58 to 69, below most starters), aged FR_FA_SEASON_AGE (27 to 33), plus the players the player released this season. They ask the price of stage 7 (`resign.asking`);
# a signing needs an empty place or a release of a player of the group who is not hurt (the dead money counts against the cap), and the cap.
FR_PRACTICE_RATING = (44, 11)     # D-136: the made-up young players of a practice squad: 44 to 54 (the fill's rookies are 45 to 55)
FR_PRACTICE_MAX_AGE = 32          # D-136: the oldest player a practice squad signs (the NFL has no age limit; its veterans' limit is practice.VETERANS)
FR_FA_SEASON_PER_GROUP = 3
FR_FA_SEASON_RATING = (58, 12)
FR_FA_SEASON_AGE = (27, 7)
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
FR_TRADE_LAST_WEEK_CALENDAR = 10  # SZ.8: in a season that plays the real 18-week calendar the deadline is the Tuesday after week 9 (2026-11-10): trades are made up to the kick-off of week 10
FR_TRADE_OFFSEASON_WEEK = 0       # SZ.8: the `week` a trade made in the offseason (stage 8, before the draft) carries in the season's log
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

# ----- SX.8k: injuries (NX6 F8, N6.8 INJ-1 to INJ-6; extras/franchise/injuries.py; FRANCHISE ONLY: never drawn, spoken or stored outside a franchise game) -----
# THE TARGET (design 17 SX.8k, INJ-3): the NFL's injury rate per team per regular season. Recorded source: Puga et al., "COVID-19 Return to Sport: NFL Injury
# Prevalence Analysis", JMIRx Med 2022 (PMC9048138), counting the NFL's official team injury reports of the 17-week (16-game) regular season: 48.8 injuries a team
# in 2018 and 59.3 in 2019 (2020: 77.6, the year without a preseason, left out); a second count of the same kind, Cureus 2022 (PMC9158490): 1,370 in 2018-2019, 42.8 a
# team (SRC-SECONDARY: peer-reviewed counts of the league's own reports, read in the search's summaries of the two papers; the NFL's own pages give rates and changes,
# not a total). Scaled to the clone's 34 places of a 53-man roster (34 / 53, a computation, not a source): 31.3 to 38.0 injuries a team a season, the band of the
# calibration (FR_INJ_TARGET); the clone's 16 games have the same length as those seasons.
FR_INJ_TARGET = (31.3, 38.0)       # new injuries of one team in one regular season (the 34 places), the band the 10,000-season run must fall in
FR_INJ_LAST_WEEK = 15             # injuries come from the games of weeks 1 to 15 (the week-16 game has no preparation after it: the play-offs have no to-do list)
# the exposure: per team and week, a practice part for every team (every place alike) and the game part, drawn for a game that was not played by the engine and,
# for a game the player plays, per play (INJ-3: a rush, a catch and its tackle, a sack, a quarterback's run, a kick-off return)
FR_INJ_PRACTICE = (4, 1303)       # (draws, chance of an injury per draw in ten thousandths) for every team every week: every place alike
FR_INJ_GAME = (16, 1310)          # (draws, chance per draw) for a team whose game the engine did not play (the computer's games, the fast run)
FR_INJ_PLAY = 441                 # chance in ten thousandths of an injury on an exposed play of a game the player plays
# CALIBRATED (work/calibrate_rate_sx8k_32x6.txt, 32 leagues x 6 seasons): the start values (1150, 1156, 389: a fifth of the injuries practice, the game part
# 1.85 a team-game = 47.6 exposed plays x 389 per ten thousand, so a played game and a computer's game hurt a team equally) gave 31.3 NEW injuries a team-season
# (a player fit for his game; the hits on a man already hurt are the same injury, 2.5 more), on the band's edge; scaled by 1.05, 1.10 and 1.15: 32.6, 33.9,
# 35.1, so the band's middle (34.65) is a factor of 1.133 on all three chances (the first measurement, 35.2, had counted every hit: B-P100)
FR_INJ_TACKLER = 50               # percent of the injuries of a play that hurt the tackler (the first defender named), else the ball carrier; a return hurts the returner
# the weights of a place in the game part of the weekly draw, from the plays of a game (work/measure_exposure_sx8k.py, 400 team-games: runs 23.4, quarterback runs 2.8,
# catches 15.4, sacks 4.0, returns 2.1 per team-game; half of the carriers' plays hurt the carrier, a return its returner, half of every play but a return a defender)
FR_INJ_GAME_WEIGHT = {"RB": 195, "WR": 128, "QB": 340, "RET": 103, "DL": 134, "LB": 134, "CB": 134, "S": 134, "K": 0, "P": 0}
# the injury kinds (INJ-5: a permanent ID, the games missed when he rests as a range, the share of the kind in percent, the positions it cannot happen to). The spoken
# names are the lines of the pools IJA to IJM of injuries.txt (the rows of spec/strings_nx.tsv); start values, UNVERIFIED (no league source gives the mix of kinds
# with the games missed in a form this game can use: SX.8p and the owner's playtest judge them)
FR_INJ_KINDS = (("IJA", 1, 3, 20, ()), ("IJB", 1, 4, 16, ()), ("IJC", 2, 5, 12, ()), ("IJD", 1, 4, 10, ()), ("IJE", 1, 3, 9, ()),
                ("IJF", 1, 2, 9, ()), ("IJG", 1, 3, 8, ()), ("IJH", 3, 6, 4, ("K", "P")), ("IJK", 3, 7, 6, ()), ("IJL", 12, 18, 2, ()),
                ("IJM", 1, 4, 4, ()))
# the statuses before a game of the regular season by the games still to miss when he rests (left): 3 or more out, 2 doubtful, 1 questionable (in the play-offs every
# hurt player is out: there is no to-do list there). A hurt player who plays plays below his best and may be hurt worse after the game (per mille), his injury
# then starts again one week longer than a new one of its kind
FR_INJ_DOUBTFUL, FR_INJ_QUESTIONABLE = 2, 1
FR_INJ_HURT_PENALTY = {"doubtful": 6, "questionable": 3}       # rating points off while he plays hurt
FR_INJ_WORSE = {"doubtful": 300, "questionable": 100}         # per mille: hurt worse after a game he played hurt
FR_INJ_RANGE_MAX = 3               # the spoken time away is a range at most this wide when it is first told (out 2 to 5 weeks); it narrows by one a week
FR_INJ_STAND_IN = {"QB": 55, "K": 60, "P": 60}                # the rating of a stand-in (a group with nobody to play: the backup quarterback, a kicker signed for the weeks)
FR_INJ_STAND_IN_OTHER = 50
FR_INJ_TEAM_MAX = 12               # no team has more than this many of its 34 players hurt at once (INJ-6: no team starved); a further injury is not drawn on it
FR_INJ_SD_MAX = (1, 2)             # (numerator, denominator): the injuries move a team's place in the computer's games at most this many standard deviations
#                                    of the league from its season's place (INJ-2: bounded like every rating effect, C-F1 holds). SWEPT (work/sweep_injuries_sx8k_64x20.txt, 64
#                                    leagues x 20 seasons, the same seeds, a hurt player's place at replacement level): the win spread is 2.886 without injuries, 2.847 at
#                                    1/4, 2.816 at 1/2, 2.756 at 1 and 2.632 unbounded (its weakest season's mean 2.56, under C-F1's 2.6): injuries are noise on the
#                                    strength the computer's games read, and the bounded score table turns noise into a smaller spread; half a standard deviation keeps
#                                    every season's mean at 2.73 or more (the first sweep, with the next man's own rating: _next_man_rating.txt)
FR_INJ_ASK_GAP = 4                 # the to-do list asks about a doubtful or questionable player whose stand-in in the lineup is this many rating points lower or more ...
FR_INJ_ASK_MAX = 2                 # ... at most this many a week, the biggest gap first (the others: F9, franchise, injury report)

# ----- SX.8l: the staff, the job rating and the owner's goal (NX6 F9, N6.8; extras/franchise/staff.py; a franchise only) -----
# THE TARGET of the firings (research B9, G): the NFL averages close to seven head-coach changes a year among its 32 teams (ESPN; Sportico: seven new head coaches a
# season from 2016 to 2023; SI's table: 9 in 2023, 7 in 2024; SRC-SECONDARY, read in the search's summaries, 2026-10-17). The clone's league has 32 teams too, and a coach
# leaves only when he is fired (no retirement of coaches), so the band of the head coaches fired in a league-season is FR_FIRE_TARGET, the mean over the runs.
FR_FIRE_TARGET = (5.0, 9.0)
FR_APPROVAL_START = 60             # the job rating (0 to 100) of a head coach new to his team
FR_APPROVAL_LEAGUE_START = (60, 41, 13)   # a new league's computer coaches (base, span, stride): 60 + (team x 13) mod 41, 60 to 100, past their grace; the player
#                                    is new (FR_APPROVAL_START, his grace). Measured (12 leagues x 8 seasons): with every coach new at 60 the grace of 32 coaches
#                                    ended together and season 2 fired 13.2 (season 1 none; the review's finding 5); every coach at 70 past the grace still fired
#                                    9.5 in season 1; with the spread the firings rise from 3.5 in season 1 to the steady state by season 7, no season over 6.1
FR_APPROVAL_GOAL = (3, 15)        # the owner's goal met: + the first; missed: - the second (calibrated, see below; the start values were (8, 12))
FR_APPROVAL_PER_WIN = 2           # + this for every regular-season win over 8 (- for every one under)
FR_APPROVAL_FINISH = (0, 1, 2, 3, 4, 6)   # + by the finish: missed the play-offs, lost in the wild card round, the division round, the conference championship, the
#                                    Super Bowl, the champion
FR_FIRE_BELOW = 55                # a head coach whose job rating is under this after the season is fired, but NEVER after a winning season (more than 8 wins of 16:
#                                    research G, EA's own fix of 2026-09-16)
FR_FIRE_GRACE = 1                 # ... and never after his first this many seasons with the team (a new coach gets a season)
FR_DANGER = 5                     # the verdict warns the player when his rating is under FR_FIRE_BELOW + this
FR_OFFERS = 3                     # a fired head coach is offered at most this many jobs, never by the team that fired him (research B9, G)
# the owner's goal of a season by the team's rank at the season's start (the exact strengths, design 4.4): (the last rank of the row, the kind, the number). The kinds:
# "title_game" reach the conference championship game, "playoffs" reach the play-offs, "wins" win at least n games of the regular season. Set from the odds of
# the fast run (12 leagues x 8 seasons with the staff left out, the chance by rank band of reaching each, wins at least n by rank: ranks 1 to 4 0.66 for 11,
# 5 to 8 0.63 for the play-offs, 9 to 12 0.59 for 9, 13 to 16 0.62 and 17 to 20 0.53 for 8, 21 to 24 0.57 for 7, 25 to 28 0.61 for 6, 29 to 32 0.60 for 5): a goal
# a team meets 53 to 66 percent of the time at every rank, 0.60 over all (in the 20-season runs the play-off band meets it 0.68 and ranks 13 to 20 0.53: the ranks
# move with the league). The start values met it 39 percent at ranks 1 to 4, where the conference championship was asked, and 44 at ranks 27 to 32
FR_GOALS = ((4, "wins", 11), (8, "playoffs", 0), (12, "wins", 9), (20, "wins", 8), (24, "wins", 7), (28, "wins", 6), (32, "wins", 5))
# the coordinators: START VALUES with no league source (UNVERIFIED; no figure of the NFL rates a coordinator), judged by SX.8p and the owner's playtest. What
# they make, measured in the 500-league run: 18 coordinators hired a league-season of 64 (a stay of about 3.5 seasons), 30 of 64 rated FR_COORD_ADAPT or more
# after the stage (a team takes the best of three candidates)
FR_COORD_RATING = (50, 21, 21)    # a coordinator candidate's rating: the first + below(the second) + below(the third), 50 to 90, mean 70
FR_COORD_CANDIDATES = 3           # the candidates for an open coordinator's place (the computer team and the staff take the best rated, the first of equals)
FR_COORD_KEEP = 60                # a computer team (and the staff, when it handles the player's team) replaces a coordinator rated under this ...
#                                    ... and a team with a new head coach replaces both (he brings his own)
FR_COORD_ADAPT = 75               # a coordinator rated this or more reads the opponent: the staff's game plan is FR_GAME_PLAN's answer to the opponent's style; a lesser
#                                    one recommends his own style (design 8.1 T2 reads the coordinators)
# SX.8l calibration (D-072; the sweeps are scratch runs of work/sim_league_sx8l.py, 8 leagues x 20 seasons each, the same seeds; the 500- and 2,000-league runs
# are work/simulate_franchise_sx8f_fast_500x20_sx8l.txt and _fast_2000x20_sx8l_2000.txt). THE GOALS met 0.60 of the time with the table above. THE FIRINGS: the
# start values (fired under 40, a goal met +8, missed -12) fired 2.1 head coaches a league-season: the play-off bonus and a goal met more often than missed lift the
# mean job rating to 73 and few coaches ever fall under 40. Under 45 and 50 with (8, 12): 3.1 and 4.0; (4, 14) under 40, 45, 50: 3.8, 5.2, 6.4; (3, 15) under 50:
# 7.1, with 4.4 a season fired in their first or second season, so a new coach gets one season (FR_FIRE_GRACE 1: 5.6 under 50); under 55 with the grace: 6.7 a
# league-season (6.5 from season 11 on), the mean job rating 63, inside the NFL's band of FR_FIRE_TARGET. With a new league's spread of starting ratings
# (FR_APPROVAL_LEAGUE_START, after the independent review) the final runs give 5.71 a league-season over 2,000 leagues x 20 seasons (6.27 from season 11 on,
# each season's mean 3.63 to 6.33: the first seasons fire fewer while the league's ratings spread out), the mean job rating 67.3.

# ----- SX.8m: the market's later items (NX6, design 17 SX.8m; extras/franchise/camp.py, undrafted.py, comp.py, tags.py, rename.py; a franchise only) -----
# THE CAMP FOCUS (research B6's LATER: "focus this camp on offense, defense or young players, a small bounded bonus"; the item is the research's own idea, no league
# source: UNVERIFIED): at the start of stage 3 every team chooses a focus and its FR_CAMP_PLAYERS first candidates of the focus get one development point each
# (the points of design 8.2, at most FR_EXTRA_WORK_POINTS a season); a candidate is an active player of the focus with fewer points than that, in the order of
# the extra work (the highest potential, the youngest, the highest rating). The computer teams and the staff take the focus whose side of the roster is
# furthest under the league's mean of that side (`camp.recommend`), "young players" when neither is under it.
FR_CAMP_FOCI = ("offense", "defense", "young")
FR_CAMP_SIDES = {"offense": ("QB", "RB", "WR"), "defense": ("DL", "LB", "CB", "S")}
FR_CAMP_YOUNG_AGE = 24            # "young players": aged this or less (after the year's aging of stage 2)
FR_CAMP_PLAYERS = 2               # the players of the focus who get a point (the points are rating added to the league: C-F4 counts them; 3 lifted the league's
#                                    mean rating by 0.3 to 0.5 from season 4 on against the same leagues without a camp, 16 leagues x 10 seasons, work/probe_later_sx8m.py)
# THE UNDRAFTED FREE AGENTS (research B4's LATER; NFL: an undrafted rookie signs for three years, operations.nfl.com contract language, SRC-OFFICIAL in research F2;
# the market right after the draft, Madden 27's draft classes with undrafted free agents, SRC-OFFICIAL in research B12): right after the last pick the prospects
# of the class nobody drafted are a market for places in camp; a team offers to the prospects it wants by the draft's own need rule (an open place, or the
# middle of his range over the weakest player who would hold a place), the most valuable to it first, at most FR_UDFA_CHASE; the prospects best first each
# sign with the team that values him most (the draft's value), at most FR_UDFA_MAX a team, on the minimum salary of a rookie for FR_FILL_YEARS, and compete
# in the roster cut like a drafted rookie (his release before the season costs no dead money). MEASURED first (16 leagues x 6 seasons, work/sx8m/probe_udfa.py):
# a market for the places the cut leaves EMPTY could sign nobody: the draft fills the roster, 2 places a league-offseason are empty after the cut (kickers and
# punters by the cut's floor), so the market sits before the cut, where the NFL has it. Start values (UNVERIFIED: the NFL's clubs sign 10 to 20 a year for a
# 90-man camp, a 34-place roster has no camp of that size)
FR_UDFA_CHASE = 4
FR_UDFA_MAX = 2
# THE COMPENSATORY PICKS (research B4's LATER, F2; NFL: a club that suffers a net loss of compensatory free agents in the free agency period is eligible for as many
# compensatory picks, offsetting each one lost by each one gained of an equal or higher value; the formula (salary, playing time, post-season honors) is not
# published; no club gets more than four in a year; the league awards at most 32, at the end of rounds 3 to 7, by the value of the players lost; SRC-OFFICIAL,
# the league's announcements on operations.nfl.com read through the search's summaries, 2026-10-17: the pages themselves answered 404 to a fetch). The clone:
# a qualifying free agent is one who signed with another team in the market for FR_COMP_QUALIFY or more (his salary is the value: the clone's market price is
# a rule of the position and the rating); the picks come in the NEXT offseason's draft (the NFL's: the free agency of one year gives the picks of the next
# draft); rounds by the value, the higher value first in its round. The values are start values (UNVERIFIED: the formula is not published), calibrated to the
# NFL's count (32 to 39 a year with the special picks; 33 to 15 clubs in 2026: research F2).
FR_COMP_QUALIFY = 20              # tenths of a million: a free agent signed for this or more is a compensatory free agent (calibrated, see below; start value 40)
FR_COMP_ROUNDS = ((77, 3), (51, 4), (36, 5), (32, 6), (0, 7))     # (the least value, the round): the round of a pick by the value of the player lost (calibrated)
# CALIBRATED (work/probe_later_sx8m.py, 32 leagues x 12 seasons): the NFL awards its 32 formula picks every year (2026: 33 to 15 clubs, by round 4 (one of them a
# special pick), 8, 9, 3 and 9: nfl.com's announcement, SRC-OFFICIAL read in the search's summary, 2026-10-17). The clone's market moves 90 free agents a
# league-offseason to another team (salaries' quartiles 2.8, 3.7, 4.9 million); the start values (qualify 4.0 million, rounds from 20, 13, 9, 6 million)
# gave 18.1 picks a league-offseason, 11 of them in round 7. The count is bound by the net loss and a team's four (reached by 72 percent of the
# league-offseasons), not by the threshold: 24.1, 23.8, 23.7 and 23.0 picks at 0.9, 1.5, 2.0 and 2.5 million (said plainly in D-073: fewer clubs end the
# market with a net loss than in the NFL). 2.0 million; the rounds are the quantiles of the awarded values at the NFL's 2026 shares (10, 25, 28, 9, 28 percent).
FR_COMP_TEAM_MAX = 4              # NFL: no club receives more than four compensatory picks in a year (SRC-OFFICIAL)
FR_COMP_TOTAL = 32                # NFL: the compensatory picks of a draft are at most the number of clubs (SRC-OFFICIAL; the special picks for minority hiring are not built)
# THE NON-EXCLUSIVE FRANCHISE TAG (research B3's LATER; NFL, operations.nfl.com franchise tags, SRC-OFFICIAL, read 2026-10-17: the non-exclusive tag pays the
# higher of the position's cap percentage average or 120 percent of his prior salary; he may negotiate with other clubs; his club has five days to match an
# offer sheet, else it is entitled to two first-round picks; the exclusive tag pays the higher of the average of the five largest prior salaries at the position
# or the non-exclusive amount). The clone's cap is a constant (D-066), so the cap percentage average is the average over the last FR_TAG_HISTORY seasons of the
# position's average of its FR_TAG_TOP highest salaries (kept in league.sav at every stage 7); the two first-round picks are the signing team's pick of the coming
# draft and of the draft after it (which years: UNVERIFIED, the page does not say; the CBA's text was not read).
FR_TAG_HISTORY = 5
FR_TAG_SHEET_PICKS = 2            # first-round picks a team gives for a player of the non-exclusive tag
# a computer team makes an offer sheet (the market price of his rating for the length of his age) when it has an empty place at his position, the room under the
# cap, both of its first-round picks, and his value to it (trades.player_value at that contract) is at least the value of the picks it would give
# (FR_TRADE_PICK_VALUE[0] each, by its situation); the team that values him most, equal values by the market's tie rule
# SX.8m, THE ONE VALUE OF THE CORE THAT MOVED (D-073): the camp's points (2 a team a season) and the compensatory picks (about 24 more rookies a league-offseason,
# more young players kept at the cut) lift the league's mean rating against the same leagues without them (32 leagues x 12 seasons, work/probe_later_sx8m.py):
# by 0.43 (the camp at 3 players), 0.30 (the compensatory picks), 0.04 (the undrafted), 0.73 together by season 10 (70.44 to 71.17), toward I8's strict edge of 72.
# Swept: FR_ROOKIE_RATING (45, 15) gives 69.67 to 70.31 over seasons 1 to 12 against SX.8l's 69.74 to 70.58 (at most 0.27 under it); three weeks of extra work
# instead of four (70.86 at season 10) and the camp at one player with (45, 15) (69.98) were the other two. The camp stays at 2 players, the rookies' base is 45.

# ----- SX.8n: the people's later items (NX6, design 17 SX.8n; extras/franchise/people.py and people_flow.py; a franchise only, D-074) -----
# THE PERSONALITY (research B10's LATER: "4 or 5 personality words set at birth, each with one rule in contract talks and morale"; the words and their rules are
# this game's own, UNVERIFIED: no league source rates a personality). Five words; a player's word is a rule of his player ID (no draw: the leagues with and without
# the items are the same leagues draw for draw, B-P103), so it is fixed when he enters the league. The key is (ID x FR_PERSON_MIX) mod 1000 against the shares in
# tenths of a percent: every 1,000 consecutive IDs have the shares exactly.
FR_PERSON_MIX = 617
FR_PERSON_SHARES = (("money", 20), ("winning", 25), ("loyalty", 20), ("playing_time", 20), ("the_game", 15))      # percent
# each word's rule in the contract talks: the percent added to the slack his mood gives (resign.floor_salary; never under 0), by mood (happy, content, unhappy);
# "playing_time" adds FR_PERSON_STARTER[0] when he holds the first place of his group and FR_PERSON_STARTER[1] when he does not
FR_PERSON_TALK = {"money": (-4, -4, 0), "winning": (4, 0, -4), "loyalty": (4, 4, 4), "the_game": (-6, 0, 4)}
FR_PERSON_STARTER = (4, -4)
# each word's rule in the morale: what a win, a loss and a week he did not play move his morale (win up, loss down, not playing down)
FR_PERSON_MORALE = {"money": (1, 1, 1), "winning": (2, 2, 1), "loyalty": (1, 1, 1), "playing_time": (1, 1, 3), "the_game": (1, 1, 0)}
FR_HOLDOUT_ALWAYS = ("money",)    # money's rule in the morale: he holds out whenever he is underpaid, whatever his morale (the others only when their morale is low)
FR_HOLDOUT_NEVER = ("loyalty",)   # loyalty's rule in the morale: he never holds out and never asks to be traded
# THE MORALE (research B10's LATER: "one number per player, up or down by results and playing time, moving the rating by at most 1 or 2 points through H8"):
# one whole number from -FR_MORALE_MAX to FR_MORALE_MAX, moved after each of the weeks 1 to FR_MORALE_LAST_WEEK by the week's result, the week's game goal and
# whether he played (the week's lineup of the injuries), halved toward zero at every new season (stage 6). It moves the player's rating IN A GAME by
# step(morale, FR_MORALE_STEP): -2 to +2 rating points. In a game the player plays the change goes through the ratings' own H8 door, so the ratings' cap of
# 1 yard and 3 points stays the ratings' (the morale moves the rating the door reads, never the door's bounds); in the computer's games through the week's
# sums, inside the bound of the week's changes FR_INJ_SD_MAX (injuries and morale together, D-074).
FR_MORALE_MAX = 6
FR_MORALE_DECAY = 1               # every week the morale first moves this much toward zero, then the week's change is added (calibrated, see SX.8n's sweeps below)
FR_MORALE_STEP = (3, 2)           # (per, cap): -1 at -3 to -5, -2 at -6, +1 at 3 to 5, +2 at 6
FR_MORALE_LAST_WEEK = 15          # the results of weeks 1 to 15 move it (the week-16 game has no preparation after it, as the injuries)
FR_MORALE_WORD = 3                # " morale high " at this or more, " morale low " at minus this or less, else " morale good "
FR_MORALE_TALK = 3                # in the contract talks a morale of this or more makes his mood one step better, of minus this or less one step worse
# THE HOLDOUTS (research B10's LATER: "one spoken event at the start of camp: Ruiz holds out. 1 pay him, 2 wait, 3 trade him"; NFL: 2025 camps had about five to
# eight veterans holding out or holding in for a new contract (Hendrickson, McLaurin, Watt, Parsons, Cook and others; CBS Sports' camp holdout tracker,
# SRC-SECONDARY), about 4 a league-offseason scaled to 34 of 53 places: the target band FR_HOLDOUT_TARGET). At the start of stage 3 a player holds out when he is
# under contract for the coming season, has played FR_HOLDOUT_SEASONS seasons or more, is rated FR_HOLDOUT_RATING or more, is paid under FR_HOLDOUT_UNDERPAID
# percent of his market price, is not loyal, and is a money player or his morale is FR_HOLDOUT_MORALE or lower; at most FR_HOLDOUT_TEAM_MAX a team (the most
# valuable). Paying him is the market contract of his rating for the length of his age; the computer teams and the staff pay when it fits under the cap and the
# staff's payroll target of stage 7 (resign.target_payroll), else he waits: his morale falls to -FR_MORALE_MAX.
FR_HOLDOUT_SEASONS = 3
FR_HOLDOUT_RATING = 75
FR_HOLDOUT_UNDERPAID = 75
FR_HOLDOUT_MORALE = -2
FR_HOLDOUT_TEAM_MAX = 1
FR_HOLDOUT_PAY_AGE = 25           # the computer teams and the staff pay a holdout only this age or younger (a new long contract for an older player is a risk the
#                                    staff does not take; the first probe paid every holdout, so nobody ever asked to be traded)
FR_HOLDOUT_TARGET = (2.0, 6.0)    # holdouts a league-offseason (the check's band)
# THE TRADE DEMANDS (research B10's LATER: "the step after a holdout; it becomes news, other teams make offers"; NFL: about four to six public trade requests a year
# (2025: Garrett, Samuel, Meyers, Hendrickson the year before; PFF and CBS Sports, SRC-SECONDARY)). A player who waited asks to be traded from week
# FR_DEMAND_WEEK when his morale is still FR_DEMAND_MORALE or lower; one the player put on the trade block at camp asks at once (week 1). Every week of the trade
# window the other teams make their offers by the trades' own rule (trades.block_offers: each gains the margin of the position); a computer team takes the best
# when it gives up at most FR_DEMAND_GIVE rating points of the position (in value, times the position's weight), else he waits for the next week; the player hears
# the best FR_DEMAND_OFFERS offers in his to-do list. A demand ends with a trade (his morale back to 0) or at the deadline.
FR_DEMAND_WEEK = 1
FR_DEMAND_MORALE = -3
FR_DEMAND_GIVE = 8
FR_DEMAND_OFFERS = 3
# THE WEEKLY GAME GOAL (research B9's LATER: "one weekly game goal spoken before kick-off"; the goals are this game's own, UNVERIFIED): every team's goal of a regular
# week follows the two teams' strengths (league.sums): stronger by FR_GAME_GOAL_GAP rating points or more, win by FR_GAME_GOAL_MARGIN points or more; weaker by
# as much, lose by no more than FR_GAME_GOAL_CLOSE points (or win); else win. A goal met lifts every player of the team by FR_GOAL_MORALE (0, see there); the
# player hears his goal before the kick-off and the verdict before the next week's menu. The numbers are set so a goal is met about half the time in each of the three bands of
# the fast run (a rule that favors a side is a parity machine, B-P90).
FR_GAME_GOAL_GAP = 2
FR_GAME_GOAL_MARGIN = 14
FR_GAME_GOAL_CLOSE = 14
FR_GAME_GOAL_PLAYED = (10, 10)    # (margin, close) in a game the engine plays (the player's): see SX.8n's calibration below
FR_GOAL_MORALE = 0                # a goal met lifts every player of the team by this, a goal missed lowers him by it. 0: THE GOAL MOVES NO MORALE (SX.8n, D-074):
#                                    with 1 the whole-program run's C-F2 was -1.00 and, with the played games' points, -0.84 (allowed 0.8): a goal is met as
#                                    often as the team's margins allow, and the margins of the player's games are his own play (a stand-in's sides in the run,
#                                    a person's skill in the game), which no number of the score table calibrates; so the goal is a spoken target with its
#                                    verdict (research B9 asks no more), and the morale moves by the results and the playing time only (research B10)
# THE PLAYER TAGS (research B2's LATER: "three at most as spoken words derived from age, rating, potential"): a star (rated FR_PTAG_STAR or more), else a rising
# player (aged FR_PTAG_YOUNG or less with high potential), else a veteran (aged FR_PTAG_VETERAN or more), else none; spoken in F9's roster with his morale and
# his word.
FR_PTAG_STAR = 85
FR_PTAG_YOUNG = 24
FR_PTAG_VETERAN = 31
# SX.8n CALIBRATION (D-074; work/sweep_people_sx8n.py, the reports work/sweep_people_sx8n_a.txt (16 leagues x 10 seasons) and _b.txt (32 x 12), the same
# leagues with the items off as the baseline, B-P103). THE MORALE: the start values (no pull toward zero) walked to the edges (65 percent of the players at 3
# or more by the season's end, a met goal only ever added and a loyal player never lost); with a goal missed taking away what a goal met gives and a pull of
# 1 a week the team's mean effect was 0.71 rating points (55 of 78) and the win spread rose 0.30; a step of (4, 2) or (4, 1) gave 0.31 but held the bottom
# three longer (persistence 0.42, 0.43 against 0.37); a pull of 2 a week gives 0.28 (22 of 78), the win spread 2.87 against 2.77 without the items, the
# persistence 0.36 against 0.375, the mean rating unchanged (the morale moves no rating outside a game). THE GOALS: at 7 points the stronger team met its goal
# 69 percent of the time and the weaker 34 (the score table's margins are wide); at 14 points 0.53 and 0.51, the even games 0.50. THE HOLDOUTS: a pay age of
# 29 paid 95 percent of them and nobody asked to be traded; 27, 26 and 25 let 9, 14 and 25 percent wait; 25 with underpaid at 75 percent: 5.2 holdouts a
# league-offseason (from the second season: every contract of a new league is at the market price), 1.6 waiting, 1.4 trade demands a league-season, 1.3 of
# them traded (the NFL's 5 to 8 holdouts and 4 to 6 trade requests a year scale to 3 to 5 and 3 to 4: the demands are fewer, said plainly in D-074).
# THE GOALS OF A PLAYED GAME (FR_GAME_GOAL_PLAYED): the whole-program run (5 x 20) found the player's team 1.00 win a season under its peers of the computer's
# games (C-F2, allowed 0.8); its goals, judged by the score table's 14 points in a game the engine played, were met 0.256 as the stronger team and 0.725 as the
# weaker (its morale fell most when it was the stronger side); with the goal's morale off the same run gave -0.70. The engine's margins (work/
# measure_goal_margins_sx8n.py, 500 played games at gaps of 2, 2.5 and 3 rating points): the median margin is 10 at every gap; at 10 points the stronger
# team meets its goal 0.517 and the weaker 0.516 (at 14: 0.415 and 0.614). So a game the engine plays (the player's, both of its teams) has the goals' points
# (10, 10); the computer's games keep the score table's 14 (B-P106). With them the run gave -0.84 (the player's goals met 0.36 and 0.63: the stand-in's sides are
# not symmetric, and in a person's game his own play sets the margins), so THE GOAL MOVES NO MORALE (FR_GOAL_MORALE 0) and the pull was swept again (work/
# sweep_people_sx8n_c.txt, 32 x 12, the same leagues without the items: win spread 2.772, persistence of the bottom three 0.375): a pull of 2 left a team's
# morale effect 0.08 rating points (no player ever at 3); a pull of 1 with the weights above 0.25 (win spread 2.862, persistence 0.384, holdouts 3.8, trade
# demands 0.9 a league-season); a pull of 2 with every weight doubled 0.35 (2.857, 0.373, 5.3, 1.4). A pull of 1, the weights as designed.

# ----- SX.8o: the game's later items (NX6, design 17 SX.8o; extras/franchise/workload.py, honors.py and staff.fitted_styles; a franchise only, D-076) -----
# THE WEIGHTED BALL CARRIER (research B2: "the original draws the ball carrier by slot ... ratings can weight the draw through H8"; research C: "with H7 and
# H8 a rating can weight that draw"; the weights are this game's own, UNVERIFIED): in a franchise game the snap's draw of who carries (a run: the six backs;
# a pass: the six receivers) weighs each place by base + step(rating - 70, per, cap) of the rating the game's roster gives it (the lineup with the morale).
# Equal weights are the original's draw itself, rnd(6) (every game outside a franchise, and a franchise game of equal ratings: N2).
# NX-D2 (D-147, the owner's second report of 2026-10-24: "the top players should play more. It should take it from like Madden"): with the N. F. L.
# rules who carries, who is thrown to and who tackles is one below(total) draw over these shares (percent of the plays; UNVERIFIED first values, the
# NFL's usage and Madden's depth chart as the model: the lead back carries most of the runs, the first receivers and the first tight end get most of the
# passes, the starters make most of the tackles). They replace D-135's DEPTH_CARRY_SLOTS and the original's even rnd(6) and rnd(17); Classic keeps those.
USAGE_RUN = (60, 25, 10, 5, 0, 0)                 # the six backs of a run (places 1 to 6 in depth order)
USAGE_PASS = (26, 21, 16, 18, 10, 9)              # the six receivers of a pass: WR1, WR2, WR3, TE1, WR4, TE2
USAGE_TACKLE = (6, 6, 5, 5, 2, 1,                  # the six linemen
                13, 11, 7, 2, 1,                   # the five linebackers
                9, 8, 4, 1,                        # the four cornerbacks
                10, 9)                             # the two safeties
CHOSEN_PLAYER_SHARE = 60                             # NX-D4: the player's man for a key down or moment gets 60 percent of his group's draw there
FR_CARRY_WEIGHT = (4, 4, 1)       # (base, per, cap): 3 to 5, so the best of six can carry 5/3 times as often as the weakest (calibrated, see below)
# SX.8o CALIBRATION of the carry weights and the returners (work/sx8o/played_sx8o.py centering 6000: the same 6,000 played games of drawn rosters against
# rosters of 70s, design 5.4 C-F3 (B-P62: within 2 percent), with the items, with cap 1, and without them (FR_CARRY_WEIGHT (4, 4, 0), FR_RETURN_STEP (4, 0))):
# without: points +1.52 and +0.94 percent (the Classic playbooks, the styles), yards a play +0.36 and +0.02; the start value (4, 4, 2): +2.48 and +1.58,
# yards +1.39 and +1.21 (the better back gets the ball more, so the offense's rating in the play's Mod rises: the item's purpose, but the Classic playbooks'
# points left the band); (4, 4, 1): +1.90 and +1.55, yards +1.09 and +0.67, inside; with 10,000 games, the very games of SX.8b's centering run
# (work/sx8o/played_sx8o_centering_10000_cap1.txt against work/calibrate_ratings_sx8b_centering_10000.txt): +1.50 and +1.44 against SX.8b's +0.87 and
# +0.94, yards +0.98 and +0.93 against -0.01 and +0.19: the items add about 0.6 percent of points and 1 percent of yards a play, inside the band. C-F2 (played 1000 a gap, the start value): the stronger team won 0.628
# at a gap of 1 rating point and 0.673 at 1.5 (SX.8b's 0.666 at 1.3 and 0.701 at 1.8): unchanged within the error.
# THE RETURNERS' RATING (research B2's slots; design 5.1 "the returners (the kick-off return has no H8 call)"): the shortest kick-off return (the original's
# 12 yards) moves by step(returner's rating - 70, per, cap), as the punter's rating moves the shortest punt; the draws are the original's. UNVERIFIED (no
# league figure rates a returner); the NFL's best kick returners gain a few yards more a return than the league's mean (SRC-SECONDARY, read in passing).
FR_RETURN_STEP = (4, 3)           # (per, cap): -3 to +3 yards
# THE WORKLOAD RULE (INJ-3, research B7's LATER: "a simple workload rule (a running back who carries a lot gets hurt more)"; per-hit wear stays SKIP; the
# numbers are this game's own, UNVERIFIED): a running back's carries of the season are counted (tenths of a carry: a game the engine plays counts every rush,
# a game it does not play counts the team's running plays, FR_WORKLOAD_RUNS, shared by the carry weights of the week's lineup). From FR_WORKLOAD_FREE on, his
# chance of being hurt as the ball carrier rises by FR_WORKLOAD_PCT percent for every FR_WORKLOAD_PER more, at most FR_WORKLOAD_MAX percent: one more
# draw a carry in a game the engine plays, one more draw a game in the week's draws of a game it does not play, the same expected injuries (B-P107).
FR_WORKLOAD_RUNS = 234            # tenths: the running plays of a team in a game (work/measure_exposure_sx8k.py: 23.4 a team-game, the quarterback runs apart)
FR_WORKLOAD_FREE = 600            # tenths: 60 carries a season before the rule acts (an even share of six backs over 15 weeks is 58.5)
FR_WORKLOAD_PER = 50              # tenths: every 5 carries more ...
FR_WORKLOAD_PCT = 20              # ... add this many percent to his chance as the ball carrier
FR_WORKLOAD_MAX = 100             # percent: at most double
# SX.8o CALIBRATION of the workload (work/sx8o/measure_honors_sx8o.py, 64 leagues x 20 seasons of the fast run; the top back of a team carries 24 percent of
# its runs by the carry weights, about 85 carries by week 15): the start values (free 60 carries, +10 percent every 10 more) hurt 1.07 backs a league-season
# by the rule (the top backs pass the free count only in the last weeks): no one could hear it; free 40, +10 every 5: 14.3 a league-season but 77 percent of
# all backs past the free count by the season's end (an even share passes 40 in week 10: the rule then acts on every back, not on the one who carries a lot);
# free 60 (an even share), +20 every 5: 5.2 a league-season, 36 percent of the backs past it by the season's end, the running backs' new injuries 263 a
# league-season against 260 without the rule (+1.3 percent), the league's rate 34.7 a team-season (FR_INJ_TARGET 31.3 to 38.0). With the carry weights' cap
# of 1 (above; the top back carries 22.7 percent of his team's runs): 3.2 a league-season, 33.5 percent of the backs past the free count, the running backs'
# new injuries 260.7, the league's rate 34.6. A team's top back late in the season is hurt as the ball carrier up to about 1.5 times as often.
# THE AWARDS (research B11's LATER: "league-wide player awards and a hall of fame ... need a new statistics model"; the NFL's AP awards read at NFL Honors:
# most valuable player, offensive and defensive player of the year, the rookies of the year, coach of the year, nfl.com's lists of the winners, SRC-OFFICIAL).
# NO STATISTICS MODEL (D-076): the computer's games are a score table with no plays, so an invented box score would be fiction and the player's own games
# would have real numbers where the others have none; an award reads only what every team has: the ratings, the games a player played his own place
# (counted every week for every team), the team's wins and the play-offs. A player's value is WEIGHT x (rating - FR_AWARD_BASE) x games / 16 plus
# FR_AWARD_WIN a win of his team; at least FR_AWARD_MIN_GAMES games. The most valuable player comes from a play-off team; one rookie award for both sides.
FR_AWARD_BASE = 60
FR_AWARD_WIN = 2
FR_AWARD_MIN_GAMES = 10
# coach of the year: the most wins over what his team's rank at the season's start lets expect (the mean wins of each band of four ranks, MEASURED over
# 64 leagues x 20 seasons of the fast run: 11.18, 9.92, 8.93, 8.23, 7.60, 6.94, 6.14, 5.06; the start values were 11.0, 10.0, 9.0, 8.5, 7.5, 7.0, 6.0, 5.0)
FR_COACH_EXPECT = (112, 99, 89, 82, 76, 69, 61, 51)     # tenths of a win, ranks 1 to 4, 5 to 8, ... 29 to 32
# THE HALL OF FAME (research B11's LATER; the Pro Football Hall of Fame: a player is eligible after five full seasons retired, a class elects four to eight,
# at most five modern-era players: nfl.com's coverage of the classes of 2024 to 2026 and secondary pages, SRC-SECONDARY). At every stage 1 the kept players
# who retired (or left) FR_HOF_WAIT or more seasons before are candidates; a candidate's hall value is his peak + his seasons + his award points
# (FR_HOF_AWARD_POINTS); those at FR_HOF_BAR or more enter, the highest first, at most FR_HOF_CLASS a season (five modern-era players scaled by 34 of 53).
FR_HOF_WAIT = 5
FR_HOF_CLASS = 3
FR_HOF_BAR = 105
FR_HOF_AWARD_POINTS = {"mvp": 6, "opoy": 4, "dpoy": 4, "roy": 1}
# SX.8o CALIBRATION of the hall (64 leagues x 30 seasons, work/sx8o/measure_honors_sx8o_64x30_bar*.txt): the first five seasons have no candidate (the wait);
# the bar at 100 (the start value) filled every class to FR_HOF_CLASS from season 19 on (2.52 a season from season 11), so the class size alone decided;
# at 110 the hall took 1.4 a season at most (1.14 from season 11), under the NFL's rate scaled to this league (about 3: five modern-era players of a 53-man
# league's 1,700 players, scaled to 1,088); 105: 2.09 a season from season 11 and 2.8 to 2.98 from season 22 on, the bar still deciding (the classes are not
# always full), the inducted's hall value 112.6 on the average.
# THE AWARDS' POSITIONS (measured, said plainly in D-076): the most valuable player is a quarterback in every season but a few in a thousand (the position's
# weight of design 4.4, 12 of 78; the NFL's has been a quarterback in most seasons since 2000); the offensive player of the year a receiver in about four of
# five (the backs' window of growth ends earlier, design 6.2), the defensive one a lineman or linebacker in about seven of ten (they have the most places).
# THE COMPUTER TEAMS' PLAYBOOKS FOLLOW THEIR BEST PLAYERS (research B8's LATER: "each computer team's style follows its best players (a team with a strong
# quarterback passes more), through the same bounded modifiers"; EA: teams adapt their playbooks to their personnel, SRC-OFFICIAL in research B8): in a
# franchise game a computer team plays its coordinator's style unless its lineup leans: the passing rating ((2 x the quarterback + the receivers' carry-weighted
# mean) / 3) FR_FIT_GAP or more over the backs' carry-weighted mean plays FR_FIT_STYLES["pass"], as much under it "run"; on defense the line and linebackers'
# mean over the backs' (cornerbacks and safeties) "rush", under it "cover". The styles are the playbooks' own (their mixes and tilts, design 10.3).
FR_FIT_GAP = 5
FR_FIT_STYLES = {"pass": "air", "run": "power", "rush": "pressure", "cover": "west"}
# SAID PLAINLY (the review of SX.8o): the run fit works through its tilts, not its mix. Every style passes more than it runs (MASS: Power Run calls runs 40
# percent of the time, Pro Style and Option 44, Air Raid 20); Power Run's bonus is a yard on its inside runs against the run calls, so a team of strong backs
# gains on the runs it calls, though it calls a few fewer than a Pro Style or Option team. Measured by the reviewer (3 leagues x 3 seasons, 4,608 computer
# team-weeks): 36.5 percent change their offense style, 21.3 percent their defense style.
# MEASURED IN THE WHOLE PROGRAM (B-P107; work/simulate_franchise_sx8f_full_5x20_*.txt): with the COMPUTER teams alone fitted the player's team won 1.07 games a
# season fewer than its peers of the computer's games (C-F2, allowed 0.8); without the fit -0.21; without the fit, the carry weights and the returners -0.53:
# the fit helped only the player's opponents, in his games, and no game of the score table has it. So the fit is EVERY team's: the player's "team" playbook
# is his coordinators', who follow his best players as every team's do, and the staff's game plan of a coordinator who keeps his own style recommends the
# style his lineup fits; a playbook the player names in F9 is his and never changes (nothing is decided for him that he did not leave to his staff).

# ----- SX.8p: the whole Franchise's 20-season test with every block on (design 16 and 17 SX.8p, D-078; NO value moved) -----
# Judged against the DESIGN's own bands (work/sx8p/design_bands_sx8p.py, beside the restated verdicts of work/simulate_franchise_sx8f.py), 500 leagues x
# 20 seasons at the values of this file (work/simulate_franchise_sx8f_fast_500x20_sx8p_base.txt) miss three: the spread of the 32 strengths under 1.0 in
# 24.8 percent of the single run-seasons (every season's mean over the runs 0.99 to 1.77), a single-place group's league mean outside 64 to 76 in 0.25 to
# 0.42 percent of them (QB, K, P; RET 0.04), and a team among the three weakest more than 5 seasons in a row in 17.2 percent of the leagues (one given team
# in 0.61 percent). THE SWEEP (work/sx8p/sweep_sx8p.py, the same 300 leagues as the fast run, proved row for row by work/sx8p/same_leagues_sx8p.py;
# work/sx8p/sweep_sx8p.txt): at these values 16.3 percent of the leagues have a streak over 5 and 24.3 percent of the run-seasons a spread under 1.0;
# FR_ROOKIE_RATING (41, 19) (a wider top, the same mean): 16.7 and 19.0, the quarterbacks outside 64 to 76 in 8.3 percent of the run-seasons; FR_DRAFT_VALUE
# with the need bonuses 12, 20 and 6: 18.7 and 25.1; FR_RESIGN_TARGET 0.55 (more free agents): 14.7 and 13.8, the persistence of the bottom three 0.334
# against 0.371; FR_TEAM_LEVEL -3..+3: 21.3 and 22.0 (the first seasons only); FR_PROGRESS_NOISE (7, -3) (a design rule, measured, not a knob): 17.3 and
# 13.0. No knob reaches a band (none reaches 0 leagues with a streak over 5, none puts every run-season's spread over 1.0), so none moved and the three
# bands are restated by D-078 with these measurements: a team's exact sum keeps a lag-1 correlation of 0.655 from one season to the next (a plain
# model of 32 teams at that correlation, with no draft order, is only a reference: work/sx8p/analyze_bands_sx8p.txt); a single-place group's league
# mean keeps a correlation of 0.80 to 0.89 (a cohort). FR_RESIGN_TARGET is the one knob that lifts the spread: on the same 300 leagues 0.50 gives
# 7.6 percent of the run-seasons under 1.0 and 0.45 gives 3.2 (every season's mean 1.10 and 1.18 at least; the streaks over 5 13.3 and 14.7 percent,
# the persistence 0.324 and 0.330), but the checked runs of 100 leagues (work/simulate_franchise_sx8f_fast_100x20_sx8p_target50.txt and _target45.txt)
# show what it costs: the staff signs again 16.7 and 8.8 percent of the contracts that run out (48 percent at 0.62), the market grows to 211 and 232 free
# agents a league-offseason, and the league's mean cap use falls to 0.658 and 0.640 (CP4's band starts at 0.65: 0.45 FAILS it). It stays 0.62, the market
# SX.8i calibrated (Q-031); it is the knob the owner's playtest may turn if the teams sound too close together in the middle seasons.


# ----- SX.10c, the catalog's offense in the game (NFL_PLAYS_DESIGN 7, D-093). UNVERIFIED start values; SX.10e measures them -----
LIVE_KNEEL = (1, 2)                    # a kneel: the quarterback goes down at once (the clock then runs on, 7-2-1)
LIVE_SPIKE = (1, 1)                    # a spike: the ball hits the ground at once and the clock stops (an incompletion)
RUNOFF_NO_HUDDLE = (20, 28)            # the player's Tempo "no huddle" between plays (normal 30 to 40, hurry up 12 to 20); wrong if
                                       # SX.10e's band of seconds per counted play moves out of 26 to 30 with it set
FR_MODEL_SACK = 40                     # the ratings door: the catalog's sack rate (per 10,000) moves 40 for each point of the ratings'
                                       # sack percent (the original's sack percents are about 2.5 times the league's 6.5 percent)
FR_MODEL_FUMBLE_BASE = 50              # the ratings' fumble steps are steps of the original's 1 in 50 (playtables.FUMBLE_ODDS)


# ----- SX.10d, the defense calls and the kicks of 2026 in the game (NFL_PLAYS_DESIGN 2.6, 4.9, 6, D-094). UNVERIFIED start values;
# SX.10e measures them with the bands -----
COMPUTER_KICKOFF_MIX = (("K001", 55), ("K002", 42), ("K003", 3))   # the computer's kick-off when it does not kick onside: deep 55, short 42
                                       # (2026 about 55 and 45, design 4.9), squib 3; wrong if SX.10e's touchbacks leave 12 to 20 percent
PIN_PUNT_TO_GOAL = 55                  # the computer punts a pin punt when its line is this close to the other goal, else a spread punt
FG_KICK_SPOT = 7                       # the holder's spot: 7 yards behind the line (a field goal of to_goal + 17 yards, RB26 11-4-2)
MISSED_FG_LEAST = 20                   # a missed field goal from inside the 20: the defense's ball at its 20 (RB26 11-4-2, G26-7)
FAIR_CATCH_KICK_SECONDS = 30           # the fair catch kick is offered after a fair catch with at most this many seconds left in a half
FAIR_CATCH_KICK_LONGEST = 65           # and a kick of at most this many yards (the field goal curve is under 30 percent beyond)
FAKE_GAIN_EXTRA = (0, 8)               # a fake kick that works gains the yards to go and 0 to 8 more
FAKE_SHORT_LOSS = 2                    # a fake run that fails ends 2 yards behind the line to a yard short of the line to gain
FR_KICK_MODEL_POINTS = 100             # the ratings door: the field goal's made rate moves 1 point for each step of the original's odds
SAFETY_KICK_TOUCHBACK = 25             # percent of the deep kick's touchbacks a kick from the 20 keeps (it reaches the end zone less)


# ----- SX.10e, the computer's calling over the catalog (NFL_PLAYS_DESIGN 7 and 8, D-095). The calling's own shares are in
# extras/plays/calling.py and calling_data.py; these are the kicks' (UNVERIFIED start values, measured in SX.10e) -----
FAKE_TO_GO = 4                         # the computer fakes a kick only on fourth and this many or fewer
COMPUTER_FAKE_PUNT = 300               # per 10,000 punts with FAKE_TO_GO or fewer to go (league: 0.8 percent of all punt formations)
COMPUTER_FAKE_FIELD_GOAL = 150         # per 10,000 such field goals (no published rate; rarer than the fake punt)
# The bands of SX.3 and SX.6 in a game that plays the catalog (both teams their team playbook, a new player's game): SX.3's foul scale and
# SX.6's goal line rates were calibrated on the original's plays, whose mix has fewer passes and fewer plays ending at the goal line.
# Measured in 10,000 games with the SX.3 and SX.6 values (work/sx10e/integration_bands_sx10e_teams_10000.txt, first run): 14.42 accepted
# fouls a game (band 12.0 to 13.6), 6.28 goal line rulings a game (the original's 1.88), 0.351 coach challenges a team-game (band 0.20 to
# 0.32) and 1.023 booth reviews a game (band 0.5 to 0.8). The values below are set by the sweep of work/sx10e/sweep_bands_sx10e.py
# (3,000 games a setting, reports integration_bands_sx10e_teams_3000_sweep_<a to i>.txt): the foul scale 1.07 gives 12.82 fouls (1.04:
# 12.53, 1.10: 13.15); the goal line rates alone moved the booth (18, 40): 0.549, (25, 55): 0.628) but not the coach challenges (0.343),
# which follow the catch and line rulings the catalog's passes and plays add (42.2 and 10.6 a game against 37.7 and 9.4), so those are
# scaled too, and the wrong windows lowered against the close ones as SX.6 did (53.3 percent of the challenges changed the ruling with
# (5, 13) and (24, 78), band 38 to 52). Setting h, with calling.LATE_PASS_FLOOR 7000 (8000 gave quarters 2 and 4 7.02 more plays than 1
# and 3, band 2 to 7): 12.73 fouls, 0.274 coach challenges a team-game changing 47.4 percent, 0.610 booth reviews changing 72.4, 6.82 more
# plays late; 10,000 games in work/sx10e/integration_bands_sx10e_teams_10000.txt (the chain's second run).
PENALTY_RATE_SCALE_CATALOG = 1.07      # the foul scale of a game that plays the catalog (SX.3's 1.2 for the original's plays)
RULING_RATES_CATALOG = {"goal": (28, 62), "catch": (4, 15), "line": (20, 86)}    # (wrong, close) per 1000 in such a game (SX.6's:
#                                        goal (60, 135), catch (6, 17), line (30, 100); the others as SX.6)
