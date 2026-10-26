"""Trades as the player hears them: the offer of the to-do list and F9's trades item (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8j (F7, N6.7, research B5, D-070). The rules are `trades.py` (no speech, no files, no draw); this module makes the spoken lines
and runs F9's menu, which uses the F9 classes (`SpokenMenu`, `ListPicker`) as the other franchise items do:

* An offer of a computer team is an item of the week's to-do list (`todo.trade_item`, asked by `weekly.py` like every item): accept (the staff's
  recommendation), decline (the "do nothing" answer) or later; an offer still open at the kick-off is declined (nothing is decided for the player).
* F9, franchise, trades: offers waiting; offer one of your players (the trade block: the other teams' best offers by the value rule); ask a team for a
  player (NX-B5: the team, then the position, then the player, then whom you give; NX-B4: then your picks to add and theirs to ask for, and the other team
  answers by the value rule, asking more of your picks when it is short); the best of a position in the league (the same, from one list of every team);
  your draft picks; the trades of the season. Every trade the player makes is made,
  written, then told (B-X53). Trades are open in the regular season up to the kick-off of the deadline's week and in the offseason from free agency
  to week 1 (D-130), never inside a game, while the draft is under way or while the roster cut is decided; from the draft to week 1 without picks.
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
    return [X.text("NXX-01", team=words.team_name(trade.other(own)), get=words.named(get), position=words.position_for(get), r=get.rating, a=get.age,
                   contract=words.contract(get), give=words.named(give), give_r=give.rating, give_a=give.age, picks=picks_line(words, trade, own))]


def made_line(words, league, trade: TR.Trade, staff: bool = False) -> str:
    """NXX-02 (the player made it: he heard the picks in the offer) or NXX-05 (the staff made it for him, with the picks, which he has not heard)."""
    own = league.team
    gives, gets, _, _ = trade.side(own)
    if staff:
        return X.text("NXX-05", team=words.team_name(trade.other(own)), get=words.named(league.players[gets]), give=words.named(league.players[gives]),
                      picks=picks_line(words, trade, own))
    return X.text("NXX-02", team=words.team_name(trade.other(own)), get=words.named(league.players[gets]), give=words.named(league.players[gives]))


def log_line(words, league, row: list) -> str:
    """A trade of the season in F9's list: " week 5: the Bears traded Smith to the Lions for Jones. the Lions add ... "."""
    week, a, b, pa, pb, picks_a, picks_b, _kind = row
    trade = TR.Trade(a, b, pa, pb, tuple(tuple(p) for p in picks_a), tuple(tuple(p) for p in picks_b))
    text_id = "NXX-25" if week >= 1 else "NXX-35"                    # SZ.8: a trade of the offseason (week 0) says so
    return X.text(text_id, n=week, team=words.team_name(a), other=words.team_name(b), give=words.named(league.players[pa]),
                  get=words.named(league.players[pb]), picks=picks_line(words, trade, league.team))


