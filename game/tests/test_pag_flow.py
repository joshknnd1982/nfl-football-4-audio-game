"""The start of a game, the coin toss, the play menus and the computer's choice (GAME_SPEC 4.14, 4.15, 4.18, 5.6, 5.7). This is inspired by Jim Kitchen.

Strict draws written by hand from the lifted pag (0x43a87e to 0x43cc63 the start and the toss, 0x43dd89 to 0x43f04c the
menus, 0x43e5be and 0x43f04c to 0x43fd00 the computer's choice, 0x453cbe the last play of a period, 0x45ffe2 conceding,
0x45f5f9 Save Game).
"""
import pytest

from nfl4.game.gamestate import SavedGame, SideStats
from nfl4.audio.output import SLOT_CROWD1
from nfl4.speech.roles import ANNOUNCER
from pagrig import Draws, engine_rig, make_rig, play, run_steps, sounds_played, texts

ENTER, ESCAPE, TAB, UP, DOWN, F1, F2, F3, F4 = 13, 27, 9, 38, 40, 112, 113, 114, 115


# ----- the start (0x43a87e) -----

def setup_draws(d: Draws) -> Draws:
    """pag's set-up GoSub: 33 + 33 surnames (all different slots), the plays of five periods, M2W, M4W, M5W."""
    for slot in range(1, 67):
        d.rnd(1708, slot * 20)
    for _ in range(5):
        d.below(8, 3)                                                # 33 plays per period
    return d.below(3, 0).below(3, 1).below(3, 2)                     # M2W 5, M4W 6, M5W 7


def test_the_start_draws_the_set_up_then_the_player_calls_the_toss_wins_and_receives(tmp_path):
    rig = make_rig(tmp_path, answers=[ENTER, ENTER], vtrnt=2)
    d = setup_draws(Draws()).rnd(2, 1)                               # the coin comes up heads
    rig.rnd.source = __import__("randsources").ScriptedRandom(d.values, strict=True)
    rig.rnd.trace = []
    from nfl4.game.pag import PlayEngine
    engine = PlayEngine(rig.game, quarterback_names=lambda s: ("Starr", "Unitas"))
    step = engine.start()
    assert step.__name__ == "coin_toss"
    step = step()
    assert step.__name__ == "kick_off" and rig.rnd.trace == d.sizes
    assert texts(rig) == [" Kim Which do you call for the coin toss ", " heads ", " here is the coin toss ",
                          " the coin comes up heads ", " Kim which do you wish to do ", " receive "]
    s = engine.s
    assert (s.wisoff, s.defense, s.half, s.plays, s.teams) == (1, 2, 2, [33] * 5, {1: "Bengals", 2: "Jets"})
    assert rig.game.quarter_clock.warning == {2: 5, 4: 6, 5: 7}
    crowd = [e for e in rig.slot_log if e.slot == SLOT_CROWD1 and e.action == "volume"]
    assert crowd[-1].volume == -100
    assert sounds_played(rig) == ["foot0"]
    assert len(s.player_names) == 58 and s.quarterbacks == {1: "Starr", 2: "Unitas"}


@pytest.mark.parametrize("call, coin, player_wins", [(1, 1, False), (1, 2, True), (2, 2, False), (2, 1, True)])
def test_the_computer_calls_when_the_player_is_at_home(tmp_path, call, coin, player_wins):
    rig = engine_rig(tmp_path, answers=[ENTER])
    rig.game.season.vtrnt = 1
    d = Draws().rnd(2, call).rnd(2, coin)
    reached = run_steps(rig, rig.engine.coin_toss, d)
    words = {1: "heads ", 2: "tails "}
    assert texts(rig)[:3] == [" the Jets call " + words[call], " here is the coin toss ", " the coin comes up " + words[coin]]
    if player_wins:
        assert texts(rig)[3:] == [" Kim which do you wish to do ", " receive "] and rig.engine.s.wisoff == 1
    else:
        assert texts(rig)[3:] == [" the Jets choose to receive "] and rig.engine.s.wisoff == 2
    assert reached == "kick_off"


