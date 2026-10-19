"""football.sav with every state of the extras saved and loaded (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 12.3, NFL_EXTRA_FEATURES C1 and
C10; PX SX.9, the stress tests of S8.3 with the extras). This is inspired by Jim Kitchen.

* A record with every field away from its start value (the franchise mark, a game's injuries, a kept penalty choice, the remarks, the
  playbooks, overtime) goes through the file and back whole, and into a loaded game's state.
* Every field of the record given a value of the wrong kind is refused whole (the start values and one notice, C10, are the caller's).
* Whole games with every switch on are saved at every H10 (between two plays) and each save is read back: the loaded record is the
  game's record; from some of them the game is loaded and played to its end by the computer's rules.
"""
import random
from dataclasses import fields

import pytest

from nfl4.data.files import savedgame
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.state import ExtrasRecord
from nfl4.game.gamestate import GameState
from nflrig import RecordingRules, SimEngine, sim_game
from pagrig import make_rig
from test_nx_pending_save import saved_at_the_prompt
from test_nx_save import a_save

QUARTERBACKS = ("Starr", "Unitas")


def every_field(tmp_path):
    pending = saved_at_the_prompt(tmp_path)[0].engine.s.extras.pending_choice
    return ExtrasRecord(
        timeouts_on=False, postseason=True, period=6, left=412, pending=14, running=True, warning_due=True, warning_given=True,
        plays=150, handled=149, last_kind="run", last_offense=2, last_two_point=True, out_of_bounds=True, unit="OTP1", announced="OTP1",
        timeouts=[2, 1], used=[5, 4], called=[True, False], recent={"TO": ["TO01", "TO03"], "PN": ["PN02"], "QB": ["QB01", "QB02", "QB05"]},
        penalties_on=True, flags=[6, 7], flag_yards=[45, 70], foul_clock="live", foul_by_offense=True, was_running=True, extension=True,
        extension_snap=True, no_snap=True, onside_on=True, onside_always=True, onside_tried=[1, 2], onside_recovered=[0, 1],
        kick_kind="onside", kick_again=True, rekick=True, kick_back=10, kick_from=25, safety_kick=True, qb_on=True, qb_runs=[4, 9],
        qb_yards=[-3, 51], challenges_on=True, chal_used=[3, 1], chal_won=[2, 0], offense_book=["air", "option"],
        defense_book=["pressure", "zone"], franchise={"league": "20261019-120000", "season": 4, "week": 18},
        injuries={"hurt": [[1012, "IJE", 3, 1]], "stand_ins": [[4, "QB", "Smith", 55]], "carries": {"1013": 77}},
        pending_choice=pending)


def test_a_record_with_every_field_away_from_its_start_goes_through_the_file_and_into_a_game(tmp_path):
    record = every_field(tmp_path)
    record.check()
    start = ExtrasRecord()
    assert all(getattr(record, f.name) != getattr(start, f.name) for f in fields(ExtrasRecord) if f.name != "rules_year")
    saved = savedgame.decode(savedgame.encode(a_save(quarter=5, extras=record.to_json(), extras_marked=True)))
    assert ExtrasRecord.from_json(saved.extras) == record
    state = GameState()
    NflRules().period_clock(make_rig(tmp_path / "g").game, state)
    state.load(saved)
    assert state.extras == record and state.overtime == 2


@pytest.mark.parametrize("name", [f.name for f in fields(ExtrasRecord)])
def test_every_field_with_a_value_of_the_wrong_kind_refuses_the_record(tmp_path, name):
    record = every_field(tmp_path)
    setattr(record, name, {"bad": [1]})
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(record.to_json())


class SavingRules(RecordingRules):
    """Every switch on; the game's record saved and read back at every H10."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.saves = []

    def between_plays(self, state):
        then = super().between_plays(state)
        raw = savedgame.encode(state.saved(100.0))
        back = savedgame.decode(raw)
        assert back.extras_marked and ExtrasRecord.from_json(back.extras) == state.extras
        self.saves.append(raw)
        return then


def all_on():
    return SavingRules(penalties_on=True, onside_on=True, onside_always=True, qb_on=True, challenges_on=True, offense_book="team",
                       defense_book="team", playbooks_on=True)


@pytest.mark.parametrize("seed", range(3))
def test_whole_games_saved_at_every_wait_read_back_whole_and_a_loaded_game_plays_to_its_end(tmp_path, seed):
    rig, engine, rules, result = sim_game(tmp_path / "a", 620 + seed, rules=all_on())
    assert result.scores is not None and len(rules.saves) > 100
    rng = random.Random(seed)
    for number, raw in enumerate(rng.sample(rules.saves, 4)):
        saved = savedgame.decode(raw)
        play = make_rig(tmp_path / ("b%d" % number), rng=random.Random(number), fast=True, vtrnt=2)
        loaded = SimEngine(play.game, all_on(), quarterback_names=lambda state: QUARTERBACKS, saved=saved)
        play.game.play_engine = loaded
        try:
            again = loaded.run()
        finally:
            play.game.play_engine = None
        assert again.scores is not None and again.scores[0] != again.scores[1]
        loaded.s.extras.check()
        assert play.rnd.fallbacks == 0
