"""Replay challenges, booth reviews and the ruling model of the N. F. L. rules mode (nfl4 only, rule 0.13; NX2, built in SX.6).
This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 6.1, 6.2 and 6.4, NFL_RULES_RESEARCH Part 3 (the 2026 rulebook, Rule 15). The original has no video and no
officials: what the engine narrates IS the ruling on the field. A play with a reviewable aspect (the five of design 6.1) draws
once whether that ruling is right and plain, right but close, or wrong; a wrong one has a TRUTH, the result the officials
should have called, kept with the ruling. Nobody is told: the announcer only hints (pools CHS and CHC), the replay official
reviews the plays of his own (scores, turnovers, a failed fourth down, every play after the two-minute warning, all of overtime:
15-1-2) when the ruling is wrong or close, and the coaches throw the flag on the others while they have a challenge and a time
out (15-1-1). A review changes a ruling only on clear and obvious evidence (15-2-1): a wrong ruling is clear with 85 percent.

The rules as plain functions (no speech, no keys; `candidates` draws nothing): `goal_distance`, `candidates`, `booth_reason`,
`challenges_left` (timeouts.py), `tally`, `moved`. `ReviewFlow` is the game's part: NflRules (extras/nfl_rules.py) owns one per
game and calls it from its hooks:

    rule(state, outcome, board, left_before, flags)   H2 step 4, after the fouls of the play were drawn and told and its live
                                           time was charged: the draw, the hint remark, the booth review. Returns the engine's
                                           next step when the booth reversed the ruling (the board is as it was at the end point
                                           with the truth set, the clock as it was before the live time), else None
    can_challenge / refusal / say_refusal  the menu item and the reasons (NXR-10 to NXR-15)
    player_challenge(state)                H3 menu_action: the question, the review; True (menu goes on) or a continuation
    computer_challenge(state)              H10: the computer's flag (a continuation or None)
    stats_lines(state)                     " Challenges Won" and " Challenges Lost" (C7)

The draws, in order (design 15, as built): after the live time L and the fouls of the play (their draws, their announcement and
the offended team's choice): `below(1000)` once for a play with an eligible aspect (the wrong windows of its aspects first, then
the close ones); for a wrong ruling the truth's yards when it needs them (`below_single(most - fewest) + fewest` of the play's own
row) and `below(100)` against 85 for the evidence; for a wrong or close one `below(100)` for the hint (70 or 50), then the remark's
own draws (comments on); for a close ruling of a booth play `below(100)` against 14; the review's two `rady` pauses and, with
comments on, `rnd(2)` for a remark of RVR or RVC; the computer's flag `below(100)` (80 after a strong hint, 30 after a close one,
only when it has a hint). Classic never reaches any of it.

A play on which a penalty took over (an accepted foul, offsetting fouls, a personal foul enforced on the try) is not ruled: its
result is not the narrated one any more. A play with a flag that was DECLINED (or not offered) is ruled like any other, and a
reversal offers its flags again against the corrected result (15-7-3 Item 3, N2.7): the announcement, the prompt, the computer's
choice, the enforcement all run again from `PenaltyFlow.settle`, with no new foul draw.

What a reversal does: the board of the play's narration end point (the ball moved, the downs not yet applied, the statistics as
the narration counted them) is put back, the ruled result's statistics are taken back and the truth's counted, the clock goes back
to the time left before the ruled play's live time, the corrected result is set in the state and the engine goes on at the step
that applies it (game/rules.py REVIEWED_FIELD: the corrected gain sentence, the end point again, the downs and the position;
REVIEWED_TOUCHDOWN; REVIEWED_FUMBLE), as it would have from a play called right. The second pass through the end point is not ruled
again and draws no new foul; its live time is charged anew.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field

from ..game import outcome as O
from ..game import phrases as P
from ..game.gamestate import other, own_half
from ..game.playtables import PASSES, RUNS
from ..game.rules import REVIEWED_FIELD, REVIEWED_FUMBLE, REVIEWED_TOUCHDOWN
from . import nx_texts as X
from . import remarks
from . import rules_2026 as R
from . import tuning as T
from .clock import period_seconds
from .kick_flow import kicks_on
from .qb_runs import KINDS, SCRAMBLE_KEY, make_entry
from .timeouts import challenges_left

log = logging.getLogger("nfl4.extras")

KEY_ENTER, KEY_TAB, KEY_UP, KEY_DOWN = "13", "9", "38", "40"
KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"

# the categories of design 6.1 and the rulings the player hears (STRINGS_NX NXR-R01 to NXR-R10)
GOAL, LINE, FUMBLE, DOWN, CATCH, BOUNDARY = "goal", "line", "fumble", "down", "catch", "boundary"
PRIORITY = (GOAL, LINE, FUMBLE, DOWN, CATCH, BOUNDARY)      # which aspect a challenge of a play is about, when none was hit
INCOMPLETE, COMPLETE, DOWN_BEFORE, FUMBLED = "NXR-R01", "NXR-R02", "NXR-R03", "NXR-R04"
SHORT_OF_GOAL, CROSSED_GOAL, SHORT_OF_LINE, MADE_THE_LINE, OUT_OF_BOUNDS, IN_BOUNDS = (
    "NXR-R05", "NXR-R06", "NXR-R07", "NXR-R08", "NXR-R09", "NXR-R10")
SCRIMMAGE_PLAYS = (1, 2, 3, 4, 5, 8, 9, 10)                 # the plays with a snap that a ruling can be about (no kicks)
REVERSED, STANDS, CONFIRMED = "reversed", "stands", "confirmed"
# why a coach may not challenge (NXR-10 to NXR-15), in the order the menu says them
REASON_TEXTS = {"overtime": "NXR-13", "warning": "NXR-12", "booth": "NXR-14", "nothing": "NXR-15", "none left": "NXR-10",
                "no timeout": "NXR-11"}
CHALLENGE = "challenge"
CHALLENGE_ACTION = (CHALLENGE, 0)


# ----- the rules, as plain functions -----

@dataclass(frozen=True)
class Candidate:
    """One reviewable aspect of a play: what was called, the opposite, the side the call went against (it gains when the call
    is reversed), how the truth is built (`how`) and the chances per 1000 that the call is wrong or right but close."""
    category: str
    ruled: str                    # the piece (NXR-R01 to NXR-R10) of what the officials called
    corrected: str                # the piece of the opposite call
    against: int                  # the side the call went against: 1 or 2
    how: str                      # "short", "touchdown", "line_short", "line_made", "down", "fumble", "incomplete", "complete"
    wrong: int
    close: int


@dataclass(frozen=True)
class Truth:
    """The result the officials should have called: a play in the field (`kind` "field"), a touchdown or a fumble lost."""
    kind: str                     # "field", "touchdown" or "fumble"
    result_kind: str              # outcome.RUN, PASS_COMPLETE or PASS_INCOMPLETE (a fumble keeps the play's own kind)
    yards: int


def goal_distance(outcome) -> int:
    """The yards from the line of scrimmage of the snap to the defense's goal line."""
    half, yard_line = outcome.spot_before
    return 100 - yard_line if half == own_half(outcome.offense) else yard_line


