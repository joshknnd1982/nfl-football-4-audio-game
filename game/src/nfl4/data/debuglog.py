"""The detailed debug log (owner rule 2026-10-18, CLAUDE.md 0.15, playbook 7.11). This is inspired by Jim Kitchen.

Claude cannot see, hear or touch another player's computer, so this file is its eyes and ears: one plain-text file per
launch in the per-user logs folder, with a startup report of the whole setup at the top and then one event per line.

    HH:MM:SS.mmm +elapsed LEVEL thread component run message          (a message is `event key=value key=value`)

What is here (all of it behind the small calls below, so the rest of the program only says WHAT happened):
- one file per launch, `nfl4-YYYYMMDD-HHMMSS.log`, the newest 10 launches kept; a launch is capped at 10 MB as a ring of two
  halves, and the startup report is written again at the top of each half, so a long session never fills the disk and
  the report is never lost;
- a crash log, `nfl4-crash.log` (1 MB, kept across launches): faulthandler for native crashes and a hang watchdog;
- one redact() inside the formatter, so no call site can skip it: the Windows account name in a path becomes <user>, the
  computer name <computer>, an e-mail address <email>, a value after password/token/key <hidden>, and the text the player
  typed (a coach's name) <typed>; the program sends nothing anywhere;
- a queue and a writer thread: a call costs a few microseconds, finish() flushes the queue before the process ends, an
  unwritable, locked or full folder falls back to the temp folder and then to no file, and the game never notices;
- levels: detailed (the default), trace (adds every random draw and every internal queue step), normal (INFO and above),
  off (the player's right: no file at all).
The names of the calls are the kit's: event(), phase(), slow(), context(), beat(), set_level(), start(), shutdown().
"""
from __future__ import annotations

import faulthandler
import getpass
import logging
import os
import queue
import re
import secrets
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
from contextlib import contextmanager

from . import paths

SLUG = "nfl4"
TRACE = 5
logging.addLevelName(TRACE, "TRACE")
LEVEL_NAMES = ("detailed", "trace", "normal", "off")
DEFAULT_LEVEL = "detailed"
_LEVEL_VALUES = {"detailed": logging.DEBUG, "trace": TRACE, "normal": logging.INFO}
_OFF = logging.CRITICAL + 10

LAUNCHES_KEPT = 10
HALF_BYTES = 5 * 1024 * 1024         # a launch is a ring of two halves: 10 MB at most
CRASH_BYTES = 1024 * 1024
SLOW_MS = 200                        # a step slower than this is written as SLOW
HEARTBEAT_SECONDS = 30.0
HANG_SECONDS = 10.0                  # no heartbeat from the game thread for this long: dump every thread's stack once
HANG_SPEECH_SECONDS = 90.0           # a wait for speech is allowed to be long (a long announcement); a hang is far longer
REPORT_WAIT_SECONDS = 8.0            # the writer holds the first lines back this long for the startup report
REPORT_CLOSE_SECONDS = 1.5           # a program closed before its startup report is done waits this long for it (shutdown)
MAX_LINE = 8 * 1024                  # one line is never longer than this (a 5 MB speech text would break the half-file cap)
MAX_TRACEBACK = 64 * 1024
QUEUE_LIMIT = 50_000                 # a stuck disk must never grow the memory without end: past this, lines are dropped

_FILE = re.compile(r"^nfl4-(\d{8}-\d{6})(?:-(\d+))?(-b)?\.log$")
_PRIVATE_KEY = re.compile(r"""(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|apikey|secret_?key|access_?key|private_?key|auth\w*)\b(\s*[=:]\s*)(?:(?:bearer|basic)\s+)?("[^"]*"|'[^']*'|\S+)""")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_BARE = re.compile(r"^[\w.:/\\@%+,;~#()\[\]<>-]+$")

# ----- the state the fast paths read -----

_threshold = _OFF                    # the lowest level that is written; nothing is written before start()
trace_on = False                     # True at the trace level: the random draws and the queue steps look at it
_log: "_DebugLog | None" = None
_last_beat = time.monotonic()
_state = "starting"                  # what the game thread is doing now, for the heartbeat and the hang report
_context = "start"                   # the screen or menu a key reaches
_exit_reason = ""
_typed: list[str] = []               # strings the player typed, replaced by <typed> in every line
# Names that are public facts (the real rosters, free agents and head coaches the game ships or the player loads): never hidden, so a log shows
# which real man the game offered and played (2026-10-26: a problem report about the Giants' starting quarterback said only "<typed>").
_public: set[str] = set()
_private_names: list[str] = []       # extra account names (tests), besides the ones found in the environment
RUN_ID = secrets.token_hex(3)
STARTED = time.monotonic()


