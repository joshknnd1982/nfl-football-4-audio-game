"""Trades as the player hears them: the offer of the to-do list and F9's trades item (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8j (F7, N6.7, research B5, D-070). The rules are `trades.py` (no speech, no files, no draw); this module makes the spoken lines
and runs F9's menu, which uses the F9 classes (`SpokenMenu`, `ListPicker`) as the other franchise items do:

* An offer of a computer team is an item of the week's to-do list (`todo.trade_item`, asked by `weekly.py` like every item): accept (the staff's
  recommendation), decline (the "do nothing" answer) or later; an offer still open at the kick-off is declined (nothing is decided for the player).
* F9, franchise, trades: offers waiting; offer one of your players (the trade block: the other teams' best offers by the value rule); ask for a player (the
  other team answers by the value rule and names the picks it wants); your draft picks; the trades of the season. Every trade the player makes is made,
  written, then told (B-X53). Trades are open in the regular season up to the kick-off of the deadline's week, never inside a game.
"""
from __future__ import annotations

from ...data import debuglog
from ...game.keys import KEY_ENTER
from ...game.spoken_menu import Item, ListPicker, SpokenMenu
from .. import nx_texts as X
from .. import tuning as T
from . import data as D
from . import trades as TR


# ----- the words -----

def pick_text(words, pick: tuple, holder: int, own: int) -> str:
    """A pick named for the player: "your round 2 pick" (his team's own), "their round 3 pick" (the giving team's own), else "the round 2 pick of the
    Bears"."""
    round_no, original = pick
    if original == own:
        return X.text("NXX-P04", round=round_no)
    if original == holder:
        return X.text("NXX-P05", round=round_no)
    return X.text("NXX-P03", round=round_no, team=words.team_name(original))


def picks_line(words, trade: TR.Trade, own: int) -> str:
    """What the picks of a trade are, for the player of team `own`: "you add ...", "the Bears add ...", or "" for none."""
    parts = []
    for giver, picks in ((trade.a, trade.picks_a), (trade.b, trade.picks_b)):
        if not picks:
            continue
        listed = (" %s " % X.text("NXX-P06")).join(pick_text(words, pick, giver, own) for pick in picks)
        parts.append(X.text("NXX-P02", list=listed) if giver == own else X.text("NXX-P01", team=words.team_name(giver), list=listed))
    return " ".join(parts)


def offer_lines(words, league, trade: TR.Trade) -> list:
    """The situation of an offer to the player's team: who he gets, who he gives, the picks."""
    own = league.team
    gives, gets, _, _ = trade.side(own)
    give, get = league.players[gives], league.players[gets]
    return [X.text("NXX-01", team=words.team_name(trade.other(own)), get=get.name, position=words.position(get.pos), r=get.rating, a=get.age,
                   contract=words.contract(get), give=give.name, give_r=give.rating, give_a=give.age, picks=picks_line(words, trade, own))]


def made_line(words, league, trade: TR.Trade, staff: bool = False) -> str:
    """NXX-02 (the player made it: he heard the picks in the offer) or NXX-05 (the staff made it for him, with the picks, which he has not heard)."""
    own = league.team
    gives, gets, _, _ = trade.side(own)
    if staff:
        return X.text("NXX-05", team=words.team_name(trade.other(own)), get=league.players[gets].name, give=league.players[gives].name,
                      picks=picks_line(words, trade, own))
    return X.text("NXX-02", team=words.team_name(trade.other(own)), get=league.players[gets].name, give=league.players[gives].name)


def log_line(words, league, row: list) -> str:
    """A trade of the season in F9's list: " week 5: the Bears traded Smith to the Lions for Jones. the Lions add ... "."""
    week, a, b, pa, pb, picks_a, picks_b, _kind = row
    trade = TR.Trade(a, b, pa, pb, tuple(tuple(p) for p in picks_a), tuple(tuple(p) for p in picks_b))
    text_id = "NXX-25" if week >= 1 else "NXX-35"                    # SZ.8: a trade of the offseason (week 0) says so
    return X.text(text_id, n=week, team=words.team_name(a), other=words.team_name(b), give=league.players[pa].name,
                  get=league.players[pb].name, picks=picks_line(words, trade, league.team))


def closed_reason(g, league) -> str | None:
    """Why the player cannot trade now (a sentence), or None when he can."""
    if g.play_engine is not None:
        return X.text("NXX-16")
    if not TR.in_window(league, league.gtp):
        return X.text("NXX-15", n=TR.last_week(league))
    return None


# ----- F9, franchise, trades -----

