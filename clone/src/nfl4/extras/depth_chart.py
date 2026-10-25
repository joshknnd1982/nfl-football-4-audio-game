"""The player's depth charts and his players for the key downs and moments (nfl4 only, rule 0.13; NX-D3, NX-D4, D-147, CLAUDE.md 0.30). This is inspired
by Jim Kitchen.

The owner's second report of 2026-10-24: "you should be able to set your starters", "if you set certain players you should have them play on key downs and
key moments again basing it off Madden". The rules part (no speech, no files):

* OUTSIDE A FRANCHISE the order of each position of a team is the real rosters' (rosters.txt, depth order); the player may put players first. The setting
  `nx_depth` keeps it by the written names: "T05 RB=Ray Davis; T05 WR=Khalil Shakir,DJ Moore" (the named players first, in that order, the others after
  them in the file's order; a name no longer on the team is left out). `with_depth` lays it over the loaded names, so the set-up's places (and a new
  franchise's) follow it. The returners (RET) may be any back, receiver or cornerback of the team: a name chosen there becomes a returner's line.
* The key situations: "down" (third and fourth down), "redzone" (the ball inside the other team's 20) and "twominute" (the last two minutes of the second
  or fourth quarter); for each, the "back" of a run and the "receiver" of a pass. The setting `nx_key_players` keeps them: "T05 redzone receiver=Dalton
  Kincaid; T05 down back=James Cook III". In the game the named man takes CHOSEN_PLAYER_SHARE of his group's draw there (`usage.with_key_player`).
* IN A FRANCHISE the player's own team's order and key players are the league's (`LeagueRecord.depth`, league.sav format 16): `order` {group: [player
  ids]} (the men he put first), `key` {situation: {role: player id}}; the other teams follow the staff's order (the best first).
"""
from __future__ import annotations

import dataclasses
import re

from . import tuning as T

TEAMS = 32
# the groups of the depth chart, the rosters' positions each holds (the quarterbacks have their own item, D-140)
GROUPS = (("RB", ("RB", "FB")), ("WR", ("WR",)), ("TE", ("TE",)), ("DL", ("DL",)), ("LB", ("LB",)), ("CB", ("CB",)), ("S", ("S",)),
          ("K", ("K",)), ("P", ("P",)), ("RET", ("RET",)))
GROUP_POSITIONS = dict(GROUPS)
RETURN_FROM = ("RB", "FB", "WR", "CB")           # a returner is a role of a back, a receiver or a cornerback
SITUATIONS = ("down", "redzone", "twominute")
ROLES = ("back", "receiver")
RED_ZONE = 20
TWO_MINUTES = 120
_DEPTH = re.compile(r"^T(\d{1,2})\s+([A-Z]{1,3})\s*=\s*(.+)$", re.IGNORECASE)
_KEY = re.compile(r"^T(\d{1,2})\s+(down|redzone|twominute)\s+(back|receiver)\s*=\s*(.+)$", re.IGNORECASE)


# ----- the settings -----

def _names_ok(names: list) -> bool:
    from .real_names import name_problem
    return all(name_problem(n) is None for n in names)


def parse_depth(text: str) -> dict:
    """{team: {group: [written names]}} from nx_depth; a part that is not "Tnn GROUP=name,name" is skipped."""
    out: dict = {}
    for part in (text or "").split(";"):
        found = _DEPTH.match(part.strip())
        if found is None:
            continue
        team, group = int(found.group(1)), found.group(2).upper()
        names = [n.strip() for n in found.group(3).split(",") if n.strip()]
        if 1 <= team <= TEAMS and group in GROUP_POSITIONS and names and _names_ok(names):
            out.setdefault(team, {})[group] = names
    return out


def render_depth(depth: dict) -> str:
    return "; ".join("T%02d %s=%s" % (team, group, ",".join(depth[team][group]))
                     for team in sorted(depth) for group in [g for g, _p in GROUPS if g in depth[team]])


def parse_keys(text: str) -> dict:
    """{team: {(situation, role): written name}} from nx_key_players."""
    out: dict = {}
    for part in (text or "").split(";"):
        found = _KEY.match(part.strip())
        if found is None:
            continue
        team, situation, role, name = int(found.group(1)), found.group(2).lower(), found.group(3).lower(), found.group(4).strip()
        if 1 <= team <= TEAMS and _names_ok([name]):
            out.setdefault(team, {})[(situation, role)] = name
    return out


def render_keys(keys: dict) -> str:
    return "; ".join("T%02d %s %s=%s" % (team, s, r, keys[team][(s, r)])
                     for team in sorted(keys) for s in SITUATIONS for r in ROLES if (s, r) in keys[team])


def clean_depth(text: str) -> str:
    return render_depth(parse_depth(text))


def clean_keys(text: str) -> str:
    return render_keys(parse_keys(text))


# ----- the order laid over the real names -----

def group_players(real, team: int, group: str) -> list:
    """The team's active players of the group in their order (RealPlayer); for RET the returners' lines."""
    positions = GROUP_POSITIONS[group]
    return [p for p in real.active(team) if p.pos in positions]


def return_candidates(real, team: int) -> list:
    """Who may return kicks: the returners first, then every back, receiver and cornerback of the team not listed as one."""
    first = group_players(real, team, "RET")
    names = {p.name.casefold() for p in first}
    return first + [p for p in real.active(team) if p.pos in RETURN_FROM and p.name.casefold() not in names]


