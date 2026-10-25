"""The sound IDs of NFL Football 4. This is inspired by Jim Kitchen.

WAV_EVENT_MAP 2 and SOUND_DESIGN 6: snd_foot0 to snd_foot25 are the original's foot0.wav to foot25.wav, beep_exit is
the system beep of the exit (SOUND_DESIGN 4). Code uses only these IDs (playbook 7.7). A player may name a file or a
sounds.txt line by the ID or by the original's file name (foot7 = snd_foot7), in any case.
The event names are the ones the owner confirmed in the listening rounds (WAV_EVENT_MAP 6); they are only words for
the player, never IDs.
"""
from __future__ import annotations

import re

FOOT_COUNT = 26
BEEP_EXIT = "beep_exit"

EVENT_NAMES = {
    0: "intro music", 1: "crowd bed 1", 2: "crowd bed 2", 3: "hike", 4: "hit, pile up", 5: "hit, two tacklers",
    6: "hit, single tackle", 7: "kick", 8: "ambient sound 1", 9: "ambient sound 2", 10: "ambient sound 3, panned",
    11: "whistle", 12: "ball contact", 13: "bleep", 14: "play noise", 15: "celebration 15", 16: "celebration 16",
    17: "celebration 17", 18: "celebration 18", 19: "celebration 19", 20: "celebration 20", 21: "celebration 21",
    22: "celebration 22", 23: "celebration 23", 24: "celebration 24", 25: "Super Bowl",
}

_FOOT = re.compile(r"^(?:snd_)?foot0*(\d+)$")


def foot_id(number: int) -> str:
    """The ID of the original's foot<number>.wav."""
    return f"snd_foot{int(number)}"


SOUND_IDS = tuple(foot_id(n) for n in range(FOOT_COUNT)) + (BEEP_EXIT,)


def canonical_id(name: str) -> str:
    """snd_foot7, SND_FOOT7, foot7 and foot07 are one sound: snd_foot7. Other names are lower-cased (and unknown
    unless they are beep_exit)."""
    key = name.strip().lower()
    match = _FOOT.match(key)
    if match and int(match.group(1)) < FOOT_COUNT:
        return foot_id(int(match.group(1)))
    return key


def is_known(name: str) -> bool:
    return canonical_id(name) in SOUND_IDS


def foot_number(sound_id: str) -> int | None:
    """7 for snd_foot7; None for beep_exit and unknown names."""
    match = _FOOT.match(canonical_id(sound_id))
    return int(match.group(1)) if match else None


def file_stems(sound_id: str) -> tuple[str, ...]:
    """The file names (without extension) a player's file for this sound may have, in the order they are tried."""
    number = foot_number(sound_id)
    if number is None:
        return (canonical_id(sound_id),)
    return (f"foot{number}", f"snd_foot{number}")


def describe(sound_id: str) -> str:
    """Plain words for a sound: "foot7, kick"; "beep_exit, the exit beep"."""
    number = foot_number(sound_id)
    if number is None:
        return "beep_exit, the exit beep" if canonical_id(sound_id) == BEEP_EXIT else sound_id
    return f"foot{number}, {EVENT_NAMES[number]}"
