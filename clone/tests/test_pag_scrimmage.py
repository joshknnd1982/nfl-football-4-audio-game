"""Plays from scrimmage, each path with strict draws written by hand from the lifted pag (GAME_SPEC 5.8, 5.9, 5.11). This is inspired by Jim Kitchen.

Every test starts the engine at the snap (0x43fd12) with both plays chosen, gives the draws in the order and with the
sizes of the lifted lines (Draws, tests/pagrig.py; a draw the test did not plan, an unused one or a size that differs
fails), and checks every spoken text, its speaker, the sounds, the pauses and the state after the play.
"""
import pytest

from nfl4.game import outcome as O
from nfl4.speech.roles import ANNOUNCER, OWN_QUARTERBACK
from pagrig import Draws, engine_rig, run_steps, sounds_played, texts

START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)


def quiet_snap_count(d: Draws) -> Draws:
    """0x43fe61 to 0x440cb2 with the fewest draws: " is up to the line ", the huddle broken, " hut 1 ", no " hut 2 ",
    no call, no extra hut."""
    return (d.rnd(4, 1).rnd(10, 1).rady().rnd(7, 1).rnd(5, 3).below(4, 0).rady())


def snap_draws(d: Draws, carrier=1, d1=1, d2=2, phrase=1) -> Draws:
    """L_440e54 (carrier, two defenders) and the snap phrase (0x441271), then its rady."""
    return d.rnd(6, carrier).rnd(17, d1).rnd(17, d2).rnd(13, phrase).rady()


def first_handoff(d: Draws, group=1, phrase=1) -> Draws:
    """The first hand-off of a game: group Int(Rnd * 4) (0 would be drawn again), phrase Int(Rnd * 9) + 1."""
    return d.below(4, group).rnd(9, phrase)


def first_dropback(d: Draws, group=1, phrase=1) -> Draws:
    return d.below(3, group).rnd(11, phrase)


def after(rig, first):
    """The spoken texts from the first one equal to `first` on."""
    spoken = texts(rig)
    return spoken[spoken.index(first):]


def snap(tmp_path, offense, defense, **state):
    fields = dict(START)
    fields.update(state)
    rig = engine_rig(tmp_path, answers=[13] * 3, offense_play=offense, defense_play=defense, **fields)
    rig.game.pause_log = []
    return rig


def test_a_line_plunge_with_the_full_snap_count_every_text_speaker_sound_and_pause(tmp_path):
    rig = snap(tmp_path, 1, 3)
    d = Draws()
    d.rnd(4, 2).rnd(10, 1).rady().rnd(7, 3).rady()                   # " is under center ", the huddle, hut 1, hut 2
    d.rnd(5, 1).rnd(10, 3).rnd(28, 17).rady().rnd(5, 3)              # one call: " Blue  17", no second call
    d.below(4, 1).rady().rnd(2, 1).rady()                            # one more " hut!", then rady before " Hike! "
    snap_draws(d, carrier=4, d1=5, d2=9, phrase=1)
    first_handoff(d, group=2, phrase=1)
    d.rnd(3, 2).rnd(50, 1).below(7, 5)                               # "on the left side", no fumble, 5 yards
    d.rnd(4, 1)                                                      # no banter (1 in 4 at 0x451119)
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert rig.said == [
        (" the Bengals break the huddle ", ANNOUNCER, 0), ("Starr is under center ", ANNOUNCER, 0),
        (" hut 1 ", OWN_QUARTERBACK, 0), (" hut 2 ", OWN_QUARTERBACK, 0), (" Blue  17", OWN_QUARTERBACK, 0),
        (" hut!", OWN_QUARTERBACK, 0), (" Hike! ", OWN_QUARTERBACK, 0),
        ("Starr takes the snap", ANNOUNCER, 0), (" He hands the ball off to Back4 ", ANNOUNCER, 0),
        ("Back4 runs through a hole on the left side", ANNOUNCER, 0), (" and is tackled by ODef5 ", ANNOUNCER, 0),
        (" There is a gain of 5 yards on the play", ANNOUNCER, 0),
        (" it's your ball on your 35yard line", ANNOUNCER, 0), (" it's second down and 5yards to go", ANNOUNCER, 0)]
    assert sounds_played(rig) == ["foot3", "foot14", "foot6"]
    assert [site for site, _ in rig.game.pause_log] == [0x44027e, 0x440344, 0x4404a6, 0x44076b, 0x440b16, 0x440cb2,
                                                        0x441b18, 0x4507b8]
    assert rig.game.pause_log[-1][1] == pytest.approx(5 / 25)
    s = rig.engine.s
    assert (s.yard_line, s.half, s.down, s.to_go) == (35, 2, 2, 5)
    assert (s.stats[1].running_plays, s.stats[1].running_yards) == (1, 5)
    assert [o.kind for o in rig.engine.outcomes] == [O.RUN]


