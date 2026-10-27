"""The newest real rosters read in the game from the NFL's own pages and converted to rosters.txt (nfl4 only, rule 0.13; CLAUDE.md 0.32, playbook
7.23; D-196). This is inspired by Jim Kitchen.

The owner on 0.16.9, with a tester's problem report (two tries of F9, get the latest rosters, each "WinHttpSendRequest failed with WinHTTP error
12002", a time-out asking raw.githubusercontent.com): "The game cannot download the rosters when it checks for updates. It thinks the rosters are on
github. The updater script must get rosters right from the nfl and convert into the game format to get the updated rosters."

So the game reads the same official pages the maintainer's script reads first (D-156): each team's own roster page and depth chart page on its NFL
club site (https://<team site>/team/players-roster/ and /team/depth-chart/), and converts each team with the script's own code (extras/roster_nfl.py:
the lists, the numbers, Madden's 22 positions from the team's chart and the page's word, the open sides balanced, the return roles). Then:
  * a man the base file (the player's, or a newer checked file of the game's GitHub page) has keeps its position while the page puts him in the
    same group, and its depth order (the team's page can lag the news, D-177); a new man gets the conversion's position and goes behind them;
  * the age is the page's Age, the seasons before this one the page's Exp less one ("R", a rookie: 0), or the player's file's seasons for a man it
    had (the maintainer's checked number);
  * a game-day elevation goes back to the practice squad (the script's return_elevations, against the player's file);
  * a man whose list or position word the conversion does not know (and the base file does not have) is left out, with a log line;
  * a team whose pages cannot be read, are not allowed by robots.txt, list fewer than 40 active men, or fail the game's checks (54 active men on a
    game day) stays as the base file has it (said and logged); with fewer than MIN_TEAMS teams read the NFL's pages count as not read;
  * the free agents follow: a man who is now on a team leaves the list, a man of the player's file who is on no team's pages now joins it with his
    position and age (released or not re-signed; the maintainer's audit of rule 0.34 stays the script's work).
The result passes the game's own checks (roster_file.check, the list loader) before anything is written (extras/franchise/rosters_flow.py).

Gently (the script's manners): robots.txt is read for each site and obeyed, every request names the game (data/web.USER_AGENT), at most WORKERS
sites are asked at once and each site gets its three requests one after the other. Nothing is kept but the converted files.
"""
from __future__ import annotations

import logging
import re
import threading
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from ..data import debuglog
from . import roster_file as RF
from . import roster_nfl as N

log = logging.getLogger("nfl4.extras")

SEASON = 2026
ROSTER_PAGE, DEPTH_PAGE, ROBOTS = "https://%s/team/players-roster/", "https://%s/team/depth-chart/", "https://%s/robots.txt"
ROBOTS_AGENT = "nfl4"
MIN_ACTIVE = 40          # a roster page with fewer active men was not read whole (the script's rule)
MIN_TEAMS = 24           # with fewer teams read from their pages the NFL's pages count as not read (a block, a new page layout)
WORKERS = 6
FA_LINE = re.compile(r"^\s*F(\d{1,4})\s*=\s*(\S+)\s+(\d{1,2}|-)\s+(.+?)\s*$")


@dataclass
class Live:
    teams: dict = field(default_factory=dict)        # team number -> RF.Team, every team (read or kept)
    read: list = field(default_factory=list)         # the teams read from their pages
    kept: list = field(default_factory=list)         # the teams kept as the player's file has them, with the reason
    notes: list = field(default_factory=list)
    stopped: bool = False


def version_of(today: str) -> str:
    return "season %d, as of %s" % (SEASON, today)


def _robots(fetch, host: str):
    """The site's robots.txt as a parser; a site with none allows everything; None when the site cannot be reached."""
    rp = urllib.robotparser.RobotFileParser()
    status, body = fetch(ROBOTS % host)
    if status == 200:
        rp.parse(body.decode("utf-8", "replace").splitlines())
    elif 400 <= status < 500:
        rp.parse([])
    else:
        return None
    return rp


def _page(fetch, url: str) -> bytes | None:
    status, body = fetch(url)
    return body if status == 200 else None


def _seasons(exp: str, previous_seasons):
    if previous_seasons is not None:
        return previous_seasons
    exp = (exp or "").strip().upper()
    if exp == "R":
        return 0
    return max(0, int(exp) - 1) if exp.isdigit() else None


