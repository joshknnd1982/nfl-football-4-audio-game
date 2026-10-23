"""One file fetched over HTTPS with Windows' own WinHTTP (nfl4: D-128, the latest N. F. L. calendar, only when the player asks). This is inspired by Jim
Kitchen.

The build leaves Python's ssl module and its OpenSSL libraries out (playbook 8.1's size budget: about 6 MB), so the game cannot use urllib for HTTPS.
WinHTTP is part of every Windows the game runs on; it uses the system's certificates and its proxy settings, and costs no byte of the build. This
module is the portability seam for the network (playbook 7.2): another platform gives `fetch` its own body.

`fetch(url)` returns (the HTTP status, the body) or raises `WebError` with a kind the caller can say in one sentence:

    offline     the name could not be resolved or the server could not be reached (no connection, no internet)
    timeout     the server did not answer in time
    too_large   the body is larger than the caller allows
    failed      anything else (a security error, a broken answer), with the WinHTTP error number in the detail

Nothing here runs by itself: the game calls it only from the menu item the player chose, and the log (rule 0.15) says what was asked and the answer.
"""
from __future__ import annotations

import ctypes
import logging
import sys
from urllib.parse import urlsplit

log = logging.getLogger("nfl4.data")

USER_AGENT = "NFL Football 4 (Josh Kennedy's audio game)"
ACCESS_AUTOMATIC_PROXY, ACCESS_DEFAULT_PROXY = 4, 0
FLAG_SECURE = 0x00800000
QUERY_STATUS_CODE, QUERY_FLAG_NUMBER = 19, 0x20000000
OFFLINE_ERRORS = {12007, 12029, 12030, 12031, 12005, 12017}      # name not resolved, cannot connect, connection error or reset, invalid URL, aborted
TIMEOUT_ERRORS = {12002}


class WebError(Exception):
    def __init__(self, kind: str, detail: str = ""):
        super().__init__("%s: %s" % (kind, detail) if detail else kind)
        self.kind = kind
        self.detail = detail


def _api():
    if sys.platform != "win32":
        raise WebError("failed", "no WinHTTP on this platform")
    dll = ctypes.WinDLL("winhttp", use_last_error=True)
    HINTERNET, DWORD, BOOL, LPCWSTR = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p
    LPDWORD = ctypes.POINTER(DWORD)
    signatures = {
        "WinHttpOpen": (HINTERNET, [LPCWSTR, DWORD, LPCWSTR, LPCWSTR, DWORD]),
        "WinHttpSetTimeouts": (BOOL, [HINTERNET, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]),
        "WinHttpConnect": (HINTERNET, [HINTERNET, LPCWSTR, ctypes.c_uint16, DWORD]),
        "WinHttpOpenRequest": (HINTERNET, [HINTERNET, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, ctypes.c_void_p, DWORD]),
        "WinHttpSendRequest": (BOOL, [HINTERNET, LPCWSTR, DWORD, ctypes.c_void_p, DWORD, DWORD, ctypes.c_size_t]),
        "WinHttpReceiveResponse": (BOOL, [HINTERNET, ctypes.c_void_p]),
        "WinHttpQueryHeaders": (BOOL, [HINTERNET, DWORD, LPCWSTR, ctypes.c_void_p, LPDWORD, LPDWORD]),
        "WinHttpQueryDataAvailable": (BOOL, [HINTERNET, LPDWORD]),
        "WinHttpReadData": (BOOL, [HINTERNET, ctypes.c_void_p, DWORD, LPDWORD]),
        "WinHttpCloseHandle": (BOOL, [HINTERNET]),
    }
    for name, (restype, argtypes) in signatures.items():
        function = getattr(dll, name)
        function.restype, function.argtypes = restype, argtypes
    return dll


def _error(what: str) -> WebError:
    code = ctypes.get_last_error()
    kind = "offline" if code in OFFLINE_ERRORS else "timeout" if code in TIMEOUT_ERRORS else "failed"
    return WebError(kind, "%s failed with WinHTTP error %d" % (what, code))


def fetch(url: str, timeout: float = 15.0, max_bytes: int = 2_000_000) -> tuple:
    """GET `url` (https only): (status, body). Raises WebError. Every handle is closed before it returns."""
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise WebError("failed", "only an https address can be fetched")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    api = _api()
    millis = max(1000, int(timeout * 1000))
    handles = []
    try:
        session = api.WinHttpOpen(USER_AGENT, ACCESS_AUTOMATIC_PROXY, None, None, 0)
        if not session:                                     # Windows 8 and older: no automatic proxy, the default one
            session = api.WinHttpOpen(USER_AGENT, ACCESS_DEFAULT_PROXY, None, None, 0)
        if not session:
            raise _error("WinHttpOpen")
        handles.append(session)
        api.WinHttpSetTimeouts(session, millis, millis, millis, millis)
        connect = api.WinHttpConnect(session, parts.hostname, parts.port or 443, 0)
        if not connect:
            raise _error("WinHttpConnect")
        handles.append(connect)
        request = api.WinHttpOpenRequest(connect, "GET", path, None, None, None, FLAG_SECURE)
        if not request:
            raise _error("WinHttpOpenRequest")
        handles.append(request)
        if not api.WinHttpSendRequest(request, None, 0, None, 0, 0, 0):
            raise _error("WinHttpSendRequest")
        if not api.WinHttpReceiveResponse(request, None):
            raise _error("WinHttpReceiveResponse")
        status = ctypes.c_uint32(0)
        size = ctypes.c_uint32(ctypes.sizeof(status))
        if not api.WinHttpQueryHeaders(request, QUERY_STATUS_CODE | QUERY_FLAG_NUMBER, None, ctypes.byref(status), ctypes.byref(size), None):
            raise _error("WinHttpQueryHeaders")
        body = bytearray()
        while True:
            available = ctypes.c_uint32(0)
            if not api.WinHttpQueryDataAvailable(request, ctypes.byref(available)):
                raise _error("WinHttpQueryDataAvailable")
            if available.value == 0:
                break
            if len(body) + available.value > max_bytes:
                raise WebError("too_large", "more than %d bytes" % max_bytes)
            buffer = ctypes.create_string_buffer(available.value)
            read = ctypes.c_uint32(0)
            if not api.WinHttpReadData(request, buffer, available.value, ctypes.byref(read)):
                raise _error("WinHttpReadData")
            body += buffer.raw[:read.value]
        return int(status.value), bytes(body)
    finally:
        for handle in reversed(handles):
            api.WinHttpCloseHandle(handle)
