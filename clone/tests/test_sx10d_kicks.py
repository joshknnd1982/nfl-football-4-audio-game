"""The kicks of 2026 in the game: the kick-off menu, the kick-offs, punts, field goals, the extra point, the fakes, the fair catch kick
and the kick fouls (nfl4 only, rule 0.13; NX-R7: G26-1, G26-4 to G26-7, G26-11, G26-13, G26-14; NFL_PLAYS_DESIGN 2.6 and 4.9; PX SX.10d,
D-094). This is inspired by Jim Kitchen.

The engine's steps of game/pag_kicks26.py are run with the model's result handed in (the hooks kickoff_result, kick_result and fake_yards
replaced on the rules object), so each ending is checked where the ball is left and what is said; the draws the engine makes itself (the
returner, the tacklers, the pauses) come from a seeded source. The kick flow's own choices (the menu, the computer's kick) are checked on a
strict scripted source.
"""
import random

import pytest

from nfl4.extras import fouls_2026 as F
from nfl4.extras import kick_flow as KF
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras import penalty_list as PL
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import descriptions as DS
from nfl4.extras.plays import model as M
from nfl4.extras.plays import play_menus as PM
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.rules import CLASSIC, FAIR_CATCH_KICK, KICKOFF_2026, NORMAL_KICKOFF, ONSIDE_KICKOFF
from nflrig import nfl_engine_rig
from randsources import ScriptedRandom, below_value

ENTER, ESCAPE, UP, DOWN, RIGHT = 13, 27, 38, 40, 39
STOPS = ("down_sentence", "after_score", "extra_point", "extra_point_choice", "kick_off", "next_play", "play_menu")


def rig_for(tmp_path, answers=(), offense_book="west", defense_book="pressure", onside_on=True, **state):
    fields = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
    fields.update(state)
    rules = NflRules(timeouts_on=False, onside_on=onside_on, offense_book=offense_book, defense_book=defense_book)
    rig = nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)
    return rig


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def run(rig, step, seed=3):
    """The engine from `step` (always run) on a seeded source until a step of STOPS; its name."""
    rig.rnd.source = random.Random(seed)
    step = step()
    while step is not None and step.__name__ not in STOPS:
        step = step()
    return step.__name__ if step is not None else None


def given(rig, **hooks):
    """The model's results handed in: kickoff_result=..., kick_result=..., fake_yards=..."""
    for name, value in hooks.items():
        setattr(rig.rules, name, (lambda *a, v=value: v))


# ----- when -----

def test_the_kicks_of_2026_need_a_playbook_and_classic_never_draws_or_speaks(tmp_path):
    rig = rig_for(tmp_path)
    assert rig.rules.kicks.on(rig.engine.s)
    plain = rig_for(tmp_path / "plain", offense_book="classic", defense_book="classic")
    s = plain.engine.s
    assert plain.rules.kicks.on(s) is False
    for what in ("punt", "field goal", "extra point"):
        assert plain.rules.special_kick(s, what) is None and CLASSIC.special_kick(s, what) is None
    assert plain.rnd.source.drawn == 0 and plain.said == []
    defense_only = rig_for(tmp_path / "d", offense_book="classic", defense_book="pressure")
    assert defense_only.rules.kicks.on(defense_only.engine.s)


# ----- the kick-off menu (design 2.6, G26-1) -----

def kicking(tmp_path, answers, **kw):
    return rig_for(tmp_path, answers=answers, wisoff=2, defense=1, **kw)


def test_enter_takes_the_deep_kick_and_the_menu_names_the_four_kicks(tmp_path):
    rig = kicking(tmp_path, [DOWN, DOWN, DOWN, DOWN, ENTER])
    mark = len(rig.said)
    assert rig.rules.before_kickoff(rig.engine.s, 1) == KICKOFF_2026
    said = texts(rig, mark)
    assert said[0] == X.text("NXB-J01", coach="Kim")
    assert said[1:] == [" 1. Deep Kick ", " 2. Short Kick ", " 3. Squib Kick ", " 4. Onside Kick ", " 1. Deep Kick "]
    assert rig.engine.s.extras.kick_call == "K001" and rig.engine.s.extras.kick_kind == NORMAL_KICKOFF


