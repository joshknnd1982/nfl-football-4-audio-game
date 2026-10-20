"""The play engine with the N. F. L. rules: the play menus with Time Out, the player's timeout, F1 and F4, out of bounds,
the period that ends at the snap or after a score, the timeouts said at a half's first kick-off, the added statistics and
help (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 5, 6.3, 10.4, PX SX.2). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source; the speech is the fake SAPI's list of (text, speaker, rate step).
"""
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import TIMEOUT_ACTION, NflRules
from nfl4.game import menus
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.rules import NORMAL_KICKOFF
from nflrig import nfl_engine_rig
from pagrig import Draws
from randsources import ScriptedRandom

ENTER, UP, DOWN, F1, F4 = 13, 38, 40, 112, 115


def script(rig, draws: Draws):
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []


def check(rig, draws: Draws):
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert rig.rnd.source.left == 0


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


# ----- the menus as data (H3, design 10.4) -----

def test_the_offense_menu_ends_with_time_out_and_save_game_with_their_letters(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.text for i in items] == [" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ",
                                       " 5. Long Pass ", " 6. Field Goal ", " 7. Punt ", " 8. Time Out ",
                                       " 9. Save Game "]
    assert [i.digit for i in items] == list(range(1, 10))
    assert items[7].action == TIMEOUT_ACTION and items[7].letter == "t"
    assert items[8].action == (menus.SAVE, 0) and items[8].letter == "s"
    assert all(i.letter == "" for i in items[:7])


def test_the_defense_menu_and_the_two_point_try_and_timeouts_off(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    s = rig.engine.s
    assert [i.text for i in rig.rules.defense_menu(s)][-2:] == [" 7. Time Out ", " 8. Save Game "]
    assert rig.rules.offense_menu(s, True) == menus.offense_menu(True)         # the try: the original's items 1 to 5
    rig = nfl_engine_rig(tmp_path / "off", rules=NflRules(timeouts_on=False))
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.text for i in items][-2:] == [" 7. Punt ", " 8. Save Game "] and items[-1].letter == "s"


def test_classic_menus_have_no_letters():
    assert all(i.letter == "" for i in menus.offense_menu() + menus.defense_menu())


# ----- the player's timeout (N1.2, design 6.3) -----

def test_t_goes_to_time_out_and_enter_calls_it_then_the_menu_starts_again(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=["t", ENTER, ENTER], wisoff=1, defense=2, half=2, yard_line=30,
                         extras=dict(left=500, pending=33, running=True))
    draws = Draws().below(6, 1)                                     # u = 4 seconds of the 33 pending
    script(rig, draws)
    step = rig.engine.offense_menu()
    check(rig, draws)
    assert step == rig.engine.offense_chosen and rig.engine.s.offense_play == 1
    said = texts(rig)
    assert said == [" Kim" + P.SELECT_OFFENSE, " 1. Line Plunge ", " 8. Time Out ", " time out called by the Bengals. ",
                    " you have 2 time outs left. ", " Kim" + P.SELECT_OFFENSE, " 1. Line Plunge "]
    x = rig.engine.s.extras
    assert x.timeouts == [2, 3] and x.used == [1, 0] and x.called == [True, False]
    assert x.left == 496 and x.pending == 0 and not x.running
    assert "snd_foot11" in [e.sound_id for e in rig.slot_log if e.action == "play"]


def test_a_second_timeout_in_the_same_dead_ball_period_is_refused_and_the_menu_stays(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=["t", ENTER, "1", ENTER], wisoff=2, defense=1, half=2, yard_line=30,
                         extras=dict(left=500, called=[True, False], timeouts=[2, 3]))
    script(rig, Draws().rnd(9, 3))                                   # the computer's offense draw after the choice
    step = rig.engine.defense_menu()
    assert step == rig.engine.defense_chosen
    said = texts(rig)
    assert said[2:5] == [" 7. Time Out ", X.text("NXT-05"), " 7. Time Out "]
    assert rig.engine.s.extras.timeouts == [2, 3]


def test_a_timeout_with_none_left_is_refused_never_granted(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=["t", ENTER, UP, UP, ENTER], wisoff=1, defense=2, half=2, yard_line=30,
                         extras=dict(left=500, timeouts=[0, 3]))
    script(rig, Draws())
    step = rig.engine.offense_menu()
    assert step == rig.engine.offense_chosen and rig.engine.s.offense_play == 6
    said = texts(rig)
    assert said[2:6] == [" 8. Time Out ", " you have no time outs left. ", " 8. Time Out ", " 7. Punt "]
    assert rig.engine.s.extras.timeouts == [0, 3] and rig.engine.s.extras.used == [0, 0]


