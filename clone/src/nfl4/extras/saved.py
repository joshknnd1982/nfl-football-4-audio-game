"""Which rules a loaded saved game is played with (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 12.3, C1, C10). This is inspired by Jim Kitchen.

football.sav (data/files/savedgame.py) holds the extras of a game played with the N. F. L. rules after the original's
values. Before such a game is loaded:
* no extras section (a Classic save): the program's rules as they are; with the N. F. L. rules the extras start from their
  start values (ExtrasRecord.load_saved);
* an extras section and the program's rules are the N. F. L. rules: they are used, with the save's own record;
* an extras section and the program's rules are Classic: asked once, " this saved game was played with the N. F. L. rules.
  do you wish to play it with those rules? ", answer yes first; yes plays this game with the N. F. L. rules (the setting
  stays Classic), no plays it as Classic and drops the extras;
* a section whose record cannot be read: as above, and when the N. F. L. rules are used, one sentence says the extras start
  fresh (" the saved rules could not be read. the game goes on with fresh time outs and a fresh clock. ").
"""
from __future__ import annotations

import logging

from ..game import prompt_texts as T
from ..game.rules import CLASSIC
from . import nx_texts as X
from .nfl_rules import NflRules, is_nfl
from .state import ExtrasRecord

KEY_ENTER, KEY_TAB, KEY_UP, KEY_DOWN, KEY_F1 = "13", "9", "38", "40", "112"


def record_usable(text: str | None) -> bool:
    if text is None:
        return False
    try:
        ExtrasRecord.from_json(text)
    except ValueError as exc:
        logging.getLogger("nfl4.extras").warning("the extras record of a saved game is not usable (%s)", exc)
        return False
    return True


def ask_yes_no(game, question: str) -> bool:
    """C9's question: the question (say5), then the answer (say5, yes first); Up, Down or Tab change it, y and n set it,
    Enter takes it, F1 asks again, any other key is echoed and the question is asked again with the answer kept."""
    keys = game.keys
    answer = True
    while True:
        keys.clk()
        game.say5(question)
        while True:
            game.say5(T.YES if answer else T.NO)
            keys.getkey(game.speech)
            code = keys.code_text
            if code == KEY_ENTER:
                return answer
            if code in (KEY_UP, KEY_DOWN, KEY_TAB):
                answer = not answer
                continue
            if code == KEY_F1:
                break
            game.saykey()
            if keys.char in ("y", "n"):
                answer = keys.char == "y"
                continue
            break


def rules_for_saved_game(game, saved):
    """None: play with the program's rules. Else the rules to play this loaded game with."""
    if saved is None or not getattr(saved, "extras_marked", False):
        return None
    usable = record_usable(saved.extras)
    if is_nfl(game.rules):
        if not usable:
            game.say5(X.text("NXM-25"))
        return None
    if not ask_yes_no(game, X.text("NXM-24")):
        return CLASSIC
    if not usable:
        game.say5(X.text("NXM-25"))
    settings = game.options.settings.game
    return NflRules(timeouts_on=settings.nx_timeouts, penalties_on=getattr(settings, "nx_penalties", True),
                    onside_on=getattr(settings, "nx_onside", True),
                    onside_always=getattr(settings, "nx_onside_question", "always") == "always",
                    qb_on=getattr(settings, "nx_qb_runs", True),
                    challenges_on=getattr(settings, "nx_challenges", True),
                    offense_book=getattr(settings, "nx_offense_playbook", "classic"),
                    defense_book=getattr(settings, "nx_defense_playbook", "classic"), playbooks_on=True)
