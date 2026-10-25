"""Penalty enforcement as plain functions: every foul of the table against the 2026 rules, the worked examples of the
research, offsetting fouls, scores, turnovers, kicks, the two-point try, the half-distance property and the computer's
choice (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 9.3, 9.4; NFL_RULES_RESEARCH Part 6; PX SX.3). This is inspired by Jim Kitchen.

Every expected value below is worked out from the rule cited next to it, not from the code. Positions are yards from the
offense's own goal line (own 35 is 35, the defense's 10 is 90).
"""
import random

import pytest

from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras.penalties import Down, PlayFacts, Result
from nfl4.game import outcome as O

AFD, LOSS, HALF, MORE = X.text("NXP-09"), X.text("NXP-10"), X.text("NXP-11"), X.text("NXP-14")


def foul(foul_id, offender=None):
    rows = F.BY_ID[foul_id]
    if offender is None:
        return rows[0]
    return next(f for f in rows if f.offender == offender)


def run(los, end, **kw):
    return PlayFacts(O.RUN, end, offense_play=1, **kw)


def complete(los, end, **kw):
    return PlayFacts(O.PASS_COMPLETE, end, offense_play=4, **kw)


def incomplete(los, **kw):
    return PlayFacts(O.PASS_INCOMPLETE, los, offense_play=kw.pop("offense_play", 4), **kw)


# ----- the yards (14-2-1) -----

def test_half_the_distance_cuts_a_penalty_to_half_of_the_way_to_the_offenders_goal_line():
    assert PEN.half_distance(30, 15) == (15, False)
    assert PEN.half_distance(10, 15) == (5, True)
    assert PEN.half_distance(4, 5) == (2, True)                       # Part 6 2.9 example 5: own 4, false start: own 2
    assert PEN.half_distance(2, 5) == (1, True)                       # the 2: one yard (the secondary source)
    assert PEN.half_distance(1, 5) == (0, True)                       # the 1: the ball stays (Part 1.5 default)
    assert PEN.move(35, 10, True) == (25, 10, False)
    assert PEN.move(90, 15, False) == (95, 5, True)                   # example 4: the defense's 10, 15 yards: its 5


@pytest.mark.parametrize("yards", [5, 10, 15])
def test_no_distance_penalty_ever_moves_the_ball_more_than_half_way_or_onto_a_goal_line(yards):
    for spot in range(1, 100):
        for by_offense in (True, False):
            new, moved, _ = PEN.move(spot, yards, by_offense)
            to_goal = spot if by_offense else 100 - spot
            assert moved <= to_goal / 2 and moved <= yards and 1 <= new <= 99


# ----- the worked examples of NFL_RULES_RESEARCH Part 6 2.9 -----

def test_example_1_defensive_holding_on_an_incomplete_pass():
    how, accepted, declined = PEN.answers(foul("P09"), Down(1, 35), incomplete(35))
    assert how == PEN.CHOICE
    assert (accepted.kind, accepted.los, accepted.new_series, accepted.yards) == (PEN.NEW_DOWN, 40, True, 5)
    assert accepted.notes == (AFD,) and accepted.penalty_first_down
    assert (declined.los, declined.down, declined.to_go) == (35, 2, 10)
    assert PEN.computer_accepts(1, accepted, declined)


def test_example_2_defensive_holding_on_a_completion_that_made_the_first_down_is_declined():
    _, accepted, declined = PEN.answers(foul("P09"), Down(1, 30, 3, 8), complete(30, 42))
    assert (accepted.los, accepted.new_series) == (35, True)
    assert (declined.los, declined.new_series) == (42, True)
    assert not PEN.computer_accepts(1, accepted, declined)


def test_example_3_offensive_holding_behind_the_end_of_a_run_is_enforced_from_its_spot():
    _, accepted, declined = PEN.answers(foul("P08"), Down(1, 40), run(40, 46), foul_spot=42)
    assert (accepted.los, accepted.down, accepted.to_go, accepted.yards) == (32, 1, 18, 10)     # 42 - 10, line 50
    assert (declined.down, declined.to_go, declined.los) == (2, 4, 46)
    assert PEN.computer_accepts(2, accepted, declined)


