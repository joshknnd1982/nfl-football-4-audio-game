"""update_rosters.py: pull the current real NFL rosters, check them and write rosters.txt (layout 2) and free_agents.txt (nfl4 only, rule 0.13;
CLAUDE.md 0.32, playbook 7.23, NX-L1, NX-L8; D-152 to D-156, SR.2). This is inspired by Jim Kitchen.

A MAINTAINER'S tool: it is never run by the game or by a player (D-154, D-156). It reads, gently and only what robots.txt allows:
  1. each team's own roster page and depth chart page (https://<team site>/team/players-roster/ and /team/depth-chart/): the official primary
     source of who is on the team, on which list, with which number, and the team's own depth order and return roles (D-156: the NFL's terms 1.3
     bar systematic retrieval; the owner carries that risk; switch this reader off with --no-official if anyone objects);
  2. nflverse's roster file and newest depth chart snapshot (CC BY 4.0; GitHub's API, one release listing and one file each): the positions with
     left and right (LDE, RDE, WLB, ...), the comparison of membership;
  3. Sleeper's player feed (free for non-commercial use, at most once a day: a feed saved today is reused): the second comparison, the free agents' ages.
  4. nflverse's snap counts (CC BY 4.0, from Pro Football Reference's game pages; one file): who played the snaps of the team's last two games.
Every page and feed is saved as it was served in <out>/raw/ (kept local, never published). A pause of --pause seconds separates two requests.

THE STARTERS (D-177, the tester's report of 2026-10-26: the Giants' page still started Jameis Winston after J.J. McCarthy was named the starter):
the team's own depth chart gives the order, except (a) where nflverse's newest chart and Sleeper's depth chart agree on a starter who is active at
that position (agreed_starters_first), and (b) where a starter played under 40 percent of the snaps in each of the last two games while a man of the
position or its other side played over 70 percent in each (snap_starters); then (c) roster_settlements.txt, whose "depth N" lines settle an order
the news gives. Every move is a warning line of the report. A man injured for a few games stays his team's starter (only a reserve list moves him).

    py -3.14 -I update_rosters.py                         pull, check, write into work\\rosters\\<date>\\ (never into the game)
    py -3.14 -I update_rosters.py --write                 the same, then copy the files into game\\assets\\data when every check passes
    py -3.14 -I update_rosters.py --saved <folder>        work from the pages saved in <folder>\\raw (no network)
    py -3.14 -I update_rosters.py --no-official           do not read the teams' sites: nflverse gives membership, Sleeper compares

The report (<out>/report.txt) lists the failures, the warnings, every difference between the sources, and every change since the previous file.
A failure never lets --write replace a file. Facts only: names, teams, positions, numbers, lists, return roles; no ratings.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import gzip
import html as _html
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from pathlib import Path

GAME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GAME / "src"))
from nfl4.extras import roster_file as RF          # noqa: E402  (the same format and checks as the game)

NFL4 = GAME.parent
DATA = GAME / "assets" / "data"
UA = "nfl4-roster-update/1.0 (maintainer's tool of a free audio football game for blind players; +https://github.com/joshknnd1982)"
SEASON = 2026

# T01 to T32 in the game's order (game/src/nfl4/game/league.py), the team's own site, nflverse's and Sleeper's abbreviation
TEAMS = (
    (1, "Bengals", "www.bengals.com", "CIN", "CIN"), (2, "Browns", "www.clevelandbrowns.com", "CLE", "CLE"),
    (3, "Ravens", "www.baltimoreravens.com", "BAL", "BAL"), (4, "Steelers", "www.steelers.com", "PIT", "PIT"),
    (5, "Bills", "www.buffalobills.com", "BUF", "BUF"), (6, "Dolphins", "www.miamidolphins.com", "MIA", "MIA"),
    (7, "Jets", "www.newyorkjets.com", "NYJ", "NYJ"), (8, "Patriots", "www.patriots.com", "NE", "NE"),
    (9, "Broncos", "www.denverbroncos.com", "DEN", "DEN"), (10, "Chargers", "www.chargers.com", "LAC", "LAC"),
    (11, "Chiefs", "www.chiefs.com", "KC", "KC"), (12, "Raiders", "www.raiders.com", "LV", "LV"),
    (13, "Colts", "www.colts.com", "IND", "IND"), (14, "Jaguars", "www.jaguars.com", "JAX", "JAX"),
    (15, "Texans", "www.houstontexans.com", "HOU", "HOU"), (16, "Titans", "www.tennesseetitans.com", "TEN", "TEN"),
    (17, "Bears", "www.chicagobears.com", "CHI", "CHI"), (18, "Lions", "www.detroitlions.com", "DET", "DET"),
    (19, "Packers", "www.packers.com", "GB", "GB"), (20, "Vikings", "www.vikings.com", "MIN", "MIN"),
    (21, "Cowboys", "www.dallascowboys.com", "DAL", "DAL"), (22, "Eagles", "www.philadelphiaeagles.com", "PHI", "PHI"),
    (23, "Giants", "www.giants.com", "NYG", "NYG"), (24, "Commanders", "www.commanders.com", "WAS", "WAS"),
    (25, "Cardinals", "www.azcardinals.com", "ARI", "ARI"), (26, "49ers", "www.49ers.com", "SF", "SF"),
    (27, "Rams", "www.therams.com", "LA", "LAR"), (28, "Seahawks", "www.seahawks.com", "SEA", "SEA"),
    (29, "Buccaneers", "www.buccaneers.com", "TB", "TB"), (30, "Falcons", "www.atlantafalcons.com", "ATL", "ATL"),
    (31, "Panthers", "www.panthers.com", "CAR", "CAR"), (32, "Saints", "www.neworleanssaints.com", "NO", "NO"),
)
NV_TEAM = {nv: t for t, _, _, nv, _ in TEAMS}
SL_TEAM = {sl: t for t, _, _, _, sl in TEAMS}
NV_RELEASE = "https://api.github.com/repos/nflverse/nflverse-data/releases/tags/%s"
SLEEPER = "https://api.sleeper.app/v1/players/nfl"

# The roster page's table headings (read raw in SR.1 and SR.2) and the list each one is. Active/PUP cannot play a game: it is PUP here.
SECTIONS = {
    "active": "", "reserve/injured": "IR", "injured reserve": "IR", "reserve/injured; designated for return": "IRD",
    "reserve/injured - designated for return": "IRD", "reserve/injured designated for return": "IRD",
    "physically unable to perform": "PUP", "reserve/physically unable to perform": "PUP", "active/physically unable to perform": "PUP",
    "reserve/pup": "PUP", "non-football injury": "NFI", "reserve/non-football injury": "NFI", "reserve/non-football illness": "NFI",
    "non-football illness": "NFI", "active/non-football injury": "NFI", "suspended by commissioner": "SUS", "reserve/suspended by commissioner": "SUS",
    "reserve/suspended": "SUS", "suspended": "SUS", "practice squad": "PS", "practice squad/injured": "PSI", "practice squad injured": "PSI",
    "reserve/retired": "RTD", "reserve/left squad": "LFT", "reserve/military": "MIL", "exempt/commissioner permission": "EXM",
    "reserve/exempt": "EXM", "exempt": "EXM", "practice squad/exempt": "PSX", "practice squad exempt": "PSX",
    # found in SR.2's first full run (2026-10-25): the Browns' and Cowboys' words for IRD, the 17th squad man of the International Pathway,
    # the Commanders' "DEV" (the league's code for the practice squad) and the Seahawks' commissioner's exempt list
    "reserve/designated to return": "IRD", "practice squad/international": "PS", "dev": "PS", "commissioner exempt": "EXM",
}
KR_LABELS, PR_LABELS = ("KR", "KOR"), ("PR",)       # the team charts' rows of the returners (the Ravens and five more say KOR)
FAMILY = {"QB": "QB", "HB": "BACK", "FB": "BACK", "WR": "WR", "TE": "TE", "LT": "OL", "LG": "OL", "C": "OL", "RG": "OL", "RT": "OL",
          "LEDG": "FRONT", "REDG": "FRONT", "DT": "FRONT", "SAM": "FRONT", "MIKE": "FRONT", "WILL": "FRONT",
          "CB": "DB", "FS": "DB", "SS": "DB", "K": "K", "P": "P", "LS": "LS"}
# Open choices resolved by balancing a team's men (D-153: "by the side of the first free row"): the first is taken on a tie
OPEN = {"EDGE?": ("LEDG", "REDG"), "T?": ("LT", "RT"), "G?": ("LG", "RG"), "OL?": ("LG", "RG", "LT", "RT", "C"), "S?": ("FS", "SS"),
        "OLB?": ("SAM", "WILL"), "ILB?": ("MIKE", "WILL"), "LB?": ("MIKE", "WILL", "SAM")}
OPEN_FAMILY = {"EDGE?": "FRONT", "T?": "OL", "G?": "OL", "OL?": "OL", "S?": "DB", "OLB?": "FRONT", "ILB?": "FRONT", "LB?": "FRONT"}


SAFETY_WORDS = ("S", "FS", "SS", "SAF")
NICKEL_ROWS = ("NB", "NCB", "N", "NICKEL", "DB")          # nickel rows and a generic DB row never move a safety (NX-D1's rule, D-157)


def family(code):
    return FAMILY.get(code) or OPEN_FAMILY.get(code)


# ----- names -----

_SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def name_key(name: str) -> str:
    """A name for matching across sources: no accents, no punctuation, no Jr./III, lower case."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold()
    s = re.sub(r"[.,'\u2019`]", "", s).replace("-", " ")             # "Kenneth Murray, Jr." is Kenneth Murray Jr.
    words = [w for w in s.split() if w not in _SUFFIX]
    return " ".join(words)


def loose_key(name: str) -> str:
    """First initial and last word: Josh Uche and Joshua Uche, Juju Brents and Julius Brents."""
    words = name_key(name).split()
    return (words[0][:1] + " " + words[-1]) if len(words) >= 2 else " ".join(words)


class Matcher:
    """Find a man of one source among the names of another: exact key first, then the loose key when it names one man only."""

    def __init__(self, names, last_name=False):
        self.exact, self.loose, self.last, self.by_last = {}, {}, last_name, {}
        for n in names:
            self.exact.setdefault(name_key(n), n)
            self.loose.setdefault(loose_key(n), []).append(n)
            words = name_key(n).split()
            if words:
                self.by_last.setdefault(words[-1], []).append(n)

    def find(self, name):
        k = name_key(name)
        if k in self.exact:
            return self.exact[k]
        hits = self.loose.get(loose_key(name), [])
        if len(hits) == 1:
            return hits[0]
        if self.last:                 # comparisons within one team only: Vega and Olaivavega Ioane, Hollywood and Marquise Brown, Dru and Andru Phillips
            words = k.split()
            hits = self.by_last.get(words[-1], []) if words else []
            return hits[0] if len(hits) == 1 else None
        return None


