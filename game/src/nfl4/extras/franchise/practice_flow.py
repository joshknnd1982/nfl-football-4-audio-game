"""The practice squad as the player hears it: F9, Franchise, practice squad (nfl4 only, rule 0.13; D-136). This is inspired by Jim Kitchen.

The rules are `practice.py` (no speech, no files, no draw). The menu, in the regular season and the play-offs, before the kick-off, never inside a
game (the free agents' menu's own conditions, `signings_flow.closed_reason`, except that the play-offs are open: a squad player may be elevated or
signed then too):

* hear the practice squad: every squad player, the best first, with his position, age, rating and the elevations he has left;
* elevate a squad player for this week's game (GitHub issue 19, D-247): a squad man starts in place of a hurt man of his family who does not play
  this week, for this game only (the same choice as the injury report's "who starts for"); Enter on a man brought up sends him back;
* sign a player to your roster: a squad player, and, when his group has no open place, the player of the group to release (his dead money said);
  one confirmation; he signs for the minimum for one season;
* add a free agent to the squad (D-187): the position first (the Franchise's families), then that position's free agents of the season (the F9 free
  agents' pool, real players at their real positions in a franchise's first season), each said with his real position, age, rating and whether he is
  a veteran; when the squad is full (16, or 17 with a real squad's international man) or has its six veterans and he is one, the squad men whose release
  makes room, the weakest first; one confirmation. The same flow is the item "add to the practice squad" of F9, Franchise, free agents;
* release a squad player: he becomes a free agent of the season;
* protect squad players, sign from another team's squad, practice squad signings around the league (S-E2, D-200; squad_moves_flow.py);
* the practice squad rules (D-187): the NFL's rules in four sentences.
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
        line = X.text("NXJ-P01", player=words.named(player), position=words.position_for(player), a=player.age, r=player.rating)
    else:
        left = max(0, P.ELEVATIONS - P.elevations(league, player))
        line = X.text("NXJ-P04", player=words.named(player), position=words.position_for(player), a=player.age, r=player.rating, n=left)
    hurt = next((h for h, sub in P.picks(league).items() if sub == player.id), None)
    if hurt is not None:                                         # D-247: brought up for this week's game by the player
        line += X.text("NXJ-P62", player=league.players[hurt].name)
    return line


def elevate_flow(g, speech, keys, store, words) -> str | None:
    """GitHub issue 19 (D-247): bring a squad man up for this week's game, to start in place of a hurt man of his family who does not play, or send a
    man brought up back to the squad. The squad man first, then (when he may take more than one place) whose place, one confirmation; made and
    written, then told (B-X53), and logged (rule 0.15). Returns the sentence to say (None when the player left with Escape)."""
    from . import injuries as I
    from . import injury_flow
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
    if not P.playoffs(league, week) and league.has_bye(league.team, week):
        return X.text("NXJ-P72")
    settings = getattr(getattr(g, "options", None), "settings", None)
    if settings is not None and getattr(settings.game, "nx_fr_auto", False):
        return X.text("NXI-55")                                   # the staff handles the lineup: its rule decides at the kick-off
    members = P.squad(league, league.team)
    if not members:
        return X.text("NXJ-P05")
    index = pick_from(X.text("NXJ-P61"), [squad_line(words, league, p) for p in members])
    if index is None:
        return None
    player = members[index]
    current = next((h for h, sub in P.picks(league).items() if sub == player.id), None)
    if current is not None:                                       # brought up already: send him back to the squad?
        I.choose(league, current, None)
        staff_name = injury_flow.starter_name(league, current, week)
        I.choose(league, current, player.id)
        if not confirmed(X.text("NXJ-P70", player=player.name, give=league.players[current].name, get=staff_name)):
            return X.text("NXI-R40", player=player.name)
        I.choose(league, current, None)
        debuglog.event("franchise", "practice_elevation_undone", week=week, season=league.season, player=player.id, hurt=current)   # rule 0.15
        store.save()
        return X.text("NXJ-P71", player=player.name, get=staff_name, give=league.players[current].name)
    problem = P.elevate_problem(league, player, week)
    if problem == "no elevations left":
        return X.text("NXJ-P63", player=player.name, n=P.ELEVATIONS)
    if problem is not None:
        return X.text("NXJ-S18")
    places = P.places_for(league, player, week)
    if not places:
        if len(P.elevated_now(league, week)) >= P.PER_GAME:
            return X.text("NXJ-P64", n=P.PER_GAME)
        return X.text("NXJ-P65", player=player.name)
    hurt = places[0]
    if len(places) > 1:
        lines = [X.text("NXJ-P67", player=words.named(h), position=words.position_for(h), get=injury_flow.starter_name(league, h.id, week))
                 for h in places]
        chosen = pick_from(X.text("NXJ-P66", player=player.name), lines)
        if chosen is None:
            return None
        hurt = places[chosen]
    asked = (X.text("NXJ-P69", get=player.name, give=hurt.name) if P.playoffs(league, week) else
             X.text("NXJ-P68", get=player.name, give=hurt.name, n=max(0, P.ELEVATIONS - P.elevations(league, player))))
    if not confirmed(asked):
        return X.text("NXI-R40", player=player.name)
    I.choose(league, hurt.id, player.id)
    for item in [i for i in league.todo if i["kind"] == D.TODO_LINEUP and i["player"] == hurt.id]:
        league.todo.remove(item)                                  # the question about his place is answered
    debuglog.event("franchise", "practice_elevated", week=week, season=league.season, player=player.id, position=player.position or player.pos,
                   hurt=hurt.id, used=P.elevations(league, player), playoffs=P.playoffs(league, week))      # rule 0.15
    store.save()                                                  # made and written, then told (B-X53)
    return X.text("NXI-65", get=player.name, give=hurt.name)


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


def release_squad_player(g, speech, keys, store, player) -> str:
    """A squad man released: one confirmation, made and written, then told. The practice squad menu's release and, issue 13 (D-226), the roster's item."""
    league = store.league
    reason = closed_reason(g, league)
    if reason is not None:
        return reason
    speech.stop()
    speech.say_async(X.text("NXJ-P16", player=player.name))
    if keys.read_key() != KEY_ENTER:
        return X.text("NXJ-S24", player=player.name)              # issue 13: "you did not release", no more "you did not sign"
    name = player.name
    P.release_from_squad(league, player)
    debuglog.event("franchise", "practice_released", week=league.gtp, season=league.season, player=player.id)
    store.save()
    return X.text("NXJ-P17", player=name)


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
        return release_squad_player(g, speech, keys, store, members[index])

    def rules():
        return X.text("NXJ-P33") + X.text("NXJ-P34") + X.text("NXJ-P35") + X.text("NXJ-P58")

    from . import squad_moves_flow as MF                            # S-E2 (D-200): protections and the other squads

    items = [Item(lambda: X.text("NXJ-P20"), enter=hear),
             Item(lambda: X.text("NXJ-P60"), enter=lambda: elevate_flow(g, speech, keys, store, words)),      # issue 19 (D-247)
             Item(lambda: X.text("NXJ-P21"), enter=promote),
             Item(lambda: X.text("NXJ-P22"), enter=add),
             Item(lambda: X.text("NXJ-P23"), enter=release),
             Item(lambda: X.text("NXJ-P37"), enter=lambda: MF.protect_flow(g, speech, keys, store, words)),
             Item(lambda: X.text("NXJ-P45"), enter=lambda: MF.sign_other_flow(g, speech, keys, store, words)),
             Item(lambda: X.text("NXJ-P53"), enter=lambda: MF.league_signings(g, speech, keys, store, words)),
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
    from . import positions as PS                                 # D-214: the real positions, never one group for a family
    pool = S.pool(league)
    groups = [code for code in PS.ALL if any(PS.position_of(p) == code for p in pool)]
    if not groups:
        return X.text("NXJ-S14")
    try:
        SpokenMenu(speech, keys, X.text("NXJ-P29"), [Item(lambda position=position: PS.word(position), enter=lambda position=position: take(position))
                                                    for position in groups], space_enters=True, digits_jump=True).run()
    except _Chosen:
        pass
    if not chosen:
        return None
    agents = [p for p in pool if PS.position_of(p) == chosen[0]]
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


__all__ = ["practice_menu", "squad_line", "add_flow", "agent_line", "elevate_flow", "D"]
