"""The startup report of the debug log: what this computer, this Windows and this setup are (playbook 7.11). This is inspired by Jim Kitchen.

Every item has a value or `n/a (reason)`, never silently missing (REQUIRED_KEYS is the list the tests hold it to). Every probe
is guarded: one that fails writes `n/a (reason)` and the traceback at DEBUG, and the report goes on. The report is built on a
worker thread after the game thread has started (the game does not wait for it); the log's writer holds the first lines back
until it is done (data/debuglog.py). Nothing here is sent anywhere.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import logging
import os
import platform
import shutil
import sys
import threading
import time

from .. import VERSION
from . import debuglog, paths

log = logging.getLogger("nfl4.report")

NA = "n/a"

# the screen readers and speech tools that matter, by process name; only these names are ever written
SCREEN_READERS = {"nvda.exe": "NVDA", "jfw.exe": "JAWS", "narrator.exe": "Narrator", "zoomtext.exe": "ZoomText",
                  "fsreader.exe": "Freedom Scientific reader", "sapi5.exe": "SAPI helper", "supernova.exe": "Supernova",
                  "snova.exe": "Supernova", "dolphin.exe": "Dolphin", "windoweyes.exe": "Window-Eyes", "zdsr.exe": "ZDSR",
                  "voiceover.exe": "VoiceOver", "orca.exe": "Orca", "cobra.exe": "Cobra", "hal.exe": "HAL",
                  "narratorquickstart.exe": "Narrator", "magnify.exe": "Magnifier", "utilman.exe": "Ease of Access"}

REQUIRED_KEYS = [
    # program
    "game", "version", "build_date", "source_commit", "bits", "frozen", "installed_or_portable", "exe_path", "program_dir",
    "data_dir", "log_dir", "log_file", "cwd_before", "cwd_after", "welcome_sentence", "command_line", "debug_log_level",
    "log_errors_last_launch", "run_id",
    # windows
    "windows_version", "windows_build", "windows_edition", "windows_bits", "display_language", "locale", "ansi_code_page",
    "oem_code_page", "time_zone", "administrator", "dpi", "cpu_count", "memory_mb", "free_space_mb", "data_on_onedrive",
    "documents_folder", "desktop_folder", "appdata_folder", "data_drive_type",
    # software
    "python", "pygame", "sdl", "audioop", "pywin32", "numpy", "screen_readers_running",
    # speech
    "speech_mode_setting", "speech_engine_in_use", "nvda_controller_dll", "nvda_running", "nvda_version", "nvda_load",
    "jaws_installed", "jaws_running", "jaws_version", "jaws_com", "sapi_started", "sapi_voice_count", "sapi_engines",
    "sapi_first_utterance", "voice_announcer", "voice_own_quarterback", "voice_opponent_quarterback", "voice_own_punter",
    "voice_opponent_punter",
    # audio
    "audio_device_opened", "audio_devices_found", "audio_format", "audio_buffer", "audio_error", "sounds_loaded",
    "sounds_problems",
    # files
    "settings_read", "settings_problems", "customization_files",
    # environment
    "env_LOCALAPPDATA", "env_APPDATA", "env_TEMP", "env_PROCESSOR_ARCHITECTURE", "env_OneDrive",
]


def na(reason: str) -> str:
    return "%s (%s)" % (NA, reason)


def _try(fn, what: str, default=None):
    """Run one probe; on failure the reason is the exception, the traceback goes to the DEBUG log, the report goes on."""
    try:
        return fn()
    except Exception as exc:
        log.debug("probe %s failed", what, exc_info=True)
        return na("%s: %s" % (type(exc).__name__, str(exc)[:100]))


def _value(value) -> str:
    if value is None or value == "":
        return na("none found")
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


# ----- Windows helpers (ctypes, no extra package) -----

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None
_shell32 = ctypes.WinDLL("shell32", use_last_error=True) if os.name == "nt" else None
_ole32 = ctypes.WinDLL("ole32") if os.name == "nt" else None
_user32 = ctypes.WinDLL("user32") if os.name == "nt" else None


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("length", wt.DWORD), ("load", wt.DWORD), ("total_phys", ctypes.c_ulonglong),
                ("avail_phys", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                ("avail_ext", ctypes.c_ulonglong)]


def memory_mb() -> str:
    status = _MemoryStatus()
    status.length = ctypes.sizeof(status)
    if not _kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return "%d total, %d free" % (status.total_phys // 2**20, status.avail_phys // 2**20)


def locale_name(kind: str) -> str:
    buf = ctypes.create_unicode_buffer(85)
    if kind == "ui":
        lang = _kernel32.GetUserDefaultUILanguage()
        if not _kernel32.LCIDToLocaleName(lang, buf, 85, 0):
            raise OSError("LCIDToLocaleName failed")
        return buf.value
    if not _kernel32.GetUserDefaultLocaleName(buf, 85):
        raise OSError("GetUserDefaultLocaleName failed")
    return buf.value


def known_folder(guid_text: str) -> str:
    class GUID(ctypes.Structure):
        _fields_ = [("a", wt.DWORD), ("b", wt.WORD), ("c", wt.WORD), ("d", ctypes.c_ubyte * 8)]

    guid = GUID()
    _ole32.CLSIDFromString.argtypes = [wt.LPCWSTR, ctypes.POINTER(GUID)]
    if _ole32.CLSIDFromString(guid_text, ctypes.byref(guid)) != 0:
        raise OSError("bad folder id")
    out = ctypes.c_wchar_p()
    result = _shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(out))
    if result != 0:
        raise OSError("SHGetKnownFolderPath %#x" % (result & 0xFFFFFFFF))
    try:
        return out.value or ""
    finally:
        _ole32.CoTaskMemFree(out)


DOCUMENTS_ID = "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
DESKTOP_ID = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
APPDATA_ID = "{3EB685DB-65F9-4CF6-A03A-E3EF65729F3D}"


def _where(path: str) -> str:
    """A folder's path plus where it lives: OneDrive, network, removable."""
    notes = []
    low = path.lower()
    if "onedrive" in low:
        notes.append("on OneDrive")
    drive = os.path.splitdrive(path)[0] or os.path.splitdrive(os.getcwd())[0]
    if path.startswith("\\\\"):
        notes.append("network share")
    elif drive:
        kind = _kernel32.GetDriveTypeW(drive + "\\")
        notes.append({2: "removable drive", 3: "fixed drive", 4: "network drive", 5: "CD drive", 6: "RAM disk"}.get(kind, "drive type %d" % kind))
    return "%s (%s)" % (path, ", ".join(notes))


