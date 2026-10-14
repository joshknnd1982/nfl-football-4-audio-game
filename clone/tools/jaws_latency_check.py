"""JAWS arrowing latency at the speakers, by loopback capture. Inspired by Jim Kitchen's Brain.

The arrowing case: an item is being spoken, a key arrives, the item is cut and the next item is spoken. Records the
speakers (WASAPI loopback, package soundcard) and, for several ways of asking JAWS, times from the command to the
start of the LAST burst of sound (the new item, "One.", about 0.2 s long), and reports the cut: when the old item's
sound ended. Also times every call (a slow call on the game's key thread is lag too). JAWS SPEAKS, about 2 minutes.
Usage: <python with soundcard, numpy, pywin32> tools/jaws_latency_check.py <report file>
Needs a quiet PC and JAWS running.
"""
import os
import statistics
import sys
import threading
import time

import numpy as np
import soundcard as sc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
from nfl4.speech.jaws import JawsBackend  # noqa: E402

RATE, CHUNK, THRESHOLD = 48000, 240, 0.01
OLD = "Press a number from one to nine, or the escape key to exit."
NEW = "Select. No panning, original."
REPEATS = 3


def record(seconds, command, chunks, at):
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        t0 = time.perf_counter()
        threading.Timer(0.1, lambda: command("old")).start()
        threading.Timer(at, lambda: command("new", t0)).start()
        while time.perf_counter() - t0 < seconds:
            data = rec.record(numframes=CHUNK)
            chunks.append((time.perf_counter() - t0 - CHUNK / RATE, float(np.abs(data).max())))


def bursts(chunks, gap=0.03):
    loud = [t for t, level in chunks if level > THRESHOLD]
    out = []
    for t in loud:
        if out and t - out[-1][1] <= gap:
            out[-1][1] = t
        else:
            out.append([t, t])
    return out


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "jaws_latency_report.txt"
    jaws = JawsBackend()
    if not jaws.is_available():
        print("JAWS is not running")
        return 1
    call_times = {}

    def timed(key, fn):
        start = time.perf_counter()
        fn()
        call_times.setdefault(key, []).append((time.perf_counter() - start) * 1000)

    variants = {
        "idle, queue (no old speech)": lambda: timed("speak", lambda: jaws.speak(NEW)),
        "stop then queue (current game)": lambda: (timed("StopSpeech", jaws.stop), timed("speak", lambda: jaws.speak(NEW))),
        "queue only (no stop)": lambda: timed("speak", lambda: jaws.speak(NEW)),
        "flush only": lambda: timed("SayString flush", lambda: jaws._object().SayString(NEW, True)),
        "stop then flush": lambda: (timed("StopSpeech", jaws.stop), timed("SayString flush", lambda: jaws._object().SayString(NEW, True))),
    }
    trace = []
    lines = ["variant | command to start of new sound (ms): median, min, max | old sound ends after command (ms): median"]
    for name, variant in variants.items():
        starts, cuts = [], []
        for _ in range(REPEATS):
            chunks, marks = [], {}

            def command(which, t0=None, variant=variant, marks=marks, name=name):
                if which == "old":
                    if not name.startswith("idle"):
                        jaws.stop()
                        jaws.speak(OLD)
                else:
                    marks["t"] = time.perf_counter() - t0
                    variant()

            record(4.0, command, chunks, 0.9)
            tc = marks.get("t", 0.9)
            found = bursts(chunks)
            trace.append(f"{name}: command at {tc * 1000:.0f} ms, bursts " + ", ".join(f"{b[0] * 1000:.0f}-{b[1] * 1000:.0f}" for b in found))
            after = [b for b in found if b[1] >= tc]
            if not after:
                continue
            first_after = after[0]
            last = found[-1]
            cuts.append((first_after[1] - tc) * 1000 if first_after is not last else 0.0)
            starts.append((last[0] - tc) * 1000 if last[0] > tc else float("nan"))
            jaws.stop()
            time.sleep(1.0)
        if starts:
            lines.append(f"{name} | {statistics.median(starts):.0f}, {min(starts):.0f}, {max(starts):.0f} | "
                         f"{statistics.median(cuts):.0f}   (runs {len(starts)})")
        else:
            lines.append(f"{name} | no sound seen")
    lines.append("")
    lines.extend(trace)
    lines.append("")
    lines.append("call times (ms): " + "; ".join(f"{k}: median {statistics.median(v):.2f}, max {max(v):.2f}"
                                               for k, v in call_times.items()))
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
