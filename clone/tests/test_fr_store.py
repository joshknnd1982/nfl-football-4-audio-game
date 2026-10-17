"""The franchise's files: league.sav with its backup, the 7.10 matrix, the crash points and the saved game (nfl4 only, rule 0.13).
This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 10.1 and 10.2, invariant I10: at any moment league.sav or league.previous.sav is whole. The matrix of
playbook 7.10 is run on a real folder (delete, empty, cut in half, random bytes, another encoding, huge, read-only, held by another
program, newer format, a value out of range for its stage, a stale .tmp); the crash points are every step of a write.
"""
import json
import random

import pytest

import filedamage
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.files import DiskFiles, MemoryFiles
from nfl4.extras.franchise.league import OFFSEASON, SEASON, LeagueRecord, new_league
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.names import load_surnames
from nfl4.game.rnd import GameRandom
from test_files_savedgame import a_game

SURNAMES = load_surnames()
NXF = {number: X.text("NXF-%d" % number) for number in (30, 31, 32, 33, 34, 35, 36, 37)}


def a_league(seed=1, season=1):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", 4, "L%d" % seed)
    league.season = season
    league.schedule = [[2, 1, 1]] * 16
    return league


def store_over(files, league=None, strict=True):
    store = FranchiseStore(files)
    store.strict = strict
    if league is not None:
        store.league = league
    return store


def opened(files, kind=True):
    store = store_over(files)
    store.open(kind)
    return store


# ----- a write: the three steps -----

def test_a_write_is_the_new_text_to_the_temporary_file_the_copy_of_the_present_file_and_the_rename():
    files = MemoryFiles()
    store = store_over(files, a_league())
    assert store.save() and files.steps == [("tmp", "league.sav"), ("commit", "league.sav")]
    assert D.PREVIOUS_FILE not in files.data and "league.sav.tmp" not in files.data
    first = files.data["league.sav"]
    files.steps.clear()
    store.league.coach = "Pat"
    assert store.save()
    assert files.steps == [("tmp", "league.sav"), ("copy", "league.sav", "league.previous.sav"), ("commit", "league.sav")]
    assert files.data["league.previous.sav"] == first and b'"coach":"Pat"' in files.data["league.sav"]


def test_a_saved_league_opens_equal_to_the_one_in_memory():
    files = MemoryFiles()
    league = a_league()
    store_over(files, league).save()
    again = opened(files)
    assert again.exists and again.league.to_json() == league.to_json() and again.take_notices() == []
    assert not again.force_classic and again.available


def test_no_folder_means_no_franchise_and_no_notice_while_the_kind_is_classic():
    store = opened(MemoryFiles(), kind=False)
    assert not store.exists and store.available and store.take_notices() == [] and not store.force_classic


# ----- the crash points (I10) -----

class Crash(Exception):
    pass


class CrashingFiles(MemoryFiles):
    """Stops the process at the n-th step of the writes (counted from 0) before it does its work."""

    def __init__(self, crash_at):
        super().__init__()
        self.crash_at = crash_at
        self.count = 0

    def _step(self):
        if self.count == self.crash_at:
            raise Crash()
        self.count += 1

    def write_tmp(self, name, data):
        self._step()
        return super().write_tmp(name, data)

    def copy(self, source, target):
        self._step()
        return super().copy(source, target)

    def commit(self, name):
        self._step()
        return super().commit(name)


@pytest.mark.parametrize("crash_at", [0, 1, 2])
def test_a_crash_at_any_step_of_the_second_write_leaves_a_usable_file(crash_at):
    files = CrashingFiles(crash_at=99)
    first, second = a_league(1), a_league(1)
    second.coach = "Second"
    store_over(files, first).save()
    survivor = files.data.copy()
    files.crash_at, files.count = crash_at, 0
    store = store_over(files, second)
    with pytest.raises(Crash):
        store.save()
    again = MemoryFiles()
    again.data = files.data
    after = opened(again)
    assert after.exists and after.league.coach in ("Kim", "Second") and after.take_notices() == []
    assert survivor["league.sav"] == files.data["league.sav"] or after.league.coach == "Second"


def test_a_crash_while_the_previous_copy_is_half_written_leaves_league_sav_whole():
    files = MemoryFiles()
    store = store_over(files, a_league())
    store.save()
    store.league.coach = "Next"
    real_copy = files.copy

    def half_copy(source, target):
        files.data[target] = files.data[source][:100]
        raise Crash()
    files.copy = half_copy
    with pytest.raises(Crash):
        store.save()
    files.copy = real_copy
    after = opened(files)
    assert after.league.coach == "Kim"                                  # the rename never happened: the old file is whole
    assert after.take_notices() == []


