"""From the Enter key that starts playback to the first sound at the speakers, in a BUILT nfl4.exe. Inspired by Jim Kitchen's Brain.

Splits the wait into: key to the speech command, the spoken prompt itself (" Press the space bar to stop.", which the
original also waited for), and what the game adds after the speech ends (rescan, decode, render, start) up to the
first sound heard on the speakers (WASAPI loopback, package soundcard). Speech runs at volume 0 (silent but takes its
real time); sounds are faint (volume 20). Needs a quiet PC.
Usage: <python with soundcard, numpy, pywin32> playback_start_latency.py <nfl4.exe> <scratch folder> [runs] [speech output] ["setting = value;setting = value"]
"""
import datetime
import os
import re
import statistics
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

exe, scratch = sys.argv[1], sys.argv[2]
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
OUTPUT = sys.argv[4] if len(sys.argv) > 4 else "sapi"
EXTRA = sys.argv[5].replace(";", "\n") + "\n" if len(sys.argv) > 5 else ""
RATE, CHUNK, THRESHOLD = 48000, 240, 0.004
chunks = []
stop = threading.Event()


def capture():
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        while not stop.is_set():
            data = rec.record(numframes=CHUNK)
            chunks.append((time.perf_counter() - CHUNK / RATE, float(np.abs(data).max())))


def stamp(line):
    return datetime.datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f")


threading.Thread(target=capture, daemon=True).start()
time.sleep(1.5)
rows = []
for run in range(RUNS):
    data = os.path.join(scratch, f"run{run}")
    os.makedirs(data, exist_ok=True)
    open(os.path.join(data, "settings.txt"), "w").write(
        f"# Brain settings, format 1\nspeech_volume = 0\nsound_volume = 20\nspeech_output = {OUTPUT}\n" + EXTRA)
    log = os.path.join(data, "logs", "nfl4.log")
    proc = subprocess.Popen([exe], env=dict(os.environ, NFL4_DATA_DIR=data, NFL4_DEBUG="1"), cwd=data)

    def window():
        found = []
        win32gui.EnumWindows(lambda h, _: found.append(h) if win32gui.IsWindowVisible(h)
                             and win32process.GetWindowThreadProcessId(h)[1] == proc.pid else None, None)
        return found[0] if found else 0

    hwnd = 0
    while not hwnd:
        hwnd = window()
        time.sleep(0.05)

    def text():
        try:
            return open(log, encoding="utf-8", errors="replace").read()
        except OSError:
            return ""

    def key(vk):
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

    for _ in range(300):
        if "Press a number from one to nine" in text():
            break
        time.sleep(0.1)
    time.sleep(2.5)
    key(0x33)                                       # 3 sounds
    for _ in range(300):
        if "no panning" in text():
            break
        time.sleep(0.1)
    time.sleep(3.0)
    wall, mark = datetime.datetime.now(), time.perf_counter()
    key(13)                                         # Enter: first panning mode starts playback
    time.sleep(8.0)
    lines = text().splitlines()
    speak = next((stamp(l) for l in lines if "speak ' Press the space bar" in l and stamp(l) >= wall), None)
    done = next((stamp(l) for l in lines if "speech done" in l and speak and stamp(l) > speak), None)
    heard = [t for t, level in chunks if t > mark and level > THRESHOLD]
    first = heard[0] if heard else None
    if speak and done and first:
        enter_to_speak = (speak - wall).total_seconds() * 1000
        speech = (done - speak).total_seconds() * 1000
        after = (first - mark) * 1000 - enter_to_speak - speech
        rows.append((enter_to_speak, speech, after, (first - mark) * 1000))
        print(f"run {run + 1}: key to speech command {enter_to_speak:.0f} ms, prompt {speech:.0f} ms, "
              f"game adds {after:.0f} ms after the prompt, Enter to first sound {(first - mark) * 1000:.0f} ms")
    else:
        print(f"run {run + 1}: incomplete", speak, done, first)
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    time.sleep(1.5)
stop.set()
if rows:
    print("median: key to speech %.0f ms, prompt %.0f ms, game adds %.0f ms, Enter to first sound %.0f ms" %
          tuple(statistics.median(r[i] for r in rows) for i in range(4)))
