"""The problem report: one zip the player sends to the owner (owner rule 0.15, playbook 7.11). This is inspired by Jim Kitchen.

A blind player cannot be asked to find a log folder or read a traceback, so the game makes the file itself: from the speech
settings menu (F9, Speech settings, "Save a problem report") or from the command line (`nfl4.exe --problem-report`, no game
window). The zip holds the newest 3 launch logs, the crash log, settings.txt, the list of customization files with their
health, system.txt (the startup report made again now) and README.txt. Every text member goes through debuglog.redact() again
on its way into the zip, so the Windows account name is <user> in all of them, the settings copy too. Saved games and season
files go in only when the player says so. The program sends nothing anywhere; the player sends the file.
"""
from __future__ import annotations

import logging
import os
import re
import time
import zipfile

from . import debuglog, paths, sysreport
from .settingsfile import FILE_NAME as SETTINGS_FILE

log = logging.getLogger("nfl4.report")

LAUNCH_LOGS = 3
MAX_MEMBER_BYTES = 12 * 1024 * 1024           # one launch log is at most 10 MB; nothing bigger goes in
SAVED_PATTERNS = (".sav", ".dat", ".gtp")      # football.sav, footbal1.dat to footbal5.dat, football.gtp, the Franchise's league.sav

README = """NFL Football 4 problem report

This file was made by NFL Football 4 on the player's computer. It holds what the game wrote down about this computer and
this session, so that the game can be fixed. It was not sent anywhere: whoever made it chooses to send it.

What is inside:
  system.txt          the startup report made again when this file was made: Windows, speech, sound, folders, settings
  logs\\               the newest launch logs (what the game did, key by key and sound by sound)
  crash-log.txt       the crash log, if the game ever stopped hard
  settings.txt        the settings file
  customization.txt   the customization files and whether each one is healthy
  saved\\              your saved games and season files, only if you chose to include them

Windows account names, the computer name and e-mail addresses are replaced by <user>, <computer> and <email>. The game never
writes a password or a key.

Send this file to the owner: open https://github.com/joshknnd1982, find the NFL Football 4 repository, choose Issues, then
New issue, describe in a few words what happened and what you pressed, and attach this file.
"""


def desktop_folder() -> str:
    for candidate in (lambda: sysreport.known_folder(sysreport.DESKTOP_ID), lambda: sysreport.known_folder(sysreport.DOCUMENTS_ID),
                      lambda: os.path.join(os.path.expanduser("~"), "Desktop"), lambda: os.path.join(paths.user_data_dir(), "reports")):
        try:
            folder = candidate()
            if folder and (os.path.isdir(folder) or folder.endswith("reports")):
                os.makedirs(folder, exist_ok=True)
                probe = os.path.join(folder, ".nfl4-write-test")
                with open(probe, "w", encoding="ascii") as handle:
                    handle.write("x")
                os.remove(probe)
                return folder
        except Exception as exc:
            log.debug("report folder candidate failed: %s", exc)
    return os.path.join(os.environ.get("TEMP", "."))


