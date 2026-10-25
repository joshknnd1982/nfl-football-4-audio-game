"""Audio layer: the original's seven sound slots plus one extra channel, with volume, pan, frequency and loops.
This is inspired by Jim Kitchen.

Built in P7 S7.2 (WAV_EVENT_MAP 1 to 4, GAME_SPEC 10, D-023, D-038; pygame-ce mixer, resampling by audioop, no numpy).
The game's sound procedures (game/sounds.py) use `Audio`; sounds are named by their IDs (`ids.py`).
"""
from .engine import Audio, SlotEvent, SystemBeeper
from .ids import BEEP_EXIT, SOUND_IDS, foot_id
from .library import Pick, SoundLibrary
from .output import (EXTRA_SLOT, SLOT_AMBIENT, SLOT_COUNT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE, SLOT_NAMES, SLOT_NOISE,
                     SLOT_ONESHOT, SLOT_TACKLE, TimedOutput)

__all__ = ["Audio", "SlotEvent", "SystemBeeper", "BEEP_EXIT", "SOUND_IDS", "foot_id", "Pick", "SoundLibrary",
           "EXTRA_SLOT", "SLOT_AMBIENT", "SLOT_COUNT", "SLOT_CROWD1", "SLOT_CROWD2", "SLOT_HIKE", "SLOT_NAMES",
           "SLOT_NOISE", "SLOT_ONESHOT", "SLOT_TACKLE", "TimedOutput"]
