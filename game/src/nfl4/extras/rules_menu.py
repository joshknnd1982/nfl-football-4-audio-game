"""F9's Rules item: Classic or the N. F. L. rules, and the switches of the features that exist (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 12.1 and 12.2 (NQ7, D-042). The design's menu has ten items; an item is in the menu once its feature is
built (SX.2: 1 Rules, 2 Time outs, then Reset the rules to the defaults last; SX.3 to SX.7 insert theirs before Reset, in the
design's order), so the player never meets a switch that does nothing; SX.3 added Penalties, SX.4 added Onside kicks and
Onside question before it, SX.5 added Quarterback runs after Time outs, SX.6 added Replay challenges after Time outs, SX.7
added Offense playbook and Defense playbook before Reset (1 Rules, 2 Time outs, 3 Replay challenges, 4 Quarterback runs, 5 Onside
kicks, 6 Onside question, 7 Penalties, 8 Offense playbook, 9 Defense playbook, 10 Reset: the design's ten items; SY.1 added Broadcast, the
the color commentator, before Reset: 10 Broadcast; SY.2 added Stadium sounds: 11 Stadium sounds; SZ.1 added Commentator, the name of the color
commentator: 12 Commentator, 13 Reset; BC.3 made 12 the Broadcast crew, the four names of the radio crew, extras/crew_menu.py). Up and
Down move, Enter or Space changes the current item and speaks its new value, Left and Right change it too, the digits go to an item, Escape
leaves (game/spoken_menu.py). A switch says " used with the N. F. L. rules " after its value while Rules is Classic, except Broadcast and
Broadcast crew, which both modes use since BC.3 (D-189). Every change is saved in settings.txt at once and
applies from the next game (" the new rules apply from the next game. "): a game in progress keeps the rules it began with.
S-D (D-193) added How much the crew talks after Broadcast (11; Stadium sounds is 12, Broadcast crew 13): a little, some, a lot (the default)
or the most; Enter goes round, Left and Right go down and up; it applies at once, also in the game being played (" from now on, also in the
game you are playing. "), because the broadcast reads the setting at every line.
RC (D-195; the owner: "Make it an exciting radio broadcast") added Play calls after it (12; Stadium sounds is 13, Broadcast crew 14,
Reset 17): radio style, exciting (the default: every play called like a radio broadcast, extras/radio_calls.py) or plain, the original's
words; Enter, Left and Right switch it; it applies at once, also in the game being played (the caller reads the setting at every sentence).
Rules = N. F. L. rules also makes the program read the extras' files (remarks.txt, CUSTOMIZABLE_CONTENT 13).
"""
from __future__ import annotations

from ..game.spoken_menu import Item, SpokenMenu
from . import crew_menu
from .broadcast import DEFAULT_TALK, next_talk, talk_words
from .radio_calls import DEFAULT_CALLS, RADIO, calls_key, next_calls
from . import depth_flow
from . import nx_texts as X
from . import quarterbacks
from .playbook_data import CLASSIC_KEY, PLAYBOOK_CHOICES, STYLE_BY_KEY, TEAM_KEY

CLASSIC, NFL = "classic", "nfl"
DEFAULTS = {"rules": NFL, "nx_timeouts": True, "nx_penalties": True, "nx_onside": True,
            "nx_onside_question": "always", "nx_onside_question_chosen": False, "nx_qb_runs": True, "nx_challenges": True,    # design 12.1 (NQ2: the N. F. L. rules since SX.9)
            "nx_offense_playbook": TEAM_KEY, "nx_defense_playbook": TEAM_KEY,      # SX.10e (D-095, Q-035): the team's playbook is the default
            "nx_playbook_chosen": False, "nx_broadcast": True, "nx_stadium": True, "nx_crew_talk": DEFAULT_TALK,
            "nx_play_calls": DEFAULT_CALLS}
SWITCHES = ("rules", "nx_timeouts", "nx_challenges", "nx_qb_runs", "nx_penalties", "nx_onside", "nx_onside_question", "nx_onside_question_chosen",
            "nx_offense_playbook", "nx_defense_playbook", "nx_playbook_chosen", "nx_broadcast", "nx_stadium", "nx_crew_talk",
            "nx_play_calls")


def rules_label(game_settings) -> str:
    return X.text("NXM-09") if game_settings.rules == NFL else X.text("NXM-08")


