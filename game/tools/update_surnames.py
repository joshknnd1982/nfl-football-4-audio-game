"""update_surnames.py: the surnames of real NFL players for the game's made-up players (nfl4 only, rule 0.13; NX-L12, D-163, D-164; CLAUDE.md 0.19). This is
inspired by Jim Kitchen.

The owner (2026-10-25, Q-016): "claude must research the last names of real nfl players and use those." With the N. F. L. rules every made-up player of the
game (a Franchise's later draft classes, the undrafted, the cut's fill, the stand-ins of injured men, the practice squads' top-ups, a quick game's last-resort
name) takes the last name of a real NFL player from game\\assets\\data\\nfl_surnames.txt, which this MAINTAINER'S tool writes (never the game, never a player).

Sources (facts only: names; no ratings, no photographs, no text of anyone):
  1. nflverse's players table (players.csv of the "players" release of nflverse/nflverse-data, CC BY 4.0, the credit is in the README): every man of the
     table who was on an NFL roster in a season (a rookie season or a last season is given);
  2. the game's own rosters.txt and free_agents.txt (the teams' pages of SR.2): today's men, whose surnames are in any case.
A surname is the table's last_name (the suffix is a field of its own: Jr., III are never part of it), trimmed; it is kept when it is 2 to 30 characters of
letters, spaces, apostrophes, hyphens and periods. One line per surname (the first spelling met in the sorted table when two differ only by case).

    py -3.14 -I update_surnames.py                         download players.csv (one request) into work\\rosters\\<date>\\raw, write into that folder
    py -3.14 -I update_surnames.py --saved <players.csv>   read a saved table (no network)
    py -3.14 -I update_surnames.py --write                 then copy nfl_surnames.txt into game\\assets\\data (only when it holds at least MIN_COUNT names)

update_rosters.py --write runs the same build after it writes the rosters (`build_from`), so the list follows the rosters.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import re
import sys
import urllib.request
from pathlib import Path

GAME = Path(__file__).resolve().parent.parent
NFL4 = GAME.parent
DATA = GAME / "assets" / "data"
URL = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
UA = "nfl4-roster-update/1.0 (maintainer's tool of a free audio football game for blind players; +https://github.com/joshknnd1982)"
MIN_COUNT = 5000                  # a table that gives fewer surnames is not the players table: nothing is written
_GOOD = re.compile(r"^[A-Za-z][A-Za-z .'\-]{0,28}[A-Za-z.]$")
_ROSTER_LINE = re.compile(r"^\s*T\d{1,2}P\d{1,3}\s*=\s*(?:\S+\s+)?\S+\s+(?:\d{1,2}|-)\s+(.+?)\s*$", re.IGNORECASE)
_FREE_LINE = re.compile(r"^\s*F\d{1,4}\s*=\s*\S+\s+(?:\d{1,2}|-)\s+(.+?)\s*$", re.IGNORECASE)
_SUFFIX = re.compile(r"\s+(?:Jr\.?|Sr\.?|II|III|IV|V)$", re.IGNORECASE)

HEADER = """# NFL Football 4 nflsurnames, format 1.
# These are the surnames of real NFL players.
# With the N. F. L. rules every made-up player of the game takes one of these last names, with a first name of the game's own list: the players of a
# Franchise's later draft classes, the undrafted, the stand-ins of injured men and the practice squads' new men. No made-up player has the full name of
# a real player of the rosters. Each line is an ID, an equals sign and a last name.
# A name has 2 to 30 characters, with no comma and no semicolon. Delete a line to get the original name back. Delete the whole file to get all of them back.
# The names are facts, used descriptively: the last names of men who played in the N. F. L. (nflverse's players table, CC BY 4.0, and the teams' own
# roster pages). They are not endorsed by the league, the teams or the players.
"""


def surname_of(full: str) -> str:
    """The last name of a written full name ("Amon-Ra St. Brown" -> "St. Brown" is not knowable: the last word; a suffix is dropped)."""
    name = _SUFFIX.sub("", full.strip())
    words = name.split()
    return words[-1] if len(words) > 1 else ""


def build_from(players_csv: bytes, roster_text: str, free_text: str) -> tuple:
    """(the file's text, the number of surnames, the sources' counts) from the players table and the game's two files."""
    seen: dict = {}
    table = csv.DictReader(io.StringIO(players_csv.decode("utf-8-sig", "replace")))
    rows = 0
    kept = 0
    for row in table:
        rows += 1
        if not (row.get("rookie_season") or row.get("last_season")):
            continue
        last = " ".join((row.get("last_name") or "").split())
        if not _GOOD.match(last):
            continue
        key = last.casefold()
        if key not in seen:
            seen[key] = last
            kept += 1
    current = 0
    for text, pattern in ((roster_text, _ROSTER_LINE), (free_text, _FREE_LINE)):
        for line in text.splitlines():
            m = pattern.match(line)
            if not m:
                continue
            last = surname_of(m.group(1))
            if last and _GOOD.match(last) and last.casefold() not in seen:
                seen[last.casefold()] = last
                current += 1
    names = sorted(seen.values(), key=lambda n: (n.casefold(), n))
    today = _dt.date.today().isoformat()
    lines = [HEADER, "VERSION = as of %s" % today]
    lines += ["S%05d = %s" % (number, name) for number, name in enumerate(names, start=1)]
    return "\n".join(lines) + "\n", len(names), {"table rows": rows, "table surnames": kept, "added from the rosters": current}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--saved", help="a players.csv saved before (no network)")
    ap.add_argument("--out", help="the folder of this run (default work\\rosters\\<date>)")
    ap.add_argument("--write", action="store_true", help="copy nfl_surnames.txt into game\\assets\\data")
    a = ap.parse_args()
    today = _dt.date.today().isoformat()
    out = Path(a.out) if a.out else NFL4 / "work" / "rosters" / today
    (out / "raw").mkdir(parents=True, exist_ok=True)
    if a.saved:
        data = Path(a.saved).read_bytes()
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        (out / "raw" / "nflverse_players.csv").write_bytes(data)
    text, count, counts = build_from(data, (DATA / "rosters.txt").read_bytes().decode("utf-8"), (DATA / "free_agents.txt").read_bytes().decode("utf-8"))
    (out / "nfl_surnames.txt").write_bytes(text.encode("utf-8"))
    print("%d surnames (%s); written: %s" % (count, ", ".join("%s %d" % kv for kv in counts.items()), out / "nfl_surnames.txt"))
    if a.write:
        if count < MIN_COUNT:
            print("NOT written into the game: fewer than %d surnames" % MIN_COUNT)
            return 1
        (DATA / "nfl_surnames.txt").write_bytes(text.encode("utf-8"))
        print("written:", DATA / "nfl_surnames.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
