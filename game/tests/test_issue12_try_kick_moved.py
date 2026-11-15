"""GitHub issue 12, the tester's answer (D-232): a penalty on the try moves the extra point by its yards (nfl4 only, rule 0.13; NFL 2026
rules 11-3-3 and 14-2-3, SRC-OFFICIAL). This is inspired by Jim Kitchen.

The question (https://github.com/joshknnd1982/nfl-football-4-audio-game/issues/12#issuecomment-6901661794): "(a) keep the one usual extra
point; (b) move the kick by the penalty's yards, so it is easier or harder to make." The tester answered "Choice b."
(https://github.com/joshknnd1982/nfl-football-4-audio-game/issues/12#issuecomment-6901694717). Rule 11-3-3: after a foul that makes a
re-Try, the offense may have the penalty enforced from the other Try spot, the kick's (the 15, moved by any earlier penalty on the try).
So the kick's spot moves by the same foul from its own spot (half the distance at most; defensive pass interference half the distance),
the kick is that much longer or shorter, its made rate follows the field goal model's difference, and one sentence before the choice
says where and how long it would be.
"""
from pathlib import Path

from nfl4.data import debuglog
from nfl4.extras import fouls_2026 as F
from nfl4.extras import kick_flow as KF
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras import rules_2026 as R
from nfl4.extras.penalty_flow import Flag
from nfl4.extras.plays import model as M
from nfl4.game import phrases as P
from pagrig import Draws
from test_nx_penalties import game, script as pen_script, check as pen_check, value_of
from test_nx_penalty_review import DEAD
from test_nx_tkey import ENTER, UP, scene, script, texts
from test_sx10d_kicks import given, rig_for, run, texts as kick_texts


def foul(by_offense: bool, yards: int, spot: str | None = None, personal: bool | None = None) -> F.Foul:
    for f in F.FOULS:
        if f.offense_side == by_offense and f.yards == yards and (spot is None or f.spot == spot) \
                and (personal is None or f.personal == personal) and not f.loss_of_down:
            return f
    raise AssertionError("no such foul in the table")


def flow_at_try(rig, offense=1):
    flow = rig.rules.penalty
    flow.down = PEN.Down(offense, 98, 1, 2, True)                  # the two-point try at the 2
    return flow


def books_on(rig):
    rig.engine.s.extras.offense_book[0] = "west"                   # the kicks of 2026 are played (a playbook, D-094)


# ----- where the kick goes -----

def test_a_foul_by_the_kicking_team_makes_the_kick_five_yards_longer(tmp_path):
    rig = game(tmp_path)
    flow = flow_at_try(rig)
    flow.move_try_kick(Flag(foul(True, 5), 1))
    assert flow.try_kick_to_goal == 20 and KF.try_kick_distance(20) == 38


def test_a_foul_by_the_defense_makes_it_shorter_and_never_more_than_half_the_distance(tmp_path):
    rig = game(tmp_path)
    flow = flow_at_try(rig)
    flow.move_try_kick(Flag(foul(False, 5), 2))
    assert flow.try_kick_to_goal == 10 and KF.try_kick_distance(10) == 28
    flow.try_kick_to_goal = R.EXTRA_POINT_SPOT
    flow.move_try_kick(Flag(foul(False, 15, personal=True), 2))        # 15 yards from the 15: half the distance, 7
    assert flow.try_kick_to_goal == 8


def test_defensive_pass_interference_moves_the_kick_half_the_distance(tmp_path):
    rig = game(tmp_path)
    flow = flow_at_try(rig)
    flow.move_try_kick(Flag(foul(False, 0, spot=F.SPOT_OF_FOUL), 2))
    assert flow.try_kick_to_goal == 8                                 # 11-3-3 Exception: half the distance from the other Try spot


def test_two_penalties_on_one_try_add_up_and_the_next_kick_off_starts_again_at_the_15(tmp_path):
    rig = game(tmp_path)
    flow = flow_at_try(rig)
    flow.move_try_kick(Flag(foul(True, 5), 1))
    flow.move_try_kick(Flag(foul(True, 5), 1))
    assert flow.try_kick_to_goal == 25                                # "as determined by any previously enforced penalty"
    flow.try_replayed = True
    flow.take_kickoff(rig.engine.s)
    assert flow.try_kick_to_goal == R.EXTRA_POINT_SPOT and not flow.try_replayed


# ----- how often it is good -----

def good_threshold(distance):
    """The highest value of the second draw (the first one never blocks: 9999) that makes the kick good."""
    low, high = 0, 10000
    while low < high:
        mid = (low + high) // 2
        draws = iter([9999, mid])
        kick = M.extra_point("return", type("R", (), {"below": lambda self, n: next(draws)})(), distance, R.EXTRA_POINT_DISTANCE)
        if kick.kind == "good":
            low = mid + 1
        else:
            high = mid
    return low


