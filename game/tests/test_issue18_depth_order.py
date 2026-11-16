"""GitHub issue 18 (D-245): "get the latest rosters" takes each team's depth order from its own depth chart page (nfl4 only, rule 0.13; CLAUDE.md
0.30, 0.32). This is inspired by Jim Kitchen.

The tester (2026-11-16, 1.0.3): "Started a Franchise with the Vikings. The depth charts are not properly updated", with a problem report: the
rosters of 2026-11-16 put Kyler Murray, Carson Wentz, Max Brosmer, then Kirk Cousins at quarterback, while the Vikings' own depth chart page started
Kirk Cousins (traded from the Raiders) ahead of the other three. D-196 kept the base file's order for every man the base file had and put new men
behind them, so the shipped order of 2026-10-26 never changed: on 2026-11-16 the game's own update left 89 positions of the league with other
starters than the teams' pages (work/i18_1116/league_check.py; 0 with this fix).

What is tested: the page's order decides for the men it lists, co-starters in one cell in the page's order; the men it does not list follow in the
base file's order, the new ones last; the change of starters is a note and a log line; a franchise brought up to the new file (the offer's third
answer) starts the page's starter; a second update on the same day is newer, so a franchise made in the morning is offered the evening's file.
"""
import html
import re

import test_rc_roster_live as RC
from nfl4.data import customlists as cl
from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF
from nfl4.extras import roster_live as L
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import roster_update as RU
from nfl4.extras.franchise import rosters_flow as F

VIKINGS, RAIDERS = 20, 12
CHART_QB = ["Kirk Cousins", "Kyler Murray", "Carson Wentz", "Max Brosmer"]


def link(name):
    return '<a href="/team/players-roster/%s/">%s</a>' % (RC.slug(name), html.escape(name))


def depth_page(team: RF.Team, rows) -> bytes:
    """A team's depth chart page in the layout of the real ones: `rows` are (table, label, [[names of a cell], ...]), then the return roles."""
    def cells(tiers):
        return "".join("<td>%s</td>" % ", ".join(link(n) for n in cell) for cell in tiers)
    body = {}
    for table, label, tiers in rows:
        body.setdefault(table, []).append("<tr><td>%s</td>%s</tr>" % (label, cells(tiers)))
    for role in RF.ROLES:
        body.setdefault("Special Teams", []).append("<tr><td>%s</td>%s</tr>" % (role, cells([[n] for n in team.roles.get(role, [])])))
    out = "".join('<table summary="%s"><tbody>%s</tbody></table>' % (table, "".join(rs)) for table, rs in body.items())
    return ("<html><body>%s</body></html>" % out).encode("utf-8")


class NFL(RC.NFL):
    """The fake NFL of test_rc_roster_live with real depth chart rows for the teams of `charts` ({team: rows})."""

    def __init__(self, teams, charts, **kw):
        super().__init__(teams, **kw)
        self.charts = charts

    def __call__(self, url):
        host = url.split("/")[2]
        t = self.hosts.get(host)
        if url.endswith("/team/depth-chart/") and t in self.charts:
            self.asked.append(url)
            return 200, depth_page(self.teams[t], self.charts[t])
        return super().__call__(url)


def traded_league():
    """The shipped league with the tester's day: Kirk Cousins traded from the Raiders to the Vikings."""
    teams = RC.shipped_teams()
    cousins = RC.man(teams[RAIDERS], "Kirk Cousins")
    teams[RAIDERS].men.remove(cousins)
    for role in RF.ROLES:
        teams[RAIDERS].roles[role] = [n for n in teams[RAIDERS].roles[role] if n != cousins.name]
    cut = next(m for m in reversed(teams[VIKINGS].men) if m.status == "" and m.pos == "WR")      # room on the 53
    teams[VIKINGS].men.remove(cut)
    teams[VIKINGS].men.append(cousins)
    return teams


def backs(team):
    return [m.name for m in team.active() if m.pos == "HB"]


def vikings_chart(teams, backs_cell):
    return {VIKINGS: [("Offense", "QB", [[n] for n in CHART_QB]), ("Offense", "RB", [backs_cell])]}


def read(net, base_text=None):
    base = base_text if base_text is not None else R.shipped_text(R.ROSTERS)
    return L.read_league(net, base)


def test_the_teams_own_chart_decides_the_order_of_the_men_it_lists(monkeypatch):
    events = []
    monkeypatch.setattr(L.debuglog, "event", lambda *a, **k: events.append((a, k)))
    teams = traded_league()
    shipped_backs = backs(teams[VIKINGS])
    cell = [shipped_backs[1], shipped_backs[0]]                        # co-starters in one cell, the page's order the other way round
    live = read(NFL(teams, vikings_chart(teams, cell)))
    vikings = live.teams[VIKINGS]
    assert VIKINGS in live.read
    assert [m.name for m in vikings.active() if m.pos == "QB"] == CHART_QB          # the tester's report: Cousins first, as the Vikings' page
    assert backs(vikings)[:2] == cell and backs(vikings)[2:] == shipped_backs[2:]  # the cell's order; the men not listed in the file's order
    assert any(n.startswith("T20 QB starters Kirk Cousins (the team's depth chart; the file before had Kyler Murray)") for n in live.notes)
    line = [k for a, k in events if a[:2] == ("rosters", "nfl_depth_order") and k.get("team") == "Vikings"]
    assert line and "QB: Kirk Cousins" in line[0]["starters_changed"] and line[0]["charted"] == 6
    raiders = [m.name for m in live.teams[RAIDERS].active() if m.pos == "QB"]
    assert "Kirk Cousins" not in raiders and raiders == [m.name for m in RC.shipped_teams()[RAIDERS].active() if m.pos == "QB" and m.name != "Kirk Cousins"]


