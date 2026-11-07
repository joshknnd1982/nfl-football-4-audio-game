"""The practice squads' protections and the signings from other teams' squads as the player hears them (nfl4 only, rule 0.13; S-E2, D-200). This is
inspired by Jim Kitchen.

The rules are `squad_moves.py` (no speech, no files, no draw). Three items of F9, Franchise, practice squad (practice_flow.practice_menu), open when the
squad menu is (the regular season and the play-offs, before a kick-off, never inside a game):

* protect squad players: every squad man, the best first, "protected" or "not protected"; Enter protects him or ends his protection (at most 4; a fifth
  is refused with one sentence). Until the player changes one, the staff protects the 4 best each week (the list's title says so).
* sign from another team's squad: the position (the families that have a man he may sign), then the men of other teams' squads he may sign (not
  protected, not of the team he plays this week, not brought up for this week's game), each with his team; with a full roster, the man of the family to
  release (the practice squad menu's own rule, `signings.releasable`); the cap; one confirmation; he signs for the minimum, one season.
* practice squad signings around the league: the season's rows, the newest first.

And `taken_lines`, the weekly report's line for each of his squad men another team signed this week (NXJ-P36). Every change is made and written, then
told (B-X53), and logged (rule 0.15).
"""
from __future__ import annotations

from ...data import debuglog
from ...game.keys import KEY_ENTER
from ...game.spoken_menu import Item, ListPicker, SpokenMenu
from .. import nx_texts as X
from . import contracts as CT
from . import data as D
from . import practice as P
from . import signings as S
from . import squad_moves as M


def taken_lines(league, rows: list, words) -> list:
    """NXJ-P36 for every row of this week in which another team signed a man of the player's squad."""
    lines = []
    for row in M.taken_from_player(league, rows):
        player = league.players.get(row[3])
        if player is None:
            continue
        lines.append(X.text("NXJ-P36", team=words.team_name(row[2]), player=player.name, position=words.position_for(player),
                            n=len(P.squad(league, league.team))))
    return lines


def protect_line(words, league, player, protected: set) -> str:
    return X.text("NXJ-P39" if player.id in protected else "NXJ-P40", player=words.named(player), position=words.position_for(player), r=player.rating)


def protect_flow(g, speech, keys, store, words) -> str | None:
    """The protections list (Enter toggles, Escape leaves). Returns the sentence to say after it, or None."""
    from .practice_flow import closed_reason
    league = store.league
    reason = closed_reason(g, league)
    if reason is not None:
        return reason
    members = P.squad(league, league.team)
    if not members:
        return X.text("NXJ-P05")

    def line(i: int) -> str:
        return protect_line(words, league, members[i], M.protected_ids(league, league.team))

    def toggle(i: int) -> str:
        player = members[i]
        on = player.id not in M.protected_ids(league, league.team)
        problem = M.set_protected(league, player, on)
        if problem == "four protected":
            return X.text("NXJ-P43")
        if problem is not None:
            return X.text("NXJ-S18")
        debuglog.event("franchise", "squad_protected", week=league.gtp, season=league.season, player=player.id, protected=on,
                       now=sorted(M.protected_ids(league, league.team)))          # rule 0.15
        store.save()                                                  # made and written, then told (B-X53)
        return X.text("NXJ-P41" if on else "NXJ-P42", player=player.name)

    title = X.text("NXJ-P38", m=len(M.protected_ids(league, league.team)), n=len(members)).rstrip()
    if M.staff_protects(league):
        title += X.text("NXJ-P44").rstrip()
    ListPicker(speech, keys, title, len(members), line, on_enter=toggle, close_on_enter=False).run()
    return None


def other_line(words, player) -> str:
    return X.text("NXJ-P47", player=words.named(player), position=words.position_for(player), a=player.age, r=player.rating,
                  team=words.team_name(player.team))


