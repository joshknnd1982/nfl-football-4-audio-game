"""Penalties in the play engine: the flag at the end of the play, the player's accept or decline prompt, the computer's
choice when the player's team fouled, a dead-ball foul before the snap, grounding, the untimed down, the ten-second run
off, offsetting fouls, the try, the statistics, the help and the clock after a foul (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN
9, 15; PX SX.3). This is inspired by Jim Kitchen.

Every draw is planned on a strict scripted source; the speech is the fake SAPI's list of (text, speaker, rate step).
"""
import pytest

from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import penalty_flow as PF
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.rules import FOUL_BEFORE_SNAP, GO_ON, NEXT_DOWN
from nflrig import nfl_engine_rig
from pagrig import Draws
from randsources import ScriptedRandom

ENTER, ESC, TAB, UP, DOWN, F1, F2, F3, F4 = 13, 27, 9, 38, 40, 112, 113, 114, 115
NO_FOUL = 9999


def script(rig, draws: Draws):
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []


def check(rig, draws: Draws):
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert rig.rnd.source.left == 0


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def game(tmp_path, answers=(), comments=False, penalties=True, **state):
    defaults = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=2)
    defaults.update(state)
    extras = defaults.pop("extras", {})
    extras.setdefault("left", 600)
    return nfl_engine_rig(tmp_path, answers=answers, comments=comments, rules=NflRules(penalties_on=penalties),
                          extras=extras, **defaults)


def value_of(rig, rows, foul_id, offender=None, offense_play=1, defense_play=1):
    """The below(10000) value that draws `foul_id` (by `offender`) from `rows`: the start of its slice."""
    total = 0
    for foul, weight in rig.rules.penalty._weighted(rows, offense_play, defense_play):
        if foul.id == foul_id and (offender is None or foul.offender == offender):
            return total
        total += weight
    raise AssertionError("%s is not in the rows" % foul_id)


def rows(rig, kind, after=True):
    flow = rig.rules.penalty
    facts = PF.PEN.PlayFacts(kind, 0)
    return flow.rows_for(facts, after)


def snap(rig):
    rig.rules.penalty.take_snap(rig.engine.s)


def play_ended(rig, kind=O.PASS_INCOMPLETE, yards=0, offense_play=4):
    """The state of a play at its end, before field_play_end (the ball moved by end_of_play's rule)."""
    s = rig.engine.s
    s.result_kind, s.offense_play, s.defense_play, s.yards = kind, offense_play, 1, yards
    s.tackle_sentence, s.tackle_sound, s.return_flag = " the tackle ", 1, True
    rig.engine.mark_spot()
    s.yard_line += yards                                             # own half: toward midfield


# ----- the player is offended: the prompt (design 9.3, C9) -----

def defensive_holding(rig, slot=4, second=2):
    """The draws of an incomplete pass with defensive holding by the Jets: the foul, Def<slot>, no second foul, L = 5."""
    value = value_of(rig, rows(rig, O.PASS_INCOMPLETE), "P09", offense_play=4)
    return Draws().below(10000, value).rnd(17, slot).rnd(T.SECOND_FOUL_CHANCE, second).below(5, 2)


