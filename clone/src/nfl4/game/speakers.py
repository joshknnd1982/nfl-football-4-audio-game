"""The original's speakers say to say6, the replay list, the speech log and the pauses dy and rady. This is inspired by Jim Kitchen.

GAME_SPEC 9.1, 9.2 and 7 (CODE (lifted) say p_42a000, say2, say3, say4, say5, say6, inrep p_4863f0, rady p_42e980, dy
p_42e880; GAP_REGISTER G-S1, G-S2, G-S4). The original speaks through one SAPI voice object in three ways:

    speaker  voice and volume                                   waits  log  replay list
    say      the announcer, volume 1                            yes    yes  no
    say2     the announcer                                      no     yes  yes
    say3     the quarterback (qorp = 1) or punter of side wisoff yes   no   no
    say4     the announcer                                      yes    yes  yes
    say5     the announcer                                      no     yes  no
    say6     the voice that spoke last                          no     yes  no

"waits" = flags 0: returns when the whole queue is spoken, so it is also a barrier for everything queued before it;
"no" = flags 1: queued, return at once. The clone's speech layer has one first-in-first-out queue for all speakers (D-031
item 1): asynchronous = `speech.say_async`, synchronous = `speech.say` (queue, then wait for the empty queue), and
nothing is cut by a voice change. The voice cache LastVoice is not needed: every call names its speaker (role), each with
its own voice and volume (D-022 item 5); say6 takes the speaker of the last text.

The speech log: while ptf is 1 the speakers print their text to footballlog.txt (`Print #3`); say3 and inrep never do.
The clone hands each line to `log_sink` (S7.5, G-S10, writes the file; None = nothing is written). SayScore prints
unconditionally (`log_print`).

The replay list (Me.m44c with the counter ilc) holds the lines of say2 and say4 since it was last emptied (`ilc = 0`, done
by the play, season and play-off engines at the places GAME_SPEC 9.2 lists); inrep (F2) speaks " here's the instant rea play "
(waited, unless norep is not 0), pauses 0.2 s, then queues every line of the list and stops after the line that equals
" <coach> select your play ". The original's list has 501 places (a store at index 501 or more ends it with run-time error 9,
asm 0x42a6a3); the clone's list has no limit and records the longest it grew (`replay_longest`), which the S8.1 property test
checks stays far below 501 (D-039).

dy(s) waits exactly s seconds with the keys pumped (the kit's KeyInput.dy, a monotonic clock); rady waits
Int(Rnd * 30) / (max(vr, 1) * 25) seconds: 0 to 1.16 s at rate 1 or below, shorter as the player speeds the speech up
(vr is the saved speech rate setting, G-S4). Two rady calls in one 15 ms clock tick draw the same number in the original
(both reseed from Timer); the clone does not (inaudible, G-S2).
"""
from __future__ import annotations

from typing import Callable

from ..speech.roles import ANNOUNCER, REFEREE, player_role
from .keys import KeyInput
from .rnd import GameRandom

REPLAY_INTRO = " here's the instant rea play "      # string 2550
REPLAY_PAUSE = 0.2                                   # inrep's dy(0.2)
RADY_STEPS = 30                                      # Int(Rnd * 30)
RADY_UNIT = 25                                       # divided by vr * 25


