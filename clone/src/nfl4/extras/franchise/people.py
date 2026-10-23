"""The people of the Franchise: a player's personality and morale, the player tags, the holdouts at camp, the trade demands and the weekly game goal (nfl4 only,
rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8n (research B2, B9 and B10's LATER items, D-074). Plain rules over the league record, no speech, no files and NO DRAW, so the program's
weekly preparation and stage 3 (`weekly.py`, `people_flow.py`) and the calibration's fast run use the very same code. Every number is data in `extras\\tuning.py`.

    personality(pid)                one of five words, a rule of the player's ID (fixed when he enters the league), each with one rule in the talks and one in morale
    morale / set_morale / effect    one whole number a player, -FR_MORALE_MAX to FR_MORALE_MAX; in a game it moves his rating by step(morale, FR_MORALE_STEP)
    after_week                      the week's results, game goals and lineups move every player's morale (the program's preparation and the fast run)
    with_morale / week_sums         the morale in a played game's ratings (the H8 door reads them) and in the computer's games (the week's sums)
    goal_for / goal_met / set_goal  the weekly game goal of a team by the two teams' strengths, and its verdict
    tag_of                          a player tag: star, rising or veteran (from rating, age and potential), or none
    holdout_of / begin_holdouts     who holds out at camp (stage 3) and what the computer teams and the staff do: pay him or let him wait
    demands_week                    the trade demands of a week of the window: filed, the other teams' offers, the computer teams' trades (kind KIND_DEMAND)
    new_season / check_people       stage 6 (the morale halved, the season's demands over) and the whole-file check of `LeagueRecord.people`

`LeagueRecord.people` (league.sav format 9):
    {"morale": {"<player ID>": m (not 0)}, "begun": the season whose camp holdouts were settled (0: none yet),
     "holdouts": [[pid, team, season, outcome]] of the last camp (outcome PENDING, PAID, WAITED, ON_BLOCK), "pending": [pid] the player's own still to be asked (stage 3),
     "demands": [[pid, team, week filed, state]] of this season (OPEN, TRADED, ENDED),
     "goal": [season, week, kind, n, told] the player's goal of the week, "verdict": [season, week, met, told] of his last goal}
"""
from __future__ import annotations

from .. import tuning as T
from . import contracts as CT
from . import data as D
from . import injuries
from .ratings import step

PERSONALITIES = ("money", "winning", "loyalty", "playing_time", "the_game")
TRAIT_TEXT = {"money": "NXU-P10", "winning": "NXU-P11", "loyalty": "NXU-P12", "playing_time": "NXU-P13", "the_game": "NXU-P14"}
TAGS = ("star", "rising", "veteran")
TAG_TEXT = {"star": "NXU-T01", "rising": "NXU-T02", "veteran": "NXU-T03"}
MORALE_TEXT = {"high": "NXU-M01", "good": "NXU-M02", "low": "NXU-M03"}
PENDING, PAID, WAITED, ON_BLOCK = 0, 1, 2, 3
OPEN, TRADED, ENDED = 0, 1, 2
GOAL_KINDS = ("margin", "win", "close")
KEYS = ("morale", "begun", "holdouts", "pending", "demands", "goal", "verdict")


def empty() -> dict:
    return {"morale": {}, "begun": 0, "holdouts": [], "pending": [], "demands": [], "goal": None, "verdict": None}


# ----- the personality -----

def personality(pid: int) -> str:
    """The player's word: (ID x FR_PERSON_MIX) mod 1000 against the shares (every 1,000 consecutive IDs have the shares exactly). No draw."""
    key = (pid * T.FR_PERSON_MIX) % 1000
    total = 0
    for word, share in T.FR_PERSON_SHARES:
        total += share * 10
        if key < total:
            return word
    return T.FR_PERSON_SHARES[-1][0]


