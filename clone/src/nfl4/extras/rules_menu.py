"""F9's Rules item: Classic or the N. F. L. rules, and the switches of the features that exist (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 12.1 and 12.2 (NQ7, D-042). The design's menu has ten items; an item is in the menu once its feature is
built (SX.2: 1 Rules, 2 Time outs, then Reset the rules to the defaults last; SX.3 to SX.7 insert theirs before Reset, in the
design's order), so the player never meets a switch that does nothing; SX.3 added Penalties, SX.4 added Onside kicks and
Onside question before it, SX.5 added Quarterback runs after Time outs (1 Rules, 2 Time outs, 3 Quarterback runs, 4 Onside
kicks, 5 Onside question, 6 Penalties, 7 Reset). Up and Down move, Enter or Space changes the current item and speaks its
new value, Left and Right change it too, the digits go to an item, Escape leaves (game/spoken_menu.py). A switch says
" used with the N. F. L. rules " after its value while Rules is Classic. Every change is saved in settings.txt at once and
applies from the next game (" the new rules apply from the next game. "): a game in progress keeps the rules it began with.
Rules = N. F. L. rules also makes the program read the extras' files (remarks.txt, CUSTOMIZABLE_CONTENT 13).
"""
from __future__ import annotations

from ..game.spoken_menu import Item, SpokenMenu
from . import nx_texts as X

CLASSIC, NFL = "classic", "nfl"
DEFAULTS = {"rules": CLASSIC, "nx_timeouts": True, "nx_penalties": True, "nx_onside": True,
            "nx_onside_question": "sensible", "nx_qb_runs": True}    # design 12.1 (NQ2: Classic until SX.9)
SWITCHES = ("rules", "nx_timeouts", "nx_qb_runs", "nx_penalties", "nx_onside", "nx_onside_question")


def rules_label(game_settings) -> str:
    return X.text("NXM-09") if game_settings.rules == NFL else X.text("NXM-08")


def switch_label(game_settings, name_id: str, value: bool) -> str:
    text = X.text(name_id) + (X.text("NXM-20") if value else X.text("NXM-21"))
    if game_settings.rules != NFL:
        text += X.text("NXM-22")
    return text


def rules_menu(game, speech, keys) -> None:
    """The menu itself (F9, Rules). `game` is the Game: its options hold the settings, `apply_rules_setting` takes them."""
    options = game.options
    settings = options.settings.game

    def apply() -> None:
        options.save()
        game.apply_rules_setting()

    def toggle_rules(step: int = 1) -> None:
        settings.rules = CLASSIC if settings.rules == NFL else NFL
        apply()

    def toggle_timeouts(step: int = 1) -> None:
        settings.nx_timeouts = not settings.nx_timeouts
        apply()

    def toggle_qb_runs(step: int = 1) -> None:
        settings.nx_qb_runs = not settings.nx_qb_runs
        apply()

    def toggle_penalties(step: int = 1) -> None:
        settings.nx_penalties = not settings.nx_penalties
        apply()

    def toggle_onside(step: int = 1) -> None:
        settings.nx_onside = not settings.nx_onside
        apply()

    def toggle_question(step: int = 1) -> None:
        settings.nx_onside_question = "sensible" if settings.nx_onside_question == "always" else "always"
        apply()

    def changed(label) -> str:
        return label() + X.text("NXM-23")

    def rules_item() -> str:
        return rules_label(settings)

    def timeouts_item() -> str:
        return switch_label(settings, "NXM-10", settings.nx_timeouts)

    def qb_runs_item() -> str:
        return switch_label(settings, "NXM-12", settings.nx_qb_runs)

    def penalties_item() -> str:
        return switch_label(settings, "NXM-16", settings.nx_penalties)

    def onside_item() -> str:
        return switch_label(settings, "NXM-13", settings.nx_onside)

    def question_item() -> str:
        text = X.text("NXM-15") if settings.nx_onside_question == "always" else X.text("NXM-14")
        if settings.rules != NFL:
            text += X.text("NXM-22")
        return text

    def reset() -> str:
        before = tuple(getattr(settings, name) for name in SWITCHES)
        for name in SWITCHES:
            setattr(settings, name, DEFAULTS[name])
        text = (rules_item() + ". " + timeouts_item().rstrip() + ". " + qb_runs_item().rstrip() + ". "
                + onside_item().rstrip() + ". " + question_item().rstrip() + ". " + penalties_item())
        if tuple(getattr(settings, name) for name in SWITCHES) == before:
            return text
        apply()
        return text + X.text("NXM-23")

    items = [
        Item(rules_item, enter=lambda: (toggle_rules(), changed(rules_item))[1], change=toggle_rules),
        Item(timeouts_item, enter=lambda: (toggle_timeouts(), changed(timeouts_item))[1], change=toggle_timeouts),
        Item(qb_runs_item, enter=lambda: (toggle_qb_runs(), changed(qb_runs_item))[1], change=toggle_qb_runs),
        Item(onside_item, enter=lambda: (toggle_onside(), changed(onside_item))[1], change=toggle_onside),
        Item(question_item, enter=lambda: (toggle_question(), changed(question_item))[1], change=toggle_question),
        Item(penalties_item, enter=lambda: (toggle_penalties(), changed(penalties_item))[1], change=toggle_penalties),
        Item(lambda: X.text("NXM-19"), enter=reset),
    ]
    SpokenMenu(speech, keys, X.text("NXM-07"), items, help_text=X.text("NXM-36"), space_enters=True,
               digits_jump=True).run()