def test_the_toss_keys_h_t_arrows_f1_and_any_other_key_q_start_again(tmp_path):
    rig = engine_rig(tmp_path, answers=["t", UP, F1, "z", DOWN, ENTER, "k", ENTER])
    rig.game.season.vtrnt = 2                                        # the player is the visitor and calls
    d = Draws().rnd(2, 2)                                            # tails: the player called tails and wins
    run_steps(rig, rig.engine.coin_toss, d)
    prompt = " Kim Which do you call for the coin toss "
    assert texts(rig) == [prompt, " heads ", "t", " tails ", " heads ", prompt, " heads ", "z", prompt, " heads ",
                          " tails ", " here is the coin toss ", " the coin comes up tails ",
                          " Kim which do you wish to do ", " receive ", "k", " kick off "]
    assert rig.engine.s.wisoff == 2                                  # the player kicks off


# ----- the play menus (4.15) -----

def menu_rig(tmp_path, answers, **state):
    fields = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)
    fields.update(state)
    return engine_rig(tmp_path, answers=answers, **fields)


def test_up_and_down_wrap_digits_choose_the_current_item_and_enter_takes_it(tmp_path):
    rig = menu_rig(tmp_path, [UP, DOWN, DOWN, "4", 97, ENTER])       # 97: keypad 1 (the game's digits, Q32)
    run_steps(rig, rig.engine.offense_menu, Draws(), until=("offense_chosen",))
    assert texts(rig) == [" Kim select the play for your off fence ", " 1. Line Plunge ", " 8. Save Game ",
                          " 1. Line Plunge ", " 2. End Run ", " 4. Short Pass ", " 1. Line Plunge "]
    assert rig.engine.s.offense_play == 1


def test_f1_speaks_position_and_down_f2_replays_f3_score_f4_clock_each_then_the_prompt(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, F1, F2, F3, F4, ENTER], yard_line=50, half=1, to_go=7, down=2)
    rig.game.replay[:] = [" a replayed line "]
    d = Draws().below(30, 0)                                         # sgc's seconds jitter (F4)
    run_steps(rig, rig.engine.offense_menu, d, until=("offense_chosen",))
    prompt = " Kim select the play for your off fence "
    spoken = texts(rig)
    assert spoken[:6] == [prompt, " 1. Line Plunge ", " 2. End Run ", " its your ball on the 50 yard line",
                          " its second down and 7yards to go", prompt]
    assert spoken[6:10] == [" 2. End Run ", " here's the instant rea play ", " a replayed line ", prompt]
    assert spoken[11:13] == [" The score is ", " tied 0 all"]
    assert spoken[-3].endswith(" remaining in the first quarter. ") and spoken[-2:] == [prompt, " 2. End Run "]
    assert rig.engine.s.offense_play == 2                            # the current item was kept


def test_any_other_key_is_echoed_and_the_menu_starts_again_at_item_1(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, "x", "9", ENTER])
    run_steps(rig, rig.engine.offense_menu, Draws(), until=("offense_chosen",))
    prompt = " Kim select the play for your off fence "
    assert texts(rig) == [prompt, " 1. Line Plunge ", " 2. End Run ", "x", prompt, " 1. Line Plunge ", "9", prompt,
                          " 1. Line Plunge "]


def test_the_defense_menu_has_seven_items_and_wraps(tmp_path):
    rig = menu_rig(tmp_path, [UP, "6", ENTER], wisoff=2, defense=1)
    run_steps(rig, rig.engine.play_menu(), Draws(), until=("defense_chosen",))
    assert texts(rig) == [" Kim select the play for your dee fence ", " 1. Goal Line ", " 7. Save Game ",
                          " 6. Long Pass "]
    assert rig.engine.s.defense_play == 6


# ----- the computer's choice (5.7) -----

def chosen(rig, d):
    step = None
    source = __import__("randsources").ScriptedRandom(d.values, strict=True)
    rig.rnd.source, rig.rnd.trace = source, []
    step = rig.engine.defense_chosen()
    assert step.__name__ == "snap" and rig.rnd.trace == d.sizes and source.left == 0
    return rig.engine.s.offense_play


