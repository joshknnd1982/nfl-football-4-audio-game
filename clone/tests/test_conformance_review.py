"""S8.1, second round: the gaps that the independent review of the conformance map found. This is inspired by Jim Kitchen.

Each test names the requirement of GAME_SPEC it closes (Q9, Q15, Q18, Q22, Q25, Q28, Q37, Q38, Q39, Q60, Q61, the length of the
phrase histories in 17.2 and 5.8/5.9, GetSexOf in 9.2). The review (an Opus 5.5 subagent that had not seen the work) read the
cited tests of every row and listed the rows whose tests named the requirement but did not pin it; Q5 and Q6, where the clone
did not follow D-025 (a) and (b), are fixed in game/program.py and game/gameclock.py with their tests in test_program_menu.py
and test_gameclock.py.
"""
import random

import pytest

from gamerig import Rig
from nfl4.data.files import playernames as pn
from nfl4.game import outcome as O
from nfl4.game.gamestate import GameState, SavedGame, SideStats, own_half
from nfl4.game.pag import PlayEngine
from nfl4.speech.roles import ANNOUNCER, OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER, OWN_QUARTERBACK
from pagrig import Draws, QUARTERBACKS, engine_rig, make_rig, run_steps, texts
from test_banter import banter_rig
from test_files_playernames import a_roster
from test_pag_breaks import break_rig
from test_pag_flow import chosen, menu_rig
from test_pag_kicks import two_point_rig
from randsources import below_value, value_for

ENTER, ESCAPE, DOWN, F1, F2 = 13, 27, 40, 112, 113


# ----- Q25: the overtime kick-off sets the half whatever it was -----

@pytest.mark.parametrize("wisoff", [1, 2])
@pytest.mark.parametrize("half", [1, 2])
def test_the_overtime_kick_off_sets_the_half_of_the_side_with_the_ball_whatever_it_was_q25(tmp_path, wisoff, half):
    """The original leaves the half as it was, so a returned overtime kick-off can be an automatic touchdown; the clone sets it as at
    every kick-off, the receiving side being the side that had the ball at the end of regulation (kept)."""
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=4, counter=32, wisoff=wisoff, defense=3 - wisoff, half=half)
    assert run_steps(rig, rig.engine.next_play, Draws(), until=("kick_off",)) == "kick_off"
    s = rig.engine.s
    assert (s.quarter, s.overtime, s.wisoff, s.defense) == (5, 1, wisoff, 3 - wisoff)
    assert s.half == own_half(wisoff)


# ----- Q15: the computer always kicks on fourth down in its own half in quarters 2 and 4 -----

@pytest.mark.parametrize("quarter", [2, 4])
@pytest.mark.parametrize("k", range(10))
def test_the_computer_always_kicks_on_fourth_down_in_its_own_half_in_quarters_2_and_4_q15(tmp_path, quarter, k):
    """Its random go-for-it test compares with a variable that is never assigned: whatever the draw (0 to 9) the answer is the punt."""
    rig = menu_rig(tmp_path, [], wisoff=2, defense=1, down=4, quarter=quarter, half=1, yard_line=45, to_go=5)
    assert chosen(rig, Draws().below(9, 2).below(10, k)) == 7


@pytest.mark.parametrize("quarter", [2, 4])
def test_more_than_20_to_go_in_quarters_2_and_4_keeps_the_drawn_play_and_draws_nothing_more_q15(tmp_path, quarter):
    rig = menu_rig(tmp_path, [], wisoff=2, defense=1, down=4, quarter=quarter, half=1, yard_line=45, to_go=21)
    assert chosen(rig, Draws().below(9, 2)) == 7                    # the punt of the fourth-down rule stays, and no second draw is made


# ----- Q18: every key but Enter, Up and Down gives the extra point prompt again with the kick -----

@pytest.mark.parametrize("key", [F1, F2, ESCAPE, "a"])
def test_the_extra_point_prompt_starts_again_at_the_kick_after_any_other_key_q18(tmp_path, key):
    rig = engine_rig(tmp_path, answers=[DOWN, key, DOWN, ENTER], wisoff=1, defense=2, half=1, yard_line=0)
    assert run_steps(rig, rig.engine.extra_point_choice, Draws(), until=("offense_menu",)) == "offense_menu"
    spoken = texts(rig)
    kick, two = " kick for extra point ", " try for two point conversion "
    assert spoken[:3] == [" Kim select ", kick, two]                  # the first pass: Down gave the try
    again = len(spoken) - 1 - spoken[::-1].index(" Kim select ")
    assert spoken[again:] == [" Kim select ", kick, two]              # after the key: the kick first, Down again gives the try
    assert rig.engine.s.two_point is True and rig.engine.s.yard_line == 2


