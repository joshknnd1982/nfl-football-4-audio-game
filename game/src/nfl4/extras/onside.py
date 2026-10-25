"""Onside kicks of the N. F. L. rules mode (nfl4 only, rule 0.13; NX4, built in SX.4). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 8, NFL_RULES_RESEARCH Part 5 (the 2026 rulebook 6-1-6: the kicking team may declare an onside kick at any
free kick, in any period and with any score; the declaration is told to the receivers, so no kick is a surprise).

The rules as plain functions (no speech, no keys, no draws): `kick_spot`, `question_due` (design 8.2, the owner's decision
D-041: the player is asked only when it makes sense), `computer_rule` (design 8.4). `OnsideFlow` is the game's part: NflRules
(extras/nfl_rules.py) owns one per game and calls it from hook H4.

    decide(state, kicking_side, again)   H4 before_kickoff: the kind of the coming kick-off. The player's team is asked (a yes
                                         or no question, "no" first) when `question_due`; the computer's team declares by the
                                         rules of design 8.4 (one draw `rnd(b) <= a` when a rule fits; the sentence that says so
                                         begins the kick, after the engine cleared the replay list); a kick made
                                         again keeps its kind and asks nothing
    kick(state)                          the engine's onside_kick step: the sentences, sounds and draws of the kick up to its
                                         result (game/rules.py ONSIDE_KEPT, ONSIDE_LOST, ONSIDE_RUN)

The draws of a kick, in order (design 15, as built): the remark of pool ON (chance 1 in 3, comments on), the distance 8 to 14
yards, the recovery by the kicking team (8 percent); when it did not: one `below(100)` (0 a touchdown, 1 to 3 a return, else
the receivers fall on the ball), the receivers' player `rnd(2)`; a return: its yards and the two tacklers as the original's
kick-off return draws them. The fouls of the kick (P24, P33) are drawn by the penalty flow at the narration end point like
every foul (design 9), after the result is known, so that the receivers can accept or decline them knowing it.
"""
from __future__ import annotations

import logging

from ..game import outcome as O
from ..game import phrases as P
from ..game.gamestate import other, own_half
from ..game.rules import NORMAL_KICKOFF, ONSIDE_KEPT, ONSIDE_KICKOFF, ONSIDE_LOST, ONSIDE_RUN
from . import nx_texts as X
from . import remarks
from . import tuning as T

log = logging.getLogger("nfl4.extras")

KEY_ENTER, KEY_TAB, KEY_UP, KEY_DOWN = "13", "9", "38", "40"
KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
TACKLERS = 17                  # the defensive players of a roster (the original's return draws two of them)


# ----- the rules, as plain functions -----

def question_due(quarter: int, left: int, lead: int, always: bool) -> bool:
    """Design 8.2 (D-041): the player's team is asked when it trails in the third or fourth quarter, or leads by one score
    (1 to 8 points) with at most 5:00 left in the fourth quarter; with the setting "always" at every kick-off and safety
    kick. Never in overtime unless "always". `lead` is the kicking team's score minus the receivers'."""
    if always:
        return True
    if quarter >= 5:
        return False
    if lead < 0:
        return quarter >= 3
    low, high = T.ONSIDE_LATE_LEAD
    return quarter == 4 and left <= T.ONSIDE_LATE_SECONDS and low <= lead <= high


def computer_rule(quarter: int, left: int, deficit: int) -> tuple[int, int] | None:
    """Design 8.4: the computer's chance `a in b` of declaring an onside kick, or None when no rule fits (no draw, never).
    `deficit` is the receivers' score minus the kicking team's. Only the fourth quarter; the first rule that fits decides."""
    if quarter != 4 or deficit < 1:
        return None
    for low, high, over, up_to, a, b in T.ONSIDE_COMPUTER_RULES:
        if low <= deficit <= high and over < left <= up_to:
            return a, b
    return None


