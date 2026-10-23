"""The fixed rules of the Franchise: the scale, the places, the groups, the stages (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 4, 6.3, 9 and 10: the numbers here are design RULES (the scale 40 to 99, the 34 places, the weights of a
team's strength, the files); the values a session calibrates live in `extras\\tuning.py` (names `FR_...`). Plain data: no reference
to the game, the speech or the files.
"""
from __future__ import annotations

FORMAT = 14                                  # league.sav's format; a higher one is "a newer version" (design 10.1). 2 adds the contracts,
#                                              3 (SX.8h) the stage of the expiring contracts in progress (`LeagueRecord.resign`),
#                                              4 (SX.8i) the market of free agency in progress (`LeagueRecord.market`),
#                                              5 (SX.8j) the trades of the season and the picks of the coming draft (`LeagueRecord.trades`),
#                                              6 (SX.8k) the injuries of the season, the stand-ins and the week's injury report (`LeagueRecord.injuries`),
#                                              7 (SX.8l) the staff: the head coaches with their job rating and goal, the coordinators, the stage in progress (`LeagueRecord.staff`)
#                                              8 (SX.8m) the compensatory picks awarded (`comp`), the first-round picks owed for a later draft (`future_picks`), the
#                                                non-exclusive tag with its history of salaries (`tags`), the market's moves (`market["moves"]`), a draft's
#                                                compensatory picks (`draft["comp"]`)
#                                              9 (SX.8n) the people: the morale of the players, the holdouts of the last camp, the trade demands, the player's game goal and
#                                                its verdict (`LeagueRecord.people`, see people.py)
#                                              10 (SX.8o) the awards and the hall of fame (`LeagueRecord.honors`, honors.py) and the season's games and carries
#                                                (`LeagueRecord.usage`, workload.py)
#                                              11 (SX.12) the season's ties of the 2026 overtime (`LeagueRecord.ties`; a history entry's "ties"); a file of
#                                                format 10 or older has none (the default: a migration with no draw)
#                                              12 (SZ.8) the real calendar of the season (`LeagueRecord.calendar`, fixtures.py): 18 weeks, the bye weeks; a file of
#                                                format 11 or older has none (the default: the original's 16 random weeks, the season goes on as it was)
#                                              13 (S8.3 round 2, D-131) the made-up players have a first name; a file of format 12 or older is migrated once
#                                                (league.give_first_names, no draw): every bare drawn surname but the player's own team's (his own names)
#                                              14 (2026-10-23, D-136) the practice squads (`LeagueRecord.practice`, practice.py); a file of format 13 or older has
#                                                none, and a league in its season gets them at once from the players cut this offseason (no draw)
COMP_FIRST_ROUND, COMP_LAST_ROUND = 3, 7     # the compensatory picks sit at the end of rounds 3 to 7 (NFL, SRC-OFFICIAL)
OLDEST_FORMAT = 1                            # SX.8g: a format-1 file is read by a migration that gives every player a contract
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
# and regression); SX.8d adds 4 (the draft) and 5 (the roster cut and the fill). SX.8h inserts the expiring contracts between 3 and 4:
# a stage's number is its ID, not its place (the files of SX.8a to SX.8g keep their numbers), so it is number 7 and sits third from the
# end of the list; the order the player hears is the list's.
# SX.8i inserts free agency (number 8) right after the expiring contracts, before the draft (research B1's order).
# SX.8l inserts the staff (number 9) right after stage 1 (design 17: the firings, the job offers, the coordinators), so a coach who moves is the new team's in
# every later stage.
STAGES: tuple[tuple[int, str], ...] = ((1, "NXE-11"), (9, "NXE-19"), (2, "NXE-12"), (3, "NXE-13"), (7, "NXE-17"), (8, "NXE-18"), (4, "NXE-14"), (5, "NXE-15"),
                                       (6, "NXE-16"))

