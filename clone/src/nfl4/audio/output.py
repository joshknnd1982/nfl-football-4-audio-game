"""Where finished sounds go: the mixer. This is inspired by Jim Kitchen.

Portability seam (playbook 7.2): the rest of the clone talks to `Output`. PygameOutput is the real mixer (pygame-ce,
SDL); TimedOutput makes no sound but keeps time, so it serves the tests and the case where no sound device can be
opened (the program then runs silently instead of ending with an error as the original did, GAP_REGISTER G-A4).

The original's seven DirectSound buffers are seven slots here (WAV_EVENT_MAP 1, GAP_REGISTER G-A1): starting a sound
in a slot stops that slot's sound, different slots mix. One more channel, the extra slot, is not an original buffer
and is never used in play: the sounds menu's previews and the exit beep (SOUND_DESIGN 6).

The level of a playing sound can change (the crowd ramps, F11): a slot's gain is applied by the mixer, not baked into
the samples. SDL_mixer has two multipliers: the sound's own volume (128 integer steps) and the panning effect (a float
multiply, 255 steps); `split_gain` shares a gain between them, so any level down to -50 dB is within half a percent and
the quietest the game sets (-79 dB) within 1 dB (TESTED in nfl4 S7.2 with SDL's disk driver: a chunk volume of 0.25 and
an effect of 0.5 turn 16000 into 1992, and an effect set on an idle channel holds from the new sound's first sample).
"""
from __future__ import annotations

import logging
import math
import threading
import time
from typing import Callable, Protocol

from .render import MIX_RATE, STEREO_FRAME

log = logging.getLogger("nfl4.audio")

# The original's buffer fields (WAV_EVENT_MAP 1), in the order of their form fields Me.m220 to Me.m238
SLOT_ONESHOT = 0      # Me.m220: intro, play, play2, playcel, ChangeVoice
SLOT_CROWD1 = 1       # Me.m224: crowd 1 (foot1), always looping
SLOT_CROWD2 = 2       # Me.m228: crowd 2 (foot2), always looping, ramped
SLOT_HIKE = 3         # Me.m22c: the hike (foot3)
SLOT_AMBIENT = 4      # Me.m230: PlayRan's ambient sounds (foot8 to foot10)
SLOT_TACKLE = 5       # Me.m234: PlayTackle (foot4, foot5, foot6, foot11)
SLOT_NOISE = 6        # Me.m238: the play noise (foot14), looping
SLOT_COUNT = 7        # the original's buffers
EXTRA_SLOT = 7        # not an original buffer: previews, the exit beep and the stadium's sounds (N. F. L. rules)
CROWD_SLOT = 8        # not an original buffer: the stadium's crowd reactions, so a hit or the referee's microphone never cuts them (2026-10-23)
CHANNELS = 9
SLOT_NAMES = ("one-shot", "crowd 1", "crowd 2", "hike", "ambient", "tackle", "play noise", "extra", "crowd reaction")


class Output(Protocol):
    def play(self, slot: int, pcm: bytes, gain: float, loop: bool = False) -> None: ...   # 16-bit stereo PCM at MIX_RATE
    def set_gain(self, slot: int, gain: float) -> None: ...
    def busy(self, slot: int) -> bool: ...
    def stop(self, slot: int) -> None: ...
    def stop_all(self) -> None: ...
    def close(self) -> None: ...


def split_gain(gain: float) -> tuple[int, int]:
    """(chunk steps 0..128, effect steps 0..255) whose product / (128 * 255) is closest to gain (0..1)."""
    if gain >= 1.0:
        return 128, 255
    if gain <= 0.0:
        return 0, 0
    chunk = min(128, max(1, math.ceil(gain * 128 - 1e-9)))
    effect = min(255, max(0, round(gain * 128 / chunk * 255)))
    return chunk, effect


def split_value(gain: float) -> float:
    """The gain the mixer really applies for split_gain(gain)."""
    chunk, effect = split_gain(gain)
    return chunk / 128 * effect / 255