# ----- fetching, gently -----

class Fetcher:
    def __init__(self, folder: Path, pause: float, offline: bool):
        self.folder, self.pause, self.offline = folder, pause, offline
        self.folder.mkdir(parents=True, exist_ok=True)
        self.robots, self.last, self.log = {}, 0.0, []

    def allowed(self, url):
        p = urllib.parse.urlparse(url)
        base = "%s://%s" % (p.scheme, p.netloc)
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                raw = self._request(base + "/robots.txt").decode("utf-8", "replace")
                (self.folder / ("robots_%s.txt" % p.netloc)).write_bytes(raw.encode("utf-8"))
                rp.parse(raw.splitlines())
            except urllib.error.HTTPError as e:
                if 400 <= e.code < 500:
                    rp.parse([])                          # no robots.txt: nothing is disallowed
                else:
                    rp = None
            except Exception:
                rp = None                                 # the host cannot be reached: fetch nothing from it
            self.robots[base] = rp
        rp = self.robots[base]
        return rp is not None and rp.can_fetch("nfl4-roster-update", url)

    def _request(self, url, accept="*/*"):
        wait = self.pause - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        finally:
            self.last = time.monotonic()

    def get(self, name, url, accept="*/*", robots=True):
        """The bytes of a page: the copy saved in this run's raw folder, else the network (robots.txt first). None when not read."""
        path = self.folder / name
        if path.exists() and path.stat().st_size > 0:
            return path.read_bytes()
        if self.offline:
            self.log.append("%s: not saved, offline" % name)
            return None
        if robots and not self.allowed(url):
            self.log.append("%s: DISALLOWED by robots.txt %s" % (name, url))
            return None
        try:
            data = self._request(url, accept)
        except Exception as e:                            # noqa: BLE001 (every failure is reported, none stops the run)
            self.log.append("%s: ERROR %s %s" % (name, e, url))
            return None
        path.write_bytes(data)
        self.log.append("%s: %d bytes %s" % (name, len(data), url))
        return data


# ----- the team pages -----

def _text(cell):
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def _slug(href):
    m = re.search(r"/players-roster/([^/?#]+)", href or "")
    return m.group(1) if m else ""


@dataclass
class PageMan:
    section: str
    name: str
    slug: str
    number: str
    word: str
    age: str = ""


def parse_roster_page(page: bytes):
    """[PageMan] from a team's roster page, every table in page order. Empty cells are kept (B-X149): the cells are read by their place."""
    t = page.decode("utf-8", "replace")
    out = []
    for block in t.split('class="nfl-o-roster"')[1:]:
        head = re.search(r'nfl-o-roster__title-status">(.*?)</span>', block, flags=re.S)
        table = re.search(r"<tbody>(.*?)</tbody>", block, flags=re.S)
        if not head or not table:
            continue
        section = _text(head.group(1))
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(1), flags=re.S):
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.S)
            if len(cells) < 3:
                continue
            link = re.search(r'nfl-o-roster__player-name[^>]*>\s*<a href="([^"]*)"[^>]*>(.*?)</a>', cells[0], flags=re.S)
            if link:
                name, slug = _text(link.group(2)), _slug(link.group(1))
            else:
                title = re.search(r'title="([^"]+)"', cells[0])
                name, slug = (_html.unescape(title.group(1)).strip() if title else _text(cells[0])), _slug(cells[0])
            number = _text(cells[1]) or "-"
            out.append(PageMan(section, name, slug, number if number.isdigit() else "-", _text(cells[2]).upper(),
                               _text(cells[5]) if len(cells) > 5 else ""))
    return out


def parse_depth_page(page: bytes):
    """(as of, [(table, label, [[(slug, name), ...] per tier]])) from a team's depth chart page."""
    t = page.decode("utf-8", "replace")
    asof = re.search(r"\(As of ([^)]*)\)", t)
    rows = []
    for m in re.finditer(r'<table summary="([^"]*)"(.*?)</table>', t, flags=re.S):
        body = re.search(r"<tbody>(.*?)</tbody>", m.group(2), flags=re.S)
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1) if body else "", flags=re.S):
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.S)
            if not cells:
                continue
            tiers = [[(_slug(h), _text(n)) for h, n in re.findall(r'<a href="([^"]*)"[^>]*>(.*?)</a>', c, flags=re.S)] for c in cells[1:]]
            rows.append((m.group(1), _text(cells[0]).upper(), tiers))
    return (asof.group(1).strip() if asof else ""), rows


# ----- nflverse and Sleeper -----

def nv_asset(fetch: Fetcher, tag: str, name: str, save: str):
    listing = fetch.get("nflverse_%s_release.json" % tag, NV_RELEASE % tag, accept="application/vnd.github+json")
    if not listing:
        return None
    for a in json.loads(listing).get("assets", []):
        if a.get("name") == name:
            return fetch.get(save, a["url"], accept="application/octet-stream")
    fetch.log.append("nflverse %s: no asset %s" % (tag, name))
    return None


def parse_nv_roster(data: bytes):
    """{team: [row]} of each man's latest week in nflverse's roster file."""
    last = {}
    for r in csv.DictReader(io.StringIO(data.decode("utf-8", "replace"))):
        k = r.get("gsis_id") or (r.get("team"), r.get("full_name"))
        if k not in last or int(r.get("week") or 0) >= int(last[k].get("week") or 0):
            last[k] = r
    out = {}
    for r in last.values():
        t = NV_TEAM.get(r.get("team"))
        if t:
            out.setdefault(t, []).append(r)
    return out


def parse_nv_depth(data: bytes):
    """{team: (snapshot time, [row])}: the newest snapshot of each team."""
    text = gzip.decompress(data).decode("utf-8", "replace") if data[:2] == b"\x1f\x8b" else data.decode("utf-8", "replace")
    best = {}
    for r in csv.DictReader(io.StringIO(text)):
        t = NV_TEAM.get(r.get("team"))
        if not t:
            continue
        dt = r.get("dt", "")
        if t not in best or dt > best[t][0]:
            best[t] = (dt, [r])
        elif dt == best[t][0]:
            best[t][1].append(r)
    return best


def parse_sleeper(data: bytes):
    """({team: [player]}, [teamless player]) of Sleeper's feed."""
    teams, free = {}, []
    for p in json.loads(data).values():
        if p.get("sport") not in (None, "nfl") or not p.get("full_name"):
            continue
        t = SL_TEAM.get(p.get("team") or "")
        if t:
            teams.setdefault(t, []).append(p)
        elif p.get("active"):
            free.append(p)
    return teams, free


# ----- positions (D-152, D-153) -----

def map_chart(abb: str, grp: str):
    """A row of nflverse's depth chart (an ESPN-style chart with sides) as a Madden position, None for a role row (H, KR, PR)."""
    a, three4 = abb.upper(), "3-4" in grp
    direct = {"QB": "QB", "RB": "HB", "HB": "HB", "FB": "FB", "WR": "WR", "SWR": "WR", "LWR": "WR", "RWR": "WR", "TE": "TE",
              "LT": "LT", "LG": "LG", "C": "C", "RG": "RG", "RT": "RT", "LCB": "CB", "RCB": "CB", "NB": "CB", "CB": "CB", "DB": "CB",
              "FS": "FS", "SS": "SS", "S": "S?", "PK": "K", "K": "K", "P": "P", "LS": "LS"}
    if a in direct:
        return direct[a]
    if three4:
        return {"NT": "DT", "LDE": "DT", "RDE": "DT", "DE": "DT", "DT": "DT", "LDT": "DT", "RDT": "DT", "WLB": "LEDG", "LOLB": "LEDG",
                "SLB": "REDG", "ROLB": "REDG", "OLB": "EDGE?", "LILB": "MIKE", "RILB": "WILL", "MLB": "MIKE", "ILB": "ILB?"}.get(a)
    return {"LDE": "LEDG", "RDE": "REDG", "DE": "EDGE?", "LDT": "DT", "RDT": "DT", "DT": "DT", "NT": "DT", "WLB": "WILL", "MLB": "MIKE",
            "SLB": "SAM", "LILB": "MIKE", "RILB": "WILL", "ILB": "ILB?", "OLB": "OLB?", "LB": "LB?"}.get(a)


def map_label(label: str, three4: bool):
    """A row label of a team's own depth chart; None when the label does not say the position (DL, a role row)."""
    a = label.upper().replace(" ", "")
    table = {"QB": "QB", "RB": "HB", "HB": "HB", "FB": "FB", "WR": "WR", "X": "WR", "Z": "WR", "SLOT": "WR", "TE": "TE", "Y": "TE",
             "LT": "LT", "LG": "LG", "C": "C", "RG": "RG", "RT": "RT", "T": "T?", "G": "G?", "OL": "OL?", "LOT": "LT", "ROT": "RT", "N": "CB",
             "LDE": "DT" if three4 else "LEDG", "RDE": "DT" if three4 else "REDG", "DE": "DT" if three4 else "EDGE?", "EDGE": "EDGE?",
             "RUSH": "EDGE?", "JACK": "EDGE?", "DT": "DT", "NT": "DT", "NG": "DT", "LDT": "DT", "RDT": "DT",
             "SAM": "REDG" if three4 else "SAM", "SLB": "REDG" if three4 else "SAM", "WLB": "LEDG" if three4 else "WILL",
             "WILL": "WILL", "MLB": "MIKE", "MIKE": "MIKE", "MIK": "MIKE", "ILB": "ILB?", "LILB": "MIKE", "RILB": "WILL",
             "OLB": "EDGE?" if three4 else "OLB?", "LOLB": "LEDG" if three4 else "OLB?", "ROLB": "REDG" if three4 else "OLB?",
             "LB": "ILB?" if three4 else "LB?", "CB": "CB", "LCB": "CB", "RCB": "CB", "NB": "CB", "NCB": "CB", "NICKEL": "CB",
             "DB": "CB", "FS": "FS", "SS": "SS", "S": "S?", "K": "K", "PK": "K", "P": "P", "LS": "LS"}
    return table.get(a)


