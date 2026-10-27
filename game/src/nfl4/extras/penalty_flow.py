"""Penalties in a game: the draws, the announcement, the accept-or-decline prompt and the enforcement (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 9 (NX7, built in SX.3). NflRules (extras/nfl_rules.py) owns one PenaltyFlow per game and calls it from
its hooks; the rules of enforcement are the plain functions of extras/penalties.py, the fouls extras/fouls_2026.py, the
player's names and weights penalties.txt (extras/penalty_list.py).

When fouls happen and the draws (design 9.1 and 15, as built):
* H2 step 2 (`at_snap`, plays 1 to 5 and the two-point try): one `below(10000)` against the dead-ball and at-snap rows; a
  hit draws the offender's slot (`rnd(12)` for the offense's backs and receivers, `rnd(17)` for the defense; none for a
  team foul). A dead-ball foul stops the snap after " hut 1 " (FOUL_BEFORE_SNAP, `before_snap_foul`); an at-snap foul
  waits for the end of the play.
* In place of a sack (`grounding`, the hook instead_of_sack): one `below(10000)` against tuning.GROUNDING_PER_10000_SACKS
  times the scale and the player's weight.
* H2 step 4 (`at_end`, the narration end point, before the play's live time L): when no foul is waiting, one
  `below(10000)` against the rows that fit the play (and the after-the-play rows when the offense keeps the ball), the
  slot, the foul's spot when it has one (pass interference: the depth of the throw; a foul by the offense on a run: 2
  yards behind the line to the end of the run; a foul by the receivers on a return: within 25 yards behind its end;
  grounding: the passer 5 to 9 yards behind the line); then with chance 1 in 40 (`rnd(40)`) a foul by the other team, one
  `below(total)` over its fitting rows, and its slot.
* After L (`settle`): the announcement, the choice (the player's prompt, or the computer's rule: no draw), the
  enforcement, and a remark of pool PN with chance 1 in 3 after an accepted penalty (comments on).

What the engine does next is the answer (game/rules.py NEXT_DOWN and the others), or None: the play stands.

Save Game at the prompt (C10, SX.9): S at the player's accept-or-decline prompt keeps the choice in the saved game when both answers give
the team that had the ball a new down before the last second of a period, a quarter or a half (`can_save`; else the prompt says NXP-22 and goes on). The board is
put as if the penalty were declined (what a file opened without the N. F. L. rules plays on), the choice goes into the extras record
(`pending_choice`) and the engine saves (SAVE_PENDING). A loaded game asks it first (`resume`, the hook resume_choice): NXP-23, the flag
again, the same prompt; accepting undoes the play's first down and enforces the penalty as it would have been. The ruling of that play and
the injuries of the rest of it are not kept (a loaded game has no play to challenge, design 12.3); nothing is drawn by the save or the
resume.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import asdict, dataclass, fields, replace

from ..data import debuglog
from ..data.files.savedgame import STATISTICS
from ..game import outcome as O
from ..game.gamestate import own_half
from ..game.playtables import QB_SNEAK
from ..game.rules import (KICK_AGAIN, NEXT_DOWN, ON_DOWNS, PERIOD_END, SAFETY_BY_PENALTY, SAVE_PENDING, TRY_AGAIN, TRY_FAILS)
from . import fouls_2026 as F
from . import nx_texts as X
from . import penalties as PEN
from . import remarks
from . import rules_2026 as R
from . import tuning as T
from .clock import is_warning_period, late_window
from .kick_flow import kicks_on
from .penalty_list import DEFAULT_TABLE

log = logging.getLogger("nfl4.extras")

KEY_ENTER, KEY_TAB, KEY_UP, KEY_DOWN = "13", "9", "38", "40"
KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
ACCEPT, DECLINE, ACCEPT_RUNOFF, YARDS_ONLY = "accept", "decline", "accept with the run off", "accept the yards only"
ANSWER_TEXTS = {ACCEPT: "NXP-A01", DECLINE: "NXP-A02", ACCEPT_RUNOFF: "NXP-A03", YARDS_ONLY: "NXP-A04"}
SAVE = "save the game"        # S at the prompt (SX.9, C10): not an answer of the list, the key that keeps the choice in a saved game
TOUCH_BACK_SPOT = 20          # the original's touch back (5.10)


def position(state, side: int) -> int:
    """The ball's place from `side`'s own goal line (0 to 100)."""
    return state.yard_line if state.half == own_half(side) else 100 - state.yard_line


def place(state, side: int, los: int) -> None:
    """Put the ball `los` yards from `side`'s own goal line (the original's half and yard line)."""
    if los <= 50:
        state.half, state.yard_line = own_half(side), los
    else:
        state.half, state.yard_line = own_half(2 if side == 1 else 1), 100 - los


def late_for_fouls(quarter: int, left: int, period: int = 0, postseason: bool = False) -> bool:
    """4-3-2 (e) 1 and 2: after the two-minute warning of the first half, in the last five minutes of the second half the clock
    starts on the snap after a penalty; overtime as its timing rules say (SX.13: the windows of clock.late_window, 16-1-3 (e),
    16-1-4 (h))."""
    return late_window(quarter, left, period, postseason)


def clock_after_foul(record, quarter: int, keeps: bool, offense_leads: bool | None = None) -> tuple[bool, bool]:
    """(the clock runs to the next snap, it restarts on the ready signal) after a foul (design 5.2, 4-3-2 (e) and (g)):
    as if the foul had not happened (a foul before the snap: as it was), restarting on the ready signal; on the snap in the
    late windows and after an offense foul before the snap in the fourth quarter or the regular season's overtime (3); after
    a ten-second run off on the ready signal (g). SX.13 (4-7-1 Item 2, a specific rule of 4-3-2 (e)(5)): a defense foul before
    the snap that stopped a running clock after the two-minute warning restarts it on the ready signal unless the offense
    chooses the snap: an offense ahead lets it run, one level or behind takes the snap (`offense_leads`; None: not asked)."""
    if record.foul_clock == "runoff":
        return record.left > 0, True
    if (offense_leads is not None and record.foul_clock == "pre" and not record.foul_by_offense and record.was_running
            and record.warning_given and record.left > 0):
        return (True, True) if offense_leads else (False, False)
    base = record.was_running if record.foul_clock == "pre" else keeps
    if late_for_fouls(quarter, record.left, record.period, record.postseason):
        return False, False
    if record.foul_clock == "pre" and record.foul_by_offense and (quarter == 4 or (quarter >= 5 and not record.postseason)):
        return False, False
    return base, base


def result_record(result: PEN.Result) -> dict:
    """A Result as plain JSON values (the kept choice, SX.9)."""
    record = asdict(result)
    for name in ("points", "notes", "pieces"):
        record[name] = list(record[name])
    return record


def result_from(record: dict) -> PEN.Result:
    values = dict(record)
    for name in ("points", "notes", "pieces"):
        values[name] = tuple(values[name])
    return PEN.Result(**{f.name: values[f.name] for f in fields(PEN.Result)})


@dataclass
class Flag:
    foul: F.Foul
    side: int                    # the team that fouled
    slot: int = 0                # 1 to 12 (backs then receivers) or 1 to 17 (defense); 0: a team foul or the passer
    spot: int | None = None      # the foul's spot when it has one (offense's view)


class PenaltyFlow:
    def __init__(self, rules):
        self.rules = rules
        self.down: PEN.Down | None = None     # the down at the snap (or the kick-off)
        self.stats = None                     # the statistics at the snap (a play the penalty erases did not happen)
        self.referee_said = ""                # the referee's last result (ref_result): a note of apply() that repeats it is not said again
        self.qb_stats = None                  # and the quarterback's runs (SX.5)
        self.late: Flag | None = None         # a late hit on a slider waiting for the end of the play (SX.5)
        self.waiting: Flag | None = None      # an at-snap foul, announced at the end of the play
        self.dead: Flag | None = None         # a dead-ball foul before the snap
        self.forced: Flag | None = None       # intentional grounding drawn in place of a sack
        self.flags: list[Flag] = []           # the fouls of the play just ended
        self.try_from_the_one = False         # a personal foul on a touchdown, enforced on the try (14-2-3)
        self.kicks26 = False                  # SX.10d: the kicks of 2026 are played, so their fouls (P34 to P37) can be drawn
        self.events: list[tuple] = []         # (quarter, what, foul ID, side, yards, before the snap): the tests and the
        #                                       calibration count them (what: accepted, declined, offset, major, on the try,
        #                                       not offered)

    @property
    def game(self):
        return self.rules.game

    @property
    def rnd(self):
        return self.rules.game.rnd

    def table(self):
        return getattr(self.game, "foul_table", None) or DEFAULT_TABLE

    # ----- the rates and the draws -----

    def weight(self, foul: F.Foul, offense_play: int, defense_play: int) -> int:
        """The foul's chance per 10,000 plays it can happen on: its rate x 100 x the calibration scale x its play factor
        (design 9.2) x the player's weight in percent (penalties.txt; 0 when off)."""
        factor = 1.0
        if foul.id == "P12":
            factor = {3: T.DPI_SCREEN_FACTOR, 5: T.DPI_LONG_FACTOR}.get(offense_play, 1)
        elif foul.id == "P11" and offense_play == 3:
            factor = T.ICT_SCREEN_FACTOR
        elif foul.id == "P16" and offense_play == 3:
            factor = T.IDP_SCREEN_FACTOR
        elif foul.id == "P14" and defense_play == 4:
            factor = T.RPS_BLITZ_FACTOR
        return int(round(foul.rate * 100 * self.rate_scale() * factor * self.table().percent(foul.id) / 100))

    def rate_scale(self) -> float:
        """SX.3's calibration scale; SX.10e: in a game that plays the catalog its own (the league's play mix has more passes than the
        original's, so the same rates gave more fouls, D-095)."""
        state = getattr(self.rules, "state", None)
        if state is not None and kicks_on(state.extras):
            return T.PENALTY_RATE_SCALE_CATALOG
        return T.PENALTY_RATE_SCALE

    def _weighted(self, rows, offense_play: int, defense_play: int) -> list[tuple[F.Foul, int]]:
        return [(foul, w) for foul in rows if (w := self.weight(foul, offense_play, defense_play)) > 0]

    def draw(self, rows, offense_play: int, defense_play: int) -> F.Foul | None:
        """One `below(10000)` against the cumulative chances of `rows` (no draw when none of them can happen)."""
        weighted = self._weighted(rows, offense_play, defense_play)
        if not weighted:
            return None
        value = self.rnd.below(10000)
        total = 0
        for foul, w in weighted:
            total += w
            if value < total:
                return foul
        return None

    def side_of(self, foul: F.Foul, offense: int) -> int:
        return offense if foul.offense_side else (2 if offense == 1 else 1)

    def slot(self, foul: F.Foul) -> int:
        """The player named: the offense's backs and receivers (12), the defense (17), a kick-off's coverage (the kicking
        team's defense, 17), the receivers' blockers (backs and receivers, 12); none for a team foul or grounding."""
        if foul.team_foul or foul.spot == F.PASS_SPOT:
            return 0
        return self.rnd(12) if foul.offender in (F.OFFENSE, F.RECEIVING) else self.rnd(17)

    def surname(self, state, flag: Flag) -> str:
        roster = state.rosters.get(flag.side)
        if flag.foul.spot == F.PASS_SPOT:
            return state.quarterbacks.get(flag.side, "")
        if roster is None or flag.slot <= 0:
            return ""
        if flag.foul.offender in (F.OFFENSE, F.RECEIVING):
            names = list(roster.running_backs) + list(roster.receivers)
        else:
            names = list(roster.defense)
        return names[flag.slot - 1] if flag.slot <= len(names) else ""

    def between(self, low: int, high: int) -> int:
        return self.rnd.below(high - low + 1) + low

    # ----- H2 step 2: at the snap -----

    def take_snap(self, state) -> None:
        offense = state.wisoff
        self.down = PEN.Down(offense, position(state, offense), state.down, state.to_go, bool(state.two_point))
        self.kicks26 = self.rules.kicks.on(state)
        self.stats = copy.deepcopy(state.stats)
        self.qb_stats = self._qb_stats(state)
        self.waiting = self.dead = self.forced = self.late = None
        self.flags = []

    @staticmethod
    def _qb_stats(state) -> tuple[list, list]:
        x = state.extras
        return list(x.qb_runs), list(x.qb_yards)

    def take_kickoff(self, state) -> None:
        """A kick-off: the receivers (wisoff) are the offense, the return starts at their goal line (5.10)."""
        self.down = PEN.Down(state.wisoff, 0)
        self.kicks26 = self.rules.kicks.on(state)
        self.stats = copy.deepcopy(state.stats)
        self.qb_stats = self._qb_stats(state)
        self.waiting = self.dead = self.forced = self.late = None
        self.flags = []
        self.try_from_the_one = False

    def at_snap(self, state, offense_play: int, defense_play: int) -> bool:
        """The draw before the snap. True: a dead-ball foul, the play is not run."""
        if not (1 <= offense_play <= 5 or offense_play >= QB_SNEAK):     # no snap count before a kick (SX.5: plays 8 to 10 snap)
            return False
        rows = [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]
        foul = self.draw(rows, offense_play, defense_play)
        if foul is None:
            return False
        flag = Flag(foul, self.side_of(foul, state.wisoff), self.slot(foul))
        if F.DEAD in foul.phases:
            self.dead = flag
            return True
        self.waiting = flag
        return False

    def slider_hit(self, state, one_in: int) -> bool:
        """SX.5 (design 7.3): after a slide, a late hit on the slider with chance 1 in `one_in`: unnecessary roughness by the
        defense (P18, 12-2-8 (d)), called after the play like the fouls of the table. One `below(one_in)` per slide; for a hit
        the defender's slot `rnd(17)`. It waits for the end of the play (`late`) and `at_end` folds it in: the only flag, or
        the second flag of the other team (the double foul rules decide), never a second flag of the same team (14-1-3).
        Like every foul after the play it is not drawn on a try (14-2-3 would carry it to the kick-off) nor when the offense
        does not keep the ball (a gain short of the line to gain on fourth down turns it over on downs)."""
        if self.down is None or self.down.two_point:
            return False
        if state.down >= 4 and state.yards < state.to_go:
            return False
        if self.rnd.below(one_in) != 0:
            return False
        foul = next(f for f in F.BY_ID["P18"] if f.offender == F.DEFENSE)
        self.late = Flag(foul, 2 if state.wisoff == 1 else 1, self.rnd(17))
        return True

    def grounding(self, state) -> bool:
        """In place of a sack: intentional grounding with chance 1 in 12 (times the scale and the player's weight)."""
        foul = F.GROUNDING
        chance = int(round(T.GROUNDING_PER_10000_SACKS * self.rate_scale() * self.table().percent(foul.id) / 100))
        if chance <= 0 or self.rnd.below(10000) >= chance:
            return False
        self.forced = Flag(foul, state.wisoff)
        return True

    # ----- H2 step 4: the fouls of the play (before L) -----

    def facts(self, state, outcome) -> PEN.PlayFacts | None:
        """What the play did, for the enforcement; None for a play no foul can be called on (the field goal that is way
        too short)."""
        down = self.down
        kind = outcome.kind
        base = state.result_kind
        offense = down.offense
        if kind == O.FIELD_GOAL_SHORT:
            return None
        kicks = self.rules.kicks
        if self.kicks26 and kind == O.PUNT and kicks.muffed:
            return None                            # SX.10d: a muffed punt the kicking team kept: no foul is drawn (a recorded simplification)
        if kind in (O.TOUCHDOWN, O.SAFETY_KIND, O.TWO_POINT_TRY, O.FUMBLE):
            under = O.KICKOFF_RETURN if (kind == O.TOUCHDOWN and outcome.offense_play == 0) else base
        else:
            under = kind
        score = outcome.score
        if kind == O.TOUCHDOWN:
            end = 100
        elif kind == O.SAFETY_KIND:
            end = 0
        elif kind == O.KICKOFF_TOUCH_BACK:
            end = position(state, offense) if self.kicks26 else TOUCH_BACK_SPOT     # SX.10d: the engine put the ball at the 35, the 40, ...
        elif kind in (O.PUNT, O.FIELD_GOAL_GOOD, O.FIELD_GOAL_MISSED, O.INTERCEPTION, O.FUMBLE):
            end = down.los
        elif kind == O.TWO_POINT_TRY:
            end = 100 if score else position(state, offense)
        else:
            end = position(state, offense)
        missed26 = kind == O.FIELD_GOAL_MISSED and self.kicks26          # SX.10d (G26-7): the engine put the ball at the kick's spot
        receivers = position(state, 2 if offense == 1 else 1) if kind == O.PUNT or missed26 else 0
        return PEN.PlayFacts(under, end, score, bool(outcome.turnover and kind != O.PUNT
                                                     and kind != O.FIELD_GOAL_MISSED), receivers,
                             outcome.offense_play, outcome.defense_play)

    def rows_for(self, facts: PEN.PlayFacts, after: bool) -> list[F.Foul]:
        if facts.kind in (O.FIELD_GOAL_GOOD, O.FIELD_GOAL_MISSED):
            key = F.FIELD_GOAL
        elif facts.turnover and facts.kind != O.INTERCEPTION:
            key = facts.kind                       # a fumble: the fouls of the play it ended
        else:
            key = facts.kind
        caught = self.rules.kicks.caught               # SX.10d: kick catch interference only on a punt the receivers caught
        rows = [f for f in F.FOULS if key in f.phases and (self.kicks26 or not f.kicks2026)
                and (f.spot != F.CATCH_SPOT or caught)]
        if after:
            rows += [f for f in F.FOULS if F.AFTER in f.phases]
        if self.down.two_point:                    # personal fouls on a try go to the kick-off: not drawn (D-050)
            rows = [f for f in rows if not f.personal and F.AFTER not in f.phases]
        return rows

    def after_allowed(self, facts: PEN.PlayFacts) -> bool:
        """The fouls after the play: on a play that ends in the field of play and leaves the offense the ball."""
        if self.down.two_point or facts.kind not in F.FIELD_PLAYS or facts.turnover or facts.score:
            return False
        result = PEN.play_result(self.down, facts)
        return result.kind == PEN.NEW_DOWN and result.ball == self.down.offense

    def draw_spot(self, flag: Flag, facts: PEN.PlayFacts) -> None:
        foul, los = flag.foul, self.down.los
        if foul.spot == F.PASS_SPOT:
            flag.spot = los - self.between(*T.GROUNDING_DROP)
        elif foul.id == "P12":
            depth = T.DPI_DEPTH_LONG if facts.offense_play == 5 else T.DPI_DEPTH_SHORT
            flag.spot = los + self.between(*depth)
        elif foul.offender == F.RECEIVING and facts.kind == O.KICKOFF_RETURN:
            end = min(facts.end, 99)
            flag.spot = self.between(max(1, end - T.RETURN_FOUL_REACH), max(1, end))
        elif foul.spot == F.THREE_AND_ONE and facts.kind == O.RUN and not facts.turnover and facts.end > los:
            flag.spot = self.between(los - T.RUN_FOUL_BEHIND, facts.end)

    def at_end(self, state, outcome) -> PEN.PlayFacts | None:
        """The draws at the narration end point (design 15 step 3). The fouls go to `self.flags`."""
        self.flags = []
        if self.down is None:
            return None
        facts = self.facts(state, outcome)
        if facts is None:
            self.waiting = self.forced = self.late = None
            return None
        first = self.forced or self.waiting
        also = self.waiting if self.forced is not None else None   # an at-snap foul and grounding on one play
        late, self.late = self.late, None
        if late is not None:                                       # SX.5: a late hit on the slider
            if first is None:
                first = late
            elif also is None and first.side != late.side:
                also = late                                         # fouls by both teams: the double foul rules decide
        self.forced = self.waiting = None
        if also is not None and also.side != first.side:
            self.draw_spot(first, facts)
            self.flags = [first, also]                                # fouls by both teams: no third draw (14-5-1)
            return facts
        rows = None                                                   # (by one team: one penalty, grounding, 14-1-3)
        if first is None:
            rows = self.rows_for(facts, self.after_allowed(facts))
            foul = self.draw(rows, facts.offense_play, facts.defense_play)
            if foul is None:
                return facts
            first = Flag(foul, self.side_of(foul, self.down.offense), self.slot(foul))
            self.draw_spot(first, facts)
        elif first.foul.spot == F.PASS_SPOT:
            self.draw_spot(first, facts)
        self.flags = [first]
        if self.rnd(T.SECOND_FOUL_CHANCE) == 1:
            if rows is None:
                rows = self.rows_for(facts, self.after_allowed(facts))
            others = [f for f in rows if self.side_of(f, self.down.offense) != first.side]
            weighted = self._weighted(others, facts.offense_play, facts.defense_play)
            total = sum(w for _, w in weighted)
            if total > 0:
                value = self.rnd.below(total)
                for foul, w in weighted:
                    value -= w
                    if value < 0:
                        self.flags.append(Flag(foul, self.side_of(foul, self.down.offense), self.slot(foul)))
                        break
        return facts

    def redo(self, state, outcome, flags: list[Flag]) -> PEN.PlayFacts | None:
        """N2.7 (15-7-3 Item 3, SX.6): a review changed the ruling of a play whose flags were declined: the same flags are offered
        again against the corrected result, so no foul is drawn. A foul by the offense on a run keeps its spot inside the
        corrected run. Returns the facts of the corrected play (None: no foul can be called on it)."""
        facts = self.facts(state, outcome)
        self.flags = list(flags) if facts is not None else []
        for flag in self.flags:
            if (flag.spot is not None and flag.foul.spot == F.THREE_AND_ONE and facts.kind == O.RUN and not facts.turnover
                    and facts.end > self.down.los):
                flag.spot = max(self.down.los - T.RUN_FOUL_BEHIND, min(flag.spot, facts.end))
        return facts

    # ----- the announcement -----

    def announce(self, state, flags: list[Flag], dead: bool) -> None:
        g = self.game
        g.ptf = 1
        if flags:
            self.rules.stadium.penalty(state, flags[0].side)     # the crowd answers the flag as it is thrown (2026-10-23)
        say = self.rules.ref_says                    # SY.3: the referee's microphone (the announcer's say4 when the broadcast is off)
        if dead:
            say(X.text("NXP-02"), last=False)
        say(X.text("NXP-01"), last=False)
        for index, flag in enumerate(flags):
            name = self.table().name(flag.foul.id)
            team = state.teams.get(flag.side, "")
            surname = self.surname(state, flag)
            last = index == len(flags) - 1
            if surname:
                say(X.text("NXP-03", foul_name=name, team=team, surname=surname), last=last)
            else:
                say(X.text("NXP-15", foul_name=name, team=team), last=last)
        g.ptf = 0

    # ----- the choice -----

    def decide(self, state, flag: Flag, accepted: PEN.Result, declined: PEN.Result,
               runoff: PEN.Result | None = None, can_save: bool = False) -> str:
        """The offended team's answer: the computer's rule for a side the computer plays, else the player's prompt (SAVE: S kept the
        choice in a saved game, only when `can_save`)."""
        offended = 2 if flag.side == 1 else 1
        if runoff is not None:
            lead = state.score(offended) - state.score(flag.side)
            best = ACCEPT_RUNOFF if PEN.takes_runoff(offended, lead) else YARDS_ONLY
        else:
            best = ACCEPT if PEN.computer_accepts(offended, accepted, declined) else DECLINE
        if offended in self.rules.auto_sides:
            g = self.game
            team = state.teams.get(offended, "")
            self.rules.ref_says(X.text("NXP-07" if best == DECLINE else "NXP-06", team=team))
            return best
        return self.ask(state, flag, accepted, declined, runoff, best, can_save)

    def ask(self, state, flag: Flag, accepted: PEN.Result, declined: PEN.Result, runoff: PEN.Result | None,
            best: str, can_save: bool = False) -> str:
        """The prompt (design 9.3, C9): what accepting and what declining gives, then the answer, starting at the better
        one by the computer's own rule. Up, Down or Tab change it, A accepts and D declines, Enter takes it, F1 says the
        flag and the prompt again, F2 to F4 as in a play menu, S saves the game with the choice kept (SX.9, C10; when it
        cannot be kept, NXP-22 and the answer again), any other key is echoed and the prompt is said again."""
        g, keys = self.game, self.game.keys
        choices = [ACCEPT_RUNOFF, YARDS_ONLY, DECLINE] if runoff is not None else [ACCEPT, DECLINE]
        current = choices.index(best)
        offense = self.down.offense
        while True:
            keys.clk()
            g.say5(X.text("NXP-04", coach=g.season.coach, situation=PEN.situation(accepted, offense)))
            if runoff is not None:
                left = state.extras.left - R.RUNOFF_SECONDS          # what accepting with the run off leaves
                g.say5(X.text("NXP-19") if left <= 0 else X.text("NXP-18") if left == 1 else X.text("NXP-17", n=left))
            g.say5(X.text("NXP-05", situation=PEN.situation(declined, offense)))
            while True:
                g.say5(X.text(ANSWER_TEXTS[choices[current]]))
                if self.game.sounds.play_noise_running():    # G-A2: no key wait with the play noise looping
                    self.game.sounds.stop_play_noise()
                keys.getkey2(g.speech, g.sounds)
                code = keys.code_text
                if code == KEY_ENTER:
                    return choices[current]
                if code in (KEY_UP, KEY_TAB):
                    current = (current - 1) % len(choices) if code == KEY_UP else (current + 1) % len(choices)
                    continue
                if code == KEY_DOWN:
                    current = (current + 1) % len(choices)
                    continue
                if code == KEY_F1:
                    self.announce(state, [flag], False)
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
                keypad = code.isdigit() and 96 <= int(code) <= 105      # the keypad types letters in this key model
                char = "" if keypad else keys.char.lower()
                if char == "a":
                    current = 0
                    continue
                if char == "d":
                    current = len(choices) - 1
                    continue
                if char == "s":
                    if can_save:
                        return SAVE
                    g.say5(X.text("NXP-22"))
                    continue
                g.saykey()
                break

    # ----- the enforcement -----

    def apply(self, state, flag: Flag | None, result: PEN.Result) -> str | None:
        """Put an accepted result into the game: the statistics, the ball, the down and the distance, the sentences after
        the penalty; returns the engine's next step."""
        x, g = state.extras, self.game
        down = self.down
        offense = down.offense
        if flag is not None:
            x.flags[flag.side - 1] += 1
            x.flag_yards[flag.side - 1] += result.yards
        if not result.keeps_play and self.stats is not None:
            state.stats = copy.deepcopy(self.stats)             # the play the penalty erased did not happen
            if self.qb_stats is not None:
                x.qb_runs, x.qb_yards = list(self.qb_stats[0]), list(self.qb_stats[1])
        if result.kind == PEN.NEW_DOWN and result.keeps_play and result.play_first_down:
            state.stats[result.ball].first_downs += 1            # as the original counts the play's first down
        if result.kind == PEN.NEW_DOWN and result.penalty_first_down:
            state.stats[result.ball].first_downs += 1            # a first down by penalty
        state.interception_flag = state.fumble_flag = state.downs_flag = False
        state.punt_flag = 0
        state.return_flag = False
        said_by_referee, self.referee_said = self.referee_said, ""
        for note in result.notes:
            if said_by_referee and note.strip().rstrip(".").strip() in said_by_referee:
                continue                                         # the referee's result has just said it (rule 0.28 (3))
            g.say4(note)
        if result.untimed:
            x.extension = True
        if result.kind == PEN.NEW_DOWN:
            place(state, result.ball, result.los)
            if result.ball != offense:                           # loss of down on fourth down: the ball goes over
                state.wisoff = offense
                state.defense = 2 if offense == 1 else 1
                return ON_DOWNS
            state.wisoff, state.defense = offense, (2 if offense == 1 else 1)
            state.down, state.to_go = (1, 10) if result.new_series else (result.down, result.to_go)
            return NEXT_DOWN
        if result.kind == PEN.SAFETY:
            x.safety_kick = True                                 # the team scored upon kicks from its own 20 (SX.4)
            return SAFETY_BY_PENALTY
        if result.kind == PEN.TRY_AGAIN:
            place(state, offense, result.los)
            state.two_point = True
            state.try_good = False
            return TRY_AGAIN
        if result.kind == PEN.TRY_FAILS:
            return TRY_FAILS
        if result.kind == PEN.REPLAY_KICK:
            x.kick_again = True                                  # the kick keeps its kind (SX.4); an onside kick made
            x.kick_back = result.yards                           # again is made from the yards back (6-3-1)
            return KICK_AGAIN
        return None

    def note(self, state, what: str, flag: Flag | None, yards: int = 0, pre: bool = False) -> None:
        self.events.append((state.quarter, what, flag.foul.id if flag else "", flag.side if flag else 0, yards, pre))

    def remark(self, state, flag: Flag) -> None:
        g = self.game
        if g.comtog == 0 and self.rnd(T.PENALTY_REMARK_CHANCE) == 1:
            values = {"<team>": state.teams.get(flag.side, ""), "<coach>": g.season.coach,
                      "<quarterback>": state.quarterbacks.get(flag.side, ""), "<surname>": self.surname(state, flag)}
            remarks.say_remark(g, state, state.extras, "PN", values)
        self.rules.broadcast.penalty(state, flag.side)          # SY.1: the analyst's own line after an accepted penalty (his own draws)

    @staticmethod
    def half_over(state) -> bool:
        """The play used the last second of a half: the second or fourth quarter, or the regular season's one overtime period, which ends
        the game by its clock (SX.13: 16-1-3 (d), (e); a play-off overtime period goes on into the next with the ball, 16-1-4 (d))."""
        return state.extras.left <= 0 and (state.quarter in (2, 4) or (state.quarter >= 5 and not state.extras.postseason))

    def extends(self, state, flag: Flag) -> bool:
        """4-8-2 (a): an accepted live foul by the defense on the last play of a half gives one untimed down."""
        return (not flag.foul.offense_side and F.AFTER not in flag.foul.phases and self.half_over(state)
                and not self.down.two_point)

    def double_extends(self, state, flags: list, result: PEN.Result, enforced) -> bool:
        """4-8-2 (h) (SX.13): a double foul on the last down of a half extends it by an untimed down, except when both fouls are dead-ball
        fouls (1), a major foul enforced against a minor one is the offense's or a dead-ball foul (2), the defense's only foul is a
        dead-ball foul (3), or the down is not played again after a change of possession (4: the play stands)."""
        if not self.half_over(state) or self.down.two_point or result.kind != PEN.NEW_DOWN:
            return False
        if all(F.AFTER in f.foul.phases for f in flags):
            return False
        defense = [f for f in flags if f.side != self.down.offense]
        if defense and all(F.AFTER in f.foul.phases for f in defense):
            return False
        if enforced is not None:
            major = flags[0] if flags[0].foul is enforced else flags[1]
            return major.side != self.down.offense and F.AFTER not in major.foul.phases
        return True

    def settle(self, state, outcome, facts: PEN.PlayFacts | None) -> str | None:
        """After L: the fouls of the play announced, chosen and enforced. Returns the engine's next step or None."""
        flags, self.flags = self.flags, []
        if facts is None or not flags:
            return None
        x, g = state.extras, self.game
        x.foul_clock = "live"
        x.foul_by_offense = flags[0].side == self.down.offense
        self.rules.game.sounds.whistle_context = "penalty"
        self.rules.game.sounds.play_tackle(8)                    # the whistle (foot11)
        self.announce(state, flags, False)
        if len(flags) == 2:
            result, enforced = PEN.double_foul(flags[0].foul, flags[1].foul, self.down, facts)
            if self.double_extends(state, flags, result, enforced):
                result = replace(result, untimed=True, notes=result.notes + (X.text("NXP-14"),))
            if enforced is None:
                self.rules.ref_says(X.text("NXP-08"))
                self.note(state, "offset", flags[0])
                self.note(state, "offset", flags[1])
                if result.kind == PEN.PLAY_STANDS:
                    return None
                return self.apply(state, None, result)
            self.rules.ref_says(X.text("NXP-20"))
            flag = flags[0] if flags[0].foul is enforced else flags[1]
            self.note(state, "major", flag, result.yards)
            return self.apply(state, flag, result)
        flag = flags[0]
        how, accepted, declined = PEN.answers(flag.foul, self.down, facts, flag.spot)
        if accepted.kind == PEN.REPLAY_KICK and self.half_over(state):
            how = PEN.AUTO_DECLINE                     # no kick is made again when the half is over: a foul by the kicking
            #                                            team does not extend a period (4-8-2 (a) is for the defense)
        if how == PEN.AUTO_DECLINE:                    # no real choice: said as the officials say it
            self.note(state, "not offered", flag)
            self.rules.ref_says(X.text("NXP-07", team=state.teams.get(2 if flag.side == 1 else 1, "")))
            return None
        if how == PEN.ON_THE_TRY:
            self.note(state, "on the try", flag)
            self.rules.ref_says(X.text("NXP-16"))
            x.flags[flag.side - 1] += 1
            self.try_from_the_one = True
            self.remark(state, flag)
            return None
        if self.extends(state, flag) and accepted.kind == PEN.NEW_DOWN:
            accepted = replace(accepted, untimed=True, notes=accepted.notes + (X.text("NXP-14"),))
        if self.half_over(state):                      # the play used the last second: the half ends after it
            if declined.kind == PEN.NEW_DOWN:
                declined = replace(declined, pieces=declined.pieces + (X.text("NXP-S08"),))
            if accepted.kind == PEN.NEW_DOWN and not accepted.untimed:
                accepted = replace(accepted, pieces=accepted.pieces + (X.text("NXP-S08"),))
        answer = self.decide(state, flag, accepted, declined, can_save=self.can_save(state, accepted, declined))
        if answer == SAVE:
            return self.suspend(state, flag, accepted, declined)
        if answer == DECLINE:
            self.note(state, "declined", flag)
            self.ref_result(state, flag, False, declined)
            return None
        self.note(state, "accepted", flag, accepted.yards)
        self.ref_result(state, flag, True, accepted)
        then = self.apply(state, flag, accepted)
        self.remark(state, flag)
        return then

    def ref_result(self, state, flag: Flag, accepted: bool, result: PEN.Result) -> None:
        """The referee's last words on the foul, as an NFL referee says them (a tester, 2026-10-23: "you don't hear the referee announcement
        of a penalty"): accepted or declined, the yards, and the down that follows. After the computer's own answer (NXP-06, NXP-07) the
        accepted or declined is not said twice."""
        offended = 2 if flag.side == 1 else 1
        by_computer = offended in self.rules.auto_sides
        situation = PEN.situation(result, self.down.offense)
        if accepted:
            yards = abs(int(result.yards or 0))
            if by_computer:
                text = X.text("NXP-26", yards=yards, situation=situation) if yards else X.text("NXP-27", situation=situation)
            else:
                text = X.text("NXP-24", yards=yards, situation=situation) if yards else X.text("NXP-28", situation=situation)
        else:
            text = X.text("NXP-27", situation=situation) if by_computer else X.text("NXP-25", situation=situation)
        debuglog.event("penalty", "referee_result", foul=flag.foul.id, accepted=accepted, by_computer=by_computer, text=text)
        self.referee_said = text
        self.rules.ref_says(text)

    # ----- Save Game at the prompt (C10, SX.9) -----

    def can_save(self, state, accepted: PEN.Result, declined: PEN.Result) -> bool:
        """The choice can be kept in a saved game: both answers give the team that had the ball a new down (the board the loaded game
        starts from is a down to play), not on a try, not on the last second of a half or a quarter (the period's end and the untimed
        down belong to the play just run)."""
        down = self.down
        return (down is not None and not down.two_point and state.extras.left > 0
                and accepted.kind == declined.kind == PEN.NEW_DOWN and accepted.ball == declined.ball == down.offense
                and not accepted.untimed and accepted.erased_score is None)

    def suspend(self, state, flag: Flag, accepted: PEN.Result, declined: PEN.Result) -> str:
        """S at the prompt: the board as if the penalty were declined (the play stands, its first down counted as the original counts
        it), the choice kept in the extras record, and the engine saves the game."""
        x = state.extras
        pending = {"foul": F.FOULS.index(flag.foul), "id": flag.foul.id, "side": flag.side, "slot": flag.slot, "spot": flag.spot,
                   "down": asdict(self.down), "accepted": result_record(accepted), "declined": result_record(declined),
                   "stats": [[int(getattr(self.stats[side], name)) for name in STATISTICS] for side in (1, 2)],
                   "qb": [list(self.qb_stats[0]), list(self.qb_stats[1])]}
        self.apply(state, None, replace(declined, keeps_play=True))
        x.pending_choice = pending
        self.note(state, "kept in the save", flag)
        log.info("penalty choice kept in the saved game: %s by side %d", flag.foul.id, flag.side)
        return SAVE_PENDING

    def resume(self, state) -> str | None:
        """A loaded game's kept choice (or a Save Game that could not write the file): NXP-23, the flag again, the prompt. Declining
        leaves the board as it is (the play stood); accepting takes back the play's first down and enforces the penalty from the down
        of the snap, as the prompt would have. S keeps it again. The engine's next step."""
        x, g = state.extras, self.game
        pending, x.pending_choice = x.pending_choice, None
        if pending is None:
            return None
        flag = Flag(F.FOULS[pending["foul"]], pending["side"], pending["slot"], pending["spot"])
        self.down = PEN.Down(**pending["down"])
        accepted, declined = result_from(pending["accepted"]), result_from(pending["declined"])
        snap = copy.deepcopy(state.stats)
        for side in (1, 2):
            for name, value in zip(STATISTICS, pending["stats"][side - 1]):
                setattr(snap[side], name, value)
        self.stats = snap
        self.qb_stats = (list(pending["qb"][0]), list(pending["qb"][1]))
        log.info("a kept penalty choice is asked again: %s by side %d, down %d and %d from %d", flag.foul.id, flag.side, self.down.down,
                 self.down.to_go, self.down.los)
        g.say5(X.text("NXP-23"))
        self.announce(state, [flag], False)
        answer = self.decide(state, flag, accepted, declined, can_save=True)
        log.info("the kept penalty choice is answered: %s", answer)
        if answer == SAVE:
            x.pending_choice = pending
            self.note(state, "kept in the save", flag)
            return SAVE_PENDING
        if answer == DECLINE:
            self.note(state, "declined", flag)
            return NEXT_DOWN
        if declined.play_first_down:               # the play's own first down, counted when the board was put
            state.stats[declined.ball].first_downs -= 1
        self.note(state, "accepted", flag, accepted.yards)
        then = self.apply(state, flag, accepted)
        self.remark(state, flag)
        return then

    # ----- a dead-ball foul before the snap -----

    def before_snap_foul(self, state) -> str:
        """FOUL_BEFORE_SNAP: the engine said the snap count up to " hut 1 ". The whistle, the flag, the enforcement (no
        choice: declining would only replay the same down), except an offense foul with the clock running after the
        two-minute warning, where the defense chooses the ten-second run off, the yards only, or to decline (4-7-1)."""
        flag, self.dead = self.dead, None
        x, g = state.extras, self.game
        x.plays += 1                                   # a new dead-ball period: H10 runs for it
        x.no_snap = True
        x.was_running = x.running
        x.running = False
        x.foul_clock = "pre"
        x.foul_by_offense = flag.foul.offense_side
        if x.extension_snap:                           # the untimed down was not played: still due
            x.extension = True
        g.sounds.whistle_context = "penalty"
        g.sounds.play_tackle(8)
        g.sounds.c2df()
        self.announce(state, [flag], True)
        how, accepted, declined = PEN.answers(flag.foul, self.down, None)
        runoff_due = (flag.foul.offense_side and flag.foul.code not in R.NO_RUNOFF_FOULS and x.was_running
                      and x.left > 0 and not self.down.two_point
                      and is_warning_period(x.period, x.postseason) and x.warning_given)
        if runoff_due:
            answer = self.decide(state, flag, accepted, declined, runoff=accepted)
            if answer == DECLINE:
                self.note(state, "declined", flag, pre=True)
                return NEXT_DOWN
            self.note(state, "accepted", flag, accepted.yards, pre=True)
            if answer == ACCEPT_RUNOFF:
                x.left = max(0, x.left - R.RUNOFF_SECONDS)
                x.foul_clock = "runoff"
                then = self.apply(state, flag, accepted)
                self.rules.ref_says(X.text("NXP-12"))
                self.remark(state, flag)
                if x.left <= 0:
                    x.no_snap = False
                    return PERIOD_END
                return then
        else:
            self.note(state, "accepted", flag, accepted.yards, pre=True)
        then = self.apply(state, flag, accepted)
        self.remark(state, flag)
        if then != NEXT_DOWN:                          # the try again: the untimed try passes no next-play step or H10,
            x.no_snap = False                          # so nothing may wait for them
            x.foul_clock = ""
        return then

    # ----- the statistics -----

    def stats_lines(self, state) -> list[str]:
        x = state.extras
        return [X.text("NXS-01"), "%s %d" % (state.teams.get(1, ""), x.flags[0]),
                "%s %d" % (state.teams.get(2, ""), x.flags[1]),
                X.text("NXS-02"), "%s %d" % (state.teams.get(1, ""), x.flag_yards[0]),
                "%s %d" % (state.teams.get(2, ""), x.flag_yards[1])]
