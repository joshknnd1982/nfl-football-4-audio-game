"""Free agents the player signs in the regular season (nfl4 only, rule 0.13; SZ.8, D-120). This is inspired by Jim Kitchen.

A player of the game wrote (2026-10-22): "You can't sign free agents or do trades." Free agency was a stage of the offseason only (`market.py`, `market_flow.py`): in the
season F9's free agents item said "the market is closed". Now the player can sign a free agent in any regular week before the kick-off, as the NFL's clubs do all year.
Plain rules over the league record, no speech, no files and NO DRAW, so the menu (`signings_flow.py`) and the tests use the very same code.

* THE POOL (`pool`): the free agents of the season, the best first: the veterans nobody signed (`ensure_pool` makes FR_FA_SEASON_PER_GROUP of them for every position group,
  rated 58 to 69 and aged 27 to 33, status "free", team 0, left 0: no offseason market ever sees them and stage 6 drops them) and the players the player released this season
  (status "free", team 0, left = the season: they are free agents of the coming offseason too, and, being released, earn no compensatory pick). The veterans are made from a
  hash of the league's ID, the season, the week and the group, never from the game's random draws, so a window closed and opened again finds the same men. The first look adds
  them to the league: they take player IDs (the players who come later, the draft's rookies, have IDs 30 higher than without the look; nothing else of the game changes).
* A SIGNING (`check`, `sign`): the player's team needs an open place at the position, or releases one of its players of the position who is not hurt (his contract ends, his dead
  money is charged to the cap year: `contracts.release`); the new contract is the price of stage 7 (`resign.asking`); the cap (`FR_CAP`) must hold after both. The places are put in
  rating order and the team's strength for the computer's games is brought up to date, as a trade does. Inside a game, in the play-offs and in the offseason nothing is signed
  here (the offseason has its market).
"""
from __future__ import annotations

import hashlib

from .. import tuning as T
from . import aging
from . import contracts as CT
from . import data as D
from . import first_names as FN
from . import injuries
from . import market
from . import resign as R


def _mix(*parts) -> int:
    """A number from the parts, the same on every machine (no draw of the game): the first eight bytes of a SHA-256."""
    return int.from_bytes(hashlib.sha256(repr(parts).encode("utf-8")).digest()[:8], "big")


def open_for_signing(league, week: int) -> bool:
    """Free agents are signed in the regular season, in a week before its kick-off."""
    from .league import SEASON
    return league.stage == SEASON and 1 <= week <= league.regular_weeks


def pool(league) -> list:
    """The free agents of the season, the best first (`resign.value`): the veterans of the pool and the players released this season."""
    return sorted((p for p in league.players.values() if p.status == "free" and p.team == 0 and p.left in (0, league.season)), key=R.value)


def pool_of(league, position: str) -> list:
    return [p for p in pool(league) if p.pos == position]


def price(player) -> tuple:
    """(salary, years) a free agent asks in the season: what he asked in stage 7 (`resign.asking`)."""
    return R.asking(player)


# NX-B3 (D-145): the real free agents' positions in the Franchise's groups (the offensive line and the long snapper have no place in it yet)
REAL_GROUP = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "WR", "DL": "DL", "LB": "LB", "CB": "CB", "S": "S", "K": "K", "P": "P"}


def add_real_free_agents(league, real) -> int:
    """NX-B3 (the owner 2026-10-24: "it should have all current free agents"): in the first season of a franchise the free agents of free_agents.txt join
    the pool, once each (a name the league already has, signed, released or retired, is never made again). No real rating: a hash of the league's ID and the
    name gives a rating in FR_FA_SEASON_RATING, as the made-up veterans have; the real age when the file has it. No draw. Returns how many joined."""
    if real is None or league.season != 1 or not getattr(real, "free_agents", ()):
        return 0
    known = {p.name.casefold() for p in league.players.values()}
    base, span = T.FR_FA_SEASON_RATING
    age_base, age_span = T.FR_FA_SEASON_AGE
    added = 0
    for _ident, agent in real.free_agents:
        position = REAL_GROUP.get(agent.pos)
        name = real.spoken(agent.name) if hasattr(real, "spoken") else agent.name
        if position is None or name.casefold() in known:
            continue
        h = _mix(league.league_id, "real free agent", agent.name)
        rating = max(D.RATING_MIN, min(D.RATING_MAX, base + h % span))
        age = agent.age if agent.age is not None else age_base + (h >> 8) % age_span
        player = _new_player(league, name, position, rating, max(D.AGE_MIN, min(D.AGE_MAX, age)))
        league.players[player.id] = player
        league.next_id += 1
        known.add(name.casefold())
        added += 1
    return added


