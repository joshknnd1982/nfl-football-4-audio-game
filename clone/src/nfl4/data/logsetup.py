"""Log file setup. This is inspired by Jim Kitchen's Brain.

One plain-text log in the per-user logs folder, rotated so it never grows without limit.
If the folder cannot be written, logging goes nowhere and the game carries on (playbook 7.10).
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading

from .paths import log_dir


def setup_logging(level: int = logging.INFO) -> str | None:
    """Returns the log file path, or None if no log file could be opened."""
    root = logging.getLogger()
    root.setLevel(level)
    try:
        folder = log_dir()
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "nfl4.log")
        handler = logging.handlers.RotatingFileHandler(path, maxBytes=512_000, backupCount=2,
                                                       encoding="utf-8")
    except OSError:
        root.addHandler(logging.NullHandler())
        return None
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    return path


def install_exception_logging() -> None:
    """Whatever escapes on any thread goes to the log instead of vanishing (playbook 7.10 last-resort handler)."""
    log = logging.getLogger("nfl4")

    def main_thread_hook(kind, value, trace):
        log.error("unhandled error", exc_info=(kind, value, trace))

    def other_thread_hook(args):
        log.error("unhandled error in thread %s", getattr(args.thread, "name", "?"),
                  exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = main_thread_hook
    threading.excepthook = other_thread_hook