def test_the_second_call_with_the_same_word_repeats_the_first_number(tmp_path):
    rig = snap(tmp_path, 1, 1)
    d = Draws().rnd(4, 1).rnd(10, 1).rady().rnd(7, 1)
    d.rnd(5, 1).rnd(10, 2).rnd(28, 5).rady()                         # " Right  5"
    d.rnd(5, 1).rnd(8, 2).rnd(28, 20)                                # the same word: the number is the first one
    d.below(4, 0).rady()
    snap_draws(d)
    first_handoff(d)
    d.rnd(50, 1).below(5, 4)                                         # Line Plunge vs Goal Line: no direction, +1
    d.rnd(4, 1)
    run_steps(rig, rig.engine.snap, d)
    assert texts(rig)[3:5] == [" Right  5", " Right  5"]
    assert texts(rig)[8:10] == ["Back1 runs straight up the middle ", " and there is a big pile up "]
    assert sounds_played(rig)[-1] == "foot4"


RUN_TEXTS = {
    (1, 1): ("Back1 runs straight up the middle ", " and there is a big pile up "),
    (1, 2): ("Back1 runs off tackle ", " and is brought down by ODef1 "),
    (1, 3): ("Back1 runs through a hole up the middle", " and is tackled by ODef1 "),
    (1, 4): ("Back1 avoids the blitz of ODef2", " AND IS CAUGHT BY ODef1 "),
    (1, 5): ("Back1 finds a hole up the middle and gets into the second airy", " before ODef1 and ODef2 can catch him"),
    (1, 6): ("Back1 runs through a hole up the middle and runs up field", " before ODef1 and ODef2 tackle him "),
    (2, 1): ("Back1 tries to run around the right side ", " ODef1 tackles him"),
    (2, 2): (None, " Back1 is tackled by ODef1 before he can get around the right side"),
    (2, 3): ("Back1 runs around the right side", " ODef1 tackles him at that point"),
    (2, 4): (" Back1 runs around the right side past ODef2", " ODef1 chases and brings him down"),
    (2, 5): (" Back1 finds his way around the right side", " before ODef1 trips him up"),
    (2, 6): (" Back1 gets around the right side and heads up field, ", " ODef1 and ODef2 chase him down"),
}


@pytest.mark.parametrize("pair", sorted(RUN_TEXTS))
def test_each_of_the_twelve_runs_speaks_its_sentences_with_the_lowest_yards(tmp_path, pair):
    from nfl4.game.playtables import RUNS
    entry = RUNS[pair]
    rig = snap(tmp_path, *pair)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_handoff(d)
    if entry.direction == 3:
        d.rnd(3, 1)
    elif entry.direction == 4:
        d.below(4, 0)
    d.rnd(50, 1).below(entry.high - entry.low, 0)
    d.rnd(4, 1)
    run_steps(rig, rig.engine.snap, d)
    run, tackle = RUN_TEXTS[pair]
    spoken = texts(rig)
    after_handoff = spoken[spoken.index(" He hands the ball off to Back1 ") + 1:]
    assert after_handoff[:2] == ([run, tackle] if run is not None else [tackle, after_handoff[1]])
    assert sounds_played(rig)[-1] == {1: "foot4", 2: "foot5", 3: "foot6"}[entry.sound]
    assert rig.engine.s.yards == entry.low


def test_a_completed_pass_its_order_sounds_and_statistics(tmp_path):
    rig = snap(tmp_path, 4, 3)                                       # Short Pass vs Long Run: 5 to 14, 10 %, 70 %
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=2, phrase=2)
    first_dropback(d, group=1, phrase=5)
    d.raw(0.5).raw(0.3)                                              # no sack (50 > 10); complete (30 < 70)
    d.rnd(9, 4).rnd(67, 1)                                           # the throw; no interception (1 in 70 - 3)
    d.rnd(2, 1).rnd(9, 6)                                            # foot5; " makes a leaping catch "
    d.rnd(50, 1).below(10, 7)                                        # no fumble; 12 yards
    d.rnd(4, 1)
    run_steps(rig, rig.engine.snap, d)
    assert after(rig, "Starr has the ball") == [
        "Starr has the ball", " He looks for an open receiver", " Starr throws a perfect spiral",
        " and Rec2 makes a leaping catch ", " There is a gain of 12 yards on the play",
        " it's your ball on your 42yard line", " it's first down and 10yards to go"]
    assert sounds_played(rig)[-2:] == ["foot12", "foot5"]            # foot12, the catch (asynchronous), the tackle
    st = rig.engine.s.stats[1]
    assert (st.pass_attempts, st.completions, st.passing_yards, st.first_downs, st.interception_count) == (1, 1, 12, 1, 3)