def ensure_pool(league, surnames: list, real=None) -> int:
    """Make the veterans the pool lacks: for every position group the pool holds at least FR_FA_SEASON_PER_GROUP free agents (the veterans made earlier, the players released
    this season and these). In a franchise's first season the real free agents come first (NX-B3, `add_real_free_agents`), so the made-up veterans only fill a group they
    leave short. Returns how many were made. Adds players to the league (status "free"); the caller saves."""
    made = add_real_free_agents(league, real)
    used = FN.name_keys(league.league_id, {p.name for p in league.players.values() if p.status == "active"} | {p.name for p in pool(league)})
    base, span = T.FR_FA_SEASON_RATING
    age_base, age_span = T.FR_FA_SEASON_AGE
    for position in D.ROSTER_ORDER:
        have = len(pool_of(league, position))
        for index in range(have, T.FR_FA_SEASON_PER_GROUP):
            h = _mix(league.league_id, league.season, league.gtp, position, index, league.next_id)
            start = (h >> 20) % len(surnames)
            name = next((surnames[(start + step) % len(surnames)] for step in range(len(surnames))
                         if surnames[(start + step) % len(surnames)] not in used), surnames[start])
            used.add(name)
            rating = max(D.RATING_MIN, min(D.RATING_MAX, base + h % span))
            age = age_base + (h >> 8) % age_span
            player = _new_player(league, FN.full_name(league.league_id, name), position, rating, age)   # D-131: first and last name
            league.players[player.id] = player
            league.next_id += 1
            made += 1
    return made


def _new_player(league, name: str, position: str, rating: int, age: int):
    from .league import Player
    return Player(league.next_id, name, position, rating, "low", age, max(0, age - 22), rating, None, 0, "free", 0, 0, -1, 0, 0)


def roster_group(league, team: int, position: str) -> list:
    """The team's players of the position, in place order (the empty places left out)."""
    return [p for p in league.group_of(team, position) if p is not None]


def open_place(league, team: int, position: str) -> bool:
    return market.filled(league, team, position) < D.GROUP_SIZE[position]


def releasable(league, team: int, position: str, week: int) -> list:
    """The players of the group the team may release to make room: not hurt (an injury is a record of the league that follows its player, so a hurt man stays until he is fit)."""
    return [p for p in roster_group(league, team, position) if injuries.healthy(league, p.id, week)]


def cap_after(league, team: int, player, release=None) -> int:
    """The cap year's use once the signing is made: the payroll less the released man's contract, plus his dead money, plus the new contract."""
    salary, _years = price(player)
    used = CT.cap_used(league, team)
    if release is not None:
        used += CT.dead_money(release) - (release.salary if CT.running(release) else 0)
    return used + salary


def problems(league, player, release, week: int) -> str | None:
    """Why the signing cannot be made (a short reason for the tests and the checks), or None when it can."""
    team = league.team
    if not open_for_signing(league, week):
        return "outside the regular season"
    if player is None or player.status != "free" or player not in pool(league):
        return "a player who is not a free agent"
    if open_place(league, team, player.pos):
        if release is not None:
            return "a release with an open place"
    else:
        if release is None:
            return "no place and no release"
        if release.status != "active" or release.team != team or release.place < 0 or release.pos != player.pos:
            return "a release who is not a player of the group"
        if not injuries.healthy(league, release.id, week):
            return "a release who is hurt"
    if cap_after(league, team, player, release) > T.FR_CAP:
        return "over the cap"
    return None


def sign(league, player, release, week: int) -> tuple:
    """The signing is made (the caller has checked `problems` and writes league.sav): the released player, when there is one, becomes a free agent of this season and his dead
    money is charged; the free agent joins the team in the place and on the contract of the price. Returns (the salary, the years, the dead money)."""
    team = league.team
    roster = league.rosters[team - 1]
    dead = 0
    if release is not None:
        index = release.place
        roster[index] = 0
        dead = CT.release(league, release)
        release.status, release.left, release.place, release.points, release.team = "free", league.season, -1, 0, 0       # (team 0: nobody lost him, so no compensatory pick)
        _forget(league, release.id)
    else:
        index = next(i for i in D.PLACES_OF[player.pos] if not roster[i])
    salary, years = price(player)
    roster[index] = player.id
    player.status, player.team, player.place, player.left, player.points = "active", team, index, 0, 0
    CT.sign(player, salary, years)
    aging.place_by_rating(league, team)
    if len(league.sums) == D.TEAMS:
        league.sums[team - 1] = league.strength_sum(team)
    return salary, years, dead


def _forget(league, pid: int) -> None:
    """A man who left the team no longer has an open trade demand or a question about him in the to-do list."""
    from . import people
    for row in league.people["demands"]:
        if row[0] == pid and row[3] == people.OPEN:
            row[3] = people.ENDED
    league.todo[:] = [item for item in league.todo
                      if not (item["kind"] == D.TODO_DEMAND and item["demand"][0] == pid) and not (item["kind"] == D.TODO_INJURY and item["player"] == pid)]
