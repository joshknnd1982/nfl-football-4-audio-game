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

SX.3, the penalties (NX7, design 9; extras/penalty_flow.py, extras/penalties.py), when the game's Penalties switch is on:
    H2  before_snap       the draw of a foul before or at the snap; a dead-ball foul answers FOUL_BEFORE_SNAP
        foul_before_snap  that foul: the whistle, the flag, the enforcement; the engine's next step
        instead_of_sack   intentional grounding in place of a sack (1 in 12)
        after_outcome     the fouls of the play (before L), then after L the flag, the choice and the enforcement:
                          `outcome.then` names the engine's next step when a penalty was accepted
    H3  offense_menu      a personal foul on a touchdown enforced on the try: the two-point try from the 1
    H4  before_kickoff    the kick-off's down for the fouls of the kick
    H10 between_plays     the clock after a foul (4-3-2 (e), (g))
    H11, H12              " Penalties" and " Penalty Yardage"; the added help on penalties

SX.4, the onside kicks (NX4, design 8; extras/onside.py), when the game's Onside kicks switch is on:
    H4  before_kickoff    the kind of the kick: the player's question (D-041: only when it makes sense, or always) or the
                          computer's declaration; the yard line of the kick (35, the 20 after a safety, moved back by an
                          accepted foul); a kick made again keeps its kind
        onside_kick       the kick's sentences, sounds and draws up to its result (the engine's step onside_kick)
    H2  after_outcome     the live time of an onside kick 3 to 5 seconds; the statistics (kept, tried); the foul draws of
                          the penalty flow include P24 and P33 for the kind
    H11, H12              " Onside Kicks Tried" and " Onside Kicks Recovered"; the added help on onside kicks

SX.5, the quarterback runs (NX3, design 7; extras/qb_runs.py), when the game's Quarterback runs switch is on:
    H3  offense_menu      8 Quarterback Sneak, 9 Quarterback Keeper, 0 (item 10) Quarterback Draw before Time Out and Save Game
    H8  qb_entry, qb_narrate, qb_slide   the rows (design 7.1), the sentences (pool QB, design 7.2) and the slide (7.3)
    H2  instead_of_sack   the original's sack becomes a scramble with 22 percent (before the grounding draw);
        instead_of_incompletion   the original's incompletion becomes a scramble with 6 percent
        computer_offense  the computer's sneaks, keepers and draws (design 7.4)
        after_tackle      the quarterback's own out-of-bounds chances (sneak never, a slider never)
        after_outcome     the statistics, the scramble's live time (clock.py)
    H11, H12              " Quarterback Runs" and " Quarterback Running Yardage"; the added help on the quarterback's runs

