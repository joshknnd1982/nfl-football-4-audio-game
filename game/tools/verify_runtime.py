"""Does the runtime of the game work in THIS Python? Run once with the 64-bit and once with the 32-bit environment
(nfl4-64, nfl4-32). Inspired by Jim Kitchen's NFL football version 4.

Written in nfl4 P6 S6.2 as work\\verify_runtime_s62.py and copied here in S7.1 in place of the kit's Brain-specific
check (fixesforgames B-X16). It finds the package and its window class under the src folder by itself, so the same file
serves any game whose wavs are named foot<N>.wav; another game changes check_wavs and the pitch and pan checks.
Defaults: the wav folder is the game's original folder, the src folder is this game's own (tools\\..\\src).

Silent by design: the mixer is SDL's dummy driver (logic) and, in a child process, the real device with every
channel at volume 0 (timing, B-A2); speech is SAPI at Volume 0 on the default device, plus five voices rendered
into memory streams (nothing audible); no window is shown; NVDA and JAWS are only asked whether they exist.
No keyboard is used (B-X14).

What this game needs from the sound side (GAME_SPEC 5.5, WAV_EVENT_MAP): plain playback of 26 wavs (8-bit and 16-bit,
mono and stereo, 8363 to 44100 Hz) with volume (hundredths of dB, amplitude 10 ** (v / 2000)), pan (the far channel
attenuated) and frequency (original + 1, playcel original + 100 * k with k from -20 to 19, not below 8000 Hz).

Usage: python verify_runtime_s62.py [all|real] <wav folder> <kit src folder> <out file>
Prints one line per check, writes the same lines to <out file>, exits 1 when any check failed.
"""
import ctypes
import glob
import importlib.util
import os
import platform
import struct
import subprocess
import sys
import time
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
MODE = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("all", "real") else "all"
WAV_DIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "..", "original")
KIT_SRC = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "src")
OUT = sys.argv[4] if len(sys.argv) > 4 else None

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
if MODE == "all":
    os.environ["SDL_AUDIODRIVER"] = "dummy"  # logic only; the real device runs in the child process

MIX = 44100
BITS = struct.calcsize("P") * 8
results = []


def check(name, func):
    try:
        results.append((name, True, func()))
    except Exception as exc:  # report every failure, keep checking the rest
        results.append((name, False, f"{type(exc).__name__}: {exc}"))


def load_wav(path):
    """(16-bit PCM bytes, rate, channels) of an 8- or 16-bit PCM wav (8-bit is unsigned)."""
    import audioop
    with wave.open(path, "rb") as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        data = w.readframes(n)
    if width == 1:
        data = audioop.lin2lin(audioop.bias(data, 1, 128), 1, 2)
    elif width != 2:
        raise ValueError(f"sample width {width} not handled")
    return data, rate, ch


