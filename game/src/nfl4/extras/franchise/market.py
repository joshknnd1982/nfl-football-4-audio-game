"""Free agency of the Franchise: the market of the players whose contracts ended (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8i (F6, N6.6, research B4, F1 and G, D-068). Plain rules over the league record, no speech, no files and no draw, so stage 8 of
the offseason (`market_flow.py`) and the calibration's fast run use the very same code.

The market is the players with the status "free" of this offseason (`pool`): the ones stage 7 did not sign again. It runs in `FR_FA_ROUNDS` rounds. In
a round every team places its offers (a computer team and the staff by `team_bids`, the player by what he chooses), then all the offers are judged together
(`resolve`): the free agents one at a time, the most valuable first, each to the offer with the highest score among those whose team still has an open place at his
position and the room under the cap. A free agent nobody signed asks `FR_FA_PRICE_DROP` percent less in the next round.

    pool / price                   who is on the market and what he asks in a round
    open_places / room             what a team can still sign: its empty places by position, the most it may pay
    team_bids / computer_bids      a team's offers for a round (the computer teams', the staff's for the player's team, and the fast run's)
    resolve / run_round            the judgement of a round: the best offer wins when its team can afford it
    check_market                   the whole-file check of `LeagueRecord.market`, the stage in progress

A team signs only into an EMPTY place (no stacking at a position, no release to make room, no big dead money), only a player rated `FR_FA_MIN_RATING` or
more, and never over its cap (`room`). The research's invariants (G): every team under the cap after the offseason, the best offer wins when two teams bid and both can
afford it, computer teams stop when the need is filled. All numbers are data in `extras\\tuning.py` (the `FR_FA_` names).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .. import tuning as T
from . import contracts as CT
from . import data as D
from . import resign as R

KEYS = ("round", "offers", "signed", "lost", "staff", "moves")      # SX.8m: "moves", the signings of the rounds judged so far (comp.py)


# ----- the market -----

def pool(league) -> list:
    """The free agents of this offseason (status "free", left in the season that just ended; a star kept for history from an earlier season is no part of
    it), the most valuable first (`resign.value`)."""
    return sorted((p for p in league.players.values() if p.status == "free" and p.left == league.season), key=R.value)


def price(player, round_no: int) -> tuple:
    """(salary, years) a free agent asks in this round (1 to `FR_FA_ROUNDS`): what he asked in stage 7 (`resign.asking`), less `FR_FA_PRICE_DROP` percent for
    every earlier round he was not signed, rounded half up, never under the minimum of his seasons."""
    salary, years = R.asking(player)
    cut = T.FR_FA_PRICE_DROP * (round_no - 1)
    return max(CT.min_salary(player.seasons), (salary * (100 - cut) + 50) // 100), years


def more(salary: int) -> int:
    """What "offer more" offers: `FR_FA_OFFER_MORE` percent over the price, rounded half up, never over the maximum salary."""
    return min(T.FR_MAX_SALARY, (salary * (100 + T.FR_FA_OFFER_MORE) + 50) // 100)


# ----- what a team can still sign -----

def filled(league, team: int, position: str) -> int:
    """SR.5: the men of the family on the team's roster."""
    from . import real_roster
    return real_roster.family_count(league, team, position)


def open_places(league, team: int, staff: bool = True) -> list:
    """SR.5 (design 21.7 (3)): the families the team holds fewer of than its roster target (FR_ROSTER_TARGET) and how many, in the roster menu's order:
    [(group, count)]; for the staff (the computer's teams) at most the room the 53 has left, the families under their minimum first. The player's own
    offers (`staff=False`) see every family under its target."""
    from . import real_roster
    out = []
    men = real_roster.members(league, team)
    for group in D.ROSTER_ORDER:
        free = T.FR_ROSTER_TARGET[group] - filled(league, team, group)
        starters = sorted((p.rating for p in men if p.pos == group), reverse=True)[:T.FR_GROUP_STARTERS[group]]
        if free <= 0 and group not in D.RESERVE_POSITIONS and len(starters) == T.FR_GROUP_STARTERS[group] and starters[-1] < T.FR_DRAFT_WEAK:
            free = 1                                       # a starter under FR_DRAFT_WEAK: one man of the family is wanted (the draft's own rule)
        if free > 0:
            out.append((group, free))
    if staff:
        room_left = real_roster.room(league, team)
        out.sort(key=lambda row: (filled(league, team, row[0]) >= T.FR_FAMILY_MIN[row[0]], D.ROSTER_ORDER.index(row[0])))
        trimmed = []
        for group, free in out:
            take = min(free, room_left)
            if take > 0:
                trimmed.append((group, take))
                room_left -= take
        out = sorted(trimmed, key=lambda row: D.ROSTER_ORDER.index(row[0]))
    return out


def room(league, team: int) -> int:
    """The most the team may pay a player it signs now: the cap less the contracts that run, the dead money, the reserve for the draft's rookies and the
    minimum for every other place still empty (each will be filled at least)."""
    return R.room(league, team) - T.FR_FA_RESERVE


