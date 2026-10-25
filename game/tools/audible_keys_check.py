"""Arrowing quickly, heard at the speakers: key to audible speech in the real program. Inspired by Jim Kitchen.

Runs tools/key_latency_check.py (real window, game and SAPI 5 voice; F2 menu, 7 Down then 7 Up keys) while
recording the speakers by WASAPI loopback (package soundcard, run this with a Python that has it and numpy),
then prints for the last key of each run of keys how long it took for that item's speech to be heard, and
for each key when sound started. This makes real sound for about 15 seconds.
Usage: <python with soundcard> tools/audible_keys_check.py <brain 64-bit python> <scratch folder> <voice id or first> [key interval seconds] [speech volume]
"""
import os
import subprocess
import sys
import threading
import time

import numpy as np
import soundcard as sc

HERE = os.path.dirname(os.path.abspath(__file__))
BRAIN_PY, SCRATCH, VOICE = sys.argv[1], sys.argv[2], sys.argv[3]
INTERVAL = sys.argv[4] if len(sys.argv) > 4 else "0.12"
VOLUME = sys.argv[5] if len(sys.argv) > 5 else "40"
RATE, CHUNK, THRESHOLD = 44100, 220, 0.004
events = []
stop = threading.Event()


def record():
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        while not stop.is_set():
            data = rec.record(numframes=CHUNK)
            events.append((time.perf_counter() - CHUNK / RATE, float(np.abs(data).max())))


threading.Thread(target=record, daemon=True).start()
time.sleep(1.0)
times = os.path.join(SCRATCH, "times.txt")
os.makedirs(SCRATCH, exist_ok=True)
env = dict(os.environ, BRAIN_TIMES_FILE=times, BRAIN_SPEECH_VOLUME=VOLUME)
out = subprocess.run([BRAIN_PY, os.path.join(HERE, "key_latency_check.py"), SCRATCH, VOICE, INTERVAL], env=env,
                     capture_output=True, text=True, timeout=120)
time.sleep(1.0)
stop.set()
print(out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-500:])
lines = dict(l.split(" ", 1) for l in open(times).read().splitlines())
keys = [float(x) for x in lines["keys"].split()]
starts = [float(x) for x in lines["starts"].split()]
# sound segments: runs of loud chunks separated by at least 40 ms of quiet
loud = [t for t, p in events if p > THRESHOLD]
segments = []
for t in loud:
    if segments and t - segments[-1][1] < 0.04:
        segments[-1][1] = t
    else:
        segments.append([t, t])
print("keys: %d; sound segments heard: %d" % (len(keys), len(segments)))
t0 = keys[0]
print("key times (ms):", " ".join("%.0f" % ((k - t0) * 1000) for k in keys))
print("hand-overs (ms):", " ".join("%.0f" % ((k - t0) * 1000) for k in starts))
print("sound segments (start-end ms):", " ".join("%.0f-%.0f" % ((a - t0) * 1000, (b - t0) * 1000) for a, b in segments if a > t0 - 500))
for i, k in enumerate(keys):
    nxt = keys[i + 1] if i + 1 < len(keys) else k + 3
    heard = [s for s in segments if k <= s[0] < nxt]
    handed = [s for s in starts if k <= s < nxt]
    print("  key %2d at +%5.0f ms: handed to output %s, first sound heard %s" % (
        i + 1, (k - keys[0]) * 1000,
        "+%3.0f ms" % ((handed[0] - k) * 1000) if handed else "never (cut by the next key first)",
        "+%3.0f ms" % ((heard[0][0] - k) * 1000) if heard else "no"))
last = keys[6]       # the last Down of the first run
after = [s for s in segments if s[1] > last + 0.1 and s[0] < keys[7]]
last_up = keys[-1]
tail = [s for s in segments if s[1] > last_up]
print("last key of the run (Up #7): sound after it ends at +%s ms" % (("%.0f" % ((tail[-1][1] - last_up) * 1000)) if tail else "none"))