def is_starter(league, player) -> bool:
    """He holds the first place of his group (the cut and a trade put the best first)."""
    return player.place >= 0 and player.place == D.PLACES_OF[player.pos][0]


def slack_change(league, player, how: str) -> int:
    """His word's rule in the contract talks: the percent added to the slack of his mood (`resign.floor_salary`)."""
    word = personality(player.id)
    if word == "playing_time":
        return T.FR_PERSON_STARTER[0] if is_starter(league, player) else T.FR_PERSON_STARTER[1]
    happy, content, unhappy = T.FR_PERSON_TALK[word]
    return {"happy": happy, "content": content, "unhappy": unhappy}[how]


def talk_mood(league, player, how: str) -> str:
    """The mood of the talk: the team's mood of last season (`resign.mood`) one step better when his morale is FR_MORALE_TALK or more, one step worse at minus
    that or less."""
    moods = ("unhappy", "content", "happy")
    m = morale(league, player.id)
    index = moods.index(how)
    if m >= T.FR_MORALE_TALK:
        index = min(2, index + 1)
    elif m <= -T.FR_MORALE_TALK:
        index = max(0, index - 1)
    return moods[index]


# ----- the morale -----

def morale(league, pid: int) -> int:
    return league.people["morale"].get(str(pid), 0)


def clamp(value: int) -> int:
    return max(-T.FR_MORALE_MAX, min(T.FR_MORALE_MAX, value))


def toward_zero(value: int) -> int:
    """The week's pull of a morale toward zero (FR_MORALE_DECAY), never past it."""
    if value > 0:
        return max(0, value - T.FR_MORALE_DECAY)
    return min(0, value + T.FR_MORALE_DECAY)


def set_morale(league, pid: int, value: int) -> None:
    value = clamp(value)
    table = league.people["morale"]
    if value:
        table[str(pid)] = value
    else:
        table.pop(str(pid), None)


def effect(value: int) -> int:
    """What a morale does to the rating in a game: step(morale, FR_MORALE_STEP), -2 to +2."""
    return step(value, *T.FR_MORALE_STEP)


def word(value: int) -> str:
    return "high" if value >= T.FR_MORALE_WORD else "low" if value <= -T.FR_MORALE_WORD else "good"


def has_morale(league) -> bool:
    return bool(league.people["morale"])


def plain_table(league, team: int) -> list:
    """The 34 places as their own players play them (nobody hurt): (identity, name, rating)."""
    out = []
    for index in range(D.PLACE_COUNT):
        player = league.player_at(team, index)
        out.append((player.id, player.name, player.rating))
    return out


def with_morale(league, team: int, table: list) -> list:
    """A lineup with the morale of every player who plays his own place added to his rating (40 to 99); a place a substitute or a stand-in plays keeps its
    replacement level (the hurt man's place counts the same whoever is behind him, INJ-2)."""
    roster = league.rosters[team - 1]
    out = []
    for index, (identity, name, rating) in enumerate(table):
        if isinstance(identity, int) and identity == roster[index]:
            rating = max(D.RATING_MIN, min(D.RATING_MAX, rating + effect(morale(league, identity))))
        out.append((identity, name, rating))
    return out


def gain_of(league, team: int, table: list) -> int:
    """The weighted sum the morale adds to a lineup (design 4.4's weights)."""
    moved = with_morale(league, team, table)
    return sum(D.WEIGHT[D.POSITION_OF_PLACE[i]] * (after[2] - before[2]) for i, (before, after) in enumerate(zip(table, moved)))


def hurt_teams(league, week: int) -> set:
    """The teams that have a player hurt for `week` by an earlier game (the frame of `injuries.effective_sums`)."""
    return {league.players[pid].team for pid, row in injuries.rows(league).items()
            if row[2] < week and injuries.status_of_row(row, week, league.regular_weeks) != D.STATUS_HEALTHY}


