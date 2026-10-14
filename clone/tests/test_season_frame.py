"""The season frame on the Game: the score speech, the clock speech, the one random function. This is inspired by Jim Kitchen.

GAME_SPEC 5.3 and 5.4 (CODE (lifted) sgc p_42bfc0, SayScore p_42b590, SayFinalScore p_42bab0), G-D2 (one generator behind one
function). The standings speech is in test_standings.py, the speakers in test_speakers.py.
"""
import pytest

from gamerig import Rig
from nfl4.game import scorespeech
from nfl4.game.league import League
from nfl4.game.scorespeech import score_sentence
from nfl4.speech.roles import ANNOUNCER
from randsources import ScriptedRandom, below_value
from specfiles import original_strings


def rig_with_teams(**kwargs):
    rig = Rig(**kwargs)
    season = rig.game.season
    season.choose_team(1, 1)               # Bengals
    season.tn3, season.tn4 = 2, 3          # this week's opponent: Jets
    return rig


# ----- the score sentences -----

def test_the_score_sentence_for_each_case_with_the_doubled_spaces_str_makes():
    assert score_sentence("Bengals", "Jets", 14, 7) == "Bengals.  14. Jets.  7"
    assert score_sentence("Bengals", "Jets", 17, 21) == "Jets.  21. Bengals.  17"
    assert score_sentence("Bengals", "Jets", 7, 7) == " tied 7 all"
    assert score_sentence("Bengals", "Jets", 0, 0) == " tied 0 all"
    assert score_sentence("Bengals", "Jets", 3, 0) == "Bengals.  3. Jets.  0"
    assert score_sentence("Bengals", "Jets", 0, 2) == "Jets.  2. Bengals.  0"


def test_the_team_names_are_right_trimmed_before_the_full_stop():
    assert score_sentence("Sea hawks  ", "Jets ", 9, 3) == "Sea hawks.  9. Jets.  3"
    assert score_sentence("Sea hawks  ", "Jets ", 3, 9) == "Jets.  9. Sea hawks.  3"


def test_the_score_texts_are_strings_of_the_original():
    strings = original_strings()
    for text in (scorespeech.THE_SCORE_IS, scorespeech.THE_FINAL_SCORE_IS, scorespeech.TIED, scorespeech.ALL,
                 scorespeech.AFTER_NAME):
        assert text in strings, text
    assert scorespeech.THE_FINAL_SCORE_IS.endswith("is")                 # no space at the end, as in the exe


def test_say_score_says_the_introduction_then_the_sentence_waited_and_logs_two_lines_whatever_ptf_is():
    rig = rig_with_teams()
    game = rig.game
    log = []
    game.log_sink = log.append
    pumps = []
    original_pump = rig.keys.pump
    rig.keys.pump = lambda: (pumps.append(1), original_pump())
    game.say_score(14, 7)
    assert rig.said == [(" The score is ", ANNOUNCER, 0), ("Bengals.  14. Jets.  7", ANNOUNCER, 0)]
    assert [kind for kind, _ in rig.sapi.events] == ["speak", "speak", "wait"]       # say5 queues, say waits
    assert log == ["", " The score is Bengals.  14. Jets.  7"] and game.ptf == 0
    assert pumps                                                                   # the original ends with DoEvents
    assert game.replay == []                                                       # say5 and say are not kept


def test_say_score_also_logs_the_two_spoken_lines_when_ptf_is_1():
    rig = rig_with_teams()
    log = []
    rig.game.log_sink, rig.game.ptf = log.append, 1
    rig.game.say_score(3, 3)
    assert log == [" The score is ", " tied 3 all", "", " The score is  tied 3 all"]


def test_say_final_score_sets_ptf_for_its_lines_and_clears_it():
    rig = rig_with_teams()
    game = rig.game
    log = []
    game.log_sink = log.append
    game.say_final_score(10, 20)
    assert rig.said == [(" The Final score is", ANNOUNCER, 0), ("Jets.  20. Bengals.  10", ANNOUNCER, 0)]
    assert [kind for kind, _ in rig.sapi.events] == ["speak", "speak", "wait"]
    assert log == [" The Final score is", "Jets.  20. Bengals.  10"] and game.ptf == 0


def test_the_scores_use_the_leagues_names_so_a_players_team_names_are_spoken():
    names = ["Own %d" % n for n in range(1, 33)]
    rig = Rig()
    rig.game.league = League(names)
    rig.game.season.choose_team(2, 2)
    rig.game.season.tn3, rig.game.season.tn4 = 8, 4
    rig.game.say_score(1, 0)
    assert rig.said[1][0] == "Own 6.  1. Own 32.  0"
    assert rig.game.own_team() == "Own 6" and rig.game.opponent_team() == "Own 32"


# ----- the clock on the Game -----

def test_sgc_says_the_time_with_say5_clears_the_key_and_leaves_f1_in_g():
    source = ScriptedRandom([below_value(30, 15)], strict=True)
    rig = Rig(rng=source)
    game = rig.game
    log = []
    game.log_sink, game.ptf = log.append, 1
    game.keys.char = "x"
    game.keys.code_text = "27"
    game.sgc(10, 30, 1)
    assert rig.said == [(" 9 minutes  53 seconds remaining in the first quarter. ", ANNOUNCER, 0)]
    assert [kind for kind, _ in rig.sapi.events] == ["speak"]                    # say5: queued, not waited
    assert log == [" 9 minutes  53 seconds remaining in the first quarter. "]
    assert game.keys.code_text == "112" and game.keys.char == ""                  # clk, then g = "112"
    assert game.replay == []


def test_sgc_twice_in_one_play_repeats_the_time_and_draws_nothing_the_second_time():
    source = ScriptedRandom([below_value(30, 20)], strict=True)
    rig = Rig(rng=source)
    rig.game.sgc(12, 33, 1)
    rig.game.sgc(12, 33, 1)
    assert rig.said[0][0] == rig.said[1][0] and source.left == 0


def test_the_games_set_up_gives_the_clock_its_warning_lengths():
    rig = Rig()
    setup = rig.game.new_game_setup()
    clock = rig.game.quarter_clock
    assert (clock.m2w, clock.m4w, clock.m5w) == setup.warnings and clock.countdown == 100


# ----- one random function -----

def test_the_game_and_the_sounds_draw_from_the_same_generator(tmp_path):
    source = ScriptedRandom([0.1, 0.2, 0.35, 0.45], strict=True)
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=source)
    assert rig.game.rnd is rig.rnd and rig.sounds.rng is rig.rnd
    assert rig.game.rnd.random() == 0.1 and rig.sounds._rnd() == 0.2
    assert rig.game.rnd(10) == 4 and rig.game.rnd.below(10) == 4        # 0.35 -> 3 + 1, 0.45 -> 4
    assert source.left == 0


def test_a_seeded_rig_repeats_its_whole_game_setup():
    import random
    one = Rig(rng=random.Random(99)).game.new_game_setup()
    two = Rig(rng=random.Random(99)).game.new_game_setup()
    assert one == two
    assert one != Rig(rng=random.Random(100)).game.new_game_setup()
