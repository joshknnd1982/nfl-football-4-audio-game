"""Re-signing, the talks and the franchise tag of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8h (F6, N6.6, research B3 and F2, D-067). Plain rules over the league record, no speech, no files and no draw, so
stage 7 of the offseason (`resign_flow.py`) and the calibration's fast run use the very same code.

A contract that ran out in stage 2 (`contracts.turn_the_year`) leaves its player with 0 years left and his last salary. Stage 7 settles each:

    plan_team / run_teams      the staff's and the computer teams' rule: players in order of value are signed again at the market price for
                               the length of their age while they are worth it (`worth_keeping`) and the cap has room (`room`); the others go
    Talk                       the player's short talk with one of his own players: his price, his floor (what his mood lets him accept) and
                               at most `FR_TALK_ROUNDS` rounds; "offer less" is accepted, answered with a counter, or ends the talk
    tag_salary                 the franchise tag, one a year, exclusive style: one year at the average of the highest salaries at his position
    sign_again / let_go        the two outcomes (a player who is let go is a free agent: status "free", no contract, no place)
    check_resign               the whole-file check of `LeagueRecord.resign`, the stage in progress

Free agency itself (SX.8i) takes the players with the status "free" of this offseason; until then stage 6 drops them like the released.
All numbers are data in `extras\\tuning.py` (the `FR_` names) and `data.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .. import tuning as T
from . import contracts as CT
from . import data as D

HAPPY, CONTENT, UNHAPPY = "happy", "content", "unhappy"
MOODS = (HAPPY, CONTENT, UNHAPPY)
MOOD_TEXT = {HAPPY: "NXW-20", CONTENT: "NXW-21", UNHAPPY: "NXW-22"}
KEYS = ("pending", "tag_used", "signed", "let_go", "league_gone", "stars")


# ----- who, in what order -----

def expiring(league, team: int) -> list:
    """The team's active players whose contract ran out, the most valuable first (`value`); D-149: the men of its bench too."""
    out = [league.players[pid] for pid in league.rosters[team - 1] if pid and league.players[pid].years == 0]
    out += [p for p in league.bench(team) if p.years == 0]
    return sorted(out, key=value)


def value(player) -> tuple:
    """The order of the talks and of the staff's signings: the part of the team's strength a player gives over his replacement (the position's
    weight times his rating over the rating of the rookie of the fill who would take his place), the best first; then the rating, then the lower ID."""
    return (-D.WEIGHT[player.pos] * (player.rating - CT.replacement_rating(player.pos)), -player.rating, player.id)


def worth_keeping(player) -> bool:
    """The staff and the computer's teams sign a player again only when he is rated `FR_RESIGN_MIN_RATING` or more (the draft class's mean true rating: a weaker
    veteran is replaced by a rookie at the cut, and his release would cost dead money)."""
    return player.rating >= T.FR_RESIGN_MIN_RATING


def asking(player) -> tuple:
    """(salary, years) a player asks: the market price of his position and rating for the length of his age; a player with fewer than
    `FR_EXCLUSIVE_SEASONS` seasons in the league has only the exclusive rights of his team (research B3: the NFL's rule that replaces the
    restricted free agent's tenders): the minimum salary of his seasons (research B4's table) for one year."""
    if player.seasons < T.FR_EXCLUSIVE_SEASONS:
        return CT.min_salary(player.seasons), 1
    salary, years = CT.market_contract(player)
    return max(CT.min_salary(player.seasons), salary), years          # (a veteran of 7 seasons rated 51 is worth 1.1 million and may not be paid under his minimum, 1.3)


# ----- the cap -----

def running_payroll(league, team: int) -> int:
    return sum(player.salary for player in CT.team_players(league, team, {}) if CT.running(player))


def running_count(league, team: int) -> int:
    return sum(1 for player in CT.team_players(league, team, {}) if CT.running(player))


def room_after(payroll: int, count: int, dead: int, cap: int | None = None, slots: int | None = None) -> int:
    """The most a player who is signed now may be paid: what is left of the cap after the contracts that run (`payroll`, `count` of them), the
    dead money, the reserve for the rookies, and the minimum for every other place still without a contract (each will be filled at least).
    D-149: a league that carries benches gives its cap and its 53 slots (`league_terms`); else FR_CAP and the 34 places."""
    cap = T.FR_CAP if cap is None else cap
    slots = D.PLACE_COUNT if slots is None else slots
    return cap - T.FR_RESIGN_RESERVE - dead - payroll - T.FR_MIN_SALARY * (slots - count - 1)


def league_terms(league) -> tuple:
    """The extra arguments of `room_after` for a league that carries benches (its cap, 53 slots); () for one that does not, so the calls stay the old ones."""
    from . import reserves
    return (CT.cap_of(league), reserves.slots(league)) if reserves.on(league) else ()


def room(league, team: int) -> int:
    return room_after(running_payroll(league, team), running_count(league, team), league.dead[team - 1], *league_terms(league))