class Speakers:
    def __init__(self, speech, keys: KeyInput, rnd: GameRandom | None = None):
        self.speech = speech
        self.keys = keys
        self.rnd = rnd if rnd is not None else GameRandom()
        self.ptf = 0                                           # 1 while the speech goes to footballlog.txt
        self.log_sink: Callable[[str], None] | None = None     # S7.5: appends one line to footballlog.txt
        self.replay: list[str] = []                            # Me.m44c(1 to ilc)
        self.replay_longest = 0
        self.norep = 0                                         # not 0: inrep leaves out its introduction
        self.wisoff = 1                                        # the side on offense: 1 = the player, 2 = the opponent
        self.qorp = 1                                          # 1: say3 speaks as a quarterback, else as a punter
        self.vr_source: Callable[[], int] = lambda: 0          # the speech rate counter vr (settings speech_rate)
        self.coach_source: Callable[[], str] = lambda: "coach"  # the coach's name for inrep's stop line
        # S7.3b: every pause with the address of its call in the lifted code (None = not recorded). The tests compare
        # the sites of a game with work/pause_table_s43.txt (GAME_SPEC 7 item 3).
        self.pause_log: list[tuple[int | None, float]] | None = None

    # ----- the log -----

    def log_print(self, text: str) -> None:
        """`Print #3, text` (an empty text is the empty line)."""
        if self.log_sink is not None:
            self.log_sink(text)

    def _logged(self, text: str) -> None:
        if self.ptf == 1:
            self.log_print(text)

    # ----- the speakers -----

    @property
    def ilc(self) -> int:
        """The replay list's counter."""
        return len(self.replay)

    def empty_replay(self) -> None:
        """`ilc = 0`: the list is empty again."""
        self.replay.clear()

    def _remember(self, text: str) -> None:
        self.replay.append(text)
        self.replay_longest = max(self.replay_longest, len(self.replay))

    def _speak(self, text: str, role: str, wait: bool, rate_step: int = 0) -> None:
        if text == "":
            return                                  # nothing to say (Speak "" is a no-op in flags 0 and 1)
        self.keys.service_timeout()                 # owner rule 0.22: a T key that came in during a long text is taken first
        if wait:
            self.speech.say(text, self.keys.quit, role=role, rate_step=rate_step)
            self.keys.service_timeout()             # and one that cut this text is taken before the next one is said
        else:
            self.speech.say_async(text, role=role, rate_step=rate_step)

    def say(self, text: str, rate_step: int = 0) -> None:
        """Announcer, waits for everything queued; logged. rate_step: banter line 113 is one step faster (Q38)."""
        self._logged(text)
        self._speak(text, ANNOUNCER, True, rate_step)

    def voice_speak(self, text: str, wait: bool) -> None:
        """The bare `Voice.Speak text, flags` of pag (" Hike! " asynchronous, the " " after the score synchronous): the
        voice that spoke last, neither logged nor kept for the replay."""
        self._speak(text, self.speech.last_role or ANNOUNCER, wait)

    def saykey(self) -> None:
        """The key echo (p_42e3d0): the speech is purged, then the key's character g2 is queued in the voice that spoke
        last, except for F1. Q58 (TESTED): heard at the normal rate, so the clone does not change it. A control
        character (Escape, Tab, Backspace) is not sent: SAPI has nothing to say for it, a screen reader would read its
        name (S7.3b; S8.2 listens). saykey p_42e3d0: Rate vr + 5 at 0x42e469 and back to vr at 0x42e580 (not heard, Q58,
        so not done), the purge 0x42e4ce, the character 0x42e531."""
        self.stopspeech()
        if self.keys.code_text == "112":
            return
        char = self.keys.char
        if char and ord(char[0]) >= 32:
            self._speak(char, self.speech.last_role or ANNOUNCER, False)

    def say2(self, text: str) -> None:
        """Announcer, asynchronous; logged, kept for the replay."""
        self._remember(text)
        self._logged(text)
        self._speak(text, ANNOUNCER, False)

    def say3(self, text: str) -> None:
        """The quarterback (qorp = 1) or the punter of the side on offense, waits; neither logged nor replayed."""
        self._speak(text, player_role(self.wisoff, punter=(self.qorp != 1)), True)

    def say4(self, text: str) -> None:
        """Announcer, waits; logged, kept for the replay."""
        self._remember(text)
        self._logged(text)
        self._speak(text, ANNOUNCER, True)

    def say5(self, text: str) -> None:
        """Announcer, asynchronous; logged, not kept for the replay (the menus and prompts)."""
        self._logged(text)
        self._speak(text, ANNOUNCER, False)

    def say_role(self, text: str, role: str) -> None:
        """A speaker of the extras (Ghip, SY.1), asynchronous; logged, not kept for the replay (the pools of the broadcast)."""
        self._logged(text)
        self._speak(text, role, False)

    def say_referee(self, text: str) -> None:
        """The referee over the microphone (SY.3): like say4, waits; logged, kept for the replay (F2 speaks it in the announcer's voice)."""
        self._remember(text)
        self._logged(text)
        self._speak(text, REFEREE, True)

    def say6(self, text: str, role: str | None = None) -> None:
        """The voice that spoke last, asynchronous; logged. role: the speaker whose voice the original had just loaded
        (F11's adjvol loads each voice before its say6; the clone names it, D-022 item 5)."""
        self._logged(text)
        self._speak(text, role or self.speech.last_role or ANNOUNCER, False)

    def stopspeech(self) -> None:
        """`Voice.Speak "", 2`: everything queued is dropped at once (stopspeech p_42e300, 0x42e371)."""
        self.speech.stop()

    def inrep(self) -> None:
        """F2, the instant replay (GAME_SPEC 9.2): the introduction (waited) unless norep is not 0, 0.2 s, then every line
        of the replay list queued, up to and including the line that equals " <coach> select your play "."""
        stop_line = " " + self.coach_source() + " select your play "
        if self.norep == 0:
            self._speak(REPLAY_INTRO, ANNOUNCER, True)
        self.dy(REPLAY_PAUSE, 0x4867c9)
        for line in list(self.replay):
            self._speak(line, ANNOUNCER, False)
            if line == stop_line:
                break

    # ----- the pauses -----

    @property
    def vr(self) -> int:
        return int(self.vr_source())

    def dy(self, seconds: float, site: int | None = None) -> None:
        """A fixed pause: keys are pumped but never end it. site: the address of the call (recorded when pause_log is
        set)."""
        if self.pause_log is not None:
            self.pause_log.append((site, seconds))
        self.keys.dy(seconds)

    def rady(self, site: int | None = None) -> None:
        """A pause of random length: Int(Rnd * 30) / (max(vr, 1) * 25) seconds, keys pumped."""
        steps = self.rnd.below(RADY_STEPS)
        seconds = steps / (max(self.vr, 1) * RADY_UNIT)
        if self.pause_log is not None:
            self.pause_log.append((site, seconds))
        self.keys.dy(seconds)