def test_example_4_a_fifteen_yard_foul_at_the_defenses_ten_is_half_the_distance():
    _, accepted, _ = PEN.answers(foul("P14"), Down(1, 90), incomplete(90))
    assert (accepted.los, accepted.new_series, accepted.yards) == (95, True, 5)
    assert accepted.notes == (AFD, HALF)


def test_example_5_a_false_start_on_the_own_4():
    how, accepted, declined = PEN.answers(foul("P01"), Down(1, 4), None)
    assert how == PEN.AUTO_ACCEPT
    assert (accepted.los, accepted.down, accepted.to_go, accepted.notes) == (2, 1, 12, (HALF,))
    assert (declined.los, declined.down, declined.to_go) == (4, 1, 10)


def test_example_6_offside_and_holding_on_one_play_offset_and_the_down_is_played_again():
    result, enforced = PEN.double_foul(foul("P03"), foul("P08"), Down(1, 30, 2, 6), complete(30, 50))
    assert enforced is None
    assert (result.kind, result.los, result.down, result.to_go) == (PEN.NEW_DOWN, 30, 2, 6)


def test_example_7_pass_interference_is_a_first_down_at_the_spot_of_the_foul_with_no_limit():
    _, accepted, _ = PEN.answers(foul("P12"), Down(1, 40), incomplete(40, offense_play=5), foul_spot=80)
    assert (accepted.los, accepted.new_series, accepted.yards, accepted.notes) == (80, True, 40, (AFD,))


# ----- every foul of the table -----

def test_p01_false_start_and_p02_delay_of_game_keep_the_down_from_the_succeeding_spot():
    for foul_id in ("P01", "P02"):
        how, accepted, _ = PEN.answers(foul(foul_id), Down(1, 30, 3, 4), None)
        assert how == PEN.AUTO_ACCEPT
        assert (accepted.los, accepted.down, accepted.to_go, accepted.yards) == (25, 3, 9, 5)


def test_p03_offside_is_five_yards_with_no_automatic_first_down_and_a_free_play():
    _, accepted, declined = PEN.answers(foul("P03"), Down(1, 30), run(30, 39))
    assert (accepted.los, accepted.down, accepted.to_go, accepted.notes) == (35, 1, 5, ())
    assert (declined.los, declined.down, declined.to_go) == (39, 2, 1)
    assert not PEN.computer_accepts(1, accepted, declined)            # 39 against 35: the play is better
    _, accepted, _ = PEN.answers(foul("P03"), Down(1, 30, 3, 4), incomplete(30))
    assert accepted.new_series and accepted.los == 35                 # the distance reaches the line: first and 10


def test_p04_neutral_zone_and_p05_encroachment_no_automatic_first_down():
    for foul_id in ("P04", "P05"):
        _, accepted, _ = PEN.answers(foul(foul_id), Down(1, 30, 3, 8), None)
        assert (accepted.los, accepted.down, accepted.to_go, accepted.new_series) == (35, 3, 3, False)
        _, accepted, _ = PEN.answers(foul(foul_id), Down(1, 30, 3, 5), None)
        assert accepted.new_series and accepted.penalty_first_down     # on the line: first and 10 (14-1-2 Item 5)


def test_p06_illegal_formation_p07_shift_and_p26_too_many_men_from_the_previous_spot():
    for foul_id, by_offense in (("P06", True), ("P07", True), ("P26", False)):
        _, accepted, _ = PEN.answers(foul(foul_id), Down(1, 40, 2, 7), complete(40, 52))
        assert accepted.los == (35 if by_offense else 45) and accepted.down == 2
        assert accepted.to_go == (12 if by_offense else 2) and not accepted.keeps_play


