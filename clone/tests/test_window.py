"""The window turns key presses into VB KeyDown codes and typed characters (hidden window, no focus taken).
This is inspired by Jim Kitchen.

Key messages are posted straight to the hidden window while its message loop runs, so the test never steals the
keyboard from the player. The window is a plain Win32 window made through ctypes. Only WM_KEYDOWN is posted: the
message loop's TranslateMessage makes the WM_CHAR itself (posting both would give every letter twice, B-W3).
"""
import threading
import time

import pytest

win32api = pytest.importorskip("win32api")
win32con = pytest.importorskip("win32con")

from nfl4.game.keys import KeyInput  # noqa: E402
from nfl4.game.texts import CAPTION  # noqa: E402
from nfl4.ui.window import GameWindow  # noqa: E402

KEYS = [27, 13, 9, 32, 38, 40, 37, 39, 49, 65, 112, 113, 114, 115, 121, 16, 17, 186, 96, 8, 46]


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
    assert chars == {65: "a", 90: "z", 49: "1", 48: "0", 32: " ", 97: "1", 105: "9"}   # keypad types digits (D-022)
    assert len([g for g in got if g[0] == "char"]) == 7                   # Enter, Backspace, Esc, arrows, F1, Shift: none


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
    assert read == [(74, "j", "j"), (79, "o", "o"), (69, "e", "e"), (38, "&", "")]   # g2 stays LCase(Chr(code))


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
