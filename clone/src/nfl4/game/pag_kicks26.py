"""pag, the kicks of 2026 in the N. F. L. rules mode with a playbook (nfl4 only, CLAUDE.md rule 0.13; NX-R7: G26-1, G26-4 to G26-7,
G26-11, G26-13; NFL_PLAYS_DESIGN 2.6 and 4.9; built in SX.10d, D-094). This is inspired by Jim Kitchen.

Never taken in Classic: `rules.special_kick` answers None and `before_kickoff` never answers KICKOFF_2026, with no draw and no word,
so the original's kicks (pag_kicks.py) play. With the kicks of 2026 each kick keeps the original's set-up (the sentences, the sounds, the
pauses and the snap count of the punter) and its ending steps (the end point, the possession or position sentence, the score), and the
result in between is the outcome model's (extras/kick_flow.py, extras/plays/model.py):

    kickoff_2026      deep, short, squib or the safety punt; a touch back at the 35, out of bounds or short of the landing zone at the
                      40, a catch in the end zone (the player is asked to run it out, as the original asks) or in the field, the return
                      told with the original's return sentences and tacklers
    punt_2026         the kinds of punt, a block, a fair catch (the fair catch kick may follow), a muff, a return, a touch back at the 20
    field_goal_2026   any distance; made, missed (the ball at the spot of the kick or the 20, G26-7), blocked and run back; the fair
                      catch kick (no snap, no rush)
    extra_point_2026  from the 15: good, no good, blocked and run back for two points
    fake_kick         a fake punt or field goal: a run or a pass that ends in the field of play, told with the original's endings
The ball's place is set before each end point, so the extras' penalty flow sees where the kick left it.
"""
from __future__ import annotations

from . import outcome as O
from . import phrases as P
from .gamestate import other, own_half

FIELD_GOAL, PUNT, EXTRA_POINT, FAIR_CATCH_KICK = "field goal", "punt", "extra point", "fair catch kick"   # extras/kick_flow.py
SHORT, SQUIB, SAFETY_PUNT = "K002", "K003", "K027"
NOT_RETURNED = {"out_of_bounds": "out_of_bounds", "landed_short": "landed_short", "touchback": "touchback_35"}


def put(s, side: int, distance: int) -> None:
    """The ball `distance` yards from `side`'s own goal line (the original's half and yard line)."""
    if distance <= 50:
        s.half, s.yard_line = own_half(side), distance
    else:
        s.half, s.yard_line = own_half(other(side)), 100 - distance


def to_goal(s) -> int:
    """The yards from the line of scrimmage to the goal line the offense attacks."""
    return 100 - s.yard_line if s.half == own_half(s.wisoff) else s.yard_line


