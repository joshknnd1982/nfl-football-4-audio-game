"""Speech backend interface. This is inspired by Jim Kitchen.

Every speech engine (SAPI 5, NVDA, a test fake, later Speech Dispatcher on Linux)
offers the same small set of calls, so the rest of the game never touches COM or DLLs
(playbook 7.2 portability seam).
"""
from __future__ import annotations

import threading
from abc import ABC, abstractmethod


class SpeechBackend(ABC):
    """One speech engine. All methods may be called from any thread and never raise."""

    name = "backend"

    @abstractmethod
    def is_available(self) -> bool:
        """True when the engine can speak right now."""

    @abstractmethod
    def speak(self, text: str) -> bool:
        """Queue text after any speech already playing, return at once. False on failure."""

    @abstractmethod
    def stop(self) -> None:
        """Stop all speech at once and drop anything queued."""

    @abstractmethod
    def wait_until_done(self, abort: threading.Event | None = None) -> None:
        """Block until everything queued has been spoken, or abort is set."""

    # Settings of engines that have them (SAPI 5); the defaults do nothing (NVDA, test fakes).
    voice_name = ""     # the voice in use
    voice_id = ""
    base_rate = 0       # the voice's own rate, which "default" restores

    def set_rate(self, rate: int | None) -> None:
        """None restores the engine's own rate."""

    def set_volume(self, volume: int) -> None:
        pass

    def set_pitch(self, pitch: int) -> None:
        pass

    def set_voice(self, voice_id: str | None) -> None:
        """None selects the engine's first voice."""

    def close(self) -> None:
        """Release the engine. Safe to call twice."""
