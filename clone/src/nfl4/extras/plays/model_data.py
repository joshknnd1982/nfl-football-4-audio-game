"""The NFL numbers the play models are calibrated to (nfl4 only, rule 0.13; NX-P3; design `spec/NFL_PLAYS_DESIGN.md` section 4).
This is inspired by Jim Kitchen.

Every table names its source and seasons. "COMPUTED" means computed in SX.10b (2026-10-20) from public data the owner approved
(Q-P15, D-090): the nflverse play-by-play of the regular seasons 2024, 2025 and 2026 to week 6, and FTN Data's charting and
participation files via nflverse (CC-BY-SA 4.0; credit: "FTN Data via nflverse"); the script is `work/sx10b/analyze_data.py`
and its full output `work/sx10b/data_numbers_sx10b.txt`. Those numbers are facts about plays (SRC-SECONDARY: the data is a
volunteer project's and a charting company's, not the league's). The published figures of `spec/NFL_PLAYS_RESEARCH.md` section 8
agree within their rounding (league 2024: completion 65.3, 7.13 yards an attempt, 2.17 percent interceptions; ours 65.6, 7.16,
2.2). Nothing here is drawn from: the models in `model.py` read these numbers.

Units: a rate is in parts per ten thousand (6500 = 65.00 percent), so a draw is `rnd.below(10000) < rate`; a share list is in
the same unit and sums to about 10000 (the model normalizes); yards are whole numbers.
"""
from __future__ import annotations

CREDIT = "Play-by-play from nflverse; charting and participation from FTN Data via nflverse (CC-BY-SA 4.0)."
SCALE = 10000

# ----- passing (COMPUTED, 2024 and 2025 regular seasons, 35,096 attempts, 39,848 drop-backs) -----

BANDS = ("behind", "0-4", "5-9", "10-14", "15-19", "20-29", "30+")       # air yards of the target
BEHIND, SHORT, MID, INTER, DEEP_IN, DEEP, BOMB = range(7)
# the whole-number range an air-yards draw takes in each band; the middle of each is the mean air of the band's completions
# (-3.47, 2.43, 6.25, 11.89, 16.82, 23.13, 37.62)
AIR_RANGE = ((-6, -1), (0, 5), (4, 9), (10, 14), (15, 19), (20, 26), (30, 45))
BAND_SHARE = (1800, 2630, 2300, 1210, 910, 720, 430)          # share of all attempts by band
BAND_COMP = (7800, 7470, 6860, 5620, 5170, 3970, 2900)          # completion by band
BAND_INT = (80, 110, 170, 280, 400, 490, 680)                   # interceptions by band, per attempt
# yards after the catch by band: shares of (0 or less, 1 to 4, 5 to 9, 10 to 19, 20 or more) and the mean of the 20+ bin
YAC_SHARE = ((510, 1900, 3650, 3210, 730), (2270, 3870, 2460, 1150, 250), (3330, 4090, 1750, 660, 170),
             (4330, 3350, 1350, 700, 270), (3800, 3420, 1560, 850, 380), (2890, 3680, 1900, 1020, 510),
             (3040, 3110, 1870, 1110, 880))
YAC_MEAN = (930, 467, 339, 331, 398, 519, 615)                  # mean yards after the catch, in hundredths of a yard
YAC_MID_RANGE = (10, 16)                                        # the 10 to 19 bin: its mean is 12.8 to 13.3 in every band
YAC_LONG_MEAN = (28, 28, 29, 29, 30, 34, 31)                    # the mean of the 20+ bin by band
LEAGUE_PASS = {"completion": 6510, "yards_per_attempt": 711, "interception": 220, "sack_per_dropback": 650,
               "scramble_per_dropback": 540, "yards_per_completion": 1092, "touchdown_per_attempt": 460,
               "throw_away_per_dropback": 357}                  # yards in hundredths

