"""The undrafted free agents of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8m (research B4's LATER, B12, F2; D-073). Plain rules, no speech, no files and no draw, so stage 4 of the offseason
(`draft_flow.stage_draft`) and the calibration's fast run use the very same code.

Right after the last pick (the NFL's undrafted rookies sign in the hours after the draft and compete in camp), the prospects of the class nobody drafted are a
market: a team offers a place in camp to the prospects it would want (an open place of his group, or the middle of his range over the weakest player who
would hold a place: the draft's own need rule, `Draft.needs`), at most `FR_UDFA_CHASE` of them; the prospects best first each sign with the team that
values him most by the draft's own value (`Draft.value`), equal values by the market's tie rule, while the team has signed fewer than `FR_UDFA_MAX`. A signed
undrafted rookie waits for the cut like a drafted one (active, no place, in the draft record's "undrafted"), on the minimum salary of a rookie for
`FR_FILL_YEARS` (the NFL's three years for an undrafted rookie); the cut keeps him when he is among the best of his group, and his release before the
season costs no dead money (`draft.apply_cut`). The fill (design 7.6) then fills what is still empty.

    team_offers(draft, team)         a team's offers (one function for the computer teams, the staff and the fast run)
    resolve(draft, offers)           the judgement: changes the league and the draft record
    run(draft, extra, skip)          every team's offers but the ones in `skip`, and the `extra` ones (the player's), judged together
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .. import tuning as T
from . import contracts as CT
from . import data as D


@dataclass(frozen=True)
class Offer:
    team: int
    prospect: int                    # the prospect's index in the class


@dataclass
class Result:
    signed: list = field(default_factory=list)      # [(prospect, team, player)] in the order they signed
    offered: dict = field(default_factory=dict)     # prospect index -> the teams that offered, in the order they were weighed


def pool(draft) -> list:
    """The prospects still available (nobody drafted or signed them), the best first by the draft board's base, then the lower number."""
    return sorted(draft.board.available(), key=lambda p: (-draft.board.base[p.index], p.index))


def wanted(draft, team: int, prospect, needs: dict | None = None) -> bool:
    """The team would want him in camp: his group has an open place, or the middle of his range is over the rating of the weakest player who would hold a
    place (the draft's need rule; the team knows him by his range)."""
    is_open, lowest = (needs or draft.needs(team))[prospect.pos]
    return is_open or (lowest is not None and prospect.middle > lowest)


def signed_by(draft, team: int) -> int:
    return sum(1 for row in draft.data["undrafted"] if row[0] == team)


def team_offers(draft, team: int, prospects: list | None = None) -> list:
    """The team's offers: the prospects it wants, the most valuable to it first (the draft's value), at most `FR_UDFA_CHASE`; none when it has signed
    `FR_UDFA_MAX` already."""
    if signed_by(draft, team) >= T.FR_UDFA_MAX:
        return []
    needs = draft.needs(team)
    chosen = [p for p in (prospects if prospects is not None else pool(draft)) if wanted(draft, team, p, needs)]
    chosen.sort(key=lambda p: (-draft.value(p, needs), p.index))
    return [Offer(team, p.index) for p in chosen[:T.FR_UDFA_CHASE]]


def sign(draft, team: int, prospect):
    """The prospect joins the team's camp: a player of the league with his true rating, undrafted, waiting for the cut, on the minimum salary of a rookie for
    `FR_FILL_YEARS`."""
    from .league import Player
    league = draft.league
    from .draft import free_number
    player = Player(league.next_id, prospect.name, prospect.pos, prospect.true, prospect.potential, prospect.age, 0, prospect.true, None, 0, "active", 0,
                    team, -1, CT.min_salary(0), T.FR_FILL_YEARS, position=prospect.position, number=free_number(league, team, prospect.position))
    league.next_id += 1
    league.players[player.id] = player
    draft.data["undrafted"].append([team, prospect.index, player.id])
    draft.board.remove(prospect)
    draft.rookies.setdefault(team, []).append(player)
    draft.middle_of[player.id] = prospect.middle
    return player