def test_the_digit_four_declares_the_onside_kick_and_d_describes_the_short_kick(tmp_path):
    rig = kicking(tmp_path, ["4", ENTER])
    assert rig.rules.before_kickoff(rig.engine.s, 1) == ONSIDE_KICKOFF and rig.engine.s.extras.kick_kind == "onside"
    rig = kicking(tmp_path / "d", ["2", "d", ENTER])
    mark = len(rig.said)
    assert rig.rules.before_kickoff(rig.engine.s, 1) == KICKOFF_2026 and rig.engine.s.extras.kick_call == "K002"
    assert DS.text("NXB-D02") in texts(rig, mark)


def test_after_a_safety_the_menu_adds_the_safety_punt_and_without_onside_kicks_it_has_no_onside(tmp_path):
    rig = kicking(tmp_path, ["5", ENTER])
    rig.engine.s.extras.safety_kick = True
    assert rig.rules.before_kickoff(rig.engine.s, 1) == KICKOFF_2026
    assert rig.engine.s.extras.kick_call == "K027" and rig.engine.s.extras.kick_from == 20
    rig = kicking(tmp_path / "off", ["4", ENTER], onside_on=False)
    mark = len(rig.said)
    rig.rules.before_kickoff(rig.engine.s, 1)
    assert " 4. Onside Kick " not in texts(rig, mark) and rig.engine.s.extras.kick_call == "K001"     # 4 is no item: an echo


def test_the_computer_draws_its_kick_from_its_mix_and_a_kick_made_again_keeps_its_call(tmp_path):
    rig = rig_for(tmp_path, wisoff=1, defense=2)
    rig.rnd.source = ScriptedRandom([below_value(100, 60)], strict=True)     # deep 0-54, short 55-96, squib 97-99
    assert rig.rules.before_kickoff(rig.engine.s, 2) == KICKOFF_2026 and rig.engine.s.extras.kick_call == "K002"
    rig.engine.s.extras.kick_again = True
    rig.engine.s.extras.kick_back = 5
    assert rig.rules.before_kickoff(rig.engine.s, 2) == KICKOFF_2026 and rig.engine.s.extras.kick_call == "K002"
    assert rig.engine.s.extras.kick_from == 30


def test_the_computer_kicks_onside_by_its_rule_late_and_behind(tmp_path):
    from nfl4.extras.onside import computer_rule
    low, high, over, up_to, _a, _b = T.ONSIDE_COMPUTER_RULES[0]              # the first rule of SX.4: a deficit and a time left
    rig = rig_for(tmp_path, wisoff=1, defense=2, quarter=4)
    rig.engine.s.extras.left = up_to
    rig.engine.s.stats[1].score = low                                         # the computer trails by `low`
    assert computer_rule(4, up_to, low) is not None
    rig.rnd.source = ScriptedRandom([0.0], strict=True)                       # its one draw: rnd(b) = 1, at most a
    assert rig.rules.before_kickoff(rig.engine.s, 2) == ONSIDE_KICKOFF


# ----- the kick-off's endings -----

def receiving(tmp_path, answers=()):
    return rig_for(tmp_path, answers=answers, wisoff=1, defense=2, half=2, yard_line=0)


@pytest.mark.parametrize("kind, line, row", [("touchback", 35, "NXB-J04"), ("out_of_bounds", 40, "NXB-J02"),
                                             ("landed_short", 40, "NXB-J03")])