def sign_other_flow(g, speech, keys, store, words) -> str | None:
    """Sign a man of another team's practice squad to the player's roster. Returns the sentence to say (None when he left with Escape)."""
    from .practice_flow import closed_reason
    from .signings_flow import release_line
    league = store.league

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    def confirmed(text: str) -> bool:
        say(text)
        return keys.read_key() == KEY_ENTER

    def pick_from(title: str, lines: list):
        return ListPicker(speech, keys, title, len(lines), lambda i: lines[i]).run()

    reason = closed_reason(g, league)
    if reason is not None:
        return reason
    week = league.gtp
    everyone = M.signable(league, league.team, week)
    from . import positions as PS                                     # D-214: the real positions, never one group for a family
    groups = [code for code in PS.ALL if any(PS.position_of(p) == code for p in everyone)]
    if not groups:
        return X.text("NXJ-P48")
    chosen: list = []

    class _Chosen(Exception):
        pass

    def take(family):
        chosen.append(family)
        raise _Chosen()
    try:
        SpokenMenu(speech, keys, X.text("NXJ-P46"), [Item(lambda family=family: PS.word(family), enter=lambda family=family: take(family))
                                                    for family in groups], space_enters=True, digits_jump=True).run()
    except _Chosen:
        pass
    if not chosen:
        return None
    men = [p for p in everyone if PS.position_of(p) == chosen[0]]
    index = pick_from(X.text("NXJ-P59"), [other_line(words, p) for p in men])
    if index is None:
        return None
    player = men[index]
    release = None
    if not S.open_place(league, league.team, player.pos):
        candidates = S.releasable(league, league.team, player.pos, week)
        if not candidates:
            return X.text("NXJ-S15")
        picked = pick_from(X.text("NXJ-S06", player=player.name), [release_line(words, p) for p in candidates])
        if picked is None:
            return None
        release = candidates[picked]
    if not M.cap_allows(league, league.team, player, release):
        return X.text("NXJ-S16", room=words.amount(max(0, CT.cap_space(league, league.team))))
    team_word = words.team_name(player.team)
    contract = words.contract_of(CT.min_salary(player.seasons), 1)
    asked = (X.text("NXJ-P49", player=player.name, team=team_word, contract=contract) if release is None else
             X.text("NXJ-P50", give=release.name, get=player.name, team=team_word, contract=contract, dead=words.amount(CT.dead_money(release))))
    if not confirmed(asked):
        return X.text("NXJ-S17", player=player.name)
    if player not in M.signable(league, league.team, week):          # nothing changed while he was asked (a guard; the questions change nothing)
        return X.text("NXJ-S18")
    old = player.team
    gone = release.name if release is not None else ""
    salary, dead = M.sign_up(league, league.team, player, release)
    M.record(league, week, old, league.team, player)
    from .signings_flow import _surnames
    refilled = M.refill(league, old, player.pos, _surnames(g), getattr(g, "real_names", None))     # the other team (a computer team) fills its squad
    debuglog.event("franchise", "squad_signed", week=week, season=league.season, team=league.team, player=player.id,
                   position=player.position or player.pos, rating=player.rating, from_team=old, own=False, released=release.id if release is not None else None,
                   salary=salary, dead_money=dead, refilled=refilled.id if refilled is not None else None, by_player=True)      # rule 0.15
    store.save()                                                      # made and written, then told (B-X53)
    return X.text("NXJ-P51", player=player.name, team=team_word) if release is None else X.text("NXJ-P52", give=gone, get=player.name, team=team_word)


def league_signings(g, speech, keys, store, words) -> str | None:
    """The season's squad signings, the newest first (Enter does nothing; Escape leaves)."""
    league = store.league
    rows = list(reversed(league.practice["signings"]))
    if not rows:
        return X.text("NXJ-P57")

    def line(i: int) -> str:
        week, old, team, pid = rows[i]
        player = league.players.get(pid)
        name, position = (player.name, words.position_for(player)) if player is not None else ("", "")
        if old == team:
            return X.text("NXJ-P56", w=week, team=words.team_name(team), player=name, position=position)
        return X.text("NXJ-P55", w=week, team=words.team_name(team), player=name, position=position, other=words.team_name(old))

    ListPicker(speech, keys, X.text("NXJ-P54"), len(rows), line, close_on_enter=False).run()
    return None


__all__ = ["taken_lines", "protect_flow", "sign_other_flow", "league_signings"]
