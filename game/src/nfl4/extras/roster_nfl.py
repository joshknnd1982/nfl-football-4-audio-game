"""The NFL's own pages read and turned into the game's rosters (nfl4 only, rule 0.13; CLAUDE.md 0.32, playbook 7.23; D-153, D-157, D-177, D-196).
This is inspired by Jim Kitchen.

These are the official pages' readers and the conversion of one team into the game's positions (Madden's 22 positions, the lists, the numbers,
the return roles), first written for the maintainer's script game/tools/update_rosters.py (SR.2) and moved here unchanged in RC (D-196, the owner
on 0.16.9: "The game cannot download the rosters when it checks for updates. It thinks the rosters are on github. The updater script must get rosters
right from the nfl and convert into the game format"), so that the game's own "get the latest rosters" (extras/franchise/rosters_flow.py and
extras/roster_live.py) reads each team's own roster page and depth chart page and converts them exactly as the maintainer's script does. The script
imports every name from here; its other sources (nflverse, Sleeper, the snap counts) stay the maintainer's cross-checks.
"""
from __future__ import annotations

import html as _html
import re
import unicodedata
from dataclasses import dataclass, field

from . import roster_file as RF

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
    exp: str = ""            # RC (D-196): the page's Exp, his seasons with this one ("R": a rookie); the game's own update reads it


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
                               _text(cells[5]) if len(cells) > 5 else "", _text(cells[6]) if len(cells) > 6 else ""))
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
             "ED": "EDGE?", "EDGE/ILB": "EDGE?", "ILB/EDGE": "EDGE?", "EDGE/OLB": "EDGE?", "OLB/EDGE": "EDGE?",   # D-196: words of 2026-10-27's pages
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


def build_team(t, page_men, depth, nv_rows, nv_chart, sl_rows, known=None):
    """The team from its own pages (membership, lists, numbers, the team's chart) and nflverse and Sleeper (the positions with sides). `known`
    (D-196, the game's own update, which has no nflverse or Sleeper): {name key: position} of the player's checked file; a man it has keeps that
    position while the team's page puts him in the same group (a man who changed groups, and a new man, get the sources' position)."""
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
        kept = (known or {}).get(name_key(pm.name))     # D-196 (the game's own update): the checked file's position, when the group agrees
        if kept in RF.MADDEN and (official_family is None or family(kept) == official_family):
            choice, why = kept, "the checked file"
        for source, code in ([] if choice else candidates):
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