def test_a_kick_off_nobody_runs_back_leaves_the_ball_where_2026_puts_it(tmp_path, kind, line, row):
    rig = receiving(tmp_path)
    rig.engine.s.extras.kick_call = "K001"
    given(rig, kickoff_result=M.KickResult(kind, line))
    mark = len(rig.said)
    assert run(rig, rig.engine.kickoff_2026) == "down_sentence"
    s = rig.engine.s
    assert X.text(row) in texts(rig, mark) and (s.half, s.yard_line, s.down, s.to_go, s.wisoff) == (2, line, 1, 10, 1)
    assert rig.engine.outcomes[-1].kind == O.KICKOFF_TOUCH_BACK


def test_a_kick_off_caught_in_the_field_is_returned_to_the_models_line(tmp_path):
    rig = receiving(tmp_path)
    rig.engine.s.extras.kick_call = "K002"
    given(rig, kickoff_result=M.KickResult("returned", 31, 23))
    mark = len(rig.said)
    assert run(rig, rig.engine.kickoff_2026) == "down_sentence"
    s = rig.engine.s
    said = texts(rig, mark)
    assert any("kicks it short into the landing zone" in t for t in said)
    assert any(t.endswith("catches the ball at the 8 ") for t in said)
    assert (s.half, s.yard_line, s.down) == (2, 31, 1) and rig.engine.outcomes[-1].kind == O.KICKOFF_RETURN


def test_a_kick_off_returned_all_the_way_is_a_touchdown(tmp_path):
    rig = receiving(tmp_path)
    given(rig, kickoff_result=M.KickResult("returned", 100, 100, True))
    assert run(rig, rig.engine.kickoff_2026) == "extra_point_choice"
    assert rig.engine.s.score(1) == 6 and P.TOUCH_DOWN in texts(rig)


@pytest.mark.parametrize("answers, line", [([DOWN, ENTER], 35), ([ENTER], 25)])
def test_a_kick_caught_in_the_end_zone_asks_the_player_to_run_it_out(tmp_path, answers, line):
    rig = receiving(tmp_path, answers)
    given(rig, kickoff_result=M.KickResult("returned", 25, 28))
    mark = len(rig.said)
    assert run(rig, rig.engine.kickoff_2026) == "down_sentence"
    said = texts(rig, mark)
    assert any("3 yards deep in the end zone" in t for t in said) and any(P.RUN_IT_OUT_1 in t for t in said)
    assert (rig.engine.s.half, rig.engine.s.yard_line) == (2, line)


def test_the_safety_punt_ends_as_a_punt_and_its_touch_back_is_at_the_20(tmp_path):
    rig = receiving(tmp_path)
    rig.engine.s.extras.kick_call = "K027"
    given(rig, kickoff_result=M.KickResult("punt_touchback", 20))
    mark = len(rig.said)
    assert run(rig, rig.engine.kickoff_2026) == "down_sentence"
    assert any("punts it from the 20" in t for t in texts(rig, mark)) and P.IT_IS_A_TOUCH_BACK in texts(rig, mark)
    assert rig.engine.s.yard_line == 20


def test_the_safety_punts_model_has_no_block_and_its_kick_offs_from_the_20_start_the_receivers_farther_up():
    src = random.Random(7)

    class R:
        @staticmethod
        def below(n):
            return int(src.random() * n)
    assert all(M.punt("spread", 80, "block", R, free_kick=True).kind != "blocked" for _ in range(3000))
    near = [M.kickoff("deep", R).start for _ in range(4000)]
    far = [M.kickoff("deep", R, spot=20, touchback_pct=T.SAFETY_KICK_TOUCHBACK).start for _ in range(4000)]
    assert sum(far) / len(far) > sum(near) / len(near) + 6


# ----- punts (G26-5) -----

def punting(tmp_path, **state):
    fields = dict(wisoff=1, defense=2, half=2, yard_line=30, down=4, to_go=8)
    fields.update(state)
    rig = rig_for(tmp_path, **fields)
    rig.engine.s.offense_play = 7
    return rig


