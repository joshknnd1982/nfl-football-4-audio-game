"""Five speakers on the SAPI 5 backend: one voice object per voice, one queue (nfl4 S7.1). This is inspired by Jim Kitchen.

GAP_REGISTER G-S1 and G-S6, D-031 items 1 and 3. The fakes behave like the measured real engine (fixesforgames B-X3):
every SpVoice made is its own object with its own voice, rate and volume (B-S21: five objects at once work); two objects
told to speak at once WOULD overlap on the sound device (nothing in SAPI queues them against each other), so the
shared fake device records every interval of sound and the tests require that none overlap; a memory stream holds its
audio only after WaitUntilDone said the voice is done (B-S2); a purge of a memory stream returns at once; a token's
Gender attribute raises when the token has none, as SpObjectToken.GetAttribute does.
"""
import threading
import time

import pytest

from nfl4.speech.roles import ANNOUNCER, OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER, OWN_QUARTERBACK
from nfl4.speech.sapi5 import SVSF_PURGE_BEFORE_SPEAK, RoleVoice, SapiBackend

SPEAK_SECONDS_PER_CHAR = 0.005   # a direct text sounds this long per character on the device
PLAY_SECONDS = 0.03              # a rendered block plays this long


class Device:
    """The sound device: every interval of sound, from the player and from voices speaking directly."""

    def __init__(self):
        self.lock = threading.Lock()
        self.sounds = []        # (who, text, start, end)

    def add(self, who, text, start, end):
        with self.lock:
            self.sounds.append([who, text, start, end])
            return self.sounds[-1]

    def overlaps(self):
        spans = sorted((s for s in self.sounds if s[3] > s[2]), key=lambda s: s[2])
        return [(a[1], b[1]) for a, b in zip(spans, spans[1:]) if b[2] < a[3] - 0.002]


class Token:
    def __init__(self, token_id, name, gender=None):
        self.Id = token_id
        self._name = name
        self._gender = gender

    def GetDescription(self):
        return self._name

    def GetAttribute(self, name):
        if name == "Gender" and self._gender is not None:
            return self._gender
        raise KeyError(name)       # SPERR_NOT_FOUND in the real engine


class Tokens:
    def __init__(self, tokens):
        self._tokens = tokens
        self.Count = len(tokens)

    def Item(self, i):
        return self._tokens[i]


TOKENS = [Token("HKEY\\Bill", "FlexVoice2 Bill", "Male"), Token("HKEY\\David", "Microsoft David", "Male"),
          Token("ENUM\\Zira", "Microsoft Zira", "Female"), Token("HKEY\\Fred", "BestSpeech Fred")]


class TokenObject:
    """SAPI.SpObjectToken: SetId works only for registry-style ids (enumerator voices are found by scanning)."""
    def SetId(self, token_id):
        for token in TOKENS:
            if token.Id.lower() == token_id.lower() and token_id.startswith("HKEY"):
                self.__dict__.update(token.__dict__)
                self.__class__ = Token
                return
        raise OSError("not a registry token")


class Stream:
    def __init__(self):
        self.data = b""

    def GetData(self):
        return memoryview(self.data)


