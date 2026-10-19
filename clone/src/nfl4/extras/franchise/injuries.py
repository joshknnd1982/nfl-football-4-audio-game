"""Injuries of the Franchise: who is hurt, for how long, who plays in his place, and the week's draws (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRA_FEATURES N6.8 (INJ-1 to INJ-6) and NFL_FRANCHISE_DESIGN 17 SX.8k (as built: entry 1.11, D-071). FRANCHISE ONLY (the owner's rule of
2026-10-16, D-062): nothing here is called outside a franchise, so a quick game, a Classic season and a season with the N. F. L. rules but no franchise
never draw, speak, store or show an injury. Rules over the league record, no speech and no files; the draws use the one GameRandom handed in, so the
program's weekly preparation (`weekly.prepare`) and the fast run of the calibration (`work\\sim_league_sx8k.py`) call the very same `after_games`.

The record, `LeagueRecord.injuries` (league.sav format 6):

    {"hurt": [[player id, kind, week hurt, back, width, offset, play], ...],
     "stand_ins": [[team, position, name, rating], ...],
     "report": None or {"season": s, "week": w, "lines": [markup, ...], "told": 0 or 1}}

* kind: the injury's ID (tuning FR_INJ_KINDS: IJA to IJM, the pools of injuries.txt that hold its spoken names);
* week hurt: the week (gtp) of the game he was hurt in; back: the first week he is fit again, so the games he misses when he rests are back - week for
  the coming week (`left`); width and offset: the shape of the range told at first ("out 2 to 4 weeks"), which narrows by one a week (`spoken_range`);
* play: the week the coach decided to play him hurt (0: no such decision). Before a game of the regular season a player is out with 3 or more games
  still to miss, doubtful with 2, questionable with 1 (`status`); in the play-offs every hurt player is out (they have no to-do list, design 8.1). A
  doubtful or questionable player plays when his coach says so: the computer teams and the staff play a questionable one and rest a doubtful one (the
  staff's rule), the player's team with the staff setting off plays him only when the player said so (`plays`: nothing is decided for him, INJ-4).

WHO PLAYS IN HIS PLACE (INJ-2; `lineup`): the place of a player who does not play is played by the next player of his group who plays, DOWN the depth
order (the group's places in order: the roster cut puts the best in place 1, design 7.6, and a trade puts the new man in the place of the man he
replaces), else the nearest one above him; his own rating never decides who it is, and his place is played at replacement level
(the lower of the next man's rating and the position's stand-in rating): so his plays go to the man behind him (the design's
"first healthy player in the depth order" read as the next man up: giving them to the group's best would make the injury of a weak player a gain). A
returner's place goes to a running back who plays, the lowest in the depth order first, then a receiver (the two returners are named together, so the other returner
cannot take it). A group with nobody to play (the quarterback, the kicker, the punter, or every player of a group hurt) is played by its STAND-IN, a
player signed for the weeks (`stand_ins`, rating FR_INJ_STAND_IN), made by the week's draws when every player of a group is hurt and kept to the end of
the season. A player who plays hurt plays FR_INJ_HURT_PENALTY points below his rating. The lineup gives the game's rosters (the place draws skip the
injured because the injured are not in them) and the strength of the computer's games (`effective_sum`); with nobody hurt it is the roster exactly.

THE DRAWS of a week (`after_games`, for the games of weeks 1 to FR_INJ_LAST_WEEK), team 1 to 32, each team in this order: every hurt player who played
hurt may be hurt worse (`below(1000)` against FR_INJ_WORSE); the practice part (FR_INJ_PRACTICE: draws `below(10000)`, a hit hurts the player in the
lineup at a place `below(34)`); the game part when the engine did not play the team's game (FR_INJ_GAME: a hit hurts the player at a place drawn by
FR_INJ_GAME_WEIGHT); an injury draws its kind (`below` the shares of the kinds his position can have), its games missed (`below(hi - lo + 1) + lo`) and
the offset of its spoken range (`below(width + 1)`). A team with FR_INJ_TEAM_MAX players hurt gets no further injury (INJ-6: no team starved). A game
the player plays has its injuries per play instead (`injury_flow.GameInjuries`, the same `injure`).

SX.8o (D-076, workload.py): in the game part the backs' and the receivers' places weigh by their shares of the carries (the carry weights of the ratings the
game read, as the weighted ball carrier of a played game shares them); then the workload rule: every back of the team whose carries of the season are past
FR_WORKLOAD_FREE draws `below(10000)` against `workload.game_chance` (his expected carries of the game, raised by his extra percent), and the team's
expected carries join the season's counts. A team whose game the engine played counted its carries and drew its workload per play.
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D
from .league import LeagueError, LeagueRecord, draw_name

HURT_FIELDS = 7
STAND_IN = "stand-in"
KIND_IDS = tuple(kind[0] for kind in T.FR_INJ_KINDS)


def empty() -> dict:
    return {"hurt": [], "stand_ins": [], "report": None}


# ----- the statuses -----

def rows(league: LeagueRecord) -> dict:
    """player id -> his injury row."""
    return {row[0]: row for row in league.injuries["hurt"]}


def row_of(league: LeagueRecord, pid: int):
    for row in league.injuries["hurt"]:
        if row[0] == pid:
            return row
    return None


def left(row, week: int) -> int:
    """The games he still misses from `week` on when he rests."""
    return row[3] - week


def status_of_row(row, week: int) -> str:
    games = left(row, week)
    if games <= 0:
        return D.STATUS_HEALTHY
    if week > D.REGULAR_WEEKS or games > T.FR_INJ_DOUBTFUL:
        return D.STATUS_OUT
    return D.STATUS_DOUBTFUL if games == T.FR_INJ_DOUBTFUL else D.STATUS_QUESTIONABLE


def status(league: LeagueRecord, pid: int, week: int) -> str:
    row = row_of(league, pid)
    return D.STATUS_HEALTHY if row is None else status_of_row(row, week)


def healthy(league: LeagueRecord, pid: int, week: int) -> bool:
    return status(league, pid, week) == D.STATUS_HEALTHY


def staff_plays(state: str) -> bool:
    """The staff's rule for a hurt player (the computer teams, and the player's team with the staff setting on): play a questionable one."""
    return state == D.STATUS_QUESTIONABLE


def plays(league: LeagueRecord, player, week: int, staff: bool, out=frozenset(), known=None) -> bool:
    """Whether the player plays the game of `week` (out: the players hurt in the game in progress; known: `rows(league)` when the caller has it)."""
    if player.id in out:
        return False
    row = known.get(player.id) if known is not None else row_of(league, player.id)
    if row is None:
        return True
    state = status_of_row(row, week)
    if state == D.STATUS_HEALTHY:
        return True
    if state == D.STATUS_OUT:
        return False
    if player.team == league.team and not staff:
        return row[6] == week                     # the player's own decision; none: he rests (nothing is decided for him)
    return staff_plays(state)


def penalty(league: LeagueRecord, pid: int, week: int, known=None) -> int:
    row = known.get(pid) if known is not None else row_of(league, pid)
    state = D.STATUS_HEALTHY if row is None else status_of_row(row, week)
    return T.FR_INJ_HURT_PENALTY.get(state, 0)


def hurt_of(league: LeagueRecord, team: int, week: int) -> list:
    """The team's players who are not fit for `week`, in place order: (player, status)."""
    out = []
    known = rows(league)
    for player in league.active_of(team):
        if player is None:
            continue
        row = known.get(player.id)
        if row is None:
            continue
        state = status_of_row(row, week)
        if state != D.STATUS_HEALTHY:
            out.append((player, state))
    return out


