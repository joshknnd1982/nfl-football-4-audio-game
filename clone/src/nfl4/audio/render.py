"""Pitch and pan rendering. This is inspired by Jim Kitchen's Brain.

The original set DirectSound's buffer frequency and pan (GAME_SPEC 5.3, 5.5). Here a sound is
resampled (linear interpolation, as a software mixer does) to the length it has when its buffer
plays at the new frequency, mixed at a fixed 44,100 Hz, and pan becomes left and right gains.

No numpy (version 1.0.3; the user chose this on 2026-10-13 after a trial; tag brain-1.0.2-numpy is the numpy version): `audioop` (package audioop-lts, 30 KB) does the resampling
(`ratecv`) and the gains with clipping (`tostereo`) in C. Measured against the numpy version on
all 42 shipped wavs at ten pitches and five pans: at most 2 of 32,768 steps apart, same lengths.
Rendered sound is 16-bit stereo PCM bytes, 4 bytes per frame.
"""
from __future__ import annotations

import audioop

from .wavdata import Sampled

MIX_RATE = 44_100
MIN_FREQ = 100            # DirectSound's documented SetFrequency limits (GAME_SPEC 5.3);
MAX_FREQ = 200_000        # outside them the original's call failed and the pitch stayed unchanged
MAX_PAN = 10_000
STEREO_FRAME = 4          # bytes of one rendered frame: two 16-bit samples


def pan_gains(pan: int) -> tuple[float, float]:
    """DirectSound pan (hundredths of a dB, negative = left): only the far channel is attenuated
    by |pan|/100 dB (DECISIONS P5)."""
    p = max(-MAX_PAN, min(MAX_PAN, int(pan)))
    far = 10.0 ** (-abs(p) / 2000.0)
    return (far, 1.0) if p > 0 else (1.0, far)


def usable_frequency(freq: int) -> bool:
    return MIN_FREQ <= freq <= MAX_FREQ


def output_frames(frames: int, freq: int) -> int:
    """Mixer frames the sound takes when its buffer plays at freq."""
    return max(1, int(round(frames * MIX_RATE / freq)))


def frames_of(pcm: bytes) -> int:
    """Frames in rendered (stereo 16-bit) sound."""
    return len(pcm) // STEREO_FRAME


def resample(sound: Sampled, freq: int) -> bytes:
    """16-bit PCM with the sound's channel count at MIX_RATE, as if the buffer ran at freq."""
    unit = 2 * sound.channels
    want = output_frames(sound.frames, freq) * unit
    last = sound.pcm[-unit:]
    # Two copies of the last frame behind the sound: the interpolation then reaches the final sample
    # and holds it, as the float version did; the result is cut to the exact length.
    out, _ = audioop.ratecv(sound.pcm + last * 2, 2, sound.channels, int(freq), MIX_RATE, None, 1, 0)
    if len(out) < want:
        hold = out[-unit:] if out else last
        out += hold * ((want - len(out)) // unit)
    return out[:want]


def render_stereo(sound: Sampled, freq: int, pan: int, volume: float) -> bytes:
    """16-bit stereo PCM bytes ready for the mixer. volume is a linear gain (1.0 = the file unchanged)."""
    pitched = resample(sound, freq)
    left_gain, right_gain = pan_gains(pan)
    scale = max(0.0, volume) * 32767.0 / 32768.0
    if sound.channels == 1:
        return audioop.tostereo(pitched, 2, left_gain * scale, right_gain * scale)
    left = audioop.tostereo(audioop.tomono(pitched, 2, 1, 0), 2, left_gain * scale, 0)
    right = audioop.tostereo(audioop.tomono(pitched, 2, 0, 1), 2, 0, right_gain * scale)
    return audioop.add(left, right, 2)


def channel_peak(pcm: bytes, channel: int) -> int:
    """Largest absolute sample of one channel (0 left, 1 right) of rendered stereo sound."""
    mono = audioop.tomono(pcm, 2, 1, 0) if channel == 0 else audioop.tomono(pcm, 2, 0, 1)
    return audioop.max(mono, 2) if mono else 0
