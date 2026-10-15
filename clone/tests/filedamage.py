"""The ways a player (or a disk) can damage a text file, for the 7.10 matrix (S7.7). This is inspired by Jim Kitchen.

Each damage is a function(path) that changes the file the way the name says; `holding` and `read_only` are context managers
for the two that are a state of the file, not of its bytes (a real Windows sharing violation, the read-only attribute).
"""
import contextlib
import os
import random
import stat
import sys

# the kinds of playbook 7.10 that change the bytes (the file is there before and after)
BYTE_DAMAGES = ("empty", "cut_in_half", "random_bytes", "other_encoding", "huge", "newer_format", "no_header",
                "bad_line_in_the_middle", "binary_zeros", "another_list_header")


def apply(kind: str, path, seed: int = 1) -> None:
    """Damage the file at `path` in place."""
    path = str(path)
    raw = open(path, "rb").read()
    text = raw.decode("utf-8-sig", errors="replace")
    rng = random.Random(seed)
    if kind == "empty":
        data = b""
    elif kind == "cut_in_half":
        data = raw[:len(raw) // 2]
    elif kind == "random_bytes":
        data = bytes(rng.randrange(256) for _ in range(max(64, len(raw) // 4)))
    elif kind == "other_encoding":
        data = text.encode("utf-16-le")                          # no byte order mark: the text is full of NUL bytes
    elif kind == "huge":
        data = raw + b"\r\n" + b"# padding padding padding padding padding\r\n" * 30000   # more than a megabyte
    elif kind == "newer_format":
        data = text.replace("format 1.", "format 2.", 1).encode("utf-8")
    elif kind == "no_header":
        data = "\r\n".join(text.splitlines()[1:]).encode("utf-8")
    elif kind == "bad_line_in_the_middle":
        lines = text.splitlines()
        lines.insert(len(lines) // 2, "this line is not an entry at all")
        lines.insert(len(lines) // 2 + 3, "[[[ ] ] ] = = =")
        data = "\r\n".join(lines).encode("utf-8")
    elif kind == "binary_zeros":
        data = b"\x00" * 300
    elif kind == "another_list_header":
        lines = text.splitlines()
        lines[0] = "# NFL Football 4 something else, format 1."
        data = "\r\n".join(lines).encode("utf-8")
    else:
        raise ValueError(kind)
    with open(path, "wb") as handle:
        handle.write(data)


@contextlib.contextmanager
def read_only(path):
    os.chmod(path, stat.S_IREAD)
    try:
        yield
    finally:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


@contextlib.contextmanager
def holding(path):
    """Another program has the file open without sharing it: a real sharing violation (Windows only)."""
    if sys.platform != "win32":
        yield
        return
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                     wintypes.DWORD, wintypes.HANDLE]
    handle = kernel32.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)      # GENERIC_READ, no sharing
    assert handle not in (None, wintypes.HANDLE(-1).value)
    try:
        yield
    finally:
        kernel32.CloseHandle(handle)
