"""The computer's calling over the catalog, the playbook's pick, the clock plays and the two-point chart, as pure rules (nfl4 only, rule
0.13; NX-P2, NX-P4, NX-R7 G26-10; NFL_PLAYS_DESIGN 7 and 8; PX SX.10e, D-095). This is inspired by Jim Kitchen.

extras/plays/calling.py: the weights are whole numbers, every draw is one below(total), the shares come from model_data (the league's
2024 and 2025 numbers) and the styles lean on them; the clock plays and the try are rules with no draw, except the early try's one draw.
"""
import ast
from pathlib import Path

import pytest

from nfl4.extras import playbook_data as PD
from nfl4.extras.plays import calling as K
from nfl4.extras.plays import calling_data as CD
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model_data as MD


class ScriptedRandom:
    """The game's generator as the calling sees it (`below(n)`), scripted: each entry is ("below", n, the value); strict."""

    def __init__(self, script, strict=True):
        self.script = list(script)

    def below(self, n):
        assert self.script, "a draw the test did not script: below(%d)" % n
        kind, size, value = self.script.pop(0)
        assert (kind, size) == ("below", n), (kind, size, n)
        return value

    def done(self):
        return not self.script


STYLES = ("", "pro", "west", "air", "power", "zone", "option", "pressure")
NEUTRAL = K.Situation(1, 10, 70, 1, 600, 0)


def offense(style="", sit=NEUTRAL, own=frozenset()):
    return dict(K.offense_weights(C.OFFENSE, style, own, sit))


def defense(style="", sit=NEUTRAL, own=frozenset()):
    return dict(K.defense_weights(C.DEFENSE, style, own, sit))


def share(weights, test):
    total = sum(weights.values())
    return 100 * sum(w for i, w in weights.items() if test(C.BY_ID[i])) / total


# ----- the offense -----

@pytest.mark.parametrize("down,to_go", [(1, 10), (2, 2), (2, 5), (2, 9), (3, 1), (3, 4), (3, 9), (4, 1)])
def test_the_pass_calls_are_the_leagues_drop_back_share_of_the_down_and_distance(down, to_go):
    sit = K.Situation(down, to_go, 60, 1, 600, 0)
    assert abs(share(offense(sit=sit), K.pass_class) - K.pass_rate(sit) / 100) < 0.1
    assert K.pass_rate(sit) in MD.PASS_RATE.values()


def test_the_catalog_games_own_foul_scale_and_ruling_rates_are_the_measured_ones():
    from nfl4.extras import tuning as T
    assert T.PENALTY_RATE_SCALE_CATALOG == 1.07 and T.PENALTY_RATE_SCALE == 1.2
    assert T.RULING_RATES_CATALOG == {"goal": (28, 62), "catch": (4, 15), "line": (20, 86)}
    assert all(T.RULING_RATES[k][0] > v[0] for k, v in T.RULING_RATES_CATALOG.items())     # fewer wrong rulings a play than SX.6's


def test_late_in_a_half_the_team_behind_passes_and_the_team_ahead_runs():
    behind = K.Situation(1, 10, 60, 4, 100, -7)
    ahead = K.Situation(1, 10, 60, 4, 250, 3)
    assert K.pass_rate(behind) == K.LATE_PASS_FLOOR and K.pass_rate(ahead) == K.LATE_LEAD_PASS_CEILING
    assert K.pass_rate(K.Situation(1, 10, 60, 1, 100, -7)) == MD.PASS_RATE["1st"]       # the first quarter: no change


def test_every_offense_play_but_the_clock_plays_can_be_called_and_the_goal_line_plays_only_near_the_goal():
    called = set(offense())
    for style in STYLES:
        called |= set(offense(style)) | set(offense(style, K.Situation(3, 1, 4, 2, 600, 0)))
        called |= set(offense(style, K.Situation(1, 10, 8, 2, 600, 0))) | set(offense(style, K.Situation(2, 10, 50, 2, 100, 0)))
    wanted = {c.id for c in C.OFFENSE if c.kind not in K.CLOCK_KINDS}
    assert wanted - called == set()
    assert not any("goal_line" in C.BY_ID[i].situations for i in offense())          # 70 yards away: none of them
    assert {i for i in offense(sit=K.Situation(1, 10, 6, 2, 600, 0)) if "goal_line" in C.BY_ID[i].situations}


