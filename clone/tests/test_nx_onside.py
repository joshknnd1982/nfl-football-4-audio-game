"""Onside kicks in the play engine: the player's question, the computer's declaration, the kick and its results, the fouls of
the kick, the kick made again, the statistics, the help and the remarks (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 8 and 15;
PX SX.4). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source and every expected number is worked out from the rule next to it, never
from a run of the game (B-X38); the speech is the fake SAPI's list of (text, speaker, rate step).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import onside as ON
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.state import ExtrasRecord
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.rules import (CLASSIC, KICK_AGAIN, NEXT_DOWN, NORMAL_KICKOFF, ONSIDE_KEPT, ONSIDE_KICKOFF, ONSIDE_LOST,
                             ONSIDE_RUN)
from nflrig import nfl_engine_rig
from pagrig import Draws, sounds_played
from randsources import ScriptedRandom

ENTER, TAB, UP, DOWN, F1, F2, F3, F4 = 13, 9, 38, 40, 112, 113, 114, 115
QUESTION = " Kim do you wish to try an onside kick "
YES, NO = " yes ", " no "


def script(rig, draws: Draws):
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []


def check(rig, draws: Draws):
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert rig.rnd.source.left == 0


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def game(tmp_path, answers=(), comments=False, onside=True, always=False, penalties=False, scores=(10, 17),
         auto_sides=(2,), left=400, **state):
    """A kick-off in the fourth quarter: the Jets (side 2) receive, the Bengals (side 1, the player) kick and trail 10 to 17
    with 400 seconds left (timeouts off: nothing is said about them)."""
    defaults = dict(wisoff=2, defense=1, half=1, yard_line=0, down=1, to_go=10, quarter=4)
    defaults.update(state)
    extras = defaults.pop("extras", {})
    extras.setdefault("left", left)
    rules = NflRules(timeouts_on=False, auto_sides=auto_sides, penalties_on=penalties, onside_on=onside,
                     onside_always=always)
    rig = nfl_engine_rig(tmp_path, answers=answers, comments=comments, rules=rules, extras=extras, **defaults)
    rig.engine.s.stats[1].score, rig.engine.s.stats[2].score = scores
    return rig


def kick_draws(distance: int = 10, recovered: bool = True, roll: int = 50, returner: int = 2, left: int = 4):
    """The draws of a kick up to its result and the live time: rady, the distance 8 to 14 (below(7) + 8), the recovery
    (below(100) < 8), then for a kick nobody recovered the roll and the receivers' player, then L = 3 to 5."""
    draws = Draws().rady(0).below(7, distance - 8).below(100, 5 if recovered else 50)
    if not recovered:
        draws.below(100, roll).rnd(2, returner)
    return draws


# ----- the rules as plain functions (design 8.2 and 8.4), every number from the rule -----

@pytest.mark.parametrize("quarter, left, lead, always, due", [
    (3, 800, -1, False, True),        # trailing in the third quarter
    (4, 500, -3, False, True),        # trailing in the fourth
    (2, 100, -10, False, False),      # not before the second half
    (1, 900, -10, False, False),
    (3, 800, 0, False, False),        # tied
    (3, 800, 3, False, False),        # leading in the third quarter
    (4, 300, 1, False, True),         # leading by one score with 5:00 left
    (4, 300, 8, False, True),         # 8 points is still one score
    (4, 300, 9, False, False),        # 9 is not
    (4, 301, 1, False, False),        # more than 5:00 left
    (4, 100, 0, False, False),        # tied late: not asked
    (5, 400, -3, False, False),       # overtime: never unless always
    (5, 400, 3, False, False),
    (5, 400, -3, True, True),
    (1, 900, 0, True, True),          # always: at every kick-off
    (2, 100, 20, True, True),
])
def test_the_question_is_due_by_the_rule_of_design_8_2(quarter, left, lead, always, due):
    assert ON.question_due(quarter, left, lead, always) is due


