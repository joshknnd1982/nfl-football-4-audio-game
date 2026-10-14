"""Time the sound library: construction, first decode of every sound, rescan, cached picks. Inspired by Jim Kitchen.
Usage: python sound_load_timing.py <folder with the shipped wavs>   (playbook 7.4.3)"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
shipped = sys.argv[1]
player = tempfile.mkdtemp(prefix="brain_timing_")

t = time.perf_counter()
from nfl4.audio.library import SoundLibrary  # noqa: E402
print(f"import audio library: {(time.perf_counter() - t) * 1000:.0f} ms")

t = time.perf_counter()
lib = SoundLibrary(shipped, player)
print(f"SoundLibrary() incl. first refresh and sounds.txt: {(time.perf_counter() - t) * 1000:.1f} ms, pool {lib.pool_size()}")

times = []
for n in range(1, 43):
    t = time.perf_counter()
    lib.pick_number(n)
    times.append((time.perf_counter() - t) * 1000)
print(f"first pick (decode) of 42 sounds: total {sum(times):.0f} ms, mean {sum(times) / 42:.1f} ms, max {max(times):.1f} ms")

t = time.perf_counter()
lib.refresh()
print(f"refresh (every playback start): {(time.perf_counter() - t) * 1000:.1f} ms")
times = []
for n in range(1, 43):
    t = time.perf_counter()
    lib.pick_number(n)
    times.append((time.perf_counter() - t) * 1000)
print(f"picks after refresh (cached decode): total {sum(times):.1f} ms, max {max(times):.2f} ms")

t = time.perf_counter()
lib.check_all()
print(f"check_all (F3 check): {(time.perf_counter() - t) * 1000:.1f} ms")
sizes = sorted(os.path.getsize(os.path.join(shipped, f)) for f in os.listdir(shipped))
print(f"wav sizes: smallest {sizes[0]}, largest {sizes[-1]}, total {sum(sizes)} bytes")
