"""Stage 8 of the offseason: free agency (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8i (F6, N6.6, research B4, D-068). The rules are `market.py` (no speech, no files, no draw); this module speaks, asks the
player and writes league.sav, in the way `resign_flow.py` and `draft_flow.py` do:

* The stage starts with ONE write: the market is opened (`league.market`, round 1) and the league is written. In each round the player hears his open places
  and the money he has, then the free agents for those places, best first, with what each asks and how many other teams are interested; he places up to
  `FR_FA_OFFERS` offers (the price, or ten percent more) and ends the round. Every offer is written as it is placed, so a window closed in the middle
  resumes at the same round with the same offers. Then all the teams' offers are judged together (`market.resolve`), the league is written, and only
  then are the results told (B-X53).
* The staff makes the offers of the player's team by the very rule of the computer teams (`market.team_bids`) when the staff setting is on, or when the
  player handed the rest of free agency to it. Nothing is decided for the player otherwise: with the staff setting off every round is asked, and a round
  with no offer signs nobody for him.
* The free agents nobody signed leave: stage 6 drops them like the released.
* SX.8m: when the player put the non-exclusive tag on one of his players (stage 7), the stage's first write also holds the offer sheet of the computer team
  that wants him (`tags.offer_sheet`, or none); the player keeps him at the offer or lets him go for two first-round picks (the staff answers by its
  recommendation when it handles his team), the answer is applied and written, then told. Every round's signings are kept in `market["moves"]`, and the
  last round's write awards the compensatory picks of next year's draft (`comp.award`), which are told with the stage's end.
"""
from __future__ import annotations

from .. import nx_texts as X
from .. import tuning as T
from . import comp
from . import data as D
from . import market as M
from . import tags
from .question import FranchiseQuestion

END, STAFF, SETTING = "end", "staff", "setting"  # how the player's questions of a round end: his offers are in, the rest is the staff's, the staff setting came on


def _offseason():
    from . import offseason                      # the stage helpers and the wait live there (a late import: offseason imports this module)
    return offseason


def stage_free_agency(p, n: int, m: int, short: bool) -> None:
    off = _offseason()
    g, store = p.g, p.store
    league = store.league
    words = store.words
    team = league.team
    settings = g.options.settings.game
    opening: list = []                           # SX.8m: what the offer sheet's answer says, heard with the stage's first lines
    header = off._stage_line(n, m, "NXE-18")
    heard_header = False
    if league.market is None:                    # the stage starts: the market is opened and written before anything is said
        league.market = M.begin()
        unwanted = None
        if tags.tagged(league) is not None:      # SX.8m: the offer sheet for the player of the non-exclusive tag (or none), in the same write
            sheet = tags.offer_sheet(league)
            if sheet is None:
                unwanted = tags.tagged(league)
                tags.close(league)
            else:
                league.tags["sheet"] = list(sheet)
        store.save()
        if unwanted is not None:
            opening.append(X.text("NXU-55", player=unwanted.name))
    if league.tags.get("sheet"):
        heard_header = not settings.nx_fr_auto   # the question of the sheet begins with the stage's line
        opening += _offer_sheet(g, words, store, league, bool(settings.nx_fr_auto), header)
    state = league.market
    count = len(M.pool(league))
    preface = ([] if heard_header else [header]) + opening + [X.text("NXJ-I01") if count == 1 else X.text("NXJ-01", n=count)]
    told_intro = said_staff = False
    leftover = 0
    while state["round"] <= T.FR_FA_ROUNDS:
        number = state["round"]
        staff = bool(settings.nx_fr_auto or state["staff"])
        mine: list = []
        if not staff:
            how = _ask_round(g, words, store, league, state, number, preface if not told_intro else [])
            told_intro = True
            if how == SETTING:                   # the staff setting was turned on in F9: the round is made again with the staff's offers
                if state["offers"]:
                    g.say2(X.text("NXJ-G03"))    # (the offers placed in this round are withdrawn, and the player is told)
                state["offers"] = []
                store.save()
                continue
            if how == STAFF:                     # the player handed the rest of free agency to the staff
                state["staff"], state["offers"] = 1, []
                store.save()
                continue
            mine = [M.make_bid(league, team, league.players[pid], salary, M.price(league.players[pid], number)[1])
                    for pid, salary in state["offers"]]
        # (when the staff makes the offers of the player's team it is a computer team of the round: `skip` is empty)
        offers = {bid.player: bid for bid in mine}
        result = M.run_round(league, number, mine, skip=() if staff else (team,))
        state["moves"] += result.moves                # SX.8m: for the compensatory picks
        signed_mine = [(player, bid) for player, bid in result.signed if bid.team == team]
        lost = [bid for bid in offers.values() if bid.player not in {pl.id for pl, _ in signed_mine}]
        state["signed"] += len(signed_mine)
        state["lost"] += len(lost)
        state["offers"] = []
        state["round"] = number + 1
        last = number == T.FR_FA_ROUNDS
        if last:
            leftover = len(M.pool(league))
            comp.award(league, state["moves"])            # SX.8m: the compensatory picks of next year's draft
            league.market = None
            league.stage_no = off._next_stage(D.STAGE_FREE_AGENCY)
        store.save()                             # written before it is told (B-X53)
        lines = _result_lines(words, league, result, signed_mine, offers, staff, short)
        if staff and not short and not said_staff:
            lines = [X.text("NXJ-G01")] + lines
            said_staff = True
        if not told_intro:                       # the staff made the first round: the stage's own lines come before its results
            lines = preface + lines
            told_intro = True
        for line in lines:                       # (in a short offseason `_result_lines` holds only his own signings and offers: he must know them before the next round)
            g.say2(line)
    closing = X.text("NXJ-F02", n=state["signed"], m=state["lost"], k=leftover)
    comp_lines = _comp_lines(league, short)
    for line in comp_lines if short else []:
        g.say2(line)
    if short:
        total = state["signed"]
        g.say2(X.text("NXJ-I04") if total == 0 else X.text("NXJ-I03") if total == 1 else X.text("NXJ-G02", n=total))
    else:
        off.wait_for_enter(g, [closing] + comp_lines + [X.text("NXE-03")])


