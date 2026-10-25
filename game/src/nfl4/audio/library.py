"""Sound library: finds the sound for an ID. This is inspired by Jim Kitchen.

Resolution chain (playbook 7.7, SOUND_DESIGN 6), first that loads wins:
  1. the player's file for the ID (sounds folder in per-user data; sounds.txt may name another file)
  2. the original wav that ships with the game (assets/sounds, D-001)
  3. a generated sound (only beep_exit has one; its full chain is in engine.Audio.beep_exit)
  4. silence, with a log line
A file that is damaged, empty or very long is skipped, logged once, and the next choice is used. The first time per
start that a file cannot be used (or a sound has no usable file at all) the library gives ONE spoken notice: the
original's unused sentence followed by the kit's (GAP_REGISTER G-A6, SOUND_DESIGN 5). A file that is merely absent
from the player's folder is the normal way to the shipped sound and gives no notice.

IDs: snd_foot0 to snd_foot25 and beep_exit (audio/ids.py); a player's file may be named foot7.wav or snd_foot7.wav.
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass

from ..data import paths
from .ids import SOUND_IDS, canonical_id, file_stems, foot_id, foot_number
from .pools import POOL_ORDER, POOLS, Member, next_free_number, scan_added
from .soundsconfig import SoundEntry, SoundsConfig, load_or_heal
from .tonegen import generated
from .wavdata import DECODER_EXTENSIONS, Sampled, SoundLoadError, load_sound_file

log = logging.getLogger("nfl4.audio")

_MAX_DECODED = 200   # decoded files kept between refreshes (the shipped set is 26)

# The original's own sentence for this case, never used by the original (string 2568, no reference in the exe,
# SOUND_DESIGN 2 and 5), then the kit's sentence. Marked CLONE in the conformance tests (GAP_REGISTER 8).
ORIGINAL_CORRUPT_TEXT = "Sorry but one or more of the wave files seem to be corrupt"
KIT_SKIPPED_TEXT = "A sound file could not be used and was skipped, details are in the log."
SOUND_FILE_NOTICE = f"{ORIGINAL_CORRUPT_TEXT}. {KIT_SKIPPED_TEXT}"


@dataclass(frozen=True)
class Pick:
    """What a request for one sound resolved to."""
    sound_id: str
    sound: Sampled | None     # None: nothing playable
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
        self._file_picks: dict[tuple, Pick] = {}
        self._reported: dict[tuple, str] = {}
        self._notices: list[str] = []
        self._file_notice_given = False      # G-A6: one notice per start
        self._added: dict[str, list[tuple[int, str]]] = {}   # pool -> the player's added files (number, real name)
        self._members: dict[str, list[Member]] = {}
        self.refresh()

    # ----- state -----

    def refresh(self) -> None:
        """Rescan both folders and sounds.txt (start-up, the sounds menu's reload).

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
            self._file_picks.clear()
            self._members.clear()
            self._added = {}
            for name in POOL_ORDER:
                added, skipped = scan_added(POOLS[name], self._player)
                self._added[name] = added
                for extra in skipped:
                    self._report(("twice", name, extra.lower()),
                                 f"{extra}: another file has the same number in the {name} pool, so this one is not used")

    @property
    def problems(self) -> list[str]:
        """Plain reasons for everything found wrong so far (sounds.txt lines, unusable files)."""
        with self._lock:
            return list(self._config.problems) + list(self._reported.values())

    def check_all(self) -> list[str]:
        """Resolve every sound once (start-up and the sounds menu's check command) and return the problems."""
        for sound_id in SOUND_IDS:
            self.pick(sound_id)
        for name in POOL_ORDER:
            self.pool_members(name)               # reads every added file once; the unusable ones are reported
        return self.problems

    def take_notices(self) -> list[str]:
        """Short sentences worth speaking (damage, bad files); each is returned once."""
        with self._lock:
            notices, self._notices = self._notices, []
            return notices

    # ----- lookup -----

    def pick(self, wanted_id: str) -> Pick:
        key = canonical_id(wanted_id)
        with self._lock:
            cached = self._picks.get(key)
            if cached is None:
                cached = self._resolve(key)
                self._picks[key] = cached
            return cached

    # ----- numbered pools (owner rule 0.14, playbook 7.7.1, audio/pools.py) -----

    def pool_members(self, pool_name: str) -> list[Member]:
        """What a pool draws from now, in draw order: the original members (foot8 to foot10; foot15 to foot24) that are not
        switched off in sounds.txt, then the player's added files by number whose file can be used. An original member with
        no usable file stays in (it plays silence, as it always did, so the draws do not move); an added file that cannot
        be read is left out, logged and counted in the one spoken notice. With nothing added and nothing off this is the
        original's list."""
        pool = POOLS[pool_name]
        with self._lock:
            cached = self._members.get(pool_name)
            if cached is not None:
                return list(cached)
            members = [Member(foot_id(n), None, n) for n in pool.originals if self.pick(foot_id(n)).source != "off"]
            for number, real in self._added.get(pool_name, []):
                path = os.path.join(self.player_dir, real)
                if self.pick_file(path).sound is not None:
                    members.append(Member(None, path, number))
            self._members[pool_name] = members
            return list(members)

    def pool_summary(self, pool_name: str) -> tuple[int, int, int]:
        """(original members in the draw, added files in the draw, the next free number) for the Sounds menu."""
        pool = POOLS[pool_name]
        members = self.pool_members(pool_name)
        added = sum(1 for m in members if m.added)
        with self._lock:
            return len(members) - added, added, next_free_number(pool, self._added.get(pool_name, []))

    def pick_for(self, member: Member) -> Pick:
        """The sound of a pool member: an original by its ID, an added file by its place."""
        return self.pick(member.sound_id) if member.sound_id is not None else self.pick_file(member.path)

    def pick_file(self, path: str) -> Pick:
        """A sound file of the player's that is named by its place, not by an ID (the banter's `[sound file.wav]`, D-048).

        The same rules as an ID's file: a file that is missing, empty, damaged or very long gives a Pick with no sound (it
        plays nothing and nothing waits for it), is logged once per file state, and gives the one spoken sound notice of
        G-A6 per start. The Pick is kept so the render cache of a sound that plays often is kept too."""
        label = "file " + os.path.basename(path)
        with self._lock:
            try:
                stat = os.stat(path)
                if not os.path.isfile(path):                  # a folder, a device: never opened
                    raise OSError("not a file")
            except OSError:
                self._report(("missing file", path.lower()), f"{label}: the file was not found", speak=True)
                return Pick(label, None, "none", path)
            key = (path.lower(), stat.st_mtime_ns, stat.st_size)
            cached = self._file_picks.get(key)
            if cached is not None:
                return cached
            try:
                sound = self._decode(path, stat)
            except SoundLoadError as exc:
                self._report(("bad", path, stat.st_mtime_ns, stat.st_size),
                             f"{label} cannot be used ({exc})", speak=True)
                pick = Pick(label, None, "none", path)
            else:
                pick = Pick(label, sound, "player", path)
            if len(self._file_picks) >= _MAX_DECODED:
                self._file_picks.clear()
            self._file_picks[key] = pick
            return pick

    def _candidates(self, key: str, entry: SoundEntry | None) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        if entry is not None and entry.file:
            named = entry.file if os.path.isabs(entry.file) else self._player.get(entry.file.lower())
            if named and not os.path.isabs(named):
                named = os.path.join(self.player_dir, named)
            if named and os.path.isfile(named):
                found.append(("player", named))
            else:
                self._report(("missing", key, entry.file), f"{key}: the file '{entry.file}' named in sounds.txt was not found")
        for stem in file_stems(key):
            for ext in DECODER_EXTENSIONS:
                real = self._player.get(stem + ext)
                if real:
                    found.append(("player", os.path.join(self.player_dir, real)))
        number = foot_number(key)
        if number is not None:
            real = self._shipped.get(f"foot{number}.wav")
            if real:
                found.append(("original", os.path.join(self.shipped_dir, real)))
        return found

    def _resolve(self, key: str) -> Pick:
        entry = self._config.get(key)
        trim = entry.volume if entry else 1.0
        if entry and entry.off:
            # GAP_REGISTER G-A3, D-038: a sound switched off plays nothing and nothing waits for it (a player who wants
            # a pause uses a silent file of that length, which plays like any other sound)
            return Pick(key, None, "off", None, trim)
        for source, path in self._candidates(key, entry):
            try:
                stat = os.stat(path)
            except OSError as exc:
                log.debug("%s: candidate %s cannot be read (%s); the next link of the chain", key, path, exc)
                continue
            try:
                sound = self._decode(path, stat)
            except SoundLoadError as exc:
                self._report(("bad", path, stat.st_mtime_ns, stat.st_size),
                             f"{key}: {os.path.basename(path)} cannot be used ({exc})", speak=True)
                continue
            return Pick(key, sound, source, path, trim)
        fallback = generated(key)
        if fallback is not None:
            return Pick(key, fallback, "generated", None, trim)
        if key in SOUND_IDS:
            self._report(("silent", key), f"{key}: no usable sound file, it stays silent", speak=True)
        else:
            self._report(("unknown", key), f"{key}: not a sound of this game, it stays silent")
        return Pick(key, None, "none", None, trim)

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
        """Log a problem once per file state; remember it for 'check files'; one spoken notice per start."""
        if key in self._reported:
            return
        self._reported[key] = text
        log.warning(text)
        if speak and not self._file_notice_given:
            self._file_notice_given = True
            self._notices.append(SOUND_FILE_NOTICE)


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
