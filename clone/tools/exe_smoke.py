"""Smoke test of a BUILT nfl4.exe (P9 S9.2). Inspired by Jim Kitchen.

Starts the exe with ITS OWN PROGRAM FOLDER as the working directory (what a double click in Explorer or an old shortcut
does, and what used to lock the folder) and a scratch data folder, speech volume 0 and sound volume 2 percent
(a faint sound the loopback capture can still see), types keys into its window, and checks:
  1. it starts and speaks the welcome and the first prompt (log at debug level),
  2. a sound plays: the speakers' loopback capture is louder during playback than before it,
  3. the right NVDA DLL file is in the bundle (PE machine type matches the build),
  4. it exits cleanly when its window is closed (exit code 0, "NFL Football 4 clone closed" in the log, no WARNING or ERROR lines), within 2 seconds of its
     last log line (no lingering process), and then nothing holds its program folder (the folder can be renamed: fixesforgames.md B-U2),
  5. which modules the process loaded (pygame, SDL), to see the bundle is complete.
NVDA mode is not exercised here (it would speak through the owner's screen reader).
  6. (rules 0.15 and 0.16) the debug log: the launch log begins with the startup report, which has every required item with a value or
     "n/a (reason)", the welcome sentence is spoken once (`welcome_spoken`), the LAST line of the log is `closed`, and the problem
     report (`nfl4.exe --problem-report`) makes a zip with the listed members.
The sound check listens to the intro sound (foot0), which plays while the game starts; the game is closed by its window's close button
(WM_CLOSE), the way a player or an uninstaller closes it; no key is typed, so no game is begun.
Usage: <python with soundcard, numpy, pywin32> exe_smoke.py <path to nfl4.exe> <bits 32|64> <scratch folder> [sound volume in dB, -34 default, -50 = a control run] [sapi|nvda|jaws|auto]
"""
import os
import struct
import subprocess
import sys
import threading
import time

import numpy as np
import soundcard as sc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logfiles
import win32api
import win32con
import win32gui
import win32process

exe, bits, scratch = sys.argv[1], int(sys.argv[2]), sys.argv[3]
SOUND_VOLUME = int(sys.argv[4]) if len(sys.argv) > 4 else -34   # decibels below full (about 2 percent); -50 makes a control run: hardly any sound
# "jaws" with JAWS not running checks the fallback to SAPI 5 inside the built exe (one expected warning)
OUTPUT = sys.argv[5] if len(sys.argv) > 5 else "sapi"
os.makedirs(scratch, exist_ok=True)
with open(os.path.join(scratch, "settings.txt"), "w", encoding="utf-8") as handle:
    handle.write("# NFL Football 4 settings, format 1\n" + "".join(f"volume_{role} = 0\n" for role in (
        "announcer", "own_quarterback", "own_punter", "opponent_quarterback", "opponent_punter")) +
        f"sound_volume = {SOUND_VOLUME}\nspeech_output = {OUTPUT}\n")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (": " + detail if detail else ""))


# ----- loopback capture (peak per 20 ms) ------------------------------------------
RATE, CHUNK = 44100, 882
peaks = []
stop_capture = threading.Event()


def capture():
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        while not stop_capture.is_set():
            peaks.append((time.perf_counter(), float(np.abs(rec.record(numframes=CHUNK)).max())))


threading.Thread(target=capture, daemon=True).start()
for _ in range(150):                       # wait up to 15 s for a quiet second (other programs may be making sound)
    time.sleep(0.1)
    last = [p for t, p in peaks if t > time.perf_counter() - 1.0]
    if len(last) >= 40 and max(last) < 0.005:
        break
baseline = max(p for _, p in peaks[-45:]) if peaks else 0.0

# ----- start the exe and find its window ------------------------------------------------------
env = dict(os.environ, NFL4_DATA_DIR=scratch, NFL4_DEBUG="1")
started = time.perf_counter()
proc = subprocess.Popen([exe], cwd=os.path.dirname(exe), env=env)     # the program folder as working directory, on purpose


def find_window():
    found = []

    def visit(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == proc.pid:
            found.append(hwnd)

    win32gui.EnumWindows(visit, None)
    return found[0] if found else 0


hwnd = 0
for _ in range(100):
    hwnd = find_window()
    if hwnd or proc.poll() is not None:
        break
    time.sleep(0.1)
check("window appears", bool(hwnd), win32gui.GetWindowText(hwnd) if hwnd else f"exit code {proc.poll()}")


def key(vk):
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)


def log_text():
    return logfiles.launch_text(scratch)


# wait until the first prompt has been spoken (speech at volume 0 still takes its time): a first start asks the kind of season
FIRST_PROMPT = "which kind of season do you wish to play"
for _ in range(300):
    if FIRST_PROMPT in log_text() or proc.poll() is not None:
        break
    time.sleep(0.1)
text = log_text()
WELCOME = "Welcome to Josh Kennedy's N. F. L. football, loosely inspired by Jim Kitchen's original games."
check("speaks the welcome sentence once", text.count(" welcome_spoken ") == 1 and WELCOME in text)
check("the window title is the caption", "NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen" in text)
check("speaks the first prompt", FIRST_PROMPT in text)
time.sleep(1.5)

# ----- the intro sound (foot0) played while the game started and the welcome was said; no key is typed ---------------------
playing = [p for t, p in peaks if t > started]
loudest = max(playing) if playing else 0.0
check("a sound plays (loopback)", loudest > max(baseline * 3, 0.0005),
      f"baseline peak {baseline:.5f}, peak during playback {loudest:.5f}")