# the coverages of FTN's participation file: (attempts by band, completion by band, interceptions by band, blitz share)
# one-high: COVER_0, COVER_1, COVER_3; two-high: COVER_2, 2_MAN, COVER_4, COVER_6, COVER_9 (NGS's grouping)
COVERAGE_BANDS = {
    "COVER_0": ((184, 610, 337, 122, 75, 79, 50), (6680, 5850, 5280, 4590, 4670, 3160, 4200), (270, 180, 240, 250, 130, 250, 200), 7150),
    "COVER_1": ((1515, 2366, 2417, 1448, 1070, 955, 524), (7360, 6870, 6300, 5400, 4820, 3480, 2710), (100, 110, 170, 220, 280, 410, 440), 4180),
    "COVER_2": ((1747, 2254, 1750, 703, 557, 469, 208), (8050, 8040, 7170, 5870, 5400, 4710, 2880), (60, 120, 140, 460, 540, 580, 1200), 1740),
    "2_MAN": ((341, 479, 567, 299, 193, 151, 75), (8210, 7330, 6510, 5050, 3730, 2720, 2400), (60, 60, 90, 230, 360, 730, 400), 1440),
    "COVER_3": ((1522, 2151, 1731, 967, 759, 511, 349), (7890, 7840, 7370, 6160, 5700, 4620, 3120), (80, 100, 190, 230, 490, 530, 830), 2830),
    "COVER_4": ((517, 705, 697, 364, 218, 161, 153), (8090, 7930, 7330, 5490, 5460, 4410, 3270), (60, 100, 230, 250, 460, 310, 390), 1880),
    "COVER_6": ((262, 397, 338, 177, 172, 105, 80), (7670, 7510, 7600, 5710, 5760, 4670, 2380), (40, 150, 120, 400, 410, 860, 880), 1550),
    "COVER_9": ((121, 170, 148, 99, 75, 58, 42), (7850, 7820, 7360, 5560, 4670, 3450, 2860), (170, 60, 270, 300, 130, 340, 1430), 1540),
}
TWO_HIGH = ("COVER_2", "2_MAN", "COVER_4", "COVER_6", "COVER_9")
MAN_COVERAGES = ("COVER_0", "COVER_1", "2_MAN")
COVERAGE_SHRINK = 60            # a cell's own attempts against this many of the band's league rate (empirical shrinkage;
                                # 150 pulled Cover 0's small cells six points above its data, SX.10b)
# completion by band, man and zone (the route profiles' man and zone split is measured against this)
MAN_COMP = (7440, 6760, 6230, 5290, 4660, 3360, 2790)
ZONE_COMP = (7960, 7900, 7300, 5890, 5530, 4520, 2980)
# completion, blitz minus no blitz, by band (a call that blitzes more or less than its coverage's usual share)
BLITZ_COMP = (-1010, -550, -340, 110, -350, -620, 220)
BLITZ_INT = (130, 110, 120, 100, 90, 70, 80)                    # interception multiplier, blitz against no blitz, in percent
                                                                # (behind the line 1.3 against 0.6 is a small count: kept at 130)
THROW_AWAY_BY_RUSHERS = {3: 290, 4: 340, 5: 390, 6: 450}       # legal throw-aways per drop-back: FTN 3.6 percent in all; the
                                                                # split by rushers is UNVERIFIED (more rushers, more pressure)
# sacks per drop-back by the number of rushers and the shell (one-high, two-high)
SACK_BY_RUSHERS = {3: (510, 530), 4: (570, 590), 5: (920, 1020), 6: (1140, 1350)}   # 2026-10-23, a tester: "blitzes rarely get home"
#                 (before: 4: (600, 620), 5: (720, 820), 6: (840, 1100), the charting's own rates; the league's total stays in its band)
RUSHER_SHARE = {2: 100, 3: 330, 4: 6910, 5: 1990, 6: 660}         # share of drop-backs (2 is two or fewer, 6 is six or more)
BLITZ_SHARE = 2910                                               # drop-backs with one or more blitzers

