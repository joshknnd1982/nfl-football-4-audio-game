"""Helpers for self-healing resource files (playbook 7.10). This is inspired by Jim Kitchen.

A damaged file is copied beside itself first (.damaged1, .damaged2, ...; the latest three are
kept), then the caller recreates it from the built-in originals. Reading is tolerant (UTF-8 with or
without a BOM, UTF-16 with a BOM, the Windows code page, CRLF or LF); a file that is locked is
retried briefly and then reported as unreadable, never as damaged. Nothing here raises, except
read_player_text, which says in its exception kinds what is wrong with the file.
"""
from __future__ import annotations

import codecs
import logging
import os
import re
import shutil
import time

log = logging.getLogger("nfl4.data")

KEEP_DAMAGED_COPIES = 3
MAX_FILE_BYTES = 1_000_000        # a player-edited text file is a few kilobytes; more than this is damage
MOVE_INSTEAD_OF_COPY_BYTES = 8_000_000
LOCK_RETRIES = 3
LOCK_PAUSE = 0.1


class FileInUse(OSError):
    """The file exists but cannot be opened (held by another program, or no permission)."""


def decode_player_text(raw: bytes) -> str:
    """Decode what an editor saved. ValueError or UnicodeError means the bytes are not a text file."""
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return raw.decode("utf-16")
    if b"\x00" in raw:
        raise ValueError("the file holds binary data")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="strict")


def read_player_text(path: str, retries: int = LOCK_RETRIES, pause: float = LOCK_PAUSE) -> str:
    """Read and decode a player-edited text file.

    ValueError / UnicodeError: the file is damaged (too large, binary, undecodable).
    FileInUse: it could not be opened after a few brief retries (locked or no permission).
    Other OSError: it could not be read for another reason (treated like FileInUse by the callers)."""
    for attempt in range(max(1, retries)):
        try:
            if os.path.getsize(path) > MAX_FILE_BYTES:
                raise ValueError("the file is far too large")
            with open(path, "rb") as handle:
                raw = handle.read(MAX_FILE_BYTES + 1)
            return decode_player_text(raw)
        except PermissionError as exc:
            if attempt + 1 < retries:
                time.sleep(pause)
                continue
            raise FileInUse(str(exc)) from exc
    raise FileInUse(path)    # not reached; keeps the type checker calm


def write_text_atomic(path: str, text: str) -> bool:
    """Write the file in one step so a crash never leaves half a file. False if it cannot be written."""
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8", newline="\r\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
        return True
    except OSError:
        log.exception("could not write %s", path)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def save_damaged_copy(path: str) -> str | None:
    """Copy a damaged file to path.damagedN (N one higher than any copy there); drop older ones.

    A very large file is moved instead of copied, so a huge junk file never fills the disk twice."""
    folder, name = os.path.split(path)
    pattern = re.compile(re.escape(name) + r"\.damaged(\d+)$", re.IGNORECASE)
    try:
        numbers = sorted(int(m.group(1)) for m in map(pattern.match, os.listdir(folder)) if m)
        number = (numbers[-1] if numbers else 0) + 1
        target = f"{path}.damaged{number}"
        if os.path.getsize(path) > MOVE_INSTEAD_OF_COPY_BYTES:
            os.replace(path, target)
        else:
            shutil.copyfile(path, target)
        for old in numbers[:max(0, len(numbers) + 1 - KEEP_DAMAGED_COPIES)]:
            try:
                os.remove(f"{path}.damaged{old}")
            except OSError:
                pass
        return target
    except OSError:
        log.exception("could not save a copy of damaged file %s", path)
        return None


def save_backup_copy(path: str, suffix: str) -> str | None:
    """Keep the player's file as path + suffix (one copy, replaced each time) before a reset they asked for."""
    target = path + suffix
    try:
        shutil.copyfile(path, target)
        return target
    except OSError:
        log.exception("could not save a backup of %s", path)
        return None
