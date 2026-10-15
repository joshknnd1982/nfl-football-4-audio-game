"""The next-play step, quarters, warnings, half time, overtime, the statistics, the key waits and the end (GAME_SPEC 5.6, 4.19; Q14, Q24, Q25, Q26, Q27). This is inspired by Jim Kitchen.

Strict draws written by hand from the lifted pag: 0x43cc68 (the next-play step), GoSub 0x45f30f (the key wait), GoSub
0x45d0be (the statistics), 0x4533d7 (the end of the game), halftime p_485b80.
"""
import pytest

from nfl4.audio.output import SLOT_CROWD1, SLOT_CROWD2
from nfl4.game import phrases as P
from pagrig import Draws, engine_rig, run_steps, sounds_played, texts

ENTER, F1, F2, F3, F4 = 13, 112, 113, 114, 115
BALL = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)


def break_rig(tmp_path, answers, **state):
    fields = dict(BALL)
    fields.update(state)
    rig = engine_rig(tmp_path, answers=answers, **fields)
    rig.game.quarter_clock.set_warnings(5, 6, 7)
    return rig


def stats_lines(number, own=0, opponent=0):
    """The 34 lines of the statistics when every number is 0 except the points (4.19)."""
    lines = [P.STATS_AFTER + str(number)]
    for name in P.STAT_NAMES:
        lines.append(name)
        if name == " Points Scored":
            lines += ["Bengals %d" % own, "Jets %d" % opponent]
        else:
            lines += ["Bengals 0", "Jets 0"]
    return lines


def test_a_play_that_is_not_the_last_goes_to_the_menu_of_the_side_with_the_ball(tmp_path):
    rig = break_rig(tmp_path, [], quarter=1, counter=5)
    assert run_steps(rig, rig.engine.next_play, Draws(), until=("offense_menu", "defense_menu")) == "offense_menu"
    assert rig.engine.s.counter == 6 and rig.said == [] and rig.engine.s.defense == 2


def test_the_end_of_the_first_quarter_the_wait_the_statistics_then_position_and_down(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=1, counter=32)
    log = []
    rig.game.log_sink = log.append
    d = Draws().rnd(4, 1)                                            # the banter draw before the position (A-15)
    assert run_steps(rig, rig.engine.next_play, d, until=("offense_menu",)) == "offense_menu"
    assert texts(rig) == [" End of the First Quarter"] + stats_lines(1) + [" it's your ball on your 30yard line",
                                                                          " it's first down and 10yards to go"]
    s = rig.engine.s
    assert (s.quarter, s.counter) == (2, 1) and rig.game.quarter_clock.countdown == 100
    assert sounds_played(rig) == ["foot11"]
    assert log[:2] == ["", " End of the First Quarter"]


def test_the_two_minute_warning_comes_when_the_counter_equals_the_plays_minus_m2w(tmp_path):
    rig = break_rig(tmp_path, [], quarter=2, counter=27)            # 33 - 5 = 28 after this play
    run_steps(rig, rig.engine.next_play, Draws(), until=("offense_menu",))
    assert texts(rig) == [" Two Minute Warning"] and sounds_played(rig) == ["foot11"]
    rig2 = break_rig(tmp_path / "b", [], quarter=2, counter=28)
    run_steps(rig2, rig2.engine.next_play, Draws(), until=("offense_menu",))
    assert rig2.said == [] and rig2.game.ptf == 0


def test_half_time_gives_the_ball_to_the_side_that_did_not_receive_first_with_halftimes_sounds(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=2, counter=32, opening_receiver=1)
    d = Draws().raw(0.5)                                             # halftime's Int(Rnd * 10) + 10, replaced by 15
    for _ in range(15):
        d.raw(0.05).raw(0.9)
    assert run_steps(rig, rig.engine.next_play, d, until=("kick_off",)) == "kick_off"
    assert texts(rig) == [" End of the Second Quarter"] + stats_lines(2)
    assert sounds_played(rig) == ["foot11", "foot0"] + ["foot15"] * 15 + ["foot0"]
    s = rig.engine.s
    assert (s.quarter, s.counter, s.wisoff, s.defense, s.half) == (3, 0, 2, 1, 1)


def test_without_a_recorded_receiver_the_player_receives_the_second_half(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=2, counter=32, opening_receiver=None)
    d = Draws().raw(0.5)
    for _ in range(15):
        d.raw(0.05).raw(0.9)
    run_steps(rig, rig.engine.next_play, d, until=("kick_off",))
    assert rig.engine.s.wisoff == 1


def test_the_third_quarter_lasts_all_its_plays_q14(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=3, counter=32)
    run_steps(rig, rig.engine.next_play, Draws().rnd(4, 1), until=("offense_menu",))
    assert texts(rig)[0] == " End of the Third Quarter" and rig.engine.s.quarter == 4


