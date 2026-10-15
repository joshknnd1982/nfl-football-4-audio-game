"""A rig for the whole program: start-up, week loop, main menu, exit. This is inspired by Jim Kitchen.

The Game with the real sound layer on the virtual clock (tests/gamerig.py), keys that answer with a policy when the script is
used up (tests/pagrig.py), a `RigStore` for the files (game/program_store.py) and a stand-in for pag whose outcomes the test
scripts: `outcomes` is a list consumed one per game, each an `Outcome` or a function(rig) that returns one.

* `ready_season(...)` fills the Game's SeasonState as a loaded season: the coach, the team, the schedule (a real one from the
  game's own `makes`, or the one given), the week, the records.
* `rig.plays` has the arguments pag was called with; `rig.said` the speech; `rig.slot_log` the sounds.
"""
import random
from dataclasses import dataclass

from gamerig import Rig
from nfl4.game.pag import GameResult
from nfl4.game.program_store import MemoryProgramStore
from pagrig import PolicyKeys, enter_policy

ENTER, ESC, UP, DOWN, F1, F5, F9 = 13, 27, 38, 40, 112, 116, 120


class RigStore(MemoryProgramStore):
    """MemoryProgramStore whose load_season applies `preset(season)` (None: no season, a new one is set up)."""

    def __init__(self, first=False, preset=None):
        super().__init__(first)
        self.preset = preset
        self.calls = []

    def load_season(self, season):
        self.calls.append("load_season")
        if self.preset is None:
            return False
        self.preset(season)
        return True

    def delete_season_files(self):
        self.calls.append("delete_season_files")
        super().delete_season_files()

    def open_log(self, fresh):
        self.calls.append(("open_log", fresh))
        super().open_log(fresh)


@dataclass
class Outcome:
    """What the stand-in pag returns and does: a result, and whether it stops the crowd beds as pag does at its end."""
    result: GameResult
    stop_beds: bool = True
    gtp: int | None = None            # the week counter pag leaves (a Super Bowl game: 0)


def played(own=24, opponent=17) -> Outcome:
    return Outcome(GameResult(scores=(own, opponent)))


def saved_game() -> Outcome:
    return Outcome(GameResult(scores=None, saved=True), stop_beds=False)


def preset_season(coach="Kim", team=(1, 1), gtp=1, seed=5, records=None):
    """A season loaded from the files: the schedule is the one `makes` draws with a seeded source."""
    def apply(season):
        from nfl4.game.rnd import GameRandom
        season.coach = coach
        season.choose_team(*team)
        season.make_schedule(GameRandom(random.Random(seed)))
        season.gtp = gtp
        if records is not None:
            records(season.records)
    return apply


def advance_week(rig):
    """What pog leaves in a regular week: the week counter one higher (the games and the files are the engine's)."""
    rig.game.season.gtp += 1


def program_rig(tmp_path, answers=(), policy=None, first=False, preset=None, outcomes=(), seed=1, fast=False,
                speech_per_char=0.0, mode="sapi", pog=advance_week, **kwargs):
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=random.Random(seed), speech_per_char=speech_per_char, mode=mode,
              **kwargs)
    keys = PolicyKeys(rig.clock, answers, policy, fast)
    rig.keys = rig.game.keys = rig.sounds.keys = keys
    if fast:
        rig.sounds.sleep = lambda seconds: rig.clock.sleep(0.02)
    rig.store = rig.game.program_store = RigStore(first, preset)
    rig.outcomes = list(outcomes)
    rig.plays = []
    game = rig.game

    def play_game(rules=None, own_names=None, saved=None, quarterback_names=None, save_sink=None, roster_sink=None):
        rig.plays.append({"own_names": own_names, "saved": saved, "save_sink": save_sink, "roster_sink": roster_sink})
        outcome = rig.outcomes.pop(0)
        if callable(outcome):
            outcome = outcome(rig)
        if outcome.stop_beds:
            rig.sounds.stop_crowds()
        if outcome.gtp is not None:
            game.season.gtp = outcome.gtp
        if outcome.result.scores is not None:
            game.m414 = outcome.result.scores
        return outcome.result

    game.play_game = play_game
    rig.pog_calls = []

    def fake_pog():
        rig.pog_calls.append(game.m414)
        if pog is not None:
            pog(rig)
        rig.ptf_after_pog = game.ptf

    game.pog = fake_pog
    return rig


def said(rig):
    return [text for text, _, _ in rig.said]


def sound_events(rig, action="play"):
    """(slot, sound id) of every slot event of one kind, in order."""
    return [(e.slot, e.sound_id) for e in rig.slot_log if e.action == action]


__all__ = ["program_rig", "advance_week", "preset_season", "RigStore", "Outcome", "played", "saved_game", "said", "sound_events",
           "enter_policy", "ENTER", "ESC", "UP", "DOWN", "F1", "F5", "F9"]
