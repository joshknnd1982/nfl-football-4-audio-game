"""Silence between the end of the spoken prompt and the first sound, as heard at the speakers. Inspired by Jim Kitchen.

Starts the game (a built nfl4.exe, or python.exe to run from source), chooses 3 sounds and the first panning mode, and
records the speakers (WASAPI loopback, package soundcard) while the prompt " Press the space bar to stop." is spoken
AUDIBLY (speech volume 100) and the sounds are silent (sound volume 0, but still started: the debug log line
"play slot" gives their start time). Gap = first "play slot" log time minus the moment the prompt's sound ended at
the speakers. Any gap over about 150 ms is a bug (playbook 7.4.3). Speech output: sapi, nvda or jaws.
Usage: <python with soundcard, numpy, pywin32> prompt_gap_check.py <nfl4.exe or python.exe> <scratch folder> [runs] [output] [extra settings]
Needs a quiet PC. The prompt is spoken aloud.
"""
import datetime
import os
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
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
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


def wait_quiet(seconds, limit=40.0):
    """Wait until the speakers have been quiet for `seconds` (the game is silent and waiting for a key)."""
    end = time.perf_counter() + limit
    while time.perf_counter() < end:
        time.sleep(0.1)
        now = time.perf_counter()
        recent = [level for t, level in chunks if t > now - seconds]
        if recent and chunks[-1][0] > now - 0.3 and max(recent) < THRESHOLD and chunks[0][0] < now - seconds:
            return


threading.Thread(target=capture, daemon=True).start()
time.sleep(1.5)
gaps = []
for run in range(RUNS):
    data = os.path.join(scratch, f"run{run}")
    os.makedirs(data, exist_ok=True)
    open(os.path.join(data, "settings.txt"), "w").write(
        f"# Brain settings, format 1\nspeech_volume = 100\nsound_volume = 0\nspeech_output = {OUTPUT}\n" + EXTRA)
    log = os.path.join(data, "logs", "nfl4.log")
    env = dict(os.environ, NFL4_DATA_DIR=data, NFL4_DEBUG="1", PYTHONPATH=SRC)
    command = [exe, "-m", "brain"] if exe.lower().endswith("python.exe") else [exe]
    proc = subprocess.Popen(command, env=env, cwd=data)

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

    wait_quiet(2.5)                                  # the title and the main prompt are spoken first
    key(0x33)                                        # 3 sounds
    time.sleep(0.5)
    wait_quiet(2.5)                                  # "3", "Select", "no panning" are spoken
    wall0, perf0 = datetime.datetime.now(), time.perf_counter()      # clock alignment between the log and the capture
    time.sleep(0.3)
    key(13)                                          # Enter: start
    time.sleep(10.0)
    lines = text().splitlines()
    asked = next((stamp(l) for l in lines if "Press the space bar to stop" in l and ("speak" in l)), None)
    plays = [stamp(l) for l in lines if "play slot" in l and asked and stamp(l) >= asked]
    if not asked or not plays:
        print(f"run {run + 1}: no data (prompt spoken {asked is not None}, plays {len(plays)})")
    else:
        def to_wall(perf):
            return wall0 + datetime.timedelta(seconds=perf - perf0)

        loud = [to_wall(t) for t, level in chunks if level > THRESHOLD and to_wall(t) >= asked]
        end = loud[0] if loud else None
        for t in loud:                               # the end of the prompt's sound: a gap over 0.35 s ends the burst
            if (t - end).total_seconds() > 0.35:
                break
            end = t
        done = next((stamp(l) for l in lines if "speech done" in l and stamp(l) > asked), None)
        gap = (plays[0] - end).total_seconds() * 1000 if end else None
        if gap is not None:
            gaps.append(gap)
        print(f"run {run + 1}: prompt commanded at 0, first sound sent {(plays[0] - asked).total_seconds():.2f} s; "
              + (f"speech heard from {(loud[0] - asked).total_seconds():.2f} to {(end - asked).total_seconds():.2f} s; "
                 f"silence between the end of the speech and the first sound {gap:.0f} ms" if loud else "no speech heard")
              + (f"; engine said done at {(done - asked).total_seconds():.2f} s" if done else ""))
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    time.sleep(1.5)
stop.set()
if gaps:
    print("median silence between the end of the prompt and the first sound: %.0f ms (min %.0f, max %.0f)" %
          (statistics.median(gaps), min(gaps), max(gaps)))