def map_word(word: str, three4: bool):
    """A position word of a roster page, of nflverse's roster or of Sleeper as a Madden position (or an open choice), None when unknown."""
    a = (word or "").upper().replace(" ", "")
    table = {"QB": "QB", "RB": "HB", "HB": "HB", "FB": "FB", "WR": "WR", "TE": "TE", "LT": "LT", "RT": "RT", "LG": "LG", "RG": "RG",
             "T": "T?", "OT": "T?", "G": "G?", "OG": "G?", "C": "C", "OL": "OL?", "G/T": "OL?", "T/G": "OL?", "C/G": "OL?", "G/C": "OL?",
             "DE": "EDGE?", "EDGE": "EDGE?", "DE/OLB": "EDGE?", "OLB/DE": "EDGE?", "DT": "DT", "NT": "DT", "DL": "DT", "DT/DE": "DT",
             "OLB": "EDGE?" if three4 else "OLB?", "ILB": "ILB?" if three4 else "MIKE", "MLB": "MIKE", "LB": "ILB?" if three4 else "LB?",
             "CB": "CB", "DB": "CB", "NB": "CB", "FS": "FS", "SS": "SS", "S": "S?", "SAF": "S?", "K": "K", "PK": "K", "P": "P", "LS": "LS"}
    return table.get(a)


def word_family(word: str):
    code = map_word(word, False)
    return family(code) if code else None


# ----- one team -----

@dataclass
class Built:
    team: RF.Team
    notes: list = field(default_factory=list)       # how each position was decided when the sources disagreed
    source: str = "official"
    chart_date: str = ""


def build_team(t, page_men, depth, nv_rows, nv_chart, sl_rows):
    """The team from its own pages (membership, lists, numbers, the team's chart) and nflverse and Sleeper (the positions with sides)."""
    notes = []
    snap, chart_rows = nv_chart if nv_chart else ("", [])
    three4 = any("3-4" in r.get("pos_grp", "") for r in chart_rows)
    asof, own_rows = depth if depth else ("", [])
    chart_by = {}                                      # name key -> best (rank, grp, abb)
    for r in chart_rows:
        k = name_key(r.get("player_name", ""))
        rank = int(r.get("pos_rank") or 99)
        if k not in chart_by or rank < chart_by[k][0]:
            chart_by[k] = (rank, r.get("pos_grp", ""), r.get("pos_abb", ""))
    chart_match = Matcher([r.get("player_name", "") for r in chart_rows])
    nv_match = Matcher([r.get("full_name", "") for r in nv_rows])
    nv_by = {r.get("full_name", ""): r for r in nv_rows}
    sl_match = Matcher([p.get("full_name", "") for p in sl_rows])
    sl_by = {p.get("full_name", ""): p for p in sl_rows}
    own_by_slug = {}                                   # slug -> [(tier, row index, label)]
    roles = {"KR": [], "PR": []}
    for ri, (table, label, tiers) in enumerate(own_rows):
        for ti, cell in enumerate(tiers):
            for slug, name in cell:
                if label in KR_LABELS + PR_LABELS:
                    roles["KR" if label in KR_LABELS else "PR"].append((ti, ri, slug, name))
                elif table != "Special Teams" or label in ("K", "PK", "P", "LS"):
                    own_by_slug.setdefault(slug, []).append((ti, ri, label))

    men, decided, open_men = [], {}, []
    for i, pm in enumerate(page_men):
        status = SECTIONS.get(re.sub(r"\s+", " ", pm.section.strip().casefold()))
        if status is None:
            notes.append("UNKNOWN LIST %r for %s" % (pm.section, pm.name))
            status = "?" + pm.section
        official_family = word_family(pm.word)
        candidates = []
        hit = chart_match.find(pm.name)
        if hit:
            rank, grp, abb = chart_by[name_key(hit)]
            candidates.append(("nflverse chart %s" % abb, map_chart(abb, grp)))
        for ti, ri, label in sorted(own_by_slug.get(pm.slug, [])):
            candidates.append(("team chart %s" % label, map_label(label, three4)))
        nv = nv_match.find(pm.name)
        if nv:
            candidates.append(("nflverse roster %s" % nv_by[nv].get("depth_chart_position"), map_word(nv_by[nv].get("depth_chart_position", ""), three4)))
        sl = sl_match.find(pm.name)
        if sl:
            candidates.append(("Sleeper %s" % sl_by[sl].get("depth_chart_position"), map_word(sl_by[sl].get("depth_chart_position") or "", three4)))
            candidates.append(("Sleeper %s" % sl_by[sl].get("position"), map_word(sl_by[sl].get("position") or "", three4)))
        candidates.append(("team page %s" % pm.word, map_word(pm.word, three4)))
        choice, why = None, ""
        safety = pm.word in SAFETY_WORDS
        for source, code in candidates:
            if safety and source.split()[-1] in NICKEL_ROWS:
                continue                  # D-157: the nickel is a role; a man his team calls a safety stays a safety (Kyle Hamilton, Jalen Pitre)
            if code and (official_family is None or family(code) == official_family):
                choice, why = code, source
                break
        if choice is None:
            notes.append("NO POSITION for %s (team page %r)" % (pm.name, pm.word))
            choice = "?"
        first = next(((s, c) for s, c in candidates if c), None)
        if first and family(first[1]) != family(choice):
            notes.append("%s: the team page says %s, %s says %s: kept %s (the team's word decides the group)" % (
                pm.name, pm.word, first[0], first[1], choice))
        own = sorted(own_by_slug.get(pm.slug, []))
        nv_rank = chart_by[name_key(hit)][0] if hit else 99
        if own and family(map_label(own[0][2], three4) or choice) in (family(choice), None):
            depth_key = (0, own[0][0], own[0][1], i)
        elif hit:
            depth_key = (1, nv_rank, 0, i)
        else:
            depth_key = (2, 0, 0, i)
        number = pm.number
        if number == "-" and nv and (nv_by[nv].get("jersey_number") or "").isdigit():
            number = nv_by[nv]["jersey_number"]
        man = RF.Man(choice, number, pm.name, status)
        men.append((depth_key, man))
        if choice in OPEN:
            open_men.append((depth_key, man))
        decided[pm.slug or pm.name] = man
    # open choices: by the side or the row with the fewest men of the team so far, starters (charted) first (D-153)
    counts = {}
    for _, m in men:
        if m.pos in RF.MADDEN:
            counts[(m.status == "", m.pos)] = counts.get((m.status == "", m.pos), 0) + 1
    for _, m in sorted(open_men, key=lambda r: (r[1].status != "", r[0])):
        options = OPEN[m.pos]
        best = min(options, key=lambda p: (counts.get((m.status == "", p), 0), options.index(p)))
        counts[(m.status == "", best)] = counts.get((m.status == "", best), 0) + 1
        m.pos = best
    men = agreed_starters_first(men, chart_rows, sl_rows, three4, asof, notes)      # D-177: the fresher sources' starters
    order = {p: n for n, p in enumerate(RF.MADDEN)}
    active = sorted([r for r in men if r[1].status == ""], key=lambda r: (order.get(r[1].pos, 99), r[0]))
    squad = [r for r in men if r[1].status == "PS"]
    rest = [r for r in men if r[1].status not in ("", "PS")]
    team = RF.Team(men=[m for _, m in active] + [m for _, m in squad] + [m for _, m in rest])
    active_names = {m.name for m in team.active()}
    by_slug_name = {pm.slug: pm.name for pm in page_men}
    for role in ("KR", "PR"):
        names = []
        for ti, ri, slug, name in sorted(roles[role]):
            real = by_slug_name.get(slug)
            if real in active_names and real not in names:
                names.append(real)
            elif real is None or real not in active_names:
                notes.append("the team chart's %s %s is not on the active roster" % (role, name))
        if not names:                                     # the team chart has no such row: nflverse's chart
            for r in sorted((r for r in chart_rows if r.get("pos_abb") == role), key=lambda r: int(r.get("pos_rank") or 99)):
                real = Matcher(active_names).find(r.get("player_name", ""))
                if real and real not in names:
                    names.append(real)
        team.roles[role] = names
    return Built(team, notes, "official", asof or snap)


CHART_SKIP_ROWS = ("NB", "NCB", "DB", "H", "KR", "PR")        # roles and nickel rows, not starting places


def _top(ranked: dict) -> dict:
    """{position: [(rank, name)]} -> {position: [names]} of the STARTERS[pos] smallest ranks (a tie at the last rank keeps every tied man)."""
    out = {}
    for pos, rows in ranked.items():
        k = RF.STARTERS.get(pos, 1)
        rows = sorted(set(rows))
        if len(rows) > k:
            rows = [r for r in rows if r[0] <= rows[k - 1][0]]
        out[pos] = [n for _r, n in rows]
    return out


def chart_starters(chart_rows, three4: bool) -> dict:
    """nflverse's newest snapshot (an ESPN-style chart): the starters of each position, by rank."""
    ranked = {}
    for r in chart_rows:
        if r.get("pos_abb", "").upper() in CHART_SKIP_ROWS:
            continue
        pos = map_chart(r.get("pos_abb", ""), "3-4" if three4 else r.get("pos_grp", ""))
        for p in (OPEN[pos] if pos in OPEN else (pos,) if pos else ()):
            ranked.setdefault(p, []).append((int(r.get("pos_rank") or 99), r.get("player_name", "")))
    return _top(ranked)


def sleeper_starters(sl_rows, three4: bool) -> dict:
    """Sleeper's depth chart order: the starters of each position."""
    ranked = {}
    for p in sl_rows:
        if not p.get("depth_chart_order") or not p.get("depth_chart_position"):
            continue
        pos = map_chart(p["depth_chart_position"], "3-4" if three4 else "4-3")
        for q in (OPEN[pos] if pos in OPEN else (pos,) if pos else ()):
            ranked.setdefault(q, []).append((int(p["depth_chart_order"]), p.get("full_name", "")))
    return _top(ranked)