def target_payroll(*league) -> int:
    """The most the staff lets the contracts of the coming season (the ones that run, the new ones and the dead money) come to when it signs players again:
    `FR_RESIGN_TARGET` of the cap. The rest of the cap is for the market, the draft and the cut. The player's own talks are held only to the cap (`room`).
    D-149: given a league that carries benches, of that league's cap."""
    cap = CT.cap_of(league[0]) if league and league_terms(league[0]) else T.FR_CAP
    return int(T.FR_RESIGN_TARGET * cap)


# ----- the staff's and the computer teams' rule -----

@dataclass
class Plan:
    team: int
    signed: list = field(default_factory=list)       # [(player, salary, years)] in the order of value
    gone: list = field(default_factory=list)         # players let go


def plan_team(league, team: int) -> Plan:
    """What the staff does for a team (the computer teams' rule and the player's when the staff handles it): the players in order of value, each
    signed again at his price when he is worth it and the cap has room, else let go. No draw; nothing is changed."""
    plan = Plan(team)
    payroll, count, dead = running_payroll(league, team), running_count(league, team), league.dead[team - 1]
    terms = league_terms(league)
    target = target_payroll(league) if terms else target_payroll()
    for player in expiring(league, team):
        salary, years = asking(player)
        if worth_keeping(player) and salary <= room_after(payroll, count, dead, *terms) and payroll + dead + salary <= target:
            plan.signed.append((player, salary, years))
            payroll += salary
            count += 1
        else:
            plan.gone.append(player)
    return plan


def sign_again(league, player, salary: int, years: int) -> None:
    CT.sign(player, salary, years)


def let_go(league, player) -> None:
    """The player's contract is over and nobody signs him: he leaves his place and is a free agent of this offseason (status "free", the team
    he last played for kept, the season he left). Dead money is not charged: a contract that ran out costs nothing."""
    if player.place >= 0:                                  # (a bench man has no place, D-149)
        league.rosters[player.team - 1][player.place] = 0
    player.status, player.left, player.place, player.points = "free", league.season, -1, 0
    CT.leave(player)


def apply_plan(league, plan: Plan) -> None:
    for player, salary, years in plan.signed:
        sign_again(league, player, salary, years)
    for player in plan.gone:
        let_go(league, player)


@dataclass
class Outcome:
    signed: int = 0
    signed_by: dict = field(default_factory=dict)    # team -> how many it signed again
    gone: list = field(default_factory=list)         # the players let go, in team order and the order of value

    def stars(self) -> list:
        """The players let go who are named in the speech: rating `FREE_STAR_RATING` or more, the best first, equals in the order they were let go."""
        named = sorted((p for p in self.gone if p.rating >= D.FREE_STAR_RATING), key=lambda p: -p.rating)
        return named[:D.STARS_NAMED]


def run_teams(league, skip: tuple = ()) -> Outcome:
    """Every team that is not in `skip`, team 1 to 32: plan, then apply. The fast run (every team a computer team) and the program (all but the
    player's, or all of them when the staff handles his) both call this."""
    from . import tags
    tags.record_history(league)                      # SX.8m: the positions' highest salaries before anybody is signed again (the non-exclusive tag's price)
    out = Outcome()
    for team in range(1, D.TEAMS + 1):
        if team in skip:
            continue
        plan = plan_team(league, team)
        apply_plan(league, plan)
        out.signed += len(plan.signed)
        out.signed_by[team] = len(plan.signed)
        out.gone += plan.gone
    return out


# ----- the talk with one of the player's own players -----

def mood(league, team: int) -> str:
    """How the team's players feel after the season that just ended (the history's last entry): happy after `FR_MOOD_WINS`[0] wins or when the
    team reached the division round (it won a wild card game or had a bye), unhappy after `FR_MOOD_WINS`[1] wins or fewer, else content; content when there is no history."""
    if not league.history:
        return CONTENT
    entry = league.history[-1]
    happy_wins, unhappy_wins = T.FR_MOOD_WINS
    wins, finish = entry["wins"][team - 1], entry["finish"][team - 1]
    if wins >= happy_wins or finish >= D.FINISH_DIVISION:
        return HAPPY
    if wins <= unhappy_wins:
        return UNHAPPY
    return CONTENT


