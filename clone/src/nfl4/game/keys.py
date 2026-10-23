"""The original's key fields and waits, without any window. This is inspired by Jim Kitchen.

GAME_SPEC 8.1: the original kept two fields, g = the key code text CStr(KeyCode) and g2 = the key character
LCase(Chr(KeyCode)), filled by Form_KeyDown, which only runs when the program calls DoEvents. The window thread posts
key codes here; pump() is DoEvents. Waiting speech does not pump, so keys typed during it are delivered afterwards,
exactly as in the original (TESTED in nfl4 S4.3: a synchronous SAPI Speak lets no message through, G-K1).
Key codes are Windows virtual-key codes, the same numbers VB's KeyDown received.

Typed characters (nfl4 S7.1, B-W3, G-K5): the window also posts the character a key typed (its WM_CHAR, which Windows
makes right after the key), in the same ordered queue. pump() keeps it in `typed`; a name prompt reads it with
take_typed() right after its key. The original's two fields do not change: g2 is still LCase(Chr(KeyCode)).

The global keys (nfl4 S7.4a, D-018, B-P13; Form_KeyDown p_42e5e0): pump() is Form_KeyDown as well as DoEvents. Alt (18)
and F10 (121) become the Escape code "27" with no character (0x42e645 to 0x42e66e); every other key sets g and g2 and
then `key_handler` is called with g, inside the pump, so F5 to F8, F11, F12 and Ctrl run their menus in the middle of
whatever wait pumped (game/hotkeys.py). A menu waits for keys itself (nested pumps) and ends with g = "112".
"""
from __future__ import annotations

import collections
import queue
import threading
import time

from ..data import debuglog

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
KEY_ALT, KEY_F10 = 18, 121           # Form_KeyDown makes both the Escape code "27" with g2 = "" (GAME_SPEC 8.1)
KEY_T = 84                           # the T key (owner rule 0.22, playbook 7.16): the code, never the character (F5 is "t" too, B-W6)
SPEAKING = 2                         # SpVoice.Status.RunningState while the voice speaks


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


