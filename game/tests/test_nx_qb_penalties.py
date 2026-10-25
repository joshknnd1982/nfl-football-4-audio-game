"""The quarterback's runs and the penalties: a snap draws a pre-snap foul for plays 8 to 10, a late hit on the slider (P18), a
run that a penalty erases is taken back from the quarterback statistics, one penalty by a team (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 7.3, 9 and 15; PX SX.5). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source; every expected number is worked out from the rule next to it (B-X38).
"""
import pytest

from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import qb_runs as QB
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.penalty_flow import Flag
from nfl4.game import outcome as O
from nfl4.game.playtables import QB_DRAW, QB_KEEPER, QB_SNEAK
from nfl4.game.rules import FOUL_BEFORE_SNAP, GO_ON, NEXT_DOWN
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from randsources import ScriptedRandom
from test_pag_scrimmage import quiet_snap_count
from nxdraws import nfl_snap_draws as snap_draws, tackle_value      # NX-D2: the N. F. L. rules draw by the usage shares

ENTER, DOWN = 13, 40
NO_FOUL = 9999
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)


def texts(rig):
    return [t for t, _, _ in rig.said]


def game(tmp_path, play, call, answers=(ENTER,), **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=False, penalties_on=True, qb_on=True)
    return nfl_engine_rig(tmp_path, answers=list(answers) + [13] * 3, rules=rules, offense_play=play, defense_play=call,
                          **fields)


def dead_and_snap_rows():
    return [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]


def value_of(rig, rows, foul_id, offender=None, offense_play=1, defense_play=1):
    total = 0
    for foul, weight in rig.rules.penalty._weighted(rows, offense_play, defense_play):
        if foul.id == foul_id and (offender is None or foul.offender == offender):
            return total
        total += weight
    raise AssertionError("%s is not in the rows" % foul_id)


def keeper_draws(yards, call=6, slide=None, late_hit=None, second=2, no_foul_at_end=True, extra=None):
    """A keeper against `call` with penalties on: the pre-snap draw (no foul), the snap, the start sentence QB01, the direction,
    no fumble, the yards, the slide (`slide` = the cut) and the late-hit draw (`late_hit` = the slot of the defender, None: not
    drawn as a hit); then at the end of the play the foul draw (no foul) or, when a foul waits, the second-foul chance."""
    entry = QB.make_entry("keeper", call)
    d = Draws().below(10000, NO_FOUL)
    quiet_snap_count(d)
    snap_draws(d)
    d.rnd(5, 1).below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, yards - entry.low)
    if yards >= T.QB_SLIDE_MIN_YARDS:
        if slide is None:
            d.rnd(T.QB_SLIDE_ONE_IN, 2)
        else:
            d.rnd(T.QB_SLIDE_ONE_IN, 1).below(3, slide)
            if late_hit is None:
                d.below(T.QB_LATE_HIT_ONE_IN, 7)                     # not a hit
            else:
                d.below(T.QB_LATE_HIT_ONE_IN, 0).rnd(17, late_hit)
    if extra is not None:
        extra(d)
    return d


def after_slide_foul(d, second=2, live=0, runoff=0, cut=0):
    """The end of a play with a waiting foul: the second-foul chance 1 in 40, L, then after the choice R and the ready cut."""
    d.rnd(T.SECOND_FOUL_CHANCE, second).below(4, live)
    d.below(11, runoff).below(4, cut)
    return d


# ----- the snap of a quarterback run draws a pre-snap foul like the other plays from scrimmage -----

@pytest.mark.parametrize("play", [QB_SNEAK, QB_KEEPER, QB_DRAW])
def test_plays_8_to_10_draw_the_foul_before_the_snap_like_plays_1_to_5(tmp_path, play):
    rig = game(tmp_path, play, 2)
    draws = Draws().below(10000, NO_FOUL)
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []
    assert rig.rules.before_snap(rig.engine.s, play, 2) == GO_ON
    assert rig.rnd.trace == [10000]
    for kick in (6, 7):
        rig.rnd.source = ScriptedRandom([], strict=True)
        assert rig.rules.before_snap(rig.engine.s, kick, 2) == GO_ON            # a kick: no snap count, no draw


def test_a_false_start_on_a_keeper_stops_the_snap_after_hut_1(tmp_path):
    rig = game(tmp_path, QB_KEEPER, 2)
    s = rig.engine.s
    draws = (Draws().below(10000, value_of(rig, dead_and_snap_rows(), "P01", offense_play=9)).rnd(12, 7)
             .rnd(4, 1).rnd(10, 1))                                  # the quarterback's line and the huddle
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []
    step = rig.engine.snap()
    assert rig.rnd.trace == draws.sizes
    said = texts(rig)
    assert " false start, on the Bengals, Rec1. " in said
    assert step == rig.engine.position and (s.yard_line, s.down, s.to_go) == (25, 1, 15)
    assert s.extras.qb_runs == [0, 0] and not s.qb_run


# ----- the late hit on the slider (design 7.3) -----