def test_the_usual_kick_is_the_measured_extra_point_and_a_longer_one_is_harder(tmp_path):
    usual = good_threshold(R.EXTRA_POINT_DISTANCE)
    assert usual == good_threshold(0) == M.M.EXTRA_POINT["good"] * 10000 // (10000 - M.M.EXTRA_POINT["blocked"])
    assert good_threshold(48) < good_threshold(38) < usual < good_threshold(26)
    assert good_threshold(38) < 9300 and good_threshold(26) > 9600


# ----- what the player hears and chooses -----

def test_the_testers_moment_the_choice_says_the_moved_kick_and_the_kick_is_that_long(tmp_path):
    """His illegal shift on the try for two: the referee's "from the 7 yard line"; the choice now says the kick would be from the 20, a
    38 yard kick, before "select"; Up and Enter take it, and the kick planned is 38 yards."""
    rig = game(tmp_path, answers=[UP, ENTER], half=1, yard_line=2, two_point=True, offense_play=1, defense_play=2)
    books_on(rig)
    draws = Draws().below(10000, value_of(rig, DEAD, "P01")).rnd(12, 1).rnd(4, 1).rnd(10, 1)
    pen_script(rig, draws)
    engine = rig.engine
    step = engine.snap()
    pen_check(rig, draws)
    assert step == engine.try_again and engine.s.yard_line == 7
    assert step() == engine.extra_point_choice
    start = len(rig.said)
    assert engine.extra_point_choice() == engine.extra_point
    said = [t for t, _, _ in rig.said[start:]]
    assert said[:4] == [X.text("NXB-J29", n=20, d=38), " " + engine.coach + P.SELECT, P.TRY_FOR_TWO, P.KICK_FOR_EXTRA_POINT]
    plan = rig.rules.special_kick(engine.s, "extra point")
    assert plan.distance == 38


def test_no_sentence_and_the_usual_kick_without_a_penalty_or_without_the_2026_kicks(tmp_path):
    rig = scene(tmp_path, answers=[ENTER], yard_line=30, extras=dict(pending=0, running=False))
    script(rig, Draws())
    books_on(rig)
    assert rig.engine.extra_point_choice() == rig.engine.extra_point
    assert texts(rig)[:2] == [" Kim" + P.SELECT, P.KICK_FOR_EXTRA_POINT]
    assert rig.rules.special_kick(rig.engine.s, "extra point").distance == R.EXTRA_POINT_DISTANCE
    plain = scene(tmp_path / "plain", answers=[ENTER], yard_line=30, extras=dict(pending=0, running=False))
    script(plain, Draws())
    plain.rules.penalty.try_kick_to_goal = 20                         # the original's extra point has no length and never fails
    assert plain.rules.try_kick_moved(plain.engine.s) is None
    plain.engine.extra_point_choice()
    assert X.text("NXB-J29", n=20, d=38) not in texts(plain)


def test_a_timeout_after_the_kick_was_chosen_keeps_the_penaltys_two_point_spot(tmp_path):
    """After the penalty he chose the kick, then T: the choice comes again; the try for two is still from the 7, not the 2."""
    rig = scene(tmp_path, answers=[UP, ENTER], two_point=False, yard_line=7, extras=dict(pending=0, running=False))
    script(rig, Draws())
    books_on(rig)
    rig.rules.penalty.try_replayed = True
    rig.rules.penalty.try_kick_to_goal = 20
    engine = rig.engine
    step = engine.extra_point_choice()                                # the kick was his last choice: it starts there, Up gives the two
    assert step == engine.offense_menu and engine.s.two_point and engine.s.yard_line == 7
    assert texts(rig)[0] == X.text("NXB-J29", n=20, d=38)


def test_the_computers_moved_kick_is_said_before_it(tmp_path):
    rig = rig_for(tmp_path, wisoff=2, defense=1, half=2, yard_line=0)
    rig.rules.penalty.try_kick_to_goal = 8                            # the player's personal foul on its touchdown (14-2-3)
    given(rig, kick_result=M.KickResult("good"))
    mark = len(rig.said)
    assert run(rig, rig.engine.extra_point) == "after_score"
    assert X.text("NXB-J30", n=8, d=26) in kick_texts(rig, mark)
    usual = rig_for(tmp_path / "usual", wisoff=2, defense=1, half=2, yard_line=0)
    given(usual, kick_result=M.KickResult("good"))
    mark = len(usual.said)
    run(usual, usual.engine.extra_point)
    assert not any("yard kick" in t for t in kick_texts(usual, mark))


def test_the_log_says_where_the_kick_moved(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = game(tmp_path / "rig")
    flow = flow_at_try(rig)
    flow.move_try_kick(Flag(foul(True, 5), 1))
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if "try_kick_spot" in line]
    assert len(lines) == 1 and "before=15" in lines[0] and "after=20" in lines[0] and "distance=38" in lines[0]
