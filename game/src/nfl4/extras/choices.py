"""The player's own choice of a target and of a blitzer (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

SY.4 and SY.5 (the owner's list after the S8.2 playtest, D-104 and D-105). Both are optional and never slow the original's pace: Enter on a play
works as it always did.

* R in the offense menu (a player whose plays are the catalog's) opens a short list: the play picks the receiver (the first item, which Enter
  keeps), the six receivers by name and position, and the first two running backs when the play can throw to one (a screen, a swing, an angle, a
  drag) and the game is not a Franchise game. The choice is for the next snap only. At the snap the engine still draws its random receiver (the
  draws of the game do not move) and the chosen one takes its place; the model throws the pass to a route that suits the kind of player (a back
  runs a swing, a screen, an angle or a drag, a tight end the short and middle routes, a wide receiver the rest).
* L in the defense menu opens the list of the seventeen defenders (the first item, kept by Enter, is a player picked by chance, as it was before).
  When the player's next call is a blitz, the chosen player is the one named on a sack, and the sack is a little likelier when a linebacker or a
  defensive back is the blitzer (8 and 12 percent): the pick of a player who rushes anyway changes nothing.

A Franchise game has no back as a target (its ratings and its injuries know the six receivers only). Without real names there are no positions to
say (the surnames of the original have none): a receiver is a receiver and a defender a defender.
"""
from __future__ import annotations

import logging

from ..data import debuglog
from ..game.rules import MENU_QUIET, MENU_REFRESH, TIMEOUT_GRANTED
from . import nx_texts as X
from .plays import catalog as C
from .plays import model as M

log = logging.getLogger("nfl4.extras")

PREFIX = "pm:"
KEY_ENTER, KEY_ESCAPE, KEY_UP, KEY_DOWN, KEY_HOME, KEY_END = "13", "27", "38", "40", "36", "35"
KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
PASS_KINDS = ("pass", "screen", "play_action", "boot", "hail_mary", "trick_pass", "rpo", "max_protect")
RECEIVER_SLOTS = 6
RECEIVER_KINDS = ("WR", "WR", "WR", "TE", "WR", "TE")                  # the receivers of the real names (extras/real_names.py)
BACK_CODES = (7, 8)                                                     # the target codes of the first two running backs
KIND_WORDS = {"WR": "NXB-T06", "TE": "NXB-T07", "RB": "NXB-T08", "": "NXB-T09"}
DEFENDER_KINDS = ("DL",) * 6 + ("LB",) * 5 + ("DB",) * 4 + ("DB",) * 2
DEFENDER_WORDS = ("NXB-T15",) * 6 + ("NXB-T16",) * 5 + ("NXB-T17",) * 4 + ("NXB-T18",) * 2