def _text(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read(MAX_MEMBER_BYTES)
    return debuglog.redact(raw.decode("utf-8", "replace"))


def newest_launches(folder: str, count: int = LAUNCH_LOGS) -> list[str]:
    """The file names of the newest `count` launches, both halves of each, oldest first."""
    pattern = re.compile(r"^nfl4-(\d{8}-\d{6})(?:-(\d+))?(?:-b)?\.log$")
    groups: dict[tuple[str, int], list[str]] = {}
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    for name in names:
        match = pattern.match(name)
        if match:
            groups.setdefault((match.group(1), int(match.group(2) or 0)), []).append(name)
    chosen = sorted(groups, reverse=True)[:count]
    out: list[str] = []
    for key in reversed(chosen):
        out.extend(sorted(groups[key]))
    return out


def log_folders() -> list[str]:
    """The usual logs folder, then the temp folder a launch falls back to when the first cannot be written (data/debuglog.py)."""
    import tempfile
    return [paths.log_dir(), os.path.join(tempfile.gettempdir(), "nfl4-logs")]


def customization_text(custom) -> str:
    if custom is None:
        return "The customization files could not be loaded at the last start.\n"
    lines = ["customization files (name, health, size, problems inside)"]
    snap = custom.snapshot
    for spec in custom.specs:
        file = custom.files[spec.key]
        path = getattr(file, "path", "") or os.path.join(custom.folder, spec.file_name)
        size = os.path.getsize(path) if os.path.isfile(path) else 0
        lines.append("%s: %s, %d bytes, %d problems" % (spec.file_name, snap.statuses.get(spec.key, "unknown"), size,
                                                        snap.problem_count(spec.key)))
    return "\n".join(lines) + "\n"


def saved_files() -> list[str]:
    """The player's saved games and season files (never the logs, settings or customization files)."""
    found = []
    root = paths.user_data_dir()
    for folder, _, names in os.walk(root):
        rel = os.path.relpath(folder, root)
        if rel.split(os.sep)[0] in ("logs", "customize", "sounds", "commercials", "exported sounds", "reports"):
            continue
        for name in names:
            if name.lower().endswith(SAVED_PATTERNS) and ".damaged" not in name.lower():
                found.append(os.path.join(folder, name))
    return found


def make(include_saves: bool = False, destination: str | None = None, system_kwargs: dict | None = None, custom=None) -> str:
    """Write the zip and return its full path. Raises OSError only when no folder can hold it."""
    began = time.perf_counter()
    debuglog.flush()                                   # the running launch's log is complete on disk first
    folder = destination or desktop_folder()
    os.makedirs(folder, exist_ok=True)
    name = "nfl4-problem-report-%s.zip" % time.strftime("%Y%m%d-%H%M%S")
    target = os.path.join(folder, name)
    logs = paths.log_dir()
    members: list[str] = []
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as bundle:
        def add(arcname: str, text: str) -> None:
            bundle.writestr(arcname, debuglog.redact(text))
            members.append(arcname)

        add("README.txt", README)
        try:
            add("system.txt", "\n".join(sysreport.render_text(**(system_kwargs or {}))) + "\n")
        except Exception as exc:
            log.warning("system.txt could not be made", exc_info=True)
            add("system.txt", "n/a (the startup report failed: %s)\n" % type(exc).__name__)
        for where in log_folders():
            for log_name in newest_launches(where):
                if "logs/" + log_name in members:
                    continue
                try:
                    add("logs/" + log_name, _text(os.path.join(where, log_name)))
                except OSError as exc:
                    log.warning("log %s not added: %s", log_name, exc)
        for where in log_folders():
            crash = os.path.join(where, debuglog.SLUG + "-crash.log")
            if os.path.isfile(crash) and "crash-log.txt" not in members:
                try:
                    add("crash-log.txt", _text(crash))
                except OSError as exc:
                    log.warning("crash log not added: %s", exc)
        settings = os.path.join(paths.user_data_dir(), SETTINGS_FILE)
        if os.path.isfile(settings):
            try:
                add("settings.txt", _text(settings))
            except OSError as exc:
                log.warning("settings not added: %s", exc)
        try:
            add("customization.txt", customization_text(custom))
        except Exception as exc:
            log.warning("customization list failed", exc_info=True)
            add("customization.txt", "n/a (%s)\n" % type(exc).__name__)
        if include_saves:
            root = paths.user_data_dir()
            for path in saved_files():
                try:
                    if os.path.getsize(path) <= MAX_MEMBER_BYTES:
                        arc = "saved/" + os.path.relpath(path, root).replace(os.sep, "/")
                        bundle.write(path, arc)
                        members.append(arc)
                except OSError as exc:
                    log.warning("saved file %s not added: %s", path, exc)
    debuglog.event("report", "problem_report", logging.INFO, path=target, members=len(members), saves=include_saves,
                   ms=round((time.perf_counter() - began) * 1000))
    return target


def listing(path: str) -> list[str]:
    with zipfile.ZipFile(path) as bundle:
        return bundle.namelist()


def run_command(argv: list[str]) -> int:
    """`nfl4.exe --problem-report [--with-saves] [--folder=PATH] [--quiet]`: no game window. A small message box says where the
    file is (a screen reader reads it), unless --quiet; the path is also printed when there is a console."""
    folder = None
    for arg in argv:
        if arg.lower().startswith("--folder="):
            folder = arg.split("=", 1)[1]
    try:
        path = make("--with-saves" in [a.lower() for a in argv], folder)
    except Exception as exc:
        log.exception("the problem report could not be made")
        text = "The problem report could not be made: %s" % exc
        code = 1
    else:
        text = "The problem report was saved as %s. Send that file to the owner." % path
        code = 0
    try:
        print(text)
    except Exception as exc:
        log.debug("no console to print on: %s", exc)
    if "--quiet" not in [a.lower() for a in argv]:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, text, "NFL Football 4 problem report", 0)
        except Exception as exc:
            log.debug("message box failed: %s", exc)
    return code
