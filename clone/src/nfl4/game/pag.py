"""The game itself: the original's procedure pag, without any window, sound card or screen reader. This is inspired by Jim Kitchen.

GAME_SPEC 4.14 to 4.19, 5.5 to 5.13, 7 and 9 (CODE (lifted) pag p_43a860 with its GoSub routines, kicksnap p_43a330,
inrep p_4863f0, halftime p_485b80; read in full in S7.3b against work/lift). The original is one routine of 33,000
assembler lines that jumps between labels. Here every label it jumps to is a STEP: a method that does what the original
does from that label on, in the same order, and returns the next step (the label it jumps to). The GoSub routines are
plain methods. So the order of every random draw, spoken text, sound and pause is the original's; the address of the
lifted line is next to each step, each draw and each pause (the pause sites are recorded for the tests).

The parts:
    pag.py            start-up, coin toss, the play menus and the computer's choice, the GoSub helpers, the result
    pag_scrimmage.py  the snap and the snap count, runs, passes, sacks, fumbles (5.8, 5.9)
    pag_catalog.py    N. F. L. rules only (SX.10c): a catalog play's result told with the original's sentence pools
    pag_kicks.py      kicksnap, field goals, punts, kick-offs and returns, the extra point and the two-point try (5.10)
    pag_kicks26.py    N. F. L. rules with a playbook only (SX.10d): the kicks of 2026 told with the original's set-ups and endings
    pag_results.py    the end of a play: the ball, touchdowns, safeties, possession, position and down, scores (5.11, 5.12)
    pag_breaks.py     the next-play step, quarters, warnings, statistics, key waits, the end, Save Game, conceding (5.6)

The extra features of the N. F. L. rules mode (nfl4 only, CLAUDE.md 0.13) reach the engine only through the Rules
object (game/rules.py) and the hooks H1 to H13 of NFL_EXTRAS_DESIGN 3; with ClassicRules everything here is the
original. Not here, by plan: the typed quarterback prompt Getqbs and the hot keys (S7.4: `quarterback_names` is handed in
until then), reading and writing football.sav and footplay.txt (S7.5: `saved` and `save_sink`), the Super Bowl
presentation (S7.3c: Game.superbowl).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Callable

from ..data import debuglog
from ..speech.roles import OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER, OWN_QUARTERBACK, pronoun
from . import phrases as P
from . import resume
from .keys import GameQuit
from .save_summary import make_info
from .gamestate import GameState, SavedGame, other, own_half
from .menus import PLAY, SAVE
from .outcome import PlayOutcome
from .pag_breaks import BreakSteps
from .pag_keepers import KeeperSteps
from .pag_kicks import KickSteps
from .pag_kicks26 import Kick26Steps
from .pag_results import ResultSteps
from .pag_catalog import CatalogSteps
from .pag_scrimmage import ScrimmageSteps
from .playtables import DEFENSE_MATCH
from .rules import (CLASSIC, FAIR_CATCH_KICK, KICK_AGAIN, MENU_QUIET, MENU_REFRESH, NEXT_DOWN, ON_DOWNS, PERIOD_END,
                    REVIEWED_FIELD, REVIEWED_FUMBLE, REVIEWED_TOUCHDOWN, SAFETY_BY_PENALTY, SAVE_PENDING, TIMEOUT_GRANTED, TRY_AGAIN,
                    TRY_FAILS)
from .setup import Roster

log = logging.getLogger("nfl4.game")


class PlayWithdrawn(BaseException):
    """A timeout was called by the T key before the snap (or the kick): the plays that were called are withdrawn, nothing of the play is
    run, and the engine goes on at `back` (owner rule 0.22, playbook 7.16). It is a BaseException so that no `except Exception` of the
    menus it unwinds through can swallow it; only PlayEngine.run catches it."""

    def __init__(self, back):
        super().__init__("a timeout was called before the snap")
        self.back = back

KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
KEY_ENTER, KEY_ESCAPE, KEY_UP, KEY_DOWN, KEY_TAB = "13", "27", "38", "40", "9"
KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT = "8", "37", "39"
KEY_LETTERS = (65, 90)                     # the codes of the letter keys A to Z


@dataclass
class GameResult:
    """What pag leaves for the rest of the program (GAME_SPEC 5.12): Me.m414 (the final or conceded score; None after
    Save Game), whether the game was saved (SavedGame = 1) or conceded."""
    scores: tuple[int, int] | None
    saved: bool = False
    conceded: bool = False


class PlayEngine(ScrimmageSteps, KeeperSteps, CatalogSteps, KickSteps, Kick26Steps, ResultSteps, BreakSteps):
    def __init__(self, game, rules=CLASSIC, own_names: Roster | None = None, saved: SavedGame | None = None,
                 quarterback_names: Callable[[GameState], tuple[str, str]] | None = None,
                 save_sink: Callable[[SavedGame], None] | None = None,
                 roster_sink: Callable[[Roster], object] | None = None,
                 opponent_names: Roster | None = None, autosave_sink: Callable[[SavedGame], object] | None = None,
                 save_ui=None):
        self.g = game
        self.rules = rules
        self.own_names = own_names
        self.opponent_names = opponent_names           # H7 (nfl4 only, SX.8b): the Franchise's opponent; None: drawn as the original
        self.saved = saved
        self.quarterback_names = quarterback_names
        self.save_sink = save_sink
        self.autosave_sink = autosave_sink            # SX.14 (NX-S4): writes the automatic save; None in the tests that do not look at it
        self.save_ui = save_ui                        # SX.14 (NX-S5, NX-S6): the slot and the quit-or-keep-playing questions of Save Game; None: the original's
        self.roster_sink = roster_sink                # S7.5: writes footplay.txt when the player's names were drawn
        self.s = GameState()
        self.clock = rules.period_clock(game, self.s)
        self.result = GameResult(None)
        self.outcomes: list[PlayOutcome] = []        # every H2 record of this game, in order (the tests read them)
        self.noise_net = 0                           # G-A2: how often the safety net had to stop the play noise
        self.last_outcome: PlayOutcome | None = None
        # the T key (owner rule 0.22, playbook 7.16, H18; the N. F. L. rules mode only): where the game is. game_on from the opening
        # kick-off (or a loaded game) to the final whistle; live from the snap or the kick to the play's end point (a request is kept);
        # back = the step a granted timeout goes back to when the play is not yet run (the play menu, the extra point's choice), None
        # when the timeout is simply granted where the game is (a kick-off, the narration between plays)
        self.game_on = False
        self.t_live = False
        self.t_screen = False                        # a "press any key" wait between periods or after a score: T is that key and is kept
        self.t_back = None
        self.t_clock = None                          # the period clock as it was before the snap took the pending runoff
        self.t_choice: tuple[int, int] | None = None     # previous_play and repeats before the computer's choice

    # ----- the T key (H18) -----

    @property
    def t_armed(self) -> bool:
        """The T key calls a timeout in this game right now (the rules have timeouts and the game is being played)."""
        return self.game_on and self.rules.timeout_keys(self.s) and not debuglog.typing_now()

    def t_cut(self) -> bool:
        """The window thread, the moment T is posted: True when the key will call (or refuse) a timeout before the play is run, so the
        speech that is playing is cut at once. During a live play the key is only kept, and nothing is cut."""
        if not self.t_armed or self.t_live:
            return False
        self.g.speech.stop()
        return True

    def on_timeout_key(self) -> bool:
        """The T key reaches the game thread (HotKeys.dispatch, inside KeyInput.pump). True when it was taken; the wait it interrupted gets
        F1 back, with `resumed` saying whether a timeout was called (the menu starts again) or not (it goes on where it was)."""
        if not self.t_armed:
            return False
        if self.t_screen:                            # the key is also the "any key" of the wait; the timeout waits for the next menu
            self.rules.timeout_key(self.s, True, None, None, "a pause between periods")
            return True
        s, live = self.s, self.t_live
        back = None if live else self.t_back
        snapped = back is not None and self.t_clock is not None       # the snap's bookkeeping is undone when the timeout is granted
        result = self.rules.timeout_key(s, live, self.undo_snap_clock if snapped else None,
                                        self.clock.snapped_called(self.t_clock) if snapped else None)
        if result == TIMEOUT_GRANTED and back is not None:
            raise PlayWithdrawn(back)
        self.keys.hand_back(result)
        return True

    def go_live(self) -> None:
        """The snap or the kick: a T key already waiting is taken first (it may still withdraw the play), then the play is live."""
        self.keys.service_timeout()
        self.t_live, self.t_back = True, None

    def dead_ball(self, back=None) -> None:
        """A dead-ball moment begins (a menu, a question, a kick-off, the try's choice): a request kept during the live play is granted
        now; `back` is where a timeout goes back to."""
        self.t_live, self.t_back = False, back
        self.rules.grant_kept_timeout(self.s)

    def undo_snap_clock(self) -> None:
        capture, self.t_clock = self.t_clock, None
        if capture is not None:
            self.clock.restore(capture)

    def withdrawn(self, withdrawal: PlayWithdrawn):
        """The step after a timeout before the snap: the computer's choice is forgotten (the repeat counters are as they were), the plays are
        withdrawn and the menu is spoken again from its top."""
        s = self.s
        if self.t_choice is not None:
            s.previous_play, s.repeats = self.t_choice
            self.t_choice = None
        self.rules.withdraw_play(s)
        self.g.qorp, self.g.ptf = 1, 0                 # a kick's set-up speaks as the punter and writes the speech log: neither goes on
        self.t_live, self.t_back = False, None
        debuglog.event("extras", "play_withdrawn", back=getattr(withdrawal.back, "__name__", "?"), quarter=s.quarter, down=s.down)
        return withdrawal.back

    # ----- the speakers, pauses and keys as pag uses them -----

    @property
    def snd(self):
        return self.g.sounds

    @property
    def rnd(self):
        return self.g.rnd

    @property
    def keys(self):
        return self.g.keys

    @property
    def coach(self) -> str:
        return self.g.season.coach

    def rady(self, site: int) -> None:
        self.g.rady(site)

    def dy(self, seconds: float, site: int) -> None:
        self.g.dy(seconds, site)

    def say3(self, text: str) -> None:
        """say3 reads the form variables wisoff and qorp: the Game's copy of wisoff follows the state before it speaks."""
        self.g.wisoff = self.s.wisoff
        self.g.say3(text)

    def _noise_net(self) -> None:
        """GAP_REGISTER G-A2: before a key wait the play noise must not be looping (the original stops it with every
        PlayTackle; the clone stops it after " is way to short", Q57). Counted, so a test proves it never acts."""
        if self.snd.play_noise_running():
            self.noise_net += 1
            log.warning("the play noise was still looping at a key wait: stopped (G-A2)")
            self.snd.stop_play_noise()

    def getkey2(self, net: bool = True) -> None:
        if net:
            self._noise_net()
        self.keys.getkey2(self.g.speech, self.snd)

    def getkey(self) -> None:
        self._noise_net()
        self.keys.getkey(self.g.speech)

    @property
    def g_code(self) -> str:
        return self.keys.code_text

    @property
    def g_char(self) -> str:
        return self.keys.char

    def menu_digit(self) -> int:
        """Val(g2) for the play menus: a main-row digit gives its number; a keypad digit too (D-027, Q32: the original's
        keypad typed letters there); anything else 0."""
        code = self.g_code
        if code.isdigit() and 96 <= int(code) <= 105:
            return int(code) - 96
        char = self.g_char
        return int(char) if len(char) == 1 and char in "0123456789" else 0

    def menu_zero(self) -> bool:
        """The key 0 (main row or keypad): item 10 of the N. F. L. rules offense menu."""
        return self.g_code == "96" or self.g_char == "0"

    # ----- names: Me.m328 running backs, Me.m34c receivers, Me.m370 defense, Me.m394 special teams, Me.m3b8 kickers -----

    def back(self, side: int, n: int) -> str:
        return self.s.rosters[side].running_backs[n - 1]

    def receiver(self, side: int, n: int) -> str:
        return self.s.rosters[side].receivers[n - 1]

    def defender(self, side: int, n: int) -> str:
        return self.s.rosters[side].defense[n - 1]

    def returner(self, side: int, n: int) -> str:
        return self.s.rosters[side].special_teams[n - 1]

    def kicker(self, side: int, n: int) -> str:
        return self.s.rosters[side].kickers[n - 1]

    def qb(self, side: int) -> str:
        return self.s.quarterbacks.get(side, "")

    # ----- the outcome hook (H2) -----

    def outcome(self, kind: str, **fields) -> PlayOutcome:
        """The narration end point of a play: the record goes through Rules.after_outcome (Classic: unchanged)."""
        s = self.s
        self.t_live, self.t_back = False, None       # the play is over: the ball is dead (H18)
        values = dict(yards=s.yards, carrier=s.carrier, defender1=s.defender1, defender2=s.defender2,
                      spot_before=self._spot_before, two_point_try=s.two_point, qb_run=s.qb_run, slid=s.slid)
        values.update(fields)
        record = PlayOutcome(kind, s.wisoff, s.offense_play, s.defense_play, **values)
        s.qb_run, s.slid = "", False                 # the quarterback's play is over (SX.5; Classic never sets them)
        record = self.rules.after_outcome(s, record)
        self.outcomes.append(record)
        self.last_outcome = record
        return record

    def end_point(self, kind: str, **fields):
        """`outcome` at a narration end point, for the steps that go on after it: the step the extras chose when they took
        over the end of the play (an accepted penalty, N. F. L. rules mode, SX.3), else None and the step goes on as the
        original (Classic: always None)."""
        return self.continuation(self.outcome(kind, **fields).then)

    def continuation(self, then):
        """The step for an answer of the extras (game/rules.py NEXT_DOWN and the others); None for None. The extras have
        set the ball, the down and the distance; the log flag a step had switched on is off again."""
        if then is None:
            return None
        s = self.s
        self.g.ptf = 0
        if then == NEXT_DOWN:
            s.text = P.ITS
            return self.position
        if then == ON_DOWNS:
            s.text = P.TURNED_OVER_ON_DOWNS
            s.downs_flag = True
            return self.possession
        if then == SAFETY_BY_PENALTY:
            return self.penalty_safety
        if then == TRY_AGAIN:
            return self.offense_menu
        if then == TRY_FAILS:
            s.try_good = False
            return self.try_result
        if then == KICK_AGAIN:
            return self.kick_off
        if then == PERIOD_END:
            return self.period_checks
        if then == REVIEWED_FIELD:                # N. F. L. rules (SX.6): a review changed the ruling; the extras restored the
            return self.gain_and_end              # board of the end point and set the corrected yards and kind
        if then == REVIEWED_TOUCHDOWN:
            return self.touchdown_reached
        if then == REVIEWED_FUMBLE:
            return self.reviewed_fumble
        if then == SAVE_PENDING:                  # N. F. L. rules (SX.9, C10): S at the accept-or-decline prompt
            return self.save_game
        if then == FAIR_CATCH_KICK:               # N. F. L. rules with a playbook (SX.10d): the player chose the fair catch kick
            return self.fair_catch_kick
        raise ValueError("unknown continuation %r" % (then,))

    def ran(self) -> bool:
        """The play is a run for the ending of the play: the original's runs (plays 1 and 2) and kick-off returns (play 0),
        and the quarterback's runs of the N. F. L. rules mode (a sneak, keeper or draw, or a pass play that became a
        scramble); never in Classic."""
        return self.s.offense_play <= 2 or bool(self.s.qb_run)

    _spot_before: tuple[int, int] = (0, 0)

    def mark_spot(self) -> None:
        self._spot_before = (self.s.half, self.s.yard_line)

    # ----- the run -----

    def run(self) -> GameResult:
        step = self.start()
        while step is not None:
            try:
                step = step()
            except PlayWithdrawn as withdrawal:        # T before the snap (H18): the play is not run, the menu comes again
                step = self.withdrawn(withdrawal)
        return self.result

    def start(self):
        """pag's start (0x43a87e to 0x43bb4c)."""
        g, s = self.g, self.s
        self.get_sex_of()                                   # 0x43aa89
        self.snd.load_ambient()                             # foot9 into the ambient buffer, silent (Q33)
        setup = (g.new_game_setup(self.own_names) if self.opponent_names is None       # GoSub 0x453eac: the rosters, the
                 else g.new_game_setup(self.own_names, self.opponent_names))           # periods, M2W to M5W
        s.gpn = 0 if self.own_names is None else 1
        s.teams = {1: g.own_team(), 2: g.opponent_team()}
        s.rosters = setup.rosters
        if setup.own_names_drawn and self.roster_sink is not None:
            self.roster_sink(setup.rosters[1])               # the original's write of footplay.txt (0x455908 to 0x456f0b)
        s.banter_names = list(setup.banter_names)
        s.plays = list(setup.plays_per_period)
        s.quarter, s.counter = setup.quarter, setup.play_counter
        if self.saved is not None:                           # SavedGame = 1
            g.say(P.GETTING_SAVED_GAME)
            s.load(self.saved)
            g.quarter_clock.countdown = self.saved.countdown
        self.getqbs()
        self.snd.set_crwd1(-100)                            # 0x43b8fe
        self.dy(0.2, 0x43b9d9)
        self.snd.play(0, 0)
        if self.saved is not None:                          # SavedGame = 0, 0x43bb41; N. F. L. rules (SX.9, C10): a choice the
            self.game_on = True                             # the loaded game is in play (H18: T works from its first question)
            if self.saved.resume:                           # SX.14 (NX-S4): an automatic save goes on with the same draws and histories
                if resume.restore(self, self.saved.resume):
                    self.get_sex_of()                       # the voices may have changed since: the He and She words follow them
                    debuglog.event("save", "resumed", draws=self.g.rnd.draws, quarter=s.quarter, counter=s.counter)
            return self.continuation(self.rules.resume_choice(s)) or self.play_menu     # save kept is asked first
        return self.coin_toss

    def get_sex_of(self) -> None:
        """GetSexOf (p_41fb50): " She " for a voice whose Gender is Female, else " He ": own and opponent quarterback,
        own and opponent punter."""
        speech = self.g.speech
        for index, role in ((1, OWN_QUARTERBACK), (2, OPPONENT_QUARTERBACK), (3, OWN_PUNTER), (4, OPPONENT_PUNTER)):
            try:
                gender = speech.role_gender(role)
            except Exception as exc:                        # a voice that cannot be asked counts as " He "
                log.warning("GetSexOf: %s", exc)
                gender = ""
            self.s.he_she[index] = pronoun(gender)

    def getqbs(self) -> None:
        """Getqbs (4.12, game/prompts.py since S7.4a): the own quarterback from footplay.txt (the Roster's last item) or
        asked, the opponent's asked unless a loaded game read footplay.txt. A test may hand the names in instead."""
        if self.quarterback_names is not None:
            own, opponent = self.quarterback_names(self.s)
        else:
            own_from_file = self.own_names.quarterback if self.own_names is not None else ""
            own, opponent = self.g.getqbs(self.s, saved=self.saved is not None, own_from_file=own_from_file)
        self.s.quarterbacks = {1: own, 2: opponent}

    # ----- the coin toss and the opening choice (4.14; 0x43bb4c to 0x43cc63) -----

    def coin_toss(self):
        g, s = self.g, self.s
        own_call = 0                                       # Ldc = 0 (0x43aea1)
        computer_call = 0                                  # L428 = 0
        if g.season.vtrnt != 1:
            own_call = self._call_the_toss()
        else:
            computer_call = self.rnd(2)                    # 0x43c121
            text = P.THE_TEAM + s.teams[2] + P.CALL + (P.HEADS_WORD if computer_call == 1 else P.TAILS_WORD)
            g.say4(text)
            g.log_print(text)
            g.log_print("")
        self.dy(0.2, 0x43c2c8)
        g.say4(P.HERE_IS_THE_COIN_TOSS)
        self.dy(0.3, 0x43c3b3)
        coin = self.rnd(2)                                 # 0x43c471
        g.ptf = 1
        g.say4(P.COIN_COMES_UP + (P.HEADS_WORD if coin == 1 else P.TAILS_WORD))
        g.ptf = 0
        if coin == own_call or (computer_call != 0 and computer_call != coin):
            return self._receive_or_kick()
        g.say4(P.THE_TEAM + s.teams[2] + P.CHOOSE_TO_RECEIVE)
        s.wisoff, s.defense, s.half = 2, 1, 1
        return self.kick_off

    def _call_the_toss(self) -> int:
        """The player calls (vtrnt = 2): heads or tails; returns 1 (heads) or 2 (tails)."""
        g = self.g
        while True:                                        # L_43bb83
            self.keys.clk()
            g.say2(" " + self.coach + P.WHICH_DO_YOU_CALL)
            answer = 1
            while True:                                    # L_43bc8f
                g.say2(P.HEADS if answer == 1 else P.TAILS)
                self.getkey2()
                code = self.g_code
                if code == KEY_ENTER:
                    text = P.THE_TEAM + self.s.teams[1] + P.CALL + (P.HEADS_WORD if answer == 1 else P.TAILS_WORD)
                    g.log_print(text)
                    g.log_print("")
                    return answer
                if code == KEY_F1:
                    break
                if code in (KEY_UP, KEY_DOWN):
                    answer = 2 if answer == 1 else 1
                    continue
                g.saykey()
                if self.g_char == "h":
                    answer = 1
                elif self.g_char == "t":
                    answer = 2
                else:
                    break

    def _receive_or_kick(self):
        """The player won the toss (0x43c76d): receive or kick off."""
        g, s = self.g, self.s
        while True:
            g.say2(" " + self.coach + P.WHICH_DO_YOU_WISH)
            answer = 1
            while True:                                    # L_43c82e
                g.say2(P.RECEIVE if answer == 1 else P.KICK_OFF)
                self.getkey2()
                code = self.g_code
                if code == KEY_ENTER:
                    if answer == 1:
                        s.wisoff, s.defense, s.half = 1, 2, 2
                    else:
                        s.wisoff, s.defense, s.half = 2, 1, 1
                    return self.kick_off
                if code == KEY_F1:
                    break
                if code in (KEY_UP, KEY_DOWN):
                    answer = 2 if answer == 1 else 1
                    continue
                g.saykey()
                if self.g_char == "r":
                    answer = 1
                elif self.g_char == "k":
                    answer = 2
                else:
                    break

    # ----- the play menus (4.15) -----

    def play_menu(self):
        """L_43dd89: the menu of the side with the ball. A safe point (NX-S4): the board is whole, nothing is being said and no draw is
        pending, so the automatic save is written here: after every play, after the period's statistics, after the half time's kick-off."""
        self.autosave()
        return self.defense_menu if self.s.wisoff == 2 else self.offense_menu

    def save_record(self, auto: bool = False) -> SavedGame:
        """What Save Game or the automatic save writes: football.sav's values, the extras, and the summary's facts (the shelf adds the
        date and the slot); an automatic save adds the engine's resume state. Pure: no draw, no speech."""
        s = self.s
        record = s.saved(self.g.quarter_clock.countdown)
        if self.save_ui is not None or self.autosave_sink is not None:     # the program's saves carry their summary; a bare sink's do not
            record.info = json.dumps(make_info(self), separators=(",", ":"))
        if auto:
            text = resume.capture(self)
            if len(text.encode("utf-8")) <= resume.LIMIT_BYTES:      # a String Variant holds 65,535 bytes; a record that is larger goes without
                record.resume = text
            else:
                debuglog.event("save", "resume_too_large", logging.WARNING, bytes=len(text))
        return record

    def autosave(self) -> None:
        """NX-S4: the game in progress is kept in the automatic save at every safe point, whole (a temporary file, then a rename). It
        never draws a number, never speaks, and a failure only goes to the debug log: a game is never stopped for its safety net."""
        if self.autosave_sink is None or not self.game_on:
            return
        try:
            self.autosave_sink(self.save_record(auto=True))
        except GameQuit:                                # the window closed: that is not a failure of the save
            raise
        except Exception:
            log.exception("the automatic save failed: the game goes on without it")

    def _menu(self, items, prompt: str, rebuild=None):
        """The loop of both play menus. Returns ("chosen", action), ("concede", None) or ("step", the engine's next step). An
        item the extras added (an action that is neither a play nor Save Game, N. F. L. rules mode) goes to Rules.menu_action
        and the menu stays: from the top when it was done (with the items made again by `rebuild`: a lost challenge or a
        last time out takes its item away, SX.6), at the same item when it was refused; when it answers a
        continuation (a challenge that changed a ruling, SX.6) the menu is left for that step. Classic's lists have no such
        item and no letter."""
        g, s = self.g, self.s
        current = 1
        speak_prompt = True
        say_item = True
        self.dead_ball()                                   # H18: the ball is dead; a time out kept from the last play is granted first
        while True:
            if speak_prompt:
                heading = self.rules.menu_heading(s)       # SX.10c: the name of an open list of plays (Classic: "", the prompt)
                g.say5(heading or " " + self.coach + prompt)
                speak_prompt = False
            if say_item:
                g.say5(items[current - 1].text)
            say_item = True
            self.getkey2()
            code = self.g_code
            if code == KEY_ENTER:
                action = items[current - 1].action
                if action[0] in (PLAY, SAVE):
                    return "chosen", action
                done = self.rules.menu_action(s, action)
                if done == MENU_REFRESH:                   # SX.10c: a setting changed: the items again, the menu stays at its place
                    if rebuild is not None:
                        items = rebuild()
                    current = min(current, len(items))
                    continue
                if isinstance(done, str):                  # a continuation of the extras (SX.6): the menu is left
                    return "step", self.continuation(done)
                if isinstance(done, tuple):                # a play of a playbook was chosen (SX.7): (PLAY, the original's family)
                    return "chosen", done
                if done:
                    current, speak_prompt = 1, True
                    if rebuild is not None:
                        items = rebuild()
                continue
            if code == KEY_ESCAPE:
                return "concede", None
            if code == KEY_UP:
                current = current - 1 if current > 1 else len(items)
                continue
            if code == KEY_DOWN:
                current = current + 1 if current < len(items) else 1
                continue
            if code in (KEY_BACKSPACE, KEY_LEFT) and self.rules.menu_back(s):    # SX.7: out of a group of plays (Classic: no)
                current, speak_prompt = 1, True
                if rebuild is not None:
                    items = rebuild()
                continue
            if code == KEY_RIGHT and self.rules.menu_right(s, items[current - 1]):   # SX.10c: a family's lists (Classic: no)
                current, speak_prompt = 1, True
                if rebuild is not None:
                    items = rebuild()
                continue
            speak_prompt = True
            if code == KEY_F1:
                how = self.keys.take_resumed()
                if how:                                    # the T key (H18): not F1
                    if how == TIMEOUT_GRANTED:             # a time out was called: the menu starts again from its top
                        current = 1
                        if rebuild is not None:
                            items = rebuild()
                    continue                               # refused: the menu goes on where it was, its prompt said again
                self.field_position()
                continue
            if code == KEY_F2:
                g.inrep()
                continue
            if code == KEY_F3:
                g.say_score(s.score(1), s.score(2))
                continue
            if code == KEY_F4:
                self.clock.speak()
                continue
            digit = self.menu_digit()
            # the key 0 is item 10 of the N. F. L. rules offense menu (digit 0); no Classic item has the digit 0
            chosen = (next((n for n, item in enumerate(items, start=1) if item.digit == digit), 0)
                      if digit or self.menu_zero() else 0)
            # the extras' letters (S, C, and the catalog's F, A, M, K, P, O, N, B); Classic's items have none. Only a letter key types a
            # letter here: the keypad's digits and the function keys have letters as their g2 too (B-W6: F5 is "t", keypad 4 is "d")
            letter = self.g_char.lower() if code.isdigit() and KEY_LETTERS[0] <= int(code) <= KEY_LETTERS[1] else ""
            if not chosen and letter:
                chosen = next((n for n, item in enumerate(items, start=1) if item.letter and item.letter == letter), 0)
            if chosen:
                current = chosen
                speak_prompt = False
                continue
            # a key no item has (SX.6: C says why; SX.10b2: D describes the item; SX.10c: plus and minus, a lone Shift)
            done = self.rules.menu_key(s, letter, items[current - 1], code)
            if done == MENU_REFRESH:                       # a favourite was added or taken off: the items again, the same place
                if rebuild is not None:
                    items = rebuild()
                current = min(current, len(items))
                speak_prompt = False
                continue
            if done == MENU_QUIET:                         # nothing is said: the next key
                speak_prompt = say_item = False
                continue
            if done:
                speak_prompt = False
                continue
            g.saykey()
            current = 1

    def offense_menu(self):
        """L_43ddc0: the player's offense (items 1 to 8; 1 to 5 during a two-point try)."""
        s = self.s
        what, action = self._menu(self.rules.offense_menu(s, s.two_point), P.SELECT_OFFENSE,
                                  lambda: self.rules.offense_menu(s, s.two_point))
        if what == "concede":
            return self.concede
        if what == "step":
            return action
        kind, play = action
        if kind == SAVE:
            return self.save_game
        s.offense_play = play
        return self.offense_chosen

    def defense_menu(self):
        """L_43e9ab: the player's defense (items 1 to 7)."""
        s = self.s
        what, action = self._menu(self.rules.defense_menu(s), P.SELECT_DEFENSE, lambda: self.rules.defense_menu(s))
        if what == "concede":
            return self.concede
        if what == "step":
            return action
        kind, play = action
        if kind == SAVE:
            return self.save_game
        s.defense_play = play
        return self.defense_chosen

    # ----- the computer's play choice (5.7) -----

    def offense_chosen(self):
        """L_43e5be (then the hook that lets the N. F. L. rules mode replace the family by a play of its playbook, design 10.4;
        Classic: nothing, no draw). Every step below returns `snap`, which has not run yet."""
        self.t_choice = (self.s.previous_play, self.s.repeats)     # a time out before the snap takes the choice back (H18)
        step = self._defense_choice()
        self.rules.computer_defense(self.s)
        return step

    def _defense_choice(self):
        """The computer defends: Int(Rnd * 6) + 1, but a play repeated a second time is matched with chance
        1/2 and from the third time on always."""
        s = self.s
        s.defense_play = self.rnd(6)
        if s.previous_play == s.offense_play:
            s.repeats += 1
        else:
            s.repeats = 0
        s.previous_play = s.offense_play
        if s.repeats == 0:
            return self.snap
        if s.repeats <= 1 and self.rnd(2) == 1:            # L588, 0x43e7c0
            return self.snap
        match = DEFENSE_MATCH.get(s.offense_play)      # the original's five plays; with the N. F. L. rules also 8 to 10
        if match is not None:
            s.defense_play = match
        return self.snap

    def defense_chosen(self):
        """L_43f04c: the computer's offense (5.7), then the hook that lets the N. F. L. rules mode replace the drawn play by a
        quarterback run (design 7.4; Classic: nothing, no draw). Every step below returns `snap`, which has not run yet."""
        self.t_choice = (self.s.previous_play, self.s.repeats)     # a time out before the snap takes the choice back (H18)
        step = self._offense_choice()
        self.rules.computer_offense(self.s)
        return step

    def _offense_choice(self):
        """The computer's offense (5.7): 2/9 each for plays 1 to 4, 1/9 the long pass, then the last-play and fourth-down
        rules."""
        s = self.s
        s.previous_play = 0
        x = self.rnd.below(9) + 2                          # L64 = Int(Rnd * 9) + 2
        s.offense_play = x // 2                            # Int(L64 / 2): exact for 2 to 10 in a Single
        if self.clock.is_last_play():
            return self._last_play_rule()
        return self._fourth_down_rule()

    def _last_play_rule(self):
        """L_453cbe: the last play of a period."""
        s = self.s
        if s.quarter in (1, 3) or s.half == 1:
            return self._fourth_down_rule()
        if s.quarter == 2:
            s.offense_play = 6
            return self.snap
        if s.score(1) - s.score(2) >= 4:
            return self._fourth_down_rule()
        s.offense_play = 6
        return self.snap

    def _fourth_down_rule(self):
        """L_43f1b4: downs 1 to 3 keep the drawn play; on fourth down the kick, or "go for it" (Int(Rnd * 4) + 1)."""
        s, clock = self.s, self.clock
        if s.down < 4:
            return self.snap
        s.offense_play = 7
        if s.half == 2 and s.yard_line < 41:
            s.offense_play = 6
        lead = s.score(1) - s.score(2)
        if s.quarter not in (2, 4, 5):                     # quarters 1 and 3
            if s.half == 1 and s.yard_line < 40:
                return self.snap
            if s.to_go > 2 and s.yard_line > 5:
                return self.snap
            if lead > 3 and s.yard_line < 4:
                return self._go_for_it()
            return self._one_in_nine()
        if s.quarter == 5:
            if s.to_go > 2 and s.half == 1:
                return self.snap
            if s.half == 2 and s.yard_line < 25:
                return self.snap
            return self._one_in_nine()
        if s.to_go > 20:                                   # quarters 2 and 4
            return self.snap
        if s.half != 2:
            self.rnd.below(10)                             # L728 = Int(Rnd * 10) + 2, compared with L718 (Q15)
            return self.snap                               # L718 is never set (Empty = 0): always the kick
        if abs(lead) > 14:
            return self._go_for_it()
        if s.quarter != 4:
            if s.half == 2 and clock.plays_left() < 7:
                return self._go_for_it()
            if s.to_go > 5:
                return self.snap
            return self._one_in_nine()
        if s.half == 2 and s.yard_line < 30 and lead < 4:
            return self.snap
        if clock.played() > 20 and lead < 8:
            return self._go_for_it()
        if s.half == 2 and clock.plays_left() < 7:
            return self._go_for_it()
        if s.to_go > 5:
            return self.snap
        return self._one_in_nine()

    def _one_in_nine(self):
        """L_43f56e: go for it when Int(Rnd * 9) + 1 = 7."""
        if self.rnd(9) == 7:
            return self._go_for_it()
        return self.snap

    def _go_for_it(self):
        """L_43fc9d: Line Plunge, End Run, Screen Pass or Short Pass."""
        self.s.offense_play = self.rnd(4)
        return self.snap

    # ----- GoSub 0x458b24: F1 in a play menu, and H13 -----

    def field_position(self) -> None:
        g, s = self.g, self.s
        text = P.F1_ITS + (P.F1_YOUR if s.wisoff == 1 else P.F1_MY) + P.BALL_ON
        text += self._half_word() + self.str_(s.yard_line) + P.YARD_LINE_SPACED
        g.say5(text)
        g.say5(P.F1_ITS_SHORT + self._down_and_distance())
        for line in self.rules.extra_situation(s):
            g.say5(line)

    # ----- small sentence helpers shared by the steps -----

    @staticmethod
    def str_(value) -> str:
        from .vbnum import str_
        return str_(value)

    def _half_word(self) -> str:
        """" the" at midfield, else " my" (the opponent's half) or " your" (the player's half)."""
        s = self.s
        if s.yard_line == 50:
            return P.THE
        return P.MY if s.half == 1 else P.YOUR

    def _down_and_distance(self) -> str:
        """" first down and" ... " to go": the yards as Str$ & "yard" & "s", or " goal" when the ball is in the
        defense's half and the yards to go are at least the distance to the goal line."""
        s = self.s
        text = P.ORDINALS.get(s.down, "") + P.DOWN_AND
        if s.in_own_half() or s.to_go < s.yard_line:
            text += self.str_(s.to_go) + P.YARD_NO_SPACE + (P.PLURAL if s.to_go > 1 else "")
        else:
            text += P.GOAL
        return text + P.TO_GO


__all__ = ["PlayEngine", "GameResult", "other", "own_half"]
