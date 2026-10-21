"""The kicks of 2026 in a game: the kick-off menu, the computer's kicks, the kick defense and the outcome models of every kick (nfl4 only,
rule 0.13; NX-R7: G26-1, G26-4 to G26-7, G26-11, G26-13; NFL_PLAYS_DESIGN 2.6 and 4.9; built in SX.10d, D-094). This is inspired by Jim
Kitchen.

When: the kicks of 2026 are played in a game of the N. F. L. rules where the player uses a playbook (an offense or a defense playbook that
is not Classic: the same switch as the catalog's menus, D-093 (15) and D-094), for both teams' kicks. With the Classic playbook the kicks
stay the original's (and SX.4's onside question), and in Classic nothing here is ever reached; SX.10e makes the team's playbook the default.

NflRules (extras/nfl_rules.py) owns one KickFlow per game and calls it from its hooks; the engine's steps are game/pag_kicks26.py:

    on(state)                            the kicks of 2026 are played in this game
    decide(state, kicking, again, safety)   H4 before_kickoff: the kick-off called (the player's menu, the computer's choice, or the
                                         kick made again after a foul) and the engine's kind: KICKOFF_2026 or ONSIDE_KICKOFF
    plan(state, what)                    the punt, the field goal or the extra point to come: the play called (the player's list or the
                                         default, the computer's choice), the receiving team's call, the fair catch kick
    kickoff_result / punt_result / field_goal_result / extra_point_result / fake_works   the model's draws (extras/plays/model.py)
    fair_catch(state, start)             a fair catch the player made in the last seconds of a half: the fair catch kick may be due
    fair_catch_question(state)           H10: the yes or no question (Q-P18), starting at no

The draws of a kick, in order: the computer's kick-off (its onside rule's draw when one fits, then one `below(100)` over its mix), the
model's draws of the kick; the engine's own draws (the returner, the return's sentence, the tacklers) are the original's.
"""
from __future__ import annotations

import logging
from typing import NamedTuple

from ..data import debuglog
from ..game.playtables import FIELD_GOAL_ODDS, PUNT_SHORTEST, RETURN_SHORTEST
from ..game.rules import KICKOFF_2026, NORMAL_KICKOFF, ONSIDE_KICKOFF
from . import nx_texts as X
from . import playbooks as PB
from . import rules_2026 as R
from . import tuning as T
from .plays import catalog as C
from .plays import descriptions
from .plays import model as M
from .plays import play_menus as PM
from .qb_runs import to_goal

log = logging.getLogger("nfl4.extras")

KEY_ENTER, KEY_UP, KEY_DOWN = "13", "38", "40"
KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
KEY_LETTERS = (65, 90)
ONSIDE, SAFETY_PUNT, DEEP = "K004", "K027", "K001"
FIELD_GOAL, PUNT, EXTRA_POINT, FAIR_CATCH_KICK = "field goal", "punt", "extra point", "fair catch kick"
DEFAULT_KICK = {FIELD_GOAL: "K021", PUNT: "K011", EXTRA_POINT: "K024", FAIR_CATCH_KICK: "K025"}
KICK_FAMILY = {"kg02": 7, "kg03": 6}          # the original's Punt (7) and Field Goal (6) whose lists hold the kinds and the fakes
# the receiving team's remembered call (K031 to K036, design 2.6) as the model's word, for a punt and for a field goal or a try
PUNT_DEFENSE = {"K031": "return", "K032": "fair_catch", "K033": "block", "K034": "safe"}
KICK_DEFENSE = {"K035": "fg_block", "K036": "fg_safe"}


class Plan(NamedTuple):
    what: str               # FIELD_GOAL, PUNT, EXTRA_POINT, FAIR_CATCH_KICK
    concept: str            # the catalog play (K011 a punt, K022 a fake field goal run, ...)
    defense: str            # the receiving team's call as the model's word ("return", "block", "fg_safe", ...)
    distance: int = 0       # a field goal's or a try's length in yards
    kick_spot: int = 0      # a field goal: the spot of the kick, yards from the defense's goal line (a blocked kick is there)
    miss_spot: int = 0      # a field goal: where the defense gets a miss (the spot of the kick, or its 20: RB26 11-4-2, G26-7)

    @property
    def fake(self) -> bool:
        return C.BY_ID[self.concept].kind == "fake"

    @property
    def kind(self) -> str:
        params = C.BY_ID[self.concept].params
        return params[0] if params else ""


