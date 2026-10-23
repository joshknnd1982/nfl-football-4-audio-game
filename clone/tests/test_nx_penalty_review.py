"""The independent review of PX SX.3 (nfl4 only, rule 0.13; D-050 item 10, work/review_sx3_findings.md): one test per
finding that was fixed. This is inspired by Jim Kitchen.
"""
from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras import penalty_list as PL
from nfl4.extras import rules_2026 as R
from nfl4.extras.penalties import Down, PlayFacts
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nfl4.game.rules import TRY_AGAIN
from pagrig import Draws
from test_nx_penalties import ENTER, check, game, play_ended, rows, script, snap, texts, value_of

DEAD = [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]


def test_1_the_run_off_prompt_says_the_time_left_after_the_run_off_and_the_clock_running_out(tmp_path):
    rig = game(tmp_path, answers=[ENTER], quarter=4, wisoff=2, defense=1, half=1, yard_line=40, offense_play=1,
               defense_play=2, extras=dict(left=39, period=4, warning_given=True, running=True, pending=30))
    draws = Draws().below(10000, value_of(rig, DEAD, "P01")).rnd(12, 1).rnd(4, 1).rnd(10, 1)
    script(rig, draws)
    step = rig.engine.snap()
    check(rig, draws)
    assert X.text("NXP-19") in texts(rig)                             # 9 left: the run off ends the quarter
    assert step == rig.engine.period_checks and rig.engine.s.extras.left == 0


def test_4_a_foul_before_the_snap_of_a_two_point_try_leaves_nothing_waiting(tmp_path):
    rig = game(tmp_path, half=1, yard_line=2, two_point=True, offense_play=1, defense_play=2)
    draws = Draws().below(10000, value_of(rig, DEAD, "P01")).rnd(12, 1).rnd(4, 1).rnd(10, 1)
    script(rig, draws)
    step = rig.engine.snap()
    check(rig, draws)
    x = rig.engine.s.extras
    assert step == rig.engine.offense_menu and rig.engine.s.yard_line == 7 and rig.engine.s.two_point
    assert not x.no_snap and x.foul_clock == ""


def test_5_a_defense_foul_on_a_good_try_is_not_offered_and_said_declined(tmp_path):
    try_down = Down(1, 98, two_point=True)
    how, _, _ = PEN.answers(F.BY_ID["P09"][0], try_down, PlayFacts(O.PASS_COMPLETE, 100, score="two-point",
                                                                   offense_play=4))
    assert how == PEN.AUTO_DECLINE
    how, _, _ = PEN.answers(F.BY_ID["P08"][0], try_down, PlayFacts(O.PASS_INCOMPLETE, 98, offense_play=4))
    assert how == PEN.AUTO_DECLINE                                    # an offense foul on a failed try: no try again
    how, accepted, _ = PEN.answers(F.BY_ID["P15"][0], try_down, PlayFacts(O.PASS_INCOMPLETE, 98, offense_play=4),
                                   foul_spot=91)
    assert how == PEN.CHOICE and accepted.kind == PEN.TRY_FAILS


def test_6_off_wins_over_a_weight_in_penalties_txt():
    assert PL.parse_value("holding; off; weight 50")[1] == 0
    assert PL.parse_value("holding; weight 50; off")[1] == 0
    assert PL.parse_value("holding; on; weight 50")[1] == 50


def test_7_delay_of_game_after_the_warning_gets_the_run_off(tmp_path):
    """SX.13 (RB26 4-7-1 (a): a foul that stops the clock during any dead ball period): the player's defense is offered the run off
    (Enter takes it: 70 left after the pending 30, 60 after the run off). Before SX.13 delay of game was excepted (Part 1.5)."""
    assert "DOG" not in R.NO_RUNOFF_FOULS
    rig = game(tmp_path, answers=[ENTER], quarter=4, wisoff=2, defense=1, half=1, yard_line=40, offense_play=1, defense_play=2,
               extras=dict(left=100, period=4, warning_given=True, running=True, pending=30))
    draws = Draws().below(10000, value_of(rig, DEAD, "P02")).rnd(4, 1).rnd(10, 1)
    script(rig, draws)
    rig.engine.snap()
    check(rig, draws)
    assert X.text("NXP-A03") in texts(rig) and rig.engine.s.extras.left == 60


