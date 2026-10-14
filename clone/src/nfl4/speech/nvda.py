"""NVDA speech backend through the NVDA controller client DLL. This is inspired by Jim Kitchen.

NVDA Controller Client 2026.2 (LGPL 2.1, NV Access, shipped unmodified in nvda_client/):
x86/nvdaControllerClient.dll for 32-bit builds, x64/ for 64-bit. Functions used (nvdaController.h):
testIfRunning, speakText, cancelSpeech, brailleMessage, and from API 2.0 (NVDA 2024.1+) speakSsml.
All return 0 on success, a Windows error code otherwise (1223 = the call was cancelled).

Waiting for speech (owner bug 2026-10-13: "a long silence after the prompt, before the sounds"):
NVDA has no "finished" call, but speakSsml with asynchronous=False returns exactly when NVDA has finished
speaking the text (TESTED on the owner's NVDA: 1.17 s for a prompt NVDA says in 1.0 s; cancelSpeech from another
thread makes the blocked call return 1223 at once; two blocked calls on two threads speak in order). The SSML mark
callback of the header cannot be used: it is an RPC callback that NVDA can deliver only while a blocking call is
open, and the first version used asynchronous calls, so no end mark ever arrived and every wait ran out its full
estimate (0.5 s + 0.09 s per character: 3 s for a 28 character prompt that takes 1 s).
A cancelSpeech sent while nothing is speaking leaves NVDA with a stale cancel: the NEXT blocking call returns 1223 after
a few milliseconds without speaking anything (TESTED: the game stops speech at start and on keys, so every wait then
ended at once and the sounds started over the prompt). So stop() cancels only when a call of ours is open or queued,
and a call that comes back 1223 although we cancelled nothing is made once more.
So every text with words is spoken by a worker thread that makes the blocking call, one text after the other, in the
order given. wait_until_done() waits until the worker has nothing in flight and nothing queued. stop() drops the
queue and cancels, which frees the blocked call. A call that never returns (NVDA stuck) is cancelled once it is
HANG_MARGIN_SECONDS past the estimate, so the game cannot wait for ever. Texts without a letter or digit (a lone "#")
are sent as asynchronous SSML, because a blocking call with nothing to say can hang for 301 s (S7.1 test).
Anything failing (DLL missing, NVDA not running or closing) makes is_available() False; the manager then falls back
to SAPI 5 silently (playbook 7.3).
"""
from __future__ import annotations

import collections
import ctypes
import logging
import os
import struct
import sys
import threading
import time
from xml.sax.saxutils import escape

from .backend import SpeechBackend

log = logging.getLogger(__name__)

SYMBOL_LEVEL_UNCHANGED = -1
SPEECH_PRIORITY_NORMAL = 0
RPC_S_UNKNOWN_IF = 1717       # NVDA older than 2024.1: API 2.0 functions missing
ERROR_CANCELLED = 1223        # a blocking call ended by cancelSpeech
HANG_MARGIN_SECONDS = 2.0     # a blocking call still open this long after the estimate is cancelled
NO_WORDS_HOLD_SECONDS = 0.3   # what the wait allows for a text with nothing to say
STALE_CANCEL_SECONDS = 0.25   # a call cancelled this quickly although we cancelled nothing met a stale cancel
UNAVAILABLE_AFTER_FAILURE = 2.0


def dll_path() -> str:
    """The controller DLL matching this process's bitness, from the source tree or a frozen build."""
    arch = "x64" if struct.calcsize("P") == 8 else "x86"
    base = getattr(sys, "_MEIPASS", None)
    root = os.path.join(base, "nfl4", "speech") if base else os.path.dirname(__file__)
    return os.path.join(root, "nvda_client", arch, "nvdaControllerClient.dll")


def estimated_seconds(text: str) -> float:
    """Upper guess for how long NVDA takes to say text: only the limit for a call that does not return, and the
    wait for old NVDA versions that cannot report the end of speech."""
    return min(30.0, 0.5 + 0.09 * len(text.strip()))


def has_words(text: str) -> bool:
    return any(ch.isalnum() for ch in text)


