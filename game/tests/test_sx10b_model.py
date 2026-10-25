"""The outcome models against the NFL's numbers (nfl4 only, rule 0.13; NX-P3; design `spec/NFL_PLAYS_DESIGN.md` section 4; SX.10b).
This is inspired by Jim Kitchen.

Each model runs under the league's defensive mix (the coverage, blitz, rusher and box shares of model_data) and is compared with
the numbers the data gives (work/sx10b/data_numbers_sx10b.txt). The tolerances are about three standard errors of the sample
plus what the design accepts (design 4.11 names each). Seeded, so a failure repeats.
"""
import random

import pytest

from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model as X
from nfl4.extras.plays import model_data as M


class Rnd:
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.draws = 0

    def below(self, n):
        self.draws += 1
        return int(self.r.random() * n)


class Scripted:
    """Gives the numbers it was given (each must be below the n asked for) and fails on a draw it was not given."""

    def __init__(self, numbers):
        self.numbers = list(numbers)

    def below(self, n):
        value = self.numbers.pop(0)
        assert 0 <= value < n, (value, n)
        return value


def league_call(rnd, for_run=False):
    covs = [(k, v) for k, v in M.COVERAGE_SHARE.items() if k in M.COVERAGE_BANDS]
    cov = covs[X.pick(rnd, [v for _k, v in covs])][0]
    blitz = X.chance(rnd, M.COVERAGE_BANDS[cov][3])
    rushers = (6 if X.chance(rnd, 2500) else 5) if blitz else (3 if X.chance(rnd, 500) else 4)
    if for_run:
        box = list(M.BOX_SHARE_ON_RUNS)[X.pick(rnd, list(M.BOX_SHARE_ON_RUNS.values()))]
    else:
        box = 6 if cov in M.TWO_HIGH else 7
    return C.Call("test", 5, box, cov, rushers, blitz, ())


def route_concept(route):
    kind = "screen" if route == "screen" else "pass"
    return C.Concept("T" + route, "O", route, "og06", kind, (((route, 100),), 100, 0, 0), "shotgun")


def stats(results):
    drops = len(results)
    thrown_away = sum(1 for r in results if r.branch == "thrown_away")
    att = [r for r in results if r.kind in ("complete", "incomplete", "interception")]
    targeted = [r for r in att if r.branch != "thrown_away"]
    comp = [r for r in att if r.kind == "complete"]
    return {
        "sack": 100 * sum(1 for r in results if r.kind == "sack" or (r.kind == "fumble" and not r.route)) / drops,
        "away": 100 * thrown_away / drops,
        "comp": 100 * len(comp) / len(att),
        "comp_targeted": 100 * len(comp) / len(targeted),
        "int": 100 * sum(1 for r in att if r.kind == "interception") / len(att),
        "ypa": sum(r.yards for r in comp) / len(att),
        "ypt": sum(r.yards for r in comp) / len(targeted),
    }


OPEN = X.Situation(to_goal=99)


def test_league_passing_matches_2024_and_2025(monkeypatch):
    # the model alone at SACK_SCALE 100 (its own calibration, design 4.11); SX.10e set the game's scale so the ENGINE's sacks, after the
    # scrambles and the grounding and with the in-game mix of plays, are 6.5 percent (test_sx10e_games.py)
    monkeypatch.setattr(X, "SACK_SCALE", 100)
    rnd = Rnd(1)
    routes = list(M.ROUTE_SHARE)
    weights = [M.ROUTE_SHARE[r] for r in routes]
    out = [X.pass_play(route_concept(routes[X.pick(rnd, weights)]), league_call(rnd), OPEN, rnd) for _ in range(15000)]
    s = stats(out)
    assert abs(s["comp"] - 65.1) <= 2.0
    assert abs(s["int"] - 2.2) <= 0.6
    assert abs(s["ypa"] - 7.11) <= 0.45
    assert abs(s["sack"] - 6.5) <= 1.0
    assert abs(s["away"] - 3.6) <= 0.8


