"""The original's speakers say to say6, the replay list, the speech log, inrep and the pauses. This is inspired by Jim Kitchen.

GAME_SPEC 9.1 and 9.2 (CODE (lifted) say, say2, say3, say4, say5, say6, inrep p_4863f0), 7 (rady, dy), GAP_REGISTER G-S1
(asynchronous, synchronous, purge), G-S2 (the pauses), G-S4 (vr). The rig's SAPI fake takes speakers and records every
text with its speaker, so the roles and the waits can be read off.
"""
import pytest

from gamerig import Rig
from nfl4.speech.roles import (ANNOUNCER, OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER, OWN_QUARTERBACK)
from nfl4.game.speakers import REPLAY_INTRO
from randsources import ScriptedRandom, below_value
from specfiles import original_strings


def kinds(rig):
    return [kind for kind, _ in rig.sapi.events]


def test_the_replay_texts_are_strings_of_the_original():
    strings = original_strings()
    assert REPLAY_INTRO == " here's the instant rea play " and REPLAY_INTRO in strings
    assert " select your play " in strings


# ----- who speaks, whether it waits, what is logged and kept -----

def test_say_is_the_announcer_waits_logs_and_is_not_kept_for_the_replay():
    rig = Rig()
    game = rig.game
    log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
    game.say(" hello ")
    assert rig.said == [(" hello ", ANNOUNCER, 0)] and kinds(rig) == ["speak", "wait"]
    assert log == [" hello "] and game.replay == []


def test_say2_is_the_announcer_does_not_wait_logs_and_is_kept_for_the_replay():
    rig = Rig()
    game = rig.game
    log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
    game.say2(" queued ")
    assert rig.said == [(" queued ", ANNOUNCER, 0)] and kinds(rig) == ["speak"]
    assert log == [" queued "] and game.replay == [" queued "] and game.ilc == 1


def test_say4_is_the_announcer_waits_logs_and_is_kept_for_the_replay():
    rig = Rig()
    game = rig.game
    log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
    game.say4(" a result ")
    assert rig.said == [(" a result ", ANNOUNCER, 0)] and kinds(rig) == ["speak", "wait"]
    assert log == [" a result "] and game.replay == [" a result "]


def test_say5_is_the_announcer_does_not_wait_logs_and_is_not_kept():
    rig = Rig()
    game = rig.game
    log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
    game.say5(" a prompt ")
    assert rig.said == [(" a prompt ", ANNOUNCER, 0)] and kinds(rig) == ["speak"]
    assert log == [" a prompt "] and game.replay == []


def test_nothing_is_logged_while_ptf_is_not_1_but_the_replay_list_still_fills():
    rig = Rig()
    game = rig.game
    log, game.log_sink = [], (lambda text: log.append(text))
    for ptf in (0, 2):
        game.ptf = ptf
        for speak in (game.say, game.say2, game.say4, game.say5, game.say6):
            speak(" x ")
    assert log == [] and game.replay == [" x "] * 4


def test_say3_is_the_quarterback_or_the_punter_of_the_side_on_offense_waits_and_is_neither_logged_nor_kept():
    cases = [(1, 1, OWN_QUARTERBACK), (2, 1, OPPONENT_QUARTERBACK), (1, 2, OWN_PUNTER), (2, 2, OPPONENT_PUNTER),
             (1, 0, OWN_PUNTER), (2, 3, OPPONENT_PUNTER)]            # qorp is 1 for a quarterback, anything else a punter
    for wisoff, qorp, role in cases:
        rig = Rig()
        game = rig.game
        log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
        game.wisoff, game.qorp = wisoff, qorp
        game.say3(" Hike! ")
        assert rig.said == [(" Hike! ", role, 0)] and kinds(rig) == ["speak", "wait"]
        assert log == [] and game.replay == []


def test_say6_speaks_with_the_voice_that_spoke_last_asynchronously_and_logs():
    rig = Rig()
    game = rig.game
    log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
    game.say6(" first ")                                      # nobody spoke yet: the announcer
    game.wisoff, game.qorp = 2, 2
    game.say3(" punt ")
    game.say6(" and the punter goes on ")
    game.say(" announcer again ")
    game.say6(" and now the announcer ")
    assert [role for _, role, _ in rig.said] == [ANNOUNCER, OPPONENT_PUNTER, OPPONENT_PUNTER, ANNOUNCER, ANNOUNCER]
    assert kinds(rig) == ["speak", "speak", "wait", "speak", "speak", "wait", "speak"]
    assert log == [" first ", " and the punter goes on ", " announcer again ", " and now the announcer "]
    assert game.replay == []


def test_an_empty_text_changes_the_replay_list_and_the_log_but_nothing_is_spoken():
    rig = Rig()
    game = rig.game
    log, game.log_sink, game.ptf = [], (lambda text: log.append(text)), 1
    game.say2("")
    game.say4("")
    game.say("")
    assert rig.said == [] and kinds(rig) == [] and game.replay == ["", ""] and log == ["", "", ""]


def test_a_synchronous_say_waits_for_everything_queued_before_it():
    rig = Rig(speech_per_char=0.01)
    game = rig.game
    game.say2("a" * 100)                                       # 1.0 s of speech, queued and the game goes on
    assert rig.clock.now == 1000.0
    game.say("b" * 50)                                         # 0.5 s more, and it waits for the whole queue
    assert rig.clock.now == pytest.approx(1000.0 + 1.5, abs=0.002)


