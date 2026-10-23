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
    H18 timeout_keys, timeout_key, grant_kept_timeout, withdraw_play   the T key (SX.2b, owner rule 0.22): a timeout at once
                          anywhere in a game until the play is run; kept for the end of a live play (below, `timeout_key`)

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

SX.10c, the catalog's offense (NFL_PLAYS_DESIGN 7, D-093; extras/offense_flow.py), when the player's offense playbook is not Classic:
    H3  offense_menu      the catalog's menus (play_menus.PlayMenus): the original's items first, Right to a family's lists,
                          F favourites, A again, M more plays, K kneel and P spike when they help, O formation and tempo
        menu_action, menu_right, menu_back, menu_key, menu_heading   Enter, Right, Left and Backspace, plus and minus, the heading
    H19 model_play        after the snap sentence: the called play's result from the outcome models (game/pag_catalog.py tells it)
        turnover_return   an interception or a lost fumble of that play is returned (G26-8), a fumble may be kept (G26-9)
    H2  after_tackle      the model's own out-of-bounds flag (no draw); after_outcome: the record names the play (the kneel's
                          and the spike's live time), Again remembers it

SX.10d, the catalog's defense and the kicks of 2026 (NFL_PLAYS_DESIGN 2.6, 4.9 and 7, D-094; extras/defense_flow.py, extras/kick_flow.py),
when the player uses a playbook:
    H3  defense_menu      the catalog's defense menus (the original's six calls first, Right to their lists, F, A, M, P Kick Defense on
                          fourth down, O Defensive Personnel and Coverage Shade); the keys go to the flow of the side with the ball
    H19 model_play        the computer's offense play against the player's call, through the same models and telling
    H4  before_kickoff    the 2026 kick-off: the player's kick-off menu or the computer's kick (KICKOFF_2026, or an onside kick)
    H20 special_kick ...  the punts, field goals, extra points, fakes and the fair catch kick of 2026 (game/pag_kicks26.py)
    H10 between_plays     the fair catch kick's question after the player's fair catch late in a half (FAIR_CATCH_KICK)

SX.10e, the computer's calling over the catalog (NFL_PLAYS_DESIGN 7 and 8, D-095; extras/plays/calling.py, extras/playbook_flow.py), in a
game that plays the catalog (the player uses a playbook; the team's playbook is a new player's default since SX.10e):
    H2  computer_offense  a side with a style calls over the whole catalog (no separate quarterback-run draw: the catalog holds them):
                          the try's play, a kneel, a spike, the Hail Mary or the laterals on a last play, or one weighted draw
        computer_defense  the same side's defense call over the whole catalog against a play the models play
    H19 model_play        then the computer's own call against the other side's call (`OffenseFlow.computer_play`)
    H21 computer_goes_for_two   after the computer's touchdown its two-point chart (G26-10); the engine's `computer_try_choice`
    H3  menu_action       Enter on a family of the player's menus is the playbook's pick with the same weights (`PlaybookFlow.pick`)

One NflRules object is made per game (`for_game`); the program keeps a configured one as Game.rules.
"""
from __future__ import annotations

import logging

from ..data import debuglog
from ..game import key_list, menus
from ..game import outcome as O
from ..game.gamestate import other, own_half
from ..game.playtables import QB_DRAW, QB_KEEPER, QB_SNEAK
from ..game.rules import (FAIR_CATCH_KICK, FOUL_BEFORE_SNAP, GO_ON, NORMAL_KICKOFF, OT_COIN_TOSS, OT_KICK_OFF, OT_SAME_BALL, OVERTIME_OVER,
                          PERIOD_OVER, SCRAMBLE, TIMEOUT_GRANTED, TIMEOUT_KEPT, TIMEOUT_REFUSED, ClassicRules)
from ..game.setup import DEFENSE_ITEMS, OFFENSE_ITEMS
from . import kick_flow
from . import nx_texts as X
from . import overtime as OT
from . import remarks
from . import rules_2026 as R
from . import timeouts
from . import tuning as T
from .clock import RUNNING_KINDS, NflPeriodClock, late_window
from .defense_flow import DefenseFlow
from .kick_flow import KickFlow
from .offense_flow import W_FOR, W_NO_BOOK, OffenseFlow, text_for
from .broadcast import Broadcast
from .choices import Choices
from .stadium import Stadium
from .onside import OnsideFlow
from .penalty_flow import PenaltyFlow, clock_after_foul
from .playbook_flow import PlaybookFlow
from .plays import calling, descriptions
from .plays import play_menus as PM
from .qb_runs import QbFlow
from .review import CHALLENGE, CHALLENGE_ACTION, ReviewFlow, capture
from .state import ExtrasRecord

log = logging.getLogger("nfl4.extras")

TIMEOUT = "timeout"
TIMEOUT_ACTION = (TIMEOUT, 0)
NAME = "N. F. L. rules"
KEY_F5, KEY_F6, KEY_F7 = "116", "117", "118"
# SX.10d: the help of the defense menus and the kicks of 2026 (F6), for a player who uses a playbook (their words are F7's,
# descriptions.F7_WORD_ROWS)
MENU_HELP_F6 = ("NXH-56", "NXH-57", "NXH-58", "NXH-62", "NXH-69")     # SX.10e: NXH-62, the computer's calling and its tries for two


def menu_item(position: int, text: str, action: tuple[str, int], letter: str = "") -> menus.MenuItem:
    """An item in the original's spoken form (" 8. Time Out "); its digit is its place."""
    return menus.MenuItem(" %d. %s " % (position, text), position % 10 if position <= 10 else -1, action, letter)


