"""The window turns key presses into VB KeyDown codes (hidden window, no focus taken). This is inspired by Jim Kitchen's Brain.

Key messages are posted straight to the hidden window while its message loop runs, so the test
never steals the keyboard from the player. The window is a plain Win32 window made through ctypes.
"""
import threading
import time

import pytest

win32api = pytest.importorskip("win32api")
win32con = pytest.importorskip("win32con")

from nfl4.game.texts import CAPTION  # noqa: E402
from nfl4.ui.window import BrainWindow  # noqa: E402

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
def test_posted_key_messages_arrive_as_virtual_key_codes():
    got, closed = [], []
    window = BrainWindow(got.append, lambda: closed.append(1))
    assert window.title == CAPTION

    def send():
        for vk in KEYS:
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)
        win32api.PostMessage(window.handle, win32con.WM_SYSKEYDOWN, 18, 0x20000000)  # Alt alone

    run_window(window, send)
    assert got == KEYS + [18]
    assert closed == [1]


@pytest.mark.window
def test_alt_f4_closes_the_window_and_never_reaches_the_game():
    got, closed = [], []
    window = BrainWindow(got.append, lambda: closed.append(1))

    def send():
        win32api.PostMessage(window.handle, win32con.WM_SYSKEYDOWN, 115, 0x20000000)   # Alt+F4

    run_window(window, send, settle=0.5)
    assert got == [] and closed == [1]


@pytest.mark.window
def test_alt_and_f10_release_are_swallowed_and_other_releases_are_harmless():
    got = []
    window = BrainWindow(got.append, lambda: None)

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
        window = BrainWindow(got.append, lambda: None)
        run_window(window, lambda: win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, 13, 0))
        assert got == [13]


@pytest.mark.window
def test_a_failing_key_handler_does_not_break_the_message_loop():
    seen = []

    def on_key(code):
        seen.append(code)
        raise RuntimeError("handler failed")

    window = BrainWindow(on_key, lambda: None)

    def send():
        for vk in (65, 66):
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, vk, 0)

    run_window(window, send)
    assert seen == [65, 66]