@pytest.mark.parametrize("result, wisoff, half, line, row", [
    (M.KickResult("fair_catch", 25, gross=45), 2, 1, 25, None),
    (M.KickResult("returned", 35, 10, gross=45), 2, 1, 35, "NXB-J09"),
    (M.KickResult("touchback", 20, gross=60), 2, 1, 20, None),
    (M.KickResult("dead", 15, gross=55), 2, 1, 15, "NXB-J11"),
    (M.KickResult("blocked", 75, defense_recovers=True), 2, 2, 25, "NXB-J08"),
])
def test_a_punts_ending_gives_the_receivers_the_ball_where_the_model_left_it(tmp_path, result, wisoff, half, line, row):
    rig = punting(tmp_path)
    given(rig, kick_result=result)
    mark = len(rig.said)
    assert run(rig, rig.engine.punt) == "down_sentence"
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line, s.down, s.to_go) == (wisoff, half, line, 1, 10)
    said = " ".join(texts(rig, mark))
    if row == "NXB-J09":
        assert "runs it back 10 yards" in said
    elif row:
        assert X.text(row).strip() in said
    assert rig.engine.outcomes[-1].kind == O.PUNT


def test_a_muffed_punt_the_kicking_team_falls_on_is_its_first_down(tmp_path):
    rig = punting(tmp_path)
    given(rig, kick_result=M.KickResult("muffed", 30, gross=40, defense_recovers=True))
    assert run(rig, rig.engine.punt) == "down_sentence"
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line, s.down, s.to_go) == (1, 1, 30, 1, 10)
    assert any("muffs the punt and the Bengals fall on it" in t for t in texts(rig))


def test_a_punt_returned_all_the_way_is_the_receivers_touchdown(tmp_path):
    rig = punting(tmp_path)
    given(rig, kick_result=M.KickResult("returned", 100, 70, True, 40))
    assert run(rig, rig.engine.punt) == "extra_point"
    assert rig.engine.s.score(2) == 6 and rig.engine.s.wisoff == 2


def test_the_players_list_of_punts_calls_a_pin_punt_and_the_computer_pins_near_the_goal(tmp_path):
    rig = punting(tmp_path, answers=["7", RIGHT, "2", ENTER])
    from pagrig import Draws, run_steps
    assert run_steps(rig, rig.engine.offense_menu, Draws(), until=("offense_chosen", "concede")) == "offense_chosen"
    assert rig.rules.offense.called == "K012" and rig.engine.s.offense_play == 7
    plan = rig.rules.special_kick(rig.engine.s, "punt")
    assert plan.concept == "K012" and plan.kind == "pin" and plan.defense == "return"
    computer = punting(tmp_path / "c", wisoff=2, defense=1, half=2, yard_line=45)       # 45 yards from the player's goal
    computer.engine.s.extras.kick_defense = "K033"
    plan = computer.rules.special_kick(computer.engine.s, "punt")
    assert plan.concept == "K012" and plan.defense == "block"


def test_the_players_fair_catch_late_in_a_half_offers_the_fair_catch_kick(tmp_path):
    rig = punting(tmp_path, wisoff=2, defense=1, half=1, yard_line=30, quarter=2)
    given(rig, kick_result=M.KickResult("fair_catch", 52, gross=45))
    assert run(rig, rig.engine.punt) == "down_sentence"
    s, x = rig.engine.s, rig.engine.s.extras
    assert x.fair_catch_kick is True and s.wisoff == 1
    x.left = 20
    rig.keys.answers = [DOWN, ENTER]                          # "no" first; Down makes it yes
    mark = len(rig.said)
    assert rig.rules.kicks.fair_catch_question(s) is True and rig.rules.kicks.fair_catch_armed
    assert X.text("NXB-J20", coach="Kim") in texts(rig, mark) and x.fair_catch_kick is False
    s.offense_play = 6
    given(rig, kick_result=M.KickResult("made"))
    mark = len(rig.said)
    assert run(rig, rig.engine.field_goal) == "after_score"
    assert any("lines up for a fair catch kick" in t for t in texts(rig, mark)) and s.score(1) == 3
    assert rig.rules.kicks.fair_catch_armed is False