class OnsideFlow:
    def __init__(self, rules):
        self.rules = rules

    @property
    def game(self):
        return self.rules.game

    @property
    def rnd(self):
        return self.rules.game.rnd

    # ----- H4: the kind of the coming kick-off -----

    def decide(self, state, kicking_side: int, again: bool) -> str:
        """NORMAL_KICKOFF or ONSIDE_KICKOFF (the extras' record keeps the kind: a kick made again after a foul is of the
        same kind and is not tried or asked again)."""
        x = state.extras
        if again:
            kind = x.kick_kind or NORMAL_KICKOFF
            x.rekick = kind == ONSIDE_KICKOFF
            return kind
        x.rekick = False
        lead = state.score(kicking_side) - state.score(other(kicking_side))
        if kicking_side in self.rules.auto_sides:
            trying = self.computer_declares(state, kicking_side, lead)
        elif question_due(state.quarter, x.left, lead, x.onside_always):
            trying = self.ask(state)
        else:
            trying = False
        x.kick_kind = ONSIDE_KICKOFF if trying else NORMAL_KICKOFF
        return x.kick_kind

    def computer_declares(self, state, kicking_side: int, lead: int) -> bool:
        rule = computer_rule(state.quarter, state.extras.left, -lead)
        if rule is None:
            return False
        chance, out_of = rule
        return self.rnd(out_of) <= chance           # the sentence that says so comes with the kick (it is replayed by F2)

    def ask(self, state, prompt: str | None = None) -> bool:
        """The player's question (design 8.2, C9): the question, then the answer, "no" first; Up, Down or Tab change it, Y
        says yes and N says no, Enter takes it, F1 asks again, F2 to F4 as in a play menu, any other key is echoed and the
        question is asked again (the keypad digits type letters in this key model, B-W6). `prompt`: another yes or no question
        asked the same way (SX.10d: the fair catch kick); the onside question by default."""
        g, keys = self.game, self.game.keys
        answer = False
        while True:
            keys.clk()
            g.say5(prompt if prompt is not None else X.text("NXO-01", coach=g.season.coach))
            while True:
                g.say5(X.text("NXO-A02") if answer else X.text("NXO-A01"))
                if g.sounds.play_noise_running():            # G-A2: no key wait with the play noise looping
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
                keypad = code.isdigit() and 96 <= int(code) <= 111     # the whole keypad types letters here (the dot is "n")
                char = "" if keypad else keys.char.lower()
                if char == "y":
                    answer = True
                    continue
                if char == "n":
                    answer = False
                    continue
                g.saykey()
                break

    # ----- the kick -----

    def remark(self, state, kicking_side: int) -> None:
        g = self.game
        if g.comtog == 0 and self.rnd(T.ONSIDE_REMARK_CHANCE) == 1:
            values = {"<team>": state.teams.get(kicking_side, ""), "<coach>": g.season.coach,
                      "<quarterback>": state.quarterbacks.get(kicking_side, "")}
            remarks.say_remark(g, state, state.extras, "ON", values)

    def kick(self, state) -> str:
        """The kick of design 8.3, from the kicking team's yard line `kick_from` (35, the 20 after a safety, moved back by an
        accepted foul): up to its result. The ball is left where the kick ended (the kicking team's half, `half` and
        `yard_line` of the state); `wisoff` stays the receivers. ONSIDE_RUN: the receivers pick it up and run, the state
        is set like a kick-off return and the engine runs the rest."""
        g, x, snd = self.game, state.extras, self.game.sounds
        kicking, receiving = state.defense, state.wisoff
        k_team, r_team = state.teams.get(kicking, ""), state.teams.get(receiving, "")
        rekick, x.rekick = x.rekick, False
        if not rekick:
            x.onside_tried[kicking - 1] += 1
        kicker = state.rosters[kicking].kickers[0]
        snd.c2uh()
        # SZ.6 (D-111, a player's e-mail: "it says onside kick twice"): the computer declares (design 8.4) and that sentence IS the line-up; the
        # player's yes needs no sentence, and a kick made again after a foul says the line-up again (the fouls were spoken between)
        declared = not rekick and kicking in self.rules.auto_sides
        g.say4(X.text("NXO-09" if declared else "NXO-02", kicking_team=k_team))     # said here so that F2 replays it
        g.say4(X.text("NXO-03", receiving_team=r_team))
        self.remark(state, kicking)
        snd.play_tackle(8)                                   # foot11, the referee's whistle: the kick is on
        snd.c2uf()
        engine = g.play_engine
        if engine is not None:
            engine.go_live()                                 # H18: the kick is made, a T key is only kept from here
        snd.play(7, -1200)                                   # foot7, the kick
        snd.play_noise()
        g.say4(X.text("NXO-04", kicker=kicker))
        g.say4(X.text("NXO-05"))
        g.rady(None)                                         # a pause of random length before the result (design 8.3)
        low, high = T.ONSIDE_DISTANCE
        distance = self.rnd.below(high - low + 1) + low
        state.half, state.yard_line = own_half(kicking), x.kick_from + distance
        if self.rnd.below(100) < T.ONSIDE_RECOVERY_PERCENT:
            self.result(X.text("NXO-06", kicking_team=k_team))
            return ONSIDE_KEPT
        roll = self.rnd.below(100)
        n = self.rnd(2)
        returner = state.rosters[receiving].special_teams[n - 1]
        state.returner = n
        if roll < T.ONSIDE_RETURN_IN_100:
            self.run_back(state, kicking, returner, touchdown=roll < T.ONSIDE_TOUCHDOWN_IN_100)
            return ONSIDE_RUN
        self.result(X.text("NXO-07", returner=returner))
        return ONSIDE_LOST

    def result(self, sentence: str) -> None:
        """The sentence of a result nobody runs back: the crowd, the sentence, the whistle (foot11, which also stops the
        play noise), the crowd down (the original's touch back)."""
        g, snd = self.game, self.game.sounds
        snd.play(12, -1000)
        snd.c2dh()
        g.say4(sentence)
        snd.play_tackle(8)
        snd.c2df()

    def run_back(self, state, kicking: int, returner: str, touchdown: bool) -> None:
        """The receivers pick it up and run. The state is set the way the original's kick-off return leaves it (the
        yards, the tackle sentence and sound, the result kind, no pause before the tackle) and the engine goes on at the
        end of the play: a touchdown when the run reaches the goal line, else the tackle and the gain."""
        g, snd, rnd = self.game, self.game.sounds, self.rnd
        spot = state.yard_line                               # the ball's yard line from the kicking team's own goal line
        snd.play(12, -1000)
        snd.c2dh()
        g.say4(X.text("NXO-08", returner=returner))
        if touchdown:
            yards = spot                                     # to the goal line: the original's countdown follows
        else:
            low, high = T.ONSIDE_RETURN_YARDS
            yards = min(rnd.below(high - low + 1) + low, spot - 1)    # never to the goal line (design 8.3)
            tackle = P.CUT_DOWN if yards < 20 else (P.TACKLED if yards < 30 else P.FINALLY_TACKLED)
            roster = state.rosters[kicking]
            first = rnd(TACKLERS)
            tackle += " " + roster.defense[first - 1] + " " + P.AND
            second = rnd.redraw(lambda: rnd(TACKLERS), lambda d: d != first, lambda: 2 if first == 1 else 1,
                                "second tackler")
            tackle += roster.defense[second - 1] + " "
            state.tackle_sentence = tackle
            state.tackle_sound = 2                           # a return of fewer than 51 yards, as the original
        state.yards = yards
        state.result_kind = O.KICKOFF_RETURN
        state.return_flag = True                             # no pause before the tackle of a kick-off return (L30c)
        state.to_go = 1                                      # the original's kick-off return: a first down for the receivers


__all__ = ["OnsideFlow", "computer_rule", "question_due"]
