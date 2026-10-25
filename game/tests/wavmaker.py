"""Builds small wav files and sounds for the audio tests. This is inspired by Jim Kitchen.

No numpy: samples are plain lists of floats in -1..1, one number per frame for mono or one
(left, right) pair per frame for stereo.
"""
import math
import struct
from array import array

from nfl4.audio.wavdata import Sampled


def _flat(samples):
    out = []
    for item in samples:
        if isinstance(item, (tuple, list)):
            out.extend(item)
        else:
            out.append(item)
    return out


def wav_bytes(samples, rate=11025, bits=16, channels=1, fmt_tag=1, extensible=False,
              data_size=None, extra_chunk=False, truncate=0):
    """samples: floats in -1..1, one per frame (mono) or one (left, right) pair per frame."""
    values = _flat(samples)
    count = len(values)
    if fmt_tag == 3:
        body = struct.pack(f"<{count}{'f' if bits == 32 else 'd'}", *values)
    elif bits == 8:
        body = bytes(max(0, min(255, round(v * 128 + 128))) for v in values)
    elif bits == 16:
        body = struct.pack(f"<{count}h", *[max(-32768, min(32767, round(v * 32767))) for v in values])
    elif bits == 24:
        ints = [max(-2**23, min(2**23 - 1, round(v * (2**23 - 1)))) for v in values]
        body = b"".join(struct.pack("<i", v)[:3] for v in ints)
    elif bits == 32:
        body = struct.pack(f"<{count}i", *[max(-2**31, min(2**31 - 1, round(v * (2**31 - 1)))) for v in values])
    else:
        raise ValueError(bits)
    if truncate:
        body = body[:-truncate]
    block = channels * bits // 8
    if extensible:
        fmt = struct.pack("<HHIIHHHHIH14s", 0xFFFE, channels, rate, rate * block, block, bits,
                          22, bits, 0, fmt_tag, b"\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71")
    else:
        fmt = struct.pack("<HHIIHH", fmt_tag, channels, rate, rate * block, block, bits)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    if extra_chunk:
        chunks += b"LIST" + struct.pack("<I", 5) + b"abcde" + b"\x00"   # odd size, padded
    size = len(body) if data_size is None else data_size
    chunks += b"data" + struct.pack("<I", size) + body
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks


def sine(freq, seconds, rate, amp=0.5):
    return [amp * math.sin(2 * math.pi * freq * (i / rate)) for i in range(int(rate * seconds))]


def sampled(samples, rate=11025, channels=1):
    """A decoded sound (brain.audio.wavdata.Sampled) made directly from float samples."""
    values = _flat(samples)
    pcm = array("h", [max(-32768, min(32767, round(v * 32768))) for v in values])
    return Sampled(pcm.tobytes(), rate, channels)


def floats(sound, channel=0):
    """One channel of a decoded sound as floats in -1..1."""
    return [v / 32768.0 for v in sound.samples(channel)]


def write(path, *args, **kwargs):
    with open(path, "wb") as handle:
        handle.write(wav_bytes(*args, **kwargs))
    return str(path)
