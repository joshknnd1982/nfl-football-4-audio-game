"""Contracts and the salary cap of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8g (F6, N6.6, research B3 and F2, D-066). Plain rules over the league record, no speech, no files and no draw, so
the offseason's stages and the calibration's fast run use the very same code.

A contract is two numbers on a `Player`: `salary` (tenths of a million dollars, the unit of the cap too) and `years` (the seasons left,
the coming one included). An active player has a contract of the minimum salary or more and 1 to `years_for_age` years (0 years between stages 2 and 7 of an offseason: it ran out and `resign.py` settles it); a retired or
released player has none (0, 0). Nothing is drawn: a salary is the market price of the position and the rating, a rookie's is fixed by his
pick, and the length is a rule of the age, so a league made twice from the same seed has the same contracts.

    market_salary / rookie_salary / years_for_age   the three price rules (all numbers are `extras\\tuning.py`, the `FR_` names)
    payroll / cap_used / cap_space                  a team's salaries (placed players and the rookies waiting for the cut), plus its dead money
    turn_the_year                                   stage 2: the cap year turns (dead money gone), every contract has a year less; a contract that
                                                    ran out stays with 0 years until SX.8h's expiring-contracts stage (`resign.py`) signs it again
                                                    or lets the player go
    release                                         a released player costs dead money against the season that follows (`FR_DEAD_SHARE`)
    cap_over / cap_releases                         the cap rule of the roster cut: a team that would be over the cap after the cut and the fill
                                                    releases more players, the ones that cost most for what they give, until it is under
    migrate / fit_to_cap                            a format-1 league gets its contracts (a migration with no draw); a team never leaves over the cap
    check_contracts                                 the whole-file check of the contracts (league.py calls it)
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D


def millions(units: int) -> str:
    """The number said before the word million: 124 is "12.4", 120 is "12", 9 is "0.9"; below zero the same with a minus sign (the sign
    and the size are worked out apart: divmod alone would make -67 "-7.3")."""
    if units < 0:
        return "-" + millions(-units)
    whole, tenth = divmod(units, D.SALARY_PER_MILLION)
    return "%d" % whole if tenth == 0 else "%d.%d" % (whole, tenth)


# ----- the three price rules -----

def market_salary(position: str, rating: int) -> int:
    """What a free player of this position and rating is paid: the minimum + (rating - 40) squared x the position's pay / the divisor,
    at most the maximum."""
    extra = (rating - D.RATING_MIN) ** 2 * T.FR_PAY[position] // T.FR_PAY_DIVISOR
    return min(T.FR_MAX_SALARY, T.FR_MIN_SALARY + extra)


def rookie_salary(overall: int) -> int:
    """What the pick number `overall` (1 to 224) is paid: straight lines between the points of `FR_ROOKIE_SCALE` (the first pick the most,
    the last the least), rounded half up; no position, as the NFL's wage scale."""
    overall = max(1, min(D.DRAFT_PICKS, overall))
    points = T.FR_ROOKIE_SCALE
    for (pick_a, pay_a), (pick_b, pay_b) in zip(points, points[1:]):
        if overall <= pick_b:
            span = pick_b - pick_a
            return pay_a + (2 * (pay_b - pay_a) * (overall - pick_a) + span) // (2 * span)        # round half up, in either direction
    return points[-1][1]


def min_salary(seasons: int) -> int:
    """The least a player with this many seasons in the league is paid (research B4's table, `FR_MIN_SALARY_BY_SEASONS`): the exclusive-rights price of
    stage 7 and the floor of a free agent's falling price. Never under `FR_MIN_SALARY`, the figure the cap's reserve for an empty place uses."""
    for last_seasons, salary in T.FR_MIN_SALARY_BY_SEASONS:
        if seasons <= last_seasons:
            return salary
    return T.FR_MIN_SALARY_BY_SEASONS[-1][1]


def years_for_age(age: int) -> int:
    """The length of a new contract of a player of this age, and the most years any contract of him may have left."""
    for last_age, years in T.FR_CONTRACT_YEARS:
        if age <= last_age:
            return years
    return T.FR_CONTRACT_YEARS[-1][1]


