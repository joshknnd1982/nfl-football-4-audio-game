"""The Rules object of the N. F. L. rules mode (nfl4 only, rule 0.13; hook H6). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 3, 5 and 6.3. ClassicRules (game/rules.py) answers every hook with the original's behavior; NflRules
answers the hooks of the features that are built. SX.2: the real clock (C2) and the timeouts (NX1):

    H1  period_clock      the clock in seconds (extras/clock.py), its record in state.extras (H5, extras/state.py)
    H2  after_tackle      a run or a catch that ends in the field of play may go out of bounds (one draw, design 5.2)
        after_outcome     the play's live time L runs (design 5.1)
    H3  offense_menu, defense_menu   Time Out (letter T) and Save Game (letter S) at the end of the play menus
        menu_action       the player's timeout from the menu (granted, or refused with a sentence)
    H4  before_kickoff    the timeouts of a new half or overtime period are said; a score as time ran out in the second
                          or fourth quarter ends the period before the kick-off
    H10 between_plays     the runoff R kept pending, the warning when R crosses 2:00, the computer's timeouts, the
                          clock-running warning before the menu (design 5.5, C9)
    H11 extra_stats_lines " Time Outs Used" after " Points Scored"
    H12 extra_help        the added lines of F5, F6 and F7 (C6)
    H13 extra_situation   F1: whether the clock runs, and the timeouts left

The order of the new draws inside a play (design 15, as built): out of bounds (after the tackle sentence), L (at the
narration end point), then between plays R, the ready-signal cut, and for each side in turn (the side with the ball first)
rule 6's draw and a timeout's u, its remark chance, its remark line, a name and the line's choices.

One NflRules object is made per game (`for_game`); the program keeps a configured one as Game.rules.
"""
from __future__ import annotations

import logging

from ..game import menus
from ..game import outcome as O
from ..game.gamestate import other
from ..game.rules import NORMAL_KICKOFF, PERIOD_OVER, ClassicRules
from ..game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
from . import nx_texts as X
from . import remarks
from . import timeouts
from . import tuning as T
from .clock import RUNNING_KINDS, NflPeriodClock, late_window
from .state import ExtrasRecord

log = logging.getLogger("nfl4.extras")

TIMEOUT = "timeout"
TIMEOUT_ACTION = (TIMEOUT, 0)
NAME = "N. F. L. rules"
KEY_F5, KEY_F6, KEY_F7 = "116", "117", "118"


def menu_item(position: int, text: str, action: tuple[str, int], letter: str = "") -> menus.MenuItem:
    """An item in the original's spoken form (" 8. Time Out "); its digit is its place."""
    return menus.MenuItem(" %d. %s " % (position, text), position, action, letter)