def test_a_late_hit_on_the_slider_is_unnecessary_roughness_15_yards_and_a_first_down(tmp_path):
    rig = game(tmp_path, QB_KEEPER, 6, answers=[ENTER], down=2, to_go=10)         # Keeper against the Long Pass: 4 to 14
    d = after_slide_foul(keeper_draws(12, slide=0, late_hit=5))                    # 12 yards, slides, cut 0, a late hit by ODef5
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    said = texts(rig)
    assert X.text("NXP-01") in said and " unnecessary roughness, on the Jets, ODef5. " in said
    assert " Starr slides feet first " in said
    s, x = rig.engine.s, rig.engine.s.extras
    # the ball: the Bengals' 30 + 12 = 42, then 15 yards from where the ball became dead: 57 is the Jets' 43
    assert (s.half, s.yard_line, s.down, s.to_go) == (1, 43, 1, 10)
    assert x.flags == [0, 1] and x.flag_yards == [0, 15]
    assert rig.rules.penalty.events == [(1, "accepted", "P18", 2, 15, False)]
    assert (x.qb_runs, x.qb_yards) == ([1, 0], [12, 0])                            # the run stands: the penalty is added to it
    assert s.stats[1].running_yards == 12
    assert rig.rules.qb.late_hits == 1 and rig.rules.qb.slides == [0]


def test_the_player_may_decline_the_penalty_on_the_late_hit(tmp_path):
    rig = game(tmp_path, QB_KEEPER, 6, answers=[DOWN, ENTER], down=2, to_go=10)
    d = keeper_draws(12, slide=1, late_hit=5)
    d.rnd(T.SECOND_FOUL_CHANCE, 2).below(4, 0)                                      # no second foul; L
    d.rnd(4, 1).below(11, 0).below(4, 0)                                            # declined: the banter draw, R and the ready cut
    #                                                                                 (after a foul the clock restarts on the ready signal)
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    s, x = rig.engine.s, rig.engine.s.extras
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 41, 1, 10)                # 12 - 1 = 11 yards from the 30: the 41; 11 >= 10, a first down
    assert x.flags == [0, 0] and rig.rules.penalty.events[-1][1] == "declined"
    assert x.qb_runs == [1, 0] and x.qb_yards == [11, 0]


def test_no_late_hit_is_drawn_without_a_slide_and_the_ordinary_draw_follows(tmp_path):
    rig = game(tmp_path, QB_KEEPER, 6, down=2, to_go=10)
    d = keeper_draws(12, slide=None)                                                # rnd(2) = 2: no slide, so no late-hit draw
    d.below(100, 99).below(10000, NO_FOUL).below(4, 0).rnd(4, 1).below(11, 0)        # out of bounds no; no foul at the end; L; R
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert rig.rules.qb.late_hits == 0 and rig.rules.penalty.events == []


def test_a_slide_without_a_hit_draws_the_ordinary_foul_chance_at_the_end(tmp_path):
    rig = game(tmp_path, QB_KEEPER, 6, down=2, to_go=10)
    d = keeper_draws(12, slide=2)                                                   # a slide, no late hit (below(40) = 7)
    d.below(10000, NO_FOUL).below(4, 0).rnd(4, 1).below(11, 0)                      # no out-of-bounds draw for a slider
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert rig.rules.qb.late_hits == 0 and rig.engine.outcomes[0].yards == 10


def test_a_late_hit_does_not_add_a_second_flag_when_a_foul_is_already_waiting(tmp_path, monkeypatch):
    rig = game(tmp_path, QB_KEEPER, 6, answers=[ENTER], down=2, to_go=10)
    flow = rig.rules.penalty
    offside = Flag(F.BY_ID["P03"][0], 2, 4)

    def waiting_offside(state, offense_play, defense_play):          # the at-snap draw found a defensive offside
        flow.waiting = offside
        return False

    monkeypatch.setattr(flow, "at_snap", waiting_offside)
    entry = QB.make_entry("keeper", 6)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 1).below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, 12 - entry.low)
    d.rnd(2, 1).below(3, 0).below(T.QB_LATE_HIT_ONE_IN, 0).rnd(17, 5)               # slide, cut 0, a late hit: no second flag
    d.rnd(T.SECOND_FOUL_CHANCE, 2).below(4, 0)                                      # no second foul; L
    d.rnd(4, 1).below(11, 0).below(4, 0)                                            # declined: the banter draw, R, the ready cut
    run_steps(rig, rig.engine.snap, d)
    said = texts(rig)
    assert " off sides, on the Jets, ODef4. " in said and not any("unnecessary roughness" in t for t in said)
    assert flow.events[-1][1:3] == ("declined", "P03")          # 12 yards and a first down beat 5 yards: the computer's rule
    assert " Kim if you accept the penalty, it will be second and 5 on your 35 yard line. " in said
    assert rig.rules.qb.late_hits == 1                                              # drawn, but the offside is the only flag


# ----- a penalty that erases the run takes it from the quarterback statistics -----

