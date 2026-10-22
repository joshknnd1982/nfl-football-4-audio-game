"""pag, part 4: the end of a play, the change of possession, the position and the down, the scores (GAME_SPEC 5.11, 5.12). This is inspired by Jim Kitchen.

CODE (lifted) pag: 0x44e537 (the ball moves), 0x443ef5 (safety), 0x44ea5c to 0x44f6ae (touchdown), 0x4506ef (a play
that ends in the field of play), 0x44df65 and 0x44dfda (turnover spot and possession), 0x4510b6 to 0x451a30 (the banter
draw, the position and down sentences, the log), 0x444146 and 0x444233 (the score and what follows it).
"""
from __future__ import annotations

from . import outcome as O
from . import phrases as P
from .banter import speak_banter
from .gamestate import other, own_half
from .playtables import TURNOVER_SPOT_ODDS, TURNOVER_SPOT_SHORTEST
from .vbnum import trim

COUNTDOWN_TENS = (50, 40, 30, 20, 10)
COUNTDOWN_ONES = (5, 4, 3, 2, 1)


class ResultSteps:

    def end_of_play(self):
        """L_44e537: the yards move the ball toward the defense's goal line."""
        g, s = self.g, self.s
        if s.half == own_half(s.wisoff):
            s.yard_line += s.yards
        else:
            s.yard_line -= s.yards
        if s.yard_line >= 50:                             # past midfield: the other half
            s.yard_line = 50 - (s.yard_line - 50)
            s.half = other(s.half)
        if s.punt_flag == 1 and s.yard_line < 1:
            g.say4(P.IT_IS_A_TOUCH_BACK)
            s.yard_line = 20
        if s.punt_flag == 1:
            s.punt_flag = 2
            step = self.end_point(O.PUNT, turnover=True)
            if step is not None:
                return step
            s.text = P.ITS_SPACE
            return self.possession
        if s.yard_line <= 0:
            if s.half == own_half(s.wisoff):
                return self.safety
            return self.touchdown
        return self.field_play_end

    def safety(self):
        """L_443ef5 (Q24 not reproduced: in overtime a safety ends the game like every score, D-027)."""
        g, s = self.g, self.s
        g.ptf = 1
        g.say4(s.tackle_sentence)
        self.snd.play_tackle(2)
        step = self.end_point(O.SAFETY_KIND, score="safety")
        if step is not None:
            return step
        g.say4(P.SAFETY)
        g.ptf = 0
        s.stats[s.defense].score += 2
        if self.rules.points_end_game(s):             # H22: Classic, every overtime score; the N. F. L. rules, Rule 16 (SX.12)
            return self.game_end
        return self.after_score

    def touchdown(self):
        """L_44ea5c: a pass caught in the end zone, or the run countdown, then " TOUCH DOWN"."""
        g, s, snd = self.g, self.s, self.snd
        if not self.ran():                                # a pass caught in the end zone (a scramble or keeper runs)
            text = " " + self.receiver(s.wisoff, s.carrier)
            catch = self.rnd(3)
            text += P.TD_CATCHES[catch - 1]
            s.tackle_sentence = text
            if catch == 1:
                self.dy(s.yards / 25, 0x44ed2d)
            snd.play(12, -1000)
            g.say4(text)
            if catch == 1:
                return self.touchdown_reached
        self.rady(0x44eea0)
        g.say4(P.HE_IS_AT_THE)
        distance = s.yards + s.yard_line                  # the distance to the goal line at the snap
        for mark in COUNTDOWN_TENS:
            if distance >= mark:
                g.say4(self.str_(mark))                   # then an empty loop (bound x L258 = 0, Q16)
        for mark in COUNTDOWN_ONES:
            if distance >= mark:
                g.say4(self.str_(mark))
                self.rady(0x44f26f)
        return self.touchdown_reached

    def touchdown_reached(self):
        """L_44f322."""
        g, s, snd = self.g, self.s, self.snd
        if s.two_point:
            step = self.end_point(O.TWO_POINT_TRY, score="two-point")
            if step is not None:
                return step
            s.try_good = True
            return self.try_result
        step = self.end_point(O.TOUCHDOWN, score="touchdown")
        if step is not None:
            return step
        g.say4(P.TOUCH_DOWN)
        self.log_replay_list()
        snd.play_tackle(8)
        snd.playcel()
        s.stats[s.wisoff].score += 6
        if self.rules.points_end_game(s, s.wisoff):       # H22 (SX.12): a touchdown that decides the overtime has no try (4-8-2 (c));
            return self.game_end                          # Classic: never (its overtime ends after the try)
        if s.wisoff == 2:                                 # the computer always kicks
            self.rady(0x44fcee)
            return self.computer_try_choice()
        self.rady(0x44f6ae)
        return self.extra_point_choice

    def computer_try_choice(self):
        """The computer's try after its touchdown: the extra point, or (N. F. L. rules, a game that plays the catalog, SX.10e G26-10) the
        two-point try of its chart, said in one sentence; its defense is the player's menu as on any of its plays. Classic: the kick."""
        s = self.s
        if not self.rules.computer_goes_for_two(s):     # H21: Classic answers no, with no draw
            return self.extra_point
        self.g.say4(self.rules.play_text("computer_try", team=s.teams.get(s.wisoff, "")))
        self.g.log_print("")
        s.two_point = True
        s.yard_line = 2
        return self.defense_menu if s.wisoff == 2 else self.offense_menu

    def field_play_end(self):
        """L_4506ef: the pause, the tackle sound and sentence, the gain or loss, the downs."""
        g, s, snd = self.g, self.s, self.snd
        if s.return_flag:                                 # L30c: no pause after a kick-off return
            s.return_flag = False
        else:
            self.dy(abs(s.yards) / 25, 0x4507b8)
        if self.ran():                                    # runs, kick-off returns, quarterback runs (SX.5)
            snd.play_tackle(s.tackle_sound)
            g.say4(s.tackle_sentence)
        else:                                             # passes, sacks, incompletions
            snd.play(12, -1000)
            g.say2(s.tackle_sentence)
            snd.play_tackle(s.tackle_sound)
        self.rules.after_tackle(s)                        # H2 (SX.2): out of bounds in N. F. L. rules mode; Classic: nothing
        snd.c2df()
        return self.gain_and_end()

    def gain_and_end(self):
        """The gain or loss sentence, the narration end point and the downs of a play that ends in the field of play (the
        second half of L_4506ef). Also a step of its own (N. F. L. rules mode, SX.6): a review that changed the ruling of
        a run, a catch or an incompletion sets the corrected yards and kind in the state and the engine goes on here, so the
        corrected gain is spoken and the downs follow from it as they would have had the play been called right."""
        g, s = self.g, self.s
        if s.yards > 0:
            g.say4(P.GAIN + trim(self.str_(s.yards)) + P.YARD + (P.PLURAL if s.yards > 1 else "") + P.ON_THE_PLAY)
        if s.yards < 0:
            g.say2(P.LOSS + trim(self.str_(abs(s.yards))) + P.YARD + (P.PLURAL if s.yards < -1 else "")
                   + P.ON_THE_PLAY_STOP)
        if s.two_point:                                   # the try failed: no announcement (Q22)
            step = self.end_point(O.TWO_POINT_TRY)
            if step is not None:
                return step
            s.try_good = False
            return self.try_result
        if s.yards == 0:
            g.say2(P.NO_GAIN)
        step = self.end_point(s.result_kind)
        if step is not None:
            return step
        s.down += 1
        s.to_go -= s.yards
        if s.to_go < 1:
            s.to_go = 10
            s.down = 1
            s.stats[s.wisoff].first_downs += 1            # a kick-off return too (Q19)
        if s.down >= 5:
            s.text = P.TURNED_OVER_ON_DOWNS
            s.downs_flag = True
            return self.possession
        return self.banter_position

    def penalty_safety(self):
        """N. F. L. rules (SX.3; never in Classic): a safety by enforcement (a foul by the offense in its own end zone, or
        intentional grounding there; the extras announced it): the original's sentence, 2 points to the defense, then
        what follows the original's safety."""
        g, s = self.g, self.s
        g.ptf = 1
        g.say4(P.SAFETY)
        g.ptf = 0
        s.stats[s.defense].score += 2
        if self.rules.points_end_game(s):             # H22 (SX.12)
            return self.game_end
        return self.after_score

    # ----- turnovers and the change of possession -----

    def turnover_spot(self):
        """L_44df65: an interception or a fumble puts the ball at a random yard line 5 to 44 in the same half (Q31).
        Q23 not reproduced (D-027): during a two-point try the turnover ends the try with no points."""
        s = self.s
        back = self.rules.turnover_return(s)          # H19 (SX.10c, G26-8): a catalog play's return; Classic and the original's plays: None
        if s.two_point:
            s.two_point = False
            s.try_good = False
            s.interception_flag = s.fumble_flag = False
            s.points = 0
            if back is not None and back[2]:          # the defense ran the try back: two points for it (RB26 11-3-2, G26-10)
                self.g.say4(back[3])
                self.g.say4(self.rules.play_text("try_scored"))
                s.stats[s.defense].score += 2
            return self.score
        if back is None:
            s.yard_line = self.rnd.below(TURNOVER_SPOT_ODDS) + TURNOVER_SPOT_SHORTEST
            return self.possession
        half, line, touchdown, sentence = back
        if sentence:
            self.g.say4(sentence)
        if touchdown:
            return self.return_touchdown()
        s.half, s.yard_line = half, line
        return self.possession

    def return_touchdown(self):
        """N. F. L. rules (SX.10c, G26-8; never in Classic): the defense ran an interception or a fumble of a catalog play back to the end
        zone. The ball is the scorers' and the original's steps after " TOUCH DOWN" follow (the log, the sounds, six points, the try)."""
        g, s, snd = self.g, self.s, self.snd
        s.interception_flag = s.fumble_flag = False
        s.wisoff, s.defense = s.defense, s.wisoff
        s.half, s.yard_line = own_half(s.defense), 0       # at the goal line the scorers attack (the try's spot is set by its choice)
        if self.last_outcome is not None:
            self.last_outcome.score = "return touchdown"
        g.say4(P.TOUCH_DOWN)
        self.log_replay_list()
        snd.play_tackle(8)
        snd.playcel()
        s.stats[s.wisoff].score += 6
        if self.rules.points_end_game(s, s.wisoff):       # H22 (SX.12): a return touchdown that decides the overtime has no try
            return self.game_end
        if s.wisoff == 2:                                 # the computer always kicks
            self.rady(0x44fcee)
            return self.computer_try_choice()
        self.rady(0x44f6ae)
        return self.extra_point_choice

    def possession(self):
        """L_44dfda: the other side gets the ball; the sentence prefix is in L4f4."""
        g, s = self.g, self.s
        if s.wisoff == 2:
            s.wisoff = 1
            s.text += P.YOUR_BALL
        else:
            s.wisoff = 2
            s.text += P.MINE
        s.text += P.ON + self._half_word() + self.str_(s.yard_line) + P.YARD_LINE_SPACED
        g.say2(s.text)
        if self.rules.possession_ends_game(s):            # H22 (SX.12): the second team's possession in overtime ended (Classic: never)
            s.downs_flag = s.interception_flag = s.fumble_flag = False
            s.punt_flag = 0
            return self.game_end
        if s.downs_flag:
            s.downs_flag = False
        elif s.interception_flag:
            s.interception_flag = False
        elif s.fumble_flag:
            s.fumble_flag = False
        elif s.punt_flag == 2:
            s.punt_flag = 0
        else:                                             # a missed field goal (and " is way to short")
            self.log_replay_list()
        self.banter()
        s.down = 1
        s.to_go = 10
        return self.down_sentence

    # ----- the position and the down (L_4510b6, L_451181, L_4513f2) -----

    def banter_position(self):
        """L_4510b6: a banter line 1 time in 4, then " it's" and the position."""
        if self.rnd(4) == 2:
            self.banter()
        self.s.text = P.ITS
        return self.position

    def position(self):
        """L_451181: the prefix in L4f4 + " your" or " my" + " ball on" + the half and the yard line (no space before
        "yard line")."""
        g, s = self.g, self.s
        text = s.text
        if s.wisoff == 1:
            text += P.YOUR
        if s.wisoff == 2:
            text += P.MY
        text += P.BALL_ON + self._half_word() + self.str_(s.yard_line) + P.YARD_LINE
        s.text = text
        g.say2(text)
        return self.down_sentence

    def down_sentence(self):
        """L_4513f2: " it's first down and 10yards to go", the replay list to the log, then H10 and the next play."""
        g, s = self.g, self.s
        s.text = P.ITS + self._down_and_distance()
        g.say2(s.text)
        g.log_print("")
        for line in list(g.replay):
            if "ball on" in line:
                g.log_print("")
            if "mine" in line:
                g.log_print("")
            g.log_print(line)
        step = self.continuation(self.rules.between_plays(s))   # H10 (Classic: nothing; N. F. L. rules: the computer's
        if step is not None:                              # challenge may have changed the ruling of the last play, SX.6)
            return step
        if self._in_stats:
            return None                                   # L4b0 = 3: back into the quarter statistics' caller
        return self.next_play

    _in_stats = False

    def log_replay_list(self) -> None:
        """`Print #3` then every line of the replay list (a touchdown, a missed field goal)."""
        g = self.g
        g.log_print("")
        for line in list(g.replay):
            g.log_print(line)

    def banter(self) -> None:
        speak_banter(self.g, self.s)

    # ----- the scores (5.12) -----

    def score(self):
        """L_444146: the points go to the side with the ball; in overtime the game ends at once."""
        s = self.s
        s.stats[s.wisoff].score += s.points
        if self.rules.points_end_game(s):             # H22: Classic, every overtime score; the N. F. L. rules, Rule 16 (SX.12)
            return self.game_end
        return self.after_score

    def after_score(self):
        """L_444233: the score, a synchronous " " on the voice that spoke last, rady, banter, the key wait, then the
        kick-off received by the side that did not score (after a safety the side that scored)."""
        g, s = self.g, self.s
        g.say_score(s.score(1), s.score(2))
        g.voice_speak(" ", wait=True)
        self.rady(0x4443cb)
        self.banter()
        self.rules.broadcast_moment(s, "score")                     # H23: Ghip after a touchdown or a field goal (the N. F. L. rules)
        self.key_wait()
        s.wisoff = other(s.wisoff)
        s.defense = other(s.wisoff)
        s.half = own_half(s.wisoff)
        return self.kick_off
