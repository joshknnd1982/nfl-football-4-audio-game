"""Time from starting nfl4.exe to its window, its log's first line and the first speech command (playbook 7.4.3). Inspired by Jim Kitchen.
Usage: <python with pywin32> startup_time_check.py <nfl4.exe> [runs]   (speech volume 0, sound volume 0)"""
import datetime
import os
import re
import subprocess
import sys
import tempfile
import time

import win32gui
import win32process

exe = sys.argv[1]
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3


def window_for(pid):
    found = []

    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
            found.append(hwnd)

    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


for i in range(runs):
    data = tempfile.mkdtemp(prefix="brain_start_")
    os.makedirs(data, exist_ok=True)
    open(os.path.join(data, "settings.txt"), "w").write("# Brain settings, format 1\nspeech_volume = 0\nsound_volume = 0\n")
    env = dict(os.environ, NFL4_DATA_DIR=data, NFL4_DEBUG="1")
    wall0 = datetime.datetime.now()
    t0 = time.perf_counter()
    proc = subprocess.Popen([exe], env=env, cwd=os.path.dirname(exe))
    window_at = None
    while time.perf_counter() - t0 < 20:
        if window_at is None and window_for(proc.pid):
            window_at = time.perf_counter() - t0
        log = os.path.join(data, "logs", "nfl4.log")
        if os.path.exists(log) and "speak 'My Brain" in open(log, encoding="utf-8", errors="replace").read():
            break
        time.sleep(0.01)
    spoke_at = time.perf_counter() - t0
    text = open(os.path.join(data, "logs", "nfl4.log"), encoding="utf-8", errors="replace").read().splitlines()
    first = datetime.datetime.strptime(text[0][:23], "%Y-%m-%d %H:%M:%S,%f")
    starting = (first - wall0).total_seconds()
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    print(f"run {i + 1}: window {window_at if window_at is None else round(window_at, 2)} s, Python reached its first log line at {starting:.2f} s, first speech command at {spoke_at:.2f} s")
    time.sleep(1)
