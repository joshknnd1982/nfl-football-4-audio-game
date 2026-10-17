"""Trades of the Franchise: the value rule, the picks of the coming draft and the computer teams' trades (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8j (F7, N6.7, research B5, F1 and G, D-070). Plain rules over the league record, no speech, no files and no draw, so the weekly
preparation of the program (`weekly.py`), the player's own proposals (`trade_flow.py`) and the calibration's fast run use the very same code.

A trade swaps ONE player of each team, both of the SAME position, so every place stays filled in the season (invariant I3) and nobody is released for it
(no dead money); the side that must give more adds up to `FR_TRADE_PICKS_MAX` picks of the coming draft. A pick is (round, the team whose pick it was by the
draft order); its owner is that team unless a trade moved it (`LeagueRecord.trades["picks"]`, the exceptions only). The draft makes the owners its own when it
begins (`draft.Draft.create`) and the table starts empty again.

    situation                        contending, middle or rebuilding, from the team's record (research F1)
    player_value / pick_value        what a player or a pick is worth to a team in its situation (research B5: rating, age, potential, contract; picks by round)
    gain                             what a trade is worth to one of its teams: what it gets less what it gives
    build                            the trade two computer teams would agree on for two players: picks added by the side that must give more, both gaining the margin of the position (`margin_of`)
    search / week                    the computer teams' trades of a week, ONE code path: a trade of the player's team is an offer that waits for his answer
    block_offers / ask               the other teams' answers to the player's proposals, by the same value rule
    execute / problems / check_trades   a trade made, why one cannot be made, the whole-file check of `LeagueRecord.trades`

Every number is data in `extras\\tuning.py` (the `FR_TRADE_` names).
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import tuning as T
from . import aging
from . import contracts as CT
from . import data as D

CONTEND, MIDDLE, REBUILD = "contend", "middle", "rebuild"
KEYS = ("picks", "log")
KIND_COMPUTER, KIND_OFFER, KIND_PLAYER = 0, 1, 2      # a trade of two computer teams; an offer the player (or the staff for him) accepted; the player's own proposal


def empty() -> dict:
    return {"picks": [], "log": []}


# ----- the picks of the coming draft -----

def owner(league, round_no: int, original: int) -> int:
    for r, o, own in league.trades["picks"]:
        if r == round_no and o == original:
            return own
    return original


def picks_of(league, team: int) -> list:
    """The picks of the coming draft the team owns: (round, original team), the earliest round first, its own pick of a round before another's."""
    out = [(r, team) for r in range(1, D.DRAFT_ROUNDS + 1) if owner(league, r, team) == team]
    out += [(r, o) for r, o, own in league.trades["picks"] if own == team and o != team]
    return sorted(out, key=lambda pick: (pick[0], pick[1] != team, pick[1]))


def move_pick(league, pick: tuple, to_team: int) -> None:
    round_no, original = pick
    table = [row for row in league.trades["picks"] if not (row[0] == round_no and row[1] == original)]
    if to_team != original:
        table.append([round_no, original, to_team])
    table.sort()
    league.trades["picks"] = table


# ----- the situation of a team (research F1) -----

def standing(records: list, team: int) -> tuple:
    return records[2 * (team - 1)], records[2 * (team - 1) + 1]


def situation(records: list, team: int) -> str:
    """Contending when the team has won FR_TRADE_CONTEND more games than it lost, rebuilding when it lost FR_TRADE_REBUILD more than it won, else middle;
    middle for everybody before FR_TRADE_MIN_GAMES games."""
    wins, losses = standing(records, team)
    if wins + losses < T.FR_TRADE_MIN_GAMES:
        return MIDDLE
    if wins - losses >= T.FR_TRADE_CONTEND:
        return CONTEND
    if losses - wins >= T.FR_TRADE_REBUILD:
        return REBUILD
    return MIDDLE


def situations(records: list) -> dict:
    return {team: situation(records, team) for team in range(1, D.TEAMS + 1)}


# ----- the value rule (research B5) -----

def worth(player) -> int:
    """What the player gives the team over the rookie of the fill who would take his place: the position's weight times the rating over the fill's middle rating
    (the unit of `resign.value`)."""
    return D.WEIGHT[player.pos] * (player.rating - CT.replacement_rating(player.pos))


def age_share(age: int, how: str) -> int:
    for last_age, share in T.FR_TRADE_AGE[how]:
        if age <= last_age:
            return share
    return T.FR_TRADE_AGE[how][-1][1]


