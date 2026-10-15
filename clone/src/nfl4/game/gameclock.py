"""The made-up game clock (F4 and the quarter starts). This is inspired by Jim Kitchen.

GAME_SPEC 5.3 (CODE (lifted) `sgc` p_42bfc0; constants checked in the assembly, the arithmetic types TESTED in S7.3a).
The original has no real clock: the time left in a quarter is made up from the play counter. Arguments: played = plays
played in the quarter (the counter), total = plays in this quarter (30 to 37), quarter = 1 to 4 (5 to 10 = overtime).

    if played <> oldtime:                      oldtime starts Empty, which equals 0
        oldtime = played;  left = total - played
        pct = Int(left * 100 / total);  spread = 30;  low = 15
        if quarter = 2 or quarter > 3:
            W = M2W (quarter 2), M4W (quarter 4) or M5W (quarter above 4)           5 to 7 each, drawn at a game's start
            if left < 5 + W:  CountDown = CountDown + W;  spread = 18;  low = 9
            if left <= W:     CountDown = 125 (W = 5), 170 (W = 6) or 215 (W = 7);  spread = 10;  low = 5
        m = pct * 15 / CountDown;  mins = Int(m);  secs = Int((Int(m * 100) - mins * 100) * 60 / 100)
        draw j = Int(Rnd * spread) - low until 0 <= secs + j <= 59;  secs = secs + j
    if quarter = 3 and played = 0:  mins = 15;  secs = 0
    text = " ";  if mins > 0: text = Str$(mins) & " minute" (& "s" if mins > 1)
    if secs > 0: text = text & " " & Str$(secs) & " second" (& "s" if secs > 1)
    say5(text & " remaining in the " & (first, second, third, fourth, over time) & " quarter. ")

TYPES (D-039, `work/vb_variant_ops_s73a.py`): the plays of a quarter are a Single Variant, so every operation of the
chain is a Single (`vbnum.single` rounds after each one); in a Double the exact decimal 4.35 * 100 would be
434.99999999999994 and give a different second in 57 of the 3,588 cases the game can produce.

CountDown is 100 at the start of every quarter (pag sets it, S7.3b) and is saved in football.sav; the same play counter
gives the same time again (oldtime), so F4 twice in one play repeats the minutes and seconds. M2W, M4W and M5W are drawn
by the game's set-up (game/setup.py). After the text the original calls clk and sets g = "112" (Game.sgc does).
"""
from __future__ import annotations

from .rnd import GameRandom
from .vbnum import int_of, single, str_

QUARTER_WORDS = {1: "first", 2: "second", 3: "third", 4: "fourth"}      # strings s41, 772, s29, 738
OVER_TIME_WORD = "over time"                                             # string 749
REMAINING_IN_THE = " remaining in the "                                  # string 675
QUARTER_END = " quarter. "                                                # string 705
MINUTE, SECOND, PLURAL = " minute", " second", "s"                        # strings 728, 732, s25
START_COUNTDOWN = 100
COUNTDOWN_AT_WARNING = {5: 125, 6: 170, 7: 215}


def quarter_word(quarter: int) -> str:
    """Lf4(quarter): "first" to "fourth", "over time" for 5 to 10. Any other number is a subscript error in VB6."""
    if quarter in QUARTER_WORDS:
        return QUARTER_WORDS[quarter]
    if 5 <= quarter <= 10:
        return OVER_TIME_WORD
    raise ValueError("no quarter %r" % (quarter,))


class QuarterClock:
    """The form variables oldtime, mins, secs, CountDown, M2W, M4W and M5W with the sgc computation."""

    def __init__(self):
        self.oldtime = 0                     # Empty, which compares equal to 0
        self.mins = 0                        # Empty until the first computation
        self.secs = 0
        self.countdown = START_COUNTDOWN
        self.warning = {2: 5, 4: 5, 5: 5}    # M2W, M4W, M5W (the game's set-up draws them, 5 to 7)

    @property
    def m2w(self) -> int:
        return self.warning[2]

    @property
    def m4w(self) -> int:
        return self.warning[4]

    @property
    def m5w(self) -> int:
        return self.warning[5]

    def set_warnings(self, m2w: int, m4w: int, m5w: int) -> None:
        self.warning = {2: m2w, 4: m4w, 5: m5w}

    def start_quarter(self) -> None:
        """pag's `CountDown = 100` at the start of every quarter."""
        self.countdown = START_COUNTDOWN

    def _warning_for(self, quarter: int) -> int:
        if quarter == 2:
            return self.warning[2]
        if quarter == 4:
            return self.warning[4]
        return self.warning[5]               # quarter above 4

    def advance(self, played: int, total: int, quarter: int, rnd: GameRandom) -> str:
        """sgc: update oldtime, mins, secs and CountDown for this play counter and return the sentence for say5."""
        word = quarter_word(quarter)         # a quarter outside 1 to 10 fails before any state changes, as Lf4(...) would
        if played != self.oldtime:
            self.oldtime = played
            left = single(total - played)
            pct = int_of(single(single(left * 100) / total))
            spread, low = 30, 15
            if quarter == 2 or quarter > 3:
                w = self._warning_for(quarter)
                if left < 5 + w:
                    self.countdown = single(self.countdown + w)
                    spread, low = 18, 9
                if left <= w:
                    if w in COUNTDOWN_AT_WARNING:
                        self.countdown = COUNTDOWN_AT_WARNING[w]
                    spread, low = 10, 5
            m = single(single(pct * 15) / self.countdown)
            self.mins = int_of(m)
            hundredths = int_of(single(m * 100))
            self.secs = int_of(single(single((hundredths - self.mins * 100) * 60) / 100))
            self.secs = rnd.redraw(lambda: self.secs + (rnd.below(spread) - low), lambda s: 0 <= s <= 59,
                                   lambda: self.secs, "clock seconds")
        if quarter == 3 and played == 0:
            self.mins, self.secs = 15, 0
        return clock_sentence(self.mins, self.secs, word)


def clock_sentence(mins: int, secs: int, word: str) -> str:
    """sgc's sentence for minutes and seconds (also the real clock's F4 in N. F. L. rules mode, SX.2): " " or Str$(mins)
    & " minute(s)", then " " & Str$(secs) & " second(s)" when there are seconds, " remaining in the <word> quarter. "."""
    text = " "
    if mins > 0:
        text = str_(mins) + MINUTE
        if mins > 1:
            text += PLURAL
    if secs > 0:
        text += " " + str_(secs) + SECOND
        if secs > 1:
            text += PLURAL
    return text + REMAINING_IN_THE + word + QUARTER_END