def week_sums(league, week: int) -> list:
    """The 32 sums of the computer's games of `week`: the injuries' (`injuries.effective_sums`) and the morale of every player who plays his own place. With no
    morale anywhere they are the injuries' sums exactly. The bound of the week's changes (`strength.LeaguePlace`, FR_INJ_SD_MAX) takes both together."""
    sums = injuries.effective_sums(league, week)
    if not has_morale(league):
        return sums
    hurt = hurt_teams(league, week)
    for team in range(1, D.TEAMS + 1):
        table = injuries.lineup(league, team, week, True, hurt_before=week) if team in hurt else plain_table(league, team)
        sums[team - 1] += gain_of(league, team, table)
    return sums


def played_ids(league, team: int, week: int, staff: bool) -> set:
    """The players who played their own place in the game of `week` (the week's lineup; the injuries of that week's own game do not count: he played it)."""
    if team in hurt_teams(league, week):
        table = injuries.lineup(league, team, week, staff, hurt_before=week)
    else:
        table = plain_table(league, team)
    roster = league.rosters[team - 1]
    return {identity for index, (identity, _name, _rating) in enumerate(table) if isinstance(identity, int) and identity == roster[index]}


def after_week(league, week: int, results: list, staff: bool = True) -> dict:
    """The week's results move every player's morale: first FR_MORALE_DECAY toward zero, then a win by his word's weight up, a loss down, the week's game goal
    met by FR_GOAL_MORALE up (missed down), a week he did not play his own place by his word's weight down. `results` are rows [stage code, week, winner, loser, winner score, loser score] (league.results, the fast run's
    week); `staff`: the player's team's lineup by the staff's rule. Returns team -> (won, goal met). Weeks after FR_MORALE_LAST_WEEK move nothing."""
    out = {}
    tied = set()                                                       # SX.12: a tie moves no morale by its result (neither a win nor a loss)
    if not 1 <= week <= league.last_prepared_week:
        return out
    for row in results:
        if row[0] != 0 or row[1] != week:
            continue
        winner, loser, ws, ls = row[2], row[3], row[4], row[5]
        if ws == ls:
            tied |= {winner, loser}
        for team, other, own, theirs in ((winner, loser, ws, ls), (loser, winner, ls, ws)):
            played = league.team in (winner, loser)                    # the player's game: the engine's margins (both of its teams)
            kind, n = told_goal(league, week) if team == league.team and told_goal(league, week) else goal_for(league.sums, team, other, played)
            out[team] = (team == winner and ws != ls, goal_met(kind, n, own, theirs))
    for team in sorted(out):
        won, met = out[team]
        playing = played_ids(league, team, week, staff or team != league.team)
        for pid in league.rosters[team - 1]:
            if not pid:
                continue
            up, down, sat = T.FR_PERSON_MORALE[personality(pid)]
            result = 0 if team in tied else (up if won else -down)
            change = result + (T.FR_GOAL_MORALE if met else -T.FR_GOAL_MORALE)
            if pid not in playing:
                change -= sat
            set_morale(league, pid, toward_zero(morale(league, pid)) + change)
    if league.team in out:
        league.people["verdict"] = [league.season, week, int(out[league.team][1]), 0]
    return out


# ----- the weekly game goal -----

def goal_for(sums: list, team: int, other: int, played: bool = False) -> tuple:
    """(kind, n) of a team's goal against `other`: stronger by FR_GAME_GOAL_GAP rating points or more, win by FR_GAME_GOAL_MARGIN or more ("margin"); weaker by as
    much, lose by no more than FR_GAME_GOAL_CLOSE ("close"); else win ("win"). Without the season's sums: win. `played`: a game the engine plays (the
    player's), whose margins are not the score table's: FR_GAME_GOAL_PLAYED's points, so a goal is met about half the time there too (B-P106)."""
    if len(sums) != D.TEAMS:
        return "win", 0
    margin, close = T.FR_GAME_GOAL_PLAYED if played else (T.FR_GAME_GOAL_MARGIN, T.FR_GAME_GOAL_CLOSE)
    gap = sums[team - 1] - sums[other - 1]
    if gap >= T.FR_GAME_GOAL_GAP * D.WEIGHT_SUM:
        return "margin", margin
    if -gap >= T.FR_GAME_GOAL_GAP * D.WEIGHT_SUM:
        return "close", close
    return "win", 0