def test_the_player_accepts_defensive_holding_with_enter_and_gets_the_first_down(tmp_path):
    rig = game(tmp_path, answers=[ENTER])
    snap(rig)
    rig.engine.s.stats[1].pass_attempts += 1                         # the incomplete pass the penalty erases
    play_ended(rig)
    draws = defensive_holding(rig)
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    i = said.index(X.text("NXP-01"))
    assert said[i - 1] == P.NO_GAIN                                  # the flag after the play's last sentence
    assert said[i + 1:i + 6] == [" defensive holding, on the Jets, ODef4. ",
                                 " Kim if you accept the penalty, it will be first and 10 on your 35 yard line. ",
                                 " if you decline it, it will be second and 10 on your 30 yard line. ", " accept ",
                                 X.text("NXP-24", yards=5, situation="it will be first and 10 on your 35 yard line"),      # the referee (2026-10-23)
                                 X.text("NXP-09")][:5]
    assert said[i + 5:i + 7] == [X.text("NXP-24", yards=5, situation="it will be first and 10 on your 35 yard line"), X.text("NXP-09")]
    s = rig.engine.s
    assert step == rig.engine.position and s.text == P.ITS
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 35, 1, 10)
    assert s.stats[1].pass_attempts == 0 and s.stats[1].first_downs == 1     # erased; a first down by penalty
    assert s.extras.flags == [0, 1] and s.extras.flag_yards == [0, 5]
    assert rig.rules.penalty.events == [(2, "accepted", "P09", 2, 5, False)]
    assert "snd_foot11" in [e.sound_id for e in rig.slot_log if e.action == "play"]


def test_the_player_declines_with_down_and_the_play_stands(tmp_path):
    rig = game(tmp_path, answers=[DOWN, ENTER])
    snap(rig)
    play_ended(rig)
    draws = defensive_holding(rig)
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert said[-3:] == [" accept ", " decline ", X.text("NXP-25", situation="it will be second and 10 on your 30 yard line")]
    s = rig.engine.s
    assert step == rig.engine.banter_position and (s.down, s.to_go, s.yard_line) == (2, 10, 30)
    assert s.extras.flags == [0, 0] and rig.rules.penalty.events[-1][1] == "declined"


def test_the_prompt_starts_at_decline_when_the_play_was_better_and_a_d_and_a_keys_set_the_answer(tmp_path):
    rig = game(tmp_path, answers=["a", "d", ENTER], down=3, to_go=8)
    snap(rig)
    play_ended(rig, O.PASS_COMPLETE, yards=12)
    value = value_of(rig, rows(rig, O.PASS_COMPLETE), "P09", offense_play=4)
    draws = Draws().below(100, 50).below(10000, value).rnd(17, 1).rnd(40, 2).below(4, 0)
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert said[-4:-1] == [" decline ", " accept ", " decline "]     # the better one first; A, then D
    assert said[-1].startswith(" the penalty is declined, ")             # the referee (2026-10-23)
    assert step == rig.engine.banter_position


def test_f1_says_the_flag_again_and_the_keypad_one_is_not_the_letter_a(tmp_path):
    rig = game(tmp_path, answers=[F1, 97, F3, ENTER], down=3, to_go=8)
    snap(rig)
    play_ended(rig, O.PASS_COMPLETE, yards=12)
    value = value_of(rig, rows(rig, O.PASS_COMPLETE), "P09", offense_play=4)
    draws = Draws().below(100, 50).below(10000, value).rnd(17, 1).rnd(40, 2).below(4, 0)
    script(rig, draws)
    rig.engine.field_play_end()
    said = texts(rig)
    first = said.index(X.text("NXP-01"))
    assert said.count(X.text("NXP-01")) == 2 and said.count(" defensive holding, on the Jets, ODef1. ") == 2
    assert said[-2] == " decline " and rig.engine.s.extras.flags == [0, 0]     # 97 typed "a": echoed, not accept
    assert said[-1].startswith(" the penalty is declined, ")                   # the referee's result (2026-10-23)
    assert said.index(X.text("NXP-01"), first + 1) > first


# ----- the player's team fouled: the computer chooses -----

def test_the_computer_accepts_holding_by_the_players_offense_on_a_run(tmp_path):
    rig = game(tmp_path)
    snap(rig)
    rig.engine.s.stats[1].running_plays += 1
    play_ended(rig, O.RUN, yards=6, offense_play=1)
    value = value_of(rig, rows(rig, O.RUN), "P08")
    draws = (Draws().below(100, 50).below(10000, value).rnd(12, 3)
             .below(9, 4)                                            # the spot: 28 + 4 = 32 (between the line and 36)
             .rnd(40, 5).below(4, 1))
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert " holding, on the Bengals, Back3. " in said
    assert X.text("NXP-06", team="Jets") in said
    assert not any(t.startswith(" Kim if you accept") for t in said)
    s = rig.engine.s
    assert step == rig.engine.position and (s.yard_line, s.down, s.to_go) == (22, 1, 18)
    assert s.stats[1].running_plays == 0 and s.extras.flags == [1, 0] and s.extras.flag_yards == [10, 0]


