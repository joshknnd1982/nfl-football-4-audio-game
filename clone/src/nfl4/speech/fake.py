"""Fake speech backend for tests: records what would be spoken. This is inspired by Jim Kitchen's Brain."""
from __future__ import annotations

import threading
import time

from .backend import SpeechBackend


class FakeBackend(SpeechBackend):
    """Each spoken text 'plays' for seconds_per_char * len(text); events are recorded in order."""

    def __init__(self, name="fake", available=True, seconds_per_char=0.0, fail_speak=False):
        self.name = name
        self.available = available
        self.seconds_per_char = seconds_per_char
        self.fail_speak = fail_speak
        self.events: list[tuple[str, str]] = []  # ("speak", text), ("stop", ""), ("wait", "")
        self._end = 0.0
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return self.available

    def speak(self, text: str) -> bool:
        if self.fail_speak:
            return False
        with self._lock:
            self.events.append(("speak", text))
            self._end = max(time.monotonic(), self._end) + self.seconds_per_char * len(text)
        return True

    def stop(self) -> None:
        with self._lock:
            self.events.append(("stop", ""))
            self._end = 0.0

    def wait_until_done(self, abort=None) -> None:
        self.events.append(("wait", ""))
        while time.monotonic() < self._end:
            if abort is not None and abort.is_set():
                return
            time.sleep(0.001)

    def set_rate(self, rate):
        self.events.append(("rate", rate))

    def set_volume(self, volume):
        self.events.append(("volume", volume))

    def set_pitch(self, pitch):
        self.events.append(("pitch", pitch))

    def set_voice(self, voice_id):
        self.events.append(("voice", voice_id))
        self.voice_id = voice_id or ""

    def spoken(self) -> list[str]:
        return [text for kind, text in self.events if kind == "speak"]