@pytest.mark.parametrize("route", list(M.ROUTES))
def test_each_route_matches_its_charted_numbers(route):
    rnd = Rnd(hash(route) % 1000)
    out = [X.pass_play(route_concept(route), league_call(rnd), OPEN, rnd) for _ in range(5000)]
    s = stats(out)
    shares, comp, ints, yac, man, zone, oob = M.ROUTES[route]
    assert abs(s["comp_targeted"] - comp / 100) <= 3.0, s
    assert abs(s["int"] - ints / 100) <= 1.6, s


def test_man_coverages_allow_fewer_completions_than_zones_and_each_is_near_its_data():
    data = {"COVER_0": 54.6, "COVER_1": 58.6, "COVER_2": 71.1, "2_MAN": 60.9, "COVER_3": 69.3, "COVER_4": 68.5,
            "COVER_6": 66.9, "COVER_9": 64.4}
    rnd = Rnd(2)
    routes = list(M.ROUTE_SHARE)
    weights = [M.ROUTE_SHARE[r] for r in routes]
    comp = {}
    for cov in data:
        out = []
        for _ in range(5000):
            blitz = X.chance(rnd, M.COVERAGE_BANDS[cov][3])
            call = C.Call("t", 5, 6 if cov in M.TWO_HIGH else 7, cov, 5 if blitz else 4, blitz, ())
            out.append(X.pass_play(route_concept(routes[X.pick(rnd, weights)]), call, OPEN, rnd))
        comp[cov] = stats(out)["comp"]
        assert abs(comp[cov] - data[cov]) <= 5.0, (cov, comp[cov])
    assert max(comp[k] for k in ("COVER_0", "COVER_1", "2_MAN")) < min(comp[k] for k in ("COVER_2", "COVER_3"))


@pytest.mark.parametrize("gap,ypc", [("middle", 4.30), ("guard", 4.43), ("tackle", 4.70), ("end", 5.15)])
def test_runs_by_gap_outside_the_10_match_the_data(gap, ypc):
    rnd = Rnd(3)
    concept = C.Concept("R", "O", gap, "og01", "run", (gap, 0), "singleback")
    out = [X.run_play(concept, league_call(rnd, True), X.Situation(to_goal=80), rnd) for _ in range(12000)]
    mean = sum(r.yards for r in out) / len(out)
    assert abs(mean - ypc) <= 0.3
    stuffed = 100 * sum(1 for r in out if r.yards <= 0) / len(out)
    data_stuffed = (M.RUN_BY_GAP[gap][0] + M.RUN_BY_GAP[gap][1]) / 100
    assert abs(stuffed - data_stuffed) <= 3.0
    fumbles = 100 * sum(1 for r in out if r.kind == "fumble") / len(out)
    assert abs(fumbles - 0.9) <= 0.35


def test_more_defenders_in_the_box_stop_runs_as_the_data_says():
    rnd = Rnd(4)
    concept = C.Concept("R", "O", "x", "og01", "run", ("guard", 0), "singleback")
    means = {}
    for box in (5, 6, 7, 8):
        call = C.Call("t", 5, box, "COVER_3", 4, False, ())
        out = [X.run_play(concept, call, X.Situation(to_goal=80), rnd) for _ in range(12000)]
        means[box] = sum(r.yards for r in out) / len(out)
    assert means[5] > means[6] > means[7] > means[8]
    assert abs((means[8] - means[6]) - (4.20 - 4.74)) <= 0.4


@pytest.mark.parametrize("shift", [-60, -20, 30, 80])
def test_a_shift_moves_the_mean_by_its_hundredths_of_a_yard(shift):
    bins = list(M.RUN_BY_GAP["guard"])

    def mean(b):
        return sum(w * m for w, m in zip(b, X.RUN_MEANS)) / sum(b)
    moved = mean(X.shift_bins(bins, shift)) - mean(bins)
    assert abs(moved - shift / 100) <= 0.05


