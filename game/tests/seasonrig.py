"""A rig for the season engine: the Game with the real sound layer on the virtual clock, a recording season store and
strict scripted draws. This is inspired by Jim Kitchen.

* `season_rig` builds the Rig of tests/gamerig.py with the Bengals (division 1, place 1) against the Jets (division 2,
  place 3), the week and the game's final score; `rig.store` records every write the engine makes in order, `rig.log`
  every line sent to the speech log;
* `run` plays a call of the engine with a strict script of draws (a `Draws` of tests/pagrig.py): the trace of draw sizes
  must equal the script's sizes and every value must be used;
* records, pairings and the hand-worked season BASE of the tests (the same as tests/test_playoffs.py).
"""
import random

from gamerig import Rig
from nfl4.game.league import DIVISIONS, PLACES
from nfl4.game.playoffs import TeamRef
from nfl4.game.standings import Records
from pagrig import Draws, PolicyKeys, enter_policy, sounds_played, texts
from randsources import ScriptedRandom

ENTER, F1, F2 = 13, 112, 113


class RecordingStore:
    """What S7.5 will write, in the order the engine asks: ("records", the 64 file values), ("gtp", n), ("pairings",
    footbal4.dat values), ("byes", footbal5.dat values)."""

    def __init__(self):
        self.events = []

    def write_records(self, records):
        self.events.append(("records", records.as_file_values()))

    def write_gtp(self, gtp):
        self.events.append(("gtp", gtp))

    def write_pairings(self, pairings):
        self.events.append(("pairings", [v for visitor, home in pairings for v in (*visitor, *home)]))

    def write_byes(self, byes):
        self.events.append(("byes", [v for team in byes for v in team]))

    def kinds(self):
        return [kind for kind, _ in self.events]


def records_of(wins: dict, default=8) -> Records:
    """Everybody 16 games: `wins` maps (division, place) to the number of wins, the rest `default` wins."""
    records = Records()
    for d in range(1, DIVISIONS + 1):
        for p in range(1, PLACES + 1):
            w = wins.get((d, p), default)
            records.wins[d - 1][p - 1], records.losses[d - 1][p - 1] = w, 16 - w
    return records


def division_wins(*rows):
    """rows: one list of four win counts per division (division 1 first)."""
    return {(d, p): w for d, row in enumerate(rows, start=1) for p, w in enumerate(row, start=1)}


# the hand-worked season: winners D1 Browns 12-4, D2 Bills 9-7, D3 Chiefs 13-3, D4 Colts 8-8, D5 Bears 12-4, D6 Cowboys
# 10-6, D7 Cardinals 13-3, D8 Buccaneers 9-7; wild cards Broncos 11-5 and Bengals 10-6, Lions 11-5 and Eagles 10-6;
# wild card games Broncos at Colts, Bengals at Bills, Lions at Buccaneers, Eagles at Cowboys; byes Browns, Chiefs, Bears,
# Cardinals (tests/test_playoffs.py works it out)
BASE = division_wins([10, 12, 8, 6], [9, 9, 7, 5], [11, 10, 13, 4], [8, 8, 8, 8],
                     [12, 11, 3, 2], [10, 10, 6, 6], [13, 5, 5, 5], [9, 9, 9, 9])
BASE_PAIRINGS = [(TeamRef(3, 1), TeamRef(4, 1)), (TeamRef(1, 1), TeamRef(2, 1)),
                 (TeamRef(5, 2), TeamRef(8, 1)), (TeamRef(6, 2), TeamRef(6, 1))]
BASE_BYES = [TeamRef(1, 2), TeamRef(3, 3), TeamRef(5, 1), TeamRef(7, 1)]


def refs(*pairs):
    return [TeamRef(*p) for p in pairs]


def season_rig(tmp_path, answers=(), own=(1, 1), opponent=(2, 3), gtp=1, scores=(24, 17), log=True, rng=None,
               speech_per_char=0.0, policy=None, fast=False):
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=rng if rng is not None else ScriptedRandom([], strict=True),
              speech_per_char=speech_per_char)
    keys = PolicyKeys(rig.clock, answers, policy, fast)
    rig.keys = rig.game.keys = rig.sounds.keys = keys
    if fast:
        rig.sounds.sleep = lambda seconds: rig.clock.sleep(0.02)
    game = rig.game
    game.season.coach = "Kim"
    game.season.choose_team(*own)
    game.season.tn3, game.season.tn4 = opponent
    game.season.gtp = gtp
    game.m414 = scores
    rig.store = game.season_store = RecordingStore()
    rig.log = []
    if log:
        game.log_sink = rig.log.append
    rig.engine = game.season_engine
    return rig


def run(rig, call, draws: Draws = None):
    """Call `call()` with the draws scripted (strict) and check the trace of draw sizes and that all values were used."""
    draws = draws if draws is not None else Draws()
    source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.source = source
    rig.rnd.trace = []
    result = call()
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert source.left == 0
    return result


def computer_game_draws(draws: Draws, coin: int, winner_index: int, loser_index: int) -> Draws:
    """One computer game: Int(Rnd * 2) + 1 = coin, then the winner's index and the loser's index (each Int(Rnd * 32) + 1)."""
    return draws.rnd(2, coin).rnd(32, winner_index).rnd(32, loser_index)


__all__ = ["RecordingStore", "records_of", "division_wins", "BASE", "BASE_PAIRINGS", "BASE_BYES", "refs", "season_rig",
           "run", "computer_game_draws", "ENTER", "F1", "F2", "Draws", "random", "sounds_played", "texts", "enter_policy"]
