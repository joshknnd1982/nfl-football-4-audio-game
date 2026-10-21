"""pag, the plays of the catalog in the N. F. L. rules mode (nfl4 only, CLAUDE.md rule 0.13; NFL_PLAYS_DESIGN 7, built in SX.10c).
This is inspired by Jim Kitchen.

Never taken in Classic: `rules.model_play` answers None there without a draw, and the original's tables play. When the player called a
play of the catalog, the outcome model (extras/plays/model.py) gives its result right after the snap sentence and these steps tell it
with the original's sentence pools, so the pace and the sounds stay the original's (NX-P7):

    a run        the hand-off sentence (its pool and memory), the run and tackle sentences of the original's entry whose yard range
                 holds the result (the family of the gap against the defense's family first), the tackle sound, the yards
    a pass       the drop-back sentence, the throw sentence, then the original's catch, incompletion, interception or sack sentences;
                 the scramble (SX.5) and intentional grounding (SX.3) take a sack's or an incompletion's place where they did before
    the quarterback's run   the pool QB sentences of SX.5 (rules.qb_narrate) and the slide
    new results  a kneel, a spike, a throw-away, a pitch, a keep, laterals and a fumble the offense keeps: short sentences that are text
                 rows of the extras (rules.play_text), never typed here
Every draw these steps make is one of the original's sentence draws in the original's order; the yards, the catch and the turnover are
the model's. The end of the play is the original's (end_of_play and what follows it).
"""
from __future__ import annotations

from . import outcome as O
from . import phrases as P
from .playtables import RUNS
from .rules import SCRAMBLE
from .setup import RUN_DIRECTIONS

END_GAPS = ("end", "laterals")


def run_entry(family: int, defense: int, yards: int):
    """The original's run entry (playtables.RUNS) whose sentences tell a run of `yards`: the entry of the defense's family when its
    range holds the yards, else the first of the six whose range holds them, else the nearest range. No draw."""
    rows = [RUNS[(family, d)] for d in range(1, 7)]
    own = RUNS[(family, defense)] if (family, defense) in RUNS else rows[0]
    if own.low <= yards < own.high:
        return own
    for row in rows:
        if row.low <= yards < row.high:
            return row

    def distance(row):
        return row.low - yards if yards < row.low else yards - row.high + 1
    return min(rows, key=distance)


