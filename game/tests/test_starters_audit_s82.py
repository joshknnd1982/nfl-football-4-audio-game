"""The starters audit (nfl4 only, rule 0.13; D-177). A tester: "Winston is not the Giants starter at QB. It is not doing the depth charts
properly. If one starter player is wrong, who else is the game getting wrong? audit and fix this." The owner: "all rosters and depth charts must
be audited, corrected, and implemented correctly into the game." This is inspired by Jim Kitchen.

1. game/tools/update_rosters.py: where nflverse's newest chart and Sleeper's depth chart agree on a starter who is on the active roster at that
   position, he goes first (a team's own page can lag a change of starter: the Giants' page still started Jameis Winston on 2026-10-25).
2. The shipped file: the Giants start J.J. McCarthy (named the starter for the game of 2026-10-25, ESPN and CBS).
3. The game: in a quick game and in a new franchise every team's starters at all 22 positions are the file's first men (the depth order of
   the file is the order the game plays).
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from nfl4.extras import roster_file as RF

TOOL = Path(__file__).resolve().parent.parent / "tools" / "update_rosters.py"
DATA = Path(__file__).resolve().parent.parent / "assets" / "data"


@pytest.fixture(scope="module")
def U():
    spec = importlib.util.spec_from_file_location("update_rosters", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["update_rosters"] = module
    spec.loader.exec_module(module)
    return module


def men_of(U, *rows):
    return [((0, i, 0, i), RF.Man(pos, "1", name, status)) for i, (pos, name, status) in enumerate(rows)]


def order(men):
    return [m.name for _k, m in sorted(men, key=lambda r: r[0])]


def test_two_fresher_sources_that_agree_put_their_starter_first(U):
    men = men_of(U, ("QB", "Jameis Winston", ""), ("QB", "J.J. McCarthy", ""), ("QB", "Tommy DeVito", ""))
    chart = [{"pos_abb": "QB", "pos_grp": "Offense", "pos_rank": "1", "player_name": "J.J. McCarthy"},
             {"pos_abb": "QB", "pos_grp": "Offense", "pos_rank": "2", "player_name": "Jameis Winston"}]
    sleeper = [{"full_name": "J.J. McCarthy", "depth_chart_position": "QB", "depth_chart_order": 1},
               {"full_name": "Jameis Winston", "depth_chart_position": "QB", "depth_chart_order": 2}]
    notes = []
    out = U.agreed_starters_first(men, chart, sleeper, False, "10/20/2026", notes)
    assert order(out) == ["J.J. McCarthy", "Jameis Winston", "Tommy DeVito"]
    assert notes and "J.J. McCarthy" in notes[0] and "Jameis Winston" in notes[0]


def test_one_source_alone_or_two_that_disagree_leave_the_teams_order(U):
    men = men_of(U, ("QB", "Jameis Winston", ""), ("QB", "J.J. McCarthy", ""))
    chart = [{"pos_abb": "QB", "pos_grp": "Offense", "pos_rank": "1", "player_name": "J.J. McCarthy"}]
    other = [{"full_name": "Jameis Winston", "depth_chart_position": "QB", "depth_chart_order": 1}]
    notes = []
    assert order(U.agreed_starters_first(men, chart, other, False, "", notes)) == ["Jameis Winston", "J.J. McCarthy"]
    assert order(U.agreed_starters_first(men, chart, [], False, "", notes)) == ["Jameis Winston", "J.J. McCarthy"]
    assert notes == []


def test_an_agreed_starter_who_is_not_active_at_the_position_is_only_reported(U):
    men = men_of(U, ("HB", "Chris Rodriguez Jr.", ""), ("HB", "Bhayshul Tuten", "IR"))
    chart = [{"pos_abb": "RB", "pos_grp": "Offense", "pos_rank": "1", "player_name": "Bhayshul Tuten"}]
    sleeper = [{"full_name": "Bhayshul Tuten", "depth_chart_position": "RB", "depth_chart_order": 1}]
    notes = []
    out = U.agreed_starters_first(men, chart, sleeper, False, "", notes)
    assert order(out) == ["Chris Rodriguez Jr.", "Bhayshul Tuten"]           # on injured reserve: the active man starts
    assert notes and "not an active HB" in notes[0]


def test_three_receivers_and_two_corners_are_compared_as_sets(U):
    men = men_of(U, ("WR", "A", ""), ("WR", "B", ""), ("WR", "C", ""), ("WR", "D", ""))
    chart = [{"pos_abb": "WR", "pos_grp": "Offense", "pos_rank": str(r), "player_name": n} for r, n in ((1, "A"), (2, "B"), (3, "D"))]
    sleeper = [{"full_name": n, "depth_chart_position": "WR", "depth_chart_order": r} for r, n in ((1, "D"), (2, "A"), (3, "B"))]
    out = U.agreed_starters_first(men, chart, sleeper, False, "", [])
    assert order(out)[:3] == ["A", "B", "D"] and order(out)[3] == "C"


def test_a_quick_game_plays_the_files_order_and_its_first_quarterback_for_every_team():
    from nfl4.extras import real_names as R
    from nfl4.extras import roster_model as RM
    R.reset_defaults_cache()
    try:
        real = R.defaults()
        _v, teams, _p = RF.parse(R.shipped_text(R.ROSTERS))
        for t, team in teams.items():
            chart, _roles, _squad = real.chart(t)
            for pos in RF.MADDEN:
                want = [m.name for m in team.active() if m.pos == pos]
                assert list(chart.get(pos, []))[:len(want)] == want, (t, pos)
            view = real.view(t)
            assert view.places[RM.QUARTERBACK] == want_qb(team), t
    finally:
        R.reset_defaults_cache()


def want_qb(team):
    return next(m.name for m in team.active() if m.pos == "QB")


def test_the_shipped_file_starts_jj_mccarthy_for_the_giants():
    _v, teams, problems = RF.parse((DATA / "rosters.txt").read_bytes().decode("utf-8"))
    assert not problems
    giants = [m.name for m in teams[23].active() if m.pos == "QB"]
    assert giants[0] == "J.J. McCarthy" and "Jameis Winston" in giants[1:]
