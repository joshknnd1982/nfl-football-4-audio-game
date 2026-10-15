"""The original's key fields and waits, without any window. This is inspired by Jim Kitchen.

GAME_SPEC 8.1: the original kept two fields, g = the key code text CStr(KeyCode) and g2 = the key character
LCase(Chr(KeyCode)), filled by Form_KeyDown, which only runs when the program calls DoEvents. The window thread posts
key codes here; pump() is DoEvents. Waiting speech does not pump, so keys typed during it are delivered afterwards,
exactly as in the original (TESTED in nfl4 S4.3: a synchronous SAPI Speak lets no message through, G-K1).
Key codes are Windows virtual-key codes, the same numbers VB's KeyDown received.

Typed characters (nfl4 S7.1, B-W3, G-K5): the window also posts the character a key typed (its WM_CHAR, which Windows
makes right after the key), in the same ordered queue. pump() keeps it in `typed`; a name prompt reads it with
take_typed() right after its key. The original's two fields do not change: g2 is still LCase(Chr(KeyCode)).
"""
from __future__ import annotations

import collections
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


class _KeyQueue:
    """What the window posted, in order: key codes (int) and typed characters (str). Like queue.SimpleQueue, plus a
    look at the next item, so the character a key typed can be taken right after that key."""

    def __init__(self):
        self._items: collections.deque = collections.deque()
        self._cv = threading.Condition()

    def put(self, item) -> None:
        with self._cv:
            self._items.append(item)
            self._cv.notify_all()

    def get(self, timeout: float | None = None):
        with self._cv:
            if not self._items and not self._cv.wait_for(lambda: bool(self._items), timeout):
                raise queue.Empty
            return self._items.popleft()

    def get_nowait(self):
        with self._cv:
            if not self._items:
                raise queue.Empty
            return self._items.popleft()

    def empty(self) -> bool:
        with self._cv:
            return not self._items

    def take_text(self, wait: float) -> str:
        """The next item if it is a typed character (waiting up to `wait` seconds for an item to come), else ""."""
        with self._cv:
            if not self._items:
                self._cv.wait_for(lambda: bool(self._items), wait)
            if self._items and isinstance(self._items[0], str):
                return self._items.popleft()
            return ""


class KeyInput:
    def __init__(self, clock=time.monotonic, sleep=time.sleep):
        self.code_text = ""   # g: "" when no key is waiting, else e.g. "27", "49"
        self.char = ""        # g2: e.g. "1", "a", "&" for the Up arrow
        self.typed = ""       # the character the last key typed on the player's keyboard ("" for keys that type none)
        self.quit = threading.Event()
        self._posted = _KeyQueue()
        self._clock = clock
        self._sleep = sleep

    # called by the window thread
    def post(self, key_code: int) -> None:
        self._posted.put(int(key_code))

    def post_char(self, char: str) -> None:
        if char:
            self._posted.put(str(char))

    def close(self) -> None:
        self.quit.set()

    # called by the game thread
    def pump(self) -> None:
        """DoEvents: run Form_KeyDown for every key posted since the last pump, in order."""
        if self.quit.is_set():
            raise GameQuit()
        while True:
            try:
                item = self._posted.get_nowait()
            except queue.Empty:
                return
            if isinstance(item, str):
                self.typed = item
                continue
            self.code_text = str(item)
            self.char = key_char(item)
            self.typed = ""

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
                item = self._posted.get(timeout=0.01)
            except queue.Empty:
                continue
            if isinstance(item, str):
                self.typed = item
                continue
            if item in MODIFIER_KEYS:
                continue
            self.code_text = str(item)
            self.char = key_char(item)
            self.typed = ""
            return item

    def take_typed(self, wait: float = 0.05) -> str:
        """The character the key just read typed: the window posts it right after the key. "" when the key typed
        nothing (arrows, F keys, Enter). Sets `typed` too."""
        if not self.typed:
            self.typed = self._posted.take_text(wait)
        return self.typed

    def wait_key(self) -> None:
        """The bare `Do: DoEvents: Loop While g = ""` of pag's final score (0x45391f): no clk, no stopspeech, no ambient
        sounds; the caller has called clk before."""
        while self.code_text == "":
            self._sleep(0.001)
            self.pump()

    def getkey(self, speech) -> None:
        """clk, wait with DoEvents for a key, then stop speech at once."""
        self.clk()
        while self.code_text == "":
            self._sleep(0.001)
            self.pump()
        speech.stop()

    def getkey2(self, speech, ambient) -> None:
        """The game's key wait with ambient sounds (GAME_SPEC 7, WAV_EVENT_MAP 4): st4 = now + 5, clk, then on every
        pass DoEvents and PlayRan until a key, then stop speech. ambient: game.sounds.GameSounds."""
        ambient.start_ambient_wait()
        self.clk()
        while True:
            self.pump()
            ambient.play_ran()
            if self.code_text != "":
                break
            self._sleep(0.001)
        speech.stop()
