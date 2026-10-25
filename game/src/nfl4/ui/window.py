"""The game window: no controls, only a caption, and every key goes to the game. This is inspired by Jim Kitchen.

A plain Win32 window made through ctypes (no GUI toolkit: the toolkit alone was 22 MB of Brain's first 92 MB install).
It has no child controls, so it keeps the keyboard focus itself and gets WM_KEYDOWN and WM_SYSKEYDOWN for every key,
like the original's Form1 (GAME_SPEC 8.1). The message's wParam is the virtual-key code VB's Form_KeyDown received.
Keys are not passed on, so no default handler acts on them, with two exceptions:
- Alt+F4 is passed on, so Windows still closes the window.
- Releasing Alt or F10 is swallowed, so Windows does not enter system-menu mode and later arrow keys still reach the
  game (GAME_SPEC 8.1: Alt and F10 are keys of the game). Alt+letter beeps are swallowed too.
Typed characters (nfl4 S7.1, fixesforgames B-W3, GAP_REGISTER G-K5): the message loop calls TranslateMessage, so a
key that types something makes a WM_CHAR, passed to `on_char` (letters as shown, keypad digits as digits, Shift+a as
"A"; GAME_SPEC 8.2, D-022 item 2). TranslateMessage POSTS that WM_CHAR behind whatever is already in the queue, so keys
that were posted before it would come first (TESTED in S7.1: five posted keys arrived as five keys, then five
characters). The loop therefore takes the WM_CHAR out at once with PeekMessage and hands the key and its character
over together: `on_key(code)` and right after it `on_char(char)`. Characters below 32 (Enter, Backspace, Escape, Tab)
and half surrogate pairs are not passed: those keys come as key codes. A test that posts both WM_KEYDOWN and WM_CHAR
gets every letter twice, because the loop makes the second one itself: tests post only WM_KEYDOWN.
Tests post key messages to a hidden window, so the keyboard is never taken from the player. Only the thread that made
the window may run its message loop; `close()` may be called from any thread.
"""
from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

from ..data import debuglog
from ..game.texts import CAPTION

log = logging.getLogger(__name__)

VK_MENU = 18   # Alt
VK_F4 = 115
VK_F10 = 121

WM_DESTROY, WM_CLOSE = 0x0002, 0x0010
WM_KEYDOWN, WM_KEYUP, WM_CHAR, WM_SYSKEYDOWN, WM_SYSKEYUP, WM_SYSCHAR = 0x0100, 0x0101, 0x0102, 0x0104, 0x0105, 0x0106
KEY_NAMES = {8: "Backspace", 9: "Tab", 13: "Enter", 16: "Shift", 17: "Ctrl", 18: "Alt", 19: "Pause", 20: "CapsLock", 27: "Escape",
             32: "Space", 33: "PageUp", 34: "PageDown", 35: "End", 36: "Home", 37: "Left", 38: "Up", 39: "Right", 40: "Down",
             44: "PrintScreen", 45: "Insert", 46: "Delete", 91: "LeftWindows", 92: "RightWindows", 93: "Menu", 144: "NumLock",
             145: "ScrollLock", 186: "Semicolon", 187: "Equals", 188: "Comma", 189: "Minus", 190: "Period", 191: "Slash",
             192: "Backquote", 219: "OpenBracket", 220: "Backslash", 221: "CloseBracket", 222: "Quote"}


def key_name(vk: int) -> str:
    if 48 <= vk <= 57 or 65 <= vk <= 90:
        return chr(vk)
    if 96 <= vk <= 105:
        return "Numpad%d" % (vk - 96)
    if 112 <= vk <= 135:
        return "F%d" % (vk - 111)
    return KEY_NAMES.get(vk, "vk%d" % vk)


def log_key(vk: int, lparam: int) -> None:
    """One key down in the debug log: its code and name, the modifiers held, whether it is an auto-repeat and the screen it
    reaches. While the player types text (a coach's name) only `typed` is written, never the key (playbook 7.11, privacy)."""
    if debuglog.typing_now():
        debuglog.event("key", "down", typed=True, ctx=debuglog.current_context())
        return
    held = "".join(name for name, code in (("Ctrl+", 0x11), ("Shift+", 0x10), ("Alt+", 0x12))
                   if user32.GetKeyState(code) & 0x8000 and vk != code)
    debuglog.event("key", "down", vk=vk, name=held + key_name(vk), repeat=bool(lparam & 0x40000000),
                   ctx=debuglog.current_context())


WS_OVERLAPPEDWINDOW = 0x00CF0000
CW_USEDEFAULT = -2147483648
SW_SHOW = 5
COLOR_WINDOW = 5
IDC_ARROW = 32512
MB_OK = 0
PM_REMOVE = 1

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HICON)]


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                   wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT,
                                wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.SetFocus.argtypes = [wintypes.HWND]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
user32.LoadCursorW.restype = wintypes.HANDLE
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

_CLASS_NAME = "KitchensincNfl4Window"
_windows: dict = {}          # window handle -> GameWindow, for the one window procedure of the class
_pending: list = []          # the window being made: messages arrive before CreateWindowEx returns its handle