def enabled(level: int = logging.DEBUG) -> bool:
    return level >= _threshold


def level_name() -> str:
    for name, value in _LEVEL_VALUES.items():
        if value == _threshold:
            return name
    return "off"


def run_id() -> str:
    return RUN_ID


# ----- values and redaction -----

def fmt_value(value) -> str:
    """One value on one line: bare when it is a plain word or number, else quoted with the escapes \\n \\r \\\" and cut at 200."""
    if value is None:
        return "none"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float):
        return "%.4g" % value
    if isinstance(value, int):
        return str(value)
    text = value if isinstance(value, str) else repr(value)
    if len(text) > 200:
        text = text[:200] + "...(+%d)" % (len(text) - 200)
    if text and _BARE.match(text):
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n") + '"'


def fields_text(fields: dict) -> str:
    return "".join(" %s=%s" % (key, fmt_value(value)) for key, value in fields.items())


def one_line(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def _short_profile_name() -> str:
    """The 8.3 short form of the profile folder's name (JOSHKE~1): TEMP and other paths often hold it instead of the long name."""
    try:
        import ctypes
        profile = os.environ.get("USERPROFILE", "")
        buf = ctypes.create_unicode_buffer(520)
        if profile and ctypes.windll.kernel32.GetShortPathNameW(profile, buf, 520):
            return os.path.basename(buf.value)
    except Exception as exc:
        logging.getLogger("nfl4.app").debug("the short profile name could not be read: %s", exc)
    return ""


def _account_names() -> list[str]:
    names: list[str] = list(_private_names)
    for getter in (getpass.getuser, lambda: os.environ.get("USERNAME", ""),
                   lambda: os.path.basename(os.path.expanduser("~")),
                   lambda: os.path.basename(os.environ.get("USERPROFILE", ""))):
        try:
            names.append(getter())
        except Exception as exc:
            logging.getLogger("nfl4.app").debug("an account name could not be read: %s", exc)
    names.append(_short_profile_name())
    return sorted({name.strip() for name in names if name and len(name.strip()) >= 2}, key=len, reverse=True)


_SECRET_WORDS = ("pass", "pwd", "token", "secret", "key", "auth")
_computer = ""
_name_pattern_cache: tuple[tuple, re.Pattern | None, re.Pattern | None] = ((), None, None)


def _patterns():
    """(account name pattern, computer name pattern) for the names found now; rebuilt only when they change."""
    global _name_pattern_cache, _computer
    names = _account_names()
    computer = (os.environ.get("COMPUTERNAME") or "").strip()
    _computer = computer.lower()
    key = (tuple(names), computer)
    if _name_pattern_cache[0] != key:
        account = None
        if names:
            # only inside a path: after a separator, so a name that is also a word (Josh Kennedy's) is left alone
            account = re.compile(r"(?<=[\\/])(?:%s)(?![\w])" % "|".join(re.escape(n) for n in names), re.IGNORECASE)
        machine = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(computer), re.IGNORECASE) if len(computer) >= 4 else None
        _name_pattern_cache = (key, account, machine)
    return _name_pattern_cache[1], _name_pattern_cache[2]


def add_private_name(name: str) -> None:
    """Another account name to hide (tests; the environment's names are always found)."""
    if name and name not in _private_names:
        _private_names.append(name)


def add_typed(*texts: str) -> None:
    """Strings the player typed or that the game loaded from the player's files (a coach's name, the quarterbacks, a renamed
    player): the log writes the length of typed text, and any line that holds one of these (the game says them aloud) shows
    <typed> instead, as a whole word in any case. Give the cleaned form as well as the raw one."""
    _resolve_public()
    for text in texts:
        text = unicodedata.normalize("NFC", (text or "").strip())
        if len(text) >= 2 and text not in _typed and text.casefold() not in _public:
            _typed.append(text)
            del _typed[:-60]


def add_public(names) -> None:
    """Names that are public facts (a real player's or coach's name, as written and as spoken): add_typed never hides them, and one
    already hidden is shown again. A name the player types that is no real man's stays hidden."""
    _public.update(unicodedata.normalize("NFC", n).strip().casefold() for n in names if n and n.strip())
    _typed[:] = [t for t in _typed if t.casefold() not in _public]


_public_sources: list = []              # callables that give public names, read only when a typed name must be checked (a list costs 50 ms)


