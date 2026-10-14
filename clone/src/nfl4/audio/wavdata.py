"""Reading sound files into 16-bit samples. This is inspired by Jim Kitchen.

Any rate, depth, channel count (1 or 2) and length is accepted (playbook 7.7); empty, cut-off,
unreadable or very long files raise SoundLoadError so the caller can fall back to the next
choice in the resolution chain. Wav files are parsed here (PCM 8/16/24/32 bit, float,
WAVE_FORMAT_EXTENSIBLE); other wav codecs and ogg, flac and mp3 go through pygame's decoder,
which hands back the mixer's own rate (44,100 Hz), so for those files the pitch step of
GAME_SPEC 5.3 is relative to 44,100 Hz instead of the file's own rate.

No numpy (version 1.0.3; the user chose this on 2026-10-13 after a trial; numpy was 28 MB of the install; tag brain-1.0.2-numpy is the numpy version): samples are plain bytes of
16-bit PCM and the sample math is `audioop` (the package audioop-lts, 30 KB, because Python 3.13
dropped the standard module). Byte order is the machine's own, little-endian on every platform
this clone targets.
"""
from __future__ import annotations

import audioop
import os
import struct
from array import array
from dataclasses import dataclass

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_SECONDS = 30.0            # "very long" files fall back (7.7); the shipped wavs are at most 250 ms
MAX_RATE = 384_000
DECODER_EXTENSIONS = (".wav", ".ogg", ".flac", ".mp3")   # lookup order for player files


class SoundLoadError(Exception):
    """A sound file cannot be used; the message is a plain reason for the log."""


@dataclass(frozen=True)
class Sampled:
    """Decoded sound: 16-bit signed PCM, interleaved, channels 1 or 2 (the format the mixer takes)."""
    pcm: bytes
    rate: int
    channels: int = 1

    @property
    def frames(self) -> int:
        return len(self.pcm) // (2 * self.channels)

    @property
    def seconds(self) -> float:
        return self.frames / self.rate

    @property
    def peak(self) -> int:
        """Largest absolute sample, 0 to 32768."""
        return audioop.max(self.pcm, 2) if self.pcm else 0

    def samples(self, channel: int = 0) -> array:
        """One channel as an array of 16-bit ints (for tests and tools; the program works on the bytes)."""
        every = array("h")
        every.frombytes(self.pcm)
        return every[channel::self.channels]

    def silenced(self) -> "Sampled":
        """Same length and rate, no sound (a sound switched off keeps its place in the pool)."""
        return Sampled(bytes(len(self.pcm)), self.rate, self.channels)


def load_sound_file(path: str) -> Sampled:
    """Decode one file. Raises SoundLoadError, never anything else."""
    try:
        size = os.path.getsize(path)
        if size > MAX_FILE_BYTES:
            raise SoundLoadError(f"file is {size // (1024 * 1024)} MB, over the {MAX_FILE_BYTES // (1024 * 1024)} MB limit")
        ext = os.path.splitext(path)[1].lower()
        if ext == ".wav":
            with open(path, "rb") as handle:
                raw = handle.read()
            try:
                sound = parse_wav(raw)
            except _UnsupportedCodec as codec:
                sound = _decode_with_pygame(path, str(codec))
        elif ext in DECODER_EXTENSIONS:
            sound = _decode_with_pygame(path, ext)
        else:
            raise SoundLoadError(f"file type {ext or '(none)'} is not supported")
        _check_usable(sound)
        return sound
    except SoundLoadError:
        raise
    except Exception as exc:  # decoder bugs must never reach the game
        raise SoundLoadError(f"{type(exc).__name__}: {exc}") from exc


def _check_usable(sound: Sampled) -> None:
    if sound.frames == 0:
        raise SoundLoadError("the file holds no sound")
    if sound.seconds > MAX_SECONDS:
        raise SoundLoadError(f"the sound is {sound.seconds:.0f} s long, over the {MAX_SECONDS:.0f} s limit")


class _UnsupportedCodec(Exception):
    pass


