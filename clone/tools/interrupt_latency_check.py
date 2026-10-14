"""Speech interrupted by new speech, heard at the speakers: how long until the new item is audible. Inspired by Jim Kitchen's Brain.

The arrowing case: an item is speaking, a key arrives, the item is cut and the next item is spoken.
Records the speakers by WASAPI loopback (package soundcard). For each way of playing speech (the
mixer player, winmm waveOut, SAPI's own output) it speaks a long text, 150 ms later issues stop plus
the item "Select. no panning", and finds when the sound ended. Start latency = end of sound minus the
command time minus the item's own audible length (measured from the engine's rendering of it). Also
the time for the old speech to be cut: the length of the sound that still plays after the stop when
the new item is silent. Makes real sound for about a minute at modest volume.
Usage: <python with soundcard, numpy, pygame-ce, pywin32> tools/interrupt_latency_check.py <voice id or first>
"""
import os
import sys
import threading
import time

import numpy as np
import soundcard as sc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
VOICE = None if sys.argv[1] == "first" else sys.argv[1]
RATE, CHUNK, THRESHOLD = 44100, 220, 0.004
events = []
stop_flag = threading.Event()


def record():
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    with mic.recorder(samplerate=RATE, channels=2, blocksize=CHUNK) as rec:
        while not stop_flag.is_set():
            data = rec.record(numframes=CHUNK)
            events.append((time.perf_counter() - CHUNK / RATE, float(np.abs(data).max())))


def wait_quiet(seconds=0.8):
    while True:
        now = time.perf_counter()
        recent = [p for t, p in events if t > now - seconds]
        if recent and max(recent) < THRESHOLD and now - events[0][0] > seconds:
            return
        time.sleep(0.05)


def last_sound_after(t0, quiet=0.7, timeout=8.0):
    """Time of the last loud chunk of the sound that follows t0 (ends after `quiet` seconds of silence)."""
    end = t0 + timeout
    while time.perf_counter() < end:
        loud = [t for t, p in list(events) if t > t0 and p > THRESHOLD]
        if loud and time.perf_counter() - (loud[-1] + CHUNK / RATE) > quiet:
            return loud[-1] + CHUNK / RATE
        time.sleep(0.02)
    return None


from nfl4.speech.sapi5 import SapiBackend, RENDER_RATE  # noqa: E402
from nfl4.speech.waveout import WaveOut  # noqa: E402
import pygame  # noqa: E402

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256, allowedchanges=0)
pygame.mixer.set_num_channels(11)
from nfl4.speech.mixerplayer import MixerSpeechPlayer  # noqa: E402

ITEM = "Select. no panning"
LONG = "This is a long item that is still speaking when the next key arrives, so it has to be cut at once."
threading.Thread(target=record, daemon=True).start()
time.sleep(1.0)

# the item's own audible length: render it once into memory and see where the last sound is
tmp = SapiBackend(voice_id=VOICE, volume=50, render=False)
tmp.start(20)
import win32com.client  # noqa: E402
stream = win32com.client.Dispatch("SAPI.SpMemoryStream")
fmt = win32com.client.Dispatch("SAPI.SpAudioFormat")
fmt.Type = 34
stream.Format = fmt
voice = win32com.client.Dispatch("SAPI.SpVoice")
if VOICE:
    token = win32com.client.Dispatch("SAPI.SpObjectToken")
    token.SetId(VOICE)
    voice.Voice = token
voice.Volume = 50
voice.AudioOutputStream = stream
voice.Speak(ITEM, 0)
pcm = np.frombuffer(bytes(stream.GetData()), dtype="<i2").astype(float) / 32768.0
loud = np.nonzero(np.abs(pcm) > THRESHOLD)[0]
ITEM_SECONDS = loud[-1] / RATE if len(loud) else 0.0
tmp.close()
print("item audible length %.0f ms" % (ITEM_SECONDS * 1000), flush=True)

for label, factory, render in (("mixer player", MixerSpeechPlayer, True), ("waveOut", lambda: WaveOut(RENDER_RATE), True),
                               ("SAPI direct", None, False)):
    kw = dict(player_factory=factory) if factory else {}
    b = SapiBackend(voice_id=VOICE, volume=50, render=render, **kw)
    st = b.start(20)
    time.sleep(0.5)
    starts = []
    for _ in range(6):
        wait_quiet()
        b.speak(LONG)
        time.sleep(0.15)
        t0 = time.perf_counter()
        b.stop()
        b.speak(ITEM)
        end = last_sound_after(t0)
        if end is not None:
            starts.append((end - t0 - ITEM_SECONDS) * 1000)
        b.stop()
    b.close()
    print("%-14s %-8s interrupted item audible after: median %4.0f ms, worst %4.0f ms (%d)" % (
        label, "(direct)" if not b.rendered else "", np.median(starts), max(starts), len(starts)) if starts else label + ": nothing heard", flush=True)
stop_flag.set()
