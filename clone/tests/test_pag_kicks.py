"""Kicks, each path with strict draws written by hand from the lifted code (GAME_SPEC 5.10, 4.16, 4.17; Q17, Q21, Q22, Q23, Q30, Q57). This is inspired by Jim Kitchen.

kicksnap p_43a330; pag 0x441dfa (field goal), 0x442ebe (punt), 0x444645 (kick-off), 0x445772 (return), 0x446c75 (touch
back), 0x44f6f0 (the extra point choice), 0x44fd30 (extra point), 0x450499 (the two-point try's result).
"""
import pytest

from nfl4.audio.output import SLOT_NOISE
from nfl4.game import outcome as O
from nfl4.speech.roles import ANNOUNCER, OPPONENT_PUNTER, OWN_PUNTER
from pagrig import Draws, engine_rig, run_steps, sounds_played, texts

ENTER, UP, DOWN, F1, F3 = 13, 38, 40, 112, 114
AFTER_KICK = ("next_play", "play_menu", "extra_point")
AFTER_TRY = ("next_play", "play_menu", "kick_off")


def quiet_kicksnap(d: Draws) -> Draws:
    """rady after " hut 1 ", no " hut 2 " (Int(Rnd * 3) + 1 = 2), one " hut" (not "!"), its rady, rady before " hike! "."""
    return d.rady().rnd(3, 2).rnd(3, 1).rnd(3, 1).rady().rady()


def plays_of(rig, sound):
    return [e for e in rig.slot_log if e.action == "play" and e.sound_id == "snd_" + sound]


# ----- field goals -----

def field_goal_draws(results):
    d = Draws().rady()
    quiet_kicksnap(d)
    d.rady().rady()
    for value in results:
        d.rnd(70, value)
    return d


def test_a_good_field_goal_three_points_and_the_kick_off_by_the_scorer(tmp_path):
    rig = engine_rig(tmp_path, answers=[ENTER], wisoff=1, defense=2, half=1, yard_line=20, offense_play=6)
    log = []
    rig.game.log_sink = log.append
    d = field_goal_draws([50, 10, 60, 5, 30])                        # 50, 60, 30 above the 20: good
    d.rady()                                                         # after the score
    assert run_steps(rig, rig.engine.snap, d) == "kick_off"
    assert rig.said == [
        (" Kick1 is in for the field goal attempt ", ANNOUNCER, 0), (" Kick2 will hold ", ANNOUNCER, 0),
        (" hut 1 ", OWN_PUNTER, 0), (" hut", OWN_PUNTER, 0), (" hike! ", OWN_PUNTER, 0),
        (" the snap is good ", ANNOUNCER, 0), (" the hold is good", ANNOUNCER, 0),
        (" the kick is up and it ", ANNOUNCER, 0), (" is good", ANNOUNCER, 0), (" The score is ", ANNOUNCER, 0),
        ("Bengals.  3. Jets.  0", ANNOUNCER, 0), (" ", ANNOUNCER, 0)]
    assert sounds_played(rig) == ["foot14", "foot7", "foot12", "foot11"]
    assert plays_of(rig, "foot7")[0].volume == -1500 and plays_of(rig, "foot12")[0].volume == -1200
    s = rig.engine.s
    assert (s.score(1), s.wisoff, s.defense, s.half) == (3, 2, 1, 1)
    assert log[:5] == ["", " Kick1 is in for the field goal attempt ", " Kick2 will hold ", " the snap is good ",
                       " the hold is good"]
    assert rig.game.qorp == 1


@pytest.mark.parametrize("miss, text, level", [(1, " is wide left", -1200), (2, " is wide right", -1200),
                                               (3, " hits the left upright", -1000),
                                               (4, " hits the right upright", -1000),
                                               (5, " hits the cross bar", -1000), (6, " falls short", -1200)])
def test_a_missed_field_goal_its_six_texts_and_levels_and_the_ball_at_the_spot(tmp_path, miss, text, level):
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=1, yard_line=20, offense_play=6)
    log = []
    rig.game.log_sink = log.append
    d = field_goal_draws([1, 1, 50, 1, 1]).rnd(6, miss)
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert texts(rig)[-3:] == [text, " it's  mine on my 20 yard line", " it's first down and 10yards to go"]
    assert plays_of(rig, "foot12")[0].volume == level
    assert rig.engine.s.wisoff == 2
    assert " the kick is up and it " in log[log.index(" it's  mine on my 20 yard line") - 12:]   # the replay is logged


