"""The window turns key presses into VB KeyDown codes and typed characters (hidden window, no focus taken).
This is inspired by Jim Kitchen.

Key messages are posted straight to the hidden window while its message loop runs, so the test never steals the
keyboard from the player. The window is a plain Win32 window made through ctypes. Only WM_KEYDOWN is posted: the
message loop's TranslateMessage makes the WM_CHAR itself (posting both would give every letter twice, B-W3).
"""
import ctypes
import threading
import time

import pytest

win32api = pytest.importorskip("win32api")
win32con = pytest.importorskip("win32con")

from nfl4.game.keys import KeyInput  # noqa: E402
from nfl4.game.texts import CAPTION  # noqa: E402
from nfl4.ui.window import GameWindow  # noqa: E402

KEYS = [27, 13, 9, 32, 38, 40, 37, 39, 49, 65, 112, 113, 114, 115, 121, 16, 17, 186, 96, 8, 46]


def possible_chars(vk: int) -> set:
    """What a key can type on this PC's keyboard layout with no modifier, with Shift down and with Caps Lock on.

    TranslateMessage builds a posted key's character from the REAL keyboard's state (TESTED in S7.1: while the owner
    held Shift, a posted 'a' typed "A" and '1' typed "!", fixesforgames B-X18), so a test may not expect one case.
    ToUnicodeEx with an explicit key state (flag 4: leave the keyboard state alone) gives the choices."""
    user32 = ctypes.WinDLL("user32")
    user32.GetKeyboardLayout.restype = ctypes.c_void_p
    user32.ToUnicodeEx.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_wchar_p,
                                   ctypes.c_int, ctypes.c_uint, ctypes.c_void_p]
    layout = user32.GetKeyboardLayout(0)
    scan = user32.MapVirtualKeyW(vk, 0)
    found = set()
    for key, value in ((None, 0), (0x10, 0x80), (0x14, 0x01)):        # nothing, Shift down, Caps Lock on
        state = (ctypes.c_ubyte * 256)()
        if key is not None:
            state[key] = value
        buffer = ctypes.create_unicode_buffer(8)
        count = user32.ToUnicodeEx(vk, scan, state, buffer, 8, 4, layout)
        if count > 0:
            found.add(buffer.value[:count])
    return found


def run_window(window, send, settle=0.3):
    """Run the message loop; `send` posts messages from another thread; then the window is closed."""
    def worker():
        time.sleep(0.05)
        send()
        time.sleep(settle)
        window.close()

    threading.Thread(target=worker, daemon=True).start()
    safety = threading.Timer(5.0, window.close)
    safety.start()
    window.run()
    safety.cancel()


@pytest.mark.window
def test_the_title_is_the_owners_title_format():
    window = GameWindow(lambda code: None, lambda: None)
    try:
        assert window.title == CAPTION == "NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen"    # rule 0.5.1
    finally:
        window.destroy()


@pytest.mark.window
def test_posted_key_messages_arrive_as_virtual_key_codes():
    got, closed = [], []
    window = GameWindow(got.append, lambda: closed.append(1))

    def send():
        for vk in KEYS:
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)
        win32api.PostMessage(window.handle, win32con.WM_SYSKEYDOWN, 18, 0x20000000)  # Alt alone

    run_window(window, send)
    assert got == KEYS + [18]
    assert closed == [1]


@pytest.mark.window
def test_keys_that_type_are_followed_by_their_character_and_others_by_none():
    got = []
    window = GameWindow(lambda code: got.append(("key", code)), lambda: None, on_char=lambda ch: got.append(("char", ch)))
    sent = [65, 90, 49, 48, 32, 97, 105, 13, 8, 27, 38, 112, 16]       # a z 1 0 space, keypad 1 and 9, Enter ...

    def send():
        for vk in sent:
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)

    run_window(window, send)
    keys = [code for kind, code in got if kind == "key"]
    assert keys == sent
    chars = {}
    for i, (kind, value) in enumerate(got):
        if kind == "char":
            assert got[i - 1][0] == "key"                               # each character right after its key
            chars[got[i - 1][1]] = value
    assert {65, 90, 32} <= set(chars) <= {65, 90, 49, 48, 32, 97, 105}  # Enter, Backspace, Esc, Up, F1, Shift: none
    for vk, char in chars.items():
        assert char in possible_chars(vk), (vk, char)                   # B-X18: the case follows the real keyboard
    assert {"a", "A"} >= possible_chars(65) and "a" in possible_chars(65)
    for vk, digit in ((97, "1"), (105, "9")):                           # keypad digits type digits (D-022)
        assert chars.get(vk, digit) == digit


