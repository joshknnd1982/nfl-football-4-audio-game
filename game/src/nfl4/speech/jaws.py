"""JAWS speech backend through Freedom Scientific's COM interface. This is inspired by Jim Kitchen.

Nothing is bundled: the player's own installed JAWS provides FSAPI.dll and registers the COM class
FreedomSci.JawsApi (both the 64-bit and the 32-bit registration exist on a JAWS 2026 PC, so a 32-bit
and a 64-bit Brain both work). The interface was read from the type library on the owner's PC
(IJawsApi, TESTED 2026-10-13, tools/JAWS_GUIDE.md): RunScript(name), SayString(text, flush),
StopSpeech(), Enable(noDDIHooks), Disable(), RunFunction(name). Only SayString is used: StopSpeech has no effect on
JAWS 2026, so stop() is SayString(" ", flush=True).

- SayString(text, False) queues the text after what JAWS is saying; it returns True when JAWS is running
  and took the text, False when JAWS is not running (TESTED without JAWS: False, no error).
- There is no "finished speaking" call and no callback. The wait of Brain's blocking say() therefore
  uses an estimate from the text length (like NVDA's fallback), and the owner tunes it with real JAWS.
- Anything failing (class not registered, JAWS not running, JAWS closing, a COM error) makes
  is_available() False or speak() False; the manager then falls back to SAPI 5 silently. Never raises.
- COM objects belong to the thread that made them (apartment threading), so each thread that speaks
  makes its own.
"""
from __future__ import annotations

import ctypes
import logging
import threading
import time

from ..data import debuglog
from .backend import SpeechBackend

log = logging.getLogger(__name__)

PROG_ID = "FreedomSci.JawsApi"
WINDOW_CLASS = "JFWUI2"          # JAWS's main window class (SECONDARY: accessible_output2); the probe covers a miss
AVAILABLE_CACHE_SECONDS = 0.3    # the manager asks is_available() right before every speak()
STOP_MARGIN_SECONDS = 1.5        # the wait estimate may be short for a slow JAWS voice: still cut this long after it
EARLY_SHARE = 0.5                # a key waiting ends a wait once this share of the guess has passed (the fastest rate measured is
#                                  about half the guess's; 2026-10-23, the owner: "with Jaws, speech is laggy when I press arrow and other keys")


def estimated_seconds(text: str) -> float:
    """How long JAWS probably takes to say text; JAWS reports no end of speech, so the wait is a guess.

    Measured 2026-10-13 on the owner's JAWS by loopback capture (tools/jaws_duration_check.py): 0.02 to 0.045 s per
    character (0.65 s for 28 characters, 1.33 s for 59), speech starts 0.05 to 0.1 s after the command. The first guess
    (0.08 s + 0.024 s per character) left a silent gap of 0.5 s before the sounds of every playback; the fit is now
    0.08 s + 0.024 s per character (0.75 s for the 28 character playback prompt). Long texts with digits run slower
    than this and overlap what follows a little; the F3 setting "sounds start right away" removes the wait entirely.
    """
    return min(30.0, 0.08 + 0.024 * len(text.strip()))


def _make_com():
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()     # no-op when this thread already did it
    return win32com.client.Dispatch(PROG_ID)


def _window_open() -> bool:
    try:
        return bool(ctypes.windll.user32.FindWindowW(WINDOW_CLASS, None))
    except Exception as exc:
        log.debug("looking for the JAWS window failed: %s", exc)
        return False


