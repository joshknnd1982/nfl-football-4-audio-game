"""SX.13, the 2026 rules audit (nfl4 only, rule 0.13; spec/NFL_RULES_AUDIT_2026.md, D-097): one test for each difference between the
2026 book and the N. F. L. rules mode that the audit fixed, and for each match the audit found untested. This is inspired by Jim Kitchen.

The rule numbers are the 2026 Official Playing Rules of the NFL (Rule-Section-Article). The play tests force the outcome model's result
through the real engine (as test_sx10c_narration.py does) and read the board, the score and the step the engine reaches.
"""
import random

import pytest

from nfl4.extras import offense_flow as OF
from nfl4.extras import overtime as OT
from nfl4.extras import nx_texts as X
from nfl4.extras import rules_2026 as R
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


def test_a_safety_kick_out_of_bounds_or_short_is_said_with_its_spot(tmp_path):
    from test_sx10d_kicks import given, rig_for as kicks_rig, run as run_from, texts
    for kind, row in (("out_of_bounds", "NXB-J25"), ("landed_short", "NXB-J26")):
        rig = kicks_rig(tmp_path / kind, wisoff=1, defense=2, half=2, yard_line=0)
        rig.engine.s.extras.kick_call = "K001"
        given(rig, kickoff_result=M.KickResult(kind, 50))
        mark = len(rig.said)
        assert run_from(rig, rig.engine.kickoff_2026) == "down_sentence"
        assert X.text(row, n=50) in texts(rig, mark) and rig.engine.s.yard_line == 50


# ----- 9-3, 11-5-1, 11-2: a punt blocked behind the kicking team's own goal line -----

def test_a_punt_blocked_behind_the_own_goal_line_is_a_safety_or_the_receivers_touchdown():
    rnd = Seeded(9)
    seen = set()
    for _ in range(60000):
        r = M.punt("spread", 95, "block", rnd)
        if r.kind == "blocked":
            assert r.start == 100, r                        # 95 yards from the receivers' goal plus 5 to 12 behind: the end zone
            seen.add(r.touchdown)
    assert seen == {True, False}
    for _ in range(20000):
        r = M.punt("spread", 60, "block", rnd)
        assert r.kind != "blocked" or r.start < 100


@pytest.mark.parametrize("touchdown, receivers_points", [(False, 2), (True, 6)])
def test_the_engine_tells_the_end_zone_block(tmp_path, touchdown, receivers_points):
    from test_sx10d_kicks import given, punting, run as run_from, texts
    rig = punting(tmp_path, wisoff=1, defense=2, half=2, yard_line=5)
    given(rig, kick_result=M.KickResult("blocked", 100, touchdown=touchdown, defense_recovers=touchdown))
    mark = len(rig.said)
    run_from(rig, rig.engine.punt)
    s = rig.engine.s
    assert s.score(2) == receivers_points and s.score(1) == 0
    said = texts(rig, mark)
    if touchdown:
        assert any("falls on it in the end zone" in t for t in said)
    else:
        assert X.text("NXB-J28") in said and s.extras.safety_kick is True


# ----- 3-36-2, 4-5-1 Item 3: the T key's timeout and the dead-ball period -----

def clock_rig(tmp_path, **extras):
    values = dict(timeouts_on=True, period=4, unit="H2", announced="H2", plays=1, handled=0, last_kind="run", last_offense=1)
    values.update(extras)
    rules = NflRules(timeouts_on=True)
    rig = nfl_engine_rig(tmp_path, rules=rules, quarter=4, wisoff=1, defense=2, half=2, yard_line=40, extras=values)
    rig.rnd.source = random.Random(2)
    return rig, rules


def test_a_t_kept_during_the_play_stops_the_clock_when_the_play_ends(tmp_path):
    from nfl4.game import outcome as O
    rig, rules = clock_rig(tmp_path, left=12, last_kind=O.RUN)
    rules.timeout_kept = True
    rules.between_plays(rig.engine.s)
    x = rig.engine.s.extras
    assert x.left == 12 and x.pending == 0 and x.running is False and x.used[0] == 1