def test_a_sack_skips_the_dropback_and_subtracts_from_the_passing_yards(tmp_path):
    rig = snap(tmp_path, 5, 4)                                       # Long Pass vs Blitz: 60 % sacks
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d, group=2, phrase=1)
    d.raw(0.59).rnd(6, 6).rnd(50, 1).below(12, 4)                     # sack; " smother "; -8 yards
    d.rnd(4, 1)
    run_steps(rig, rig.engine.snap, d)
    assert after(rig, "Starr takes the snap") == ["Starr takes the snap", " ODef1 and ODef2 smother Starr ",
                              " There is a loss of 8 yards on the play.", " it's your ball on your 22yard line",
                              " it's second down and 18yards to go"]
    assert sounds_played(rig)[-2:] == ["foot12", "foot5"]
    st = rig.engine.s.stats[1]
    assert (st.pass_attempts, st.sacked, st.passing_yards) == (1, 1, -8)


def test_the_sack_test_compares_a_single_as_the_original_does(tmp_path):
    """L4d0 = Rnd * 100 is stored as a Single (FSTP float 0x44a399): 5.0000001 is 5 in a Single, so a sack at 5 %."""
    rig = snap(tmp_path, 3, 1)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d)
    d.raw(0.050000001).rnd(6, 1).rnd(50, 1).below(12, 11)
    d.rnd(4, 1)
    run_steps(rig, rig.engine.snap, d)
    assert rig.engine.s.stats[1].sacked == 1 and 0.050000001 * 100 > 5


def test_an_interception_on_the_first_pass_and_the_spot_in_the_same_half(tmp_path):
    rig = snap(tmp_path, 3, 1)                                       # Screen vs Goal Line: 90 %
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_dropback(d)
    d.raw(0.5).raw(0.3).rnd(9, 1).rnd(87, 2)                         # 1 / (90 - 3): the interception
    d.rnd(2, 2).below(40, 10)                                        # " picks off the pass ", the spot 15
    run_steps(rig, rig.engine.snap, d)
    assert after(rig, " He steps back to pass") == [" He steps back to pass", " Starr puts the ball up", " and ODef1 picks off the pass ",
                              " the ball is now mine on your 15 yard line", " it's first down and 10yards to go"]
    assert sounds_played(rig)[-2:] == ["foot12", "foot6"]
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line, s.stats[1].intercepted, s.stats[1].interception_count) == (2, 2, 15, 1, 0)
    assert rig.engine.outcomes[-1].kind == O.INTERCEPTION


def test_an_incompletion_bats_the_ball_back_with_the_offenses_own_defender_q56(tmp_path):
    rig = snap(tmp_path, 4, 5)                                       # Short Pass vs Short Pass: 25 %, 70 %
    rig.game.pause_log = []
    d = quiet_snap_count(Draws())
    snap_draws(d, d1=3)
    first_dropback(d)
    d.raw(0.5).raw(0.8).rnd(9, 1).rnd(67, 1)                         # incomplete (80 >= 70)
    d.rnd(9, 6).below(4, 2)                                          # " bats it right back at "; pause (2 + 4) / 9
    d.rnd(4, 1)
    run_steps(rig, rig.engine.snap, d)
    assert after(rig, " Def3 bats it right back at Starr ") == [" Def3 bats it right back at Starr ", " There is no gain on the play",
                              " it's your ball on your 30yard line", " it's second down and 10yards to go"]
    assert sounds_played(rig)[-2:] == ["foot12", "foot11"]
    assert (0x44d024, pytest.approx(6 / 9)) in [(site, s) for site, s in rig.game.pause_log]
    assert rig.engine.s.stats[1].completions == 0 and rig.engine.s.stats[1].pass_attempts == 1


def test_a_fumbled_run_is_not_a_running_play_and_its_tackle_sentence_is_never_spoken_q60(tmp_path):
    rig = snap(tmp_path, 1, 2)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_handoff(d)
    d.rnd(50, 13).below(40, 0)                                       # the fumble; the spot 5
    run_steps(rig, rig.engine.snap, d)
    assert after(rig, "Back1 runs off tackle ") == ["Back1 runs off tackle ", " there is a fumble on the play ",
                              " the ball is now mine on your 5 yard line", " it's first down and goal to go"]
    st = rig.engine.s.stats[1]
    assert (st.running_plays, st.running_yards, st.fumbles_lost) == (0, 0, 1)
    assert sounds_played(rig)[-1] == "foot6"


