"""A week of the Franchise: the preparation, the news, the to-do list and its deadline (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.4 and 8 (F5). The rules are `todo.py` (the items and their effects) and `news.py` (the lines a week's results
make); this module is the flow in the program's week loop and speaks, asks the player (`FranchiseQuestion`, on the original's key
wait) and writes league.sav, as `offseason.py` does for the stages:

* `before_menu` (H15, inside the main menu, after today's game and before " <coach> select "), on the first pass of a week only. The
  PREPARATION changes the league and saves BEFORE anything is spoken (B-X53): the computer teams' points of extra work and the news
  of the week that was just played, this week's items, the told mark. A window closed in the middle of the questions resumes with
  the same items (the preparation is not made twice); the lines already told are marked told as they are spoken.
* `before_game` (H15, when "play game" is chosen): the deadline. Items still waiting are said and asked once more; an item still
  left for later is closed with its "do nothing" answer and NXD-30 says so (design 8.1: nothing is decided for the player). A game
  that is loaded from a saved game is past its kick-off: its items are closed the same way.
* `staff_takes` (the setting nx_fr_auto): every item still waiting takes the staff's recommendation at once, at the first pass of the
  week and at the kick-off, and one sentence says how many.
* SX.8k: the preparation first draws the injuries of the week that was played (`injuries.after_games`, the one code path of the fast run too; the
  player's game drew its own per play and is left out), makes the player's injury report (told after the news) and the news of another team's injury
  (NWJ), and asks about his doubtful and questionable players who matter (`injuries.to_ask`: play him or rest him; nothing is decided for him).
* SX.8n: the preparation first moves every player's morale by the week that was played (`people.after_week`: the results, the game goals, who played; before the
  injuries of that week's games are drawn), makes the trade demands of the week after the week's trades (`people.demands_week`: a computer team's demand may be
  a trade, the player's is an item of his to-do list), tells a new demand in the news (NWH) and sets the player's game goal (told at the kick-off).
* SX.8j: the preparation also makes the computer teams' trades of the week (`trades.week`, the one code path of the fast run too): a trade of two
  computer teams is made at once and told in the news (NWX); a trade with the player's team is an offer in his to-do list (accept, decline, later).
"""
from __future__ import annotations

from ...game.banter import play_line
from ...game.banter_markup import Speak, parse_markup, speak_text
from .. import nx_texts as X
from .. import playbook_data as PD
from .. import playbooks as PB
from ..nfl_rules import is_nfl
from . import data as D
from . import injuries, injury_flow, news, people, people_flow, staff, todo, trade_flow, trades, workload
from .league import SEASON, team_index
from .news_pools import DEFAULT_POOLS
from .question import FranchiseQuestion


def in_regular_season(league) -> bool:
    return league is not None and league.stage == SEASON and 1 <= league.gtp <= league.regular_weeks


# ----- the preparation of a week (the league changes and is saved before anything is said) -----

def prepare(p, league, week: int) -> None:
    """The first pass of `week`: the computer teams' points and the news of the week before, the computer teams' trades of this week (SX.8j) and their
    news, this week's items (the trade offered to the player among them), the told mark; saved."""
    g, store = p.g, p.store
    pools = g.news_pools or DEFAULT_POOLS
    todo.drop_old(league, week)
    events = []
    back = []
    staff_setting = bool(getattr(g.options.settings.game, "nx_fr_auto", False))
    if week > 1:                                             # what the week that was just played brings (judged before a trade changes a strength)
        todo.computer_extra_work(league, week - 1)
        events = news.week_events(league, week - 1, cut=False)
        people.after_week(league, week - 1, league.results, staff_setting)     # SX.8n: the morale (who played: before that week's injuries join the league)
        workload.count_games(league, week - 1, staff_setting)                  # SX.8o: the games each player played his own place (the awards)
        back = injuries.after_games(league, week - 1, g.rnd, surnames_of(g), played_teams(league, week - 1)).back
    made, offers = trades.week(league, week, league.records)
    demanded, own_demands, filed = people.demands_week(league, week, league.records)       # SX.8n: after the week's own trades
    if week > 1:                                             # (SX.8j: the trades of the computer teams share the week's lines; SX.8k: so does another team's injury)
        hurt = injury_flow.headline(league, week)
        extra = news.trade_events(league, made + demanded) + news.demand_events(league, filed) + ([hurt] if hurt is not None else [])
        news.make_entries(league, news.with_trades(events, extra), pools, store.words, g.rnd, week - 1)
    elif filed or demanded:                                  # SX.8n: week 1 has no week before it; its demands and their trades are news at once (the review)
        news.make_entries(league, news.with_trades([], news.trade_events(league, demanded) + news.demand_events(league, filed)), pools, store.words, g.rnd, 1)
    lines = injury_flow.report_lines(league, week, back, store.words, getattr(g, "injury_pools", None), g.rnd,
                                     bool(getattr(g.options.settings.game, "nx_fr_auto", False)))
    from . import practice
    lines += practice.report_lines(league, store.words)          # D-136: the player's squad players elevated this week
    league.injuries["report"] = {"season": league.season, "week": week, "lines": lines, "told": 0} if lines else None
    items = []
    extra = todo.extra_work_item(league, week)
    if extra is not None:
        items.append(extra)
    plan = None if p.season.on_bye else _game_plan_item(p, league, week)         # SZ.8: a bye week has no opponent to plan for
    if plan is not None:
        items.append(plan)
    items += [todo.trade_item(league, week, offer) for offer in offers]
    items += [injury_flow.item(league, week, pid) for pid in injuries.to_ask(league, week)]
    items += [people_flow.demand_item(league, week, row, choices) for row, choices in own_demands]
    league.todo.extend(items)
    people.set_goal(league, week, 0 if p.season.on_bye else team_index(p.season.tn3, p.season.tn4))    # SX.8n: the player's game goal of the week, told at the kick-off (a bye week has none)
    league.told = [league.season, week]
    league.prepared = [league.season, week]
    store.save()


