"""SR.2 (NX-L8; D-154 to D-156): game/tools/update_rosters.py on saved pages, never the network. This is inspired by Jim Kitchen.

The fixtures in tests/data/rosters_sr2 are excerpts of pages and feeds saved on 2026-10-25 (work/sr2/make_fixtures.py): the Ravens' roster page
(3 rows of every table) and depth chart page (every row), nflverse's rows of the Ravens (roster, the two newest depth chart snapshots) and
Sleeper's Ravens and two free agents.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from nfl4.extras import roster_file as RF

TOOL = Path(__file__).resolve().parent.parent / "tools" / "update_rosters.py"
spec = importlib.util.spec_from_file_location("update_rosters", TOOL)
U = importlib.util.module_from_spec(spec)
sys.modules["update_rosters"] = U                  # a dataclass looks up its module while the class is made
spec.loader.exec_module(U)
FIX = Path(__file__).resolve().parent / "data" / "rosters_sr2"
# The excerpts are kept on the maintainer's computer only (D-156: the teams' pages are never republished; .gitignore): a copy of the repository
# without them skips the tests that read them, and work/sr2/make_fixtures.py makes them again from a run's saved pages.


@pytest.fixture(scope="module")
def ravens():
    if not (FIX / "T03_roster.html").exists():
        pytest.skip("the saved page excerpts are not in this copy (D-156)")
    page = U.parse_roster_page((FIX / "T03_roster.html").read_bytes())
    depth = U.parse_depth_page((FIX / "T03_depth.html").read_bytes())
    nv = U.parse_nv_roster((FIX / "nflverse_roster.csv").read_bytes())[3]
    chart = U.parse_nv_depth((FIX / "nflverse_depth.csv.gz").read_bytes())[3]
    sl_teams, sl_free = U.parse_sleeper((FIX / "sleeper.json").read_bytes())
    return page, depth, nv, chart, sl_teams[3], sl_free


def test_the_roster_page_is_read_table_by_table_with_its_empty_cells(ravens):
    page = ravens[0]
    sections = {pm.section for pm in page}
    assert "Active" in sections and "Practice Squad" in sections
    assert all(U.SECTIONS.get(s.casefold()) is not None for s in sections)
    assert all(pm.name and pm.slug and (pm.number == "-" or pm.number.isdigit()) for pm in page)
    assert all(U.word_family(pm.word) for pm in page)                    # every position word is known (B-X149: a shifted column gives "6-3")


def test_the_depth_page_keeps_its_rows_tiers_and_links(ravens):
    asof, rows = ravens[1]
    tables = {table for table, _, _ in rows}
    assert tables == {"Offense", "Defense", "Special Teams"}
    labels = {label for _, label, _ in rows}
    assert {"QB", "LT", "C", "RT", "PR"} <= labels and labels & set(U.KR_LABELS)          # the Ravens call the kick returner KOR
    assert all(slug for _, _, tiers in rows for cell in tiers for slug, _ in cell)


def test_the_newest_nflverse_snapshot_is_taken(ravens):
    snap, rows = ravens[3]
    assert rows and all(r["dt"] == snap for r in rows)


def test_the_chart_rows_become_maddens_positions():
    assert U.map_chart("LDE", "Base 4-3 D") == "LEDG" and U.map_chart("RDE", "Base 4-3 D") == "REDG"
    assert U.map_chart("SLB", "Base 4-3 D") == "SAM" and U.map_chart("MLB", "Base 4-3 D") == "MIKE" and U.map_chart("WLB", "Base 4-3 D") == "WILL"
    assert U.map_chart("NT", "Base 3-4 D") == "DT" and U.map_chart("LDE", "Base 3-4 D") == "DT"                 # D-153, UNVERIFIED (Q-077)
    assert U.map_chart("WLB", "Base 3-4 D") == "LEDG" and U.map_chart("SLB", "Base 3-4 D") == "REDG"
    assert U.map_chart("LILB", "Base 3-4 D") == "MIKE" and U.map_chart("RILB", "Base 3-4 D") == "WILL"
    assert U.map_chart("RB", "3WR 1TE") == "HB" and U.map_chart("NB", "Base 4-3 D") == "CB"
    assert U.map_chart("KR", "Special Teams") is None and U.map_chart("H", "Special Teams") is None             # roles, never positions
    assert U.map_word("TE", False) == "TE" and U.word_family("TE") == "TE" != U.word_family("WR")             # a tight end never a receiver


def test_a_whole_team_is_built_with_real_positions_lists_and_roles(ravens):
    page, depth, nv, chart, sl, _ = ravens
    built = U.build_team(3, page, depth, nv, chart, sl)
    team = built.team
    assert len(team.men) == len(page)                                    # nobody left off, nobody made up
    assert all(m.pos in RF.MADDEN for m in team.men)
    by_name = {m.name: m for m in team.men}
    for pm in page:                                                      # the team's own word decides the group (D-153)
        assert U.family(by_name[pm.name].pos) == U.word_family(pm.word), pm.name
        assert by_name[pm.name].status == U.SECTIONS[pm.section.casefold()]
    for role in ("KR", "PR"):
        assert all(name in {m.name for m in team.active()} for name in team.roles[role])


def test_the_comparison_lists_who_one_source_has_and_the_other_not(ravens):
    page, depth, nv, chart, sl, _ = ravens
    built = U.build_team(3, page, depth, nv, chart, sl)
    lines = U.compare(3, built, nv, sl)
    assert all(line.startswith("  ") and "(" in line for line in lines)   # the excerpt has 3 rows a table, so nflverse has many more men


def test_names_match_across_sources():
    m = U.Matcher(["Joshua Uche", "Mike Ford Jr.", "Trebor Peña"])
    assert m.find("Josh Uche") == "Joshua Uche" and m.find("Mike Ford") == "Mike Ford Jr." and m.find("Trebor Pena") == "Trebor Peña"
    assert U.Matcher(["Josh Allen", "Jonah Allen"]).find("J. Allen") is None              # two men with one loose key: no guess


def test_the_free_agents_are_refreshed_and_keep_their_ids(ravens):
    _, _, _, _, sl, free = ravens
    old = "# header\nVERSION = season 2026, as of 2026-10-24\nF001 = WR 32 Tyreek Hill\nF002 = LB 36 Bobby Wagner\nF003 = QB 30 Signed Man\n"
    teams = {3: RF.Team(men=[RF.Man("QB", "1", "Signed Man")])}
    previous = {U.name_key("Released Man"): (3, "", "WR", "Released Man")}
    text, removed, added = U.refresh_free_agents(old, previous, teams, free, {3: sl}, "2026-10-25")
    assert removed == ["Signed Man"] and added == []                     # a released man Sleeper does not show as free is not added
    assert "F001 = WR" in text and "F002 = LB" in text and "F003" not in text and "as of 2026-10-25" in text


def test_an_age_comes_from_the_birth_date_not_from_the_feeds_stale_age_field():
    assert U.age_on({"birth_date": "1994-03-01", "age": 31}, "2026-10-25") == "32"
    assert U.age_on({"birth_date": "1994-10-26"}, "2026-10-25") == "31" and U.age_on({"age": 30}, "2026-10-25") == "-"


def test_a_safety_stays_a_safety_on_a_nickel_or_a_generic_db_row():
    page = [U.PageMan("Active", "Safe Man", "safe-man", "14", "S"), U.PageMan("Active", "Corner Man", "corner-man", "20", "CB")]
    depth = ("", [("Defense", "DB", [[("safe-man", "Safe Man")]]), ("Defense", "NB", [[("corner-man", "Corner Man")]])])
    team = U.build_team(1, page, depth, [], None, []).team
    assert {m.name: m.pos for m in team.men}["Safe Man"] in ("FS", "SS") and {m.name: m.pos for m in team.men}["Corner Man"] == "CB"


def test_settlements_and_game_day_elevations():
    men = [RF.Man("QB", str(i), "Man %d" % i) for i in range(55)] + [RF.Man("WR", "-", "Squad Man", "PS")]
    teams = {9: RF.Team(men=men, roles={"KR": ["Man 1"], "PR": ["Man 2"]})}
    notes = []
    U.apply_settlements(teams, [("S001", 9, "Man 1", "IR", "a source"), ("S002", 9, "Nobody", "PS", "x"), ("S003", 9, "Squad Man", "off", "y")], notes)
    assert teams[9].roles["KR"] == [] and next(m for m in teams[9].men if m.name == "Man 1").status == "IR"
    assert "Squad Man" not in {m.name for m in teams[9].men} and any("no longer applies" in n for n in notes)
    previous = {U.name_key("Man 3"): (9, "PS", "QB", "Man 3"), U.name_key("Man 4"): (9, "PS", "QB", "Man 4"), U.name_key("Man 5"): (9, "PS", "QB", "Man 5")}
    U.return_elevations(teams, previous, notes)
    assert [m.name for m in teams[9].squad()] == ["Man 3", "Man 4"] and len(teams[9].active()) == 52       # at most 2 a game
    text = "# x\nS001 = T18 | Thomas Harper | IR | nflverse RES\n# S002 = T01 | Not | PS | commented out\n"
    assert U.read_settlements(text) == [("S001", 18, "Thomas Harper", "IR", "nflverse RES")]
    assert all(s[1] in range(1, 33) for s in U.read_settlements(U.SETTLEMENTS.read_bytes().decode("utf-8")))


def test_a_failed_pull_never_replaces_the_shipped_files(tmp_path):
    before = (U.DATA / "rosters.txt").read_bytes(), (U.DATA / "free_agents.txt").read_bytes()
    (tmp_path / "raw").mkdir()
    assert U.main(["--saved", str(tmp_path), "--write", "--date", "2026-10-25"]) == 1          # nothing saved: every check fails
    assert ((U.DATA / "rosters.txt").read_bytes(), (U.DATA / "free_agents.txt").read_bytes()) == before
    assert "FAILURES" in (tmp_path / "report.txt").read_bytes().decode("utf-8")


def test_robots_txt_is_obeyed(tmp_path, monkeypatch):
    f = U.Fetcher(tmp_path, 0, False)
    import urllib.robotparser
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(["User-agent: *", "Disallow: /team/"])
    f.robots["https://example.test"] = rp
    monkeypatch.setattr(f, "_request", lambda *a, **k: pytest.fail("a disallowed page was requested"))
    assert f.get("x.html", "https://example.test/team/players-roster/") is None
    assert "DISALLOWED" in f.log[-1]