def test_the_fair_catch_kick_is_not_offered_early_far_or_to_the_computer(tmp_path):
    rig = punting(tmp_path, wisoff=2, defense=1, quarter=1)
    rig.rules.kicks.fair_catch(rig.engine.s, 1, 52)
    assert rig.engine.s.extras.fair_catch_kick is False                       # the first quarter
    rig = punting(tmp_path / "far", wisoff=2, defense=1, quarter=4)
    rig.rules.kicks.fair_catch(rig.engine.s, 1, 40)                           # a kick of 70 yards
    assert rig.engine.s.extras.fair_catch_kick is False
    rig.rules.kicks.fair_catch(rig.engine.s, 2, 52)                           # the computer's fair catch
    assert rig.engine.s.extras.fair_catch_kick is False
    rig.engine.s.extras.fair_catch_kick, rig.engine.s.extras.left = True, 90  # too much time left: no question
    rig.engine.s.wisoff = 1
    mark = len(rig.said)
    assert rig.rules.kicks.fair_catch_question(rig.engine.s) is False and texts(rig, mark) == []
    assert rig.engine.s.extras.fair_catch_kick is False


def test_a_fair_catch_kick_chosen_and_not_kicked_is_forgotten_at_the_next_menu_or_kick_off(tmp_path):
    rig = rig_for(tmp_path, answers=[ENTER])
    kicks, s = rig.rules.kicks, rig.engine.s
    kicks.fair_catch_armed = True
    rig.rules.offense_menu(s, False)                          # the period ended at the snap: the menu comes again
    assert kicks.fair_catch_armed is False
    kicks.fair_catch_armed = True
    s.wisoff, s.defense = 2, 1
    rig.rules.before_kickoff(s, 1)
    assert kicks.fair_catch_armed is False
    s.wisoff, s.defense, s.offense_play = 1, 2, 6
    assert rig.rules.special_kick(s, "field goal").what == "field goal"


def test_between_plays_answers_the_fair_catch_kick_continuation(tmp_path):
    rig = rig_for(tmp_path, answers=[DOWN, ENTER], quarter=4)
    s, x = rig.engine.s, rig.engine.s.extras
    x.fair_catch_kick, x.left, x.plays = True, 15, 1
    rig.rnd.source = random.Random(2)
    assert rig.rules.between_plays(s) == FAIR_CATCH_KICK
    assert rig.engine.continuation(FAIR_CATCH_KICK) == rig.engine.fair_catch_kick


# ----- field goals (G26-6, G26-7) and the extra point (G26-4) -----

def kicking_a_field_goal(tmp_path, **state):
    fields = dict(wisoff=1, defense=2, half=1, yard_line=30, down=4, to_go=6)
    fields.update(state)
    rig = rig_for(tmp_path, **fields)
    rig.engine.s.offense_play = 6
    return rig


def test_a_made_field_goal_scores_three(tmp_path):
    rig = kicking_a_field_goal(tmp_path)
    given(rig, kick_result=M.KickResult("made"))
    assert rig.rules.special_kick(rig.engine.s, "field goal").distance == 47
    assert run(rig, rig.engine.field_goal) == "after_score" and rig.engine.s.score(1) == 3
    assert P.IS_GOOD in texts(rig)


@pytest.mark.parametrize("yard_line, half, line", [(30, 1, 37), (8, 1, 20)])
def test_a_missed_field_goal_is_the_defenses_ball_at_the_spot_of_the_kick_or_its_20(tmp_path, yard_line, half, line):
    rig = kicking_a_field_goal(tmp_path, yard_line=yard_line)
    given(rig, kick_result=M.KickResult("missed"))
    assert run(rig, rig.engine.field_goal) == "down_sentence"
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line) == (2, half, line)


