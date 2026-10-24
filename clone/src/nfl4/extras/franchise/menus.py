"""F9's Franchise item: your roster, the league history, the franchise settings, and the way between a classic season and a
franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 11 and 3.7. These are settings menus, so they use the F9 classes (`SpokenMenu`, `ListPicker`) with their keys
as they are; the questions inside the program's flow use `FranchiseQuestion`. The item is shown only with the N. F. L. rules and is
built each time F9 opens (`franchise_item_shown`), so with Rules = Classic F9's list is exactly the original's and no franchise
file is opened. SX.8a builds: the roster, league history, franchise settings (offseason only: the other settings come with their
features), play classic seasons, back to your franchise and start a franchise now. SX.8b speaks the ratings and the potential in
the roster and adds the team ratings; SX.8e adds the to-do list and the news; SX.8l your job and staff (the goal, the job rating, the coordinators).
"""
from __future__ import annotations

from ...data import debuglog
from ...game import extra_texts as words
from ...game.keys import KEY_ENTER
from ...game.spoken_menu import Item, ListPicker, SpokenMenu
from ..nfl_rules import is_nfl
from .. import nx_texts as X
from . import data as D
from . import history, honors_flow, market_flow, mode, news, signings_flow, staff_flow, todo, trade_flow, weekly
from .league import team_ref

ROSTER_ORDER = D.ROSTER_ORDER
HELP_LINES = {"116": ("NXH-34",), "117": ("NXH-35", "NXH-37", "NXH-39", "NXH-40", "NXH-41", "NXH-42", "NXH-43", "NXH-44", "NXH-45", "NXH-46", "NXH-72", "NXH-74",
                "NXH-76", "NXH-77", "NXH-78"),
              "118": ("NXH-36", "NXH-38", "NXH-73")}   # F5, F6 and F7 (H12, while the franchise is in use)
PICKS_TOLD = ("first", "mine", "all")                          # nx_fr_picks_told: which picks of the draft are told (design 7.3)
PICKS_TOLD_TEXT = {"first": "NXF-22", "mine": "NXF-25", "all": "NXF-26"}


class _Closed(Exception):
    """An action that ends the menu (a switch was asked for): F9's root goes on, the menu below it is closed."""


class _Answered(Exception):
    """An answer of the to-do list was taken: the menu of the item ends."""


def help_lines(key: str) -> list:
    """The Franchise's lines added to the help of F5, F6 and F7 (design 14: NXH-34 to NXH-38)."""
    return [X.text(text_id) for text_id in HELP_LINES.get(key, ())]


def franchise_item_shown(g) -> bool:
    """F9 shows the Franchise item with the N. F. L. rules, when the franchise folder can be used (design 11)."""
    if not is_nfl(g.rules):
        return False
    store = g.franchise()
    store.open(g.options.settings.game.nx_season_kind == "franchise")
    mode._settle_open(g, store)
    return store.available and not store.creating


def _words(g) -> history.Words:
    return history.Words(lambda team: g.league.team(*team_ref(team)))


def _lines_picker(speech, keys, title: str, lines: list, on_enter=None) -> None:
    """A list to hear; `on_enter(index)` (SX.8m: the roster's renaming) acts on Enter and returns the sentence to say, the list stays."""
    if not lines:
        speech.stop()
        speech.say_async(X.text("NXG-18"))
        return
    ListPicker(speech, keys, title, len(lines), lambda i: lines[i], on_enter=on_enter, close_on_enter=False).run()


def _lineup_choices(league, item) -> list:
    from . import injury_flow
    return injury_flow.lineup_choices(league, item)


def roster_line(words, league, player) -> str:
    """A player of the player's team in F9's roster: his line with his contract (NXL-33), then his tag, morale and word (SX.8n, NXU-T05 or NXU-T06)."""
    from . import people_flow
    return words.player_with_contract(player) + people_flow.roster_words(words, league, player)


