"""The folder of a Franchise on disk, and the same in memory for the tests (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 10.1: league.sav is written in three steps (the new text to `league.sav.tmp`, the present league.sav
copied to `league.previous.sav`, the temporary file renamed to league.sav) so that at every moment one of the two files is
whole; each step is one method here (`write_tmp`, `copy`, `commit`), so a test can stop between any two of them. Nothing in
this module raises except `read` (FileInUse for a file held by another program, ValueError for a file over the size limit);
every write answers True or False.
"""
from __future__ import annotations

import logging
import os
import shutil
import time

from ...data.healing import FileInUse, save_damaged_copy, write_text_atomic
from . import data as D

log = logging.getLogger("nfl4.data")

TMP = ".tmp"
LOCK_RETRIES, LOCK_PAUSE = 3, 0.1


class DiskFiles:
    def __init__(self, folder: str):
        self.folder = folder

    def path(self, name: str) -> str:
        return os.path.join(self.folder, name)

    def exists(self, name: str) -> bool:
        return os.path.exists(self.path(name))

    def folder_exists(self) -> bool:
        return os.path.isdir(self.folder)

    def read(self, name: str) -> bytes | None:
        """The file whole; None when it is not there; FileInUse when it cannot be opened (held, no permission); ValueError
        when it is over the size limit (damage, not read)."""
        path = self.path(name)
        for attempt in range(LOCK_RETRIES):
            try:
                if os.path.getsize(path) > D.SAVE_MAX_BYTES:
                    raise ValueError("the file is far too large")
                with open(path, "rb") as handle:
                    return handle.read()
            except FileNotFoundError:
                return None
            except PermissionError as exc:
                if attempt + 1 < LOCK_RETRIES:
                    time.sleep(LOCK_PAUSE)
                    continue
                raise FileInUse(str(exc)) from exc
            except OSError as exc:
                raise FileInUse(str(exc)) from exc
        return None

    def write_tmp(self, name: str, data: bytes) -> bool:
        """Step 1: the new content to name + ".tmp", flushed to the disk."""
        path = self.path(name) + TMP
        try:
            os.makedirs(self.folder, exist_ok=True)
            with open(path, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            return True
        except OSError:
            log.exception("could not write %s", path)
            self.remove(name + TMP)
            return False

    def copy(self, source: str, target: str) -> bool:
        """Step 2: a copy of the present file (the previous one)."""
        try:
            shutil.copyfile(self.path(source), self.path(target))
            return True
        except OSError:
            log.exception("could not copy %s to %s", source, target)
            return False

    def commit(self, name: str) -> bool:
        """Step 3: the temporary file becomes the file (the moment a write counts)."""
        try:
            os.replace(self.path(name) + TMP, self.path(name))
            return True
        except OSError:
            log.exception("could not rename %s", name + TMP)
            return False

    def write(self, name: str, data: bytes) -> bool:
        return self.write_tmp(name, data) and self.commit(name)

    def write_text(self, name: str, text: str) -> bool:
        """history.txt: whole through a temporary file and a rename, for Notepad (UTF-8, Windows line ends)."""
        try:
            return write_text_atomic(self.path(name), text)
        except Exception:
            log.exception("could not write %s", name)
            return False

    def remove(self, name: str) -> None:
        try:
            os.remove(self.path(name))
        except FileNotFoundError:
            pass
        except OSError:
            log.exception("could not delete %s", name)

    def set_aside(self, name: str) -> None:
        """A copy of a damaged file (<name>.damagedN, three kept), then the file is removed."""
        path = self.path(name)
        if os.path.exists(path):
            save_damaged_copy(path)
            self.remove(name)

    def move(self, source: str, target: str) -> bool:
        try:
            os.makedirs(os.path.dirname(self.path(target)), exist_ok=True)
            os.replace(self.path(source), self.path(target))
            return True
        except OSError:
            log.exception("could not move %s to %s", source, target)
            return False


class MemoryFiles:
    """The same folder in memory (the tests' rigs): `held` names raise FileInUse when read; `unwritable` makes every write
    fail; `steps` lists the writes in order (a test can compare it with the three steps of design 10.1)."""

    def __init__(self):
        self.data: dict[str, bytes] = {}
        self.held: set[str] = set()
        self.unwritable = False
        self.steps: list[tuple] = []
        self.aside: list[str] = []

    def path(self, name: str) -> str:
        return "memory:" + name

    def exists(self, name: str) -> bool:
        return name in self.data

    def folder_exists(self) -> bool:
        return bool(self.data)

    def read(self, name: str) -> bytes | None:
        if name in self.held:
            raise FileInUse(name)
        data = self.data.get(name)
        if data is not None and len(data) > D.SAVE_MAX_BYTES:
            raise ValueError("the file is far too large")
        return data

    def write_tmp(self, name: str, data: bytes) -> bool:
        self.steps.append(("tmp", name))
        if self.unwritable:
            return False
        self.data[name + TMP] = data
        return True

    def copy(self, source: str, target: str) -> bool:
        self.steps.append(("copy", source, target))
        if self.unwritable or source not in self.data:
            return False
        self.data[target] = self.data[source]
        return True

    def commit(self, name: str) -> bool:
        self.steps.append(("commit", name))
        if self.unwritable or name + TMP not in self.data:
            return False
        self.data[name] = self.data.pop(name + TMP)
        return True

    def write(self, name: str, data: bytes) -> bool:
        return self.write_tmp(name, data) and self.commit(name)

    def write_text(self, name: str, text: str) -> bool:
        if self.unwritable:
            return False
        self.data[name] = text.replace("\n", "\r\n").encode("utf-8")
        return True

    def remove(self, name: str) -> None:
        self.data.pop(name, None)

    def set_aside(self, name: str) -> None:
        if name in self.data:
            self.aside.append(name)
            self.data.pop(name)

    def move(self, source: str, target: str) -> bool:
        if self.unwritable or source not in self.data:
            return False
        self.data[target] = self.data.pop(source)
        return True
