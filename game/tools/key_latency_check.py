"""Key to speech in the real program: arrowing through the speech settings menu. Inspired by Jim Kitchen.

Starts brain.app.main() (window, real SAPI 5 voice, real mixer) with the voice at volume 1 and the
sound volume at 0, opens F2, then presses Down every INTERVAL seconds (like a player arrowing
quickly) and Up the same way. For every key, the time from the moment the game reads the key to the
moment speech for it was handed to the audio output (the first hand-over after the key). Prints
median and worst. A key whose speech was cut by the next key before it started counts as unspoken.
Usage (from game/): python tools/key_latency_check.py <scratch folder> [voice id] [interval seconds]
"""
import os
import statistics
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
os.environ["NFL4_DATA_DIR"] = sys.argv[1]
os.makedirs(sys.argv[1], exist_ok=True)
VOICE = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "first" else ""
INTERVAL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
with open(os.path.join(sys.argv[1], "settings.txt"), "w", encoding="utf-8") as handle:
    handle.write("# Brain settings, format 1\nspeech_volume = " + os.environ.get("BRAIN_SPEECH_VOLUME", "1") + "\nsound_volume = 0\n")
    if VOICE:
        handle.write(f"speech_voice = {VOICE}\n")

import nfl4.app as app  # noqa: E402
from nfl4.audio import output as audio_output  # noqa: E402
from nfl4.audio.engine import SystemBeeper  # noqa: E402
from nfl4.game.keys import KeyInput  # noqa: E402
from nfl4.speech.sapi5 import SapiBackend  # noqa: E402

ESC, DOWN, UP, F2 = 27, 40, 38, 113
ENTER = 13
if len(sys.argv) > 4 and sys.argv[4] == "voices":       # arrowing through the voice list (1,789 voices on the owner's PC)
    SCRIPT = [F2, ENTER] + [DOWN] * 12 + [UP] * 6 + [ESC, ESC, ESC]
else:
    SCRIPT = [F2] + [DOWN] * 7 + [UP] * 7 + [ESC, ESC]
previous = [None]
key_times = []          # when the game read each Up or Down
starts = []             # when speech was handed to the output
backends = []
real_init = SapiBackend.__init__


def init(self, *a, **k):
    real_init(self, *a, **k)
    backends.append(self)


SapiBackend.__init__ = init


def watch():
    last = 0.0
    while True:
        if backends and backends[0].last_start_at != last:
            last = backends[0].last_start_at
            starts.append(time.perf_counter())
        time.sleep(0.0005)


threading.Thread(target=watch, daemon=True).start()


class Typist(KeyInput):
    def getkey(self, speech):
        self.clk()
        if self.code_text == "":
            time.sleep(1.0)
            self.post(SCRIPT.pop(0))
        super().getkey(speech)

    def read_key(self):
        if self._posted.empty() and SCRIPT:
            time.sleep(INTERVAL if previous[0] == SCRIPT[0] else 1.5)    # a pause before the first key of a run
            previous[0] = SCRIPT[0]
            self.post(SCRIPT.pop(0))
        code = super().read_key()
        if code in (UP, DOWN):
            key_times.append(time.perf_counter())
        return code


class SilentOutput(audio_output.PygameOutput):
    def __init__(self, buffer=256):
        super().__init__(buffer)
        self.volume = 0.0


SystemBeeper.beep = lambda self: True
app.KeyInput = Typist
audio_output.PygameOutput = SilentOutput
import nfl4.audio.engine as engine  # noqa: E402
engine.PygameOutput = SilentOutput
app.main()

if os.environ.get("BRAIN_TIMES_FILE"):      # perf_counter times for tools/audible_keys_check.py (same clock in every process)
    with open(os.environ["BRAIN_TIMES_FILE"], "w") as out:
        out.write("keys " + " ".join(f"{t:.4f}" for t in key_times) + chr(10))
        out.write("starts " + " ".join(f"{t:.4f}" for t in starts) + chr(10))
lags = []
for i, t in enumerate(key_times):
    nxt = key_times[i + 1] if i + 1 < len(key_times) else t + 5
    first = next((s for s in starts if s >= t), None)
    if first is not None and first < nxt:
        lags.append((first - t) * 1000)
voice = backends[0].voice_name if backends else "?"
print(f"{voice}: {len(lags)} of {len(key_times)} keys got speech before the next key; "
      f"key to speech start median {statistics.median(lags):.0f} ms, worst {max(lags):.0f} ms" if lags
      else f"{voice}: no key got speech")