class NvdaBackend(SpeechBackend):
    name = "NVDA"

    def __init__(self, path: str | None = None, loader=ctypes.WinDLL, clock=time.monotonic):
        self._path = path or dll_path()
        self._loader = loader
        self._clock = clock
        self._dll = None
        self._load_failed = False
        self._lock = threading.Lock()                 # loading the DLL
        self._ssml_ok = True
        self._cv = threading.Condition()
        self._queue: collections.deque = collections.deque()    # (generation, text)
        self._generation = 0
        self._in_flight: tuple[str, float] | None = None        # (text, when the blocking call began)
        self._hold_until = 0.0                        # end of speech that cannot be waited for call by call
        self._worker: threading.Thread | None = None
        self._closed = False
        self._failed_until = 0.0

    # ----- DLL ----------------------------------------------------------------------
    def _load(self):
        if self._dll is not None or self._load_failed:
            return self._dll
        with self._lock:
            if self._dll is None and not self._load_failed:
                try:
                    dll = self._loader(self._path)
                    dll.nvdaController_testIfRunning.restype = ctypes.c_ulong
                    dll.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
                    dll.nvdaController_speakText.restype = ctypes.c_ulong
                    dll.nvdaController_cancelSpeech.restype = ctypes.c_ulong
                    dll.nvdaController_brailleMessage.argtypes = [ctypes.c_wchar_p]
                    dll.nvdaController_brailleMessage.restype = ctypes.c_ulong
                    try:
                        dll.nvdaController_speakSsml.argtypes = [ctypes.c_wchar_p, ctypes.c_int,
                                                                 ctypes.c_int, ctypes.c_bool]
                        dll.nvdaController_speakSsml.restype = ctypes.c_ulong
                    except (AttributeError, OSError):
                        self._ssml_ok = False
                    self._dll = dll
                    log.info("NVDA controller client loaded from %s", self._path)
                except Exception as exc:
                    self._load_failed = True
                    log.warning("NVDA controller client not usable (%s): %s", self._path, exc)
        return self._dll

    def _call(self, name: str, *args) -> int:
        dll = self._load()
        if dll is None:
            return -1
        try:
            return int(getattr(dll, name)(*args))
        except Exception as exc:
            log.warning("NVDA %s failed: %s", name, exc)
            return -1

    # ----- SpeechBackend -----------------------------------------------------------
    def is_available(self) -> bool:
        if self._clock() < self._failed_until:
            return False
        return self._call("nvdaController_testIfRunning") == 0

    def speak(self, text: str) -> bool:
        log.debug("NVDA speak %r", text)         # NFL4_DEBUG=1: the timing tools read this
        if self._load() is None:
            return False
        with self._cv:
            if self._closed:
                return False
            self._queue.append((self._generation, text))
            if self._worker is None:
                self._worker = threading.Thread(target=self._run, name="nvda-speech", daemon=True)
                self._worker.start()
            self._cv.notify_all()
        return True

    def stop(self) -> None:
        with self._cv:
            speaking = self._in_flight is not None or bool(self._queue) or self._clock() < self._hold_until
            self._generation += 1                # whatever is queued is dropped, whatever is in flight is cancelled
            self._queue.clear()
            self._hold_until = 0.0
            self._cv.notify_all()
        if speaking:                             # an idle cancel would leave a stale cancel that kills the next call
            self._call("nvdaController_cancelSpeech")

    def wait_until_done(self, abort: threading.Event | None = None) -> None:
        stuck = False
        with self._cv:
            while True:
                if abort is not None and abort.is_set():
                    return
                now = self._clock()
                in_flight = self._in_flight
                if in_flight is None and not self._queue and now >= self._hold_until:
                    return
                if in_flight is not None and now - in_flight[1] > estimated_seconds(in_flight[0]) + HANG_MARGIN_SECONDS:
                    stuck = True
                    break
                self._cv.wait(0.02)
        if stuck:
            log.warning("NVDA did not finish speaking in time; cancelling it")
            self.stop()

    def braille(self, message: str) -> None:
        self._call("nvdaController_brailleMessage", message)

    def close(self) -> None:
        with self._cv:
            speaking = self._in_flight is not None or bool(self._queue)
            self._closed = True
            self._generation += 1
            self._queue.clear()
            self._cv.notify_all()
        if speaking and self._dll is not None:       # an idle cancel would be left behind for the next program that calls NVDA
            self._call("nvdaController_cancelSpeech")

    # ----- the worker: one blocking call after the other ---------------------------------
    def _run(self) -> None:
        while True:
            with self._cv:
                while not self._queue and not self._closed:
                    self._cv.wait()
                if self._closed:
                    return
                generation, text = self._queue.popleft()
                if generation != self._generation:
                    continue
                if has_words(text) and self._ssml_ok:
                    self._in_flight = (text, self._clock())
            try:
                self._speak_one(text, generation)
            except Exception as exc:               # a worker must never die
                log.warning("NVDA speech failed: %s", exc)
            with self._cv:
                self._in_flight = None
                self._cv.notify_all()

    def _speak_one(self, text: str, generation: int = 0) -> None:
        if self._ssml_ok:
            ssml = f"<speak>{escape(text)}</speak>"
            blocking = has_words(text)
            for attempt in (1, 2):
                began = self._clock()
                code = self._call("nvdaController_speakSsml", ssml, SYMBOL_LEVEL_UNCHANGED,
                                  SPEECH_PRIORITY_NORMAL, not blocking)
                log.debug("NVDA speakSsml (%s) returned %s after %.2f s", "blocking" if blocking else "async", code,
                          self._clock() - began)
                stale = (blocking and code == ERROR_CANCELLED and generation == self._generation
                         and self._clock() - began < STALE_CANCEL_SECONDS)
                if not stale or attempt == 2:
                    break
                log.debug("NVDA call was cancelled by nobody: a stale cancel, asking again")
            if code == RPC_S_UNKNOWN_IF:
                self._ssml_ok = False              # older NVDA: plain text from now on, waited for by estimate
            elif code in (0, ERROR_CANCELLED):
                if not blocking:
                    self._hold(NO_WORDS_HOLD_SECONDS)
                return
            else:
                self._note_failure("speakSsml", code)
                return
        code = self._call("nvdaController_speakText", text)
        if code == 0:
            self._hold(estimated_seconds(text))
        else:
            self._note_failure("speakText", code)

    def _hold(self, seconds: float) -> None:
        with self._cv:
            self._hold_until = max(self._clock(), self._hold_until) + seconds

    def _note_failure(self, what: str, code: int) -> None:
        log.warning("NVDA %s returned %s; using the other speech engine for a moment", what, code)
        self._failed_until = self._clock() + UNAVAILABLE_AFTER_FAILURE
