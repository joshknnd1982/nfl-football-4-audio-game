"""Generated sounds. This is inspired by Jim Kitchen.

Brain needs almost none (SOUND_DESIGN.md: every silent event stays silent). The one generated
sound is the fallback for the exit beep when the system's default sound cannot be played.
A sound is a list of segments held as data (playbook 7.8); synthesis is deterministic.

No numpy (version 1.0.3; the user chose this on 2026-10-13 after a trial; tag brain-1.0.2-numpy is the numpy version):
plain Python on 16-bit samples. Measured on the owner's PC: 2.6 to 3.4 million samples per second (2 seconds of
sound in about 30 ms; numpy is about 35 times faster). Fine for effects and for music of some seconds at start-up;
a game with minutes of generated music writes those once as wav files (at build time or first run) instead of
synthesizing them at every start, or the user chooses the numpy variant of the starter kit (playbook 7.1.1).
"""
from __future__ import annotations

import math
import random
import wave
from array import array
from dataclasses import dataclass

from .render import MIX_RATE
from .wavdata import Sampled


@dataclass(frozen=True)
class Segment:
    wave: str            # "square", "triangle", "sine" or "noise" (seeded)
    start_hz: float
    end_hz: float        # a sweep when different from start_hz
    ms: float
    volume: float        # 0..1; 0 makes a rest
    attack_ms: float = 2.0
    release_ms: float = 2.0   # short edges so nothing clicks


# GENERATED sounds by sound ID. beep_exit: fallback only, 880 Hz square, 80 ms (SOUND_DESIGN.md).
GENERATED_SOUNDS: dict[str, tuple[Segment, ...]] = {
    "beep_exit": (Segment("square", 880.0, 880.0, 80.0, 0.35),),
}


def synthesize(segments: tuple[Segment, ...], rate: int = MIX_RATE, seed: int = 1) -> Sampled:
    rng = random.Random(seed)
    out = array("h")
    phase = 0.0
    for seg in segments:
        if seg.wave not in ("square", "triangle", "sine", "noise"):
            raise ValueError(f"unknown waveform {seg.wave!r}")
        n = max(1, int(round(rate * seg.ms / 1000.0)))
        attack = min(n // 2, int(rate * seg.attack_ms / 1000.0))
        release = min(n // 2, int(rate * seg.release_ms / 1000.0))
        sweep = (seg.end_hz - seg.start_hz) / (n - 1) if n > 1 else 0.0
        ph = phase
        for i in range(n):
            ph += (seg.start_hz + sweep * i) / rate
            frac = ph % 1.0
            if seg.wave == "square":
                value = 1.0 if frac < 0.5 else -1.0
            elif seg.wave == "triangle":
                value = 4.0 * abs(frac - 0.5) - 1.0
            elif seg.wave == "sine":
                value = math.sin(2.0 * math.pi * ph)
            else:
                value = rng.uniform(-1.0, 1.0)
            if attack and i < attack:
                value *= i / attack
            if release and i >= n - release:
                value *= 1.0 - (i - (n - release)) / (release - 1) if release > 1 else 1.0
            out.append(max(-32768, min(32767, int(round(value * seg.volume * 32768.0)))))
        phase = ph % 1.0
    if not out:
        out.append(0)
    return Sampled(out.tobytes(), rate, 1)


def generated(sound_id: str) -> Sampled | None:
    segments = GENERATED_SOUNDS.get(sound_id)
    return synthesize(segments) if segments else None


def write_wav(path: str, sound: Sampled) -> None:
    """16-bit wav, for exporting generated sounds (Sounds menu, S7.7)."""
    with wave.open(path, "wb") as out:
        out.setnchannels(sound.channels)
        out.setsampwidth(2)
        out.setframerate(sound.rate)
        out.writeframes(sound.pcm)