@pytest.mark.parametrize("quarter, left, deficit, rule", [
    (4, 120, 1, (9, 10)),             # 2:00 or less, any deficit: 9 in 10 (the SX.4 calibration lifted the design's limit of 16)
    (4, 1, 16, (9, 10)),
    (4, 120, 17, (9, 10)),
    (4, 121, 5, None),                # 2:01 to 5:00 needs 9 or more down
    (4, 121, 9, (6, 10)),
    (4, 300, 30, (6, 10)),
    (4, 301, 8, None),                # 5:01 to 10:00 needs 9 or more down (the calibration moved it from 17)
    (4, 301, 9, (1, 4)),
    (4, 301, 17, (1, 4)),
    (4, 600, 40, (1, 4)),
    (4, 601, 40, None),               # more than 10:00 left: never
    (4, 100, 0, None),                # not trailing: never
    (4, 100, -7, None),
    (3, 100, 10, None),               # only the fourth quarter
    (5, 100, 10, None),
])
def test_the_computers_rules_of_design_8_4(quarter, left, deficit, rule):
    assert ON.computer_rule(quarter, left, deficit) == rule


# ----- the player's question -----

def test_the_player_says_yes_with_y_and_enter_and_the_kick_follows(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER])
    step = rig.engine.kick_off()
    assert step.__name__ == "onside_kick" and rig.engine.s.extras.kick_kind == ONSIDE_KICKOFF
    assert texts(rig) == [QUESTION, NO, YES]                          # the answer starts at no


def test_enter_takes_no_and_the_normal_kick_off_follows(tmp_path):
    rig = game(tmp_path, answers=[ENTER])
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == [QUESTION, NO] and rig.engine.s.extras.kick_kind == NORMAL_KICKOFF


def test_up_down_and_tab_change_the_answer_and_n_sets_no(tmp_path):
    rig = game(tmp_path, answers=[UP, DOWN, TAB, "n", "y", ENTER])
    assert rig.rules.before_kickoff(rig.engine.s, 1) == ONSIDE_KICKOFF
    assert texts(rig) == [QUESTION, NO, YES, NO, YES, NO, YES]


def test_f1_asks_again_f3_says_the_score_and_the_keypad_one_is_not_y(tmp_path):
    rig = game(tmp_path, answers=[F1, F3, 97, ENTER])                 # the keypad's 1 types "a" in this key model (B-W6)
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == [QUESTION, NO, QUESTION, NO,                  # F1: the question again
                          " The score is ", "Jets.  17. Bengals.  10",  # F3: the score, then the question again
                          QUESTION, NO, "a",                           # the keypad's 1: the letter a is echoed, not y
                          QUESTION, NO]


def test_the_player_is_not_asked_when_it_does_not_make_sense_and_nothing_is_drawn(tmp_path):
    rig = game(tmp_path, answers=[], scores=(24, 17), left=400)       # leads by 7 with 6:40 left: not late enough
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == [] and rig.engine.s.extras.kick_kind == NORMAL_KICKOFF


def test_the_always_setting_asks_at_every_kick_off(tmp_path):
    rig = game(tmp_path, answers=[ENTER], always=True, quarter=1, scores=(0, 0))
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == [QUESTION, NO]


def test_with_the_switch_off_there_is_no_question_and_no_kick(tmp_path):
    rig = game(tmp_path, answers=[], onside=False, always=True)
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF
    assert texts(rig) == []


def test_the_first_kick_off_still_records_its_receiver_when_it_is_an_onside_kick(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], always=True, quarter=1, scores=(0, 0), first_kickoff=True)
    step = rig.engine.kick_off()
    s = rig.engine.s
    assert step.__name__ == "onside_kick" and s.opening_receiver == 2 and s.first_kickoff is False


def test_an_unknown_kind_of_kick_off_is_refused(tmp_path):
    rig = game(tmp_path)
    rig.rules.before_kickoff = lambda state, side: "squib"
    with pytest.raises(ValueError):
        rig.engine.kick_off()


# ----- the computer's declaration -----

def test_the_computer_declares_by_its_rule_and_says_so_when_the_kick_begins(tmp_path):
    rig = game(tmp_path, scores=(17, 10), left=100, defense=2, wisoff=1, half=2)       # the Jets kick and trail 10 to 17
    s = rig.engine.s
    script(rig, Draws().rnd(10, 9))                                    # 9 in 10: a draw of 9 declares
    assert rig.rules.before_kickoff(s, 2) == ONSIDE_KICKOFF
    assert texts(rig) == [] and s.extras.kick_kind == ONSIDE_KICKOFF   # the decision says nothing yet ...
    draws = kick_draws(distance=10)                                    # the kick only: the live time comes with the end point
    script(rig, draws)
    rig.rules.onside_kick(s)
    check(rig, draws)
    assert texts(rig)[:2] == [" the Jets will try an onside kick. ", " the Jets line up for an onside kick. "]   # ... the kick does


