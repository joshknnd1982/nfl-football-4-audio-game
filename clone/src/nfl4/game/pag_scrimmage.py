"""pag, part 2: the snap and the plays from scrimmage (GAME_SPEC 5.8, 5.9). This is inspired by Jim Kitchen.

CODE (lifted) pag 0x43fd12 to 0x44dfda. Every random draw is the original's, in its order and range; the players L31c and
L390 are not drawn (they only name the fake texts that are never spoken, Q35, Q40, D-028 item 5). See pag.py for the
structure; the steps return the next step.
"""
from __future__ import annotations

from . import outcome as O
from . import phrases as P
from .playtables import (FUMBLE_NUMBER, INTERCEPTION_FLOOR, INTERCEPTION_NUMBER, PASSES, QB_SNEAK, RUNS, SACK,
                         SACK_PHRASES)
from .rules import FOUL_BEFORE_SNAP, GO_ON, SCRAMBLE
from .setup import RUN_DIRECTIONS, SNAP_WORDS
from .vbnum import single


class ScrimmageSteps:

    def snap(self):
        """L_43fd12: after the choice of both plays."""
        s = self.s
        if self.clock.before_snap():                     # H1: a pending runoff ran the period out (N. F. L. rules only;
            return self.period_checks                    # Classic returns None): the period ends before the snap
        verdict = self.rules.before_snap(s, s.offense_play, s.defense_play)   # H2 step 2 (Classic: always on)
        if verdict == FOUL_BEFORE_SNAP:                  # N. F. L. rules (SX.3): a dead-ball foul, the play is not run:
            self.snap_count(until_first_hut=True)        # the snap count up to " hut 1 ", then the flag
            return self.continuation(self.rules.foul_before_snap(s)) or self.play_menu
        if verdict != GO_ON:
            return self.play_menu
        self.mark_spot()
        s.qb_run, s.slid = "", False                    # no quarterback run yet (N. F. L. rules mode, SX.5)
        if s.offense_play == 6:
            return self.field_goal
        if s.offense_play == 7:
            self.snap_draws()
            return self.punt
        self.snap_count()
        self.snap_draws()
        return self.snap_phrase

    def snap_count(self, until_first_hut: bool = False) -> None:
        """0x43fda9 to 0x440e12: the huddle, the quarterback at the line and his calls, " Hike! ", the hike sound.
        until_first_hut (N. F. L. rules, SX.3; never in Classic): a dead-ball foul stops it right after " hut 1 "."""
        g, s, rnd, snd = self.g, self.s, self.rnd, self.snd
        line = self.qb(s.wisoff) + P.QB_LINE[rnd(4) - 1]                      # drawn first (0x43fe61)
        huddle = P.THE_TEAM + s.teams[s.wisoff]
        huddle += P.NO_HUDDLE if rnd(10) == 7 else P.HUDDLE_BROKEN              # drawn second (0x440093)
        g.say5(huddle)
        snd.c2uh()
        g.say5(line)
        snd.c2uf()
        self.dy(0.2, 0x44027e)
        self.say3(P.HUT_1)
        if until_first_hut:
            return
        self.rady(0x440344)
        if rnd(7) == 3:
            self.say3(P.HUT_2)
            self.rady(0x4404a6)
        if rnd(5) != 3:                                                         # the first call, 4 in 5
            word = rnd(10)
            number = rnd(28)
            self.say3(SNAP_WORDS[word - 1] + self.str_(number))
            self.rady(0x44076b)
            if rnd(5) != 3:                                                     # the second call, 4 in 5
                word2 = rnd(8)
                number2 = rnd(28)
                if word == word2:
                    number2 = number
                self.say3(SNAP_WORDS[word2 - 1] + self.str_(number2))
        for _ in range(rnd.below(4)):                                           # 0 to 3 more huts
            self.rady(0x440b16)
            self.say3(P.HUT + ("!" if rnd(2) == 1 else ""))
        self.rady(0x440cb2)
        g.voice_speak(P.HIKE, wait=False)                                       # `Voice.Speak " Hike! ", 1`
        snd.play_hike()
        snd.c2dh()

    def snap_draws(self) -> None:
        """L_440e54: the replay list is emptied (F2 replays from here), the ball carrier and two different defenders."""
        g, s, rnd = self.g, self.s, self.rnd
        s.yards = 0
        g.empty_replay()
        s.carrier = rnd(6)
        s.defender1 = rnd(17)
        s.defender2 = rnd.redraw(lambda: rnd(17), lambda d: d != s.defender1,
                                 lambda: 2 if s.defender1 == 1 else 1, "second defender")
        s.text = ""
        s.tackle_sentence = " tackle string "
        s.tackle_sound = 0

    def snap_phrase(self):
        """0x44121c: "<quarterback> takes the snap" (13 phrases, never one of the last six), then the play."""
        g, s = self.g, self.s
        s.text = self.qb(s.wisoff)
        number = s.snap_history.draw(self.rnd, len(P.SNAP_PHRASES), "snap phrase")
        if s.two_point:
            g.ptf = 1
        s.text += P.SNAP_PHRASES[number - 1]
        g.say4(s.text)
        self.rady(0x441b18)
        s.play_kind = 1
        pair = (s.offense_play, s.defense_play)
        if s.offense_play <= 2:
            return self.run_play(self.rules.modifiers.run(*pair, RUNS[pair]))
        if s.offense_play >= QB_SNEAK:                     # a quarterback run (N. F. L. rules mode only, SX.5)
            return self.qb_run_play()
        return self.pass_play(self.rules.modifiers.pass_(*pair, PASSES[pair]))

    # ----- runs (5.9) -----

    def handoff_sentence(self) -> None:
        """GoSub 0x451b58: the hand-off sentence (say4); its memory is the snap sentence in L4f4 (Q34)."""
        g, s = self.g, self.s
        sentence_now = s.text
        number = s.handoff.draw(self.rnd, lambda group: sentence_now)
        uses_he_she, phrase = P.HANDOFF_PHRASES[number - 1]
        s.text = (s.he_she[s.wisoff] + phrase if uses_he_she else phrase) + " " + self.back(s.wisoff, s.carrier) + " "
        g.say4(s.text)

    def run_play(self, entry):
        s, rnd = self.s, self.rnd
        self.handoff_sentence()
        direction = ""
        if entry.direction == 3:
            direction = RUN_DIRECTIONS[rnd(3) - 1]                    # Int(Rnd * 3) + 1
        elif entry.direction == 4:
            direction = RUN_DIRECTIONS[rnd.below(4) + 4 - 1]          # Int(Rnd * 4) + 4
        rb = self.back(s.wisoff, s.carrier)
        d1 = self.defender(s.defense, s.defender1)
        d2 = self.defender(s.defense, s.defender2)
        run, tackle = self.run_sentences(entry.key, rb, d1, d2, direction)
        if run is not None:
            s.text = run
            self.g.say2(run)
        s.tackle_sentence = tackle
        s.tackle_sound = entry.sound
        s.result_kind = O.RUN
        return self.fumble_or_yards(entry.low, entry.high)

    @staticmethod
    def run_sentences(key: str, rb: str, d1: str, d2: str, direction: str) -> tuple[str | None, str]:
        """The run sentence (say2; None for End Run against Short Run) and the tackle sentence of a run entry, joined as
        the lifted lines join them (0x446e29 to 0x4494be)."""
        if key == "plunge_goal_line":
            return rb + P.RUNS_STRAIGHT, P.PILE_UP
        if key == "plunge_short_run":
            return rb + P.RUNS_OFF_TACKLE, P.BROUGHT_DOWN + P.BY + d1 + " "
        if key == "plunge_long_run":
            return rb + P.RUNS_THROUGH_A_HOLE + direction, P.TACKLED_BY + d1 + " "
        if key == "plunge_blitz":
            return rb + P.AVOIDS_THE_BLITZ + d2, P.CAUGHT_BY + d1 + " "
        if key == "plunge_short_pass":
            return (rb + P.FINDS_A_HOLE + direction + P.SECOND_AIRY,
                    P.BEFORE + d1 + P.AND + d2 + P.CAN_CATCH_HIM)
        if key == "plunge_long_pass":
            return (rb + P.RUNS_THROUGH_A_HOLE + direction + P.RUNS_UP_FIELD,
                    P.BEFORE + d1 + P.AND + d2 + P.TACKLE_HIM)
        if key == "end_goal_line":
            return rb + P.TRIES_TO_RUN + direction + " ", " " + d1 + P.TACKLES_HIM
        if key == "end_short_run":
            return None, " " + rb + P.IS_TACKLED_BY + d1 + P.BEFORE_HE_CAN_GET + direction
        if key == "end_long_run":
            return rb + P.RUNS + direction, " " + d1 + P.TACKLES_HIM_AT_THAT_POINT
        if key == "end_blitz":
            return " " + rb + P.RUNS + direction + P.PAST + d2, " " + d1 + P.CHASES_AND_BRINGS_HIM_DOWN
        if key == "end_short_pass":
            return " " + rb + P.FINDS_HIS_WAY + direction, P.BEFORE + d1 + P.TRIPS_HIM_UP
        if key == "end_long_pass":
            return " " + rb + P.GETS + direction + P.HEADS_UP_FIELD, " " + d1 + P.AND + d2 + P.CHASE_HIM_DOWN
        raise ValueError("no run entry %r" % (key,))

    # ----- passes (5.9) -----

    def dropback_sentence(self) -> None:
        """GoSub 0x4528c8: the drop-back sentence, built into L4f4 (spoken only when the pass is not a sack)."""
        s = self.s
        number = s.dropback.draw(self.rnd, lambda group: group)
        s.text = s.he_she[s.wisoff] + P.DROPBACK_PHRASES[number - 1]

    def pass_play(self, entry):
        """L_44a1b3, entered after the drop-back sentence of the entry was built."""
        g, s, rnd = self.g, self.s, self.rnd
        self.dropback_sentence()
        s.play_kind = 2
        stats = s.stats[s.wisoff]
        stats.interception_count += 3
        stats.pass_attempts += 1
        if single(rnd.random() * 100) <= entry.sack:          # L4d0: a Single (FSTP float, 0x44a399)
            away = self.rules.instead_of_sack(s)               # N. F. L. rules (SX.5 scramble, SX.3 grounding); Classic: None
            if away == SCRAMBLE:
                return self.scramble()
            if away is not None:
                return self.thrown_away(away)
            return self.sack()
        complete_roll = single(rnd.random() * 100)            # L138, drawn before the throw sentence (0x44b367)
        if complete_roll >= entry.complete and self.rules.instead_of_incompletion(s):   # N. F. L. rules (SX.5); Classic: no
            return self.scramble()                                                     # draw, False
        g.say4(s.text)
        s.text = " " + self.qb(s.wisoff)
        number = s.throw_history.draw(rnd, len(P.THROW_PHRASES), "throw phrase")
        s.text += P.THROW_PHRASES[number - 1]
        g.say4(s.text)
        s.tackle_sentence = P.AND
        odds = max(INTERCEPTION_FLOOR, entry.complete - stats.interception_count)
        if rnd.below_single(odds) + 1 == INTERCEPTION_NUMBER:    # Int(Rnd * L2fc) + 1, VarMul: a Single
            return self.interception()
        if complete_roll >= entry.complete:
            return self.incomplete()
        return self.complete(entry)

    def sack(self):
        s = self.s
        s.stats[s.wisoff].sacked += 1
        number = s.sack_history.draw(self.rnd, SACK_PHRASES, "sack phrase")
        qb = self.qb(s.wisoff)
        d1 = self.defender(s.defense, s.defender1)
        texts = {1: " " + d1 + P.SACKS + qb + " ", 2: " " + qb + P.IS_SACKED_BY + d1 + " ",
                 3: " " + d1 + P.SLAMS + qb + P.TO_THE_GROUND, 4: " " + qb + P.IS_SLAMMED_BY + d1 + " ",
                 5: " " + qb + P.IS_CHASED_DOWN_BY + d1 + " "}
        if number == 6:
            s.tackle_sentence = " " + d1 + P.AND + self.defender(s.defense, s.defender2) + P.SMOTHER + qb + " "
        else:
            s.tackle_sentence = texts[number]
        s.tackle_sound = 2 if number == 6 else 3
        s.result_kind = O.SACK
        return self.fumble_or_yards(SACK.low, SACK.high)

    def thrown_away(self, sentence: str):
        """N. F. L. rules (SX.3; never in Classic): in place of the sack the passer throws the ball away (intentional
        grounding, design 9.2 P15): the drop-back sentence as for a pass, then the play ends as an incomplete pass with
        `sentence` as its tackle sentence and the whistle; the extras announce the foul at the narration end point."""
        g, s = self.g, self.s
        g.say4(s.text)
        s.tackle_sentence = sentence
        s.tackle_sound = 8
        s.yards = 0
        s.result_kind = O.PASS_INCOMPLETE
        return self.end_of_play

    def interception(self):
        g, s, snd = self.g, self.s, self.snd
        s.text = P.AND + self.defender(s.defense, s.defender1)
        word = self.rnd(2)
        s.stats[s.wisoff].intercepted += 1
        s.text += P.INTERCEPTS if word == 1 else P.PICKS_OFF
        snd.play(12, -1000)
        g.say4(s.text)
        snd.c2df()
        snd.play_tackle(3)
        s.text = P.THE_BALL_IS_NOW
        s.stats[s.wisoff].interception_count = 0
        s.interception_flag = True
        return self.end_point(O.INTERCEPTION, turnover=True) or self.turnover_spot

    def incomplete(self):
        s = self.s
        number = s.incomplete_history.draw(self.rnd, 9, "incompletion")
        rec = self.receiver(s.wisoff, s.carrier)
        texts = {1: " " + rec + P.DROPS_THE_BALL, 2: " " + rec + P.OUT_OF_BOUNDS, 3: P.OVER_THE_HEAD_OF + rec + " ",
                 4: P.FALLS_SHORT_OF + rec + " ", 5: P.BATTED_DOWN_BY + self.defender(s.defense, s.defender1) + " ",
                 # Q56 (kept): the defender of the side ON OFFENSE, Me.m370(wisoff, L578) (0x44cc09)
                 6: " " + self.defender(s.wisoff, s.defender1) + P.BATS_IT_BACK_AT + self.qb(s.wisoff) + " ",
                 7: P.THROUGH_THE_HANDS_OF + rec + " ", 8: P.OFF_THE_CHEST_OF + rec + " ",
                 9: P.OFF_THE_BACK_OF + rec + " "}
        s.tackle_sentence = texts[number]
        s.tackle_sound = 8
        # L128 = Int(Rnd * L1d4) + L1d4: L1d4 is an Integer, a Single or (a menu digit, Val) a Double Variant, so the
        # original rounds the product only sometimes; a pause of 1/9 s more or less on a set below 1e-5: kept in Double
        steps = self.rnd.below(s.offense_play) + s.offense_play
        self.dy(steps / 9, 0x44d024)
        s.yards = 0
        s.result_kind = O.PASS_INCOMPLETE
        return self.end_of_play

    def complete(self, entry):
        s = self.s
        s.stats[s.wisoff].completions += 1
        s.tackle_sound = self.rnd(2) + 1                                     # Int(Rnd * 2) + 2: foot5 or foot6
        number = s.catch_history.draw(self.rnd, len(P.CATCH_PHRASES), "catch phrase")
        s.tackle_sentence += self.receiver(s.wisoff, s.carrier) + P.CATCH_PHRASES[number - 1]
        s.result_kind = O.PASS_COMPLETE
        return self.fumble_or_yards(entry.low, entry.high)

    # ----- the fumble test and the yards (L_44d917) -----

    def fumble_or_yards(self, low: int, high: int):
        s, rnd = self.s, self.rnd
        if rnd(self.rules.modifiers.fumble_odds(s.wisoff)) == FUMBLE_NUMBER:
            return self.fumble()
        s.yards = rnd.below_single(high - low) + low                        # Int(Rnd * (L548 - L44)) + L44, VarMul
        stats = s.stats[s.wisoff]
        if s.play_kind == 1:
            stats.running_plays += 1                                        # not for a fumbled run (Q60)
            stats.running_yards += s.yards
        if s.play_kind == 2:
            stats.passing_yards += s.yards
        return self.end_of_play

    def fumble(self):
        """L_44dd35: the sentence kept for the end of the play is never spoken (Q60)."""
        g, s, snd = self.g, self.s, self.snd
        s.fumble_flag = True
        s.stats[s.wisoff].fumbles_lost += 1
        g.say4(P.FUMBLE)
        snd.play_tackle(3)
        snd.c2df()
        s.text = P.THE_BALL_IS_NOW
        return self.end_point(O.FUMBLE, turnover=True) or self.turnover_spot
