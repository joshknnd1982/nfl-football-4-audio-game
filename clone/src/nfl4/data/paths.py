"""Where Brain keeps per-user files and finds its own files. This is inspired by Jim Kitchen's Brain.

Portability seam (playbook 7.2, 9.3): only this module knows Windows folder names.
Per-user data: %APPDATA%\\Kitchensinc Revival\\Brain (settings, player sounds, logs).
Program folder: the folder of brain.exe in a build, clone/ when run from source.
"""
from __future__ import annotations

import os
import sys

VENDOR_FOLDER = "Kitchensinc Revival"
GAME_FOLDER = "Brain"


def user_data_dir() -> str:
    """Per-user data folder. NFL4_DATA_DIR overrides it (tests, portable use)."""
    override = os.environ.get("NFL4_DATA_DIR")
    if override:
        return override
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(base, VENDOR_FOLDER, GAME_FOLDER)


def log_dir() -> str:
    return os.path.join(user_data_dir(), "logs")


def export_dir() -> str:
    """Where the Sounds menu saves generated sounds as wav files (playbook 7.7)."""
    return os.path.join(user_data_dir(), "exported sounds")


def open_folder(path: str) -> bool:
    """Show a folder in Windows Explorer (portability seam: the other platforms open it their own way)."""
    try:
        os.makedirs(path, exist_ok=True)
        os.startfile(path)   # noqa: S606 (Windows only, a folder the program itself made)
        return True
    except OSError:
        return False


def program_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