def test_the_computer_declines_holding_when_the_play_lost_more(tmp_path):
    rig = game(tmp_path, down=2, to_go=7)
    snap(rig)
    play_ended(rig, O.SACK, yards=-9, offense_play=4)
    value = value_of(rig, rows(rig, O.SACK), "P08", offense_play=4)
    draws = Draws().below(10000, value).rnd(12, 2).rnd(40, 3).below(5, 0)
    script(rig, draws)
    rig.engine.field_play_end()
    check(rig, draws)
    assert X.text("NXP-07", team="Jets") in texts(rig)
    assert rig.engine.s.down == 3                                    # the sack's down counts


# ----- a dead-ball foul before the snap (design 9.1) -----

def test_a_false_start_stops_the_snap_after_hut_1_and_the_down_is_not_counted(tmp_path):
    rig = game(tmp_path, offense_play=1, defense_play=2, extras=dict(left=500))
    s = rig.engine.s
    counter = s.counter
    dead = [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]
    draws = (Draws().below(10000, value_of(rig, dead, "P01")).rnd(12, 7)
             .rnd(4, 1).rnd(10, 1))                                  # the quarterback's line and the huddle
    script(rig, draws)
    step = rig.engine.snap()
    check(rig, draws)
    said = texts(rig)
    i = said.index(P.HUT_1)
    assert said[i + 1:i + 4] == [X.text("NXP-02"), X.text("NXP-01"), " false start, on the Bengals, Rec1. "]
    assert step == rig.engine.position and (s.yard_line, s.down, s.to_go) == (25, 1, 15)
    assert s.extras.no_snap and rig.rules.penalty.events == [(2, "accepted", "P01", 1, 5, True)]
    script(rig, Draws())
    rig.engine.position()
    rig.engine.down_sentence()
    assert rig.engine.next_play() == rig.engine.play_menu
    assert s.counter == counter and not s.extras.no_snap            # not a counted play


def test_an_offside_at_the_snap_waits_for_the_end_of_the_play(tmp_path):
    rig = game(tmp_path, offense_play=1, defense_play=2)
    dead = [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]
    draws = Draws().below(10000, value_of(rig, dead, "P03")).rnd(17, 9)
    script(rig, draws)
    assert rig.rules.before_snap(rig.engine.s, 1, 2) == GO_ON
    check(rig, draws)
    waiting = rig.rules.penalty.waiting
    assert waiting.foul.id == "P03" and waiting.side == 2 and waiting.slot == 9
    assert rig.rules.before_snap(rig.engine.s, 7, 2) == GO_ON          # a punt: no foul before the snap is drawn


def test_no_draw_at_all_with_penalties_off(tmp_path):
    rig = game(tmp_path, penalties=False)
    script(rig, Draws())
    assert rig.rules.before_snap(rig.engine.s, 1, 2) == GO_ON and rig.rules.instead_of_sack(rig.engine.s) is None
    assert rig.rnd.trace == []
    assert rig.rules.extra_stats_lines(rig.engine.s)[0] == X.text("NXS-03")
    assert X.text("NXH-09") not in rig.rules.extra_help("116")


def test_a_switched_off_foul_is_never_drawn_and_a_weight_of_200_doubles_it(tmp_path):
    from nfl4.extras.penalty_list import FoulTable
    rig = game(tmp_path)
    snap(rig)
    holding = F.BY_ID["P08"][0]
    base = rig.rules.penalty.weight(holding, 1, 1)
    rig.game.foul_table = FoulTable({}, {"P08": 0})
    assert rig.rules.penalty.weight(holding, 1, 1) == 0
    assert all(f.id != "P08" for f, _ in rig.rules.penalty._weighted(rows(rig, O.RUN), 1, 1))
    rig.game.foul_table = FoulTable({"P08": "hold"}, {"P08": 200})
    assert rig.rules.penalty.weight(holding, 1, 1) == 2 * base
    assert rig.rules.penalty.table().name("P08") == "hold"