def render(data, rate, ch, play_rate, left, right):
    """16-bit stereo at 44100 Hz: the sound resampled as if its buffer played at play_rate, then panned."""
    import audioop
    frame = ch * 2
    want = int((len(data) // frame) * MIX / play_rate) * ch * 2
    out, _ = audioop.ratecv(data + data[-frame:] * 2, 2, ch, play_rate, MIX, None, 1, 0)
    out = out[:want] + b"\0" * max(0, want - len(out))
    if ch == 1:
        return audioop.tostereo(out, 2, left, right)
    lch, rch = audioop.tomono(out, 2, 1, 0), audioop.tomono(out, 2, 0, 1)
    return audioop.add(audioop.tostereo(lch, 2, left, 0), audioop.tostereo(rch, 2, 0, right), 2)


def gains(volume, pan):
    """(left, right) amplitude for DirectSound volume and pan in hundredths of dB (the far side attenuated)."""
    base = 10 ** (volume / 2000)
    return base * (10 ** (-pan / 2000) if pan > 0 else 1.0), base * (10 ** (pan / 2000) if pan < 0 else 1.0)


def check_python():
    import sys as _s
    venv = _s.prefix != _s.base_prefix
    return f"Python {platform.python_version()} {BITS}-bit, venv {venv}, {_s.executable}"


def check_imports():
    names = {}
    for mod in ("pygame", "audioop", "pythoncom", "win32com.client", "win32api", "pefile", "PyInstaller", "pytest"):
        m = __import__(mod, fromlist=["x"])
        names[mod] = getattr(m, "__version__", getattr(m, "ver", None)) or "ok"
    import audioop
    import pygame
    numpy_found = importlib.util.find_spec("numpy") is not None
    if numpy_found:
        raise RuntimeError("numpy is installed in this environment (rule 0.11: not for this game)")
    return (f"pygame-ce {pygame.version.ver} (SDL {'.'.join(map(str, pygame.get_sdl_version()))}), "
            f"audioop from {os.path.basename(os.path.dirname(audioop.__file__))}, pefile {names['pefile']}, "
            f"PyInstaller {names['PyInstaller']}, pytest {names['pytest']}, numpy absent")


def check_wavs():
    paths = sorted(glob.glob(os.path.join(WAV_DIR, "foot*.wav")), key=lambda p: int(os.path.basename(p)[4:-4]))
    if len(paths) != 26:
        raise RuntimeError(f"{len(paths)} foot wavs found in {WAV_DIR}, expected 26")
    import audioop
    import pygame
    pygame.mixer.pre_init(MIX, -16, 2, 256)
    pygame.mixer.init()
    worst = (0.0, "")
    total = 0.0
    frames_out = 0
    formats = set()
    for p in paths:
        data, rate, ch = load_wav(p)
        formats.add((ch, rate))
        t = time.perf_counter()
        buf = render(data, rate, ch, rate + 1, *gains(-1200, 0))
        pygame.mixer.Sound(buffer=buf)
        took = (time.perf_counter() - t) * 1000
        total += took
        frames_out += len(buf) // 4
        if took > worst[0]:
            worst = (took, os.path.basename(p))
        if audioop.max(buf, 2) > 32767 or len(buf) % 4:
            raise RuntimeError(f"{p}: bad buffer")
    pygame.mixer.quit()
    return (f"all 26 wavs ({len(formats)} formats) decoded and rendered at +1 Hz, {frames_out} output frames, "
            f"total {total:.0f} ms, worst {worst[0]:.0f} ms ({worst[1]})")


def check_pitch_and_pan():
    import audioop
    # playcel pitch: original + 100 * k, k -20 .. 19, never below 8000 Hz (foot15 to foot24)
    lens = {}
    for n in (15, 17, 19, 21, 24):
        data, rate, ch = load_wav(os.path.join(WAV_DIR, f"foot{n}.wav"))
        for k in (-20, 19):
            fr = max(8000, rate + 100 * k)
            buf = render(data, rate, ch, fr, 1.0, 1.0)
            expected = int((len(data) // (ch * 2)) * MIX / fr)
            if len(buf) // 4 != expected:
                raise RuntimeError(f"foot{n} at {fr} Hz: {len(buf) // 4} frames, expected {expected}")
            lens[(n, k)] = len(buf) // 4
    # pan: DirectSound pan +1400 attenuates the LEFT by 1400 hundredths of dB, -1500 the right
    data, rate, ch = load_wav(os.path.join(WAV_DIR, "foot13.wav"))
    ref = audioop.max(render(data, rate, ch, rate + 1, 1.0, 1.0), 2)  # the unpanned peak after resampling
    for pan in (1400, -1500, 0):
        l, r = gains(-250, pan)
        buf = render(data, rate, ch, rate + 1, l, r)
        peak_l = audioop.max(audioop.tomono(buf, 2, 1, 0), 2)
        peak_r = audioop.max(audioop.tomono(buf, 2, 0, 1), 2)
        if abs(peak_l - ref * l) > 3 or abs(peak_r - ref * r) > 3:
            raise RuntimeError(f"pan {pan}: peaks {peak_l}/{peak_r}, expected {ref * l:.0f}/{ref * r:.0f}")
    # a stereo source keeps its two channels apart (foot1: 16-bit stereo, 22050 Hz)
    data, rate, ch = load_wav(os.path.join(WAV_DIR, "foot1.wav"))
    buf = render(data, rate, ch, rate + 1, 0.5, 1.0)
    if audioop.max(audioop.tomono(buf, 2, 1, 0), 2) > audioop.max(audioop.tomono(buf, 2, 0, 1), 2):
        raise RuntimeError("stereo source: left not quieter than right at left gain 0.5")
    return "pitch -2000/+1900 Hz lengths exact, pan +1400/-1500/0 within 3 of 32768, stereo source keeps its channels"


def check_mixer_dummy():
    import pygame
    pygame.mixer.pre_init(MIX, -16, 2, 256)
    pygame.mixer.init()
    pygame.mixer.set_num_channels(8)
    driver = pygame.mixer.get_init()
    data, rate, ch = load_wav(os.path.join(WAV_DIR, "foot15.wav"))
    snd = pygame.mixer.Sound(buffer=render(data, rate, ch, rate + 1, 1.0, 1.0))
    chans = [pygame.mixer.Channel(i) for i in range(7)]  # the original has seven buffer slots (G-A1)
    for c in chans:
        c.set_volume(0.0)
        c.play(snd)
    busy = sum(c.get_busy() for c in chans)
    deadline = time.time() + 2.0
    while any(c.get_busy() for c in chans) and time.time() < deadline:
        time.sleep(0.005)
    idle = not any(c.get_busy() for c in chans)
    # a looping sound stays busy and stop() ends it (the crowd beds)
    c0 = chans[0]
    c0.play(snd, loops=-1)
    time.sleep(0.4)
    still = c0.get_busy()
    c0.stop()
    stopped = not c0.get_busy()
    pygame.mixer.quit()
    if busy != 7 or not idle or not still or not stopped:
        raise RuntimeError(f"busy {busy} of 7, idle after end {idle}, loop busy {still}, stopped {stopped}")
    return f"dummy driver {driver}: 7 of 7 slots busy, all idle at the end, loop with stop works"


def check_mixer_real():
    env = {k: v for k, v in os.environ.items() if k != "SDL_AUDIODRIVER"}  # the child uses the real device
    out = subprocess.run([sys.executable, os.path.abspath(__file__), "real", WAV_DIR, KIT_SRC],
                         capture_output=True, text=True, timeout=120, env=env)
    line = [x for x in out.stdout.splitlines() if x.startswith(("PASS", "FAIL"))]
    if not line or line[-1].startswith("FAIL"):
        raise RuntimeError((line[-1] if line else out.stdout + out.stderr)[:400])
    return line[-1][5:].split(": ", 1)[1]


def real_device_run():
    import pygame
    pygame.mixer.pre_init(MIX, -16, 2, 256)
    pygame.mixer.init()
    got = pygame.mixer.get_init()
    parts = []
    for n, offset in ((16, -2000), (15, 1900), (22, 1)):
        data, rate, ch = load_wav(os.path.join(WAV_DIR, f"foot{n}.wav"))
        fr = max(8000, rate + offset)
        snd = pygame.mixer.Sound(buffer=render(data, rate, ch, fr, 1.0, 1.0))
        c = pygame.mixer.Channel(0)
        c.set_volume(0.0)  # silent test
        start = time.perf_counter()
        c.play(snd)
        while c.get_busy():
            time.sleep(0.001)
        busy = (time.perf_counter() - start) * 1000
        expected = snd.get_length() * 1000
        if abs(busy - expected) > 120:
            raise RuntimeError(f"foot{n}@{fr}Hz expected {expected:.0f} ms, busy {busy:.0f} ms")
        parts.append(f"foot{n}@{fr}Hz expected {expected:.0f} ms, busy {busy:.0f} ms")
    pygame.mixer.quit()
    return f"real device at channel volume 0, mixer {got}: " + "; ".join(parts)


def check_sapi():
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    voices = voice.GetVoices("", "")
    count = voices.Count
    default = voice.Voice.GetDescription()
    voice.Volume = 0  # silent test
    start = time.perf_counter()
    voice.Speak("Hike", 1)  # asynchronous
    returned = (time.perf_counter() - start) * 1000
    done = voice.WaitUntilDone(15000)
    spoke = (time.perf_counter() - start) * 1000
    voice.Speak("", 2)  # purge
    if not done:
        raise RuntimeError("the default voice did not finish a one-word line in 15 s")
    # the game needs one voice object per role voice (D-031): five distinct voices into memory streams
    objs = []
    for i in range(min(5, count)):
        v = win32com.client.Dispatch("SAPI.SpVoice")
        v.Voice = voices.Item(i)
        stream = win32com.client.Dispatch("SAPI.SpMemoryStream")
        fmt = win32com.client.Dispatch("SAPI.SpAudioFormat")
        fmt.Type = 22  # 22 kHz, 16-bit, mono
        stream.Format = fmt
        v.AudioOutputStream = stream
        objs.append((v, stream, v.Voice.GetDescription()))
    for v, _, _ in objs:
        v.Speak("Hike", 1)
    sizes = []
    for v, stream, name in objs:
        if not v.WaitUntilDone(15000):
            raise RuntimeError(f"voice '{name}' did not finish in 15 s")
        sizes.append(len(bytes(stream.GetData())))
    return (f"pywin32 SAPI.SpVoice: {count} voices, default '{default}', Volume 0, async Speak returned in "
            f"{returned:.0f} ms and finished in {spoke:.0f} ms; {len(objs)} voice objects at once into memory, "
            f"bytes {sizes}")


def check_voice_registry():
    import winreg
    key = r"SOFTWARE\Microsoft\Speech\Voices\Tokens"
    out = []
    for flag, label in ((winreg.KEY_WOW64_64KEY, "64-bit view"), (winreg.KEY_WOW64_32KEY, "32-bit view")):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ | flag) as k:
                out.append(f"{label} {winreg.QueryInfoKey(k)[0]}")
        except OSError:
            out.append(f"{label} 0")
    return "voice tokens in the registry: " + ", ".join(out)


def find_package():
    """The game's package under the src folder: the one that holds ui\\window.py (brain in the kit, nfl4 later)."""
    found = sorted(glob.glob(os.path.join(KIT_SRC, "*", "ui", "window.py")))
    if not found:
        raise RuntimeError(f"no package with ui\\window.py under {KIT_SRC}")
    return os.path.basename(os.path.dirname(os.path.dirname(found[0])))


def check_window():
    import pygame
    sys.path.insert(0, KIT_SRC)
    module = importlib.import_module(f"{find_package()}.ui.window")  # the kit's ctypes Win32 window
    cls = [c for n, c in vars(module).items() if isinstance(c, type) and n.endswith("Window") and c.__module__ == module.__name__][0]
    window = cls(lambda code: None, lambda: None)
    pygame.mixer.init(MIX, -16, 2, 256)
    ok = pygame.mixer.get_init() is not None
    pygame.mixer.quit()
    window.destroy()
    if not ok:
        raise RuntimeError("the pygame mixer failed in a process with a Win32 window")
    return "the kit's ctypes Win32 window is created (not shown) and destroyed; the mixer works in the same process"


def check_nvda():
    arch = "x64" if BITS == 64 else "x86"
    dll = ctypes.WinDLL(os.path.join(KIT_SRC, find_package(), "speech", "nvda_client", arch, "nvdaControllerClient.dll"))
    status = dll.nvdaController_testIfRunning()
    return f"{arch} nvdaControllerClient.dll loaded; testIfRunning = {status} ({'NVDA running' if status == 0 else 'NVDA not running'})"


def check_jaws():
    import winreg
    seen = []
    for flag, label in ((winreg.KEY_WOW64_64KEY, "64-bit view"), (winreg.KEY_WOW64_32KEY, "32-bit view")):
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"FreedomSci.JawsApi\CLSID", 0, winreg.KEY_READ | flag) as k:
                seen.append(f"{label} {winreg.QueryValue(k, '')}")
        except OSError:
            seen.append(f"{label} not registered")
    if all("not registered" in s for s in seen):
        raise RuntimeError("FreedomSci.JawsApi is not registered (JAWS missing; the game then falls back, B-S15)")
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    win32com.client.Dispatch("FreedomSci.JawsApi")  # created only; no method is called, JAWS is not asked to speak
    return "FreedomSci.JawsApi registered (" + ", ".join(seen) + ") and creatable (no call made)"


def check_sleep():
    ctypes.windll.winmm.timeBeginPeriod(1)
    try:
        samples = []
        for _ in range(200):
            t = time.perf_counter()
            time.sleep(0.001)
            samples.append(time.perf_counter() - t)
    finally:
        ctypes.windll.winmm.timeEndPeriod(1)
    samples.sort()
    return f"sleep(1 ms): median {samples[100] * 1000:.2f} ms, worst {samples[-1] * 1000:.2f} ms"


def main():
    if MODE == "real":
        check(f"real mixer {BITS}-bit", real_device_run)
        for name, ok, detail in results:
            print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        sys.exit(0 if all(ok for _, ok, _ in results) else 1)
    check("python", check_python)
    check("imports", check_imports)
    check("wavs", check_wavs)
    check("pitch and pan", check_pitch_and_pan)
    check("mixer, dummy driver", check_mixer_dummy)
    check("mixer, real device", check_mixer_real)
    check("sapi", check_sapi)
    check("voice registry", check_voice_registry)
    check("window", check_window)
    check("nvda", check_nvda)
    check("jaws", check_jaws)
    check("sleep precision", check_sleep)
    lines = [f"{'PASS' if ok else 'FAIL'} {name}: {detail}" for name, ok, detail in results]
    lines.append(f"RESULT {BITS}-bit: {sum(ok for _, ok, _ in results)} of {len(results)} checks passed")
    text = "\n".join(lines) + "\n"
    print(text)
    if OUT:
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)


if __name__ == "__main__":
    main()