def test_a_stale_temporary_file_is_deleted_unread():
    files = MemoryFiles()
    store_over(files, a_league()).save()
    files.data["league.sav.tmp"] = b"half of a write"
    after = opened(files)
    assert after.exists and "league.sav.tmp" not in files.data and after.take_notices() == []


# ----- the healing table (design 10.1) -----

def two_saves(files):
    store = store_over(files, a_league())
    store.save()
    store.league.coach = "Second"
    store.save()
    return store


def test_a_damaged_league_sav_uses_the_copy_and_keeps_the_damaged_file():
    files = MemoryFiles()
    two_saves(files)
    files.data["league.sav"] = b"damaged"
    after = opened(files)
    assert after.exists and after.league.coach == "Kim" and after.take_notices() == [NXF[30]]
    assert files.aside == ["league.sav"] and json.loads(files.data["league.sav"])["coach"] == "Kim"      # written back whole
    assert not after.force_classic


def test_a_missing_league_sav_uses_the_copy_and_says_so():
    files = MemoryFiles()
    two_saves(files)
    del files.data["league.sav"]
    after = opened(files)
    assert after.exists and after.league.coach == "Kim" and after.take_notices() == [NXF[36]]
    assert "league.sav" in files.data


def test_both_files_damaged_set_the_franchise_aside_and_make_a_classic_season():
    files = MemoryFiles()
    two_saves(files)
    files.data["league.sav"] = b"damaged"
    files.data["league.previous.sav"] = b"damaged too"
    after = opened(files, kind=True)
    assert not after.exists and after.force_classic and after.take_notices() == [NXF[31]]
    assert sorted(files.aside) == ["league.previous.sav", "league.sav"] and "league.sav" not in files.data


def test_one_damaged_and_the_other_missing_is_the_same_as_both_damaged():
    files = MemoryFiles()
    store_over(files, a_league()).save()
    files.data["league.sav"] = b"damaged"
    after = opened(files, kind=True)
    assert not after.exists and after.force_classic and after.take_notices() == [NXF[31]]


def test_both_missing_while_the_kind_is_franchise_says_so_and_makes_a_classic_season():
    after = opened(MemoryFiles(), kind=True)
    assert not after.exists and after.force_classic and after.take_notices() == [NXF[37]]


def test_a_newer_format_is_left_alone_and_the_franchise_is_not_used_this_run():
    files = MemoryFiles()
    store_over(files, a_league()).save()
    files.data["league.sav"] = files.data["league.sav"].replace(b'"format":5', b'"format":6', 1)
    before = dict(files.data)
    after = opened(files, kind=True)
    assert not after.exists and not after.available and after.force_classic and after.take_notices() == [NXF[34]]
    assert files.data == before and not after.save()                    # nothing is written, nothing is set aside


def test_a_file_held_by_another_program_is_not_damage_and_nothing_is_written():
    files = MemoryFiles()
    store_over(files, a_league()).save()
    files.held.add("league.sav")
    after = opened(files, kind=True)
    assert not after.available and after.take_notices() == [NXF[35]] and not after.save()
    assert not files.aside and "league.sav" in files.data


def test_a_file_over_the_size_limit_is_damage_without_being_read():
    files = MemoryFiles()
    two_saves(files)
    files.data["league.sav"] = b"x" * (D.SAVE_MAX_BYTES + 1)
    after = opened(files)
    assert after.exists and after.take_notices() == [NXF[30]]


def test_a_folder_that_cannot_be_written_plays_on_from_memory_and_says_so_once():
    files = MemoryFiles()
    store = store_over(files, a_league())
    files.unwritable = True
    assert not store.save() and not store.save()
    assert store.unwritable and store.take_notices() == [NXF[32]]
    assert store.exists                                                  # the league in memory is still there


def test_a_record_that_fails_its_own_check_is_never_written():
    files = MemoryFiles()
    league = a_league()
    league.players[3].rating = 100
    store = store_over(files, league, strict=False)
    assert not store.save() and "league.sav" not in files.data and store.take_notices() == [NXF[32]]
    store.strict = True
    with pytest.raises(Exception):
        store.save()


# ----- the same on a real folder: the 7.10 matrix -----

BYTE_KINDS = [kind for kind in filedamage.BYTE_DAMAGES if kind != "newer_format"]