def test_a_blocked_field_goal_is_the_defenses_ball_at_the_kick_and_one_run_back_is_its_touchdown(tmp_path):
    rig = kicking_a_field_goal(tmp_path)
    given(rig, kick_result=M.KickResult("blocked", defense_recovers=True))
    assert run(rig, rig.engine.field_goal) == "down_sentence"
    assert (rig.engine.s.wisoff, rig.engine.s.yard_line) == (2, 37) and X.text("NXB-J13") in texts(rig)
    rig = kicking_a_field_goal(tmp_path / "td")
    given(rig, kick_result=M.KickResult("blocked", touchdown=True, defense_recovers=True))
    assert run(rig, rig.engine.field_goal) == "extra_point" and rig.engine.s.score(2) == 6


def test_a_field_goal_may_be_tried_from_the_players_own_half(tmp_path):
    rig = kicking_a_field_goal(tmp_path, half=2, yard_line=45)
    plan = rig.rules.special_kick(rig.engine.s, "field goal")
    assert plan.distance == 55 + 17
    given(rig, kick_result=M.KickResult("missed"))
    assert run(rig, rig.engine.field_goal) == "down_sentence"
    assert P.WAY_TO_SHORT not in texts(rig)


def test_the_extra_point_can_be_good_miss_or_be_blocked_for_two_points(tmp_path):
    for result, own, other_ in ((M.KickResult("good"), 1, 0), (M.KickResult("no_good"), 0, 0),
                                (M.KickResult("blocked", touchdown=True, defense_recovers=True), 0, 2)):
        rig = rig_for(tmp_path / result.kind, half=1, yard_line=0)
        given(rig, kick_result=result)
        mark = len(rig.said)
        assert run(rig, rig.engine.extra_point) == "after_score"
        assert (rig.engine.s.score(1), rig.engine.s.score(2)) == (own, other_)
        if result.kind == "no_good":
            assert X.text("NXB-J15") in texts(rig, mark)
    plan = rig.rules.special_kick(rig.engine.s, "extra point")
    assert plan.distance == 33 and plan.concept == "K024"


def test_the_kick_defense_reaches_the_computers_field_goal(tmp_path):
    rig = kicking_a_field_goal(tmp_path, wisoff=2, defense=1)
    rig.engine.s.extras.kick_defense = "K035"
    assert rig.rules.special_kick(rig.engine.s, "field goal").defense == "fg_block"
    rig.engine.s.extras.kick_defense = "K033"                 # a punt's call: the field goal is defended as usual
    assert rig.rules.special_kick(rig.engine.s, "field goal").defense == "return"


# ----- the fakes and the swinging gate -----

def test_a_fake_punt_run_that_works_is_a_first_down(tmp_path):
    rig = punting(tmp_path, to_go=3)
    rig.rules.offense.called = "K015"
    given(rig, fake_yards=5)
    mark = len(rig.said)
    assert run(rig, rig.engine.punt) == "down_sentence"
    s = rig.engine.s
    assert X.text("NXB-J17") in texts(rig, mark) and (s.wisoff, s.down, s.to_go, s.yard_line) == (1, 1, 10, 35)


def test_a_fake_field_goal_pass_that_fails_on_fourth_down_turns_the_ball_over(tmp_path):
    rig = kicking_a_field_goal(tmp_path)
    rig.rules.offense.called = "K023"
    given(rig, fake_yards=0)
    assert run(rig, rig.engine.field_goal) == "down_sentence"
    assert rig.engine.s.wisoff == 2 and any("throws the ball" in t for t in texts(rig))


