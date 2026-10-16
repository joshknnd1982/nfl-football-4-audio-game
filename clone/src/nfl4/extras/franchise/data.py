"""The fixed rules of the Franchise: the scale, the places, the groups, the stages (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 4, 6.3, 9 and 10: the numbers here are design RULES (the scale 40 to 99, the 34 places, the weights of a
team's strength, the files); the values a session calibrates live in `extras\\tuning.py` (names `FR_...`). Plain data: no reference
to the game, the speech or the files.
"""
from __future__ import annotations

FORMAT = 1                                   # league.sav's format; a higher one is "a newer version" (design 10.1)
GAME_MARKER = "NFL Football 4 franchise"
FOLDER = "franchise"                         # the folder of the data folder that holds every franchise file
LEAGUE_FILE, PREVIOUS_FILE, HISTORY_FILE, SAVED_FILE = "league.sav", "league.previous.sav", "history.txt", "football.sav"
OLD_FOLDER = "old"                           # archived franchises: old\league-1.sav and old\history-1.txt (the three newest)
OLD_COPIES = 3
SAVE_MAX_BYTES = 8_000_000                   # FR_SAVE_MAX_BYTES: a larger file is damage without being read (a league of 20
#                                              seasons is under 1,000,000)

RATING_MIN, RATING_MAX, RATING_NEUTRAL = 40, 99, 70
AGE_MIN, AGE_MAX = 21, 40
STAR_PEAK = 85                               # a retired or released player with a peak of at least this is kept for history
RETIRE_FROM_AGE = 30                         # design 6.3: a player under 30 never retires and never draws (invariant I1)
RETIRE_DRAW = 1000                           # the retirement chance is per mille: one draw below(1000) against it
STARS_NAMED = 3                              # the other teams' retiring stars named in stage 2 (design 6.3)
MAX_SEASONS = 9999
TEAMS = 32
POTENTIALS = ("high", "average", "low")

# the ten position groups (design 4.2); a player belongs to one position for life
POSITIONS = ("RB", "WR", "QB", "DL", "LB", "CB", "S", "RET", "K", "P")
POSITION_TEXT = {"RB": "NXL-01", "WR": "NXL-02", "QB": "NXL-03", "DL": "NXL-04", "LB": "NXL-05", "CB": "NXL-06", "S": "NXL-07",
                 "RET": "NXL-08", "K": "NXL-09", "P": "NXL-10"}
GROUP_TEXT = {"RB": "NXL-11", "WR": "NXL-12", "DL": "NXL-14", "LB": "NXL-15", "CB": "NXL-16", "S": "NXL-17", "RET": "NXL-18",
              "QB": "NXL-03", "K": "NXL-09", "P": "NXL-10"}           # the groups of one place use the position's own word
POTENTIAL_TEXT = {"high": "NXK-20", "average": "NXK-21", "low": "NXK-22"}   # the potential words (rows added by SX.8b for the roster)

# the original's slots (spec 5.5, H7): (section heading of footplay.txt, number in it, position). The order is footplay.txt's,
# then the quarterback; a place is its index 0 to 33 in a team's roster list.
_DEFENSE = ["DL"] * 6 + ["LB"] * 5 + ["CB"] * 4 + ["S"] * 2
PLACES: tuple[tuple[str, int, str], ...] = tuple(
    [("Running Backs:", n, "RB") for n in range(1, 7)]
    + [("Receivers:", n, "WR") for n in range(1, 7)]
    + [("Defensive Players:", n, position) for n, position in enumerate(_DEFENSE, start=1)]
    + [("Special Teams Players:", n, "RET") for n in range(1, 3)]
    + [("Kickers:", 1, "K"), ("Kickers:", 2, "P")]
    + [("Quarterback:", 1, "QB")])
PLACE_COUNT = len(PLACES)                    # 34
POSITION_OF_PLACE = tuple(position for _, _, position in PLACES)
PLACES_OF = {position: tuple(i for i, p in enumerate(POSITION_OF_PLACE) if p == position) for position in POSITIONS}
GROUP_SIZE = {position: len(places) for position, places in PLACES_OF.items()}
ROSTER_ORDER = ("QB", "RB", "WR", "DL", "LB", "CB", "S", "RET", "K", "P")      # the order the groups are listed and spoken in