def add_public_source(source) -> None:
    """`source()` gives public names (real_names.build registers each set of names it makes); it is called the first time a typed name
    must be checked, so the many rebuilds of the names cost nothing here."""
    _public_sources.append(source)
    del _public_sources[:-4]


def _resolve_public() -> None:
    while _public_sources:
        source = _public_sources.pop(0)
        try:
            add_public(source())
        except Exception:                   # the log never stops the game
            pass


def redact(text: str) -> str:
    """The one place where private text is removed. Called by the writer for every line before it reaches the disk."""
    account, machine = _patterns()
    if not text.isascii():
        text = unicodedata.normalize("NFC", text)        # a name typed with a combining accent still matches
    lowered = text.lower()                          # each pattern below runs only when its tell-tale is in the line (the writer's cost)
    if account is not None and ("\\" in text or "/" in text):
        text = account.sub("<user>", text)
    if machine is not None and _computer in lowered:
        text = machine.sub("<computer>", text)
    if "@" in text:
        text = _EMAIL.sub("<email>", text)
    if any(word in lowered for word in _SECRET_WORDS):
        text = _PRIVATE_KEY.sub(lambda m: m.group(1) + m.group(2) + "<hidden>", text)
    if _typed and _public_sources:
        _resolve_public()                   # names registered before the rosters were read are shown once they are
    if _typed:
        folded = text.casefold()
        for typed in tuple(_typed):
            if typed.casefold() in folded:
                text = re.sub(r"(?<!\w)%s(?!\w)" % re.escape(typed), "<typed>", text, flags=re.IGNORECASE)
                folded = text.casefold()
    return text


# ----- the call sites' small API -----

def event(component: str, event_name: str, level: int = logging.DEBUG, /, **fields) -> None:
    """One event line. Costs one comparison when the level is not wanted. The first three arguments are positional only, so
    a field may be called `name` or `level`."""
    if level < _threshold:
        return
    try:
        message = "%s%s" % (event_name, fields_text(fields) if fields else "")
        logging.getLogger("nfl4." + component).log(level, "%s", message)
    except Exception:                       # a value whose repr() raises must never reach the game
        if _log is not None:
            _log.errors += 1


def trace(component: str, event_name: str, /, **fields) -> None:
    if trace_on:
        event(component, event_name, TRACE, **fields)


def beat() -> None:
    """The game thread is alive (called from the key pump, which the game thread runs about 1,000 times a second)."""
    global _last_beat
    _last_beat = time.monotonic()


def set_state(text: str) -> None:
    global _state
    _state = text


def state() -> str:
    return _state


def set_context(name: str) -> str:
    """The screen or menu the keys reach now. Returns the previous one."""
    global _context
    previous, _context = _context, name
    return previous


def current_context() -> str:
    return _context


def typing_now() -> bool:
    """True while the player types text: a prompt sets a context that begins with "typing", and no key is written then."""
    return _context.startswith("typing")


@contextmanager
def context(name: str):
    previous = set_context(name)
    try:
        yield
    finally:
        set_context(previous)


@contextmanager
def phase(name: str, limit_ms: int = SLOW_MS):
    """A startup phase or any step worth timing: always one `phase` line at DEBUG, and SLOW when it took more than the limit."""
    began = time.perf_counter()
    try:
        yield
    finally:
        ms = (time.perf_counter() - began) * 1000.0
        if ms > limit_ms:
            event("perf", "SLOW", logging.INFO, name=name, ms=round(ms))
        elif _threshold <= logging.DEBUG:
            event("perf", "phase", name=name, ms=round(ms, 1))


def slow(name: str, limit_ms: int = SLOW_MS):
    """The same, for steps that are usually fast: nothing is written unless the step is slow."""
    return _Slow(name, limit_ms)


class _Slow:
    def __init__(self, name, limit_ms):
        self.name, self.limit_ms = name, limit_ms

    def __enter__(self):
        self.began = time.perf_counter()
        return self

    def __exit__(self, *exc):
        ms = (time.perf_counter() - self.began) * 1000.0
        if ms > self.limit_ms:
            event("perf", "SLOW", logging.INFO, name=self.name, ms=round(ms))
        return False


def set_exit_reason(reason: str) -> None:
    """The first reason wins (the game's own exit comes before the window's close it causes)."""
    global _exit_reason
    if not _exit_reason:
        _exit_reason = reason


def exit_reason() -> str:
    return _exit_reason or "unknown"


# ----- the report -----