def _with_ages(team: RF.Team, page_men, previous_ages: dict) -> None:
    by_name = {pm.name: pm for pm in page_men}
    for m in team.men:
        pm = by_name.get(m.name)
        before = previous_ages.get(N.name_key(m.name), (None, None))
        age = int(pm.age) if pm is not None and pm.age.isdigit() else before[0]
        m.age = age if age is not None and RF.AGE_LOW <= age <= RF.AGE_HIGH else None
        seasons = _seasons(pm.exp if pm is not None else "", before[1])
        if seasons is not None and m.age is not None and seasons > m.age - RF.AGE_LOW:
            seasons = None
        m.seasons = seasons


def fetch_team(fetch, host: str):
    """The pages of one team: (page_men, depth) or (None, reason). Network only, no conversion."""
    from ..data.web import WebError
    try:
        rp = _robots(fetch, host)
        if rp is None:
            return None, "the site could not be reached"
        urls = (ROSTER_PAGE % host, DEPTH_PAGE % host)
        if not all(rp.can_fetch(ROBOTS_AGENT, u) for u in urls):
            return None, "the site's robots.txt does not allow it"
        roster = _page(fetch, urls[0])
        if roster is None:
            return None, "the roster page was not sent"
        page_men = N.parse_roster_page(roster)
        active = sum(1 for pm in page_men if N.SECTIONS.get(pm.section.strip().casefold()) == "")
        if active < MIN_ACTIVE:
            return None, "the roster page has %d active men" % active
        depth_page = _page(fetch, urls[1])
        return (page_men, N.parse_depth_page(depth_page) if depth_page is not None else None), ""
    except WebError as exc:
        return None, "%s (%s)" % (exc.kind, exc.detail)


def fetch_pages(fetch, stop: threading.Event | None = None, workers: int = WORKERS) -> dict:
    """{team: ((page_men, depth) or None, reason)} of the 32 teams' own pages, WORKERS sites at a time; {} when stopped."""
    results: dict = {}

    def one(row):
        t, nick, host = row[0], row[1], row[2]
        if stop is not None and stop.is_set():
            return
        pages, reason = fetch_team(fetch, host)
        results[t] = (pages, reason)
        debuglog.event("rosters", "nfl_pages", logging.INFO, team=nick, read=pages is not None,
                       men=len(pages[0]) if pages is not None else 0, why=reason or None)

    with ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="nfl4-nfl-pages") as pool:
        list(pool.map(one, N.TEAMS))
    return {} if stop is not None and stop.is_set() else results


def keep_order(team: RF.Team, base: RF.Team | None) -> None:
    """The base file's depth order for the active men it has at the same position (the maintainer's rule: an injured starter stays the starter,
    only a reserve list moves him; a team's page can lag the news, D-177); the men new to a position come after them, in the chart's order."""
    if base is None:
        return
    rank = {}
    for i, m in enumerate(base.active()):
        rank.setdefault((N.name_key(m.name), m.pos), i)
    active = [m for m in team.men if m.status == ""]
    order = {p: n for n, p in enumerate(RF.MADDEN)}
    placed = sorted(enumerate(active), key=lambda im: (order.get(im[1].pos, 99), 0 if (N.name_key(im[1].name), im[1].pos) in rank else 1,
                                                      rank.get((N.name_key(im[1].name), im[1].pos), 0), im[0]))
    team.men = [m for _i, m in placed] + [m for m in team.men if m.status != ""]