def switch_label(game_settings, name_id: str, value: bool) -> str:
    text = X.text(name_id) + (X.text("NXM-20") if value else X.text("NXM-21"))
    if game_settings.rules != NFL:
        text += X.text("NXM-22")
    return text


def talk_label(game_settings) -> str:
    """S-D (D-193): "How much the crew talks: a lot". Both modes: no " used with the N. F. L. rules "."""
    return X.text("NXM-64") + ": " + talk_words(getattr(game_settings, "nx_crew_talk", DEFAULT_TALK))


def calls_label(game_settings) -> str:
    """RC (D-195): "Play calls: radio style, exciting" or "Play calls: plain, the original's words". Both modes."""
    key = calls_key(getattr(game_settings, "nx_play_calls", DEFAULT_CALLS)) or DEFAULT_CALLS
    return X.text("NXM-70") + ": " + X.text("NXM-71" if key == RADIO else "NXM-72")


def playbook_name(choice: str) -> str:
    """The spoken name of a playbook setting: Classic, the team's own style, or a style."""
    if choice == TEAM_KEY:
        return X.text("NXM-35")
    if choice in STYLE_BY_KEY:
        return X.text(STYLE_BY_KEY[choice].name_id)
    return X.text("NXM-27")


def playbook_label(game_settings, text_id: str, choice: str) -> str:
    text = X.text(text_id) + ": " + playbook_name(choice)
    if game_settings.rules != NFL:
        text += X.text("NXM-22")
    return text


