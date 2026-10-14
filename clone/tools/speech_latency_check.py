"""Speech latency on the real SAPI 5 voices: key to speech start, direct mode and rendered mode. Inspired by Jim Kitchen's Brain.

Plays nothing audible (voice volume 0). Types what a player does when arrowing quickly: stop speech,
say the next item, every 80 ms, then lets the last one finish. For each voice and mode prints the
time from the key (stop plus say) to the moment the speech was handed to the output, median and
worst, and how many of the 12 items were handed over. Direct mode hands the text to SAPI's own audio
output (that call is quick, the output then waits; DECISIONS 2026-10-13 explains); rendered mode hands
the finished audio to the waveOut player, so its numbers include making the speech.
Usage (from clone/): python tools/speech_latency_check.py [voice id ...]
"""
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from nfl4.speech.sapi5 import SapiBackend  # noqa: E402

ITEMS = ["Voice", "Speech rate", "Speech volume", "Speech pitch", "Speech output, SAPI 5 voice only",
         "Restore the speech settings", "Open the settings folder", "Voice", "Speech rate", "Speech volume",
         "Speech pitch", "Speech output, SAPI 5 voice only"]
VOICES = sys.argv[1:] or [None, r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\TokenEnums\DoubleTalk\Perfect Paul"]

for voice_id in VOICES:
    for render in (False, True):
        b = SapiBackend(voice_id=voice_id, volume=0, render=render)
        started = b.start(20)
        if not started.ok:
            print("start failed:", started.error)
            continue
        time.sleep(0.3)
        lags, handed = [], 0
        for text in ITEMS:
            before = b.last_start_at
            t0 = time.monotonic()
            b.stop()
            b.speak(text)
            deadline = t0 + 2.0
            while b.last_start_at == before and time.monotonic() < deadline:
                time.sleep(0.001)
            if b.last_start_at != before:
                handed += 1
                lags.append((b.last_start_at - t0) * 1000)
            time.sleep(max(0.0, 0.08 - (time.monotonic() - t0)))
        b.wait_until_done()
        b.close()
        mode = "rendered" if render else "direct  "
        if lags:
            print("%-14s %s handed %2d/12  key to start: median %5.0f ms  worst %5.0f ms" % (
                started.voice_name[:14], mode, handed, statistics.median(lags), max(lags)))
        else:
            print(started.voice_name, mode, "nothing handed over")
