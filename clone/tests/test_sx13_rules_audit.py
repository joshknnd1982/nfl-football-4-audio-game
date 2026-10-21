"""SX.13, the 2026 rules audit (nfl4 only, rule 0.13; spec/NFL_RULES_AUDIT_2026.md, D-097): one test for each difference between the
2026 book and the N. F. L. rules mode that the audit fixed, and for each match the audit found untested. This is inspired by Jim Kitchen.

The rule numbers are the 2026 Official Playing Rules of the NFL (Rule-Section-Article). The play tests force the outcome model's result
through the real engine (as test_sx10c_narration.py does) and read the board, the score and the step the engine reaches.
"""
import random

import pytest

from nfl4.extras import offense_flow as OF
from nfl4.extras import overtime as OT
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model as M
from nflrig import nfl_engine_rig

START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
UNTIL = ("next_play", "kick_off", "extra_point_choice", "extra_point", "score", "offense_menu", "play_menu", "game_end",
         "defense_menu", "after_score")


def rig_for(tmp_path, play, result, monkeypatch, extras=None, **state):
    """The player's offense (side 1, a West Coast book) calls `play`; the model's result is `result`; seeded draws for the rest."""
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=True, qb_on=False, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules, extras=extras, **fields)
    monkeypatch.setattr(M, "play", lambda concept, call, situation, rnd: result)
    s = rig.engine.s
    rules.offense.called = play
    s.offense_play = OF.engine_family(C.BY_ID[play])
    s.defense_play = 2
    rig.rnd.source = random.Random(11)
    return rig


def run_play(rig, until=UNTIL):
    step = rig.engine.snap
    while step is not None and step.__name__ not in until:
        step = step()
    return step.__name__ if step is not None else None


# ----- 4-8-2 (c): no try after a last-second touchdown that a try cannot change -----

@pytest.mark.parametrize("own, other, tried", [(20, 10, False), (10, 20, False), (10, 19, False), (14, 17, False), (14, 20, True),
                                               (12, 20, True), (13, 20, True), (10, 30, False)])
def test_a_touchdown_as_the_fourth_quarter_runs_out_has_a_try_only_when_the_try_can_change_the_result(tmp_path, monkeypatch, own,
                                                                                                        other, tried):
    rig = rig_for(tmp_path, "O001", M.Result("run", 70, gap="guard"), monkeypatch, quarter=4, extras=dict(left=2, running=True))
    s = rig.engine.s
    s.stats[1].score, s.stats[2].score = own, other
    step = run_play(rig)
    assert s.extras.left == 0 and s.stats[1].score == own + 6
    assert step == ("extra_point_choice" if tried else "game_end")


def test_a_return_touchdown_as_time_runs_out_has_no_try_when_it_cannot_matter(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("interception", 15, "slant", 3, 15, return_touchdown=True), monkeypatch,
                  quarter=4, extras=dict(left=2, running=True))
    s = rig.engine.s
    s.stats[1].score, s.stats[2].score = 10, 20
    assert run_play(rig) == "game_end" and s.stats[2].score == 26


@pytest.mark.parametrize("quarter", [1, 2, 3])
def test_a_last_second_touchdown_of_another_quarter_keeps_its_try(tmp_path, monkeypatch, quarter):
    rig = rig_for(tmp_path, "O001", M.Result("run", 70, gap="guard"), monkeypatch, quarter=quarter,
                  extras=dict(left=2, running=True, period=quarter, unit="H1" if quarter < 3 else "H2",
                              announced="H1" if quarter < 3 else "H2"))
    rig.engine.s.stats[2].score = 30
    assert run_play(rig) == "extra_point_choice"


def test_the_regular_seasons_overtime_period_has_the_fourth_quarters_rule(tmp_path, monkeypatch):
    """16-1-3 (e): the first team's touchdown as the one period runs out wins with no try; in a play-off period the try is played."""
    for postseason, expected in ((False, "game_end"), (True, "extra_point_choice")):
        folder = tmp_path / str(postseason)
        rig = rig_for(folder, "O001", M.Result("run", 70, gap="guard"), monkeypatch, quarter=5, overtime=1,
                      extras=dict(left=2, running=True, period=5, postseason=postseason, ot_phase=OT.FIRST, ot_first=1,
                                  ot_receiver=1, ot_base=10))
        s = rig.engine.s
        s.stats[1].score, s.stats[2].score = 10, 10
        assert run_play(rig) == expected, postseason
        if not postseason:
            assert s.extras.ot_phase == OT.OVER


def test_the_rule_reads_the_margin_after_the_six_points():
    from nfl4.game.gamestate import GameState, SideStats
    from nfl4.extras.state import ExtrasRecord
    x = ExtrasRecord()
    x.left = 0
    s = GameState(quarter=4)
    for margin, cannot in ((1, True), (0, False), (-1, False), (-2, False), (-3, True), (7, True)):
        s.stats = {1: SideStats(score=20 + margin), 2: SideStats(score=20)}
        assert OT.last_try_cannot_matter(x, s, 1) is cannot, margin
    x.left = 1
    assert OT.last_try_cannot_matter(x, s, 1) is False


