"""SX.14 (CLAUDE.md 0.23, playbook 7.17, NX-S2, NX-S3, NX-S6, NX-S8): the saves, the season and the franchise on the real files. This is inspired by Jim Kitchen.

The classic store (data/files/store.py) over a real folder and the franchise store (extras/franchise/store.py) over its in-memory folder: a
saved game is never removed by loading, a damaged or old one is named by `classify` and left where it is, the season and the franchise move to the
backup on the player's word and come back, and a failed move loses nothing.
"""
import json

from nfl4.data.files import shelf
from nfl4.data.files.store import FileProgramStore
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.season import SeasonState
from savesrig import a_saved
from test_files_savedgame import a_game
from test_files_store import a_season_on_disk, data, make


def with_week(week, own=14):
    return a_saved(own=own, week=week)


# ----- the classic store -----

def test_a_saved_game_is_kept_when_it_is_read_and_a_slot_is_a_file_of_its_own(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=5)
    assert store.save_game(with_week(5)) is True and store.save_game(with_week(5, own=3), 3) is True
    assert sorted(p.name for p in (tmp_path / "data").glob("football*.sav")) == ["football.sav", "football3.sav"]
    again = make(tmp_path)
    entries = again.shelf.scan(again.classify)
    assert [(e.slot, e.status) for e in entries] == [(1, "ok"), (3, "ok")] and again.has_saved_game()
    again.load_season(SeasonState())
    again.shelf.scan(again.classify)
    assert data(tmp_path, "football.sav").exists() and data(tmp_path, "football3.sav").exists()      # nothing deleted anything


def test_a_save_of_another_week_is_old_and_a_save_with_no_season_is_an_orphan_and_neither_is_removed(tmp_path):
    a_season_on_disk(tmp_path, gtp=5).save_game(with_week(4))
    again = make(tmp_path)
    assert [e.status for e in again.shelf.scan(again.classify)] == ["stale"] and not again.has_saved_game()
    assert data(tmp_path, "football.sav").exists() and again.take_notices() == []
    lone = make(tmp_path / "lone")
    lone.save_game(with_week(1))
    again = make(tmp_path / "lone")
    assert [e.status for e in again.shelf.scan(again.classify)] == ["orphan"] and data(tmp_path / "lone", "football.sav").exists()


def test_a_save_of_the_original_with_no_summary_counts_as_this_weeks(tmp_path):
    a_season_on_disk(tmp_path, gtp=5).save_game(a_saved(with_info=False))
    again = make(tmp_path)
    assert again.has_saved_game() and again.shelf.scan(again.classify)[0].info == {}


def test_a_damaged_save_is_neither_set_aside_nor_announced_by_the_store_it_waits_for_the_menu(tmp_path):
    a_season_on_disk(tmp_path, gtp=2).save_game(with_week(2))
    data(tmp_path, "football.sav").write_bytes(b"\x02\x00\x01")
    again = make(tmp_path)
    assert again.take_notices() == [] and [e.status for e in again.shelf.scan(again.classify)] == ["damaged"]
    assert data(tmp_path, "football.sav").exists() and not list((tmp_path / "data").glob("*.damaged*"))


def test_a_game_week_that_moves_makes_the_older_saves_old(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=5)
    store.save_game(with_week(5))
    assert store.has_saved_game()
    store.write_gtp(6)
    assert not store.has_saved_game()


def test_the_automatic_save_is_written_whole_and_found(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=5)
    assert store.autosave(with_week(5, own=9))
    assert not list((tmp_path / "data").glob("*.tmp")) and [e.kind for e in store.shelf.scan(store.classify)] == ["auto"]