def test_a_snap_or_a_kick_ends_the_dead_ball_period(tmp_path):
    rig, rules = clock_rig(tmp_path, left=300)
    x = rig.engine.s.extras
    x.called = [True, True]
    rig.engine.go_live()                                     # the kick-off, a punt, a kicked try: the ball is live
    assert x.called == [False, False]


def test_a_timeout_may_be_called_before_a_try_at_0_00_and_not_after_it(tmp_path):
    from nfl4.game.rules import TIMEOUT_GRANTED, TIMEOUT_REFUSED
    rig, rules = clock_rig(tmp_path, left=0, period=2, unit="H1", announced="H1")
    rig.engine.s.quarter = 2
    rules.try_due = True
    assert rules.timeout_key(rig.engine.s, False) == TIMEOUT_GRANTED
    rules.try_due = False
    rig.engine.s.extras.called = [False, False]
    assert rules.timeout_key(rig.engine.s, False) == TIMEOUT_REFUSED


def test_a_touchdown_makes_the_try_due_and_the_kick_ends_it(tmp_path):
    rig, rules = clock_rig(tmp_path, left=0, period=2, unit="H1", announced="H1")
    s = rig.engine.s
    s.quarter = 2                                            # the second quarter keeps its try (4-8-2 (c) is the fourth's)
    s.stats[1].score = 6
    assert rules.points_end_game(s, 1) is False and rules.try_due is True
    rules.ball_live(s)
    assert rules.try_due is False


# ----- 4-3-1 (b): an onside kick the kicking team recovers starts no clock -----

def test_an_onside_kick_the_kickers_keep_takes_no_time():
    from nfl4.extras import clock as CL
    from nfl4.game import outcome as O
    from nfl4.game.gamestate import GameState
    rnd = Seeded(1)
    kept = O.PlayOutcome(O.ONSIDE_KICK, 1, 0, 0, turnover=True)
    lost = O.PlayOutcome(O.ONSIDE_KICK, 1, 0, 0, turnover=False)
    assert CL.live_time(kept, GameState(), rnd) == 0
    assert CL.live_time(lost, GameState(), rnd) >= T.LIVE_ONSIDE[0]


# ----- 15-5-2, 4-7-4: the ten seconds after a reversal of a play that began after the warning -----

@pytest.mark.parametrize("left, after", [(40, 30), (11, 1), (8, 0)])
def test_a_reversal_after_the_warning_to_a_running_clock_runs_ten_seconds_off(tmp_path, left, after):
    from nfl4.game import outcome as O
    rig, rules = clock_rig(tmp_path, left=left, warning_given=True, last_kind=O.RUN)
    rules.review.runoff_due = True
    mark = len(rig.said)
    rules.between_plays(rig.engine.s)
    x = rig.engine.s.extras
    assert x.left == after and X.text("NXP-12") in [t for t, _, _ in rig.said[mark:]]
    assert x.pending <= R.RUNOFF_PLAY_CLOCK
    if after == 0:
        assert x.pending == 0 and rig.engine.clock.period_over()


def test_a_timeout_avoids_the_ten_seconds_and_a_stopped_clock_has_none(tmp_path):
    from nfl4.game import outcome as O
    rig, rules = clock_rig(tmp_path, left=40, warning_given=True, last_kind=O.RUN)
    rules.review.runoff_due = True
    rules.timeout_kept = True
    rules.between_plays(rig.engine.s)
    assert rig.engine.s.extras.left == 40 and rig.engine.s.extras.used[0] == 1
    rig, rules = clock_rig(tmp_path / "inc", left=40, warning_given=True, last_kind=O.PASS_INCOMPLETE)
    rules.review.runoff_due = True
    mark = len(rig.said)
    rules.between_plays(rig.engine.s)
    assert rig.engine.s.extras.left == 40 and X.text("NXP-12") not in [t for t, _, _ in rig.said[mark:]]
    assert rules.review.runoff_due is False