def agreed_starters_first(men, chart_rows, sl_rows, three4: bool, asof: str, notes: list):
    """D-177 (the tester's report of 2026-10-26: the Giants' page still started Jameis Winston a day after J.J. McCarthy was named the starter;
    47 such places in the file of 2026-10-25): a team's own depth chart page can lag a change of starter. Where nflverse's newest chart and
    Sleeper's depth chart BOTH name a man among a position's starters, and he is on the active roster at that position, he goes before the
    men the team's page put first. A man the two sources agree on at another position is only reported (the team's word decides the
    position, D-157). Returns `men` with new depth keys; every move is a note for the report."""
    if not chart_rows or not sl_rows:
        return men
    nv, sl = chart_starters(chart_rows, three4), sleeper_starters(sl_rows, three4)
    out = []
    by_pos = {}
    for key, m in men:
        if m.status == "":
            by_pos.setdefault(m.pos, []).append((key, m))
    moved = {}
    for pos, rows in by_pos.items():
        agreed = [n for n in nv.get(pos, []) if name_key(n) in {name_key(x) for x in sl.get(pos, [])}]
        if not agreed:
            continue
        keys = [name_key(n) for n in agreed]
        before = [m.name for _k, m in sorted(rows, key=lambda r: r[0])][:RF.STARTERS.get(pos, 1)]
        here = {name_key(m.name): m for _k, m in rows}
        first = [here[k] for k in keys if k in here]
        if first:
            for rank, m in enumerate(first):
                moved[id(m)] = (-1, rank, 0, 0)
            after = [m.name for m in first] + [n for n in before if name_key(n) not in keys]
            after = after[:RF.STARTERS.get(pos, 1)]
            if [name_key(n) for n in after] != [name_key(n) for n in before]:
                notes.append("%s starters %s (nflverse's chart and Sleeper agree; the team's page%s had %s)" % (
                    pos, "/".join(after), " of %s" % asof if asof else "", "/".join(before) or "nobody"))
        for k, n in zip(keys, agreed):
            if k not in here:
                notes.append("%s: nflverse's chart and Sleeper start %s, who is not an active %s here (kept as the team's page has him)" % (
                    pos, n, pos))
    for key, m in men:
        out.append((moved.get(id(m), key), m))
    return out


SNAP_LOW, SNAP_HIGH = 0.40, 0.70     # D-177: a starter under 40 percent of the snaps in each of the last two games, a backup over 70 in each
SNAP_SIDES = {"LT": ("RT",), "RT": ("LT",), "LG": ("RG",), "RG": ("LG",), "LEDG": ("REDG",), "REDG": ("LEDG",), "FS": ("SS",), "SS": ("FS",),
              "SAM": ("MIKE", "WILL"), "MIKE": ("SAM", "WILL"), "WILL": ("SAM", "MIKE")}     # the other side a man may take (roster_model)
SNAP_NEVER = ("K", "P", "LS", "FB")


def parse_snaps(data: bytes) -> dict:
    """{team: {name key: {week: share of the team's offensive or defensive snaps}}} of nflverse's snap counts (regular season)."""
    out = {}
    for r in csv.DictReader(io.StringIO(data.decode("utf-8", "replace"))):
        if r.get("game_type") != "REG":
            continue
        t = NV_TEAM.get(r.get("team"))
        if not t:
            continue
        share = max(float(r.get("offense_pct") or 0), float(r.get("defense_pct") or 0))
        out.setdefault(t, {}).setdefault(name_key(r.get("player", "")), {})[int(r.get("week") or 0)] = share
    return out


def snap_starters(team: RF.Team, snaps: dict, notes: list) -> list:
    """D-177: who actually plays. In the team's last two games (nflverse's snap counts), a starter who played in both under SNAP_LOW of the
    snaps while a man of the same position (or its other side, SNAP_SIDES) who is not a starter played over SNAP_HIGH in both gives that man his
    place: the man starts, at the starter's position, and the starter follows him. A man absent from a game (injured, inactive) is never moved
    either way: the team's starter when healthy stays the starter (a short injury is not modelled; a reserve list is). Returns the weeks read."""
    weeks = sorted({w for man in snaps.values() for w in man})[-2:]
    if len(weeks) < 2:
        return weeks

    def every(m, test):
        v = snaps.get(name_key(m.name), {})
        return all(w in v and test(v[w]) for w in weeks)

    for pos in RF.MADDEN:
        if pos in SNAP_NEVER:
            continue
        active = team.active()
        k = RF.STARTERS.get(pos, 1)
        starters = [m for m in active if m.pos == pos][:k]
        taken = {id(m) for p in RF.MADDEN for m in [x for x in active if x.pos == p][:RF.STARTERS.get(p, 1)]}
        for s in starters:
            if not every(s, lambda x: x < SNAP_LOW):
                continue
            pool = [m for m in active if id(m) not in taken and (m.pos == pos or m.pos in SNAP_SIDES.get(pos, ()))]
            best = [m for m in pool if every(m, lambda x: x > SNAP_HIGH)]
            if not best:
                continue
            c = max(best, key=lambda m: sum(snaps[name_key(m.name)][w] for w in weeks))
            was = c.pos
            team.men.remove(c)
            c.pos = pos
            team.men.insert(team.men.index(s), c)
            taken.add(id(c))
            notes.append("%s %s starts before %s (snaps in weeks %s: %s and %s)%s" % (
                pos, c.name, s.name, "/".join(map(str, weeks)),
                "/".join("%d%%" % round(100 * snaps[name_key(c.name)][w]) for w in weeks),
                "/".join("%d%%" % round(100 * snaps[name_key(s.name)][w]) for w in weeks),
                "" if was == pos else "; he moves from %s" % was))
    return weeks


def team_from_nflverse(t, nv_rows, nv_chart, sl_rows):
    """--no-official, or a team whose page could not be read: nflverse's statuses give the lists (ACT and INA active, DEV squad, RES reserve)."""
    kind = {"ACT": "Active", "INA": "Active", "DEV": "Practice Squad", "RES": "Reserve/Injured"}
    page_men = [PageMan(kind[r["status"]], r["full_name"], "", r.get("jersey_number") or "-", r.get("position", ""))
                for r in nv_rows if r.get("status") in kind]
    built = build_team(t, page_men, None, nv_rows, nv_chart, sl_rows)
    built.source = "nflverse"
    return built


# ----- comparisons, changes, free agents -----

def compare(t, built, nv_rows, sl_rows):
    """Lines of the report: who one source has and the other has not."""
    out = []
    mine_active = [m.name for m in built.team.active()]
    mine_squad = [m.name for m in built.team.squad()]
    mine_all = [m.name for m in built.team.men]
    nv_active = [r["full_name"] for r in nv_rows if r.get("status") in ("ACT", "INA")]
    nv_squad = [r["full_name"] for r in nv_rows if r.get("status") == "DEV"]
    # Sleeper keeps long-retired men tied to a team (2026-10-25: Ali Marpet, Ha Ha Clinton-Dix) and "Duplicate Player" rows: only its active men count
    # ("Inactive" is Sleeper's word for a man on a reserve list, so the other direction compares with all of its men)
    sl_all = [p["full_name"] for p in sl_rows if p.get("status") == "Active" and "duplicate" not in p["full_name"].casefold()]
    sl_any = [p["full_name"] for p in sl_rows if "duplicate" not in p["full_name"].casefold()]

    def diff(a, b):
        mb, plain = Matcher(b, last_name=True), Matcher(b)
        lasts = {}
        for n in a:
            words = name_key(n).split()
            lasts[words[-1] if words else ""] = lasts.get(words[-1] if words else "", 0) + 1

        def found(n):                 # the last-name match only when the name is the only one of its last name on both sides
            words = name_key(n).split()
            return plain.find(n) is not None or (lasts.get(words[-1] if words else "", 0) == 1 and mb.find(n) is not None)
        return sorted(n for n in a if not found(n))

    for label, a, b in (("active here, not active in nflverse", mine_active, nv_active), ("active in nflverse, not active here", nv_active, mine_active),
                        ("squad here, not squad in nflverse", mine_squad, nv_squad), ("squad in nflverse, not squad here", nv_squad, mine_squad),
                        ("on the team here, not on it in Sleeper", mine_all, sl_any), ("on the team in Sleeper, not here", sl_all, mine_all)):
        d = diff(a, b)
        if d:
            out.append("  %s (%d): %s" % (label, len(d), ", ".join(d)))
    return out


def read_previous(text: str):
    """{name key: (team, list, group, name)} of a rosters.txt of format 1 or 2 (RET and role lines left out)."""
    out = {}
    for line in text.replace("\r\n", "\n").split("\n"):
        m = re.match(r"\s*T(\d{2})P\d{2,3}\s*=\s*(.*)$", line)
        if not m:
            continue
        words = m.group(2).split(";")[0].split()                        # SR.7: "; age N; seasons N" is not part of the name
        status = words[0] if words and words[0] in RF.STATUSES else ""
        if status:
            words = words[1:]
        if len(words) < 3 or words[0] == "RET":
            continue
        group = RF.GROUP_OF.get(words[0], words[0])
        name = " ".join(words[2:])
        out.setdefault(name_key(name), (int(m.group(1)), status, group, name))
    return out


def changes(previous, teams):
    now = {}
    for t, team in teams.items():
        for m in team.men:
            now.setdefault(name_key(m.name), (t, m.status, RF.GROUP_OF.get(m.pos, m.pos), m.name))
    lines = []
    for k, (t, s, g, n) in sorted(now.items(), key=lambda r: (r[1][0], r[1][3])):
        if k not in previous:
            lines.append("T%02d new: %s (%s %s)" % (t, n, s or "active", g))
            continue
        pt, ps, pg, _ = previous[k]
        if pt != t:
            lines.append("T%02d from T%02d: %s (%s)" % (t, pt, n, s or "active"))
        elif ps != s:
            lines.append("T%02d %s: %s -> %s" % (t, n, ps or "active", s or "active"))
        if pg != g and pg not in ("RET",):
            lines.append("T%02d %s: group %s -> %s" % (t, n, pg, g))
    for k, (pt, ps, pg, n) in sorted(previous.items(), key=lambda r: (r[1][0], r[1][3])):
        if k not in now:
            lines.append("T%02d gone: %s (was %s %s)" % (pt, n, ps or "active", pg))
    return lines


def age_on(player: dict, today: str) -> str:
    """The age on the file's date from Sleeper's birth date. Sleeper's own "age" field is not kept up (2026-10-25: Tyreek Hill, born 1994-03-01,
    "age" 31); "-" when the feed has no birth date."""
    try:
        born = _dt.date.fromisoformat(player.get("birth_date") or "")
        day = _dt.date.fromisoformat(today)
    except ValueError:
        return "-"
    return str(day.year - born.year - ((day.month, day.day) < (born.month, born.day)))