def goal_met(kind: str, n: int, own: int, theirs: int) -> bool:
    if kind == "margin":
        return own - theirs >= n
    if kind == "close":
        return theirs - own <= n
    return own > theirs


def told_goal(league, week: int):
    """(kind, n) of the goal the player heard for `week` (set at the week's preparation), or None: his team is judged by it even when a trade of the week
    changed the strengths since (the review of SX.8n)."""
    goal = league.people["goal"]
    if goal is not None and goal[0] == league.season and goal[1] == week:
        return goal[2], goal[3]
    return None


def set_goal(league, week: int, opponent: int) -> list | None:
    """The player's goal of `week` against `opponent` (weeks 1 to FR_MORALE_LAST_WEEK: the weeks whose result is judged, so every goal he hears gets its
    verdict), kept untold until the kick-off."""
    if not 1 <= week <= league.last_prepared_week or not 1 <= opponent <= D.TEAMS or opponent == league.team:
        league.people["goal"] = None
        return None
    kind, n = goal_for(league.sums, league.team, opponent, played=True)
    league.people["goal"] = [league.season, week, kind, n, 0]
    return league.people["goal"]


# ----- the player tags -----

def tag_of(player) -> str | None:
    """A star (rated FR_PTAG_STAR or more), else a rising player (aged FR_PTAG_YOUNG or less with high potential), else a veteran (FR_PTAG_VETERAN or older)."""
    if player.rating >= T.FR_PTAG_STAR:
        return "star"
    if player.age <= T.FR_PTAG_YOUNG and player.potential == "high":
        return "rising"
    if player.age >= T.FR_PTAG_VETERAN:
        return "veteran"
    return None


# ----- the holdouts at camp (stage 3) -----

def underpaid(player) -> bool:
    return player.salary * 100 < CT.market_salary(player.pos, player.rating) * T.FR_HOLDOUT_UNDERPAID


def holds_out(league, player) -> bool:
    """He is placed, under contract for the coming season, has played FR_HOLDOUT_SEASONS seasons, is rated FR_HOLDOUT_RATING or more, is underpaid, is not of a
    word that never holds out, and is of a word that always does or his morale is FR_HOLDOUT_MORALE or lower."""
    if player.status != "active" or player.place < 0 or player.years < 1 or player.seasons < T.FR_HOLDOUT_SEASONS or player.rating < T.FR_HOLDOUT_RATING:
        return False
    word_ = personality(player.id)
    if word_ in T.FR_HOLDOUT_NEVER or not underpaid(player):
        return False
    return word_ in T.FR_HOLDOUT_ALWAYS or morale(league, player.id) <= T.FR_HOLDOUT_MORALE


def holdout_of(league, team: int) -> list:
    """The team's players who hold out, at most FR_HOLDOUT_TEAM_MAX, the most valuable first (`resign.value`)."""
    from . import resign
    out = [p for p in league.active_of(team) if p is not None and holds_out(league, p)]
    return sorted(out, key=resign.value)[:T.FR_HOLDOUT_TEAM_MAX]


def new_contract(player) -> tuple:
    """What paying him means: the market contract of his rating for the length of his age, never under what he has."""
    salary, years = CT.market_contract(player)
    return max(salary, player.salary), years


def can_pay(league, team: int, player, salary: int) -> bool:
    """The raise fits under the cap: his new salary within the room of stage 7's rule with him counted as unsigned (`resign.room_after`)."""
    from . import resign
    return salary <= resign.room_after(resign.running_payroll(league, team) - player.salary, resign.running_count(league, team) - 1, league.dead[team - 1])