def surnames_of(g) -> list:
    """The surname pool the league names its players from (the player's surnames.txt), for a stand-in's name."""
    pool = getattr(g, "pool", None)
    if pool is not None:
        return list(pool.original)
    from ...game.names import load_surnames
    return load_surnames()


def played_teams(league, week: int) -> tuple:
    """The two teams of the player's game of `week` (the engine played it, so its injuries came per play), or () when the league has no such result."""
    for row in league.results:
        if row[0] == 0 and row[1] == week and league.team in (row[2], row[3]):
            return row[2], row[3]
    return ()


def _table(g):
    return g.playbook_table or PB.DEFAULT_TABLE


def _game_plan_item(p, league, week: int):
    g, season = p.g, p.season
    settings = g.options.settings.game
    table = _table(g)
    opponent = team_index(season.tn3, season.tn4) - 1

    teams = staff.fitted_styles(league, week)        # SX.8l: the opponent plays its coordinators' styles; SX.8o: or the styles its best players fit

    def style(side: str) -> str:
        key = teams[opponent][0 if side == "O" else 1] if teams is not None else table.team_style(opponent, side)
        return key if key in table.styles else PD.CLASSIC_KEY

    def recommend(side: int, theirs: str) -> str:     # SX.8l: the player's coordinators make the staff's game plan; SX.8o: with his lineup's fit
        return staff.recommended(league, side, theirs, set(table.styles), teams[league.team - 1][side] if teams is not None else None)

    return todo.game_plan_item(league, week, style("O"), style("D"), settings.nx_offense_playbook, settings.nx_defense_playbook,
                               set(table.styles), recommend if teams is not None else None)


# ----- the news -----

def say_markup(g, markup: str) -> None:
    """A kept news line: a plain line is said (say2, queued); a line with a sound, a pause or a faster part plays as a banter line."""
    pieces = parse_markup(markup).pieces
    if pieces is None:
        return
    if all(isinstance(piece, Speak) and not piece.faster for piece in pieces):
        for piece in pieces:
            text = speak_text(piece, "", "", iter(()))
            if text.strip():
                g.say2(text)
        return
    play_line(g, pieces, "", "", [], say=g.say2)


def plain_text(markup: str) -> str:
    """What a kept line says in words (for the lists of F9), "" when it only plays sounds."""
    pieces = parse_markup(markup).pieces
    if pieces is None:
        return ""
    parts = [speak_text(piece, "", "", iter(())).strip() for piece in pieces if isinstance(piece, Speak)]
    return " ".join(part for part in parts if part)


def speak_news(p, league) -> None:
    """The lines of the week that are not told yet: NXN-01, then each line (marked told as it is said), then league.sav."""
    g = p.g
    last = league.last_prepared_week
    fresh = [e for e in news.untold(league) if e["season"] == league.season and e["week"] <= last]
    if fresh:
        g.say2(X.text("NXN-01"))
        for entry in fresh:
            say_markup(g, entry["markup"])
            entry["told"] = 1
    for entry in league.news:                                  # a line of an older season is not told late
        if not entry["told"] and entry not in fresh and entry["week"] <= last:
            entry["told"] = 1
    if fresh:
        p.store.save()