def test_the_lists_share_the_calls_as_the_league_and_trick_plays_and_old_formations_are_rare():
    w = offense()
    runs = {g: share(w, lambda c, g=g: c.group == g) for g in K.RUN_GROUP_MASS}
    assert runs["og01"] > runs["og03"] > runs["og13"] > runs["og19"]
    assert share(w, lambda c: c.group == "og16") < 0.6 and share(w, lambda c: c.group == "og19") < 0.6
    screens = share(w, lambda c: c.group == "og05") / share(w, K.pass_class)
    assert abs(screens - MD.SCREEN_SHARE / 10000) < 0.01
    assert share(w, lambda c: c.kind in K.CLOCK_KINDS) == 0


def test_a_style_leans_on_its_lists_and_its_own_plays_count_double():
    option, pro = offense("option"), offense("pro")
    assert share(option, lambda c: c.group == "og14") > 2.5 * share(pro, lambda c: c.group == "og14")
    assert share(offense("air"), K.pass_class) > share(pro, K.pass_class) > share(offense("power"), K.pass_class)
    own = frozenset(i for i, _w in PD.STYLE_BY_KEY["west"].offense)
    plain, leaned = offense("west"), offense("west", own=own)
    assert leaned["O017"] * plain["O072"] > 1.9 * plain["O017"] * leaned["O072"]       # O017 is West Coast's own, O072 is not


def test_short_yardage_calls_the_sneak_and_the_power_runs_more():
    short = offense(sit=K.Situation(3, 1, 50, 2, 600, 0))
    assert share(short, lambda c: c.kind == "sneak") > 3 * share(offense(sit=K.Situation(2, 1, 50, 2, 600, 0)),
                                                                  lambda c: c.kind == "sneak")


def test_the_try_calls_the_goal_line_list_a_quarter_of_them_runs():
    w = dict(K.try_weights({c.id for c in C.CATALOG}))
    runs = sum(v for i, v in w.items() if C.BY_ID[i].kind in ("run", "sneak"))
    assert abs(100 * runs / sum(w.values()) - 100 * MD.TWO_POINT["run_tries"] / (MD.TWO_POINT["run_tries"] + MD.TWO_POINT["pass_tries"])) < 6
    assert "K026" in w and w["K026"] < 20


# ----- the defense -----

def test_the_base_weights_give_the_leagues_coverage_rusher_blitz_and_box_shares():
    w = defense("pro")
    total = sum(w.values())

    def by(attr):
        out = {}
        for i, v in w.items():
            key = getattr(C.BY_ID[i].params, attr)
            out[key] = out.get(key, 0) + 100 * v / total
        return out

    coverage = {k: v for k, v in MD.COVERAGE_SHARE.items() if k.startswith("COVER") or k == "2_MAN"}
    for key, value in coverage.items():
        assert abs(by("coverage")[key] - 100 * value / sum(coverage.values())) < 1.0, key
    rushers = {k: v for k, v in MD.RUSHER_SHARE.items() if k >= 3}
    for key, value in rushers.items():
        assert abs(by("rushers")[key] - 100 * value / sum(rushers.values())) < 1.0, key
    assert abs(by("blitz")[True] - MD.BLITZ_SHARE / 100) < 1.0
    for key, value in MD.BOX_SHARE_ON_RUNS.items():
        assert abs(by("box")[key] - value / 100) < 1.0, key


def test_the_situation_calls_come_only_in_their_situations():
    special = {c.id for c in C.DEFENSE if set(c.situations) & {"goal_line", "two_point", "late"} or c.params.coverage == C.PREVENT}
    assert set(CD.DEFENSE_BASE) == {c.id for c in C.DEFENSE} - special
    assert not set(defense()) & special
    near = defense(sit=K.Situation(1, 3, 3, 2, 600, 0))
    assert 55 < share(near, lambda c: "goal_line" in c.situations) < 65
    protect = defense(sit=K.Situation(1, 10, 60, 4, 90, -7))
    assert 20 < share(protect, lambda c: c.id in ("D087", "D024", "D083")) < 30
    hail = defense(sit=K.Situation(1, 10, 55, 2, 5, 0, last_play=True))
    assert 65 < share(hail, lambda c: c.id == K.HAIL_MARY_CALL) < 75
    tries = defense(sit=K.Situation(1, 2, 2, 2, 600, 0, two_point=True))
    assert set(tries) == {i for i, _w in K.TRY_CALLS}