class NflRules(ClassicRules):
    name = NAME

    def __init__(self, timeouts_on: bool = True, auto_sides: tuple[int, ...] = (2,), penalties_on: bool = False,
                 onside_on: bool = False, onside_always: bool = False, qb_on: bool = False, challenges_on: bool = False,
                 offense_book: str = "classic", defense_book: str = "classic", playbooks_on: bool = False,
                 broadcast_on: bool = False, radio_banter: bool = False, stadium_on: bool = False, commentator: str = "Ghip"):
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
        self.timeout_kept = False                 # H18: the T key was pressed while a play was live: granted at the next dead-ball moment
        self.try_due = False                      # SX.13: a touchdown's try is still to be played (a timeout may come before it at 0:00)
        self.after_play = False                   # H18: a play just ended and H10 has not run yet (a timeout then stops the whole runoff)
        # SX.7, the playbooks: the player's choice for a new game (classic, team or a style key, design 12.1: the F9 items 8 and
        # 9) and whether the computer's side plays the style of its team; a hand-made object has neither (Classic plays)
        self.offense_book = offense_book
        self.defense_book = defense_book
        self.playbooks_on = bool(playbooks_on)
        # SY.1 (the radio broadcast, rule 0.27): the radio banter instead of the original's jokes, and Ghip; a hand-made object has neither
        self.broadcast = Broadcast(self, radio_banter=radio_banter, ghip=broadcast_on, commentator=commentator)
        self.stadium = Stadium(self, on=stadium_on)      # SY.2: the crowd, the hits and the chain; a hand-made object has none
        self.choices = Choices(self)                     # SY.4, SY.5: the player's target and blitzer (nothing until he chooses)
        self.game = None
        self.state = None
        self.clock: NflPeriodClock | None = None
        self.penalty = PenaltyFlow(self)
        self.onside = OnsideFlow(self)
        self.qb = QbFlow(self)
        self.review = ReviewFlow(self)
        self.books = PlaybookFlow(self)
        self.offense = OffenseFlow(self)           # SX.10c: the catalog's offense of the player (D-093)
        self.defense = DefenseFlow(self)           # SX.10d: the catalog's defense of the player (D-094)
        self.kicks = KickFlow(self)                # SX.10d: the kicks of 2026 (D-094)
        self.modifiers = self.books.modifiers     # H8: the playbooks' rows (unchanged while no play of a playbook is called)

    def for_game(self) -> "NflRules":
        """A fresh object for one game, with the same switches (Game.play_game)."""
        fresh = type(self)(self.timeouts_on, self.auto_sides, self.penalties_on, self.onside_on, self.onside_always,
                           self.qb_on, self.challenges_on, self.offense_book, self.defense_book, self.playbooks_on,
                           self.broadcast.ghip, self.broadcast.radio_banter, self.stadium.on)
        fresh.broadcast.commentator = self.broadcast.commentator          # SZ.1: the name (set on the object, so a subclass's constructor stays as it is)
        return fresh

    # ----- H1 -----

    def period_clock(self, game, state) -> NflPeriodClock:
        self.game, self.state = game, state
        state.extras = ExtrasRecord(timeouts_on=self.timeouts_on, postseason=game.season.in_playoffs,
                                    penalties_on=self.penalties_on, onside_on=self.onside_on,
                                    onside_always=self.onside_always, qb_on=self.qb_on,
                                    challenges_on=self.challenges_on)
        self.clock = NflPeriodClock(game, state)
        self.broadcast.attach(game, state)         # SY.1: this game's own generator for the broadcast
        self.stadium.attach(game, state)           # SY.2: and for the stadium sounds
        self.modifiers.bind(state)                 # SX.8b: the ratings of the players in the play (a Franchise game's rosters)
        self.books.resolve(game, state)            # SX.7: the playbook of each side's offense and defense
        self.offense.resolve(game, state)          # SX.10c: the player's favourites, the menu at its top
        self.defense.resolve(game, state)          # SX.10d: the defense's menu at its top
        return self.clock

    @property
    def rnd(self):
        return self.game.rnd

    # ----- H2 -----

    def before_snap(self, state, offense_play: int, defense_play: int) -> str:
        """Step 2: a foul before or at the snap (design 9.1)."""
        self.after_play = False
        self.offense.result = None                 # SX.10c: a new play: no catalog result of an earlier play is read again
        self.review.replaying = self.review.clock_held = False    # SX.6: a new play: no corrected end point is still waited for
        if state.extras.penalties_on:
            self.penalty.take_snap(state)
            if self.penalty.at_snap(state, offense_play, defense_play):
                self.books.clear()                  # SX.7: the play is not run, the plays are called again
                self.offense.clear()                # SX.10c: the catalog's call too
                self.defense.clear()                # SX.10d: and the defense's
                return FOUL_BEFORE_SNAP
        self.broadcast.before_snap(state, offense_play)        # SY.1: Ghip, when a team goes for it on fourth down (his own draws)
        self.books.arm(state, offense_play, defense_play)      # SX.7: the plays that were called move the rows (H8)
        return GO_ON

    def foul_before_snap(self, state) -> str:
        return self.penalty.before_snap_foul(state)

    def instead_of_sack(self, state) -> str | None:
        """In place of the sack the original drew: a scramble (design 7.1, SX.5), else intentional grounding (design 9.2 P15,
        the sentence of the throw), else None and the sack stands."""
        if self.qb.scramble_from_sack(state):
            self.offense.drop_result()        # SX.10c: the model's sack is not the play
            return SCRAMBLE
        if not state.extras.penalties_on or not self.penalty.grounding(state):
            return None
        self.offense.drop_result()
        return X.text("NXP-21", quarterback=state.quarterbacks.get(state.wisoff, ""))

    def instead_of_incompletion(self, state) -> bool:
        """The original's draw gave an incompletion, before the throw sentence: a scramble with 6 percent (design 7.1)."""
        if self.qb.scramble_from_incomplete(state):
            self.offense.drop_result()        # SX.10c: the model's incompletion is not the play
            return True
        return False

    def computer_offense(self, state) -> None:
        playbooks = self.books.in_use(state.extras)
        if self.books.catalog_side(state, state.wisoff, "O"):     # SX.10e: the catalog's calling holds the quarterback's runs too
            self.books.computer_offense(state)
            return
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
        model = self.offense.out_of_bounds(state)    # SX.10c: a catalog play's own flag (its route's or its gap's share), no draw
        if model is not None:
            if model and not state.slid:
                x.out_of_bounds = True
                self.game.say2(X.text("NXC-04"))
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
        self.offense.finish(state, outcome)        # SX.10c: the record names the catalog play, Again, the menu at its top
        self.defense.finish(state, outcome)        # SX.10d: the defense's Again, its menu at its top
        self.choices.clear()                       # SY.4, SY.5: the target and the blitzer were for this play only
        self.books.forget_calls()                  # then nothing is called and the menu starts at its top (the rows stay armed
        #                                            until the ruling below has read the row the play used)
        board = None
        if x.challenges_on and not replaying:
            self.review.forget()                   # the ruling of an earlier play is gone
            board = capture(state)                 # the board a reversal goes back to: before the bookkeeping below
        left_before = x.left                       # and the clock a reversal goes back to: before the live time
        self.after_play = True                     # H18: until H10 runs, a timeout (the T key) takes the whole runoff away
        x.plays += 1
        x.running = False                          # the play is over: H10 decides whether the clock runs to the next snap
        x.pending = 0
        x.last_kind = outcome.kind
        self.broadcast.note_outcome(state, outcome)    # SY.1: what the play was, for Ghip after the down sentence
        self.stadium.note_outcome(state, outcome)      # SY.2: the hit and the catch
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
        self.modifiers.arm(None)                   # SX.7: the play's rows are done
        if state.quarter >= 5 and outcome.kind == O.PUNT and not outcome.turnover and outcome.then is None:
            OT.kickers_kept_punt(x, state, outcome.offense)     # SX.12: a muffed punt the kickers kept was the receivers' chance (16-1-5 (c))
        injuries = self.game_injuries()
        if injuries is not None:                   # SX.8k (a Franchise game only): the draws of a play that can hurt a player
            injuries.after_play(state, outcome)
        return outcome

    # ----- H23 (SY.1, the radio broadcast, rule 0.27) -----

    def ref_says(self, text: str, last: bool = True) -> None:
        """A sentence of the referee (SY.3): over the microphone in a voice of his own when the broadcast is on (the click of the microphone
        before the first sentence and after the last), else the announcer's say4, as before. Waited, logged and kept for F2 like say4."""
        g = self.game
        if self.broadcast.ghip and hasattr(g, "say_referee"):
            self.stadium.mic(True)
            g.say_referee(text)
            if last:
                self.stadium.mic(False)
        else:
            g.say4(text)

    def banter_lines(self, game):
        return self.broadcast.banter_lines(game)

    def broadcast_moment(self, state, what: str, quarter: int = 0) -> None:
        self.broadcast.moment(state, what, quarter)
        self.stadium.moment(state, what, quarter)

    def game_injuries(self):
        """The Franchise's injuries of the game in progress (extras/franchise/injury_flow.GameInjuries), or None: every game that is not a game of a
        franchise season has none, so it draws, says and stores no injury (INJ-1)."""
        return getattr(self.game, "game_injuries", None) if self.game is not None else None

    def second_tackler(self, state, first: int, second: int) -> int:
        """H16 (SX.8k): the kick-off return's tacklers; a Franchise game keeps them two men."""
        injuries = self.game_injuries()
        return second if injuries is None else injuries.other_man(state.defense, first, second)

    def draw_carrier(self, state, rnd) -> int:
        """H17 (SX.8o): the ball carrier; a Franchise game weighs the places by the players' ratings (equal weights, and every other game: rnd(6))."""
        values = self.modifiers.carrier_weights(state) if hasattr(self.modifiers, "carrier_weights") else None
        if values is None:
            drawn = rnd(6)
        else:
            from .franchise import workload
            drawn = workload.draw(rnd, values)
        return self.choices.carrier(state, drawn)        # SY.4: the receiver the player chose takes the drawn one's place (the draw is made)

    def sack_defenders(self, state) -> tuple[int, int]:
        return self.choices.sack_defenders(state)        # H24 (SY.5)

    def after_draws(self, state) -> None:
        """H16 (SX.8k): the snap's draws are made; a Franchise game keeps its two tacklers two men."""
        injuries = self.game_injuries()
        if injuries is not None:
            injuries.after_draws(state)

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
            if self.offense.active(state):                     # SX.10c (design 2.6): items 1 to 5 and More Plays, no tail
                self.offense.clear()
                return self.offense.items(state)
            return menus.offense_menu(True)                    # the try is untimed: the original's items 1 to 5
        self.books.offense_id = ""                 # SX.7: a play that was called and not run (the period ended at the snap)
        self.offense.clear()                       # SX.10c: the same for the catalog's call
        self.kicks.fair_catch_armed = False        # SX.10d: a fair catch kick chosen and not kicked (the period ended) is gone
        if self.offense.active(state):             # SX.10c: the catalog's menus (design 2.2)
            return self._tail(state, self.offense.items(state))
        items = [menu_item(n, text.strip()[3:], (menus.PLAY, n)) for n, text in enumerate(OFFENSE_ITEMS[:7], start=1)]
        if state.extras.qb_on:                     # design 10.4: 8 sneak, 9 keeper, 0 draw (item 10, digit 0)
            for play, text_id in ((QB_SNEAK, "NXM-01"), (QB_KEEPER, "NXM-02"), (QB_DRAW, "NXM-03")):
                position = len(items) + 1
                item = menu_item(position, X.text(text_id), (menus.PLAY, play))
                items.append(item._replace(digit=position % 10))
        return self._tail(state, items)

    def defense_menu(self, state) -> list[menus.MenuItem]:
        self.books.defense_id = ""
        self.defense.clear()                       # SX.10d: nothing is called yet
        if self.defense.active(state):             # SX.10d: the catalog's defense menus (design 2.2)
            return self._tail(state, self.defense.items(state))
        items = [menu_item(n, text.strip()[3:], (menus.PLAY, n)) for n, text in enumerate(DEFENSE_ITEMS[:6], start=1)]
        return self._tail(state, items)

    def flow(self, state):
        """The catalog's menus the player is in: the offense's while he has the ball, the defense's while the computer has it (None: the
        original's items, a playbook that is Classic)."""
        if self.offense.active(state):
            return self.offense
        if self.defense.active(state):
            return self.defense
        return None

    def _tail(self, state, items: list[menus.MenuItem]) -> list[menus.MenuItem]:
        """Design 10.4: Time Out (T) when timeouts are on, then Save Game (S) last."""
        if state.extras.challenges_on and self.review.can_challenge(state, 1):       # SX.6: only while one is allowed
            items.append(menu_item(len(items) + 1, X.text("NXM-04"), CHALLENGE_ACTION, "c"))
        if state.extras.timeouts_on:               # no letter: the T key calls the timeout at once, anywhere (H18, rule 0.22)
            items.append(menu_item(len(items) + 1, X.text("NXM-05"), TIMEOUT_ACTION))
        items.append(menu_item(len(items) + 1, X.text("NXM-06"), (menus.SAVE, 0), "s"))
        return items

    def menu_action(self, state, action: tuple[str, int]):
        """An added item was taken with Enter. True: done, the menu starts again; False: refused, the menu stays; a
        continuation (a challenge that changed a ruling, SX.6): the menu is left for the step it names."""
        if str(action[0]).split(":")[-1] in (PM.MORE, PM.OPEN) and (self.offense.owns(action) or self.defense.owns(action)):
            self._hints_known()                    # SZ.5: More Plays or a list opened: the player has found the other plays
        if self.offense.owns(action):              # SX.10c: an item of the catalog's menus
            return self.offense.action(state, action)
        if self.defense.owns(action):              # SX.10d: an item of the catalog's defense menus
            return self.defense.action(state, action)
        if action[0] == CHALLENGE:
            return self.review.player_challenge(state)
        if action[0] != TIMEOUT:
            log.warning("unknown menu action %r", action)
            return False
        return self.player_timeout(state)

    def menu_back(self, state) -> bool:
        """Backspace or Left: in the catalog's menus one level up (SX.10c, SX.10d); elsewhere nothing (the key is the original's)."""
        flow = self.flow(state)
        return flow is not None and flow.back(state)

    def menu_right(self, state, item) -> bool:
        """Right: a family's lists of plays, and the family's next list (SX.10c, design 2.3)."""
        flow = self.flow(state)
        opened = flow is not None and flow.right(state, item)
        if opened:
            self._hints_known()                      # SZ.5
        return opened

    def menu_heading(self, state) -> str:
        """The name of the open list of the catalog's menus, said in place of the prompt (SX.10c)."""
        flow = self.flow(state)
        return flow.heading(state) if flow is not None else ""

    HINT_RUNS = 3          # the hints are given in the first three program runs that reach the menus; Right or M used for real ends them

    def _hint_settings(self):
        return getattr(getattr(getattr(self.game, "options", None), "settings", None), "game", None)

    def menu_hint(self, state) -> str:
        """SZ.5 (D-110; a player's e-mail of 2026-10-22: no other plays were found on defense, and "recommended formations" came with no recommended
        play): one sentence after the first item of the catalog's top menu (where Right and M are, that Enter lets the playbook pick) and of its
        settings list (that "the playbook's choice" is not a recommendation), once for each in a program run and in the first three runs only,
        in the voice that spoke last. A player who opens a list with Right or More Plays is told no more. No draw, no state of the game."""
        flow, game, settings = self.flow(state), self.game, self._hint_settings()
        if flow is None or game is None or settings is None or state.two_point:
            return ""
        level, side = flow.menus.level, flow.menus.context.side
        if level == PM.TOP:
            key, text_id = ("top", side), ("NXB-H17" if side == "O" else "NXB-H18")
        elif level == PM.SETTINGS_LEVEL:
            key, text_id = ("settings", ""), "NXB-H19"
        else:
            return ""
        told = getattr(game, "menu_hints_told", None)
        if told is None:
            told = game.menu_hints_told = set()
        if key in told or settings.nx_menu_hints >= self.HINT_RUNS:
            return ""
        if not told:                                            # the first hint of this program run: one more run counted, saved
            settings.nx_menu_hints += 1
            self._save_settings()
        told.add(key)
        debuglog.event("menu", "hint", id=text_id, runs=settings.nx_menu_hints)
        return X.text(text_id)

    def _save_settings(self) -> None:
        try:
            self.game.options.save()
        except Exception as exc:
            log.debug("the menu hints could not be saved: %s", exc)

    def _hints_known(self) -> None:
        """The player opened a list with Right or More Plays: he knows where the plays are, the hints stop for good."""
        settings = self._hint_settings()
        if settings is not None and settings.nx_menu_hints < self.HINT_RUNS:
            settings.nx_menu_hints = self.HINT_RUNS
            self._save_settings()

    def menu_key(self, state, letter: str, item=None, code: str = ""):
        """The letter C when the menu has no Challenge the Ruling item: the reason why (NXR-10 to NXR-15), the menu goes on. The letter D
        (NX-P8, D-091): the plain description of the current item, in the voice that spoke last, once per press, not written to the
        game's speech log; the menu stays on the item. No menu of the N. F. L. rules gives the letter D to an item (a test)."""
        if letter == "d" and item is not None:
            return self.describe_item(state, item)
        if letter == "w" and item is not None:
            return self.say_likely(state, item)
        if letter == "c" and state.extras.challenges_on:
            return self.review.say_refusal(state, 1)
        if letter == "r" and item is not None and state.wisoff == 1 and self.offense.owns(item.action):
            return self.choices.receiver_menu(state, item)               # SY.4: who the next pass goes to
        if letter == "l" and item is not None and state.wisoff == 2 and self.defense.owns(item.action):
            return self.choices.blitzer_menu(state)                      # SY.5: who blitzes
        if item is not None and self.offense.owns(item.action):     # SX.10c: plus, minus and a lone Shift in the catalog's menus
            return self.offense.key(state, code, item)
        if item is not None and self.defense.owns(item.action):     # SX.10d: the same in the defense's
            return self.defense.key(state, code, item)
        return False

    def describe_item(self, state, item) -> bool:
        """Say the description of a live play menu item; False (the key falls through to the key echo) when the item has none."""
        if self.offense.owns(item.action):         # SX.10c: an item of the catalog's menus (play_menus.PlayMenus.describe)
            row = self.offense.describe_row(item.action)
        elif self.defense.owns(item.action):       # SX.10d: the defense's
            row = self.defense.describe_row(item.action)
        else:
            row = descriptions.action_row(state.wisoff == 1, item.action)
        if row is None:
            log.warning("no description for the menu item %r", item.action)
            return False
        debuglog.event("key", "describe", item=item.action, row=row)
        self.game.voice_speak(descriptions.text(row), wait=False)
        return True

    def say_likely(self, state, item) -> bool:
        """The W key (D-112, Q-050; the owner: "a key that says which play the playbook would most likely call"): on a play type, the
        play Enter would most likely get and how often; in a list, the play of it the playbook most likely calls; on a single play, that it
        is one play; on any other item (or with no playbook in use) what W is for. The same weights as Enter's pick and NO draw, so the
        game is the same with or without the key. Said in the voice that spoke last, once per press, not written to the game's speech
        log (as D); the menu stays on the item."""
        flow = self.flow(state)
        if flow is None:                           # the original's items: no playbook in use for this side
            sentence = X.text(W_NO_BOOK)
        else:                                      # a tail item (Save Game, Time Out, Challenge) or a menu without plays: what W is for
            sentence = (flow.likely_text(state, item) if flow.owns(item.action) else "") or X.text(W_FOR)
        debuglog.event("key", "likely", item=item.action, text=sentence.strip())
        self.game.voice_speak(sentence, wait=False)
        return True

    # ----- H4 -----

    def before_kickoff(self, state, kicking_side: int) -> str:
        x = state.extras
        self.broadcast.opening(state)              # SY.1: Ghip before the opening kick-off
        x.out_of_bounds = False
        self.after_play = False
        self.books.clear()                         # SX.7: a kick-off is a new play: nothing is called
        self.offense.clear()                       # SX.10c: nor a catalog play
        self.defense.clear()                       # SX.10d: nor a defense call
        self.kicks.fair_catch_armed = False        # SX.10d: nor a fair catch kick
        self.try_due = False                       # SX.13: the try is over
        self.review.clock_held = False             # SX.6: a kick-off is a new dead-ball period
        if x.left <= 0 and (state.quarter in (2, 4) or (state.quarter >= 5 and not x.postseason)):
            # SX.12: a score as the regular season's one overtime period ran out ends it too (16-1-3 (d)); a play-off period's kick-off
            # opens the next period, as a kick-off after a score as the first or third quarter ran out
            # no kick-off is made: nothing of the kick that was to come is left over (a safety kick on the last play of a half,
            # a kick to be made again): the next half starts with a kick-off from the 35
            x.safety_kick = x.kick_again = x.rekick = x.free_after_safety = False
            x.kick_back = 0
            return PERIOD_OVER          # a score as time ran out: the half or the game ends after the try, no kick-off
        OT.at_kickoff(x, state, kicking_side)      # SX.12: the overtime's possession rule (nothing before overtime)
        self._overtime_news(state)
        if x.timeouts_on and x.announced != x.unit:
            x.announced = x.unit
            text_id = "NXT-06" if x.unit.startswith("H") else ("NXT-14" if x.unit.startswith("OTP") else "NXT-07")
            self.game.say4(X.text(text_id, n=x.timeouts_of(1)))
        if x.penalties_on:
            self.penalty.take_kickoff(state)
        # SX.4: where the kick is made from (6-1-2, 11-5-2: the 35, the 20 after a safety, moved back by an accepted foul
        # on a kick made again, 6-3-1) and whether it is an onside kick
        again, x.kick_again = x.kick_again, False
        safety = x.safety_kick and not again
        if again:                      # moved back by the yards of the foul, never more than half the distance to the goal
            spot = x.kick_from - min(x.kick_back, x.kick_from // 2)      # line (14-2-1), so never to or past it
        else:
            spot = R.SAFETY_KICK_SPOT if x.safety_kick else R.KICKOFF_SPOT
        x.free_after_safety = safety or (again and x.free_after_safety)       # SX.13: a safety kick made again is still one (6-2-4)
        x.kick_from, x.kick_back, x.safety_kick = spot, 0, False
        if self.kicks.on(state):                   # SX.10d: the 2026 kick-off menu (it replaces the onside question, design 2.6)
            return self.kicks.decide(state, kicking_side, again, safety)
        if not x.onside_on:
            return NORMAL_KICKOFF
        return self.onside.decide(state, kicking_side, again)

    def onside_kick(self, state) -> str:
        return self.onside.kick(state)

    # ----- H10 -----

    def between_plays(self, state) -> str | None:
        x = state.extras
        if x.handled == x.plays:                 # nothing new since the last call (the statistics speak the down again)
            return None
        x.handled = x.plays
        self.after_play = False
        if self.possession_ends_game(state):      # SX.12: the overtime decided between two plays (the kickers kept their kick
            return OVERTIME_OVER                  # after their score, 16-1-5 (c)); the possession step catches the other changes
        self._overtime_news(state)
        self.stadium.between(state, self.broadcast.facts)     # SY.2: the crowd's answer to the last play and the chain (before Ghip consumes the facts)
        self.broadcast.between(state)             # SY.1: Ghip's line about the last play, after the down sentence
        if x.challenges_on:                       # SX.6: the computer's flag on the last play, before the clock goes on
            then = self.review.computer_challenge(state)
            if then is not None:                  # the ruling was reversed: the engine goes on at the step that applies it
                return then
        keeps = x.last_kind in RUNNING_KINDS and state.wisoff == x.last_offense and not x.last_two_point
        ready = False
        if keeps and x.out_of_bounds:
            if late_window(state.quarter, x.left, x.period, x.postseason):
                keeps = False                     # stopped until the snap
            else:
                ready = True                      # stopped, restarted on the ready signal: a shorter runoff
        cap = None
        if x.foul_clock:                          # SX.3: after a foul, as if it had not happened, except 4-3-2 (e), (g)
            keeps, ready = clock_after_foul(x, state.quarter, keeps,
                                            state.score(state.wisoff) > state.score(other(state.wisoff)))
            cap = R.RUNOFF_PLAY_CLOCK if x.foul_clock == "runoff" else R.PLAY_CLOCK_AFTER_PENALTY
            x.foul_clock = ""
        if self.review.clock_held:                # SX.6: a time out was called in this dead-ball period before a challenge that
            keeps = ready = False                 # changed the play: the clock stays stopped to the snap
            self.review.clock_held = False
        if self.timeout_kept:                     # H18: the T key pressed during the play: granted now, before the runoff is drawn, so
            if self.grant_kept_timeout(state) == TIMEOUT_GRANTED:     # the clock stops when the play ends (SX.13: 3-36-2; it cost
                keeps = ready = False                                 # the runoff's seconds before)
        if self.review.take_runoff() and (keeps or ready):
            # SX.13 (15-5-2, 4-7-4): the reversed play began after the two-minute warning and its corrected result keeps the clock
            # running: ten seconds run off, then both clocks start on the ready signal with a play clock of 30; under ten seconds the
            # half or the game is over. A timeout taken in this dead ball (the T key during the play) avoided it (it is charged)
            x.left = max(0, x.left - R.RUNOFF_SECONDS)
            self.game.say4(X.text("NXP-12"))
            debuglog.event("extras", "review_runoff", left=x.left)
            keeps = ready = x.left > 0
            cap = R.RUNOFF_PLAY_CLOCK
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
        if x.fair_catch_kick and self.kicks.fair_catch_question(state):     # SX.10d (G26-13, Q-P18): the player said yes
            return FAIR_CATCH_KICK

    def resume_choice(self, state) -> str | None:
        """SX.9 (C10): the accept-or-decline choice a Save Game at the prompt kept, asked first when the game is loaded (or again when
        the file could not be written)."""
        x = state.extras
        if x is None or x.pending_choice is None:
            return None
        return self.penalty.resume(state)

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

    # ----- the T key (H18, owner rule 0.22, playbook 7.16) -----

    def timeout_keys(self, state) -> bool:
        return state.extras is not None and state.extras.timeouts_on

    def timeout_key(self, state, live: bool, undo=None, called=None, where: str = "live play") -> str:
        """The T key reached the game thread. During a live play the request is kept for the next dead-ball moment (the real rule grants a
        timeout only while the ball is dead, NFL 3-36-2 and 4-5-1) and nothing is said. Otherwise the speech that is playing is cut at
        once and the timeout is called or refused with its sentence. `undo` gives the snap's runoff back (the T came during the snap
        count, so the play is not run); `called` is then what the snap took of the dead-ball period."""
        if live:
            self.timeout_kept = True
            self._log_timeout_key(state, where, TIMEOUT_KEPT)
            return TIMEOUT_KEPT
        self.game.stopspeech()
        return self._call_timeout(state, "before the snap" if undo is not None else "dead ball", undo, called)

    def grant_kept_timeout(self, state) -> str | None:
        """A request kept during the live play is granted (or refused with its sentence) at the first dead-ball moment."""
        if not self.timeout_kept:
            return None
        self.timeout_kept = False
        if state.extras is None or not state.extras.timeouts_on:
            return None
        return self._call_timeout(state, "after the play", None)

    def ball_live(self, state) -> None:
        """SX.13 (4-5-1 Item 3, 3-8-1): a snap or a kick ends the dead-ball period, so a timeout called before a kick-off, a punt, a
        field goal or a kicked try no longer counts at the next dead ball (the scrimmage snap also clears it in the clock's before_snap)."""
        x = state.extras
        self.try_due = False
        if x is not None:
            x.called = [False, False]

    def _call_timeout(self, state, where: str, undo=None, called=None) -> str:
        x, g = state.extras, self.game
        why = None
        if x.left <= 0 and not x.extension and not (self.try_due or state.two_point):    # SX.13: the try is a down still to come
            why, sentence = "no time", X.text("NXT-16")
        else:
            reason = timeouts.refusal(x, 1, called)
            if reason is not None:
                why, sentence = reason, X.text("NXT-04" if reason == "none" else "NXT-05")
        if why is not None:
            g.say5(sentence)
            self._log_timeout_key(state, where, TIMEOUT_REFUSED, why)
            return TIMEOUT_REFUSED
        if undo is not None:
            undo()
        if self.after_play:                       # between the end of a play and H10: no runoff is drawn, the clock stays stopped
            self.review.clock_held = True
        self.grant(state, 1)
        self._log_timeout_key(state, where, TIMEOUT_GRANTED)
        return TIMEOUT_GRANTED

    def _log_timeout_key(self, state, where: str, result: str, why: str = "") -> None:
        x = state.extras
        debuglog.event("extras", "timeout_key", logging.INFO, where=where, result=result, why=why or None, quarter=state.quarter,
                       left=x.left, timeouts=x.timeouts_of(1), called=x.called_by(1))

    def withdraw_play(self, state) -> None:
        """A timeout was called before the snap: the plays that were called are withdrawn (nothing of them is run)."""
        self.books.clear()
        self.offense.clear()
        self.offense.reset()
        self.defense.clear()
        self.defense.reset()

    @staticmethod
    def live_timeout_sentence() -> str:
        return X.text("NXT-15")

    def grant(self, state, side: int) -> None:
        """A timeout: charged, the clock stopped after u seconds, the whistle (foot11), the announcer, a remark 1 in 3."""
        g, x = self.game, state.extras
        self.offense.reset()                      # SX.10c: the player's menu starts at its top again
        self.defense.reset()                      # SX.10d: the defense's too
        timeouts.charge(x, side)
        self.clock.stop_for_timeout(self.rnd)
        g.sounds.whistle_context = "timeout"
        g.sounds.play_tackle(8)                   # foot11, as the original's whistles of the period ends
        left = x.timeouts_of(side)
        g.ptf = 1
        self.ref_says(X.text("NXT-01", team=state.teams.get(side, "")))      # SY.3: the referee, over the microphone
        if side == 1:
            g.say4({0: X.text("NXT-10"), 1: X.text("NXT-12")}.get(left) or X.text("NXT-03", n=left))
        else:
            g.say4({0: X.text("NXT-09"), 1: X.text("NXT-11")}.get(left) or X.text("NXT-02", n=left))
        g.ptf = 0
        if g.comtog == 0 and self.rnd(T.TIMEOUT_REMARK_CHANCE) == 1:
            values = {"<team>": state.teams.get(side, ""), "<coach>": g.season.coach,
                      "<quarterback>": state.quarterbacks.get(side, "")}
            remarks.say_remark(g, state, x, "TO", values)

    # ----- H19 (SX.10c): the catalog's plays -----

    def model_play(self, state):
        result = self.offense.model_play(state)
        if result is None:
            result = self.defense.model_play(state)     # SX.10d: the computer's play against the player's call
        if result is None:
            result = self.offense.computer_play(state)  # SX.10e: the computer's call over the catalog against any defense
        return result

    def computer_goes_for_two(self, state) -> bool:
        """H21 (SX.10e, G26-10): after the computer's touchdown, in a game that plays the catalog, its two-point chart; Classic and every
        game that plays the original's plays: never (the computer always kicks, no draw)."""
        if not self.books.catalog_side(state, state.wisoff, "O"):
            return False
        margin = state.score(state.wisoff) - state.score(other(state.wisoff))
        yes = calling.goes_for_two(state.quarter, margin, self.rnd, state.extras.left)
        debuglog.event("extras", "computer_try", side=state.wisoff, margin=margin, quarter=state.quarter, two=yes)
        return yes

    def turnover_return(self, state):
        return self.offense.turnover_return(state)

    def play_text(self, key: str, **values) -> str:
        if key in OVERTIME_SENTENCES:
            return X.text(OVERTIME_SENTENCES[key], **values)
        return text_for(key, **values)

    # ----- H22 (SX.12): the 2026 overtime, Rule 16 (extras/overtime.py) -----

    def overtime_follows(self, state) -> bool:
        """A tie at the end of the fourth quarter begins overtime; a tie at the end of the regular season's one period is the game's result
        (16-1-3 (d)). A play-off period never reaches the game's end tied (period_end_step goes on)."""
        return state.quarter <= 4

    def overtime_lines(self, state) -> list[str]:
        return [X.text("NXC-06"), X.text("NXC-08" if state.extras.postseason else "NXC-07")]

    def overtime_toss(self, state) -> bool:
        return True

    def overtime_kicks_first(self, state) -> bool:
        """The computer won the overtime toss: it kicks off with the league's share of toss winners (one draw, tuning)."""
        kicks = self.rnd.below(1000) < T.OT_KICK_FIRST_PER_MILLE
        debuglog.event("extras", "overtime_toss", kicks=kicks)
        return kicks

    def points_end_game(self, state, touchdown_by: int | None = None) -> bool:
        x = state.extras
        over = OT.after_points(x, state, touchdown_by)
        if state.quarter >= 5:
            debuglog.event("extras", "overtime_points", phase=x.ot_phase, first=x.ot_first, scores=[state.score(1), state.score(2)],
                           touchdown_by=touchdown_by or 0, over=over)
        if not over and touchdown_by is not None and OT.last_try_cannot_matter(x, state, touchdown_by):
            # SX.13 (4-8-2 (c)): a touchdown on the down in which the game's time ran out (the fourth period, and the regular season's
            # overtime period, which has the fourth period's provisions, 16-1-3 (e)) has no try when a good try cannot change the result
            if state.quarter >= 5:
                x.ot_phase = OT.OVER
            debuglog.event("extras", "no_last_try", quarter=state.quarter, scorer=touchdown_by,
                           scores=[state.score(1), state.score(2)])
            return True
        if not over and touchdown_by is not None:
            self.try_due = True                    # SX.13: the try's down is still to come (a timeout may be called at 0:00 before it)
        return over

    def possession_ends_game(self, state) -> bool:
        x = state.extras
        before = x.ot_phase
        over = OT.at_possession(x, state)
        if state.quarter >= 5 and x.ot_phase != before:
            debuglog.event("extras", "overtime_phase", phase=x.ot_phase, was=before, ball=state.wisoff)
        return over

    def period_end_step(self, state) -> str | None:
        step = OT.period_end(state.extras, state)
        if step is not None:
            debuglog.event("extras", "overtime_period", next=step, period=state.overtime + 1)
        return {OT.SAME_BALL: OT_SAME_BALL, OT.KICK_OFF: OT_KICK_OFF, OT.COIN_TOSS: OT_COIN_TOSS}.get(step)

    def third_period_receiver(self, state) -> int:
        return OT.third_period_receiver(state.extras)

    def overtime_toss_won(self, state, winner: int) -> None:
        state.extras.ot_toss_loser = other(winner)
        debuglog.event("extras", "overtime_toss_won", winner=winner)

    def third_period_chooser(self, state) -> int:
        return state.extras.ot_toss_loser

    def overtime_fourth_down(self, state) -> str | None:
        """The second team behind on its initial possession (16-1-3 (b)): a punt or a missed chance ends the game, so it goes for it, and kicks
        a field goal only when the kick ties the game and is in the original's range (its own fourth-down rule: the other half, inside the 41)."""
        behind = OT.second_possession_trailing(state.extras, state, state.wisoff)
        if behind == 0:
            return None
        if behind <= 3 and state.half != own_half(state.wisoff) and state.yard_line < 41:
            return "kick"
        return "go"

    def game_over_lines(self, state) -> list[str]:
        if state.quarter >= 5 and state.score(1) == state.score(2):
            return [X.text("NXC-11")]
        return []

    def _overtime_news(self, state) -> None:
        if OT.sudden_news(state.extras, state):
            self.game.say4(X.text("NXC-10"))

    # ----- H20 (SX.10d): the kicks of 2026 -----

    def special_kick(self, state, what: str):
        return self.kicks.plan(state, what)

    def kickoff_call(self, state) -> str:
        return self.kicks.kickoff_call(state)

    def kickoff_result(self, state):
        return self.kicks.kickoff_result(state)

    @staticmethod
    def kickoff_touchback() -> int:
        return R.KICKOFF_TOUCHBACK

    def kick_result(self, state, plan):
        if plan.what == kick_flow.PUNT:
            return self.kicks.punt_result(state, plan)
        if plan.what == kick_flow.EXTRA_POINT:
            return self.kicks.extra_point_result(state, plan)
        return self.kicks.field_goal_result(state, plan)

    def fake_yards(self, state, plan) -> int:
        return self.kicks.fake_yards(state, plan)

    def kick_text(self, key: str, **values) -> str:
        return kick_flow.text_for(key, **values)

    def fair_catch(self, state, receivers: int, start: int) -> None:
        self.kicks.fair_catch(state, receivers, start)

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
        ids = {KEY_F5: ("NXH-02", "NXH-01", "NXH-23", "NXH-09", "NXH-47", "NXH-14", "NXH-18", "NXH-27"),
               KEY_F6: ("NXH-03", "NXH-04", "NXH-63", "NXH-64", "NXH-65", "NXH-66", "NXH-70", "NXH-67", "NXH-68", "NXH-71", "NXH-05", "NXH-06", "NXH-24", "NXH-25", "NXH-10", "NXH-11", "NXH-15",
                        "NXH-16", "NXH-19", "NXH-20", "NXH-22", "NXH-28", "NXH-29", "NXH-30") + MENU_HELP_F6,     # SX.12: overtime after the clock
               KEY_F7: ("NXH-07", "NXH-08", "NXH-26", "NXH-12", "NXH-13", "NXH-17", "NXH-21", "NXH-31", "NXH-32",
                        "NXH-33") + descriptions.F7_WORD_ROWS}.get(key, ())
        timeout_lines = ("NXH-01", "NXH-05", "NXH-07")
        challenge_lines = ("NXH-23", "NXH-24", "NXH-25", "NXH-26")
        penalty_lines = ("NXH-09", "NXH-47", "NXH-10", "NXH-11", "NXH-12", "NXH-13", "NXH-22")
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
            menus_used = PlaybookFlow.player_uses_a_book(x)
        else:
            playbooks = self.playbooks_on or "classic" not in (self.offense_book, self.defense_book)
            menus_used = "classic" != self.offense_book or "classic" != self.defense_book
        # the lines about the menus are for a player whose own books are playbooks; the others for anyone who meets a style
        lines = [X.text(i) for i in ids if (timeouts_on or i not in timeout_lines)
                 and (playbooks or i not in playbook_lines) and (menus_used or i not in ("NXH-27",) + MENU_HELP_F6)
                 and (challenges_on or i not in challenge_lines)
                 and (penalties_on or i not in penalty_lines) and (onside_on or i not in onside_lines)
                 and (qb_on or i not in qb_lines)]
        on = {name for name, flag in (("timeouts", timeouts_on), ("challenges", challenges_on), ("penalties", penalties_on),
                                      ("qb", qb_on), ("playbooks", menus_used)) if flag}
        self.help_features = on                              # the tests read which features the lines were made for
        return lines + key_list.help_lines(key, "nfl", on)   # CLAUDE.md 0.24: every key, from the master list (game/key_list.py)


OVERTIME_SENTENCES = {"overtime_kicks": "NXC-09"}      # SX.12: the computer won the overtime toss and kicks off


def rules_from_settings(game_settings, auto_sides: tuple[int, ...] = (2,)):
    """The program's rules for a Rules setting (design 12.1): Classic, or the N. F. L. rules with their switches."""
    from ..game.rules import CLASSIC
    if getattr(game_settings, "rules", "classic") != "nfl":
        return CLASSIC
    return NflRules(timeouts_on=getattr(game_settings, "nx_timeouts", True), auto_sides=auto_sides,
                    penalties_on=getattr(game_settings, "nx_penalties", True),
                    onside_on=getattr(game_settings, "nx_onside", True),
                    onside_always=getattr(game_settings, "nx_onside_question", "always") == "always",
                    qb_on=getattr(game_settings, "nx_qb_runs", True),
                    challenges_on=getattr(game_settings, "nx_challenges", True),
                    offense_book=getattr(game_settings, "nx_offense_playbook", "team"),
                    defense_book=getattr(game_settings, "nx_defense_playbook", "team"),
                    playbooks_on=True, broadcast_on=getattr(game_settings, "nx_broadcast", True), radio_banter=True,
                    stadium_on=getattr(game_settings, "nx_stadium", True), commentator=getattr(game_settings, "nx_commentator", "Ghip"))


def is_nfl(rules) -> bool:
    return isinstance(rules, NflRules)