class JawsBackend(SpeechBackend):
    name = "JAWS"

    def __init__(self, factory=_make_com, window_open=_window_open, clock=time.monotonic):
        self._factory = factory
        self._window_open = window_open
        self._clock = clock
        self._local = threading.local()
        self._broken = False          # the COM class cannot be made at all (JAWS not installed): stop trying
        self._cv = threading.Condition()
        self._deadline = 0.0
        self._early = 0.0             # the earliest end of our speech (EARLY_SHARE of the guess): a key waiting may end a wait from then
        self._flush_next = False      # the next text interrupts JAWS (set by stop(): the game stops the speech on every key)
        self.key_waiting = None       # a callable: True when a key is waiting for the game (app.py sets it to KeyInput.key_waiting)
        self._checked_at = -1e9
        self._checked = False

    # ----- COM ------------------------------------------------------------------------
    def _object(self):
        obj = getattr(self._local, "obj", None)
        if obj is None and not self._broken:
            try:
                obj = self._factory()
                self._local.obj = obj
            except Exception as exc:
                self._broken = True
                log.info("JAWS interface not available (%s): %s", PROG_ID, exc)
        return obj

    def _call(self, method: str, *args):
        """One COM call. Returns its result, or None when it could not be made."""
        obj = self._object()
        if obj is None:
            return None
        try:
            return getattr(obj, method)(*args)
        except Exception as exc:       # JAWS closing, RPC gone: drop the object, make a new one next time
            self._local.obj = None
            log.info("JAWS %s failed: %s", method, exc)
            return None

    def describe(self, running: bool = False) -> dict:
        """What the startup report says about JAWS: is its COM class registered, and (only when JAWS runs, so that nothing
        is started by looking) does the COM object answer."""
        try:
            import winreg
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, PROG_ID))
            installed = "yes, %s is registered" % PROG_ID
        except OSError:
            installed = "no, %s is not registered" % PROG_ID
        if not running:
            return {"installed": installed, "com": "not probed (JAWS is not running)"}
        com = "the COM object was made" if self._object() is not None else "the COM object could not be made"
        return {"installed": installed, "com": com}

    # ----- SpeechBackend ---------------------------------------------------------------
    def is_available(self) -> bool:
        now = self._clock()
        if now - self._checked_at < AVAILABLE_CACHE_SECONDS:
            return self._checked
        up = False
        try:
            up = bool(self._window_open()) or bool(self._call("SayString", "", False))
        except Exception:
            up = False
        self._checked, self._checked_at = up, now
        return up

    def speak(self, text: str) -> bool:
        if not text.strip():
            return True
        flush, self._flush_next = self._flush_next, False
        if not bool(self._call("SayString", text, flush)):
            self._checked_at = -1e9           # ask again next time
            return False
        log.debug("JAWS speak %r flush=%s", text, flush)       # NFL4_DEBUG=1: lets the exe smoke test see what JAWS was given
        with self._cv:
            now = self._clock()
            guess = estimated_seconds(text)
            if flush:                         # JAWS dropped what it was saying: our speech starts now
                self._early, self._deadline = now + guess * EARLY_SHARE, now + guess
            else:                             # queued after what we said before
                self._early = max(now, self._early) + guess * EARLY_SHARE
                self._deadline = max(now, self._deadline) + guess
        return True

    def stop(self) -> None:
        """Cut Brain's speech. StopSpeech does nothing on JAWS 2026 (TESTED by loopback, 2026-10-13: the old item
        played to its natural end, 1.9 s later, so arrowing through a menu lagged by whole items). A flushed
        SayString of a space cuts the speech in about 80 ms and says nothing. Only when Brain's own speech may still
        be playing: the game calls stop() on every key, and JAWS's unrelated speech is not ours to cut."""
        with self._cv:
            playing = self._clock() < self._deadline + STOP_MARGIN_SECONDS
            self._deadline = 0.0
            self._early = 0.0
            self._flush_next = True       # the game's next text interrupts whatever JAWS says then, its own echo of the key too
            self._cv.notify_all()
        if playing:
            self._call("SayString", " ", True)

    def is_speaking(self) -> bool:
        """The original's RunningState = 2 (nfl4 S7.4a): JAWS gives no signal, so the estimated end of our speech."""
        with self._cv:
            return self._clock() < self._deadline

    def wait_until_done(self, abort: threading.Event | None = None) -> None:
        """Until the guessed end of our speech; a key waiting for the game ends it from the earliest end on (EARLY_SHARE): JAWS gives no
        end of speech, and at a fast JAWS rate the guess is far too long, so without this every key waited for it (2026-10-23)."""
        key_waiting = self.key_waiting
        with self._cv:
            while True:
                if abort is not None and abort.is_set():
                    return
                now = self._clock()
                left = self._deadline - now
                if left <= 0:
                    return
                if key_waiting is not None and now >= self._early:
                    try:
                        waiting = bool(key_waiting())
                    except Exception:
                        waiting = False
                    if waiting:
                        debuglog.event("speech", "jaws_wait_ended_by_key", left_ms=round(left * 1000))
                        return
                self._cv.wait(min(left, 0.02))

    def close(self) -> None:
        self._local.obj = None