def test_p08_offensive_holding_on_a_pass_from_the_previous_spot_and_behind_the_line_on_a_run():
    _, accepted, declined = PEN.answers(foul("P08"), Down(1, 30, 2, 6), complete(30, 45))
    assert (accepted.los, accepted.down, accepted.to_go) == (20, 2, 16)
    assert PEN.computer_accepts(2, accepted, declined)
    _, accepted, _ = PEN.answers(foul("P08"), Down(1, 30), run(30, 33), foul_spot=28)     # behind the line
    assert (accepted.los, accepted.to_go) == (20, 20)
    _, accepted, _ = PEN.answers(foul("P08"), Down(1, 30), run(30, 27), foul_spot=29)     # the run ended behind it
    assert accepted.los == 20


def test_p08_holding_on_a_sack_is_declined_by_the_defense_to_keep_the_down():
    _, accepted, declined = PEN.answers(foul("P08"), Down(1, 30), PlayFacts(O.SACK, 22, offense_play=4))
    assert (accepted.los, accepted.down, accepted.to_go) == (20, 1, 20)
    assert (declined.los, declined.down, declined.to_go) == (22, 2, 18)
    assert not PEN.computer_accepts(2, accepted, declined)            # 2 yards apart: the second down decides


def test_p09_p10_p11_five_yards_and_an_automatic_first_down_from_the_previous_spot():
    for foul_id in ("P09", "P10", "P11"):
        _, accepted, _ = PEN.answers(foul(foul_id), Down(1, 40, 3, 15), PlayFacts(O.SACK, 33, offense_play=4))
        assert (accepted.los, accepted.new_series, accepted.notes) == (45, True, (AFD,))


def test_p12_pass_interference_in_the_end_zone_is_a_first_down_on_the_one():
    _, accepted, _ = PEN.answers(foul("P12"), Down(1, 70), incomplete(70, offense_play=5), foul_spot=105)
    assert accepted.los == 99 and accepted.new_series and accepted.yards == 29
    _, accepted, _ = PEN.answers(foul("P12"), Down(1, 98), incomplete(98), foul_spot=101)
    assert accepted.los == 99                                         # inside the 2: halfway to the goal line
    _, accepted, _ = PEN.answers(foul("P12"), Down(1, 99), incomplete(99), foul_spot=101)
    assert accepted.los == 99


def test_p13_offensive_pass_interference_ten_from_the_previous_spot_keeps_the_down():
    _, accepted, _ = PEN.answers(foul("P13"), Down(1, 50, 3, 3), complete(50, 70))
    assert (accepted.los, accepted.down, accepted.to_go, accepted.new_series) == (40, 3, 13, False)


def test_p14_roughing_the_passer_from_the_better_of_the_previous_and_the_dead_ball_spot():
    _, accepted, _ = PEN.answers(foul("P14"), Down(1, 30), complete(30, 45))
    assert (accepted.los, accepted.new_series, accepted.keeps_play) == (60, True, True)
    _, accepted, _ = PEN.answers(foul("P14"), Down(1, 30), incomplete(30))
    assert (accepted.los, accepted.keeps_play) == (45, False)


def test_p15_intentional_grounding_loss_of_down_and_the_worse_spot_or_a_safety():
    g = foul("P15")
    _, accepted, declined = PEN.answers(g, Down(1, 30, 2, 10), incomplete(30), foul_spot=23)
    assert (accepted.los, accepted.down, accepted.to_go, accepted.notes) == (20, 3, 20, (LOSS,))
    assert (declined.down, declined.los) == (3, 30)
    assert PEN.computer_accepts(2, accepted, declined)
    _, accepted, _ = PEN.answers(g, Down(1, 8), incomplete(8), foul_spot=2)
    assert (accepted.los, accepted.down) == (2, 2)                    # the spot of the pass is worse than 4 (half way)
    _, accepted, _ = PEN.answers(g, Down(1, 5), incomplete(5), foul_spot=-2)
    assert accepted.kind == PEN.SAFETY and accepted.points == (0, 2)
    _, accepted, _ = PEN.answers(g, Down(2, 40, 4, 3), incomplete(40), foul_spot=33)
    assert (accepted.kind, accepted.ball, accepted.los, accepted.new_series) == (PEN.NEW_DOWN, 1, 70, True)