def _toward_zero(numerator: int, divisor: int) -> int:
    """Whole-number division that rounds toward zero, so a saving and a cost of the same size count the same."""
    value = abs(numerator) // divisor
    return value if numerator >= 0 else -value


def player_value(player, how: str) -> int:
    """What the player is worth to a team in this situation: his worth (never under 0) weighted by his age, by his potential while he is young, plus what his
    contract saves against his market price for the years he has left (minus what it costs over it)."""
    value = max(0, worth(player)) * age_share(player.age, how) // 100
    if player.age <= T.FR_TRADE_YOUNG:
        value = value * T.FR_TRADE_POTENTIAL[player.potential] // 100
    saving = (CT.market_salary(player.pos, player.rating) - player.salary) * player.years
    return value + _toward_zero(saving, T.FR_TRADE_MONEY_DIVISOR)


def margin_of(position: str) -> int:
    """What a computer team must gain from a trade of two players of this position: FR_TRADE_MARGIN rating points of the position, in value (times the
    position's weight), so a trade of linemen and a trade of quarterbacks ask the same improvement at the position (a flat margin let quarterbacks alone through)."""
    return T.FR_TRADE_MARGIN * D.WEIGHT[position]


def pick_value(round_no: int, how: str) -> int:
    return T.FR_TRADE_PICK_VALUE[round_no - 1] * T.FR_TRADE_PICK_SHARE[how] // 100


# ----- a trade -----

@dataclass(frozen=True)
class Trade:
    """Team `a` gives player `give_a` and the picks `picks_a`; team `b` gives `give_b` and `picks_b` (picks as (round, original team))."""
    a: int
    b: int
    give_a: int
    give_b: int
    picks_a: tuple = ()
    picks_b: tuple = ()

    def to_list(self) -> list:
        return [self.a, self.b, self.give_a, self.give_b, [list(p) for p in self.picks_a], [list(p) for p in self.picks_b]]

    @classmethod
    def from_list(cls, row) -> "Trade":
        a, b, give_a, give_b, picks_a, picks_b = row
        return cls(a, b, give_a, give_b, tuple(tuple(p) for p in picks_a), tuple(tuple(p) for p in picks_b))

    def side(self, team: int) -> tuple:
        """(the player the team gives, the player it gets, the picks it gives, the picks it gets)."""
        if team == self.a:
            return self.give_a, self.give_b, self.picks_a, self.picks_b
        return self.give_b, self.give_a, self.picks_b, self.picks_a

    def other(self, team: int) -> int:
        return self.b if team == self.a else self.a


def gain(league, trade: Trade, team: int, how: str) -> int:
    """What the trade is worth to `team` in the situation `how`: the player and the picks it gets less the player and the picks it gives."""
    gives, gets, picks_out, picks_in = trade.side(team)
    return (player_value(league.players[gets], how) - player_value(league.players[gives], how)
            + sum(pick_value(r, how) for r, _ in picks_in) - sum(pick_value(r, how) for r, _ in picks_out))


def traded_this_season(league) -> set:
    return {pid for row in league.trades["log"] for pid in (row[3], row[4])}


def trades_of(league, team: int) -> int:
    """How many trades the team made this season."""
    return sum(1 for row in league.trades["log"] if team in (row[1], row[2]))


def in_window(league, week: int) -> bool:
    """Trades are made in the regular season up to the kick-off of week FR_TRADE_LAST_WEEK (the trade deadline)."""
    from .league import SEASON
    return league.stage == SEASON and 1 <= week <= T.FR_TRADE_LAST_WEEK


def cap_after(league, trade: Trade, team: int) -> int:
    gives, gets, _, _ = trade.side(team)
    return CT.cap_used(league, team) - league.players[gives].salary + league.players[gets].salary


def problems(league, trade: Trade, week: int) -> str | None:
    """Why the trade cannot be made now (a short reason for the tests and the checks), or None when it can."""
    if not in_window(league, week):
        return "outside the trade window"
    if trade.a == trade.b or not (1 <= trade.a <= D.TEAMS and 1 <= trade.b <= D.TEAMS):
        return "the teams"
    pa, pb = league.players.get(trade.give_a), league.players.get(trade.give_b)
    for player, team in ((pa, trade.a), (pb, trade.b)):
        if player is None or player.status != "active" or player.team != team or player.place < 0:
            return "a player who is not on his team"
    if pa.pos != pb.pos:
        return "players of different positions"
    if {pa.id, pb.id} & traded_this_season(league):
        return "a player traded already this season"
    for team, picks in ((trade.a, trade.picks_a), (trade.b, trade.picks_b)):
        if len(picks) > T.FR_TRADE_PICKS_MAX or len(set(picks)) != len(picks):
            return "too many picks"
        owned = set(picks_of(league, team))
        if any(tuple(pick) not in owned for pick in picks):
            return "a pick the team does not own"
    for team in (trade.a, trade.b):
        if cap_after(league, trade, team) > T.FR_CAP:
            return "over the cap"
    return None