def franchise_menu(g, speech, keys) -> None:
    store = g.franchise()
    in_use = g.franchise_in_use
    settings = g.options.settings.game

    # ----- the to-do list (design 8.1, 11) -----

    def ask_in_menu(item: dict) -> bool:
        """One item as an F9 menu (the F9 classes read keys without the global keys, design 3.7): False when Escape left it."""
        league = store.league
        if item["kind"] == D.TODO_EXTRA_WORK and not todo.valid_players(league, item):
            league.todo.remove(item)
            store.save()
            return True
        if item["kind"] == D.TODO_LINEUP and not _lineup_choices(league, item):
            league.todo.remove(item)                # D-143: he plays after all, or nobody else is fit
            store.save()
            return True
        situation, answers = weekly.item_view(g, league, item)
        own = todo.answer_count(league, item)
        taken: list = []

        def take(index: int):
            taken.append(index)
            raise _Answered()

        items = [Item(lambda text=text: text.strip(), enter=lambda index=index: take(index)) for index, text in enumerate(answers)]
        try:
            SpokenMenu(speech, keys, " ".join(part.strip() for part in situation), items, space_enters=True,
                       digits_jump=True).run()
        except _Answered:
            pass
        if not taken:
            return False
        done, text = weekly.finish_item(store, league, item, taken[0], own)
        if text:
            speech.stop()
            speech.say_async(text)
        return True

    def todo_menu():
        league = store.league
        if g.play_engine is not None or not weekly.in_regular_season(league) or not todo.waiting(league):
            return X.text("NXD-07")            # inside a game the deadline has passed: the list is closed
        for item in list(todo.waiting(league)):
            if item in league.todo and not ask_in_menu(item):
                return None
        return X.text("NXD-07") if not todo.waiting(league) else None

    # ----- the injury report (SX.8k, INJ-4): the player's hurt players; Enter on a doubtful or questionable one changes whether he plays -----

    def injury_menu():
        from . import injuries, injury_flow
        league = store.league
        week = league.gtp
        staff = bool(settings.nx_fr_auto)
        rows = injury_flow.list_lines(_words(g), league, week, staff)
        if not rows:
            return X.text("NXI-53")

        def choose_starter(pid: int):
            """D-143 (NX-B1): who starts in place of `pid`, the staff's choice first; the choice is written, then said."""
            if g.play_engine is not None or not weekly.in_regular_season(league):
                return X.text("NXI-54")
            if staff:
                return X.text("NXI-55")
            choices = injuries.cover_choices(league, pid, week)
            if not choices:
                return X.text("NXI-64")
            words = _words(g)
            names = [injury_flow.choice_text(words, choice, index == 0) for index, choice in enumerate(choices)]
            picked = ListPicker(speech, keys, X.text("NXI-63", player=league.players[pid].name), len(names), lambda i: names[i]).run()
            if picked is None:
                return None
            injuries.choose(league, pid, None if picked == 0 else choices[picked].id)
            for item in [i for i in league.todo if i["kind"] == D.TODO_LINEUP and i["player"] == pid]:
                league.todo.remove(item)           # the question about his place is answered
            debuglog.event("franchise", "lineup_chosen", week=week, player=pid, starts=choices[picked].id, staff=picked == 0, where="F9")   # rule 0.15
            store.save()                           # written, then told (B-X53)
            rows[:] = injury_flow.list_lines(_words(g), league, week, staff)
            return injury_flow.starts_text(league, pid, choices[picked])

        def enter(index: int):
            pid = rows[index][1]
            if pid is None:
                return None
            if isinstance(pid, tuple):             # D-143: the row "who starts for <player>"
                return choose_starter(pid[1])
            if g.play_engine is not None or not weekly.in_regular_season(league):
                return X.text("NXI-54")            # the kick-off has passed: the lineup is the game's
            if staff:
                return X.text("NXI-55")            # the staff handles it: its rule decides at the kick-off (the review of SX.8k)
            player = league.players[pid]
            play = not injuries.plays(league, player, week, False)
            injuries.decide(league, pid, week, play)
            for item in [i for i in league.todo if i["kind"] == D.TODO_INJURY and i["player"] == pid]:
                league.todo.remove(item)           # the question about him is answered
            store.save()
            rows[:] = injury_flow.list_lines(_words(g), league, week, staff)     # with the staff setting on, the staff's rule stands at the kick-off
            return injury_flow.result_text(league, pid, play)

        ListPicker(speech, keys, X.text("NXF-44"), len(rows), lambda i: rows[i][0], on_enter=enter, close_on_enter=False).run()
        return None

    # ----- the news (design 8.3, 11) -----

    def news_menu():
        league = store.league
        shown = [(entry, weekly.plain_text(entry["markup"])) for entry in news.newest_first(league)]
        shown = [(entry, text) for entry, text in shown if text]
        if not shown:
            return X.text("NXN-02")
        first = (shown[0][0]["season"], shown[0][0]["week"])
        latest = [text for entry, text in shown if (entry["season"], entry["week"]) == first]
        earlier = []                                 # the earlier weeks, newest first, each with its heading (design 8.3)
        heading = first
        for entry, text in shown:
            key = (entry["season"], entry["week"])
            if key == first:
                continue
            if key != heading:
                heading = key
                earlier.append(X.text("NXN-03") if key[1] == D.NEWS_OFFSEASON else X.text("NXN-05", n=key[1]))
            earlier.append(text)
        title = X.text("NXN-03" if first[1] == D.NEWS_OFFSEASON else "NXN-01").strip().rstrip(".")
        items = [Item(lambda: title, enter=lambda: _lines_picker(speech, keys, title, latest))]
        if earlier:
            items.append(Item(lambda: X.text("NXN-04"), enter=lambda: _lines_picker(speech, keys, X.text("NXN-04"), earlier)))
        SpokenMenu(speech, keys, X.text("NXF-12"), items, space_enters=True, digits_jump=True).run()
        return None

    # ----- the roster -----

    def rookies_of(position: str) -> list:
        """The player's rookies of one group who wait for the cut (stages 4 and 5)."""
        league = store.league
        return [r for r in league.waiting_rookies(league.team) if r.pos == position]

    def group_picker(position: str) -> None:
        word = _words(g)
        league = store.league
        players = [p for p in league.group_of(league.team, position) if p is not None]
        lines = [roster_line(word, league, p) for p in players]      # SX.8b: the rating and the potential are spoken; SX.8g: and the contract; SX.8n: the tag, morale, word
        rookies = rookies_of(position)
        for rookie in rookies:                                 # a rookie is told by his range until the cut (design 7.6, 11)
            if league.draft is not None:                       # the draft record lives until the cut is applied (stage 5)
                low, high = league.rookie_range(rookie)
                lines.append(word.prospect_line(rookie.name, rookie.pos, low, high, rookie.age, rookie.potential))
            else:
                lines.append(word.player(rookie))
        everyone = players + rookies

        def enter(index: int):                                 # SX.8m: Enter renames the player, with the original's typed prompt
            from . import rename
            player = everyone[index]
            text = rename.ask(g, speech, keys, store, player)
            if index < len(players):
                lines[index] = roster_line(word, league, player)
            return text

        _lines_picker(speech, keys, word.group(position), lines, on_enter=enter)

    def roster_menu() -> None:
        word = _words(g)
        league = store.league

        def count(position: str) -> int:               # the players in the group now: fewer than its places while places are empty
            return (sum(1 for player in league.group_of(league.team, position) if player is not None)
                    + len(rookies_of(position)))
        items = [Item(lambda position=position: X.text("NXL-30", group=word.group(position), n=count(position)),
                      enter=lambda position=position: group_picker(position)) for position in ROSTER_ORDER]
        SpokenMenu(speech, keys, X.text("NXF-13"), items, space_enters=True, digits_jump=True).run()

    # ----- the history -----

    def history_menu() -> None:
        league = store.league
        word = _words(g)
        sections = [("NXG-01", lambda: history.champions_lines(league, word)),
                    ("NXG-02", lambda: [history.record_line(league)] if league.history else []),
                    ("NXG-03", lambda: history.season_lines(league, word)),
                    ("NXG-04", lambda: history.record_lines(league, word)),
                    ("NXG-05", lambda: history.retired_lines(league, word)),
                    ("NXG-06", lambda: honors_flow.award_lines(league, word)),       # SX.8o
                    ("NXG-07", lambda: honors_flow.hall_lines(league, word))]
        items = [Item(lambda text_id=text_id: X.text(text_id),
                      enter=lambda text_id=text_id, make=make: _lines_picker(speech, keys, X.text(text_id), make()))
                 for text_id, make in sections]
        SpokenMenu(speech, keys, X.text("NXF-14"), items, space_enters=True, digits_jump=True).run()

    # ----- the team ratings (design 11, NXF-15) -----

    def ratings_menu() -> None:
        league = store.league
        title = X.text("NXL-41", k=league.rank_of(league.team)).strip().rstrip(".")
        _lines_picker(speech, keys, title, history.team_rating_lines(league, _words(g)))

    # ----- the salary cap (design 17 SX.8g, NXF-28) -----

    def cap_menu() -> None:
        league = store.league
        _lines_picker(speech, keys, X.text("NXF-28"), history.cap_lines(league, _words(g)))

    # ----- the free agents (design 17 SX.8i, NXF-29) -----

    def market_menu() -> None:
        league = store.league
        if league.market is not None:                  # the stage of free agency is in progress: its list (the offers are the stage's questions)
            _lines_picker(speech, keys, X.text("NXF-29"), market_flow.market_lines(league, _words(g)))
            return
        signings_flow.free_agents_menu(g, speech, keys, store, _words(g))      # SZ.8: in the regular season the player signs free agents here

    # ----- the trades (design 17 SX.8j, NXF-43) -----

    def trades_menu() -> None:
        trade_flow.trades_menu(g, speech, keys, store, _words(g), ask_in_menu)

    # ----- the practice squad (D-136, NXF-47) -----

    def practice_menu() -> None:
        from .practice_flow import practice_menu as run
        run(g, speech, keys, store, store.words)

    # ----- your job and staff (design 17 SX.8l, NXF-45) -----

    def job_menu() -> None:
        _lines_picker(speech, keys, X.text("NXF-45"), staff_flow.job_lines(store.league))

    # ----- the settings -----

    def settings_menu() -> None:
        def offseason_label() -> str:
            return X.text("NXF-21") if settings.nx_fr_offseason == "full" else X.text("NXF-24")

        def toggle(step: int = 1) -> None:
            settings.nx_fr_offseason = "short" if settings.nx_fr_offseason == "full" else "full"
            g.options.save()

        def picks_label() -> str:
            return X.text(PICKS_TOLD_TEXT[settings.nx_fr_picks_told])

        def cycle(step: int = 1) -> None:
            at = PICKS_TOLD.index(settings.nx_fr_picks_told) if settings.nx_fr_picks_told in PICKS_TOLD else 0
            settings.nx_fr_picks_told = PICKS_TOLD[(at + step) % len(PICKS_TOLD)]
            g.options.save()

        def auto_label() -> str:
            return X.text("NXF-20") + "," + X.text("NXM-20" if settings.nx_fr_auto else "NXM-21")

        def flip(step: int = 1) -> None:
            settings.nx_fr_auto = not settings.nx_fr_auto
            g.options.save()

        items = [Item(auto_label, enter=lambda: (flip(), auto_label())[1], change=flip),
                 Item(offseason_label, enter=lambda: (toggle(), offseason_label())[1], change=toggle),
                 Item(picks_label, enter=lambda: (cycle(), picks_label())[1], change=cycle)]
        SpokenMenu(speech, keys, X.text("NXF-16"), items, space_enters=True, digits_jump=True).run()

    # ----- the latest N. F. L. calendar (D-128, NXF-48) -----

    def latest_calendar():
        from . import calendar_flow
        return calendar_flow.run(g, speech, keys, store if store.exists else None)

    # ----- between the kinds of season (design 3.5) -----

    def confirmed(text_id: str) -> bool:
        speech.stop()
        speech.say_async(X.text(text_id))
        return keys.read_key() == KEY_ENTER

    def ask_switch(kind: str, confirm_id: str | None):
        def act():
            if confirm_id is not None and not confirmed(confirm_id):
                return words.NOTHING_CHANGED
            if store.exists:
                mode.set_kind(g, kind)                   # a franchise to be made sets the kind when the league exists
            g.program.request_switch(kind)
            raise _Closed()
        return act

    if in_use:
        items = [Item(lambda: X.text("NXF-11"), enter=todo_menu),
                 Item(lambda: X.text("NXF-12"), enter=news_menu),
                 Item(lambda: X.text("NXF-13"), enter=roster_menu),
                 Item(lambda: X.text("NXF-14"), enter=history_menu),
                 Item(lambda: X.text("NXF-15"), enter=ratings_menu),
                 Item(lambda: X.text("NXF-28"), enter=cap_menu),
                 Item(lambda: X.text("NXF-29"), enter=market_menu),
                 Item(lambda: X.text("NXF-43"), enter=trades_menu),
                 Item(lambda: X.text("NXF-44"), enter=injury_menu),
                 Item(lambda: X.text("NXF-47"), enter=practice_menu),
                 Item(lambda: X.text("NXF-45"), enter=job_menu),
                 Item(lambda: X.text("NXF-16"), enter=settings_menu),
                 Item(lambda: X.text("NXF-17"), enter=ask_switch("classic", "NXF-23"))]
    elif store.exists:
        items = [Item(lambda: X.text("NXF-18"), enter=ask_switch("franchise", None)),
                 Item(lambda: X.text("NXF-14"), enter=history_menu)]
    else:
        items = [Item(lambda: X.text("NXF-19"), enter=ask_switch("franchise", "NXF-27"))]
    items.append(Item(lambda: X.text("NXF-48"), enter=latest_calendar))      # D-128: the last item in every case (only when the player asks)
    try:
        SpokenMenu(speech, keys, X.text("NXF-10"), items, space_enters=True, digits_jump=True).run()
    except _Closed:
        speech.stop()