def is_run(outcome) -> bool:
    """The play is a run for the statistics: the original's runs, the quarterback's runs and a scramble."""
    return bool(outcome.qb_run) or outcome.offense_play <= 2 or outcome.offense_play >= 8


def base_kind(state, outcome) -> str:
    """The kind of play behind a touchdown or a fumble (the engine keeps it in the state), else the outcome's own kind."""
    if outcome.kind in (O.TOUCHDOWN, O.FUMBLE):
        return state.result_kind
    return outcome.kind


def is_throw_away(state, outcome) -> bool:
    """The incompletion is the passer throwing the ball away (the sentence of intentional grounding, NXP-21: the sack the
    original drew turned into a foul or a play with no receiver in it, SX.3)."""
    return state.tackle_sentence == X.text("NXP-21", quarterback=state.quarterbacks.get(outcome.offense, ""))


def _make(category: str, ruled: str, corrected: str, against: int, how: str, rates=None) -> Candidate:
    wrong, close = (rates or T.RULING_RATES)[category]
    return Candidate(category, ruled, corrected, against, how, wrong, close)


def ruling_rates(state) -> dict:
    """SX.6's rates; SX.10e: in a game that plays the catalog the goal line's own (the outcome models end the league's many goal line
    plays a yard or two short or over, three times the original's, D-095)."""
    if kicks_on(state.extras):
        return dict(T.RULING_RATES, **T.RULING_RATES_CATALOG)
    return T.RULING_RATES