def execute(league, trade: Trade, week: int, kind: int) -> None:
    """The trade is made: the two players change places (the same position), the picks change owners, the teams' places are put in rating order, the
    season's log and the teams' strengths for the computer's games are brought up to date (design 5.2: the computer's results follow the rosters as they
    are). The caller has checked `problems` and writes league.sav."""
    pa, pb = league.players[trade.give_a], league.players[trade.give_b]
    index_a, index_b = pa.place, pb.place
    league.rosters[trade.a - 1][index_a] = pb.id
    league.rosters[trade.b - 1][index_b] = pa.id
    pa.team, pa.place = trade.b, index_b
    pb.team, pb.place = trade.a, index_a
    for pick in trade.picks_a:
        move_pick(league, pick, trade.b)
    for pick in trade.picks_b:
        move_pick(league, pick, trade.a)
    league.trades["log"].append([week, trade.a, trade.b, pa.id, pb.id, [list(p) for p in trade.picks_a], [list(p) for p in trade.picks_b], kind])
    aging.place_by_rating(league, trade.a)
    aging.place_by_rating(league, trade.b)
    if len(league.sums) == D.TEAMS:
        league.sums[trade.a - 1] = league.strength_sum(trade.a)
        league.sums[trade.b - 1] = league.strength_sum(trade.b)


# ----- the picks that even a trade -----

def cover(gap: int, picks: list, how: str) -> tuple | None:
    """The picks (of `picks`, the giver's) that give the receiver, valued in the receiver's situation `how`, at least `gap` more: the cheapest single pick that is
    enough; else the most valuable pick and again for what is left, at most FR_TRADE_PICKS_MAX picks. None when they cannot. () when nothing is needed."""
    chosen: list = []
    left = list(picks)
    while gap > 0:
        if len(chosen) >= T.FR_TRADE_PICKS_MAX or not left:
            return None
        cheapest_first = sorted(left, key=lambda p: (pick_value(p[0], how), -p[0], p[1]))
        enough = [p for p in cheapest_first if pick_value(p[0], how) >= gap]
        pick = enough[0] if enough else cheapest_first[-1]
        chosen.append(pick)
        left.remove(pick)
        gap -= pick_value(pick[0], how)
    return tuple(sorted(chosen))


def build(league, a: int, b: int, give_a, give_b, how: dict) -> Trade | None:
    """The trade two computer teams agree on for these two players (research B5): when one side gains less than the margin (`margin_of`) the other adds its picks
    (`cover`), and both must then gain at least the margin in their own situations. None when no such trade exists."""
    plain = Trade(a, b, give_a.id, give_b.id)
    gain_a, gain_b = gain(league, plain, a, how[a]), gain(league, plain, b, how[b])
    margin = margin_of(give_a.pos)
    if gain_a >= margin and gain_b >= margin:
        return plain
    if gain_a < margin and gain_b < margin:
        return None
    payer, receiver = (a, b) if gain_b < margin else (b, a)
    picks = cover(margin - min(gain_a, gain_b), picks_of(league, payer), how[receiver])
    if picks is None:
        return None
    trade = Trade(a, b, give_a.id, give_b.id, picks if payer == a else (), picks if payer == b else ())
    if gain(league, trade, a, how[a]) < margin or gain(league, trade, b, how[b]) < margin:
        return None
    return trade


def group(league, team: int, position: str) -> list:
    return [p for p in league.group_of(team, position) if p is not None]


def rotation(season: int, week: int) -> list:
    """The order in which the teams look for trades this week: team 1 to 32 turned by the season and the week, so no team is always first (a rule that favors a
    side is a parity machine, B-P90)."""
    start = (season * 11 + week * 5) % D.TEAMS
    return [(start + i) % D.TEAMS + 1 for i in range(D.TEAMS)]


def points(value: int, position: str) -> int:
    """A gain in thousandths of a rating point of the position (value over the position's weight): how the search compares trades of different positions."""
    return value * 1000 // D.WEIGHT[position]