def test_an_accepted_offside_erases_the_run_and_its_counts(tmp_path, monkeypatch):
    rig = game(tmp_path, QB_KEEPER, 5, answers=[ENTER], down=2, to_go=7)
    flow = rig.rules.penalty
    offside = Flag(F.BY_ID["P03"][0], 2, 4)

    def waiting_offside(state, offense_play, defense_play):
        flow.waiting = offside
        return False

    monkeypatch.setattr(flow, "at_snap", waiting_offside)
    entry = QB.make_entry("keeper", 5)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 1).below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, 5 - entry.low)    # 5 yards: no slide draw
    d.below(100, 99)                                                                # not out of bounds
    after_slide_foul(d)
    run_steps(rig, rig.engine.snap, d)
    s, x = rig.engine.s, rig.engine.s.extras
    assert flow.events[-1][:3] == (1, "accepted", "P03")
    assert (s.yard_line, s.down, s.to_go) == (35, 2, 2)                              # five yards, the down replayed (7 - 5 to go)
    assert (x.qb_runs, x.qb_yards) == ([0, 0], [0, 0])                              # the run did not happen
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (0, 0)
    assert [o.qb_run for o in rig.engine.outcomes] == ["keeper"]                    # the record of the play was made
    assert [e[2] for e in rig.rules.qb.events] == ["keeper"]                        # and the calibration saw it


# ----- the review's findings (SX.5): where a late hit may be drawn, and the double foul -----

def test_no_late_hit_is_drawn_on_a_two_point_try(tmp_path):
    rig = game(tmp_path, QB_KEEPER, 6, half=1, yard_line=12, two_point=True)
    rig.rules.penalty.take_snap(rig.engine.s)
    rig.rnd.source = ScriptedRandom([], strict=True)                                # no below(40) and no slot
    assert rig.rules.penalty.slider_hit(rig.engine.s, T.QB_LATE_HIT_ONE_IN) is False and rig.rules.penalty.late is None


@pytest.mark.parametrize("down, to_go, yards, drawn", [(4, 26, 8, False), (4, 8, 8, True), (4, 7, 8, True), (3, 26, 8, True),
                                                      (1, 10, 8, True)])
def test_a_late_hit_on_fourth_down_is_drawn_only_when_the_offense_keeps_the_ball(tmp_path, down, to_go, yards, drawn):
    rig = game(tmp_path, QB_KEEPER, 6, down=down, to_go=to_go)
    rig.engine.s.yards = yards
    rig.rules.penalty.take_snap(rig.engine.s)
    rig.rnd.source = ScriptedRandom(Draws().below(T.QB_LATE_HIT_ONE_IN, 0).rnd(17, 3).values if drawn else [], strict=True)
    assert rig.rules.penalty.slider_hit(rig.engine.s, T.QB_LATE_HIT_ONE_IN) is drawn


def test_a_late_hit_and_a_foul_by_the_offense_are_a_double_foul_and_the_fifteen_yards_count(tmp_path, monkeypatch):
    rig = game(tmp_path, QB_KEEPER, 6, answers=[ENTER], down=2, to_go=10)
    flow = rig.rules.penalty
    formation = Flag(F.BY_ID["P06"][0], 1, 3)                                        # illegal formation by the Bengals

    def waiting_formation(state, offense_play, defense_play):
        flow.waiting = formation
        return False

    monkeypatch.setattr(flow, "at_snap", waiting_formation)
    entry = QB.make_entry("keeper", 6)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    d.rnd(5, 1).below(4, 0).rnd(entry.fumble, 1).below(entry.high - entry.low, 12 - entry.low)
    d.rnd(2, 1).below(3, 0).below(T.QB_LATE_HIT_ONE_IN, 0).rnd(17, 5)               # slide, cut 0, a late hit
    d.below(4, 0)                                                                   # L (both teams flagged: no second-foul draw)
    d.below(11, 0).below(4, 0)                                                      # R and the ready cut after the foul
    run_steps(rig, rig.engine.snap, d)
    said = texts(rig)
    assert " illegal formation, on the Bengals, Back3. " in said and " unnecessary roughness, on the Jets, ODef5. " in said
    assert X.text("NXP-20") in said                                                 # only the fifteen yard penalty counts
    assert [e[1:3] for e in flow.events] == [("major", "P18")]
    assert rig.engine.s.extras.flag_yards == [0, 15]


def test_the_help_line_on_the_late_hit_needs_penalties_and_the_menu_line_says_offense(tmp_path):
    on = game(tmp_path / "on", QB_KEEPER, 6)
    assert X.text("NXH-22") in on.rules.extra_help("117")
    assert X.text("NXH-20") in on.rules.extra_help("117") and "late hit" not in X.text("NXH-20")
    off = nfl_engine_rig(tmp_path / "off", rules=NflRules(timeouts_on=False, penalties_on=False, qb_on=True))
    assert X.text("NXH-22") not in off.rules.extra_help("117")
    assert X.text("NXH-18").startswith(" In the offense menu, 8 is")


def test_the_classic_stub_takes_the_engines_arguments(tmp_path):
    from nfl4.game.rules import CLASSIC
    with pytest.raises(RuntimeError, match="Classic"):
        CLASSIC.qb_entry(object(), scramble=True)
