"""Speech manager modes and fallbacks (playbook 7.2, 7.3). This is inspired by Jim Kitchen's Brain."""
import threading
import time

from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager


def make(mode="sapi", sapi_ok=True, nvda_ok=True):
    sapi = FakeBackend("SAPI 5", available=sapi_ok)
    nvda = FakeBackend("NVDA", available=nvda_ok)
    return SpeechManager(sapi, nvda, mode), sapi, nvda


def test_default_mode_is_sapi_even_when_nvda_runs():
    manager, sapi, nvda = make()
    assert manager.mode == "sapi"
    manager.say_async("hello")
    assert sapi.spoken() == ["hello"] and nvda.spoken() == []


def test_auto_and_nvda_modes_use_nvda_when_it_runs():
    for mode in ("auto", "nvda"):
        manager, sapi, nvda = make(mode)
        manager.say_async("hello")
        assert nvda.spoken() == ["hello"] and sapi.spoken() == []


def test_nvda_not_running_falls_back_to_sapi_silently():
    for mode in ("auto", "nvda"):
        manager, sapi, nvda = make(mode, nvda_ok=False)
        manager.say("hello")
        assert sapi.spoken() == ["hello"]


def test_nvda_closing_mid_game_falls_back_to_sapi():
    manager, sapi, nvda = make("auto")
    manager.say_async("one")
    nvda.available = False
    manager.say_async("two")
    assert nvda.spoken() == ["one"] and sapi.spoken() == ["two"]


def test_speak_failure_tries_the_other_engine():
    manager, sapi, nvda = make("nvda")
    nvda.fail_speak = True
    manager.say_async("x")
    assert sapi.spoken() == ["x"]


def test_sapi_broken_uses_nvda_rather_than_silence():
    manager, sapi, nvda = make("sapi", sapi_ok=False)
    manager.say_async("x")
    assert nvda.spoken() == ["x"]


def test_no_engine_at_all_does_not_raise():
    manager = SpeechManager(None, None)
    manager.say("x")
    manager.say_async("x")
    manager.stop()
    manager.close()


def test_say_waits_and_say_async_does_not():
    manager, sapi, _ = make()
    sapi.seconds_per_char = 0.01
    start = time.monotonic()
    manager.say_async("0123456789")
    assert time.monotonic() - start < 0.05
    manager.say("0123456789")       # waits for both: 20 chars = 0.2 s
    assert time.monotonic() - start >= 0.19


def test_say_wait_ends_when_aborted():
    manager, sapi, _ = make()
    sapi.seconds_per_char = 1.0
    abort = threading.Event()
    threading.Timer(0.05, abort.set).start()
    start = time.monotonic()
    manager.say("long text", abort)
    assert time.monotonic() - start < 1.0


def test_stop_reaches_every_engine():
    manager, sapi, nvda = make()
    manager.stop()
    assert ("stop", "") in sapi.events and ("stop", "") in nvda.events


def test_mode_change_stops_speech_and_ignores_unknown_modes():
    manager, sapi, _ = make()
    manager.mode = "auto"
    assert manager.mode == "auto" and ("stop", "") in sapi.events
    manager.mode = "loud"
    assert manager.mode == "auto"


def test_screen_reader_message_only_through_nvda():
    manager, sapi, nvda = make()
    assert manager.screen_reader_message("no voices")
    assert nvda.spoken() == ["no voices"] and sapi.spoken() == []
    manager, sapi, nvda = make(nvda_ok=False)
    assert not manager.screen_reader_message("no voices")


def test_settings_calls_reach_sapi_only_and_the_voice_facts_come_from_it():
    sapi, nvda = FakeBackend("sapi"), FakeBackend("nvda")
    sapi.voice_name, sapi.base_rate = "Fake Voice", 2
    manager = SpeechManager(sapi, nvda)
    manager.set_rate(3)
    manager.set_volume(50)
    manager.set_pitch(-1)
    manager.set_voice("tok")
    assert sapi.events == [("rate", 3), ("volume", 50), ("pitch", -1), ("voice", "tok")]
    assert nvda.events == []
    assert (manager.voice_name, manager.base_rate) == ("Fake Voice", 2)
    assert manager.nvda_running() and not SpeechManager(sapi, None).nvda_running()
    assert SpeechManager(None, nvda).voice_name == ""      # no SAPI 5: nothing to report, nothing to set