# ----- Q22: during a two-point try F1 speaks the down and distance of the touchdown play -----

def test_f1_during_the_two_point_try_speaks_the_down_and_distance_of_the_touchdown_play_q22(tmp_path):
    rig = two_point_rig(tmp_path, [F1, ENTER], None)
    run_steps(rig, rig.engine.offense_menu, Draws(), until=("offense_chosen",))
    spoken = texts(rig)
    assert " its second down and goal to go" in spoken               # the touchdown play's down (two_point_rig: down 2) at the 2
    assert any(t.startswith(" its your ball on") for t in spoken)


# ----- Q9: a typed quarterback name loses its leading spaces when footplay.txt is read back -----

def test_a_typed_quarterback_name_loses_its_leading_spaces_when_the_file_is_read_back_q9():
    text = pn.with_quarterback(pn.format_roster(a_roster(quarterback="")), "   Starr")
    parsed = pn.parse(text)
    assert parsed.sound and parsed.roster.quarterback == "Starr"


# ----- Q38: banter line 113 is one rate step faster, also after another voice spoke -----

def test_line_113_is_one_rate_step_faster_even_when_the_quarterback_spoke_last_q38(tmp_path):
    from nfl4.game.banter import speak_banter
    rig, state = banter_rig(tmp_path, [value_for(142, 113), value_for(58, 1), below_value(30, 0)])
    rig.game.wisoff, rig.game.qorp = 1, 1
    rig.game.say3(" Hut ")
    assert rig.said[-1][1] == OWN_QUARTERBACK
    speak_banter(rig.game, state)
    text, role, step = rig.said[-1]
    assert role == ANNOUNCER and step == 1                          # the original loses the +1 when the voice has to be loaded again


# ----- Q60: a fumbled pass keeps its attempt and its completion or sack -----

def test_a_fumbled_pass_keeps_its_attempt_and_its_completion_or_sack_q60(tmp_path):
    rig = engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)
    rig.keys.fast = True
    rig.sounds.sleep = lambda seconds: rig.clock.sleep(0.02)
    rig.rnd.source = random.Random(60)
    engine, s = rig.engine, rig.engine.s
    stats = s.stats[1]
    seen = {"sack": 0, "catch": 0}
    for _ in range(2500):
        s.wisoff, s.defense, s.half, s.yard_line, s.down, s.to_go = 1, 2, 2, 30, 1, 10
        s.offense_play, s.defense_play = 5, 6
        before = (stats.pass_attempts, stats.completions, stats.sacked, stats.fumbles_lost, stats.running_plays)
        step = engine.snap
        while step.__name__ not in ("next_play", "play_menu", "touchdown"):
            step = step()
        after = (stats.pass_attempts, stats.completions, stats.sacked, stats.fumbles_lost, stats.running_plays)
        if after[3] > before[3]:
            assert after[0] == before[0] + 1 and after[4] == before[4]       # the attempt stays, no running play is counted
            assert (after[1] - before[1]) + (after[2] - before[2]) == 1       # a completion or a sack, never both, never neither
            seen["sack" if after[2] > before[2] else "catch"] += 1
    assert min(seen.values()) > 0, seen


# ----- Q61: the kick-off's play noise loops under the run-out question -----

def test_the_play_noise_of_the_kick_off_still_loops_when_the_run_out_question_is_asked_and_the_touch_back_stops_it_q61(tmp_path):
    from test_pag_kicks import AFTER_KICK, kickoff_draws
    rig = engine_rig(tmp_path, answers=[DOWN, ENTER], wisoff=1, defense=2, half=2)
    running_at_waits = []
    real = rig.engine.getkey2

    def spy(net=True):
        running_at_waits.append((net, rig.sounds.play_noise_running()))
        return real(net=net)
    rig.engine.getkey2 = spy
    run_steps(rig, rig.engine.kick_off, kickoff_draws(2, 1), until=AFTER_KICK)
    assert running_at_waits[0] == (False, True)                       # the question: no safety net, the noise is looping
    assert not rig.sounds.play_noise_running()                        # the touch back's PlayTackle(8) stopped it
    assert rig.engine.noise_net == 0


# ----- the lengths of the phrase histories (5.8, 5.9, 17.2) -----

@pytest.mark.parametrize("field, size, count", [("snap_history", 6, 13), ("sack_history", 4, 6), ("throw_history", 4, 9),
                                                 ("incomplete_history", 6, 9), ("catch_history", 6, 9)])
