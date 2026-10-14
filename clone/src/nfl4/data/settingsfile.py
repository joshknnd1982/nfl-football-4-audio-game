"""The player's settings.txt: saved speech and sound settings, self-healing. This is inspired by Jim Kitchen's Brain.

The original kept no settings at all (GAME_SPEC 3.1: first voice, volume 90, every run the same).
The clone's settings (F2 speech, F3 sounds) are saved per user in plain lines, same style as
sounds.txt (DECISIONS P7 S7.2), so one missing comma never breaks anything (playbook 7.9, 7.10):

    speech_volume = 80
    speech_rate = original

Lines starting with # are notes. A bad line is skipped and reported, its setting stays original. A file
that is empty, binary, too large, of an unknown format version or all junk is copied aside as
settings.txt.damaged1 and recreated with the original values. A file held by another program is left
alone (the original values are used this run and nothing is saved over it). A folder or file that
cannot be written is told once and the program carries on from memory.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Callable

from . import paths
from .healing import read_player_text, save_damaged_copy, write_text_atomic
from .settings import AudioSettings, Settings, SpeechSettings

log = logging.getLogger("nfl4.data")

FORMAT_VERSION = 1
FILE_NAME = "settings.txt"
MODES = ("sapi", "nvda", "jaws", "auto")
_MODE_WORDS = {"sapi": "sapi", "sapi5": "sapi", "sapi 5": "sapi", "nvda": "nvda", "jaws": "jaws", "auto": "auto", "automatic": "auto"}
_START_WORDS = {"after_prompt": False, "prompt": False, "after": False, "original": False,
                "right_away": True, "early": True, "now": True, "at_once": True}
_VERSION = re.compile(r"^#\s*Brain settings,\s*format\s+(\d+)", re.IGNORECASE)
_NAME = re.compile(r"^[a-z_]+$")

HEADER = f"""# Brain settings, format {FORMAT_VERSION}. Lines starting with # are notes and are ignored.
#
# Brain saves this file itself whenever you change a setting in its menus (F2 speech, F3 sounds).
# You can also edit it in Notepad while Brain is closed: one setting per line, name = value.
# A line that cannot be understood is skipped and that setting stays original. If this file is
# damaged, Brain saves a copy next to it (settings.txt.damaged1) and makes a new one.
#
# speech_voice     the voice's identifier. Empty means the first voice in Windows' list (original).
#                  Choose a voice in the F2 menu rather than typing this.
# speech_rate      -10 to 10, or original for the voice's own rate (original)
# speech_volume    0 to 100 (original 90)
# speech_pitch     -10 to 10 (original 0). Not every voice supports it.
# speech_output    sapi = the SAPI 5 voice only (original), nvda = NVDA only, jaws = JAWS only, auto = NVDA or JAWS when one runs
# list_letters     type = typing letters searches a list for a name (default), first = a letter jumps to the
#                  next name that starts with it (press it again for the one after)
# sound_volume     0 to 100 percent (original 100)
# pitch_variation  0 to 20; 20 is the original, 0 plays every sound at its own pitch
# sound_start      after_prompt = the sounds start when the spoken prompt has ended (original),
#                  right_away = they start at once and the prompt is still being spoken
#
"""


class SettingsFormatError(ValueError):
    """The file as a whole is unusable (empty, unknown version, nothing understood)."""


def render(settings: Settings, voice_name: str = "") -> str:
    sp, au = settings.speech, settings.audio
    lines = [HEADER.rstrip("\n")]
    if voice_name and sp.voice_id:
        lines.append(f"# The voice below is: {voice_name.replace(chr(10), ' ')}")
    lines += [
        f"speech_voice = {sp.voice_id or ''}",
        f"speech_rate = {'original' if sp.rate is None else sp.rate}",
        f"speech_volume = {sp.volume}",
        f"speech_pitch = {sp.pitch}",
        f"speech_output = {sp.mode}",
        f"list_letters = {sp.list_letters}",
        f"sound_volume = {au.effects_volume}",
        f"pitch_variation = {au.pitch_spread}",
        f"sound_start = {'right_away' if au.start_early else 'after_prompt'}",
    ]
    return "\n".join(lines) + "\n"


def _number(value: str, low: int, high: int) -> int:
    text = value.strip().rstrip("%").strip()
    if not re.fullmatch(r"[+-]?\d{1,6}", text):
        raise ValueError(f"'{value[:20]}' is not a whole number")
    number = int(text)
    if not low <= number <= high:
        raise ValueError(f"{number} is outside {low} to {high}")
    return number


def parse(text: str) -> tuple[Settings, list[str]]:
    """Parse the file's text into settings and a list of plain problems. Raises SettingsFormatError when unusable."""
    settings = Settings.defaults()
    sp, au = settings.speech, settings.audio
    problems: list[str] = []
    nonblank = 0
    understood = 0
    header_seen = False
    seen: set[str] = set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().lstrip("﻿")
        if not line:
            continue
        nonblank += 1
        version = _VERSION.match(line)
        if version:
            if int(version.group(1)) != FORMAT_VERSION:
                raise SettingsFormatError(f"unknown format version {version.group(1)}")
            header_seen = True
            continue
        if line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        name = name.strip().lower()
        value = value.strip()
        if not sep or not _NAME.match(name):
            problems.append(f"line {number}: '{line[:40]}' is not 'name = value'")
            continue
        try:
            _apply(name, value, sp, au)
        except KeyError:
            problems.append(f"line {number}: '{name[:30]}' is not a known setting")
            continue
        except ValueError as exc:
            problems.append(f"line {number}: {name}: {exc}")
            continue
        understood += 1
        if name in seen:
            problems.append(f"line {number}: {name} appears twice, the last one is used")
        seen.add(name)
    if nonblank == 0:
        raise SettingsFormatError("the file is empty")
    if not header_seen and understood == 0 and problems:
        raise SettingsFormatError("no header and nothing understood")
    return settings, problems


