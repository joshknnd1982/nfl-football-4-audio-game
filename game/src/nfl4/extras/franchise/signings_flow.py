"""Free agents as the player hears them: F9, Franchise, free agents, in the regular season (nfl4 only, rule 0.13; SZ.8, D-120). This is inspired by Jim Kitchen.

The rules are `signings.py` (no speech, no files, no draw); this module makes the sentences and runs the menu with the F9 classes (`SpokenMenu`, `ListPicker`), as `trade_flow.py`
does for the trades:

* the menu: sign a free agent; hear the free agents (every one, the best first). It opens only in the regular season, before the kick-off, never inside a game; the offseason has its
  market (`market_flow.py`, F9 shows its list while the stage is in progress).
* sign a free agent: the position, the free agents of it (best first, with what each asks), and, when the team has no open place at the position, the player of the group to release
  (his dead money is said with him); then ONE confirmation with everything the signing does (the contract, the release and its dead money), Enter to do it, Escape to say no.
  The signing is made and written, then told (B-X53).
* release a player (GitHub issue 13, D-226): the position, the team's men of it, then `release_player`, the same as the item "release him" of F9, Franchise,
  your roster: the reason he cannot be released, or ONE confirmation with his contract, his dead money and the cap room after. Open in the season (the
  regular weeks and the play-offs) before the kick-off; the offseason's roster cut releases men there.
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
    return X.text("NXJ-S04", player=words.named(player), position=words.position_for(player), a=player.age, r=player.rating, contract=words.contract_of(salary, years))


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
    return CT.cap_of(league) - CT.cap_used(league, league.team)


# ----- F9, franchise, free agents -----

def free_agents_menu(g, speech, keys, store, words) -> None:
    league = store.league
    reason = closed_reason(g, league)
    if reason is not None:
        speech.stop()
        speech.say_async(reason)
        return
    S.ensure_pool(league, _surnames(g), getattr(g, "real_names", None))      # NX-B3: the real free agents in season 1; the first look adds the veterans to the league (nothing is written until something is signed or the next save)

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    def confirmed(text: str) -> bool:
        say(text)
        return keys.read_key() == KEY_ENTER

    def choose_group(title: str):
        """D-214: a real position of the 22 (free safeties apart from strong safeties, each linebacker apart), never one group for a family."""
        from . import positions as PS
        return PS.choose(speech, keys, title, PS.ALL)

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
        from . import positions as PS
        code = choose_group(X.text("NXJ-S05"))
        if code is None:
            return None
        position = PS.family_word(code)                           # the family: the signing's rules (the open place, the release) work on it
        agents = [p for p in S.pool_of(league, position) if PS.position_of(p) == code]
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

    def to_squad():
        from .practice_flow import add_flow                       # D-187: the practice squad's add, reached where a player looks for free agents
        return add_flow(g, speech, keys, store, words)

    def release_one():
        return release_flow(g, speech, keys, store, words)

    items = [Item(lambda: X.text("NXJ-S01"), enter=sign_one),
             Item(lambda: X.text("NXJ-S02"), enter=hear_all),
             Item(lambda: X.text("NXJ-P28"), enter=to_squad),
             Item(lambda: X.text("NXJ-S20"), enter=release_one)]  # issue 13 (D-226): a release with no signing
    SpokenMenu(speech, keys, X.text("NXJ-S03", room=words.amount(max(0, cap_room(league)))), items, space_enters=True, digits_jump=True).run()


# ----- a release on its own (GitHub issue 13, D-226) -----

def release_closed(g, league) -> str | None:
    """Why no man of the 53 can be released now (a sentence), or None when one can."""
    if g.play_engine is not None:
        return X.text("NXJ-S27")
    if not S.open_for_release(league, league.gtp):
        return X.text("NXJ-S28")                                  # the offseason: its roster cut releases men
    if league.prepared != [league.season, league.gtp]:
        return X.text("NXJ-S29")
    return None


def group_word(family: str) -> str:
    """The family's word for "at least <n> <group>": quarterbacks is the roster's heading (the group of one place says quarterback)."""
    return X.text("NXL-60").strip() if family == "QB" else X.text(D.GROUP_TEXT[family]).strip()


def release_player(g, speech, keys, store, words, player) -> str:
    """Release one man of the 53: the reason he cannot be, or ONE confirmation with his contract, the dead money and the cap room after, Enter to do it,
    Escape to say no; made and written, then told (B-X53), with a starter the player had chosen at his place said once. Returns the sentence."""
    league = store.league
    week = league.gtp
    reason = release_closed(g, league)
    problem = S.release_problem(league, player, week)
    if reason is None and problem is not None:
        if problem == "a player who is hurt":
            reason = X.text("NXJ-S25", player=player.name)
        elif problem == "a team would be short of a position":
            reason = X.text("NXJ-S26", player=player.name, n=T.FR_FAMILY_MIN.get(player.pos, 0), group=group_word(player.pos))
        elif problem == "over the cap":
            reason = X.text("NXJ-S16", room=words.amount(max(0, cap_room(league))))
        else:
            reason = X.text("NXJ-S33")
    if reason is not None:
        debuglog.event("franchise", "release_refused", week=week, season=league.season, player=player.id, reason=problem or "closed")   # rule 0.15
        return reason
    room_after = CT.cap_of(league) - S.cap_after_release(league, league.team, player)
    speech.stop()
    speech.say_async(X.text("NXJ-S22", player=player.name, contract=words.contract(player), dead=words.amount(CT.dead_money(player)),
                            room=words.amount(max(0, room_after))))
    if keys.read_key() != KEY_ENTER:
        return X.text("NXJ-S24", player=player.name)
    name, salary, years = player.name, player.salary, player.years
    dead = S.release_alone(league, player)
    from . import real_roster
    debuglog.event("franchise", "player_released", week=week, season=league.season, player=player.id, position=player.position or player.pos,
                   rating=player.rating, salary=salary, years=years, dead_money=dead, roster=real_roster.roster_count(league, league.team))   # rule 0.15
    from .. import lineup as L
    told = " ".join(t.strip() for t in L.FranchiseBackend(g, store).notices())     # a starter he had chosen there: who starts now, said here once
    store.save()
    text = X.text("NXJ-S23", player=name, n=real_roster.roster_count(league, league.team), m=D.ROSTER_MAX)
    return text + (" " + told + " " if told else "")


def release_flow(g, speech, keys, store, words) -> str | None:
    """F9, Franchise, free agents, release a player: the position (D-214: each real position on its own), the team's men of it in the chart's order with
    each one's contract and dead money, then `release_player`."""
    league = store.league
    reason = release_closed(g, league)
    if reason is not None:
        return reason
    from . import positions as PS
    code = PS.choose(speech, keys, X.text("NXJ-S30"), PS.ALL)
    if code is None:
        return None
    chart = league.chart[league.team - 1]
    men = [league.players[pid] for pid in chart.get(code, ()) if pid in league.players and league.players[pid].status == "active"]
    if not men:
        return X.text("NXJ-S32")
    index = ListPicker(speech, keys, X.text("NXJ-S31"), len(men), lambda i: release_line(words, men[i])).run()
    if index is None:
        return None
    return release_player(g, speech, keys, store, words, men[index])


def _surnames(g) -> list:
    from .weekly import surnames_of
    return surnames_of(g)