def fit_level(league, team: int, player) -> int:
    """0 when the player would not be better than the weakest of the team's players at his position, 1 when he would, 2 when he would be the best (also
    when the group is empty)."""
    from . import real_roster
    ratings = sorted((p.rating for p in real_roster.members(league, team) if p.pos == player.pos), reverse=True)[:T.FR_GROUP_STARTERS[player.pos]]
    if not ratings or player.rating > max(ratings):
        return 2
    return 1 if player.rating > min(ratings) else 0


def score(league, team: int, player, salary: int) -> int:
    """The score of an offer: the salary in tenths of a million raised by the fit (percent), so equal money is told apart by the better fit."""
    return salary * (100 + T.FR_FA_FIT[fit_level(league, team, player)])


TIE_PRIME = 37                                   # a prime above the 32 teams: multiplying 1..32 by a number from 1 to 36 never repeats a value


def tie_key(team: int, player_id: int) -> int:
    """Equal scores are told apart by a fixed rule that favors no team: the free agent's ID picks a multiplier from 1 to 36 and the team number times it, modulo the prime 37,
    is the team's place in his queue (the lowest first). For one player no two teams share a key; for two neighbouring teams the order is reversed for about half the
    players, and every team is first for some. Nothing is drawn; the same offers always give the same signing."""
    return (team * (1 + player_id % (TIE_PRIME - 1))) % TIE_PRIME


def chase(round_no: int) -> int:
    """How many free agents a team chases for each open place in this round: `FR_FA_CHASE` in the first, one more in every later round (a team whose first choices went
    elsewhere looks further down the list instead of leaving the place to the draft)."""
    return T.FR_FA_CHASE + round_no - 1


@dataclass(frozen=True)
class Bid:
    team: int
    player: int                      # the free agent's ID
    salary: int
    years: int
    score: int


def make_bid(league, team: int, player, salary: int, years: int) -> Bid:
    return Bid(team, player.id, salary, years, score(league, team, player, salary))


def by_position(free: list) -> dict:
    out: dict = {}
    for player in free:
        out.setdefault(player.pos, []).append(player)
    return out


def team_bids(league, team: int, round_no: int, free_by_position: dict) -> list:
    """What the staff offers for a team in this round: for every position with open places the most valuable free agents rated `FR_FA_MIN_RATING` or more whose
    price the team can pay, `FR_FA_CHASE` of them for each open place (a second is chased in case the first goes elsewhere). Judged together with the other teams'
    offers by `resolve`; whatever is not needed any more by then lapses. No draw; nothing is changed."""
    bids: list = []
    space = room(league, team)
    for position, count in open_places(league, team):
        taken = 0
        for player in free_by_position.get(position, ()):
            if player.rating < T.FR_FA_MIN_RATING:
                continue
            salary, years = price(player, round_no)
            if salary > space:
                continue
            bids.append(make_bid(league, team, player, salary, years))
            taken += 1
            if taken >= count * chase(round_no):
                break
    return bids


def computer_bids(league, round_no: int, skip: tuple = ()) -> list:
    """The offers of every team that is not in `skip`, team 1 to 32 (the fast run skips nobody; the program skips the player's team unless the staff handles it)."""
    free = by_position(pool(league))
    bids: list = []
    for team in range(1, D.TEAMS + 1):
        if team not in skip:
            bids += team_bids(league, team, round_no, free)
    return bids


def interest(bids: list) -> dict:
    """How many offers each free agent has: player ID -> count."""
    out: dict = {}
    for bid in bids:
        out[bid.player] = out.get(bid.player, 0) + 1
    return out


# ----- the judgement of a round -----

@dataclass
class Decision:
    """One free agent's judgement: every offer in the order it was weighed (`ranked`), the ones passed over because the team could not sign him any more
    (`passed`), and the winner or None."""
    player: object
    ranked: list
    passed: list = field(default_factory=list)
    winner: Bid | None = None


@dataclass
class Round:
    number: int
    decisions: list = field(default_factory=list)
    signed: list = field(default_factory=list)       # [(player, bid)] in the order they were signed
    moves: list = field(default_factory=list)        # SX.8m: [player ID, the team he left, the team he joined, salary] of every signing (comp.py)


def can_sign(league, bid: Bid) -> bool:
    """The team has a spot on its 53 (SR.5) and the room under the cap for his salary."""
    from . import real_roster
    player = league.players[bid.player]
    return player.status == "free" and real_roster.room(league, bid.team) > 0 and bid.salary <= room(league, bid.team)


def sign(league, player, bid: Bid) -> None:
    """The free agent joins the team's chart (SR.5) on the contract of the offer."""
    from . import real_roster
    real_roster.join(league, bid.team, player, refresh=False)
    CT.sign(player, bid.salary, bid.years)