def candidates(state, outcome, record) -> list[Candidate]:
    """The reviewable aspects of the play that just ended, in the order of PRIORITY (design 6.1). `state` is the game at the
    narration end point: the ball has moved, the down and the distance are the snap's. No draw."""
    if outcome.two_point_try or outcome.offense_play not in SCRIMMAGE_PLAYS:
        return []
    base = base_kind(state, outcome)
    if base not in (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE):
        return []
    offense, defense = outcome.offense, other(outcome.offense)
    d, y, to_go = goal_distance(outcome), outcome.yards, state.to_go
    found: list[Candidate] = []
    rates = ruling_rates(state)
    if outcome.kind == O.TOUCHDOWN:
        if base != O.PASS_INCOMPLETE and 0 <= y - d <= T.GOAL_REACH:
            found.append(_make(GOAL, CROSSED_GOAL, SHORT_OF_GOAL, defense, "short", rates))
    elif outcome.kind == O.FUMBLE:
        found.append(_make(FUMBLE, FUMBLED, DOWN_BEFORE, offense, "down", rates))
    elif outcome.kind in (O.RUN, O.PASS_COMPLETE):
        short = d - y
        if 1 <= short <= T.GOAL_REACH:
            found.append(_make(GOAL, SHORT_OF_GOAL, CROSSED_GOAL, offense, "touchdown", rates))
        if to_go < d:                                           # the line to gain is not the goal line
            if y >= to_go and y - to_go <= T.LINE_REACH:
                found.append(_make(LINE, MADE_THE_LINE, SHORT_OF_LINE, defense, "line_short", rates))
            elif 0 < to_go - y <= T.LINE_REACH:
                found.append(_make(LINE, SHORT_OF_LINE, MADE_THE_LINE, offense, "line_made", rates))
        found.append(_make(DOWN, DOWN_BEFORE, FUMBLED, defense, "fumble", rates))
        if outcome.kind == O.PASS_COMPLETE:
            if record.out_of_bounds:                            # the receiver ended the play out of bounds: was he in?
                found.append(_make(BOUNDARY, IN_BOUNDS, OUT_OF_BOUNDS, defense, "incomplete", rates))
            else:
                found.append(_make(CATCH, COMPLETE, INCOMPLETE, defense, "incomplete", rates))
    elif outcome.kind == O.PASS_INCOMPLETE:
        if is_throw_away(state, outcome):                       # no receiver was ever near it: there is no catch to rule on
            return []
        if state.tackle_sentence.endswith(P.OUT_OF_BOUNDS):     # the incompletion "catches it out of bounds"
            found.append(_make(BOUNDARY, OUT_OF_BOUNDS, IN_BOUNDS, offense, "complete", rates))
        else:
            found.append(_make(CATCH, INCOMPLETE, COMPLETE, offense, "complete", rates))
    return sorted(found, key=lambda c: PRIORITY.index(c.category))


def plain_choice(found: list[Candidate], outcome) -> Candidate:
    """The aspect a challenge is about when the draw hit none (the ruling is right and plain): the first of PRIORITY, except
    that on a pass the catch (or the side line) is what a coach would be looking at, not whether the runner fumbled."""
    if not is_run(outcome):
        for cand in found:
            if cand.category != DOWN:
                return cand
    return found[0]


def booth_reason(state, outcome, record) -> str:
    """Why the coaches may not challenge this play (15-1-2): "overtime", "warning" (it began after the two-minute warning),
    "booth" (a score, a turnover or a failed fourth down as ruled), else "" (a coach may)."""
    if state.quarter >= 5:
        return "overtime"
    if record.warning_given:
        return "warning"
    if outcome.kind in (O.TOUCHDOWN, O.FUMBLE):
        return "booth"
    if outcome.kind in (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE) and state.down == 4 and outcome.yards < state.to_go:
        return "booth"
    return ""


def ruled_result(state, outcome) -> str:
    """"run", "complete", "incomplete" or "fumble": what the narration counted in the statistics."""
    if outcome.kind == O.FUMBLE:
        return "fumble"
    base = base_kind(state, outcome)
    return {O.RUN: "run", O.PASS_COMPLETE: "complete", O.PASS_INCOMPLETE: "incomplete"}[base]


