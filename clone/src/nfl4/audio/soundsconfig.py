"""The player's sounds.txt: per-sound file, volume trim, off switch. This is inspired by Jim Kitchen.

Playbook 7.7 names this file sounds.json; 7.9 warns that strict JSON breaks on one missing comma,
so Brain uses plain lines instead (DECISIONS P7 S7.2):

    brain05 = file=my best bell.wav; volume=80
    brain07 = off

Lines starting with # are notes. Bad lines are skipped and counted, never fatal. A file that is
empty, unreadable or of an unknown format version is copied aside and recreated (playbook 7.10).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

from ..data.healing import read_player_text, save_damaged_copy, write_text_atomic

log = logging.getLogger("nfl4.audio")

FORMAT_VERSION = 1
FILE_NAME = "sounds.txt"
MAX_VOLUME_PERCENT = 200

DEFAULT_TEXT = f"""# Brain sounds, format {FORMAT_VERSION}. Lines starting with # are notes and are ignored.
#
# To replace a sound, put a wav file (ogg, flac and mp3 also work) in this folder and name it like
# the sound: brain5.wav replaces sound number 5. Old Brain sound sets work as they are: copy their
# brain1.wav, brain2.wav and so on here. Add brain43.wav, brain44.wav and so on to add sounds, but
# keep the numbers in a row (no gaps), as Jim Kitchen's own readme says.
# The file beep_exit.wav replaces the beep played when Brain ends without the game menu.
#
# For more control, add a line here: the sound name, an equals sign, then settings separated by
# semicolons. Settings: file=NAME (use another file in this folder), volume=PERCENT (0 to 200,
# 100 is unchanged), off (this sound stays silent but keeps its place). Examples, remove the #:
# brain5 = file=my best bell.wav; volume=80
# brain7 = off
# beep_exit = volume=50
#
# If this file is damaged, Brain saves a copy next to it (sounds.txt.damaged1) and makes a new one.
"""

_ID = re.compile(r"^(brain\d+|beep_exit)$", re.IGNORECASE)
_NUMBERED = re.compile(r"^brain0*(\d+)$")


def canonical_id(sound_id: str) -> str:
    """brain5, Brain05 and brain005 are one sound: brain05. Other IDs are lower-cased."""
    key = sound_id.strip().lower()
    match = _NUMBERED.match(key)
    return f"brain{int(match.group(1)):02d}" if match else key
_VERSION = re.compile(r"^#\s*Brain sounds,\s*format\s+(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class SoundEntry:
    file: str | None = None
    volume: float = 1.0      # linear gain from the percent setting
    off: bool = False


@dataclass
class SoundsConfig:
    entries: dict[str, SoundEntry] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)   # plain reasons, for the log and "check files"

    def get(self, sound_id: str) -> SoundEntry | None:
        return self.entries.get(canonical_id(sound_id))


def parse(text: str) -> SoundsConfig:
    """Parse the file's text. Raises ValueError when the file is unusable as a whole."""
    config = SoundsConfig()
    nonblank = 0
    header_seen = False
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        nonblank += 1
        version = _VERSION.match(line)
        if version:
            if int(version.group(1)) != FORMAT_VERSION:
                raise ValueError(f"unknown format version {version.group(1)}")
            header_seen = True
            continue
        if line.startswith("#"):
            continue
        sound_id, sep, rest = line.partition("=")
        sound_id = sound_id.strip()
        if not sep or not _ID.match(sound_id):
            config.problems.append(f"line {number}: '{line[:40]}' is not 'sound name = settings'")
            continue
        entry = _parse_settings(sound_id, rest, number, config.problems)
        if entry is not None:
            config.entries[canonical_id(sound_id)] = entry
    if nonblank == 0:
        raise ValueError("the file is empty")
    if not header_seen and not config.entries and config.problems:
        raise ValueError("no header and nothing usable")
    return config