def market_lines(league, words) -> list:
    """The lines of F9's free agents item while the market is open: every free agent of this offseason, the most valuable first, with what he asks in the
    round that is next and how many teams are interested; empty when the market is not open."""
    state = league.market
    if state is None:
        return []
    number = state["round"]
    heard = M.interest(M.computer_bids(league, number, skip=(league.team,)))
    offered = {pid: salary for pid, salary in state["offers"]}
    return [_free_agent_line(words, player, number, heard, offered) for player in M.pool(league)]


# ----- the results of a round -----

def _result_lines(words, league, result, signed_mine: list, offers: dict, staff: bool, short: bool) -> list:
    """What the player hears of a round: his own signings, his offers that lost and why, then (in a full offseason) the most valuable signings of the other
    teams and how many more there were."""
    team = league.team
    lines: list = []
    won = {player.id for player, _ in signed_mine}
    decisions = {decision.player.id: decision for decision in result.decisions}
    for player, bid in signed_mine:
        lines.append(X.text("NXJ-E01", player=player.name, contract=words.contract_of(bid.salary, bid.years)))
    if staff and not signed_mine and not short:
        lines.append(X.text("NXJ-E06"))
    for pid, bid in offers.items():
        if pid in won:
            continue
        decision = decisions.get(pid)
        if decision is not None and decision.winner is not None:
            lines.append(X.text("NXJ-E02", player=decision.player.name, team=words.team_name(decision.winner.team)))
        else:
            lines.append(X.text("NXJ-E03", player=league.players[pid].name))
    if short:
        return lines
    others = [(player, bid) for player, bid in result.signed if bid.team != team]
    for player, bid in others[:D.STARS_NAMED]:
        lines.append(X.text("NXJ-E04", player=player.name, team=words.team_name(bid.team), position=words.position_for(player), r=player.rating))
    if len(others) > D.STARS_NAMED:
        rest = len(others) - D.STARS_NAMED
        lines.append(X.text("NXJ-I02") if rest == 1 else X.text("NXJ-E05", n=rest))
    return lines


# ----- the player's round -----

def _ask_round(g, words, store, league, state: dict, number: int, preface: list) -> str:
    """The player's questions of one round until he ends it (END: his offers are in `state["offers"]`) or hands the rest to the staff (STAFF). A setting turned
    on in F9 hands it over too (the setting is read at every step)."""
    team = league.team
    settings = g.options.settings.game
    notice: list = []
    start = 0
    while True:
        if settings.nx_fr_auto:
            return SETTING
        pool = M.pool(league)
        needs = M.open_places(league, team, staff=False)
        space = M.room(league, team)
        lines = list(preface) + notice
        preface, notice = [], []
        if not needs:                            # nothing to sign: no question, the round is judged
            if number == 1 or lines:             # (said once: a later round of a team that is full has nothing new to tell)
                lines.append(X.text("NXJ-D01"))
                for line in lines:
                    g.say2(line)
            state["offers"] = []
            return END
        positions = {position for position, _ in needs}
        wanted = [pl for pl in pool if pl.pos in positions]
        heard = M.interest(M.computer_bids(league, number, skip=(team,)))
        offered = {pid: salary for pid, salary in state["offers"]}
        lines.append(X.text("NXJ-02", round=number, m=T.FR_FA_ROUNDS, list=words.open_places(needs), room=words.amount(max(0, space))))
        if not wanted:
            lines.append(X.text("NXJ-D05"))
        shown = wanted[:T.FR_FA_LIST]
        items = [_free_agent_line(words, pl, number, heard, offered) for pl in shown]
        more_at = len(items)
        if len(wanted) > len(shown):
            items.append(X.text("NXJ-B01"))
        end_at = len(items)
        items.append(X.text("NXJ-B02"))
        items.append(X.text("NXJ-B03"))
        index = FranchiseQuestion(g, lines, items, start=start).ask()
        start = index
        if index == end_at:
            return END
        if index == end_at + 1:
            return STAFF
        if index == more_at and len(wanted) > len(shown):
            everyone = [_free_agent_line(words, pl, number, heard, offered) for pl in wanted]
            taken = FranchiseQuestion(g, [X.text("NXJ-B01")], everyone, escape_value=-1).ask()
            if taken < 0:
                continue
            notice = _offer_menu(g, words, store, league, state, number, wanted[taken], needs, space)
            continue
        notice = _offer_menu(g, words, store, league, state, number, shown[index], needs, space)


