"""How long does a RUNNING JAWS really take to say the game's texts? Inspired by Jim Kitchen.

Speaks each text through the JAWS backend and records what Windows plays on the default speakers (WASAPI loopback,
package soundcard). The first loud sample is the start of speech, the last loud sample before 0.6 s of quiet is the end.
Compares the real time with the backend's estimate (0.3 s + 0.07 s per character). JAWS SPEAKS during this check.
Usage: <python with soundcard, numpy, pywin32> tools/jaws_duration_check.py <report file>
Needs a quiet PC (no other sound) and JAWS running.
"""
import os
import sys
import threading
import time

import numpy as np
import soundcard as sc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from nfl4.game import texts  # noqa: E402
from nfl4.speech.jaws import JawsBackend, estimated_seconds  # noqa: E402

RATE = 48000
CHUNK = 480
THRESHOLD = 0.01     # the idle loopback level is 0.0002; JAWS peaks near 1.0
QUIET_SECONDS = 0.6

SAMPLES = [texts.TITLE_SPOKEN, texts.NO_GAME_MENU, " Hike! ", "One.", "Speech settings.",
           "Voice: Microsoft David. Speech rate: 0, original.", texts.THANK_YOU]


def record(seconds, send, chunks):
    """Record the speakers for `seconds` in this thread; `send` is called from a timer at 0.8 s."""
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        t0 = time.perf_counter()
        threading.Timer(0.8, lambda: send(time.perf_counter() - t0)).start()
        while time.perf_counter() - t0 < seconds:
            data = rec.record(numframes=CHUNK)
            chunks.append((time.perf_counter() - t0, float(np.abs(data).max())))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "jaws_duration_report.txt"
    jaws = JawsBackend()
    if not jaws.is_available():
        print("JAWS is not running")
        return 1
    lines = ["text | chars | start after command (s) | audible length (s) | backend estimate (s)"]
    for text in SAMPLES:
        chunks, sent_at = [], []

        def send(stamp, text=text):
            jaws.speak(text)
            sent_at.append(stamp)

        record(0.8 + estimated_seconds(text) + 1.5, send, chunks)
        begin = sent_at[0] if sent_at else 0.8
        loud = [stamp for stamp, level in chunks if level > THRESHOLD and stamp >= begin - 0.05]
        if not loud:
            lines.append(f"{text.strip()[:40]!r} | {len(text.strip())} | no sound seen")
            jaws.stop()
            time.sleep(1.0)
            continue
        start = loud[0]
        end = start
        for stamp in loud:                    # the end: the last loud chunk before a quiet gap of QUIET_SECONDS
            if stamp - end > QUIET_SECONDS:
                break
            end = stamp
        lines.append(f"{text.strip()[:40]!r} | {len(text.strip())} | {start - begin:.2f} | {end - start:.2f} | "
                     f"{estimated_seconds(text):.2f}")
        jaws.stop()
        time.sleep(1.0)
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
