"""pag, the quarterback's runs of the N. F. L. rules mode (nfl4 only, CLAUDE.md rule 0.13; NFL_EXTRAS_DESIGN 7, built in SX.5).
This is inspired by Jim Kitchen.

Never taken in Classic: the offense plays 8, 9 and 10 exist only in the N. F. L. rules menu, and the two seams in
pag_scrimmage.py (`instead_of_sack` answering SCRAMBLE, `instead_of_incompletion`) are answered None and False by the
Classic rules without a draw. A designed run (a sneak, keeper or draw) is spoken like the original's run of 5.9: the snap
sentence (pag_scrimmage.snap_phrase), then the start sentence, the run sentence, the tackle sound and sentence and the gain
sentence; the fumble test comes before the yards as in `fumble_or_yards`, the slide after them. A scramble replaces the
sack or the throw of a pass play: the drop-back sentence, " <quarterback> cannot find a receiver and takes off running ",
then the same. What is said and drawn is the Rules object's (qb_entry, qb_narrate, qb_slide): this file only runs the steps
of the engine, so it knows no text of the extras.

    qb_run_play()   offense play 8, 9 or 10 after the snap sentence
    scramble()      a pass play that became a run; the stats of the pass are taken back
    qb_yards(entry) the fumble test and the yards of the run (the original's order), the slide, the running statistics
"""
from __future__ import annotations

from . import outcome as O
from .playtables import FUMBLE_NUMBER


class KeeperSteps:

    def qb_run_play(self):
        """The designed run chosen from the menu (offense play 8 sneak, 9 keeper, 10 draw)."""
        s = self.s
        entry = self.rules.qb_entry(s)
        s.play_kind = 1
        s.qb_run = entry.key
        return self._qb_run(entry)

    def scramble(self):
        """The pass play became a run (design 7.1): the stats of the pass the quarterback did not throw are taken back, the
        drop-back sentence is spoken, then the run."""
        s = self.s
        stats = s.stats[s.wisoff]
        stats.pass_attempts -= 1                  # no pass was thrown (the original counted it before the sack test)
        stats.interception_count -= 3             # and the interception count did not grow
        self.g.say4(s.text)                       # the drop-back sentence, as a pass says it
        s.play_kind = 1
        entry = self.rules.qb_entry(s, scramble=True)
        s.qb_run = entry.key
        return self._qb_run(entry)

    def _qb_run(self, entry):
        s = self.s
        d1 = self.defender(s.defense, s.defender1)
        d2 = self.defender(s.defense, s.defender2)
        run, tackle = self.rules.qb_narrate(s, entry, d1, d2)     # the pool QB sentence is said here; the direction drawn
        s.text = run
        if entry.key == "scramble":
            self.g.say4(run)
        else:
            self.g.say2(run)
        s.tackle_sentence = tackle
        s.tackle_sound = entry.sound
        s.result_kind = O.RUN
        return self.qb_yards(entry)

    def qb_yards(self, entry):
        """The fumble test (1 in entry.fumble), the yards, the slide, the running statistics; the original's order."""
        s, rnd = self.s, self.rnd
        if rnd(entry.fumble) == FUMBLE_NUMBER:
            return self.fumble()
        s.yards = rnd.below(entry.high - entry.low) + entry.low
        self.rules.qb_slide(s)                    # a gain of 8 or more yards that did not score may end in a slide
        stats = s.stats[s.wisoff]
        stats.running_plays += 1                  # not for a fumbled run (Q60)
        stats.running_yards += s.yards
        return self.end_of_play