def _apply(name: str, value: str, sp: SpeechSettings, au: AudioSettings) -> None:
    """Set one value; KeyError for an unknown name, ValueError for a bad value (the setting keeps its old value)."""
    if name == "speech_voice":
        if len(value) > 400 or any(ord(c) < 32 for c in value):
            raise ValueError("not a voice identifier")
        sp.voice_id = value or None
    elif name == "speech_rate":
        sp.rate = None if value.lower() in ("original", "") else _number(value, -10, 10)
    elif name == "speech_volume":
        sp.volume = _number(value, 0, 100)
    elif name == "speech_pitch":
        sp.pitch = _number(value, -10, 10)
    elif name == "speech_output":
        mode = _MODE_WORDS.get(value.lower())
        if mode is None:
            raise ValueError(f"'{value[:20]}' is not sapi, nvda, jaws or auto")
        sp.mode = mode
    elif name == "list_letters":
        if value.lower() not in ("type", "first"):
            raise ValueError(f"'{value[:20]}' is not type or first")
        sp.list_letters = value.lower()
    elif name == "sound_volume":
        au.effects_volume = _number(value, 0, 100)
    elif name == "pitch_variation":
        au.pitch_spread = _number(value, 0, 20)
    elif name == "sound_start":
        word = value.lower().replace(" ", "_").replace("-", "_")
        if word not in _START_WORDS:
            raise ValueError(f"'{value[:20]}' is not after_prompt or right_away")
        au.start_early = _START_WORDS[word]
    else:
        raise KeyError(name)


UNWRITABLE_NOTICE = ("Brain could not save its settings file, so changes last only until Brain closes. "
                     "The file belongs in the Brain folder inside Kitchensinc Revival in your AppData Roaming folder.")
IN_USE_NOTICE = "settings.txt is in use by another program, so Brain uses the original settings this time."
VOICE_MISSING_NOTICE = "The voice saved in the settings was not found, so the first voice is used."


class SettingsStore:
    """Loads, heals and saves settings.txt. Never raises. Notices are short sentences to speak once."""

    def __init__(self, folder: str | None = None, voice_name: Callable[[], str] = lambda: ""):
        self.folder = folder or paths.user_data_dir()
        self.path = os.path.join(self.folder, FILE_NAME)
        self.settings = Settings.defaults()
        self.voice_name = voice_name
        self._notices: list[str] = []
        self._problems: list[str] = []
        self._save_blocked = False       # the file could not be read: never write over what we did not read
        self._unwritable_noted = False

    # ----- loading -----

    def load(self) -> Settings:
        """Read settings.txt (creating or resetting it as needed) and return the settings in force."""
        try:
            self._load()
        except Exception:                # a last-resort net: whatever happens the original settings run
            log.exception("settings could not be loaded; using the original settings")
            self.settings = Settings.defaults()
        return self.settings

    def _load(self) -> None:
        self.settings = Settings.defaults()
        if not os.path.isfile(self.path):
            self._create("created")
            return
        try:
            settings, problems = parse(read_player_text(self.path))
        except OSError as exc:           # FileInUse, or any other failure to read the file
            log.warning("%s cannot be read now (%s); using the original settings, nothing is saved this run",
                        self.path, exc)
            self._save_blocked = True
            self._notices.append(IN_USE_NOTICE)
            return
        except (ValueError, UnicodeError) as exc:
            log.warning("%s is unusable (%s); resetting it", self.path, exc)
            saved = save_damaged_copy(self.path)
            if self._write(Settings.defaults()):
                self._notices.append("settings.txt was damaged and has been reset to the original settings."
                                     + (" A copy was saved." if saved else ""))
            return
        self.settings = settings
        self._problems = problems
        if problems:
            for problem in problems:
                log.warning("%s: %s", FILE_NAME, problem)
            count = len(problems)
            self._notices.append(f"{count} problem{'s' if count != 1 else ''} found in settings.txt, "
                                 "details are in the log.")

    def _create(self, why: str) -> None:
        if self._write(self.settings):
            log.info("%s %s", why, self.path)

    # ----- saving -----

    def save(self) -> bool:
        """Write the settings now (called after every change). False when it could not be written."""
        if self._save_blocked:
            return False
        return self._write(self.settings)

    def _write(self, settings: Settings) -> bool:
        try:
            name = self.voice_name() if settings.speech.voice_id else ""
        except Exception:
            name = ""
        if write_text_atomic(self.path, render(settings, name)):
            self._unwritable_noted = False
            return True
        if not self._unwritable_noted:
            self._unwritable_noted = True
            self._notices.append(UNWRITABLE_NOTICE)
        return False

    # ----- notices -----

    def note_voice_fallback(self, wanted: str | None, used: str) -> None:
        """The voice in settings.txt is not installed any more: say so once (the saved choice is kept)."""
        if wanted and wanted.lower() != (used or "").lower():
            self._notices.append(VOICE_MISSING_NOTICE)

    def note_voice_crashed(self, label: str, used: str) -> None:
        """The saved voice took the program down last time: say so once (the saved choice is kept, picking it again retries)."""
        self._notices.append(f"The voice {label} crashed Brain last time, so Brain uses {used or 'the first voice'} for now. "
                             "Choose it again in the voice list to try it again.")

    def take_notices(self) -> list[str]:
        notices, self._notices = self._notices, []
        return notices

    @property
    def problems(self) -> list[str]:
        return list(self._problems)
