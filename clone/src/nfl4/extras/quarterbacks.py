"""Every team's quarterbacks, and the starter the player chooses (nfl4 only, rule 0.13; D-132, the owner's answer to Q-065: "List and choose"). This is
inspired by Jim Kitchen.

F9, Rules, Quarterbacks (shown with every rules setting; the real names are used with the N. F. L. rules):

* Outside a franchise the quarterbacks are the real rosters' (rosters.txt, in depth order, extras/real_names.py). The first quarterback of a team starts
  unless the player chose another: the choice is the setting `nx_qb_starters` ("T05=Tyler Huntley; T12=Kenny Pickett"), kept by the written name, so a
  new rosters.txt keeps a choice whose player is still on the team and drops one whose player left (the first quarterback starts again; the log says
  so). `with_starters` lays the choices over the loaded names: the chosen man takes the first quarterback's line, so every game with the real names
  names and plays him (Getqbs' default, the play-by-play), and a NEW franchise gives him its quarterback place.
* In a franchise the quarterbacks are the league's own: the roster's quarterback place starts (the Franchise has one, data.PLACES), and the practice
  squad's quarterbacks are behind him. For his own team the player may make a squad quarterback the starter: he is signed to the roster for the minimum
  and the starter is released (the practice squad's own move, `practice.promote`, with its checks and its confirmation; F9, Franchise, practice squad
  does the same). The other teams' staffs choose their own starters. In the offseason there are no practice squads (they end with the season).

The rules part (`parse_choices` to `with_starters`) has no speech and no files; `quarterbacks_menu` speaks.
"""
from __future__ import annotations

import dataclasses
import logging
import re

from ..data import debuglog
from . import nx_texts as X

log = logging.getLogger("nfl4.extras")

TEAMS = 32
_ENTRY = re.compile(r"^T(\d{1,2})\s*=\s*(.+)$", re.IGNORECASE)


# ----- the choices (the setting nx_qb_starters) -----

def parse_choices(text: str) -> dict:
    """{team 1 to 32: the written name of its chosen starter} from the setting; a part that is not "Tnn=name" or names no team is skipped."""
    from .real_names import name_problem
    out: dict = {}
    for part in (text or "").split(";"):
        part = part.strip()
        if not part:
            continue
        found = _ENTRY.match(part)
        if found is None:
            continue
        team, name = int(found.group(1)), found.group(2).strip()
        if 1 <= team <= TEAMS and name_problem(name) is None:
            out[team] = name
    return out


def render_choices(choices: dict) -> str:
    return "; ".join("T%02d=%s" % (team, choices[team]) for team in sorted(choices))


def clean(text: str) -> str:
    """The setting's value as it is saved: only whole choices, in team order."""
    return render_choices(parse_choices(text))


def quarterbacks_of(real, team: int) -> list:
    """The team's quarterbacks of the loaded rosters (RealPlayer), in depth order: the first one starts."""
    if real is None or not 1 <= team <= TEAMS:
        return []
    return [player for player in real.rosters[team - 1] if player.pos == "QB"]


def with_starters(real, choices: dict):
    """The real names with every chosen starter moved to his team's first quarterback line (the others keep their order behind him). A choice whose
    player is not a quarterback of that team in the rosters (a new rosters.txt) is left out: the team's first quarterback starts."""
    if real is None or not choices:
        return real
    rosters = list(real.rosters)
    for team, name in sorted(choices.items()):
        roster = list(rosters[team - 1])
        slots = [index for index, player in enumerate(roster) if player.pos == "QB"]
        chosen = next((index for index in slots if roster[index].name.casefold() == name.casefold()), None)
        if chosen is None:
            log.info("quarterbacks: the chosen starter %r is not a quarterback of team %d in the rosters; the first one starts", name, team)
            continue
        order = [chosen] + [index for index in slots if index != chosen]
        players = [roster[index] for index in order]
        for slot, player in zip(slots, players):
            roster[slot] = player
        rosters[team - 1] = tuple(roster)
    return dataclasses.replace(real, rosters=tuple(rosters))


