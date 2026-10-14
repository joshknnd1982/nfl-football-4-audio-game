"""SAPI 5 backend logic with a fake COM voice (no real engine). This is inspired by Jim Kitchen."""
import time

import pytest

from nfl4.speech.sapi5 import SVSF_ASYNC, SVSF_IS_XML, SVSF_PURGE_BEFORE_SPEAK, SapiBackend, apply_pitch


class FakeToken:
    def __init__(self, token_id, name, broken=False):
        self.Id = token_id
        self._name = name

    def GetDescription(self):
        return self._name


class FakeTokens:
    def __init__(self, tokens):
        self._tokens = tokens
        self.Count = len(tokens)

    def Item(self, i):
        return self._tokens[i]


class FakeVoice:
    """Speech 'plays' for 30 ms per Speak; records calls."""
    def __init__(self, tokens, rate=2, fail_speak=False):
        self._tokens = tokens
        self.Rate = rate
        self.Volume = 100
        self.Voice = None
        self.calls = []
        self._end = 0.0
        self.fail_speak = fail_speak

    def GetVoices(self, required, optional):
        return FakeTokens(self._tokens)

    def Speak(self, text, flags):
        if self.fail_speak and text:
            raise OSError("engine broke")
        self.calls.append((text, flags))
        if flags & SVSF_PURGE_BEFORE_SPEAK:
            self._end = 0.0
        if text:
            self._end = max(time.monotonic(), self._end) + 0.03
        return 1

    def WaitUntilDone(self, ms):
        return time.monotonic() >= self._end


class FakeTokenObject:
    """SAPI.SpObjectToken: SetId works only for registry-style IDs."""
    def SetId(self, token_id):
        if not token_id.startswith("HKEY"):
            raise OSError("not a registry token")
        self.Id = token_id
        self._name = token_id.rsplit("\\", 1)[-1]

    def GetDescription(self):
        return self._name


TOKENS = [FakeToken("HKEY\\Bill", "FlexVoice2 Bill"), FakeToken("HKEY\\David", "Microsoft David"),
          FakeToken("ENUM\\Zira", "Microsoft Zira")]


def backend(voice, **kw):
    b = SapiBackend(voice_factory=lambda: voice, token_factory=FakeTokenObject, com_init=False, **kw)
    started = b.start(5)
    return b, started


def test_first_voice_volume_90_rate_kept():
    voice = FakeVoice(TOKENS, rate=2)
    b, started = backend(voice)
    try:
        assert started.ok and started.voice_count == 3
        assert started.voice_name == "FlexVoice2 Bill"     # GetVoices Item(0), GAME_SPEC 3.1
        assert voice.Volume == 90 and voice.Rate == 2 and started.base_rate == 2
    finally:
        b.close()


def test_no_voices_reported_not_raised():
    b, started = backend(FakeVoice([]))
    assert not started.ok and started.voice_count == 0
    assert not b.is_available() and not b.speak("x")
    b.close()


def test_sapi_missing_reported():
    def broken():
        raise OSError("class not registered")
    b = SapiBackend(voice_factory=broken, com_init=False)
    started = b.start(5)
    assert not started.ok and "unavailable" in started.error


def test_speak_is_async_and_wait_until_done_waits():
    voice = FakeVoice(TOKENS)
    b, _ = backend(voice)
    try:
        t = time.monotonic()
        b.speak("one")
        b.speak("two")
        assert time.monotonic() - t < 0.02
        b.wait_until_done()
        assert time.monotonic() - t >= 0.055
        assert voice.calls == [("one", SVSF_ASYNC), ("two", SVSF_ASYNC)]  # flags as the original (no XML)
        assert not b.is_speaking()
    finally:
        b.close()