def test_p16_ineligible_receiver_down_field_five_from_the_previous_spot():
    _, accepted, _ = PEN.answers(foul("P16"), Down(1, 40, 1, 10), complete(40, 48))
    assert (accepted.los, accepted.down, accepted.to_go) == (35, 1, 15)


def test_p17_face_mask_by_the_defense_from_the_end_of_the_run_and_by_the_ball_carrier():
    _, accepted, _ = PEN.answers(foul("P17", F.DEFENSE), Down(1, 30), run(30, 34))
    assert (accepted.los, accepted.new_series, accepted.keeps_play) == (49, True, True)
    _, accepted, _ = PEN.answers(foul("P17", F.DEFENSE), Down(1, 30), PlayFacts(O.SACK, 24, offense_play=4))
    assert (accepted.los, accepted.keeps_play) == (45, False)        # behind the line: from the previous spot
    _, accepted, _ = PEN.answers(foul("P17", F.OFFENSE), Down(1, 30), run(30, 40), foul_spot=35)
    assert (accepted.los, accepted.down, accepted.to_go) == (20, 1, 20)


def test_p18_and_p21_after_the_play_the_down_counts_and_the_yards_are_added():
    for foul_id in ("P18", "P21"):
        _, accepted, declined = PEN.answers(foul(foul_id, F.DEFENSE), Down(1, 30), run(30, 34))
        assert (accepted.los, accepted.new_series, accepted.keeps_play, accepted.yards) == (49, True, True, 15)
        assert (declined.down, declined.to_go) == (2, 6)
        _, accepted, _ = PEN.answers(foul(foul_id, F.OFFENSE), Down(1, 30), run(30, 34))
        assert (accepted.los, accepted.down, accepted.to_go) == (19, 2, 21)
        _, accepted, _ = PEN.answers(foul(foul_id, F.OFFENSE), Down(1, 30), run(30, 45))
        assert (accepted.los, accepted.new_series, accepted.play_first_down) == (30, True, True)   # 14-4-9 Item 1


def test_p19_illegal_block_on_a_run_and_on_a_kick_off_return():
    _, accepted, _ = PEN.answers(foul("P19", F.OFFENSE), Down(1, 30), run(30, 50), foul_spot=40)
    assert (accepted.los, accepted.down, accepted.to_go) == (30, 1, 10)
    kick = PlayFacts(O.KICKOFF_RETURN, 40)
    _, accepted, declined = PEN.answers(foul("P19", F.RECEIVING), Down(1, 0), kick, foul_spot=30)
    assert (accepted.ball, accepted.los, accepted.new_series) == (1, 20, True)
    assert declined.los == 40 and PEN.computer_accepts(2, accepted, declined)


def test_p20_horse_collar_fifteen_from_the_end_of_the_run():
    _, accepted, _ = PEN.answers(foul("P20"), Down(1, 50, 2, 3), run(50, 60))
    assert (accepted.los, accepted.new_series, accepted.keeps_play) == (75, True, True)


def test_p22_running_into_the_kicker_and_p23_roughing_on_a_punt():
    punt = PlayFacts(O.PUNT, 30, receivers_spot=25, offense_play=7)
    _, accepted, declined = PEN.answers(foul("P22"), Down(1, 30, 4, 7), punt)
    assert (accepted.los, accepted.down, accepted.to_go, accepted.notes) == (35, 4, 2, ())
    assert (declined.kind, declined.ball, declined.los) == (PEN.NEW_DOWN, 2, 25)
    assert PEN.computer_accepts(1, accepted, declined)                 # the ball is worth more than 5 yards
    _, accepted, _ = PEN.answers(foul("P23"), Down(1, 30, 4, 7), punt)
    assert (accepted.los, accepted.new_series, accepted.notes) == (45, True, (AFD,))


