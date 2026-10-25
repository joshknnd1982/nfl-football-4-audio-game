"""SAPI 5 voice list for the voice setting. This is inspired by Jim Kitchen.

Taken from SAPI's own enumeration (GetVoices), not the registry: on the owner's PC SAPI lists
1,789 voices and the registry 249, and Brain's default is SAPI's item 0 (DECISIONS P6).
Reading all 1,789 names and IDs took 0.24 s (64-bit) and 0.34 s (32-bit) in S7.1, so the list
is still built on a background thread with its own COM apartment, cached, and refreshed only
on request (playbook 7.4). One broken entry is logged and skipped, never stopping the list.
No COM voice is created per entry; only the chosen voice is used by the speech thread.
Bitness: each build lists the voices its own bitness can use (separate 32- and 64-bit builds).
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoiceInfo:
    index: int        # position in SAPI's list; index 0 is the original's choice
    voice_id: str     # token ID, saved in settings
    name: str         # description read to the player
    engine: str = ""  # the speech engine that provides it (registry enumerator or vendor), for the engine list


def default_token_source():
    import win32com.client
    return win32com.client.Dispatch("SAPI.SpVoice").GetVoices("", "")


ENGINE_FALLBACK = "Other voices"


def engine_of(token, voice_id: str) -> str:
    """The engine a voice belongs to: the name of its registry enumerator (TokenEnums, one per engine that
    lists its own voices), else the Vendor attribute of an installed voice token. No COM voice is created."""
    parts = voice_id.split(chr(92))
    if "TokenEnums" in parts:
        at = parts.index("TokenEnums") + 1
        if at < len(parts) - 1 and parts[at].strip():
            return parts[at].strip()
    try:
        vendor = str(token.GetAttribute("Vendor")).strip()
        if vendor:
            return vendor
    except Exception as exc:
        log.debug("voice %s has no Vendor attribute (%s)", voice_id, exc)
    return ENGINE_FALLBACK


def group_by_engine(voices: list[VoiceInfo]) -> list[tuple[str, list[VoiceInfo]]]:
    """(engine, its voices) for every engine, engines in alphabetical order, voices in SAPI's order."""
    groups: dict[str, list[VoiceInfo]] = {}
    for voice in voices:
        groups.setdefault(voice.engine or ENGINE_FALLBACK, []).append(voice)
    return sorted(groups.items(), key=lambda item: item[0].casefold())


def _initial(name: str) -> str:
    for char in name:
        if char.isalnum():
            return char.casefold()
    return ""


def first_letter_index(names: list[str], char: str, current: int) -> int | None:
    """The next name after current (wrapping round) that starts with char; None when there is none.
    Pressing the same letter again therefore goes on to the one after."""
    count = len(names)
    char = char.casefold()
    for step in range(1, count + 1):
        i = (current + step) % count
        if _initial(names[i]) == char:
            return i
    return None


def enumerate_voices(token_source=default_token_source) -> tuple[list[VoiceInfo], int]:
    """Return (voices, number of broken entries skipped). Never raises."""
    try:
        tokens = token_source()
        count = int(tokens.Count)
    except Exception as exc:
        log.warning("voice list unavailable: %s", exc)
        return [], 0
    voices: list[VoiceInfo] = []
    broken = 0
    for i in range(count):
        try:
            token = tokens.Item(i)
            voice_id = str(token.Id)
            try:
                name = str(token.GetDescription()).strip()
            except Exception:
                name = ""
            voices.append(VoiceInfo(i, voice_id, name or voice_id.rsplit("\\", 1)[-1], engine_of(token, voice_id)))
        except Exception as exc:
            broken += 1
            if broken <= 10:
                log.warning("voice %d skipped: %s", i, exc)
    if broken:
        log.warning("%d broken voice entries skipped of %d", broken, count)
    return voices, broken


def search(voices: list[VoiceInfo], text: str) -> list[VoiceInfo]:
    """Voices whose name starts with text first, then those containing it (case-insensitive)."""
    needle = text.strip().casefold()
    if not needle:
        return list(voices)
    starts = [v for v in voices if v.name.casefold().startswith(needle)]
    first = {v.index for v in starts}
    contains = [v for v in voices if needle in v.name.casefold() and v.index not in first]
    return starts + contains


class VoiceCatalog:
    """Cached voice list, built off the main thread."""

    def __init__(self, token_source=default_token_source, com_init=True):
        self._token_source = token_source
        self._com_init = com_init
        self._lock = threading.Lock()
        self._voices: list[VoiceInfo] | None = None
        self._broken = 0
        self._loaded = threading.Event()
        self._thread: threading.Thread | None = None

    def load_async(self, refresh: bool = False) -> None:
        """Start building the list in the background (again, if refresh is True)."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            if self._voices is not None and not refresh:
                return
            self._loaded.clear()
            self._thread = threading.Thread(target=self._build, name="voice-list", daemon=True)
            self._thread.start()

    def voices(self, timeout: float | None = 10.0) -> list[VoiceInfo]:
        """The cached list; starts loading if needed and waits up to timeout."""
        self.load_async()
        self._loaded.wait(timeout)
        with self._lock:
            return list(self._voices or [])

    @property
    def loaded(self) -> bool:
        """True once a list was built (it may be empty)."""
        return self._loaded.is_set()

    @property
    def broken(self) -> int:
        return self._broken

    def _build(self) -> None:
        pythoncom = None
        if self._com_init:
            import pythoncom
            pythoncom.CoInitialize()
        try:
            voices, broken = enumerate_voices(self._token_source)
            with self._lock:
                self._voices, self._broken = voices, broken
        finally:
            self._loaded.set()
            if pythoncom is not None:
                pythoncom.CoUninitialize()