def test_stopspeech_purges_the_queue():
    rig = Rig(speech_per_char=0.01)
    rig.game.say2("a" * 100)
    rig.game.stopspeech()
    assert kinds(rig) == ["speak", "stop"]
    rig.game.say("x")                                          # nothing is queued any more: no wait for the purged line
    assert rig.clock.now == pytest.approx(1000.01, abs=0.003)


def test_the_logs_empty_line_goes_to_the_sink_and_a_missing_sink_loses_nothing_and_breaks_nothing():
    rig = Rig()
    log = []
    rig.game.log_sink = log.append
    rig.game.log_print("")
    rig.game.log_sink = None
    rig.game.log_print("nobody listens")
    assert log == [""]
    rig.game.ptf = 1
    rig.game.say5(" fine ")                                    # no sink: nothing is written, nothing fails


# ----- the replay list and inrep -----

def test_the_replay_list_counts_empties_and_remembers_its_longest_length():
    rig = Rig()
    game = rig.game
    for n in range(7):
        game.say2("line %d" % n)
    assert game.ilc == 7 and game.replay_longest == 7
    game.empty_replay()
    assert game.ilc == 0 and game.replay == [] and game.replay_longest == 7
    game.say4("again")
    assert game.ilc == 1 and game.replay_longest == 7


def test_inrep_says_its_introduction_waits_pauses_a_fifth_of_a_second_and_queues_the_lines():
    rig = Rig(speech_per_char=0.01)
    game = rig.game
    game.season.coach = "Bob"
    game.replay[:] = [" one ", " two ", " three "]
    log = []
    game.log_sink, game.ptf = log.append, 1
    game.inrep()
    assert [text for text, _, _ in rig.said] == [REPLAY_INTRO, " one ", " two ", " three "]
    assert all(role == ANNOUNCER for _, role, _ in rig.said)
    assert kinds(rig) == ["speak", "wait", "speak", "speak", "speak"]              # the introduction is waited for
    assert game.replay == [" one ", " two ", " three "] and log == []              # neither kept again nor logged
    # the intro's speech (0.01 s a character), the 0.2 s pause, and then the three lines are only queued
    assert rig.clock.now - 1000.0 == pytest.approx(len(REPLAY_INTRO) * 0.01 + 0.2, abs=0.01)


def test_inrep_leaves_out_its_introduction_when_norep_is_set():
    rig = Rig(speech_per_char=0.01)
    game = rig.game
    game.replay[:] = [" one "]
    game.norep = 1
    game.inrep()
    assert [text for text, _, _ in rig.said] == [" one "] and kinds(rig) == ["speak"]
    assert rig.clock.now - 1000.0 == pytest.approx(0.2, abs=0.002)


def test_inrep_stops_after_the_line_that_says_select_your_play():
    rig = Rig()
    game = rig.game
    game.season.coach = "Bob"
    game.replay[:] = [" a ", " Bob select your play ", " after "]
    game.inrep()
    assert [text for text, _, _ in rig.said] == [REPLAY_INTRO, " a ", " Bob select your play "]
    rig2 = Rig()
    rig2.game.season.coach = "Alice"                          # another coach's name does not match: all lines
    rig2.game.replay[:] = [" a ", " Bob select your play ", " after "]
    rig2.game.inrep()
    assert [text for text, _, _ in rig2.said][1:] == [" a ", " Bob select your play ", " after "]


def test_inrep_with_an_empty_list_says_only_the_introduction():
    rig = Rig()
    rig.game.inrep()
    assert [text for text, _, _ in rig.said] == [REPLAY_INTRO]


# ----- the pauses -----

def test_dy_waits_the_seconds_and_pumps_keys_without_ending_early():
    rig = Rig()
    rig.keys.post(65)
    start = rig.clock.now
    rig.game.dy(0.3)
    assert rig.clock.now - start == pytest.approx(0.3, abs=0.002)
    assert rig.keys.code_text == "65"                          # the key was delivered and did not end the pause


@pytest.mark.parametrize("vr, expected_rate", [(-10, 1), (-1, 1), (0, 1), (1, 1), (2, 2), (5, 5), (10, 10)])
def test_rady_waits_the_drawn_thirtieth_over_vr_times_25_with_vr_at_least_1(vr, expected_rate):
    for steps in (0, 1, 15, 29):
        rig = Rig(rng=ScriptedRandom([below_value(30, steps)], strict=True))
        rig.game.vr_source = lambda: vr
        start = rig.clock.now
        rig.game.rady()
        assert rig.clock.now - start == pytest.approx(steps / (expected_rate * 25), abs=0.002)


def test_rady_is_longest_at_rate_1_and_shorter_as_the_speech_gets_faster():
    longest = 29 / 25
    assert longest == pytest.approx(1.16)
    rig = Rig(rng=ScriptedRandom([below_value(30, 29)], strict=True))
    rig.game.vr_source = lambda: 5
    rig.game.rady()
    waited = rig.clock.now - 1000.0
    assert waited == pytest.approx(29 / (5 * 25), abs=0.002) and waited < longest / 4


def test_the_rate_counter_comes_from_the_games_setting():
    rig = Rig()
    assert rig.game.vr == 0
    rig.game.vr_source = lambda: 7
    assert rig.game.vr == 7