def hurt_count(league: LeagueRecord, team: int, week: int) -> int:
    return len(hurt_of(league, team, week))


# ----- the stand-ins -----

def stand_in(league: LeagueRecord, team: int, position: str, extra=()):
    for row in list(extra) + league.injuries["stand_ins"]:
        if row[0] == team and row[1] == position:
            return row
    return None


def stand_in_rating(position: str) -> int:
    return T.FR_INJ_STAND_IN.get(position, T.FR_INJ_STAND_IN_OTHER)


def used_names(league: LeagueRecord, extra=()) -> set:
    names = {p.name for p in league.players.values() if p.status == "active"}
    names |= {row[2] for row in list(extra) + league.injuries["stand_ins"]}
    return names


def make_stand_in(league: LeagueRecord, team: int, position: str, rnd, surnames: list, extra=()) -> list:
    """A stand-in for the group: a name (the league's own name rule: `rnd(len(surnames))` again while it is in use) and the stand-in rating."""
    return [team, position, draw_name(rnd, surnames, used_names(league, extra)), stand_in_rating(position)]


def needs_stand_in(league: LeagueRecord, team: int, position: str, week: int, out=frozenset()) -> bool:
    """Every player of the group is hurt (or out of the game in progress): nobody can be sure to play."""
    group = [p for p in league.group_of(team, position) if p is not None]
    return bool(group) and all(p.id in out or not healthy(league, p.id, week) for p in group)


