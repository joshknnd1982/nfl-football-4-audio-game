"""A catalog play told in the game (nfl4 only, rule 0.13; NX-P3, NX-P7, NX-R7 G26-8, G26-9, G26-10, G26-12; NFL_PLAYS_DESIGN 7; PX SX.10c,
D-093). This is inspired by Jim Kitchen.

The outcome model's result is forced (model.play is replaced by one result) and the engine runs from the snap on a seeded source: the
original's sentence pools tell it (the hand-off, run and tackle sentences of the entry whose range holds the yards; the drop-back, throw,
catch, incompletion, interception and sack sentences), the new sentences are the text rows, the ball, the statistics, the turnover's
return and the defense's touchdown are checked against the numbers worked out here (B-X38).
"""
import random

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import offense_flow as OF
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model as M
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.pag_catalog import run_entry
from nfl4.game.playtables import RUNS
from nflrig import nfl_engine_rig

START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
UNTIL = ("next_play", "kick_off", "extra_point_choice", "extra_point", "score", "offense_menu", "play_menu", "game_end")


def rig_for(tmp_path, play, result, monkeypatch, qb_on=False, defense_play=2, extras=None, **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=True, qb_on=qb_on, offense_book="west", defense_book="classic")
    rig = nfl_engine_rig(tmp_path, rules=rules, extras=extras, **fields)
    monkeypatch.setattr(M, "play", lambda concept, call, situation, rnd: result)
    s = rig.engine.s
    rules.offense.called = play
    s.offense_play = OF.engine_family(C.BY_ID[play])
    s.defense_play = defense_play
    rig.rnd.source = random.Random(11)
    return rig


def run_play(rig):
    step = rig.engine.snap
    while step is not None and step.__name__ not in UNTIL:
        step = step()
    return step.__name__ if step is not None else None


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def joined(rig, start=0):
    return " ".join(texts(rig, start))


# ----- runs -----

def test_the_run_sentences_are_the_original_entrys_whose_range_holds_the_yards():
    assert run_entry(1, 2, 3) is RUNS[(1, 2)]                       # the defense's own entry holds 3 (-1 to 4)
    assert run_entry(1, 2, 6) is RUNS[(1, 3)]                       # it does not hold 6: the first that does (0 to 6)
    assert run_entry(1, 6, 45) is RUNS[(1, 6)]                      # none holds 45: the nearest range (11 to 29)
    assert run_entry(2, 2, -3) is RUNS[(2, 2)] and run_entry(2, 1, -9) is RUNS[(2, 3)]


def test_a_catalog_run_is_told_with_the_originals_pools_and_moves_the_ball(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O001", M.Result("run", 6, gap="guard"), monkeypatch)
    mark = len(rig.said)
    assert run_play(rig) == "next_play"
    s = rig.engine.s
    said = joined(rig, mark)
    assert P.RUNS_THROUGH_A_HOLE in said and (P.GAIN + "6" + P.YARD + P.PLURAL + P.ON_THE_PLAY) in said
    assert any(phrase in said for _he, phrase in P.HANDOFF_PHRASES)
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 36, 2, 4)
    assert s.stats[1].running_plays == 1 and s.stats[1].running_yards == 6
    assert rig.engine.outcomes[-1].catalog == "O001" and rig.engine.outcomes[-1].kind == O.RUN


