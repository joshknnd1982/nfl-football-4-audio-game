"""Log file setup: the entry points the program calls. This is inspired by Jim Kitchen.

The detailed debug log itself (one file per launch, the startup report, the crash log, the redaction) is in
data/debuglog.py (CLAUDE.md 0.15, playbook 7.11). If the folder cannot be written, logging goes to the temp folder and
then nowhere, and the game carries on (playbook 7.10).
"""
from __future__ import annotations

import logging

from . import debuglog


def setup_logging(level: str | int | None = None, folder: str | None = None) -> str | None:
    """Start the log. `level` is a debug_log name (detailed, trace, normal, off); the old logging numbers still work
    (DEBUG is detailed, anything higher is normal). Returns the log file path, or None when no file could be opened."""
    if isinstance(level, int):
        level = "detailed" if level <= logging.DEBUG else "normal"
    return debuglog.start(level or debuglog.DEFAULT_LEVEL, folder)


def install_exception_logging() -> None:
    """Whatever escapes on any thread goes to the log instead of vanishing (playbook 7.10 last-resort handler)."""
    debuglog.install_exception_hooks()