def test_a_run_into_the_end_zone_counts_down_from_the_distance_at_the_snap(tmp_path):
    rig = snap(tmp_path, 1, 5, half=1, yard_line=3)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_handoff(d)
    d.rnd(3, 1).rnd(50, 1).below(7, 0)                               # 8 yards from the 3
    d.rady().rady().rady().rady()                                    # " he is at the ", then 3, 2, 1 each with rady
    d.celebration(8).rady()
    run_steps(rig, rig.engine.snap, d, until=("extra_point_choice",))
    spoken = texts(rig)
    assert spoken[spoken.index(" he is at the "):] == [" he is at the ", " 3", " 2", " 1", " TOUCH DOWN"]
    assert rig.engine.s.score(1) == 6
    assert sounds_played(rig)[-10:] == ["foot11"] + ["foot15"] * 8 + ["foot12"]


def test_a_pass_caught_in_the_end_zone_waits_yards_over_25_then_no_countdown(tmp_path):
    rig = snap(tmp_path, 5, 1, half=1, yard_line=10)
    rig.game.pause_log = []
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=3)
    first_dropback(d)
    d.raw(0.5).raw(0.1).rnd(9, 1).rnd(37, 1).rnd(2, 2).rnd(9, 1)     # complete (10 < 40)
    d.rnd(50, 1).below(35, 5)                                        # 20 yards from the 10
    d.rnd(3, 1).celebration(8).rady()
    run_steps(rig, rig.engine.snap, d, until=("extra_point_choice",))
    spoken = texts(rig)
    assert spoken[-2:] == [" Rec3 catches the pass in the end zone ", " TOUCH DOWN"]
    assert (0x44ed2d, pytest.approx(20 / 25)) in rig.game.pause_log


def test_a_catch_that_breaks_a_tackle_counts_down_from_ten(tmp_path):
    rig = snap(tmp_path, 5, 1, half=1, yard_line=10)
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=3)
    first_dropback(d)
    d.raw(0.5).raw(0.1).rnd(9, 1).rnd(37, 1).rnd(2, 2).rnd(9, 1).rnd(50, 1).below(35, 5)
    d.rnd(3, 2).rady()                                               # the catch sentence, then rady, " he is at the "
    d.rady().rady().rady().rady().rady()                             # " 10", then 5 to 1 each with rady
    d.celebration(8).rady()
    run_steps(rig, rig.engine.snap, d, until=("extra_point_choice",))
    spoken = texts(rig)
    assert spoken[spoken.index(" Rec3 catches the pass, breaks a tackle and heads up field "):] == [
        " Rec3 catches the pass, breaks a tackle and heads up field ", " he is at the ", " 10", " 5", " 4", " 3",
        " 2", " 1", " TOUCH DOWN"]


def test_a_safety_gives_two_points_to_the_defense_and_the_conceding_side_kicks(tmp_path):
    rig = snap(tmp_path, 2, 2, yard_line=3)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_handoff(d)
    d.below(4, 0).rnd(50, 1).below(5, 2)                             # -3 yards from the own 3
    d.rady()                                                         # after the score (0x4443cb)
    assert run_steps(rig, rig.engine.snap, d) == "kick_off"
    spoken = texts(rig)
    assert spoken[spoken.index(" Back1 is tackled by ODef1 before he can get around the right side"):] == [
        " Back1 is tackled by ODef1 before he can get around the right side", " in the end zone for a safety",
        " The score is ", "Jets.  2. Bengals.  0", " "]
    s = rig.engine.s
    assert (s.score(2), s.wisoff, s.defense, s.half) == (2, 2, 1, 1)   # the scorer (the opponent) receives
    assert sounds_played(rig)[-1] == "foot5"


def test_a_failed_fourth_down_turns_the_ball_over_on_downs(tmp_path):
    rig = snap(tmp_path, 1, 1, down=4, to_go=5)
    d = quiet_snap_count(Draws())
    snap_draws(d)
    first_handoff(d)
    d.rnd(50, 1).below(5, 5 - 3)                                     # +2 yards (Goal Line: -3 to 1, so 2 - 3 = -1)
    run_steps(rig, rig.engine.snap, d)
    spoken = texts(rig)
    assert spoken[-3:] == [" There is a loss of 1 yard on the play.",
                           " ball turned over on downs the ball is now  mine on your 29 yard line",
                           " it's first down and 10yards to go"]
    assert rig.engine.s.wisoff == 2 and rig.engine.s.down == 1