def tally(stats, result: str, run: bool, yards: int, sign: int) -> None:
    """The original's statistics of a result (sign +1 counts it, -1 takes it back): a run adds a play and its yards, a
    completion a catch and its yards, a fumble lost one more fumble (and, for a pass, the catch the original had counted before
    the fumble test), an incompletion nothing (the attempt was counted at the throw and stays)."""
    if result == "run":
        stats.running_plays += sign
        stats.running_yards += sign * yards
    elif result == "complete":
        stats.completions += sign
        stats.passing_yards += sign * yards
    elif result == "fumble":
        stats.fumbles_lost += sign
        if not run:
            stats.completions += sign


def moved(spot: tuple[int, int], offense: int, yards: int) -> tuple[int, int]:
    """The ball (half, yard line) after `yards` from `spot`, as the original's end of a play moves it (5.11)."""
    half, yard_line = spot
    yard_line = yard_line + yards if half == own_half(offense) else yard_line - yards
    if yard_line >= 50:                                         # past midfield: the other half
        yard_line = 50 - (yard_line - 50)
        half = other(half)
    return half, yard_line


# ----- the board of a play (design 3 H5: the snapshot a challenge goes back to) -----

BOARD_FIELDS = ("wisoff", "defense", "half", "yard_line", "down", "to_go", "yards", "text", "tackle_sentence", "tackle_sound",
                "result_kind", "play_kind", "counter", "punt_flag", "return_flag", "downs_flag", "interception_flag",
                "fumble_flag", "try_good", "points", "two_point", "carrier", "defender1", "defender2", "offense_play",
                "defense_play")


@dataclass
class Board:
    """What a play and its apply step change, as it was at the narration end point: the fields of BOARD_FIELDS, both sides'
    statistics and the quarterback counts (the clock is given back by the live time, the timeouts are never given back)."""
    values: dict
    stats: dict
    qb_runs: list
    qb_yards: list


def capture(state) -> Board:
    return Board({name: getattr(state, name) for name in BOARD_FIELDS}, copy.deepcopy(state.stats),
                 list(state.extras.qb_runs), list(state.extras.qb_yards))


def restore(state, board: Board) -> None:
    for name, value in board.values.items():
        setattr(state, name, value)
    state.stats = copy.deepcopy(board.stats)
    state.extras.qb_runs, state.extras.qb_yards = list(board.qb_runs), list(board.qb_yards)


@dataclass
class Ruling:
    """The ruling on the last play, kept until the next play ends: what a challenge is about and what it would find."""
    number: int                   # the play's number: x.plays at its end point (a later end point makes it stale)
    quarter: int
    primary: Candidate            # the aspect a challenge is about: the one the draw hit, else the first of PRIORITY
    wrong: bool
    clear: bool                   # a wrong ruling that the replay shows clearly and obviously (15-2-1)
    close: bool                   # right, but close
    hint: str                     # "", "strong" or "close": what the announcer let be heard (the computer hears the same)
    truth: Truth | None           # the result the officials should have called (a wrong ruling only)
    reason: str                   # booth_reason: "" when a coach may challenge it
    board: Board
    outcome: object               # the PlayOutcome of the ruled play
    result: str                   # ruled_result
    run: bool
    left_before: int = 0          # the time left in the period before the ruled play's live time L was charged (a reversal restores it)
    left_after: int = 0           # ... and after it: the clock when the play ended (0: the play used the last second of the period)
    flags: list = field(default_factory=list)    # the flags of the play that were declined (N2.7: offered again after a reversal)
    challenged: bool = False      # a coach threw the flag on it (once: a review looks at every aspect, 15-2-2)