# modules the process has loaded (bundle completeness, DLL bitness)
try:
    handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, proc.pid)
    import win32process as wp
    modules = [os.path.basename(wp.GetModuleFileNameEx(handle, m)).lower() for m in wp.EnumProcessModulesEx(handle, 3)]  # 3 = 32 and 64-bit modules (a 64-bit driver watching a 32-bit exe)
    wanted = [m for m in modules if any(k in m for k in ("sdl2", "python3", "_mixer", "pywintypes"))]
    print("  modules of interest:", ", ".join(sorted(set(wanted))))
    check("python and SDL loaded", any("sdl2" in m for m in modules) and any(m.startswith("python3") for m in modules))
except Exception as exc:  # the module list is a bonus check
    print("  module list unavailable:", exc)

win32api.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)    # the window's close button: the program leaves at once (rule 0.10)
escaped = time.perf_counter()
closed_logged = None
while proc.poll() is None and time.perf_counter() - escaped < 40:
    if closed_logged is None and " app " in log_text() and " closed code=" in log_text():
        closed_logged = time.perf_counter()
    time.sleep(0.05)
if proc.poll() is None:
    proc.kill()
    code = None
else:
    code = proc.returncode
if closed_logged is None and " closed code=" in log_text():
    closed_logged = time.perf_counter()     # the process ended within one polling step of the line
lingered = None if closed_logged is None else time.perf_counter() - closed_logged
stop_capture.set()
print(f"  ran {time.perf_counter() - started:.1f} s")
check("exits cleanly", code == 0, f"exit code {code}")
check("the process is gone within 2 seconds of its last log line (no lingering process)", lingered is not None and lingered <= 2.0, "no closing line" if lingered is None else f"{lingered:.2f} s")
program_folder = os.path.dirname(exe)
probe = program_folder + "_probe_rename"
try:
    os.rename(program_folder, probe)
    os.rename(probe, program_folder)
    renamed = True
except OSError as exc:
    renamed = False
    print("  cannot rename the program folder:", exc)
check("nothing holds the program folder after exit (it can be renamed)", renamed)
text = log_text()
check("closes through its own exit path", "NFL Football 4 clone closed" in text)
lines = text.splitlines()
check("the launch log begins with the startup report", bool(lines) and lines[0].startswith("==== startup report"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from nfl4.data.sysreport import REQUIRED_KEYS   # noqa: E402  (the list of items the report must hold)
header = lines[:lines.index("==== end of startup report ====")] if "==== end of startup report ====" in lines else []
held = {l.split(" = ", 1)[0]: l.split(" = ", 1)[1] for l in header if " = " in l}
missing = [k for k in REQUIRED_KEYS if not held.get(k, "").strip()]
check("the startup report has every item with a value or n/a (reason)", not missing, ", ".join(missing[:5]))
check("the report's n/a items always say why", all(v.startswith("n/a (") for v in held.values() if v.startswith("n/a")))
check("the last line of the log is `closed`", bool(lines) and " closed code=" in lines[-1], lines[-1][:80] if lines else "empty")
report_out = os.path.join(scratch, "report-out")
made = subprocess.run([exe, "--problem-report", "--quiet", "--folder=" + report_out], env=env, cwd=os.path.dirname(exe),
                      capture_output=True, text=True, timeout=120)
zips = [n for n in os.listdir(report_out)] if os.path.isdir(report_out) else []
check("--problem-report makes one zip without a window", made.returncode == 0 and len(zips) == 1, made.stdout.strip()[:100])
bad = [l for l in text.splitlines() if (" WARNING " in l or " ERROR " in l or "Traceback" in l)
       and not (OUTPUT != "sapi" and "preferred engine unavailable" in l)]
check("no warnings or errors in the log", not bad, "; ".join(bad[:3]))
spoken = [l.split("speak ", 1)[1] for l in text.splitlines() if "speak " in l]
print("  spoken:", *[s[:60] for s in spoken[:8]], sep="\n    ")

# ----- bundled NVDA DLL: file present and the right architecture ----------------------------------
dll = os.path.join(os.path.dirname(exe), "_internal", "nfl4", "speech", "nvda_client",
                   "x64" if bits == 64 else "x86", "nvdaControllerClient.dll")
machine = None
if os.path.exists(dll):
    with open(dll, "rb") as handle:
        data = handle.read(4096)
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    machine = struct.unpack_from("<H", data, pe + 4)[0]
want = 0x8664 if bits == 64 else 0x14C
check("NVDA DLL bundled, right architecture", machine == want, f"{dll} machine {machine and hex(machine)}")
try:
    import pefile
    flags = pefile.PE(exe, fast_load=True).OPTIONAL_HEADER.DllCharacteristics
    # Control Flow Guard kills the process (0xC0000409) when a voice that emulates a CPU runs generated code (SmoothTalker)
    check("Control Flow Guard flag is off in nfl4.exe (voices that emulate a CPU)", not flags & 0x4000, hex(flags))
except ImportError:
    print("SKIP Control Flow Guard check (pefile not installed in this environment)")
sounds = os.path.join(os.path.dirname(exe), "assets", "sounds")
count = len([f for f in os.listdir(sounds) if f.lower().endswith(".wav")]) if os.path.isdir(sounds) else 0
check("26 wavs beside the exe", count == 26, f"{count}")
print("ALL PASS" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