def test_a_play_across_the_two_minutes_is_still_a_coachs():
    """15-1-2 (a): only a play that BEGINS after the warning is the replay official's (the warning is due, not yet given)."""
    from nfl4.extras import review as RV
    from nfl4.extras.state import ExtrasRecord
    from nfl4.game import outcome as O
    from test_nx_review_rules import outcome, state_of
    record = ExtrasRecord()
    record.warning_due, record.warning_given = True, False
    assert RV.booth_reason(state_of(quarter=4, down=2, to_go=5), outcome(O.RUN, yards=4), record) == ""
    record.warning_due, record.warning_given = False, True
    assert RV.booth_reason(state_of(quarter=4, down=2, to_go=5), outcome(O.RUN, yards=4), record) == "warning"


def test_a_timeout_and_a_lost_challenge_cost_two_timeouts(tmp_path):
    """15-6-1: a team that takes a timeout and then challenges unsuccessfully is charged a second one."""
    from pagrig import Draws
    from test_nx_review_fixes import timeout_scene
    from test_nx_review_flows import CLOSE, ENTER, ESCAPE, the_menu
    rig = timeout_scene(tmp_path, ["t", "c", ENTER, "y", ENTER, ESCAPE], ruling=CLOSE())
    the_menu(rig, Draws().below(6, 1).rady().rady())
    x = rig.engine.s.extras
    assert x.timeouts == [1, 3] and x.used == [2, 0]


# ----- 4-7-1 (a) and Item 2: the runoff for delay of game, and a defense foul's ready signal -----

def test_delay_of_game_after_the_warning_offers_the_ten_second_runoff():
    from nfl4.extras import fouls_2026 as F
    delay = F.BY_ID["P02"][0]
    assert delay.code == "DOG" and delay.code not in R.NO_RUNOFF_FOULS and delay.offense_side and F.DEAD in delay.phases


@pytest.mark.parametrize("leads, expected", [(True, (True, True)), (False, (False, False)), (None, (False, False))])
def test_a_defense_foul_after_the_warning_lets_a_leading_offense_run_the_clock(leads, expected):
    from nfl4.extras import penalty_flow as PF
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord(left=100, foul_clock="pre", foul_by_offense=False, was_running=True, warning_given=True, period=4)
    assert PF.clock_after_foul(record, 4, False, leads) == expected      # None (not asked): the late window, on the snap
    before = ExtrasRecord(left=400, foul_clock="pre", foul_by_offense=False, was_running=True, warning_given=False, period=4)
    assert PF.clock_after_foul(before, 4, False, leads) == (True, True)   # before the warning: as if no foul


# ----- 4-8-2 (a), (e), (h): the untimed down in overtime, after offsetting fouls and for the fair catch kick -----

def penalty_state(quarter, postseason=False):
    from nfl4.extras.state import ExtrasRecord
    from nfl4.game.gamestate import GameState
    s = GameState(quarter=quarter, wisoff=1, defense=2)
    s.extras = ExtrasRecord(left=0, postseason=postseason, period=quarter if quarter <= 4 else 5)
    return s


def test_an_accepted_defense_foul_extends_the_regular_seasons_overtime_period():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import penalties as PEN
    from nfl4.extras.penalty_flow import Flag, PenaltyFlow
    flow = PenaltyFlow(NflRules())
    flow.down = PEN.Down(1, 30)
    holding = Flag(F.BY_ID["P09"][0], 2)
    assert flow.extends(penalty_state(5), holding) is True
    assert flow.extends(penalty_state(5, postseason=True), holding) is False     # a play-off period goes on into the next one
    assert flow.extends(penalty_state(2), holding) is True and flow.extends(penalty_state(1), holding) is False