def test_quarterback_runs_and_the_sneak():
    rnd = Rnd(5)
    neutral = C.Call("t", 5, 7, "COVER_3", 4, False, ())
    keeps = [X.play(C.BY_ID["O047"], league_call(rnd, True), X.Situation(to_goal=80), rnd) for _ in range(12000)]
    assert abs(sum(r.yards for r in keeps) / len(keeps) - 4.87) <= 0.45
    sneaks = [X.play(C.BY_ID["O046"], neutral, X.Situation(to_goal=40, down=3, distance=1), rnd) for _ in range(8000)]
    assert abs(100 * sum(1 for r in sneaks if r.yards >= 1) / len(sneaks) - 81.8) <= 4.0


def test_play_action_gains_more_than_the_same_routes_without_the_fake():
    rnd = Rnd(6)
    routes = "hitch 40 dig 30 post 30"
    bits = routes.split()
    pairs = tuple((bits[i], int(bits[i + 1])) for i in range(0, len(bits), 2))
    plain = C.Concept("A", "O", "a", "og06", "pass", (pairs, 100, 0, 0), "shotgun", strong=("x",), weak=("y",))
    fake = plain._replace(kind="play_action", formation="under_center")
    a = stats([X.pass_play(plain, league_call(rnd), OPEN, rnd) for _ in range(12000)])
    b = stats([X.pass_play(fake, league_call(rnd), OPEN, rnd) for _ in range(12000)])
    assert 0.5 <= b["ypa"] - a["ypa"] <= 2.2          # data: 8.10 against 6.81 (design 4.4)
    assert b["sack"] < a["sack"] and b["int"] < a["int"]


def test_screens_complete_like_the_data_and_are_almost_never_sacked():
    rnd = Rnd(7)
    out = [X.play(C.BY_ID[i], league_call(rnd), OPEN, rnd) for i in ("O017", "O018", "O021") for _ in range(3000)]
    s = stats(out)
    assert abs(s["comp"] - 86.0) <= 4.0 and s["sack"] < 1.0 and abs(s["ypa"] - 5.59) <= 0.8


def test_the_run_pass_options_throw_about_a_quarter_of_the_time():
    rnd = Rnd(8)
    out = [X.play(C.BY_ID["O131"], league_call(rnd, True), X.Situation(to_goal=80), rnd) for _ in range(10000)]
    thrown = [r for r in out if r.branch == "throw"]
    assert abs(100 * len(thrown) / len(out) - 26) <= 6
    att = [r for r in thrown if r.kind in ("complete", "incomplete", "interception")]
    assert 100 * sum(1 for r in att if r.kind == "complete") / len(att) >= 80          # data: 84.1 (bubbles and flats)
    given = [r for r in out if r.branch == "give"]
    assert abs(sum(r.yards for r in given) / len(given) - 4.57) <= 0.5


def test_the_read_option_reads_the_call():
    rnd = Rnd(9)
    crash = C.Call("t", 4, 8, "COVER_1", 5, True, ("run_blitz",))
    home = C.Call("t", 4, 7, "COVER_3", 4, False, ("qb_contain", "contain"))
    keep_crash = sum(1 for _ in range(4000) if X.play(C.BY_ID["O124"], crash, OPEN, rnd).branch == "keep") / 4000
    keep_home = sum(1 for _ in range(4000) if X.play(C.BY_ID["O124"], home, OPEN, rnd).branch == "keep") / 4000
    assert keep_crash > 0.8 and keep_home < 0.2


def test_passes_inside_the_10_complete_like_the_data():
    rnd = Rnd(10)
    routes = list(M.ROUTE_SHARE)
    weights = [M.ROUTE_SHARE[r] for r in routes]
    pairs = []
    for _ in range(12000):
        to_goal = 1 + rnd.below(10)
        pairs.append((to_goal, X.pass_play(route_concept(routes[X.pick(rnd, weights)]), league_call(rnd),
                                           X.Situation(to_goal=to_goal), rnd)))
    assert abs(stats([r for _g, r in pairs])["comp"] - 52.7) <= 4.0
    assert all(r.yards <= g for g, r in pairs if r.kind == "complete")
    assert all(r.yards <= g + 9 for g, r in pairs if r.kind == "interception")       # caught in the end zone at the deepest