def test_the_last_timeout_says_none_are_left_and_a_remark_may_follow(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=["t", ENTER, "s", ENTER], comments=True, wisoff=1, defense=2, half=2,
                         yard_line=30, extras=dict(left=500, timeouts=[1, 3]))
    draws = Draws().rnd(3, 1).rnd(5, 2)                              # the remark chance 1 in 3, then TO02
    script(rig, draws)
    step = rig.engine.offense_menu()
    check(rig, draws)
    assert step == rig.engine.save_game
    said = texts(rig)
    i = said.index(" time out called by the Bengals. ")
    assert said[i + 1:i + 3] == [" you have no time outs left. ", X.text("TO02")]    # its exact spaces (a default)


def test_the_s_key_goes_to_save_game(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=["s", ENTER], wisoff=1, defense=2, half=2, yard_line=30)
    script(rig, Draws())
    assert rig.engine.offense_menu() == rig.engine.save_game
    assert texts(rig)[-1] == " 9. Save Game "


# ----- F1 and F4 in a play menu (H13, design 5.5) -----

def test_f1_adds_the_clock_and_the_timeouts_after_the_original_sentences(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=[F1, "1", ENTER], wisoff=1, defense=2, half=2, yard_line=30, down=2,
                         to_go=7, extras=dict(left=500, pending=30, running=True, timeouts=[2, 1]))
    script(rig, Draws())
    rig.engine.offense_menu()
    said = texts(rig)
    i = said.index(" the clock is running ")
    assert said[i - 2].startswith(P.F1_ITS) and said[i - 1].startswith(P.F1_ITS_SHORT)
    assert said[i + 1] == " you have 2 time outs left, and the Jets have 1. "


def test_f1_says_the_clock_is_stopped(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    assert rig.rules.extra_situation(rig.engine.s) == [" the clock is stopped ",
                                                       " you have 3 time outs left, and the Jets have 3. "]
    rig = nfl_engine_rig(tmp_path / "off", rules=NflRules(timeouts_on=False))
    assert rig.rules.extra_situation(rig.engine.s) == [" the clock is stopped "]


def test_f4_in_a_play_menu_speaks_the_real_time_and_draws_nothing(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=[F4, ENTER], quarter=2, wisoff=1, defense=2, half=2, yard_line=30,
                         extras=dict(left=192, period=2))
    script(rig, Draws())
    rig.engine.offense_menu()
    assert " 3 minutes  12 seconds remaining in the second quarter. " in texts(rig)
    assert rig.rnd.trace == []


# ----- out of bounds (H2 after_tackle, design 5.2) -----

def run_ended(rig, kind=O.RUN, yards=5):
    s = rig.engine.s
    s.result_kind, s.offense_play, s.yards = kind, 1 if kind == O.RUN else 4, yards
    s.tackle_sentence, s.tackle_sound, s.return_flag = " Back1 is brought down ", 1, True
    rig.engine.mark_spot()


def test_out_of_bounds_follows_the_tackle_sentence_and_comes_before_the_gain(tmp_path):
    rig = nfl_engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=35, down=1, to_go=10,
                         extras=dict(left=600))
    run_ended(rig)
    draws = Draws().below(100, 7).below(4, 1)                        # 7 is below 8: out of bounds; L = 5
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert said == [" Back1 is brought down ", " and is pushed out of bounds ", P.GAIN + "5" + P.YARD + P.PLURAL
                    + P.ON_THE_PLAY]
    x = rig.engine.s.extras
    assert x.out_of_bounds and x.left == 595 and x.plays == 1 and step == rig.engine.banter_position


def test_in_bounds_says_nothing_more_and_an_incompletion_draws_no_out_of_bounds(tmp_path):
    rig = nfl_engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=35, extras=dict(left=600))
    run_ended(rig)
    draws = Draws().below(100, 8).below(4, 0)
    script(rig, draws)
    rig.engine.field_play_end()
    check(rig, draws)
    assert " and is pushed out of bounds " not in texts(rig) and not rig.engine.s.extras.out_of_bounds
    rig = nfl_engine_rig(tmp_path / "b", wisoff=1, defense=2, half=2, yard_line=35, extras=dict(left=600))
    run_ended(rig, kind=O.PASS_INCOMPLETE, yards=0)
    draws = Draws().below(5, 0)                                      # only L of an incompletion
    script(rig, draws)
    rig.engine.field_play_end()
    check(rig, draws)


def test_a_completion_goes_out_of_bounds_more_often_than_a_run(tmp_path):
    from nfl4.extras import tuning as T
    assert T.OUT_OF_BOUNDS_PASS_COMPLETE > T.OUT_OF_BOUNDS_RUN
    rig = nfl_engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=35, extras=dict(left=600))
    run_ended(rig, kind=O.PASS_COMPLETE)
    draws = Draws().below(100, T.OUT_OF_BOUNDS_PASS_COMPLETE - 1).below(4, 0)
    script(rig, draws)
    rig.engine.field_play_end()
    check(rig, draws)
    assert rig.engine.s.extras.out_of_bounds