def test_a_field_goal_from_the_own_half_is_way_too_short_and_the_clone_stops_the_play_noise_q57(tmp_path):
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=40, offense_play=6)
    d = Draws().rady()
    quiet_kicksnap(d)
    d.rady().rady()                                                  # no five draws
    run_steps(rig, rig.engine.snap, d)
    assert texts(rig)[-4:] == [" the kick is up and it ", " is way to short", " it's  mine on your 40 yard line",
                               " it's first down and 10yards to go"]
    assert not rig.sounds.play_noise_running()
    assert rig.game.ptf == 1                                         # the log flag stays on (Q30)
    assert [e.action for e in rig.slot_log if e.slot == SLOT_NOISE][-1] == "stop"


# ----- punts -----

def punt_draws(distance_index, ending):
    d = Draws().rnd(6, 1).rnd(17, 1).rnd(17, 2)                      # the draws of the snap (L_440e54)
    d.rady()
    quiet_kicksnap(d)
    d.rady().rady()
    d.below(35, distance_index).rady()
    d.extend(ending)
    return d


def test_a_punt_with_a_fair_catch_its_sentences_and_the_ball_for_the_other_side(tmp_path):
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=30, offense_play=7)
    d = punt_draws(20, Draws().rnd(3, 1).rnd(2, 2))                  # 45 yards, " ORet2 calls for a fair catch "
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert texts(rig) == [" ORet1 and ORet2 are back deep to receive the punt ",
                          " Kick2 is ready to take the snap and  kick the punt ", " hut 1 ", " hut", " hike! ",
                          "Kick2 takes the long snap", " He gets the kick off ", " it's a.  pretty good kick",
                          " it travels 45yards in the air", " ORet2 calls for a fair catch ",
                          " it's  mine on my 25 yard line", " it's first down and 10yards to go"]
    assert sounds_played(rig) == ["foot14", "foot7", "foot12", "foot11"]
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line) == (2, 1, 25)
    assert rig.engine.outcomes[-1].kind == O.PUNT


def test_a_punt_into_the_end_zone_is_a_touch_back_at_the_20(tmp_path):
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=1, yard_line=40, offense_play=7)
    d = punt_draws(34, Draws().rnd(3, 2))                            # 59 yards: high booming, out of bounds
    run_steps(rig, rig.engine.snap, d)
    assert texts(rig)[-6:] == [" it's a.  high booming kick", " it travels 59yards in the air",
                               " the ball hits and bounces out of bounds ", " IT IS A TOUCH BACK",
                               " it's  mine on my 20 yard line", " it's first down and 10yards to go"]


def test_a_punt_downed_by_a_receiver_of_the_kicking_side(tmp_path):
    rig = engine_rig(tmp_path, wisoff=2, defense=1, half=1, yard_line=30, offense_play=7)
    d = punt_draws(0, Draws().rnd(3, 3).rnd(6, 4))                   # 25 yards: a pooch kick
    run_steps(rig, rig.engine.snap, d)
    assert texts(rig)[6:10] == [" He gets the kick off ", " it's a.  pooch kick", " it travels 25yards in the air",
                                " the ball is downed by ORec4 "]
    assert rig.said[2][1] == OPPONENT_PUNTER


# ----- kick-offs -----

def kickoff_draws(returner=1, deep=3):
    return Draws().rnd(2, returner).rnd(7, deep).rady().rady()


def test_the_player_returns_a_kick_off_the_marks_the_tacklers_and_the_first_down_q19(tmp_path):
    rig = engine_rig(tmp_path, answers=[ENTER], wisoff=1, defense=2, half=2, yard_line=40)
    d = kickoff_draws(1, 3)
    d.rnd(5, 2).rnd(8, 1).below(30, 13)                              # a phrase, range 30, 25 yards
    d.rady().rady().rady().rady().rady().rady()                      # rady, then the 5, 10, 15, 20, 25 each with rady
    d.rnd(17, 7).rnd(17, 7).rnd(17, 3)                               # the second tackler drawn again (equal)
    d.rnd(4, 1)
    assert run_steps(rig, rig.engine.kick_off, d, until=AFTER_KICK) == "next_play"
    assert texts(rig) == [
        " Ret1 and Ret2 are back deep to receive the kick off ", "OKick1  is ready to kick off ",
        " The kick off is up and is headed for the end zone", "Ret1 catches the ball 3 yards deep in the end zone ",
        " Kim do you wish for Ret1 to run the ball out ", " yes ",
        " He is running left he cuts right he cuts back to the left", "Ret1 is at the 5", " the 10", " the 15",
        " the 20", " 25", " He is tackled by ODef7  and ODef3 ", " There is a gain of 25 yards on the play",
        " it's your ball on your 25yard line", " it's first down and 10yards to go"]
    assert sounds_played(rig) == ["foot11", "foot7", "foot14", "foot12", "foot5"]
    s = rig.engine.s
    assert (s.opening_receiver, s.first_kickoff, s.stats[1].first_downs, s.return_flag) == (1, False, 1, False)
    assert rig.engine.noise_net == 0


