"""Speech manager: the only speech entry point the game uses. This is inspired by Jim Kitchen.

The original spoke in three ways on one SAPI voice (GAME_SPEC 7 item 1, 9.1; GAP_REGISTER G-S1):
  flags 0, synchronous (say, say3, say4)      speak and wait until EVERYTHING queued is spoken -> SpeechManager.say
  flags 1, asynchronous (say2, say5, say6)     queue after current speech, go on                 -> SpeechManager.say_async
  flags 2 with "" (stopspeech)                  purge at once                                     -> SpeechManager.stop
nfl4 S7.1 (D-031 items 1 and 3): every call names its speaker (`role`: the announcer, a quarterback or a punter,
speech/roles.py). The SAPI 5 engine speaks each text with that speaker's voice and volume in ONE queue, so a synchronous
line is a barrier for everything queued before it and nothing is cut by a voice change. NVDA and JAWS ignore the
speaker (the screen reader's own voice speaks everything). `rate_step` speaks one text faster (banter line 113, Q38);
only SAPI 5 applies it. The rate counter vr (set_rate) reaches only SAPI 5: with NVDA or JAWS it changes only the game's
pauses and the number it speaks (G-S4).

Output modes (playbook 7.2, 7.3.1): "auto" (nfl4's default since SZ.4, D-109, after a player's e-mail: NVDA if it runs, else
JAWS if it runs, else SAPI 5; the program asks once whether to speak through the screen reader it found), "sapi" (G-S7: the
five voices of the game, as the original always spoke), "nvda" (NVDA, else SAPI 5) and "jaws" (JAWS, else SAPI 5). Whatever the mode, if the chosen engine is missing or fails, another one is
used, so the game is never silent and never crashes; every engine call is guarded here (fixesforgames B-X2).
"""
from __future__ import annotations

import logging
import threading
import time