def search(league, week: int, records: list) -> list:
    """The computer teams' trades of this week, worked out on the league as it stands (the teams of one trade take no other this week, so the trades do not
    depend on each other). Every contending team looks at every rebuilding team's best veteran (age FR_TRADE_VETERAN_AGE or more) of each position for one of
    its own players of that position rated at least FR_TRADE_UPGRADE lower; for every pair of a contender and a rebuilder it keeps the trade the contender gains
    most from (`build`, the cap allowing; the gain in rating points of the position, `points`; the first of equal gains in the order of the search). Then the
    week takes these trades the greatest gain first (equal gains: the week's turned order of the contender, then of the rebuilder, `rotation`), each team in one
    trade, at most FR_TRADE_WEEK_MAX; a team starts at most FR_TRADE_SEASON_MAX a season. Taking the best trade of the week, not the first contender's, keeps a team's number from deciding (the SX.8j review: with one trade a week the
    turned order alone gave the trade to its first contender, and the order evens out only over 32 seasons). No draw; nothing is changed."""
    if not T.FR_TRADE_FIRST_WEEK <= week <= T.FR_TRADE_LAST_WEEK or not in_window(league, week):
        return []
    how = situations(records)
    traded = traded_this_season(league)
    order = rotation(league.season, week)
    able = {team for team in order if trades_of(league, team) < T.FR_TRADE_SEASON_MAX}
    contenders = [team for team in order if how[team] == CONTEND and team in able]
    rebuilders = [team for team in order if how[team] == REBUILD and team in able]
    candidates: list = []
    for place, c in enumerate(contenders):
        for other_place, r in enumerate(rebuilders):
            best, best_points = None, None
            for position in D.POSITIONS:
                veterans = [p for p in group(league, r, position) if p.age >= T.FR_TRADE_VETERAN_AGE and p.id not in traded]
                if not veterans:
                    continue
                get = max(veterans, key=lambda p: (p.rating, -p.id))
                for give in group(league, c, position):
                    if give.id in traded or give.rating > get.rating - T.FR_TRADE_UPGRADE:
                        continue
                    trade = build(league, c, r, give, get, how)
                    if trade is None or problems(league, trade, week) is not None:
                        continue
                    value = points(gain(league, trade, c, how[c]), position)
                    if best_points is None or value > best_points:
                        best, best_points = trade, value
            if best is not None:
                candidates.append((-best_points, place, other_place, best))
    candidates.sort(key=lambda row: (row[0], row[1], row[2]))
    busy: set = set()
    out: list = []
    for _points, _place, _other_place, trade in candidates:
        if len(out) >= T.FR_TRADE_WEEK_MAX:
            break
        if trade.a in busy or trade.b in busy:
            continue
        out.append(trade)
        busy |= {trade.a, trade.b}
    return out


def week(league, week_no: int, records: list) -> tuple:
    """The trades of the week's preparation: the search; every trade of two computer teams is made at once, a trade of the player's team is returned as an offer
    for him (his to-do list, or the staff's answer when the staff handles it). The fast run has no player's team (team 0): every trade is made. Returns (the
    trades made, the offers)."""
    made, offers = [], []
    for trade in search(league, week_no, records):
        if league.team in (trade.a, trade.b):
            offers.append(trade)
        else:
            execute(league, trade, week_no, KIND_COMPUTER)
            made.append(trade)
    return made, offers


# ----- the player's own proposals (`trade_flow.py` speaks them) -----

def block_offers(league, team: int, player, records: list, week: int) -> list:
    """The player puts one of his players on the block: every other team that would gain the margin of the position from him for one of its own players of the same position
    makes its best offer for the player's team (the staff's view: the most it is worth to the player's team), adding as many of its picks as it can while it
    still gains the margin (the most valuable first). The best FR_TRADE_LIST offers, best first (equal: the order of the teams). [(Trade, the player's gain)]."""
    how = situations(records)
    traded = traded_this_season(league)
    if player.id in traded:
        return []
    offers = []
    margin = margin_of(player.pos)
    for other in rotation(league.season, week):
        if other == team:
            continue
        best = None
        for theirs in group(league, other, player.pos):
            if theirs.id in traded:
                continue
            plain = Trade(team, other, player.id, theirs.id)
            if gain(league, plain, other, how[other]) < margin:
                continue
            sweet: list = []
            for pick in picks_of(league, other):
                if len(sweet) >= T.FR_TRADE_PICKS_MAX:
                    break
                trial = Trade(team, other, player.id, theirs.id, (), tuple(sweet + [pick]))
                if gain(league, trial, other, how[other]) >= margin:
                    sweet.append(pick)
            trade = Trade(team, other, player.id, theirs.id, (), tuple(sorted(sweet)))
            if problems(league, trade, week) is not None:
                continue
            value = gain(league, trade, team, how[team])
            if best is None or value > best[1]:
                best = (trade, value)
        if best is not None:
            offers.append(best)
    offers.sort(key=lambda pair: -pair[1])                   # sorted keeps the order of the teams for equal gains
    return offers[:T.FR_TRADE_LIST]


