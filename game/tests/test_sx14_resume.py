"""SX.14 (CLAUDE.md 0.23, playbook 7.17, NX-S4): the automatic save. This is inspired by Jim Kitchen.

A game is written to the automatic save at every safe point (the play menu), whole, without a draw and without a word; a game killed at any
of those points and started again from the file goes on to the SAME result as the game that was never interrupted (the same plays, the same
statistics, the same final score and the same number of draws), in Classic and with the N. F. L. rules. The kill is a BaseException raised
by the sink right after it kept the record, which is what a process that is gone does to the engine; the second game is a new rig, a new
Game and a new random generator that knows nothing of the first one.
"""
import json
import random

import pytest

from nfl4.data.files import savedgame
from nfl4.game import resume
from nfl4.game.rules import CLASSIC
from nflrig import SimEngine, RecordingRules, QUARTERBACKS
from pagrig import make_rig


class Killed(BaseException):
    """The process is gone."""


def new_rules(kind):
    if kind == "classic":
        return CLASSIC
    return RecordingRules(penalties_on=True, onside_on=True, qb_on=True, playbooks_on=True,
                          offense_book="west_coast", defense_book="pressure")


def run_game(tmp_path, seed, kind, saved=None, sink=None, rng_seed=None):
    rig = make_rig(tmp_path, rng=random.Random(seed if rng_seed is None else rng_seed), fast=True, vtrnt=2)
    engine = SimEngine(rig.game, new_rules(kind), quarterback_names=lambda state: QUARTERBACKS, saved=saved, autosave_sink=sink)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, engine, result


def fingerprint(rig, engine, result):
    s = engine.s
    return {"scores": result.scores, "stats": s.stats, "draws": rig.rnd.draws, "quarter": s.quarter, "counter": s.counter,
            "kinds": [o.kind for o in engine.outcomes], "yards": [o.yards for o in engine.outcomes]}


def kept_through_the_file(records):
    """The sink: every record goes through the file format and back, as it would on the disk."""
    def sink(record):
        records.append(savedgame.decode(savedgame.encode(record)))
        return True
    return sink


@pytest.mark.parametrize("kind", ["classic", "nfl"])
def test_the_automatic_save_changes_no_draw_and_no_result(tmp_path, kind):
    plain = run_game(tmp_path / "a", 5, kind)
    records = []
    watched = run_game(tmp_path / "b", 5, kind, sink=kept_through_the_file(records))
    assert fingerprint(*plain) == fingerprint(*watched)
    assert len(records) >= plain[1].s.quarter * 10                             # about every play: a safe point is the play menu


def test_an_automatic_save_is_the_game_file_with_the_summary_and_the_resume_sections(tmp_path):
    records = []
    run_game(tmp_path, 2, "classic", sink=kept_through_the_file(records))
    record = records[len(records) // 2]
    info = json.loads(record.info)
    assert info["own"] == "Bengals" and info["opp"] == "Jets" and info["week"] == 1 and info["kind"] == "classic"
    assert isinstance(info["lm"], int) and info["ls"] is None
    assert json.loads(record.resume)["v"] == resume.FORMAT and record.stats[1].score >= 0


@pytest.mark.parametrize("kind", ["classic", "nfl"])
@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_a_game_killed_at_a_play_and_started_again_ends_as_the_unbroken_game_does(tmp_path, kind, seed):
    records = []
    whole = run_game(tmp_path / "whole", seed, kind, sink=kept_through_the_file(records))
    expected = fingerprint(*whole)
    count = len(records)
    assert count > 20
    for number in (3, count // 4, count // 2, count - 3):
        kept = []

        def killing(record, number=number, kept=kept):
            kept.append(savedgame.decode(savedgame.encode(record)))
            if len(kept) == number:
                raise Killed()
            return True
        with pytest.raises(Killed):
            run_game(tmp_path / ("killed%d" % number), seed, kind, sink=killing)
        again = run_game(tmp_path / ("again%d" % number), seed, kind, saved=kept[-1], rng_seed=987654)      # another generator: the file brings its own
        tail = len(again[1].outcomes)
        assert fingerprint(*again)["scores"] == expected["scores"], (kind, seed, number)
        assert again[1].s.stats == whole[1].s.stats and again[0].rnd.draws == expected["draws"], (kind, seed, number)
        assert [o.kind for o in again[1].outcomes] == expected["kinds"][-tail:], (kind, seed, number)
        assert [o.yards for o in again[1].outcomes] == expected["yards"][-tail:], (kind, seed, number)


def test_a_resume_part_that_cannot_be_used_leaves_the_game_to_go_on_from_the_saved_board(tmp_path):
    records = []
    run_game(tmp_path / "a", 3, "classic", sink=kept_through_the_file(records))
    record = records[10]
    for bad in ("not json", "[]", '{"v":2}', '{"v":1,"state":{"zzz":1},"clock":{},"rng":{}}', '{"v":1,"state":{"__class__":"os"}}'):
        record.resume = bad
        rig, engine, result = run_game(tmp_path / ("b%d" % len(bad)), 3, "classic", saved=record, rng_seed=5)
        assert result.scores is not None                                 # the game was played to its end from the board
    # a class that is not one of the four kept by an automatic save is refused, never built
    with pytest.raises(resume.ResumeError):
        resume.from_plain({"__class__": "Popen", "fields": {}})


def test_the_state_goes_to_plain_text_and_back_with_tuples_and_any_keys(tmp_path):
    from nfl4.game.phrases import GroupedPhrases, PhraseHistory
    from nfl4.game.setup import Roster
    value = {1: [PhraseHistory(4), (1, 2)], ("a", 3): Roster(["x"], [], [], [], [], quarterback="q", ratings={("Running Backs:", 1): 80}),
             "g": GroupedPhrases(4, 9, "hand-off")}
    value[1][0].enter(3)
    back = resume.from_plain(json.loads(json.dumps(resume.to_plain(value))))
    assert back[1][0].values == value[1][0].values and back[1][1] == (1, 2)
    assert back[("a", 3)].ratings == {("Running Backs:", 1): 80}
    assert back["g"].history.values == value["g"].history.values and back["g"].memory is None
    with pytest.raises(resume.ResumeError):
        resume.to_plain(object())


def test_a_franchise_rosters_ratings_fit_in_the_resume_part_and_a_too_large_one_is_left_out(tmp_path):
    from nfl4.game.setup import Roster
    rig = make_rig(tmp_path, rng=random.Random(1), fast=True, vtrnt=2)
    engine = SimEngine(rig.game, new_rules("classic"), quarterback_names=lambda state: QUARTERBACKS)
    ratings = {("Running Backs:", n): 70 + n for n in range(1, 7)} | {("Receivers:", n): 60 + n for n in range(1, 7)}
    engine.s.rosters = {1: Roster(["a"] * 6, ["b"] * 6, ["c"] * 17, ["d"] * 2, ["e"] * 2, quarterback="Q", ratings=ratings),
                        2: Roster(["a"] * 6, ["b"] * 6, ["c"] * 17, ["d"] * 2, ["e"] * 2, quarterback="Q", ratings=dict(ratings))}
    assert len(resume.capture(engine).encode()) < resume.LIMIT_BYTES
    assert engine.save_record(auto=True).resume is not None
    engine.s.player_names = ["x" * 100] * 700                                    # far more than the file can hold
    assert engine.save_record(auto=True).resume is None
