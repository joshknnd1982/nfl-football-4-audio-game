"""Where the tools find the program's debug log (playbook 7.11): one file per launch, `nfl4-YYYYMMDD-HHMMSS.log`, in <data>/logs.

The tools used to read a single `nfl4.log`; since the detailed debug log (rule 0.15) there is one file per launch (and a second
half file `-b.log` when a launch is long). `launch_text(data_dir)` is the text of the newest launch, both halves in order.
"""
import glob
import os
import re


def launch_files(data_dir: str) -> list[str]:
    logs = os.path.join(data_dir, "logs")
    files = sorted(glob.glob(os.path.join(logs, "nfl4-2*.log")))
    if not files:
        return []
    stems = sorted({re.sub(r"(-b)?\.log$", "", f) for f in files})
    newest = stems[-1]
    halves = [p for p in (newest + ".log", newest + "-b.log") if os.path.exists(p)]

    def sequence(path):
        with open(path, encoding="utf-8", errors="replace") as handle:
            match = re.search(r"^-- part \d+, sequence (\d+)", handle.read(200000), re.MULTILINE)
        return int(match.group(1)) if match else 0

    return sorted(halves, key=sequence)


def launch_text(data_dir: str) -> str:
    """The newest launch's log, "" when there is none yet."""
    parts = []
    for path in launch_files(data_dir):
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                parts.append(handle.read())
        except OSError:
            pass
    return "\n".join(parts)
