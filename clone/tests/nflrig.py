"""A rig for whole games with the N. F. L. rules (nfl4 only, rule 0.13; PX SX.2). This is inspired by Jim Kitchen.

* `SimEngine`: the play engine with BOTH sides played by the computer (the calibration of NFL_EXTRAS_DESIGN 5.7): the
  player's side calls the toss, receives, returns kick-offs 1 time in 2, kicks the extra point, chooses its offense with the
  computer's draw of 5.7 and a mirrored fourth-down and last-play rule, and its defense with Int(Rnd * 6) + 1; its timeouts
  are the computer's rules (NflRules with auto_sides (1, 2)).
* `RecordingRules`: NflRules that records every timeout, warning and period end with the clock, for the property tests;
  penalties off unless asked (SX.3: `penalties_on=True`; the flow's `events` list every flag).
* `sim_game(tmp_path, seed)`: one whole seeded game on the fast virtual clock; returns the rig, the engine and the rules.
"""
import random

from gamerig import Rig
from nfl4.extras.nfl_rules import NflRules
from nfl4.game.pag import PlayEngine
from pagrig import PolicyKeys, make_rig, named_roster
from randsources import ScriptedRandom

QUARTERBACKS = ("Starr", "Unitas")


def feature_help(rules, key):
    """Rules.extra_help(key) without the lines SX.10b2 generates from the master key list (and without F7's added football words): the
    lines of the features themselves, as the tests of each feature read them."""
    from nfl4.extras.plays import descriptions
    from nfl4.game import key_list
    lines = rules.extra_help(key)
    generated = key_list.help_lines(key, "nfl", rules.help_features)
    cut = len(generated) if key != "118" else len(descriptions.F7_WORD_ROWS)
    return lines[:len(lines) - cut] if cut else lines


def nfl_engine_rig(tmp_path, answers=(), comments=False, rules=None, extras=None, gtp=1, **state):
    """engine_rig (tests/pagrig.py) with the N. F. L. rules: Bengals (side 1, coach Kim, Starr) against the Jets (Unitas),
    named rosters, comments off unless asked, a strict scripted source with no draws. `extras` sets fields of the extras
    record (state.extras), `state` fields of the GameState. rig.engine, rig.rules; the game knows the engine (the hot
    keys read its rules)."""
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=ScriptedRandom([], strict=True))
    keys = PolicyKeys(rig.clock, answers, None, False)
    rig.keys = rig.game.keys = rig.sounds.keys = keys
    season = rig.game.season
    season.coach = "Kim"
    season.choose_team(1, 1)
    season.tn3, season.tn4 = 2, 3
    season.gtp = gtp
    rig.game.comtog_source = (lambda: 0) if comments else (lambda: 1)
    rules = rules if rules is not None else NflRules()
    engine = PlayEngine(rig.game, rules, quarterback_names=lambda s: QUARTERBACKS)
    engine.game_on = True                  # SX.2b: the game is in play (the T key calls a timeout); a test of the first kick-off sets it back
    s = engine.s
    s.teams = {1: "Bengals", 2: "Jets"}
    s.rosters = {1: named_roster(""), 2: named_roster("O")}
    s.quarterbacks = {1: "Starr", 2: "Unitas"}
    own, opp = s.rosters[1], s.rosters[2]
    s.banter_names = (own.running_backs + own.receivers + own.defense + opp.running_backs + opp.receivers
                      + opp.defense)
    s.plays = [33, 33, 33, 33, 33]
    for name, value in state.items():
        setattr(s, name, value)
    for name, value in (extras or {}).items():
        setattr(s.extras, name, value)
    rig.engine, rig.rules = engine, rules
    rig.game.play_engine = engine
    return rig