def closed_reason(g, league) -> str | None:
    """Why the player cannot trade now (a sentence), or None when he can."""
    if g.play_engine is not None:
        return X.text("NXX-16")
    if TR.closed_in_offseason_moves(league):
        debuglog.event("franchise", "trades_closed", why="draft or cut in progress", stage=league.stage, stage_no=league.stage_no)    # rule 0.15
        return X.text("NXX-37")                                     # D-130: the draft or the roster cut is in progress
    if not TR.in_window(league, league.gtp):
        debuglog.event("franchise", "trades_closed", why="outside the window", stage=league.stage, stage_no=getattr(league, "stage_no", 0),
                       week=league.gtp)
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
        own = TR.group(league, league.team, position, bench=True)
        index = pick_from(words.group(position), [words.player(pl) for pl in own])
        if index is None:
            return None
        player = own[index]
        if player.id in TR.traded_this_season(league):
            return X.text("NXX-27")
        offers = TR.block_offers(league, league.team, player, league.records, league.gtp)
        if not offers:
            return X.text("NXX-17", give=words.named(player))
        lines = []
        for trade, _gain in offers:
            get = league.players[trade.give_b]
            lines.append(X.text("NXX-18", team=words.team_name(trade.b), get=words.named(get), r=get.rating, a=get.age, picks=picks_line(words, trade, league.team)))
        chosen = pick_from(X.text("NXX-11"), lines)
        if chosen is None:
            return None
        trade = offers[chosen][0]
        if TR.problems(league, trade, league.gtp) is not None:
            return X.text("NXX-03")
        if confirmed(X.text("NXX-22", team=words.team_name(trade.b), get=words.named(league.players[trade.give_b]), give=words.named(player),
                            picks=picks_line(words, trade, league.team))):
            make(trade)
            return None
        return X.text("NXX-04", team=words.team_name(trade.b))

    def choose_picks(give, get):
        """NX-B4: the picks of the player's proposal, both ways. A short menu whose first item sends the proposal (so Enter keeps the old pace); the others
        add one of his picks, ask for one of theirs, or take one out. Returns (offered, asked), or None when he leaves with Escape."""
        league = store.league
        own, other = league.team, get.team
        offered: list = []
        asked: list = []

        class _Send(Exception):
            pass

        def current() -> str:
            trade = TR.Trade(own, other, give.id, get.id, tuple(offered), tuple(asked))
            return picks_line(words, trade, own) or X.text("NXX-47")

        def send():
            raise _Send()

        def add_from(mine: bool):
            chosen_list, holder = (offered, own) if mine else (asked, other)
            if len(chosen_list) >= T.FR_TRADE_PICKS_MAX:
                return X.text("NXX-54", n=T.FR_TRADE_PICKS_MAX)
            left = [pick for pick in TR.picks_of(league, holder) if pick not in chosen_list]
            if not left:
                return X.text("NXX-24") if mine else X.text("NXX-55", team=words.team_name(other))
            title = X.text("NXX-48") if mine else X.text("NXX-49")
            index = pick_from(title, [pick_text(words, pick, holder, own) for pick in left])
            if index is None:
                return None
            pick = left[index]
            chosen_list.append(pick)
            debuglog.event("franchise", "trade_pick_added", side="offered" if mine else "asked", round=pick[0], original=pick[1],
                           other=other)                                                                     # rule 0.15
            named = pick_text(words, pick, holder, own)
            return X.text("NXX-P02", list=named) if mine else X.text("NXX-51", list=named)

        def take_out():
            chosen = [(offered, pick, own) for pick in offered] + [(asked, pick, other) for pick in asked]
            if not chosen:
                return X.text("NXX-53")
            index = pick_from(X.text("NXX-50"), [pick_text(words, pick, holder, own) for _list, pick, holder in chosen])
            if index is None:
                return None
            where, pick, holder = chosen[index]
            where.remove(pick)
            debuglog.event("franchise", "trade_pick_removed", round=pick[0], original=pick[1], other=other)    # rule 0.15
            return X.text("NXX-52", list=pick_text(words, pick, holder, own))

        items = [Item(lambda: X.text("NXX-46", picks=current()), enter=send),
                 Item(lambda: X.text("NXX-48"), enter=lambda: add_from(True)),
                 Item(lambda: X.text("NXX-49"), enter=lambda: add_from(False)),
                 Item(lambda: X.text("NXX-50"), enter=take_out)]
        try:
            SpokenMenu(speech, keys, X.text("NXX-45", give=words.named(give), get=words.named(get)), items, space_enters=True, digits_jump=True).run()
        except _Send:
            return tuple(offered), tuple(asked)
        return None

    def propose_for(get, position):
        """What the player gives for `get` (NX-B5's last step): one of his players of the position, then the picks (NX-B4), then the other team's answer
        by the value rule, to confirm."""
        league = store.league
        traded = TR.traded_this_season(league)
        own = [pl for pl in TR.group(league, league.team, position, bench=True) if pl.id not in traded]
        lines = [words.player(pl) for pl in own] + [X.text("NXM-L84")]          # SR.6: any man for any man (D-164 (5)), so the last line goes to another position
        index = pick_from(X.text("NXX-19", group=words.group(position), get=words.named(get)), lines)
        if index is None:
            return None
        if index == len(own):
            other = choose_group(X.text("NXM-L85"))
            if other is None:
                return None
            own = [pl for pl in TR.group(league, league.team, other, bench=True) if pl.id not in traded]
            if not own:
                return X.text("NXX-27")
            index = pick_from(X.text("NXX-19", group=words.group(other), get=words.named(get)), [words.player(pl) for pl in own])
            if index is None:
                return None
        give = own[index]
        before = ""
        if not TR.picks_open(league):
            offered, asked = (), ()
            before = X.text("NXX-36")                                  # D-139: from the draft to week 1 player for player, said once
        elif TR.picks_of(league, league.team) or TR.picks_of(league, get.team):
            chosen = choose_picks(give, get)
            if chosen is None:
                return None
            offered, asked = chosen
        else:
            offered, asked = (), ()
        trade, added = TR.propose(league, league.team, give, get, offered, asked, league.records, league.gtp)
        debuglog.event("franchise", "trade_proposed", other=get.team, give=give.id, get=get.id, offered=len(offered), asked=len(asked),
                       answer="no" if trade is None else ("more" if added else "yes"), added=len(added))     # rule 0.15
        team = words.team_name(get.team)
        if trade is None:
            return before + X.text("NXX-23", team=team)
        more = X.text("NXX-44", team=team) if added else ""
        if confirmed(before + more + X.text("NXX-22", team=team, get=words.named(get), give=words.named(give), picks=picks_line(words, trade, league.team))):
            make(trade)
            return None
        return X.text("NXX-04", team=team)

    def ask_a_team():
        """NX-B5: the team first, then the position, then the player, then what you give."""
        league = store.league
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        teams = [team for team in range(1, D.TEAMS + 1) if team != league.team]

        def find(text: str):
            text = text.casefold()
            return next((i for i, team in enumerate(teams) if words.team_name(team).casefold().startswith(text)), None)
        chosen = ListPicker(speech, keys, X.text("NXX-39"), len(teams), lambda i: words.team_name(teams[i]), search=find).run()
        if chosen is None:
            return None
        other = teams[chosen]
        position = choose_group(X.text("NXX-40", team=words.team_name(other)))
        if position is None:
            return None
        traded = TR.traded_this_season(league)
        theirs = [pl for pl in TR.group(league, other, position, bench=True) if pl.id not in traded]
        if not theirs:
            return X.text("NXX-43", team=words.team_name(other), group=words.group(position))
        target = pick_from(X.text("NXX-41", group=words.group(position), team=words.team_name(other)),
                           [X.text("NXX-42", player=words.named(pl), r=pl.rating, a=pl.age, contract=words.contract(pl)) for pl in theirs])
        if target is None:
            return None
        debuglog.event("franchise", "trade_target", other=other, position=position, get=theirs[target].id)       # rule 0.15
        return propose_for(theirs[target], position)

    def ask_for_a_player():
        """The best of a position in the whole league (the list before NX-B5, kept as the second way to ask)."""
        league = store.league
        reason = closed_reason(g, league)
        if reason is not None:
            return reason
        position = choose_group(X.text("NXX-12"))
        if position is None:
            return None
        traded = TR.traded_this_season(league)
        others = sorted((pl for team in range(1, D.TEAMS + 1) if team != league.team for pl in TR.group(league, team, position, bench=True)
                         if pl.id not in traded), key=lambda pl: (-pl.rating, pl.id))
        target = pick_from(X.text("NXX-20", group=words.group(position)),
                           [X.text("NXX-21", player=words.named(pl), team=words.team_name(pl.team), r=pl.rating, a=pl.age, contract=words.contract(pl))
                            for pl in others])
        if target is None:
            return None
        return propose_for(others[target], position)

    def draft_picks():
        league = store.league
        if league.draft is not None:                         # the draft has begun: the picks he makes in it (traded ones included)
            from .draft import Draft
            made = Draft(league).picks_of(league.team)
            return X.text("NXX-29", list=", ".join(X.text("NXK-15", round=r, pick=k) for r, k in made) if made else X.text("NXK-13"))
        if not TR.picks_open(league):
            return X.text("NXX-36")                                 # D-130: after the draft and before week 1 a trade is player for player
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
             Item(lambda: X.text("NXX-38"), enter=ask_a_team),                  # NX-B5: the team first
             Item(lambda: X.text("NXX-12"), enter=ask_for_a_player),            # the league's best of a position, the second way
             Item(lambda: X.text("NXX-13"), enter=draft_picks),
             Item(lambda: X.text("NXX-14"), enter=season_trades)]
    SpokenMenu(speech, keys, X.text("NXX-28", n=TR.last_week(store.league)), items, space_enters=True, digits_jump=True).run()