class NflRules(ClassicRules):
    name = NAME

    def __init__(self, timeouts_on: bool = True, auto_sides: tuple[int, ...] = (2,)):
        # the switch for a new game; a game reads its own from state.extras (a loaded game keeps the switch it was saved
        # with, C1)
        self.timeouts_on = bool(timeouts_on)
        self.auto_sides = tuple(auto_sides)       # the sides whose timeouts the computer decides (the sim: both)
        self.game = None
        self.state = None
        self.clock: NflPeriodClock | None = None

    def for_game(self) -> "NflRules":
        """A fresh object for one game, with the same switches (Game.play_game)."""
        return type(self)(self.timeouts_on, self.auto_sides)

    # ----- H1 -----

    def period_clock(self, game, state) -> NflPeriodClock:
        self.game, self.state = game, state
        state.extras = ExtrasRecord(timeouts_on=self.timeouts_on, postseason=game.season.gtp >= 17)
        self.clock = NflPeriodClock(game, state)
        return self.clock

    @property
    def rnd(self):
        return self.game.rnd

    # ----- H2 -----

    def after_tackle(self, state) -> None:
        """Design 5.2: a run or a completion that ended in the field of play goes out of bounds with the chance of its
        kind; the sentence follows the tackle sentence."""
        x = state.extras
        x.out_of_bounds = False
        if state.two_point or state.result_kind not in (O.RUN, O.PASS_COMPLETE):
            return
        rate = T.OUT_OF_BOUNDS_RUN if state.result_kind == O.RUN else T.OUT_OF_BOUNDS_PASS_COMPLETE
        if self.rnd.below(100) < rate:
            x.out_of_bounds = True
            self.game.say2(X.text("NXC-04"))

    def after_outcome(self, state, outcome):
        x = state.extras
        x.plays += 1
        x.running = False                          # the play is over: H10 decides whether the clock runs to the next snap
        x.pending = 0
        x.last_kind = outcome.kind
        x.last_offense = outcome.offense
        x.last_two_point = bool(outcome.two_point_try)
        self.clock.play_time(outcome, self.rnd)
        return outcome

    # ----- H3 -----

    def offense_menu(self, state, two_point_try: bool) -> list[menus.MenuItem]:
        if two_point_try:
            return menus.offense_menu(True)                    # the try is untimed: the original's items 1 to 5
        items = [menu_item(n, text.strip()[3:], (menus.PLAY, n)) for n, text in enumerate(OFFENSE_ITEMS[:7], start=1)]
        return self._tail(state, items)

    def defense_menu(self, state) -> list[menus.MenuItem]:
        items = [menu_item(n, text.strip()[3:], (menus.PLAY, n)) for n, text in enumerate(DEFENSE_ITEMS[:6], start=1)]
        return self._tail(state, items)

    def _tail(self, state, items: list[menus.MenuItem]) -> list[menus.MenuItem]:
        """Design 10.4: Time Out (T) when timeouts are on, then Save Game (S) last."""
        if state.extras.timeouts_on:
            items.append(menu_item(len(items) + 1, X.text("NXM-05"), TIMEOUT_ACTION, "t"))
        items.append(menu_item(len(items) + 1, X.text("NXM-06"), (menus.SAVE, 0), "s"))
        return items

    def menu_action(self, state, action: tuple[str, int]) -> bool:
        """An added item was taken with Enter. True: done, the menu starts again; False: refused, the menu stays."""
        if action[0] != TIMEOUT:
            log.warning("unknown menu action %r", action)
            return False
        return self.player_timeout(state)

    # ----- H4 -----

    def before_kickoff(self, state, kicking_side: int) -> str:
        x = state.extras
        x.out_of_bounds = False
        if x.left <= 0 and state.quarter in (2, 4):
            return PERIOD_OVER          # a score as time ran out: the half or the game ends after the try, no kick-off
        if x.timeouts_on and x.announced != x.unit:
            x.announced = x.unit
            text_id = "NXT-06" if x.unit.startswith("H") else ("NXT-14" if x.unit.startswith("OTP") else "NXT-07")
            self.game.say4(X.text(text_id, n=x.timeouts_of(1)))
        return NORMAL_KICKOFF

    # ----- H10 -----

    def between_plays(self, state) -> None:
        x = state.extras
        if x.handled == x.plays:                  # nothing new since the last call (the statistics speak the down again)
            return
        x.handled = x.plays
        keeps = x.last_kind in RUNNING_KINDS and state.wisoff == x.last_offense and not x.last_two_point
        ready = False
        if keeps and x.out_of_bounds:
            if late_window(state.quarter, x.left):
                keeps = False                     # stopped until the snap
            else:
                ready = True                      # stopped, restarted on the ready signal: a shorter runoff
        lead = state.score(state.wisoff) - state.score(other(state.wisoff))
        self.clock.runoff(self.rnd, keeps, ready, lead)
        if x.timeouts_on and x.left > 0:          # at 0:00 the period is over: no timeout can be granted
            for side in (state.wisoff, other(state.wisoff)):
                if side not in self.auto_sides or timeouts.refusal(x, side) is not None:
                    continue
                if timeouts.computer_calls(timeouts.situation(state, x, side), self.rnd):
                    self.grant(state, side)
        if x.running and x.pending >= x.left > 0:
            self.game.say5(X.text("NXC-05") if x.left == 1 else X.text("NXC-03", n=x.left))

    # ----- timeouts -----

    def player_timeout(self, state) -> bool:
        x = state.extras
        why = timeouts.refusal(x, 1)
        if why == "none":
            self.game.say5(X.text("NXT-04"))
            return False
        if why == "called":
            self.game.say5(X.text("NXT-05"))
            return False
        self.grant(state, 1)
        return True

    def grant(self, state, side: int) -> None:
        """A timeout: charged, the clock stopped after u seconds, the whistle (foot11), the announcer, a remark 1 in 3."""
        g, x = self.game, state.extras
        timeouts.charge(x, side)
        self.clock.stop_for_timeout(self.rnd)
        g.sounds.play_tackle(8)                   # foot11, as the original's whistles of the period ends
        left = x.timeouts_of(side)
        g.ptf = 1
        g.say4(X.text("NXT-01", team=state.teams.get(side, "")))
        if side == 1:
            g.say4({0: X.text("NXT-10"), 1: X.text("NXT-12")}.get(left) or X.text("NXT-03", n=left))
        else:
            g.say4({0: X.text("NXT-09"), 1: X.text("NXT-11")}.get(left) or X.text("NXT-02", n=left))
        g.ptf = 0
        if g.comtog == 0 and self.rnd(T.TIMEOUT_REMARK_CHANCE) == 1:
            values = {"<team>": state.teams.get(side, ""), "<coach>": g.season.coach,
                      "<quarterback>": state.quarterbacks.get(side, "")}
            remarks.say_remark(g, state, x, "TO", values)

    # ----- H11, H12, H13 -----

    def extra_stats_lines(self, state) -> list[str]:
        x = state.extras
        if not x.timeouts_on:
            return []
        return [X.text("NXS-03"), "%s %d" % (state.teams.get(1, ""), x.used_of(1)),
                "%s %d" % (state.teams.get(2, ""), x.used_of(2))]

    def extra_situation(self, state) -> list[str]:
        x = state.extras
        lines = [X.text("NXC-01") if x.running else X.text("NXC-02")]
        if x.timeouts_on:
            text_id = "NXT-13" if x.timeouts_of(1) == 1 else "NXT-08"
            lines.append(X.text(text_id, n=x.timeouts_of(1), team=state.teams.get(2, ""), m=x.timeouts_of(2)))
        return lines

    def extra_help(self, key: str) -> list[str]:
        ids = {KEY_F5: ("NXH-02", "NXH-01"), KEY_F6: ("NXH-03", "NXH-04", "NXH-05", "NXH-06"),
               KEY_F7: ("NXH-07", "NXH-08")}.get(key, ())
        timeout_lines = ("NXH-01", "NXH-05", "NXH-07")
        on = self.state.extras.timeouts_on if self.state is not None else self.timeouts_on   # a loaded game's own switch
        return [X.text(i) for i in ids if on or i not in timeout_lines]


def rules_from_settings(game_settings, auto_sides: tuple[int, ...] = (2,)):
    """The program's rules for a Rules setting (design 12.1): Classic, or the N. F. L. rules with their switches."""
    from ..game.rules import CLASSIC
    if getattr(game_settings, "rules", "classic") != "nfl":
        return CLASSIC
    return NflRules(timeouts_on=getattr(game_settings, "nx_timeouts", True), auto_sides=auto_sides)


def is_nfl(rules) -> bool:
    return isinstance(rules, NflRules)