def trades_menu(g, speech, keys, store, words, ask_in_menu) -> None:
    """F9's trades item. `ask_in_menu` answers one to-do item as the franchise menu does (the offers waiting are to-do items)."""

    def say(text: str) -> None:
        speech.stop()
        speech.say_async(text)

    def lines_picker(title: str, lines: list) -> None:
        if not lines:
            say(X.text("NXG-18"))
            return
        ListPicker(speech, keys, title, len(lines), lambda i: lines[i], close_on_enter=False).run()

    def pick_from(title: str, lines: list) -> int | None:
        return ListPicker(speech, keys, title, len(lines), lambda i: lines[i]).run()

    def confirmed(text: str) -> bool:
        say(text)
        return keys.read_key() == KEY_ENTER

    def make(trade: TR.Trade) -> None:
        league = store.league
        TR.execute(league, trade, league.gtp, TR.KIND_PLAYER)
        debuglog.event("franchise", "trade_made", week=league.gtp, stage=league.stage, a=trade.a, b=trade.b, give_a=trade.give_a, give_b=trade.give_b,
                       picks_a=len(trade.picks_a), picks_b=len(trade.picks_b))                    # rule 0.15
        store.save()                                             # made and written, then told (B-X53)
        say(made_line(words, league, trade))

    def offers_waiting():
        league = store.league
        waiting = [item for item in league.todo if item["kind"] == D.TODO_TRADE and item["state"] in (D.ITEM_NEW, D.ITEM_LATER)]
        if g.play_engine is not None or not waiting:
            return X.text("NXD-07")
        for item in waiting:
            if item in league.todo and not ask_in_menu(item):
                return None
        return None

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

    def offer_a_player():
        league = store.league
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        position = choose_group(X.text("NXX-11"))
        if position is None:
            return None
        own = TR.group(league, league.team, position)
        index = pick_from(words.group(position), [words.player(pl) for pl in own])
        if index is None:
            return None
        player = own[index]
        if player.id in TR.traded_this_season(league):
            return X.text("NXX-27")
        offers = TR.block_offers(league, league.team, player, league.records, league.gtp)
        if not offers:
            return X.text("NXX-17", give=player.name)
        lines = []
        for trade, _gain in offers:
            get = league.players[trade.give_b]
            lines.append(X.text("NXX-18", team=words.team_name(trade.b), get=get.name, r=get.rating, a=get.age, picks=picks_line(words, trade, league.team)))
        chosen = pick_from(X.text("NXX-11"), lines)
        if chosen is None:
            return None
        trade = offers[chosen][0]
        if TR.problems(league, trade, league.gtp) is not None:
            return X.text("NXX-03")
        if confirmed(X.text("NXX-22", team=words.team_name(trade.b), get=league.players[trade.give_b].name, give=player.name,
                            picks=picks_line(words, trade, league.team))):
            make(trade)
            return None
        return X.text("NXX-04", team=words.team_name(trade.b))

    def ask_for_a_player():
        league = store.league
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        position = choose_group(X.text("NXX-12"))
        if position is None:
            return None
        traded = TR.traded_this_season(league)
        others = sorted((pl for team in range(1, D.TEAMS + 1) if team != league.team for pl in TR.group(league, team, position)
                         if pl.id not in traded), key=lambda pl: (-pl.rating, pl.id))
        target = pick_from(X.text("NXX-20", group=words.group(position)),
                           [X.text("NXX-21", player=pl.name, team=words.team_name(pl.team), r=pl.rating, a=pl.age, contract=words.contract(pl))
                            for pl in others])
        if target is None:
            return None
        get = others[target]
        own = [pl for pl in TR.group(league, league.team, position) if pl.id not in traded]
        if not own:
            return X.text("NXX-27")
        index = pick_from(X.text("NXX-19", group=words.group(position), get=get.name), [words.player(pl) for pl in own])
        if index is None:
            return None
        trade = TR.ask(league, league.team, own[index], get, league.records, league.gtp)
        if trade is None:
            return X.text("NXX-23", team=words.team_name(get.team))
        if confirmed(X.text("NXX-22", team=words.team_name(get.team), get=get.name, give=own[index].name, picks=picks_line(words, trade, league.team))):
            make(trade)
            return None
        return X.text("NXX-04", team=words.team_name(get.team))

    def draft_picks():
        league = store.league
        if league.draft is not None:                         # the draft has begun: the picks he makes in it (traded ones included)
            from .draft import Draft
            made = Draft(league).picks_of(league.team)
            return X.text("NXX-29", list=", ".join(X.text("NXK-15", round=r, pick=k) for r, k in made) if made else X.text("NXK-13"))
        picks = TR.picks_of(league, league.team)
        if not picks:
            return X.text("NXX-24")
        lines_picker(X.text("NXX-13"), [pick_text(words, pick, league.team, league.team) for pick in picks])
        return None

    def season_trades():
        league = store.league
        lines_picker(X.text("NXX-14"), [log_line(words, league, row) for row in league.trades["log"]])
        return None

    items = [Item(lambda: X.text("NXX-10"), enter=offers_waiting),
             Item(lambda: X.text("NXX-11"), enter=offer_a_player),
             Item(lambda: X.text("NXX-12"), enter=ask_for_a_player),
             Item(lambda: X.text("NXX-13"), enter=draft_picks),
             Item(lambda: X.text("NXX-14"), enter=season_trades)]
    SpokenMenu(speech, keys, X.text("NXX-28", n=TR.last_week(store.league)), items, space_enters=True, digits_jump=True).run()
