"""The game's own "get the latest rosters" reads the NFL's pages (nfl4 only, rule 0.13; CLAUDE.md 0.32; RC, D-196). This is inspired by Jim Kitchen.

The owner on 0.16.9, with a tester's problem report (two tries, each a time-out asking GitHub, WinHTTP error 12002): "The game cannot download the
rosters when it checks for updates. It thinks the rosters are on github. The updater script must get rosters right from the nfl and convert into the
game format". The network is faked: a small NFL whose 32 club sites serve robots.txt, a roster page and a depth chart page in the layout of the real
ones (the readers are extras/roster_nfl.py, the maintainer's script's own), made from the shipped rosters.txt with the changes a test wants.

What is tested: a whole league read from the pages and converted (lists, numbers, ages, seasons, positions and depth order of the men the checked
file has); a signing, a release and a man put on injured reserve come through, and the free agents follow; GitHub blocked (the tester's network)
changes nothing; a team whose pages fail, are disallowed by robots.txt or fail a check stays as it was; with too few teams read, a newer checked file
of GitHub's is used, else the reason is said; the same men twice is "nothing newer"; the maintainer's script still reads with the moved code.
"""
import html
import re

import pytest

from nfl4.data.web import WebError
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF
from nfl4.extras import roster_live as L
from nfl4.extras import roster_nfl as N
from nfl4.extras.franchise import rosters_flow as F

SECTION = {"": "Active", "PS": "Practice Squad", "IR": "Reserve/Injured", "IRD": "Reserve/Injured; Designated for Return",
           "PUP": "Reserve/Physically Unable to Perform", "NFI": "Reserve/Non-Football Injury", "SUS": "Reserve/Suspended by Commissioner",
           "PSI": "Practice Squad/Injured", "RTD": "Reserve/Retired", "LFT": "Reserve/Left Squad", "MIL": "Reserve/Military",
           "EXM": "Exempt/Commissioner Permission", "PSX": "Practice Squad/Exempt"}
WORD = {"QB": "QB", "HB": "RB", "FB": "FB", "WR": "WR", "TE": "TE", "LT": "T", "RT": "T", "LG": "G", "RG": "G", "C": "C", "LEDG": "DE",
        "REDG": "DE", "DT": "DT", "SAM": "LB", "MIKE": "LB", "WILL": "LB", "CB": "CB", "FS": "S", "SS": "S", "K": "K", "P": "P", "LS": "LS"}
TODAY = "2026-11-03"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def roster_page(team: RF.Team) -> bytes:
    blocks = {}
    for m in team.men:
        exp = "R" if m.seasons == 0 else str(m.seasons + 1) if m.seasons is not None else ""
        cell = '<div class="nfl-o-roster__player-name"><a href="/team/players-roster/%s/">%s</a></div>' % (slug(m.name), html.escape(m.name))
        row = "<tr>" + "".join("<td>%s</td>" % c for c in (cell, m.number if m.number != "-" else "", WORD[m.pos], "6-2", "220",
                                                             m.age if m.age is not None else "", exp, "State")) + "</tr>"
        blocks.setdefault(SECTION[m.status], []).append(row)
    out = "".join('<section class="nfl-o-roster"><span class="nfl-o-roster__title-status">%s</span><table><thead></thead><tbody>%s</tbody>'
                  '</table></section>' % (section, "".join(rows)) for section, rows in blocks.items())
    return ("<html><body>%s</body></html>" % out).encode("utf-8")


def depth_page(team: RF.Team) -> bytes:
    def link(name):
        return '<a href="/team/players-roster/%s/">%s</a>' % (slug(name), html.escape(name))
    rows = []
    for role in RF.ROLES:
        rows.append("<tr><td>%s</td>%s</tr>" % (role, "".join("<td>%s</td>" % link(n) for n in team.roles.get(role, []))))
    return ('<html><body>(As of 11/03/2026)<table summary="Special Teams"><tbody>%s</tbody></table></body></html>' % "".join(rows)).encode("utf-8")