def dead_money(player) -> int:
    """What releasing the player costs: `FR_DEAD_SHARE` percent of his salary for each year he has left, rounded half up."""
    return (player.salary * player.years * T.FR_DEAD_SHARE + 50) // 100


def released_free(player) -> bool:
    """SX.8m: an undrafted rookie released at his first cut (still waiting for a place, never drafted) costs no dead money."""
    return player.place < 0 and player.drafted is None and player.status == "active"


def release_cost(player) -> int:
    """The dead money releasing him would charge now: `dead_money`, or nothing for an undrafted rookie at his first cut (`released_free`)."""
    return 0 if released_free(player) else dead_money(player)


def sign(player, salary: int, years: int) -> None:
    player.salary, player.years = salary, years


def market_contract(player) -> tuple:
    """(salary, years) of a new contract at the market price: the position and the rating, the length of his age."""
    return market_salary(player.pos, player.rating), years_for_age(player.age)


def initial_contract(player) -> tuple:
    """The contract a player of a league that is just made (or migrated) has: the market price and a length that only the player's ID
    varies (1 to the length of his age), so the contracts of a team do not all run out in the same year and nothing is drawn."""
    salary, years = market_contract(player)
    return salary, 1 + player.id % years


def pick_number(round_no: int, in_round: int) -> int:
    """The pick's place among the draft's regular picks (1 to 224), the number the rookie scale reads: a compensatory pick (33 and on of its round, SX.8m)
    is paid as the last pick of its round (it sits at the round's end)."""
    return (round_no - 1) * D.TEAMS + min(in_round, D.TEAMS)


def draft_overall(player) -> int:
    """The scale's pick number of a drafted player: [season, round, pick in the round]."""
    _season, round_no, in_round = player.drafted
    return pick_number(round_no, in_round)


# ----- a team's money -----

def team_players(league, team: int, waiting: dict | None = None) -> list:
    """The team's players that are paid: the 34 places and the rookies waiting for the cut (`waiting` is draft.waiting_by_team's table; when
    it is None the draft record's own picks are used)."""
    placed = [league.players[pid] for pid in league.rosters[team - 1] if pid]
    placed += [p for p in league.players.values() if p.status == "practice" and p.team == team]     # D-136: the practice squad is paid too
    if waiting is None:
        return placed + league.waiting_rookies(team)          # (the drafted rookies and, SX.8m, the undrafted free agents in camp)
    return placed + list(waiting.get(team, ()))


def running(player) -> bool:
    """A contract that counts against the cap: the player has years left. A contract that has run out (0 years, between stages 2 and 7 of
    an offseason) keeps its last salary on the player, for the franchise tag's raise, but costs nothing."""
    return player.years > 0


def payroll(league, team: int, waiting: dict | None = None) -> int:
    return sum(player.salary for player in team_players(league, team, waiting) if running(player))


def payrolls(league) -> list:
    """The 32 payrolls (team 1 first) of every active player, placed or waiting."""
    totals = [0] * D.TEAMS
    for player in league.players.values():
        if player.status in ("active", "practice") and running(player):          # D-136: the practice squads are paid too
            totals[player.team - 1] += player.salary
    return totals


def cap_used(league, team: int, waiting: dict | None = None) -> int:
    """The payroll and the dead money of the cap year."""
    return payroll(league, team, waiting) + league.dead[team - 1]


def cap_space(league, team: int, waiting: dict | None = None) -> int:
    return T.FR_CAP - cap_used(league, team, waiting)


def cap_ranking(league) -> list:
    """The teams 1 to 32 with the most cap space first, equal space to the lower team number."""
    totals = payrolls(league)
    space = [T.FR_CAP - totals[t] - league.dead[t] for t in range(D.TEAMS)]
    return sorted(range(1, D.TEAMS + 1), key=lambda team: (-space[team - 1], team))


# ----- the year turns (stage 2) -----

def turn_the_year(league) -> int:
    """Stage 2, after everybody is a year older and the retired have left: the cap year turns (the dead money of the season that is over is
    gone) and every contract has a year less. A contract that ran out is left with 0 years (and its last salary): stage 7, the expiring
    contracts (`resign.py`, SX.8h), signs the player again or lets him go. Returns how many contracts ran out."""
    league.dead = [0] * D.TEAMS
    expired = 0
    for player in league.players.values():
        if player.status != "active":
            continue
        player.years -= 1
        if player.years <= 0:
            player.years = 0
            expired += 1
    return expired