# the weights of a team's strength (design 4.4): they follow how often the engine reads each place; the sum is 78
WEIGHT = {"QB": 12, "RB": 2, "WR": 2, "DL": 2, "LB": 2, "CB": 2, "S": 2, "K": 4, "P": 2, "RET": 1}
WEIGHT_SUM = sum(WEIGHT[position] for position in POSITION_OF_PLACE)
WEIGHT_OF_KEY = {(heading, number): WEIGHT[position] for heading, number, position in PLACES}   # the key of Roster.ratings

# the stages of an offseason (design 3.3): (the stage's number, the id of its name). A later session inserts its stage here, so
# the spoken "stage n of m" follows the list. SX.8a built stages 1 and 6, SX.8c added 2 (aging and retirement) and 3 (progression
# and regression); SX.8d adds 4 (the draft) and 5 (the roster cut and the fill).
STAGES: tuple[tuple[int, str], ...] = ((1, "NXE-11"), (2, "NXE-12"), (3, "NXE-13"), (4, "NXE-14"), (5, "NXE-15"), (6, "NXE-16"))

# the draft (design 7): seven rounds of one pick for each team, in the same order in every round
DRAFT_ROUNDS = 7
DRAFT_PICKS = DRAFT_ROUNDS * TEAMS           # 224
RANGE_SPAN = 6                               # the spoken range of a prospect: the low end to the low end + 6 (about 62 to 68)
RANGE_MIDDLE = 3                             # the middle of that range: the low end + 3
MAX_ROOKIES = DRAFT_ROUNDS                   # the rookies a team can have waiting for the cut (one a round)
CUT_FLOOR_GROUP_MAX = 2                      # the cut's rating floor (tuning FR_CUT_FLOOR) is for groups of this many places or fewer
STAGE_REVIEW, STAGE_AGING, STAGE_DEVELOPMENT, STAGE_DRAFT, STAGE_CUT, STAGE_NEW_SEASON = 1, 2, 3, 4, 5, 6

# the rounds a team can last in, for the history (the finish)
FINISH_MISSED, FINISH_WILD_CARD, FINISH_DIVISION, FINISH_CHAMPIONSHIP, FINISH_SUPER_BOWL, FINISH_CHAMPION = range(6)
FINISH_TEXT = {FINISH_MISSED: "NXE-22", FINISH_WILD_CARD: "NXE-23", FINISH_DIVISION: "NXE-24", FINISH_CHAMPIONSHIP: "NXE-25",
               FINISH_SUPER_BOWL: "NXE-26", FINISH_CHAMPION: "NXE-27"}
# the stage of a game for H14's game_played, and the play-off round it is (0: a regular week)
REGULAR, WILD_CARD, DIVISION, CHAMPIONSHIP, SUPER_BOWL = "regular", "wild_card", "division", "championship", "super_bowl"
STAGE_CODE = {REGULAR: 0, WILD_CARD: 1, DIVISION: 2, CHAMPIONSHIP: 3, SUPER_BOWL: 4}
CODE_STAGE = {code: stage for stage, code in STAGE_CODE.items()}
# the finish of the team that LOSES in a round
LOST_IN = {WILD_CARD: FINISH_WILD_CARD, DIVISION: FINISH_DIVISION, CHAMPIONSHIP: FINISH_CHAMPIONSHIP, SUPER_BOWL: FINISH_SUPER_BOWL}

# the play-off coin of a computer game leans by strength within these per mille (design 5.2; 500 is the original's coin)
PLAYOFF_CHANCE_MIN, PLAYOFF_CHANCE_MAX = 250, 750
# the original's score table has 32 entries (game\playoffs.py SCORE_TABLE): a shifted index stays in 1 to 32
SCORE_TABLE_SIZE = 32

MAX_RESULTS = 400                            # games of one season (16 weeks of 16 games and 13 play-off games), with room
MAX_HISTORY = 500                            # seasons kept
