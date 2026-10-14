"""Audio layer: wav playback with per-sound pitch and pan, nine slots. This is inspired by Jim Kitchen's Brain.

Built in P7 S7.2 (GAME_SPEC 5, 10; DECISIONS P6: pygame-ce mixer; resampling by audioop, no numpy since 1.0.3).
The game logic (S7.3) uses `SoundLibrary` (what to play) and `Audio` (how to play it).
"""
from .engine import Audio, SystemBeeper
from .library import Pick, SoundLibrary, sound_id
from .output import SLOT_COUNT, TimedOutput

__all__ = ["Audio", "SystemBeeper", "Pick", "SoundLibrary", "sound_id", "SLOT_COUNT", "TimedOutput"]
