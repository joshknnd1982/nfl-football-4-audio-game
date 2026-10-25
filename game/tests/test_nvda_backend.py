"""NVDA backend with a fake controller DLL (never speaks). This is inspired by Jim Kitchen.

The fake DLL behaves as the real one was measured on the owner's NVDA (2026-10-13): speakSsml with
asynchronous=False returns when the speech has ended, or at once with code 1223 when cancelSpeech is called from
another thread; asynchronous=True returns at once.
"""
import threading
import time

import pytest

import nfl4.speech.nvda as nvda_module
from nfl4.speech.nvda import ERROR_CANCELLED, RPC_S_UNKNOWN_IF, NvdaBackend, estimated_seconds, has_words


class Func:
    def __init__(self, impl):
        self.impl = impl
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.impl(*args)


class FakeDll:
    def __init__(self, running=True, ssml_code=0, speech_seconds=0.1):
        self.running = running
        self.ssml_code = ssml_code
        self.speech_seconds = speech_seconds       # how long NVDA "speaks" a blocking call
        self.cancelled = threading.Event()
        self.open_calls = 0
        self.stale_cancel = False                   # real NVDA: a cancel with no call open kills the NEXT blocking call
        self.calls = []
        self.lock = threading.Lock()
        self.nvdaController_testIfRunning = Func(lambda: 0 if self.running else 1753)
        self.nvdaController_speakText = Func(self._speak_text)
        self.nvdaController_cancelSpeech = Func(self._cancel)
        self.nvdaController_brailleMessage = Func(lambda m: self._log(("braille", m)) or 0)
        self.nvdaController_speakSsml = Func(self._speak_ssml)

    def _log(self, entry):
        with self.lock:
            self.calls.append(entry)

    def _cancel(self):
        self._log(("cancel",))
        if self.open_calls == 0:
            self.stale_cancel = True
        self.cancelled.set()
        return 0

    def _speak_text(self, text):
        self._log(("text", text))
        return 0 if self.running else 1753

    def _speak_ssml(self, ssml, symbols, priority, asynchronous):
        self._log(("ssml", ssml, asynchronous))
        if self.ssml_code:
            return self.ssml_code
        if asynchronous:
            return 0
        if self.stale_cancel:
            self.stale_cancel = False
            return ERROR_CANCELLED                  # returns at once, says nothing
        self.cancelled.clear()
        self.open_calls += 1
        try:
            if self.cancelled.wait(self.speech_seconds):
                return ERROR_CANCELLED
            return 0
        finally:
            self.open_calls -= 1

    def ssml_texts(self):
        with self.lock:
            return [c[1] for c in self.calls if c[0] == "ssml"]


def make(dll):
    return NvdaBackend(path="fake.dll", loader=lambda path: dll)


def test_missing_dll_means_unavailable_and_silent():
    def fail(path):
        raise OSError("not found")
    backend = NvdaBackend(path="missing.dll", loader=fail)
    assert not backend.is_available()
    assert not backend.speak("x")
    backend.stop()
    backend.wait_until_done()


def test_not_running_means_unavailable():
    assert not make(FakeDll(running=False)).is_available()
    assert make(FakeDll()).is_available()


def test_text_is_spoken_by_a_blocking_call_with_escaped_ssml_and_no_mark():
    dll = FakeDll()
    backend = make(dll)
    assert backend.speak("a & b <c>")
    backend.wait_until_done()
    entry = [c for c in dll.calls if c[0] == "ssml"][0]
    assert entry[1] == "<speak>a &amp; b &lt;c&gt;</speak>" and entry[2] is False     # blocking: its return is the end


def test_the_wait_ends_when_nvda_finishes_not_at_the_estimate():
    """The bug: the wait used to run out the whole estimate (3 s for the 28 character playback prompt)."""
    backend = make(FakeDll(speech_seconds=0.15))
    text = " Press the space bar to stop. "
    backend.speak(text)
    start = time.monotonic()
    backend.wait_until_done()
    took = time.monotonic() - start
    assert 0.1 < took < 0.6 and estimated_seconds(text) > 2.5


def test_wait_with_nothing_spoken_returns_at_once():
    backend = make(FakeDll())
    start = time.monotonic()
    backend.wait_until_done()
    assert time.monotonic() - start < 0.05


def test_texts_are_spoken_one_after_the_other_in_order_and_the_wait_covers_all():
    dll = FakeDll(speech_seconds=0.1)
    backend = make(dll)
    for word in ("one", "two", "three"):
        backend.speak(word)
    start = time.monotonic()
    backend.wait_until_done()
    assert time.monotonic() - start > 0.25
    assert dll.ssml_texts() == ["<speak>one</speak>", "<speak>two</speak>", "<speak>three</speak>"]


def test_stop_cancels_the_open_call_drops_the_queue_and_ends_waits():
    dll = FakeDll(speech_seconds=10.0)
    backend = make(dll)
    backend.speak("a long sentence")
    backend.speak("never said")
    time.sleep(0.1)
    threading.Timer(0.05, backend.stop).start()
    start = time.monotonic()
    backend.wait_until_done()
    assert time.monotonic() - start < 1.0
    assert ("cancel",) in dll.calls
    time.sleep(0.2)
    assert dll.ssml_texts() == ["<speak>a long sentence</speak>"]          # the queued text was dropped