# ----- grounding in place of a sack (design 9.2 P15) -----

def test_grounding_replaces_the_sack_and_the_computer_takes_the_loss_of_down(tmp_path):
    rig = game(tmp_path, down=2, to_go=10)
    snap(rig)
    script(rig, Draws().below(10000, 0))
    away = rig.rules.instead_of_sack(rig.engine.s)
    assert away == X.text("NXP-21", quarterback="Starr")
    step = rig.engine.thrown_away(away)
    s = rig.engine.s
    assert step == rig.engine.end_of_play and s.tackle_sentence == away and s.result_kind == O.PASS_INCOMPLETE
    assert rig.engine.end_of_play() == rig.engine.field_play_end
    draws = Draws().below(5, 2).rnd(40, 2).below(5, 0)             # the passer 7 yards back, no second, L = 3
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert " intentional grounding, on the Bengals, Starr. " in said and X.text("NXP-10") in said
    assert step == rig.engine.position and (s.yard_line, s.down, s.to_go) == (20, 3, 20)


def test_an_offside_waiting_from_the_snap_and_grounding_offset(tmp_path):
    rig = game(tmp_path, down=2, to_go=10)
    snap(rig)
    rig.rules.penalty.waiting = PF.Flag(F.BY_ID["P03"][0], 2, 3)
    script(rig, Draws().below(10000, 0))
    rig.engine.thrown_away(rig.rules.instead_of_sack(rig.engine.s))
    rig.engine.end_of_play()
    draws = Draws().below(5, 2).below(5, 0)                         # the passer's spot, then L: no third draw
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert " off sides, on the Jets, ODef3. " in said and " intentional grounding, on the Bengals, Starr. " in said
    assert X.text("NXP-08") in said
    s = rig.engine.s
    assert step == rig.engine.position and (s.yard_line, s.down, s.to_go) == (30, 2, 10)


def test_grounding_is_rare_and_never_happens_with_penalties_off(tmp_path):
    rig = game(tmp_path)
    script(rig, Draws().below(10000, 9999))
    assert rig.rules.instead_of_sack(rig.engine.s) is None
    assert T.GROUNDING_PER_10000_SACKS * T.PENALTY_RATE_SCALE < 1000


# ----- the last play of a half (4-8-2 (a)) and the ten-second run off (4-7-1) -----

def test_an_accepted_defense_foul_on_the_last_play_of_the_half_gives_an_untimed_down(tmp_path):
    rig = game(tmp_path, answers=[ENTER], quarter=2, extras=dict(left=4, period=2, warning_given=True))
    snap(rig)
    play_ended(rig)
    value = value_of(rig, rows(rig, O.PASS_INCOMPLETE), "P09", offense_play=4)
    draws = Draws().below(10000, value).rnd(17, 4).rnd(40, 2).below(5, 2)    # L = 5 runs the clock out
    script(rig, draws)
    rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert any(t.endswith(", " + X.text("NXP-S09") + ". ") for t in said)
    assert any(t.endswith(", " + X.text("NXP-S08") + ". ") for t in said)
    assert X.text("NXP-14") in said
    x, clock = rig.engine.s.extras, rig.engine.clock
    assert x.left == 0 and x.extension and not clock.period_over()
    assert clock.before_snap() is False and not x.extension and clock.period_over()


