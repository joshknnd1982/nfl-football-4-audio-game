"""Start a BUILT nfl4.exe with a given SAPI 5 voice saved in its settings and report whether it survives. Inspired by Jim Kitchen.
Usage: <python> exe_voice_check.py <nfl4.exe> [seconds] [voice id]   (default voice: SmoothTalker; speech volume 0)
A native crash of the voice shows as exit code 3221226505 (0xC0000409) or 3221225477 (0xC0000005) within a second."""
import os
import subprocess
import sys
import tempfile
import time

exe = sys.argv[1]
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 15
data = tempfile.mkdtemp(prefix="brain_st_")
voice = sys.argv[3] if len(sys.argv) > 3 else r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\TokenEnums\SmoothTalker\SmoothTalker"
open(os.path.join(data, "settings.txt"), "w").write(
    f"# Brain settings, format 1\nspeech_voice = {voice}\nspeech_volume = 0\nsound_volume = 0\n")
env = dict(os.environ, NFL4_DATA_DIR=data, NFL4_DEBUG="1")
t0 = time.perf_counter()
proc = subprocess.Popen([exe], env=env, cwd=data)
while time.perf_counter() - t0 < seconds and proc.poll() is None:
    time.sleep(0.2)
alive = proc.poll() is None
print("alive after", round(time.perf_counter() - t0, 1), "s:", alive, "| exit code", proc.poll())
if alive:
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logfiles  # noqa: E402  (one log file per launch since rule 0.15)
print(logfiles.launch_text(data)[-2500:] or "no log")
settings = open(os.path.join(data, "settings.txt"), encoding="utf-8").read()
print("settings voice line:", [l for l in settings.splitlines() if l.startswith("speech_voice")])
