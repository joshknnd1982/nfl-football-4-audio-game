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
            self.outcome(O.PUNT, turnover=True)
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
        self.outcome(O.SAFETY_KIND, score="safety")
        g.say4(P.SAFETY)
        g.ptf = 0
        s.stats[s.defense].score += 2
        if s.quarter == 5:
            return self.game_end
        return self.after_score

    def touchdown(self):
        """L_44ea5c: a pass caught in the end zone, or the run countdown, then " TOUCH DOWN"."""
        g, s, snd = self.g, self.s, self.snd
        if s.offense_play >= 3:
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
            self.outcome(O.TWO_POINT_TRY, score="two-point")
            s.try_good = True
            return self.try_result
        self.outcome(O.TOUCHDOWN, score="touchdown")
        g.say4(P.TOUCH_DOWN)
        self.log_replay_list()
        snd.play_tackle(8)
        snd.playcel()
        s.stats[s.wisoff].score += 6
        if s.wisoff == 2:                                 # the computer always kicks
            self.rady(0x44fcee)
            return self.extra_point
        self.rady(0x44f6ae)
        return self.extra_point_choice

    def field_play_end(self):
        """L_4506ef: the pause, the tackle sound and sentence, the gain or loss, the downs."""
        g, s, snd = self.g, self.s, self.snd
        if s.return_flag:                                 # L30c: no pause after a kick-off return
            s.return_flag = False
        else:
            self.dy(abs(s.yards) / 25, 0x4507b8)
        if s.offense_play <= 2:                           # runs and kick-off returns
            snd.play_tackle(s.tackle_sound)
            g.say4(s.tackle_sentence)
        else:                                             # passes, sacks, incompletions
            snd.play(12, -1000)
            g.say2(s.tackle_sentence)
            snd.play_tackle(s.tackle_sound)
        self.rules.after_tackle(s)                        # H2 (SX.2): out of bounds in N. F. L. rules mode; Classic: nothing
        snd.c2df()
        if s.yards > 0:
            g.say4(P.GAIN + trim(self.str_(s.yards)) + P.YARD + (P.PLURAL if s.yards > 1 else "") + P.ON_THE_PLAY)
        if s.yards < 0:
            g.say2(P.LOSS + trim(self.str_(abs(s.yards))) + P.YARD + (P.PLURAL if s.yards < -1 else "")
                   + P.ON_THE_PLAY_STOP)
        if s.two_point:                                   # the try failed: no announcement (Q22)
            self.outcome(O.TWO_POINT_TRY)
            s.try_good = False
            return self.try_result
        if s.yards == 0:
            g.say2(P.NO_GAIN)
        self.outcome(s.result_kind)
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

    # ----- turnovers and the change of possession -----

    def turnover_spot(self):
        """L_44df65: an interception or a fumble puts the ball at a random yard line 5 to 44 in the same half (Q31).
        Q23 not reproduced (D-027): during a two-point try the turnover ends the try with no points."""
        s = self.s
        if s.two_point:
            s.two_point = False
            s.try_good = False
            s.interception_flag = s.fumble_flag = False
            s.points = 0
            return self.score
        s.yard_line = self.rnd.below(TURNOVER_SPOT_ODDS) + TURNOVER_SPOT_SHORTEST
        return self.possession

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
        self.rules.between_plays(s)                       # H10 (Classic: nothing)
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
        if s.quarter == 5:
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
        self.key_wait()
        s.wisoff = other(s.wisoff)
        s.defense = other(s.wisoff)
        s.half = own_half(s.wisoff)
        return self.kick_off