def folder_with_two_saves(tmp_path):
    folder = tmp_path / "franchise"
    store = store_over(DiskFiles(str(folder)), a_league())
    store.save()
    store.league.coach = "Second"
    store.save()
    return folder


@pytest.mark.parametrize("kind", BYTE_KINDS)
def test_every_byte_damage_of_league_sav_falls_back_to_the_copy_on_disk(tmp_path, kind):
    folder = folder_with_two_saves(tmp_path)
    filedamage.apply(kind, folder / "league.sav")
    after = opened(DiskFiles(str(folder)))
    assert after.exists and after.league.coach == "Kim" and after.take_notices() == [NXF[30]], kind
    assert (folder / "league.sav.damaged1").exists()
    assert LeagueRecord.from_json((folder / "league.sav").read_text(encoding="utf-8")).coach == "Kim"


@pytest.mark.parametrize("kind", ["empty", "random_bytes", "cut_in_half"])
def test_both_files_damaged_on_disk_are_kept_aside_and_a_classic_season_begins(tmp_path, kind):
    folder = folder_with_two_saves(tmp_path)
    filedamage.apply(kind, folder / "league.sav")
    filedamage.apply(kind, folder / "league.previous.sav")
    after = opened(DiskFiles(str(folder)))
    assert not after.exists and after.force_classic and after.take_notices() == [NXF[31]]
    assert (folder / "league.sav.damaged1").exists() and (folder / "league.previous.sav.damaged1").exists()


def test_a_huge_file_on_disk_is_damage_without_being_read(tmp_path):
    folder = folder_with_two_saves(tmp_path)
    with open(folder / "league.sav", "wb") as handle:
        handle.truncate(D.SAVE_MAX_BYTES + 1)
    after = opened(DiskFiles(str(folder)))
    assert after.exists and after.league.coach == "Kim" and after.take_notices() == [NXF[30]]


def test_a_value_out_of_range_for_its_stage_on_disk_is_damage(tmp_path):
    folder = folder_with_two_saves(tmp_path)
    data = json.loads((folder / "league.sav").read_text(encoding="utf-8"))
    data["players"][5][3] = 100                                         # a rating of 100
    (folder / "league.sav").write_text(json.dumps(data), encoding="utf-8")
    after = opened(DiskFiles(str(folder)))
    assert after.league.coach == "Kim" and after.take_notices() == [NXF[30]]


def test_a_record_written_at_stage_1_with_an_empty_place_is_damage_but_at_a_later_stage_it_is_not(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "STAGES", ((1, "NXE-11"), (2, "NXE-12"), (6, "NXE-16")))
    folder = tmp_path / "franchise"
    league = a_league()
    league.stage, league.gtp, league.records = OFFSEASON, 0, [8, 8] * 32
    pid = league.rosters[2][4]
    league.players[pid].status, league.players[pid].team, league.players[pid].place = "retired", 0, -1
    league.rosters[2][4] = 0
    for stage_no, usable in ((2, True), (1, False)):
        league.stage_no = stage_no
        raw = league.to_json().encode("utf-8")
        folder.mkdir(exist_ok=True)
        (folder / "league.sav").write_bytes(raw)
        (folder / "league.previous.sav").unlink(missing_ok=True)
        after = opened(DiskFiles(str(folder)), kind=False)
        assert after.exists == usable, stage_no


def test_a_read_only_league_sav_is_read_and_a_write_fails_with_the_notice(tmp_path):
    folder = folder_with_two_saves(tmp_path)
    with filedamage.read_only(folder / "league.sav"):
        store = opened(DiskFiles(str(folder)))
        assert store.exists and store.take_notices() == []
        store.league.coach = "Third"
        assert not store.save() and store.take_notices() == [NXF[32]]
    assert opened(DiskFiles(str(folder))).league.coach == "Second"


def test_a_league_sav_held_by_another_program_on_disk_is_not_damage(tmp_path):
    folder = folder_with_two_saves(tmp_path)
    with filedamage.holding(folder / "league.sav"):
        store = opened(DiskFiles(str(folder)))
    assert not store.available and store.take_notices() == [NXF[35]]
    assert not (folder / "league.sav.damaged1").exists()


def test_a_newer_format_on_disk_is_left_untouched(tmp_path):
    folder = folder_with_two_saves(tmp_path)
    path = folder / "league.sav"
    path.write_bytes(path.read_bytes().replace(b'"format":5', b'"format":6', 1))
    raw = path.read_bytes()
    after = opened(DiskFiles(str(folder)))
    assert not after.available and after.take_notices() == [NXF[34]] and path.read_bytes() == raw