# ----- 16-1-4 (e): the captain who lost the overtime toss has the first choice at the third play-off period -----

def third_period_rig(tmp_path, answers, loser):
    rules = NflRules(timeouts_on=True)
    rig = nfl_engine_rig(tmp_path, answers=answers, rules=rules, quarter=5, overtime=2, wisoff=1, defense=2, half=2, yard_line=40,
                         extras=dict(period=6, postseason=True, left=0, ot_phase=OT.SUDDEN, ot_first=2, ot_receiver=2,
                                     ot_toss_loser=loser))
    rig.rnd.source = random.Random(4)
    return rig


@pytest.mark.parametrize("answers, receiver", [([13, 13, 13], 1), ([13, 13, 40, 13], 2)])
def test_the_player_who_lost_the_toss_chooses_to_receive_or_kick_at_the_third_period(tmp_path, answers, receiver):
    from nfl4.game.rules import OT_KICK_OFF
    rig = third_period_rig(tmp_path, answers, loser=1)
    step = rig.engine.next_overtime_period(OT_KICK_OFF)
    s = rig.engine.s
    assert step.__name__ == "kick_off" and s.wisoff == receiver and s.defense == 3 - receiver and s.overtime == 3
    assert any(rig.engine.coach + " " in t or "receive" in t.lower() for t, _, _ in rig.said)


def test_the_computer_that_lost_the_toss_chooses_with_its_toss_share(tmp_path):
    from nfl4.game.rules import OT_KICK_OFF
    rig = third_period_rig(tmp_path, [13, 13], loser=2)
    rig.rules.overtime_kicks_first = lambda state: True              # its one draw said "kick"
    assert rig.engine.next_overtime_period(OT_KICK_OFF).__name__ == "kick_off" and rig.engine.s.wisoff == 1
    rig = third_period_rig(tmp_path / "r", [13, 13], loser=2)
    rig.rules.overtime_kicks_first = lambda state: False
    assert rig.engine.next_overtime_period(OT_KICK_OFF).__name__ == "kick_off" and rig.engine.s.wisoff == 2


def test_the_overtime_toss_records_its_loser_and_the_save_keeps_it(tmp_path):
    from nfl4.extras.state import ExtrasRecord
    rules = NflRules(timeouts_on=True)
    rig = nfl_engine_rig(tmp_path, rules=rules, quarter=5, overtime=1)
    rig.engine.g.season.vtrnt = 1                                    # the computer calls: heads (1); the coin: heads (1): it wins
    from randsources import ScriptedRandom
    rig.rnd.source = ScriptedRandom([0.0, 0.0, 0.0], strict=False)
    rig.engine.overtime_coin_toss()
    x = rig.engine.s.extras
    assert x.ot_toss_loser == 1
    assert ExtrasRecord.from_json(x.to_json()).ot_toss_loser == 1


# ----- 16-1-3 (e), 16-1-4 (h), 4-3-2 (a), (e): the clock's late windows in overtime -----

@pytest.mark.parametrize("period, postseason, left, late", [
    (5, False, 400, False), (5, False, 301, False), (5, False, 300, True), (5, False, 10, True),     # the fourth period's timing
    (5, True, 100, False), (6, True, 121, False), (6, True, 120, True), (7, True, 30, False),        # play-offs: OT2 as a first half
    (8, True, 301, False), (8, True, 300, True), (10, True, 120, True), (12, True, 300, True)])       # OT4 as the fourth period
def test_the_late_windows_of_overtime(period, postseason, left, late):
    from nfl4.extras import clock as CL
    from nfl4.extras import penalty_flow as PF
    assert CL.late_window(5, left, period, postseason) is late
    assert PF.late_for_fouls(5, left, period, postseason) is late


@pytest.mark.parametrize("postseason, expected", [(False, (False, False)), (True, (True, True))])
def test_an_offense_foul_before_the_snap_stops_the_clock_to_the_snap_only_in_the_regular_seasons_overtime(postseason, expected):
    """4-3-2 (e)(3) names the fourth period and the regular season's overtime; a play-off period 1 at 10:00 is as if no foul."""
    from nfl4.extras import penalty_flow as PF
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord(left=600, foul_clock="pre", foul_by_offense=True, was_running=True, period=5, postseason=postseason)
    assert PF.clock_after_foul(record, 5, False) == expected


# ----- 6-1-2 (e), 6-1-4 (d)(3), 6-2-4, 6-1-5: free kicks that are not made from the 35 -----

class Seeded:
    def __init__(self, seed):
        self.src = random.Random(seed)

    def below(self, n):
        return int(self.src.random() * n)