def test_an_end_run_long_gain_scores_with_the_originals_countdown(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O009", M.Result("run", 70, gap="end"), monkeypatch)
    mark = len(rig.said)
    assert run_play(rig) == "extra_point_choice"
    said = texts(rig, mark)
    assert P.TOUCH_DOWN in said and P.HE_IS_AT_THE in said and rig.engine.s.stats[1].score == 6


def test_a_pitch_is_its_own_sentence_then_the_end_run(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O015", M.Result("run", 4, gap="end", branch="pitch"), monkeypatch)
    mark = len(rig.said)
    run_play(rig)
    s = rig.engine.s
    rb = s.rosters[1].running_backs[s.carrier - 1]
    assert X.text("NXB-H04", quarterback="Starr", player=rb) in texts(rig, mark)


def test_the_last_plays_laterals_have_their_sentence(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O156", M.Result("run", 12, gap="laterals"), monkeypatch)
    mark = len(rig.said)
    run_play(rig)
    assert X.text("NXB-H06") in texts(rig, mark)


def test_an_option_keep_is_the_quarterbacks_run_and_a_sneak_its_pile(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O049", M.Result("run", 5, gap="qb", branch="keep"), monkeypatch, qb_on=True)
    mark = len(rig.said)
    run_play(rig)
    said = joined(rig, mark)
    assert X.text("NXB-H05", quarterback="Starr") in said and rig.engine.outcomes[-1].qb_run == "keeper"
    rig = rig_for(tmp_path / "sneak", "O046", M.Result("run", 1, gap="qb"), monkeypatch, qb_on=True)
    mark = len(rig.said)
    run_play(rig)
    assert X.text("NXQ-03", quarterback="Starr") in texts(rig, mark) and rig.engine.outcomes[-1].qb_run == "sneak"


# ----- passes -----

def test_a_catalog_catch_is_told_with_the_throw_and_catch_pools(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("complete", 12, "slant", 3, 8), monkeypatch)
    mark = len(rig.said)
    assert run_play(rig) == "next_play"
    s = rig.engine.s
    said = joined(rig, mark)
    assert any(p in said for p in P.THROW_PHRASES) and any(p in said for p in P.CATCH_PHRASES)
    assert s.stats[1].completions == 1 and s.stats[1].pass_attempts == 1 and s.stats[1].passing_yards == 12
    assert (s.yard_line, s.down) == (42, 1)


def test_an_incompletion_is_the_originals_and_a_throw_away_is_its_sentence(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("incomplete", 0, "slant", 3, 8), monkeypatch)
    run_play(rig)
    assert rig.engine.outcomes[-1].kind == O.PASS_INCOMPLETE and rig.engine.s.down == 2
    rig = rig_for(tmp_path / "away", "O017", M.Result("incomplete", 0, branch="thrown_away"), monkeypatch)
    mark = len(rig.said)
    run_play(rig)
    assert X.text("NXB-H03", quarterback="Starr") in texts(rig, mark)


def test_a_sack_is_the_originals_sentences_with_the_models_loss(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("sack", -7), monkeypatch)
    run_play(rig)
    s = rig.engine.s
    assert rig.engine.outcomes[-1].kind == O.SACK and s.yard_line == 23 and s.stats[1].sacked == 1 and s.stats[1].passing_yards == -7


def test_a_sack_becomes_a_scramble_where_the_quarterback_runs_and_the_models_result_is_dropped(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("sack", -7), monkeypatch, qb_on=True)
    flow = rig.rules.offense
    monkeypatch.setattr(rig.rules.qb, "scramble_from_sack", lambda state: True)
    run_play(rig)
    assert rig.engine.outcomes[-1].qb_run == "scramble" and flow.result is None


# ----- the clock plays -----

def test_the_kneel_takes_a_knee_loses_a_yard_and_uses_a_second_or_two(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O152", M.Result("kneel", -1), monkeypatch, quarter=4, extras=dict(left=100))
    mark = len(rig.said)
    run_play(rig)
    s = rig.engine.s
    assert X.text("NXB-H01", quarterback="Starr") in texts(rig, mark)
    assert s.yard_line == 29 and rig.engine.outcomes[-1].catalog == "O152"
    assert 98 <= s.extras.left + s.extras.pending <= 99 or 98 <= s.extras.left <= 99


def test_a_kneel_on_the_own_one_never_goes_into_the_end_zone(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O152", M.Result("kneel", -1), monkeypatch, yard_line=1)
    run_play(rig)
    assert rig.engine.s.yard_line == 1 and rig.engine.outcomes[-1].kind == O.RUN


def test_the_spike_stops_the_clock_with_an_incompletion(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O153", M.Result("spike", 0), monkeypatch, quarter=2, extras=dict(left=50, running=True))
    mark = len(rig.said)
    run_play(rig)
    s = rig.engine.s
    assert X.text("NXB-H02", quarterback="Starr") in texts(rig, mark)
    assert rig.engine.outcomes[-1].kind == O.PASS_INCOMPLETE and s.extras.left == 49 and not s.extras.running
    assert s.stats[1].pass_attempts == 1 and s.down == 2


# ----- turnovers -----

def test_an_interception_is_returned_from_where_it_was_caught(tmp_path, monkeypatch):
    # the line of scrimmage is the player's 30: caught 15 yards on, at the 45, the Jets run it back 23 to the player's 22
    rig = rig_for(tmp_path, "O017", M.Result("interception", 15, "slant", 3, 15, return_yards=23), monkeypatch)
    mark = len(rig.said)
    run_play(rig)
    s = rig.engine.s
    d1 = s.rosters[2].defense[s.defender1 - 1]
    assert X.text("NXB-H08", player=d1, n=23) in texts(rig, mark)
    assert (s.wisoff, s.half, s.yard_line) == (2, 2, 22)


def test_an_interception_run_back_all_the_way_is_the_defenses_touchdown(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("interception", 15, "slant", 3, 15, return_touchdown=True), monkeypatch)
    mark = len(rig.said)
    assert run_play(rig) == "extra_point"                 # the computer always kicks
    s = rig.engine.s
    said = texts(rig, mark)
    assert P.TOUCH_DOWN in said and s.stats[2].score == 6 and s.wisoff == 2
    assert rig.engine.outcomes[-1].score == "return touchdown"


def test_an_interception_in_the_end_zone_is_a_touch_back(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("interception", 75, "go", 6, 75), monkeypatch)
    run_play(rig)
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line) == (2, 1, 20)


def test_a_lost_fumble_is_at_its_spot_and_a_kept_one_is_the_offenses(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O001", M.Result("fumble", 4, gap="guard", fumble_lost=True), monkeypatch)
    run_play(rig)
    s = rig.engine.s
    assert (s.wisoff, s.half, s.yard_line) == (2, 2, 34) and s.stats[1].fumbles_lost == 1
    rig = rig_for(tmp_path / "kept", "O001", M.Result("fumble", 4, gap="guard"), monkeypatch)
    mark = len(rig.said)
    run_play(rig)
    s = rig.engine.s
    assert X.text("NXB-H07", team="Bengals") in joined(rig, mark)
    assert (s.wisoff, s.yard_line, s.down) == (1, 34, 2) and s.stats[1].fumbles_lost == 0


def test_a_try_run_back_by_the_defense_gives_it_two_points(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O017", M.Result("interception", 3, "slant", 1, 3, return_touchdown=True), monkeypatch,
                  two_point=True, yard_line=2, half=1)
    rig.engine.s.stats[1].score = 6
    mark = len(rig.said)
    run_play(rig)
    s = rig.engine.s
    assert X.text("NXB-H10") in texts(rig, mark) and s.stats[2].score == 2 and s.stats[1].score == 6


def test_the_models_out_of_bounds_flag_is_the_clocks(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O001", M.Result("run", 6, gap="end", out_of_bounds=True), monkeypatch)
    mark = len(rig.said)
    run_play(rig)
    assert rig.engine.s.extras.out_of_bounds and X.text("NXC-04") in texts(rig, mark)
    rig = rig_for(tmp_path / "in", "O001", M.Result("run", 6, gap="end"), monkeypatch)
    run_play(rig)
    assert not rig.engine.s.extras.out_of_bounds


def test_a_computers_play_and_a_play_of_the_originals_menu_never_use_the_model(tmp_path, monkeypatch):
    rig = rig_for(tmp_path, "O001", M.Result("run", 6, gap="guard"), monkeypatch)
    rig.rules.offense.called = ""
    s = rig.engine.s
    assert rig.rules.model_play(s) is None
    rig.rules.offense.called = "O001"
    s.wisoff, s.defense = 2, 1
    assert rig.rules.model_play(s) is None


@pytest.mark.parametrize("seed", range(6))
def test_the_real_model_through_the_engine_ends_every_kind_of_play(tmp_path, seed):
    """No forced result: the real model for a play of each kind, on seeded sources: the play ends where the original's plays end."""
    kinds = ("run", "pass", "screen", "play_action", "option", "rpo", "trick_pass", "hail_mary", "laterals", "qb_run", "sneak")
    for kind in kinds:
        concept = next(c for c in C.OFFENSE if c.kind == kind)
        rules = NflRules(timeouts_on=True, qb_on=True, offense_book="west", defense_book="classic")
        rig = nfl_engine_rig(tmp_path / ("%s%d" % (kind, seed)), rules=rules, **START)
        rules.offense.called = concept.id
        rig.engine.s.offense_play = OF.engine_family(concept)
        rig.engine.s.defense_play = 1 + seed % 6
        rig.rnd.source = random.Random(seed * 31 + len(kind))
        assert run_play(rig) in UNTIL, kind
        assert rig.engine.outcomes and rig.engine.outcomes[0].catalog == concept.id
