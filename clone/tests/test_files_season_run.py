"""Whole seeded seasons written through the real files and read back (data/files/store.py). This is inspired by Jim Kitchen.

The season engine writes through a `SeasonStore` and the prompts through a `SetupStore` (D-044, D-045). Here the real store
sits behind both, next to the recording store of tests/seasonrig.py: after every call of the engine a SECOND store, made over
the same folder the way the next start of the program makes it, must load exactly the state the engine holds, with no
notice; and the real store must have been asked for the same writes, in the same order, with the same values as the
recording one (so the files hold what the original's files would).
"""
import random

import pytest

from nfl4.data.files.store import FileProgramStore
from nfl4.game.season import SeasonState
from seasonrig import RecordingStore
from test_season_games import Season, check_regular_season

OWN = (3, 2)


class Tee:
    """Forwards each SeasonStore write to the recording store and to the real one, and notes the order."""

    def __init__(self, recording, real):
        self.recording, self.real = recording, real

    def write_records(self, records):
        self.recording.write_records(records)
        self.real.write_records(records)

    def write_gtp(self, gtp):
        self.recording.write_gtp(gtp)
        self.real.write_gtp(gtp)

    def write_pairings(self, pairings):
        self.recording.write_pairings(pairings)
        self.real.write_pairings(pairings)

    def write_byes(self, byes):
        self.recording.write_byes(byes)
        self.real.write_byes(byes)


class FileSeason(Season):
    """A Season whose files are real; `reloads` counts the checks made after engine calls."""

    def __init__(self, tmp_path, seed, policy, own, concede=False):
        super().__init__(tmp_path / "rig", seed, policy, own, concede)
        self.folder = tmp_path / "data"
        self.real = FileProgramStore(str(self.folder), str(self.folder / "customize"))
        self.reloads = 0
        game = self.game
        self.recording = game.season_store
        game.season_store = Tee(self.recording, self.real)
        game.setup_store = self.real
        self.real.write_coach_and_team(game.season.tn1, game.season.tn2, game.season.coach)
        self.real.write_gtp(1)
        self.real_pog = game.pog
        game.pog = self.pog_and_check

    def pog_and_check(self):
        result = self.real_pog()
        self.check_files()
        return result

    def check_files(self):
        state = self.game.season
        again = FileProgramStore(str(self.folder), str(self.folder / "customize"))
        assert again.take_notices() == []
        if state.gtp == 0:                       # the season is over: the engine writes no 0 when the team is out (D-044)
            return
        loaded = SeasonState()
        assert again.load_season(loaded), "the files of week %d do not load" % state.gtp
        assert (loaded.coach, loaded.tn1, loaded.tn2, loaded.gtp) == (state.coach, state.tn1, state.tn2, state.gtp)
        assert loaded.schedule == state.schedule
        assert loaded.records.as_file_values() == state.records.as_file_values()
        assert loaded.playoffs.pairings == state.playoffs.pairings and loaded.playoffs.byes == state.playoffs.byes
        self.reloads += 1


def play_through_files(tmp_path, seed, policy="random", own=OWN, concede=False):
    season = FileSeason(tmp_path, seed, policy, own, concede)
    season.regular_season()
    if season.game.season.gtp in (17, 18):
        season.playoffs()
    return season


@pytest.mark.parametrize("seed", range(6))
def test_a_season_written_and_read_back_week_by_week_is_the_state_of_the_engine(tmp_path, seed):
    season = play_through_files(tmp_path, seed)
    check_regular_season(season)
    assert season.reloads >= 15                          # every regular week at least, and the play-off weeks that were reached
    assert season.real.take_notices() == []


@pytest.mark.parametrize("seed, policy", [(100, "win"), (101, "win"), (102, "win"), (103, "win"), (200, "lose"), (201, "lose")])
def test_the_play_off_weeks_are_read_back_too(tmp_path, seed, policy):
    season = play_through_files(tmp_path, seed, policy=policy)
    assert season.game.season.gtp == 0
    assert season.reloads >= 15                      # every regular week, and each play-off week after a win
    if policy == "win" and len(season.rounds) >= 2:
        assert season.reloads >= 16                  # a second round was read back


def test_every_write_of_the_engine_reaches_the_real_files_in_the_recorded_order(tmp_path):
    """Replay the recording store's events into a fresh folder: the files must be the ones the engine's own run left."""
    season = play_through_files(tmp_path, 7, policy="win")
    replay = FileProgramStore(str(tmp_path / "replay"), str(tmp_path / "replay" / "customize"))
    for kind, values in season.recording.events:
        if kind == "records":
            from nfl4.game.standings import Records
            replay.write_records(Records.from_file_values(values))
        elif kind == "gtp":
            replay.write_gtp(values)
        elif kind == "pairings":
            from nfl4.game.playoffs import PlayoffState
            replay.write_pairings(PlayoffState.pairings_from_values(values))
        elif kind == "byes":
            from nfl4.game.playoffs import PlayoffState
            replay.write_byes(PlayoffState.byes_from_values(values))
        else:
            raise AssertionError(kind)
    for name in ("football.gtp", "footbal3.dat", "footbal4.dat", "footbal5.dat"):
        mine, theirs = tmp_path / "data" / name, tmp_path / "replay" / name
        assert mine.exists() == theirs.exists(), name
        if mine.exists():
            assert mine.read_bytes() == theirs.read_bytes(), name
    assert "gtp" in season.recording.kinds() and "records" in season.recording.kinds()


def test_a_season_that_ends_leaves_nothing_but_the_previous_names(tmp_path):
    season = play_through_files(tmp_path, 3, policy="lose")
    from nfl4.game.setup import COUNTS, Roster
    roster = Roster(*[[f"{h}{i}" for i in range(c)] for h, c in zip("rdkst", COUNTS)], quarterback="Unitas")
    assert season.real.write_player_names(roster)
    assert season.game.season.gtp == 0
    season.real.delete_season_files()                       # what Program.season_over asks of the store
    assert sorted(p.name for p in (tmp_path / "data").iterdir()) == ["customize"]
    assert [p.name for p in (tmp_path / "data" / "customize").iterdir()] == ["footplay.previous.txt"]
    fresh = FileProgramStore(str(tmp_path / "data"), str(tmp_path / "data" / "customize"))
    assert fresh.take_notices() == [] and fresh.load_season(SeasonState()) is False
