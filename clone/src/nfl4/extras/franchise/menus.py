"""F9's Franchise item: your roster, the league history, the franchise settings, and the way between a classic season and a
franchise (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 11 and 3.7. These are settings menus, so they use the F9 classes (`SpokenMenu`, `ListPicker`) with their keys
as they are; the questions inside the program's flow use `FranchiseQuestion`. The item is shown only with the N. F. L. rules and is
built each time F9 opens (`franchise_item_shown`), so with Rules = Classic F9's list is exactly the original's and no franchise
file is opened. SX.8a builds: the roster, league history, franchise settings (offseason only: the other settings come with their
features), play classic seasons, back to your franchise and start a franchise now. SX.8b speaks the ratings and the potential in
the roster and adds the team ratings; SX.8e adds the to-do list and the news.
"""
from __future__ import annotations

from ...game import extra_texts as words
from ...game.keys import KEY_ENTER
from ...game.spoken_menu import Item, ListPicker, SpokenMenu
from ..nfl_rules import is_nfl
from .. import nx_texts as X
from . import data as D
from . import history, mode
from .league import team_ref

ROSTER_ORDER = ("QB", "RB", "WR", "DL", "LB", "CB", "S", "RET", "K", "P")


class _Closed(Exception):
    """An action that ends the menu (a switch was asked for): F9's root goes on, the menu below it is closed."""


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


def _lines_picker(speech, keys, title: str, lines: list) -> None:
    if not lines:
        speech.stop()
        speech.say_async(X.text("NXG-18"))
        return
    ListPicker(speech, keys, title, len(lines), lambda i: lines[i], close_on_enter=False).run()


def franchise_menu(g, speech, keys) -> None:
    store = g.franchise()
    in_use = g.franchise_in_use
    settings = g.options.settings.game

    # ----- the roster -----

    def group_picker(position: str) -> None:
        word = _words(g)
        league = store.league
        players = [p for p in league.group_of(league.team, position) if p is not None]
        lines = [word.player(p) for p in players]              # SX.8b: the rating and the potential are spoken
        _lines_picker(speech, keys, word.group(position), lines)

    def roster_menu() -> None:
        word = _words(g)
        items = [Item(lambda position=position: X.text("NXL-30", group=word.group(position), n=D.GROUP_SIZE[position]),
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
                    ("NXG-05", lambda: history.retired_lines(league, word))]
        items = [Item(lambda text_id=text_id: X.text(text_id),
                      enter=lambda text_id=text_id, make=make: _lines_picker(speech, keys, X.text(text_id), make()))
                 for text_id, make in sections]
        SpokenMenu(speech, keys, X.text("NXF-14"), items, space_enters=True, digits_jump=True).run()

    # ----- the team ratings (design 11, NXF-15) -----

    def ratings_menu() -> None:
        league = store.league
        title = X.text("NXL-41", k=league.rank_of(league.team)).strip().rstrip(".")
        _lines_picker(speech, keys, title, history.team_rating_lines(league, _words(g)))

    # ----- the settings -----

    def settings_menu() -> None:
        def offseason_label() -> str:
            return X.text("NXF-21") if settings.nx_fr_offseason == "full" else X.text("NXF-24")

        def toggle(step: int = 1) -> None:
            settings.nx_fr_offseason = "short" if settings.nx_fr_offseason == "full" else "full"
            g.options.save()

        items = [Item(offseason_label, enter=lambda: (toggle(), offseason_label())[1], change=toggle)]
        SpokenMenu(speech, keys, X.text("NXF-16"), items, space_enters=True, digits_jump=True).run()

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
        items = [Item(lambda: X.text("NXF-13"), enter=roster_menu),
                 Item(lambda: X.text("NXF-14"), enter=history_menu),
                 Item(lambda: X.text("NXF-15"), enter=ratings_menu),
                 Item(lambda: X.text("NXF-16"), enter=settings_menu),
                 Item(lambda: X.text("NXF-17"), enter=ask_switch("classic", "NXF-23"))]
    elif store.exists:
        items = [Item(lambda: X.text("NXF-18"), enter=ask_switch("franchise", None)),
                 Item(lambda: X.text("NXF-14"), enter=history_menu)]
    else:
        items = [Item(lambda: X.text("NXF-19"), enter=ask_switch("franchise", "NXF-27"))]
    try:
        SpokenMenu(speech, keys, X.text("NXF-10"), items, space_enters=True, digits_jump=True).run()
    except _Closed:
        speech.stop()