def say_deadline(g, league) -> None:
    """The sentence about the trade deadline this week has, if any (`trades.notice_id`): week 1 says where trades and free agents are, the week before the deadline
    that it is next week, its week that it is the last, the week after that it has passed. Not kept in the news (the trades menu says the deadline too)."""
    notice = trades.notice_id(league, league.gtp)
    if notice is not None:
        g.say2(X.text(notice, n=trades.last_week(league)))


# ----- the to-do list -----

def item_view(g, league, item: dict, later: bool = True) -> tuple:
    """(the situation, the answers' texts) of an item, "later" last when allowed; the answers before it are the item's own."""
    words = g.franchise().words
    if item["kind"] == D.TODO_EXTRA_WORK:
        situation = [X.text("NXD-10")]
        answers = [X.text("NXD-A02", player=pl.name, position=words.position(pl.pos), r=pl.rating, potential=words.potential(pl.potential))
                   for pl in todo.valid_players(league, item)]
        answers.append(X.text("NXD-A03"))
    elif item["kind"] == D.TODO_TRADE:                       # SX.8j: an offer of a computer team, accept (the staff's recommendation) or decline
        situation = trade_flow.offer_lines(words, league, trades.Trade.from_list(item["trade"]))
        answers = [X.text("NXX-A01"), X.text("NXX-A02")]
    elif item["kind"] == D.TODO_INJURY:                      # SX.8k: play or rest a hurt player (the staff's recommendation first)
        situation, answers = injury_flow.item_view(words, league, item)
    elif item["kind"] == D.TODO_DEMAND:                      # SX.8n: a player asks to be traded: the offers and "keep him" (the staff's recommendation first)
        situation, answers = people_flow.demand_view(words, league, item)
    else:
        table = _table(g)
        theirs_o, theirs_d, ours_o, ours_d = item["styles"]
        situation = [X.text("NXD-20", team=g.opponent_team(), their_offense=table.style_name(theirs_o),
                            their_defense=table.style_name(theirs_d), our_offense=table.style_name(ours_o),
                            our_defense=table.style_name(ours_d))]
        answers = [X.text("NXD-21"), X.text("NXD-22")]
    if later:
        answers.append(X.text("NXD-A01"))
    return situation, answers


def finish_item(store, league, item: dict, answer: int, answers: int) -> tuple:
    """Take the answer `answer` of an item whose own answers number `answers` (the answer after them is "later"): (True, what came
    of it) when the item is done, (False, "") when it was put off. The league is saved. The caller says the text."""
    if answer >= answers:
        todo.put_off(item)
        store.save()
        return False, ""
    text = ""
    wanted = people_flow.demand_choices(league, item)[answer] is not None if item["kind"] == D.TODO_DEMAND else False     # SX.8n: he chose a trade
    chosen = todo.apply_answer(league, item, answer)
    if item["kind"] == D.TODO_TRADE:
        trade = trades.Trade.from_list(item["trade"])
        own = trade.other(league.team)
        words = getattr(store, "words", None)
        if chosen is not None:
            text = trade_flow.made_line(words, league, chosen)
        elif answer == 0:
            text = X.text("NXX-03")
        else:
            text = X.text("NXX-04", team=words.team_name(own))
    elif item["kind"] == D.TODO_EXTRA_WORK:
        if chosen is not None:
            text = X.text("NXD-11", player=chosen.name)
    elif item["kind"] == D.TODO_INJURY:
        text = injury_flow.result_text(league, item["player"], bool(chosen))
    elif item["kind"] == D.TODO_DEMAND:
        text = people_flow.demand_result(getattr(store, "words", None), league, item, chosen, wanted=wanted)
    elif item["state"] == D.ITEM_SET:
        text = X.text("NXD-23")
    store.save()
    return True, text


def still_waiting(league, item: dict) -> bool:
    """The item is still on the list and waiting. F9 works at every question of the flow (design 3.7), so an item can be answered
    there while the flow's question for it, or for an earlier item, is open: the flow then leaves it alone."""
    return any(listed is item for listed in league.todo) and item["state"] in (D.ITEM_NEW, D.ITEM_LATER)


