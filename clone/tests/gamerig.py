"""Test rig for the game logic: virtual clock, scripted keys, fake speech with speakers. This is inspired by Jim Kitchen.

fixesforgames B-X1 (built in the first logic session, nfl4 S7.1): nothing really waits. The clock is virtual, the
fake engines (speech/fake.py) "speak" on it, and the keys are typed when the game waits for one, so whole flows run in
milliseconds and every pause and wait can be measured exactly. S7.3 to S7.5 extend it (sounds, files, random numbers).
"""
from nfl4.game.flow import Game
from nfl4.game.keys import MODIFIER_KEYS, GameQuit, KeyInput
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager


class Clock:
    """Virtual time: sleeping advances it, nothing really waits."""

    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def key_of(char: str) -> int:
    """The key code that types a character on the main keyboard (letters, digits, space)."""
    if char.isalpha():
        return ord(char.upper())
    if char.isdigit():
        return ord(char)
    if char == " ":
        return 32
    raise ValueError(f"no key types {char!r} in the rig")


class ScriptedKeys(KeyInput):
    """Keys on a virtual clock. `answers` are typed when the game waits for a key, one per wait:
    an int is a key code; a one-character str is the key that types it followed by its character (as the window
    hands them over); ("wait", seconds) lets virtual time pass first."""

    def __init__(self, clock, answers=()):
        super().__init__(clock=clock, sleep=clock.sleep)
        self.answers = list(answers)
        self.waits = 0
        self.read = []

    def type_next(self) -> bool:
        """Type the next answer (after any waits in front of it). False when there is none."""
        while self.answers:
            answer = self.answers.pop(0)
            if isinstance(answer, tuple):
                self._sleep(answer[1])
                continue
            if isinstance(answer, str):
                self.post(key_of(answer))
                self.post_char(answer)
            else:
                self.post(answer)
            return True
        return False

    def getkey(self, speech):
        self.clk()
        self.waits += 1
        if self.code_text == "":
            self.type_next()
        for _ in range(200000):
            if self.code_text != "":
                break
            self._sleep(0.001)
            self.pump()
        else:
            raise AssertionError("the game waits for a key that the test never presses")
        speech.stop()

    def read_key(self):
        """Menus of the added functions: an answer is typed when the menu waits."""
        while True:
            if self.quit.is_set():
                raise GameQuit()
            if self._posted.empty():
                if not self.type_next():
                    raise AssertionError("the menu waits for a key that the test never presses")
                continue
            code = super().read_key()
            if code in MODIFIER_KEYS:
                continue
            self.read.append(code)
            return code


class Rig:
    """The game on a virtual clock with a SAPI-like fake (it takes speakers) and an NVDA fake."""

    def __init__(self, answers=(), speech_per_char=0.0, mode="sapi", nvda_running=False, notice_sources=()):
        self.clock = Clock()
        self.sapi = FakeBackend("SAPI 5", takes_roles=True, seconds_per_char=speech_per_char,
                                clock=self.clock, sleep=self.clock.sleep)
        self.nvda = FakeBackend("NVDA", available=nvda_running, seconds_per_char=speech_per_char,
                                clock=self.clock, sleep=self.clock.sleep)
        self.speech = SpeechManager(self.sapi, self.nvda, mode)
        self.keys = ScriptedKeys(self.clock, answers)
        self.game = Game(self.speech, self.keys, clock=self.clock, sleep=self.clock.sleep,
                         notice_sources=notice_sources)

    def run(self):
        self.game.run()
        return self

    @property
    def said(self):
        """(text, speaker, rate step) of everything SAPI was given."""
        return self.sapi.said