class Choices:
    def __init__(self, rules):
        self.rules = rules
        self.target = 0           # 0: none; 1 to 6 a receiver; 7 and 8 a running back: for the next snap
        self.used_kind = ""       # the kind of the target used at this snap ("WR", "TE", "RB", "" none or unknown)
        self.blitzer = 0          # 0: none; 1 to 17 a defender: for the next blitz of the player's defense

    def clear(self) -> None:
        self.target = self.blitzer = 0
        self.used_kind = ""

    # ----- what the game knows -----

    @property
    def game(self):
        return self.rules.game

    def franchise(self) -> bool:
        """The game is a game of a franchise season (its ratings and injuries know the six receivers only)."""
        return self.rules.game_injuries() is not None

    def real(self) -> bool:
        return getattr(self.game, "real_names", None) is not None

    # ----- the engine's calls -----

    def carrier(self, state, drawn: int) -> int:
        """H17: the receiver of this snap. The draw was made; the chosen one replaces it when the player's called play is a pass that can
        be thrown to him."""
        target, self.target = self.target, 0
        self.used_kind = ""
        if not target or state.wisoff != 1:
            return drawn
        concept = C.BY_ID.get(self.rules.offense.called)
        if concept is None or concept.side != "O" or concept.kind not in PASS_KINDS:
            return drawn
        if target in BACK_CODES and not self.has_back_route(concept):
            debuglog.event("extras", "target_ignored", play=concept.id, target=target, why="no route for a back")
            return drawn
        kind = "RB" if target in BACK_CODES else self.receiver_kind(target)
        self.used_kind = kind
        debuglog.event("extras", "target_used", play=concept.id, target=target, kind=kind or None)
        return target

    def receiver_kind(self, target: int) -> str:
        return RECEIVER_KINDS[target - 1] if self.real() and not self.franchise() else ""

    @staticmethod
    def has_back_route(concept: C.Concept) -> bool:
        return bool(concept.params and any(name in M.ROUTE_TARGETS["RB"] for name, _w in concept.params[0]))

    def blitz_active(self, state) -> bool:
        """The player's defense called a blitz and chose who blitzes."""
        if not self.blitzer or state.defense != 1:
            return False
        call = C.BY_ID.get(self.rules.defense.called)
        return bool(call is not None and call.side == "D" and getattr(call.params, "blitz", False))

    def blitzer_kind(self, state) -> str:
        return DEFENDER_KINDS[self.blitzer - 1] if self.blitz_active(state) else ""

    def situation_values(self, state, own: bool) -> dict:
        """The model's inputs that the player's choices make (empty, as ever, when the player chose nothing)."""
        values = {}
        if own and self.used_kind:
            values["target"] = self.used_kind
        kind = self.blitzer_kind(state) if state.wisoff == 2 else ""
        if kind:
            values["blitzer"] = kind
        return values

    def sack_defenders(self, state) -> tuple[int, int]:
        """H24: who is named on a sack: the blitzer the player chose (the second name, if the draw gave him, is the one the draw named first)."""
        if not self.blitz_active(state):
            return state.defender1, state.defender2
        first = self.blitzer
        second = state.defender2 if state.defender2 != first else state.defender1
        return first, second

    # ----- the menus -----

    def receiver_menu(self, state, item):
        """R in the player's offense menu."""
        concept = None
        kind, value = item.action[0][len(PREFIX):], item.action[1]
        if kind in ("call", "again") and value in C.BY_ID and C.BY_ID[value].side == "O":
            concept = C.BY_ID[value]
        g = self.game
        if concept is not None and concept.kind not in PASS_KINDS:
            g.say5(X.text("NXB-T21"))
            return MENU_QUIET
        roster = state.rosters[1]
        rows = []
        listed: set = set()              # SR.4: an empty place of the real roster repeats its cover's name; the list says each man once
        for slot, name in enumerate(roster.receivers[:RECEIVER_SLOTS], start=1):
            if name.casefold() in listed:
                continue
            listed.add(name.casefold())
            rows.append((slot, X.text("NXB-T05", player=name, position=X.text(KIND_WORDS[self.receiver_kind(slot)]))))
        if not self.franchise() and (concept is None or self.has_back_route(concept)):
            for code, name in zip(BACK_CODES, roster.running_backs):
                if name.casefold() in listed:
                    continue
                listed.add(name.casefold())
                rows.append((code, X.text("NXB-T05", player=name, position=X.text(KIND_WORDS["RB"]))))
        chosen = self.choose(state, "NXB-T01", "NXB-T02", rows, self.target)
        if chosen is None:
            return MENU_QUIET
        self.target = chosen
        names = dict(rows)
        if chosen:
            name = roster.receivers[chosen - 1] if chosen <= RECEIVER_SLOTS else roster.running_backs[chosen - RECEIVER_SLOTS - 1]
            g.say5(X.text("NXB-T03", player=name))
        else:
            g.say5(X.text("NXB-T04"))
        debuglog.event("extras", "target_chosen", target=chosen, items=len(names))
        return MENU_REFRESH

    def blitzer_menu(self, state):
        """L in the player's defense menu."""
        g = self.game
        roster = state.rosters[1]
        real = self.real() or self.franchise()
        rows = []
        for slot, name in enumerate(roster.defense[:len(DEFENDER_KINDS)], start=1):
            word = DEFENDER_WORDS[slot - 1] if real else "NXB-T19"
            rows.append((slot, X.text("NXB-T05", player=name, position=X.text(word))))
        chosen = self.choose(state, "NXB-T11", "NXB-T12", rows, self.blitzer)
        if chosen is None:
            return MENU_QUIET
        self.blitzer = chosen
        if chosen:
            g.say5(X.text("NXB-T13", player=roster.defense[chosen - 1]))
        else:
            g.say5(X.text("NXB-T14"))
        debuglog.event("extras", "blitzer_chosen", blitzer=chosen)
        return MENU_REFRESH

    def choose(self, state, prompt_id: str, none_id: str, rows: list, current_code: int):
        """The list in the original's style (as the kick-off menu): the prompt, then the current item; Up and Down move and go around, Home
        and End, a digit chooses, Enter takes it, Escape leaves it as it was; F1 says the prompt again (and takes back a T key, which calls a
        time out here as anywhere: a time out leaves the list); F2 to F4 as in a play menu; any other key is echoed. The first item is the
        choice of none; its code is 0. Returns the chosen code, or None when nothing was chosen."""
        g, keys = self.game, self.game.keys
        items = [(0, X.text(none_id))] + rows
        current = next((i for i, (code, _text) in enumerate(items) if code == current_code), 0)
        prompt = True
        while True:
            if prompt:
                keys.clk()
                g.say5(X.text(prompt_id, coach=g.season.coach))
                prompt = False
            g.say5(" %d. %s " % (current + 1, items[current][1]))
            if g.sounds.play_noise_running():
                g.sounds.stop_play_noise()
            keys.getkey2(g.speech, g.sounds)
            code = keys.code_text
            if code == KEY_ENTER:
                return items[current][0]
            if code == KEY_ESCAPE:
                return None
            if code == KEY_UP:
                current = (current - 1) % len(items)
                continue
            if code == KEY_DOWN:
                current = (current + 1) % len(items)
                continue
            if code == KEY_HOME:
                current = 0
                continue
            if code == KEY_END:
                current = len(items) - 1
                continue
            if code == KEY_F1:
                if keys.take_resumed() == TIMEOUT_GRANTED:
                    return None                          # a time out was called: the play menu goes on from its top
                prompt = True
                continue
            if code == KEY_F2:
                g.inrep()
                prompt = True
                continue
            if code == KEY_F3:
                g.say_score(state.score(1), state.score(2))
                continue
            if code == KEY_F4:
                self.rules.clock.speak()
                continue
            keypad = code.isdigit() and 96 <= int(code) <= 105
            char = keys.char if len(keys.char) == 1 else ""
            digit = int(code) - 96 if keypad else (int(char) if char.isdigit() else -1)
            if 1 <= digit <= len(items):
                current = digit - 1
                continue
            g.saykey()
            prompt = True
