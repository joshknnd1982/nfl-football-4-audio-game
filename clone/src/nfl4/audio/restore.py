"""Reset commands for the player's sounds: one sound or all (playbook 7.7, 7.10). This is inspired by Jim Kitchen's Brain.

"Restore" means: the original plays again. A sound the player put in the sounds folder under the
sound's own name (brain5.wav, beep_exit.wav) would keep overriding it, so it is moved, never
deleted, into the folder "removed sounds" inside the sounds folder, where the player can take it
back. Files named freely and pointed at by a `file=` entry stay where they are (other sounds may use
them); with the entry gone they are simply not used.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

from ..data.healing import save_backup_copy, write_text_atomic
from .soundsconfig import DEFAULT_TEXT, FILE_NAME, canonical_id, drop_entry
from .wavdata import DECODER_EXTENSIONS

log = logging.getLogger("nfl4.audio")

REMOVED_FOLDER = "removed sounds"
BACKUP_SUFFIX = ".before-reset"
_ID_NAMED = re.compile(r"^(brain0*\d+|beep_exit)$", re.IGNORECASE)


@dataclass
class RestoreResult:
    moved: list[str] = field(default_factory=list)    # file names put into the removed sounds folder
    entry_removed: bool = False                        # a line left sounds.txt
    failed: bool = False                               # something could not be done (details in the log)

    @property
    def changed(self) -> bool:
        return bool(self.moved) or self.entry_removed


def _id_named_files(player_dir: str, only: str | None = None) -> list[str]:
    try:
        names = sorted(os.listdir(player_dir))
    except OSError:
        return []
    found = []
    for name in names:
        stem, ext = os.path.splitext(name)
        if ext.lower() not in DECODER_EXTENSIONS or not _ID_NAMED.match(stem):
            continue
        if only is not None and canonical_id(stem) != canonical_id(only):
            continue
        if os.path.isfile(os.path.join(player_dir, name)):
            found.append(name)
    return found


def _move_aside(player_dir: str, names: list[str], result: RestoreResult) -> None:
    if not names:
        return
    target_dir = os.path.join(player_dir, REMOVED_FOLDER)
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError:
        log.exception("could not create %s", target_dir)
        result.failed = True
        return
    for name in names:
        stem, ext = os.path.splitext(name)
        target = os.path.join(target_dir, name)
        copy = 1
        while os.path.exists(target):
            copy += 1
            target = os.path.join(target_dir, f"{stem} ({copy}){ext}")
        try:
            os.replace(os.path.join(player_dir, name), target)
            result.moved.append(name)
        except OSError:
            log.exception("could not move %s aside", name)
            result.failed = True


def restore_sound(player_dir: str, sound_id: str) -> RestoreResult:
    """One sound back to the original: its sounds.txt line is removed and its own-named files are moved aside."""
    result = RestoreResult()
    result.entry_removed = drop_entry(player_dir, sound_id)
    _move_aside(player_dir, _id_named_files(player_dir, sound_id), result)
    log.info("restored %s: %s", sound_id, result)
    return result


def restore_all_sounds(player_dir: str) -> RestoreResult:
    """Every sound back to the original: sounds.txt is rewritten (the old one kept once as sounds.txt.before-reset)
    and every own-named sound file is moved aside, the added brain43, brain44 ... included."""
    result = RestoreResult()
    path = os.path.join(player_dir, FILE_NAME)
    if os.path.isfile(path):
        save_backup_copy(path, BACKUP_SUFFIX)
    if write_text_atomic(path, DEFAULT_TEXT):
        result.entry_removed = True
    else:
        result.failed = True
    _move_aside(player_dir, _id_named_files(player_dir), result)
    log.info("restored all sounds: %s", result)
    return result
