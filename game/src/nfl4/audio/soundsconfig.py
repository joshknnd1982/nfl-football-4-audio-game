"""The player's sounds.txt: per-sound file, volume trim, off switch. This is inspired by Jim Kitchen.

Playbook 7.7 names this file sounds.json; 7.9 warns that strict JSON breaks on one missing comma, so the starter kit
uses plain lines instead (fixesforgames B-A1; SOUND_DESIGN 6):

    snd_foot7 = file=my kick.wav; volume=80
    snd_foot13 = off

Lines starting with # are notes. Bad lines are skipped and counted, never fatal. A file that is empty, unreadable or
of an unknown format version is copied aside and recreated (playbook 7.10).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

from ..data.healing import read_player_text, save_damaged_copy, write_text_atomic
from .ids import EVENT_NAMES, FOOT_COUNT, canonical_id, is_known

log = logging.getLogger("nfl4.audio")

FORMAT_VERSION = 1
FILE_NAME = "sounds.txt"
MAX_VOLUME_PERCENT = 200

_SOUND_LIST = "\n".join(f"#   foot{n}: {EVENT_NAMES[n]}" for n in range(FOOT_COUNT))

DEFAULT_TEXT = f"""# NFL Football 4 sounds, format {FORMAT_VERSION}. Lines starting with # are notes and are ignored.
#
# To replace a sound, put a wav file (ogg, flac and mp3 also work) in this folder and give it the
# name of the original file: foot7.wav replaces the kick. The name snd_foot7.wav works too.
# The file beep_exit.wav replaces the two beeps played when the game ends.
# The sounds of the game:
{_SOUND_LIST}
#
# For more control, add a line here: the sound name, an equals sign, then settings separated by
# semicolons. Settings: file=NAME (use another file in this folder), volume=PERCENT (0 to 200,
# 100 is unchanged), off (this sound is not played and the game does not wait for it; for a pause
# instead, use a silent wav file as long as the pause you want).
# Examples, remove the # to use one:
# snd_foot7 = file=my kick.wav; volume=80
# snd_foot13 = off
# beep_exit = volume=50
#
# The sound volume of the whole game is in the F11 menu.
# If this file is damaged, the game saves a copy next to it (sounds.txt.damaged1) and makes a new one.
"""

_VERSION = re.compile(r"^#\s*NFL Football 4 sounds,\s*format\s+(\d+)", re.IGNORECASE)


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
        if not sep or not is_known(sound_id):
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


UNWRITABLE_NOTICE = ("sounds.txt could not be written, so the game uses the original sound settings. "
                     "It belongs in the sounds folder inside the NFL Football 4 folder of Kitchensinc Revival "
                     "in your AppData Roaming folder.")
IN_USE_NOTICE = "sounds.txt is in use by another program, so the game uses the original sound settings this time."


def drop_entry(sounds_dir: str, sound_id: str) -> bool:
    """Remove the line(s) for one sound from sounds.txt, keeping notes and other lines. True when the file was changed.

    An unreadable or unusable file is left to load_or_heal (the caller refreshes the library first)."""
    path = os.path.join(sounds_dir, FILE_NAME)
    try:
        text = read_player_text(path)
    except (OSError, ValueError, UnicodeError) as exc:
        log.debug("%s cannot be read to restore a sound (%s)", path, exc)
        return False
    wanted = canonical_id(sound_id)
    kept: list[str] = []
    dropped = False
    for raw in text.splitlines():
        line = raw.strip().lstrip("﻿")
        name, sep, _ = line.partition("=")
        if sep and not line.startswith("#") and is_known(name) and canonical_id(name) == wanted:
            dropped = True
            continue
        kept.append(raw)
    return dropped and write_text_atomic(path, "\n".join(kept) + "\n")