def staff_pays(league, team: int, player) -> bool:
    """The computer teams' and the staff's rule: pay him when he is FR_HOLDOUT_PAY_AGE or younger, it fits under the cap and the coming season's payroll stays
    within the staff's target of stage 7."""
    from . import resign
    if player.age > T.FR_HOLDOUT_PAY_AGE:
        return False
    salary, _years = new_contract(player)
    payroll = resign.running_payroll(league, team) - player.salary + salary + league.dead[team - 1]
    return can_pay(league, team, player, salary) and payroll <= resign.target_payroll()


def pay(league, player) -> tuple:
    salary, years = new_contract(player)
    CT.sign(player, salary, years)
    return salary, years


def wait(league, player) -> None:
    set_morale(league, player.id, -T.FR_MORALE_MAX)


def row_of(league, pid: int):
    for row in league.people["holdouts"]:
        if row[0] == pid:
            return row
    return None


def begin_holdouts(league, own_by_staff: bool) -> list:
    """Stage 3 starts: every team's holdouts (team 1 to 32), each paid or left to wait by the staff's rule, the player's own (unless the staff handles his team)
    left for his answer in `pending`. The rows of the last camp are replaced. Returns the rows."""
    rows, pending = [], []
    for team in range(1, D.TEAMS + 1):
        for player in holdout_of(league, team):
            if team == league.team and not own_by_staff:
                rows.append([player.id, team, league.season, PENDING])
                pending.append(player.id)
                continue
            if staff_pays(league, team, player):
                pay(league, player)
                rows.append([player.id, team, league.season, PAID])
            else:
                wait(league, player)
                rows.append([player.id, team, league.season, WAITED])
    league.people.update(holdouts=rows, pending=pending, begun=league.season)
    return rows


def answer_holdout(league, pid: int, outcome: int) -> None:
    """The player's answer (or the staff's for him) for his holdout `pid`: PAID, WAITED or ON_BLOCK (he asks to be traded at once)."""
    player = league.players[pid]
    row = row_of(league, pid)
    if outcome == PAID:
        pay(league, player)
    elif outcome == WAITED:
        wait(league, player)
    elif outcome == ON_BLOCK:
        set_morale(league, pid, -T.FR_MORALE_MAX)
    row[3] = outcome
    league.people["pending"] = [p for p in league.people["pending"] if p != pid]


# ----- the trade demands -----

def demand_of(league, pid: int):
    for row in league.people["demands"]:
        if row[0] == pid:
            return row
    return None


def file_demands(league, week: int) -> list:
    """The players who ask to be traded this week (in the order of the camp's rows): one put on the trade block at camp from the window's first week, one who waited
    from FR_DEMAND_WEEK while his morale is FR_DEMAND_MORALE or lower; still on the team he held out for, at most one demand a season. (A loyal player never
    held out, so he never asks: FR_HOLDOUT_NEVER is the camp's rule.)"""
    from . import trades as TR
    made = []
    if not TR.in_window(league, week):
        return made
    for pid, team, _season, outcome in league.people["holdouts"]:
        player = league.players.get(pid)
        if player is None or player.status != "active" or player.team != team or demand_of(league, pid) is not None:
            continue
        if outcome == ON_BLOCK or (outcome == WAITED and week >= T.FR_DEMAND_WEEK and morale(league, pid) <= T.FR_DEMAND_MORALE):
            row = [pid, team, week, OPEN]
            league.people["demands"].append(row)
            made.append(row)
    return made


def offers_for(league, row: list, records: list, week: int) -> list:
    """The other teams' offers for a demanding player by the trades' own rule (`trades.block_offers`), the best FR_DEMAND_OFFERS: [(Trade, the gain of his team)].
    A computer team's demand never hears an offer of the player's team (taking it would trade one of his players without his answer; the review of SX.8n)."""
    from . import trades as TR
    player = league.players[row[0]]
    offers = TR.block_offers(league, row[1], player, records, week)
    if row[1] != league.team:
        offers = [(trade, gain) for trade, gain in offers if league.team not in (trade.a, trade.b)]
    return offers[:T.FR_DEMAND_OFFERS]