class Voice:
    """One SpVoice object. make_seconds: time to make a text in memory; slow voices exceed the 0.25 s probe."""

    def __init__(self, device, slow_names=(), log=None):
        self.device = device
        self.slow_names = slow_names
        self.log = log if log is not None else []
        self.Voice = TOKENS[0]
        self.Rate = 0
        self.Volume = 100
        self.direct_output = True    # a new SpVoice speaks on the sound device until it is given a memory stream
        self._stream = None
        self._making = None          # (text, stream, ready_at)
        self._sound = None           # the device interval of direct speech
        self.calls = []

    def GetVoices(self, required, optional):
        return Tokens(TOKENS)

    def GetAudioOutputs(self):
        class Outputs:
            def Item(self, i):
                return "default output"
        return Outputs()

    @property
    def AudioOutputStream(self):
        return self._stream

    @AudioOutputStream.setter
    def AudioOutputStream(self, stream):
        self._stream = stream
        self.direct_output = False

    @property
    def AudioOutput(self):
        return "default output"

    @AudioOutput.setter
    def AudioOutput(self, value):
        self._stream = None
        self.direct_output = True

    def _make_seconds(self):
        return 1.0 if self.Voice.GetDescription() in self.slow_names else 0.005

    def Speak(self, text, flags):
        name = self.Voice.GetDescription()
        self.calls.append((text, flags))
        if flags & SVSF_PURGE_BEFORE_SPEAK:
            self._making = None
            if self._sound is not None and self._sound[3] > time.monotonic():
                self._sound[3] = time.monotonic()            # direct speech stops at once
            self._sound = None
        if not text:
            return 1
        if self.direct_output:
            now = time.monotonic()
            self._sound = self.device.add(name, text, now, now + SPEAK_SECONDS_PER_CHAR * len(text))
            self.log.append(("direct", name, self.Volume, self.Rate, text))
        else:
            self._making = (f"{name}|{self.Volume}|{self.Rate}|{text}", self._stream,
                            time.monotonic() + self._make_seconds())
        return 1

    def WaitUntilDone(self, ms):
        deadline = time.monotonic() + ms / 1000.0
        while True:
            now = time.monotonic()
            if self._making is not None:
                content, stream, ready = self._making
                if now >= ready:
                    if len(content) % 2:
                        content += "~"                       # whole 16-bit samples, never trimmed as silence
                    stream.data = content.encode("ascii")
                    self._making = None
                    return True
            elif self._sound is not None:
                if now >= self._sound[3]:
                    self._sound = None
                    return True
            else:
                return True
            if now >= deadline:
                return False
            time.sleep(0.0005)


class Player:
    """Rendered audio: every block plays PLAY_SECONDS after the one before it, on the shared device."""

    def __init__(self, device):
        self.device = device
        self.blocks = []
        self.resets = 0
        self._end = 0.0
        self._current = []

    def write(self, pcm):
        text = bytes(pcm).decode("ascii")
        text = text[:-1] if text.endswith("~") else text
        start = max(time.monotonic(), self._end)
        self._end = start + PLAY_SECONDS
        self.blocks.append(text)
        self._current.append(self.device.add("player", text, start, self._end))
        return True

    def busy(self):
        return time.monotonic() < self._end

    def reset(self):
        self.resets += 1
        now = time.monotonic()
        for sound in self._current:
            sound[3] = min(sound[3], max(sound[2], now))
        self._current = []
        self._end = 0.0

    def close(self):
        pass


ROLES = {ANNOUNCER: RoleVoice("HKEY\\Bill", 95), OWN_QUARTERBACK: RoleVoice("HKEY\\David", 80),
         OPPONENT_QUARTERBACK: RoleVoice("ENUM\\Zira", 60), OWN_PUNTER: RoleVoice(None, 50),
         OPPONENT_PUNTER: RoleVoice("hkey\\david", 30)}


class Rig:
    def __init__(self, roles=None, slow=(), render=True, factory_fails_after=None):
        self.device = Device()
        self.log = []
        self.made = []
        self.trials = []
        self.player = Player(self.device)

        def factory():
            if factory_fails_after is not None and len(self.made) >= factory_fails_after:
                raise OSError("class not registered")
            voice = Voice(self.device, slow, self.log)
            self.made.append(voice)
            return voice

        self.backend = SapiBackend(voice_factory=factory, token_factory=TokenObject, com_init=False, render=render,
                                   player_factory=lambda: self.player, stream_factory=Stream,
                                   roles=dict(roles or ROLES), default_role=ANNOUNCER)
        self.backend.on_voice_trial = lambda voice_id: self.trials.append(("trial", voice_id))
        self.backend.on_voice_proven = lambda voice_id: self.trials.append(("proven", voice_id))
        started = self.backend.start(5)
        assert started.ok, started.error

    def heard(self):
        """(voice, volume, rate, text) of everything that reached the device, in the order it sounded."""
        out = []
        for who, text, start, end in sorted(self.device.sounds, key=lambda s: s[2]):
            if who == "player":
                name, volume, rate, words = text.split("|", 3)
                out.append((name, int(volume), int(rate), words))
            else:
                entry = next(e for e in self.log if e[0] == "direct" and e[4] == text and e[1] == who)
                out.append((who, entry[2], entry[3], text))
        return out

    def close(self):
        self.backend.close()