def test_two_point_tries_from_the_2_against_goal_line_defenses():
    rnd = Rnd(11)
    calls = [C.BY_ID[i].params for i in ("D001", "D002", "D031", "D032", "D034", "D086")]
    try_spot = X.Situation(to_goal=2, down=1, distance=2)

    def rate(ids):
        made = total = 0
        for cid in ids:
            for _ in range(2000):
                r = X.play(C.BY_ID[cid], calls[rnd.below(len(calls))], try_spot, rnd)
                made += r.kind in ("run", "complete") and r.yards >= 2
                total += 1
        return 100 * made / total
    assert abs(rate(("O002", "O150", "O046")) - 54.1) <= 10
    assert abs(rate(("O031", "O148", "O149", "O078", "O027")) - 42.2) <= 12


@pytest.mark.parametrize("distance", [25, 35, 42, 47, 52, 57])
def test_field_goals_by_distance(distance):
    rnd = Rnd(distance)
    made = 100 * sum(1 for _ in range(6000) if X.field_goal(distance, "", rnd).kind == "made") / 6000
    expect = X.field_goal_rate(distance)[0] / 100
    assert abs(made - expect) <= 1.8
    band = next(row for row in M.FIELD_GOAL if row[0][0] <= distance <= row[0][1])
    assert abs(made - band[1] / 100) <= 4.0


def test_a_long_field_goal_is_allowed_and_rarely_made():
    assert 0 < X.field_goal_rate(64)[0] < 5000 and X.field_goal_rate(75)[0] < 1500


def test_the_extra_point_misses_sometimes():
    rnd = Rnd(12)
    good = 100 * sum(1 for _ in range(12000) if X.extra_point("", rnd).kind == "good") / 12000
    assert abs(good - 95.2) <= 0.8


def test_the_2026_kickoff_mix_gives_the_touchbacks_and_the_start_of_2026():
    rnd = Rnd(13)
    out = [X.kickoff("deep" if rnd.below(100) < 55 else "short", rnd) for _ in range(12000)]
    touchbacks = 100 * sum(1 for r in out if r.kind == "touchback") / len(out)
    assert abs(touchbacks - 15.6) <= 2.5
    start = sum(r.start for r in out if not r.touchdown) / sum(1 for r in out if not r.touchdown)
    assert abs(start - 30.3) <= 1.5
    assert {r.start for r in out if r.kind == "touchback"} == {35}
    assert all(r.start == 40 for r in out if r.kind == "out_of_bounds")


def test_a_squib_that_lands_short_gives_the_ball_at_the_40():
    rnd = Scripted([9999, 0])          # out of bounds: no (9999 is past its 80); landed short: yes (0 is below 1500)
    assert X.kickoff("squib", rnd) == X.KickResult("landed_short", 40)


def test_punts_from_their_usual_spots_match_the_data():
    rnd = Rnd(14)
    out = [X.punt("spread", 50 + rnd.below(31), "return", rnd) for _ in range(15000)]
    share = {k: 100 * sum(1 for r in out if r.kind == k) / len(out) for k in
             ("blocked", "touchback", "fair_catch", "downed", "out_of_bounds", "returned", "muffed")}
    data = {"blocked": 0.5, "touchback": 7.6, "fair_catch": 27.2, "downed": 11.7, "out_of_bounds": 10.2, "returned": 36.4,
            "muffed": 0.9}
    for kind, value in data.items():
        assert abs(share[kind] - value) <= 3.5, (kind, share[kind])
    gross = [r.gross for r in out if r.gross]
    assert abs(sum(gross) / len(gross) - 47.2) <= 1.5