def next_playbook(choice: str, step: int) -> str:
    """The next value in the order Classic, Team playbook, the seven styles (Left and Right go both ways)."""
    index = PLAYBOOK_CHOICES.index(choice) if choice in PLAYBOOK_CHOICES else 0
    return PLAYBOOK_CHOICES[(index + step) % len(PLAYBOOK_CHOICES)]


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

    def toggle_challenges(step: int = 1) -> None:
        settings.nx_challenges = not settings.nx_challenges
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
        settings.nx_onside_question_chosen = True       # the player's own choice: a later read keeps it (D-085)
        apply()

    def toggle_broadcast(step: int = 1) -> None:
        settings.nx_broadcast = not settings.nx_broadcast
        apply()

    def change_talk(step: int = 1) -> None:
        """S-D: the next level; saved at once. The broadcast reads it at every line, so it needs no new rules object."""
        from ..data import debuglog
        settings.nx_crew_talk = next_talk(settings.nx_crew_talk, step)
        options.save()
        debuglog.event("setting", "change", name="nx_crew_talk", value=settings.nx_crew_talk)

    def talk_item() -> str:
        return talk_label(settings)

    def change_calls(step: int = 1) -> None:
        """RC (D-195): radio or plain; saved at once. The radio caller reads it at every sentence, so it needs no new rules object."""
        from ..data import debuglog
        settings.nx_play_calls = next_calls(calls_key(settings.nx_play_calls) or DEFAULT_CALLS)
        options.save()
        debuglog.event("setting", "change", name="nx_play_calls", value=settings.nx_play_calls)

    def calls_item() -> str:
        return calls_label(settings)

    def toggle_stadium(step: int = 1) -> None:
        settings.nx_stadium = not settings.nx_stadium
        apply()

    def change_offense_playbook(step: int = 1) -> None:
        settings.nx_offense_playbook = next_playbook(settings.nx_offense_playbook, step)
        settings.nx_playbook_chosen = True              # SX.10e: the player's own choice, Classic too: a later read keeps it (D-095)
        apply()

    def change_defense_playbook(step: int = 1) -> None:
        settings.nx_defense_playbook = next_playbook(settings.nx_defense_playbook, step)
        settings.nx_playbook_chosen = True
        apply()

    def changed(label) -> str:
        text = label() + X.text("NXM-23")
        if getattr(game, "franchise_in_use", False) and settings.rules != NFL:     # design 3.1: the franchise waits for the N. F. L. rules
            text += X.text("NXF-04")
        return text

    def rules_item() -> str:
        text = rules_label(settings)
        if getattr(game, "franchise_in_use", False) and settings.rules == NFL:    # design 11: said after the value
            text += "." + X.text("NXM-26")
        return text

    def timeouts_item() -> str:
        return switch_label(settings, "NXM-10", settings.nx_timeouts)

    def challenges_item() -> str:
        return switch_label(settings, "NXM-11", settings.nx_challenges)

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

    def stadium_item() -> str:
        return switch_label(settings, "NXM-38", settings.nx_stadium)

    def crew_item() -> str:
        return crew_menu.label(settings)

    def choose_crew() -> str:
        """Enter: the crew's four names (BC.3); the item is said again afterwards, with the sentence about the next game when a name changed."""
        if crew_menu.crew_menu(game, speech, keys, settings, apply):
            return changed(crew_item)
        return crew_item()

    def broadcast_item() -> str:
        """Both modes since BC.3: no " used with the N. F. L. rules "."""
        return X.text("NXM-37") + (X.text("NXM-20") if settings.nx_broadcast else X.text("NXM-21"))

    def offense_playbook_item() -> str:
        return playbook_label(settings, "NXM-17", settings.nx_offense_playbook)

    def defense_playbook_item() -> str:
        return playbook_label(settings, "NXM-18", settings.nx_defense_playbook)

    def reset() -> str:
        before = tuple(getattr(settings, name) for name in SWITCHES)
        for name in SWITCHES:
            setattr(settings, name, DEFAULTS[name])
        text = (rules_item() + ". " + timeouts_item().rstrip() + ". " + challenges_item().rstrip() + ". "
                + qb_runs_item().rstrip() + ". " + onside_item().rstrip() + ". " + question_item().rstrip() + ". "
                + penalties_item().rstrip() + ". " + offense_playbook_item().rstrip() + ". " + defense_playbook_item().rstrip()
                + ". " + broadcast_item().rstrip() + ". " + talk_item() + ". " + calls_item() + ". " + stadium_item())
        if tuple(getattr(settings, name) for name in SWITCHES) == before:
            return text
        apply()
        return text + X.text("NXM-23")

    items = [
        Item(rules_item, enter=lambda: (toggle_rules(), changed(rules_item))[1], change=toggle_rules),
        Item(timeouts_item, enter=lambda: (toggle_timeouts(), changed(timeouts_item))[1], change=toggle_timeouts),
        Item(challenges_item, enter=lambda: (toggle_challenges(), changed(challenges_item))[1], change=toggle_challenges),
        Item(qb_runs_item, enter=lambda: (toggle_qb_runs(), changed(qb_runs_item))[1], change=toggle_qb_runs),
        Item(onside_item, enter=lambda: (toggle_onside(), changed(onside_item))[1], change=toggle_onside),
        Item(question_item, enter=lambda: (toggle_question(), changed(question_item))[1], change=toggle_question),
        Item(penalties_item, enter=lambda: (toggle_penalties(), changed(penalties_item))[1], change=toggle_penalties),
        Item(offense_playbook_item, enter=lambda: (change_offense_playbook(), changed(offense_playbook_item))[1],
             change=change_offense_playbook),
        Item(defense_playbook_item, enter=lambda: (change_defense_playbook(), changed(defense_playbook_item))[1],
             change=change_defense_playbook),
        Item(broadcast_item, enter=lambda: (toggle_broadcast(), changed(broadcast_item))[1], change=toggle_broadcast),
        Item(talk_item, enter=lambda: (change_talk(), talk_item() + "," + X.text("NXM-69"))[1], change=change_talk),     # S-D (D-193)
        Item(calls_item, enter=lambda: (change_calls(), calls_item() + "," + X.text("NXM-69"))[1], change=change_calls),  # RC (D-195)
        Item(stadium_item, enter=lambda: (toggle_stadium(), changed(stadium_item))[1], change=toggle_stadium),
        Item(crew_item, enter=choose_crew),
        Item(lambda: quarterbacks.item_label(settings), enter=lambda: (quarterbacks.quarterbacks_menu(game, speech, keys), None)[1]),    # D-132
        Item(lambda: depth_flow.item_label(settings), enter=lambda: (depth_flow.depth_menu(game, speech, keys), None)[1]),        # NX-D3, NX-D4
        Item(lambda: X.text("NXM-19"), enter=reset),
    ]
    SpokenMenu(speech, keys, X.text("NXM-07"), items, help_text=X.text("NXM-36"), space_enters=True,
               digits_jump=True).run()