def add_ages(teams, nv_rows, sl_teams, today: str) -> int:
    """SR.7 (Q-078, D-167): every man's age on the file's date and his NFL seasons before this one, from nflverse's roster table (birth_date,
    rookie_year or years_exp), else Sleeper's feed (birth_date, years_exp): his own team's row by name, then by the loose name when it names one man,
    then the league's when only one man has the name. A man no source dates keeps no age (the game then makes one). Returns how many got an age."""
    def entries(rows, name_field, rookie):
        for r in rows:
            name = r.get(name_field) or ""
            born = r.get("birth_date") or ""
            if not name or not born:
                continue
            age = age_on({"birth_date": born}, today)
            if age == "-":
                continue
            seasons = rookie(r)
            yield name, int(age), seasons

    def nv_rookie(r):
        year = r.get("rookie_year") or r.get("entry_year") or ""
        return SEASON - int(year) if str(year).isdigit() else None

    def sl_rookie(r):
        exp = r.get("years_exp")
        return int(exp) if isinstance(exp, int) or str(exp or "").isdigit() else None

    exact, loose, league = {}, {}, {}
    for source, rows_of, field, rookie in (("nv", nv_rows, "full_name", nv_rookie), ("sl", sl_teams, "full_name", sl_rookie)):
        for t, rows in rows_of.items():
            for name, age, seasons in entries(rows, field, rookie):
                for table, key in ((exact, (source, t, name_key(name))), (loose, (source, t, loose_key(name))), (league, (source, name_key(name)))):
                    table.setdefault(key, set()).add((age, seasons))
    given = 0
    for t, team in teams.items():
        for m in team.men:
            found = None
            for source in ("nv", "sl"):
                for table, key in ((exact, (source, t, name_key(m.name))), (loose, (source, t, loose_key(m.name))), (league, (source, name_key(m.name)))):
                    hits = table.get(key, set())
                    if len(hits) == 1:
                        found = next(iter(hits))
                        break
                if found:
                    break
            if found and RF.AGE_LOW <= found[0] <= RF.AGE_HIGH:
                m.age = found[0]
                seasons = found[1]
                m.seasons = seasons if seasons is not None and 0 <= seasons <= m.age - RF.AGE_LOW else None
                given += 1
    return given


FA_LINE = re.compile(r"^\s*F(\d{1,4})\s*=\s*(\S+)\s+(\d{1,2}|-)\s+(.+?)\s*$")


# D-169 (the owner 2026-10-26: "it doesn't have all free agents example is kicker"): the whole pool of real free agents, from nflverse's players table.
# D-185 (a tester 2026-10-27: "Make sure all free agents are completely accurate. Do a full audit and correct any inaccuracies."; the owner: "claude
# should search the internet to do the audit if needed to ensure player and field position accuracy"). The audit of 2026-10-27
# (work\tester_1027\FREE_AGENTS_AUDIT_1027.md) found the matching by names wrong: a loose key (first initial and last name) took another man's Sleeper
# record (Daxton Hill of the Bengals was "free" through a teamless D. Hill; ages of 35 and 38 for men of 28 and 22), the old list's men were kept
# without a check (Ogbo Okoronkwo of the 49ers, a man retired since), and nflverse's weekly roster, the third source, was not read (20 men on a team's
# active roster, practice squad or reserve list in its newest week). And the file said only OL, DL, LB and S, so every free lineman became a left
# tackle in a franchise. So now:
#   * a man is matched across the sources by his league ID first (nflverse's gsis_id, which Sleeper and nflverse's roster carry), by his exact name
#     only when no ID links him, never by the loose key;
#   * a free agent is a man of nflverse's players table, not retired (FA_GONE), of this season or the one before (or the one before that while he
#     is in the news, D-172), on NO team in any of the three sources (the teams' own pages, nflverse's newest weekly roster, Sleeper), and active
#     and teamless in Sleeper (the second source must agree); a man of the old list or of the previous rosters is kept only by the same rule;
#   * his position is the league's own (nflverse's GSIS word), made a Madden position (D-152) by his newest depth chart row of his family
#     (nflverse's charts of 2026, 2025 and 2024: the side of a tackle, a guard or an edge, the role of a backer, free or strong safety); a word
#     no row settles takes one of its positions by a hash of the name (no draw), and the report lists those men;
#   * the age is the linked record's birth date.
FA_POSITION = {"QB": "QB", "RB": "RB", "HB": "RB", "FB": "FB", "WR": "WR", "TE": "TE",
               "OT": "OL", "T": "OL", "G": "OL", "OG": "OL", "C": "OL", "OL": "OL",
               "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "EDGE": "DL",
               "LB": "LB", "ILB": "LB", "MLB": "LB", "OLB": "LB",
               "CB": "CB", "S": "S", "SAF": "S", "FS": "S", "SS": "S", "K": "K", "P": "P", "LS": "LS"}
FA_GONE = ("RET", "RSR")                        # nflverse: retired, reserve/retired
FA_SEASONS = 2                                  # this season and the one before
# D-172 (the owner 2026-10-26: "Justin Tucker is still a free agent and not listed"): a man whose last season was the one before last (Tucker: released in
# May 2025, unsigned all of 2025) is a free agent too when Sleeper has news of him within FA_NEWS_DAYS of the file's date; one gone quiet that long is
# out of the league (2026-10-25: 64 such men kept, 449 left out). Neither source marks every retirement, so known retirees are settled by hand.
FA_OLDER_SEASONS = 3
FA_NEWS_DAYS = 365
FA_ON_TEAM = ("ACT", "RES", "INA", "DEV", "PUP", "EXE", "SUS", "NWT", "RSN")   # D-185: nflverse's weekly statuses of a man on a team's lists
# D-185: the reserve lists (injured reserve and the others), which a team's roster page does not always show (the Bears' page of 2026-10-27 lacks Dallis
# Flowers, on their injured reserve since 2026-08-07): nflverse's week decides. For the active roster and the practice squad (ACT, INA, DEV) the team's
# page of today is newer than the week's list (the Colts released Thomas Morstead from their squad after week 7): a man the page was read for and
# does not list is free again.
FA_RESERVE = ("RES", "PUP", "SUS", "EXE", "NWT", "RSN")
FA_SETTLEMENTS = Path(__file__).resolve().parent / "free_agent_settlements.txt"
# D-185: the file's positions are the 22 of Madden NFL (D-152) in this order; the older family words still read in the game (real_names)
FA_ORDER = ("QB", "HB", "FB", "WR", "TE", "LT", "LG", "C", "RG", "RT", "LEDG", "REDG", "DT", "SAM", "MIKE", "WILL", "CB", "FS", "SS", "K", "P", "LS")
FA_WORD_CODE = {"RB": "HB", "OL": "OL?", "DL": "DT", "LB": "LB?", "S": "S?"}      # an old line's family word as a code to settle
_CB_WORDS, _SAFETY_WORDS = ("CB",), ("S", "SAF", "FS", "SS")


def read_fa_rules(text: str) -> tuple:
    """free_agent_settlements.txt: "X001 = name | why | source". The why "free: ..." makes a man a free agent although a source still has him on a
    list (a release the sources have not caught up with), "position XX: ..." gives his field position (D-185); any other why means he is never a free
    agent (a retiree, a man on a list no source shows). Returns (never: set of name keys, free: set, positions: {name key: code})."""
    never, free, positions = set(), set(), {}
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip().startswith("#") or "=" not in line:
            continue
        parts = [p.strip() for p in line.split("=", 1)[1].split("|")]
        if not parts[0]:
            continue
        why = (parts[1] if len(parts) > 1 else "").casefold()
        found = re.match(r"position\s+([a-z]{1,4})\b", why)
        if found and found.group(1).upper() in FA_ORDER:
            positions[name_key(parts[0])] = found.group(1).upper()
        elif why.startswith("free"):
            free.add(name_key(parts[0]))
        else:
            never.add(name_key(parts[0]))
    return never, free, positions


def read_fa_settlements(text: str) -> set:
    """name keys of the men free_agent_settlements.txt says are never free agents."""
    return read_fa_rules(text)[0]


FA_HEADER = """# NFL Football 4 freeagents, format 1.
# These are the real NFL free agents a new franchise starts with: every player who was on an NFL roster this season or last season, has not retired,
# and is on no team's roster, practice squad or reserve list when the list was made.
# Each line is an ID, an equals sign, the position, the age and the name. The age is a number, or a minus sign when it is not known.
# The positions are the 22 of a real roster: QB, HB, FB, WR, TE, LT, LG, C, RG, RT, LEDG and REDG (the left and right edge), DT, SAM, MIKE and WILL
# (the strong-side, middle and weak-side linebacker), CB, FS, SS, K, P and LS. The words RB, OL, DL, LB and S of older files are read too.
# In the first season of a new franchise these players are the free agents of F9, Franchise, free agents, and the ones a practice squad may sign;
# the game makes up players only for a position this list has too few of. The game gives them no real ratings: a free agent's rating is made by the game.
# A new season: replace the lines, change the VERSION line, save the file, then choose Reload in the Customize item of the F9 menu.
# Write an ID = off to leave a player out. A name has 1 to 30 characters, with no comma and no semicolon.
# Delete the whole file to get the original list back. The names are facts, used descriptively.
# They are not endorsed by the teams or the league.
# Sources: nflverse's players table, weekly rosters and depth charts (CC BY 4.0, github.com/nflverse), Sleeper's player feed, the teams' own roster pages.""".split("\n")