def test_a_false_start_after_the_warning_with_the_clock_running_offers_the_run_off(tmp_path):
    rig = game(tmp_path, answers=[ENTER], quarter=4, wisoff=2, defense=1, half=1, yard_line=40, offense_play=1,
               defense_play=2, extras=dict(left=100, period=4, warning_given=True, running=True, pending=30))
    s = rig.engine.s
    dead = [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]
    draws = Draws().below(10000, value_of(rig, dead, "P01")).rnd(12, 1).rnd(4, 1).rnd(10, 1)
    script(rig, draws)
    step = rig.engine.snap()
    check(rig, draws)
    said = texts(rig)
    i = said.index(X.text("NXP-17", n=60))                            # 70 left: 60 after the run off (review, D-050)
    assert said[i - 1].startswith(" Kim if you accept the penalty, it will be first and 15 on my 35 yard line")
    assert said[i + 1] == " if you decline it, it will be first and 10 on my 40 yard line. "
    assert said[i + 2:i + 4] == [X.text("NXP-A03"), X.text("NXP-12")]     # the player's side is tied: the run off
    assert s.extras.left == 60 and s.extras.foul_clock == "runoff"
    assert step == rig.engine.position and s.yard_line == 35 and s.half == 1


def test_the_run_off_that_takes_the_last_seconds_ends_the_period(tmp_path):
    rig = game(tmp_path, quarter=2, wisoff=1, defense=2, offense_play=1, defense_play=2,
               extras=dict(left=38, period=2, warning_given=True, running=True, pending=30))
    rig.engine.s.stats[2].score = 3                                  # the computer's defense leads: the run off
    dead = [f for f in F.FOULS if F.DEAD in f.phases or F.SNAP in f.phases]
    draws = Draws().below(10000, value_of(rig, dead, "P01")).rnd(12, 1).rnd(4, 1).rnd(10, 1)
    script(rig, draws)
    step = rig.engine.snap()
    check(rig, draws)
    assert step == rig.engine.period_checks and rig.engine.s.extras.left == 0
    assert X.text("NXP-12") in texts(rig)


# ----- two fouls, the try, the kick-off -----

def test_fouls_by_both_teams_offset_and_the_down_is_played_again(tmp_path):
    rig = game(tmp_path, down=2, to_go=6)
    snap(rig)
    rig.engine.s.stats[1].completions += 1
    play_ended(rig, O.PASS_COMPLETE, yards=15)
    run_rows = rows(rig, O.PASS_COMPLETE)
    first = value_of(rig, run_rows, "P08", offense_play=4)
    others = [f for f in run_rows if f.offender == F.DEFENSE]
    second = value_of(rig, others, "P09", offense_play=4)
    total = sum(w for _, w in rig.rules.penalty._weighted(others, 4, 1))
    draws = (Draws().below(100, 50).below(10000, first).rnd(12, 1).rnd(40, 1).below(total, second).rnd(17, 2)
             .below(4, 0))
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    said = texts(rig)
    assert " holding, on the Bengals, Back1. " in said and " defensive holding, on the Jets, ODef2. " in said
    assert X.text("NXP-08") in said
    s = rig.engine.s
    assert step == rig.engine.position and (s.yard_line, s.down, s.to_go) == (30, 2, 6)
    assert s.stats[1].completions == 0 and s.extras.flags == [0, 0]


def test_a_personal_foul_on_a_touchdown_is_enforced_on_the_try(tmp_path):
    rig = game(tmp_path, half=1, yard_line=5)
    snap(rig)
    s = rig.engine.s
    s.result_kind, s.offense_play, s.defense_play, s.yards = O.RUN, 1, 2, 5
    value = value_of(rig, rows(rig, O.RUN, after=False), "P20")
    draws = Draws().below(10000, value).rnd(17, 5).rnd(40, 2).below(4, 0).celebration(8).rady(0)
    script(rig, draws)
    step = rig.engine.touchdown_reached()
    check(rig, draws)
    assert X.text("NXP-16") in texts(rig) and P.TOUCH_DOWN in texts(rig)
    assert rig.rules.penalty.try_from_the_one and step == rig.engine.extra_point_choice
    s.two_point, s.yard_line = True, 2
    rig.rules.offense_menu(s, True)
    assert s.yard_line == 1 and not rig.rules.penalty.try_from_the_one