def base_names(game):
    """The real names as the files give them, before any chosen starter: the customization's (the player's rosters.txt over the shipped one), or the
    shipped ones for a program without the player's files."""
    custom = getattr(game, "customization", None)
    base = getattr(getattr(custom, "snapshot", None), "real_names", None) if custom is not None else None
    if base is None:
        from . import real_names
        base = real_names.defaults()
    return base


def apply(game) -> None:
    """The loaded real names with the player's chosen starters (called when the customization is applied and when a choice changes). Nothing changes
    while the game has no real names (the Rules are Classic: the files of the extras are not read)."""
    if getattr(game, "real_names", None) is None:
        return
    base = base_names(game)
    if base is None:
        return
    choices = parse_choices(game.options.settings.game.nx_qb_starters)
    game.real_names = with_starters(base, choices)
    if choices:
        debuglog.event("names", "quarterbacks_chosen", teams=sorted(choices))


# ----- F9, Rules, Quarterbacks -----

def item_label(settings) -> str:
    return X.text("NXM-58") + ("" if settings.rules == "nfl" else X.text("NXM-22"))


def quarterbacks_menu(game, speech, keys) -> None:
    """The list of the 32 teams; Enter on a team lists its quarterbacks; Enter on one makes him the starter (outside a franchise) or, on the player's
    own team of a franchise, signs a practice squad quarterback to the roster as the starter."""
    from ..game.spoken_menu import ListPicker

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    store = game.franchise() if getattr(game, "franchise_in_use", False) else None
    if store is not None and store.league is not None:
        _franchise_menu(game, speech, keys, store, say)
        return
    real = game.real_names if getattr(game, "real_names", None) is not None else None
    if real is None:                                   # Classic does not read the files of the extras; the N. F. L. rules could not read them
        say(X.text("NXJ-Q20") if game.options.settings.game.rules != "nfl" else X.text("NXJ-Q10"))
        return

    def team_name(team: int) -> str:
        from .franchise.league import team_ref
        return game.league.team(*team_ref(team))

    def team_line(team: int) -> str:
        names = [game.real_names.spoken(p.name) for p in quarterbacks_of(game.real_names, team)]
        if not names:
            return X.text("NXJ-Q04", team=team_name(team))
        line = X.text("NXJ-Q02", team=team_name(team), player=names[0])
        return line + (X.text("NXJ-Q03", list=", ".join(names[1:])) if len(names) > 1 else "")

    def search(text: str):
        text = text.casefold()
        return next((team - 1 for team in range(1, TEAMS + 1) if team_name(team).casefold().startswith(text)), None)

    def open_team(index: int):
        team = index + 1
        players = quarterbacks_of(game.real_names, team)
        if not players:
            return X.text("NXJ-Q04", team=team_name(team))
        spoken = [game.real_names.spoken(p.name) for p in players]
        labels = [X.text("NXJ-Q06", player=spoken[0])] + spoken[1:]
        chosen = ListPicker(speech, keys, X.text("NXJ-Q05", team=team_name(team)), len(labels), lambda i: labels[i]).run()
        if chosen is None:
            return team_line(team)
        if chosen == 0:
            return X.text("NXJ-Q09", player=spoken[0], team=team_name(team))
        settings = game.options.settings.game
        choices = parse_choices(settings.nx_qb_starters)
        if players[chosen].name.casefold() == (quarterbacks_of(base_names(game), team) or [players[0]])[0].name.casefold():
            choices.pop(team, None)                    # the rosters' own first quarterback again: no choice is kept for the team
        else:
            choices[team] = players[chosen].name
        settings.nx_qb_starters = render_choices(choices)
        game.options.save()
        apply(game)
        debuglog.event("names", "quarterback_starter", team=team, starter=players[chosen].name, chosen=len(choices))      # rule 0.15
        return X.text("NXJ-Q08", player=spoken[chosen], team=team_name(team))

    ListPicker(speech, keys, X.text("NXJ-Q01"), TEAMS, lambda i: team_line(i + 1), on_enter=open_team, close_on_enter=False,
               search=search).run()