# ----- the ends of the periods (design 5.4) -----

def test_a_runoff_that_runs_the_period_out_ends_it_at_the_snap_without_a_play(tmp_path):
    rig = nfl_engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=35, offense_play=1, defense_play=3,
                         extras=dict(left=20, pending=30, running=True))
    script(rig, Draws())
    step = rig.engine.snap()
    assert step == rig.engine.period_checks
    assert rig.engine.s.extras.left == 0 and rig.engine.clock.period_over() and texts(rig) == []


def test_a_runoff_shorter_than_the_time_left_runs_at_the_snap_and_the_play_goes_on(tmp_path):
    rig = nfl_engine_rig(tmp_path, wisoff=1, defense=2, half=2, yard_line=35, offense_play=6, defense_play=3,
                         extras=dict(left=50, pending=30, running=True))
    script(rig, Draws())
    assert rig.engine.snap() == rig.engine.field_goal
    assert rig.engine.s.extras.left == 20 and rig.engine.s.extras.pending == 0


def test_a_score_as_time_ran_out_in_the_second_or_fourth_quarter_ends_the_period_before_the_kickoff(tmp_path):
    for quarter in (2, 4):
        rig = nfl_engine_rig(tmp_path / str(quarter), quarter=quarter, wisoff=2, defense=1, half=1,
                             extras=dict(left=0, period=quarter, announced="H1" if quarter == 2 else "H2",
                                         unit="H1" if quarter == 2 else "H2"))
        script(rig, Draws())
        assert rig.engine.kick_off() == rig.engine.next_play
        assert texts(rig) == [] and rig.rnd.trace == []


def test_in_the_first_and_third_quarters_the_kickoff_after_such_a_score_still_comes(tmp_path):
    for quarter in (1, 3):
        rig = nfl_engine_rig(tmp_path / str(quarter), quarter=quarter, extras=dict(left=0, period=quarter,
                                                                                    announced="H1", unit="H1"))
        assert rig.rules.before_kickoff(rig.engine.s, 1) == NORMAL_KICKOFF


def test_the_timeouts_are_said_once_at_the_first_kickoff_of_a_half_and_of_an_overtime_period(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    s, x = rig.engine.s, rig.engine.s.extras
    rig.rules.before_kickoff(s, 2)
    rig.rules.before_kickoff(s, 2)
    assert texts(rig) == [" each team has 3 time outs for this half. "]
    x.unit = "OT1"
    x.timeouts = [2, 2]
    rig.rules.before_kickoff(s, 2)
    assert texts(rig)[-1] == " each team has 2 time outs for this period. "
    rig = nfl_engine_rig(tmp_path / "off", rules=NflRules(timeouts_on=False))
    rig.rules.before_kickoff(rig.engine.s, 2)
    assert texts(rig) == []


# ----- the added statistics (H11) and help (H12) -----

def test_the_statistics_add_the_timeouts_used(tmp_path):
    rig = nfl_engine_rig(tmp_path, extras=dict(used=[1, 2]))
    assert rig.rules.extra_stats_lines(rig.engine.s) == [" Time Outs Used", "Bengals 1", "Jets 2"]
    rig = nfl_engine_rig(tmp_path / "off", rules=NflRules(timeouts_on=False))
    assert rig.rules.extra_stats_lines(rig.engine.s) == []


def test_f5_f6_f7_add_their_lines_after_the_original_text_during_an_nfl_game(tmp_path):
    from nfl4.game import extra_texts as words
    from nfl4.game import help_texts as H
    rig = nfl_engine_rig(tmp_path)
    hot = rig.game.hotkeys
    for menu, original, ids in ((hot.speckeys, H.SPECIAL_KEYS, ("NXH-02", "NXH-01")),       # the clock, then the T key
                                (hot.say_hints, H.TERMINOLOGY + H.TERMINOLOGY_CLONE_END, ("NXH-07", "NXH-08"))):
        start = len(rig.said)
        menu()
        said = texts(rig, start)
        lead = [original] + ([words.KEYS_ADDED_F9] if menu == hot.speckeys else [])      # S8.2: F9 is in the key list, in every mode
        assert said[:len(lead)] == lead and said[len(lead):] == [X.text(i) for i in ids]
    rig.rules.state.extras.timeouts_on = False
    assert rig.rules.extra_help("117") == [X.text("NXH-03"), X.text("NXH-04"), X.text("NXH-06")]


def test_the_help_of_a_classic_program_has_no_added_lines(tmp_path):
    rig = nfl_engine_rig(tmp_path)
    rig.game.play_engine = None                                      # no game: the program's rules, Classic
    start = len(rig.said)
    rig.game.hotkeys.speckeys()
    from nfl4.game import extra_texts as words
    from nfl4.game import help_texts as H
    assert texts(rig, start) == [H.SPECIAL_KEYS, words.KEYS_ADDED_F9]
