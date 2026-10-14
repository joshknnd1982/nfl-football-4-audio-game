"""The game window: no controls, only a caption, and every key goes to the game. This is inspired by Jim Kitchen's Brain.

A plain Win32 window made through ctypes (no GUI toolkit: the toolkit alone was 22 MB of the 92 MB install, P10).
It has no child controls, so it keeps the keyboard focus itself and gets WM_KEYDOWN and WM_SYSKEYDOWN for
every key, like the original's Form1 (GAME_SPEC 8.1). The message's wParam is the virtual-key code VB's
Form_KeyDown received. Keys are not passed on, so no default handler acts on them, with two exceptions:
- Alt+F4 is passed on, so Windows still closes the window.
- Releasing Alt or F10 is swallowed, so Windows does not enter system-menu mode and later arrow
  keys still reach the game (DECISIONS P5: Alt and F10 are plain keys). Alt+letter beeps are swallowed too.
TranslateMessage is never called: no WM_CHAR is wanted. Tests post key messages to a hidden window, so the
keyboard is never taken from the player. Only the thread that made the window may run its message loop;
`close()` may be called from any thread.
"""
from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

from ..game.texts import CAPTION

log = logging.getLogger(__name__)

VK_MENU = 18   # Alt
VK_F4 = 115
VK_F10 = 121

WM_DESTROY, WM_CLOSE = 0x0002, 0x0010
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP, WM_SYSCHAR = 0x0100, 0x0101, 0x0104, 0x0105, 0x0106
WS_OVERLAPPEDWINDOW = 0x00CF0000
CW_USEDEFAULT = -2147483648
SW_SHOW = 5
COLOR_WINDOW = 5
IDC_ARROW = 32512
MB_OK = 0

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
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
user32.LoadCursorW.restype = wintypes.HANDLE
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

_CLASS_NAME = "KitchensincBrainWindow"
_windows: dict = {}          # window handle -> BrainWindow, for the one window procedure of the class
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


class BrainWindow:
    def __init__(self, on_key, on_close):
        self._on_key = on_key
        self._on_close = on_close
        self._looping = False
        _register()
        _pending.append(self)
        try:
            self.handle = user32.CreateWindowExW(0, _CLASS_NAME, CAPTION, WS_OVERLAPPEDWINDOW, CW_USEDEFAULT,
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
                self._on_key(int(wparam))
                return 0
            if msg in (WM_KEYUP, WM_SYSKEYUP):
                if wparam in (VK_MENU, VK_F10):
                    return 0                                                  # no system-menu mode
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
            if msg == WM_SYSCHAR:
                return 0                                                      # no beep for Alt+letter
            if msg == WM_CLOSE:
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

    # ----- what the program uses -----
    @property
    def title(self) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(self.handle, buffer, 256)
        return buffer.value

    def show(self) -> None:
        user32.ShowWindow(self.handle, SW_SHOW)
        user32.SetForegroundWindow(self.handle)

    def run(self) -> None:
        """The message loop; returns when the window has been destroyed."""
        msg = wintypes.MSG()
        self._looping = True
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
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
        user32.MessageBoxW(self.handle, text, title, MB_OK)
