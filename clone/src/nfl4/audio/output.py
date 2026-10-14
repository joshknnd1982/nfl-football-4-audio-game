"""Where finished sounds go: the mixer. This is inspired by Jim Kitchen's Brain.

Portability seam (playbook 7.2): the rest of the clone talks to `Output`. PygameOutput is the real
mixer (pygame-ce, SDL); TimedOutput makes no sound but keeps time, so it serves the tests and
the case where no sound device can be opened (the program then runs silently instead of ending
with an error as the original did, GAME_SPEC 15).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Protocol

from .render import MIX_RATE, STEREO_FRAME

log = logging.getLogger("nfl4.audio")

SLOT_COUNT = 9        # the nine playback slots, numbered 0..8 here (GAME_SPEC 5.1)
BEEP_SLOT = 9         # the tenth channel: exit beep, previews (never one of the nine)
CHANNELS = 10


class Output(Protocol):
    def play(self, slot: int, pcm: bytes) -> None: ...      # 16-bit stereo PCM at MIX_RATE (render.render_stereo)
    def busy(self, slot: int) -> bool: ...
    def stop(self, slot: int) -> None: ...
    def stop_all(self) -> None: ...
    def close(self) -> None: ...


class PygameOutput:
    """Ten mixer channels at 44,100 Hz, 16-bit stereo. Raises OutputError if the mixer cannot start."""

    def __init__(self, buffer: int = 256):
        import pygame
        self._pygame = pygame
        last = None
        for size in (buffer, 512, 1024, 2048):
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                pygame.mixer.init(frequency=MIX_RATE, size=-16, channels=2, buffer=size, allowedchanges=0)
                break
            except pygame.error as exc:
                last = exc
        else:
            raise OutputError(f"the sound system could not start: {last}")
        pygame.mixer.set_num_channels(CHANNELS)
        self._channels = [pygame.mixer.Channel(i) for i in range(CHANNELS)]
        self.buffer = size
        self.volume = 1.0       # tools set 0.0 to measure a real device without a sound
        log.info("mixer started: %s, buffer %d frames", pygame.mixer.get_init(), size)

    def play(self, slot: int, pcm: bytes) -> None:
        try:
            sound = self._pygame.mixer.Sound(buffer=pcm)     # raw samples in the mixer's own format
            channel = self._channels[slot]
            channel.set_volume(self.volume)
            channel.play(sound)      # the channel keeps its own reference to the sound
        except Exception:
            log.exception("could not play on slot %d", slot)

    def busy(self, slot: int) -> bool:
        try:
            return bool(self._channels[slot].get_busy())
        except Exception:
            return False

    def stop(self, slot: int) -> None:
        try:
            self._channels[slot].stop()
        except Exception:
            log.exception("could not stop slot %d", slot)

    def stop_all(self) -> None:
        for slot in range(CHANNELS):
            self.stop(slot)

    def close(self) -> None:
        try:
            self._pygame.mixer.quit()
        except Exception:
            log.exception("mixer did not close cleanly")


class OutputError(Exception):
    pass


class TimedOutput:
    """No sound; a slot is busy for exactly as long as its sound would take. Records what was played."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._ends = [0.0] * CHANNELS
        self._lock = threading.Lock()
        self.played: list[tuple[int, bytes]] = []

    def play(self, slot: int, pcm: bytes) -> None:
        with self._lock:
            self._ends[slot] = self._clock() + len(pcm) / STEREO_FRAME / MIX_RATE
            self.played.append((slot, pcm))

    def busy(self, slot: int) -> bool:
        with self._lock:
            return self._clock() < self._ends[slot]

    def stop(self, slot: int) -> None:
        with self._lock:
            self._ends[slot] = 0.0

    def stop_all(self) -> None:
        with self._lock:
            self._ends = [0.0] * CHANNELS

    def close(self) -> None:
        pass
