"""Start and end of the process: never hold the program folder, always really end. This is inspired by Jim Kitchen's Brain.

Owner bug 2026-10-13: after uninstalling, the program folder (C:\\Program Files\\My Brain) was left behind and could
not be deleted ("folder in use") until the computer was restarted. Three things in the program itself can cause that,
all closed here (the installer has its own part, playbook 8.2):
1. The process's current directory. A process whose working directory is the program folder holds that folder open for
   as long as it lives (the installer's "start now" box and shortcuts start the program in its own folder).
   leave_program_folder() moves the process to the player's data folder at the start.
2. A process that does not end. Python waits for non-daemon threads and finishes by unwinding native libraries; a voice
   engine, the audio library or a screen reader's RPC call that hangs keeps the process alive with no window, invisible
   to the player. finish() flushes the log and ends the process with os._exit, which cannot be held up.
3. A close that hangs half way. arm_exit_deadline() starts a daemon timer when the window closes: if the orderly
   shutdown has not ended the process after a few seconds, the process is ended anyway.
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
import threading

log = logging.getLogger(__name__)

EXIT_DEADLINE_SECONDS = 6.0


def _inside(path: str, folder: str) -> bool:
    try:
        path, folder = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(folder))
        return path == folder or path.startswith(folder.rstrip("\\/") + os.sep)
    except (OSError, ValueError):
        return False


def leave_program_folder(program_dir: str, safe_dir: str) -> str | None:
    """Move the process out of the program folder (or any folder below it). Returns the new directory, or None when
    the process was not inside it. Tries safe_dir (made if needed), then the temp folder, then the system drive root."""
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = program_dir                         # the folder is gone or unreadable: treat it as inside
    if not _inside(cwd, program_dir):
        return None
    for target in (safe_dir, tempfile.gettempdir(), os.path.abspath(os.sep)):
        try:
            os.makedirs(target, exist_ok=True)
            os.chdir(target)
            log.debug("working directory moved out of the program folder to %s", target)
            return target
        except OSError:
            continue
    return None


def arm_exit_deadline(seconds: float = EXIT_DEADLINE_SECONDS, exit_fn=os._exit, code: int = 0) -> threading.Timer:
    """End the process in `seconds` whatever is still running (daemon timer; call .cancel() to disarm)."""
    def expire():
        log.warning("closing did not finish in %.0f s: ending the process", seconds)
        _flush_logs()
        exit_fn(code)

    timer = threading.Timer(seconds, expire)
    timer.daemon = True
    timer.start()
    return timer


def _flush_logs() -> None:
    try:
        logging.shutdown()
    except Exception:
        pass
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None:
                stream.flush()
        except Exception:
            pass


def finish(code: int = 0, exit_fn=os._exit) -> None:
    """The last call of the program: flush the log, then end the process at once. Threads that are stuck in native
    code (a voice engine, the audio device, an RPC call) cannot keep it alive and nothing stays open afterwards."""
    _flush_logs()
    exit_fn(int(code) if isinstance(code, int) else 0)