def _dispatch(hwnd, msg, wparam, lparam):
    window = _windows.get(hwnd) or (_pending[-1] if _pending else None)
    if window is None:
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
    return window._wnd_proc(hwnd, msg, wparam, lparam)


_DISPATCH = WNDPROC(_dispatch)      # lives as long as the process: Windows calls it for every window of the class
_class_registered = False


def _register() -> None:
    global _class_registered
    if _class_registered:
        return
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc = _DISPATCH
    wc.hInstance = kernel32.GetModuleHandleW(None)
    wc.hCursor = user32.LoadCursorW(None, IDC_ARROW)
    wc.hbrBackground = COLOR_WINDOW + 1
    wc.lpszClassName = _CLASS_NAME
    if not user32.RegisterClassExW(ctypes.byref(wc)):
        raise OSError(f"RegisterClassEx failed: {ctypes.get_last_error()}")
    _class_registered = True


class GameWindow:
    def __init__(self, on_key, on_close, on_char=None, title: str = CAPTION):
        self._on_key = on_key
        self._on_close = on_close
        self._on_char = on_char
        self._looping = False
        _register()
        _pending.append(self)
        try:
            self.handle = user32.CreateWindowExW(0, _CLASS_NAME, title, WS_OVERLAPPEDWINDOW, CW_USEDEFAULT,
                                                 CW_USEDEFAULT, 420, 160, None, None,
                                                 kernel32.GetModuleHandleW(None), None)
        finally:
            _pending.pop()
        if not self.handle:
            raise OSError(f"CreateWindowEx failed: {ctypes.get_last_error()}")
        _windows[self.handle] = self

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        try:
            if msg in (WM_KEYDOWN, WM_SYSKEYDOWN):
                if wparam == VK_F4 and msg == WM_SYSKEYDOWN:
                    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)   # Alt+F4: Windows closes the window
                log_key(int(wparam), int(lparam))
                self._on_key(int(wparam))
                return 0
            if msg == WM_CHAR:                     # one the loop did not pair with its key (not expected)
                self._deliver_char(int(wparam))
                return 0
            if msg in (WM_KEYUP, WM_SYSKEYUP):
                if wparam in (VK_MENU, VK_F10):
                    return 0                                                  # no system-menu mode
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
            if msg == WM_SYSCHAR:
                return 0                                                      # no beep for Alt+letter
            if msg == WM_CLOSE:
                debuglog.event("app", "window_close", logging.INFO)
                self._on_close()
                user32.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                _windows.pop(hwnd, None)
                if self._looping:                                         # a quit message left in the queue would end the next loop
                    user32.PostQuitMessage(0)
                return 0
        except Exception:                                                     # never let an error cross into Windows
            log.exception("window message %s failed", msg)
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _deliver_char(self, code: int) -> None:
        if self._on_char is not None and code >= 32 and not 0xD800 <= code <= 0xDFFF:
            try:
                self._on_char(chr(code))
            except Exception:
                log.exception("character handler failed")

    # ----- what the program uses -----
    @property
    def title(self) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(self.handle, buffer, 256)
        return buffer.value

    def in_front(self) -> bool:
        return user32.GetForegroundWindow() == self.handle

    def show(self) -> bool:
        """Show the window and take the keyboard. Windows may refuse a program that was not started by the foreground
        program (one started from a console that is not in front): joining the input queue of the foreground thread for
        the moment of the call is the usual way (found with the listening tool, nfl4 S4.1). True when it is in front."""
        user32.ShowWindow(self.handle, SW_SHOW)
        if not self.in_front():
            foreground = user32.GetForegroundWindow()
            other = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
            mine = kernel32.GetCurrentThreadId()
            attached = bool(other) and other != mine and bool(user32.AttachThreadInput(mine, other, True))
            try:
                user32.BringWindowToTop(self.handle)
                user32.SetForegroundWindow(self.handle)
                user32.SetFocus(self.handle)
            finally:
                if attached:
                    user32.AttachThreadInput(mine, other, False)
        return self.in_front()

    def run(self) -> None:
        """The message loop; returns when the window has been destroyed."""
        msg = wintypes.MSG()
        char = wintypes.MSG()
        self._looping = True
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_KEYDOWN and msg.hWnd == self.handle:
                    # makes the WM_CHAR of a key that types (B-W3); take it out now so it follows its own key
                    typed = None
                    if user32.TranslateMessage(ctypes.byref(msg)) and user32.PeekMessageW(
                            ctypes.byref(char), self.handle, WM_CHAR, WM_CHAR, PM_REMOVE):
                        typed = int(char.wParam)
                    user32.DispatchMessageW(ctypes.byref(msg))
                    if typed is not None:
                        self._deliver_char(typed)
                    continue
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self._looping = False

    def close(self) -> None:
        """Ask the window to close, from any thread (the game thread calls it when the game ends)."""
        user32.PostMessageW(self.handle, WM_CLOSE, 0, 0)

    def destroy(self) -> None:
        if user32.IsWindow(self.handle):
            user32.DestroyWindow(self.handle)

    def message_box(self, text: str, title: str) -> None:
        """A plain box, OK only, no icon: the kind the original's MsgBox showed, with the same Windows sound (D-032 item 3)."""
        user32.MessageBoxW(self.handle, text, title, MB_OK)