def _parse_settings(sound_id: str, rest: str, number: int, problems: list[str]) -> SoundEntry | None:
    file = None
    volume = 1.0
    off = False
    for item in (part.strip() for part in rest.split(";")):
        if not item:
            continue
        key, eq, value = item.partition("=")
        key = key.strip().lower()
        value = value.strip()
        if key == "off" and not eq:
            off = True
        elif key == "file" and value:
            file = value
        elif key == "volume":
            try:
                percent = float(value.rstrip("%"))
            except ValueError:
                problems.append(f"line {number}: volume '{value}' is not a number")
                continue
            if not 0 <= percent <= MAX_VOLUME_PERCENT:
                problems.append(f"line {number}: volume {percent:g} is outside 0 to {MAX_VOLUME_PERCENT}")
                continue
            volume = percent / 100.0
        else:
            problems.append(f"line {number}: setting '{item[:30]}' is not known")
    return SoundEntry(file=file, volume=volume, off=off)


def load_or_heal(sounds_dir: str) -> tuple[SoundsConfig, list[str]]:
    """Make sure the sounds folder and sounds.txt exist and are usable; return (config, notices).

    notices are short sentences the program may speak (playbook 7.10: one per start).
    Never raises: if nothing can be written, or the file is held by another program, the built-in
    defaults are used from memory and the file is left alone."""
    notices: list[str] = []
    path = os.path.join(sounds_dir, FILE_NAME)
    try:
        os.makedirs(sounds_dir, exist_ok=True)
    except OSError:
        log.exception("could not create the sounds folder %s", sounds_dir)
    if not os.path.isfile(path):
        if write_text_atomic(path, DEFAULT_TEXT):
            log.info("created %s", path)
        else:
            notices.append(UNWRITABLE_NOTICE)
        return parse(DEFAULT_TEXT), notices
    try:
        config = parse(read_player_text(path))
    except OSError as exc:       # FileInUse or any other failure to read: use the originals, leave the file alone
        log.warning("%s cannot be read now (%s); using the original sound settings", path, exc)
        notices.append(IN_USE_NOTICE)
        return parse(DEFAULT_TEXT), notices
    except (ValueError, UnicodeError) as exc:
        log.warning("%s is unusable (%s); resetting it", path, exc)
        saved = save_damaged_copy(path)
        if write_text_atomic(path, DEFAULT_TEXT):
            notices.append("sounds.txt was damaged and has been reset to the original settings."
                           + (" A copy was saved." if saved else ""))
        else:
            notices.append(UNWRITABLE_NOTICE)
        return parse(DEFAULT_TEXT), notices
    if config.problems:
        for problem in config.problems:
            log.warning("%s: %s", FILE_NAME, problem)
        count = len(config.problems)
        notices.append(f"{count} problem{'s' if count != 1 else ''} found in sounds.txt, details are in the log.")
    return config, notices


UNWRITABLE_NOTICE = ("sounds.txt could not be written, so Brain uses the original sound settings. "
                     "It belongs in the sounds folder inside the Brain folder of Kitchensinc Revival in your AppData Roaming folder.")
IN_USE_NOTICE = "sounds.txt is in use by another program, so Brain uses the original sound settings this time."


def drop_entry(sounds_dir: str, sound_id: str) -> bool:
    """Remove the line(s) for one sound from sounds.txt, keeping notes and other lines. True when the file was changed.

    An unreadable or unusable file is left to load_or_heal (the caller refreshes the library first)."""
    path = os.path.join(sounds_dir, FILE_NAME)
    try:
        text = read_player_text(path)
    except (OSError, ValueError, UnicodeError):
        return False
    wanted = canonical_id(sound_id)
    kept: list[str] = []
    dropped = False
    for raw in text.splitlines():
        line = raw.strip().lstrip("﻿")
        name, sep, _ = line.partition("=")
        if sep and not line.startswith("#") and _ID.match(name.strip()) and canonical_id(name) == wanted:
            dropped = True
            continue
        kept.append(raw)
    return dropped and write_text_atomic(path, "\n".join(kept) + "\n")