class MenuClosedByTimeoutKey(Exception):
    """The T key was pressed in a menu that reads its keys itself (F9) during a game: the menu closes and the timeout is called
    (owner rule 0.22, playbook 7.16). Raised by `read_key` only while `timeout_close` says the key calls a timeout."""


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
        # Form_KeyDown's calls of the global menus: key_handler(g) after every key (game/hotkeys.py sets it)
        self.key_handler = None
        # S8.2: F1 repeats the prompt; at the next key wait the game says where the help is (hotkeys.py sets f1_hint)
        self.f1_hint = None
        self.f1_hint_window = 3.0
        self._f1_at = None
        # owner rule 0.22 (nfl4, N. F. L. rules): the T key. `timeout_eager` is called by the window thread the moment the key is
        # posted (it cuts the speech that is playing, so a wait on the speech ends at once); `timeout_posts` counts the T keys posted and
        # not yet taken by pump(), so the speakers know to pump before they say anything; `timeout_close` says whether a menu that
        # reads its own keys must close on T; `resumed` is what a handled T leaves for the wait it interrupted
        self.timeout_eager = None
        self.timeout_close = None
        self.timeout_posts = 0
        self.resumed = ""

    # called by the window thread
    def post(self, key_code: int) -> None:
        code = int(key_code)
        if code == KEY_T and self.timeout_eager is not None:
            # counted and queued BEFORE the speech is cut, so a game thread that wakes from the cut finds the key waiting
            self.timeout_posts += 1
            self._posted.put(code)
            counted = False
            try:
                counted = bool(self.timeout_eager())    # True: this T is a timeout key (it cut the speech); the speakers pump for it
            except Exception:                           # the window thread must never be stopped by it
                pass
            if not counted:
                self.timeout_posts = max(0, self.timeout_posts - 1)
            return
        self._posted.put(code)

    def post_char(self, char: str) -> None:
        if char:
            self._posted.put(str(char))

    def close(self) -> None:
        self.quit.set()

    def key_waiting(self) -> bool:
        """A key is posted and not yet taken by the game (any thread may ask; the JAWS wait does, 2026-10-23)."""
        return not self._posted.empty()

    # called by the game thread
    def pump(self) -> None:
        """DoEvents: run Form_KeyDown for every key posted since the last pump, in order."""
        debuglog.beat()                            # the hang watchdog: the game thread is alive
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
            self.typed = ""
            if item == KEY_T and self.timeout_posts > 0:
                self.timeout_posts -= 1
            if item in (KEY_ALT, KEY_F10):         # 0x42e645: KeyCode = Empty, g = "27", g2 = "", no menu
                self.code_text = "27"
                self.char = ""
                debuglog.event("key", "pump", vk=item, as_code="27", ctx=debuglog.current_context())
                continue
            if debuglog.typing_now():                 # while the player types a name, a key is never written (playbook 7.11)
                debuglog.event("key", "pump", typed=True, ctx=debuglog.current_context())
            else:
                debuglog.event("key", "pump", vk=item, ctx=debuglog.current_context())
            self.code_text = str(item)
            self.char = key_char(item)
            self._f1_at = self._clock() if item == KEY_F1 else None     # only a real F1 key, never the hand-back's
            if self.key_handler is not None:       # 0x42e6f0 to 0x42e811: F12, F11, F8, F7, F6, F5, Ctrl
                self.key_handler(self.code_text)

    def service_timeout(self) -> None:
        """Before anything is said: a T key is waiting (the window posted it while the game thread was inside a long text) and the
        speakers must not start a new text before it is taken. Everything posted up to it is taken first, in order."""
        if self.timeout_posts > 0:
            self.pump()

    def hand_back(self, how: str) -> None:
        """What a handled T key leaves for the wait it interrupted: g = "112", as every global key does (D-018), and `resumed` says
        which way the wait goes on: "granted" (a timeout was called: the menu starts again from its top) or "refused" (the menu
        goes on where it was). A wait that does not read `resumed` simply repeats its prompt, as after F1."""
        self.code_text = "112"
        self.char = ""
        self.resumed = how

    def take_resumed(self) -> str:
        how, self.resumed = self.resumed, ""
        return how

    def _say_f1_hint(self) -> None:
        """At the first key wait after the player's F1 (the prompt is queued by then): the one-sentence help hint, once."""
        at, self._f1_at = self._f1_at, None
        if at is not None and self.f1_hint is not None and self._clock() - at <= self.f1_hint_window:
            self.f1_hint()

    def wait_speech(self, speech) -> None:
        """`Do: DoEvents: Loop While g = "" And Voice.Status.RunningState = 2` (speckeys, readins, SayHints and the
        standings' wait): until a key comes or the speech has ended. The caller clears the key first when it must."""
        while True:
            self.pump()
            if self.code_text != "" or not speech.is_speaking():
                return
            self._sleep(0.001)

    def clk(self) -> None:
        """Clear the key code text, DoEvents, clear the key character, DoEvents (that order; clk p_429ac0: 0x429b07,
        0x429b0f, 0x429b19, 0x429b1b)."""
        self.code_text = ""
        self.resumed = ""                  # a new wait: what an earlier T key left for the old one is gone
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
            debuglog.beat()
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
            if item == KEY_T and self.timeout_posts > 0:
                self.timeout_posts -= 1
            self.code_text = str(item)
            self.char = key_char(item)
            self.typed = ""
            if debuglog.typing_now():
                debuglog.event("key", "read", typed=True, ctx=debuglog.current_context())
            else:
                debuglog.event("key", "read", vk=item, ctx=debuglog.current_context())
            if item == KEY_T and self.timeout_close is not None and self.timeout_close():
                raise MenuClosedByTimeoutKey()      # F9 during a game: the menu closes and the timeout is called (rule 0.22)
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
        self._say_f1_hint()
        while self.code_text == "":
            self._sleep(0.001)
            self.pump()

    def getkey(self, speech) -> None:
        """clk, wait with DoEvents for a key, then stop speech at once (getkey p_429b40: 0x429b7c, 0x429ba4, 0x429bb8)."""
        self.clk()
        self._say_f1_hint()
        while self.code_text == "":
            self._sleep(0.001)
            self.pump()
        speech.stop()

    def getkey2(self, speech, ambient) -> None:
        """The game's key wait with ambient sounds (GAME_SPEC 7, WAV_EVENT_MAP 4): st4 = now + 5, clk, then on every
        pass DoEvents and PlayRan until a key, then stop speech. ambient: game.sounds.GameSounds. (getkey2 p_429c00:
        0x429c63, 0x429c6c, 0x429c98, 0x429c9d, 0x429ccb.)"""
        ambient.start_ambient_wait()
        self.clk()
        self._say_f1_hint()
        while True:
            self.pump()
            ambient.play_ran()
            if self.code_text != "":
                break
            self._sleep(0.001)
        speech.stop()