# ----- who plays each place -----

def lineup(league: LeagueRecord, team: int, week: int, staff: bool, out=frozenset(), extra_stand_ins=(), make=None, hurt_before=None) -> list:
    """The 34 places as they are played in the game of `week`: (identity, name, rating), identity the player's id or (STAND_IN, position). A place with
    nobody to play it takes the team's stand-in of its position; `make(position)` makes one when there is none (the week's `settle`, and a game in
    progress), else that is an error (every lineup after the week's draws has the stand-ins it needs). A place a substitute plays (the next man up, a
    returner's cover) is played at REPLACEMENT LEVEL, the lower of his rating and his position's stand-in rating: the depth chart moves up one and a
    replacement player fills the bottom, so the hurt player's own rating counts for nothing (INJ-2) and his place counts the same whoever is behind
    him and in whatever order the places are (the review of SX.8k: with the next man's own rating an injury raised the strength of a team whose
    places were not in rating order, or whose last man was hurt). `hurt_before`: only the injuries of games before that week count (the computer's
    games of a week do not see the injuries of the player's game of the same week)."""
    places: list = [None] * D.PLACE_COUNT
    playing: dict = {}
    known = rows(league)
    if hurt_before is not None:
        known = {pid: row for pid, row in known.items() if row[2] < hurt_before}
    for index in range(D.PLACE_COUNT):
        player = league.player_at(team, index)
        if player is None:
            raise LeagueError("team %d has an empty place %d" % (team, index))
        if plays(league, player, week, staff, out, known):
            playing[player.id] = max(D.RATING_MIN, player.rating - (0 if player.id in out else penalty(league, player.id, week, known)))

    def entry(player, hurt=None):
        rating = playing[player.id]
        return player.id, player.name, rating if hurt is None else min(rating, stand_in_rating(hurt.pos))

    def substitute(position, hurt):
        row = stand_in(league, team, position, extra_stand_ins)
        if row is None and make is not None:
            row = make(position)
        if row is None:
            raise LeagueError("team %d has nobody to play %s and no stand-in" % (team, position))
        return (STAND_IN, position), row[2], row[3]

    depths = {}
    for position in D.POSITIONS:
        indices = D.PLACES_OF[position]
        group = [league.player_at(team, i) for i in indices]
        depth = group                                          # the depth order is the place order (the cut places the best first; season 1: as drawn)
        depths[position] = depth
        if position == "RET":
            continue
        for index, player in zip(indices, group):
            if player.id in playing:
                places[index] = entry(player)
                continue
            rank = depth.index(player)
            below = [q for q in depth[rank + 1:] if q.id in playing]
            above = [q for q in reversed(depth[:rank]) if q.id in playing]
            places[index] = entry((below or above)[0], player) if below or above else substitute(position, player)
    taken: set = set()
    for index, player in zip(D.PLACES_OF["RET"], [league.player_at(team, i) for i in D.PLACES_OF["RET"]]):
        if player.id in playing:
            places[index] = entry(player)
    for index, player in zip(D.PLACES_OF["RET"], [league.player_at(team, i) for i in D.PLACES_OF["RET"]]):
        if places[index] is not None:
            continue
        backs = [q for q in list(reversed(depths["RB"])) + list(reversed(depths["WR"])) if q.id in playing and q.id not in taken]
        if backs:
            taken.add(backs[0].id)
            places[index] = entry(backs[0], player)
        else:
            places[index] = substitute("RET", player)
    return places


