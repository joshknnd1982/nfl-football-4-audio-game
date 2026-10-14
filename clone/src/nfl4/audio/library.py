"""Sound library: finds the sound for an ID. This is inspired by Jim Kitchen's Brain.

Resolution chain (playbook 7.7), first that loads wins:
  1. the player's file for the ID (sounds folder in per-user data; sounds.txt may name another file)
  2. the original wav that ships with the clone (assets/sounds, Jim Kitchen's permission, DECISIONS)
  3. a generated sound (only beep_exit has one)
  4. silence, with a log line
A player's file that is damaged, empty or very long is skipped, logged once, and the next choice is used.

IDs: brain1 .. brainN (written brain01 .. in the spec; both spellings of the number are found,
files are named like the original's brain5.wav or padded brain05.wav) and beep_exit.

Pool (DECISIONS P4): N = highest number such that brain1 .. brainN all exist (player or shipped);
the original counted files and picked 1..count, which made gaps silent. Files beyond a gap are
logged and not used. `pool_size()` is the raw N; the game logic uses max(1, N) (GAME_SPEC 5.2).
"""
from __future__ import annotations

import logging
import os
import re
import threading
from dataclasses import dataclass

from ..data import paths
from .soundsconfig import SoundEntry, SoundsConfig, canonical_id, load_or_heal
from .tonegen import GENERATED_SOUNDS, generated
from .wavdata import DECODER_EXTENSIONS, Sampled, SoundLoadError, load_sound_file

log = logging.getLogger("nfl4.audio")

_NUMBERED = re.compile(r"^brain0*(\d+)$", re.IGNORECASE)
_MAX_DECODED = 200   # decoded files kept between refreshes (the shipped set is 42)


def sound_id(number: int) -> str:
    """The spec's ID for a wav number: brain01 .. brain09, brain10 .."""
    return f"brain{number:02d}"


@dataclass(frozen=True)
class Pick:
    """What a request for one sound resolved to. Mirrors what the original's statements saw."""
    sound_id: str
    sound: Sampled | None     # None: nothing playable (the original's failed CreateSoundBufferFromFile)
    size: int | None          # bytes of the file the original's FileLen would read; None: no file at all
    source: str               # "player", "original", "generated", "off" or "none"
    path: str | None = None
    volume: float = 1.0       # trim from sounds.txt, linear

    @property
    def rate(self) -> int | None:
        """The sound's own sample rate: the original's GetFrequency."""
        return self.sound.rate if self.sound is not None else None