def test_a_stale_tmp_on_disk_is_removed(tmp_path):
    folder = folder_with_two_saves(tmp_path)
    (folder / "league.sav.tmp").write_bytes(b"{")
    opened(DiskFiles(str(folder)))
    assert not (folder / "league.sav.tmp").exists()


# ----- a new franchise keeps the old ones as copies (design 3.2) -----

def test_a_new_franchise_moves_the_old_one_to_old_and_keeps_the_three_newest():
    files = MemoryFiles()
    store = store_over(files, a_league(1))
    store.save()
    for seed in (2, 3, 4, 5):
        previous = files.data["league.sav"]
        store.create(a_league(seed))
        assert files.data["old/league-1.sav"] == previous
    assert sorted(name for name in files.data if name.startswith("old/league")) == ["old/league-1.sav", "old/league-2.sav", "old/league-3.sav"]
    assert json.loads(files.data["old/league-3.sav"])["league_id"] == "L2"       # the oldest kept is the second league
    assert json.loads(files.data["league.sav"])["league_id"] == "L5"
    assert "league.previous.sav" not in files.data or json.loads(files.data["league.sav"])["league_id"] == "L5"


# ----- the franchise's saved game (design 10.2) -----

def with_extras(saved):
    from nfl4.extras.state import ExtrasRecord
    saved.extras, saved.extras_marked = ExtrasRecord().to_json(), True
    return saved


def test_a_saved_game_carries_the_league_season_and_week_and_loads_only_there():
    files = MemoryFiles()
    league = a_league()
    league.gtp = 1
    store = store_over(files, league)
    store.save()
    assert store.save_game(with_extras(a_game()))
    assert b"franchise" in files.data["football.sav"]
    again = opened(files)
    assert again.has_saved_game() and again.take_notices() == []
    saved = again.take_saved_game()
    assert saved is not None and "football.sav" not in files.data and not again.has_saved_game()


def test_a_saved_game_of_another_week_is_set_aside_with_the_notice():
    files = MemoryFiles()
    league = a_league()
    store = store_over(files, league)
    store.save()
    store.save_game(with_extras(a_game()))
    league.gtp, league.records = 2, [1, 0] * 32
    store.save()
    again = opened(files)
    assert not again.has_saved_game() and again.take_notices() == [NXF[33]]
    assert "football.sav" not in files.data and files.aside == ["football.sav"]


def test_a_saved_game_without_the_mark_or_damaged_is_set_aside():
    files = MemoryFiles()
    store = store_over(files, a_league())
    store.save()
    store.save_game(a_game())                                          # no extras record: nothing says which week it is
    assert not opened(files).has_saved_game()
    files.data["football.sav"] = b"junk"
    again = opened(files)
    assert not again.has_saved_game() and again.take_notices() == [" The saved game could not be read and was set aside. "]


def test_the_extras_record_without_a_franchise_value_is_the_old_text():
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord()
    assert "franchise" not in record.to_json() and ExtrasRecord.from_json(record.to_json()).franchise is None
    record.franchise = {"league": "L1", "season": 2, "week": 3}
    assert ExtrasRecord.from_json(record.to_json()).franchise == record.franchise
    record.franchise = {"league": "L1", "season": 0, "week": 3}
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(record.to_json())


# ----- a fuzz: whatever is in league.sav, opening it never raises and leaves either a whole league or none -----

def test_random_damage_to_league_sav_never_raises_and_never_loads_a_record_that_fails_its_check():
    base = a_league().to_json().encode("utf-8")
    rng = random.Random(7)
    for case in range(150):
        data = bytearray(base)
        for _ in range(rng.choice((1, 1, 2, 5))):
            kind = rng.choice(("flip", "cut", "insert", "delete", "swap"))
            at = rng.randrange(len(data))
            if kind == "flip":
                data[at] = rng.randrange(256)
            elif kind == "cut":
                del data[at:]
            elif kind == "insert":
                data[at:at] = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 20)))
            elif kind == "delete":
                del data[at:at + rng.randrange(1, 30)]
            else:
                other = rng.randrange(len(data))
                data[at], data[other] = data[other], data[at]
        files = MemoryFiles()
        files.data["league.sav"] = bytes(data)
        store = opened(files, kind=True)
        if store.exists:
            store.league.check()                      # whatever loaded is a whole record
        else:
            assert store.force_classic and store.take_notices() == [NXF[31]], case
