"""Frequency, pan and level. This is inspired by Jim Kitchen.

The original set each DirectSound buffer's frequency, pan and volume (WAV_EVENT_MAP 1, 3 and 4). Here a sound is
resampled (linear interpolation, as a software mixer does) to the length it has when its buffer plays at the new
frequency, mixed at a fixed 44,100 Hz, and pan becomes left and right gains. The volume is applied by the mixer
(output.py), so a playing sound's level can change; `level_gain` turns DirectSound's hundredths of a decibel into it.

No numpy (rule 0.11, D-036): `audioop` (package audioop-lts, 30 KB) does the resampling (`ratecv`) and the gains with
clipping (`tostereo`) in C. Rendered sound is 16-bit stereo PCM bytes, 4 bytes per frame.
"""
from __future__ import annotations

import audioop

from .wavdata import Sampled

MIX_RATE = 44_100
MIN_FREQ = 100            # DirectSound's documented SetFrequency limits; outside them the call failed and
MAX_FREQ = 200_000        # the frequency stayed unchanged
MAX_PAN = 10_000
SILENT_VOLUME = -10_000   # DSBVOLUME_MIN: hundredths of a decibel; this and below is silence
STEREO_FRAME = 4          # bytes of one rendered frame: two 16-bit samples


def level_gain(volume: int) -> float:
    """DirectSound volume (hundredths of a decibel, 0 = the file unchanged) as a linear gain: 10 ** (v / 2000)
    (D-023). 0 and above is full; -10000 and below is silence."""
    v = int(volume)
    if v >= 0:
        return 1.0
    if v <= SILENT_VOLUME:
        return 0.0
    return 10.0 ** (v / 2000.0)


def pan_gains(pan: int) -> tuple[float, float]:
    """DirectSound pan (hundredths of a dB, negative = left): only the far channel is attenuated by |pan|/100 dB
    (D-023, WAV_EVENT_MAP 3: SetPan)."""
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
    """16-bit stereo PCM bytes ready for the mixer. volume is a linear gain baked into the samples: the player's trim
    from sounds.txt (1.0 = the file unchanged); the game's own levels are the mixer's (level_gain)."""
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
