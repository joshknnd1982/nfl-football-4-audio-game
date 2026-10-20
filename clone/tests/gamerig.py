"""Test rig for the game logic: virtual clock, scripted keys, fake speech with speakers. This is inspired by Jim Kitchen.

fixesforgames B-X1 (built in the first logic session, nfl4 S7.1): nothing really waits. The clock is virtual, the
fake engines (speech/fake.py) "speak" on it, and the keys are typed when the game waits for one, so whole flows run in
milliseconds and every pause and wait can be measured exactly. S7.2 added the sounds: the real audio layer with the
shipped wavs on a silent TimedOutput that keeps time on the same clock, and a slot log of every play, level change and
stop (GAP_REGISTER G-A1). S7.3 to S7.5 extend it (files, random numbers).
"""
from nfl4.audio.engine import Audio
from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import TimedOutput
from nfl4.data.settings import AudioSettings
from nfl4.game.flow import Game
from nfl4.game.keys import MODIFIER_KEYS, GameQuit, KeyInput
from nfl4.game.rnd import GameRandom
from nfl4.game.sounds import GameSounds
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
        self.speech_waits = 0
        self.read = []
        # S8.2: the F1 help hint is a clone addition of the key layer (CLAUDE.md 0.17). The rigs leave it OFF so that the many tests that
        # pin the original's exact speech after F1 (and the golden Classic transcript) keep doing so; the tests of the hint switch it on
        # (`rig.keys.hint_enabled = True`): test_s82_help_and_names.py, the main menu's F1 and F11's F1.
        self.hint_enabled = False

    def _say_f1_hint(self):
        if not self.hint_enabled:
            self._f1_at = None
            return
        super()._say_f1_hint()

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
        self._say_f1_hint()
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

    def wait_speech(self, speech):
        """F5, F6, F7's wait while the voice speaks (S7.4a). Nothing is typed unless the next answer is
        ("cut", seconds, key): then `key` is typed `seconds` of virtual time into the wait (an answer as above).
        ("end",) says that this wait runs to the end of the speech, so the next "cut" belongs to a later wait."""
        self.speech_waits += 1
        cut = None
        if self.answers and isinstance(self.answers[0], tuple) and self.answers[0][0] == "cut":
            _, after, key = self.answers.pop(0)
            cut = (self._clock() + after, key)
        elif self.answers and self.answers[0] == ("end",):
            self.answers.pop(0)
        while True:
            self.pump()
            if self.code_text != "" or not speech.is_speaking():
                if cut is not None:
                    raise AssertionError("the speech ended before the test's key was typed")
                return
            if cut is not None and self._clock() >= cut[0]:
                self.answers.insert(0, cut[1])
                cut = None
                self.type_next()
                continue
            self._sleep(0.001)

    def wait_key(self):
        """pag's bare DoEvents loop at the final score: the next answer is typed when it waits."""
        self.waits += 1
        self._say_f1_hint()
        self.pump()
        if self.code_text == "":
            self.type_next()
        for _ in range(200000):
            if self.code_text != "":
                return
            self._sleep(0.001)
            self.pump()
        raise AssertionError("the game waits for a key that the test never presses")

    def getkey2(self, speech, ambient):
        """The game's key wait with ambient sounds: a ("wait", s) answer lets virtual time pass in 1 ms steps, with
        DoEvents and PlayRan on every step as the original's loop does, before the next key is typed."""
        ambient.start_ambient_wait()
        self.clk()
        self._say_f1_hint()
        self.waits += 1
        wait_left = 0.0
        for _ in range(20_000_000):
            self.pump()
            ambient.play_ran()
            if self.code_text != "":
                break
            if wait_left > 1e-9:
                step = min(0.001, wait_left)
                self._sleep(step)
                wait_left -= step
            elif self.answers and isinstance(self.answers[0], tuple):
                wait_left = self.answers.pop(0)[1]
            elif not self.type_next():
                raise AssertionError("the game waits for a key that the test never presses")
        speech.stop()

    def read_key(self):
        """Menus of the added functions: an answer is typed when the menu waits."""
        while True:
            if self.quit.is_set():
                raise GameQuit()
            while self._posted.take_text(0.0):
                pass                                       # the character a key typed that no menu asked for (S7.4b)
            if self._posted.empty():
                if not self.type_next():
                    raise AssertionError("the menu waits for a key that the test never presses")
                continue
            code = super().read_key()
            if code in MODIFIER_KEYS:
                continue
            self.read.append(code)
            return code


class Beeper:
    """The exit beep's system sound, counted instead of heard."""

    def __init__(self):
        self.calls = 0

    def beep(self):
        self.calls += 1
        return True


class Rig:
    """The game on a virtual clock with a SAPI-like fake (it takes speakers) and an NVDA fake.

    sounds_dir: the player's sounds folder (a tmp_path); with it the rig also has the audio layer (`audio`, `sounds`,
    `slot_log`, `output`), on the shipped wavs unless shipped_dir names another folder. rng: the source of the game's ONE
    random function (`rig.rnd`, game/rnd.py; anything with random(): a seeded random.Random, a scripted source), shared by
    the game's draws and the sounds' draws as in the program (G-D2)."""

    def __init__(self, answers=(), speech_per_char=0.0, mode="sapi", nvda_running=False, notice_sources=(),
                 sounds_dir=None, shipped_dir=None, rng=None, sound_level=0):
        self.clock = Clock()
        self.sapi = FakeBackend("SAPI 5", takes_roles=True, seconds_per_char=speech_per_char,
                                clock=self.clock, sleep=self.clock.sleep)
        self.nvda = FakeBackend("NVDA", available=nvda_running, seconds_per_char=speech_per_char,
                                clock=self.clock, sleep=self.clock.sleep)
        self.speech = SpeechManager(self.sapi, self.nvda, mode)
        self.keys = ScriptedKeys(self.clock, answers)
        self.rnd = GameRandom(rng)
        self.audio = self.sounds = self.output = None
        self.slot_log = []
        if sounds_dir is not None:
            self.audio_settings = AudioSettings(sound_level=sound_level)
            self.output = TimedOutput(self.clock)
            self.beeper = Beeper()
            library = SoundLibrary(shipped_dir or shipped_sounds_dir(), str(sounds_dir))
            self.audio = Audio(library, self.audio_settings, output=self.output, beeper=self.beeper,
                               clock=self.clock, slot_log=self.slot_log)
            self.sounds = GameSounds(self.audio, self.keys, self.audio_settings, rng=self.rnd, clock=self.clock,
                                     sleep=self.clock.sleep)
        self.game = Game(self.speech, self.keys, clock=self.clock, sleep=self.clock.sleep,
                         notice_sources=notice_sources, sounds=self.sounds, rnd=self.rnd)
        # nfl4 (SX.9, NQ2): a new player's settings say the N. F. L. rules; the rig's Game plays Classic (its rules are CLASSIC unless a test
        # hands others), the baseline every conformance test is written for, so its settings say Classic too. A test of the N. F. L. rules
        # sets them (frrig, nflrig, rules_from_settings); tests/test_sx9_switches.py checks the program's own default
        self.game.options.settings.game.rules = "classic"

    def run(self):
        self.game.run()
        return self

    @property
    def said(self):
        """(text, speaker, rate step) of everything SAPI was given."""
        return self.sapi.said