class Kick26Steps:

    def text26(self, key: str, **values) -> str:
        return self.rules.kick_text(key, **values)

    # ----- the kick-off (G26-1, G26-11) -----

    def kickoff_2026(self):
        """The receivers are wisoff, the kicking team L504 (as the original's kick-off)."""
        g, s, snd, rnd = self.g, self.s, self.snd, self.rnd
        call = self.rules.kickoff_call(s)
        snd.c2uh()
        g.say4(" " + self.returner(s.wisoff, 1) + P.AND + self.returner(s.wisoff, 2) + P.KICKOFF_BACK_DEEP)
        self.dy(0.2, 0x444949)
        g.say4(self.kicker(s.defense, 1) + P.READY_TO_KICK_OFF)
        snd.play_tackle(8)
        snd.c2uf()
        self.go_live()                                       # H18: the kick is made; a T key is only kept from here
        snd.play(7, -1200)
        snd.play_noise()
        if call == SAFETY_PUNT:
            g.say4(self.text26("safety_punt", kicker=self.kicker(s.defense, 2)))
        elif call == SHORT:
            g.say4(self.text26("short_kick", kicker=self.kicker(s.defense, 1)))
        elif call == SQUIB:
            g.say4(self.text26("squib_kick", kicker=self.kicker(s.defense, 1)))
        else:
            g.say4(P.KICKOFF_UP)
        s.returner = rnd(2)
        result = self.rules.kickoff_result(s)
        returner = self.returner(s.wisoff, s.returner)
        if result.kind in NOT_RETURNED:
            return self.kick_not_returned(self.text26(NOT_RETURNED[result.kind]), result.start)
        # the safety punt (a free kick from the 20) may also end as a punt does: a touch back at the 20, a fair catch, downed, dead
        if result.kind == "punt_touchback":
            return self.kick_not_returned(P.IT_IS_A_TOUCH_BACK, result.start)
        if result.kind == "fair_catch":
            return self.kick_not_returned(" " + returner + P.FAIR_CATCH, result.start)
        if result.kind == "downed":
            return self.kick_not_returned(P.DOWNED_BY + self.receiver(s.defense, rnd(6)) + " ", result.start)
        if result.kind == "dead":
            return self.kick_not_returned(self.text26("rolls_dead"), result.start)
        catch = result.start - result.returned               # the receivers' yard line of the catch (0 or less: in the end zone)
        if catch <= 0:
            deep = max(1, -catch)
            text = returner + P.CATCHES_THE_BALL + self.str_(deep) + P.YARD + (P.YARD_SPACE if deep == 1 else P.YARDS_SPACE)
            text += P.DEEP_IN_THE_END_ZONE
        else:
            text = self.text26("caught_at", returner=returner, n=catch)
        self.dy(0.2, 0x445053)
        self.rady(0x4450aa)
        self.rady(0x4450f5)
        snd.play(12, -1000)
        snd.c2dh()
        g.say4(text)
        if catch <= 0 and s.wisoff == 1 and not result.touchdown and not self.ask_run_it_out():
            g.say4(P.DOWNS_IN_END_ZONE)                       # the player downs it: a touch back at the 35 (RB26 6-2)
            return self.kick_not_returned("", self.rules.kickoff_touchback())
        return self.return_2026(catch, result.start, result.returned)

    def kick_not_returned(self, sentence: str, line: int):
        """A kick-off nobody runs back: the sentence, the whistle (foot11, which stops the play noise), the crowd down, the end point, the
        receivers' first down at `line` (their yard line)."""
        g, s, snd = self.g, self.s, self.snd
        if sentence:
            g.say4(sentence)
        snd.play_tackle(8)
        snd.c2df()
        put(s, s.wisoff, line)
        step = self.end_point(O.KICKOFF_TOUCH_BACK, yards=0)
        if step is not None:
            return step
        s.text = P.ITS_CAPITAL
        s.down, s.to_go = 1, 10
        return self.position

    def return_2026(self, catch: int, end: int, back: int):
        """The return of a kick-off (L_445772's sentences and draws) to the receivers' yard line `end` (100: a touchdown): the return's
        sentence, the marks passed after the catch, the tacklers; the play ends as the original's return."""
        g, s, rnd = self.g, self.s, self.rnd
        last = s.last_return_run
        run = rnd.redraw(lambda: rnd(len(P.RETURN_RUNS)), lambda n: n != last, lambda: 1 if last != 1 else 2, "return description")
        s.last_return_run = run
        g.say4(P.RETURN_RUNS[run - 1])
        self.rady(0x445d42)
        if end > 4 and catch < 5:
            self.rady(0x445dc0)
            g.say4(self.returner(s.wisoff, s.returner) + P.IS_AT_THE_5)
        for past, text in P.RETURN_MARKS:
            if end > past and past >= catch:
                self.rady(0x445f3e)
                g.say4(text)
        if end > 50:
            self.rady(0x4466a6)
            g.say4(P.ONE_MAN_TO_BEAT)
        tackle = P.CUT_DOWN if back < 20 else (P.TACKLED if back < 30 else P.FINALLY_TACKLED)
        first = rnd(17)
        tackle += " " + self.defender(s.defense, first) + " "
        s.tackle_sound = 3
        if end < 51:
            s.tackle_sound = 2
            tackle += P.AND
            second = rnd.redraw(lambda: rnd(17), lambda d: d != first, lambda: 2 if first == 1 else 1, "second tackler")
            second = self.rules.second_tackler(s, first, second)
            tackle += self.defender(s.defense, second) + " "
        s.tackle_sentence = tackle
        s.half, s.yard_line = own_half(s.wisoff), 0
        s.to_go = 1
        s.return_flag = True
        s.yards = end
        s.result_kind = O.KICKOFF_RETURN
        return self.end_of_play

    # ----- the punt (G26-5) -----

    def punt_2026(self, plan):
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
        if plan.fake:
            return self.fake_kick(plan, self.kicker(s.wisoff, 2))
        snd.play(7, -1200)
        result = self.rules.kick_result(s, plan)
        receivers = s.defense
        if result.kind == "blocked":
            g.say4(self.text26("punt_blocked"))
            snd.play_tackle(8)
            snd.c2df()
            return self.punt_over(result.start, 0)
        g.say4(s.he_she[s.wisoff + 2] + P.KICK_OFF_GETS)
        self.rady(0x443631)
        snd.c2dh()
        gross = result.gross
        g.say4(P.ITS_A + (P.POOCH if gross < 40 else (P.PRETTY_GOOD if gross < 50 else P.HIGH_BOOMING)))
        self.rady(0x443861)
        snd.c2df()
        snd.play(12, -1000)
        g.say4(P.IT_TRAVELS + self.str_(gross) + P.YARDS_IN_THE_AIR)
        returner = self.returner(receivers, rnd(2))
        kind = result.kind
        if kind == "touchback":
            g.say4(P.IT_IS_A_TOUCH_BACK)
        elif kind == "fair_catch":
            g.say4(" " + returner + P.FAIR_CATCH)
            self.rules.fair_catch(s, receivers, result.start)
        elif kind == "out_of_bounds":
            g.say4(P.OUT_OF_BOUNDS_PUNT)
        elif kind == "downed":
            g.say4(P.DOWNED_BY + self.receiver(s.wisoff, rnd(6)) + " ")
        elif kind == "dead":
            g.say4(self.text26("rolls_dead"))
        elif kind == "muffed":
            g.say4(self.text26("muffed", returner=returner, team=s.teams[s.wisoff]))
            snd.play_tackle(8)
            return self.punt_muffed(result.start, gross)
        elif result.touchdown:
            g.say4(self.text26("return_td", player=returner))
            snd.play_tackle(8)
            step = self.end_point(O.PUNT, turnover=True)
            return step if step is not None else self.return_touchdown()
        else:
            back = result.returned
            g.say4(self.text26("punt_return", returner=returner, n=back) if back > 0
                   else self.text26("punt_return_none", returner=returner))
            g.say4(self.text26("brought_down", player=self.defender(s.wisoff, rnd(17))))
        snd.play_tackle(8)
        return self.punt_over(result.start, gross)

    def punt_over(self, line: int, gross: int):
        """The receivers' ball at their yard line `line`: the end point, then the original's possession sentence."""
        s = self.s
        s.result_kind = O.PUNT
        s.yards = gross
        put(s, s.defense, line)
        s.punt_flag = 2                                      # the possession sentence of a punt (no replay list to the log)
        step = self.end_point(O.PUNT, turnover=True)
        if step is not None:
            return step
        s.text = P.ITS_SPACE
        return self.possession

    def punt_muffed(self, line: int, gross: int):
        """The kicking team fell on the receivers' muff: its first down where the ball was (the receivers' yard line `line`)."""
        s = self.s
        s.result_kind = O.PUNT
        s.yards = gross
        put(s, s.defense, line)
        step = self.end_point(O.PUNT)
        if step is not None:
            return step
        s.punt_flag = 0
        s.down, s.to_go = 1, 10
        s.text = P.ITS
        return self.position

    # ----- the field goal and the fair catch kick (G26-6, G26-7, G26-13) -----

    def field_goal_2026(self, plan):
        g, s, snd = self.g, self.s, self.snd
        g.empty_replay()
        g.log_print("")
        g.ptf = 1
        fair_catch_kick = plan.what == FAIR_CATCH_KICK
        if fair_catch_kick:
            g.say4(self.text26("fair_catch_kick", kicker=self.kicker(s.wisoff, 1)))
        else:
            g.say4(" " + self.kicker(s.wisoff, 1) + P.FG_IN)
        g.say4(" " + self.kicker(s.wisoff, 2) + P.WILL_HOLD)
        self.rady(0x442081)
        if fair_catch_kick:
            self.go_live()                                   # no snap: the kick is a free kick
        else:
            self.kicksnap()
            snd.play_noise()
            g.say4(P.SNAP_IS_GOOD)
            if plan.fake:
                g.ptf = 0
                return self.fake_kick(plan, self.kicker(s.wisoff, 2))
            self.rady(0x4421d1)
            g.say4(P.HOLD_IS_GOOD)
        snd.play(7, -1500)
        result = self.rules.kick_result(s, plan)
        spot = plan.kick_spot                               # the spot of the kick, from the defense's goal line
        if result.kind == "blocked":
            g.say4(self.text26("kick_blocked"))
            g.ptf = 0
            snd.play_tackle(8)
            snd.c2df()
            put(s, s.defense, spot)
            if result.touchdown:
                g.say4(self.text26("blocked_return_td", player=self.defender(s.defense, self.rnd(17))))
                step = self.end_point(O.FIELD_GOAL_MISSED, turnover=True)
                return step if step is not None else self.return_touchdown()
            step = self.end_point(O.FIELD_GOAL_MISSED, turnover=True)
            if step is not None:
                return step
            s.text = P.ITS_SPACE
            return self.possession
        g.say4(P.KICK_IS_UP)
        self.rady(0x442390)
        snd.c2dh()
        if result.kind == "made":
            snd.c2df()
            snd.play(12, -1200)
            g.say4(P.IS_GOOD)
            g.ptf = 0
            snd.play_tackle(8)
            step = self.end_point(O.FIELD_GOAL_GOOD, score="field goal")
            if step is not None:
                return step
            s.points = 3
            return self.score
        miss = self.rnd(6)
        snd.c2df()
        snd.play(12, -1000 if 3 <= miss <= 5 else -1200)
        g.say4(P.FG_MISSES[miss - 1])
        g.ptf = 0
        snd.play_tackle(8)
        put(s, s.defense, plan.miss_spot)                   # RB26 11-4-2: the spot of the kick, or the 20 (G26-7)
        step = self.end_point(O.FIELD_GOAL_MISSED, turnover=True)
        if step is not None:
            return step
        s.text = P.ITS_SPACE
        return self.possession

    def fair_catch_kick(self):
        """The player said yes to the fair catch kick (H10): it is the next snap, a field goal the extras tell as the fair catch kick."""
        s = self.s
        s.defense = other(s.wisoff)
        s.offense_play, s.defense_play = 6, 1
        self.t_choice = None
        return self.snap

    # ----- the extra point (G26-4) -----

    def extra_point_2026(self, plan):
        g, s, snd = self.g, self.s, self.snd
        g.ptf = 1
        g.say4(" " + self.kicker(s.wisoff, 1) + P.XP_IN)
        g.say4(" " + self.kicker(s.wisoff, 2) + P.WILL_HOLD)
        self.rady(0x44ff7d)
        self.kicksnap()
        g.say4(P.SNAP_IS_GOOD)
        self.rady(0x450082)
        g.say4(P.HOLD_IS_GOOD)
        snd.play(7, -1500)
        result = self.rules.kick_result(s, plan)
        s.points = 0
        if result.kind == "blocked":
            g.say4(self.text26("kick_blocked"))
            g.ptf = 0
            snd.play_tackle(8)
            snd.c2df()
            if result.touchdown:                             # RB26 11-3-2: the defense scores two points on a try
                g.say4(self.text26("blocked_try_two", player=self.defender(s.defense, self.rnd(17))))
                s.stats[s.defense].score += 2
            return self.score
        g.say4(P.KICK_IS_UP)
        self.rady(0x450241)
        g.say4(P.XP_GOOD if result.kind == "good" else self.text26("extra_point_missed"))
        g.ptf = 0
        snd.play(12, -1200)
        snd.play_tackle(8)
        snd.c2df()
        if result.kind == "good":
            s.points = 1
        return self.score

    # ----- the fakes -----

    def fake_kick(self, plan, kicker: str):
        """A fake punt or field goal (K015, K016, K022, K023): the punter or the holder runs or throws; the play ends in the field of play
        as a run or a pass of the original (the downs decide what follows)."""
        g, s, rnd = self.g, self.s, self.rnd
        g.say4(self.text26("fake"))
        yards = min(self.rules.fake_yards(s, plan), to_goal(s))
        stats = s.stats[s.wisoff]
        if plan.kind == "run":
            s.offense_play, s.play_kind = 1, 1
            g.say4(self.text26("fake_run", player=kicker))
            s.tackle_sentence = self.text26("brought_down", player=self.defender(s.defense, s.defender1))
            s.tackle_sound = 2
            s.result_kind = O.RUN
            stats.running_plays += 1
            stats.running_yards += yards
        else:
            s.offense_play, s.play_kind = 4, 2
            g.say4(self.text26("fake_pass", player=kicker))
            stats.pass_attempts += 1
            receiver = self.receiver(s.wisoff, s.carrier)
            if yards > 0:
                stats.completions += 1
                stats.passing_yards += yards
                s.tackle_sound = rnd(2) + 1
                number = s.catch_history.draw(rnd, len(P.CATCH_PHRASES), "catch phrase")
                s.tackle_sentence = P.AND + receiver + P.CATCH_PHRASES[number - 1]
                s.result_kind = O.PASS_COMPLETE
            else:
                yards = 0
                s.tackle_sentence = P.FALLS_SHORT_OF + receiver + " "
                s.tackle_sound = 8
                s.result_kind = O.PASS_INCOMPLETE
        s.yards = yards
        return self.end_of_play