def ask(league, team: int, give, get, records: list, week: int) -> Trade | None:
    """The player asks for `get` (another team's player) and offers `give` (his own of the same position): the other team agrees when it gains the margin,
    asking the player's picks to make it up when it does not (`cover`, valued in its situation). None when it says no."""
    if give.pos != get.pos or give.team != team or get.team == team:
        return None
    how = situations(records)
    other = get.team
    plain = Trade(team, other, give.id, get.id)
    short = margin_of(get.pos) - gain(league, plain, other, how[other])
    picks = cover(short, picks_of(league, team), how[other]) if short > 0 else ()
    if picks is None:
        return None
    trade = Trade(team, other, give.id, get.id, picks, ())
    if problems(league, trade, week) is not None or gain(league, trade, other, how[other]) < margin_of(get.pos):
        return None
    return trade


# ----- the season's end and the whole-file check -----

def new_season(league) -> None:
    """Stage 6: the season's trades are history; the picks of the next draft start with their teams (the draft made the table empty)."""
    league.trades = {"picks": list(league.trades["picks"]), "log": []}


def check_trades(league, whole) -> None:
    """LeagueError (through `whole`) unless `league.trades` is whole: the pick table (round 1 to 7, two different teams, one row per pick; empty while a draft
    is in progress or done), and the season's log (weeks of the window, two teams, two players of the league, picks, the kind)."""
    from .league import LeagueError
    data = league.trades
    if not isinstance(data, dict) or set(data) != set(KEYS):
        raise LeagueError("the trades hold %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    table = data["picks"]
    if not isinstance(table, list) or len(table) > D.DRAFT_PICKS:
        raise LeagueError("the pick table is %r" % (type(table).__name__,))
    seen: set = set()
    for row in table:
        if not isinstance(row, list) or len(row) != 3:
            raise LeagueError("a traded pick is %r" % (row,))
        whole(row[0], 1, D.DRAFT_ROUNDS, "a traded pick's round")
        whole(row[1], 1, D.TEAMS, "a traded pick's team")
        whole(row[2], 1, D.TEAMS, "a traded pick's owner")
        if row[1] == row[2] or (row[0], row[1]) in seen:
            raise LeagueError("the traded pick %r is listed twice or with its own team" % (row,))
        seen.add((row[0], row[1]))
    if table and league.draft is not None:
        raise LeagueError("traded picks while a draft is in progress")
    log = data["log"]
    if not isinstance(log, list) or len(log) > D.MAX_TRADES:
        raise LeagueError("the trades of the season are %r" % (type(log).__name__,))
    for row in log:
        if not isinstance(row, list) or len(row) != 8:
            raise LeagueError("a trade is %r" % (row,))
        whole(row[0], 1, T.FR_TRADE_LAST_WEEK, "a trade's week")
        whole(row[1], 1, D.TEAMS, "a trade's team")
        whole(row[2], 1, D.TEAMS, "a trade's team")
        whole(row[7], KIND_COMPUTER, KIND_PLAYER, "a trade's kind")
        if row[1] == row[2]:
            raise LeagueError("a team traded with itself: %r" % (row,))
        for pid in (row[3], row[4]):
            whole(pid, 1, 10 ** 9, "a traded player")
            if pid not in league.players:
                raise LeagueError("player %r of a trade is not in the league" % (pid,))
        for picks in (row[5], row[6]):
            if not isinstance(picks, list) or len(picks) > T.FR_TRADE_PICKS_MAX:
                raise LeagueError("the picks of a trade are %r" % (picks,))
            for pick in picks:
                if not isinstance(pick, list) or len(pick) != 2:
                    raise LeagueError("a pick of a trade is %r" % (pick,))
                whole(pick[0], 1, D.DRAFT_ROUNDS, "a pick's round")
                whole(pick[1], 1, D.TEAMS, "a pick's team")
