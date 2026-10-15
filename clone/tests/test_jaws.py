"""JAWS backend and its place in the speech manager (playbook 7.3.1). This is inspired by Jim Kitchen.

The COM object is replaced by a fake with the interface read from the type library on the owner's PC
(IJawsApi: SayString(text, flush) -> bool, StopSpeech()). One test makes the real COM object
(JAWS not running: SayString answers False, nothing is spoken).
"""
import struct
import threading

import pytest

from nfl4.speech.fake import FakeBackend
from nfl4.speech.jaws import JawsBackend, estimated_seconds
from nfl4.speech.manager import SpeechManager


class FakeJawsCom:
    def __init__(self, running=True):
        self.running = running
        self.calls = []

    def SayString(self, text, flush):
        self.calls.append(("say", text, flush))
        return self.running

    def StopSpeech(self):
        self.calls.append(("stop",))


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make(running=True, window=False):
    com = FakeJawsCom(running)
    made = []

    def factory():
        made.append(threading.get_ident())
        return com

    clock = Clock()
    backend = JawsBackend(factory=factory, window_open=lambda: window, clock=clock)
    return backend, com, made, clock


def test_speak_queues_after_current_speech_without_flushing():
    backend, com, _, _ = make()
    assert backend.speak("hello there")
    assert com.calls == [("say", "hello there", False)]


def test_jaws_not_running_means_unavailable_and_speak_false_without_errors():
    backend, com, _, _ = make(running=False)
    assert not backend.is_available()
    assert not backend.speak("hello")


def test_availability_by_window_needs_no_com_call_and_by_probe_otherwise():
    backend, com, made, _ = make(window=True)
    assert backend.is_available() and com.calls == [] and made == []
    backend, com, _, _ = make(window=False)
    assert backend.is_available()
    assert com.calls == [("say", "", False)]         # the probe: an empty text, no flush, says nothing


def test_availability_is_remembered_briefly_and_a_failed_speak_forces_a_new_check():
    backend, com, _, clock = make()
    assert backend.is_available() and backend.is_available()
    assert len(com.calls) == 1
    clock.now += 0.5
    assert backend.is_available()
    assert len(com.calls) == 2
    com.running = False
    assert not backend.speak("x")
    assert not backend.is_available()


def test_stop_cuts_with_a_flushed_space_not_stop_speech_and_ends_a_wait():
    backend, com, _, clock = make()
    backend.speak("a fairly long sentence that takes a while")
    backend.stop()
    assert com.calls[-1] == ("say", " ", True)            # StopSpeech does nothing on JAWS 2026 (loopback test)
    assert ("stop",) not in com.calls
    backend.wait_until_done()          # deadline cleared: returns at once on the fixed clock


def test_stop_without_our_speech_leaves_jaws_alone():
    backend, com, _, clock = make()
    backend.stop()                                          # nothing spoken: the game calls stop() on every key
    assert com.calls == []
    backend.speak("hello")
    clock.now += 60                                         # long finished, even with the margin
    backend.stop()
    assert [c for c in com.calls if c[0] == "say" and c[2] is True] == []


def test_stop_still_cuts_when_the_estimate_was_short():
    backend, com, _, clock = make()
    backend.speak("x")                                      # estimate 0.185 s
    clock.now += 1.0                                        # a slow voice is still talking
    backend.stop()
    assert com.calls[-1] == ("say", " ", True)


def test_arrowing_pattern_cuts_then_queues_the_next_item():
    backend, com, _, clock = make()
    backend.speak("Voice: Microsoft David.")
    backend.stop()
    backend.speak("Speech rate: 0, original.")
    assert [c[1:] for c in com.calls if c[0] == "say"][-2:] == [(" ", True), ("Speech rate: 0, original.", False)]


def test_wait_uses_an_estimate_from_the_text_and_ends_on_abort():
    assert estimated_seconds("") == pytest.approx(0.08)
    assert estimated_seconds("x" * 100) == pytest.approx(2.48)
    assert estimated_seconds("x" * 10000) == 30.0
    backend = JawsBackend(factory=lambda: FakeJawsCom(), window_open=lambda: False)
    backend.speak("x" * 100)           # 2.48 s real time unless aborted
    abort = threading.Event()
    threading.Timer(0.05, abort.set).start()
    backend.wait_until_done(abort)     # returns when aborted (the test would hang otherwise)
    assert abort.is_set()


def test_empty_text_is_accepted_and_not_sent():
    backend, com, _, _ = make()
    assert backend.speak("  ") and com.calls == []


def test_a_com_error_is_swallowed_and_the_object_is_made_again():
    made = []

    class Dying(FakeJawsCom):
        def SayString(self, text, flush):
            raise OSError("JAWS closed")

    objects = [Dying(), FakeJawsCom()]

    def factory():
        made.append(1)
        return objects[len(made) - 1]

    backend = JawsBackend(factory=factory, window_open=lambda: False)
    assert not backend.speak("one")
    assert backend.speak("two")
    assert len(made) == 2


def test_a_missing_com_class_is_tried_once_and_never_raises():
    calls = []

    def factory():
        calls.append(1)
        raise OSError("class not registered")

    backend = JawsBackend(factory=factory, window_open=lambda: False)
    assert not backend.is_available() and not backend.speak("x")
    backend.stop()
    backend.wait_until_done()
    backend.close()
    assert len(calls) == 1


def test_each_thread_makes_its_own_com_object():
    backend, com, made, _ = make()
    backend.speak("main")
    done = threading.Thread(target=lambda: backend.speak("other"))
    done.start()
    done.join()
    assert len(made) == 2 and len(set(made)) == 2