def test_p22_and_p23_on_a_field_goal_good_is_declined_and_missed_is_accepted():
    good = PlayFacts(O.FIELD_GOAL_GOOD, 75, score="field goal", offense_play=6)
    _, accepted, declined = PEN.answers(foul("P23"), Down(1, 75, 4, 6), good)
    assert declined.kind == PEN.FIELD_GOAL and accepted.erased_score == "field goal"
    assert not PEN.computer_accepts(1, accepted, declined)
    missed = PlayFacts(O.FIELD_GOAL_MISSED, 75, offense_play=6)
    _, accepted, declined = PEN.answers(foul("P23"), Down(1, 75, 4, 6), missed)
    assert (declined.ball, declined.los) == (2, 25) and accepted.los == 87
    assert PEN.computer_accepts(1, accepted, declined)


def test_p24_offside_on_the_kick_off_gives_the_receivers_five_from_the_dead_ball_spot():
    _, accepted, declined = PEN.answers(foul("P24"), Down(1, 0), PlayFacts(O.KICKOFF_TOUCH_BACK, 20))
    assert (accepted.ball, accepted.los, accepted.new_series) == (1, 25, True)
    assert declined.los == 20 and PEN.computer_accepts(1, accepted, declined)
    how, _, _ = PEN.answers(foul("P24"), Down(1, 0), PlayFacts(O.KICKOFF_RETURN, 100, score="touchdown"))
    assert how == PEN.AUTO_DECLINE                                     # the return's touchdown stands


def test_p25_holding_on_a_return_ten_from_the_spot_of_the_foul_and_a_returned_touchdown_erased():
    _, accepted, _ = PEN.answers(foul("P25"), Down(1, 0), PlayFacts(O.KICKOFF_RETURN, 100, score="touchdown"),
                                 foul_spot=80)
    assert (accepted.los, accepted.erased_score) == (70, "touchdown")
    _, accepted, _ = PEN.answers(foul("P25"), Down(1, 0), PlayFacts(O.KICKOFF_RETURN, 30), foul_spot=8)
    assert (accepted.los, accepted.notes) == (4, (HALF,))


def test_p33_belongs_to_the_onside_kick_and_is_never_drawn_before_it_exists():
    assert foul("P33").phases == (F.ONSIDE,) and foul("P33").rate == 4.0     # its rule values are kept for SX.4
    play_phases = {O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK, O.INTERCEPTION, O.PUNT, F.FIELD_GOAL,
                   O.KICKOFF_RETURN, O.KICKOFF_TOUCH_BACK, F.DEAD, F.SNAP, F.AFTER}
    assert not play_phases & set(foul("P33").phases)                  # no play of this build can draw it


# ----- scores, turnovers, the try -----

def test_a_touchdown_pass_with_holding_by_the_offense_is_erased_by_the_defense():
    _, accepted, declined = PEN.answers(foul("P08"), Down(1, 70), complete(70, 100, score="touchdown"))
    assert declined.kind == PEN.TOUCHDOWN and accepted.erased_score == "touchdown" and accepted.los == 60
    assert PEN.computer_accepts(2, accepted, declined)
    assert PEN.situation(accepted, 1).startswith(X.text("NXP-S05") + ", ")


def test_a_touchdown_with_defensive_holding_is_kept_by_the_offense_and_a_personal_foul_goes_to_the_try():
    how, accepted, declined = PEN.answers(foul("P09"), Down(1, 70), complete(70, 100, score="touchdown"))
    assert how == PEN.CHOICE and not PEN.computer_accepts(1, accepted, declined)
    how, _, _ = PEN.answers(foul("P20"), Down(1, 95), run(95, 100, score="touchdown"))
    assert how == PEN.ON_THE_TRY