def old_kickoff(kind, rnd, spot=35, touchback_pct=100):
    """SX.10d's kick-off as it was (the reference: a kick from the 35 must draw exactly what it drew)."""
    from nfl4.extras.plays.model_data import KICKOFF_2025, KICKOFF_2026, KICKOFF_RETURN
    if kind == "onside":
        return M.KickResult("onside")
    if M.chance(rnd, KICKOFF_2026["out_of_bounds"]):
        return M.KickResult("out_of_bounds", 40)
    if kind == "squib" and M.chance(rnd, M.SQUIB_SHORT):
        return M.KickResult("landed_short", 40)
    if M.chance(rnd, M.KICK_TOUCHBACK.get(kind, 0) * touchback_pct // 100):
        return M.KickResult("touchback", 35)
    if M.chance(rnd, KICKOFF_2025["return_td"]):
        return M.KickResult("returned", 100, 100, True)
    catch = M.between(rnd, *M.KICK_CATCH[kind]) + (35 - spot)
    low, high = KICKOFF_RETURN[M.pick(rnd, [w for _r, w in KICKOFF_RETURN])][0]
    back = M.between(rnd, low, high) * M.KICK_RETURN_SCALE[kind] // 100
    start = catch + back
    if start >= 100:
        return M.KickResult("returned", 100, back, True)
    return M.KickResult("returned", max(1, start), back)


@pytest.mark.parametrize("kind", ["deep", "short", "squib"])
def test_a_kick_off_from_the_35_draws_exactly_what_it_drew_before(kind):
    a, b = Seeded(5), Seeded(5)
    for _ in range(3000):
        assert M.kickoff(kind, a) == old_kickoff(kind, b)
    assert a.src.random() == b.src.random()


def test_the_receivers_ball_after_a_short_or_out_of_bounds_free_kick():
    assert M.short_kick_spot(35) == 40                     # 25 yards from the kick
    assert M.short_kick_spot(30) == 45                     # a kick made again from the 30
    assert M.short_kick_spot(20, safety=True) == 50        # a safety kick: 30 yards
    assert M.short_kick_spot(15, safety=True) == 55        # a safety kick made again 5 yards back
    assert M.short_kick_spot(20, safety=True, landed=62) == 62    # it came down less than 30 yards from the kick: that spot


@pytest.mark.parametrize("spot, safety", [(20, True), (30, False), (25, True)])
@pytest.mark.parametrize("kind", ["deep", "short", "squib"])
def test_a_free_kick_from_another_spot_is_never_returned_from_short_of_the_landing_zone(kind, spot, safety):
    rnd = Seeded(spot * 7 + len(kind))
    least = M.short_kick_spot(spot, safety)
    for _ in range(4000):
        r = M.kickoff(kind, rnd, spot=spot, touchback_pct=T.SAFETY_KICK_TOUCHBACK, safety=safety)
        if r.kind == "returned" and not r.touchdown:
            assert r.start - r.returned <= M.LANDING_ZONE_FRONT, r
        if r.kind in ("landed_short", "out_of_bounds"):
            assert r.start >= least, r


@pytest.mark.parametrize("given, expected", [
    (M.KickResult("touchback", 20, gross=85), M.KickResult("punt_touchback", 35, gross=85)),
    (M.KickResult("fair_catch", 30, gross=50), M.KickResult("landed_short", 50, gross=50)),
    (M.KickResult("returned", 41, 11, gross=50), M.KickResult("landed_short", 50, gross=50)),
    (M.KickResult("returned", 25, 10, gross=65), M.KickResult("returned", 25, 10, gross=65)),
    (M.KickResult("out_of_bounds", 12, gross=68), M.KickResult("out_of_bounds", 50, gross=68)),
    (M.KickResult("downed", 6, gross=74), M.KickResult("dead", 6, gross=74)),
    (M.KickResult("dead", 15, gross=65), M.KickResult("dead", 15, gross=65)),
    (M.KickResult("fair_catch", 18, gross=62), M.KickResult("fair_catch", 18, gross=62)),
    (M.KickResult("dead", 66, gross=14), M.KickResult("landed_short", 66, gross=14)),
])
def test_the_safety_punt_is_read_as_the_free_kick_it_is(given, expected):
    from nfl4.extras.kick_flow import KickFlow
    assert KickFlow.safety_punt(given, 20, True) == expected


def test_after_a_safety_the_computer_kicks_deep_with_no_draw_and_a_safety_kick_made_again_stays_one(tmp_path):
    from randsources import ScriptedRandom
    rules = NflRules(timeouts_on=False, onside_on=False, offense_book="west", defense_book="pressure")
    rig = nfl_engine_rig(tmp_path, rules=rules, wisoff=1, defense=2, half=2, yard_line=0)
    x = rig.engine.s.extras
    rig.rnd.source = ScriptedRandom([], strict=True)
    x.safety_kick = True
    rules.before_kickoff(rig.engine.s, 2)
    assert x.kick_call == "K001" and x.kick_from == 20 and x.free_after_safety is True
    x.kick_again, x.kick_back = True, 5
    rules.before_kickoff(rig.engine.s, 2)
    assert x.kick_from == 15 and x.free_after_safety is True
    rig.rnd.source = random.Random(3)
    rules.before_kickoff(rig.engine.s, 2)                  # the next kick-off is an ordinary one
    assert x.kick_from == 35 and x.free_after_safety is False
