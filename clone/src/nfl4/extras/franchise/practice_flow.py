"""The practice squad as the player hears it: F9, Franchise, practice squad (nfl4 only, rule 0.13; D-136). This is inspired by Jim Kitchen.

The rules are `practice.py` (no speech, no files, no draw). The menu, in the regular season and the play-offs, before the kick-off, never inside a
game (the free agents' menu's own conditions, `signings_flow.closed_reason`, except that the play-offs are open: a squad player may be elevated or
signed then too):

* hear the practice squad: every squad player, the best first, with his position, age, rating and the elevations he has left;
* sign a player to your roster: a squad player, and, when his group has no open place, the player of the group to release (his dead money said);
  one confirmation; he signs for the minimum for one season;
* add a free agent to the squad: the free agents of the season (the F9 free agents' pool), when the squad has room (16, at most 6 veterans);
* release a squad player: he becomes a free agent of the season.
Every change is made and written, then told (B-X53), and logged (rule 0.15).
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
from .league import SEASON
from .signings_flow import _surnames, free_agent_line, release_line


def squad_line(words, league, player) -> str:
    if P.playoffs(league, league.gtp):                           # the play-offs: no limit of elevations
        return X.text("NXJ-P01", player=player.name, position=words.position(player.pos), a=player.age, r=player.rating)
    left = max(0, P.ELEVATIONS - P.elevations(league, player))
    return X.text("NXJ-P04", player=player.name, position=words.position(player.pos), a=player.age, r=player.rating, n=left)


def closed_reason(g, league) -> str | None:
    if g.play_engine is not None:
        return X.text("NXJ-P10")
    if league.stage != SEASON:
        return X.text("NXJ-P11")
    if league.prepared != [league.season, league.gtp]:
        return X.text("NXJ-S19")
    return None


def practice_menu(g, speech, keys, store, words) -> None:
    league = store.league
    reason = closed_reason(g, league)
    if reason is not None:
        speech.stop()
        speech.say_async(reason)
        return

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    def confirmed(text: str) -> bool:
        say(text)
        return keys.read_key() == KEY_ENTER

    def pick_from(title: str, lines: list):
        return ListPicker(speech, keys, title, len(lines), lambda i: lines[i]).run()

    def hear():
        members = P.squad(league, league.team)
        if not members:
            return X.text("NXJ-P05")
        lines = [squad_line(words, league, p) for p in members]
        ListPicker(speech, keys, X.text("NXJ-P03", n=len(members)), len(lines), lambda i: lines[i], close_on_enter=False).run()
        return None

    def promote():
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        members = P.squad(league, league.team)
        if not members:
            return X.text("NXJ-P05")
        index = pick_from(X.text("NXJ-P03", n=len(members)), [squad_line(words, league, p) for p in members])
        if index is None:
            return None
        player = members[index]
        week = league.gtp
        release = None
        if not S.open_place(league, league.team, player.pos):
            candidates = S.releasable(league, league.team, player.pos, week)
            if not candidates:
                return X.text("NXJ-S15")
            chosen = pick_from(X.text("NXJ-S06", player=player.name), [release_line(words, p) for p in candidates])
            if chosen is None:
                return None
            release = candidates[chosen]
        problem = P.promote_problem(league, player, release, week)
        if problem == "over the cap":
            return X.text("NXJ-S16", room=words.amount(max(0, CT.cap_space(league, league.team))))
        if problem is not None:
            return X.text("NXJ-S18")
        contract = words.contract_of(CT.min_salary(player.seasons), 1)
        asked = (X.text("NXJ-P06", player=player.name, contract=contract) if release is None else
                 X.text("NXJ-P07", give=release.name, get=player.name, contract=contract, dead=words.amount(CT.dead_money(release))))
        if not confirmed(asked):
            return X.text("NXJ-S17", player=player.name)
        names = (player.name, release.name if release is not None else "")
        salary, dead = P.promote(league, player, release)
        debuglog.event("franchise", "practice_promoted", week=week, season=league.season, player=player.id, position=player.pos,
                       rating=player.rating, salary=salary, released=release.id if release is not None else None, dead_money=dead)
        store.save()
        return X.text("NXJ-P08", player=names[0]) if release is None else X.text("NXJ-P09", give=names[1], get=names[0])

    def add():
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        S.ensure_pool(league, _surnames(g))
        agents = [p for p in S.pool(league) if p.age <= P.T.FR_PRACTICE_MAX_AGE]
        if not agents:
            return X.text("NXJ-S14")
        index = pick_from(X.text("NXJ-P12"), [free_agent_line(words, p) for p in agents])
        if index is None:
            return None
        player = agents[index]
        problem = P.sign_problem(league, player)
        if problem is not None:
            return X.text("NXJ-P13") if problem.startswith(("the practice squad is full", "too many")) else X.text("NXJ-S18")
        if not confirmed(X.text("NXJ-P14", player=player.name, contract=words.contract_of(P.salary_of(player), 1))):
            return X.text("NXJ-S17", player=player.name)
        P.sign_to_squad(league, player)
        debuglog.event("franchise", "practice_signed", week=league.gtp, season=league.season, player=player.id, position=player.pos, rating=player.rating)
        store.save()
        return X.text("NXJ-P15", player=player.name)

    def release():
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        members = P.squad(league, league.team)
        if not members:
            return X.text("NXJ-P05")
        index = pick_from(X.text("NXJ-P03", n=len(members)), [squad_line(words, league, p) for p in members])
        if index is None:
            return None
        player = members[index]
        if not confirmed(X.text("NXJ-P16", player=player.name)):
            return X.text("NXJ-S17", player=player.name)
        name = player.name
        P.release_from_squad(league, player)
        debuglog.event("franchise", "practice_released", week=league.gtp, season=league.season, player=player.id)
        store.save()
        return X.text("NXJ-P17", player=name)

    items = [Item(lambda: X.text("NXJ-P20"), enter=hear),
             Item(lambda: X.text("NXJ-P21"), enter=promote),
             Item(lambda: X.text("NXJ-P22"), enter=add),
             Item(lambda: X.text("NXJ-P23"), enter=release)]
    title = X.text("NXJ-P02", n=len(P.squad(league, league.team)))
    SpokenMenu(speech, keys, title, items, space_enters=True, digits_jump=True).run()


__all__ = ["practice_menu", "squad_line", "D"]
