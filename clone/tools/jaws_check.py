"""Check Brain's JAWS backend against a RUNNING JAWS. This is inspired by Jim Kitchen.

Start JAWS first, then run (from the clone folder; the 32-bit environment checks the 32-bit registration):
  C:\\Users\\joshk\\.kitchensinc-venvs\\nfl4-64\\Scripts\\python.exe tools\\jaws_check.py <report file>
JAWS SPEAKS during this check, about 15 seconds: a short sentence, a second one queued after it,
a long sentence that is cut off half-way by StopSpeech, and one flushed sentence. The report lists what each call
returned and how long it took. Listen for: the first two sentences in order, the long one stopping, nothing left over.
"""
import os
import struct
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from nfl4.speech.jaws import JawsBackend, _window_open, estimated_seconds  # noqa: E402


def timed(label, call, lines):
    start = time.perf_counter()
    result = call()
    lines.append(f"{label}: {result!r} in {(time.perf_counter() - start) * 1000:.1f} ms")
    return result


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "jaws_check_report.txt"
    lines = [f"JAWS check, {struct.calcsize('P') * 8}-bit Python {sys.version.split()[0]}"]
    jaws = JawsBackend()
    lines.append(f"window class JFWUI2 found: {_window_open()}")
    com = jaws._object()
    lines.append(f"COM object made: {com is not None}")
    ok = timed("is_available", jaws.is_available, lines)
    if not ok:
        lines.append("JAWS is not running (or not reachable): nothing was spoken. Start JAWS and run this again.")
        open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("\n".join(lines))
        return 1
    timed("speak 1", lambda: jaws.speak("Brain JAWS check. This is sentence one."), lines)
    timed("speak 2 (queued)", lambda: jaws.speak("This is sentence two, queued after one."), lines)
    start = time.perf_counter()
    jaws.wait_until_done()
    lines.append(f"estimated wait for both: {time.perf_counter() - start:.2f} s "
                 f"(estimates {estimated_seconds('Brain JAWS check. This is sentence one.'):.2f} + "
                 f"{estimated_seconds('This is sentence two, queued after one.'):.2f}); did JAWS finish at about that moment?")
    time.sleep(0.5)
    long_text = ("This long sentence should be cut off by stop speech, so you should hear only the first words "
                 "of it and never the end of it, which is the word banana.")
    timed("speak long", lambda: jaws.speak(long_text), lines)
    time.sleep(0.7)
    timed("stop", jaws.stop, lines)
    time.sleep(1.5)
    timed("speak after stop", lambda: jaws.speak("Speech works again after stop."), lines)
    jaws.wait_until_done()
    time.sleep(0.5)
    lines.append("Then a flush test (not used by the game): the second SayString with flush interrupts the first.")
    obj = jaws._object()
    timed("say long, no flush", lambda: obj.SayString("This sentence should be interrupted by the next one.", False), lines)
    time.sleep(0.5)
    timed("say flushed", lambda: obj.SayString("Flushed sentence. The check is finished.", True), lines)
    time.sleep(3)
    lines.append("Done. Report what you heard.")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
