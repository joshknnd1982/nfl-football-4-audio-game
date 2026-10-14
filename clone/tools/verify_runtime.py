"""Runtime check for the Brain clone (P6 S6.2). Inspired by Jim Kitchen's Brain.

Checks, silently, that every library the clone will use loads and works in the
running Python (run once with the 64-bit and once with the 32-bit environment):
audio with per-sound pitch and pan on nine channels at once, SAPI 5 speech,
the wx window toolkit together with pygame, the NVDA controller client,
and how precise short sleeps are (the playback loop sleeps 1-2 ms per pass).

Nothing is audible: sounds play at channel volume 0, speech at SAPI volume 0,
no window is shown, NVDA is only asked whether it is running.

Usage: python verify_runtime.py <folder with brain*.wav> <nvda controller folder>
Prints one line per check and exits 1 if any check failed.
"""
import ctypes
import os
import platform
import struct
import sys
import time
import wave
import winreg

results = []


def check(name, func):
    try:
        detail = func()
        results.append((name, True, detail))
    except Exception as exc:  # report every failure, keep checking the rest
        results.append((name, False, f"{type(exc).__name__}: {exc}"))


def read_wav_mono(path):
    """Return (16-bit mono PCM bytes, sample rate) for 8- or 16-bit mono PCM."""
    import audioop
    with wave.open(path, "rb") as w:
        rate, width, frames = w.getframerate(), w.getsampwidth(), w.readframes(w.getnframes())
    if width == 1:  # 8-bit wav is unsigned
        frames = audioop.lin2lin(audioop.bias(frames, 1, 128), 1, 2)
    return frames, rate


def pitched_stereo(data, play_rate, mix_rate, left, right):
    """Resample so the sound plays as if its buffer ran at play_rate, then pan (audioop, no numpy)."""
    import audioop
    out, _ = audioop.ratecv(data + data[-2:] * 2, 2, 1, play_rate, mix_rate, None, 1, 0)
    return audioop.tostereo(out, 2, left, right)


def check_python():
    bits = struct.calcsize("P") * 8
    return f"Python {platform.python_version()} {bits}-bit at {sys.executable}"


def check_audio(wav_dir):
    def run():
        import audioop
        import pygame
        mix_rate = 44100
        pygame.mixer.pre_init(mix_rate, -16, 2, 256)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(9)
        got = pygame.mixer.get_init()
        # Pitch: two wavs at the lowest and highest offsets (GAME_SPEC 5.3: -2000 and +1900 Hz).
        timings = []
        for name, offset in (("brain36.wav", -2000), ("brain21.wav", 1900)):
            data, rate = read_wav_mono(os.path.join(wav_dir, name))
            play_rate = rate + offset
            # Pan +750 (hundredths of dB): left gain 10^(-750/2000), right 1 (GAME_SPEC 5.5).
            pcm = pitched_stereo(data, play_rate, mix_rate, 10 ** (-750 / 2000), 1.0)
            snd = pygame.mixer.Sound(buffer=pcm)
            ch = pygame.mixer.Channel(0)
            ch.set_volume(0.0)  # silent test
            start = time.perf_counter()
            ch.play(snd)
            while ch.get_busy():
                time.sleep(0.001)
            heard = time.perf_counter() - start
            expected = len(data) / 2 / play_rate
            timings.append(f"{name}@{play_rate}Hz expected {expected*1000:.0f} ms, busy {heard*1000:.0f} ms")
        # Nine channels at once.
        data, rate = read_wav_mono(os.path.join(wav_dir, "brain21.wav"))
        snd = pygame.mixer.Sound(buffer=pitched_stereo(data, rate, mix_rate, 1.0, 1.0))
        chans = [pygame.mixer.Channel(i) for i in range(9)]
        for ch in chans:
            ch.set_volume(0.0)
            ch.play(snd)
        busy = sum(ch.get_busy() for ch in chans)
        pygame.mixer.stop()
        pygame.mixer.quit()
        if busy != 9:
            raise RuntimeError(f"only {busy} of 9 channels busy")
        return f"pygame-ce {pygame.version.ver}, audioop-lts {audioop.__name__}, mixer {got}, 9 of 9 channels; " + "; ".join(timings)
    return run


def check_sapi():
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    voices = voice.GetVoices("", "")
    count = voices.Count
    first = voices.Item(0).GetDescription() if count else "none"
    voice.Voice = voices.Item(0)
    voice.Volume = 0  # silent test
    start = time.perf_counter()
    voice.Speak("test", 1)  # SVSFlagsAsync
    returned = time.perf_counter() - start
    voice.Speak("", 2)  # SVSFPurgeBeforeSpeak: stop at once
    voice.WaitUntilDone(1000)
    return f"pywin32 SAPI.SpVoice: {count} voices, first '{first}', async Speak returned in {returned*1000:.0f} ms, purge ok"


def check_voice_registry():
    """Count SAPI 5 voice tokens the cheap way (playbook 7.4), this process's view only."""
    key = r"SOFTWARE\Microsoft\Speech\Voices\Tokens"
    counts = []
    for hive, label in ((winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")):
        try:
            with winreg.OpenKey(hive, key) as k:
                counts.append(f"{label} {winreg.QueryInfoKey(k)[0]}")
        except OSError:
            counts.append(f"{label} 0")
    return "voice tokens in this bitness: " + ", ".join(counts)


def check_wx_with_pygame():
    """Name kept from the wxPython days: the Win32 window (ctypes) and the pygame mixer in one process."""
    import sys
    import pygame
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
    from nfl4.ui.window import BrainWindow
    window = BrainWindow(lambda code: None, lambda: None)
    pygame.mixer.init(44100, -16, 2, 256)  # both libraries in one process
    ok = pygame.mixer.get_init() is not None
    pygame.mixer.quit()
    window.destroy()
    if not ok:
        raise RuntimeError("pygame mixer failed in a process with a Win32 window")
    return "Win32 window created through ctypes (not shown), pygame mixer works in the same process"


def check_nvda(controller_dir):
    def run():
        arch = "x64" if struct.calcsize("P") == 8 else "x86"
        dll = ctypes.WinDLL(os.path.join(controller_dir, arch, "nvdaControllerClient.dll"))
        status = dll.nvdaController_testIfRunning()
        return f"{arch} DLL loaded; testIfRunning = {status} ({'NVDA running' if status == 0 else 'NVDA not running'})"
    return run


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
    return f"sleep(1 ms): median {samples[100]*1000:.2f} ms, worst {samples[-1]*1000:.2f} ms"


def check_pyinstaller():
    import PyInstaller
    return f"PyInstaller {PyInstaller.__version__} importable"


def main():
    wav_dir, controller_dir = sys.argv[1], sys.argv[2]
    check("python", check_python)
    check("audio", check_audio(wav_dir))
    check("sapi", check_sapi)
    check("voice registry", check_voice_registry)
    check("wx with pygame", check_wx_with_pygame)
    check("nvda", check_nvda(controller_dir))
    check("sleep precision", check_sleep)
    check("pyinstaller", check_pyinstaller)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)


if __name__ == "__main__":
    main()
