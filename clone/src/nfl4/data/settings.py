"""Settings with the original's values as defaults. This is inspired by Jim Kitchen's Brain.

S7.1 holds the speech settings in memory only; P7 S7.5 saves and loads them (per user, plain
text, self-healing per playbook 7.10).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SpeechSettings:
    mode: str = "sapi"           # "sapi" (original), "nvda", "jaws", "auto"  (DECISIONS P6, P10 JAWS)
    voice_id: str | None = None  # None = first voice in SAPI's list (GAME_SPEC 3.1)
    rate: int | None = None      # None = the voice's own rate, read and kept (GAME_SPEC 3.1)
    volume: int = 90             # GAME_SPEC 3.1
    pitch: int = 0               # clone addition; 0 sends text exactly as the original did
    list_letters: str = "type"   # clone addition: letter keys in lists: "type" = type-ahead search, "first" = first-letter jump


@dataclass
class AudioSettings:
    effects_volume: int = 100    # percent; 100 = the original's SetVolume 0 (full volume, GAME_SPEC 5.4)
    pitch_spread: int = 20       # steps of 100 Hz: the original's r = Int(Rnd * 40) - 20 (GAME_SPEC 5.3); 0 = no change
    start_early: bool = False    # clone addition: False = the sounds wait for the spoken prompt (original); True = they start at once


@dataclass
class Settings:
    speech: SpeechSettings
    audio: AudioSettings = field(default_factory=AudioSettings)

    @classmethod
    def defaults(cls) -> "Settings":
        return cls(speech=SpeechSettings())