def test_an_interception_with_a_defense_foul_is_taken_back_and_with_an_offense_foul_kept():
    pick = PlayFacts(O.INTERCEPTION, 40, turnover=True, offense_play=4)
    _, accepted, declined = PEN.answers(foul("P09"), Down(1, 40), pick)
    assert declined.kind == PEN.TURNOVER and declined.pieces == (X.text("NXP-S11"),)
    assert (accepted.ball, accepted.los, accepted.new_series) == (1, 45, True)
    assert PEN.computer_accepts(1, accepted, declined)
    _, accepted, declined = PEN.answers(foul("P13"), Down(1, 40), pick)
    assert not PEN.computer_accepts(2, accepted, declined)
    fumble = PlayFacts(O.RUN, 40, turnover=True, offense_play=1)
    assert PEN.play_result(Down(1, 40), fumble).pieces == (X.text("NXP-S12"),)


def test_a_safety_with_a_defense_foul_is_erased_and_with_an_offense_foul_kept():
    sack = PlayFacts(O.SACK, 0, score="safety", offense_play=4)
    _, accepted, declined = PEN.answers(foul("P09"), Down(1, 3), sack)
    assert declined.kind == PEN.SAFETY and accepted.los == 8 and PEN.computer_accepts(1, accepted, declined)
    _, accepted, declined = PEN.answers(foul("P08"), Down(1, 3), sack)
    assert not PEN.computer_accepts(2, accepted, declined)


def test_the_two_point_try_is_played_again_or_fails():
    try_down = Down(1, 98, two_point=True)
    _, accepted, declined = PEN.answers(foul("P08"), try_down, complete(98, 100, score="two-point"))
    assert declined.kind == PEN.TRY_GOOD and (accepted.kind, accepted.los) == (PEN.TRY_AGAIN, 88)
    assert PEN.computer_accepts(2, accepted, declined)
    _, accepted, declined = PEN.answers(foul("P09"), try_down, incomplete(98))
    assert declined.kind == PEN.TRY_FAILS and (accepted.kind, accepted.los) == (PEN.TRY_AGAIN, 99)
    assert PEN.computer_accepts(1, accepted, declined)
    how, accepted, _ = PEN.answers(foul("P01"), try_down, None)
    assert how == PEN.AUTO_ACCEPT and (accepted.kind, accepted.los) == (PEN.TRY_AGAIN, 93)
    _, accepted, _ = PEN.answers(foul("P15"), try_down, incomplete(98), foul_spot=91)
    assert accepted.kind == PEN.TRY_FAILS
    assert PEN.situation(accepted, 1) == X.text("NXP-S15")
    assert PEN.situation(Result(PEN.TRY_AGAIN, 1, 93), 1) == X.text("NXP-S16", yard=7)


# ----- offsetting (14-5-1) -----

def test_fifteen_against_a_minor_five_is_enforced_alone_from_the_previous_spot():
    result, enforced = PEN.double_foul(foul("P18", F.DEFENSE), foul("P06"), Down(1, 30, 2, 8), run(30, 33))
    assert enforced is foul("P18", F.DEFENSE)
    assert (result.los, result.new_series, result.keeps_play) == (45, True, False)
    result, enforced = PEN.double_foul(foul("P09"), foul("P18", F.OFFENSE), Down(1, 30, 2, 8), complete(30, 33))
    assert enforced is None                                           # defensive holding has a first down: not minor


def test_two_fouls_after_the_play_offset_and_the_play_stands_and_a_kick_off_is_kicked_again():
    result, enforced = PEN.double_foul(foul("P18", F.DEFENSE), foul("P21", F.OFFENSE), Down(1, 30), run(30, 33))
    assert (result.kind, enforced) == (PEN.PLAY_STANDS, None)
    result, _ = PEN.double_foul(foul("P24"), foul("P25"), Down(1, 0), PlayFacts(O.KICKOFF_RETURN, 30))
    assert result.kind == PEN.REPLAY_KICK and result.notes == (X.text("NXP-13"),)


# ----- the computer's choice and the words of the prompt -----