@pytest.fixture
def rig():
    made = Rig()
    yield made
    made.close()


def test_every_speaker_speaks_with_its_own_voice_and_volume_in_one_queue(rig):
    for role, text in ((ANNOUNCER, "first down"), (OWN_QUARTERBACK, "hut one"), (OPPONENT_QUARTERBACK, "hike"),
                       (OWN_PUNTER, "punt"), (OPPONENT_PUNTER, "kick"), (ANNOUNCER, "touchdown")):
        rig.backend.speak(text, role)
    rig.backend.wait_until_done()
    assert rig.heard() == [("FlexVoice2 Bill", 95, 0, "first down"), ("Microsoft David", 80, 0, "hut one"),
                           ("Microsoft Zira", 60, 0, "hike"), ("FlexVoice2 Bill", 50, 0, "punt"),
                           ("Microsoft David", 30, 0, "kick"), ("FlexVoice2 Bill", 95, 0, "touchdown")]
    assert len(rig.made) == 3                      # one object per distinct voice: Bill (start), David, Zira
    assert rig.device.overlaps() == [] and rig.player.resets == 0


def test_a_voice_change_never_cuts_the_text_before_it(rig):
    rig.backend.speak("Hike!", OWN_QUARTERBACK)         # GAME_SPEC 7 item 1: the unguarded " Hike! " (Q52)
    rig.backend.speak("He hands off to Jones", ANNOUNCER)
    rig.backend.wait_until_done()
    texts = [h[3] for h in rig.heard()]
    assert texts == ["Hike!", "He hands off to Jones"]
    first = sorted(rig.device.sounds, key=lambda s: s[2])[0]
    assert first[3] - first[2] == pytest.approx(PLAY_SECONDS, abs=0.002)   # played to its end
    assert rig.player.resets == 0


def test_a_slow_voice_speaks_directly_and_keeps_its_place_in_the_queue():
    rig = Rig(slow=("Microsoft Zira",))
    try:
        rig.backend.speak("the snap", ANNOUNCER)
        rig.backend.speak("blue 17", OPPONENT_QUARTERBACK)        # Zira: too slow to render, so direct
        rig.backend.speak("he drops back", ANNOUNCER)
        rig.backend.wait_until_done()
        assert [(h[0], h[3]) for h in rig.heard()] == [("FlexVoice2 Bill", "the snap"), ("Microsoft Zira", "blue 17"),
                                                       ("FlexVoice2 Bill", "he drops back")]
        assert rig.device.overlaps() == []
    finally:
        rig.close()


def test_without_a_sound_device_every_voice_speaks_directly_one_after_the_other():
    rig = Rig(render=False)
    try:
        for role, text in ((ANNOUNCER, "one"), (OWN_QUARTERBACK, "two"), (OPPONENT_QUARTERBACK, "three"),
                           (ANNOUNCER, "four")):
            rig.backend.speak(text, role)
        rig.backend.wait_until_done()
        assert [h[3] for h in rig.heard()] == ["one", "two", "three", "four"]
        assert rig.device.overlaps() == [] and rig.player.blocks == []
    finally:
        rig.close()


def test_stop_cuts_a_direct_voice_at_once_and_drops_what_waits_behind_it():
    rig = Rig(slow=("Microsoft Zira",))
    try:
        rig.backend.speak("x", OPPONENT_QUARTERBACK)              # opens and probes Zira (0.25 s), then speaks
        rig.backend.wait_until_done()
        long_line = "a long direct line of the opponent's quarterback calling the signals"   # 0.34 s
        rig.backend.speak(long_line, OPPONENT_QUARTERBACK)
        time.sleep(0.05)
        rig.backend.speak("never heard", ANNOUNCER)
        t0 = time.monotonic()
        rig.backend.stop()
        rig.backend.wait_until_done()
        assert time.monotonic() - t0 < 0.1
        assert "never heard" not in [h[3] for h in rig.heard()]
        cut = next(s for s in rig.device.sounds if s[1] == long_line)
        assert cut[3] - cut[2] < 0.2                                 # cut short, not played to its end
        zira = next(v for v in rig.made if v.Voice.GetDescription() == "Microsoft Zira")
        assert ("", 3) in zira.calls                                 # purged
        rig.backend.speak("after the stop", ANNOUNCER)
        rig.backend.wait_until_done()
        assert rig.heard()[-1][3] == "after the stop"
    finally:
        rig.close()