def test_offside_on_the_kick_off_gives_the_receivers_five_more_yards(tmp_path):
    rig = game(tmp_path, answers=[ENTER], wisoff=1, defense=2, half=2, yard_line=0)
    s = rig.engine.s
    assert rig.rules.before_kickoff(s, 2) == "normal"
    value = value_of(rig, rows(rig, O.KICKOFF_TOUCH_BACK, after=False), "P24")
    draws = Draws().below(10000, value).rnd(17, 6).rnd(40, 2)
    script(rig, draws)
    step = rig.engine.touch_back()
    check(rig, draws)
    said = texts(rig)
    assert " off sides on the kick off, on the Jets, ODef6. " in said
    assert " Kim if you accept the penalty, it will be first and 10 on your 25 yard line. " in said
    assert step == rig.engine.position and (s.half, s.yard_line, s.down, s.to_go) == (2, 25, 1, 10)


# ----- the statistics, the help, the clock after a foul -----

def test_the_statistics_add_the_penalties_and_their_yards(tmp_path):
    rig = game(tmp_path, extras=dict(flags=[2, 3], flag_yards=[15, 25]))
    lines = rig.rules.extra_stats_lines(rig.engine.s)
    assert lines[:6] == [X.text("NXS-01"), "Bengals 2", "Jets 3", X.text("NXS-02"), "Bengals 15", "Jets 25"]
    assert lines[6] == X.text("NXS-03")


def test_the_help_of_f5_f6_and_f7_names_the_penalties_when_they_are_on(tmp_path):
    rig = game(tmp_path)
    assert X.text("NXH-09") in rig.rules.extra_help("116")
    from nflrig import feature_help
    assert [X.text("NXH-10"), X.text("NXH-11")] == feature_help(rig.rules, "117")[-2:]
    assert [X.text("NXH-12"), X.text("NXH-13")] == feature_help(rig.rules, "118")[-2:]


@pytest.mark.parametrize("clock, quarter, left, offense, keeps, expected", [
    ("live", 1, 600, False, True, (True, True)),       # as if no foul, the ready signal
    ("live", 1, 600, False, False, (False, False)),
    ("live", 2, 100, False, True, (False, False)),     # after the first half's warning: on the snap
    ("live", 4, 290, False, True, (False, False)),     # the last five minutes of the second half
    ("pre", 3, 600, True, False, (True, True)),        # before the snap with the clock running: running again
    ("pre", 4, 600, True, False, (False, False)),      # an offense foul before the snap in the fourth quarter
    ("pre", 4, 600, False, False, (True, True)),
    ("runoff", 4, 60, True, False, (True, True)),      # after the run off: the ready signal
    ("runoff", 4, 0, True, False, (False, True)),
])
def test_the_clock_after_a_foul(clock, quarter, left, offense, keeps, expected):
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord(left=left, foul_clock=clock, foul_by_offense=offense, was_running=True)
    assert PF.clock_after_foul(record, quarter, keeps) == expected


def test_the_record_with_penalties_is_checked_whole(tmp_path):
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord(penalties_on=True, flags=[3, 1], flag_yards=[20, 5], foul_clock="live")
    assert ExtrasRecord.from_json(record.to_json()) == record
    for bad in (dict(flags=[1]), dict(flag_yards=[1, -1]), dict(foul_clock="later"), dict(extension=1)):
        broken = ExtrasRecord(**bad)
        with pytest.raises(ValueError):
            broken.check()


def test_a_classic_game_never_reaches_the_penalties(tmp_path):
    from nfl4.game.rules import CLASSIC
    assert CLASSIC.before_snap(None, 1, 1) == GO_ON and CLASSIC.instead_of_sack(None) is None
    with pytest.raises(RuntimeError):
        CLASSIC.foul_before_snap(None)
    assert FOUL_BEFORE_SNAP != GO_ON and NEXT_DOWN