def kicks_on(x) -> bool:
    """The kicks of 2026 are played: the player uses an offense or a defense playbook (D-094)."""
    return x is not None and (x.offense_book[0] != PB.CLASSIC or x.defense_book[0] != PB.CLASSIC)


class KickFlow:
    def __init__(self, rules):
        self.rules = rules
        self.caught = False        # the receivers caught or fair-caught the punt being told (kick catch interference can be called)
        self.muffed = False         # the receivers muffed it and the kicking team kept it (no foul is drawn on it)
        self.fair_catch_armed = False     # the player said yes to the fair catch kick: the next field goal is that kick
        self.events: list[tuple] = []     # (what, side, concept, result kind, a number): the tests and the calibration count them

    @property
    def game(self):
        return self.rules.game

    @property
    def rnd(self):
        return self.rules.game.rnd

    @property
    def table(self) -> PB.Table:
        return getattr(self.game, "playbook_table", None) or PB.DEFAULT_TABLE

    def on(self, state) -> bool:
        return kicks_on(state.extras)

    def name(self, concept: str) -> str:
        return self.table.name(concept)

    def start_kick(self) -> None:
        """A new kick: nothing of the last one is read again."""
        self.caught = self.muffed = False

    # ----- the kick-off (G26-1, G26-11; design 2.6) -----

    def kickoff_items(self, state, safety: bool) -> list[str]:
        """The player's kick-off menu: deep, short, squib, onside (with the Onside kicks switch on), the safety punt after a safety; a kind
        switched off in plays.txt is left out, the deep kick never."""
        x = state.extras
        ids = [item.action[1] for item in PM.kickoff_items(safety)]
        return [i for i in ids if i == DEEP or (i not in self.table.disabled and (i != ONSIDE or x.onside_on))]

    def decide(self, state, kicking_side: int, again: bool, safety: bool) -> str:
        """H4: the kick-off called and the engine's kind of kick. A kick made again after a foul keeps its call and asks nothing."""
        x = state.extras
        self.start_kick()
        if again and x.kick_call:
            call = x.kick_call
            x.rekick = call == ONSIDE
        else:
            x.rekick = False
            if kicking_side in self.rules.auto_sides:
                lead = state.score(kicking_side) - state.score(3 - kicking_side)
                call = self.computer_kickoff(state, kicking_side, lead, safety)
            else:
                call = self.kickoff_menu(state, safety)
        x.kick_call = call
        x.kick_kind = ONSIDE_KICKOFF if call == ONSIDE else NORMAL_KICKOFF
        debuglog.event("extras", "kickoff_called", side=kicking_side, call=call, spot=x.kick_from, again=again)
        return ONSIDE_KICKOFF if call == ONSIDE else KICKOFF_2026

    def computer_kickoff(self, state, kicking_side: int, lead: int, safety: bool) -> str:
        """The computer: an onside kick by SX.4's rules (design 8.4), else one draw over its mix (tuning.COMPUTER_KICKOFF_MIX)."""
        if state.extras.onside_on and self.rules.onside.computer_declares(state, kicking_side, lead):
            return ONSIDE
        mix = T.COMPUTER_KICKOFF_MIX
        roll = self.rnd.below(sum(w for _c, w in mix))
        for call, weight in mix:
            if roll < weight:
                return call
            roll -= weight
        return DEEP

    def kickoff_menu(self, state, safety: bool) -> str:
        """The player's kick-off menu in the original's style (design 2.6): the prompt, then the current item; Up and Down move and go
        around, a digit chooses, Enter takes it (the deep kick first, so Enter keeps the original's pace), D says the item's description,
        F1 says the prompt again (and takes back a T key, which calls a time out here as anywhere), F2 to F4 as in a play menu, any other
        key is echoed and the prompt is said again."""
        g, keys = self.game, self.game.keys
        items = self.kickoff_items(state, safety)
        current = 0
        prompt = True
        while True:
            if prompt:
                keys.clk()
                g.say5(X.text("NXB-J01", coach=g.season.coach))
                prompt = False
            g.say5(" %d. %s " % (current + 1, self.name(items[current])))
            if g.sounds.play_noise_running():            # G-A2: no key wait with the play noise looping
                g.sounds.stop_play_noise()
            keys.getkey2(g.speech, g.sounds)
            code = keys.code_text
            if code == KEY_ENTER:
                return items[current]
            if code == KEY_UP:
                current = (current - 1) % len(items)
                continue
            if code == KEY_DOWN:
                current = (current + 1) % len(items)
                continue
            if code == KEY_F1:
                keys.take_resumed()                      # the T key: granted or refused, the menu is said again either way
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
            letter = char.lower() if code.isdigit() and KEY_LETTERS[0] <= int(code) <= KEY_LETTERS[1] else ""
            if letter == "d":                            # NX-P8: the item's plain description, once per press, not logged
                g.voice_speak(descriptions.text(descriptions.play_row(items[current])), wait=False)
                continue
            g.saykey()
            prompt = True

    def kickoff_result(self, state) -> M.KickResult:
        """The model's kick-off from the kicking team's yard line `kick_from` (the 35; the 20 after a safety; farther back after a foul):
        the deep, short or squib kick, or the safety punt (a free kick nobody can block, its receivers' call the remembered one)."""
        x = state.extras
        call = self.kickoff_call(state)
        if call == SAFETY_PUNT:
            defense = self.receiving_call(state, PUNT, receivers=state.wisoff)
            result = M.punt("spread", 100 - x.kick_from, defense, self.rnd, free_kick=True)
            if result.kind == "touchback":           # a punt's touch back: the 20 (RB26 11-6)
                result = result._replace(kind="punt_touchback", start=R.PUNT_TOUCHBACK)
            elif result.kind == "out_of_bounds":     # a free kick out of bounds: the receivers' 40 (RB26 6-2-1)
                result = result._replace(start=R.KICK_OUT_OF_BOUNDS)
            elif result.kind == "muffed":            # the receivers fall on their own muff (a recorded simplification)
                result = result._replace(kind="returned", returned=0, defense_recovers=False)
        else:
            pct = T.SAFETY_KICK_TOUCHBACK if x.kick_from < R.KICKOFF_SPOT else 100
            result = M.kickoff(C.BY_ID[call].params[0], self.rnd, spot=x.kick_from, touchback_pct=pct)
            result = self.returner_door(state, result)
        self.note("kickoff", state.defense, call, result.kind, result.start)
        return result

    def returner_door(self, state, result: M.KickResult) -> M.KickResult:
        """The ratings door of a kick-off return (H8, SX.8o's FR_RETURN_STEP; SX.10e: the 2026 kick-off asked it nowhere): a returned kick
        that is not already a touchdown moves by the returner's step of the original's shortest return (none outside a Franchise, no
        draw); one carried past the goal line is a touchdown."""
        if result.kind != "returned" or result.touchdown:
            return result
        shift = self.rules.modifiers.return_shortest(state.wisoff, state.returner) - RETURN_SHORTEST
        if not shift:
            return result
        back = max(0, result.returned + shift)
        start = result.start - result.returned + back
        if start >= 100:
            return result._replace(start=100, returned=back, touchdown=True)
        return result._replace(start=max(1, start), returned=back)

    @staticmethod
    def kickoff_call(state) -> str:
        return state.extras.kick_call or DEEP

    # ----- the punt, the field goal, the extra point and the fair catch kick -----

    def receiving_call(self, state, what: str, receivers: int) -> str:
        """The receiving team's call as the model's word: the player's remembered kick defense, the computer's return (design 2.6)."""
        if receivers != 1:
            return "return"
        remembered = state.extras.kick_defense or "K031"
        if what == PUNT:
            return PUNT_DEFENSE.get(remembered, "return")
        return KICK_DEFENSE.get(remembered, "return")

    def plan(self, state, what: str) -> Plan | None:
        """The kick to come, or None when the kicks are the original's (the engine plays them as the original)."""
        if not self.on(state):
            return None
        self.start_kick()
        if what == FIELD_GOAL and self.fair_catch_armed:
            self.fair_catch_armed = False
            what = FAIR_CATCH_KICK
        concept = DEFAULT_KICK[what]
        called = self.rules.offense.called if state.wisoff == 1 else ""
        family = KICK_FAMILY.get(C.BY_ID[called].group) if called in C.BY_ID else None
        if what in (FIELD_GOAL, PUNT) and family == (6 if what == FIELD_GOAL else 7):
            concept = called                          # the player's list: a kind of punt, a fake
        elif what in (FIELD_GOAL, PUNT) and state.wisoff in self.rules.auto_sides and self.computer_fakes(state, what):
            concept = "K015" if what == PUNT else "K022"      # SX.10e: the computer's rare fake on a short fourth down
            if self.rnd.below(2):                             # half of them a pass
                concept = "K016" if what == PUNT else "K023"
            concept = concept if concept not in self.table.disabled else DEFAULT_KICK[what]
        elif what == PUNT and state.wisoff == 2 and to_goal(state) <= T.PIN_PUNT_TO_GOAL:
            concept = "K012"                          # the computer's pin punt near the other goal
        defense = self.receiving_call(state, PUNT if what == PUNT else FIELD_GOAL, 3 - state.wisoff)
        distance = kick_spot = miss_spot = 0
        if what in (FIELD_GOAL, FAIR_CATCH_KICK):
            kick_spot = to_goal(state) + (T.FG_KICK_SPOT if what == FIELD_GOAL else 0)    # a fair catch kick is kicked from the catch
            distance = kick_spot + 10
            miss_spot = max(T.MISSED_FG_LEAST, kick_spot)
        elif what == EXTRA_POINT:
            distance = R.EXTRA_POINT_DISTANCE
        plan = Plan(what, concept, defense, distance, kick_spot, miss_spot)
        debuglog.event("extras", "kick_planned", what=what, side=state.wisoff, concept=concept, defense=defense, distance=distance)
        return plan

    def computer_fakes(self, state, what: str) -> bool:
        """SX.10e: the computer fakes a punt or a field goal only on a fourth down of FAKE_TO_GO yards or fewer, with one draw then
        (tuning.COMPUTER_FAKE_PUNT, COMPUTER_FAKE_FIELD_GOAL; the league fakes 0.8 percent of its punts, model_data.FAKE_PUNT)."""
        if state.down != 4 or state.to_go > T.FAKE_TO_GO or (state.quarter == 5 and what == FIELD_GOAL):
            return False
        rate = T.COMPUTER_FAKE_PUNT if what == PUNT else T.COMPUTER_FAKE_FIELD_GOAL
        return self.rnd.below(10000) < rate

    def ratings_points(self, side: int) -> int:
        """The ratings door (H8): the kicker's step of the original's field goal odds as points of the made rate (none outside a Franchise)."""
        return (self.rules.modifiers.field_goal_odds(side) - FIELD_GOAL_ODDS) * T.FR_KICK_MODEL_POINTS

    def punt_result(self, state, plan: Plan) -> M.KickResult:
        shift = self.rules.modifiers.punt(state.wisoff)[1] - PUNT_SHORTEST       # the punter's rating (H8), 0 outside a Franchise
        result = M.punt(plan.kind, to_goal(state), plan.defense, self.rnd, gross_shift=shift)
        self.caught = result.kind in ("returned", "fair_catch", "muffed")
        self.muffed = result.kind == "muffed"
        self.note(PUNT, state.wisoff, plan.concept, result.kind, result.start)
        return result

    def field_goal_result(self, state, plan: Plan) -> M.KickResult:
        result = M.field_goal(plan.distance, plan.defense, self.rnd, fair_catch_kick=plan.what == FAIR_CATCH_KICK,
                              made_shift=self.ratings_points(state.wisoff))
        self.note(plan.what, state.wisoff, plan.concept, result.kind, plan.distance)
        return result

    def extra_point_result(self, state, plan: Plan) -> M.KickResult:
        result = M.extra_point(plan.defense, self.rnd)
        self.note(EXTRA_POINT, state.wisoff, plan.concept, result.kind, plan.distance)
        return result

    def fake_yards(self, state, plan: Plan) -> int:
        """A fake kick's gain: the model says whether it gains the yards to go (design 4.9); one that works gains them and 0 to 8 more, a
        run that fails ends 2 yards behind the line to a yard short of the line to gain, a pass that fails is incomplete (0)."""
        rnd = self.rnd
        works = M.fake_kick(state.to_go, plan.defense, rnd)
        if works:
            low, high = T.FAKE_GAIN_EXTRA
            yards = state.to_go + low + rnd.below(high - low + 1)
        elif plan.kind == "run":
            low, high = -T.FAKE_SHORT_LOSS, max(-T.FAKE_SHORT_LOSS, state.to_go - 1)
            yards = low + rnd.below(high - low + 1)
        else:
            yards = 0
        self.note("fake", state.wisoff, plan.concept, "converted" if works else "stopped", yards)
        return yards

    def note(self, what: str, side: int, concept: str, kind: str, number: int) -> None:
        self.events.append((what, side, concept, kind, number))
        debuglog.event("extras", "kick_result", what=what, side=side, concept=concept, kind=kind, number=number)

    # ----- the fair catch kick (G26-13, Q-P18) -----

    def fair_catch(self, state, receivers: int, start: int) -> None:
        """The punt was fair-caught at the receivers' yard line `start`: the player's fair catch in the second or fourth quarter, with the
        kick in range, makes the fair catch kick due; the question waits for the clock after the punt (H10)."""
        x = state.extras
        if (receivers == 1 and 1 not in self.rules.auto_sides and state.quarter in (2, 4)
                and (100 - start) + 10 <= T.FAIR_CATCH_KICK_LONGEST):
            x.fair_catch_kick = True

    def fair_catch_question(self, state) -> bool:
        """H10 after the punt: the question, when the fair catch kick is due and at most FAIR_CATCH_KICK_SECONDS are left; a yes arms the
        next field goal as the fair catch kick. The computer never tries one (a recorded simplification)."""
        x = state.extras
        due, x.fair_catch_kick = x.fair_catch_kick, False
        if not due or state.wisoff != 1 or not 0 < x.left <= T.FAIR_CATCH_KICK_SECONDS:
            return False
        g = self.game
        yes = self.rules.onside.ask(state, X.text("NXB-J20", coach=g.season.coach))
        debuglog.event("extras", "fair_catch_kick", asked=True, yes=yes, left=x.left)
        self.fair_catch_armed = yes
        return yes

    # ----- the kick defense (design 2.6) -----

    def set_kick_defense(self, state, concept: str) -> None:
        state.extras.kick_defense = "" if concept == "K031" else concept
        self.game.say5(X.text("NXB-J22", name=self.name(concept)))
        debuglog.event("setting", "kick_defense", value=concept)


def text_for(key: str, **values) -> str:
    """The sentences of the 2026 kicks (game/pag_kicks26.py asks for them by key; rows NXB-J02 on)."""
    return X.text(SENTENCES[key], **values)


SENTENCES = {"out_of_bounds": "NXB-J02", "landed_short": "NXB-J03", "touchback_35": "NXB-J04", "caught_at": "NXB-J05",
             "short_kick": "NXB-J06", "squib_kick": "NXB-J07", "punt_blocked": "NXB-J08", "punt_return": "NXB-J09",
             "punt_return_none": "NXB-J10", "rolls_dead": "NXB-J11", "muffed": "NXB-J12", "kick_blocked": "NXB-J13",
             "blocked_return_td": "NXB-J14", "extra_point_missed": "NXB-J15", "blocked_try_two": "NXB-J16", "fake": "NXB-J17",
             "fake_run": "NXB-J18", "fake_pass": "NXB-J19", "fair_catch_kick": "NXB-J21", "safety_punt": "NXB-J23",
             "brought_down": "NXB-J24", "return_td": "NXB-H09"}