def leave(player) -> None:
    """A retired player's contract is over (no dead money)."""
    player.salary = player.years = 0


def release(league, player) -> int:
    """A released player: his dead money is charged to the team's cap year and his contract is over. Returns the dead money."""
    dead = dead_money(player)
    league.dead[player.team - 1] += dead
    player.salary = player.years = 0
    return dead


# ----- the cap rule of the roster cut (stage 5) -----

def replacement_rating(position: str) -> int:
    """The middle rating of an undrafted rookie of the fill in this group (design 7.6), what a released player's place is filled with."""
    base, span = T.FR_FILL_RATING if D.GROUP_SIZE[position] >= 3 else T.FR_FILL_RATING_SMALL
    return base + span // 2


def cap_after_cut(league, team: int, waiting: dict, released: list) -> int:
    """The cap the team will use once the players in `released` are gone and the empty places are filled with undrafted rookies (each
    paid the minimum, so the figure is exact): the salaries of the rest, the fill, the dead money held and the dead money of the release."""
    gone = {player.id for player in released}
    kept = [player for player in team_players(league, team, waiting) if player.id not in gone]
    held = {position: 0 for position in D.POSITIONS}
    for player in kept:
        held[player.pos] += 1
    empty = sum(max(0, D.GROUP_SIZE[position] - count) for position, count in held.items())
    return (sum(player.salary for player in kept) + empty * T.FR_MIN_SALARY + league.dead[team - 1]
            + sum(release_cost(player) for player in released))


def cap_over(league, team: int, waiting: dict, released: list) -> int:
    """How far over the cap the team would be after the cut and the fill (0 or less: it is under)."""
    return cap_after_cut(league, team, waiting, released) - T.FR_CAP


