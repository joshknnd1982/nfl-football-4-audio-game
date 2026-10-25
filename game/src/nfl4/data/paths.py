"""Where NFL Football 4 keeps per-user files and finds its own files. This is inspired by Jim Kitchen.

Portability seam (playbook 7.2, 9.3): only this module knows Windows folder names.
Per-user data: %APPDATA%\\Kitchensinc Revival\\NFL Football 4 (settings, the season files, saved game, the player's
sounds and customization files, logs). GAP_REGISTER G-F8 and D-024 item 3: the original kept its files in
Documents\\kitchensinc, shared with Jim Kitchen's other programs; the game never reads or writes that folder.
Program folder: the folder of nfl4.exe in a build, game/ when run from source.
"""
from __future__ import annotations

import logging
import os
import sys

VENDOR_FOLDER = "Kitchensinc Revival"
GAME_FOLDER = "NFL Football 4"


def user_data_dir() -> str:
    """Per-user data folder. NFL4_DATA_DIR overrides it (tests, portable use)."""
    override = os.environ.get("NFL4_DATA_DIR")
    if override:
        return override
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(base, VENDOR_FOLDER, GAME_FOLDER)


def log_dir() -> str:
    return os.path.join(user_data_dir(), "logs")


def customize_dir() -> str:
    """The player's customization files (teams.txt, divisions.txt, surnames.txt, banter.txt, footplay.txt and the
    sounds subfolder for the banter's own sounds; D-032 item 11, D-035). Made, read and healed by data/customize.py
    (S7.7), except footplay.txt, which data/files/store.py keeps (S7.5)."""
    return os.path.join(user_data_dir(), "customize")


def commercials_dir() -> str:
    """The player's own commercial files (owner rule 0.14, playbook 7.7.1; game/commercials.py). The game ships none."""
    return os.path.join(user_data_dir(), "commercials")


def export_dir() -> str:
    """Where the Sounds menu saves generated sounds as wav files (playbook 7.7)."""
    return os.path.join(user_data_dir(), "exported sounds")


def open_folder(path: str) -> bool:
    """Show a folder in Windows Explorer (portability seam: the other platforms open it their own way)."""
    try:
        os.makedirs(path, exist_ok=True)
        os.startfile(path)   # noqa: S606 (Windows only, a folder the program itself made)
        return True
    except OSError as exc:
        logging.getLogger("nfl4.data").warning("the folder %s could not be opened: %s", path, exc)
        return False


def program_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