def test_without_a_chart_row_the_base_order_stays_and_a_new_man_comes_last():
    teams = traded_league()
    live = read(RC.NFL(teams))                                          # the pages list no position rows (only the returners)
    qbs = [m.name for m in live.teams[VIKINGS].active() if m.pos == "QB"]
    assert qbs == ["Kyler Murray", "Carson Wentz", "Max Brosmer", "Kirk Cousins"]      # what D-196 did for every man: kept only without a chart
    assert not any(n.startswith("T20 QB starters") for n in live.notes)


def test_a_man_the_chart_lists_comes_before_a_man_it_does_not_list():
    teams = traded_league()
    rows = {VIKINGS: [("Offense", "QB", [["Max Brosmer"], ["Kirk Cousins"]])]}       # the page lists two of the four
    qbs = [m.name for m in read(NFL(teams, rows)).teams[VIKINGS].active() if m.pos == "QB"]
    assert qbs == ["Max Brosmer", "Kirk Cousins", "Kyler Murray", "Carson Wentz"]


def test_the_downloaded_file_has_the_order_and_the_time_of_day(tmp_path):
    teams = traded_league()
    folder = tmp_path / "customize"
    folder.mkdir()
    got = F.download(NFL(teams, vikings_chart(teams, backs(teams[VIKINGS])[:2])), str(folder))
    assert got.result == F.OK and F.rosters_problem(got.rosters) is None
    assert re.fullmatch(r"season 2026, as of \d{4}-\d{2}-\d{2} \d{2}:\d{2}", got.version)
    _v, parsed, problems = RF.parse(got.rosters)
    assert not problems and [m.name for m in parsed[VIKINGS].active() if m.pos == "QB"] == CHART_QB
    assert RU.spoken_date(got.version).count(",") == 1 and ":" not in RU.spoken_date(got.version)


def test_a_second_update_on_the_same_day_is_newer():
    morning, evening = "season 2026, as of 2026-11-16", "season 2026, as of 2026-11-16 18:40"
    assert RU.newer(evening, morning) and not RU.newer(morning, evening) and not RU.newer(evening, evening)
    assert RU.newer("season 2026, as of 2026-11-16 18:41", evening)
    assert RU.newer("season 2026, as of 2026-11-17", evening) and not RU.newer(evening, "season 2026, as of 2026-11-17")
    assert RU.date_of(evening) == "2026-11-16" and RU.time_of(evening) == "18:40" and RU.time_of(morning) == ""
    assert RU.spoken_date(evening) == "November 16, 2026"


def test_a_franchise_brought_up_to_the_file_starts_the_charts_starter(tmp_path, monkeypatch):
    """The offer's third answer (the player's own team too, issue 9) on the tester's Vikings: the file's order comes into his chart, and the staff
    keeps the real starter (FR_DEPTH_HOLD: a quarterback is passed only by a man 8 points better)."""
    from drrig import full_league
    import test_rosters_update_sr6 as SR
    monkeypatch.setattr(F, "folder_of", lambda g: str(tmp_path))
    teams = traded_league()
    live = read(NFL(teams, vikings_chart(teams, backs(teams[VIKINGS])[:2])))
    version = "season 2026, as of 2026-11-16 18:40"
    text = RF.render(version, live.teams)
    problems = {kind: cl.Problems(R.FILE_NAMES[kind]) for kind in R.FILE_NAMES}
    real = R.build([], R.parse_entries(text, R.ROSTERS).entries, [], R.defaults(), problems)
    league = full_league(team=VIKINGS)
    league.reserves_on = True
    league.roster_version = "season 2026, as of 2026-11-16"                # made from the morning's file, as the tester's
    chart = league.chart[VIKINGS - 1]["QB"]
    murray = next(pid for pid in chart if league.players[pid].name == "Kyler Murray")
    assert chart[0] == murray
    cousins = next(p for p in league.players.values() if p.name == "Kirk Cousins")
    cousins.rating = league.players[murray].rating                       # equal ratings: only the real order decides
    store = SR.store_of(league)
    assert RU.offer_due(league, real) == version
    F.offer(SR.Game(real=real), None, None, store, ask=lambda q, items: 2)
    league = store.league
    qbs = [league.players[pid].name for pid in league.chart[VIKINGS - 1]["QB"]]
    assert qbs[0] == "Kirk Cousins" and qbs == [n for n in CHART_QB if n in qbs]     # full_league keeps a family at its target (three)
    assert RR.chart_view(league, VIKINGS) is not None
    league.check()