def parse_wav(raw: bytes) -> Sampled:
    """Parse a RIFF wave file. Raises SoundLoadError for damage, _UnsupportedCodec for other codecs."""
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise SoundLoadError("not a RIFF wave file")
    fmt = None
    data = None
    pos = 12
    while pos + 8 <= len(raw):
        chunk_id = raw[pos:pos + 4]
        (chunk_size,) = struct.unpack_from("<I", raw, pos + 4)
        body = pos + 8
        available = len(raw) - body
        if chunk_id == b"data":
            # A stream-style or cut-off header: use what is there.
            data = raw[body:body + min(chunk_size, available)]
            if fmt is not None:
                break
        elif chunk_id == b"fmt ":
            if chunk_size < 16 or available < 16:
                raise SoundLoadError("the format block is cut off")
            fmt = raw[body:body + min(chunk_size, available)]
        pos = body + chunk_size + (chunk_size & 1)
        if chunk_size > available:
            break
    if fmt is None:
        raise SoundLoadError("no format block")
    if data is None:
        raise SoundLoadError("no sound data block")
    tag, channels, rate, _, block_align, bits = struct.unpack_from("<HHIIHH", fmt, 0)
    if tag == 0xFFFE and len(fmt) >= 26:       # WAVE_FORMAT_EXTENSIBLE: the real tag starts the GUID
        (tag,) = struct.unpack_from("<H", fmt, 24)
    if channels not in (1, 2):
        raise SoundLoadError(f"{channels} channels are not supported (1 or 2)")
    if not 1 <= rate <= MAX_RATE:
        raise SoundLoadError(f"sample rate {rate} Hz is not usable")
    if tag == 1 and bits in (8, 16, 24, 32):
        width = bits // 8
    elif tag == 3 and bits in (32, 64):
        width = bits // 8
    else:
        raise _UnsupportedCodec(f"wav format {tag}, {bits} bit")
    frame_bytes = width * channels
    frames = len(data) // frame_bytes
    if frames == 0:
        raise SoundLoadError("the file holds no sound")
    chunk = bytes(data[:frames * frame_bytes])
    if tag == 3:
        pcm = _float_to_pcm16(chunk, bits)
    elif bits == 8:
        pcm = audioop.lin2lin(audioop.bias(chunk, 1, 128), 1, 2)    # unsigned with silence at 128 -> signed -> 16 bit
    elif bits == 16:
        pcm = chunk
    elif bits == 24:
        pcm = audioop.lin2lin(chunk, 3, 2)
    else:
        pcm = audioop.lin2lin(chunk, 4, 2)
    return Sampled(pcm, int(rate), channels)


def _float_to_pcm16(chunk: bytes, bits: int) -> bytes:
    """32 or 64-bit float samples to 16-bit. Not a number counts as silence, out of range as full scale."""
    values = array("f" if bits == 32 else "d")
    values.frombytes(chunk)
    out = array("h")
    for v in values:
        v = 0.0 if v != v else max(-1.0, min(1.0, v))
        out.append(max(-32768, min(32767, int(round(v * 32768.0)))))
    return out.tobytes()


def _decode_with_pygame(path: str, what: str) -> Sampled:
    """Use the mixer's decoder (ogg, flac, mp3, other wav codecs). Needs the mixer running."""
    import pygame
    if not pygame.mixer.get_init():
        raise SoundLoadError(f"{what} needs the sound system, which is not running")
    try:
        raw = pygame.mixer.Sound(path).get_raw()
    except pygame.error as exc:
        raise SoundLoadError(f"cannot decode {what}: {exc}") from exc
    rate, fmt, channels = pygame.mixer.get_init()
    if fmt != -16 or channels not in (1, 2):
        raise SoundLoadError(f"the mixer's format {fmt}, {channels} channels cannot be used for {what}")
    if channels == 2:
        left, right = audioop.tomono(raw, 2, 1, 0), audioop.tomono(raw, 2, 0, 1)
        if left == right:
            return Sampled(left, int(rate), 1)    # a mono file the mixer doubled
    return Sampled(bytes(raw), int(rate), int(channels))
