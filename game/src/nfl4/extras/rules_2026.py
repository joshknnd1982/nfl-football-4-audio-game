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
# overtime warnings (SRC-OFFICIAL, SX.13: 16-1-3 (e) gives the regular season's period the fourth period's timing, 16-1-4 (h) times the
# end of play-off period 2 as the end of the first half and of period 4 as the end of the fourth; 15-3-9 (b), (c) speak of the
# "overtime half in the postseason"): at 2:00 of the regular season's period and of play-off periods 2 and 4 (every second one after
# them: the game's reading where the book stops at the fourth)
OT_POST_WARNING_EVERY = 2
LATE_FIRST_HALF_SECONDS = 120          # 4-3-2: in the last 2:00 of the first half a runner out of bounds stops the clock
FIVE_MINUTE_RULE_SECONDS = 300         # 4-3-2(a)(3), 4-3-2(e)(2): the last 5:00 of the second half; overtime alike (Part 1.5)
PLAY_CLOCK = 40                        # 4-6: bounds the runoff ranges only
FIELD_GOAL_MAX_CLOCK = 5               # 11-4-2 Note 5: a field goal attempt runs at most 5 seconds off
TRY_UNTIMED = True                     # 4-3-2(h), 11-3-1: the extra point and the two-point try take no time
NO_TRY_THAT_CANNOT_MATTER = True       # 4-8-2 (c): no try after a touchdown during the down in which the fourth period expired, when a
#                                        good try would not affect the outcome (SX.13; also the regular season's overtime, 16-1-3 (e))

# ----- overtime (SX.12, Rule 16 of the 2026 book, printed pages 64 to 66; NFL_RULES_RESEARCH Part 7) -----
OT_TOSS_VISITOR_CALLS = True           # 16-1-2: at the end of regulation a new toss, the visiting team's captain calls it (4-2-2)
OT_TOSS_NO_DEFER = True                # 4-2-2's deferral is "to the second half"; overtime has none: the winner receives or kicks (reading)
OT_BOTH_POSSESS = True                 # 16-1-3 (a), 16-1-4 (a): both teams must have the opportunity to possess the ball once ...
OT_SAFETY_WINS = True                  # ... unless the kicking team scores a safety on the receivers' initial possession: it wins
OT_NEXT_SCORE_WINS = True              # 16-1-3 (b), (c): then the side ahead wins; a first possession without a score, or a tie after
#                                        both, makes the next score by any method the winner
OT_REGULAR_PERIODS = 1                 # 16-1-3 (d): at most one 10-minute period in the regular season, even when the second team has
OT_REGULAR_TIE = True                  # not had its possession; tied at its end, the game is a tie
OT_POST_UNTIL_WINNER = True            # 16-1-4 (d): play-off periods of 15 minutes, as many as needed; a period also follows when the
#                                        second team's initial possession has not ended
OT_POST_LOSER_CHOOSES_PERIOD = 3       # 16-1-4 (e): the captain who lost the toss has the first choice at the third period
OT_POST_NEW_TOSS_AFTER = 4             # 16-1-4 (i): after the fourth period another toss (the game repeats the pattern: periods 5, 9, ...)
OT_KICK_IS_OPPORTUNITY = True          # 16-1-5 (c): a kick-off is the receivers' opportunity to possess, even when the kickers recover it
OT_NO_COACH_CHALLENGES = True          # 16-1-5 (d): the replay official starts every review (15-1-2 (b); NO_COACH_CHALLENGE_IN_OVERTIME)
OT_TRY_NOT_IN_SUDDEN_DEATH = True      # 4-8-2 (c): no try after a touchdown that ends a sudden-death overtime (the game is decided)

# ----- timeouts -----
TIMEOUTS_PER_HALF = 3                 # 4-5-1 Item 1: three charged timeouts each half, no carry-over
OT_REGULAR_TIMEOUTS = 2                # 16-1-3 (e): two in the one regular-season period
OT_POST_TIMEOUTS = 3                   # 16-1-4 (g): "three timeouts during a half", a pair of play-off overtime periods (SRC-OFFICIAL)
ONE_CHARGED_TIMEOUT_PER_DEAD_BALL = True   # 4-5-1 Item 3
# A request with no timeout left is ignored (4-5-1 Item 3): the game's menu refuses it with a sentence and never grants
# it, so the delay-of-game foul for a granted excess timeout and the foul of 4-5-1 Item 4 cannot arise (design 4).