def processes() -> list[tuple[str, int]]:
    """(lower-case exe name, pid) of every process; used only to look for the screen readers by name."""
    class Entry(ctypes.Structure):
        _fields_ = [("size", wt.DWORD), ("usage", wt.DWORD), ("pid", wt.DWORD), ("heap", ctypes.c_size_t), ("module", wt.DWORD),
                    ("threads", wt.DWORD), ("parent", wt.DWORD), ("priority", wt.LONG), ("flags", wt.DWORD),
                    ("exe", ctypes.c_wchar * 260)]

    _kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    _kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    for name in ("Process32FirstW", "Process32NextW"):
        getattr(_kernel32, name).argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    snap = _kernel32.CreateToolhelp32Snapshot(0x2, 0)
    if not snap or snap == ctypes.c_void_p(-1).value:
        raise OSError("CreateToolhelp32Snapshot failed")
    found = []
    try:
        entry = Entry()
        entry.size = ctypes.sizeof(entry)
        more = _kernel32.Process32FirstW(snap, ctypes.byref(entry))
        while more:
            found.append((entry.exe.lower(), int(entry.pid)))
            more = _kernel32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        _kernel32.CloseHandle(snap)
    return found


def _process_path(pid: int) -> str:
    _kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = _kernel32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        raise OSError("cannot open the process")
    try:
        size = wt.DWORD(1024)
        buf = ctypes.create_unicode_buffer(1024)
        _kernel32.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
        if not _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            raise OSError("QueryFullProcessImageName failed")
        return buf.value
    finally:
        _kernel32.CloseHandle(ctypes.c_void_p(handle))