def acceptable(league, row: list, gain: int) -> bool:
    """The computer teams' and the staff's rule: take an offer that costs at most FR_DEMAND_GIVE rating points of the position."""
    return gain >= -T.FR_DEMAND_GIVE * D.WEIGHT[league.players[row[0]].pos]


def trade_on_demand(league, trade, week: int) -> None:
    """A demand's trade is made (kind KIND_DEMAND): the demand is over and the player's morale is 0 (a new start). The caller has checked `trades.problems`."""
    from . import trades as TR
    TR.execute(league, trade, week, TR.KIND_DEMAND)
    row = demand_of(league, trade.give_a)
    if row is not None:
        row[3] = TRADED
    set_morale(league, trade.give_a, 0)


def end_demands(league, week: int) -> None:
    """Outside the window (after the deadline) every open demand ends; a demand whose player left his team ends too."""
    from . import trades as TR
    for row in league.people["demands"]:
        if row[3] != OPEN:
            continue
        player = league.players.get(row[0])
        if not TR.in_window(league, week) or player is None or player.status != "active" or player.team != row[1]:
            row[3] = ENDED


def demands_week(league, week: int, records: list) -> tuple:
    """The trade demands of the week's preparation (after the week's own trades, `trades.week`): the window's end, the new demands, then every open demand in the
    order it was filed: a computer team takes the best offer when it is `acceptable`; a demand of the player's team is returned with its offers for his to-do
    list. Returns (the trades made, [(row, offers)] for the player, the rows filed this week)."""
    from . import trades as TR
    end_demands(league, week)
    filed = file_demands(league, week)
    made, own = [], []
    for row in league.people["demands"]:
        if row[3] != OPEN:
            continue
        offers = offers_for(league, row, records, week)
        if row[1] == league.team:
            if offers:
                own.append((row, offers))
            continue
        if offers and acceptable(league, row, offers[0][1]) and TR.problems(league, offers[0][0], week) is None:
            trade_on_demand(league, offers[0][0], week)
            made.append(offers[0][0])
    return made, own, filed


def demand_answers(league, row: list, offers: list) -> list:
    """The answers of the player's demand item in order, the staff's recommendation first: the offers (best first) and None ("keep him"); "keep him" first when
    the best offer is not acceptable."""
    trades_ = [trade for trade, _gain in offers]
    if offers and acceptable(league, row, offers[0][1]):
        return trades_ + [None]
    return [None] + trades_


# ----- the season's end and the whole-file check -----

def new_season(league) -> None:
    """Stage 6: every active player's morale halved toward zero (the others' dropped), the season's demands and goals over, the camp's rows of players who left
    the league dropped."""
    table = {}
    for key, value in league.people["morale"].items():
        player = league.players.get(int(key))
        if player is not None and player.status == "active":
            half = int(value / 2)
            if half:
                table[key] = half
    league.people["morale"] = table
    league.people["demands"] = []
    league.people["goal"] = None
    league.people["verdict"] = None
    league.people["holdouts"] = [row for row in league.people["holdouts"] if row[0] in league.players]