def test_offsetting_fouls_on_the_last_down_of_a_half_give_an_untimed_down():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import penalties as PEN
    from nfl4.extras.penalty_flow import Flag, PenaltyFlow
    flow = PenaltyFlow(NflRules())
    flow.down = PEN.Down(1, 30)
    replay = PEN.replay_down(flow.down, PEN.PlayFacts("run", 34))
    live = [Flag(F.BY_ID["P08"][0], 1), Flag(F.BY_ID["P09"][0], 2)]
    assert flow.double_extends(penalty_state(2), live, replay, None) is True
    assert flow.double_extends(penalty_state(4), live, replay, None) is True
    assert flow.double_extends(penalty_state(3), live, replay, None) is False
    after = [f for f in F.BY_ID["P18"]]
    both_after = [Flag(after[0], 2), Flag(after[1], 1)]
    assert flow.double_extends(penalty_state(2), both_after, replay, None) is False             # exception (1)
    dead_defense = [Flag(F.BY_ID["P08"][0], 1), Flag(after[0], 2)]
    assert flow.double_extends(penalty_state(2), dead_defense, replay, None) is False           # exception (3)
    major_offense = [Flag(F.BY_ID["P16"][0], 1), Flag(F.BY_ID["P03"][0], 2)]
    assert flow.double_extends(penalty_state(2), major_offense, replay, F.BY_ID["P16"][0]) is False
    assert flow.double_extends(penalty_state(2), live, PEN.Result(PEN.PLAY_STANDS), None) is False   # exception (4)


def test_a_fair_catch_as_time_runs_out_offers_the_untimed_fair_catch_kick(tmp_path):
    from test_sx10d_kicks import punting
    rig = punting(tmp_path, wisoff=2, defense=1, half=1, yard_line=30, quarter=2)
    s, x = rig.engine.s, rig.engine.s.extras
    s.wisoff, s.defense = 1, 2
    rig.rules.kicks.fair_catch(s, 1, 52)
    x.left = 0
    rig.keys.answers = [40, 13]                              # "no" first; Down makes it yes
    assert rig.rules.kicks.fair_catch_question(s) is True and x.extension is True
    assert rig.engine.clock.period_over() is False


# ----- 14-5-2, 14-3-6, 14-4-5, 14-4-8: the penalty enforcement -----

def test_double_fouls_with_a_change_of_possession_are_played_again():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import penalties as PEN
    from nfl4.game import outcome as O
    result, enforced = PEN.double_foul(F.BY_ID["P34"][0], F.BY_ID["P24"][0], PEN.Down(1, 0), PEN.PlayFacts(O.KICKOFF_RETURN, 30))
    assert enforced is None and result.kind == PEN.REPLAY_KICK
    result, enforced = PEN.double_foul(F.BY_ID["P37"][0], F.BY_ID["P22"][0], PEN.Down(1, 40, 4, 8),
                                       PEN.PlayFacts(O.PUNT, 40, receivers_spot=30))
    assert enforced is None and (result.kind, result.ball, result.los, result.down, result.to_go) == (PEN.NEW_DOWN, 1, 40, 4, 8)
    result, enforced = PEN.double_foul(F.BY_ID["P14"][0], F.BY_ID["P16"][0], PEN.Down(1, 30, 2, 6),
                                       PEN.PlayFacts(O.INTERCEPTION, 30, turnover=True))
    assert enforced is None and (result.kind, result.los, result.down, result.to_go) == (PEN.NEW_DOWN, 30, 2, 6)
    result, enforced = PEN.double_foul(F.BY_ID["P14"][0], F.BY_ID["P16"][0], PEN.Down(1, 30), PEN.PlayFacts(O.PASS_INCOMPLETE, 30))
    assert enforced is F.BY_ID["P14"][0]                     # no change of possession: 15 against 5 (14-5-1 Exception 1)