def test_stop_cuts_rendered_speech_at_once(rig):
    for i in range(20):
        rig.backend.speak(f"line {i}", OWN_QUARTERBACK if i % 2 else ANNOUNCER)
    time.sleep(0.05)
    t0 = time.monotonic()
    rig.backend.stop()
    rig.backend.wait_until_done()
    assert time.monotonic() - t0 < 0.1
    assert rig.player.resets >= 1 and len(rig.heard()) < 20


def test_the_rate_counter_reaches_every_voice_and_a_rate_step_only_its_text(rig):
    rig.backend.set_rate(3)
    rig.backend.speak("normal", ANNOUNCER)
    rig.backend.speak("red leather yellow leather", ANNOUNCER, rate_step=1)     # banter line 113 (Q38)
    rig.backend.speak("quarterback", OWN_QUARTERBACK)
    rig.backend.wait_until_done()
    assert [(h[3], h[2]) for h in rig.heard()] == [("normal", 3), ("red leather yellow leather", 4), ("quarterback", 3)]
    rig.backend.set_rate(10)
    rig.backend.speak("fast", ANNOUNCER, rate_step=1)
    rig.backend.wait_until_done()
    assert rig.heard()[-1][2] == 10                                              # clamped to the SAPI range
    rig.backend.set_rate(None)
    rig.backend.speak("own rate", ANNOUNCER)
    rig.backend.wait_until_done()
    assert rig.heard()[-1][2] == 0                                               # the first voice's base rate


def test_the_crash_guard_arms_each_new_voice_before_it_opens_and_clears_it_after_its_first_text():
    rig = Rig(roles={ANNOUNCER: RoleVoice(None, 95), OWN_QUARTERBACK: RoleVoice("HKEY\\David", 95),
                     OPPONENT_QUARTERBACK: RoleVoice("ENUM\\Zira", 95)}, slow=("Microsoft Zira",))
    try:
        assert rig.trials == [("trial", ""), ("proven", "")]           # the first voice is never set aside
        rig.backend.speak("hut", OWN_QUARTERBACK)
        rig.backend.wait_until_done()
        assert rig.trials[2:] == [("trial", "HKEY\\David"), ("proven", "HKEY\\David")]   # proven by its probe
        rig.backend.speak("hike", OPPONENT_QUARTERBACK)
        rig.backend.wait_until_done()
        # a slow voice is proven only when its first text has been spoken to the end
        assert rig.trials[4:] == [("trial", "ENUM\\Zira"), ("proven", "ENUM\\Zira")]
        rig.backend.speak("hike again", OPPONENT_QUARTERBACK)
        rig.backend.wait_until_done()
        assert len(rig.trials) == 6                                     # once per voice
    finally:
        rig.close()


def test_choosing_a_speakers_voice_opens_it_and_probes_it_again(rig):
    rig.backend.set_role_voice(OWN_QUARTERBACK, "ENUM\\Zira")
    for _ in range(300):
        if ("proven", "ENUM\\Zira") in rig.trials:
            break
        time.sleep(0.01)
    assert ("trial", "ENUM\\Zira") in rig.trials and ("proven", "ENUM\\Zira") in rig.trials
    assert rig.backend.role_voice(OWN_QUARTERBACK).voice_id == "ENUM\\Zira"
    rig.backend.speak("hut", OWN_QUARTERBACK)
    rig.backend.wait_until_done()
    assert rig.heard()[-1][:2] == ("Microsoft Zira", 80)
    before = len(rig.trials)
    rig.backend.set_role_voice(ANNOUNCER, None)            # chosen again (the same first voice): probed again
    for _ in range(300):
        if len(rig.trials) > before:
            break
        time.sleep(0.01)
    assert rig.trials[before:] == [("trial", "")]          # proven already: no second all clear
    assert rig.backend.voice_name == "FlexVoice2 Bill"