def _free_agent_line(words, player, number: int, heard: dict, offered: dict) -> str:
    salary, years = M.price(player, number)
    return words.free_agent(player, salary, years, heard.get(player.id, 0), offered.get(player.id))


def _offer_menu(g, words, store, league, state: dict, number: int, player, needs: list, space: int) -> list:
    """The offer for one free agent: the price, ten percent more, withdraw or never mind. Returns the lines to say with the next question."""
    salary, years = M.price(player, number)
    raised = M.more(salary)
    current = next((s for pid, s in state["offers"] if pid == player.id), None)
    kinds, items = [], []
    if salary <= space:
        kinds.append("price")
        items.append(X.text("NXJ-C02", contract=words.contract_of(salary, years)))
    if raised <= space and raised > salary:
        kinds.append("more")
        items.append(X.text("NXJ-C03", contract=words.contract_of(raised, years), n=T.FR_FA_OFFER_MORE))
    if current is not None:
        kinds.append("withdraw")
        items.append(X.text("NXJ-C04"))
    kinds.append("back")
    items.append(X.text("NXJ-C05"))
    situation = [X.text("NXJ-C01", player=player.name, room=words.amount(max(0, space)))]
    kind = kinds[FranchiseQuestion(g, situation, items).ask()]
    if kind == "back":
        return []
    if kind == "withdraw":
        state["offers"] = [row for row in state["offers"] if row[0] != player.id]
        store.save()
        return [X.text("NXJ-C08", player=player.name)]
    amount = salary if kind == "price" else raised
    others = [row for row in state["offers"] if row[0] != player.id]
    open_here = dict(needs).get(player.pos, 0)
    at_position = sum(1 for pid, _ in others if league.players[pid].pos == player.pos)
    if len(others) >= T.FR_FA_OFFERS:
        return [X.text("NXJ-D03")]
    if at_position >= open_here * M.chase(number):
        return [X.text("NXJ-D02")]
    state["offers"] = others + [[player.id, amount]]
    store.save()                                 # the offer is written as it is placed
    return [X.text("NXJ-C07", player=player.name, contract=words.contract_of(amount, years))]


# ----- the offer sheet of the non-exclusive tag (SX.8m) -----

def _offer_sheet(g, words, store, league, staff: bool, header: str) -> list:
    """The computer team's offer for the player of the non-exclusive tag: keep him at the offer or let him go for its first-round picks of this draft and the
    next. With the staff handling the player's team the staff's recommendation is taken. The answer is applied and written; returns the lines that tell it."""
    team, salary, years = league.tags["sheet"]
    player = tags.tagged(league)
    contract = words.contract_of(salary, years)
    can = tags.can_match(league, player, salary)
    lead: list = []
    if staff:
        keep = tags.should_match(league, player, salary, years)
        lead.append(X.text("NXU-56", player=player.name))
    else:
        situation = [header, X.text("NXU-50", team=words.team_name(team), player=player.name, position=words.position_for(player), contract=contract),
                     X.text("NXU-51") if can else X.text("NXU-52")]
        recommended = tags.should_match(league, player, salary, years)
        kinds = ([True, False] if recommended else [False, True]) if can else [False]
        items = [X.text("NXU-A08") if kind else X.text("NXU-A09") for kind in kinds]
        keep = kinds[FranchiseQuestion(g, situation, items).ask()]
    if keep:
        tags.match(league, player, salary, years)
        text = X.text("NXU-53", player=player.name, contract=contract)
    else:
        tags.let_go(league, player, team, salary, years)
        text = X.text("NXU-54", player=player.name, team=words.team_name(team))
    tags.close(league)
    store.save()                                  # written before it is told (B-X53)
    return lead + [text]


def _comp_lines(league, short: bool) -> list:
    """The compensatory picks awarded at the end of the stage for next year's draft: the league's count (a full offseason) and the player's own."""
    season = league.season + 1
    rows = [row for row in league.comp if row[0] == season]
    own = comp.of_team(league, league.team, season)
    lines = []
    if rows and not short:
        lines.append(X.text("NXU-60", n=len(rows)) if len(rows) > 1 else X.text("NXU-64"))
    if own:
        rounds = ", ".join(X.text("NXU-62", round=r) for r in own)
        lines.append(X.text("NXU-61", n=len(own), list=rounds) if len(own) > 1 else X.text("NXU-63", list=rounds))
    return lines