def release_value(player) -> tuple:
    """The order in which the staff lets players go to get under the cap: first those who are no better than the player who would replace
    them (the one who saves most first), then the least rating over his replacement, weighted by the position's part of the strength, for each
    tenth of a million the release saves; the dearer one first, then the lower ID. A release that saves nothing (the minimum salary, or dead
    money as large as the salary) is no candidate."""
    saved = player.salary - T.FR_MIN_SALARY - dead_money(player)
    loss = D.WEIGHT[player.pos] * (player.rating - replacement_rating(player.pos))
    if loss <= 0:
        return (0, -saved, -player.salary, player.id)
    return (1, loss * 1000 // saved, -player.salary, player.id)


def cap_candidates(league, team: int, waiting: dict, released: list) -> list:
    """The players who may be released to save money, the staff's order first."""
    gone = {player.id for player in released}
    out = [player for player in team_players(league, team, waiting)
           if player.id not in gone and player.salary - T.FR_MIN_SALARY - dead_money(player) > 0]
    return sorted(out, key=release_value)


def cap_releases(league, team: int, waiting: dict, released: list) -> list:
    """The players the staff releases besides `released` (the cut's own list) to get the team under the cap: the first of the staff's order,
    again and again, until the cap after the cut and the fill is met. Empty when it already is."""
    extra: list = []
    while cap_over(league, team, waiting, released + extra) > 0:
        candidates = cap_candidates(league, team, waiting, released + extra)
        if not candidates:
            break                                       # nobody saves anything: the team stays over the cap; stage 5 tells the player (NXA-16)
        extra.append(candidates[0])
    return extra


# ----- a league that has no contracts yet (a new league, a format-1 file) -----

def fit_to_cap(league) -> int:
    """No team starts over the cap: a team whose cap use is over it gets every salary above the minimum lowered by the same share (rounded
    down, so the sum fits). Returns how many teams were changed."""
    changed = 0
    for team in range(1, D.TEAMS + 1):
        over = cap_used(league, team) - T.FR_CAP
        if over <= 0:
            continue
        players = [player for player in team_players(league, team)           # a rookie's pay is fixed by his pick: it is not lowered
                   if player.salary > T.FR_MIN_SALARY and not (player.drafted is not None and player.seasons < T.FR_ROOKIE_YEARS)]
        adjustable = sum(player.salary - T.FR_MIN_SALARY for player in players)
        if adjustable <= over:
            continue                                    # impossible with this scale; the whole-file check does not look at the cap
        keep = adjustable - over
        for player in players:
            player.salary = T.FR_MIN_SALARY + (player.salary - T.FR_MIN_SALARY) * keep // adjustable
        changed += 1
    return changed


def give_initial_contracts(league) -> None:
    """A new league: every player the market price and a length from his ID (see `initial_contract`)."""
    for player in league.players.values():
        if player.status == "active":
            sign(player, *initial_contract(player))
    league.dead = [0] * D.TEAMS
    fit_to_cap(league)


def migrate(league) -> None:
    """A format-1 league (SX.8a to SX.8f) gets its contracts, with no draw and the same answer for the same file: a player drafted in the
    last `FR_ROOKIE_YEARS` seasons has his rookie contract (the scale of his pick, the years he has left of the four); every other active
    player the market price and a length from his ID; the retired and the released none; no dead money. No team is left over the cap (outside
    stages 4 and 5, where the roster cut's own cap rule does that)."""
    for player in league.players.values():
        if player.status != "active":
            player.salary = player.years = 0
        elif player.drafted is not None and player.seasons < T.FR_ROOKIE_YEARS:
            sign(player, rookie_salary(draft_overall(player)), max(1, T.FR_ROOKIE_YEARS - player.seasons))
        else:
            sign(player, *initial_contract(player))
    league.dead = [0] * D.TEAMS
    if league.draft is None:                                # in stages 4 and 5 the waiting rookies are counted: the cut's own cap rule settles it
        fit_to_cap(league)


# ----- the whole-file check (league.py) -----

def _years_may_be_zero(league):
    """Who may hold a contract of 0 years, for the whole-file check: nobody outside the stages that hold them. After stage 2 (the record says
    stage 3) and at the start of stage 7 (before the stage has settled the computer's teams) anybody; during stage 7 the player's own players
    still to be asked (`resign["pending"]`). Returns None for anybody, else the set of the IDs allowed (empty: nobody)."""
    from .league import OFFSEASON
    if league.stage != OFFSEASON:
        return set()
    if league.stage_no == D.STAGE_DEVELOPMENT or (league.stage_no == D.STAGE_CONTRACTS and league.resign is None):
        return None
    if league.stage_no == D.STAGE_CONTRACTS and isinstance(league.resign, dict) and isinstance(league.resign.get("pending"), list):
        return {pid for pid in league.resign["pending"] if isinstance(pid, int)}
    return set()


def check_contracts(league, whole) -> None:
    """LeagueError (through `whole`) unless every contract is in range: an active player has the minimum salary or more and 1 to the longest
    contract of the scale years, a retired or released player a value in range (the simulation's CP2 asks for none: the file is lenient
    because a record is damage when a value is out of range, not when a rule is broken). The cap, the length by age and the rookie scale are
    rules of the simulation, not of the file (a file that breaks them is still a file; the 20-season check reports them, CP1 to CP5)."""
    from .league import LeagueError
    longest = max(years for _age, years in T.FR_CONTRACT_YEARS)
    pending = _years_may_be_zero(league)
    for player in league.players.values():
        if player.status == "active":
            whole(player.salary, T.FR_MIN_SALARY, T.FR_MAX_SALARY, "the salary of player %d" % player.id)
            whole(player.years, 0 if pending is None or player.id in pending else 1, longest, "the contract years of player %d" % player.id)
        else:
            whole(player.salary, 0, T.FR_MAX_SALARY, "the salary of player %d" % player.id)
            whole(player.years, 0, longest, "the contract years of player %d" % player.id)
    dead = league.dead
    if not isinstance(dead, list) or len(dead) != D.TEAMS:
        raise LeagueError("the dead money is %r" % (type(dead).__name__ if not isinstance(dead, list) else len(dead),))
    for value in dead:
        whole(value, 0, D.MAX_DEAD, "the dead money")