def players_table(out: Path, offline: bool):
    """nflverse's players table (players.csv) of this run: the saved copy in <out>/raw, else one request (none when offline); None when it is missing."""
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))      # (-I leaves the script's folder out of the path)
    import update_surnames as US
    saved = out / "raw" / "nflverse_players.csv"
    if saved.exists():
        return saved.read_bytes()
    if offline:
        return None
    req = urllib.request.Request(US.URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    saved.parent.mkdir(parents=True, exist_ok=True)
    saved.write_bytes(data)
    return data


def week_teams(data: bytes | None) -> dict:
    """D-185: {gsis_id: (team, status)} of nflverse's weekly roster file, its newest week, for the men a team keeps on a list (FA_ON_TEAM)."""
    if not data:
        return {}
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig", "replace"))))
    weeks = [int(r.get("week") or 0) for r in rows if (r.get("week") or "").isdigit()]
    newest = max(weeks) if weeks else 0
    return {r["gsis_id"]: (r.get("team") or "", r.get("status") or "") for r in rows
            if r.get("gsis_id") and (r.get("status") or "") in FA_ON_TEAM and int(r.get("week") or 0) == newest}


def chart_codes(sources) -> dict:
    """D-185: {gsis_id: Madden code (or an open code)} of each man's newest depth chart row in nflverse's charts: the newer layout (dt, pos_abb, pos_grp;
    2026 and 2025) and the older one (week, depth_position; 2024). `sources` are the files' bytes, newest season first; a season's row wins over an
    older season's. Return rows (KR, PR) and the holder say nothing of a position."""
    out: dict = {}
    for data in sources:
        if not data:
            continue
        text = gzip.decompress(data).decode("utf-8", "replace") if data[:2] == b"\x1f\x8b" else data.decode("utf-8-sig", "replace")
        best: dict = {}
        for r in csv.DictReader(io.StringIO(text)):
            gid = r.get("gsis_id") or ""
            if not gid or gid in out:
                continue
            if "pos_abb" in r:
                abb, when, group = (r.get("pos_abb") or "").upper(), r.get("dt") or "", r.get("pos_grp") or ""
            else:
                abb, when, group = (r.get("depth_position") or "").upper(), "%03d" % int(r.get("week") or 0), ""
            if abb in ("KR", "PR", "H", ""):
                continue
            code = map_chart(abb, group)
            if code is not None and (gid not in best or when > best[gid][0]):
                best[gid] = (when, code)
        for gid, (_when, code) in best.items():
            out[gid] = code
    return out


def _settle_open(code: str, name: str) -> str:
    """An open code (T?, EDGE?, S?, ...) with nothing to settle it: one of its positions by a hash of the name (the same on every run, no draw)."""
    import hashlib
    options = OPEN.get(code)
    if not options:
        return code
    return options[int.from_bytes(hashlib.sha256(name_key(name).encode("utf-8")).digest()[:4], "big") % len(options)]


def fa_position(nv_word: str, sl_word: str, chart: str | None, name: str):
    """D-185: (Madden position, how) of a free agent: the league's word (nflverse's GSIS position; Sleeper's when nflverse says only DB or nothing),
    its side or role from his newest chart row of the same family (a corner stays a corner and a safety a safety, a back stays a halfback or a
    fullback), else a hash of the name among the word's positions. None when no source names a position."""
    word = (nv_word or "").upper()
    if not word or word == "DB" or map_word(word, False) is None:
        word = (sl_word or "").upper() or word
    code = map_word(word, False)
    if code is None and chart is None:
        return None
    if code is None:
        code = chart
    fam = family(code)
    if chart is not None and family(chart) == fam:
        if fam == "DB" and word in _CB_WORDS and chart != "CB":
            chart = "CB"                                  # a corner on a safety's row stays a corner (NX-D1's rule, D-157)
        if fam == "DB" and word in _SAFETY_WORDS and chart == "CB":
            chart = None                                  # a safety on a nickel or a corner's row stays a safety
        if fam == "BACK" and code == "FB" and chart != "FB":
            chart = None                                  # a fullback charted as a halfback is still a fullback (a back charted FB is one)
    if chart is not None and family(chart) == fam:
        how = "chart"
        if chart not in OPEN:
            code = chart                                  # the row names the side or the role
        elif code in OPEN:
            both = [p for p in OPEN[code] if p in OPEN[chart]]
            code = both[0] if len(both) == 1 else (chart if set(OPEN[chart]) <= set(OPEN[code]) else code)
        # an open row (S, OLB, DE) never makes a specific word (FS, an edge) less exact
    else:
        how = "word"
    if code in OPEN:
        return _settle_open(code, name), how + ", side or role by hash"
    return code, how


def _sleeper_links(sl_all) -> tuple:
    """({gsis_id: record}, {name key: [records]}) of Sleeper's feed (every man, with or without a team, active or not)."""
    by_id, by_name = {}, {"#born": {}}
    for p in sl_all:
        gid = (p.get("gsis_id") or "").strip()
        if gid:
            by_id[gid] = p
        by_name.setdefault(name_key(p.get("full_name") or ""), []).append(p)
        if p.get("birth_date"):
            by_name["#born"].setdefault(p["birth_date"], []).append(p)        # "#born" is no name key (a key has no "#")
    return by_id, by_name


def same_man(matcher, name: str):
    """D-185: the name of `matcher` that is this man: the exact key, or the loose key only when one first name starts with the other (Matt and Matthew
    Judon, Dax and Daxton Hill), never another man of the same initial (a teamless D. Hill is not Daxton Hill)."""
    hit = matcher.find(name)
    if hit is None or name_key(hit) == name_key(name):
        return hit
    a, b = name_key(name).split()[0], name_key(hit).split()[0]
    return hit if a.startswith(b) or b.startswith(a) else None


def sleeper_ids(data: bytes | None) -> dict:
    """D-185: {gsis_id: Sleeper player ID} of nflverse's roster file (every row of the season, the cut men too)."""
    if not data:
        return {}
    return {r["gsis_id"]: r["sleeper_id"] for r in csv.DictReader(io.StringIO(data.decode("utf-8-sig", "replace")))
            if r.get("gsis_id") and r.get("sleeper_id")}


def _names_of(r: dict) -> list:
    """The names a man of nflverse's players table goes by: his display name, and his first names (common, football) with his last name."""
    last = (r.get("last_name") or "").strip()
    names = [(r.get("display_name") or "").strip()]
    for first in (r.get("football_name"), r.get("common_first_name"), r.get("first_name")):
        if first and last:
            names.append("%s %s" % (first.strip(), last))
    return [n for n in dict.fromkeys(names) if n]


def _sleeper_of(r: dict, by_id: dict, by_name: dict, sleeper_ids: dict, by_player: dict):
    """The Sleeper record of a man of nflverse's table: by his gsis_id, by the Sleeper ID nflverse's roster gives him, else by one exact name with
    the same birth date (or the only man of that name); None when nothing links him (never the loose key, D-185)."""
    gid = r.get("gsis_id") or ""
    if gid in by_id:
        return by_id[gid]
    if sleeper_ids.get(gid) in by_player:
        return by_player[sleeper_ids[gid]]
    for name in _names_of(r):
        rows = [p for p in by_name.get(name_key(name), []) if not (p.get("gsis_id") or "").strip() or p["gsis_id"].strip() == gid]
        born = [p for p in rows if p.get("birth_date") and p.get("birth_date") == r.get("birth_date")]
        if len(born) == 1:
            return born[0]
        near = [p for p in rows if _years_apart(p.get("birth_date"), r.get("birth_date")) <= 1]
        if len(near) == 1:
            return near[0]                                # the sources' birth dates differ a little (Gabe Davis 1999-03-01 and 1999-04-01;
        if len(rows) == 1 and (word_family(rows[0].get("position") or "") in (None, word_family(r.get("position") or ""))   # 1999-01-01 is
                               or (r.get("position") or "").upper() == "DB") and _years_apart(rows[0].get("birth_date"), r.get("birth_date")) < 9:
            return rows[0]                                # nflverse's "not known"); the only man of the name, of the same family
    born_on = r.get("birth_date") or ""
    last = name_key(r.get("last_name") or "")
    if born_on and not born_on.endswith("-01-01") and last:
        same = [p for p in by_name.get("#born", {}).get(born_on, []) if name_key(p.get("last_name") or "") == last]
        if len(same) == 1:
            return same[0]                                # a nickname the tables do not share (Carlos and Boogie Basham, born 1997-12-16)
    return None


def _years_apart(a, b) -> float:
    """Years between two birth dates; 0 when one is missing or is nflverse's January 1st that means not known."""
    try:
        if not a or not b or b.endswith("-01-01") or a.endswith("-01-01"):
            return 0.0
        return abs((_dt.date.fromisoformat(a) - _dt.date.fromisoformat(b)).days) / 365.25
    except ValueError:
        return 0.0


def free_agent_pool(nv_players: bytes | None, on_team, sl_free, today: str, sl_all=None, nv_week=None, charts=None, notes=None,
                    sleeper_ids=None, read_pages=None) -> list:
    """[(Madden position, age, name)] of D-185's rule, sorted by position then name; [] without the players table. `on_team` is a Matcher of the names on
    the teams' pages and in Sleeper's teams; `sl_all` every Sleeper record (default `sl_free`); `nv_week` week_teams(); `charts` chart_codes();
    `notes` a list for the men whose position a hash settled."""
    if not nv_players:
        return []
    from nfl4.extras.real_names import name_problem
    sl_all = list(sl_all) if sl_all is not None else list(sl_free)
    by_id, by_name = _sleeper_links(sl_all)
    by_player = {str(p.get("player_id")): p for p in sl_all if p.get("player_id")}
    nv_week = nv_week or {}
    charts = charts or {}
    settled, free_anyway, placed = (read_fa_rules(FA_SETTLEMENTS.read_bytes().decode("utf-8")) if FA_SETTLEMENTS.exists() else (set(), set(), {}))
    news_since = (_dt.datetime.fromisoformat(today) - _dt.timedelta(days=FA_NEWS_DAYS)).timestamp() * 1000
    read_pages = set(read_pages or ())
    out, seen = [], set()
    for r in csv.DictReader(io.StringIO(nv_players.decode("utf-8-sig"))):
        try:
            last = int(r.get("last_season") or 0)
        except ValueError:
            continue
        name = (r.get("display_name") or "").strip()
        if last < SEASON - FA_OLDER_SEASONS + 1 or (r.get("status") or "") in FA_GONE or not name or name_problem(name):
            continue
        week = nv_week.get(r.get("gsis_id") or "")
        if week is not None and name_key(name) not in free_anyway and (week[1] in FA_RESERVE or NV_TEAM.get(week[0]) not in read_pages):
            continue                                  # D-185: on a team's list in nflverse's newest week
        if any(same_man(on_team, n) for n in _names_of(r)) or name_key(name) in seen or name_key(name) in settled:
            continue
        sl = _sleeper_of(r, by_id, by_name, sleeper_ids or {}, by_player)
        if sl is None or sl.get("team") or not sl.get("active"):
            continue                                  # Sleeper has him on a team, retired, or does not know him: the second source must agree
        if same_man(on_team, sl.get("full_name") or ""):
            continue                                  # (the name the teams' pages use: Dax Hill for Daxton Hill)
        if last < SEASON - FA_SEASONS + 1 and float(sl.get("news_updated") or 0) < news_since:
            continue                                  # out a whole season and no news for a year (D-172)
        found = fa_position(r.get("position") or "", sl.get("position") or "", charts.get(r.get("gsis_id") or ""), name)
        if found is None:
            continue
        code, how = found
        if name_key(name) in placed:
            code, how = placed[name_key(name)], "settled"     # the maintainer's web search (free_agent_settlements.txt)
        if notes is not None and "hash" in how:
            notes.append("%s: %s, %s (no depth chart row settles it)" % (name, code, r.get("position")))
        age = age_on(sl, today)                           # Sleeper's birth date first (D-169), nflverse's when it has none
        if age == "-" and not (r.get("birth_date") or "").endswith("-01-01"):
            age = age_on({"birth_date": r.get("birth_date")}, today)
        if week is not None and notes is not None:
            notes.append("%s: on the %s list of %s in nflverse's week, not on that team's page today: free" % (name, week[1], week[0]))
        seen.add(name_key(name))
        out.append((code, age, name))
    out.sort(key=lambda row: (FA_ORDER.index(row[0]), name_key(row[2])))
    return out


def refresh_free_agents(old_text, previous, teams, sl_free, sl_teams, today, nv_players=None, nv_week=None, charts=None, sl_all=None, reasons=None,
                        notes=None, sl_ids=None, read_pages=None):
    """free_agents.txt again. With nflverse's players table (D-185): exactly the men of `free_agent_pool`; a man of the old list keeps his ID and is
    written with the pool's position, age and spelling; a man of the old list who is not in the pool any more is left out (`reasons` gets why);
    a man of the previous rosters or of the old list whom nflverse's table does not know at all stays only when Sleeper has exactly one active,
    teamless man of his name with news within FA_NEWS_DAYS. New men get new IDs after the old ones. Without the table (a failed read) the old list
    stays, less the men now on a team."""
    on_names = []
    for team in teams.values():
        for m in team.men:
            on_names.append(m.name)
    for rows in sl_teams.values():
        for p in rows:
            on_names.append(p["full_name"])
    on_team = Matcher(on_names)
    on_exact = {name_key(n) for n in on_names}
    reasons = {} if reasons is None else reasons
    header, kept, removed, top = list(FA_HEADER), [], [], 0
    old = []
    for line in old_text.replace("\r\n", "\n").split("\n"):
        m = FA_LINE.match(line)
        if m:
            top = max(top, int(m.group(1)))
            old.append((int(m.group(1)), m.group(2), m.group(3), m.group(4)))
    if not nv_players:
        free_match = Matcher([p["full_name"] for p in sl_free])
        free_by = {p["full_name"]: p for p in sl_free}
        for ident, pos, age, name in old:
            if name_key(name) in on_exact:
                removed.append(name)
                reasons[name] = "on a team"
                continue
            hit = free_match.find(name)
            if hit and age_on(free_by[hit], today) != "-":
                age = age_on(free_by[hit], today)
            kept.append((ident, pos, age, name))
        body = header + ["", "VERSION = season %d, as of %s" % (SEASON, today)]
        body += ["F%03d = %s %s %s" % row for row in kept]
        return "\n".join(body) + "\n", removed, []
    sl_all = list(sl_all) if sl_all is not None else list(sl_free) + [p for rows in sl_teams.values() for p in rows]
    pool = free_agent_pool(nv_players, on_team, sl_free, today, sl_all, nv_week, charts, notes, sl_ids, read_pages)
    pool_by = {name_key(n): (pos, age, n) for pos, age, n in pool}
    pool_match = Matcher([n for _p, _a, n in pool])
    known_nv = Matcher([n for r in csv.DictReader(io.StringIO(nv_players.decode("utf-8-sig"))) for n in _names_of(r)])
    _by_id, by_name = _sleeper_links(sl_all)
    news_since = (_dt.datetime.fromisoformat(today) - _dt.timedelta(days=FA_NEWS_DAYS)).timestamp() * 1000
    settled = read_fa_settlements(FA_SETTLEMENTS.read_bytes().decode("utf-8")) if FA_SETTLEMENTS.exists() else set()

    def sleeper_only(name: str):
        """(position, age) of a man nflverse does not know, when Sleeper has exactly one active, teamless man of the name in the news; else None."""
        if same_man(known_nv, name) or name_key(name) in on_exact or same_man(on_team, name) or name_key(name) in settled:
            return None
        rows = by_name.get(name_key(name), [])
        if len(rows) != 1 or rows[0].get("team") or not rows[0].get("active") or float(rows[0].get("news_updated") or 0) < news_since:
            return None
        found = fa_position("", rows[0].get("position") or "", None, name)
        return (found[0], age_on(rows[0], today)) if found else None

    used, id_of = set(), {}
    for ident, pos, age, name in old:
        hit = same_man(pool_match, name)
        k = name_key(hit) if hit else None
        if k in pool_by and k not in used:
            p, a, spelled = pool_by[k]
            kept.append((ident, p, a, spelled))
            used.add(k)
            id_of[k] = ident
            continue
        if k in used:
            removed.append(name)
            reasons[name] = "the same man as F%03d %s (one man written twice)" % (id_of[k], pool_by[k][2])
            continue
        alone = sleeper_only(name)
        if alone is not None and name_key(name) not in used:
            kept.append((ident, alone[0], alone[1], name))
            used.add(name_key(name))
            continue
        removed.append(name)
        reasons[name] = ("on a team" if name_key(name) in on_exact or same_man(on_team, name) else
                         "not a free agent in the sources (signed, retired, out of the league, or not linked to a real record)")
    added = []
    for k, (_pt, _ps, pg, name) in sorted(previous.items(), key=lambda r: (r[1][0], r[1][3])):
        if k in used or pg not in RF.SPOKEN and pg not in FA_POSITION:
            continue
        if same_man(pool_match, name) and name_key(same_man(pool_match, name)) in used:
            continue
        alone = sleeper_only(name)
        if alone is None:
            continue
        top += 1
        kept.append((top, alone[0], alone[1], name))
        added.append(name)
        used.add(k)
    for pos, age, name in pool:
        if name_key(name) in used:
            continue
        top += 1
        kept.append((top, pos, age, name))
        added.append(name)
        used.add(name_key(name))
    body = header + ["", "VERSION = season %d, as of %s" % (SEASON, today)]
    body += ["F%03d = %s %s %s" % (i, pos, age, name) for i, pos, age, name in kept]
    return "\n".join(body) + "\n", removed, added


# ----- settlements and game-day elevations -----

SETTLEMENTS = Path(__file__).resolve().parent / "roster_settlements.txt"
_SETTLE = re.compile(r"^\s*(S\d{3,4})\s*=\s*T(\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*$")


def read_settlements(text: str):
    """[(ID, team, name, what, source)] of roster_settlements.txt: the maintainer's decisions after a web search (rule 0.8), each with its source."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        m = _SETTLE.match(line)
        if m and not line.lstrip().startswith("#"):
            out.append((m.group(1), int(m.group(2)), m.group(3), m.group(4).strip(), m.group(5)))
    return out


def apply_settlements(teams, settlements, notes):
    """A settlement puts a man on his real list ("active", "PS", "IR", ...) or takes him off a team whose page still lists him ("off").
    One that no longer finds its man is said in the report, so a stale decision is seen and removed."""
    for ident, t, name, what, source in settlements:
        team = teams.get(t)
        man = next((m for m in team.men if m.name.casefold() == name.casefold()), None) if team else None
        if man is None:
            notes.append("settlement %s no longer applies: T%02d has no %s (remove it from roster_settlements.txt)" % (ident, t, name))
            continue
        depth = re.fullmatch(r"depth\s+(\d{1,2})", what.casefold())
        if depth:                                   # D-177: the man's place in his position's depth order on the active roster (news settles it)
            n = int(depth.group(1))
            same = [m for m in team.men if m.status == "" and m.pos == man.pos]
            if man.status != "" or not 1 <= n <= len(same):
                notes.append("settlement %s: %s is not an active man with a depth %d (check it)" % (ident, man.name, n))
                continue
            if same.index(man) + 1 == n:
                notes.append("settlement %s is already true: the sources have %s at depth %d (remove it)" % (ident, man.name, n))
                continue
            team.men.remove(man)
            same.remove(man)
            team.men.insert(team.men.index(same[n - 1]) if n - 1 < len(same) else team.men.index(same[-1]) + 1, man)
        elif what.casefold() == "off":
            team.men.remove(man)
            for role in RF.ROLES:
                team.roles[role] = [n for n in team.roles[role] if n != man.name]
        else:
            status = "" if what.casefold() == "active" else what.upper()
            if status not in ("",) + RF.STATUSES:
                notes.append("settlement %s: unknown list %r" % (ident, what))
                continue
            man.status = status
            if status:
                for role in RF.ROLES:
                    team.roles[role] = [n for n in team.roles[role] if n != man.name]
        notes.append("settled %s: T%02d %s is %s (%s)" % (ident, t, man.name, what, source))


def return_elevations(teams, previous, notes):
    """A practice squad man elevated for a game day stays a squad man (NFL: he reverts after the game; at most 2 a game). A team page listing more
    than 53 active men on a game day shows its elevations as active: every active man who was on that team's squad in the previous checked file
    goes back to the squad (at most 2), and the report says so."""
    for t, team in teams.items():
        active = team.active()
        if len(active) <= RF.ACTIVE_MAX:
            continue
        back = [m for m in active if previous.get(name_key(m.name), (0, ""))[:2] == (t, "PS")][:2]
        for m in back:
            m.status = "PS"
            for role in RF.ROLES:
                team.roles[role] = [n for n in team.roles[role] if n != m.name]
            notes.append("T%02d %s: active on the page, on the squad in the previous file: a game-day elevation, back on the practice squad" % (t, m.name))


# ----- the run -----

def run(out: Path, offline: bool, official: bool, pause: float, today: str, previous_dir: Path = DATA):
    raw = out / "raw"
    fetch = Fetcher(raw, pause, offline)
    nv_ros = nv_asset(fetch, "rosters", "roster_%d.csv" % SEASON, "nflverse_roster_%d.csv" % SEASON)
    nv_dep = nv_asset(fetch, "depth_charts", "depth_charts_%d.csv.gz" % SEASON, "nflverse_depth_charts_%d.csv.gz" % SEASON)
    sl = fetch.get("sleeper_players_nfl.json", SLEEPER, accept="application/json")
    nv_snaps = nv_asset(fetch, "snap_counts", "snap_counts_%d.csv" % SEASON, "nflverse_snap_counts_%d.csv" % SEASON)     # D-177
    snaps = parse_snaps(nv_snaps) if nv_snaps else {}
    nv_rows = parse_nv_roster(nv_ros) if nv_ros else {}
    nv_charts = parse_nv_depth(nv_dep) if nv_dep else {}
    sl_teams, sl_free = parse_sleeper(sl) if sl else ({}, [])
    teams, built, report = {}, {}, []
    for t, nick, host, _, _ in TEAMS:
        b = None
        if official:
            rp = fetch.get("T%02d_%s_roster.html" % (t, nick), "https://%s/team/players-roster/" % host, accept="text/html")
            dp = fetch.get("T%02d_%s_depth.html" % (t, nick), "https://%s/team/depth-chart/" % host, accept="text/html")
            page_men = parse_roster_page(rp) if rp else []
            if sum(1 for pm in page_men if SECTIONS.get(pm.section.strip().casefold()) == "") >= 40:
                b = build_team(t, page_men, parse_depth_page(dp) if dp else None, nv_rows.get(t, []), nv_charts.get(t), sl_teams.get(t, []))
            else:
                report.append("T%02d %s: the team's roster page could not be read (%d rows): nflverse gives the lists" % (t, nick, len(page_men)))
        if b is None:
            b = team_from_nflverse(t, nv_rows.get(t, []), nv_charts.get(t), sl_teams.get(t, []))
        snap_starters(b.team, snaps.get(t, {}), b.notes)                # D-177: who played the most snaps in the last two games
        teams[t], built[t] = b.team, b
    previous_text = (previous_dir / "rosters.txt").read_bytes().decode("utf-8")
    previous = read_previous(previous_text)
    settle_notes = []
    apply_settlements(teams, read_settlements(SETTLEMENTS.read_bytes().decode("utf-8")) if SETTLEMENTS.exists() else [], settle_notes)
    return_elevations(teams, previous, settle_notes)
    aged = add_ages(teams, nv_rows, sl_teams, today)                    # SR.7 (D-167): the real ages and seasons
    failures, warnings = RF.check(teams)
    men = sum(len(team.men) for team in teams.values())
    if not snaps:
        warnings.append("nflverse's snap counts could not be read: the starters are the charts' only (D-177)")
    if men and aged < 0.95 * men:
        warnings.append("only %d of %d men have an age (the sources' birth dates are missing)" % (aged, men))
    warnings.extend(n for n in settle_notes if "no longer applies" in n or "unknown list" in n)
    for t in sorted(built):
        for note in built[t].notes:
            (failures if note.startswith(("UNKNOWN LIST", "NO POSITION")) else warnings).append("T%02d: %s" % (t, note))
    for t, team in teams.items():
        for m in team.men:
            if m.status.startswith("?"):
                failures.append("T%02d: %s is on an unknown list %s" % (t, m.name, m.status[1:]))
    # the sources against each other: a team whose lists differ by more than 10 men is a broken read, not a day's moves
    for t, nick, _, _, _ in TEAMS:
        lines = compare(t, built[t], nv_rows.get(t, []), sl_teams.get(t, []))
        big = [l for l in lines if int(re.search(r"\((\d+)\)", l).group(1)) > 10 and "in Sleeper, not here" not in l]
        if big and nv_rows:
            failures.append("T%02d %s: the sources differ by more than 10 men in one list (%s)" % (t, nick, "; ".join(l.split(":")[0].strip() for l in big)))
        if lines:
            report.append("T%02d %s (%s, chart %s):" % (t, nick, built[t].source, built[t].chart_date or "-"))
            report.extend(lines)
    change_lines = changes(previous, teams)
    version = "season %d, as of %s" % (SEASON, today)
    text = RF.render(version, teams)
    v2, parsed, problems = RF.parse(text)
    if problems or RF.render(v2, parsed) != text:
        failures.append("the written file does not read back the same (%s)" % problems[:3])
    try:
        nv_players = players_table(out, offline)
    except (OSError, urllib.error.URLError) as exc:
        nv_players = None
        warnings.append("nflverse's players table could not be read (%s): the free agents are the previous list's" % exc)
    if nv_players is None:
        warnings.append("no nflverse players table: the free agents are the previous list's (D-169)")
    # D-185: the third source (nflverse's newest weekly roster), the free agents' last depth chart rows (2026, 2025, 2024) and every Sleeper record
    older_charts = [nv_asset(fetch, "depth_charts", "depth_charts_%d.csv" % season, "nflverse_depth_charts_%d.csv" % season)
                    for season in (SEASON - 1, SEASON - 2)] if nv_players is not None else []
    sl_all = [p for p in json.loads(sl).values() if p.get("sport") in (None, "nfl") and p.get("full_name")] if sl else None
    fa_reasons, fa_notes = {}, []
    fa_text, fa_removed, fa_added = refresh_free_agents((previous_dir / "free_agents.txt").read_bytes().decode("utf-8"), previous, teams, sl_free, sl_teams,
                                                        today, nv_players, nv_week=week_teams(nv_ros), charts=chart_codes([nv_dep] + older_charts),
                                                        sl_all=sl_all, reasons=fa_reasons, notes=fa_notes, sl_ids=sleeper_ids(nv_ros),
                                                        read_pages={t for t in built if built[t].source == "official"})
    if nv_players is not None and not nv_ros:
        warnings.append("nflverse's weekly roster could not be read: the free agents are checked against the teams' pages and Sleeper only (D-185)")
    fa_counts = {}
    for line in fa_text.split("\n"):
        m = FA_LINE.match(line)
        if m:
            fa_counts[m.group(2)] = fa_counts.get(m.group(2), 0) + 1
    for word, least in (("K", 3), ("P", 3), ("LS", 2), ("QB", 5), ("CB", 20), ("WR", 20)):
        if nv_players is not None and fa_counts.get(word, 0) < least:
            failures.append("free agents: only %d %s (a broken read of the players table?)" % (fa_counts.get(word, 0), word))
    (out / "rosters.txt").write_bytes(text.encode("utf-8"))
    (out / "free_agents.txt").write_bytes(fa_text.encode("utf-8"))
    counts = ["T%02d %-10s active %2d squad %2d reserve %2d  KR %s  PR %s" % (
        t, nick, len(teams[t].active()), len(teams[t].squad()), len(teams[t].reserves()),
        "/".join(teams[t].roles["KR"][:2]) or "-", "/".join(teams[t].roles["PR"][:2]) or "-") for t, nick, *_ in TEAMS]
    rep = ["update_rosters.py, %s. Sources: %s." % (today, "the teams' own pages, nflverse, Sleeper" if official else "nflverse, Sleeper (the teams' pages switched off)"),
           "", "FAILURES (%d)" % len(failures)] + failures + ["", "WARNINGS (%d)" % len(warnings)] + warnings
    rep += ["", "TEAMS"] + counts + ["", "SETTLEMENTS AND GAME-DAY ELEVATIONS (%d)" % len(settle_notes)] + settle_notes
    rep += ["", "THE SOURCES COMPARED"] + report
    rep += ["", "CHANGES SINCE THE PREVIOUS FILE (%d)" % len(change_lines)] + change_lines
    rep += ["", "FREE AGENTS: %d left out: %s" % (len(fa_removed), "; ".join("%s (%s)" % (n, fa_reasons.get(n, "on a team")) for n in fa_removed)),
            "FREE AGENTS: %d added (on the previous rosters or in the real pool of D-169, on no team now, without a team in Sleeper): %s" % (
                len(fa_added), ", ".join(fa_added)),
            "FREE AGENTS BY POSITION: %s" % ", ".join("%s %d" % kv for kv in sorted(fa_counts.items())),
            "FREE AGENTS WHOSE SIDE OR ROLE A HASH SETTLED, AND MEN FREE BY TODAY'S TEAM PAGES (%d; D-185, check them): %s" % (len(fa_notes), "; ".join(fa_notes)),
            "", "FETCH LOG"] + fetch.log
    (out / "report.txt").write_bytes(("\n".join(rep) + "\n").encode("utf-8"))
    return failures, warnings, text, fa_text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="the folder of this run (default work\\rosters\\<date>)")
    ap.add_argument("--saved", help="read the pages saved in this run folder's raw folder; no network")
    ap.add_argument("--no-official", action="store_true", help="do not read the teams' own sites")
    ap.add_argument("--write", action="store_true", help="copy the files into game\\assets\\data when every check passes")
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between two requests (default 3)")
    ap.add_argument("--date", help="the date of the VERSION line (default today)")
    ap.add_argument("--previous", help="the folder of the last published rosters.txt and free_agents.txt (default: the game's assets/data folder)")
    a = ap.parse_args(argv)
    today = a.date or _dt.date.today().isoformat()
    out = Path(a.saved) if a.saved else Path(a.out) if a.out else NFL4 / "work" / "rosters" / today
    failures, warnings, text, fa_text = run(out, bool(a.saved), not a.no_official, a.pause, today, Path(a.previous) if a.previous else DATA)
    print("%d failures, %d warnings; report: %s" % (len(failures), len(warnings), out / "report.txt"))
    for f in failures[:20]:
        print("  FAIL", f)
    if a.write:
        if failures:
            print("NOT WRITTEN: the shipped files stay as they are.")
            return 1
        (DATA / "rosters.txt").write_bytes(text.encode("utf-8"))
        (DATA / "free_agents.txt").write_bytes(fa_text.encode("utf-8"))
        print("written:", DATA / "rosters.txt", DATA / "free_agents.txt")
        refresh_surnames(out, bool(a.saved), text, fa_text)
    return 1 if failures else 0


def refresh_surnames(out: Path, offline: bool, text: str, fa_text: str) -> None:
    """NX-L12 (SR.5, D-164): the surnames of real NFL players follow the rosters: nflverse's players table (saved in this run's raw folder, or one request)
    and the new files make nfl_surnames.txt (update_surnames.py's rule); a table that gives too few names leaves the shipped file as it is."""
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))      # (-I leaves the script's folder out of the path)
    import update_surnames as US
    saved = out / "raw" / "nflverse_players.csv"
    try:
        if saved.exists():
            data = saved.read_bytes()
        elif offline:
            print("nfl_surnames.txt: no saved players table, kept as it is")
            return
        else:
            req = urllib.request.Request(US.URL, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            saved.write_bytes(data)
        surnames, count, _counts = US.build_from(data, text, fa_text)
    except Exception as exc:                                  # noqa: BLE001 (the maintainer reads it)
        print("nfl_surnames.txt: kept as it is (%s)" % exc)
        return
    if count < US.MIN_COUNT:
        print("nfl_surnames.txt: kept as it is (only %d surnames)" % count)
        return
    (DATA / "nfl_surnames.txt").write_bytes(surnames.encode("utf-8"))
    print("written:", DATA / "nfl_surnames.txt", "(%d surnames)" % count)


if __name__ == "__main__":
    sys.exit(main())
