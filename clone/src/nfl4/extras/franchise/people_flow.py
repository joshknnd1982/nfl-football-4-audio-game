"""The people's speech in the Franchise: the holdouts at camp (stage 3), a trade demand in the to-do list, the weekly game goal and its verdict, the roster's words
(nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 17 SX.8n (D-074). The rules are `people.py` (no speech, no files, no draw); this module speaks, asks the player (`FranchiseQuestion`, on the
original's key wait) and writes league.sav:

* Stage 3 starts with ONE write: every team's holdouts are settled by the staff's rule (`people.begin_holdouts`), the player's own (unless the staff handles his
  team) wait in `people["pending"]`; then the stage speaks. Each of his answers (pay him, wait, trade him; the staff's recommendation first) is applied and
  written, then told (B-X53). The staff setting is read at every step; nothing is decided for him while it is off.
* A trade demand of his team is a to-do item each week of the window: the other teams' offers and "keep him", the staff's recommendation first.
* The game goal is said before the kick-off (H15 `before_game`), its verdict before the next week's menu (after the news).
"""
from __future__ import annotations

from .. import nx_texts as X
from . import people as P
from . import trades as TR
from .question import FranchiseQuestion

HOLDOUT_TEXT = {P.PAID: "NXU-H20", P.WAITED: "NXU-H21", P.ON_BLOCK: "NXU-H22"}


# ----- the holdouts at camp -----

def holdouts(p, header: str) -> tuple:
    """Stage 3's holdouts before the camp's focus: (whether a question was asked, so the stage's first line was said with it; the lines still to say)."""
    g, store = p.g, p.store
    league, words = store.league, store.words
    lines: list = []
    if league.people["begun"] != league.season:
        staff = bool(g.options.settings.game.nx_fr_auto)
        rows = P.begin_holdouts(league, staff)
        store.save()                                            # written before anything is said
        for pid, team, _season, outcome in rows:
            if team == league.team and outcome != P.PENDING:           # the staff decided for him (the setting is on); his own is asked below
                lines.append(staff_line(words, league, pid, outcome))
        others = [row for row in rows if row[1] != league.team]
        if others:
            lines.insert(0, X.text("NXU-H06", n=len(others)))
    asked = False
    while league.people["pending"]:
        pid = league.people["pending"][0]
        player = league.players[pid]
        if g.options.settings.game.nx_fr_auto:                   # read at every step: the setting turned on in F9 hands the rest to the staff
            outcome = P.PAID if P.staff_pays(league, league.team, player) else P.WAITED
            P.answer_holdout(league, pid, outcome)
            store.save()
            lines.append(staff_line(words, league, pid, outcome))
            continue
        salary, years = P.new_contract(player)
        fits = P.can_pay(league, league.team, player, salary)
        situation = ([] if asked else [header]) + lines + [X.text("NXU-H01", player=player.name, position=words.position(player.pos), r=player.rating,
                                                                   contract=words.contract(player), ask=words.contract_of(salary, years))]
        if not fits:
            situation.append(X.text("NXU-H02"))
        recommended = P.PAID if P.staff_pays(league, league.team, player) else P.WAITED
        kinds = [recommended] + [k for k in (P.PAID, P.WAITED, P.ON_BLOCK) if k != recommended and (k != P.PAID or fits)]
        items = [X.text({P.PAID: "NXU-H10", P.WAITED: "NXU-H11", P.ON_BLOCK: "NXU-H12"}[k]) for k in kinds]
        outcome = kinds[FranchiseQuestion(g, situation, items).ask()]
        P.answer_holdout(league, pid, outcome)
        store.save()                                            # written before it is told
        g.say2(X.text(HOLDOUT_TEXT[outcome], player=player.name, contract=words.contract(player)))
        asked, lines = True, []
    return asked, lines


def staff_line(words, league, pid: int, outcome: int) -> str:
    player = league.players[pid]
    if outcome == P.PAID:
        return X.text("NXU-H23", player=player.name, contract=words.contract(player))
    return X.text("NXU-H24", player=player.name)


# ----- a trade demand of the player's team (a to-do item) -----

def demand_item(league, week: int, row: list, offers: list) -> dict:
    return {"kind": "trade_demand", "season": league.season, "week": week, "state": 0,
            "demand": [row[0], [trade.to_list() for trade, _gain in offers]]}


def demand_choices(league, item: dict) -> list:
    """The item's answers in order (the staff's recommendation first): Trade objects and None ("keep him")."""
    pid, rows = item["demand"]
    trades_ = [TR.Trade.from_list(r) for r in rows]
    demand = P.demand_of(league, pid) or [pid, league.team, item["week"], P.OPEN]
    pairs = [(t, TR.gain(league, t, league.team, TR.situation(league.records, league.team))) for t in trades_]
    return P.demand_answers(league, demand, pairs)


def demand_view(words, league, item: dict) -> tuple:
    pid = item["demand"][0]
    player = league.players[pid]
    situation = [X.text("NXU-D01", player=player.name, position=words.position(player.pos), n=len(item["demand"][1]))]
    answers = []
    from . import trade_flow
    for choice in demand_choices(league, item):
        if choice is None:
            answers.append(X.text("NXU-D10"))
        else:
            other = choice.other(league.team)
            _gives, gets, _po, _pi = choice.side(league.team)
            answers.append(X.text("NXU-D11", team=words.team_name(other), get=league.players[gets].name, r=league.players[gets].rating,
                                  picks=trade_flow.picks_line(words, choice, league.team)))
    return situation, answers


def demand_result(words, league, item: dict, trade, staff: bool = False, wanted: bool = False) -> str:
    """What the answer did: the trade made, "he stays" (keep him), or, when he chose a trade that could no longer be made, NXU-D13."""
    pid = item["demand"][0]
    if trade is None:
        return X.text("NXU-D13" if wanted else "NXU-D12", player=league.players[pid].name)
    from . import trade_flow
    return trade_flow.made_line(words, league, trade, staff)


# ----- the game goal -----

def goal_text(league) -> str | None:
    goal = league.people["goal"]
    if goal is None:
        return None
    kind, n = goal[2], goal[3]
    return X.text({"margin": "NXU-G01", "win": "NXU-G02", "close": "NXU-G03"}[kind], n=n)


def say_goal(p) -> None:
    """Before the kick-off of a regular week: the player's goal, once (its told mark)."""
    league = p.store.league
    goal = league.people["goal"]
    if goal is None or goal[4] or goal[0] != league.season or goal[1] != league.gtp:
        return
    p.g.say2(goal_text(league))
    goal[4] = 1
    p.store.save()


def say_verdict(p) -> None:
    """Before the next week's menu: whether last week's goal was met, once."""
    league = p.store.league
    verdict = league.people["verdict"]
    if verdict is None or verdict[3] or verdict[0] != league.season:
        return
    p.g.say2(X.text("NXU-G04" if verdict[2] else "NXU-G05"))
    verdict[3] = 1
    p.store.save()


# ----- the roster's words -----

def roster_words(words, league, player) -> str:
    """NXU-T05 or NXU-T06: his tag (if any), his morale and his word, after his line in F9's roster."""
    trait = X.text(P.TRAIT_TEXT[P.personality(player.id)])
    morale = X.text(P.MORALE_TEXT[P.word(P.morale(league, player.id))])
    tag = P.tag_of(player)
    if tag is None:
        return X.text("NXU-T06", morale=morale, trait=trait)
    return X.text("NXU-T05", tag=X.text(P.TAG_TEXT[tag]), morale=morale, trait=trait)