class PygameOutput:
    """Eight mixer channels at 44,100 Hz, 16-bit stereo. Raises OutputError if the mixer cannot start.

    devicename: SDL's device; the tests give a file name with SDL's disk driver to read the mixed output."""

    def __init__(self, buffer: int = 256, devicename: str | None = None):
        import pygame
        self._pygame = pygame
        last = None
        for size in (buffer, 512, 1024, 2048):
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                if devicename:
                    pygame.mixer.init(frequency=MIX_RATE, size=-16, channels=2, buffer=size, allowedchanges=0,
                                      devicename=devicename)
                else:
                    pygame.mixer.init(frequency=MIX_RATE, size=-16, channels=2, buffer=size, allowedchanges=0)
                break
            except pygame.error as exc:
                last = exc
        else:
            raise OutputError(f"the sound system could not start: {last}")
        pygame.mixer.set_num_channels(CHANNELS)
        self._channels = [pygame.mixer.Channel(i) for i in range(CHANNELS)]
        self._sounds: list = [None] * CHANNELS
        self._gains = [1.0] * CHANNELS
        self._lock = threading.Lock()
        self.buffer = size
        self.volume = 1.0       # tools and timing tests set 0.0 BEFORE the first sound to use a real device silently
        log.info("mixer started: %s, buffer %d frames", pygame.mixer.get_init(), size)

    def play(self, slot: int, pcm: bytes, gain: float, loop: bool = False) -> None:
        try:
            with self._lock:
                channel = self._channels[slot]
                channel.stop()          # the old sound ends; SDL_mixer also drops the channel's effect
                sound = self._pygame.mixer.Sound(buffer=pcm)     # raw samples in the mixer's own format
                self._sounds[slot] = sound
                self._gains[slot] = gain
                self._apply(slot)       # on the idle channel: holds from the new sound's first sample
                channel.play(sound, loops=-1 if loop else 0)    # the channel keeps its own reference
        except Exception:
            log.exception("could not play on slot %d", slot)

    def set_gain(self, slot: int, gain: float) -> None:
        try:
            with self._lock:
                self._gains[slot] = gain
                if self._channels[slot].get_busy():
                    self._apply(slot)
        except Exception:
            log.exception("could not set the level of slot %d", slot)

    def _apply(self, slot: int) -> None:
        chunk, effect = split_gain(self._gains[slot] * self.volume)
        sound = self._sounds[slot]
        if sound is not None:
            sound.set_volume(chunk / 128)                 # exact: pygame takes int(volume * 128)
        side = 1.0 if effect == 255 else (effect + 0.25) / 255   # pygame takes int(volume * 255)
        self._channels[slot].set_volume(side, side)       # two values: SDL's panning effect, a float multiply

    def busy(self, slot: int) -> bool:
        try:
            return bool(self._channels[slot].get_busy())
        except Exception:
            log.exception("could not ask slot %d if it is busy", slot)
            return False

    def stop(self, slot: int) -> None:
        try:
            with self._lock:
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
    """No sound; a slot is busy for exactly as long as its sound would take (a loop until it is stopped).
    Records what was played and every level change."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, keep: bool = True):
        self._clock = clock
        self._keep = keep
        self._ends = [0.0] * CHANNELS
        self._lock = threading.Lock()
        self.gains = [1.0] * CHANNELS
        # (slot, pcm, gain, loop) of every play, for the tests; the program's silent output (no sound device) keeps nothing, because
        # every sound it was given would stay in memory for the whole run (S8.3, fixesforgames B-A20)
        self.played: list[tuple[int, bytes, float, bool]] = []

    def play(self, slot: int, pcm: bytes, gain: float, loop: bool = False) -> None:
        with self._lock:
            seconds = len(pcm) / STEREO_FRAME / MIX_RATE
            self._ends[slot] = math.inf if loop and seconds > 0 else self._clock() + seconds
            self.gains[slot] = gain
            if self._keep:
                self.played.append((slot, pcm, gain, loop))

    def set_gain(self, slot: int, gain: float) -> None:
        with self._lock:
            self.gains[slot] = gain

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