def file_version(path: str) -> str:
    """The fixed file version (a.b.c.d) of an exe or dll."""
    version = ctypes.WinDLL("version")
    size = version.GetFileVersionInfoSizeW(path, None)
    if not size:
        raise OSError("no version resource")
    data = ctypes.create_string_buffer(size)
    if not version.GetFileVersionInfoW(path, 0, size, data):
        raise OSError("GetFileVersionInfo failed")
    pointer = ctypes.c_void_p()
    length = wt.UINT()
    if not version.VerQueryValueW(data, "\\", ctypes.byref(pointer), ctypes.byref(length)) or not pointer.value:
        raise OSError("VerQueryValue failed")
    info = (ctypes.c_uint32 * 13).from_address(pointer.value)
    ms, ls = info[4], info[5]
    fixed = "%d.%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)
    # NVDA's exe keeps a placeholder fixed version; its real version is in the product version string
    if version.VerQueryValueW(data, "\\VarFileInfo\\Translation", ctypes.byref(pointer), ctypes.byref(length)) and pointer.value:
        lang, page = (ctypes.c_uint16 * 2).from_address(pointer.value)
        if version.VerQueryValueW(data, "\\StringFileInfo\\%04x%04x\\ProductVersion" % (lang, page), ctypes.byref(pointer),
                                  ctypes.byref(length)) and pointer.value:
            product = ctypes.wstring_at(pointer.value, max(0, length.value - 1)).strip()
            if product and product != fixed:
                return "%s (file %s)" % (product, fixed)
    return fixed


def running_screen_readers(procs=None) -> list[str]:
    names = sorted({SCREEN_READERS[name] for name, _ in (procs if procs is not None else processes()) if name in SCREEN_READERS})
    return names


def pe_bits(path: str) -> str:
    """32 or 64 from the header of an exe or dll."""
    with open(path, "rb") as handle:
        head = handle.read(64)
        if head[:2] != b"MZ":
            raise OSError("not a PE file")
        handle.seek(int.from_bytes(head[60:64], "little"))
        sig = handle.read(6)
    if sig[:4] != b"PE\0\0":
        raise OSError("no PE header")
    machine = int.from_bytes(sig[4:6], "little")
    return {0x14C: "32", 0x8664: "64", 0xAA64: "arm64"}.get(machine, "machine %#x" % machine)


def voice_token_facts(voice_id: str) -> dict:
    """Language, engine DLL, its bitness and the registry hive of a voice token (read from the registry, without opening the voice)."""
    import winreg
    out = {"token": voice_id.rsplit("\\", 1)[-1], "hive": voice_id.split("\\", 1)[0]}
    root_name, _, subkey = voice_id.partition("\\")
    root = {"HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE, "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER}.get(root_name)
    if root is None:
        out["language"] = na("token is not in the registry")
        return out
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | view) as key:
                clsid = None
                try:
                    clsid = winreg.QueryValueEx(key, "CLSID")[0]
                except OSError:
                    pass
                try:
                    with winreg.OpenKey(key, "Attributes") as attrs:
                        out["language"] = winreg.QueryValueEx(attrs, "Language")[0]
                except OSError:
                    out["language"] = na("no Language attribute")
            out["registry_view"] = "64-bit" if view == winreg.KEY_WOW64_64KEY else "32-bit"
            if clsid:
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "CLSID\\" + clsid + "\\InprocServer32", 0,
                                        winreg.KEY_READ | view) as key:
                        dll = os.path.expandvars(winreg.QueryValueEx(key, "")[0])
                    out["engine_dll"] = os.path.basename(dll)
                    out["engine_bits"] = pe_bits(dll)
                except OSError as exc:
                    out["engine_dll"] = na("%s" % exc)
            else:
                out["engine_dll"] = na("the token names no engine")
            return out
        except OSError:
            continue
    out["language"] = na("token not found in the registry")
    return out


# ----- the sections -----

