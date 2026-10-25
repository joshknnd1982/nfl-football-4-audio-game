"""Time the sound library and the renders: construction, first decode of all 27 sounds (what the start does), rescan,
cached picks, and the first render of each sound at its own rate. This is inspired by Jim Kitchen.
Usage: python sound_load_timing.py [<folder with the shipped wavs>]   (playbook 7.4.3; default: the game's assets)"""
import os
import shutil
import sys
import tempfile
import time

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "src"))
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
shipped = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CODE, "assets", "sounds")
player = tempfile.mkdtemp(prefix="nfl4_timing_")

try:
    t = time.perf_counter()
    from nfl4.audio.ids import SOUND_IDS  # noqa: E402
    from nfl4.audio.library import SoundLibrary  # noqa: E402
    from nfl4.audio.render import render_stereo  # noqa: E402
    print(f"import audio library: {(time.perf_counter() - t) * 1000:.0f} ms")

    t = time.perf_counter()
    lib = SoundLibrary(shipped, player)
    print(f"SoundLibrary() incl. first refresh and sounds.txt: {(time.perf_counter() - t) * 1000:.1f} ms")

    t = time.perf_counter()
    problems = lib.check_all()
    print(f"check_all at start (first decode of all {len(SOUND_IDS)} sounds): {(time.perf_counter() - t) * 1000:.0f} ms,"
          f" problems {len(problems)}")

    t = time.perf_counter()
    lib.refresh()
    lib.check_all()
    print(f"refresh and check_all again (decodes cached): {(time.perf_counter() - t) * 1000:.1f} ms")

    times = []
    for sound_id in SOUND_IDS:
        pick = lib.pick(sound_id)
        t = time.perf_counter()
        render_stereo(pick.sound, pick.sound.rate, 0, 1.0)
        times.append(((time.perf_counter() - t) * 1000, sound_id))
    print(f"first render of each sound at its own rate: total {sum(ms for ms, _ in times):.0f} ms, "
          f"max {max(times)[0]:.1f} ms ({max(times)[1]})")
    sizes = sorted(os.path.getsize(os.path.join(shipped, f)) for f in os.listdir(shipped))
    print(f"wav sizes: smallest {sizes[0]}, largest {sizes[-1]}, total {sum(sizes)} bytes")
finally:
    shutil.rmtree(player, ignore_errors=True)
