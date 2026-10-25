"""pag, part 5: the next-play step, the periods, the statistics, the key wait, the end, Save Game and conceding. This is inspired by Jim Kitchen.

GAME_SPEC 5.6, 4.18, 4.19 (CODE (lifted) pag 0x43cc68 (the next-play step and the period checks), GoSub 0x45f30f (the
key wait), GoSub 0x45d0be (the quarter statistics), 0x4533d7 (the end of the game and overtime), 0x45f5f9 (Save Game),
0x45ffe2 (quit and concede), 0x4608e3 (the crowds stop)). Every reading of the play counter goes through the period
clock (H1).
"""
from __future__ import annotations

from . import phrases as P
from . import program_texts, save_texts
from .gamestate import other, own_half
from .rules import OT_COIN_TOSS, OT_KICK_OFF
from .vbnum import trim

KEY_F1, KEY_F2, KEY_F3, KEY_F4 = "112", "113", "114", "115"
KEY_ENTER, KEY_UP, KEY_DOWN, KEY_TAB = "13", "38", "40", "9"


class BreakSteps:

    # ----- the next-play step (L_43cc68) -----

    def next_play(self):
        s = self.s
        s.defense = other(s.wisoff)
        self.clock.after_play(self.last_outcome)
        return self.period_checks()

    def period_checks(self):
        """The rest of the next-play step: the warnings and the ends of the periods. Also a step of its own (N. F. L.
        rules mode, SX.2): a pending runoff that ran the period out at the snap ends the period here, without counting
        another play (Classic never takes that way: its clock never says so)."""
        g, s, clock, snd = self.g, self.s, self.clock, self.snd
        if s.quarter <= 1:
            if clock.period_over():
                self._end_of_quarter(1)
                clock.start_period(1)
                s.quarter = 2
                self.key_wait()
                self.quarter_stats()
            return self.play_menu
        if s.quarter <= 2:
            self._two_minute_warning()
            if clock.period_over():
                self._end_of_quarter(2)
                clock.start_period(0)
                s.quarter = 3
                self.key_wait()
                self.quarter_stats()
                s.wisoff = 2 if s.opening_receiver == 1 else 1      # `If L158 <> 1`: Empty gives the player
                s.defense = other(s.wisoff)
                s.half = own_half(s.wisoff)
                g.halftime()
                self.snd.commercial("halftime")                      # owner rule 0.14
                self.rules.broadcast_moment(s, "half_time")          # H23
                return self.kick_off
            return self.play_menu
        if s.quarter <= 3:
            if clock.period_over():
                self._end_of_quarter(3)
                clock.start_period(1)
                s.quarter = 4
                self.key_wait()
                self.quarter_stats()
            return self.play_menu
        if s.quarter <= 4:
            self._two_minute_warning()
            if clock.period_over():
                snd.whistle_context = "final"
                snd.play_tackle(8)
                return self.game_end
            return self.play_menu
        self._two_minute_warning()                                   # overtime
        if clock.period_over():
            following = self.rules.period_end_step(s)                # H22 (SX.12): a play-off overtime period goes on (Classic: None)
            if following is not None:
                return self.next_overtime_period(following)
            snd.play(2, 0)                                           # foot2 once, waited (0x43dd2a)
            return self.game_end
        return self.play_menu

    def next_overtime_period(self, following: str):
        """N. F. L. rules (SX.12, 16-1-4; never in Classic): a play-off overtime period ended with no winner. The next one begins as the
        original's overtime does (the sentence, the key wait, the statistics) and starts with the ball where it was, a kick-off by the side
        that received the last tossed period's (16-1-4 (e)), or a new coin toss (16-1-4 (i))."""
        g, s = self.g, self.s
        s.overtime += 1
        g.ptf = 1
        g.say4(P.OVERTIME_NUMBER + self.str_(s.overtime))
        g.ptf = 0
        self.clock.start_period(0)
        self.key_wait()
        self.quarter_stats()
        if following == OT_COIN_TOSS:
            return self.overtime_coin_toss
        if following == OT_KICK_OFF:
            chooser = self.rules.third_period_chooser(s)            # SX.13 (16-1-4 (e)): the toss's loser has the first choice
            if chooser == 1:
                return self._receive_or_kick()
            if chooser == 2:
                if self.rules.overtime_kicks_first(s):              # the computer chooses as it does after winning a toss
                    g.say4(self.rules.play_text("overtime_kicks", team=s.teams[2]))
                    s.wisoff, s.defense, s.half = 1, 2, 2
                else:
                    g.say4(P.THE_TEAM + s.teams[2] + P.CHOOSE_TO_RECEIVE)
                    s.wisoff, s.defense, s.half = 2, 1, 1
                return self.kick_off
            s.wisoff = self.rules.third_period_receiver(s)          # a game saved before SX.13 knows no toss loser: SX.12's reading
            s.defense = other(s.wisoff)
            s.half = own_half(s.wisoff)
            return self.kick_off
        return self.play_menu

    def _end_of_quarter(self, quarter: int) -> None:
        g = self.g
        g.ptf = 1
        g.log_print("")
        self.snd.whistle_context = "quarter"
        self.snd.play_tackle(8)
        g.say4(P.END_OF_QUARTER[quarter])
        g.ptf = 0
        self.rules.broadcast_moment(self.s, "quarter_end", quarter)      # H23: Ghip (the N. F. L. rules' broadcast)
        if quarter != 2:                                             # the end of quarter 2 is the half time break below
            self.snd.commercial("quarter")                           # owner rule 0.14: the player's own commercials, off by default

    def _two_minute_warning(self) -> None:
        """Quarter 2, 4 and overtime: the log flag is on from L2cc - W on (and off again at once), the warning when the
        counter equals it (say4, then GoSub 0x458aa5: PlayTackle(8))."""
        g, clock = self.g, self.clock
        if not clock.warning_zone():
            return
        g.ptf = 1
        if clock.warning_due():
            g.log_print("")
            g.say4(P.TWO_MINUTE_WARNING)
            self.snd.whistle_context = "twominute"
            self.snd.play_tackle(8)
            self.snd.commercial("two-minute-warning")                # owner rule 0.14
            self.rules.broadcast_moment(self.s, "two_minute")        # H23
            clock.warning_given()                                    # H1 (Classic: nothing; the N. F. L. clock: once)
        g.ptf = 0

    # ----- GoSub 0x45f30f: the key wait between periods and after a score -----

    def key_wait(self) -> None:
        g, s = self.g, self.s
        self.t_screen = True                                        # H18: T is the "any key" here, and its timeout waits for the next menu
        try:
            while True:
                self.getkey2()
                code = self.g_code
                if code == KEY_F2:
                    g.inrep()
                    continue
                if code == KEY_F1:
                    g.say5(P.PRESS_ANY_KEY)
                    continue
                if code == KEY_F3:
                    g.say_score(s.score(1), s.score(2))
                    continue
                if code == KEY_F4:
                    self.clock.speak()
                    continue
                return
        finally:
            self.t_screen = False

    # ----- GoSub 0x45d0be: the statistics -----

    def statistics_number(self) -> int:
        """The quarter just ended. The original says L3c0 - 1 + L238, one too high in and after overtime (Q26, not
        reproduced, D-027): the game takes one off once an overtime has started."""
        s = self.s
        number = s.quarter - 1 + s.overtime
        return number - 1 if s.overtime > 0 else number

    def quarter_stats(self) -> None:
        g, s = self.g, self.s
        g.ptf = 1
        g.log_print("")
        g.empty_replay()
        g.quarter_clock.start_quarter()                             # CountDown = 100
        g.say2(P.STATS_AFTER + trim(self.str_(self.statistics_number())))
        values = {side: s.stats[side].stat_values() for side in (1, 2)}
        for index, name in enumerate(P.STAT_NAMES):
            g.say2(name)
            g.say2(s.teams[1] + " " + trim(self.str_(values[1][index])))
            g.say2(s.teams[2] + " " + trim(self.str_(values[2][index])))
        for line in self.rules.extra_stats_lines(s):              # H11 (Classic: nothing)
            g.say2(line)
        g.log_print("")
        g.ptf = 0
        self.t_screen = True                                        # H18: as in key_wait
        try:
            while True:
                g.norep = 1
                self.getkey()
                g.stopspeech()
                if self.g_code in (KEY_F1, KEY_F2):
                    g.inrep()
                    continue
                break
        finally:
            self.t_screen = False
        g.empty_replay()
        g.norep = 0
        # `If L194 = 1 And gtp = 20 Then superbowl, end` cannot happen: the game's end ran superbowl, which set gtp 42
        if s.finished or s.quarter == 3 or s.quarter >= 5:
            return
        self._in_stats = True                                       # L4b0 = 3: banter, position and down, Return
        step = self.banter_position
        while step is not None:
            step = step()
        self._in_stats = False

    # ----- the end of the game (L_4533d7) -----

    def game_end(self):
        g, s = self.g, self.s
        if s.quarter != 5:
            g.ptf = 1
            g.log_print("")
            g.say4(P.END_OF_QUARTER[4])
            g.ptf = 0
        if s.score(1) == s.score(2) and self.rules.overtime_follows(s):     # H22 (SX.12): the regular season's one period may end tied
            s.overtime += 1
            g.ptf = 1
            g.say4(P.OVERTIME_NUMBER + self.str_(s.overtime))
            for line in self.rules.overtime_lines(s):                # H22: the N. F. L. rules' overtime in two sentences (Classic: none)
                g.say4(line)
            g.ptf = 0
            s.quarter = 5
            self.clock.start_period(0)
            self.key_wait()
            self.quarter_stats()
            if self.rules.overtime_toss(s):                          # H22 (SX.12, 16-1-2): a new toss, called by the visitors
                return self.overtime_coin_toss
            s.defense = other(s.wisoff)                              # the side with the ball at the end receives
            s.half = own_half(s.wisoff)                              # Q25 not reproduced: the half is set (D-027)
            return self.kick_off
        self.game_on = False                                        # H18: the final whistle: T calls nothing any more
        g.ptf = 1
        g.say4(P.GAME_IS_OVER)
        for line in self.rules.game_over_lines(s):                  # H22 (SX.12): " The game ends in a tie. " (Classic: none)
            g.say4(line)
        self.rules.broadcast_moment(s, "game_end")                  # H23: Ghip at the final whistle
        g.log_print("")
        g.ptf = 0
        s.final_scores = (s.score(1), s.score(2))
        self.result.scores = s.final_scores
        if g.season.gtp == g.season.playoff_week(4):                # the Super Bowl week: 20, or after a calendar's 18 weeks 22
            g.superbowl(s.final_scores)                             # Q27: once, in place of the final score (S7.3c)
        else:
            self.final_score()
        self.snd.commercial("final")                                # owner rule 0.14: after the final score, before the statistics
        s.quarter += 1
        s.finished = True                                           # L194 = 1
        self.quarter_stats()
        if g.season.gtp == 42:
            g.season.gtp = 0
        return self.finish

    def final_score(self) -> None:
        """0x4537bd: the final score, then a bare DoEvents loop until a key; F2 replays, then F2 and F1 both speak the
        final score again (4.19)."""
        g, s = self.g, self.s
        while True:
            g.ptf = 1
            g.say_final_score(s.score(1), s.score(2))
            g.ptf = 0
            self.keys.clk()
            self._noise_net()
            self.keys.wait_key()
            if self.g_code == KEY_F2:
                g.inrep()
                continue
            if self.g_code == KEY_F1:
                continue
            return

    def finish(self):
        """L_4608e3: crowd 1 and crowd 2 stop; pag returns."""
        self.snd.stop_crowds()
        return None

    # ----- Save Game (4.18; L_45f5f9) -----

    def save_game(self):
        g, s, ui = self.g, self.s, self.save_ui
        self.game_on = False                                        # H18: the game is saved (it is put back on if it could not be)
        self.result.saved = True                                    # SavedGame = 1
        record = self.save_record()
        slot = None
        if ui is not None:                                          # SX.14 (NX-S6): which of the three places, the game's own first
            slot = ui.choose_slot(self, record)
            if slot is None:                                        # Escape: nothing is saved and the game goes on where it was
                self.result.saved = False
                self.game_on = True
                g.say(save_texts.SAVE_CANCELLED)
                return self.continuation(self.rules.resume_choice(s)) or self.play_menu
        written = (self.save_sink(record) if ui is None else self.save_sink(record, slot)) if self.save_sink is not None else None
        if written is False:                                        # football.sav could not be written (S7.5)
            self.result.saved = False
            self.game_on = True
            g.say(program_texts.SAVE_FAILED)                        # the game goes on: nothing was kept (N. F. L. rules, SX.9:
            return self.continuation(self.rules.resume_choice(s)) or self.play_menu     # a choice at the prompt is asked again)
        self.keys.pump()
        g.say(P.GAME_SAVED)
        self.keys.pump()
        if ui is not None:                                          # SX.14 (NX-S5): quit (the original's end) or keep playing
            if ui.quit_or_keep(self, slot) == "keep":
                self.result.saved = False
                self.game_on = True
                return self.continuation(self.rules.resume_choice(s)) or self.play_menu
            ui.saved_and_quit(self, slot)
        return None                                                 # the crowds are not stopped (Q33)

    # ----- quit and concede (4.18; L_45ffe2) -----

    def concede(self):
        g, s, snd = self.g, self.s, self.snd
        while True:
            for _ in range(2):
                for _ in range(3):
                    snd.play2("foot13")                             # a key stops the current bleep only
                self.dy(0.5, 0x46019b)
            answer = 2
            g.say5(P.CONCEDE)
            again = False
            while True:
                self.getkey()
                code = self.g_code
                if code == KEY_ENTER:
                    break
                if code in (KEY_TAB, KEY_UP, KEY_DOWN):
                    answer = 1 if answer == 2 else 2
                    g.say5(P.YES if answer == 1 else P.NO)
                    continue
                g.saykey()
                if self.g_char == "n":
                    answer = 2
                    break
                if self.g_char == "y":
                    answer = 1
                    break
                again = True
                break
            if again:
                continue
            if answer == 2:
                return self.play_menu
            self.game_on = False                                    # H18: conceded, the game is over
            own, opponent = s.score(1), s.score(2)
            if own >= opponent:                                     # a loss whatever the score (Me.m414)
                own = 0
                if opponent == 0:
                    opponent = 1
            s.final_scores = (own, opponent)
            self.result.scores = s.final_scores
            self.result.conceded = True
            return self.finish