def convert(pages: dict, base_text: str) -> Live:
    """Every team from its own pages, converted on `base_text` (the checked file the update starts from: its positions, depth order, ages and
    seasons are kept for the men it has); a team whose pages failed stays as the base has it. Nothing is written."""
    _version, base_teams, _problems = RF.parse(base_text)
    # a man is looked up on his own team first, then in the league only by a name that one man has (two Justin Jeffersons, a receiver and a
    # linebacker; Byron Murphy Jr. and Byron Murphy II have one key)
    counts: dict = {}
    for team in base_teams.values():
        for m in team.men:
            counts[N.name_key(m.name)] = counts.get(N.name_key(m.name), 0) + 1
    league = {N.name_key(m.name): m for team in base_teams.values() for m in team.men if counts[N.name_key(m.name)] == 1}
    live = Live()
    for t, nick, *_rest in N.TEAMS:
        got, reason = pages.get(t, (None, "not asked"))
        if got is None:
            if t in base_teams:
                live.teams[t] = base_teams[t]
                live.kept.append((t, reason))
            continue
        page_men, depth = got
        mine = dict(league)
        mine.update({N.name_key(m.name): m for m in (base_teams[t].men if t in base_teams else [])})
        built = N.build_team(t, page_men, depth, [], None, [], known={k: m.pos for k, m in mine.items()})
        team = built.team
        unknown = [m for m in team.men if m.pos not in RF.MADDEN or m.status.startswith("?")]
        for m in unknown:
            team.men.remove(m)
            for role in RF.ROLES:
                team.roles[role] = [n for n in team.roles.get(role, []) if n != m.name]
        live.notes.extend("T%02d: %s" % (t, n) for n in built.notes if not n.startswith(("UNKNOWN LIST", "NO POSITION")))
        live.notes.extend("T%02d: %s left out: his list or position on the team's page is not one the game knows" % (t, m.name) for m in unknown)
        keep_order(team, base_teams.get(t))
        _with_ages(team, page_men, {k: (m.age, m.seasons) for k, m in mine.items()})
        live.teams[t] = team
        live.read.append(t)
    if live.read:
        elevated: list = []
        N.return_elevations({t: live.teams[t] for t in live.read}, N.read_previous(base_text), elevated)
        live.notes.extend(elevated)
    # a team read from its pages that fails the game's checks (more than 53 active men on a game day, no kicker...) stays as the base has it:
    # one team's page of the moment never stops the others' update
    for _round in range(3):
        failures, _warnings = RF.check(live.teams)
        bad: dict = {}
        for line in failures:
            m = re.match(r"T(\d{2})\b", line)
            if m and int(m.group(1)) in live.read and int(m.group(1)) in base_teams:
                bad.setdefault(int(m.group(1)), line)
        if not bad:
            break
        for t, line in bad.items():
            live.teams[t] = base_teams[t]
            live.read.remove(t)
            live.kept.append((t, line))
    return live


def read_league(fetch, base_text: str, stop: threading.Event | None = None, workers: int = WORKERS) -> Live:
    """fetch_pages, then convert on `base_text`."""
    pages = fetch_pages(fetch, stop, workers)
    if stop is not None and stop.is_set():
        return Live(stopped=True)
    return convert(pages, base_text)


def same_men(a_text: str, b_text: str) -> bool:
    """The two rosters.txt texts list the same men in the same places (the VERSION line aside)."""
    def body(text):
        return [line for line in text.replace("\r\n", "\n").split("\n") if line.strip() and not line.lstrip().startswith(("#", "VERSION"))]
    return body(a_text) == body(b_text)


def free_agents(old_text: str, previous_text: str, teams: dict, version: str) -> tuple:
    """(the new free_agents.txt text, how many left, how many joined): the player's list with the men now on a team taken out and the men of his
    rosters file who are on no team now put in (their position and age from that file), the comments kept, the VERSION line the new one."""
    on_team = {N.name_key(m.name) for team in teams.values() for m in team.men}
    _v, previous_teams, _p = RF.parse(previous_text)
    lines, listed, numbers, left = [], set(), [], 0
    for line in old_text.replace("\r\n", "\n").split("\n"):
        if line.strip().upper().startswith("VERSION"):
            lines.append("VERSION = " + version)
            continue
        m = FA_LINE.match(line)
        if m:
            numbers.append(int(m.group(1)))
            key = N.name_key(m.group(4))
            if key in on_team:
                left += 1
                continue
            listed.add(key)
        lines.append(line)
    while lines and not lines[-1].strip():
        lines.pop()
    joined = 0
    number = max(numbers, default=0)
    for t in sorted(previous_teams):
        for man in previous_teams[t].men:
            key = N.name_key(man.name)
            if key in on_team or key in listed or man.status in ("RTD",):
                continue
            listed.add(key)
            number += 1
            joined += 1
            lines.append("F%03d = %s %s %s" % (number, man.pos, man.age if man.age is not None else "-", man.name))
    return "\n".join(lines) + "\n", left, joined