def test_each_phrase_history_has_the_length_of_the_spec_and_no_phrase_comes_back_inside_it(field, size, count):
    from nfl4.game.rnd import GameRandom
    history = getattr(GameState(), field)
    assert len(history.values) == size
    rnd = GameRandom(random.Random(size * 100 + count))
    drawn = [history.draw(rnd, count, field) for _ in range(4000)]
    for index, value in enumerate(drawn):
        assert value not in drawn[max(0, index - size):index]
    assert any(drawn[index] == drawn[index - size - 1] for index in range(size + 1, len(drawn)))   # but one just outside it does


def test_the_hand_off_and_drop_back_histories_keep_the_last_16_values():
    state = GameState()
    assert len(state.handoff.history.values) == 16 and len(state.dropback.history.values) == 16
    assert (state.handoff.groups, state.handoff.per_group, state.dropback.groups, state.dropback.per_group) == (4, 9, 3, 11)


# ----- Q28, Q37, Q39: what a loaded game does not know -----

def test_a_loaded_game_restarts_the_interception_counts_the_histories_and_the_opponents_names_q28_q37_q39(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(28), vtrnt=2)
    stats = {1: SideStats(score=10, interception_count=9), 2: SideStats(score=3, interception_count=12)}
    saved = SavedGame(2, 1, 1, 3, 12, [31, 32, 33, 34, 35], 100, stats, 40, 2, 6, "Namath", None)
    engine = PlayEngine(rig.game, rig.game.rules.for_game(), saved=saved, quarterback_names=lambda s: QUARTERBACKS)
    step = engine.start()
    s = engine.s
    assert step.__name__ == "play_menu" and (s.quarter, s.counter, s.yard_line, s.down) == (3, 12, 40, 2)
    assert s.stats[1].interception_count == s.stats[2].interception_count == 0           # Q28: they restart
    assert s.overtime == 0                                                               # Q28: the overtime count restarts
    assert s.banter_used == [] and all(set(getattr(s, f).values) == {0} for f in
                                       ("snap_history", "sack_history", "throw_history", "incomplete_history", "catch_history"))
    assert set(s.handoff.history.values) == {0} and s.handoff.memory is None            # Q37: no history comes from the file
    assert len(s.rosters[2].names()) == 33 and not hasattr(saved, "rosters")            # Q39: the opponent's names are new
    assert 5 <= rig.game.quarter_clock.m2w <= 7 and 5 <= rig.game.quarter_clock.m4w <= 7 and 5 <= rig.game.quarter_clock.m5w <= 7   # Q28: drawn again


# ----- 9.2: GetSexOf -----

def test_get_sex_of_asks_the_voices_of_the_four_players_and_never_the_announcer_s9_2(tmp_path):
    rig = engine_rig(tmp_path)
    asked = []

    def role_gender(role):
        asked.append(role)
        if role == OPPONENT_QUARTERBACK:
            raise OSError("the voice cannot be asked")
        return "Female" if role == OPPONENT_PUNTER else "Male"
    rig.game.speech.role_gender = role_gender
    rig.engine.get_sex_of()
    assert asked == [OWN_QUARTERBACK, OPPONENT_QUARTERBACK, OWN_PUNTER, OPPONENT_PUNTER]
    assert rig.engine.s.he_she == {1: " He ", 2: " He ", 3: " He ", 4: " She "}      # an error counts as " He "


# ----- 5.8: the snap count of the opponent, and the huddle skipped one time in ten -----

def test_the_snap_count_of_the_opponent_is_in_its_quarterbacks_voice_and_one_huddle_in_ten_is_skipped_s5_8(tmp_path):
    from randsources import ScriptedRandom
    from test_pag_scrimmage import snap
    rig = snap(tmp_path, 1, 3, wisoff=2, half=1)
    rig.engine.s.defense = 1
    d = Draws().rnd(4, 1).rnd(10, 7).rady().rnd(7, 1).rnd(5, 3).below(4, 0).rady()       # no hut 2, no call, no extra hut
    source = ScriptedRandom(d.values, strict=True)
    rig.rnd.source, rig.rnd.trace = source, []
    rig.engine.snap_count()
    assert rig.rnd.trace == d.sizes and source.left == 0
    assert rig.said == [(" the Jets come to the line without a huddle ", ANNOUNCER, 0), ("Unitas is up to the line ", ANNOUNCER, 0),
                        (" hut 1 ", OPPONENT_QUARTERBACK, 0), (" Hike! ", OPPONENT_QUARTERBACK, 0)]