# play action against the same band without it: completion points, the interception multiplier, a yard after the catch
PLAY_ACTION_COMP = (-70, 140, -770, 520, 1320, 920, 710)
PLAY_ACTION_INT = 78            # percent: 1.8 against 2.3 per attempt
PLAY_ACTION_YAC = 1             # yards: the completions of a fake gain about one more yard in every band
PLAY_ACTION_SACK = 88           # percent: 5.9 against 6.7 per drop-back
PLAY_ACTION_SHARE = 2290        # of charted drop-backs; NFL_PLAYS_RESEARCH 2.7 (PFF 25.65 percent of plays) counts differently
# motion and formation (selection is in these, so they are kept small; design 4.6)
MOTION_COMP = 150               # completion points with motion (66.8 against 63.3; half of it kept)
MOTION_INT = 90                 # percent (2.0 against 2.4)
MOTION_SACK = 93                # percent (6.3 against 6.8)
FORMATION_SACK = {"under_center": 88, "shotgun": 103, "pistol": 85, "empty": 109}     # percent
FORMATION_RUN_SHIFT = {"under_center": -10, "shotgun": 10, "pistol": 20}               # hundredths of a yard a carry

# the routes FTN charts for the targeted receiver: the band shares, completion, interceptions, yards after the catch (hundredths),
# completion against man and against zone, and the share of completions that end out of bounds
ROUTES = {
    "quick_out": ((1350, 5810, 2670, 140, 20, 10, 0), 7530, 86, 448, 7250, 7710, 3740),
    "hitch": ((440, 3770, 4000, 1150, 460, 150, 20), 7500, 159, 336, 6400, 7850, 700),
    "screen": ((9220, 700, 50, 10, 0, 10, 10), 8600, 60, 975, 8430, 8700, 1330),
    "dig": ((90, 720, 2000, 3620, 2490, 1030, 60), 5940, 424, 368, 5600, 6190, 710),
    "go": ((10, 250, 450, 850, 1830, 3510, 3090), 3500, 403, 492, 3120, 3970, 2090),
    "deep_out": ((40, 320, 2110, 3870, 2650, 920, 100), 5380, 262, 190, 5330, 5430, 5230),
    "drag": ((1180, 5560, 2620, 470, 130, 30, 0), 7180, 122, 576, 6420, 7790, 1830),
    "slant": ((220, 2520, 6200, 830, 190, 30, 10), 6780, 236, 457, 6270, 7380, 300),
    "swing": ((8430, 1290, 170, 30, 40, 30, 0), 8310, 52, 966, 7830, 8450, 3320),
    "post": ((40, 260, 1510, 2410, 2070, 1780, 1920), 5460, 628, 539, 5650, 5340, 450),
    "corner": ((20, 770, 1040, 1430, 2290, 2990, 1460), 4410, 437, 488, 4240, 4610, 2490),
    "wheel": ((200, 1020, 1330, 1870, 2890, 2350, 340), 4840, 198, 658, 4650, 5100, 2920),
    "angle": ((660, 6340, 2590, 380, 0, 0, 30), 7510, 221, 545, 7290, 7600, 210),
}
ROUTE_SHARE = {"quick_out": 1870, "hitch": 1790, "screen": 990, "dig": 890, "go": 820, "deep_out": 740, "drag": 680,
               "slant": 600, "swing": 500, "post": 500, "corner": 440, "wheel": 100, "angle": 90}    # of targets with a route
SCREEN_SACK = 3                  # percent of the drop-back sack rate on a screen (FTN marks the throw; a screen is almost never sacked)
RPO_PASS = {"completion": 8410, "yards_per_attempt": 535, "interception": 50, "sack_per_dropback": 140}
RPO_SHARE_OF_PLAYS = 470         # run and pass together, of scrimmage plays (FTN); about three quarters end as runs
TRICK_PASS = {"completion": 6150, "yards_per_attempt": 1011, "interception": 330, "sack_per_dropback": 1110}

# ----- running (COMPUTED, 2024 and 2025; non-quarterback runs outside the opponent's 10 unless named) -----