class Report:
    """The startup report: sections of `key = value` lines, each filled when its facts are known."""

    def __init__(self):
        self.sections: list[tuple[str, list[tuple[str, str]]]] = []
        self.thread: threading.Thread | None = None      # the thread that makes the report (data/sysreport.py)
        self.on_close = None                             # called when the program ends before the report is done: fills what is missing
        self.emitted: set[str] = set()                   # the keys the newest file header held
        self.done = threading.Event()
        self.lock = threading.Lock()

    def section(self, title: str, items: list[tuple[str, str]]) -> None:
        with self.lock:
            self.sections.append((title, [(str(k), str(v)) for k, v in items]))

    def add(self, key: str, value: str) -> None:
        """Put one more item in the last section."""
        with self.lock:
            if not self.sections:
                self.sections.append(("report", []))
            self.sections[-1][1].append((str(key), str(value)))

    def keys(self) -> set[str]:
        with self.lock:
            return {key for _, items in self.sections for key, _ in items}

    def lines(self) -> list[str]:
        out = ["==== startup report: %s %s run %s ====" % (SLUG, "log", RUN_ID)]
        with self.lock:
            for title, items in self.sections:
                out.append("-- " + title)
                out.extend("%s = %s" % (key, one_line(value)) for key, value in items)
            self.emitted = {key for _, items in self.sections for key, _ in items}
        if not self.done.is_set():
            out.append("-- (the report was not complete when this file began; the rest follows among the first lines below)")
        out.append("==== end of startup report ====")
        return out

    def late_lines(self) -> list[str]:
        """What was added to the report after a file's header was written (a slow probe), as `key = value` lines."""
        with self.lock:
            out = ["-- late startup report items"]
            for title, items in self.sections:
                out.extend("%s = %s" % (key, one_line(value)) for key, value in items if key not in self.emitted)
        return out if len(out) > 1 else []


# ----- the files -----

def _stamp(now: float | None = None) -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(now))


def prune_launches(folder: str, keep: int) -> None:
    """Delete the launch logs older than the newest `keep` (both halves of each). Only files of this program's own name."""
    launches: dict[tuple[str, int], list[str]] = {}
    try:
        names = os.listdir(folder)
    except OSError:
        return
    for name in names:
        match = _FILE.match(name)
        if match:
            launches.setdefault((match.group(1), int(match.group(2) or 0)), []).append(name)
    for key in sorted(launches, reverse=True)[keep:]:
        for name in launches[key]:
            try:
                os.remove(os.path.join(folder, name))
            except OSError:
                pass            # a file held by another program stays until the next start


class _Ring:
    """Two half files. The older half is dropped when the newer is full; each begins with the startup report."""

    def __init__(self, folder: str, stem: str, half_bytes: int, header):
        self.folder, self.stem, self.half = folder, stem, half_bytes
        self.paths = [os.path.join(folder, stem + ".log"), os.path.join(folder, stem + "-b.log")]
        self.header = header          # a function that gives the report lines
        self.index = 0
        self.sequence = 0
        self.size = 0
        self.handle = None
        self.need_header = True

    def _open(self, header_now: bool = True, mode: str = "wb") -> None:
        """Open the next half. Its header, the startup report, is written at once, except for the first half of a launch, which
        is opened before the report is complete: that one gets it with its first line."""
        if self.handle is not None:
            try:
                self.handle.close()
            except OSError:
                pass
            self.handle = None
        self.sequence += 1
        self.handle = open(self.paths[self.index], mode)
        self.size = 0
        self.need_header = True
        if header_now:
            self._write_header()

    def _raw(self, data: bytes) -> None:
        self.handle.write(data)
        self.size += len(data)

    def write(self, line: str) -> None:
        data = (line + "\n").encode("utf-8", "replace")
        if self.handle is None:
            self._open()
        elif self.size + len(data) > self.half and not self.need_header:
            self.index = 1 - self.index
            self._open()
        if self.need_header:
            self._write_header()
        self._raw(data)

    def _write_header(self) -> None:
        self.need_header = False
        lines = [redact(text) for text in self.header()]
        lines += ["-- part %d, sequence %d of run %s --" % (self.index + 1, self.sequence, RUN_ID), ""]
        self._raw("\n".join(lines).encode("utf-8", "replace"))

    def flush(self) -> None:
        if self.handle is not None:
            self.handle.flush()

    def close(self) -> None:
        if self.handle is not None:
            try:
                self.handle.close()
            except OSError:
                pass
            self.handle = None