def test_the_computer_prefers_points_then_the_ball_then_a_first_down_then_field_position():
    td = Result(PEN.TOUCHDOWN, 1, points=(6, 0))
    down = Result(PEN.NEW_DOWN, 1, 60, new_series=True)
    assert PEN.better_for(1, td, down) is td and PEN.better_for(2, td, down) is down
    mine = Result(PEN.NEW_DOWN, 1, 40, 4, 2)
    theirs = Result(PEN.NEW_DOWN, 2, 60, new_series=True)
    assert PEN.better_for(1, theirs, mine) is mine
    first = Result(PEN.NEW_DOWN, 1, 41, new_series=True, penalty_first_down=True)
    long = Result(PEN.NEW_DOWN, 1, 47, 4, 1)
    assert PEN.better_for(1, long, first) is first
    assert PEN.computer_accepts(1, Result(PEN.NEW_DOWN, 1, 50, 2, 3), Result(PEN.NEW_DOWN, 1, 44, 2, 9))


def test_the_runoff_is_taken_by_a_defense_that_leads_or_is_tied():
    assert PEN.takes_runoff(2, 3) and PEN.takes_runoff(2, 0) and not PEN.takes_runoff(2, -1)


def test_the_situations_are_said_with_the_original_words_of_the_position():
    assert PEN.situation(Result(PEN.NEW_DOWN, 1, 40, new_series=True), 1) == \
        "it will be first and 10 on your 40 yard line"
    assert PEN.situation(Result(PEN.NEW_DOWN, 1, 95, 2, 5), 1) == "it will be second and goal on my 5 yard line"
    assert PEN.situation(Result(PEN.NEW_DOWN, 1, 50, 3, 4), 1) == "it will be third and 4 on the 50 yard line"
    assert PEN.situation(Result(PEN.NEW_DOWN, 2, 30, new_series=True), 1) == \
        "it will be my ball, first and 10 on my 30 yard line"
    assert PEN.situation(Result(PEN.NEW_DOWN, 1, 70, new_series=True), 2) == \
        "it will be your ball, first and 10 on my 30 yard line"
    assert PEN.situation(Result(PEN.NEW_DOWN, 1, 40, 2, 3, untimed=True), 1).endswith(", " + X.text("NXP-S09"))
    assert PEN.situation(Result(PEN.FIELD_GOAL, 1, points=(3, 0)), 1) == X.text("NXP-S06")


# ----- a property over random plays -----

def test_random_fouls_and_plays_always_give_a_valid_result():
    rnd = random.Random(7)
    kinds = (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK)
    for _ in range(4000):
        los = rnd.randint(1, 99)
        down = Down(rnd.choice((1, 2)), los, rnd.randint(1, 4), rnd.randint(1, 25))
        kind = rnd.choice(kinds)
        end = los if kind == O.PASS_INCOMPLETE else max(1, min(99, los + rnd.randint(-10, 30)))
        facts = PlayFacts(kind, end, offense_play=rnd.randint(1, 5))
        rows = [f for f in F.FOULS if kind in f.phases or F.AFTER in f.phases or F.SNAP in f.phases]
        f = rnd.choice(rows)
        spot = None
        if f.id == "P12":
            spot = los + rnd.randint(5, 40)
        elif f.spot == F.PASS_SPOT:
            spot = los - rnd.randint(5, 9)
        elif f.spot == F.THREE_AND_ONE and kind == O.RUN and end > los:
            spot = rnd.randint(los - 2, end)
        if F.AFTER in f.phases and PEN.play_result(down, facts).ball != down.offense:
            continue
        how, accepted, declined = PEN.answers(f, down, facts, spot)
        for result in (accepted, declined):
            if result.kind == PEN.NEW_DOWN:
                assert 1 <= result.los <= 99 and 1 <= result.down <= 4 and result.to_go >= 1
        if accepted.kind == PEN.NEW_DOWN and f.spot not in (F.SPOT_OF_FOUL, F.PASS_SPOT) and not accepted.keeps_play:
            moved = abs(accepted.los - (down.los if accepted.ball == down.offense else 100 - down.los))
            assert moved <= max(f.yards, 0) or f.spot == F.THREE_AND_ONE
