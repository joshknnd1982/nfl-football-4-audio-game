"""Numbered sound pools the player can extend. This is inspired by Jim Kitchen.

Owner rule 0.14 (2026-10-16), playbook 7.7.1, WAV_EVENT_MAP 8. The original draws among numbered wavs for two events
only: the ambient sounds while a key is awaited (foot8, foot9, foot10: PlayRan) and the celebration sounds (foot15 to
foot24: playcel, halftime, superbowl, finplay17). Every other foot<N> is a different sound for a different event (foot4
to foot6 are chosen by the kind of tackle, foot14 is the play noise ...), so it is not a pool and takes no added files.

All 26 files share the base "foot", so added files cannot use it (foot26.wav would say nothing about its event). A pool
therefore has a plain-word name, and the player's added files use it as their base: celebration10.wav, ambient4.wav.
The names are scanned from the sounds folder (never probed number by number), in any case, with any extension the sound
layer reads, any count of digits, in number order, gaps allowed. With nothing added a pool is exactly the original's
list, so every random draw of the original is unchanged (golden transcript).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .wavdata import DECODER_EXTENSIONS

log = logging.getLogger("nfl4.audio")

MAX_ADDED = 5000        # a folder with more matching names than this is cut here (logged); far above any real use


@dataclass(frozen=True)
class Pool:
    name: str                    # the base of an added file's name: celebration3.wav
    label: str                   # plain words for the menu
    originals: tuple[int, ...]   # the foot numbers of the original members, in the original's draw order


POOLS: dict[str, Pool] = {
    "ambient": Pool("ambient", "ambient sounds while a key is awaited", (8, 9, 10)),
    "celebration": Pool("celebration", "celebration sounds", tuple(range(15, 25))),
}
POOL_ORDER = ("ambient", "celebration")


@dataclass(frozen=True)
class Member:
    """One sound a pool can draw. Originals are played by their ID (the same call the original's draw made), added
    members by their file."""
    sound_id: str | None         # snd_foot9 ...; None for an added file
    path: str | None             # the added file's full path; None for an original
    number: int                  # foot number for an original, the number in the file name for an added one

    @property
    def added(self) -> bool:
        return self.path is not None


def added_pattern(pool: Pool) -> re.Pattern:
    extensions = "|".join(re.escape(ext) for ext in DECODER_EXTENSIONS)
    return re.compile(rf"^{re.escape(pool.name)}(\d+)({extensions})$")


def scan_added(pool: Pool, listing: dict[str, str]) -> tuple[list[tuple[int, str]], list[str]]:
    """The player's added files of a pool: [(number, real file name)] in number order, and the names left out.

    `listing` maps the lower-case file name to the real name (the library's case-insensitive seam). Two files with the
    same number (celebration7.wav and celebration07.ogg) count once: the first by name is used, the other is reported."""
    pattern = added_pattern(pool)
    found: dict[int, list[str]] = {}
    for lower, real in listing.items():
        match = pattern.match(lower)
        if match:
            found.setdefault(int(match.group(1)), []).append(real)
    chosen: list[tuple[int, str]] = []
    skipped: list[str] = []
    for number in sorted(found):
        names = sorted(found[number], key=str.lower)
        chosen.append((number, names[0]))
        skipped.extend(names[1:])
    if len(chosen) > MAX_ADDED:
        log.warning("the %s pool has %d added files; only the first %d are used", pool.name, len(chosen), MAX_ADDED)
        skipped.extend(name for _, name in chosen[MAX_ADDED:])
        chosen = chosen[:MAX_ADDED]
    return chosen, skipped


def next_free_number(pool: Pool, added: list[tuple[int, str]]) -> int:
    """The number the Sounds menu suggests for the next added file: one past the highest number used by an added file
    (the originals are named foot<N>, so their numbers never collide with the pool's base)."""
    return max((number for number, _ in added), default=0) + 1