def effective_sum(league: LeagueRecord, team: int, week: int, staff: bool = True, hurt_before=None) -> int:
    """The weighted sum of the ratings the team plays the week's game with (design 4.4 over the lineup): the healthy players only, a hurt player's
    place at replacement level (INJ-2)."""
    table = lineup(league, team, week, staff, hurt_before=hurt_before)
    return sum(D.WEIGHT[D.POSITION_OF_PLACE[i]] * rating for i, (_id, _name, rating) in enumerate(table))


def nobody_hurt(league: LeagueRecord) -> bool:
    return not league.injuries["hurt"]


def effective_sums(league: LeagueRecord, week: int) -> list:
    """The 32 sums of the computer's games of `week`: the season's sums (`league.sums`) moved by what the injuries take from each team, so a league with
    nobody hurt has exactly the season's sums (and the original's results at equal strengths)."""
    sums = list(league.sums)
    if nobody_hurt(league):
        return sums
    teams = {league.players[pid].team for pid, row in rows(league).items() if row[2] < week and status_of_row(row, week) != D.STATUS_HEALTHY}
    for team in sorted(teams):                       # (an injury of this week's game counts from the next week, as in the fast run)
        sums[team - 1] += effective_sum(league, team, week, hurt_before=week) - league.strength_sum(team)
    return sums


# ----- an injury -----

def kinds_for(position: str) -> list:
    return [kind for kind in T.FR_INJ_KINDS if position not in kind[4]]


def draw_kind(rnd, position: str):
    kinds = kinds_for(position)
    roll = rnd.below(sum(kind[3] for kind in kinds))
    for kind in kinds:
        if roll < kind[3]:
            return kind
        roll -= kind[3]
    raise AssertionError("the shares of the kinds")


def kind_of(kind_id: str):
    for kind in T.FR_INJ_KINDS:
        if kind[0] == kind_id:
            return kind
    raise LeagueError("no injury kind %r" % (kind_id,))


def max_games() -> int:
    """The most games one injury can keep a player out from the week after his game (the longest kind, one more when he was hurt worse)."""
    return max(kind[2] for kind in T.FR_INJ_KINDS) + 1


