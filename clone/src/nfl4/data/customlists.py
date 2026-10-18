"""Customization list files: one plain text file per list, healed when damaged. This is inspired by Jim Kitchen.

Playbook 7.9 and 7.10, D-032 item 7, D-048. nfl4 is the first game with customization lists, so this is the format
"chosen once" and reused by every later game (the module is generic: the game's own name and its lists are arguments, and
it knows nothing about football). The file:

    # NFL Football 4 teams, format 1.        <- the header: the game, the list, the format version (always the first line)
    # plain-word notes, one `#` line each
    T01 = Bengals                            <- one entry per line: a permanent ID, an equals sign, the value
    T02 = Browns

Plain UTF-8 (a byte order mark and UTF-16 with a byte order mark are accepted, the Windows code page is the fallback),
CRLF or LF, blank lines and `#` lines ignored, spaces around the equals sign and at the ends ignored, the ID not case
sensitive. Strict formats (JSON) are not used: one missing comma must not break a file the player edits.

What is a damaged (unusable) file and what is only a bad line, playbook 7.10:
* unusable: empty, binary or undecodable, far too large, no header on its first line, the header of another list or of
  another game, a format version this program does not read (older or newer). The file is copied to <name>.damagedN (three
  kept), recreated from the built-in values, and ONE notice says so. Nothing the player wrote is lost.
* a bad line (not `ID = value`, or a value the list's rules refuse) is skipped, the built-in value is used for its ID and the
  list's code counts it: ONE spoken summary per file ("2 problems found in teams.txt, details are in the log").
* a file that is missing is recreated silently (the first start, or the player deleted it to get the originals back);
* a file held by another program is not damaged: the built-in values are used, nothing is copied or written, one notice;
* a file that cannot be written (read-only, no permission): the built-in values are used this time, one notice.

Nothing here raises: `ListFile.load` returns a `ListLoad` whatever the disk holds.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

from .healing import FileInUse, read_player_text, save_backup_copy, save_damaged_copy, write_text_atomic

log = logging.getLogger("nfl4.data")

FORMAT_VERSION = 1
BACKUP_SUFFIX = ".before-reset"          # the player's file before a reset they asked for (the same as sounds.txt)

# the statuses of a load
OK = "ok"                    # the file was read
CREATED = "created"          # it was missing and has been written from the built-in values
RESET = "reset"              # it was unusable: copied aside and written again from the built-in values
KEPT_DAMAGED = "damaged"     # it was unusable and could not be replaced: the built-in values are used this time
LOCKED = "locked"            # another program holds it: the built-in values are used this time
UNWRITABLE = "unwritable"    # it was missing and could not be written: the built-in values are used
FAILED = "failed"            # an unexpected error (logged): the built-in values are used
UNREADABLE = "unreadable"    # it exists but could not be read for another reason than a sharing violation

_ENTRY = re.compile(r"^([A-Za-z][A-Za-z0-9]*)\s*=\s*(.*)$")


class ListFormatError(ValueError):
    """The text is not a list file of this kind: the file is unusable."""


@dataclass(frozen=True)
class Entry:
    line: int
    id: str           # upper case
    value: str


@dataclass
class ParsedList:
    version: int
    entries: list[Entry] = field(default_factory=list)
    bad_lines: list[tuple[int, str]] = field(default_factory=list)   # (line number, plain reason)


@dataclass
class ListLoad:
    name: str
    status: str
    parsed: ParsedList | None = None     # None: the built-in values are used
    why: str = ""                        # what was wrong, for the log


def header_line(game: str, kind: str) -> str:
    return f"# {game} {kind}, format {FORMAT_VERSION}."


def parse_list(text: str, game: str, kind: str) -> ParsedList:
    """Split a list file into its entries. ListFormatError when the text is not a list of this kind; bad lines are returned,
    never raised."""
    lines = text.splitlines()
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        raise ListFormatError("the file is empty")
    header = re.match(r"#\s*" + re.escape(game) + r"\s+" + re.escape(kind) + r"\s*,\s*format\s+(\d+)",
                      lines[index].strip(), re.IGNORECASE)          # words after the version on that line do not matter
    if header is None:
        raise ListFormatError("the first line is not the header '%s'" % header_line(game, kind))
    version = int(header.group(1))
    if version != FORMAT_VERSION:
        raise ListFormatError("it is format %d and this game reads format %d" % (version, FORMAT_VERSION))
    parsed = ParsedList(version)
    for number in range(index + 1, len(lines)):
        line = lines[number].strip()
        if not line or line.startswith("#"):
            continue
        match = _ENTRY.match(line)
        if match is None:
            parsed.bad_lines.append((number + 1, "the line is not an ID, an equals sign and a value"))
        else:
            value = match.group(2).replace("\t", " ").strip()      # a tab inside a value is a space (7.10: tolerant reading)
            parsed.entries.append(Entry(number + 1, match.group(1).upper(), value))
    return parsed


def render_list(game: str, kind: str, notes: Sequence[str], entries: Iterable[tuple[str, str]]) -> str:
    """The text of a list file: the header, the plain-word notes, a blank line and the entries."""
    lines = [header_line(game, kind)]
    lines.extend(("# " + note).rstrip() for note in notes)
    lines.append("")
    lines.extend(f"{entry_id} = {value}" for entry_id, value in entries)
    return "\n".join(lines) + "\n"


class ListFile:
    """One list file of the customization folder: read it, heal it, write the built-in copy, reset it."""

    def __init__(self, folder: str, name: str, game: str, kind: str, default_text: Callable[[], str]):
        self.folder = folder
        self.name = name
        self.game = game
        self.kind = kind
        self.default_text = default_text

    @property
    def path(self) -> str:
        return os.path.join(self.folder, self.name)

    def load(self) -> ListLoad:
        """Never raises. Creates the folder and the file when they are missing."""
        try:
            return self._load()
        except Exception as exc:                       # whatever goes wrong the built-in values are used (7.10)
            log.exception("loading %s failed", self.path)
            return ListLoad(self.name, FAILED, None, "%s: %s" % (type(exc).__name__, exc))

    def _load(self) -> ListLoad:
        path = self.path
        try:
            os.makedirs(self.folder, exist_ok=True)
        except OSError:
            log.warning("could not make the folder %s", self.folder, exc_info=True)
        if not os.path.lexists(path):
            ok = self.write_defaults()
            return ListLoad(self.name, CREATED if ok else UNWRITABLE)
        if os.path.isdir(path):
            log.warning("%s is a folder, not a file", path)
            return ListLoad(self.name, KEPT_DAMAGED, None, "it is a folder")
        try:
            text = read_player_text(path)
        except ValueError as exc:                      # binary, undecodable or far too large (UnicodeError is one too)
            return self._damaged(str(exc))
        except FileNotFoundError:                      # it went away between the test and the read: the same as missing
            ok = self.write_defaults()
            return ListLoad(self.name, CREATED if ok else UNWRITABLE)
        except FileInUse as exc:                       # held by another program: not damage
            log.warning("%s is held by another program (%s): the built-in values are used this time", path, exc)
            return ListLoad(self.name, LOCKED, None, str(exc))
        except OSError as exc:                         # any other read error: not damage either
            log.warning("%s could not be read (%s): the built-in values are used this time", path, exc)
            return ListLoad(self.name, UNREADABLE, None, str(exc))
        try:
            return ListLoad(self.name, OK, parse_list(text, self.game, self.kind))
        except ListFormatError as exc:
            return self._damaged(str(exc))

    def _damaged(self, why: str) -> ListLoad:
        log.warning("%s is damaged (%s)", self.path, why)
        # a file that cannot be replaced is found damaged again at every reload: one copy of the same bytes is enough, so the
        # player's older copies are not pushed out of the three that are kept
        if not _newest_copy_is_same(self.path) and save_damaged_copy(self.path) is None:    # never replace a file whose
            return ListLoad(self.name, KEPT_DAMAGED, None, why)                              # copy could not be made
        if self.write_defaults():
            return ListLoad(self.name, RESET, None, why)
        return ListLoad(self.name, KEPT_DAMAGED, None, why)

    def write_defaults(self) -> bool:
        try:
            return write_text_atomic(self.path, self.default_text())
        except Exception:
            log.exception("could not make the built-in text of %s", self.path)
            return False

    def exists(self) -> bool:
        return os.path.lexists(self.path)

    def reset(self) -> tuple[bool, bool]:
        """The player asked. Returns (written, kept): `kept` is True when their file was kept as <name>.before-reset.

        Their file is never replaced unless its copy was made (a copy that cannot be made, a full disk, a folder or a
        read-only file in the way: nothing is written and `written` is False). A file that already is the built-in text
        needs no copy, so a second reset never pushes the player's earlier copy out; and the copies before it are moved
        to .before-reset2 and .before-reset3 (the newest three are kept)."""
        if not os.path.isfile(self.path):
            return self.write_defaults(), False
        try:
            current = open(self.path, "rb").read()
            builtin = self.default_text().replace("\n", "\r\n").encode("utf-8")
        except Exception:
            log.exception("could not read %s to reset it", self.path)
            return False, False
        if current == builtin:
            return True, False
        if not _rotate_backups(self.path) or save_backup_copy(self.path, BACKUP_SUFFIX) is None:
            return False, False
        return self.write_defaults(), True


def _newest_copy_is_same(path: str) -> bool:
    """True when the newest <name>.damagedN copy has exactly the bytes of the file."""
    folder, name = os.path.split(path)
    pattern = re.compile(re.escape(name) + r"\.damaged(\d+)$", re.IGNORECASE)
    try:
        numbers = sorted(int(m.group(1)) for m in map(pattern.match, os.listdir(folder)) if m)
        return bool(numbers) and open(f"{path}.damaged{numbers[-1]}", "rb").read() == open(path, "rb").read()
    except OSError as exc:
        log.debug("could not compare %s with its damaged copy (%s)", path, exc)
        return False


def _rotate_backups(path: str) -> bool:
    """<name>.before-reset becomes .before-reset2 and that .before-reset3 (the oldest is dropped), so a reset never replaces
    the copy of an earlier one. False when the move failed (then nothing may be overwritten)."""
    try:
        first, second, third = path + BACKUP_SUFFIX, path + BACKUP_SUFFIX + "2", path + BACKUP_SUFFIX + "3"
        if os.path.exists(second):
            os.replace(second, third)
        if os.path.exists(first):
            os.replace(first, second)
        return True
    except OSError:
        log.warning("could not move the earlier copies of %s", path, exc_info=True)
        return False


class Problems:
    """What was wrong in one file, written to the log as it is found; `count` is the number of entries with a problem (the
    number the one spoken summary says)."""

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.items: list[tuple[object, str]] = []

    def add(self, key: object, text: str) -> None:
        self.items.append((key, text))
        log.warning("%s, %s: %s", self.file_name, key, text)

    @property
    def count(self) -> int:
        return len({key for key, _ in self.items})

    @property
    def messages(self) -> list[str]:
        return ["%s: %s" % (key, text) for key, text in self.items]


def plural(count: int, word: str) -> str:
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def problems_notice(file_name: str, count: int) -> str:
    """The one spoken summary of a file with bad lines (playbook 7.9)."""
    return " %s found in %s, details are in the log. " % (plural(count, "problem"), file_name)


__all__ = ["FORMAT_VERSION", "BACKUP_SUFFIX", "OK", "CREATED", "RESET", "KEPT_DAMAGED", "LOCKED", "UNWRITABLE", "FAILED",
           "UNREADABLE",
           "ListFormatError", "Entry", "ParsedList", "ListLoad", "ListFile", "header_line", "parse_list", "render_list",
           "Problems", "problems_notice", "plural", "FileInUse"]