class CatalogSteps:

    def catalog_play(self, result):
        """After the snap sentence: the model's result, told."""
        if result.kind == "kneel":
            return self.catalog_kneel(result)
        if result.kind == "spike":
            return self.catalog_spike(result)
        if result.gap == "qb":
            return self.catalog_qb_run(result)
        if result.gap:
            return self.catalog_run(result)
        return self.catalog_pass(result)

    # ----- the clock plays -----

    def catalog_kneel(self, result):
        """The quarterback takes a knee: a run of the model's yards (one lost), the whistle, the running statistics."""
        s = self.s
        s.play_kind = 1
        s.tackle_sentence = self.rules.play_text("kneel", quarterback=self.qb(s.wisoff))
        s.tackle_sound = 8
        s.result_kind = O.RUN
        return self.catalog_yards(result)

    def catalog_spike(self, result):
        """The quarterback spikes the ball: an incomplete pass that stops the clock (RB26 8-2-1 Item 3)."""
        s = self.s
        s.play_kind = 2
        s.stats[s.wisoff].pass_attempts += 1
        s.tackle_sentence = self.rules.play_text("spike", quarterback=self.qb(s.wisoff))
        s.tackle_sound = 8
        s.yards = 0
        s.result_kind = O.PASS_INCOMPLETE
        return self.end_of_play

    # ----- runs -----

    def catalog_run(self, result):
        g, s = self.g, self.s
        s.play_kind = 1
        rb = self.back(s.wisoff, s.carrier)
        if result.branch == "pitch":
            s.text = self.rules.play_text("pitch", quarterback=self.qb(s.wisoff), player=rb)
            g.say4(s.text)
        elif result.gap == "laterals":
            s.text = self.rules.play_text("laterals")
            g.say4(s.text)
        else:
            self.handoff_sentence()
        family = 2 if result.gap in END_GAPS else 1
        entry = run_entry(family, s.defense_play, result.yards)
        direction = ""
        if entry.direction == 3:
            direction = RUN_DIRECTIONS[self.rnd(3) - 1]                    # the original's draws of the entry's direction
        elif entry.direction == 4:
            direction = RUN_DIRECTIONS[self.rnd.below(4) + 4 - 1]
        d1 = self.defender(s.defense, s.defender1)
        d2 = self.defender(s.defense, s.defender2)
        run, tackle = self.run_sentences(entry.key, rb, d1, d2, direction)
        if run is not None:
            s.text = run
            g.say2(run)
        s.tackle_sentence = tackle
        s.tackle_sound = entry.sound
        s.result_kind = O.RUN
        if result.kind == "fumble":
            return self.catalog_fumble(result)
        return self.catalog_yards(result)

    def catalog_qb_run(self, result):
        """A sneak, a keeper, a draw or an option's keep: SX.5's sentences (the pool QB, the direction) and the slide."""
        g, s = self.g, self.s
        s.play_kind = 1
        if result.branch == "keep":
            g.say4(self.rules.play_text("keep", quarterback=self.qb(s.wisoff)))
        entry = self.rules.qb_entry(s)             # the sound and the direction of the run (the yards are the model's)
        s.qb_run = entry.key
        d1 = self.defender(s.defense, s.defender1)
        d2 = self.defender(s.defense, s.defender2)
        run, tackle = self.rules.qb_narrate(s, entry, d1, d2)
        s.text = run
        g.say2(run)
        s.tackle_sentence = tackle
        s.tackle_sound = entry.sound
        s.result_kind = O.RUN
        if result.kind == "fumble":
            return self.catalog_fumble(result)
        s.yards = result.yards
        if s.qb_run != "sneak":                    # a gain of 8 or more that did not score may end in a slide; a sneak never slides
            self.rules.qb_slide(s)                 # (SX.5 design 7.3; the original's sneak never gains 8, the model's can, SX.10e)
        stats = s.stats[s.wisoff]
        stats.running_plays += 1
        stats.running_yards += s.yards
        return self.end_of_play

    # ----- passes -----

    def catalog_pass(self, result):
        g, s, rnd = self.g, self.s, self.rnd
        self.dropback_sentence()
        s.play_kind = 2
        stats = s.stats[s.wisoff]
        stats.interception_count += 3              # as the original's pass (a scramble takes both back)
        stats.pass_attempts += 1
        sacked = result.kind == "sack" or (result.kind == "fumble" and result.band < 0)
        if sacked:
            away = self.rules.instead_of_sack(s)   # SX.5's scramble and SX.3's grounding stay where they were
            if away == SCRAMBLE:
                return self.scramble()
            if away is not None:
                return self.thrown_away(away)
            self.sack_sentence()
            if result.kind == "fumble":
                return self.catalog_fumble(result)
            return self.catalog_yards(result)
        if result.kind == "incomplete" and result.branch == "thrown_away":
            return self.thrown_away(self.rules.play_text("throw_away", quarterback=self.qb(s.wisoff)))
        if result.kind == "incomplete" and self.rules.instead_of_incompletion(s):
            return self.scramble()
        g.say4(s.text)                             # the drop-back sentence
        s.text = " " + self.qb(s.wisoff)
        number = s.throw_history.draw(rnd, len(P.THROW_PHRASES), "throw phrase")
        s.text += P.THROW_PHRASES[number - 1]
        g.say4(s.text)
        s.tackle_sentence = P.AND
        if result.kind == "interception":
            return self.interception()
        if result.kind == "incomplete":
            return self.incomplete()
        stats.completions += 1
        s.tackle_sound = self.rnd(2) + 1                                     # foot5 or foot6, as the original's catch
        number = s.catch_history.draw(rnd, len(P.CATCH_PHRASES), "catch phrase")
        s.tackle_sentence += self.receiver(s.wisoff, s.carrier) + P.CATCH_PHRASES[number - 1]
        s.result_kind = O.PASS_COMPLETE
        if result.kind == "fumble":
            return self.catalog_fumble(result)
        return self.catalog_yards(result)

    # ----- the yards and the fumbles -----

    def catalog_yards(self, result):
        s = self.s
        s.yards = result.yards
        stats = s.stats[s.wisoff]
        if s.play_kind == 1:                       # as the original's fumble_or_yards: a sack's loss counts in the passing yards
            stats.running_plays += 1
            stats.running_yards += s.yards
        if s.play_kind == 2:
            stats.passing_yards += s.yards
        return self.end_of_play

    def catalog_fumble(self, result):
        """A fumble: lost, the original's fumble (its sentence, sounds and end point; the spot is the model's, turnover_spot); kept by the
        offense (G26-9), the play ends at the spot with " there is a fumble on the play " and who fell on it."""
        s = self.s
        if result.fumble_lost:
            s.yards = 0                            # as the original's fumble: the record carries no gain; the spot is the extras'
            return self.fumble()
        s.tackle_sentence += P.FUMBLE + self.rules.play_text("recovered", team=s.teams[s.wisoff])
        s.tackle_sound = 3
        return self.catalog_yards(result)