def program_section(first_args=(), cwd_before: str = "", cwd_after: str = "", welcome: str = "", last_errors: str = "") -> list:
    frozen = bool(getattr(sys, "frozen", False))
    exe = sys.executable if frozen else na("running from source: %s" % sys.executable)
    pdir = paths.program_dir()

    def build_date() -> str:
        target = sys.executable if frozen else os.path.join(pdir, "src", "nfl4", "__init__.py")
        return time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(target)))

    def commit() -> str:
        head = os.path.join(os.path.dirname(pdir) if not frozen else pdir, ".git", "HEAD")
        if not os.path.isfile(head):
            return na("not recorded in this build")
        with open(head, encoding="utf-8") as handle:
            ref = handle.read().strip()
        if ref.startswith("ref:"):
            ref_path = os.path.join(os.path.dirname(head), *ref[5:].split("/"))
            with open(ref_path, encoding="utf-8") as handle:
                ref = handle.read().strip()
        return ref[:10]

    def installed() -> str:
        if not frozen:
            return "source tree"
        return "installed" if any(n.lower().startswith("unins") for n in os.listdir(pdir)) else "portable"

    return [
        ("game", "NFL Football 4"), ("version", VERSION), ("build_date", _try(build_date, "build date")),
        ("source_commit", _try(commit, "source commit")), ("bits", "%d-bit Python" % (ctypes.sizeof(ctypes.c_void_p) * 8)),
        ("frozen", "yes, built exe" if frozen else "no, source"), ("installed_or_portable", _try(installed, "installed")),
        ("exe_path", exe), ("program_dir", pdir), ("data_dir", paths.user_data_dir()), ("log_dir", paths.log_dir()),
        ("log_file", os.path.basename(debuglog.path() or "") or na("no log file")),
        ("log_folder_used", debuglog.folder_info()),
        ("cwd_before", cwd_before or na("not recorded")), ("cwd_after", cwd_after or na("not moved, was not in the program folder")),
        ("welcome_sentence", welcome or na("not set")), ("command_line", " ".join(first_args) or "(none)"),
        ("debug_log_level", debuglog.level_name()), ("log_errors_last_launch", last_errors or "0"), ("run_id", debuglog.run_id()),
    ]