def _franchise_menu(game, speech, keys, store, say) -> None:
    from ..game.keys import KEY_ENTER
    from ..game.spoken_menu import ListPicker
    from .franchise import contracts as CT
    from .franchise import data as D
    from .franchise import injuries
    from .franchise import practice as P
    from .franchise import signings as S
    from .franchise.history import Words
    from .franchise.league import team_ref
    from .franchise.practice_flow import closed_reason

    league = store.league
    words = Words(lambda team: game.league.team(*team_ref(team)))

    def starter(team: int):
        return league.player_at(team, D.PLACES_OF["QB"][0])

    def backups(team: int) -> list:
        return [p for p in P.squad(league, team) if p.pos == "QB"]

    def team_line(team: int) -> str:
        first = starter(team)
        name = words.team_name(team)
        if first is None:
            return X.text("NXJ-Q04", team=name)
        line = X.text("NXJ-Q12", team=name, player=first.name, r=first.rating, a=first.age)
        behind = backups(team)
        if behind:
            line += X.text("NXJ-Q13", list=", ".join(X.text("NXJ-Q14", player=p.name, r=p.rating) for p in behind))
        return line

    def search(text: str):
        text = text.casefold()
        return next((team - 1 for team in range(1, TEAMS + 1) if words.team_name(team).casefold().startswith(text)), None)

    def own_team() -> str | None:
        team = league.team
        first = starter(team)
        behind = backups(team)
        labels = ([X.text("NXJ-Q16", player=first.name, r=first.rating, a=first.age)] if first is not None else [])
        labels += [X.text("NXJ-Q17", player=p.name, r=p.rating, a=p.age) for p in behind]
        if not labels:
            return X.text("NXJ-Q04", team=words.team_name(team))
        chosen = ListPicker(speech, keys, X.text("NXJ-Q15"), len(labels), lambda i: labels[i]).run()
        if chosen is None:
            return team_line(team)
        offset = 1 if first is not None else 0
        if chosen < offset:
            return X.text("NXJ-Q07", player=first.name) if behind else X.text("NXJ-Q19")
        player = behind[chosen - offset]
        reason = closed_reason(game, league)
        if reason is not None:
            return reason
        week = league.gtp
        release = None
        if not S.open_place(league, team, "QB"):
            release = first
            if release is None or not injuries.healthy(league, release.id, week):
                return X.text("NXJ-S15")
        problem = P.promote_problem(league, player, release, week)
        if problem == "over the cap":
            return X.text("NXJ-S16", room=words.amount(max(0, CT.cap_space(league, team))))
        if problem is not None:
            return X.text("NXJ-S18")
        contract = words.contract_of(CT.min_salary(player.seasons), 1)
        asked = (X.text("NXJ-P06", player=player.name, contract=contract) if release is None else
                 X.text("NXJ-P07", give=release.name, get=player.name, contract=contract, dead=words.amount(CT.dead_money(release))))
        say(asked)
        if keys.read_key() != KEY_ENTER:
            return X.text("NXJ-S17", player=player.name)
        names = (player.name, release.name if release is not None else "")
        salary, dead = P.promote(league, player, release)
        debuglog.event("franchise", "quarterback_starter", week=week, season=league.season, player=player.id, rating=player.rating, salary=salary,
                       released=release.id if release is not None else None, dead_money=dead)                  # rule 0.15
        store.save()                                   # made and written, then told (B-X53)
        return X.text("NXJ-P08", player=names[0]) if release is None else X.text("NXJ-P09", give=names[1], get=names[0])

    def open_team(index: int):
        team = index + 1
        if team == league.team:
            return own_team()
        return team_line(team) + X.text("NXJ-Q18", team=words.team_name(team))

    ListPicker(speech, keys, X.text("NXJ-Q11"), TEAMS, lambda i: team_line(i + 1), on_enter=open_team, close_on_enter=False,
               search=search, start=league.team - 1).run()