def test_the_run_out_question_keys_q17_and_the_touch_back(tmp_path):
    rig = engine_rig(tmp_path, answers=[F1, UP, "y", "x", ENTER], wisoff=1, defense=2, half=2)
    d = kickoff_draws(2, 1)
    assert run_steps(rig, rig.engine.kick_off, d, until=AFTER_KICK) == "next_play"
    prompt = " Kim do you wish for Ret2 to run the ball out "
    assert texts(rig)[3:] == ["Ret2 catches the ball 1 yard deep in the end zone ", prompt, " yes ", prompt, " yes ",
                              " no ", "y", " yes ", "x", " no ",
                              " he downs the ball in the end zone for a touch back", " It's  your ball on your 20yard line",
                              " it's first down and 10yards to go"]
    assert rig.engine.noise_net == 0                                 # the play noise loops under this question


def test_the_computer_takes_the_touch_back_1_time_in_2(tmp_path):
    rig = engine_rig(tmp_path, wisoff=2, defense=1, half=1)
    d = kickoff_draws(1, 7).rnd(2, 2)
    run_steps(rig, rig.engine.kick_off, d, until=AFTER_KICK)
    assert texts(rig)[3:] == ["ORet1 catches the ball 7 yards deep in the end zone ",
                              " he downs the ball in the end zone for a touch back", " It's  my ball on my 20yard line",
                              " it's first down and 10yards to go"]


def test_a_long_return_for_a_touchdown_counts_down_from_100_and_leaves_the_return_flag_set(tmp_path):
    rig = engine_rig(tmp_path, wisoff=2, defense=1, half=1)
    d = kickoff_draws(1, 7).rnd(2, 1)
    d.rnd(5, 1).rnd(8, 6).below(90, 89)                              # range 90: 101 yards
    d.rady().rady()
    for _ in range(9):                                               # the 10 to 45 and " he is still running"
        d.rady()
    d.rnd(17, 1)                                                     # one tackler (51 or more)
    d.rady()                                                         # " he is at the "
    d.rady().rady().rady().rady().rady()                             # 5 to 1
    d.celebration(8).rady()                                          # the computer's extra point follows
    run_steps(rig, rig.engine.kick_off, d, until=("extra_point",))
    spoken = texts(rig)
    assert spoken[spoken.index(" he is still running there is one man to beat"):] == [
        " he is still running there is one man to beat", " he is at the ", " 50", " 40", " 30", " 20", " 10", " 5",
        " 4", " 3", " 2", " 1", " TOUCH DOWN"]
    assert rig.engine.s.return_flag is True                          # the next pause after a play is skipped (L30c)


# ----- the extra point and the two-point try -----

def test_the_computers_extra_point_never_fails_q21(tmp_path):
    rig = engine_rig(tmp_path, answers=[ENTER], wisoff=2, defense=1, half=1)
    d = Draws().rady()
    quiet_kicksnap(d)
    d.rady().rady().rady()
    run_steps(rig, rig.engine.extra_point, d)
    assert texts(rig)[:9] == [" OKick1 is in for the extra point attempt ", " OKick2 will hold ", " hut 1 ", " hut",
                              " hike! ", " the snap is good ", " the hold is good", " the kick is up and it ",
                              " is good for the extra point "]
    assert sounds_played(rig) == ["foot7", "foot12", "foot11"]
    assert rig.engine.s.score(2) == 1


def test_the_extra_point_choice_resets_to_the_kick_after_f3_q18_and_takes_the_two_point_try(tmp_path):
    rig = engine_rig(tmp_path, answers=[DOWN, F3, DOWN, ENTER], wisoff=1, defense=2, half=1, yard_line=0)
    log = []
    rig.game.log_sink = log.append
    reached = run_steps(rig, rig.engine.extra_point_choice, Draws(), until=("offense_menu",))
    assert reached == "offense_menu"
    assert texts(rig) == [" Kim select ", " kick for extra point ", " try for two point conversion ", " The score is ",
                          " tied 0 all", " Kim select ", " kick for extra point ", " try for two point conversion "]
    s = rig.engine.s
    assert (s.two_point, s.yard_line, s.half) == (True, 2, 1)
    assert log == ["", " The score is  tied 0 all", ""]            # SayScore always logs; then the try's blank line