def test_right_on_field_goal_and_punt_opens_their_kinds_and_the_try_offers_the_swinging_gate(tmp_path):
    rig = punting(tmp_path)
    flow, s = rig.rules.offense, rig.engine.s
    items = rig.rules.offense_menu(s, False)
    assert rig.rules.menu_right(s, items[5]) is True
    assert [i.text for i in rig.rules.offense_menu(s, False)][:3] == [" 1. Field Goal ", " 2. Fake Field Goal Run ",
                                                                      " 3. Fake Field Goal Pass "]
    flow.reset()
    assert rig.rules.menu_right(s, items[6]) is True and len(rig.rules.offense_menu(s, False)) >= 7
    flow.reset()
    s.two_point = True
    flow.menus.set_context(flow.context(s))
    assert "K026" in [c.id for c in PM.concepts_of("og17", flow.context(s))]
    flow.called = "K026"
    rig.rnd.source = random.Random(1)
    result = rig.rules.model_play(s)
    assert result.kind == "run" and result.gap == "end" and s.offense_play == 2
    plain = rig_for(tmp_path / "plain", offense_book="west", defense_book="classic")
    assert "K011" in plain.rules.offense.usable(plain.engine.s)


# ----- the kick fouls (G26-14) -----

def test_the_2026_kick_fouls_are_drawn_only_with_the_kicks_of_2026_and_catch_interference_only_on_a_caught_punt(tmp_path):
    rig = rig_for(tmp_path)
    flow = rig.rules.penalty
    facts = PEN.PlayFacts(O.PUNT, 30, receivers_spot=25)
    flow.down = PEN.Down(1, 30, 4, 8)
    flow.kicks26, rig.rules.kicks.caught = True, True
    assert "P37" in {f.id for f in flow.rows_for(facts, False)}
    rig.rules.kicks.caught = False
    assert "P37" not in {f.id for f in flow.rows_for(facts, False)}
    flow.kicks26 = False
    rig.rules.kicks.caught = True
    assert not {"P34", "P35", "P36", "P37"} & {f.id for f in flow.rows_for(facts, False)}
    flow.kicks26 = True
    goal = PEN.PlayFacts(O.FIELD_GOAL_MISSED, 30)
    assert "P36" in {f.id for f in flow.rows_for(goal, False)}
    kick = PEN.PlayFacts(O.KICKOFF_RETURN, 30)
    assert {"P34", "P35"} <= {f.id for f in flow.rows_for(kick, False)}


def test_kick_catch_interference_gives_the_receivers_15_yards_beyond_their_catch():
    foul = F.BY_ID["P37"][0]
    down = PEN.Down(1, 30, 4, 8)
    result = PEN.accept(foul, down, PEN.PlayFacts(O.PUNT, 30, receivers_spot=25))
    assert (result.kind, result.ball, result.los, result.new_series, result.yards) == (PEN.NEW_DOWN, 2, 40, True, 15)
    near = PEN.accept(foul, down, PEN.PlayFacts(O.PUNT, 30, receivers_spot=90))
    assert near.los == 95 and near.notes                       # half the distance to the goal


def test_a_missed_field_goals_declined_result_is_the_spot_of_the_kick():
    down = PEN.Down(1, 70, 4, 6)
    assert PEN.play_result(down, PEN.PlayFacts(O.FIELD_GOAL_MISSED, 70, receivers_spot=37)).los == 37
    assert PEN.play_result(down, PEN.PlayFacts(O.FIELD_GOAL_MISSED, 70)).los == 30          # the original's spot


def test_the_new_fouls_have_names_that_penalties_txt_can_hold():
    for foul_id in ("P34", "P35", "P36", "P37"):
        name = PL.DEFAULT_TABLE.name(foul_id)
        assert 1 <= len(name) <= 30 and "," not in name and ";" not in name
        assert all(f.kicks2026 for f in F.BY_ID[foul_id])
    assert not any(f.kicks2026 for f in F.FOULS if f.id < "P34")
