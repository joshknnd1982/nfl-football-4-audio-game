"""pag, part 3: the kicks (GAME_SPEC 5.10, 4.16, 4.17). This is inspired by Jim Kitchen.

CODE (lifted) kicksnap p_43a330; pag 0x441dfa (field goal), 0x442ebe (punt), 0x444645 (kick-off), 0x445772 (return),
0x446c75 (touch back), 0x44f6f0 (the extra point choice), 0x44fd30 (extra point), 0x450499 (the two-point try's result).
"""
from __future__ import annotations

from . import outcome as O
from . import phrases as P
from .gamestate import other
from .playtables import (FIELD_GOAL_DRAWS, FIELD_GOAL_NEEDED, RETURN_KIND_ODDS, RETURN_RANGE, RETURN_RANGES,
                         RETURN_SHORTEST)
from .rules import NORMAL_KICKOFF

KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
KEY_ENTER, KEY_UP, KEY_DOWN = "13", "38", "40"
RETURN_MARK_SITES = (0x445f3e, 0x44602b, 0x446118, 0x446205, 0x4462f2, 0x4463df, 0x4464cc, 0x4465b9)


class KickSteps:

    def kicksnap(self) -> None:
        """kicksnap (p_43a330): the punter of the kicking side calls the snap; every say3 waits."""
        g, rnd = self.g, self.rnd
        g.qorp = 2
        self.snd.c2uf()
        self.say3(P.KICK_HUT_1)
        self.rady(0x43a42f)
        if rnd(3) != 2:                                   # " hut 2 " with 2 in 3
            self.say3(P.KICK_HUT_2)
            self.rady(0x43a4fe)
            if rnd(2) != 2:                               # then " hut 3 " with 1 in 2
                self.say3(P.KICK_HUT_3)
                self.rady(0x43a5c5)
        for _ in range(rnd(3)):                           # 1 to 3 " hut" or " hut!" (1 in 3)
            self.say3(P.HUT + ("!" if rnd(3) == 3 else ""))
            self.rady(0x43a73c)
        self.rady(0x43a774)
        self.say3(P.KICK_HIKE)
        g.qorp = 1

    # ----- the field goal -----

    def field_goal(self):
        g, s, snd = self.g, self.s, self.snd
        g.empty_replay()
        g.log_print("")
        g.ptf = 1
        g.say4(" " + self.kicker(s.wisoff, 1) + P.FG_IN)
        g.say4(" " + self.kicker(s.wisoff, 2) + P.WILL_HOLD)
        self.rady(0x442081)
        self.kicksnap()
        snd.play_noise()
        g.say4(P.SNAP_IS_GOOD)
        self.rady(0x4421d1)
        g.say4(P.HOLD_IS_GOOD)
        snd.play(7, -1500)
        g.say4(P.KICK_IS_UP)
        self.rady(0x442390)
        snd.c2dh()
        if not ((s.wisoff == 1 and s.half == 1) or s.wisoff == 2):
            snd.c2df()                                    # the player kicking from his own half
            snd.play(12, -1200)
            g.say4(P.WAY_TO_SHORT)                         # the log flag stays on (Q30)
            snd.stop_play_noise()                         # Q57 not reproduced (D-034, G-A2)
            self.outcome(O.FIELD_GOAL_SHORT)
            s.text = P.ITS_SPACE
            return self.possession
        odds = self.rules.modifiers.field_goal_odds(s.wisoff)
        good = 0
        for _ in range(FIELD_GOAL_DRAWS):
            if self.rnd(odds) > s.yard_line:
                good += 1
        if good >= FIELD_GOAL_NEEDED:
            snd.c2df()
            snd.play(12, -1200)
            g.say4(P.IS_GOOD)
            g.ptf = 0
            snd.play_tackle(8)
            self.outcome(O.FIELD_GOAL_GOOD, score="field goal")
            s.points = 3
            return self.score
        miss = self.rnd(6)
        snd.c2df()
        level = -1000                                     # the uprights and the cross bar
        if miss < 3 or miss == 6:
            level = -1200                                 # wide left, wide right, short
        snd.play(12, level)
        g.say4(P.FG_MISSES[miss - 1])
        g.ptf = 0
        snd.play_tackle(8)
        self.outcome(O.FIELD_GOAL_MISSED, turnover=True)
        s.text = P.ITS_SPACE
        return self.possession

    # ----- the punt -----

    def punt(self):
        g, s, snd, rnd = self.g, self.s, self.snd, self.rnd
        g.empty_replay()
        snd.c2uh()
        g.say4(" " + self.returner(s.defense, 1) + P.AND + self.returner(s.defense, 2) + P.PUNT_BACK_DEEP)
        g.say4(" " + self.kicker(s.wisoff, 2) + P.READY_TO_PUNT + P.KICK_THE_PUNT)
        self.rady(0x443238)
        self.kicksnap()
        snd.play_noise()
        g.say4(self.kicker(s.wisoff, 2) + P.LONG_SNAP)
        snd.c2uf()
        self.rady(0x44345b)
        snd.play(7, -1200)
        g.say4(s.he_she[s.wisoff + 2] + P.KICK_OFF_GETS)
        self.rady(0x443631)
        snd.c2dh()
        odds, shortest = self.rules.modifiers.punt(s.wisoff)
        s.yards = rnd.below(odds) + shortest                  # L32c = Int(Rnd * 35) + 25
        kind = P.POOCH if s.yards < 40 else (P.PRETTY_GOOD if s.yards < 50 else P.HIGH_BOOMING)
        g.say4(P.ITS_A + kind)
        self.rady(0x443861)
        snd.c2df()
        s.punt_flag = 1
        text = P.IT_TRAVELS + self.str_(s.yards) + P.YARDS_IN_THE_AIR
        snd.play(12, -1000)
        g.say4(text)
        end = rnd(3)
        if end == 1:
            text = " " + self.returner(s.defense, rnd(2)) + P.FAIR_CATCH
        elif end == 2:
            text = P.OUT_OF_BOUNDS_PUNT
        else:
            text = P.DOWNED_BY + self.receiver(s.wisoff, rnd(6)) + " "
        g.say4(text)
        snd.play_tackle(8)
        s.result_kind = O.PUNT
        return self.end_of_play

    # ----- the kick-off (L_444645) -----

    def kick_off(self):
        """The receiving side is wisoff, the kicking side L504."""
        g, s, snd, rnd = self.g, self.s, self.snd, self.rnd
        kind = self.rules.before_kickoff(s, s.defense)       # H4: the kind (Classic: "normal", no question)
        if kind != NORMAL_KICKOFF:
            raise NotImplementedError("kick-off kind %r: the onside kick is built in SX.4" % (kind,))
        if s.first_kickoff:                                  # L8a8 = 1: the first kick-off records its receiver
            s.opening_receiver = s.wisoff
            s.first_kickoff = False
        g.empty_replay()
        s.offense_play = 0
        self.mark_spot()
        snd.c2uh()
        g.say4(" " + self.returner(s.wisoff, 1) + P.AND + self.returner(s.wisoff, 2) + P.KICKOFF_BACK_DEEP)
        self.dy(0.2, 0x444949)
        g.say4(self.kicker(s.defense, 1) + P.READY_TO_KICK_OFF)
        snd.play_tackle(8)
        snd.c2uf()
        snd.play(7, -1200)
        snd.play_noise()
        g.say4(P.KICKOFF_UP)
        s.returner = rnd(2)
        text = self.returner(s.wisoff, s.returner) + P.CATCHES_THE_BALL
        deep = rnd(7)
        text += self.str_(deep) + P.YARD + (P.YARD_SPACE if deep == 1 else P.YARDS_SPACE) + P.DEEP_IN_THE_END_ZONE
        self.dy(0.2, 0x445053)
        self.rady(0x4450aa)
        self.rady(0x4450f5)
        snd.play(12, -1000)
        snd.c2dh()
        g.say4(text)
        if s.wisoff == 2:                                    # the computer returns 1 time in 2
            return self.kick_return if rnd(2) == 1 else self.touch_back
        return self.run_it_out

    def run_it_out(self):
        """4.16: the player's returner, run it out or not (Q17: every key but Enter, F1, y and n toggles). The play
        noise of the kick-off still loops here, as in the original (no PlayTackle before this question)."""
        g, s = self.g, self.s
        while True:                                          # L_4452a1
            g.say5(" " + self.coach + P.RUN_IT_OUT_1 + self.returner(s.wisoff, s.returner) + P.RUN_IT_OUT_2)
            answer = 1
            while True:                                      # L_445429
                g.say5(P.YES if answer == 1 else P.NO)
                self.getkey2(net=False)
                code = self.g_code
                if code == KEY_ENTER:
                    return self.touch_back if answer == 2 else self.kick_return
                if code == KEY_F1:
                    break
                if code not in (KEY_UP, KEY_DOWN):
                    g.saykey()
                    if self.g_char == "y":
                        answer = 1
                        continue
                    if self.g_char == "n":
                        answer = 2
                        continue
                answer = 2 if answer == 1 else 1

    def kick_return(self):
        """L_445772."""
        g, s, rnd = self.g, self.s, self.rnd
        last = s.last_return_run
        run = rnd.redraw(lambda: rnd(len(P.RETURN_RUNS)), lambda n: n != last, lambda: 1 if last != 1 else 2,
                         "return description")
        s.last_return_run = run
        g.say4(P.RETURN_RUNS[run - 1])
        kind = rnd(RETURN_KIND_ODDS)
        reach = RETURN_RANGES.get(kind, RETURN_RANGE)
        yards = rnd.below(reach) + RETURN_SHORTEST
        self.rady(0x445d42)
        if yards > 4:
            self.rady(0x445dc0)
            g.say4(self.returner(s.wisoff, s.returner) + P.IS_AT_THE_5)
        for (past, text), site in zip(P.RETURN_MARKS, RETURN_MARK_SITES):
            if yards > past:
                self.rady(site)
                g.say4(text)
        if yards > 50:
            self.rady(0x4466a6)
            g.say4(P.ONE_MAN_TO_BEAT)
        tackle = P.CUT_DOWN if yards < 20 else (P.TACKLED if yards < 30 else P.FINALLY_TACKLED)
        first = rnd(17)
        tackle += " " + self.defender(s.defense, first) + " "
        s.tackle_sound = 3
        if yards < 51:
            s.tackle_sound = 2
            tackle += P.AND
            second = rnd.redraw(lambda: rnd(17), lambda d: d != first, lambda: 2 if first == 1 else 1,
                                "second tackler")
            tackle += self.defender(s.defense, second) + " "
        s.tackle_sentence = tackle
        s.yard_line = 0
        s.to_go = 1
        s.return_flag = True
        s.yards = yards
        s.result_kind = O.KICKOFF_RETURN
        return self.end_of_play

    def touch_back(self):
        """L_446c75."""
        g, s, snd = self.g, self.s, self.snd
        g.say4(P.DOWNS_IN_END_ZONE)
        snd.play_tackle(8)
        snd.c2df()
        self.outcome(O.KICKOFF_TOUCH_BACK, yards=0)
        s.text = P.ITS_CAPITAL
        s.yard_line = 20
        s.to_go = 10
        s.down = 1
        return self.position

    # ----- after the player's touchdown: the extra point or the two-point try (4.17) -----

    def extra_point_choice(self):
        """L_44f6f0 (Q18: F2, F3, F4 and every other key give the prompt again with the kick)."""
        g, s = self.g, self.s
        while True:
            g.say5(" " + self.coach + P.SELECT)
            choice = 1
            while True:
                g.say5(P.KICK_FOR_EXTRA_POINT if choice == 1 else P.TRY_FOR_TWO)
                self.getkey2()
                if self.g_code == KEY_ENTER:
                    g.empty_replay()
                    if choice == 1:
                        return self.extra_point
                    g.log_print("")
                    s.two_point = True
                    s.yard_line = 2
                    return self.offense_menu
                if self.g_code in (KEY_UP, KEY_DOWN):
                    choice = 2 if choice == 1 else 1
                    continue
                if self.g_code == KEY_F3:
                    g.say_score(s.score(1), s.score(2))
                if self.g_code == KEY_F4:
                    self.clock.speak()
                if self.g_code == KEY_F2:
                    g.inrep()
                break

    def extra_point(self):
        """L_44fd30: it never fails (Q21)."""
        g, s, snd = self.g, self.s, self.snd
        text = " " + self.kicker(s.wisoff, 1) + P.XP_IN
        g.ptf = 1
        g.say4(text)
        g.say4(" " + self.kicker(s.wisoff, 2) + P.WILL_HOLD)
        self.rady(0x44ff7d)
        self.kicksnap()
        g.say4(P.SNAP_IS_GOOD)
        self.rady(0x450082)
        g.say4(P.HOLD_IS_GOOD)
        snd.play(7, -1500)
        g.say4(P.KICK_IS_UP)
        self.rady(0x450241)
        g.say4(P.XP_GOOD)
        g.ptf = 0
        snd.play(12, -1200)
        snd.play_tackle(8)
        snd.c2df()
        s.points = 1
        return self.score

    def try_result(self):
        """L_450499: 2 points when the try reached the end zone, else 0 (Q22: not announced)."""
        g, s = self.g, self.s
        g.ptf = 0
        if s.try_good:
            g.ptf = 0
            self.snd.play_tackle(8)
            g.ptf = 1
            g.say4(P.TWO_POINT_GOOD)
            g.ptf = 0
            s.points = 2
        else:
            s.points = 0
        s.two_point = False
        s.try_good = False
        return self.score


__all__ = ["KickSteps", "other"]