def ordered(players: list, names: list) -> list:
    """The named players first (in the order named, by written name), then the others in their order."""
    by_name = {p.name.casefold(): p for p in players}
    first = []
    for name in names:
        p = by_name.get(name.casefold())
        if p is not None and p not in first:
            first.append(p)
    return first + [p for p in players if p not in first]


def with_depth(real, depth: dict):
    """The real names with every team's chosen order laid over its lines (the positions keep their slots in the file; the returners' lines are made
    from the chosen names). A team the player did not touch is unchanged."""
    if real is None or not depth:
        return real
    from .real_names import RealPlayer
    rosters = list(real.rosters)
    for team, groups in depth.items():
        if not 1 <= team <= TEAMS:
            continue
        roster = list(rosters[team - 1])
        for group, names in groups.items():
            if group == "RET":
                candidates = {p.name.casefold(): p for p in reversed(return_candidates(dataclasses.replace(real, rosters=tuple(rosters)), team))}
                chosen = [candidates[n.casefold()] for n in names if n.casefold() in candidates]
                old = [p for p in roster if p.pos == "RET" and not p.squad]
                new = [RealPlayer("RET", p.number, p.name) for p in chosen] + [p for p in old if p.name.casefold() not in {n.casefold() for n in names}]
                roster = [p for p in roster if not (p.pos == "RET" and not p.squad)]
                cut = next((i for i, p in enumerate(roster) if p.squad), len(roster))
                roster[cut:cut] = new
                continue
            positions = GROUP_POSITIONS[group]
            slots = [i for i, p in enumerate(roster) if p.pos in positions and not p.squad]
            players = ordered([roster[i] for i in slots], names)
            for slot, player in zip(slots, players):
                roster[slot] = player
        rosters[team - 1] = tuple(roster)
    return dataclasses.replace(real, rosters=tuple(rosters))


def put_first(depth: dict, team: int, group: str, name: str, current: list) -> dict:
    """The setting after the player made `name` the first of the group: he leads, then the group's other players in their current order (so a second
    choice keeps the first one's place behind him)."""
    out = {t: dict(g) for t, g in depth.items()}
    order = [name] + [n for n in current if n.casefold() != name.casefold()]
    out.setdefault(team, {})[group] = order
    return out


def reset_team(depth: dict, team: int) -> dict:
    out = {t: dict(g) for t, g in depth.items() if t != team}
    return out


# ----- the key downs and moments in a game -----

def situation_of(state, to_goal: int, left: int | None) -> str | None:
    """The key situation of the snap, the first that holds: the red zone, third or fourth down, the last two minutes of a half; else None."""
    if 0 < to_goal <= RED_ZONE:
        return "redzone"
    if state.down >= 3:
        return "down"
    if left is not None and state.quarter in (2, 4) and left <= TWO_MINUTES:
        return "twominute"
    return None


def place_of(names: list, spoken: str) -> int | None:
    """The place 1 to len(names) the man of that spoken name holds in the game's roster section, or None."""
    for index, name in enumerate(names, start=1):
        if name and name.casefold() == spoken.casefold():
            return index
    return None


def key_share() -> int:
    return T.CHOSEN_PLAYER_SHARE


def key_names(game) -> dict:
    """{(situation, role): the spoken name} of the player's men for the key downs and moments in the game being played: a franchise's (league.depth,
    by player id) or the setting's for the player's team (by written name); {} when he named none."""
    real = getattr(game, "real_names", None)
    if getattr(game, "franchise_in_use", False):
        store = game.franchise()
        league = getattr(store, "league", None)
        if league is None:
            return {}
        out = {}
        for situation, roles in (league.depth or {}).get("key", {}).items():
            for role, pid in roles.items():
                player = league.players.get(pid)
                if player is not None and player.status == "active" and player.team == league.team:
                    out[(situation, role)] = player.name
        return out
    if real is None:
        return {}
    from .franchise.league import team_index
    season = game.season
    team = team_index(season.tn1, season.tn2) if 1 <= season.tn1 <= 8 and 1 <= season.tn2 <= 4 else 0
    chosen = parse_keys(game.options.settings.game.nx_key_players).get(team, {})
    return {key: real.spoken(name) for key, name in chosen.items()}


def key_place_for(game, state, kind) -> int | None:
    """NX-D4: the place (1 to 6) of the player's man for this snap's key situation in his offense's roster section, or None (not his offense, not a
    key situation, nobody named, or the man is not in the game's six: hurt, or no longer on the team)."""
    if state is None or state.wisoff != 1 or getattr(state, "qb_run", ""):
        return None
    from .qb_runs import to_goal
    extras = getattr(state, "extras", None)
    left = getattr(extras, "left", None) if extras is not None and not isinstance(extras, str) else None
    situation = situation_of(state, to_goal(state), left)
    if situation is None:
        return None
    from .usage import PASS
    role = "receiver" if kind == PASS else "back"
    name = key_names(game).get((situation, role))
    if not name:
        return None
    roster = state.rosters.get(1) if hasattr(state, "rosters") else None
    if roster is None:
        return None
    section = roster.receivers if role == "receiver" else roster.running_backs
    return place_of(section, name)