@pytest.mark.parametrize("k, play", [(0, 1), (1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (7, 4), (8, 5)])
def test_the_computers_play_is_int_of_x_over_2_for_x_2_to_10(tmp_path, k, play):
    rig = menu_rig(tmp_path, [], wisoff=2, defense=1)
    assert chosen(rig, Draws().below(9, k)) == play


FOURTH = dict(wisoff=2, defense=1, down=4)


@pytest.mark.parametrize("state, extra, play", [
    (dict(quarter=1, half=1, yard_line=30, to_go=5), [], 7),                     # own half inside its 40: punt
    (dict(quarter=1, half=2, yard_line=30, to_go=3), [], 6),                     # more than 2 to go: field goal
    (dict(quarter=1, half=2, yard_line=3, to_go=1, scores=(7, 0)), [("rnd", 4, 2)], 2),   # the player leads by 7
    (dict(quarter=3, half=2, yard_line=3, to_go=1), [("rnd", 9, 7), ("rnd", 4, 1)], 1),   # 1 in 9: go
    (dict(quarter=3, half=2, yard_line=3, to_go=1), [("rnd", 9, 1)], 6),
    (dict(quarter=2, half=1, yard_line=45, to_go=5), [("below", 10, 3)], 7),     # Q15: always the kick
    (dict(quarter=2, half=2, yard_line=30, to_go=5, scores=(21, 0)), [("rnd", 4, 4)], 4),   # 15 or more apart
    (dict(quarter=2, half=2, yard_line=30, to_go=5, counter=27), [("rnd", 4, 3)], 3),       # under 7 plays left
    (dict(quarter=2, half=2, yard_line=30, to_go=8), [], 6),
    (dict(quarter=4, half=2, yard_line=20, to_go=5), [], 6),                     # below 30, the player not 4 ahead
    (dict(quarter=4, half=2, yard_line=35, to_go=5, counter=21, scores=(5, 0)), [("rnd", 4, 1)], 1),
    (dict(quarter=5, half=1, yard_line=30, to_go=3), [], 7),                     # overtime
    (dict(quarter=5, half=2, yard_line=30, to_go=1), [("rnd", 9, 2)], 6),
])
def test_the_fourth_down_rules(tmp_path, state, extra, play):
    fields = dict(FOURTH)
    scores = state.pop("scores", (0, 0))
    fields.update(state)
    rig = menu_rig(tmp_path, [], **fields)
    rig.engine.s.stats[1].score, rig.engine.s.stats[2].score = scores
    d = Draws().below(9, 2)
    for kind, n, k in extra:
        getattr(d, kind)(n, k)
    assert chosen(rig, d) == play


@pytest.mark.parametrize("quarter, half, scores, play", [(2, 2, (0, 0), 6), (2, 1, (0, 0), 2), (1, 2, (0, 0), 2),
                                                         (4, 2, (3, 0), 6), (4, 2, (4, 0), 2), (5, 2, (0, 0), 6)])
def test_the_last_play_of_a_period(tmp_path, quarter, half, scores, play):
    rig = menu_rig(tmp_path, [], wisoff=2, defense=1, quarter=quarter, half=half, down=1, counter=32)
    rig.engine.s.stats[1].score, rig.engine.s.stats[2].score = scores
    assert chosen(rig, Draws().below(9, 2)) == play                  # x = 4: End Run when the normal rules apply


def test_a_repeated_play_is_matched_half_the_time_the_second_time_and_always_after(tmp_path):
    rig = menu_rig(tmp_path, [])
    engine = rig.engine
    engine.s.offense_play = 5
    script = Draws().rnd(6, 1).rnd(6, 2).rnd(2, 1).rnd(6, 3).rnd(6, 4)     # no coin flip from the third time on
    source = __import__("randsources").ScriptedRandom(script.values, strict=True)
    rig.rnd.source, rig.rnd.trace = source, []
    defenses = []
    for _ in range(4):
        engine.offense_chosen()
        defenses.append(engine.s.defense_play)
    assert defenses == [1, 2, 6, 6] and rig.rnd.trace == script.sizes
    engine.s.repeats = 0                                            # the second time with the flip that matches
    rig.rnd.source = __import__("randsources").ScriptedRandom(Draws().rnd(6, 1).rnd(2, 2).values, strict=True)
    engine.offense_chosen()
    assert engine.s.defense_play == 6 and engine.s.repeats == 1
    engine.s.offense_play = 6                                       # a field goal has no matching defense
    engine.s.previous_play = 6
    engine.s.repeats = 5
    rig.rnd.source = __import__("randsources").ScriptedRandom(Draws().rnd(6, 2).values, strict=True)
    engine.offense_chosen()
    assert engine.s.defense_play == 2


# ----- quit and concede, Save Game (4.18) -----

def test_escape_bleeps_six_times_and_tab_then_enter_concedes_the_game_as_a_loss(tmp_path):
    rig = menu_rig(tmp_path, [ESCAPE, TAB, ENTER])
    rig.engine.s.stats[1].score = 7
    reached = run_steps(rig, rig.engine.offense_menu, Draws(), until=("never",))
    assert reached is None
    assert texts(rig)[2:] == [" Do you wish to quit and concede this game? no ", " yes "]
    assert sounds_played(rig) == ["foot13"] * 6
    assert rig.engine.result.scores == (0, 1) and rig.engine.result.conceded
    assert [e.action for e in rig.slot_log if e.slot in (1, 2)] == ["stop", "stop"]


def test_n_goes_back_to_the_menu_and_another_key_bleeps_again(tmp_path):
    rig = menu_rig(tmp_path, [ESCAPE, "q", "n", ENTER])
    run_steps(rig, rig.engine.offense_menu, Draws(), until=("offense_chosen",))
    assert texts(rig) == [" Kim select the play for your off fence ", " 1. Line Plunge ",
                          " Do you wish to quit and concede this game? no ", "q",
                          " Do you wish to quit and concede this game? no ", "n",
                          " Kim select the play for your off fence ", " 1. Line Plunge "]
    assert sounds_played(rig) == ["foot13"] * 12


def test_a_conceded_game_when_behind_keeps_the_real_score(tmp_path):
    rig = menu_rig(tmp_path, [ESCAPE, "y"])
    rig.engine.s.stats[1].score, rig.engine.s.stats[2].score = 3, 10
    run_steps(rig, rig.engine.offense_menu, Draws(), until=("never",))
    assert rig.engine.result.scores == (3, 10)


def test_save_game_hands_the_original_values_over_and_says_game_saved(tmp_path):
    rig = menu_rig(tmp_path, [UP, ENTER], quarter=3, counter=12, yard_line=22)
    rig.engine.s.stats[2].score = 14
    rig.engine.s.opening_receiver = 2
    saved = []
    rig.engine.save_sink = saved.append
    assert run_steps(rig, rig.engine.offense_menu, Draws(), until=("never",)) is None
    assert texts(rig)[-1] == " Game Saved " and rig.engine.result.saved
    record = saved[0]
    assert (record.wisoff, record.quarter, record.counter, record.yard_line, record.opening_receiver) == (1, 3, 12, 22, 2)
    assert record.stats[2].score == 14 and record.opponent_quarterback == "Unitas"
    assert not [e for e in rig.slot_log if e.action == "stop" and e.slot in (1, 2)]    # the crowds go on (Q33)


def test_a_loaded_game_starts_at_the_play_menu_of_the_side_with_the_ball(tmp_path):
    rig = make_rig(tmp_path, answers=["7", ENTER])
    stats = {1: SideStats(score=10), 2: SideStats(score=3, interception_count=9)}
    saved = SavedGame(2, 1, 1, 3, 12, [31, 32, 33, 34, 35], 100, stats, 40, 2, 6, "Namath", None)
    result = play(rig, saved=saved, quarterback_names=lambda s: ("Starr", s.quarterbacks[2]))
    assert result.saved
    spoken = texts(rig)
    assert spoken[0] == " getting saved game "
    assert spoken[1:4] == [" Kim select the play for your dee fence ", " 1. Goal Line ", " 7. Save Game "]