def floor_salary(salary: int, how: str, least: int = T.FR_MIN_SALARY, extra: int = 0) -> int:
    """The least a player in this mood accepts for his price: T.FR_MOOD_SLACK[how] percent under it, rounded half up like `lower_offer` (so a
    happy player, whose slack is the step of an offer for less, always accepts the first offer), never under `least` (his minimum salary). SX.8n: `extra`, his
    personality's percent (`people.slack_change`), is added to the slack, which is never under 0."""
    slack = max(0, T.FR_MOOD_SLACK[how] + extra)
    return max(least, (salary * (100 - slack) + 50) // 100)


def lower_offer(salary: int, least: int = T.FR_MIN_SALARY) -> int:
    """What "offer less" offers: `FR_OFFER_LESS` percent under his present price, rounded half up, never under `least` (his minimum salary)."""
    return max(least, (salary * (100 - T.FR_OFFER_LESS) + 50) // 100)


ACCEPTED, COUNTER, ENDED = "accepted", "counter", "ended"


@dataclass
class Talk:
    """One talk: `ask` the price now (it only comes down), `years` the length (the length of his age, never changed: a choice of the talk never
    forces a longer contract, research G), `floor` what his mood lets him accept, `least` his minimum salary (nothing is offered under it),
    `round` 1 to `FR_TALK_ROUNDS`."""
    ask: int
    years: int
    floor: int
    round: int = 1
    least: int = T.FR_MIN_SALARY

    @classmethod
    def start(cls, player, how: str, extra: int = 0) -> "Talk":
        salary, years = asking(player)
        least = CT.min_salary(player.seasons)
        return cls(salary, years, floor_salary(salary, how, least, extra), 1, least)

    def offer_less(self) -> tuple:
        """(ACCEPTED, salary): the offer is at or over his floor and he signs at the offer; (COUNTER, salary): he comes down halfway to his floor
        (rounded up) and the next round begins; (ENDED, 0): it was the last round and he leaves."""
        offer = lower_offer(self.ask, self.least)
        if offer >= self.floor:
            return ACCEPTED, offer
        if self.round >= T.FR_TALK_ROUNDS:
            return ENDED, 0
        self.ask = max(self.floor, (self.ask + self.floor + 1) // 2)
        self.round += 1
        return COUNTER, self.ask


# ----- the franchise tag -----

def tag_salary(league, player) -> int:
    """One year at the average of the `FR_TAG_TOP` highest salaries at his position among the contracts that run, or `FR_TAG_RAISE` percent of
    his last salary, or his market price, whichever is most, never over the maximum (research B3: exclusive style); SX.8m: never under the price of the
    non-exclusive tag (the NFL's exclusive tag pays the higher of the five largest salaries and the non-exclusive amount)."""
    top = sorted((p.salary for p in league.players.values() if p.status == "active" and p.pos == player.pos and CT.running(p)),
                 reverse=True)[:T.FR_TAG_TOP]
    average = (sum(top) + len(top) // 2) // len(top) if top else 0
    raised = (player.salary * T.FR_TAG_RAISE + 50) // 100
    from . import tags
    return min(T.FR_MAX_SALARY, max(average, raised, CT.market_salary(player.pos, player.rating), tags.nonexclusive_salary(league, player)))


# ----- the stage in progress (league.resign) -----

def begin(league, own_team_by_staff: bool) -> dict:
    """Stage 7 starts: the computer's teams (and the player's when the staff handles it) are settled at once; the player's own expiring players
    wait to be asked, the most valuable first. Returns the record of the stage (the caller stores it in `league.resign` and saves)."""
    skip = () if own_team_by_staff else (league.team,)
    out = run_teams(league, skip)
    others = [p for p in out.gone if p.team != league.team]
    named = Outcome(gone=others).stars()
    return {"pending": [p.id for p in expiring(league, league.team)], "tag_used": 0,
            "signed": out.signed_by.get(league.team, 0), "let_go": len([p for p in out.gone if p.team == league.team]),
            "league_gone": len(others), "stars": [p.id for p in named]}


def check_resign(league, whole) -> None:
    """LeagueError (through `whole`) unless `league.resign` is None or, in stage 7, a whole record of the stage in progress."""
    from .league import OFFSEASON, LeagueError
    data = league.resign
    if data is None:
        return
    if league.stage != OFFSEASON or league.stage_no != D.STAGE_CONTRACTS:
        raise LeagueError("a stage of expiring contracts in progress in stage %r %r" % (league.stage, league.stage_no))
    if not isinstance(data, dict) or set(data) != set(KEYS):
        raise LeagueError("the stage of the expiring contracts holds %r" % (sorted(data) if isinstance(data, dict) else type(data).__name__,))
    pending = data["pending"]
    if not isinstance(pending, list) or len(pending) > D.PLACE_COUNT:
        raise LeagueError("the players still to be asked are %r" % (pending if not isinstance(pending, list) else len(pending),))
    seen: set = set()
    for pid in pending:
        whole(pid, 1, 10 ** 9, "a player still to be asked")
        player = league.players.get(pid)
        if (pid in seen or player is None or player.status != "active" or player.team != league.team or player.place < 0
                or player.years != 0):
            raise LeagueError("player %r is not one of the player's own whose contract has run out" % (pid,))
        seen.add(pid)
    whole(data["tag_used"], 0, 1, "the franchise tag used")
    for key in ("signed", "let_go"):
        whole(data[key], 0, D.PLACE_COUNT * 2, "the players " + key)
    whole(data["league_gone"], 0, D.TEAMS * D.PLACE_COUNT, "the players of the league let go")
    stars = data["stars"]
    if not isinstance(stars, list) or len(stars) > D.STARS_NAMED:
        raise LeagueError("the stars let go are %r" % (stars if not isinstance(stars, list) else len(stars),))
    for pid in stars:
        whole(pid, 1, 10 ** 9, "a star let go")
        player = league.players.get(pid)
        if player is None or player.status != "free":
            raise LeagueError("player %r is named as a star let go but is not a free agent" % (pid,))