def two_point_rig(tmp_path, answers, yards_draw, extra=()):
    rig = engine_rig(tmp_path, answers=answers, wisoff=1, defense=2, half=1, yard_line=2, two_point=True,
                     down=2, to_go=7)
    return rig


def test_a_two_point_try_from_the_2_that_scores(tmp_path):
    rig = two_point_rig(tmp_path, [UP, DOWN, DOWN, ENTER, ENTER], None)
    d = Draws().rnd(6, 1)                                            # the computer's defense: Goal Line
    d.rnd(4, 1).rnd(10, 1).rady().rnd(7, 1).rnd(5, 3).below(4, 0).rady()
    d.rnd(6, 1).rnd(17, 1).rnd(17, 2).rnd(13, 1).rady()
    d.below(4, 1).rnd(9, 1).below(4, 0).rnd(50, 1).below(6, 5)       # End Run vs Goal Line: +2 (-3 + 5)
    d.rady().rady().rady()                                           # " he is at the ", " 2", " 1"
    d.rady()                                                         # after the score
    reached = run_steps(rig, rig.engine.offense_menu, d, until=AFTER_TRY)
    assert reached == "kick_off"
    spoken = texts(rig)
    assert spoken[:5] == [" Kim select the play for your off fence ", " 1. Line Plunge ", " 5. Long Pass ",
                          " 1. Line Plunge ", " 2. End Run "]                # items 1 to 5 wrap during the try
    assert spoken[spoken.index(" he is at the "):] == [" he is at the ", " 2", " 1", " the two point conversion is good ",
                                                       " The score is ", "Bengals.  2. Jets.  0", " "]
    assert rig.engine.s.two_point is False and rig.engine.s.score(1) == 2


def test_a_failed_two_point_try_is_not_announced_q22(tmp_path):
    rig = two_point_rig(tmp_path, [ENTER, ENTER], None)
    d = Draws().rnd(6, 1)
    d.rnd(4, 1).rnd(10, 1).rady().rnd(7, 1).rnd(5, 3).below(4, 0).rady()
    d.rnd(6, 1).rnd(17, 1).rnd(17, 2).rnd(13, 1).rady()
    d.below(4, 1).rnd(9, 1).rnd(50, 1).below(5, 3)                   # Line Plunge vs Goal Line: 0 yards
    d.rady()
    run_steps(rig, rig.engine.offense_menu, d, until=AFTER_TRY)
    spoken = texts(rig)
    assert spoken[spoken.index(" and there is a big pile up "):] == [" and there is a big pile up ", " The score is ",
                                                                     " tied 0 all", " "]


def test_a_turnover_on_a_two_point_try_ends_the_try_without_points_q23(tmp_path):
    rig = two_point_rig(tmp_path, [ENTER, ENTER], None)
    d = Draws().rnd(6, 1)
    d.rnd(4, 1).rnd(10, 1).rady().rnd(7, 1).rnd(5, 3).below(4, 0).rady()
    d.rnd(6, 1).rnd(17, 1).rnd(17, 2).rnd(13, 1).rady()
    d.below(4, 1).rnd(9, 1).rnd(50, 13)                              # a fumble: no spot is drawn
    d.rady()
    assert run_steps(rig, rig.engine.offense_menu, d, until=AFTER_TRY) == "kick_off"
    spoken = texts(rig)
    assert spoken[spoken.index(" there is a fumble on the play "):] == [" there is a fumble on the play ",
                                                                        " The score is ", " tied 0 all", " "]
    s = rig.engine.s
    assert (s.two_point, s.wisoff, s.defense, s.fumble_flag) == (False, 2, 1, False)    # the opponent receives


def test_a_return_flag_left_by_a_touchdown_return_skips_the_pause_of_the_next_play_in_the_field(tmp_path):
    """L30c is reset only where a play ends in the field of play (0x45073e), so after a kick-off returned for a
    touchdown the next such play has no pause of |yards| / 25 before its tackle (kept: the exact algorithm)."""
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, return_flag=True,
                     offense_play=1, defense_play=1, result_kind=O.RUN)
    rig.game.pause_log = []
    rig.engine.s.yards = 1
    run_steps(rig, rig.engine.end_of_play, Draws().rnd(4, 1))
    assert 0x4507b8 not in [site for site, _ in rig.game.pause_log]
    assert rig.engine.s.return_flag is False