def test_every_punt_spot_is_the_receivers_yard_line_from_their_own_goal():
    rnd = Rnd(18)
    for to_goal in (40, 55, 70, 85):
        for _ in range(3000):
            r = X.punt("spread", to_goal, "block", rnd)
            if r.kind == "blocked":
                assert to_goal < r.start <= 99              # behind the line of scrimmage, the receivers' side is farther
            elif r.kind in ("fair_catch", "downed", "out_of_bounds", "dead", "muffed"):
                assert 1 <= r.start < to_goal               # downfield of the line
            elif r.kind == "touchback":
                assert r.start == 20


def test_a_pin_punt_lands_closer_and_is_returned_less():
    rnd = Rnd(15)
    pin = [X.punt("pin", 55, "return", rnd) for _ in range(6000)]
    spread = [X.punt("spread", 55, "return", rnd) for _ in range(6000)]
    assert sum(1 for r in pin if r.kind == "returned") < sum(1 for r in spread if r.kind == "returned")
    assert sum(r.start for r in pin if not r.touchdown) < sum(r.start for r in spread if not r.touchdown)


def test_turnover_returns_match_the_data():
    rnd = Rnd(16)
    returns = [X.interception_return(rnd) for _ in range(20000)]
    assert abs(100 * sum(1 for _y, td in returns if td) / len(returns) - 7.4) <= 0.6
    plain = [y for y, td in returns if not td]
    assert abs(100 * sum(1 for y in plain if y == 0) / len(plain) - 43.0 / 0.926) <= 2.5
    sacks = [X.fumble(rnd, "sack") for _ in range(20000)]
    assert abs(100 * sum(1 for f, _l, _t in sacks if f) / len(sacks) - 11.4) <= 0.8


def test_every_offense_concept_gives_a_result_against_every_kind_of_call():
    rnd = Rnd(17)
    calls = [c.params for c in C.DEFENSE]
    for concept in C.OFFENSE:
        for call in calls[::7]:
            for to_goal in (99, 30, 8, 1):
                r = X.play(concept, call, X.Situation(to_goal=to_goal, down=1, distance=min(10, to_goal)), rnd)
                assert r.kind in ("run", "complete", "incomplete", "sack", "interception", "fumble", "kneel", "spike")
                assert -25 <= r.yards <= to_goal + 9, (concept.id, r)
                if r.kind in ("run", "complete"):
                    assert r.yards <= to_goal


def test_no_best_play_every_concept_has_a_call_it_is_weak_against_and_every_call_a_play_it_is_weak_against():
    tags = [X.call_tags(c.params) for c in C.DEFENSE]
    for concept in C.OFFENSE:
        assert any(X.matchup(concept, t) < 0 for t in tags), concept.id
        assert any(X.matchup(concept, t) > 0 for t in tags), concept.id
    for call, t in zip(C.DEFENSE, tags):
        assert any(X.matchup(concept, t) > 0 for concept in C.OFFENSE), call.id


def test_the_same_seed_gives_the_same_plays_and_one_value_ranges_draw_nothing():
    a = [X.play(C.BY_ID["O027"], C.BY_ID["D017"].params, OPEN, Rnd(99)) for _ in range(5)]
    b = [X.play(C.BY_ID["O027"], C.BY_ID["D017"].params, OPEN, Rnd(99)) for _ in range(5)]
    assert a == b
    rnd = Scripted([])
    assert X.between(rnd, 4, 4) == 4


def test_a_scripted_source_reaches_a_sack():
    # the first draw is the sack test: 0 is below any sack rate; then the sack's yards (the first row, no gain) and no fumble
    rnd = Scripted([0, 0, 9999])
    result = X.pass_play(C.BY_ID["O032"], C.BY_ID["D011"].params, OPEN, rnd)
    assert result == X.Result("sack", 0)


def test_the_models_read_no_engine_module():
    import ast
    from pathlib import Path
    folder = Path(X.__file__).resolve().parent
    for name in ("model.py", "model_data.py", "catalog.py"):
        tree = ast.parse((folder / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.level == 1 or node.module == "__future__" or node.module == "typing", (name, node.module)