def test_speech_after_a_stop_is_spoken_normally():
    dll = FakeDll(speech_seconds=5.0)
    backend = make(dll)
    backend.speak("first")
    time.sleep(0.1)
    backend.stop()
    dll.speech_seconds = 0.05
    backend.speak("second")
    backend.wait_until_done()
    assert dll.ssml_texts() == ["<speak>first</speak>", "<speak>second</speak>"]


def test_a_call_that_never_returns_is_cancelled_after_the_estimate_plus_a_margin(monkeypatch):
    monkeypatch.setattr(nvda_module, "HANG_MARGIN_SECONDS", 0.1)
    monkeypatch.setattr(nvda_module, "estimated_seconds", lambda text: 0.1)
    dll = FakeDll(speech_seconds=60.0)
    backend = make(dll)
    backend.speak("stuck")
    start = time.monotonic()
    backend.wait_until_done()
    took = time.monotonic() - start
    assert 0.15 < took < 2.0 and ("cancel",) in dll.calls


def test_abort_ends_the_wait():
    backend = make(FakeDll(speech_seconds=10.0))
    backend.speak("x" * 200)
    abort = threading.Event()
    threading.Timer(0.05, abort.set).start()
    start = time.monotonic()
    backend.wait_until_done(abort)
    assert time.monotonic() - start < 0.5
    backend.stop()


def test_text_without_words_is_sent_as_asynchronous_ssml_and_waited_for_briefly():
    dll = FakeDll(speech_seconds=60.0)           # a blocking call would hang: it must not be made
    backend = make(dll)
    assert not has_words("#") and has_words("a1")
    backend.speak("#")
    start = time.monotonic()
    backend.wait_until_done()
    assert dll.calls[-1][2] is True
    assert 0.2 < time.monotonic() - start < 1.0


def test_old_nvda_falls_back_to_speak_text_and_waits_the_estimate():
    dll = FakeDll(ssml_code=RPC_S_UNKNOWN_IF)
    backend = make(dll)
    assert backend.speak("hi")
    start = time.monotonic()
    backend.wait_until_done()
    assert ("text", "hi") in dll.calls
    assert abs((time.monotonic() - start) - estimated_seconds("hi")) < 0.15
    backend.speak("again")
    backend.wait_until_done()
    assert ("text", "again") in dll.calls
    assert sum(1 for c in dll.calls if c[0] == "ssml") == 1                  # SSML not retried


def test_a_failing_call_makes_nvda_unavailable_for_a_moment_so_the_manager_falls_back():
    dll = FakeDll(ssml_code=5)
    backend = make(dll)
    backend.speak("hello")
    backend.wait_until_done()
    assert not backend.is_available()


def test_close_stops_the_worker_and_refuses_new_speech():
    dll = FakeDll(speech_seconds=5.0)
    backend = make(dll)
    backend.speak("hello")
    time.sleep(0.1)
    backend.close()
    assert not backend.speak("more")
    assert ("cancel",) in dll.calls


def test_braille():
    dll = FakeDll()
    make(dll).braille("Brain")
    assert ("braille", "Brain") in dll.calls


def test_a_stop_while_nothing_is_speaking_sends_no_cancel_so_no_stale_cancel_is_left():
    """The game stops speech at start and on keys: an idle cancel made NVDA end the next wait at once (owner bug)."""
    dll = FakeDll(speech_seconds=0.15)
    backend = make(dll)
    backend.stop()
    backend.stop()
    assert ("cancel",) not in dll.calls
    backend.speak(" Press the space bar to stop. ")
    start = time.monotonic()
    backend.wait_until_done()
    assert time.monotonic() - start > 0.1                       # it really waited for the speech
    assert dll.ssml_texts() == ["<speak> Press the space bar to stop. </speak>"]


def test_a_call_cancelled_at_once_by_nobody_is_made_again_and_waited_for():
    dll = FakeDll(speech_seconds=0.15)
    dll.stale_cancel = True                                      # a stale cancel from elsewhere
    backend = make(dll)
    backend.speak("hello there")
    start = time.monotonic()
    backend.wait_until_done()
    assert time.monotonic() - start > 0.1
    assert len(dll.ssml_texts()) == 2                            # the first call died at once, the second spoke


def test_stop_while_speaking_still_cancels_and_leaves_the_next_call_alone():
    dll = FakeDll(speech_seconds=5.0)
    backend = make(dll)
    backend.speak("a long sentence")
    time.sleep(0.1)
    backend.stop()
    time.sleep(0.1)
    assert ("cancel",) in dll.calls and not dll.stale_cancel
    dll.speech_seconds = 0.05
    backend.speak("next")
    backend.wait_until_done()
    assert dll.ssml_texts()[-1] == "<speak>next</speak>"


def test_closing_while_idle_leaves_no_stale_cancel_behind():
    dll = FakeDll()
    backend = make(dll)
    backend.speak("done soon")
    backend.wait_until_done()
    backend.close()
    assert ("cancel",) not in dll.calls and not dll.stale_cancel


def test_is_speaking_follows_our_calls_so_the_help_menus_wait_under_nvda():
    """nfl4 S7.4a: F5, F6 and F7 wait while the engine speaks (the original's RunningState = 2); under NVDA that is a
    call of ours in flight or queued, and a stop ends it."""
    dll = FakeDll(speech_seconds=10.0)
    backend = make(dll)
    assert not backend.is_speaking()
    backend.speak("a long sentence")
    assert backend.is_speaking()
    backend.stop()
    deadline = time.monotonic() + 2.0
    while backend.is_speaking() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not backend.is_speaking()
    backend.close()