RUN_BINS = ("loss", "no gain", "1-3", "4-6", "7-9", "10-19", "20+")
RUN_RANGES = (None, (0, 0), (1, 3), (4, 6), (7, 9), (10, 16), None)     # loss and 20+ have their own tables
# by the gap the run goes through (middle is the center, guard the A and B gaps, tackle the C gap, end outside)
RUN_BY_GAP = {
    "middle": (760, 700, 3720, 2770, 1130, 790, 140),
    "guard": (650, 780, 3820, 2760, 1040, 740, 190),
    "tackle": (850, 790, 3730, 2340, 1160, 850, 290),
    "end": (1370, 700, 2790, 2220, 1300, 1230, 380),
    "all": (890, 750, 3540, 2530, 1150, 890, 250),
}
RUN_YPC_BY_GAP = {"middle": 430, "guard": 443, "tackle": 470, "end": 515, "all": 463}      # hundredths, outside the 10
# by the defenders in the box (all gaps): the model multiplies a gap's bins by box / all
RUN_BY_BOX = {
    5: (710, 540, 2880, 2690, 1590, 1320, 270),
    6: (850, 700, 3420, 2620, 1240, 920, 240),
    7: (910, 770, 3730, 2480, 1050, 820, 230),
    8: (1210, 1100, 3840, 2010, 760, 760, 330),
}
BOX_SHARE_ON_RUNS = {5: 400, 6: 5250, 7: 3470, 8: 870}
RUN_LOSS = ((-1, 4340), (-2, 2570), (-3, 1450), (-4, 740), (-5, 460), (-6, 150), (-7, 120), (-8, 50), (-9, 40), (-10, 40))
RUN_LONG = (((20, 29), 5750), ((30, 39), 1810), ((40, 49), 1120), ((50, 69), 990), ((70, 95), 330))   # 20+: mean 33
LEAGUE_RUN = {"yards_per_carry": 437, "outside_10_yards_per_carry": 463, "stuffed": 1750, "ten_plus": 1040,
              "fumble": 80, "fumble_lost_share": 5750, "out_of_bounds": 510}
# PFF's yards a carry by run concept, 2020 to 2022 (SRC-SECONDARY, NFL_PLAYS_RESEARCH 8): the concepts' small shifts
CONCEPT_YPC_PFF = {"inside_zone": 390, "outside_zone": 378, "duo": 371, "power": 453, "counter": 390, "pull_lead": 385,
                   "draw": 595}
QB_DESIGNED = (1410, 690, 2790, 2130, 1400, 1270, 310)          # quarterback designed runs, not sneaks (963 runs, 4.87 a carry)
QB_SNEAK = (90, 1730, 7890, 230, 20, 40, 0)                     # sneaks (527, 1.57 a carry; 81.8 percent of 1-to-go converted)
SCRAMBLE = (0, 10, 2620, 2770, 1870, 2200, 530)                 # 2,151 scrambles, 7.66 a carry
RPO_RUN = (650, 700, 3670, 2870, 1210, 670, 230)                # 2,325 run-pass options that ended as runs, 4.57 a carry
TRICK_RUN = (1480, 510, 2250, 1990, 1480, 1820, 470)            # 236 trick runs (end arounds, reverses), 5.46 a carry
SHORT_YARDAGE_CONVERTED = 6700  # 3rd or 4th and 1 or 2, non-quarterback runs
# runs that start inside the opponent's 5 (1,287 runs: 1.05 a carry, 38.2 percent touchdowns) against all runs (24,612), the bins
# loss, no gain, 1-3 and 4 or more; the model multiplies a run's bins by inside / all within 5 yards of the goal line
GOAL_LINE_RUNS = ((1530, 940), (1830, 810), (5700, 3660), (930, 4590))
QB_LONG_RANGE = (20, 40)        # the 20+ bin of a quarterback run: its mean is 30.3 (non-quarterbacks 33.0)
QB_LOSS_EXTRA = 5000            # a quarterback's loss is one yard deeper half the time (loss mean -2.83 against -2.22)
QB_RUN_FUMBLE = (300, 4300)     # designed quarterback runs: fumbles per run, the share lost

# ----- turnovers (COMPUTED, 2024 and 2025) -----

FUMBLE = {"run": (90, 5750), "completion": (100, 4830), "sack": (1140, 5020), "scramble": (100, 4550)}  # (per play, lost share)
FUMBLE_RETURN_TD = {"run": 530, "completion": 450, "sack": 1280}     # of lost fumbles
INTERCEPTION_RETURN_TD = 740    # of interceptions
# the returns that are not touchdowns (low, high, share): of all interceptions 43.0 percent are not returned, 24.5 go 20 yards or
# more and 7.7 go 40 or more (most of those are the touchdowns), the median is 3 and the 75th percentile 19 (767 interceptions)
INTERCEPTION_RETURN = ((0, 0, 4640), (1, 9, 2380), (10, 19, 1130), (20, 39, 1550), (40, 99, 300))