def test_the_ball_carriers_face_mask_after_the_catch_is_enforced_three_and_one():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import penalties as PEN
    from nfl4.game import outcome as O
    mask = [f for f in F.BY_ID["P17"] if f.offender == F.OFFENSE][0]
    _how, accepted, _declined = PEN.answers(mask, PEN.Down(1, 30), PEN.PlayFacts(O.PASS_COMPLETE, 50))
    assert (accepted.kind, accepted.los, accepted.down, accepted.to_go) == (PEN.NEW_DOWN, 35, 1, 5)


def test_an_offense_foul_behind_its_own_goal_line_and_a_run_that_ends_there_are_safeties():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import penalties as PEN
    from nfl4.game import outcome as O
    holding = F.BY_ID["P08"][0]
    _how, accepted, _declined = PEN.answers(holding, PEN.Down(1, 1), PEN.PlayFacts(O.RUN, 5), foul_spot=-1)
    assert accepted.kind == PEN.SAFETY and accepted.ball == 2 and accepted.points == (0, 2)       # 14-3-6 Exception 2
    how, _accepted, declined = PEN.answers(holding, PEN.Down(1, 3), PEN.PlayFacts(O.RUN, 0, score="safety"), foul_spot=2)
    assert how == PEN.AUTO_DECLINE and declined.kind == PEN.SAFETY                                 # 14-3-6 Exception 3


def test_kick_catch_interference_never_takes_a_punt_return_touchdown_away():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import penalties as PEN
    from nfl4.game import outcome as O
    how, _a, _d = PEN.answers(F.BY_ID["P37"][0], PEN.Down(1, 40, 4, 8),
                              PEN.PlayFacts(O.PUNT, 40, score="return touchdown", receivers_spot=100))
    assert how == PEN.AUTO_DECLINE


# ----- 7-2-1, 11-2, 8-7-1, 7-2-1 (c), 8-2-1 Item 3: the plays -----

def defense_call():
    return next(c for c in C.CATALOG if c.side == "D").params


@pytest.mark.parametrize("play", ["O001", "O017", "O051"])
def test_no_fumble_is_drawn_once_the_ball_carrier_reached_the_goal_line(play):
    rnd = Seeded(13)
    for to_goal in (1, 2, 3):
        situation = M.Situation(to_goal=to_goal, down=1, distance=to_goal)
        for _ in range(6000):
            r = M.play(C.BY_ID[play], defense_call(), situation, rnd)
            assert not (r.kind == "fumble" and r.yards >= to_goal), (play, to_goal, r)


def test_a_fumbled_lateral_is_the_laterals_run_never_a_sack(tmp_path, monkeypatch):
    rnd = Seeded(21)
    situation = M.Situation(to_goal=70, down=1, distance=10)
    laterals = [r for r in (M.play(C.BY_ID["O138"], defense_call(), situation, rnd) for _ in range(40000))
                if r.kind == "fumble" and r.gap == "laterals"]
    assert laterals and all(-12 <= r.yards <= -5 for r in laterals)
    rig = rig_for(tmp_path, "O138", laterals[0]._replace(fumble_lost=False), monkeypatch)
    sacked = rig.engine.s.stats[1].sacked
    run_play(rig)
    assert rig.engine.s.stats[1].sacked == sacked and rig.engine.outcomes[-1].kind != "sack"


def test_no_play_simulates_a_kneel_and_the_clock_plays_keep_their_formation(tmp_path):
    assert C.BY_ID["O155"].name == "Victory Formation Pass" and "fake kneel" in C.LEFT_OUT
    assert not any("pretend" in X.text(row).lower() and "kneel" in X.text(row).lower() for row in ("NXY-S55",))
    rules = NflRules(timeouts_on=True, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules)
    rig.engine.s.extras.play_settings = {"formation": "shotgun"}
    for play in ("O152", "O153", "O141"):
        assert rules.offense.situation(rig.engine.s, C.BY_ID[play]).formation == ""
    assert rules.offense.situation(rig.engine.s, C.BY_ID["O017"]).formation == "shotgun"


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
