"""S8.3, GAP_REGISTER G-S9 (nfl4): every kind of sentence the program says, made into memory by one voice of every SAPI 5 engine installed
(nothing is played, nothing is heard), with the program's own ways of writing a text again when a voice makes no sound (speech_variants).

    <venv python> -I sapi_render_check.py reduce <corpus.jsonl> <reduced.json>
    <venv python> -I sapi_render_check.py run <reduced.json> <report.json> [voices per engine]
    <venv python> -I sapi_render_check.py one <reduced.json> <voice id> <out.json>      (the child of run)

A text is SILENT for a voice when neither it nor any of its variants makes audio; a text that needs a variant is HEALED (the program speaks
the variant); the rest are fine. The parent starts one child per voice with a timeout, because an old engine can hang.
"""
import json
import re
import subprocess
import sys
import time

import os
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC)

NOISE = re.compile(r"^(text|nobody|j\d|t\d|message|only once|back again|a very long|one|two|t\d+-)\b|^(.)\2{20,}$|^`$")   # the stress tests' own texts


def signature(text):
    marks = tuple(sorted({c for c in text if not c.isalnum() and c != " "}))
    return (marks, bool(re.search(r"\d\s+\d", text)), bool(re.search(r"\d\.\d", text)), bool(re.search(r"\d,\d", text)),
            any(ord(c) > 127 for c in text), bool(re.search(r"\b[A-Z]\.", text)), len(text) > 120, len(text) < 6,
            bool(re.search(r"\d[A-Za-z]", text)), bool(re.search(r"[A-Za-z]\d", text)), bool(re.search(r"\d{3,}", text)),
            bool(re.search(r"\s{2,}", text)), text != text.strip())


def reduce(corpus, out):
    texts = [json.loads(line) for line in open(corpus, encoding="utf-8")]
    texts = [t for t in texts if t.strip() and not NOISE.match(t.strip())]
    groups = {}
    for t in texts:
        groups.setdefault(signature(t), []).append(t)
    keep = []
    for sig, items in groups.items():
        items.sort(key=len)
        keep += {items[0], items[len(items) // 2], items[-1]}
    keep += [t for t in texts if any(ord(c) > 127 for c in t)][:40]
    keep = sorted(set(keep))
    json.dump({"all": len(texts), "texts": keep}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("texts %d, signatures %d, kept %d" % (len(texts), len(groups), len(keep)))


def one(reduced, voice_id, out):
    import pythoncom
    import win32com.client
    from nfl4.speech.sapi5 import SAFT_44KHZ_16BIT_MONO, speech_variants, split_chunks
    pythoncom.CoInitialize()
    texts = json.load(open(reduced, encoding="utf-8"))["texts"]
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    # the enumerated token, as the program's own backend gets it: a token made with SetId(voice id) crashed the process with the SAM and
    # Votrax emulations (heap corruption, stack overrun) while the program itself speaks with them (S8.3)
    tokens = voice.GetVoices("", "")
    token = next(tokens.Item(i) for i in range(tokens.Count) if str(tokens.Item(i).Id) == voice_id)
    voice.Voice = token

    def render(text):
        stream = win32com.client.Dispatch("SAPI.SpMemoryStream")
        fmt = win32com.client.Dispatch("SAPI.SpAudioFormat")
        fmt.Type = SAFT_44KHZ_16BIT_MONO
        stream.Format = fmt
        voice.AudioOutputStream = stream
        voice.Speak(text, 1)
        if not voice.WaitUntilDone(15000):
            voice.Speak("", 1 | 2)
            return None
        return len(bytes(stream.GetData()))

    result = {"voice": voice_id, "fine": 0, "healed": [], "silent": [], "timeout": [], "error": [], "seconds": 0.0}
    began = time.time()
    for text in texts:
        try:
            state = "fine"
            for chunk in [c for c in split_chunks(text) if c.strip()]:
                size = render(chunk)
                if size is None:
                    state = "timeout"
                    break
                if size:
                    continue
                healed = False
                for variant in speech_variants(chunk):
                    size = render(variant)
                    if size:
                        healed = True
                        break
                state = "healed" if healed and state == "fine" else state
                if not healed:
                    state = "silent"
                    break
            if state == "fine":
                result["fine"] += 1
            else:
                result[state].append(text)
        except Exception as exc:
            result["error"].append("%s: %r" % (text[:60], exc))
            if len(result["error"]) > 5:
                break
    result["seconds"] = round(time.time() - began, 1)
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False)


def run(reduced, report, per_engine=1):
    from nfl4.speech.voices import enumerate_voices, group_by_engine
    import pythoncom
    pythoncom.CoInitialize()
    voices, broken = enumerate_voices()
    groups = group_by_engine(voices)
    print("%d voices, %d engines, %d broken entries, %d bits" % (len(voices), len(groups), broken, 64 if sys.maxsize > 2**32 else 32), flush=True)
    results = []
    for engine, members in groups:
        for member in members[:per_engine]:
            out = report + ".%d.json" % len(results)
            began = time.time()
            try:
                subprocess.run([sys.executable, "-I", __file__, "one", reduced, member.voice_id, out], timeout=90,
                               capture_output=True)
                data = json.load(open(out, encoding="utf-8"))
            except Exception as exc:
                data = {"voice": member.voice_id, "fine": 0, "healed": [], "silent": [], "timeout": [], "error": ["child: %r" % exc],
                        "seconds": round(time.time() - began, 1)}
            data["engine"], data["name"] = engine, member.name
            results.append(data)
            print("%-28s %-40s fine %4d healed %3d silent %3d timeout %3d error %d  %5.1f s" % (
                engine[:28], member.name[:40], data["fine"], len(data["healed"]), len(data["silent"]), len(data["timeout"]),
                len(data["error"]), data["seconds"]), flush=True)
    json.dump(results, open(report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "reduce":
        reduce(sys.argv[2], sys.argv[3])
    elif cmd == "one":
        one(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        run(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 1)