def test_the_declaration_is_in_the_replay_list_that_f2_speaks(tmp_path):
    rig = game(tmp_path, scores=(17, 10), left=100, defense=2, wisoff=1, half=2)
    script(rig, Draws().rnd(10, 9))
    step = rig.engine.kick_off()                                       # the engine clears the replay list, then the kick
    assert step.__name__ == "onside_kick"
    draws = kick_draws(distance=10).below(3, 0)
    script(rig, draws)
    step()
    assert rig.game.replay[:2] == [" the Jets will try an onside kick. ", " the Jets line up for an onside kick. "]


def test_a_kick_made_again_does_not_declare_again(tmp_path):
    rig = game(tmp_path, scores=(17, 10), left=100, defense=2, wisoff=1, half=2, extras=dict(rekick=True, kick_kind="onside"))
    draws = kick_draws(distance=10)
    script(rig, draws)
    rig.rules.onside_kick(rig.engine.s)
    check(rig, draws)
    assert " the Jets will try an onside kick. " not in texts(rig)


def test_the_kick_moves_back_at_most_half_the_distance_to_the_goal_line(tmp_path):
    rig = game(tmp_path, scores=(17, 10), left=100, defense=2, wisoff=1, half=2, extras=dict(kick_kind="normal"))
    x = rig.engine.s.extras
    seen = []
    for _ in range(12):                                                # an accepted offside again and again
        x.kick_again, x.kick_back = True, 5
        rig.rules.before_kickoff(rig.engine.s, 2)
        seen.append(x.kick_from)
    assert seen[:7] == [30, 25, 20, 15, 10, 5, 3]                      # from the 5 the half distance is 2, so 3
    assert seen[7:] == [2, 1, 1, 1, 1]                                 # from 3 it is 1, from 2 it is 1, from 1 nothing


def test_the_computer_does_not_declare_when_the_draw_is_above_its_chance(tmp_path):
    rig = game(tmp_path, scores=(17, 10), left=100, defense=2, wisoff=1, half=2)
    script(rig, Draws().rnd(10, 10))
    assert rig.rules.before_kickoff(rig.engine.s, 2) == NORMAL_KICKOFF and texts(rig) == []


@pytest.mark.parametrize("left, scores, size, kick, skip", [
    (250, (19, 10), 10, 6, 7),         # 9 down with 4:10 left: 6 in 10
    (500, (27, 10), 4, 1, 2),          # 17 down with 8:20 left: 1 in 4
])
def test_the_other_two_rules_draw_their_own_chances(tmp_path, left, scores, size, kick, skip):
    for value, kind in ((kick, ONSIDE_KICKOFF), (skip, NORMAL_KICKOFF)):
        rig = game(tmp_path / str(value), scores=scores, left=left, defense=2, wisoff=1, half=2)
        script(rig, Draws().rnd(size, value))
        assert rig.rules.before_kickoff(rig.engine.s, 2) == kind
        check(rig, Draws().rnd(size, value))


@pytest.mark.parametrize("quarter, left, scores", [
    (3, 100, (40, 10)),                # only the fourth quarter
    (4, 200, (13, 10)),                # 3 down with 3:20 left: no rule
    (4, 100, (10, 10)),                # tied
    (4, 100, (10, 17)),                # leading
    (4, 700, (40, 10)),                # more than 10:00 left
    (5, 100, (10, 17)),
])
def test_the_computer_never_declares_and_draws_nothing_otherwise(tmp_path, quarter, left, scores):
    rig = game(tmp_path, scores=scores, quarter=quarter, left=left, defense=2, wisoff=1, half=2)
    script(rig, Draws())
    assert rig.rules.before_kickoff(rig.engine.s, 2) == NORMAL_KICKOFF
    assert texts(rig) == []


def test_always_does_not_change_the_computer(tmp_path):
    rig = game(tmp_path, always=True, scores=(10, 10), quarter=2, left=700, defense=2, wisoff=1, half=2)
    script(rig, Draws())
    assert rig.rules.before_kickoff(rig.engine.s, 2) == NORMAL_KICKOFF


# ----- the kick and its results (design 8.3) -----