# the draft (design 7): seven rounds of one pick for each team, in the same order in every round
DRAFT_ROUNDS = 7
DRAFT_PICKS = DRAFT_ROUNDS * TEAMS           # 224
RANGE_SPAN = 6                               # the spoken range of a prospect: the low end to the low end + 6 (about 62 to 68)
RANGE_MIDDLE = 3                             # the middle of that range: the low end + 3
CUT_FLOOR_GROUP_MAX = 2                      # the cut's rating floor (tuning FR_CUT_FLOOR) is for groups of this many places or fewer
STAGE_REVIEW, STAGE_AGING, STAGE_DEVELOPMENT, STAGE_DRAFT, STAGE_CUT, STAGE_NEW_SEASON = 1, 2, 3, 4, 5, 6
STAGE_CONTRACTS = 7                          # SX.8h: the expiring contracts, after the development and before the draft
STAGE_FREE_AGENCY = 8                        # SX.8i: free agency, after the expiring contracts and before the draft
STAGE_STAFF = 9                              # SX.8l: the staff, after the season in review and before the retirements
STAGE_MAX = 9                                # the highest stage number a record may name
FREE_STAR_RATING = 80                        # a player of this rating or more who is not signed again is named in the stage's speech (at most STARS_NAMED)

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

# the to-do list (design 8.1): the kinds are data, so a later update adds its own (contracts, injuries, coordinators: design 17)
TODO_EXTRA_WORK, TODO_GAME_PLAN = "extra_work", "game_plan"
TODO_TRADE = "trade_offer"                    # SX.8j: a trade a computer team offers the player (design 17)
TODO_INJURY = "injury"                        # SX.8k: play or rest a doubtful or questionable player of the player's team (INJ-4)
TODO_DEMAND = "trade_demand"                  # SX.8n: a player of the player's team asks to be traded: the other teams' offers, or keep him
TODO_KINDS = (TODO_EXTRA_WORK, TODO_GAME_PLAN, TODO_TRADE, TODO_INJURY, TODO_DEMAND)
ITEM_NEW, ITEM_LATER, ITEM_SET = 0, 1, 2     # not asked yet; answered "later"; the game plan, taken for this week's game
REGULAR_WEEKS = 16                           # the original's regular season; a league that plays the real calendar has `LeagueRecord.regular_weeks` (18)
MAX_REGULAR_WEEKS = 18                       # the longest regular season a record may name (the real calendar's), for the whole-file checks
SUPER_BOWL_WEEK = 20                         # the last week (gtp) of a season: the Super Bowl
NEWS_LAST_WEEK = 15                          # the news of a week is made after weeks 1 to 15 (design 8.3); a league that plays the calendar: LeagueRecord.last_prepared_week
NEWS_OFFSEASON = 99                          # the `week` of an offseason's news line (SZ.8: it was 16, which is a regular week of the calendar; a file of format 11 or older is migrated)
MAX_NEWS = 400                               # lines kept in league.sav (a season's 15 weeks of 4 and the offseason's, with room)
MAX_TODO = 200
# the fourteen kinds of news line of news.txt (design 8.3, 15); the letter says the kind
NEWS_POOLS = ("NWB", "NWU", "NWC", "NWS", "NWL", "NWY", "NWZ", "NWM", "NWT", "NWR", "NWD", "NWP", "NWK", "NWX",      # NWX (SX.8j): a trade between two other teams
              "NWJ",                                                                                          # NWJ (SX.8k): another team's player out for weeks
              "NWH")                                                                                          # NWH (SX.8n): a player asks to be traded
# the pools of injuries.txt (SX.8k, INJ-5): the spoken name of each injury kind (tuning FR_INJ_KINDS) and IJX, the announcer's line when a player is hurt in a game
INJURY_KIND_POOLS = ("IJA", "IJB", "IJC", "IJD", "IJE", "IJF", "IJG", "IJH", "IJK", "IJL", "IJM")
INJURY_POOLS = INJURY_KIND_POOLS + ("IJX",)
MAX_HURT = 400                               # injury records of one season kept in league.sav (a bound for the whole-file check)
STATUS_OUT, STATUS_DOUBTFUL, STATUS_QUESTIONABLE, STATUS_HEALTHY = "out", "doubtful", "questionable", "healthy"

SALARY_PER_MILLION = 10                      # a salary is a whole number of tenths of a million dollars (SX.8g, D-066): 124 is 12.4 million
MAX_DEAD = 100_000                           # the most dead money a team's record may hold (a bound for the whole-file check)

MAX_DEMANDS = 64                             # the trade demands of one season kept in league.sav (SX.8n)
MAX_TRADES = 200                            # the trades of one season kept in league.sav (SX.8j)
MAX_RESULTS = 400                           # games of one season (16 weeks of 16 games and 13 play-off games, or the calendar's 272 and 13), with room
MAX_HISTORY = 500                            # seasons kept
