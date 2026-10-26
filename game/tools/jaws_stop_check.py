"""Which call really stops a RUNNING JAWS? Measured at the speakers (WASAPI loopback). This is inspired by Jim Kitchen.

The owner's JAWS check of 2026-10-26 played the long test sentence to its end ("banana"), although the game's stop (a flushed space,
SayString(" ", True)) cut it in about 80 ms on 2026-10-13. For each way of stopping, JAWS is given a long sentence (queued), and 0.8 s
later the stop is called; the recording shows when the sound really ended after the call. A run with no stop gives the natural end.
JAWS SPEAKS during this check, about 2 minutes. Keep the PC quiet and press no key.
Usage: <python with soundcard, numpy, pywin32> tools/jaws_stop_check.py <report file>
"""
import os
import statistics
import subprocess
import sys
import threading
import time

import numpy as np
import soundcard as sc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from nfl4.speech.jaws import JawsBackend, _window_open  # noqa: E402

RATE, CHUNK, THRESHOLD = 48000, 240, 0.01
LONG = ("This long sentence should be cut off by stop speech, so you should hear only the first words "
        "of it and never the end of it, which is the word banana.")
AT, SECONDS, REPEATS = 0.8, 7.0, 2


def record(seconds, start, stop_at, stop, chunks, marks):
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        t0 = time.perf_counter()
        threading.Timer(0.1, start).start()

        def call():
            marks["t"] = time.perf_counter() - t0
            begin = time.perf_counter()
            try:
                marks["result"] = repr(stop())
            except Exception as exc:          # a call JAWS does not know is a finding, not a crash
                marks["result"] = "error: %s" % exc
            marks["ms"] = (time.perf_counter() - begin) * 1000
        threading.Timer(stop_at, call).start()
        while time.perf_counter() - t0 < seconds:
            data = rec.record(numframes=CHUNK)
            chunks.append((time.perf_counter() - t0 - CHUNK / RATE, float(np.abs(data).max())))


def sound_end(chunks, after):
    """The last loud moment, and the end of the loud stretch that runs through `after` (the stop's call)."""
    loud = [t for t, level in chunks if level > THRESHOLD]
    if not loud:
        return None, None
    stretch_end = None
    for t in loud:
        if t >= after - 0.05:
            if stretch_end is None or t - stretch_end <= 0.15:
                stretch_end = t
            else:
                break
    return loud[-1], stretch_end


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "jaws_stop_report.txt"
    jaws = JawsBackend()
    if not (_window_open() and jaws.is_available()):
        print("JAWS is not running (no JFWUI2 window): start JAWS, wait until it speaks, then run this again")
        return 1
    obj = jaws._object()
    nvda = "nvda.exe" in subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    ways = {
        "no stop (the natural end)": lambda: None,
        "SayString(' ', True), the game's stop": lambda: obj.SayString(" ", True),
        "SayString('', True)": lambda: obj.SayString("", True),
        "SayString('One.', True)": lambda: obj.SayString("One.", True),
        "StopSpeech()": lambda: obj.StopSpeech(),
        "RunFunction('StopSpeech')": lambda: obj.RunFunction("StopSpeech"),
        "StopSpeech() then SayString(' ', True)": lambda: (obj.StopSpeech(), obj.SayString(" ", True)),
    }
    lines = ["JAWS stop check, %d-bit Python; NVDA running: %s" % (64 if sys.maxsize > 2 ** 32 else 32, nvda),
             "way | sound after the call (ms): each run | the call's result and time"]
    natural = []
    for name, stop in ways.items():
        cuts, notes = [], []
        for _ in range(REPEATS):
            chunks, marks = [], {}
            record(SECONDS, lambda: obj.SayString(LONG, False), AT, stop, chunks, marks)
            last, stretch = sound_end(chunks, marks.get("t", AT))
            if last is None:
                cuts.append(float("nan"))
            else:
                cuts.append((stretch - marks["t"]) * 1000 if stretch is not None else 0.0)
            notes.append("%s in %.1f ms" % (marks.get("result"), marks.get("ms", -1)))
            obj.SayString(" ", True)
            time.sleep(1.5)
        if name.startswith("no stop"):
            natural = cuts
        lines.append("%s | %s | %s" % (name, ", ".join("%.0f" % c for c in cuts), "; ".join(notes)))
    if natural:
        n = statistics.median(natural)
        lines += ["", "A way stops JAWS when its sound ends well before the natural end (%.0f ms after the call): about 150 ms or less is a cut." % n]
    obj.SayString("The stop check is finished.", False)
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