def test_the_kicking_team_recovers_it(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER])
    s = rig.engine.s
    step = rig.engine.kick_off()
    start = len(texts(rig))
    draws = kick_draws(distance=10).below(3, 1)                        # 10 yards, recovered, L = 3 + 1
    script(rig, draws)
    step = step()
    check(rig, draws)
    assert texts(rig)[start:] == [" the Bengals line up for an onside kick. ", " the Jets send in their hands team. ",
                                  " Kick1 bounces the ball along the ground. ", " there is a scramble for the ball. ",
                                  " and the Bengals recover it. "]
    assert sounds_played(rig) == ["foot11", "foot7", "foot14", "foot12", "foot11"]   # whistle, kick, noise, crowd, whistle
    assert step == rig.engine.possession and s.text == P.ITS
    assert (s.half, s.yard_line, s.wisoff) == (2, 45, 2)               # the Bengals' own 35 + 10, flipped by possession
    assert s.extras.onside_tried == [1, 0] and s.extras.onside_recovered == [1, 0]
    assert s.extras.left == 396 and not rig.sounds.play_noise_running()      # L = 4 seconds; the whistle stopped the noise
    script(rig, Draws())
    assert step() == rig.engine.down_sentence
    assert texts(rig)[-1] == P.ITS + P.YOUR_BALL + P.ON + P.YOUR + " 45" + P.YARD_LINE_SPACED
    assert s.wisoff == 1 and (s.down, s.to_go) == (1, 10)


def test_the_receivers_fall_on_the_ball(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER])
    s = rig.engine.s
    step = rig.engine.kick_off()
    draws = kick_draws(distance=8, recovered=False, roll=50, returner=2).below(3, 0)
    script(rig, draws)
    start = len(texts(rig))
    step = step()
    check(rig, draws)
    assert texts(rig)[-1] == " and ORet2 falls on the ball. "
    assert step == rig.engine.position and s.text == P.ITS_CAPITAL
    assert (s.half, s.yard_line, s.wisoff, s.down, s.to_go) == (2, 43, 2, 1, 10)      # 35 + 8 from the Bengals' goal
    assert s.extras.onside_tried == [1, 0] and s.extras.onside_recovered == [0, 0]
    assert s.extras.left == 397                                        # L = 3 + 0
    assert sounds_played(rig)[-1] == "foot11" and len(texts(rig)) - start == 5


def test_the_distance_runs_from_8_to_14_yards(tmp_path):
    for distance in (8, 14):
        rig = game(tmp_path / str(distance), answers=["y", ENTER])
        step = rig.engine.kick_off()
        draws = kick_draws(distance=distance, recovered=False).below(3, 0)
        script(rig, draws)
        step()
        assert rig.engine.s.yard_line == 35 + distance and rig.engine.s.half == 2


def test_a_recovery_needs_a_draw_below_the_eight_percent_chance(tmp_path):
    for value, kept in ((7, True), (8, False)):
        rig = game(tmp_path / str(value), answers=["y", ENTER])
        step = rig.engine.kick_off()
        draws = Draws().rady(0).below(7, 3).below(100, value)
        if not kept:
            draws.below(100, 50).rnd(2, 1)
        script(rig, draws.below(3, 2))
        step()
        assert rig.engine.s.extras.onside_recovered == ([1, 0] if kept else [0, 0])


def test_the_receivers_pick_it_up_and_run(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER])
    s = rig.engine.s
    step = rig.engine.kick_off()
    # roll 2 (a return, not a touchdown), the receivers' first player, 5 + below(40) = 15 yards, tacklers Def4 and Def9
    draws = Draws().rady(0).below(7, 2).below(100, 50).below(100, 2).rnd(2, 1).below(40, 10).rnd(17, 4).rnd(17, 9)
    script(rig, draws)
    step = step()
    check(rig, draws)
    assert step == rig.engine.end_of_play and texts(rig)[-1] == " ORet1 picks it up and runs "
    assert (s.half, s.yard_line, s.wisoff) == (2, 45, 2)               # the ball at the Bengals' 45 before the run
    assert s.yards == 15 and s.result_kind == O.KICKOFF_RETURN and s.return_flag is True and s.to_go == 1
    assert s.tackle_sentence == P.CUT_DOWN + " Def4 " + P.AND + "Def9 " and s.tackle_sound == 2
    assert s.extras.onside_tried == [1, 0] and s.extras.left == 400    # the live time comes with the end of the play
    script(rig, Draws())
    assert step() == rig.engine.field_play_end and s.yard_line == 30   # 45 - 15 toward the Bengals' goal, nobody scores
    draws = Draws().below(4, 1)                                        # L = 3 + 15 \ 10 + 1 = 5 seconds
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    assert texts(rig)[-2:] == [P.CUT_DOWN + " Def4 " + P.AND + "Def9 ", P.GAIN + "15" + P.YARD + P.PLURAL + P.ON_THE_PLAY]
    assert s.extras.left == 395 and s.stats[2].first_downs == 1 and step == rig.engine.banter_position


