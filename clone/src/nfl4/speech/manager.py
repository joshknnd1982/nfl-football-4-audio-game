"""Speech manager: the only speech entry point the game uses. This is inspired by Jim Kitchen's Brain.

The original had three speech calls (GAME_SPEC 7, PROCEDURE_INDEX):
  say(text)    speak and wait until spoken            -> SpeechManager.say
  say2(text)   queue after current speech, go on      -> SpeechManager.say_async
  stopspeech   stop at once                           -> SpeechManager.stop

Output modes (playbook 7.2, 7.3.1): "sapi" (Brain's default: the original always used its SAPI voice),
"nvda" (NVDA, else SAPI 5), "jaws" (JAWS, else SAPI 5) and "auto" (NVDA if it runs, else JAWS if it runs,
else SAPI 5). Whatever the mode, if the chosen engine is missing or fails, another one is used, so the
game is never silent and never crashes.
"""
from __future__ import annotations

import logging
import threading

from .backend import SpeechBackend

log = logging.getLogger(__name__)

MODES = ("sapi", "nvda", "jaws", "auto")
MODE_NAMES = {"sapi": "SAPI 5 voice only", "nvda": "NVDA only", "jaws": "JAWS only", "auto": "automatic"}


class SpeechManager:
    def __init__(self, sapi: SpeechBackend | None, nvda: SpeechBackend | None, mode: str = "sapi",
                 jaws: SpeechBackend | None = None):
        self.sapi = sapi
        self.nvda = nvda
        self.jaws = jaws
        self._mode = mode if mode in MODES else "sapi"
        self._lock = threading.Lock()
        self._fallback_logged = False

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value in MODES:
            self.stop()
            self._mode = value

    def _order(self) -> list[SpeechBackend]:
        """Engines to try, preferred first."""
        if self._mode == "sapi":
            order = [self.sapi, self.nvda, self.jaws]
        elif self._mode == "nvda":
            order = [self.nvda, self.sapi]
        elif self._mode == "jaws":
            order = [self.jaws, self.sapi]
        else:  # "auto": NVDA when it runs, else JAWS when it runs, else SAPI 5 (playbook 7.3, 7.3.1)
            order = [self.nvda, self.jaws, self.sapi]
        return [b for b in order if b is not None]

    def _send(self, text: str) -> SpeechBackend | None:
        """Queue text on the first engine that takes it. Returns that engine."""
        for i, backend in enumerate(self._order()):
            try:
                if backend.is_available() and backend.speak(text):
                    if i and not self._fallback_logged:
                        self._fallback_logged = True
                        log.warning("speech mode %s: preferred engine unavailable, using %s",
                                    self._mode, backend.name)
                    return backend
            except Exception as exc:  # backends should not raise; be safe anyway
                log.warning("%s speak failed: %s", backend.name, exc)
        log.warning("no speech engine could say %r", text)
        return None

    def say(self, text: str, abort: threading.Event | None = None) -> None:
        """Speak and wait until spoken (the original's say). abort ends the wait early."""
        backend = self._send(text)
        if backend is not None:
            try:
                backend.wait_until_done(abort)
            except Exception as exc:  # a dying engine must not turn a wait into a program error
                log.warning("%s wait failed: %s", backend.name, exc)

    def say_async(self, text: str) -> None:
        """Queue after current speech and return at once (the original's say2)."""
        self._send(text)

    def stop(self) -> None:
        """Stop speech at once (the original's stopspeech), on every engine."""
        for backend in (self.sapi, self.nvda, self.jaws):
            if backend is not None:
                try:
                    backend.stop()
                except Exception as exc:
                    log.warning("%s stop failed: %s", backend.name, exc)

    # ----- settings menu (clone additions): passed to SAPI 5, the one engine that has them -----

    def _on_sapi(self, what: str, call, default=None):
        """One call to the SAPI 5 engine; a failing engine is logged, never raised into the game."""
        if self.sapi is None:
            return default
        try:
            return call(self.sapi)
        except Exception as exc:
            log.warning("sapi %s failed: %s", what, exc)
            return default

    def set_rate(self, rate: int | None) -> None:
        self._on_sapi("set_rate", lambda s: s.set_rate(rate))

    def set_volume(self, volume: int) -> None:
        self._on_sapi("set_volume", lambda s: s.set_volume(volume))

    def set_pitch(self, pitch: int) -> None:
        self._on_sapi("set_pitch", lambda s: s.set_pitch(pitch))

    def set_voice(self, voice_id: str | None) -> None:
        self._on_sapi("set_voice", lambda s: s.set_voice(voice_id))

    @property
    def voice_name(self) -> str:
        return self._on_sapi("voice_name", lambda s: s.voice_name, "")

    @property
    def voice_id(self) -> str:
        return self._on_sapi("voice_id", lambda s: s.voice_id, "")

    @property
    def base_rate(self) -> int:
        return self._on_sapi("base_rate", lambda s: s.base_rate, 0)

    def watch_voice_health(self, callback) -> None:
        """Call callback once, when the SAPI 5 voice has spoken something to the end (the crash guard's all clear)."""
        if self.sapi is not None and hasattr(self.sapi, "on_healthy"):
            self.sapi.on_healthy = callback

    def nvda_running(self) -> bool:
        try:
            return self.nvda is not None and bool(self.nvda.is_available())
        except Exception as exc:
            log.warning("nvda availability check failed: %s", exc)
            return False

    def jaws_running(self) -> bool:
        try:
            return self.jaws is not None and bool(self.jaws.is_available())
        except Exception as exc:
            log.warning("jaws availability check failed: %s", exc)
            return False

    def screen_reader_message(self, text: str) -> bool:
        """Say text through NVDA, else JAWS, if one runs (used when SAPI 5 has no voices, GAME_SPEC 15)."""
        for backend in (self.nvda, self.jaws):
            try:
                if backend is not None and backend.is_available() and backend.speak(text):
                    return True
            except Exception as exc:
                log.warning("%s message failed: %s", backend.name, exc)
        return False

    def close(self) -> None:
        for backend in (self.sapi, self.nvda, self.jaws):
            if backend is not None:
                try:
                    backend.close()
                except Exception:
                    pass