def test_a_style_leans_its_defense_and_third_and_long_brings_more_pressure():
    assert share(defense("pressure"), lambda c: c.group in ("dg05", "dg06")) > 1.5 * share(defense("pro"),
                                                                                         lambda c: c.group in ("dg05", "dg06"))
    long_ = defense(sit=K.Situation(3, 9, 60, 2, 600, 0))
    assert share(long_, lambda c: c.params.blitz) > share(defense(), lambda c: c.params.blitz)


def test_every_neutral_call_can_be_drawn():
    assert all(v > 0 for v in defense().values()) and len(defense()) == len(CD.DEFENSE_BASE)


# ----- the draws -----

def test_a_draw_is_one_below_of_the_whole_weights_and_nothing_is_no_draw():
    weights = [("O001", 3), ("O002", 5)]
    rnd = ScriptedRandom([("below", 8, 3)], strict=True)
    assert K.draw(weights, rnd) == "O002" and rnd.done()
    assert K.draw([], ScriptedRandom([], strict=True)) == ""


def test_the_calling_has_no_float_and_reads_no_clock_or_file():
    source = (Path(K.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, float)]
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)]
    assert "import random" not in source and "open(" not in source and "import time" not in source


# ----- the clock plays and the try -----

def test_kneel_helps_as_design_2_7():
    assert K.kneel_helps(4, 80, 1, 3, 2) and not K.kneel_helps(4, 81, 1, 3, 2)      # (4 - 2) downs x 40
    assert not K.kneel_helps(4, 30, 1, 0, 0) and not K.kneel_helps(4, 30, 1, -3, 0)
    assert K.kneel_helps(2, 40, 3, -10, 3) and not K.kneel_helps(1, 10, 1, 7, 0)
    assert not K.kneel_helps(4, 30, 1, 3, 0, two_point=True) and not K.kneel_helps(4, 0, 1, 3, 0)


def test_the_computer_spikes_only_without_timeouts_in_the_last_minute_and_in_reach():
    assert K.spike_wanted(4, 50, True, 1, -3, 0, 40)
    assert not K.spike_wanted(4, 50, True, 1, -3, 1, 40)        # a timeout left: it calls the timeout
    assert not K.spike_wanted(4, 50, False, 1, -3, 0, 40)       # the clock is stopped
    assert not K.spike_wanted(4, 50, True, 3, -3, 0, 40)        # no down would be left
    assert not K.spike_wanted(4, 50, True, 1, 3, 0, 40)         # ahead: it lets the clock run
    assert not K.spike_wanted(3, 50, True, 1, -3, 0, 40) and not K.spike_wanted(2, 70, True, 1, 0, 0, 40)


def test_the_last_play_of_a_half_is_the_hail_mary_or_the_laterals_when_only_a_touchdown_helps():
    assert K.last_play_call(4, -6, 40, True) == K.HAIL_MARY
    assert K.last_play_call(4, -6, 80, True) == K.LATERALS
    assert K.last_play_call(4, -2, 20, True) == ""                # a field goal ties or wins it
    assert K.last_play_call(2, 0, 50, True) == K.HAIL_MARY        # a 67-yard kick is too long
    assert K.last_play_call(2, 0, 30, True) == "" and K.last_play_call(2, 0, 50, False) == ""


@pytest.mark.parametrize("margin", range(-16, 17))
def test_the_two_point_chart_in_the_last_ten_minutes_has_no_draw(margin):
    rnd = ScriptedRandom([], strict=True)
    assert K.goes_for_two(4, margin, rnd, left=K.CHART_SECONDS) == (margin in K.TWO_POINT_CHART)
    assert K.goes_for_two(5, margin, rnd, left=900) == (margin in K.TWO_POINT_CHART_OVERTIME)       # D-175: overtime keeps SX.12's chart


def test_the_chart_is_the_papers_and_earlier_one_draw_decides():
    assert K.TWO_POINT_CHART == frozenset((-10, -5, -2, 1, 2, 4, 5, 7))   # D-175: behind by 1 or 8 the league's coaches kick
    yes = ScriptedRandom([("below", 10000, K.TWO_POINT_EARLY - 1)], strict=True)
    no = ScriptedRandom([("below", 10000, K.TWO_POINT_EARLY)], strict=True)
    assert K.goes_for_two(2, -8, yes) is True and K.goes_for_two(4, -8, no, left=K.CHART_SECONDS + 1) is False