class NFL:
    """32 club sites (extras/roster_nfl.TEAMS) serving the teams given; GitHub's address answers from `github` (missing: 404) or raises."""

    def __init__(self, teams: dict, github=None, github_error=None, robots=None, down=(), page=None):
        self.teams, self.github, self.github_error = teams, github or {}, github_error
        self.robots, self.down, self.page, self.asked = robots or {}, set(down), page or {}, []
        self.hosts = {host: t for t, _nick, host, *_ in N.TEAMS}

    def __call__(self, url):
        self.asked.append(url)
        if "githubusercontent" in url:
            if self.github_error is not None:
                raise self.github_error
            name = url.rsplit("/", 1)[1]
            return (200, self.github[name].encode("utf-8")) if name in self.github else (404, b"404: Not Found")
        host = url.split("/")[2]
        t = self.hosts.get(host)
        if t is None or t in self.down:
            raise WebError("timeout", "WinHttpSendRequest failed with WinHTTP error 12002")
        if url.endswith("/robots.txt"):
            return (200, self.robots[t].encode()) if t in self.robots else (404, b"")
        if url.endswith("/team/players-roster/"):
            return 200, self.page.get(t) or roster_page(self.teams[t])
        if url.endswith("/team/depth-chart/"):
            return 200, depth_page(self.teams[t])
        return 404, b""


def shipped_teams():
    _v, teams, problems = RF.parse(R.shipped_text(R.ROSTERS))
    assert not problems
    return teams


def man(team, name):
    return next(m for m in team.men if m.name == name)


@pytest.fixture
def folder(tmp_path):
    return tmp_path / "customize"


def download(net, folder):
    folder.mkdir(parents=True, exist_ok=True)
    return F.download(net, str(folder), today=TODAY)


def changed_league():
    """The shipped league with a day's moves: a free agent signed by T01, a T02 man released, a T03 starter put on injured reserve."""
    teams = shipped_teams()
    free = [line for line in R.shipped_text(R.FREE_AGENTS).split("\n") if L.FA_LINE.match(line)]
    signed = L.FA_LINE.match(free[0])
    teams[1].men.append(RF.Man(signed.group(2), "88", signed.group(4), "PS", int(signed.group(3)) if signed.group(3).isdigit() else None, None))
    released = next(m for m in teams[2].men if m.status == "PS")
    teams[2].men.remove(released)
    hurt = next(m for m in teams[3].active() if m.pos == "WR")
    hurt.status = "IR"
    for role in RF.ROLES:
        teams[3].roles[role] = [n for n in teams[3].roles[role] if n != hurt.name]
    return teams, signed.group(4), released, hurt


# ----- the whole read -----

def test_the_league_is_read_from_the_teams_own_pages_and_a_days_moves_come_through(folder):
    teams, signed, released, hurt = changed_league()
    net = NFL(teams)
    got = download(net, folder)
    assert got.result == F.OK and got.source == F.NFL and got.read == 32 and not got.kept
    assert got.version == "season 2026, as of %s" % TODAY
    _v, read, problems = RF.parse(got.rosters)
    assert not problems and not RF.check(read)[0]
    assert man(read[1], signed).status == "PS" and man(read[1], signed).number == "88"
    assert all(released.name not in {m.name for m in t.men} for t in read.values())
    assert man(read[3], hurt.name).status == "IR"
    free = {L.FA_LINE.match(line).group(4) for line in got.free.split("\n") if L.FA_LINE.match(line)}
    assert signed not in free and released.name in free                       # the free agents follow the day's moves
    assert F.free_agents_problem(got.free) is None and "VERSION = season 2026, as of %s" % TODAY in got.free
    ship = shipped_teams()
    for t in (5, 20, 32):                                                     # an untouched team: every man where the checked file has him
        assert [(m.name, m.pos, m.status, m.number, m.age, m.seasons) for m in read[t].men] == \
               [(m.name, m.pos, m.status, m.number, m.age, m.seasons) for m in ship[t].men]
        assert read[t].roles == ship[t].roles
    assert net.asked.count("https://www.bengals.com/robots.txt") == 1         # robots.txt first, once a site


def test_known_men_keep_their_checked_positions_and_depth_order_though_the_page_says_only_the_group(folder):
    teams = shipped_teams()
    read = L.read_league(NFL(teams), R.shipped_text(R.ROSTERS)).teams       # the same men: the converter itself (download says nothing newer)
    for t in range(1, 33):                                                    # the pages say DE, LB, T, G, S: the sides are the checked file's
        assert [(m.name, m.pos) for m in read[t].active()] == [(m.name, m.pos) for m in teams[t].active()], t


def test_the_same_men_are_nothing_newer(folder):
    folder.mkdir(parents=True)
    (folder / "rosters.txt").write_text(R.shipped_text(R.ROSTERS), encoding="utf-8")
    got = F.download(NFL(shipped_teams()), str(folder), today=TODAY)
    assert got.result == F.NOTHING_NEWER and got.source == F.NFL


