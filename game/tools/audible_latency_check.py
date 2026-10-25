"""Audible speech latency: command to sound leaving the speakers, by loopback capture. Inspired by Jim Kitchen.

Records what Windows plays on the default speakers (WASAPI loopback, package soundcard) and measures,
for each way of speaking, the time from the speak command to the first audible sound, and from a
stop command to the end of the sound. It makes real sound for about a minute (short words, modest
volume). Ways measured: the game's SAPI 5 backend rendered (waveOut), the game's SAPI 5 backend
direct (SAPI's own output), and NVDA through its controller client when NVDA runs (its own voice).
Usage: <python with soundcard and numpy> tools/audible_latency_check.py <voice id or "first"> [path to the brain src folder]
The capture runs in this Python; the backends are imported from the brain src folder (64-bit Python only).
"""
import os
import sys
import threading
import time

import numpy as np
import soundcard as sc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(HERE), "src"))
VOICE = None if sys.argv[1] == "first" else sys.argv[1]
RATE = 44100
CHUNK = 220                      # 5 ms
THRESHOLD = 0.004

events = []                      # (time of chunk end, peak)
stop_flag = threading.Event()


def record():
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        while not stop_flag.is_set():
            data = rec.record(numframes=CHUNK)
            events.append((time.perf_counter(), float(np.abs(data).max())))


def wait_quiet(seconds=0.6):
    while True:
        now = time.perf_counter()
        recent = [p for t, p in events if t > now - seconds]
        if now - events[0][0] > seconds and recent and max(recent) < THRESHOLD:
            return
        time.sleep(0.05)


def onset_after(t0, timeout=3.0):
    end = t0 + timeout
    while time.perf_counter() < end:
        for t, p in list(events):
            if t > t0 and p > THRESHOLD:
                return (t - t0 - CHUNK / RATE) * 1000
        time.sleep(0.002)
    return None


def silence_after(t0, timeout=3.0):
    """Time from t0 until 60 ms of silence."""
    end = t0 + timeout
    while time.perf_counter() < end:
        snap = [(t, p) for t, p in list(events) if t > t0]
        run = 0
        for t, p in snap:
            run = run + 1 if p < THRESHOLD else 0
            if run >= 12:
                return (t - t0 - 0.06) * 1000
        time.sleep(0.005)
    return None


def trial(label, speak, stop, texts):
    onsets, cuts = [], []
    for text in texts:
        wait_quiet()
        t0 = time.perf_counter()
        speak(text)
        o = onset_after(t0)
        if o is not None:
            onsets.append(o)
        time.sleep(0.25)
        t1 = time.perf_counter()
        stop()
        c = silence_after(t1)
        if c is not None:
            cuts.append(c)
    f = lambda xs: "median %4.0f ms, worst %4.0f ms (%d)" % (np.median(xs), max(xs), len(xs)) if xs else "none heard"
    print("%-34s start: %s | stop: %s" % (label, f(onsets), f(cuts)), flush=True)


threading.Thread(target=record, daemon=True).start()
time.sleep(1.0)
TEXTS = ["Speech rate, forty percent.", "Speech volume, ninety.", "Restore the speech settings.", "Voice, Fred.",
         "Speech pitch, zero.", "Open the settings folder.", "Select. no panning", "Help."]

from nfl4.speech.sapi5 import SapiBackend  # noqa: E402
from nfl4.speech.nvda import NvdaBackend  # noqa: E402

for render in (True, False):
    b = SapiBackend(voice_id=VOICE, volume=50, render=render)
    st = b.start(20)
    time.sleep(0.5)
    mode = "rendered" if b.rendered else "direct"
    trial(f"game SAPI 5 {st.voice_name[:12]} ({mode})", b.speak, b.stop, TEXTS)
    b.close()
nv = NvdaBackend()
if nv.is_available():
    trial("NVDA (its own voice)", nv.speak, nv.stop, TEXTS)
stop_flag.set()