def check_people(league, whole) -> None:
    """LeagueError (through `whole`) unless `league.people` is whole: the morale of players of the league in range, the camp's rows, the player's own holdout still
    to be asked only at stage 3, the demands, the goal and its verdict."""
    from .league import OFFSEASON, LeagueError
    data = league.people
    if not isinstance(data, dict) or set(data) != set(KEYS):
        raise LeagueError("the people hold %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    table = data["morale"]
    if not isinstance(table, dict) or len(table) > 4 * D.TEAMS * D.PLACE_COUNT:
        raise LeagueError("the morale is %r" % (type(table).__name__,))
    for key, value in table.items():
        if not isinstance(key, str) or not key.isascii() or not key.isdigit() or key != str(int(key)) or int(key) not in league.players:
            raise LeagueError("the morale of %r, who is not in the league" % (key,))
        whole(value, -T.FR_MORALE_MAX, T.FR_MORALE_MAX, "a morale")
        if value == 0:
            raise LeagueError("a morale of 0 kept for player %s" % key)
    whole(data["begun"], 0, D.MAX_SEASONS, "the season of the camp's holdouts")
    rows = data["holdouts"]
    if not isinstance(rows, list) or len(rows) > D.TEAMS * D.PLACE_COUNT:
        raise LeagueError("the holdouts are %r" % (type(rows).__name__,))
    seen = set()
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a holdout is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "a holdout's player")
        whole(row[1], 1, D.TEAMS, "a holdout's team")
        whole(row[2], 1, D.MAX_SEASONS, "a holdout's season")
        whole(row[3], PENDING, ON_BLOCK, "a holdout's outcome")
        if row[0] not in league.players or row[0] in seen:
            raise LeagueError("the holdout of player %r, who is not in the league or held out twice" % (row[0],))
        seen.add(row[0])
    pending = data["pending"]
    if not isinstance(pending, list):
        raise LeagueError("the holdouts still to ask are %r" % (type(pending).__name__,))
    for pid in pending:
        whole(pid, 1, 10 ** 9, "a holdout still to ask")
    open_rows = [row[0] for row in rows if row[3] == PENDING]
    if sorted(pending) != sorted(open_rows) or len(set(pending)) != len(pending):
        raise LeagueError("the holdouts still to ask %r are not the camp's open ones %r" % (pending, open_rows))
    if pending and not (league.stage == OFFSEASON and league.stage_no == D.STAGE_DEVELOPMENT):
        raise LeagueError("a holdout still to ask outside stage 3")
    for pid in pending:
        player = league.players.get(pid)
        if player is None or player.status != "active" or player.team != league.team or player.place < 0:
            raise LeagueError("the holdout %r to ask is not a player of the player's team" % (pid,))
    demands = data["demands"]
    if not isinstance(demands, list) or len(demands) > D.MAX_DEMANDS:
        raise LeagueError("the trade demands are %r" % (type(demands).__name__,))
    asked = set()
    for row in demands:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a trade demand is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "a trade demand's player")
        whole(row[1], 1, D.TEAMS, "a trade demand's team")
        whole(row[2], 1, T.FR_TRADE_LAST_WEEK_CALENDAR, "a trade demand's week")
        whole(row[3], OPEN, ENDED, "a trade demand's state")
        if row[0] not in league.players or row[0] in asked:
            raise LeagueError("the trade demand of player %r, who is not in the league or asked twice" % (row[0],))
        asked.add(row[0])
    goal = data["goal"]
    if goal is not None:
        if not isinstance(goal, list) or len(goal) != 5 or goal[2] not in GOAL_KINDS:
            raise LeagueError("the game goal is %r" % (goal,))
        whole(goal[0], 1, D.MAX_SEASONS, "the goal's season")
        whole(goal[1], 1, D.MAX_REGULAR_WEEKS, "the goal's week")
        whole(goal[3], 0, 99, "the goal's points")
        whole(goal[4], 0, 1, "the goal's told mark")
    verdict = data["verdict"]
    if verdict is not None:
        if not isinstance(verdict, list) or len(verdict) != 4:
            raise LeagueError("the goal's verdict is %r" % (verdict,))
        whole(verdict[0], 1, D.MAX_SEASONS, "the verdict's season")
        whole(verdict[1], 1, D.MAX_REGULAR_WEEKS, "the verdict's week")
        whole(verdict[2], 0, 1, "the verdict")
        whole(verdict[3], 0, 1, "the verdict's told mark")