def test_8_after_a_penalty_the_runoff_is_bounded_by_the_play_clock_of_25(tmp_path):
    rig = game(tmp_path, quarter=2, extras=dict(left=600, plays=1, handled=0, last_kind=O.RUN, last_offense=1,
                                                foul_clock="live"))
    draws = Draws().below(11, 10).below(4, 0)                        # 40, the ready-signal cut 2: 38, capped at 25
    script(rig, draws)
    rig.rules.between_plays(rig.engine.s)
    assert rig.engine.s.extras.pending == R.PLAY_CLOCK_AFTER_PENALTY


def test_9_a_personal_foul_by_the_offense_before_a_fumble_lets_the_defense_keep_the_ball():
    fumble = PlayFacts(O.RUN, 40, turnover=True, offense_play=1)
    how, _, declined = PEN.answers(F.BY_ID["P17"][1], Down(1, 40), fumble, foul_spot=40)
    assert F.BY_ID["P17"][1].offender == F.OFFENSE
    assert how == PEN.AUTO_DECLINE and declined.kind == PEN.TURNOVER


def test_10_a_foul_not_offered_is_said_declined(tmp_path):
    rig = game(tmp_path, wisoff=1, defense=2, half=2, yard_line=0)
    s = rig.engine.s
    rig.rules.before_kickoff(s, 2)
    s.result_kind, s.offense_play, s.yards = O.KICKOFF_RETURN, 0, 0
    value = value_of(rig, rows(rig, O.KICKOFF_RETURN, after=False), "P24")
    draws = Draws().below(10000, value).rnd(17, 6).rnd(40, 2).below(4, 0).celebration(8).rady(0)
    script(rig, draws)
    rig.engine.touchdown_reached()
    check(rig, draws)
    said = texts(rig)
    i = said.index(X.text("NXP-07", team="Bengals"))
    assert said[i - 1] == " off sides on the kick off, on the Jets, ODef6. " and said[i + 1] == " TOUCH DOWN"
    assert rig.rules.penalty.events[-1][1] == "not offered"


def test_11_on_the_last_play_of_a_half_both_answers_say_the_half_ends(tmp_path):
    rig = game(tmp_path, answers=[ENTER], quarter=2, extras=dict(left=4, period=2, warning_given=True))
    snap(rig)
    play_ended(rig, O.RUN, yards=3, offense_play=1)
    value = value_of(rig, rows(rig, O.RUN), "P18", F.DEFENSE)       # unnecessary roughness after the play: no extension
    draws = Draws().below(100, 50).below(10000, value).rnd(17, 1).rnd(40, 2).below(4, 2)
    script(rig, draws)
    rig.engine.field_play_end()
    check(rig, draws)
    halves = [t for t in texts(rig) if t.endswith(", " + X.text("NXP-S08") + ". ")]
    assert len(halves) == 3 and halves[0].startswith(" Kim if you accept")
    assert halves[2].startswith(" the penalty is accepted. ")                  # the referee's result says it too (2026-10-23)
    x = rig.engine.s.extras
    assert x.left == 0 and not x.extension and rig.rules.penalty.events[-1][1] == "accepted"


def test_13_grounding_on_the_goal_line_is_not_a_safety():
    _, accepted, _ = PEN.answers(F.GROUNDING, Down(1, 6), PlayFacts(O.PASS_INCOMPLETE, 6, offense_play=4),
                                 foul_spot=0)
    assert accepted.kind == PEN.NEW_DOWN and accepted.los == 1


def test_the_try_again_continuation_is_the_offense_menu(tmp_path):
    rig = game(tmp_path)
    assert rig.engine.continuation(TRY_AGAIN) == rig.engine.offense_menu
    assert isinstance(rig.rules, NflRules)