# ----- kicks (COMPUTED; the 2026 kick-off from 2026 weeks 1 to 6 with the 2025 return shapes) -----

KICKOFF_2026 = {"touchback": 1560, "out_of_bounds": 80, "returned": 8190, "return_td": 10}
KICKOFF_2025 = {"touchback": 2110, "out_of_bounds": 140, "returned": 7600, "return_td": 20}
KICKOFF_RETURN = (((5, 14), 350), ((15, 24), 4250), ((25, 34), 4580), ((35, 49), 630), ((50, 99), 190))  # return yards
PUNT = {"gross_mean": 4721, "blocked": 50, "touchback": 760, "fair_catch": 2720, "downed": 1170, "out_of_bounds": 1020,
        "inside_20": 4030, "returned": 3640, "return_mean": 1179, "return_td": 60, "muffed_lost": 90}
PUNT_GROSS_PERCENTILES = ((10, 36), (25, 41), (50, 47), (75, 54), (90, 59))
PUNT_RETURN = (((0, 0), 0), ((1, 5), 2500), ((6, 9), 2400), ((10, 14), 2600), ((15, 19), 1420), ((20, 39), 780),
               ((40, 99), 300))
FIELD_GOAL = (((18, 29), 9770, 20, 519), ((30, 39), 9430, 190, 690), ((40, 44), 8450, 140, 367), ((45, 49), 7690, 360, 363),
              ((50, 54), 7330, 250, 397), ((55, 59), 6790, 140, 212), ((60, 70), 4440, 670, 45))   # (distance, made, blocked, n)
FIELD_GOAL_ESPN_2025 = {"20-29": 9810, "30-39": 9300, "40-49": 8430, "50+": 6880, "all": 8560}   # SRC-SECONDARY, research 8
EXTRA_POINT = {"good": 9520, "blocked": 90}                     # 2,943 tries 2024 to 2026; ESPN 2025: 95.9
TWO_POINT = {"run": 5410, "pass": 4220, "run_tries": 74, "pass_tries": 232}
TWO_POINT_TRY_SHARE = 980       # of touchdowns followed by a try for two in 2024 (Fox, SRC-SECONDARY)
KNEELS_PER_GAME, SPIKES_PER_GAME = 154, 29                     # hundredths, both teams
FAKE_PUNT = {"share_of_punt_formations": 80, "success": 5000}  # 32 fakes in 4,011 punt formations; first down or touchdown
LATERALS_PER_PLAY = 6           # per 10,000 plays (40 of 65,950)
NO_HUDDLE_SHARE = 1100          # of scrimmage plays (play-by-play flag)

# ----- the defense's mix (COMPUTED from FTN unless named) -----

COVERAGE_SHARE = {"COVER_1": 2950, "COVER_3": 2270, "COVER_2": 2180, "COVER_4": 800, "2_MAN": 610, "COVER_6": 440,
                  "COVER_0": 400, "COVER_9": 210, "COMBO": 120, "BLOWN": 10}
NGS_2025 = {"two_high": 4200, "COVER_2": 1390, "COVER_4": 1720, "COVER_6": 920}     # SRC-OFFICIAL (NGS); a different grouping
DEFENSIVE_BACKS_SHARE = {3: 100, 4: 2630, 5: 6260, 6: 940, 7: 30}
# drop-backs over all plays by down and distance (the computer's calling, SX.10e)
PASS_RATE = {"1st": 4980, "2nd 1-3": 3620, "2nd 4-7": 5570, "2nd 8+": 7490, "3rd 1-2": 3870, "3rd 3-6": 8720,
             "3rd 7+": 9220, "4th": 6630}
SCREEN_SHARE, MOTION_SHARE, TRICK_SHARE = 840, 5160, 40          # of charted drop-backs
TIME_TO_THROW = 267             # hundredths of a second (participation, 2024 and 2025)