class _DebugLog:
    """The running log of this launch: the queue, the writer thread, the files, the crash log and the watchdog."""

    def __init__(self, folder: str | None, level: str, half_bytes: int = HALF_BYTES):
        self.level = level
        self.folder = folder
        self.half_bytes = half_bytes
        self.report = Report()
        self.queue: queue.SimpleQueue = queue.SimpleQueue()
        self.errors = 0               # lines or files that failed; reported in the next launch's startup report
        self.dropped = 0
        self.path: str | None = None
        self.crash_path: str | None = None
        self.crash_file = None
        self.ring: _Ring | None = None
        self.handler: logging.Handler | None = None
        self.writer: threading.Thread | None = None
        self.watchdog: threading.Thread | None = None
        self.stop_watchdog = threading.Event()
        self.alive = True
        self.report_wait = REPORT_WAIT_SECONDS
        self.began = time.time()
        self.hang_dumped = False
        self.recoveries = 0
        self.fallback_reason = ""        # why the logs folder was not used, for the startup report

    # ----- opening -----

    def open_files(self) -> None:
        folder = self.folder
        for candidate in (folder, os.path.join(tempfile.gettempdir(), "nfl4-logs")):
            if not candidate:
                continue
            try:
                os.makedirs(candidate, exist_ok=True)
                self._open_in(candidate)
                self.folder = candidate
                return
            except OSError as exc:
                self.errors += 1
                self.path = None
                self.ring = None
                if candidate == folder:
                    self.fallback_reason = "%s: %s" % (type(exc).__name__, exc)
        self.alive = False            # no folder works: the game runs without a log file

    def _open_in(self, folder: str) -> None:
        prune_launches(folder, LAUNCHES_KEPT - 1)
        stamp = _stamp(self.began)
        stem, number = "nfl4-" + stamp, 1
        while True:                                                       # two launches in one second: the next free number
            self.ring = _Ring(folder, stem, self.half_bytes, self.report.lines)
            try:
                self.ring._open(header_now=False, mode="xb")              # never truncate another process's file
                break
            except FileExistsError:
                number += 1
                stem = "nfl4-%s-%d" % (stamp, number)
        self.path = self.ring.paths[0]
        self._open_crash(folder)

    def _open_crash(self, folder: str) -> None:
        path = os.path.join(folder, SLUG + "-crash.log")
        try:
            if os.path.exists(path) and os.path.getsize(path) > CRASH_BYTES:                       # keep the newest half, not nothing
                with open(path, "rb") as old:
                    old.seek(-CRASH_BYTES // 2, 2)
                    tail = old.read()
                with open(path, "wb") as new:
                    new.write(b"--- (older entries cut) ---\n" + tail)
        except OSError as exc:
            self.errors += 1
            logging.getLogger("nfl4.app").debug("the crash log could not be trimmed: %s", exc)
        redact_file(path)                                                 # paths written by the last launch's faulthandler
        try:
            self.crash_file = open(path, "ab", buffering=0)
            self.crash_path = path
            self.crash_file.write(("--- launch %s %s ---\n" % (RUN_ID, time.strftime("%Y-%m-%d %H:%M:%S"))).encode("ascii"))
            try:
                faulthandler.enable(self.crash_file, all_threads=True)       # a voice DLL that kills the process (7.4.5)
            except (RuntimeError, ValueError, OSError):
                self.errors += 1
        except OSError:
            self.errors += 1
            self.crash_file = None

    # ----- the threads -----

    def start_threads(self) -> None:
        self.writer = threading.Thread(target=self._run, name="debuglog", daemon=True)
        self.writer.start()
        self.watchdog = threading.Thread(target=self._watch, name="watchdog", daemon=True)
        self.watchdog.start()

    def put(self, created: float, thread: str, levelno: int, name: str, text: str) -> None:
        if not self.alive:
            return
        if self.queue.qsize() > QUEUE_LIMIT:
            self.dropped += 1
            return
        self.queue.put((created, thread, levelno, name, text))

    def _line(self, item) -> str:
        created, thread, levelno, name, text = item
        stamp = time.strftime("%H:%M:%S", time.localtime(created)) + ".%03d" % int((created % 1) * 1000)
        elapsed = created - self.began
        line = "%s +%.3f %s %s %s %s %s" % (stamp, elapsed, logging.getLevelName(levelno), thread, name.replace("nfl4.", "", 1)
                                           or "nfl4", RUN_ID, one_line(text))
        return redact(line)

    def _run(self) -> None:
        self.report.done.wait(self.report_wait)         # the report goes first; the first lines wait for it
        ring = self.ring
        late = not self.report.done.is_set()            # a slow probe: its items follow the header as lines, when they come
        while True:
            item = self.queue.get()
            if item is None:
                break
            if late and self.report.done.is_set() and ring is not None and self.alive:
                late = False
                try:
                    for text in self.report.late_lines():
                        ring.write(redact(text))
                except Exception:
                    self.errors += 1
            if isinstance(item, threading.Event):
                self._flush()
                item.set()
                continue
            try:
                if ring is not None and self.alive:
                    ring.write(self._line(item))
            except Exception:                          # a disk error: count it, try the temp folder once, never raise
                self.errors += 1
                ring = self._recover(ring)
            if self.queue.empty():
                self._flush()
        if late and ring is not None and self.alive:       # the program ended before the next line: the late items still go in
            try:
                for text in self.report.late_lines():
                    ring.write(redact(text))
            except Exception:
                self.errors += 1
        self._flush()

    def _recover(self, ring):
        try:
            if ring is not None:
                ring.close()
        except Exception as exc:
            self.errors += 1
            logging.getLogger("nfl4.app").debug("the log file did not close cleanly: %s", exc)
        self.recoveries += 1
        if ring is not None and self.recoveries == 1:                    # one failed write is often a passing lock: the same file, once
            try:
                ring.handle = open(ring.paths[ring.index], "ab")
                ring.size = ring.handle.tell()
                return ring
            except Exception:
                self.errors += 1
        if self.folder and not self.folder.startswith(tempfile.gettempdir()):
            try:
                folder = os.path.join(tempfile.gettempdir(), "nfl4-logs")
                os.makedirs(folder, exist_ok=True)
                new = _Ring(folder, "nfl4-%s-%d" % (_stamp(self.began), 90 + self.recoveries), self.half_bytes, self.report.lines)
                new._open(header_now=False)
                self.ring, self.path, self.folder = new, new.paths[0], folder
                return new
            except Exception:
                self.errors += 1
        self.alive = False
        self.ring = None
        return None

    def _flush(self) -> None:
        try:
            if self.ring is not None:
                self.ring.flush()
        except Exception:
            self.errors += 1

    def flush(self, timeout: float = 2.0) -> None:
        if not self.alive or self.writer is None or not self.writer.is_alive():
            return
        token = threading.Event()
        self.queue.put(token)
        token.wait(timeout)

    # ----- the watchdog: heartbeat, hang -----

    def _watch(self) -> None:
        last_heartbeat = time.monotonic()
        while not self.stop_watchdog.wait(1.0):
            now = time.monotonic()
            age = now - _last_beat
            limit = HANG_SPEECH_SECONDS if _state.startswith("speech wait") else HANG_SECONDS
            if age > limit and not self.hang_dumped:
                self.hang_dumped = True
                self._dump_hang(age)
            elif age <= limit:
                self.hang_dumped = False
            if now - last_heartbeat >= HEARTBEAT_SECONDS:
                last_heartbeat = now
                event("app", "heartbeat", logging.INFO, since_beat=round(age, 1), state=_state, ctx=_context,
                      threads=threading.active_count(), queued=self.queue.qsize(), dropped=self.dropped)

    def _dump_hang(self, age: float) -> None:
        event("app", "HANG", logging.ERROR, since_beat=round(age, 1), state=_state, ctx=_context,
              stacks="in " + os.path.basename(self.crash_path or "the crash log"))
        if self.crash_file is not None and self.crash_path and os.path.getsize(self.crash_path) < CRASH_BYTES:
            try:
                self.crash_file.write(("--- hang in run %s: no heartbeat for %.1f s, state %s ---\n"
                                       % (RUN_ID, age, _state)).encode("ascii", "replace"))
                faulthandler.dump_traceback(self.crash_file, all_threads=True)
            except (OSError, ValueError, RuntimeError):
                self.errors += 1


def redact_file(path: str) -> None:
    """Rewrite a text file through redact() (the crash log: faulthandler writes native stack text straight to the file, outside
    the formatter, so its paths are cleaned when the file is closed and again at the next start). Never raises."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read(CRASH_BYTES * 2)
        text = raw.decode("utf-8", "replace")
        clean = redact(text)
        if clean != text:
            with open(path, "wb") as handle:
                handle.write(clean.encode("utf-8", "replace"))
    except OSError as exc:
        logging.getLogger("nfl4.app").debug("%s could not be cleaned: %s", path, exc)


class _QueueHandler(logging.Handler):
    """Hands every record to the writer thread as plain text: the call costs a format and a queue put."""

    def __init__(self, owner: _DebugLog):
        super().__init__(logging.NOTSET)
        self.owner = owner

    def emit(self, record: logging.LogRecord) -> None:
        try:
            text = record.getMessage()
            if len(text) > MAX_LINE:
                text = text[:MAX_LINE] + "...(+%d characters)" % (len(text) - MAX_LINE)
            if record.exc_info and record.exc_info[0] is not None:
                trace_text = "".join(traceback.format_exception(*record.exc_info)).rstrip()
                if len(trace_text) > MAX_TRACEBACK:
                    trace_text = trace_text[:MAX_TRACEBACK // 2] + "\n...(cut)...\n" + trace_text[-MAX_TRACEBACK // 2:]
                text += " traceback=" + trace_text
            self.owner.put(record.created, record.threadName or "?", record.levelno, record.name, text)
        except Exception:
            self.owner.errors += 1


# ----- starting and stopping -----

STATE_FILE = SLUG + "-state.txt"


def last_launch_errors(folder: str | None = None) -> str:
    """What the previous launch counted (lines it could not write, lines it dropped), for the next startup report."""
    try:
        with open(os.path.join(folder or paths.log_dir(), STATE_FILE), encoding="utf-8") as handle:
            return handle.read().strip()[:200] or "0"
    except OSError:
        return "0 (no earlier launch recorded)"


def _write_state(log: "_DebugLog") -> None:
    """What this launch counted, in the usual logs folder (the next launch reads it there), else beside the log it wrote."""
    for folder in (paths.log_dir(), log.folder):
        if not folder:
            continue
        try:
            with open(os.path.join(folder, STATE_FILE), "w", encoding="utf-8") as handle:
                handle.write("%d write errors, %d dropped lines (run %s)\n" % (log.errors, log.dropped, RUN_ID))
            return
        except OSError as exc:
            logging.getLogger("nfl4.app").debug("the log state could not be written in %s: %s", folder, exc)

def level_from_environment(argv: list[str] | None = None) -> str | None:
    """--debug-log=trace on the command line, else NFL4_DEBUG_LOG=trace, else NFL4_DEBUG=1 (the old switch: detailed)."""
    for arg in argv or ():
        if arg.lower().startswith("--debug-log="):
            value = arg.split("=", 1)[1].strip().lower()
            if value in LEVEL_NAMES:
                return value
    value = os.environ.get("NFL4_DEBUG_LOG", "").strip().lower()
    if value in LEVEL_NAMES:
        return value
    return DEFAULT_LEVEL if os.environ.get("NFL4_DEBUG") else None


def level_from_settings_file(folder: str) -> str | None:
    """Read `debug_log = ...` from settings.txt before the settings are loaded, so the first line is written at the right level."""
    try:
        with open(os.path.join(folder, "settings.txt"), "rb") as handle:
            data = handle.read(200_000)
    except OSError:
        return None
    for raw in data.decode("utf-8", "replace").splitlines():
        line = raw.strip().lstrip("\ufeff")
        if line.lower().startswith("debug_log"):
            name, sep, value = line.partition("=")
            if sep and name.strip().lower() == "debug_log" and value.strip().lower() in LEVEL_NAMES:
                return value.strip().lower()
    return None


def start(level: str = DEFAULT_LEVEL, folder: str | None = None, half_bytes: int = HALF_BYTES) -> str | None:
    """Open the log for this launch. Returns the path of the first half, or None when there is no file (off, or no folder
    could be written; the game goes on either way)."""
    global _log, _threshold, trace_on
    shutdown_quietly()
    del _typed[:]                           # names registered by an earlier launch in this process are not this launch's
    if level not in LEVEL_NAMES:
        level = DEFAULT_LEVEL
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, _QueueHandler):
            root.removeHandler(handler)
    if level == "off":
        _threshold, trace_on = _OFF, False
        root.setLevel(logging.WARNING)
        if not root.handlers:
            root.addHandler(logging.NullHandler())      # no stderr fallback in a windowed program
        return None
    wanted = _LEVEL_VALUES[level]
    log = _DebugLog(folder if folder is not None else paths.log_dir(), level, half_bytes)
    log.open_files()
    if log.alive:
        log.start_threads()
    log.handler = _QueueHandler(log)
    log.handler.setLevel(wanted)
    root.addHandler(log.handler)
    root.setLevel(wanted)
    _log = log
    _threshold = wanted
    trace_on = wanted <= TRACE
    return log.path


def shutdown_quietly() -> None:
    global _log
    if _log is not None:
        shutdown("restarted", None, say=False)


def set_level(level: str) -> str:
    """The player changed the debug_log setting. `off` stops writing at once; turning it on again starts the log if none runs."""
    global _threshold, trace_on
    if level not in LEVEL_NAMES:
        return level_name()
    if level == "off":
        if _log is not None:
            event("app", "log_level", logging.INFO, old=level_name(), new="off")
            flush()
        _threshold, trace_on = _OFF, False
        logging.getLogger().setLevel(logging.WARNING)
        if _log is not None and _log.handler is not None:
            _log.handler.setLevel(_OFF)
        return "off"
    if _log is None:
        start(level)
        if _log is not None:
            _log.report.section("note", [("log_started", "turned on by the player during play; the startup report of this launch was not made")])
            _log.report.done.set()
        event("app", "log_level", logging.INFO, new=level)
        return level
    wanted = _LEVEL_VALUES[level]
    old = level_name()
    _threshold, trace_on = wanted, wanted <= TRACE
    logging.getLogger().setLevel(wanted)
    if _log.handler is not None:
        _log.handler.setLevel(wanted)
    event("app", "log_level", logging.INFO, old=old, new=level)
    return level


def report() -> Report | None:
    return _log.report if _log is not None else None


def report_done() -> None:
    """The startup report is complete: the writer puts it at the top of the file and then the events."""
    if _log is not None:
        _log.report.done.set()


def path() -> str | None:
    return _log.path if _log is not None else None


def folder_info() -> str:
    """Where the log really goes and why not the usual place, for the startup report."""
    if _log is None:
        return "n/a (no log is running)"
    note = " (the logs folder could not be used: %s)" % _log.fallback_reason if _log.fallback_reason else ""
    return "%s%s" % (_log.folder or "none", note)


def crash_path() -> str | None:
    return _log.crash_path if _log is not None else None


def errors() -> int:
    return _log.errors if _log is not None else 0


def flush(timeout: float = 2.0) -> None:
    if _log is not None:
        _log.flush(timeout)


def shutdown(reason: str = "", code: int | None = 0, say: bool = True) -> None:
    """The last call of the program (data/lifecycle.finish): the line `closed` is the file's last line, then the queue is
    written out and the files are closed."""
    global _log, _threshold, trace_on
    log = _log
    if log is None:
        return
    if say:
        event("app", "closed", logging.INFO, code=code, reason=reason or exit_reason(), seconds=round(time.monotonic() - STARTED, 1),
              errors=log.errors, dropped=log.dropped)
    log.stop_watchdog.set()
    if log.report.thread is not None and not log.report.done.is_set():
        log.report.thread.join(REPORT_CLOSE_SECONDS)     # a program closed at once still gets a whole report
    if not log.report.done.is_set() and log.report.on_close is not None:
        try:
            log.report.on_close()
        except Exception as exc:
            logging.getLogger("nfl4.app").debug("the report could not be completed at the end: %s", exc)
    log.report.done.set()
    if log.writer is not None and log.writer.is_alive():
        log.queue.put(None)
        log.writer.join(2.0)
    if log.ring is not None:
        log.ring.close()
    if log.handler is not None:
        logging.getLogger().removeHandler(log.handler)
    try:
        faulthandler.disable()
    except Exception:
        pass
    if log.crash_file is not None:
        try:
            log.crash_file.close()
        except OSError:
            pass
    if log.crash_path:
        redact_file(log.crash_path)
    _write_state(log)
    _log = None
    _threshold, trace_on = _OFF, False


# ----- errors that escape -----

def install_exception_hooks() -> None:
    """Whatever escapes on any thread goes to the log with its traceback instead of vanishing (playbook 7.10)."""
    log = logging.getLogger("nfl4.app")

    def main_thread_hook(kind, value, trace_back):
        log.error("unhandled error", exc_info=(kind, value, trace_back))
        report_done()                      # the process may end right after this: write what is queued, report or not
        flush(2.0)

    def other_thread_hook(args):
        log.error("unhandled error in thread %s", getattr(args.thread, "name", "?"),
                  exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    def unraisable_hook(args):
        log.error("unraisable error: %s (object %s)", args.err_msg, type(args.object).__name__,
                  exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = main_thread_hook
    threading.excepthook = other_thread_hook
    sys.unraisablehook = unraisable_hook