def test_role_details_read_the_gender_without_opening_the_voice(rig):
    made = len(rig.made)
    zira = rig.backend.role_details(OPPONENT_QUARTERBACK)
    assert (zira.voice_id, zira.name, zira.gender) == ("ENUM\\Zira", "Microsoft Zira", "Female")
    assert rig.backend.role_details(OWN_QUARTERBACK).gender == "Male"
    rig.backend.set_role_voice(OWN_PUNTER, "HKEY\\Fred")
    assert rig.backend.role_details(OWN_PUNTER).gender == ""              # no Gender attribute: the original's " He "
    assert len(rig.made) <= made + 1                                     # only the chosen Fred was opened
    assert all(v.Voice.GetDescription() != "Microsoft Zira" for v in rig.made)


def test_an_unknown_speaker_is_the_announcer_and_a_missing_voice_the_first_voice():
    rig = Rig(roles={ANNOUNCER: RoleVoice("HKEY\\David", 70), OWN_QUARTERBACK: RoleVoice("ENUM\\Gone", 40)})
    try:
        rig.backend.speak("who am I", "the referee")
        rig.backend.speak("gone", OWN_QUARTERBACK)
        rig.backend.wait_until_done()
        assert [(h[0], h[1], h[3]) for h in rig.heard()] == [("Microsoft David", 70, "who am I"),
                                                             ("FlexVoice2 Bill", 40, "gone")]
    finally:
        rig.close()


def test_a_voice_object_that_cannot_be_made_falls_back_to_the_announcers():
    rig = Rig(factory_fails_after=1)
    try:
        rig.backend.speak("hut", OWN_QUARTERBACK)
        rig.backend.wait_until_done()
        assert [(h[0], h[3]) for h in rig.heard()] == [("FlexVoice2 Bill", "hut")]
    finally:
        rig.close()


def test_a_synchronous_line_waits_for_everything_queued_before_it(rig):
    from nfl4.speech.manager import SpeechManager
    manager = SpeechManager(rig.backend, None)
    manager.say_async("This is week  1 of Josh Kennedy's N. F. L. football ", role=ANNOUNCER)
    manager.say_async(" Hike! ", role=OWN_QUARTERBACK)
    t0 = time.monotonic()
    manager.say(" He drops back ", role=ANNOUNCER)
    assert time.monotonic() - t0 >= 3 * PLAY_SECONDS - 0.01
    assert [h[3] for h in rig.heard()] == ["This is week  1 of Josh Kennedy's N. F. L. football ", " Hike! ", " He drops back "]
    assert not rig.backend.is_speaking()


def test_a_text_of_spaces_is_only_a_barrier(rig):
    rig.backend.speak("one", ANNOUNCER)
    rig.backend.speak(" ", OWN_QUARTERBACK)
    rig.backend.wait_until_done()
    assert [h[3] for h in rig.heard()] == ["one"]
    assert len(rig.made) == 1                       # no voice was opened for a text with nothing to say


def test_thousands_of_texts_and_stops_from_two_threads_never_hang_or_overlap(rig):
    roles = [ANNOUNCER, OWN_QUARTERBACK, OPPONENT_QUARTERBACK, OWN_PUNTER, OPPONENT_PUNTER]

    def talker(offset):
        for i in range(1500):
            rig.backend.speak(f"t{offset}-{i}", roles[(i + offset) % 5])
            if i % 97 == 0:
                rig.backend.stop()

    threads = [threading.Thread(target=talker, args=(n,)) for n in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    done = threading.Event()
    threading.Thread(target=lambda: (rig.backend.wait_until_done(), done.set()), daemon=True).start()
    rig.backend.stop()
    assert done.wait(10)
    assert rig.device.overlaps() == []