class SoundLibrary:
    def __init__(self, shipped_dir: str | None = None, player_dir: str | None = None):
        self.shipped_dir = shipped_dir or shipped_sounds_dir()
        self.player_dir = player_dir or player_sounds_dir()
        self._lock = threading.RLock()
        self._config = SoundsConfig()
        self._shipped: dict[str, str] = {}
        self._player: dict[str, str] = {}
        self._picks: dict[str, Pick] = {}
        self._decoded: dict[tuple, Sampled] = {}
        self._reported: dict[tuple, str] = {}
        self._notices: list[str] = []
        self._pool = 0
        self.refresh()

    # ----- state -----

    def refresh(self) -> None:
        """Rescan both folders and sounds.txt (start of every playback, Sounds menu reload).

        Missing folder or sounds.txt is recreated, a damaged one is reset (playbook 7.10)."""
        with self._lock:
            config, notices = load_or_heal(self.player_dir)
            self._config = config
            self._notices.extend(notices)
            # damage reports stay (they belong to one file state); the rest is recomputed
            self._reported = {k: v for k, v in self._reported.items() if k[0] == "bad"}
            self._shipped = _listing(self.shipped_dir)
            self._player = _listing(self.player_dir)
            self._picks.clear()
            self._pool = self._count_pool()

    @property
    def problems(self) -> list[str]:
        """Plain reasons for everything found wrong so far (sounds.txt lines, unusable files)."""
        with self._lock:
            return list(self._config.problems) + list(self._reported.values())

    def check_all(self) -> list[str]:
        """Resolve every sound once (the Sounds menu's check command) and return the problems."""
        for number in range(1, self._pool + 1):
            self.pick_number(number)
        self.pick("beep_exit")
        return self.problems

    def take_notices(self) -> list[str]:
        """Short sentences worth speaking (damage, bad files); each is returned once."""
        with self._lock:
            notices, self._notices = self._notices, []
            return notices

    def pool_size(self) -> int:
        """N: brain1 .. brainN all exist. 0 when nothing is there (the logic then uses 1)."""
        return self._pool

    # ----- lookup -----

    def pick_number(self, number: int) -> Pick:
        return self.pick(sound_id(number))

    def pick(self, wanted_id: str) -> Pick:
        key = canonical_id(wanted_id)
        match = _NUMBERED.match(key)
        with self._lock:
            cached = self._picks.get(key)
            if cached is None:
                cached = self._resolve(key, int(match.group(1)) if match else None)
                self._picks[key] = cached
            return cached

    def _candidates(self, key: str, number: int | None, entry: SoundEntry | None) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        if entry is not None and entry.file:
            named = entry.file if os.path.isabs(entry.file) else self._player.get(entry.file.lower())
            if named and not os.path.isabs(named):
                named = os.path.join(self.player_dir, named)
            if named and os.path.isfile(named):
                found.append(("player", named))
            else:
                self._report(("missing", key, entry.file), f"{key}: the file '{entry.file}' named in sounds.txt was not found")
        stems = [f"brain{number}", f"brain{number:02d}"] if number is not None else [key]
        for stem in dict.fromkeys(stems):
            for ext in DECODER_EXTENSIONS:
                real = self._player.get(stem + ext)
                if real:
                    found.append(("player", os.path.join(self.player_dir, real)))
        if number is not None:
            real = self._shipped.get(f"brain{number}.wav")
            if real:
                found.append(("original", os.path.join(self.shipped_dir, real)))
        return found

    def _resolve(self, key: str, number: int | None) -> Pick:
        entry = self._config.get(key)
        trim = entry.volume if entry else 1.0
        size: int | None = None
        for source, path in self._candidates(key, number, entry):
            try:
                stat = os.stat(path)
            except OSError:
                continue
            if size is None:
                size = stat.st_size            # the file the original would have read (FileLen)
            try:
                sound = self._decode(path, stat)
            except SoundLoadError as exc:
                self._report(("bad", path, stat.st_mtime_ns, stat.st_size),
                             f"{key}: {os.path.basename(path)} cannot be used ({exc})", speak=True)
                continue
            return Pick(key, sound.silenced() if entry and entry.off else sound,
                        stat.st_size, "off" if entry and entry.off else source, path, trim)
        fallback = generated(key)
        if fallback is not None:
            return Pick(key, fallback.silenced() if entry and entry.off else fallback, None,
                        "off" if entry and entry.off else "generated", None, trim)
        self._report(("silent", key), f"{key}: no usable sound file, it stays silent")
        return Pick(key, None, size, "none", None, trim)

    def _decode(self, path: str, stat: os.stat_result) -> Sampled:
        cache_key = (path.lower(), stat.st_mtime_ns, stat.st_size)
        sound = self._decoded.get(cache_key)
        if sound is None:
            sound = load_sound_file(path)
            if len(self._decoded) >= _MAX_DECODED:
                self._decoded.clear()
            self._decoded[cache_key] = sound
        return sound

    def _report(self, key: tuple, text: str, speak: bool = False) -> None:
        """Log a problem once per file state; remember it for 'check files'."""
        if key in self._reported:
            return
        self._reported[key] = text
        log.warning(text)
        if speak:
            self._notices.append("A sound file could not be used and was skipped, details are in the log.")

    # ----- pool -----

    def _count_pool(self) -> int:
        def present(number: int) -> bool:
            if f"brain{number}.wav" in self._shipped:
                return True
            for stem in (f"brain{number}", f"brain{number:02d}"):
                if any(stem + ext in self._player for ext in DECODER_EXTENSIONS):
                    return True
            entry = self._config.get(sound_id(number))
            return bool(entry and entry.file and entry.file.lower() in self._player)

        n = 0
        while present(n + 1):
            n += 1
        extra = sorted({int(m.group(1)) for name in list(self._player) + list(self._shipped)
                        if (m := re.match(r"^brain0*(\d+)\.", name)) and int(m.group(1)) > n + 1})
        if extra:
            self._report(("gap", n, tuple(extra)),
                         f"brain{n + 1} is missing, so the sounds {', '.join(f'brain{e}' for e in extra[:5])}"
                         f"{' ...' if len(extra) > 5 else ''} are not used (numbers must follow each other)")
        return n


def _listing(folder: str) -> dict[str, str]:
    """lower-case file name -> real name (case-insensitive lookup seam, playbook 7.2)."""
    try:
        return {name.lower(): name for name in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, name))}
    except OSError:
        return {}


def shipped_sounds_dir() -> str:
    return os.path.join(paths.program_dir(), "assets", "sounds")


def player_sounds_dir() -> str:
    return os.path.join(paths.user_data_dir(), "sounds")


KNOWN_GENERATED = tuple(GENERATED_SOUNDS)
