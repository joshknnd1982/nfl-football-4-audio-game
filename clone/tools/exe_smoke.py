"""Smoke test of a BUILT nfl4.exe (P9 S9.2). Inspired by Jim Kitchen's Brain.

Starts the exe with ITS OWN PROGRAM FOLDER as the working directory (what a double click in Explorer or an old shortcut
does, and what used to lock the folder) and a scratch data folder, speech volume 0 and sound volume 2 percent
(a faint sound the loopback capture can still see), types keys into its window, and checks:
  1. it starts and speaks the title and the main prompt (log at debug level),
  2. a sound plays: the speakers' loopback capture is louder during playback than before it,
  3. the right NVDA DLL file is in the bundle (PE machine type matches the build),
  4. it exits cleanly (exit code 0, "Brain clone closed" in the log, no WARNING or ERROR lines), within 2 seconds of its
     last log line (no lingering process), and then nothing holds its program folder (the folder can be renamed: fixesforgames.md B-U2),
  5. which modules the process loaded (pygame, SDL), to see the bundle is complete.
NVDA mode is not exercised here (it would speak through the owner's screen reader).
Usage: <python with soundcard, numpy, pywin32> exe_smoke.py <path to nfl4.exe> <bits 32|64> <scratch folder> [sound volume] [sapi|nvda|jaws|auto]
"""
import os
import struct
import subprocess
import sys
import threading
import time

import numpy as np
import soundcard as sc
import win32api
import win32con
import win32gui
import win32process

exe, bits, scratch = sys.argv[1], int(sys.argv[2]), sys.argv[3]
SOUND_VOLUME = int(sys.argv[4]) if len(sys.argv) > 4 else 2    # 0 makes a control run: no sound expected
# "jaws" with JAWS not running checks the fallback to SAPI 5 inside the built exe (one expected warning)
OUTPUT = sys.argv[5] if len(sys.argv) > 5 else "sapi"
os.makedirs(scratch, exist_ok=True)
with open(os.path.join(scratch, "settings.txt"), "w", encoding="utf-8") as handle:
    handle.write(f"# Brain settings, format 1\nspeech_volume = 0\nsound_volume = {SOUND_VOLUME}\nspeech_output = {OUTPUT}\n")
log_path = os.path.join(scratch, "logs", "nfl4.log")
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
    try:
        with open(log_path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


# wait until the main prompt has been spoken (speech at volume 0 still takes its time)
for _ in range(300):
    if "Press a number from one to nine" in log_text() or proc.poll() is not None:
        break
    time.sleep(0.1)
text = log_text()
check("speaks the title", "by Josh Kennedy, inspired by Jim Kitchen" in text)
check("speaks the main prompt", "Press a number from one to nine" in text)
time.sleep(1.5)

# ----- play: 3 sounds, first panning mode, listen for 5 s, stop -----------------------------------
key(0x33)                                  # "3"
time.sleep(3.0)                            # panning menu speech
key(13)                                    # Enter: the first mode
for _ in range(100):
    if "Press the space bar to stop" in log_text():
        break
    time.sleep(0.1)
time.sleep(6.0)                            # sounds play (mixer is at 2 percent)
mark = time.perf_counter()
playing = [p for t, p in peaks if t > mark - 4.5]
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

key(32)                                    # space: stop playback
time.sleep(2.0)
key(27)                                    # Escape: exit (the original speaks its goodbye first, several seconds)
escaped = time.perf_counter()
closed_logged = None
while proc.poll() is None and time.perf_counter() - escaped < 40:
    if closed_logged is None and "Brain clone closed" in log_text():
        closed_logged = time.perf_counter()
    time.sleep(0.05)
if proc.poll() is None:
    proc.kill()
    code = None
else:
    code = proc.returncode
if closed_logged is None and "Brain clone closed" in log_text():
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
check("closes through its own exit path", "Brain clone closed" in text)
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
check("42 wavs beside the exe", count == 42, f"{count}")
print("ALL PASS" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