def test_stop_purges():
    voice = FakeVoice(TOKENS)
    b, _ = backend(voice)
    try:
        b.speak("long")
        b.stop()
        b.wait_until_done()
        assert voice.calls[-1] == ("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
    finally:
        b.close()


def test_pitch_wraps_text_in_xml_only_when_set():
    assert apply_pitch("a&b", 0) == ("a&b", 0)
    assert apply_pitch("a&b<", 5) == ('<pitch absmiddle="5">a&amp;b&lt;</pitch>', SVSF_IS_XML)
    voice = FakeVoice(TOKENS)
    b, _ = backend(voice, pitch=-3)
    try:
        b.speak("hi")
        b.wait_until_done()
        assert voice.calls[-1] == ('<pitch absmiddle="-3">hi</pitch>', SVSF_ASYNC | SVSF_IS_XML)
    finally:
        b.close()


def test_saved_voice_by_set_id_and_by_scan():
    b, started = backend(FakeVoice(TOKENS), voice_id="HKEY\\David")
    assert started.voice_name == "David"          # found by SetId
    b.close()
    b, started = backend(FakeVoice(TOKENS), voice_id="ENUM\\Zira")
    assert started.voice_name == "Microsoft Zira"  # SetId refused, found by scanning the list
    b.close()


def test_missing_saved_voice_falls_back_to_first():
    b, started = backend(FakeVoice(TOKENS), voice_id="ENUM\\Gone")
    assert started.voice_name == "FlexVoice2 Bill"
    b.close()


def test_settings_change_rate_volume_voice():
    voice = FakeVoice(TOKENS, rate=1)
    b, _ = backend(voice, rate=4)
    try:
        assert voice.Rate == 4
        b.set_rate(30)
        b.set_volume(55)
        b.set_voice("ENUM\\Zira")
        b.speak("x")
        b.wait_until_done()
        assert voice.Rate == 10 and voice.Volume == 55 and voice.Voice.Id == "ENUM\\Zira"
        b.set_rate(None)                       # back to the voice's own base rate
        b.speak("x")
        b.wait_until_done()
        assert voice.Rate == 1
        assert b.base_rate == 1 and b.voice_id == "ENUM\\Zira" and b.voice_name      # what the settings menu reads
    finally:
        b.close()


def test_engine_failure_never_raises_or_hangs():
    voice = FakeVoice(TOKENS, fail_speak=True)
    b, _ = backend(voice)
    try:
        assert b.speak("x")
        t = time.monotonic()
        b.wait_until_done()
        assert time.monotonic() - t < 0.5
    finally:
        b.close()


@pytest.mark.parametrize("value, expected", [(-50, -10), (0, 0), (50, 10)])
def test_pitch_clamped(value, expected):
    b = SapiBackend(pitch=value, voice_factory=lambda: FakeVoice(TOKENS), com_init=False)
    assert b._pitch == expected


class Status:
    RunningState, CurrentStreamNumber, InputWordPosition = 2, 1, 0


class StuckVoice(FakeVoice):
    """Holds the audio device at word 0 forever, as in the two-programs deadlock (S7.1 test)."""
    Status = Status()

    def WaitUntilDone(self, ms):
        return False


def test_stalled_speech_is_stopped_by_the_watchdog(monkeypatch):
    import nfl4.speech.sapi5 as sapi5
    monkeypatch.setattr(sapi5, "STALL_SECONDS", 0.3)
    voice = StuckVoice(TOKENS)
    b, _ = backend(voice)
    try:
        t = time.monotonic()
        b.speak("never ends")
        b.wait_until_done()
        assert 0.3 <= time.monotonic() - t < 2.0
        assert voice.calls[-1] == ("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
    finally:
        b.close()


def test_slow_but_moving_speech_is_not_cut(monkeypatch):
    import nfl4.speech.sapi5 as sapi5
    monkeypatch.setattr(sapi5, "STALL_SECONDS", 0.3)

    class Moving:
        RunningState, CurrentStreamNumber = 2, 1

        @property
        def InputWordPosition(self):
            return int(time.monotonic() * 10)       # a new word every 0.1 s

    class SlowVoice(FakeVoice):
        Status = Moving()

        def Speak(self, text, flags):
            super().Speak(text, flags)
            if text:
                self._end = time.monotonic() + 1.0   # one long second of speech

    voice = SlowVoice(TOKENS)
    b, _ = backend(voice)
    try:
        b.speak("slow")
        b.wait_until_done()
        assert voice.calls[-1] == ("slow", SVSF_ASYNC)   # finished, never purged
    finally:
        b.close()