def resolve(draft, offers: list, own: tuple = ()) -> Result:
    """Judge every offer together: the prospects best first; each signs with the team that values him most (the draft's value with the team's needs as
    they are then), equal values by `market.tie_key`, among the offering teams that still want him and have signed fewer than `FR_UDFA_MAX`. A team in
    `own` (the player's, when he chose himself) is not held to the computer's need rule: his choice is his want (the review of SX.8m)."""
    from .market import tie_key
    by_prospect: dict = {}
    for offer in offers:
        by_prospect.setdefault(offer.prospect, []).append(offer.team)
    result = Result()
    for prospect in pool(draft):
        teams = list(dict.fromkeys(by_prospect.get(prospect.index, ())))
        if not teams:
            continue
        open_teams = []
        for team in teams:
            needs = draft.needs(team)
            if signed_by(draft, team) < T.FR_UDFA_MAX and (team in own or wanted(draft, team, prospect, needs)):
                open_teams.append((-draft.value(prospect, needs), tie_key(team, prospect.index + 1), team))
        result.offered[prospect.index] = teams
        if open_teams:
            team = min(open_teams)[2]
            result.signed.append((prospect, team, sign(draft, team, prospect)))
    return result


def computer_offers(draft, skip: tuple = ()) -> list:
    prospects = pool(draft)
    offers = []
    for team in range(1, D.TEAMS + 1):
        if team not in skip:
            offers += team_offers(draft, team, prospects)
    return offers


def run(draft, extra: list = (), skip: tuple = (), own: tuple = ()) -> Result:
    """The undrafted market right after the draft: the offers of every team but the ones in `skip` and the `extra` offers (the player's), judged together;
    `own` the teams whose offers are a person's own choice (not held to the need rule)."""
    return resolve(draft, computer_offers(draft, skip) + list(extra), own=tuple(own))


def check_undrafted(league, data: dict, whole, taken: set, slots_done: bool) -> set:
    """LeagueError unless the draft record's "undrafted" rows are whole: prospects nobody drafted, each once, signed only once the draft is complete, at most
    `FR_UDFA_MAX` a team, each a player waiting for the cut with his prospect's name, position, rating, potential and age, undrafted. Returns their IDs."""
    from .league import LeagueError
    rows = data["undrafted"]
    if not isinstance(rows, list) or len(rows) > D.TEAMS * T.FR_UDFA_MAX:
        raise LeagueError("the undrafted signings are %r" % (type(rows).__name__ if not isinstance(rows, list) else len(rows),))
    if rows and not slots_done:
        raise LeagueError("undrafted free agents signed before the draft is over")
    ids: set = set()
    per_team: dict = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 3:
            raise LeagueError("an undrafted signing is %r" % (row,))
        team, index, pid = row
        whole(team, 1, D.TEAMS, "an undrafted signing's team")
        whole(index, 0, len(data["class"]) - 1, "an undrafted signing's prospect")
        whole(pid, 1, 10 ** 9, "an undrafted signing's player")
        if index in taken or pid in ids:
            raise LeagueError("the undrafted signing %r is a drafted prospect or twice" % (row,))
        per_team[team] = per_team.get(team, 0) + 1
        if per_team[team] > T.FR_UDFA_MAX:
            raise LeagueError("team %d signed %d undrafted free agents" % (team, per_team[team]))
        player = league.players.get(pid)
        prospect = data["class"][index]
        if (player is None or player.status != "active" or player.place != -1 or player.team != team or player.drafted is not None
                or (player.name, player.pos, player.rating, player.potential, player.age) != (prospect[1], prospect[0], prospect[2], prospect[3], prospect[4])):
            raise LeagueError("the undrafted signing %r is not a rookie waiting for the cut" % (row,))
        taken.add(index)
        ids.add(pid)
    return ids