SX.6, replay challenges, booth reviews and the ruling model (NX2, design 6; extras/review.py), when the game's Replay challenges
switch is on:
    H2  after_outcome     the ruling draw of a play with a reviewable aspect (after the fouls of the play were drawn, charged
                          its live time L and told, and no foul took the play away): the hint remark, the replay official's
                          review of a play of his own; a reversal puts the board of the end point and the clock back,
                          `outcome.then` names the engine's step that applies the corrected result (REVIEWED_FIELD,
                          REVIEWED_TOUCHDOWN, REVIEWED_FUMBLE) and the flags that were declined are offered again (N2.7)
    H3  offense_menu, defense_menu   Challenge the Ruling (letter C) before Time Out, only while a challenge is allowed
        menu_action       the player's challenge: the question, the review; a reversal leaves the menu for the step it names
        menu_key          the letter C when the menu has no such item: why the coach may not challenge (NXR-10 to NXR-15)
    H10 between_plays     the computer's flag on the last play, before the runoff; a reversal names the engine's next step
    H11, H12              " Challenges Won" and " Challenges Lost"; the added help on challenges

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
from ..game.playtables import QB_DRAW, QB_KEEPER, QB_SNEAK
from ..game.rules import FOUL_BEFORE_SNAP, GO_ON, NORMAL_KICKOFF, PERIOD_OVER, SCRAMBLE, ClassicRules
from ..game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
from . import nx_texts as X
from . import remarks
from . import rules_2026 as R
from . import timeouts
from . import tuning as T
from .clock import RUNNING_KINDS, NflPeriodClock, late_window
from .onside import OnsideFlow
from .penalty_flow import PenaltyFlow, clock_after_foul
from .playbook_flow import PlaybookFlow
from .qb_runs import QbFlow
from .review import CHALLENGE, CHALLENGE_ACTION, ReviewFlow, capture
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

    def __init__(self, timeouts_on: bool = True, auto_sides: tuple[int, ...] = (2,), penalties_on: bool = False,
                 onside_on: bool = False, onside_always: bool = False, qb_on: bool = False, challenges_on: bool = False,
                 offense_book: str = "classic", defense_book: str = "classic", playbooks_on: bool = False):
        # the switches for a new game; a game reads its own from state.extras (a loaded game keeps the switches it was saved
        # with, C1). penalties_on and onside_on are off unless given: the program's rules come from the settings
        # (rules_from_settings, nx_penalties and nx_onside on by default), and a rules object made by hand (the clock's
        # tests) has no fouls, no onside kicks and no draws for them
        self.timeouts_on = bool(timeouts_on)
        self.penalties_on = bool(penalties_on)
        self.onside_on = bool(onside_on)
        self.onside_always = bool(onside_always)  # the player is asked about an onside kick at every kick-off (design 8.2)
        self.qb_on = bool(qb_on)                  # the quarterback's sneak, keeper, draw and scramble (SX.5, off unless given)
        self.challenges_on = bool(challenges_on)  # the ruling model, booth reviews and challenges (SX.6, off unless given)
        self.auto_sides = tuple(auto_sides)       # the sides whose timeouts, penalty choices and onside kicks the computer decides
        # SX.7, the playbooks: the player's choice for a new game (classic, team or a style key, design 12.1: the F9 items 8 and
        # 9) and whether the computer's side plays the style of its team; a hand-made object has neither (Classic plays)
        self.offense_book = offense_book
        self.defense_book = defense_book
        self.playbooks_on = bool(playbooks_on)
        self.game = None
        self.state = None
        self.clock: NflPeriodClock | None = None
        self.penalty = PenaltyFlow(self)
        self.onside = OnsideFlow(self)
        self.qb = QbFlow(self)
        self.review = ReviewFlow(self)
        self.books = PlaybookFlow(self)
        self.modifiers = self.books.modifiers      # H8: the playbooks' rows (unchanged while no play of a playbook is called)

    def for_game(self) -> "NflRules":
        """A fresh object for one game, with the same switches (Game.play_game)."""
        return type(self)(self.timeouts_on, self.auto_sides, self.penalties_on, self.onside_on, self.onside_always,
                          self.qb_on, self.challenges_on, self.offense_book, self.defense_book, self.playbooks_on)

    # ----- H1 -----

    def period_clock(self, game, state) -> NflPeriodClock:
        self.game, self.state = game, state
        state.extras = ExtrasRecord(timeouts_on=self.timeouts_on, postseason=game.season.gtp >= 17,
                                    penalties_on=self.penalties_on, onside_on=self.onside_on,
                                    onside_always=self.onside_always, qb_on=self.qb_on,
                                    challenges_on=self.challenges_on)
        self.clock = NflPeriodClock(game, state)
        self.books.resolve(game, state)            # SX.7: the playbook of each side's offense and defense
        return self.clock

    @property
    def rnd(self):
        return self.game.rnd

    # ----- H2 -----

    def before_snap(self, state, offense_play: int, defense_play: int) -> str:
        """Step 2: a foul before or at the snap (design 9.1)."""
        self.review.replaying = self.review.clock_held = False    # SX.6: a new play: no corrected end point is still waited for
        if state.extras.penalties_on:
            self.penalty.take_snap(state)
            if self.penalty.at_snap(state, offense_play, defense_play):
                self.books.clear()                  # SX.7: the play is not run, the plays are called again
                return FOUL_BEFORE_SNAP
        self.books.arm(state, offense_play, defense_play)      # SX.7: the plays that were called move the rows (H8)
        return GO_ON

    def foul_before_snap(self, state) -> str:
        return self.penalty.before_snap_foul(state)

    def instead_of_sack(self, state) -> str | None:
        """In place of the sack the original drew: a scramble (design 7.1, SX.5), else intentional grounding (design 9.2 P15,
        the sentence of the throw), else None and the sack stands."""
        if self.qb.scramble_from_sack(state):
            return SCRAMBLE
        if not state.extras.penalties_on or not self.penalty.grounding(state):
            return None
        return X.text("NXP-21", quarterback=state.quarterbacks.get(state.wisoff, ""))

    def instead_of_incompletion(self, state) -> bool:
        """The original's draw gave an incompletion, before the throw sentence: a scramble with 6 percent (design 7.1)."""
        return self.qb.scramble_from_incomplete(state)

    def computer_offense(self, state) -> None:
        playbooks = self.books.in_use(state.extras)
        self.qb.computer_offense(state, self.books.qb_percent(state) if playbooks else 100)
        if playbooks:                              # SX.7: the style's play of the family that was drawn
            self.books.computer_offense(state)

    def computer_defense(self, state) -> None:
        if self.books.in_use(state.extras):
            self.books.computer_defense(state)

    def qb_entry(self, state, scramble: bool = False):
        entry = self.qb.entry(state, scramble)
        return entry if scramble else self.modifiers.qb_run(entry)      # SX.7: a quarterback play's tilt

    def qb_narrate(self, state, entry, defender1: str, defender2: str):
        return self.qb.narrate(state, entry, defender1, defender2)

    def qb_slide(self, state) -> None:
        self.qb.slide(state)

    def after_tackle(self, state) -> None:
        """Design 5.2: a run or a completion that ended in the field of play goes out of bounds with the chance of its
        kind; the sentence follows the tackle sentence."""
        x = state.extras
        x.out_of_bounds = False
        if state.two_point or state.result_kind not in (O.RUN, O.PASS_COMPLETE):
            return
        rate = T.OUT_OF_BOUNDS_RUN if state.result_kind == O.RUN else T.OUT_OF_BOUNDS_PASS_COMPLETE
        if state.qb_run:                           # the quarterback's own chances (design 7.1); a slider is down in bounds
            rate = 0 if state.slid else T.QB_OUT_OF_BOUNDS[state.qb_run]
            if rate == 0:
                return
        if self.rnd.below(100) < rate:
            x.out_of_bounds = True
            self.game.say2(X.text("NXC-04"))

    def after_outcome(self, state, outcome):
        x = state.extras
        replaying, redo = self.review.take_replay() if x.challenges_on else (False, [])   # a play a review corrected (SX.6)
        if not replaying:                          # SX.7: what was called and what came of it (a corrected play is the same call)
            self.books.record(state, outcome)
        self.books.clear()                         # then nothing is called and the menu starts at its top
        board = None
        if x.challenges_on and not replaying:
            self.review.forget()                   # the ruling of an earlier play is gone
            board = capture(state)                 # the board a reversal goes back to: before the bookkeeping below
        left_before = x.left                       # and the clock a reversal goes back to: before the live time
        x.plays += 1
        x.running = False                          # the play is over: H10 decides whether the clock runs to the next snap
        x.pending = 0
        x.last_kind = outcome.kind
        x.last_offense = outcome.offense
        x.last_two_point = bool(outcome.two_point_try)
        self.qb.count(state, outcome)              # before the penalty flow can take the play away (it restores the count)
        facts = None
        if x.penalties_on:
            if not replaying:
                facts = self.penalty.at_end(state, outcome)       # the foul draws come before L (15)
            elif redo:                             # N2.7: the declined flags of the play, offered again: no new foul draw
                facts = self.penalty.redo(state, outcome, redo)
        self.clock.play_time(outcome, self.rnd)
        flags, decisions = [], len(self.penalty.events)
        if x.penalties_on and (not replaying or redo):
            flags = list(self.penalty.flags)       # `settle` clears them: a ruling keeps the ones that were declined
            outcome.then = self.penalty.settle(state, outcome, facts)
        if outcome.then is None:
            if outcome.kind == O.SAFETY_KIND:
                x.safety_kick = True                # the team scored upon kicks next, from its own 20 (11-5-2)
            elif outcome.kind == O.ONSIDE_KICK and outcome.turnover:
                x.onside_recovered[other(outcome.offense) - 1] += 1       # the kicking team kept it (no foul took it away)
            elif board is not None and self.unchanged_by_fouls(decisions):
                # SX.6: the ruling of the play, its hint and the replay official's review. A reversal names the step that
                # applies the corrected result and offers the declined flags again
                outcome.then = self.review.rule(state, outcome, board, left_before, flags)
        return outcome

    def unchanged_by_fouls(self, decisions: int) -> bool:
        """The play is the narrated one after the flow: no foul was accepted, offset or enforced on the try (those take the play
        away or leave a mark that a reversal could not take back); declined and not offered are no mark."""
        return all(e[1] in ("declined", "not offered") for e in self.penalty.events[decisions:])

    # ----- H3 -----

    def offense_menu(self, state, two_point_try: bool) -> list[menus.MenuItem]:
        if two_point_try:
            if self.penalty.try_from_the_one:                  # a personal foul on the touchdown, enforced on the try
                self.penalty.try_from_the_one = False          # (14-2-3): half the distance from the 2
                state.yard_line = 1
            return menus.offense_menu(True)                    # the try is untimed: the original's items 1 to 5
        self.books.offense_id = ""                 # SX.7: a play that was called and not run (the period ended at the snap)
        items = self.books.offense_items(state)    # SX.7: the player's playbook (groups, then plays), None for Classic
        if items is not None:
            return self._tail(state, items)
        items = [menu_item(n, text.strip()[3:], (menus.PLAY, n)) for n, text in enumerate(OFFENSE_ITEMS[:7], start=1)]
        if state.extras.qb_on:                     # design 10.4: 8 sneak, 9 keeper, 0 draw (item 10, digit 0)
            for play, text_id in ((QB_SNEAK, "NXM-01"), (QB_KEEPER, "NXM-02"), (QB_DRAW, "NXM-03")):
                position = len(items) + 1
                item = menu_item(position, X.text(text_id), (menus.PLAY, play))
                items.append(item._replace(digit=position % 10))
        return self._tail(state, items)

    def defense_menu(self, state) -> list[menus.MenuItem]:
        self.books.defense_id = ""
        items = self.books.defense_items(state)
        if items is None:
            items = [menu_item(n, text.strip()[3:], (menus.PLAY, n)) for n, text in enumerate(DEFENSE_ITEMS[:6], start=1)]
        return self._tail(state, items)

    def _tail(self, state, items: list[menus.MenuItem]) -> list[menus.MenuItem]:
        """Design 10.4: Time Out (T) when timeouts are on, then Save Game (S) last."""
        if state.extras.challenges_on and self.review.can_challenge(state, 1):       # SX.6: only while one is allowed
            items.append(menu_item(len(items) + 1, X.text("NXM-04"), CHALLENGE_ACTION, "c"))
        if state.extras.timeouts_on:
            items.append(menu_item(len(items) + 1, X.text("NXM-05"), TIMEOUT_ACTION, "t"))
        items.append(menu_item(len(items) + 1, X.text("NXM-06"), (menus.SAVE, 0), "s"))
        return items

    def menu_action(self, state, action: tuple[str, int]):
        """An added item was taken with Enter. True: done, the menu starts again; False: refused, the menu stays; a
        continuation (a challenge that changed a ruling, SX.6): the menu is left for the step it names."""
        if self.books.owns(action):                # SX.7: a group of the playbook, Back, or a play of it
            return self.books.action(state, action)
        if action[0] == CHALLENGE:
            return self.review.player_challenge(state)
        if action[0] != TIMEOUT:
            log.warning("unknown menu action %r", action)
            return False
        return self.player_timeout(state)

    def menu_back(self, state) -> bool:
        """Backspace or Left: from a group of the playbook back to the groups (SX.7)."""
        return self.books.back(state)

    def menu_key(self, state, letter: str) -> bool:
        """The letter C when the menu has no Challenge the Ruling item: the reason why (NXR-10 to NXR-15), the menu goes on."""
        if letter == "c" and state.extras.challenges_on:
            return self.review.say_refusal(state, 1)
        return False

    # ----- H4 -----

    def before_kickoff(self, state, kicking_side: int) -> str:
        x = state.extras
        x.out_of_bounds = False
        self.books.clear()                         # SX.7: a kick-off is a new play: nothing is called
        self.review.clock_held = False             # SX.6: a kick-off is a new dead-ball period
        if x.left <= 0 and state.quarter in (2, 4):
            # no kick-off is made: nothing of the kick that was to come is left over (a safety kick on the last play of a half,
            # a kick to be made again): the next half starts with a kick-off from the 35
            x.safety_kick = x.kick_again = x.rekick = False
            x.kick_back = 0
            return PERIOD_OVER          # a score as time ran out: the half or the game ends after the try, no kick-off
        if x.timeouts_on and x.announced != x.unit:
            x.announced = x.unit
            text_id = "NXT-06" if x.unit.startswith("H") else ("NXT-14" if x.unit.startswith("OTP") else "NXT-07")
            self.game.say4(X.text(text_id, n=x.timeouts_of(1)))
        if x.penalties_on:
            self.penalty.take_kickoff(state)
        # SX.4: where the kick is made from (6-1-2, 11-5-2: the 35, the 20 after a safety, moved back by an accepted foul
        # on a kick made again, 6-3-1) and whether it is an onside kick
        again, x.kick_again = x.kick_again, False
        if again:                      # moved back by the yards of the foul, never more than half the distance to the goal
            spot = x.kick_from - min(x.kick_back, x.kick_from // 2)      # line (14-2-1), so never to or past it
        else:
            spot = R.SAFETY_KICK_SPOT if x.safety_kick else R.KICKOFF_SPOT
        x.kick_from, x.kick_back, x.safety_kick = spot, 0, False
        if not x.onside_on:
            return NORMAL_KICKOFF
        return self.onside.decide(state, kicking_side, again)

    def onside_kick(self, state) -> str:
        return self.onside.kick(state)

    # ----- H10 -----

    def between_plays(self, state) -> str | None:
        x = state.extras
        self.books.group = None                   # SX.7: the next menu starts at its top
        if x.handled == x.plays:                  # nothing new since the last call (the statistics speak the down again)
            return None
        x.handled = x.plays
        if x.challenges_on:                       # SX.6: the computer's flag on the last play, before the clock goes on
            then = self.review.computer_challenge(state)
            if then is not None:                  # the ruling was reversed: the engine goes on at the step that applies it
                return then
        keeps = x.last_kind in RUNNING_KINDS and state.wisoff == x.last_offense and not x.last_two_point
        ready = False
        if keeps and x.out_of_bounds:
            if late_window(state.quarter, x.left):
                keeps = False                     # stopped until the snap
            else:
                ready = True                      # stopped, restarted on the ready signal: a shorter runoff
        cap = None
        if x.foul_clock:                          # SX.3: after a foul, as if it had not happened, except 4-3-2 (e), (g)
            keeps, ready = clock_after_foul(x, state.quarter, keeps)
            cap = R.RUNOFF_PLAY_CLOCK if x.foul_clock == "runoff" else R.PLAY_CLOCK_AFTER_PENALTY
            x.foul_clock = ""
        if self.review.clock_held:                # SX.6: a time out was called in this dead-ball period before a challenge that
            keeps = ready = False                 # changed the play: the clock stays stopped to the snap
            self.review.clock_held = False
        lead = state.score(state.wisoff) - state.score(other(state.wisoff))
        self.clock.runoff(self.rnd, keeps, ready, lead, cap)
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
        lines = []
        if x.penalties_on:
            lines += self.penalty.stats_lines(state)
        if x.timeouts_on:
            lines += [X.text("NXS-03"), "%s %d" % (state.teams.get(1, ""), x.used_of(1)),
                      "%s %d" % (state.teams.get(2, ""), x.used_of(2))]
        if x.challenges_on:
            lines += self.review.stats_lines(state)
        if x.qb_on:
            lines += self.qb.stats_lines(state)
        if x.onside_on:
            lines += [X.text("NXS-06"), "%s %d" % (state.teams.get(1, ""), x.onside_tried[0]),
                      "%s %d" % (state.teams.get(2, ""), x.onside_tried[1]),
                      X.text("NXS-07"), "%s %d" % (state.teams.get(1, ""), x.onside_recovered[0]),
                      "%s %d" % (state.teams.get(2, ""), x.onside_recovered[1])]
        return lines

    def extra_situation(self, state) -> list[str]:
        x = state.extras
        lines = [X.text("NXC-01") if x.running else X.text("NXC-02")]
        if x.timeouts_on:
            text_id = "NXT-13" if x.timeouts_of(1) == 1 else "NXT-08"
            lines.append(X.text(text_id, n=x.timeouts_of(1), team=state.teams.get(2, ""), m=x.timeouts_of(2)))
        return lines

    def extra_help(self, key: str) -> list[str]:
        ids = {KEY_F5: ("NXH-02", "NXH-01", "NXH-23", "NXH-09", "NXH-14", "NXH-18", "NXH-27"),
               KEY_F6: ("NXH-03", "NXH-04", "NXH-05", "NXH-06", "NXH-24", "NXH-25", "NXH-10", "NXH-11", "NXH-15", "NXH-16",
                        "NXH-19", "NXH-20", "NXH-22", "NXH-28", "NXH-29", "NXH-30"),
               KEY_F7: ("NXH-07", "NXH-08", "NXH-26", "NXH-12", "NXH-13", "NXH-17", "NXH-21", "NXH-31", "NXH-32",
                        "NXH-33")}.get(key, ())
        timeout_lines = ("NXH-01", "NXH-05", "NXH-07")
        challenge_lines = ("NXH-23", "NXH-24", "NXH-25", "NXH-26")
        penalty_lines = ("NXH-09", "NXH-10", "NXH-11", "NXH-12", "NXH-13", "NXH-22")
        onside_lines = ("NXH-14", "NXH-15", "NXH-16", "NXH-17")
        qb_lines = ("NXH-18", "NXH-19", "NXH-20", "NXH-21", "NXH-22")
        playbook_lines = ("NXH-27", "NXH-28", "NXH-29", "NXH-30", "NXH-31", "NXH-32", "NXH-33")
        x = self.state.extras if self.state is not None else None        # a loaded game's own switches
        timeouts_on = x.timeouts_on if x is not None else self.timeouts_on
        challenges_on = x.challenges_on if x is not None else self.challenges_on
        penalties_on = x.penalties_on if x is not None else self.penalties_on
        onside_on = x.onside_on if x is not None else self.onside_on
        qb_on = x.qb_on if x is not None else self.qb_on
        if x is not None:                          # a game's own books; before a game the settings' choice
            playbooks = PlaybookFlow.in_use(x)
        else:
            playbooks = self.playbooks_on or "classic" not in (self.offense_book, self.defense_book)
        return [X.text(i) for i in ids if (timeouts_on or i not in timeout_lines) and (playbooks or i not in playbook_lines)
                and (challenges_on or i not in challenge_lines)
                and (penalties_on or i not in penalty_lines) and (onside_on or i not in onside_lines)
                and (qb_on or i not in qb_lines)]


def rules_from_settings(game_settings, auto_sides: tuple[int, ...] = (2,)):
    """The program's rules for a Rules setting (design 12.1): Classic, or the N. F. L. rules with their switches."""
    from ..game.rules import CLASSIC
    if getattr(game_settings, "rules", "classic") != "nfl":
        return CLASSIC
    return NflRules(timeouts_on=getattr(game_settings, "nx_timeouts", True), auto_sides=auto_sides,
                    penalties_on=getattr(game_settings, "nx_penalties", True),
                    onside_on=getattr(game_settings, "nx_onside", True),
                    onside_always=getattr(game_settings, "nx_onside_question", "sensible") == "always",
                    qb_on=getattr(game_settings, "nx_qb_runs", True),
                    challenges_on=getattr(game_settings, "nx_challenges", True),
                    offense_book=getattr(game_settings, "nx_offense_playbook", "classic"),
                    defense_book=getattr(game_settings, "nx_defense_playbook", "classic"),
                    playbooks_on=True)


def is_nfl(rules) -> bool:
    return isinstance(rules, NflRules)