def ask_item(p, league, item: dict, later: bool = True) -> bool:
    """One item as a question of the program's flow (the original's key wait): True when it was answered, False for "later"."""
    g = p.g
    if not still_waiting(league, item):
        return True
    if item["kind"] == D.TODO_EXTRA_WORK and not todo.valid_players(league, item):
        league.todo.remove(item)                              # nobody can take the point any more
        p.store.save()
        return True
    situation, answers = item_view(g, league, item, later)
    own = todo.answer_count(league, item)
    answer = FranchiseQuestion(g, situation, answers).ask()
    if not still_waiting(league, item):                       # answered in F9 meanwhile: that answer stands
        return True
    done, text = finish_item(p.store, league, item, answer, own)
    if text:
        g.say2(text)
    return done


def staff_takes(p, league) -> int:
    """The setting "the staff handles the to do list" is on: every item still waiting takes the staff's recommendation (the first answer, 0), the
    league is saved, and the sentence says how many (design 8.1). Returns how many."""
    items = todo.waiting(league)
    made = []
    for item in items:
        result = todo.apply_answer(league, item, 0)
        if item["kind"] in (D.TODO_TRADE, D.TODO_DEMAND) and result is not None:
            made.append(result)
    if items:
        p.store.save()
        p.g.say2(X.text("NXD-04" if len(items) == 1 else "NXD-03", n=len(items)))
        for trade in made:                                    # SX.8j: his roster changed, so the trade the staff made is said
            p.g.say2(trade_flow.made_line(p.store.words, league, trade, staff=True))
    return len(items)


def ask_list(p, league) -> None:
    """The items of this week that were not asked yet (design 3.4 item 3)."""
    g = p.g
    items = todo.waiting(league, include_later=False)
    if not items:
        return
    g.say2(X.text("NXD-02" if len(items) == 1 else "NXD-01", coach=league.coach, n=len(items)))
    for number, item in enumerate(items, start=1):
        g.say2(X.text("NXD-05", n=number))
        ask_item(p, league, item)


# ----- H15: the two places the program's week loop calls -----

def before_menu(p) -> None:
    """Design 3.4: week 1 NXF-08, the news, the to-do list; once a week (the told mark), also across a restart."""
    g, league = p.g, p.store.league
    if not in_regular_season(league):
        return
    announce = league.gtp == 1 and league.told != [league.season, 1]       # the season line, once
    fresh = league.prepared != [league.season, league.gtp]               # the first pass of the week
    if fresh:
        prepare(p, league, league.gtp)
    if announce:
        g.say2(X.text("NXF-08", n=league.season))
    speak_news(p, league)
    if fresh:
        say_deadline(g, league)                              # SZ.8: where trades and free agents are, and the deadline, once a week with the news
    injury_flow.say_report(p, league)                        # SX.8k: the injury report after the news, once
    people_flow.say_verdict(p)                               # SX.8n: last week's game goal, met or missed, once
    if g.options.settings.game.nx_fr_auto:
        staff_takes(p, league)
    else:
        ask_list(p, league)


def before_game(p) -> None:
    """The deadline: items still waiting are asked once more; what is left for later is closed with its do-nothing answer."""
    g, store = p.g, p.store
    league = store.league
    if not in_regular_season(league):
        return
    _deadline(p, league)
    if not p.saved_game:                                      # SX.8n: the game goal, the last words before the kick-off (a loaded game's kick-off is past)
        people_flow.say_goal(p)


def _deadline(p, league) -> None:
    g, store = p.g, p.store
    items = todo.waiting(league)
    if not items:
        return
    if g.options.settings.game.nx_fr_auto and not p.saved_game:       # the setting was turned on after the week's first pass
        staff_takes(p, league)
        return
    if not p.saved_game:                                      # a loaded game's kick-off is past: no more questions
        g.say2(X.text("NXD-06", n=len(items)))
        for item in items:
            ask_item(p, league, item)
    if todo.close_unanswered(league):
        g.say2(X.text("NXD-30"))
    store.save()


def game_rules(p):
    """The rules of this game when the player took the staff's game plan: the g.rules object of a new game with the plan's
    playbooks on the sides the player plays a playbook on; None otherwise (the program's rules are used)."""
    league = p.store.league
    if not in_regular_season(league) or not is_nfl(p.g.rules):
        return None
    plan = todo.plan_of(league, league.gtp)
    if plan is None:
        return None
    rules = p.g.rules.for_game()
    if rules.offense_book != PD.CLASSIC_KEY and plan[0] != PD.CLASSIC_KEY:     # a side that was Classic when the plan was taken,
        rules.offense_book = plan[0]                                           # or is Classic now (the setting may have changed
    if rules.defense_book != PD.CLASSIC_KEY and plan[1] != PD.CLASSIC_KEY:     # since), keeps the settings' choice
        rules.defense_book = plan[1]
    return rules