def test_github_blocked_like_the_testers_network_changes_nothing(folder):
    teams, signed, _released, _hurt = changed_league()
    got = download(NFL(teams, github_error=WebError("timeout", "WinHttpSendRequest failed with WinHTTP error 12002")), folder)
    assert got.result == F.OK and got.source == F.NFL and got.read == 32
    assert signed in got.rosters


def test_a_team_whose_pages_fail_is_disallowed_or_fails_a_check_stays_as_it_was(folder):
    teams, signed, _released, _hurt = changed_league()
    crowded = shipped_teams()[6]
    for n in range(54 - len(crowded.active())):                              # 54 active on a game day (men new to the team, not elevations
        crowded.men.insert(0, RF.Man("WR", "1%d" % n, "Extra Receiver%s" % chr(65 + n), "", 24, 1))     # of its own squad): fails the check
    assert len(crowded.active()) == 54
    teams[6] = crowded
    robots = {7: "User-agent: *\nDisallow: /team/\n"}
    net = NFL(teams, robots=robots, down={9})
    got = download(net, folder)
    assert got.result == F.OK and got.read == 29
    assert sorted(t for t, _r in got.kept) == [6, 7, 9]
    reasons = dict(got.kept)
    assert "robots.txt" in reasons[7] and "timeout" in reasons[9] and "active men" in reasons[6]
    assert not any(u.startswith("https://www.newyorkjets.com/team/") for u in net.asked)     # disallowed: never asked
    _v, read, _p = RF.parse(got.rosters)
    ship = shipped_teams()
    for t in (6, 7, 9):
        assert [(m.name, m.pos, m.status) for m in read[t].men] == [(m.name, m.pos, m.status) for m in ship[t].men]
    assert X.text("NXZ-U23", n=3).strip() in F.source_sentence(got)


def test_too_few_teams_read_takes_githubs_newer_checked_file_or_says_why(folder):
    newer = "\n".join(("VERSION = season 2026, as of 2026-11-02") if line.startswith("VERSION") else line
                      for line in R.shipped_text(R.ROSTERS).split("\n"))
    down = set(range(1, 33))
    got = download(NFL({}, github={"rosters.txt": newer}, down=down), folder)
    assert got.result == F.OK and got.source == F.GITHUB and got.version == "season 2026, as of 2026-11-02"
    assert F.source_sentence(got) == X.text("NXZ-U24")
    got = download(NFL({}, down=down), folder)
    assert got.result == F.OFFLINE and "0 teams" in got.detail
    got = download(NFL({}, down=down, github_error=WebError("timeout", "12002")), folder)
    assert got.result == F.OFFLINE
    assert F.sentence(got.result, got.version, got.detail) == X.text("NXZ-U05", label=X.text("NXZ-U06"))


def test_a_man_with_a_position_word_the_game_does_not_know_is_left_out_not_his_team(folder):
    teams = shipped_teams()
    page = roster_page(teams[4]).replace(b"<td>RB</td>", b"<td>XYZ</td>", 1)
    first_back = next(m for m in teams[4].men if m.pos == "HB" and m.status == "")
    newcomer = page.replace(html.escape(first_back.name).encode(), b"Brand Newman", 1)
    got = download(NFL(teams, page={4: newcomer}), folder)
    assert got.result == F.OK and 4 not in dict(got.kept)
    assert "Brand Newman" not in got.rosters


def test_the_text_says_where_the_rosters_came_from():
    got = F.Download(F.OK, "season 2026, as of 2026-11-03", source=F.NFL, read=32, kept=[])
    assert F.source_sentence(got).strip() == X.text("NXZ-U22").strip()
    got.kept = [(6, "x")]
    assert X.text("NXZ-U25").strip() in F.source_sentence(got)
    assert "N. F. L." in X.text("NXZ-U02") and "GitHub" not in X.text("NXZ-U02")


def test_the_maintainers_script_reads_with_the_moved_code():
    import importlib.util
    import sys
    from pathlib import Path
    tool = Path(__file__).resolve().parent.parent / "tools" / "update_rosters.py"
    spec = importlib.util.spec_from_file_location("update_rosters_rc", tool)
    module = importlib.util.module_from_spec(spec)
    sys.modules["update_rosters_rc"] = module
    spec.loader.exec_module(module)
    assert module.build_team is N.build_team and module.parse_roster_page is N.parse_roster_page and module.TEAMS is N.TEAMS
