"""Fake speech backend for tests: records what would be spoken. This is inspired by Jim Kitchen.

Like the real engines it is measured against (fixesforgames B-X3): texts queue one after the other, each "plays" for
seconds_per_char * len(text), stop drops everything at once, and wait_until_done returns when the last one has played.
With takes_roles=True it behaves like the SAPI 5 backend for speakers (nfl4 S7.1): it is given the speaker and the rate
step of every text and records them; otherwise it is like NVDA and JAWS, which ignore speakers.
"""
from __future__ import annotations

import threading
import time

from .backend import SpeechBackend


class FakeBackend(SpeechBackend):
    """Each spoken text 'plays' for seconds_per_char * len(text); events are recorded in order."""

    def __init__(self, name="fake", available=True, seconds_per_char=0.0, fail_speak=False, takes_roles=False,
                 clock=time.monotonic, sleep=time.sleep):
        self.name = name
        self.available = available
        self.seconds_per_char = seconds_per_char
        self.fail_speak = fail_speak
        self.takes_roles = takes_roles
        self.events: list[tuple[str, str]] = []  # ("speak", text), ("stop", ""), ("wait", ""), settings
        self.said: list[tuple[str, str | None, int]] = []   # (text, speaker, rate step) of every text taken
        self.genders: dict[str, str] = {}   # speaker -> the Gender attribute of its voice (role_details)
        self.role_voices: dict[str, str] = {}   # speaker -> the voice id it resolves to (set_role_voice, role_details)
        self._end = 0.0
        self._lock = threading.Lock()
        self._clock = clock
        self._sleep = sleep

    def is_available(self) -> bool:
        return self.available

    def speak(self, text: str, role: str | None = None, rate_step: int = 0) -> bool:
        if self.fail_speak:
            return False
        with self._lock:
            self.events.append(("speak", text))
            self.said.append((text, role, rate_step))
            self._end = max(self._clock(), self._end) + self.seconds_per_char * len(text)
        return True

    def stop(self) -> None:
        with self._lock:
            self.events.append(("stop", ""))
            self._end = 0.0

    def wait_until_done(self, abort=None) -> None:
        self.events.append(("wait", ""))
        while self._clock() < self._end:
            if abort is not None and abort.is_set():
                return
            self._sleep(0.001)

    def is_speaking(self) -> bool:
        return self._clock() < self._end

    def set_rate(self, rate):
        self.events.append(("rate", rate))

    def set_volume(self, volume):
        self.events.append(("volume", volume))

    def set_pitch(self, pitch):
        self.events.append(("pitch", pitch))

    def set_voice(self, voice_id):
        self.events.append(("voice", voice_id))
        self.voice_id = voice_id or ""

    def set_role_voice(self, role, voice_id):
        self.events.append(("role_voice", f"{role}={voice_id or ''}"))
        if voice_id:
            self.role_voices[role] = voice_id
        else:
            self.role_voices.pop(role, None)

    def set_role_volume(self, role, volume):
        self.events.append(("role_volume", f"{role}={volume}"))

    def role_details(self, role, timeout=3.0):
        from .sapi5 import VoiceDetails
        voice_id = self.role_voices.get(role, f"token-{role}")
        return VoiceDetails(voice_id, f"voice of {role}", self.genders.get(role, ""))

    def spoken(self) -> list[str]:
        return [text for kind, text in self.events if kind == "speak"]
