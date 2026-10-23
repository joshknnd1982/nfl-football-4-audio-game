"""Free agents as the player hears them: F9, Franchise, free agents, in the regular season (nfl4 only, rule 0.13; SZ.8, D-120). This is inspired by Jim Kitchen.

The rules are `signings.py` (no speech, no files, no draw); this module makes the sentences and runs the menu with the F9 classes (`SpokenMenu`, `ListPicker`), as `trade_flow.py`
does for the trades:

* the menu: sign a free agent; hear the free agents (every one, the best first). It opens only in the regular season, before the kick-off, never inside a game; the offseason has its
  market (`market_flow.py`, F9 shows its list while the stage is in progress).
* sign a free agent: the position, the free agents of it (best first, with what each asks), and, when the team has no open place at the position, the player of the group to release
  (his dead money is said with him); then ONE confirmation with everything the signing does (the contract, the release and its dead money), Enter to do it, Escape to say no.
  The signing is made and written, then told (B-X53).
"""
from __future__ import annotations

from ...data import debuglog
from ...game.keys import KEY_ENTER
from ...game.spoken_menu import Item, ListPicker, SpokenMenu
from .. import nx_texts as X
from .. import tuning as T
from . import contracts as CT
from . import data as D
from . import signings as S
from .league import SEASON


# ----- the words -----

def free_agent_line(words, player) -> str:
    """NXJ-S04: a free agent with what he asks."""
    salary, years = S.price(player)
    return X.text("NXJ-S04", player=player.name, position=words.position(player.pos), a=player.age, r=player.rating, contract=words.contract_of(salary, years))


def release_line(words, player) -> str:
    """NXJ-S07: a player of the team who may be released, with his contract and what releasing him costs."""
    return X.text("NXJ-S07", player=player.name, r=player.rating, a=player.age, contract=words.contract(player), dead=words.amount(CT.dead_money(player)))


def closed_reason(g, league) -> str | None:
    """Why the player cannot sign a free agent now (a sentence), or None when he can."""
    if g.play_engine is not None:
        return X.text("NXJ-S13")
    if league.stage != SEASON:
        return X.text("NXJ-H01")                                  # the offseason: the market is closed outside its own stage (the original words of SX.8i, with where to sign now)
    if not S.open_for_signing(league, league.gtp):
        return X.text("NXJ-S12")                                  # the play-offs
    if league.prepared != [league.season, league.gtp]:
        return X.text("NXJ-S19")                                  # the results and the standings of the week before are still being told: the new week is not prepared (its injuries are not settled)
    return None


def cap_room(league) -> int:
    return T.FR_CAP - CT.cap_used(league, league.team)


# ----- F9, franchise, free agents -----

def free_agents_menu(g, speech, keys, store, words) -> None:
    league = store.league
    reason = closed_reason(g, league)
    if reason is not None:
        speech.stop()
        speech.say_async(reason)
        return
    S.ensure_pool(league, _surnames(g))                           # the first look adds the veterans to the league (nothing is written until something is signed or the next save)

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    def confirmed(text: str) -> bool:
        say(text)
        return keys.read_key() == KEY_ENTER

    def choose_group(title: str):
        chosen: list = []

        class _Chosen(Exception):
            pass

        def take(position):
            chosen.append(position)
            raise _Chosen()
        items = [Item(lambda position=position: words.group(position), enter=lambda position=position: take(position)) for position in D.ROSTER_ORDER]
        try:
            SpokenMenu(speech, keys, title, items, space_enters=True, digits_jump=True).run()
        except _Chosen:
            pass
        return chosen[0] if chosen else None

    def pick_from(title: str, lines: list):
        return ListPicker(speech, keys, title, len(lines), lambda i: lines[i]).run()

    def hear_all():
        agents = S.pool(league)
        if not agents:
            return X.text("NXJ-S14")
        lines = [free_agent_line(words, p) for p in agents]
        ListPicker(speech, keys, X.text("NXJ-S05"), len(lines), lambda i: lines[i], close_on_enter=False).run()
        return None

    def sign_one():
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        position = choose_group(X.text("NXJ-S05"))
        if position is None:
            return None
        agents = S.pool_of(league, position)
        if not agents:
            return X.text("NXJ-S14")
        index = pick_from(X.text("NXJ-S05"), [free_agent_line(words, p) for p in agents])
        if index is None:
            return None
        player = agents[index]
        salary, years = S.price(player)
        week = league.gtp
        release = None
        if not S.open_place(league, league.team, position):
            candidates = S.releasable(league, league.team, position, week)
            if not candidates:
                return X.text("NXJ-S15")
            chosen = pick_from(X.text("NXJ-S06", player=player.name), [release_line(words, p) for p in candidates])
            if chosen is None:
                return None
            release = candidates[chosen]
        problem = S.problems(league, player, release, week)
        if problem == "over the cap":
            return X.text("NXJ-S16", room=words.amount(max(0, cap_room(league))))
        if problem is not None:
            return X.text("NXJ-S18")
        contract = words.contract_of(salary, years)
        if release is None:
            asked = X.text("NXJ-S08", player=player.name, contract=contract)
        else:
            asked = X.text("NXJ-S09", give=release.name, get=player.name, contract=contract, dead=words.amount(CT.dead_money(release)))
        if not confirmed(asked):
            return X.text("NXJ-S17", player=player.name)
        names = (player.name, release.name if release is not None else "")
        _salary, _years, dead = S.sign(league, player, release, week)
        debuglog.event("franchise", "free_agent_signed", week=week, season=league.season, player=player.id, position=player.pos, rating=player.rating,
                       salary=salary, years=years, released=release.id if release is not None else None, dead_money=dead)       # rule 0.15
        store.save()                                              # made and written, then told (B-X53)
        return X.text("NXJ-S10", player=names[0], contract=contract) if release is None else X.text("NXJ-S11", give=names[1], get=names[0], contract=contract)

    items = [Item(lambda: X.text("NXJ-S01"), enter=sign_one),
             Item(lambda: X.text("NXJ-S02"), enter=hear_all)]
    SpokenMenu(speech, keys, X.text("NXJ-S03", room=words.amount(max(0, cap_room(league)))), items, space_enters=True, digits_jump=True).run()


def _surnames(g) -> list:
    from .weekly import surnames_of
    return surnames_of(g)