from ..data import debuglog
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
        self.last_role: str | None = None     # the speaker of the last text (the original's say6 speaks with it)

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        if value in MODES:
            self.stop()
            debuglog.event("speech", "mode", old=self._mode, new=value)
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

    def active_engine(self) -> SpeechBackend | None:
        """The engine that would speak the next text: the first available one in the mode's order."""
        for backend in self._order():
            try:
                if backend.is_available():
                    return backend
            except Exception as exc:
                log.warning("%s availability check failed: %s", backend.name, exc, exc_info=exc)
        return None

    def _send(self, text: str, role: str | None, rate_step: int) -> SpeechBackend | None:
        """Queue text on the first engine that takes it. Returns that engine."""
        self.last_role = role
        began = time.perf_counter()
        skipped = []
        for i, backend in enumerate(self._order()):
            try:
                if not backend.is_available():
                    skipped.append(backend.name)
                    continue
                if getattr(backend, "takes_roles", False):
                    taken = backend.speak(text, role=role, rate_step=rate_step)
                else:
                    taken = backend.speak(text)
                if taken:
                    if i and not self._fallback_logged:
                        self._fallback_logged = True
                        log.warning("speech mode %s: preferred engine unavailable, using %s",
                                    self._mode, backend.name)
                    self._log_request(backend, text, role, rate_step, began, skipped)
                    return backend
                skipped.append(backend.name + " refused")
            except Exception as exc:  # backends should not raise; be safe anyway
                log.warning("%s speak failed: %s", backend.name, exc, exc_info=exc)
                skipped.append(backend.name + " raised")
        log.warning("no speech engine could say %r (tried: %s)", text, ", ".join(skipped) or "none")
        return None

    @staticmethod
    def _log_request(backend, text, role, rate_step, began, skipped) -> None:
        """The log line of a text an engine took. Whatever goes wrong while it is written (an engine whose queue_length raises, a log
        that fails) is not a refusal: the text is spoken already and must not be offered to the next engine (S8.3, fixesforgames B-P118)."""
        try:
            queued = backend.queue_length() if hasattr(backend, "queue_length") else None
        except Exception as exc:
            log.debug("%s queue_length failed: %s", backend.name, exc)
            queued = None
        try:
            debuglog.event("speech", "request", role=role, rate_step=rate_step or None, backend=backend.name,
                           accepted_ms=round((time.perf_counter() - began) * 1000, 2), tried_first=skipped or None,
                           chars=len(text), queued=queued,
                           text="<typed echo>" if debuglog.typing_now() and len(text.strip()) <= 3 else text)
        except Exception as exc:
            log.debug("the log line of a speech request failed: %s", exc)

    def say(self, text: str, abort: threading.Event | None = None, *, role: str | None = None,
            rate_step: int = 0) -> None:
        """Speak and wait until everything queued is spoken (the original's say). abort ends the wait early."""
        backend = self._send(text, role, rate_step)
        if backend is not None:
            began = time.perf_counter()
            previous = debuglog.state()
            debuglog.set_state("speech wait (%s)" % backend.name)
            try:
                backend.wait_until_done(abort)
            except Exception as exc:  # a dying engine must not turn a wait into a program error
                log.warning("%s wait failed: %s", backend.name, exc, exc_info=exc)
            finally:
                debuglog.set_state(previous)
                debuglog.beat()
                debuglog.event("speech", "ended", backend=backend.name, waited_ms=round((time.perf_counter() - began) * 1000),
                               aborted=bool(abort is not None and abort.is_set()) or None)

    def say_async(self, text: str, *, role: str | None = None, rate_step: int = 0) -> None:
        """Queue after current speech and return at once (the original's say2)."""
        self._send(text, role, rate_step)

    def stop(self) -> None:
        """Stop speech at once (the original's stopspeech), on every engine."""
        debuglog.event("speech", "stop")
        for backend in (self.sapi, self.nvda, self.jaws):
            if backend is not None:
                try:
                    backend.stop()
                except Exception as exc:
                    log.warning("%s stop failed: %s", backend.name, exc, exc_info=exc)

    def is_speaking(self) -> bool:
        """True while the engine in use still has speech queued or playing (the original's RunningState = 2)."""
        backend = self.active_engine()
        try:
            return bool(backend is not None and getattr(backend, "is_speaking", lambda: False)())
        except Exception as exc:
            log.warning("%s speaking check failed: %s", getattr(backend, "name", "?"), exc, exc_info=exc)
            return False

    # ----- settings (clone additions): passed to SAPI 5, the one engine that has them -----

    def _on_sapi(self, what: str, call, default=None):
        """One call to the SAPI 5 engine; a failing engine is logged, never raised into the game."""
        if self.sapi is None:
            return default
        try:
            return call(self.sapi)
        except Exception as exc:
            log.warning("sapi %s failed: %s", what, exc, exc_info=exc)
            return default

    def set_rate(self, rate: int | None) -> None:
        self._on_sapi("set_rate", lambda s: s.set_rate(rate))

    def set_volume(self, volume: int) -> None:
        self._on_sapi("set_volume", lambda s: s.set_volume(volume))

    def set_pitch(self, pitch: int) -> None:
        self._on_sapi("set_pitch", lambda s: s.set_pitch(pitch))

    def set_voice(self, voice_id: str | None) -> None:
        self._on_sapi("set_voice", lambda s: s.set_voice(voice_id))

    def set_role_voice(self, role: str, voice_id: str | None) -> None:
        self._on_sapi("set_role_voice", lambda s: s.set_role_voice(role, voice_id))

    def set_role_volume(self, role: str, volume: int) -> None:
        self._on_sapi("set_role_volume", lambda s: s.set_role_volume(role, volume))

    def set_role_effect(self, role: str, effect: str | None) -> None:
        self._on_sapi("set_role_effect", lambda s: s.set_role_effect(role, effect))

    def role_details(self, role: str):
        """The id, name and Gender attribute of a speaker's SAPI voice (None when SAPI 5 is not running)."""
        return self._on_sapi("role_details", lambda s: s.role_details(role))

    def role_gender(self, role: str) -> str:
        """The Gender attribute of the voice that speaks for `role` now: the SAPI voice's when SAPI 5 speaks, "" with
        NVDA or JAWS (so GetSexOf says " He ", G-S6)."""
        if self.sapi is None or self.active_engine() is not self.sapi:
            return ""
        details = self.role_details(role)
        return details.gender if details is not None else ""

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

    def watch_voice_trials(self, arm, clear) -> None:
        """The crash guard for every voice (playbook 7.4.5): arm(voice_id) before SAPI 5 opens or probes a voice,
        clear(voice_id) when that voice has made or spoken its first text."""
        if self.sapi is not None:
            if hasattr(self.sapi, "on_voice_trial"):
                self.sapi.on_voice_trial = arm
            if hasattr(self.sapi, "on_voice_proven"):
                self.sapi.on_voice_proven = clear

    def screen_reader_speaks(self) -> bool:
        """NVDA or JAWS, not SAPI 5, would speak the next text: the game's own voices are not used then (SZ.4, D-109)."""
        engine = self.active_engine()
        return engine is not None and not getattr(engine, "takes_roles", False)

    def nvda_running(self) -> bool:
        try:
            return self.nvda is not None and bool(self.nvda.is_available())
        except Exception as exc:
            log.warning("nvda availability check failed: %s", exc, exc_info=exc)
            return False

    def jaws_running(self) -> bool:
        try:
            return self.jaws is not None and bool(self.jaws.is_available())
        except Exception as exc:
            log.warning("jaws availability check failed: %s", exc, exc_info=exc)
            return False

    def screen_reader_message(self, text: str) -> bool:
        """Say text through NVDA, else JAWS, if one runs (used when SAPI 5 has no voices, GAP_REGISTER G-F9)."""
        for backend in (self.nvda, self.jaws):
            try:
                if backend is not None and backend.is_available() and backend.speak(text):
                    return True
            except Exception as exc:
                log.warning("%s message failed: %s", getattr(backend, "name", "?"), exc, exc_info=exc)
        return False

    def close(self) -> None:
        for backend in (self.sapi, self.nvda, self.jaws):
            if backend is not None:
                try:
                    backend.close()
                except Exception as exc:
                    log.warning("%s close failed: %s", backend.name, exc, exc_info=exc)