class ReviewFlow:
    def __init__(self, rules):
        self.rules = rules
        self.pending: Ruling | None = None
        self.replaying = False         # the play's corrected end point is next: not ruled and not drawn again (module note)
        self.clock_held = False        # a time out was called in this dead-ball period before the reversal: the corrected play's
        #                                runoff is not drawn, the clock stays stopped to the snap (nfl_rules.between_plays)
        self.redo: list = []           # the flags of that play, to be offered again against the corrected result (15-7-3 Item 3)
        self.runoff_due = False        # SX.13 (15-5-2, 4-7-4): a reversal of a play that began after the two-minute warning: when the
        #                                corrected play keeps the clock running, ten seconds run off (nfl_rules.between_plays)
        self.corrected = 0                 # the corrected end points that passed the hook: one for every reversal (the tests)
        self.rulings: list[tuple] = []     # (quarter, category, wrong, close, hint, booth reason): the tests and the calibration
        self.events: list[tuple] = []      # (quarter, "coach" or "booth", side, category, wrong, result, ruled piece, booth reason,
        #                                    time outs the side had when it threw the flag): ditto

    @property
    def game(self):
        return self.rules.game

    @property
    def rnd(self):
        return self.rules.game.rnd

    # ----- the ruling model (design 6.1) -----

    def take_replay(self) -> tuple[bool, list]:
        """The end point that follows a reversal is the corrected play's: (True, the flags of the play to offer again), said once,
        then every end point is ruled again."""
        replaying, redo = self.replaying, self.redo
        self.replaying, self.redo = False, []
        if replaying:
            self.corrected += 1
        return replaying, redo

    def forget(self) -> None:
        self.pending = None

    def rule(self, state, outcome, board: Board, left_before: int, flags: list) -> str | None:
        """H2 step 4, after the live time L and the fouls of the play (a flag that was declined stays with the ruling: a reversal
        offers it again). Returns the engine's next step when the booth reversed the ruling, else None."""
        x = state.extras
        self.pending = None
        found = candidates(state, outcome, x)
        if not found:
            return None
        rnd = self.rnd
        reason = booth_reason(state, outcome, x)
        factor = T.BOOTH_PLAY_WRONG_FACTOR if reason else 1          # a play of the replay official's own is wrong more often
        value = rnd.below(1000)
        hit, wrong = None, False
        total = 0
        for cand in found:
            total += cand.wrong * factor
            if value < total:
                hit, wrong = cand, True
                break
        if hit is None:
            for cand in found:
                total += cand.close
                if value < total:
                    hit = cand
                    break
        primary = hit or plain_choice(found, outcome)
        truth, clear = None, False
        if wrong:
            truth = self.make_truth(primary, state, outcome)
            clear = rnd.below(100) < T.RULING_CLEAR_PERCENT
        hint = ""
        if hit is not None:
            if rnd.below(100) < (T.HINT_STRONG_PERCENT if wrong else T.HINT_CLOSE_PERCENT):
                hint = "strong" if wrong else "close"
        ruling = Ruling(x.plays, state.quarter, primary, wrong, clear, hit is not None and not wrong, hint, truth, reason,
                        board, outcome, ruled_result(state, outcome), is_run(outcome), left_before, x.left, list(flags))
        self.pending = ruling
        self.rulings.append((state.quarter, primary.category, wrong, ruling.close, hint, reason))
        if hint:
            self.say_hint(state, ruling)
        if not reason:
            return None
        if wrong or (ruling.close and rnd.below(100) < T.BOOTH_CLOSE_PERCENT):
            result = self.review(state, ruling, 0)
            self.events.append((state.quarter, "booth", 0, primary.category, wrong, result, primary.ruled, reason, 0))
            self.after_review(state, ruling, result, 0)
            if result == REVERSED:
                return self.reverse(state, ruling)
        return None

    def row(self, state, outcome):
        """The play's own row of the outcome table: the yards a result of it draws (H8)."""
        pair = (outcome.offense_play, outcome.defense_play)
        if outcome.qb_run == SCRAMBLE_KEY:
            return make_entry(SCRAMBLE_KEY, outcome.defense_play)
        modifiers = self.rules.modifiers
        if outcome.offense_play >= 8:
            return modifiers.qb_run(make_entry(KINDS[outcome.offense_play], outcome.defense_play))
        if outcome.offense_play <= 2:
            return modifiers.run(*pair, RUNS[pair])
        return modifiers.pass_(*pair, PASSES[pair])

    def make_truth(self, cand: Candidate, state, outcome) -> Truth:
        """The result the officials should have called. One draw for the yards of a catch or a runner who was down before the
        fumble (`below_single(most - fewest) + fewest` of the play's row, the original's own formula), none otherwise."""
        d = goal_distance(outcome)
        run = is_run(outcome)
        base = O.RUN if run else O.PASS_COMPLETE
        how = cand.how
        if how == "short":
            return Truth("field", base, d - 1)
        if how == "touchdown":
            return Truth("touchdown", base, d)
        if how == "line_short":
            return Truth("field", base, state.to_go - 1)
        if how == "line_made":
            return Truth("field", base, state.to_go)
        if how == "fumble":
            return Truth("fumble", base, 0)
        if how == "incomplete":
            return Truth("field", O.PASS_INCOMPLETE, 0)
        entry = self.row(state, outcome)
        yards = self.rnd.below_single(entry.high - entry.low) + entry.low         # "down" and "complete"
        result = base if how == "down" else O.PASS_COMPLETE
        if yards >= d:
            return Truth("touchdown", result, yards)
        behind = 100 - d                                        # the ball's distance from its own goal line
        return Truth("field", result, max(yards, 1 - behind))

    # ----- the hint -----

    def values(self, state, side: int) -> dict:
        g = self.game
        return {"<team>": state.teams.get(side, ""), "<coach>": g.season.coach,
                "<quarterback>": state.quarterbacks.get(side, "")}

    def say_hint(self, state, ruling: Ruling) -> None:
        pool = "CHS" if ruling.hint == "strong" else "CHC"
        remarks.say_remark(self.game, state, state.extras, pool, self.values(state, ruling.primary.against))

    # ----- the review (design 6.2 and 6.4) -----

    def review(self, state, ruling: Ruling, side: int) -> str:
        """The referee goes under the hood (the replay official stopped the game when `side` is 0): the whistle, the pause, the
        verdict. No game time passes. Returns REVERSED, STANDS (wrong, but not clear and obvious) or CONFIRMED (right)."""
        g = self.game
        g.sounds.play_tackle(8)                                  # foot11, the referee's whistle
        if side == 0:
            self.announce(X.text("NXR-08"))
        self.announce(X.text("NXR-04"))
        g.dy(T.REVIEW_PAUSE)
        g.rady(None)
        g.rady(None)
        if ruling.wrong and ruling.clear:
            result = REVERSED
            self.announce(X.text("NXR-05"))
            self.announce(X.text("NXR-16", ruling=X.text(ruling.primary.corrected)))
        elif ruling.wrong:
            result = STANDS
            self.announce(X.text("NXR-06"))
        else:
            result = CONFIRMED
            self.announce(X.text("NXR-07"))
        return result

    def announce(self, text: str) -> None:
        """A sentence of a review: waited and logged like the play-by-play, but not kept for F2 (N2.6: the instant replay
        speaks the play again, never a review)."""
        g = self.game
        logged, kept = g.ptf, len(g.replay)                      # the log flag: on for the review's sentences, as it was after
        g.ptf = 1
        g.say4(text)
        del g.replay[kept:]
        g.ptf = logged

    def after_review(self, state, ruling: Ruling, result: str, side: int) -> None:
        """What follows the verdict: the lost time out of a challenge that did not change the ruling (also with the Time outs
        switch off: that switch only takes the Time Out item and the computer's own calls away, D-053), then a remark with
        chance 1 in 2 (comments on): RVR after a reversal, RVC after a ruling that stands or is confirmed (RVC03 only after
        a lost challenge)."""
        g, x = self.game, state.extras
        lost = side != 0 and result != REVERSED
        if lost:
            x.timeouts[side - 1] = max(0, x.timeouts[side - 1] - 1)      # charged: one fewer left, one more used
            x.used[side - 1] += 1
            x.called[side - 1] = True                                    # one charged time out a dead-ball period (4-5-1 Item 3)
            self.announce(X.text("NXR-09", team=state.teams.get(side, "")))
        if g.comtog == 0 and self.rnd(T.REVIEW_REMARK_ONE_IN) == 1:
            pool = "RVR" if result == REVERSED else "RVC"
            exclude = () if lost else ("RVC03",)
            remarks.say_remark(g, state, x, pool, self.values(state, ruling.primary.against), exclude=exclude)

    # ----- a reversal -----

    def reverse(self, state, ruling: Ruling) -> str:
        """Put the play's board back, take the ruled result's statistics back and count the truth's, give the clock the live time
        back, set the corrected result in the state and name the step that applies it (game/rules.py)."""
        x, o, t = state.extras, ruling.outcome, ruling.truth
        restore(state, ruling.board)
        stats = state.stats[o.offense]
        tally(stats, ruling.result, ruling.run, o.yards, -1)
        if t.kind == "fumble":
            tally(stats, "fumble", ruling.run, 0, +1)
        else:
            result = {O.RUN: "run", O.PASS_COMPLETE: "complete", O.PASS_INCOMPLETE: "incomplete"}[t.result_kind]
            tally(stats, result, ruling.run, t.yards, +1)
        state.result_kind = t.result_kind
        state.yards = t.yards
        state.two_point = False
        state.qb_run, state.slid = o.qb_run, o.slid
        state.fumble_flag = t.kind == "fumble"
        state.interception_flag = state.downs_flag = state.return_flag = False
        state.punt_flag = 0
        if t.kind == "fumble":
            state.half, state.yard_line = o.spot_before
        else:
            state.half, state.yard_line = moved(o.spot_before, o.offense, t.yards)
        length = period_seconds(x.period, x.postseason)         # the clock goes back to before the ruled play's live time (15-5-1),
        ran_off = max(0, ruling.left_after - x.left)            # less what ran off since the play (the signal time of a time out)
        x.left = max(0, min(length, ruling.left_before) - ran_off)
        self.clock_held = bool(x.called[0] or x.called[1])      # a time out of this dead-ball period (never a lost challenge: that
        x.pending, x.running = 0, False                         # ruling cannot be challenged again) keeps the clock stopped; else
        #                                                         the corrected play draws its own runoff (H10)
        if t.kind == "fumble" or t.result_kind == O.PASS_INCOMPLETE or ruling.primary.category == BOUNDARY:
            x.out_of_bounds = False                             # no run ended at the side line (a fumble, an incompletion, a catch that
        #                                                         was made in or out) in the corrected play; every other reversal keeps the fact
        if x.warning_due and not x.warning_given and x.left > R.WARNING_SECONDS:
            x.warning_due = False
        self.pending = None
        self.replaying, self.redo = True, list(ruling.flags)    # the flags of the play are offered again (15-7-3 Item 3)
        self.runoff_due = bool(x.warning_given)                 # the play began after the two-minute warning (15-5-2)
        return {"field": REVIEWED_FIELD, "touchdown": REVIEWED_TOUCHDOWN, "fumble": REVIEWED_FUMBLE}[t.kind]

    def take_runoff(self) -> bool:
        """True once after a reversal of a play that began after the two-minute warning (15-5-2)."""
        due, self.runoff_due = self.runoff_due, False
        return due

    # ----- the coaches' challenges (design 6.4) -----

    def refusal(self, state, side: int) -> str | None:
        """None when `side`'s coach may challenge the last play now, else the reason: "nothing" (no reviewable ruling on the
        last play, or a play has ended since, or a review looked at it already), "overtime", "warning", "booth" (15-1-2),
        "none left" (15-1-1 (f)), "no timeout" (15-1-1 (d))."""
        x, r = state.extras, self.pending
        if r is None or r.number != x.plays or r.quarter != state.quarter or r.challenged:
            return "nothing"
        if r.reason:
            return r.reason
        if r.left_after <= 0:
            return "nothing"                  # the play that used the last second of a period is over for a coach: a reversal
        #                                       would have to reopen the finished period (the replay official still reviews it)
        if challenges_left(x, side) <= 0:
            return "none left"
        if x.timeouts_of(side) <= 0:                          # (also with the Time outs switch off: the teams keep their time outs
            return "no timeout"                               # for the challenges, D-053)
        return None

    def can_challenge(self, state, side: int) -> bool:
        return self.refusal(state, side) is None

    def say_refusal(self, state, side: int) -> bool:
        """The letter C when the menu has no item for it: say why, and go on with the menu."""
        why = self.refusal(state, side)
        if why is None:
            return False
        self.game.say5(X.text(REASON_TEXTS[why]))
        return True

    def throw(self, state, side: int, ruling: Ruling) -> str | None:
        """The flag is thrown (the coach has been asked or the computer decided): the review, the cost, a remark. Returns the
        continuation of a reversal, else None."""
        x = state.extras
        ruling.challenged = True
        timeouts = x.timeouts_of(side)
        x.chal_used[side - 1] += 1
        result = self.review(state, ruling, side)
        if result == REVERSED:
            x.chal_won[side - 1] += 1
        self.events.append((state.quarter, "coach", side, ruling.primary.category, ruling.wrong, result,
                            ruling.primary.ruled, ruling.reason, timeouts))
        self.after_review(state, ruling, result, side)
        if result == REVERSED:
            return self.reverse(state, ruling)
        return None

    def ask(self, state, ruling: Ruling) -> bool:
        """The player's question (design 6.4, C9): what was ruled, the challenges and time outs he has and what a lost
        challenge costs, then the answer, "no" first; Up, Down or Tab change it, Y says yes and N says no, Enter takes it, F1
        asks again, F2 to F4 as in a play menu, any other key is echoed and the question is asked again (the keypad digits
        type letters in this key model, B-W6: the whole keypad is guarded)."""
        g, keys, x = self.game, self.game.keys, state.extras
        answer = False
        while True:
            keys.clk()
            n, m = challenges_left(x, 1), x.timeouts_of(1)
            status = {(True, True): "NXR-19", (True, False): "NXR-17", (False, True): "NXR-18"}.get((n == 1, m == 1), "NXR-02")
            g.say5(X.text("NXR-01", coach=g.season.coach, ruling=X.text(ruling.primary.ruled)))
            g.say5(X.text(status, n=n, m=m))
            while True:
                g.say5(X.text("NXO-A02") if answer else X.text("NXO-A01"))
                if g.sounds.play_noise_running():                # G-A2: no key wait with the play noise looping
                    g.sounds.stop_play_noise()
                keys.getkey2(g.speech, g.sounds)
                code = keys.code_text
                if code == KEY_ENTER:
                    return answer
                if code in (KEY_UP, KEY_DOWN, KEY_TAB):
                    answer = not answer
                    continue
                if code == KEY_F1:
                    break
                if code == KEY_F2:
                    g.inrep()
                    break
                if code == KEY_F3:
                    g.say_score(state.score(1), state.score(2))
                    break
                if code == KEY_F4:
                    self.rules.clock.speak()
                    break
                keypad = code.isdigit() and 96 <= int(code) <= 111
                char = "" if keypad else keys.char.lower()
                if char == "y":
                    answer = True
                    continue
                if char == "n":
                    answer = False
                    continue
                g.saykey()
                break

    def player_challenge(self, state) -> bool | str:
        """H3 menu_action: True when the menu starts again, a continuation when a reversal changed the play, False when the
        challenge is refused (its reason is said)."""
        if self.say_refusal(state, 1):
            return False
        ruling = self.pending
        if not self.ask(state, ruling):
            return True
        then = self.throw(state, 1, ruling)
        return True if then is None else then

    def computer_challenge(self, state) -> str | None:
        """H10: the coach of the side the ruling went against throws the flag when it may and has heard a hint: with chance 80
        percent after a strong one, 30 after a close-call one (design 6.4, N2.5; it hears what the announcer says, so it can lose
        a challenge on a close call). The hint is a fact of the play: F8 only mutes the announcer for the player, so the
        computer's coach hears it either way and no draw depends on F8 (D-053). Returns the continuation of a reversal, else None."""
        ruling = self.pending
        if ruling is None or not ruling.hint:
            return None
        side = ruling.primary.against
        if side not in self.rules.auto_sides or self.refusal(state, side) is not None:
            return None
        chance = T.COMPUTER_CHALLENGE_STRONG_PERCENT if ruling.hint == "strong" else T.COMPUTER_CHALLENGE_CLOSE_PERCENT
        if self.rnd.below(100) >= chance:
            return None
        self.announce(X.text("NXR-03", team=state.teams.get(side, ""), ruling=X.text(ruling.primary.ruled)))
        return self.throw(state, side, ruling)

    # ----- the statistics (C7) -----

    def stats_lines(self, state) -> list[str]:
        x = state.extras
        lost = [x.chal_used[i] - x.chal_won[i] for i in (0, 1)]
        return [X.text("NXS-04"), "%s %d" % (state.teams.get(1, ""), x.chal_won[0]),
                "%s %d" % (state.teams.get(2, ""), x.chal_won[1]),
                X.text("NXS-05"), "%s %d" % (state.teams.get(1, ""), lost[0]),
                "%s %d" % (state.teams.get(2, ""), lost[1])]
