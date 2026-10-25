"""Start nfl4 (the source with a Python, or a built nfl4.exe) with a SAPI 5 voice that kills its process, twice, and check the crash guard
(playbook 7.4.5, S8.3). This is inspired by Jim Kitchen.

    <python> voice_crash_check.py <voice id> source <python of the bitness to test> [seconds]
    <python> voice_crash_check.py <voice id> exe <path to nfl4.exe> [seconds]

Start 1 has the voice saved for the announcer (speech volume 0): it must die with a native exit code (0xC0000409, 0xC0000005, 0xC0000374 ...),
or live (then the voice is not a crasher in this process and the check says so). A leftover `voice_trial.txt` must be there. Start 2 on the
same data folder must stay alive for `seconds`, have the voice in `crashed_voices.txt` and the notice in its log. Each process is ended by its
PID. It opens the game's window for a moment, like exe_smoke.py. Prints one verdict line per start.
"""
import os
import subprocess
import sys
import tempfile
import time

voice, kind, command = sys.argv[1], sys.argv[2], sys.argv[3]
seconds = float(sys.argv[4]) if len(sys.argv) > 4 else 15
SRC = r"C:\Users\joshk\OneDrive\dev\games\kitchensinc\nfl4\game\src"
data = tempfile.mkdtemp(prefix="nfl4_vc_")
roles = ("announcer", "own_quarterback", "opponent_quarterback", "own_punter", "opponent_punter")
with open(os.path.join(data, "settings.txt"), "w", encoding="utf-8") as handle:
    handle.write("# NFL Football 4 settings, format 1\nspeech_output = sapi\n")
    for role in roles:
        handle.write(f"volume_{role} = 0\n")
    handle.write(f"voice_announcer = {voice}\nsound_volume = -50\n")
env = dict(os.environ, NFL4_DATA_DIR=data)
if kind == "source":
    env["PYTHONPATH"] = SRC
    argv = [command, "-m", "nfl4"]
else:
    argv = [command]


def start():
    began = time.perf_counter()
    proc = subprocess.Popen(argv, env=env, cwd=data)
    while time.perf_counter() - began < seconds and proc.poll() is None:
        time.sleep(0.2)
    alive = proc.poll() is None
    code = proc.poll()
    if alive:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    return alive, code, round(time.perf_counter() - began, 1)


def show(code):
    return "none" if code is None else "%d (0x%X)" % (code, code & 0xFFFFFFFF)


alive1, code1, took1 = start()
trial = os.path.isfile(os.path.join(data, "voice_trial.txt"))
print("start 1: alive=%s after %s s, exit code %s, voice_trial.txt left=%s" % (alive1, took1, show(code1), trial))
alive2, code2, took2 = start()
crashed = ""
path = os.path.join(data, "crashed_voices.txt")
if os.path.isfile(path):
    crashed = open(path, encoding="utf-8", errors="replace").read()
logs = []
folder = os.path.join(data, "logs")
if os.path.isdir(folder):
    for name in sorted(os.listdir(folder)):
        if name.startswith("nfl4-2"):
            logs.append(open(os.path.join(folder, name), encoding="utf-8", errors="replace").read())
notice = any("crashed" in text.lower() and "last time" in text.lower() for text in logs[-1:])
print("start 2: alive=%s after %s s, exit code %s, crashed_voices lists the voice=%s, notice in the second log=%s" % (
    alive2, took2, show(code2), voice.lower() in crashed.lower(), notice))
print("data folder:", data)
verdict = "GUARD OK" if (not alive1 and trial and alive2 and voice.lower() in crashed.lower()) else (
    "NOT A CRASHER HERE" if alive1 and alive2 else "CHECK THE LINES ABOVE")
print(verdict)
sys.exit(0 if verdict != "CHECK THE LINES ABOVE" else 1)
