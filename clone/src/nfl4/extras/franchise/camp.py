"""The camp focus of the Franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8m (research B6's LATER: "focus this camp on offense, defense or young players", a small bounded bonus; D-073). Plain rules, no
speech, no files and no draw, so stage 3 of the offseason (`offseason.stage_development`) and the calibration's fast run use the very same code.

At the start of stage 3, before the year's progression is drawn, every team chooses a focus: its `FR_CAMP_PLAYERS` first candidates of the focus get one
development point each (design 8.2: +1 on the change of the progression, at most `FR_EXTRA_WORK_POINTS` a season). The computer teams and the staff take
`recommend`'s focus; the player chooses (the staff's recommendation first) unless the staff handles his team.

    candidates(league, team, focus)    the players of the focus who can take a point, in the order of the extra work (design 8.1 T1)
    recommend(league, team)             the focus whose side is furthest under the league's mean of that side, else "young"
    apply(league, choices)              every team's camp: its focus (the choice given, else the recommendation) and its points; returns what each got
"""
from __future__ import annotations

from .. import tuning as T
from . import data as D

FOCUS_TEXT = {"offense": "NXU-A01", "defense": "NXU-A02", "young": "NXU-A03"}


def in_use() -> bool:
    """The camp is held: `FR_CAMP_PLAYERS` is over 0 (0 is no camp: no question, no point, no sentence)."""
    return T.FR_CAMP_PLAYERS > 0


def in_focus(player, focus: str) -> bool:
    if focus == "young":
        return player.age <= T.FR_CAMP_YOUNG_AGE
    return player.pos in T.FR_CAMP_SIDES[focus]


def candidates(league, team: int, focus: str) -> list:
    """The team's players in its places who belong to the focus and have fewer than `FR_EXTRA_WORK_POINTS` points, the highest potential first, then the
    youngest, the highest rating, the lower ID (the extra work's order)."""
    pool = [p for p in league.active_of(team) if p is not None and in_focus(p, focus) and p.points < T.FR_EXTRA_WORK_POINTS]
    pool.sort(key=lambda p: (D.POTENTIALS.index(p.potential), p.age, -p.rating, p.id))
    return pool[:T.FR_CAMP_PLAYERS]


def side_mean(league, team: int, side: str) -> tuple:
    """(weighted sum, weight) of the ratings in the team's filled places of one side (the weights of design 4.4)."""
    total = weight = 0
    for player in league.active_of(team):
        if player is not None and player.pos in T.FR_CAMP_SIDES[side]:
            total += D.WEIGHT[player.pos] * player.rating
            weight += D.WEIGHT[player.pos]
    return total, weight


def recommend(league, team: int) -> str:
    """The side whose weighted mean is furthest under the league's mean of that side (compared by cross-multiplying, whole numbers only); "young" when neither
    side is under its league's mean; offense before defense at equal distances."""
    shortfalls = []
    for side in ("offense", "defense"):
        league_total = league_weight = 0
        for other in range(1, D.TEAMS + 1):
            total, weight = side_mean(league, other, side)
            league_total += total
            league_weight += weight
        total, weight = side_mean(league, team, side)
        if not weight or not league_weight:
            continue
        # league mean - team mean = (league_total / league_weight) - (total / weight), compared on the common denominator
        shortfalls.append((league_total * weight - total * league_weight, league_weight * weight, side))
    best = None
    for numerator, denominator, side in shortfalls:
        if numerator <= 0:
            continue
        if best is None or numerator * best[1] > best[0] * denominator:
            best = (numerator, denominator, side)
    return best[2] if best else "young"


def give(players: list) -> None:
    for player in players:
        player.points += 1


def apply(league, choices: dict | None = None) -> dict:
    """Every team's camp, team 1 to 32: its focus (`choices[team]` when given, else `recommend`) and a point for each of its candidates. Returns
    team -> (focus, the players who got a point)."""
    choices = choices or {}
    out = {}
    if not in_use():
        return {team: (choices.get(team) or "young", []) for team in range(1, D.TEAMS + 1)}
    for team in range(1, D.TEAMS + 1):
        focus = choices.get(team) or recommend(league, team)
        picked = candidates(league, team, focus)
        out[team] = (focus, picked)
    for _focus, picked in out.values():                     # the recommendations are all read before any point is given
        give(picked)
    return out