@pytest.mark.window
def test_shift_down_in_the_keyboard_state_makes_the_posted_keys_type_their_shifted_characters():
    """The cause of the S7.1 repeat-run failures, shown on purpose (B-X18): the window thread's keyboard state, not the
    posted message, decides the case. Only this thread's state is changed and it is put back."""
    user32 = ctypes.WinDLL("user32")
    saved = (ctypes.c_ubyte * 256)()
    user32.GetKeyboardState(saved)
    shifted = (ctypes.c_ubyte * 256)(*saved)
    shifted[0x10] = shifted[0xA0] = 0x80          # VK_SHIFT, VK_LSHIFT down
    shifted[0x14] = 0                             # Caps Lock off
    got = []
    window = GameWindow(lambda code: got.append(("key", code)), lambda: None, on_char=lambda ch: got.append(("char", ch)))

    def send():
        for vk in (65, 49):
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)

    user32.SetKeyboardState(shifted)
    try:
        run_window(window, send)
    finally:
        user32.SetKeyboardState(saved)
    chars = [value for kind, value in got if kind == "char"]
    shifted_a = possible_chars(65) - {"a"}
    assert got[0] == ("key", 65) and got[2] == ("key", 49)
    assert chars[0] in shifted_a and chars[0] != "a"                       # "A": the real keyboard state decides
    assert chars[1] in possible_chars(49) and chars[1] != "1"              # "!" on a US layout


@pytest.mark.window
def test_a_window_without_a_character_handler_still_gets_every_key():
    got = []
    window = GameWindow(got.append, lambda: None)

    def send():
        for vk in (65, 66, 13):
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)

    run_window(window, send)
    assert got == [65, 66, 13]


@pytest.mark.window
def test_typed_characters_reach_the_key_input_in_order_with_their_keys():
    keys = KeyInput()
    window = GameWindow(keys.post, keys.close, on_char=keys.post_char)

    def send():
        for vk in (74, 79, 69, 38):                                     # j o e, Up
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)

    run_window(window, send)
    keys.quit.clear()
    read = []
    for _ in range(4):
        code = keys.read_key()
        read.append((code, keys.char, keys.take_typed(0.01)))
    # g2 stays LCase(Chr(code)); the typed character's case follows the real keyboard's Shift and Caps Lock (B-X18)
    assert [(code, char, typed.lower()) for code, char, typed in read] == \
           [(74, "j", "j"), (79, "o", "o"), (69, "e", "e"), (38, "&", "")]
    assert all(typed in possible_chars(code) for code, _, typed in read[:3])


@pytest.mark.window
def test_alt_f4_closes_the_window_and_never_reaches_the_game():
    got, closed = [], []
    window = GameWindow(got.append, lambda: closed.append(1))

    def send():
        win32api.PostMessage(window.handle, win32con.WM_SYSKEYDOWN, 115, 0x20000000)   # Alt+F4

    run_window(window, send, settle=0.5)
    assert got == [] and closed == [1]


@pytest.mark.window
def test_alt_and_f10_release_are_swallowed_and_other_releases_are_harmless():
    got = []
    window = GameWindow(got.append, lambda: None)

    def send():
        for vk in (18, 121, 65):
            win32api.PostMessage(window.handle, win32con.WM_KEYUP, vk, 0)
        win32api.PostMessage(window.handle, win32con.WM_SYSKEYUP, 18, 0)
        win32api.PostMessage(window.handle, win32con.WM_SYSCHAR, 65, 0)
        win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, 40, 0)

    run_window(window, send)
    assert got == [40]


@pytest.mark.window
def test_two_windows_one_after_the_other_and_close_from_another_thread():
    for _ in range(2):
        got = []
        window = GameWindow(got.append, lambda: None)
        run_window(window, lambda: win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, 13, 0))
        assert got == [13]


@pytest.mark.window
def test_a_failing_key_handler_does_not_break_the_message_loop():
    seen = []

    def on_key(code):
        seen.append(code)
        raise RuntimeError("handler failed")

    window = GameWindow(on_key, lambda: None)

    def send():
        for vk in (65, 66):
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)

    run_window(window, send)
    assert seen == [65, 66]