def test_a_long_return_is_never_a_touchdown_by_chance(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], extras=dict(safety_kick=True))      # a kick from the 20 and 8 yards: the 28
    step = rig.engine.kick_off()
    # a return of 5 + below(40) = 5 + 39 = 44 yards would pass the goal line; the first tackler is Def1, the second draw is
    # the same player and is drawn again (Def2)
    draws = (Draws().rady(0).below(7, 0).below(100, 50).below(100, 3).rnd(2, 2).below(40, 39).rnd(17, 1).rnd(17, 1)
             .rnd(17, 2))
    script(rig, draws)
    step()
    check(rig, draws)
    s = rig.engine.s
    assert s.yard_line == 28 and s.yards == 27                          # capped at 28 - 1: the run stops on the 1
    assert s.tackle_sentence == P.TACKLED + " Def1 " + P.AND + "Def2 "   # 27 is from 20 to 29: tackled


def test_one_in_a_hundred_failures_is_a_touchdown_all_the_way(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER])
    s = rig.engine.s
    step = rig.engine.kick_off()
    draws = Draws().rady(0).below(7, 3).below(100, 50).below(100, 0).rnd(2, 2)
    script(rig, draws)
    step = step()
    check(rig, draws)
    assert step == rig.engine.end_of_play and texts(rig)[-1] == " ORet2 picks it up and runs "
    assert s.yards == 46 and (s.half, s.yard_line) == (2, 46)          # the ball at the 35 + 11 and all the way home
    assert step() == rig.engine.touchdown and s.yard_line == 0


def test_the_kick_from_the_twenty_after_a_safety(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER])
    s = rig.engine.s
    outcome = O.PlayOutcome(O.SAFETY_KIND, 2, 1, 1, score="safety")
    script(rig, Draws().below(4, 0))                                   # the safety's live time: a run's 4 to 7 seconds
    rig.rules.after_outcome(s, outcome)
    assert s.extras.safety_kick is True
    step = rig.engine.kick_off()
    assert s.extras.kick_from == 20 and s.extras.safety_kick is False
    draws = kick_draws(distance=12, recovered=False).below(3, 0)
    script(rig, draws)
    step()
    assert (s.half, s.yard_line) == (2, 32)                            # the 20 + 12
    rig.rules.before_kickoff(s, 2)                                     # the next kick-off is from the 35 again
    assert s.extras.kick_from == 35


def test_a_safety_on_the_last_play_of_a_half_does_not_move_the_next_kick_off(tmp_path):
    rig = game(tmp_path, quarter=2, extras=dict(left=0, safety_kick=True, kick_again=True, kick_back=5, kick_from=30,
                                                kick_kind="onside"))
    x = rig.engine.s.extras
    assert rig.rules.before_kickoff(rig.engine.s, 1) == "period over"
    assert (x.safety_kick, x.kick_again, x.rekick, x.kick_back) == (False, False, False, 0)
    x.left = 900
    assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF       # quarter 2: the player is not asked
    assert x.kick_from == 35                                           # not the 20, not the 30 of the kick left over


def test_classic_has_no_onside_kick():
    with pytest.raises(RuntimeError):
        CLASSIC.onside_kick(None)
    assert CLASSIC.before_kickoff(None, 1) == NORMAL_KICKOFF


@pytest.mark.parametrize("code", [96, 97, 105, 106, 107, 109, 110, 111])
def test_no_key_of_the_keypad_answers_the_question(tmp_path, code):
    """The whole keypad types letters in this key model (96 to 105 the letters a to i, and 106 to 111 j, k, m, n, o): the
    dot is an n and must not answer no (found by the review: only 96 to 105 were guarded)."""
    rig = game(tmp_path, answers=[DOWN, code, ENTER])                  # Down says yes; the keypad key is only echoed
    assert rig.rules.before_kickoff(rig.engine.s, 1) == ONSIDE_KICKOFF
    said = texts(rig)
    assert said.count(QUESTION) == 2 and said[-1] == YES and said.count(NO) == 1


def test_the_record_refuses_a_kick_from_beyond_the_35_or_before_the_goal_line():
    for value in (0, 36, -5):
        x = ExtrasRecord()
        x.kick_from = value
        with pytest.raises(ValueError):
            x.check()
    x = ExtrasRecord()
    x.kick_from = 35
    x.check()