def windows_section() -> list:
    import winreg

    def reg(name: str) -> str:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return str(winreg.QueryValueEx(key, name)[0])

    def edition() -> str:
        name = reg("ProductName")
        if "Windows 10" in name and int(reg("CurrentBuildNumber")) >= 22000:
            name = name.replace("Windows 10", "Windows 11")           # the registry keeps the old product name on Windows 11
        parts = [name]
        for name in ("EditionID", "DisplayVersion"):
            try:
                parts.append(reg(name))
            except OSError:
                pass
        return " ".join(parts)

    def build() -> str:
        text = reg("CurrentBuildNumber")
        try:
            text += "." + reg("UBR")
        except OSError:
            pass
        return text

    def zone() -> str:
        return "%s, UTC%+d" % (time.tzname[0], -time.timezone // 3600 + (1 if time.daylight and time.localtime().tm_isdst > 0 else 0))

    def dpi() -> str:
        return str(_user32.GetDpiForSystem())

    def drive_free() -> str:
        root = paths.user_data_dir()
        while root and not os.path.exists(root):
            parent = os.path.dirname(root)
            if parent == root:
                break
            root = parent
        return str(shutil.disk_usage(root).free // 2**20)

    version = sys.getwindowsversion()
    arch = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or platform.machine()
    return [
        ("windows_version", "%d.%d (%s)" % (version.major, version.minor, platform.version())),
        ("windows_build", _try(build, "windows build")), ("windows_edition", _try(edition, "windows edition")),
        ("windows_bits", "%s (processor %s)" % ("64-bit" if "64" in arch else "32-bit", arch)),
        ("display_language", _try(lambda: locale_name("ui"), "display language")),
        ("locale", _try(lambda: locale_name("region"), "locale")),
        ("ansi_code_page", _try(lambda: _kernel32.GetACP(), "ansi code page")),
        ("oem_code_page", _try(lambda: _kernel32.GetOEMCP(), "oem code page")),
        ("time_zone", _try(zone, "time zone")),
        ("administrator", _try(lambda: bool(_shell32.IsUserAnAdmin()), "administrator")),
        ("dpi", _try(dpi, "dpi")), ("cpu_count", os.cpu_count() or na("unknown")),
        ("memory_mb", _try(memory_mb, "memory")), ("free_space_mb", _try(drive_free, "free space")),
        ("data_on_onedrive", _try(lambda: "yes" if "onedrive" in paths.user_data_dir().lower() else "no", "onedrive")),
        ("documents_folder", _try(lambda: _where(known_folder(DOCUMENTS_ID)), "documents folder")),
        ("desktop_folder", _try(lambda: _where(known_folder(DESKTOP_ID)), "desktop folder")),
        ("appdata_folder", _try(lambda: _where(known_folder(APPDATA_ID)), "appdata folder")),
        ("data_drive_type", _try(lambda: _where(paths.user_data_dir()), "data drive")),
    ]


def software_section() -> list:
    from importlib import metadata

    def package(name: str) -> str:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return na("not installed")

    def pygame_version() -> tuple[str, str]:
        import pygame
        return pygame.version.ver, ".".join(str(n) for n in pygame.get_sdl_version())

    pyg = _try(pygame_version, "pygame")
    return [
        ("python", "%s %s" % (platform.python_implementation(), platform.python_version())),
        ("pygame", pyg[0] if isinstance(pyg, tuple) else pyg), ("sdl", pyg[1] if isinstance(pyg, tuple) else pyg),
        ("audioop", _try(lambda: package("audioop-lts") if sys.version_info >= (3, 13) else "built in", "audioop")),
        ("pywin32", _try(lambda: package("pywin32"), "pywin32")),
        ("numpy", "present, %s" % package("numpy") if "numpy" in sys.modules and sys.modules["numpy"] else "not loaded"),
        ("screen_readers_running", _try(lambda: ", ".join(running_screen_readers()) or "none found", "screen readers")),
    ]


def speech_section(speech, speech_settings, started=None, first_utterance: str = "") -> list:
    """speech: the SpeechManager; speech_settings: settings.speech; started: the SapiStart."""
    procs = _try(processes, "processes")
    procs = procs if isinstance(procs, list) else []
    by_name = {}
    for name, pid in procs:
        by_name.setdefault(name, pid)

    def running_version(exe: str) -> str:
        pid = by_name.get(exe)
        if pid is None:
            return na("%s is not running" % exe)
        return file_version(_process_path(pid))

    nvda = getattr(speech, "nvda", None)
    jaws = getattr(speech, "jaws", None)
    sapi = getattr(speech, "sapi", None)
    if started is None:
        started = getattr(sapi, "started", None)
    if sapi is not None and getattr(sapi, "first_utterance", None) == "":
        until = time.monotonic() + 2.0                       # the first text is usually handed over within a second or two
        while not sapi.first_utterance and time.monotonic() < until:
            time.sleep(0.05)
    describe_nvda = _try(lambda: nvda.describe(), "nvda describe") if nvda is not None and hasattr(nvda, "describe") else {}
    describe_jaws = _try(lambda: jaws.describe(running="jfw.exe" in by_name), "jaws describe") if jaws is not None and hasattr(jaws, "describe") else {}
    describe_nvda = describe_nvda if isinstance(describe_nvda, dict) else {}
    describe_jaws = describe_jaws if isinstance(describe_jaws, dict) else {}
    engine = _try(lambda: getattr(speech.active_engine(), "name", None) or na("no engine can speak"), "active engine")
    items = [
        ("speech_mode_setting", getattr(speech_settings, "mode", na("unknown"))),
        ("speech_engine_in_use", engine),
        ("nvda_controller_dll", describe_nvda.get("dll", na("NVDA backend not described"))),
        ("nvda_running", "nvda.exe" in by_name if procs else na("process list unavailable")),
        ("nvda_version", _try(lambda: running_version("nvda.exe"), "nvda version")),
        ("nvda_load", describe_nvda.get("load", na("not described"))),
        ("jaws_installed", describe_jaws.get("installed", na("JAWS backend not described"))),
        ("jaws_running", "jfw.exe" in by_name if procs else na("process list unavailable")),
        ("jaws_version", _try(lambda: running_version("jfw.exe"), "jaws version")),
        ("jaws_com", describe_jaws.get("com", na("not described"))),
        ("sapi_started", (("yes, %s" % started.voice_name) if started is not None and started.ok else
                          ("no: %s" % started.error if started is not None else na("not started")))),
        ("sapi_voice_count", getattr(started, "voice_count", na("unknown"))),
    ]
    items.append(("sapi_engines", _try(lambda: voice_engines_text(), "sapi engines")))
    first = first_utterance or getattr(sapi, "first_utterance", "")
    items.append(("sapi_first_utterance", first or na("no text spoken yet when the report was made")))
    for role in ("announcer", "own_quarterback", "opponent_quarterback", "own_punter", "opponent_punter"):
        items.append(("voice_" + role, _try(lambda role=role: voice_text(speech, speech_settings, role), "voice " + role)))
    return items


def voice_engines_text(limit: int = 12) -> str:
    """The voice engines SAPI lists and how many voices each has."""
    from ..speech.voices import VoiceCatalog, group_by_engine
    catalog = VoiceCatalog()
    voices = catalog.voices(timeout=8.0)
    if not voices:
        return na("SAPI listed no voices")
    groups = group_by_engine(voices)
    text = "; ".join("%s: %d" % (name, len(group)) for name, group in groups[:limit])
    if len(groups) > limit:
        text += "; and %d more engines" % (len(groups) - limit)
    return "%d voices in %d engines (%s)%s" % (len(voices), len(groups), text,
                                               ", %d broken entries skipped" % catalog.broken if catalog.broken else "")


def voice_text(speech, speech_settings, role: str) -> str:
    saved = (speech_settings.voices or {}).get(role)
    details = speech.role_details(role)
    if details is None:
        return na("SAPI 5 not running; saved choice %s" % (saved or "first voice"))
    facts = voice_token_facts(details.voice_id)
    chosen = "saved choice" if saved else "first voice in SAPI's list (no choice saved)"
    if saved and saved.strip().lower() != details.voice_id.strip().lower():
        chosen = "saved voice not found, the first voice is used instead"
    return ("%s; token %s; language %s; engine %s %s-bit; registry %s %s; gender %s; chosen by: %s"
            % (details.name, facts.get("token"), facts.get("language"), facts.get("engine_dll", na("unknown")),
               facts.get("engine_bits", na("unknown")), facts.get("hive"), facts.get("registry_view", na("unknown")),
               details.gender or na("none"), chosen))


def audio_section(audio) -> list:
    def devices():
        from pygame._sdl2 import audio as sdl_audio
        names = sdl_audio.get_audio_device_names(False)
        return "; ".join(names) if names else na("SDL found no output device")

    def fmt():
        import pygame
        init = pygame.mixer.get_init()
        if not init:
            return na("the mixer is not running")
        return "%d Hz, %s, %d channels" % (init[0], "16-bit" if init[1] == -16 else str(init[1]), init[2])

    output = getattr(audio, "output", None)
    ok = bool(getattr(audio, "ok", False))
    problems = _try(lambda: audio.library.problems, "sound problems")
    library = getattr(audio, "library", None)
    shipped = _try(lambda: len([n for n in os.listdir(library.shipped_dir) if n.lower().endswith(".wav")]), "shipped sounds")
    player = _try(lambda: len([n for n in os.listdir(library.player_dir)]) if os.path.isdir(library.player_dir) else 0, "player sounds")
    return [
        ("audio_device_opened", ("yes, " + type(output).__name__ + ", SDL driver " + os.environ.get("SDL_AUDIODRIVER", "default"))
         if ok else "no: %s" % getattr(audio, "error", na("unknown"))),
        ("audio_devices_found", _try(devices, "audio devices")), ("audio_format", _try(fmt, "audio format")),
        ("audio_buffer", getattr(output, "buffer", na("no buffer"))), ("audio_error", getattr(audio, "error", None) or "none"),
        ("sounds_loaded", "%s shipped wav files found, %s files in the player's sounds folder" % (shipped, player)),
        ("sounds_problems", ("none" if problems == [] else ("; ".join(problems[:6]) if isinstance(problems, list) else problems))),
    ]


def files_section(store, custom, settings) -> list:
    def settings_read() -> str:
        from . import settingsfile
        if settings is None:
            raise ValueError("no settings in memory")
        text = settingsfile.render(settings)
        pairs = [line for line in text.splitlines() if line and not line.startswith("#")]
        return " ".join(line.replace(" = ", "=") for line in pairs if not line.startswith("voice_"))

    def customization() -> str:
        if custom is None:
            return na("the customization files could not be loaded")
        snap = custom.snapshot
        parts = []
        for spec in custom.specs:
            path = custom.files[spec.key].path if hasattr(custom.files[spec.key], "path") else spec.file_name
            size = os.path.getsize(path) if os.path.isfile(path) else 0
            parts.append("%s=%s (%d bytes, %d problems)" % (spec.file_name, snap.statuses.get(spec.key, "unknown"), size,
                                                          snap.problem_count(spec.key)))
        return "; ".join(parts)

    return [
        ("settings_read", _try(settings_read, "settings")),
        ("settings_problems", ("; ".join(store.problems[:6]) or "none") if store is not None else na("settings store not available here")),
        ("customization_files", _try(customization, "customization")),
    ]


def environment_section() -> list:
    out = []
    for name in ("LOCALAPPDATA", "APPDATA", "TEMP", "PROCESSOR_ARCHITECTURE", "OneDrive"):
        out.append(("env_" + name, os.environ.get(name) or na("not set")))
    return out


def missing_keys(report: debuglog.Report) -> list[str]:
    have = report.keys()
    return [key for key in REQUIRED_KEYS if key not in have]


def fill_missing(report: debuglog.Report, reason: str = "not collected on this start") -> None:
    """Any required item a probe did not deliver is written as n/a, so the report is never silently short."""
    for key in missing_keys(report):
        report.add(key, na(reason))


def build(report: debuglog.Report, *, args=(), cwd_before="", cwd_after="", welcome="", last_errors="", speech=None,
          speech_settings=None, started=None, audio=None, store=None, custom=None, settings=None,
          first_utterance="") -> None:
    """Fill the startup report. Called on a worker thread; each section is guarded so one failing section never stops the rest."""
    sections = [
        ("program", lambda: program_section(args, cwd_before, cwd_after, welcome, last_errors)),
        ("windows", windows_section), ("software", software_section),
        ("audio", lambda: audio_section(audio)),
        ("files", lambda: files_section(store, custom, settings)),
        ("environment", environment_section),
        ("speech", lambda: speech_section(speech, speech_settings, started, first_utterance)),    # last: it waits for the first text
    ]
    for title, make in sections:
        began = time.perf_counter()
        try:
            items = make()
        except Exception as exc:
            log.warning("report section %s failed", title, exc_info=True)
            items = [(key, na("section failed: %s" % type(exc).__name__)) for key in REQUIRED_KEYS if _section_of(key) == title]
        report.section(title, [(k, _value(v)) for k, v in items])
        debuglog.event("report", "section", title=title, ms=round((time.perf_counter() - began) * 1000, 1))
    fill_missing(report)


_SECTION_KEYS: dict[str, str] = {}


def _section_of(key: str) -> str:
    if not _SECTION_KEYS:
        order = ["program", "windows", "software", "speech", "audio", "files", "environment"]
        marks = {"game": 0, "windows_version": 1, "python": 2, "speech_mode_setting": 3, "audio_device_opened": 4,
                 "settings_read": 5, "env_LOCALAPPDATA": 6}
        current = 0
        for name in REQUIRED_KEYS:
            current = marks.get(name, current)
            _SECTION_KEYS[name] = order[current]
    return _SECTION_KEYS.get(key, "program")


def build_in_background(**kwargs) -> threading.Thread:
    """Start the report on its own thread; it ends with debuglog.report_done() whatever happens."""
    report = debuglog.report()

    def work():
        try:
            if report is not None:
                build(report, **kwargs)
        except Exception:
            log.exception("the startup report failed")
        finally:
            debuglog.report_done()

    thread = threading.Thread(target=work, name="startup-report", daemon=True)
    if report is not None:
        report.thread = thread
        report.on_close = lambda: fill_missing(report, "the program ended before this item was collected")
    thread.start()
    return thread


def render_text(**kwargs) -> list[str]:
    """The report made again now, as lines (the problem report's system.txt)."""
    report = debuglog.Report()
    build(report, **kwargs)
    return report.lines()
