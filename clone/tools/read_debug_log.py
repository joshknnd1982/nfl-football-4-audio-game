"""Read a debug log or a problem report the way Claude needs it (playbook 7.11). This is inspired by Jim Kitchen.

    python clone/tools/read_debug_log.py <log file | problem-report zip | logs folder> [--lines N] [--all] [--replay]

Prints, in this order:
  1. the setup in ten lines (game, Windows, language, screen readers, speech, sound, folders, log level);
  2. every WARNING, ERROR, SLOW and HANG, with a count per component and per speech backend;
  3. the 40 lines before the first ERROR and the 40 lines before the end;
  4. the settings and the customization files' health;
  5. the random seed(s) and the games, seasons and leagues that started.
--replay builds the key script of the first game (or `--game N`) from its seed and its keys and plays it again on the clone's test
rig (tests/pagrig.py), then compares what the replay said with what the log says the game said, and prints the first line where
they differ. It is exact for a log made at the `trace` level (every random draw is in the log); for a `detailed` log it needs the
seed and the draw count and holds only as long as the timing-dependent sound draws came out the same. A failure that comes from
the player's setup is reproduced with the fake speech and sound backends set to fail the same way, never by guessing.
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import re
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LINE = re.compile(r"^(\d\d:\d\d:\d\d\.\d{3}) \+(\d+\.\d+) (\w+) (.+?) (\S+) ([0-9a-f]{6}) (.*)$")
FIELD = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')
PART = re.compile(r"^-- part (\d+), sequence (\d+) of run (\w+) --")
IMPORTANT = ("WARNING", "ERROR", "CRITICAL")


class Event:
    __slots__ = ("time", "elapsed", "level", "thread", "component", "run", "message", "name", "fields", "raw")

    def __init__(self, raw, match):
        self.raw = raw
        self.time, self.elapsed, self.level, self.thread, self.component, self.run, self.message = match.groups()
        head, _, rest = self.message.partition(" ")
        self.name = head
        self.fields = {key: unquote(value) for key, value in FIELD.findall(rest)}


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\n', '\n').replace('\\r', '\r').replace('\\"', '"').replace('\\\\', '\\')
    return value


class Log:
    def __init__(self, texts: list[str], crash: str = "", name: str = ""):
        self.name = name
        self.crash = crash
        self.report: dict[str, str] = {}
        self.events: list[Event] = []
        self.other: list[str] = []
        for text in texts:
            self._read(text)

    def _read(self, text: str) -> None:
        in_report = False
        for raw in text.splitlines():
            if raw.startswith("==== startup report"):
                in_report = True
                continue
            if raw.startswith("==== end of startup report"):
                in_report = False
                continue
            if in_report:
                key, sep, value = raw.partition(" = ")
                if sep:
                    self.report[key] = value
                continue
            match = LINE.match(raw)
            if match:
                self.events.append(Event(raw, match))
            elif raw.strip() and not PART.match(raw):
                key, sep, value = raw.partition(" = ")
                if sep and " " not in key and not raw.startswith(("--", "====")):
                    self.report.setdefault(key, value)           # an item the startup report added after the file began
                else:
                    self.other.append(raw)

    def find(self, component=None, name=None, level=None):
        for event in self.events:
            if (component is None or event.component.endswith(component)) and (name is None or event.name == name) \
                    and (level is None or event.level == level):
                yield event


def load(path: str) -> Log:
    """A launch log (both halves are found beside it), a problem-report zip (its newest log) or a logs folder (its newest launch)."""
    if os.path.isdir(path):
        names = sorted(n for n in os.listdir(path) if re.match(r"^nfl4-\d{8}-\d{6}", n) and n.endswith(".log"))
        if not names:
            raise SystemExit("no launch log in " + path)
        path = os.path.join(path, [n for n in names if not n.endswith("-b.log")][-1])
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as bundle:
            logs = sorted(n for n in bundle.namelist() if n.startswith("logs/"))
            newest = [n for n in logs if n.rsplit("-b.log", 1)[0].rsplit(".log", 1)[0] == _stem(logs[-1])]
            texts = [bundle.read(n).decode("utf-8", "replace") for n in newest]
            crash = bundle.read("crash-log.txt").decode("utf-8", "replace") if "crash-log.txt" in bundle.namelist() else ""
            system = bundle.read("system.txt").decode("utf-8", "replace") if "system.txt" in bundle.namelist() else ""
        log = Log(texts, crash, path)
        if not log.report:
            log._read(system)
        return log
    base = path[:-len("-b.log")] if path.endswith("-b.log") else path[:-len(".log")]
    halves = [p for p in (base + ".log", base + "-b.log") if os.path.exists(p)]
    texts = [open(p, encoding="utf-8", errors="replace").read() for p in halves]
    texts.sort(key=_sequence)
    crash_path = os.path.join(os.path.dirname(path), "nfl4-crash.log")
    crash = open(crash_path, encoding="utf-8", errors="replace").read() if os.path.exists(crash_path) else ""
    return Log(texts, crash, path)


def _stem(name: str) -> str:
    return name[:-len("-b.log")] if name.endswith("-b.log") else name[:-len(".log")]


def _sequence(text: str) -> int:
    match = re.search(r"^-- part \d+, sequence (\d+)", text, re.MULTILINE)
    return int(match.group(1)) if match else 0


def setup_lines(log: Log) -> list[str]:
    r = log.report.get
    return [
        "game: %s %s, %s, %s, %s" % (r("game", "?"), r("version", "?"), r("bits", "?"), r("frozen", "?"), r("installed_or_portable", "?")),
        "windows: %s, build %s, %s, %s" % (r("windows_version", "?"), r("windows_build", "?"), r("windows_edition", "?"), r("windows_bits", "?")),
        "language: display %s, locale %s, ansi %s, oem %s, %s" % (r("display_language", "?"), r("locale", "?"), r("ansi_code_page", "?"),
                                                                  r("oem_code_page", "?"), r("time_zone", "?")),
        "machine: %s cpus, memory %s MB, free %s MB, administrator %s, dpi %s" % (r("cpu_count", "?"), r("memory_mb", "?"),
                                                                                  r("free_space_mb", "?"), r("administrator", "?"), r("dpi", "?")),
        "screen readers running: %s; NVDA %s (%s); JAWS %s" % (r("screen_readers_running", "?"), r("nvda_running", "?"), r("nvda_version", "?"),
                                                              r("jaws_running", "?")),
        "speech: setting %s, in use %s; SAPI %s, %s voices" % (r("speech_mode_setting", "?"), r("speech_engine_in_use", "?"), r("sapi_started", "?"),
                                                              r("sapi_voice_count", "?")),
        "announcer voice: %s" % r("voice_announcer", "?"),
        "sound: %s; %s; %s; problems: %s" % (r("audio_device_opened", "?"), r("audio_format", "?"), r("audio_devices_found", "?"), r("sounds_problems", "?")),
        "folders: data %s; documents %s; OneDrive data %s" % (r("data_dir", "?"), r("documents_folder", "?"), r("data_on_onedrive", "?")),
        "log: level %s, file %s, run %s, errors last launch %s" % (r("debug_log_level", "?"), r("log_file", "?"), r("run_id", "?"), r("log_errors_last_launch", "?")),
    ]


def problems(log: Log) -> tuple[list[Event], dict, dict]:
    bad = [e for e in log.events if e.level in IMPORTANT or e.name in ("SLOW", "HANG")]
    per_component = collections.Counter(e.component for e in bad)
    backends = collections.Counter()
    for e in log.events:
        if e.component.endswith("speech") and e.name == "request":
            backends[e.fields.get("backend", "?") + " spoke"] += 1
    for e in bad:
        for name in ("SAPI 5", "NVDA", "JAWS"):
            if name.lower() in e.message.lower():
                backends[name + " problems"] += 1
    return bad, per_component, backends


def seeds(log: Log) -> list[str]:
    out = []
    for e in log.events:
        if e.component.endswith("rnd") and e.name in ("seed", "season_start", "game_start", "league_start"):
            out.append("%s %s %s" % (e.time, e.name, " ".join("%s=%s" % kv for kv in e.fields.items())))
    return out


def report(log: Log, lines: int = 40, everything: bool = False) -> str:
    out = ["== setup"] + setup_lines(log)
    bad, per_component, backends = problems(log)
    out += ["", "== warnings, errors, slow steps (%d)" % len(bad)]
    out += [e.raw[:400] for e in (bad if everything else bad[:60])]
    if len(bad) > 60 and not everything:
        out.append("... %d more (use --all)" % (len(bad) - 60))
    out += ["by component: " + ", ".join("%s %d" % kv for kv in per_component.most_common()) or "none"]
    out += ["by backend: " + ", ".join("%s %d" % kv for kv in sorted(backends.items())) or "none"]
    first_error = next((i for i, e in enumerate(log.events) if e.level in ("ERROR", "CRITICAL")), None)
    if first_error is not None:
        out += ["", "== the %d lines before the first error and the error" % lines]
        out += [e.raw[:300] for e in log.events[max(0, first_error - lines):first_error + 1]]
    out += ["", "== the last %d lines" % lines] + [e.raw[:300] for e in log.events[-lines:]]
    last = log.events[-1].name if log.events else ""
    out += ["last event: %s%s" % (last or "none", "" if last == "closed" else "   (NOT `closed`: the program did not end normally)")]
    if log.crash.strip():
        out += ["", "== crash log (%d lines, first 25)" % len(log.crash.splitlines())] + log.crash.splitlines()[:25]
    out += ["", "== settings and customization files"]
    for key in ("settings_read", "settings_problems", "customization_files"):
        out.append("%s = %s" % (key, log.report.get(key, "?")))
    out += ["", "== random seeds, games, seasons, leagues"] + (seeds(log) or ["none logged"])
    return "\n".join(out)


# ----- replay -----

def game_window(log: Log, number: int = 1):
    """(start event, events of that game up to its end) for the number-th game_start."""
    starts = [i for i, e in enumerate(log.events) if e.component.endswith("rnd") and e.name == "game_start"]
    if number > len(starts):
        raise SystemExit("the log holds %d game(s)" % len(starts))
    begin = starts[number - 1]
    end = next((i for i in range(begin, len(log.events)) if log.events[i].name == "game_end"), len(log.events))
    return log.events[begin], log.events[begin:end + 1]


def replay(log: Log, number: int = 1, tmp: str | None = None) -> dict:
    """Play the number-th game of the log again on the pag rig and compare what it said. Returns a dict with the verdict."""
    sys.path[:0] = [os.path.join(os.path.dirname(HERE), "src"), os.path.join(os.path.dirname(HERE), "tests")]
    from pagrig import make_rig, play
    start, window = game_window(log, number)
    keys = [int(e.fields["vk"]) for e in window if e.component.endswith("key") and e.name in ("pump", "read") and "vk" in e.fields]
    draws = [(int(e.fields["n"]), float(e.fields["x"])) for e in log.events if e.component.endswith("rnd") and e.name == "draw"]
    before = int(start.fields.get("draws", 0))
    seed = start.fields.get("seed", "given")
    recorded = [x for n, x in draws if n > before]
    mode = "recorded draws (trace)" if recorded else None
    if recorded:
        source = _Recorded(recorded)
    elif seed != "given":
        source = random.Random(int(seed))
        for _ in range(before):
            source.random()
        mode = "seed %s, %d draws skipped" % (seed, before)
    else:
        raise SystemExit("this game has neither a seed nor recorded draws: it cannot be replayed")
    heard = [e.fields["text"] for e in window if e.component.endswith("speech") and e.name == "request" and "text" in e.fields]
    folder = tmp or tempfile.mkdtemp(prefix="nfl4-replay-")
    from pathlib import Path
    rig = make_rig(Path(folder), rng=source, answers=keys, policy=None, vtrnt=int(start.fields.get("vtrnt", 2)))
    season = rig.game.season
    if "tn1" in start.fields:
        season.choose_team(int(start.fields["tn1"]), int(start.fields["tn2"]))
        season.tn3, season.tn4 = int(start.fields["tn3"]), int(start.fields["tn4"])
    error = ""
    try:
        play(rig)
    except Exception as exc:                          # the replay ran out of keys or draws: where it stopped is the finding
        error = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    said = [text for text, _, _ in rig.said]
    n = min(len(said), len(heard))
    first = next((i for i in range(n) if not _same(heard[i], said[i])), None)
    return {"mode": mode, "keys": len(keys), "logged_speech": len(heard), "replayed_speech": len(said),
            "identical": first is None and len(said) == len(heard) and not error, "first_difference": first,
            "logged": heard[first] if first is not None else None, "replayed": said[first] if first is not None else None, "stopped": error}


def _same(logged: str, replayed: str) -> bool:
    """The log hides the player's names as <typed>; the replay speaks them, so that word matches whatever stands in its place."""
    if "<typed>" not in logged:
        return logged == replayed
    pattern = ".+?".join(re.escape(part) for part in logged.split("<typed>"))
    return re.fullmatch(pattern, replayed, re.DOTALL) is not None


class _Recorded:
    """A random source that gives the numbers the log recorded, in order."""

    def __init__(self, values):
        self.values = list(values)
        self.at = 0

    def random(self) -> float:
        if self.at >= len(self.values):
            raise IndexError("the log recorded only %d draws; the replay needs more" % len(self.values))
        self.at += 1
        return self.values[self.at - 1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read an NFL Football 4 debug log or problem report.")
    parser.add_argument("path")
    parser.add_argument("--lines", type=int, default=40)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--game", type=int, default=1)
    args = parser.parse_args(argv)
    log = load(args.path)
    if args.replay:
        verdict = replay(log, args.game)
        for key, value in verdict.items():
            print("%s: %s" % (key, value))
        return 0 if verdict["identical"] else 2
    print(report(log, args.lines, args.all))
    return 0


if __name__ == "__main__":
    sys.exit(main())