def resolve(league, bids: list, round_no: int) -> Round:
    """Judge the offers of a round together: the free agents in the order of their value, the best first; each signs with the offer of the highest score among
    those whose team can still sign him (equal scores: `tie_key`). Changes the league (the signed leave the market, the teams' places are filled and put in rating
    order) and returns the round."""
    by_player: dict = {}
    for bid in bids:
        by_player.setdefault(bid.player, []).append(bid)
    result = Round(round_no)
    touched: set = set()
    # SR.5: a computer team signs only for the needs it bid for (its families under their targets, at most its roster's room): an offer for a family whose
    # need is met by an earlier signing of the round lapses (the player's own offers are his choice, held only to his room and his cap)
    spots = {team: dict(open_places(league, team)) for team in {b.team for b in bids} if team != league.team}
    for pid in sorted(by_player, key=lambda pid: R.value(league.players[pid])):
        player = league.players[pid]
        ranked = sorted(by_player[pid], key=lambda b: (-b.score, tie_key(b.team, pid)))
        decision = Decision(player, ranked)
        for bid in ranked:
            if bid.team in spots and spots[bid.team].get(player.pos, 0) <= 0:
                decision.passed.append(bid)
                continue
            if can_sign(league, bid):
                if bid.team in spots:
                    spots[bid.team][player.pos] -= 1
                decision.winner = bid
                if player.team:                                                          # (a player the player released in the season has no team: nobody lost him)
                    result.moves.append([player.id, player.team, bid.team, bid.salary])     # (a free agent keeps the team he last played for until he signs)
                sign(league, player, bid)
                result.signed.append((player, bid))
                touched.add(bid.team)
                break
            decision.passed.append(bid)
        result.decisions.append(decision)
    from . import real_roster
    for team in sorted(touched):
        real_roster.refresh_view(league, team)
    return result


def run_round(league, round_no: int, extra: list = (), skip: tuple = ()) -> Round:
    """One round: the offers of the teams that are not in `skip` (the staff's), the `extra` offers (the player's), judged together."""
    return resolve(league, computer_bids(league, round_no, skip) + list(extra), round_no)


def run_market(league, skip: tuple = ()) -> list:
    """All the rounds of free agency with no offers but the staff's (the fast run, and the program when every team is a computer team)."""
    return [run_round(league, number, (), skip) for number in range(1, T.FR_FA_ROUNDS + 1)]


# ----- the stage in progress (league.market) -----

def begin() -> dict:
    """Stage 8 starts: round 1, nothing offered yet. The caller stores it in `league.market` and saves."""
    return {"round": 1, "offers": [], "signed": 0, "lost": 0, "staff": 0, "moves": []}


def check_market(league, whole) -> None:
    """LeagueError (through `whole`) unless `league.market` is None or, in stage 8, a whole record of the stage in progress."""
    from .league import OFFSEASON, LeagueError
    data = league.market
    if data is None:
        return
    if league.stage != OFFSEASON or league.stage_no != D.STAGE_FREE_AGENCY:
        raise LeagueError("a market in progress in stage %r %r" % (league.stage, league.stage_no))
    if not isinstance(data, dict) or set(data) != set(KEYS):
        raise LeagueError("the market holds %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    whole(data["round"], 1, T.FR_FA_ROUNDS, "the round of the market")
    whole(data["signed"], 0, D.PLACE_COUNT * 2, "the players signed in the market")
    whole(data["lost"], 0, T.FR_FA_ROUNDS * T.FR_FA_OFFERS, "the offers lost in the market")
    whole(data["staff"], 0, 1, "the staff's offers")
    offers = data["offers"]
    if not isinstance(offers, list) or len(offers) > T.FR_FA_OFFERS:
        raise LeagueError("the offers are %r" % (offers if not isinstance(offers, list) else len(offers),))
    seen: set = set()
    for row in offers:
        if not isinstance(row, list) or len(row) != 2:
            raise LeagueError("an offer is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "an offer's player")
        whole(row[1], T.FR_MIN_SALARY, T.FR_MAX_SALARY, "an offer's salary")
        player = league.players.get(row[0])
        if row[0] in seen or player is None or player.status != "free" or player.left != league.season:
            raise LeagueError("player %r is offered a contract but is not a free agent of this offseason" % (row[0],))
        seen.add(row[0])
    moves = data["moves"]                                      # SX.8m: the signings of the rounds judged so far
    if not isinstance(moves, list) or len(moves) > D.TEAMS * D.PLACE_COUNT:
        raise LeagueError("the market's moves are %r" % (type(moves).__name__ if not isinstance(moves, list) else len(moves),))
    for row in moves:
        if not isinstance(row, list) or len(row) != 4:
            raise LeagueError("a move of the market is %r" % (row,))
        whole(row[0], 1, 10 ** 9, "a moved player")
        whole(row[1], 1, D.TEAMS, "the team a free agent left")
        whole(row[2], 1, D.TEAMS, "the team a free agent joined")
        whole(row[3], T.FR_MIN_SALARY, T.FR_MAX_SALARY, "the salary of a move")