def jaws_manager(mode, jaws_ok=True, nvda_ok=True, sapi_ok=True):
    sapi, nvda, jaws = FakeBackend("SAPI 5", available=sapi_ok), FakeBackend("NVDA", available=nvda_ok), \
        FakeBackend("JAWS", available=jaws_ok)
    return SpeechManager(sapi, nvda, mode, jaws), sapi, nvda, jaws


def test_jaws_mode_uses_jaws_and_falls_back_to_sapi():
    manager, sapi, nvda, jaws = jaws_manager("jaws")
    manager.say_async("hello")
    assert jaws.spoken() == ["hello"] and sapi.spoken() == [] and nvda.spoken() == []
    manager, sapi, nvda, jaws = jaws_manager("jaws", jaws_ok=False)
    manager.say("hello")
    assert sapi.spoken() == ["hello"] and nvda.spoken() == []
    manager, sapi, nvda, jaws = jaws_manager("jaws")
    jaws.fail_speak = True
    manager.say_async("x")
    assert sapi.spoken() == ["x"]


def test_auto_prefers_nvda_then_jaws_then_sapi():
    manager, sapi, nvda, jaws = jaws_manager("auto")
    manager.say_async("a")
    assert nvda.spoken() == ["a"] and jaws.spoken() == []
    manager, sapi, nvda, jaws = jaws_manager("auto", nvda_ok=False)
    manager.say_async("b")
    assert jaws.spoken() == ["b"] and sapi.spoken() == []
    manager, sapi, nvda, jaws = jaws_manager("auto", nvda_ok=False, jaws_ok=False)
    manager.say_async("c")
    assert sapi.spoken() == ["c"]


def test_jaws_closing_mid_game_falls_back_to_sapi():
    manager, sapi, nvda, jaws = jaws_manager("jaws")
    manager.say_async("one")
    jaws.available = False
    manager.say_async("two")
    assert jaws.spoken() == ["one"] and sapi.spoken() == ["two"]


def test_nvda_and_sapi_modes_do_not_use_jaws_unless_nothing_else_works():
    for mode in ("sapi", "nvda"):
        manager, sapi, nvda, jaws = jaws_manager(mode)
        manager.say_async("x")
        assert jaws.spoken() == []
    manager, sapi, nvda, jaws = jaws_manager("sapi", sapi_ok=False, nvda_ok=False)
    manager.say_async("x")
    assert jaws.spoken() == ["x"]


def test_stop_close_and_running_checks_reach_jaws():
    manager, sapi, nvda, jaws = jaws_manager("auto")
    manager.stop()
    assert ("stop", "") in jaws.events
    assert manager.jaws_running()
    assert not SpeechManager(sapi, nvda).jaws_running()
    assert not jaws_manager("auto", jaws_ok=False)[0].jaws_running()


def test_screen_reader_message_goes_to_nvda_then_jaws():
    manager, sapi, nvda, jaws = jaws_manager("sapi")
    assert manager.screen_reader_message("no voices")
    assert nvda.spoken() == ["no voices"] and jaws.spoken() == []
    manager, sapi, nvda, jaws = jaws_manager("sapi", nvda_ok=False)
    assert manager.screen_reader_message("no voices")
    assert jaws.spoken() == ["no voices"]
    manager, sapi, nvda, jaws = jaws_manager("sapi", nvda_ok=False, jaws_ok=False)
    assert not manager.screen_reader_message("no voices")


def test_real_com_object_with_jaws_not_running_is_quiet_and_calm():
    """Needs JAWS installed (its COM class registered); skipped otherwise. Never speaks."""
    backend = JawsBackend()
    if backend._object() is None:
        pytest.skip("JAWS COM class not registered on this PC")
    bits = struct.calcsize("P") * 8
    if backend.is_available():
        pytest.skip(f"JAWS is running; this {bits}-bit test is for the not-running case")
    assert not backend.speak("this must not be spoken")
    backend.stop()
    backend.close()


def test_jaws_output_is_saved_read_back_and_accepted_in_any_spelling():
    from nfl4.data.settings import Settings
    from nfl4.data.settingsfile import parse, render
    s = Settings.defaults()
    s.speech.mode = "jaws"
    back, problems = parse(render(s))
    assert back.speech.mode == "jaws" and problems == []
    back, problems = parse("speech_output =  JAWS \n")
    assert back.speech.mode == "jaws" and problems == []
    back, problems = parse("sound_volume = -5\nspeech_output = jawz\n")
    assert back.speech.mode == "sapi" and len(problems) == 1


# ----- no "sounds start right away" setting in nfl4 (GAP_REGISTER G-S11, D-031 item 1; Brain had one in F3) -----

def test_nfl4_has_no_sound_start_setting_the_original_wait_stays():
    from nfl4.data.settings import Settings
    from nfl4.data.settingsfile import parse, render
    s = Settings.defaults()
    assert not hasattr(s.audio, "start_early") and "sound_start" not in render(s)      # S7.2 removed the kit's field
    assert not hasattr(s.audio, "effects_volume") and not hasattr(s.audio, "pitch_spread")
    back, problems = parse("sound_volume = -5\nsound_start = right_away\n")
    assert back.audio.sound_level == -500 and len(problems) == 1           # an unknown setting, reported


def test_is_speaking_is_the_estimated_end_of_our_speech_so_the_help_menus_wait_under_jaws():
    """nfl4 S7.4a: JAWS gives no signal, so F5, F6 and F7 wait on the estimate a blocking say uses."""
    backend, com, _, clock = make()
    assert not backend.is_speaking()
    backend.speak("hello there")
    assert backend.is_speaking()
    clock.now += estimated_seconds("hello there") + 0.01
    assert not backend.is_speaking()
    backend.speak("again")
    backend.stop()
    assert not backend.is_speaking()