# ----- penalties (SX.3; the fouls themselves are extras/fouls_2026.py; NFL_RULES_RESEARCH Part 6) -----
HALF_DISTANCE = True                   # 14-2-1: never more than half the distance from the spot of enforcement to the
#                                        offender's goal line; not for the spot fouls (pass interference, 8-5) nor for
#                                        intentional grounding at the spot of the pass (8-2-1). The game has whole yards
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
NO_RUNOFF_FOULS = ()                   # SX.13: 4-7-1 (a) names "a foul by either team that stops the clock during any dead ball
#                                        period", so delay of game after the warning has the run off too (was ("DOG",), Part 1.5's
#                                        default)
PLAY_CLOCK_AFTER_PENALTY = 25          # 4-6-2 (e), 4-6-3: after a penalty the play clock is 25; it bounds the runoff
RUNOFF_PLAY_CLOCK = 30                 # 4-6-3 (c): after a ten-second run off the play clock is 30
UNTIMED_DOWN = True                   # 4-8-2 (a): an accepted foul by the defense on the last play of a half gives the
#                                        offense one untimed down
ONE_PENALTY_PER_TEAM = True            # 14-1-3: the offended team chooses one penalty of a multiple foul
DOUBLE_FOUL_REPLAY = True              # 14-5-1: fouls by both teams offset and the down is played again (no choice);
MAJOR_AGAINST_MINOR = 15               # Exception 1: a 15-yard foul against a 5-yard foul with no automatic first down,
#                                        loss of down or run off is enforced alone

# ----- challenges and reviews (SX.6; NFL_RULES_RESEARCH Part 3) -----
CHALLENGES_PER_GAME = 2                # 15-1-1 (f): two challenges for each team in a game ...
CHALLENGE_THIRD_AFTER_WINS = 1         # ... and a third once at least ONE of them changed the ruling (2024 amendment)
CHALLENGES_MAX = 3                     # 15-1-1 (f): a fourth is never allowed
CHALLENGE_NEEDS_TIMEOUT = True         # 15-1-1 (d): a team with no time out in hand may not challenge
LOST_CHALLENGE_CHARGES_TIMEOUT = True  # 15-1-1 (e), 15-6-1: an unsuccessful challenge costs a time out, a won one costs nothing
NO_COACH_CHALLENGE_AFTER_WARNING = True    # 15-1-2 (a): a play that BEGINS after the two-minute warning is the replay official's
NO_COACH_CHALLENGE_IN_OVERTIME = True      # 15-1-2 (b), 16-5-d
BOOTH_ONLY_SCORES_AND_TURNOVERS = True     # 15-1-2 (c) to (e): scores, tries, turnovers and a failed fourth down are the replay
#                                            official's (he may start a review of them, no time out is charged, no cap)
CLEAR_AND_OBVIOUS = True               # 15-2-1: a ruling is changed only on clear and obvious video evidence
# The game has no sidelines of its own, no pass interference to review and no video; the reviewable aspects it models are the
# five of design 6.1 (15-3-2 catch or no catch, 15-3-3 down by contact and fumble, 15-3-4 goal line, 15-3-5 boundary line,
# 15-3-7 line to gain). Judgment fouls are never reviewable (15-4). A review looks at every reviewable aspect of the play, not
# only the stated one (15-2-2).

# ----- free kicks and the onside kick (SX.4; NFL_RULES_RESEARCH Part 5) -----
KICKOFF_SPOT = 35                      # 6-1-2: a kick-off is made from the kicking team's own 35
EXTRA_POINT_DISTANCE = 33              # 11-3-1 (b): the try kick is snapped from the 15 (a kick of about 33 yards; SX.10d, G26-4)
KICKOFF_TOUCHBACK = 35                 # 6-2: a 2026 kick-off touchback (one into the landing zone that goes into the end zone: the 20)
KICK_OUT_OF_BOUNDS = 40                # 6-2-1: a free kick out of bounds, and a kick short of the landing zone, at the receivers' 40
PUNT_TOUCHBACK = 20                    # 11-6: a punt's touchback
SAFETY_KICK_SPOT = 20                  # 11-5-2, 6-1-6 (b): the team scored upon kicks from its own 20; an onside kick too
ONSIDE_ANY_TIME = True                 # 6-1-6 (2026): the kicking team may declare an onside kick at any time of the game,
#                                        whatever the score and the period; the declaration is told to the receivers, so
#                                        no kick is a surprise (the game's computer and player both declare first)
ONSIDE_MIN_DISTANCE = 10               # 6-1-6 (e), 6-2-5: the kicking team may touch the ball only after a receiver did or
#                                        after it has gone 10 yards (the receivers' restraining line); the game's kick
#                                        goes 8 to 14 yards (a receiver may touch it first) and keeps this as a record
ONSIDE_FOUL_YARDS = 5                  # 6-1-6 penalty, 6-2-5 Item 1, 6-3-1: loss of five yards, the kick made again; for an
#                                        illegal touch the receivers may take the ball at the spot instead