def test_a_tie_after_four_quarters_goes_to_overtime_with_the_right_statistics_number_q26(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=4, counter=32, wisoff=2, defense=1, half=1)
    assert run_steps(rig, rig.engine.next_play, Draws(), until=("kick_off",)) == "kick_off"
    assert texts(rig) == [" End of the Fourth Quarter", " We are going into over time number  1"] + stats_lines(4)
    s = rig.engine.s
    assert (s.quarter, s.counter, s.overtime, s.wisoff, s.defense, s.half) == (5, 0, 1, 2, 1, 1)   # Q25: half set
    assert sounds_played(rig) == ["foot11"]


def test_the_end_of_a_won_game_final_score_wait_statistics_and_the_crowds_stop(tmp_path):
    rig = break_rig(tmp_path, [F1, F2, ENTER, ENTER], quarter=4, counter=32)
    rig.engine.s.stats[1].score = 7
    rig.game.replay[:] = [" last line "]
    assert run_steps(rig, rig.engine.next_play, Draws(), until=("never",)) is None
    final = [" The Final score is", "Bengals.  7. Jets.  0"]
    assert texts(rig) == ([" End of the Fourth Quarter", " THE GAME IS OVER"] + final + final
                          + [" here's the instant rea play ", " last line ", " End of the Fourth Quarter",
                             " THE GAME IS OVER"] + final + stats_lines(4, 7, 0))      # say4 lines are in the replay
    assert rig.engine.result.scores == (7, 0) and rig.game.m414 is None    # play_game keeps m414
    assert [e.slot for e in rig.slot_log if e.action == "stop"][-2:] == [SLOT_CROWD1, SLOT_CROWD2]


def test_a_score_in_overtime_ends_the_game_at_once_and_its_statistics_number_is_5(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=5, overtime=1, counter=3, points=3)
    assert run_steps(rig, rig.engine.score, Draws(), until=("never",)) is None
    assert texts(rig) == [" THE GAME IS OVER", " The Final score is", "Bengals.  3. Jets.  0"] + stats_lines(5, 3, 0)


def test_a_safety_in_overtime_ends_the_game_too_q24(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=5, overtime=1, counter=3, wisoff=1, defense=2,
                    tackle_sentence=" ODef1 sacks Starr ")
    assert run_steps(rig, rig.engine.safety, Draws(), until=("never",)) is None
    assert texts(rig)[:4] == [" ODef1 sacks Starr ", " in the end zone for a safety", " THE GAME IS OVER",
                              " The Final score is"]
    assert rig.engine.result.scores == (0, 2)


def test_the_end_of_an_overtime_period_without_a_score_plays_foot2_and_starts_the_next(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=5, overtime=1, counter=32)
    assert run_steps(rig, rig.engine.next_play, Draws(), until=("kick_off",)) == "kick_off"
    assert texts(rig)[0] == " We are going into over time number  2" and rig.engine.s.overtime == 2
    assert texts(rig)[1] == P.STATS_AFTER + "5"
    assert sounds_played(rig) == ["foot2"]


def test_the_super_bowl_game_runs_its_presentation_once_and_ends_the_season_q27(tmp_path):
    rig = break_rig(tmp_path, [ENTER], quarter=4, counter=32)
    rig.engine.s.stats[2].score = 3
    rig.game.season.gtp = 20
    calls = []

    def presentation(scores):                      # the real presentation has its own tests (test_superbowl.py)
        calls.append(scores)
        rig.game.season.gtp = 42                   # what superbowl's last statement does

    rig.game.superbowl = presentation
    run_steps(rig, rig.engine.next_play, Draws(), until=("never",))
    assert calls == [(0, 3)] and rig.game.season.gtp == 0
    assert " The Final score is" not in texts(rig)


def test_the_key_wait_f1_hint_f2_replay_f3_score_f4_clock_then_any_key(tmp_path):
    rig = break_rig(tmp_path, [F1, F2, F3, F4, ENTER])
    rig.game.replay[:] = [" a line "]
    source = __import__("randsources").ScriptedRandom(Draws().below(30, 15).values, strict=True)
    rig.rnd.source = source
    rig.engine.key_wait()
    spoken = texts(rig)
    assert spoken[:5] == [P.PRESS_ANY_KEY, " here's the instant rea play ", " a line ", " The score is ", " tied 0 all"]
    assert spoken[5].endswith(" remaining in the first quarter. ") and len(spoken) == 6


def test_the_statistics_wait_replays_without_the_introduction_on_f1_and_f2(tmp_path):
    rig = break_rig(tmp_path, [F2, F1, ENTER], quarter=3)
    rig.engine.quarter_stats()
    spoken = texts(rig)
    assert spoken[:34] == stats_lines(2)
    assert spoken[34:] == stats_lines(2) + stats_lines(2)            # the replay is the statistics, norep = 1
    assert rig.game.norep == 0 and rig.game.replay == []
