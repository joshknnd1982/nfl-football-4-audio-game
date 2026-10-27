"""The excited voice: how much higher, faster and louder a play call is said at each level of excitement. This is inspired by Jim Kitchen.

XV (D-198, 2026-10-27; the owner asked for an enthusiastic radio announcer whose voice rises on the big plays, the speed and the volume
raised with the excitement, and "user should be able to turn it on or off"). The radio calls (extras/radio_calls.py) give every call a
level of excitement:
    1 routine        a short run, an incompletion, the huddle and the snap: the voice as it is
    2 gain           a first down, a catch, a gain of ten or more, a big down: a little higher
    3 big play       a gain of 20 or more, a long return, a field goal, the countdown of a long run: higher, faster, louder
    4 turnover       an interception, a fumble, a sack, a turnover on downs, a safety: higher and faster again
    5 touchdown      the touchdown: the most
The setting F9, Rules, Excited voice (nx_excited_voice) switches it off: every call is then said in the voice as it is.

What each engine can do (MEASURED on the owner's PC, work/xv_1027/sapi.txt and nvda.txt):
    * the game's own voices (SAPI 5): the rate in steps (one step makes a sentence about 13 % shorter, two about 23 %), the pitch in steps
      of SAPI's XML <pitch absmiddle> (one step raises it 2 % on Microsoft David, 9 % on DECtalk Paul, 14 % on an OpenEVV voice; FlexVoice
      and Lucent voices ignore it) and the volume (0 to 100, capped);
    * NVDA: SSML <prosody pitch="110%" rate="112%"> through the controller client's speakSsml (NVDA 2024.1 and newer); NVDA reads only
      percentages (speechXml.py, RE_PERCENTAGE). On the owner's NVDA with IBM ECI: pitch 110 % raised it about 20 %, rate 112 % made the
      sentence 25 % shorter, so NVDA's steps are small;
    * JAWS: SayString has no pitch or rate, so JAWS says the words and the exclamation marks only.
Capitals are NOT a way to raise the pitch: MEASURED on 14 voices, no voice said a word in capitals higher, and many spelled it or stretched
it ("GOT IT" is "got I T" on Microsoft Zira; BeSTspeech said "WOW" in four times the time). So a call is written and spoken in normal case.
"""
from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape

ROUTINE, GAIN, BIG_PLAY, TURNOVER, TOUCHDOWN = 1, 2, 3, 4, 5
LEVEL_NAMES = {0: "none", ROUTINE: "routine", GAIN: "gain", BIG_PLAY: "big play", TURNOVER: "turnover", TOUCHDOWN: "touchdown"}


@dataclass(frozen=True)
class Lift:
    rate: int            # SAPI 5 rate steps added to the player's rate
    pitch: int           # SAPI 5 pitch steps added to the player's pitch
    volume: int          # SAPI 5 volume points added to the speaker's volume (at most 100)
    nvda_pitch: int      # NVDA: prosody pitch in percent (100: unchanged)
    nvda_rate: int       # NVDA: prosody rate in percent


NONE = Lift(0, 0, 0, 100, 100)
LIFTS = {
    ROUTINE: NONE,
    GAIN: Lift(0, 1, 0, 103, 100),
    BIG_PLAY: Lift(1, 2, 5, 106, 106),
    TURNOVER: Lift(2, 2, 5, 108, 110),
    TOUCHDOWN: Lift(2, 3, 5, 110, 112),
}


def lift_of(level: int) -> Lift:
    """The amounts of a level; any other number (0, a level a later session has not defined) changes nothing."""
    return LIFTS.get(int(level or 0), NONE)


def nvda_ssml(text: str, level: int = 0) -> str:
    """The SSML that NVDA's speakSsml is given for one text: the text alone, or inside a prosody element at a lifted level."""
    lift = lift_of(level)
    if lift.nvda_pitch == 100 and lift.nvda_rate == 100:
        return f"<speak>{escape(text)}</speak>"
    return (f'<speak><prosody pitch="{lift.nvda_pitch}%" rate="{lift.nvda_rate}%">{escape(text)}</prosody></speak>')