def test_the_season_goes_to_the_backup_with_its_saved_games_and_comes_back(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=5)
    store.save_game(with_week(5))
    store.autosave(with_week(5))
    store = make(tmp_path)
    assert store.season_peek().gtp == 5 and store.season_peek().coach == "Kim Lee"
    assert store.delete_season() and store.season_deleted()
    names = sorted(p.name for p in (tmp_path / "data").iterdir())
    assert "footbal1.dat" not in names and "football.sav" not in names and "autosave.sav" not in names
    assert (tmp_path / "data" / "backup" / "season" / "footbal1.dat").exists() and (tmp_path / "data" / "backup" / "season" / "football.sav").exists()
    again = make(tmp_path)
    assert again.season_peek() is None and again.season_deleted()
    assert again.restore_season() and again.season_peek().gtp == 5 and again.has_saved_game()
    assert not again.season_deleted()


def test_a_season_is_not_restored_over_another_and_a_second_delete_replaces_the_backup(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.delete_season()
    a_season_on_disk(tmp_path, gtp=8)
    newer = make(tmp_path)
    assert not newer.restore_season() and newer.season_peek().gtp == 8              # a season is there: nothing is overwritten
    assert newer.delete_season() and newer.restore_season() and newer.season_peek().gtp == 8


def test_a_season_that_cannot_be_moved_is_put_back_whole(tmp_path, monkeypatch):
    import os
    a_season_on_disk(tmp_path, gtp=4)
    store = make(tmp_path)
    real = os.replace
    calls = []

    def failing(source, target):
        calls.append(source)
        if len(calls) == 3:
            raise PermissionError("held")
        return real(source, target)
    monkeypatch.setattr(os, "replace", failing)
    assert not store.delete_season()
    monkeypatch.setattr(os, "replace", real)
    assert make(tmp_path).season_peek().gtp == 4
    assert data(tmp_path, "footbal1.dat").exists() and data(tmp_path, "football.gtp").exists()


# ----- the franchise store -----

def a_franchise(files=None):
    from nfl4.extras.franchise.league import new_league
    from nfl4.game.rnd import GameRandom
    import random
    files = files or MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True
    store.open(True)
    league = new_league(GameRandom(random.Random(3)), ["Smith", "Jones", "Brown", "Davis", "Miller", "Wilson"] * 400, "Kim", 1, "L1")
    store.create(league)
    return store, files


def test_the_franchises_saves_belong_to_its_season_and_week(tmp_path):
    store, files = a_franchise()
    saved = a_game()
    saved.extras = '{"rules_year":2026}'
    saved.extras_marked = True
    assert store.save_game(saved, 2) and store.autosave(saved)
    entries = store.shelf.scan(store.classify)
    assert [(e.slot, e.status) for e in entries] == [(2, "ok"), (None, "ok")] and store.has_saved_game()
    store.league.gtp = 2                                                            # the week moved on: the marked saves are old
    assert [e.status for e in store.shelf.scan(store.classify)] == ["stale", "stale"]
    assert "football2.sav" in files.data and "autosave.sav" in files.data          # and nothing was set aside


def test_a_franchise_moves_to_the_backup_with_its_saves_and_comes_back(tmp_path):
    store, files = a_franchise()
    saved = a_game()
    saved.extras, saved.extras_marked = '{"rules_year":2026}', True
    store.save_game(saved, 1)
    store.save_game(saved, 3)
    league_id = store.league.league_id
    assert store.delete_franchise() and store.league is None and store.deleted_exists()
    assert "league.sav" not in files.data and "football.sav" not in files.data and "football3.sav" not in files.data
    assert D.OLD_FOLDER + "/league-1.sav" in files.data and D.OLD_FOLDER + "/football3-1.sav" in files.data
    assert store.restore_deleted() and store.league.league_id == league_id and "football3.sav" in files.data
    assert not store.deleted_exists() and not store.restore_deleted()


def test_a_franchise_is_not_restored_over_another(tmp_path):
    store, files = a_franchise()
    store.delete_franchise()
    other, _ = a_franchise(files)
    assert other.exists and not other.restore_deleted() and other.league.league_id == "L1"


def test_a_franchise_that_cannot_be_moved_is_not_lost():
    store, files = a_franchise()
    files.unwritable = True
    assert not store.delete_franchise() and store.league is not None and "league.sav" in files.data