class RecordingRules(NflRules):
    def __init__(self, timeouts_on=True, auto_sides=(1, 2), penalties_on=False, onside_on=False, onside_always=False,
                 qb_on=False, challenges_on=False, offense_book="classic", defense_book="classic", playbooks_on=False):
        super().__init__(timeouts_on, auto_sides, penalties_on, onside_on, onside_always, qb_on, challenges_on,
                         offense_book, defense_book, playbooks_on)
        self.onsides = []           # (quarter, kicking side, seconds left, kicking team's lead, result) of every onside kick
        self.timeouts = []          # (quarter, side, seconds left after it, timeouts left of that side)
        self.periods = []           # (quarter, counted plays, seconds left) at each period end
        self.warnings = []          # (quarter, seconds left) when the warning was said
        self.lefts = []             # every time left seen at H10
        self.dead_balls = []        # (side, quarter, the play count) of every timeout: never twice in one dead-ball period
        self.used = None            # the game's own object (Game.play_game calls for_game): what a test must read
        self.forced = None          # SX.7: ((offense, defense) of side 1, (offense, defense) of side 2) style keys, whatever the
        #                             settings and the teams say (the balance test puts one style against Classic)

    def for_game(self):
        self.used = super().for_game()
        self.used.forced = self.forced
        return self.used

    def period_clock(self, game, state):
        clock = super().period_clock(game, state)
        if self.forced is not None:
            (o1, d1), (o2, d2) = self.forced
            state.extras.offense_book, state.extras.defense_book = [o1, o2], [d1, d2]
        return clock

    def grant(self, state, side):
        super().grant(state, side)
        x = state.extras
        self.timeouts.append((state.quarter, side, x.left, x.timeouts_of(side), x.unit))
        self.dead_balls.append((side, state.quarter, x.plays))

    def between_plays(self, state):
        then = super().between_plays(state)            # a computer's won challenge answers the step of the corrected play (SX.6)
        self.lefts.append((state.quarter, state.extras.left, state.extras.pending))
        return then

    def onside_kick(self, state):
        kicking = state.defense
        lead = state.score(kicking) - state.score(3 - kicking)
        left = state.extras.left
        result = super().onside_kick(state)
        self.onsides.append((state.quarter, kicking, left, lead, result))
        return result


class SimEngine(PlayEngine):
    """Both sides by the computer (design 5.7's calibration)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.steps = []             # (quarter, counter) at every counted play

    def next_play(self):
        if not getattr(self.s.extras, "no_snap", False):     # a foul before the snap is not a counted play (SX.3)
            self.steps.append((self.s.quarter, self.s.counter))
        return super().next_play()

    def period_checks(self):
        rules = self.rules
        if getattr(rules, "periods", None) is not None and self.clock.period_over():
            rules.periods.append((self.s.quarter, self.s.counter, self.s.extras.left))
        return super().period_checks()

    def _two_minute_warning(self):
        if self.clock.warning_zone() and isinstance(self.rules, RecordingRules):
            self.rules.warnings.append((self.s.quarter, self.s.extras.left))
        return super()._two_minute_warning()

    def _call_the_toss(self) -> int:
        return self.rnd(2)

    def _receive_or_kick(self):
        s = self.s
        s.wisoff, s.defense, s.half = 1, 2, 2
        return self.kick_off

    def run_it_out(self):
        return self.kick_return if self.rnd(2) == 1 else self.touch_back

    def extra_point_choice(self):
        return self.extra_point

    def offense_menu(self):
        s = self.s
        x = self.rnd.below(9) + 2
        s.offense_play = x // 2
        lead = s.score(1) - s.score(2)
        if self.clock.is_last_play() and s.quarter in (2, 4) and s.half == 1 and (s.quarter == 2 or lead > -4):
            s.offense_play = 6
        elif s.down >= 4:
            s.offense_play = 6 if s.half == 1 and s.yard_line < 41 else 7
            if self.rnd(9) == 7:
                s.offense_play = self.rnd(4)
        self.rules.computer_offense(s)             # SX.5: the computer's sneaks, keepers and draws (no draw in Classic)
        return self.offense_chosen

    def defense_menu(self):
        self.s.defense_play = self.rnd(6)
        return self.defense_chosen

    def defense_chosen(self):
        step = super().defense_chosen()             # the computer's offense is chosen: now what the defense called is known
        self.rules.computer_defense(self.s)         # SX.7: the player's side too picks the style's play of its family
        return step


def sim_game(tmp_path, seed, rules=None, gtp=1, own_names=None, opponent_names=None, quarterbacks=QUARTERBACKS, trace=False):
    """One whole seeded game. `own_names` and `opponent_names` are the Franchise's rosters (H7, SX.8b: with ratings), the
    quarterbacks' names are handed in as the Franchise does; `trace` records the size of every draw in rig.rnd.trace."""
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=gtp)
    if trace:
        rig.rnd.trace = []
    rules = rules if rules is not None else RecordingRules()
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: quarterbacks, own_names=own_names,
                       opponent_names=opponent_names)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, engine, rules, result
