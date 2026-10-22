"""The referee's microphone: a public-address sound for a rendered voice (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

SY.3 (the owner's list after the S8.2 playtest: a referee microphone), D-103. A voice that the program renders into memory (SapiBackend,
speech/sapi5.py) can be given a public-address sound before it is played: band-limited to about 300 Hz to 4.5 kHz (a horn speaker), with two quiet
echoes of a stadium (85 ms and 170 ms) and a short tail. Plain Python with `audioop` (rule 0.11: no numpy), at the speed of C:

* the top is cut by two boxes of four samples (a moving average: first null at 11 kHz, 3 dB down at about 4.5 kHz, no resampling and so no
  aliasing);
* the bottom is cut by subtracting a box of 64 samples (3 dB down at about 300 Hz), built from six averages of the signal with its own shifted copy;
* the echoes are the delayed copies added.

16-bit mono PCM in, the same format out and never louder than the format allows (audioop saturates). It cannot reach a voice that the program
does not render (a slow voice, which is played directly, NVDA and JAWS), which then speak plainly.
"""
from __future__ import annotations

import audioop

TOP_BOXES = (2, 2)           # two boxes of 2**2 = 4 samples
BOTTOM_BOX = 6               # a box of 2**6 = 64 samples
ECHOES = ((0.085, 0.32), (0.17, 0.18))      # (seconds, gain) of the stadium's two echoes
TAIL_SECONDS = 0.22         # silence added at the end for the last echo to ring
MAKE_UP = 1.35              # what the band limit took away, given back


def _shifted(pcm: bytes, samples: int) -> bytes:
    """The signal `samples` samples later (the front is silence, the end falls off): the same length."""
    return bytes(min(len(pcm), 2 * samples)) + pcm[:max(0, len(pcm) - 2 * samples)]


def _average(a: bytes, b: bytes) -> bytes:
    return audioop.add(audioop.mul(a, 2, 0.5), audioop.mul(b, 2, 0.5), 2)


def box(pcm: bytes, power: int) -> bytes:
    """A moving average of 2**power samples, in `power` steps: each averages the signal with itself shifted by 1, 2, 4 ... samples."""
    out = pcm
    for k in range(power):
        out = _average(out, _shifted(out, 1 << k))
    return out


def band_limit(pcm: bytes, rate: int) -> bytes:
    """The voice without what a horn speaker does not carry: below about 300 Hz and above about 4.5 kHz (at a sample rate of 44.1 kHz)."""
    if len(pcm) < 8:
        return pcm
    top = pcm
    for power in TOP_BOXES:
        top = box(top, power)
    low = box(top, BOTTOM_BOX)
    aligned = _shifted(top, (1 << BOTTOM_BOX) // 2 - 1)       # the long box delays by half its length
    return audioop.add(aligned, audioop.mul(low, 2, -1.0), 2)


def apply(pcm: bytes, rate: int) -> bytes:
    """The public-address sound of one chunk of rendered speech (16-bit mono PCM at `rate`)."""
    if len(pcm) < 8:
        return pcm
    pcm = pcm[:len(pcm) & ~1]
    base = band_limit(pcm, rate) + bytes(2 * int(rate * TAIL_SECONDS))
    out = audioop.mul(base, 2, MAKE_UP)
    for seconds, gain in ECHOES:
        lag = bytes(2 * int(rate * seconds))
        shifted = (lag + audioop.mul(base, 2, gain * MAKE_UP))[:len(out)]
        out = audioop.add(out, shifted, 2)
    return out
