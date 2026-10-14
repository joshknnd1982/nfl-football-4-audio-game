"""Which processes hold files of a folder open? (Windows Restart Manager, the same service installers use.) Inspired by Jim Kitchen's Brain.

Usage: python who_holds_folder.py <folder> [more files or folders]
Lists every process the Restart Manager says uses any file under the folder (exe, dlls, wavs, anything), with its
process id and name, and says whether the folder itself can be renamed right now. Use it after closing the game and
before uninstalling: "folder in use" with nothing in Task Manager is nearly always another program (a screen reader,
Explorer, the search indexer, a virus scanner) that opened a file of the game, or a process whose working directory is
the folder. Nothing is changed or closed by this tool.
"""
import ctypes
import os
import sys
from ctypes import wintypes

CCH_RM_SESSION_KEY = 32
ERROR_MORE_DATA = 234


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [("dwProcessId", wintypes.DWORD), ("ProcessStartTime", FILETIME)]


class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [("Process", RM_UNIQUE_PROCESS), ("strAppName", ctypes.c_wchar * 256),
                ("strServiceShortName", ctypes.c_wchar * 64), ("ApplicationType", ctypes.c_int),
                ("AppStatus", ctypes.c_ulong), ("TSSessionId", wintypes.DWORD), ("bRestartable", wintypes.BOOL)]


rm = ctypes.WinDLL("rstrtmgr")


def holders(paths):
    session = wintypes.DWORD()
    key = ctypes.create_unicode_buffer(CCH_RM_SESSION_KEY + 1)
    if rm.RmStartSession(ctypes.byref(session), 0, key) != 0:
        raise OSError("RmStartSession failed")
    try:
        array = (wintypes.LPCWSTR * len(paths))(*paths)
        if rm.RmRegisterResources(session, len(paths), array, 0, None, 0, None) != 0:
            raise OSError("RmRegisterResources failed")
        needed, count, reasons = wintypes.UINT(0), wintypes.UINT(0), wintypes.DWORD(0)
        code = rm.RmGetList(session, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reasons))
        if code == 0 and needed.value == 0:
            return []
        info = (RM_PROCESS_INFO * max(needed.value, 1))()
        count = wintypes.UINT(len(info))
        code = rm.RmGetList(session, ctypes.byref(needed), ctypes.byref(count), info, ctypes.byref(reasons))
        if code != 0:
            raise OSError(f"RmGetList failed {code}")
        return [(info[i].Process.dwProcessId, info[i].strAppName) for i in range(count.value)]
    finally:
        rm.RmEndSession(session)


def files_under(folder, limit=400):
    out = []
    for base, _dirs, files in os.walk(folder):
        out.extend(os.path.join(base, name) for name in files)
        if len(out) >= limit:
            break
    return out[:limit]


def main():
    folder = os.path.abspath(sys.argv[1])
    paths = files_under(folder) + [os.path.abspath(p) for p in sys.argv[2:]]
    found = holders(paths) if paths else []
    print(f"{folder}: {len(paths)} files checked")
    print("held by:", ", ".join(f"{name} (pid {pid})" for pid, name in found) if found else "no process")
    probe = folder + "_probe_rename"
    try:
        os.rename(folder, probe)
        os.rename(probe, folder)
        print("the folder can be renamed: nothing holds it")
    except OSError as exc:
        print(f"the folder cannot be renamed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