def width_for(games: int) -> int:
    return min(T.FR_INJ_RANGE_MAX, (games + 1) // 2)


def draw_injury(rnd, position: str, worse: int = 0) -> tuple:
    """(kind id, games missed, offset of the spoken range): the kind, its games (`worse` more for a player hurt worse) and the range's offset."""
    kind = draw_kind(rnd, position)
    games = rnd.below(kind[2] - kind[1] + 1) + kind[1] + worse
    offset = rnd.below(width_for(games) + 1)
    return kind[0], games, offset


def injure(league: LeagueRecord, pid: int, kind: str, games: int, offset: int, week: int) -> list:
    """He was hurt in the game of `week` and misses `games` from the next week on when he rests; a player already hurt keeps the later of the two."""
    back = week + 1 + games
    row = row_of(league, pid)
    if row is None:
        row = [pid, kind, week, back, width_for(games), offset, 0]
        league.injuries["hurt"].append(row)
        return row
    if back > row[3]:
        row[1:6] = [kind, week, back, width_for(games), offset]
        row[6] = 0
    return row


def spoken_range(row, week: int) -> tuple:
    """(low, high) of the games he misses from `week` on as they are told: the first range narrows by one a week and always holds the truth."""
    games = left(row, week)
    width = max(0, row[4] - max(0, week - row[2] - 1))       # told first before the week after the game he was hurt in
    offset = min(row[5], width)
    low = games - offset
    return max(1, low), low + width


# ----- the week's draws (one code path: the program's preparation and the fast run) -----

class WeekInjuries:
    """What the draws of one week did: the new injuries (player id, kind, the week, from a game the engine played or not), the players hurt worse, the
    players back, the new stand-ins."""

    def __init__(self):
        self.new: list = []
        self.again: list = []
        self.worse: list = []
        self.back: list = []
        self.stand_ins: list = []
        self.workload: list = []               # SX.8o: the backs hit by the workload rule's draw


def _place_by_weight(rnd, weights=None) -> int:
    """A place of the week's game part: FR_INJ_GAME_WEIGHT, the backs' and the receivers' places by their shares of the carries (SX.8o, `weights`)."""
    if weights is None:
        weights = [T.FR_INJ_GAME_WEIGHT[D.POSITION_OF_PLACE[i]] for i in range(D.PLACE_COUNT)]
    roll = rnd.below(sum(weights))
    for index, weight in enumerate(weights):
        if roll < weight:
            return index
        roll -= weight
    raise AssertionError("the weights of the places")


def at_limit(league: LeagueRecord, team: int, pid: int, week: int, more: int = 0) -> bool:
    """INJ-6: an injury from the games of `week` would make one more of the team's players hurt for the next week while FR_INJ_TEAM_MAX (with `more` hurt in
    the game in progress) are already: it is not drawn. A player who is hurt for the next week anyway adds nobody."""
    if not healthy(league, pid, week + 1):
        return False
    return hurt_count(league, team, week + 1) + more >= T.FR_INJ_TEAM_MAX


def _hit(league, team, week, index, rnd, done: WeekInjuries, table: list) -> None:
    """A hit at `index` of the week's lineup (`table[0]`): the player who plays the place is hurt; the lineup is made again at once, so a hurt man is not
    hit again in the same week (the next man up plays his place). A new injury (`done.new`) is one of a player who was fit for the game; a hit of a
    player who played hurt is the same injury made longer (`done.again`), as an injury report lists him once."""
    identity = table[0][index][0]
    if identity in table[1]:
        return
    if not isinstance(identity, int):                       # a stand-in is not hurt
        return
    if at_limit(league, team, identity, week):
        return
    player = league.players[identity]
    fit = healthy(league, identity, week)
    kind, games, offset = draw_injury(rnd, player.pos)
    injure(league, identity, kind, games, offset, week)
    (done.new if fit else done.again).append((identity, kind, week))
    table[1].add(identity)
    table[0] = week_table(league, team, week, table[1])


def week_table(league: LeagueRecord, team: int, week: int, hit=frozenset()) -> list:
    """The lineup that played the game of `week` (the injuries of earlier games), less the players the week's draws have hit so far; a place left with
    nobody takes a placeholder for the rest of the week's draws (a stand-in is never hit, and `settle` signs the real one)."""
    return lineup(league, team, week, staff=False, out=frozenset(hit), hurt_before=week,
                  make=lambda position: [team, position, "", stand_in_rating(position)])


def after_games(league: LeagueRecord, week: int, rnd, surnames: list, played=()) -> WeekInjuries:
    """The injuries of the games of `week` (1 to FR_INJ_LAST_WEEK): hurt worse, practice, and the game part of every team whose game the engine did not
    play (`played`: the two teams of the player's game, whose injuries came per play). Then the players fit for the next week leave the list (`back`) and
    a group with nobody fit gets its stand-in. Changes the league; returns what it did."""
    done = WeekInjuries()
    if not 1 <= week <= T.FR_INJ_LAST_WEEK:
        return done
    from . import workload
    for team in range(1, D.TEAMS + 1):
        table = [week_table(league, team, week), set()]
        rated = workload.rated_table(league, team, table[0])      # SX.8o: the ratings the game read (the carry weights of its backs and receivers)
        for player, state in hurt_of(league, team, week):
            if row_of(league, player.id)[2] >= week:
                continue                                   # hurt in this week's game itself (a game the engine played): no draw of "worse"
            if state in (D.STATUS_DOUBTFUL, D.STATUS_QUESTIONABLE) and plays(league, player, week, staff=False):
                if rnd.below(1000) < T.FR_INJ_WORSE[state] and not at_limit(league, team, player.id, week):
                    kind, games, offset = draw_injury(rnd, player.pos, worse=1)
                    injure(league, player.id, kind, games, offset, week)
                    done.worse.append((player.id, kind, week))
        draws, chance = T.FR_INJ_PRACTICE
        for _ in range(draws):
            if rnd.below(10000) < chance:
                _hit(league, team, week, rnd.below(D.PLACE_COUNT), rnd, done, table)
        if team in played:
            continue                                       # its carries and its workload came per play (injury_flow.GameInjuries)
        draws, chance = T.FR_INJ_GAME
        shares = workload.place_weights(rated)
        for _ in range(draws):
            if rnd.below(10000) < chance:
                _hit(league, team, week, _place_by_weight(rnd, shares), rnd, done, table)
        carries = workload.expected_carries(rated)
        for pid, tenths in carries.items():                # SX.8o, the workload rule (INJ-3): the backs' carries of the season before this game
            extra = workload.extra_percent(league, pid)
            if extra and pid not in table[1]:
                if rnd.below(10000) < workload.game_chance(tenths, extra):
                    index = next((i for i in D.PLACES_OF["RB"] if table[0][i][0] == pid), None)
                    if index is not None:
                        before = len(done.new) + len(done.again)
                        _hit(league, team, week, index, rnd, done, table)
                        if len(done.new) + len(done.again) > before:
                            done.workload.append(pid)
        for pid, tenths in carries.items():
            workload.add_carries(league, pid, tenths)
    settle(league, week + 1, rnd, surnames, done)
    return done


def settle(league: LeagueRecord, week: int, rnd, surnames: list, done: WeekInjuries | None = None) -> WeekInjuries:
    """Before the games of `week`: the players fit again leave the list, and every group with nobody fit gets its stand-in (in team and group order)."""
    done = done or WeekInjuries()
    keep = []
    for row in league.injuries["hurt"]:
        (keep if left(row, week) > 0 else done.back).append(row)
    done.back = [row[0] for row in done.back]
    league.injuries["hurt"][:] = keep
    for team in range(1, D.TEAMS + 1):

        def make(position, team=team):
            row = make_stand_in(league, team, position, rnd, surnames)
            league.injuries["stand_ins"].append(row)
            done.stand_ins.append(row)
            return row
        lineup(league, team, week, staff=False, make=make)     # every hurt player resting: the most stand-ins any decision of the week can need
    return done


def decide(league: LeagueRecord, pid: int, week: int, play: bool) -> None:
    """The coach's decision for a doubtful or questionable player before the game of `week`."""
    row = row_of(league, pid)
    if row is not None:
        row[6] = week if play else 0


def lineup_decided(league: LeagueRecord, team: int, week: int, staff: bool) -> None:
    """The kick-off of the player's game: his decisions are written into the rows (with the staff setting on, the staff's rule), so the week's draws know
    who played hurt."""
    for player, state in hurt_of(league, team, week):
        if state in (D.STATUS_DOUBTFUL, D.STATUS_QUESTIONABLE):
            decide(league, player.id, week, plays(league, player, week, staff))


def end_of_season(league: LeagueRecord) -> None:
    """The offseason begins: every player is fit for the next season, the stand-ins leave (design: injuries are a matter of the season)."""
    league.injuries = empty()


def ask_gap(league: LeagueRecord, team: int, pid: int, week: int) -> int:
    """How many rating points the team loses at his place when he rests (his rating against who would play it): the to-do list asks when it is large."""
    player = league.players[pid]
    resting = lineup(league, team, week, staff=False, out=frozenset({pid}))
    return player.rating - resting[player.place][2]


def to_ask(league: LeagueRecord, week: int) -> list:
    """The player's doubtful and questionable players the to-do list asks about this week: a gap of FR_INJ_ASK_GAP or more, the biggest first (equal: place
    order), at most FR_INJ_ASK_MAX."""
    if not 1 <= week <= D.REGULAR_WEEKS:
        return []
    found = []
    for player, state in hurt_of(league, league.team, week):
        if state in (D.STATUS_DOUBTFUL, D.STATUS_QUESTIONABLE):
            gap = ask_gap(league, league.team, player.id, week)
            if gap >= T.FR_INJ_ASK_GAP:
                found.append((-gap, player.place, player.id))
    found.sort()
    return [pid for _gap, _place, pid in found[:T.FR_INJ_ASK_MAX]]


# ----- the whole-file check (format 6) -----

def check_injuries(league: LeagueRecord, whole) -> None:
    record = league.injuries
    if not isinstance(record, dict) or set(record) != {"hurt", "stand_ins", "report"}:
        raise LeagueError("the injuries are %r" % (type(record).__name__,))
    hurt, standing, report = record["hurt"], record["stand_ins"], record["report"]
    if not isinstance(hurt, list) or len(hurt) > D.MAX_HURT or not isinstance(standing, list) or len(standing) > D.TEAMS * len(D.POSITIONS):
        raise LeagueError("the injury lists are %r" % (record,) if len(str(record)) < 80 else "the injury lists are too long")
    if league.stage != "season" and (hurt or standing):
        raise LeagueError("injuries outside the season")
    seen = set()
    for row in hurt:
        if not isinstance(row, list) or len(row) != HURT_FIELDS:
            raise LeagueError("an injury is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "an injured player")
        player = league.players.get(row[0])
        if player is None or player.status != "active" or row[0] in seen:
            raise LeagueError("the injured player %r is not an active player, or is there twice" % (row[0],))
        seen.add(row[0])
        if row[1] not in KIND_IDS:
            raise LeagueError("an injury of the kind %r" % (row[1],))
        whole(row[2], 1, T.FR_INJ_LAST_WEEK, "an injury's week")
        whole(row[3], row[2] + 1, row[2] + 1 + max_games(), "an injury's return")
        whole(row[4], 0, T.FR_INJ_RANGE_MAX, "an injury's range")
        whole(row[5], 0, row[4], "an injury's offset")
        if row[6] != 0:
            whole(row[6], row[2] + 1, D.REGULAR_WEEKS, "an injury's decision")
    places = set()
    for row in standing:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a stand-in is %r" % (row,))
        whole(row[0], 1, D.TEAMS, "a stand-in's team")
        if row[1] not in D.POSITIONS or (row[0], row[1]) in places:
            raise LeagueError("a stand-in of the position %r, or a second one" % (row[1],))
        places.add((row[0], row[1]))
        if not isinstance(row[2], str) or not 1 <= len(row[2]) <= 40 or any(ord(c) < 32 for c in row[2]):
            raise LeagueError("a stand-in has the name %r" % (row[2],))
        whole(row[3], D.RATING_MIN, D.RATING_MAX, "a stand-in's rating")
    if report is not None:
        if not isinstance(report, dict) or set(report) != {"season", "week", "lines", "told"}:
            raise LeagueError("the injury report is %r" % (report,))
        whole(report["season"], 1, D.MAX_SEASONS, "the injury report's season")
        whole(report["week"], 1, D.REGULAR_WEEKS, "the injury report's week")
        whole(report["told"], 0, 1, "the injury report's told mark")
        lines = report["lines"]
        if not isinstance(lines, list) or len(lines) > D.PLACE_COUNT + 2 or any(
                not isinstance(line, str) or not 1 <= len(line) <= 2000 or any(ord(c) < 32 for c in line) for line in lines):
            raise LeagueError("the injury report's lines are %r" % (lines,) if len(str(lines)) < 80 else "the injury report's lines")
