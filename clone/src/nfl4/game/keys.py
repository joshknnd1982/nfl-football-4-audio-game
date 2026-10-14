"""The original's key fields and waits, without any window. This is inspired by Jim Kitchen's Brain.

GAME_SPEC 8.1 and 8.4: the original kept two fields, the key code text CStr(KeyCode) and the key
character LCase(Chr(KeyCode)), filled by Form_KeyDown, which only runs when the program calls
DoEvents. The window thread posts key codes here; pump() is DoEvents. Waiting speech does not
pump, so keys typed during it are delivered afterwards, exactly as in the original.
Key codes are Windows virtual-key codes, the same numbers VB's KeyDown received.
"""
from __future__ import annotations

import queue
import threading
import time

KEY_ESCAPE = 27
KEY_ENTER = 13
KEY_UP = 38
KEY_DOWN = 40
KEY_F1 = 112
KEY_F2, KEY_F3, KEY_F4 = 113, 114, 115
KEY_SPACE = 32
KEY_PAGE_UP, KEY_PAGE_DOWN, KEY_END, KEY_HOME = 33, 34, 35, 36
KEY_LEFT, KEY_RIGHT = 37, 39
# Shift, Ctrl, Alt, Caps Lock, Windows keys, Num Lock, Scroll Lock: never an answer in a menu
MODIFIER_KEYS = frozenset({16, 17, 18, 20, 91, 92, 144, 145})


def typed_character(key_code: int) -> str:
    """The letter, digit or space a key types in a menu's type-ahead search; "" for any other key."""
    if 65 <= key_code <= 90:
        return chr(key_code).lower()
    if 48 <= key_code <= 57:
        return chr(key_code)
    if 96 <= key_code <= 105:
        return chr(key_code - 96 + 48)
    return " " if key_code == KEY_SPACE else ""


class GameQuit(Exception):
    """The window was closed: unwind the game thread."""


def key_char(key_code: int) -> str:
    """LCase(Chr(KeyCode)) with the Windows ANSI code page 1252 (GAME_SPEC 8.1)."""
    try:
        char = bytes([key_code & 0xFF]).decode("cp1252")
    except UnicodeDecodeError:  # 0x81, 0x8D, 0x8F, 0x90, 0x9D: Windows maps these to the same code point
        char = chr(key_code & 0xFF)
    return char.lower()


class KeyInput:
    def __init__(self, clock=time.monotonic, sleep=time.sleep):
        self.code_text = ""   # "" when no key is waiting, else e.g. "27", "49"
        self.char = ""        # e.g. "1", "a", "&" for the Up arrow
        self.quit = threading.Event()
        self._posted: queue.SimpleQueue = queue.SimpleQueue()
        self._clock = clock
        self._sleep = sleep

    # called by the window thread
    def post(self, key_code: int) -> None:
        self._posted.put(key_code)

    def close(self) -> None:
        self.quit.set()

    # called by the game thread
    def pump(self) -> None:
        """DoEvents: run Form_KeyDown for every key posted since the last pump, in order."""
        if self.quit.is_set():
            raise GameQuit()
        while True:
            try:
                code = self._posted.get_nowait()
            except queue.Empty:
                return
            self.code_text = str(code)
            self.char = key_char(code)

    def clk(self) -> None:
        """Clear the key code text, DoEvents, clear the key character, DoEvents (that order)."""
        self.code_text = ""
        self.pump()
        self.char = ""
        self.pump()

    def dy(self, seconds: float) -> None:
        """Wait with DoEvents until more than seconds have passed (clock never wraps at midnight)."""
        end = self._clock() + seconds
        while True:
            self.pump()
            if self._clock() > end:
                return
            self._sleep(0.001)

    def read_key(self) -> int:
        """The next key in the order it was typed, for the menus of the clone's added functions.

        Unlike getkey this never discards a key typed ahead, and it skips Shift, Ctrl and Alt on
        their own. The original's two fields are still filled (key code text, key character)."""
        while True:
            if self.quit.is_set():
                raise GameQuit()
            try:
                code = self._posted.get(timeout=0.01)
            except queue.Empty:
                continue
            if code in MODIFIER_KEYS:
                continue
            self.code_text = str(code)
            self.char = key_char(code)
            return code

    def getkey(self, speech) -> None:
        """clk, wait with DoEvents for a key, then stop speech at once."""
        self.clk()
        while self.code_text == "":
            self._sleep(0.001)
            self.pump()
        speech.stop()
