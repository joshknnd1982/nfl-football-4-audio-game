"""The practice squad as the player hears it: F9, Franchise, practice squad (nfl4 only, rule 0.13; D-136). This is inspired by Jim Kitchen.

The rules are `practice.py` (no speech, no files, no draw). The menu, in the regular season and the play-offs, before the kick-off, never inside a
game (the free agents' menu's own conditions, `signings_flow.closed_reason`, except that the play-offs are open: a squad player may be elevated or
signed then too):

* hear the practice squad: every squad player, the best first, with his position, age, rating and the elevations he has left;
* sign a player to your roster: a squad player, and, when his group has no open place, the player of the group to release (his dead money said);
  one confirmation; he signs for the minimum for one season;
* add a free agent to the squad (D-187): the position first (the Franchise's families), then that position's free agents of the season (the F9 free
  agents' pool, real players at their real positions in a franchise's first season), each said with his real position, age, rating and whether he is
  a veteran; when the squad is full (16, or 17 with a real squad's international man) or has its six veterans and he is one, the squad men whose release
  makes room, the weakest first; one confirmation. The same flow is the item "add to the practice squad" of F9, Franchise, free agents;
* release a squad player: he becomes a free agent of the season;
* the practice squad rules (D-187): the NFL's rules in three sentences.
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
from .signings_flow import _surnames, release_line


def squad_line(words, league, player) -> str:
    if P.playoffs(league, league.gtp):                           # the play-offs: no limit of elevations
        return X.text("NXJ-P01", player=words.named(player), position=words.position_for(player), a=player.age, r=player.rating)
    left = max(0, P.ELEVATIONS - P.elevations(league, player))
    return X.text("NXJ-P04", player=words.named(player), position=words.position_for(player), a=player.age, r=player.rating, n=left)


def agent_line(words, player) -> str:
    """D-187: a free agent who may join the squad: his real position, age, rating, and whether he is a veteran (the squad keeps at most six)."""
    return X.text("NXJ-P30" if P.veteran(player) else "NXJ-P31", player=words.named(player), position=words.position_for(player), a=player.age,
                  r=player.rating)


def closed_reason(g, league) -> str | None:
    if g.play_engine is not None:
        return X.text("NXJ-P10")
    if league.stage != SEASON:
        return X.text("NXJ-P11")
    if league.prepared != [league.season, league.gtp]:
        return X.text("NXJ-S19")
    return None


def promote_player(g, speech, keys, store, words, player) -> tuple:
    """The squad player signs to the roster with the practice squad menu's own questions (the place of the group, the man to release, the contract, one
    confirmation). Returns (the sentence to say, True when he was signed). SR.6: the starting lineup uses it for a squad man the player chose as a starter."""
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
        return reason, False
    week = league.gtp
    release = None
    if not S.open_place(league, league.team, player.pos):
        candidates = S.releasable(league, league.team, player.pos, week)
        if not candidates:
            return X.text("NXJ-S15"), False
        chosen = pick_from(X.text("NXJ-S06", player=player.name), [release_line(words, p) for p in candidates])
        if chosen is None:
            return None, False
        release = candidates[chosen]
    problem = P.promote_problem(league, player, release, week)
    if problem == "over the cap":
        return X.text("NXJ-S16", room=words.amount(max(0, CT.cap_space(league, league.team)))), False
    if problem is not None:
        return X.text("NXJ-S18"), False
    contract = words.contract_of(CT.min_salary(player.seasons), 1)
    asked = (X.text("NXJ-P06", player=player.name, contract=contract) if release is None else
             X.text("NXJ-P07", give=release.name, get=player.name, contract=contract, dead=words.amount(CT.dead_money(release))))
    if not confirmed(asked):
        return X.text("NXJ-S17", player=player.name), False
    names = (player.name, release.name if release is not None else "")
    salary, dead = P.promote(league, player, release)
    debuglog.event("franchise", "practice_promoted", week=week, season=league.season, player=player.id, position=player.pos,
                   rating=player.rating, salary=salary, released=release.id if release is not None else None, dead_money=dead)
    store.save()
    return X.text("NXJ-P08", player=names[0]) if release is None else X.text("NXJ-P09", give=names[1], get=names[0]), True


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
        return promote_player(g, speech, keys, store, words, members[index])[0]

    def add():
        return add_flow(g, speech, keys, store, words)

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

    def rules():
        return X.text("NXJ-P33") + X.text("NXJ-P34") + X.text("NXJ-P35")

    items = [Item(lambda: X.text("NXJ-P20"), enter=hear),
             Item(lambda: X.text("NXJ-P21"), enter=promote),
             Item(lambda: X.text("NXJ-P22"), enter=add),
             Item(lambda: X.text("NXJ-P23"), enter=release),
             Item(lambda: X.text("NXJ-P32"), enter=rules)]
    title = X.text("NXJ-P02", n=len(P.squad(league, league.team)))
    SpokenMenu(speech, keys, title, items, space_enters=True, digits_jump=True).run()


def add_flow(g, speech, keys, store, words) -> str | None:
    """D-187: add a free agent to the player's practice squad: the position, the free agents of it, the release that makes room when the squad is full or
    has its six veterans, one confirmation. Returns the sentence to say (None when the player left with Escape). Used by the practice squad menu and by
    F9, Franchise, free agents."""
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
    S.ensure_pool(league, _surnames(g), getattr(g, "real_names", None))      # NX-B3: the real free agents in a franchise's first season
    chosen: list = []

    class _Chosen(Exception):
        pass

    def take(position):
        chosen.append(position)
        raise _Chosen()
    groups = [position for position in D.ROSTER_ORDER if S.pool_of(league, position)]
    if not groups:
        return X.text("NXJ-S14")
    try:
        SpokenMenu(speech, keys, X.text("NXJ-P29"), [Item(lambda position=position: words.group(position), enter=lambda position=position: take(position))
                                                    for position in groups], space_enters=True, digits_jump=True).run()
    except _Chosen:
        pass
    if not chosen:
        return None
    agents = S.pool_of(league, chosen[0])
    index = pick_from(X.text("NXJ-P12"), [agent_line(words, p) for p in agents])
    if index is None:
        return None
    player = agents[index]
    release = None
    problem = P.sign_problem(league, player)
    if problem in ("the practice squad is full", "too many veterans"):
        choices = P.release_choices(league, player)
        if not choices:
            return X.text("NXJ-P13")
        title = (X.text("NXJ-P24", n=len(P.squad(league, league.team)), player=player.name) if problem == "the practice squad is full" else
                 X.text("NXJ-P25", player=player.name))
        picked = pick_from(title, [squad_line(words, league, p) for p in choices])
        if picked is None:
            return None
        release = choices[picked]
        problem = P.sign_problem(league, player, release=release)
    if problem == "over the cap":
        return X.text("NXJ-S16", room=words.amount(max(0, CT.cap_space(league, league.team))))
    if problem is not None:
        return X.text("NXJ-S18")
    contract = words.contract_of(P.salary_of(player), 1)
    asked = (X.text("NXJ-P14", player=player.name, contract=contract) if release is None else
             X.text("NXJ-P26", give=release.name, get=player.name, contract=contract))
    if not confirmed(asked):
        return X.text("NXJ-S17", player=player.name)
    gone = release.name if release is not None else ""
    P.sign_to_squad(league, player, release=release)
    debuglog.event("franchise", "practice_signed", week=league.gtp, season=league.season, player=player.id, position=player.position or player.pos,
                   rating=player.rating, veteran=P.veteran(player), released=release.id if release is not None else None)      # rule 0.15
    store.save()                                                  # made and written, then told (B-X53)
    return X.text("NXJ-P15", player=player.name) if release is None else X.text("NXJ-P27", give=gone, get=player.name)


__all__ = ["practice_menu", "squad_line", "add_flow", "agent_line", "D"]
