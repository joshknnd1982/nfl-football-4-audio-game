"""The Super Bowl presentation, superbowl p_484860, called by pag after the player's Super Bowl game (GAME_SPEC 5.6 item 7;
Q27, audit finding A-07). This is inspired by Jim Kitchen.

Strict draws from the lifted code (0x484947 to 0x485a92): the winner sentence, 8 to 15 celebration sounds (Int(Rnd * 8) + 8, then
for each Int(Rnd * 10) + 15 and the pitch Int(Rnd * 40) - 20), foot25 when the player's team won, 8 to 15 more, getkey; F1 or F2
play it all again with new draws. gtp is 42 at the end (pag then sets 0).
"""
import random

from nfl4.audio.output import SLOT_ONESHOT
from pagrig import Draws, enter_policy, make_rig, play, sounds_played
from seasonrig import ENTER, F1, F2, run, season_rig, texts

WIN = " The Bengals have Won the super Bowl!  They beat the Jets by the score of 24, to 17. "
LOSS = " The Jets have Won the super Bowl!  They beat the Bengals by the score of 24, to 17. "


def presentation_rig(tmp_path, answers, scores):
    return season_rig(tmp_path, answers=answers, own=(1, 1), opponent=(2, 3), gtp=20, scores=scores)


def test_the_player_wins_the_sentence_a_run_foot25_and_a_second_run(tmp_path):
    rig = presentation_rig(tmp_path, [ENTER], (24, 17))
    draws = Draws().celebration(8).celebration(9)
    run(rig, lambda: rig.game.superbowl((24, 17)), draws)
    assert texts(rig) == [WIN]
    assert sounds_played(rig) == ["foot15"] * 8 + ["foot25"] + ["foot15"] * 9
    plays = [e for e in rig.slot_log if e.action == "play"]
    assert [e.volume for e in plays] == [-300] * 8 + [0] + [-300] * 9
    assert [e.freq for e in plays if e.sound_id == "snd_foot15"] == [44100 + 1600] * 17
    foot25 = plays[8]
    assert (foot25.slot, foot25.freq) == (SLOT_ONESHOT, 11025)
    assert plays[9].time - foot25.time > 11.4                       # foot25 is waited to its end (11.46 s)
    assert rig.game.season.gtp == 42 and rig.game.ptf == 1 and rig.game.replay == [WIN]
    assert rig.keys.waits == 1


def test_the_opponent_wins_the_sentence_names_it_first_and_there_is_one_run_and_no_foot25(tmp_path):
    rig = presentation_rig(tmp_path, [ENTER], (17, 24))
    run(rig, lambda: rig.game.superbowl((17, 24)), Draws().celebration(10))
    assert texts(rig) == [LOSS]
    assert sounds_played(rig) == ["foot15"] * 10
    assert rig.game.season.gtp == 42


def test_equal_scores_go_to_the_opponent_as_in_the_lifted_test(tmp_path):
    rig = presentation_rig(tmp_path, [ENTER], (17, 17))
    run(rig, lambda: rig.game.superbowl((17, 17)), Draws().celebration(8))
    assert texts(rig) == [" The Jets have Won the super Bowl!  They beat the Bengals by the score of 17, to 17. "]


def test_f1_and_f2_play_it_all_again_with_new_draws_and_the_list_is_emptied_each_time(tmp_path):
    rig = presentation_rig(tmp_path, [F1, F2, ENTER], (24, 17))
    draws = Draws()
    for first, second in ((8, 9), (10, 11), (12, 13)):
        draws.celebration(first).celebration(second)
    run(rig, lambda: rig.game.superbowl((24, 17)), draws)
    assert texts(rig) == [WIN] * 3
    assert sounds_played(rig) == (["foot15"] * 8 + ["foot25"] + ["foot15"] * 9
                                  + ["foot15"] * 10 + ["foot25"] + ["foot15"] * 11
                                  + ["foot15"] * 12 + ["foot25"] + ["foot15"] * 13)
    assert rig.game.replay == [WIN] and rig.keys.waits == 3
    assert " here's the instant rea play " not in texts(rig)         # this procedure does not use inrep


def test_any_other_key_ends_it_and_the_speech_is_stopped(tmp_path):
    rig = presentation_rig(tmp_path, [27], (17, 24))
    run(rig, lambda: rig.game.superbowl((17, 24)), Draws().celebration(8))
    kinds = [kind for kind, _ in rig.sapi.events]
    assert kinds[-1] == "stop" and rig.game.season.gtp == 42


def test_pag_runs_the_presentation_once_in_place_of_the_final_score_and_the_season_ends(tmp_path):
    for seed in (3, 5, 8):
        rig = make_rig(tmp_path / str(seed), rng=random.Random(seed), policy=enter_policy, fast=True, gtp=20)
        play(rig)
        spoken = [t for t, _, _ in rig.said]
        presentations = [t for t in spoken if " have Won the super Bowl! " in t]
        assert len(presentations) == 1 and " The Final score is" not in spoken
        assert rig.game.season.gtp == 0
        assert rig.game.rnd.fallbacks == 0
