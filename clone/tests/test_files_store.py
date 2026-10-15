"""FileProgramStore: the real files and their healing (data/files/store.py). This is inspired by Jim Kitchen.

GAME_SPEC 3 and 12, D-024 items 3 to 5, D-029 item 5, G-F3 to G-F5, G-F8, playbook 7.10. Every test works in a temporary data
folder; the store checks its files once, when it is made, so each test makes a second store to "start the program again".
"""
import os
import random
import stat
import sys

import pytest

from nfl4.data.files import pairingsfile, playernames, variant, weekfile
from nfl4.data.files.store import (LOCKED, NAMES_REPAIRED, NAMES_REPLACED, SAVED_DAMAGED, SEASON_DAMAGED, UNWRITABLE,
                                   FileProgramStore)
from nfl4.game.playoffs import TeamRef
from nfl4.game.rnd import GameRandom
from nfl4.game.schedule import make_schedule
from nfl4.game.season import SeasonState
from nfl4.game.setup import COUNTS, Roster
from nfl4.game.standings import Records
from seasonrig import BASE_BYES, BASE_PAIRINGS, BASE, records_of
from test_files_savedgame import a_game

TEAM = (3, 2)


def make(tmp_path, first=False):
    return FileProgramStore(str(tmp_path / "data"), str(tmp_path / "data" / "customize"), first=first)


def data(tmp_path, name):
    return tmp_path / "data" / name


def a_season_on_disk(tmp_path, gtp=1, records=None, playoffs=False):
    """What the program writes by the time the week is `gtp`: the team, the schedule, the week, the records, the play-off files."""
    store = make(tmp_path)
    store.write_coach_and_team(*TEAM, "Kim Lee")
    store.write_schedule(make_schedule(GameRandom(random.Random(5)), *TEAM))
    store.write_gtp(gtp)
    if gtp >= 2:
        store.write_records(records if records is not None else records_of(BASE))
    if playoffs or gtp >= 17:
        games = {17: 4, 18: 4, 19: 2, 20: 1}[gtp]
        pairings = ([(TeamRef(3, 2), TeamRef(4, 1))] + list(BASE_PAIRINGS[1:]))[:games]
        store.write_pairings(pairings)
        if gtp <= 18:
            store.write_byes(BASE_BYES)
    return store


def a_names_file(tmp_path, roster=None):
    store = make(tmp_path)
    roster = roster or Roster(*[[f"{h}{i}" for i in range(c)] for h, c in zip("rdkst", COUNTS)], quarterback="Unitas")
    assert store.write_player_names(roster)
    return roster


# ----- the start -----

def test_a_first_start_finds_nothing_says_nothing_and_writes_nothing(tmp_path):
    store = make(tmp_path, first=True)
    assert store.first_run() is True and store.has_saved_game() is False
    assert store.load_season(SeasonState()) is False and store.take_notices() == []
    assert store.player_names() is None
    assert not (tmp_path / "data").exists()                     # reading creates nothing
    assert make(tmp_path, first=False).first_run() is False


def test_a_season_written_by_the_program_is_loaded_whole_by_the_next_start(tmp_path):
    a_season_on_disk(tmp_path, gtp=5)
    again = make(tmp_path)
    assert again.take_notices() == []
    season = SeasonState()
    assert again.load_season(season) is True
    assert (season.coach, season.tn1, season.tn2, season.gtp) == ("Kim Lee", 3, 2, 5)
    assert season.schedule == make_schedule(GameRandom(random.Random(5)), *TEAM)
    assert season.records.as_file_values() == records_of(BASE).as_file_values()
    assert season.playoffs.pairings == [] and season.playoffs.byes == []
    assert again.load_season(SeasonState()) is False             # a season is loaded once


def test_the_loaded_state_keeps_the_objects_the_engine_already_holds(tmp_path):
    a_season_on_disk(tmp_path, gtp=17)
    season = SeasonState()
    records, playoffs, pairings = season.records, season.playoffs, season.playoffs.pairings
    assert make(tmp_path).load_season(season)
    assert season.records is records and season.playoffs is playoffs and season.playoffs.pairings is pairings
    assert len(pairings) == 4 and season.playoffs.byes == BASE_BYES


@pytest.mark.parametrize("gtp", [1, 2, 9, 16, 17, 18, 19, 20])
def test_every_week_the_original_can_be_in_is_loaded(tmp_path, gtp):
    a_season_on_disk(tmp_path, gtp=gtp)
    store = make(tmp_path)
    season = SeasonState()
    assert store.take_notices() == [] and store.load_season(season) and season.gtp == gtp
    assert season.set_week_opponent() is not None if gtp <= 16 else season.set_playoff_opponent()


def test_week_1_may_have_no_records_file_but_week_2_may_not(tmp_path):
    a_season_on_disk(tmp_path, gtp=1)
    assert not data(tmp_path, "footbal3.dat").exists()
    assert make(tmp_path).load_season(SeasonState())
    a_season_on_disk(tmp_path, gtp=2)
    data(tmp_path, "footbal3.dat").unlink()
    store = make(tmp_path)
    assert store.take_notices() == [SEASON_DAMAGED] and store.load_season(SeasonState()) is False


def test_a_first_value_of_0_in_footbal1_is_a_damaged_file_not_a_quiet_new_season(tmp_path):
    a_season_on_disk(tmp_path, gtp=4)
    data(tmp_path, "footbal1.dat").write_bytes(variant.pack_integer(0))
    store = make(tmp_path)
    assert store.take_notices() == [SEASON_DAMAGED] and store.load_season(SeasonState()) is False
    live = [n for n in os.listdir(tmp_path / "data") if ".damaged" not in n]
    assert live == [] and "footbal1.dat.damaged1" in os.listdir(tmp_path / "data")       # the season files all went, as copies


def test_season_files_left_without_footbal1_are_removed_quietly(tmp_path):
    a_season_on_disk(tmp_path, gtp=4)
    data(tmp_path, "footbal1.dat").unlink()
    store = make(tmp_path)
    assert store.take_notices() == [] and store.load_season(SeasonState()) is False
    left = sorted(os.listdir(tmp_path / "data"))
    assert left == sorted(n + ".damaged1" for n in ("footbal2.dat", "football.gtp", "footbal3.dat"))   # kept as copies


def test_a_season_that_ended_but_was_not_cleaned_up_is_cleaned_up_with_the_names_kept(tmp_path):
    a_names_file(tmp_path)                                  # first: every store checks the season when it is made
    a_season_on_disk(tmp_path, gtp=0)
    store = make(tmp_path)
    assert store.take_notices() == [] and store.load_season(SeasonState()) is False
    assert sorted(os.listdir(tmp_path / "data")) == ["customize"]
    assert sorted(os.listdir(tmp_path / "data" / "customize")) == ["footplay.previous.txt"]


# ----- a season file that cannot be used -----

def corrupt(path, how):
    raw = path.read_bytes()
    if how == "empty":
        path.write_bytes(b"")
    elif how == "half":
        path.write_bytes(raw[:len(raw) // 2 + 1])
    elif how == "random":
        path.write_bytes(bytes(random.Random(1).randrange(256) for _ in range(len(raw))))
    elif how == "text":
        path.write_bytes(b"this is not a season file at all, it is text\r\n")
    elif how == "huge":
        path.write_bytes(b"\x00" * 2_000_000)
    elif how == "missing":
        path.unlink()


@pytest.mark.parametrize("how", ["empty", "half", "random", "text", "huge", "missing"])
@pytest.mark.parametrize("name, gtp", [("footbal1.dat", 3), ("footbal2.dat", 3), ("football.gtp", 3), ("footbal3.dat", 3),
                                      ("footbal4.dat", 17), ("footbal5.dat", 18)])
def test_a_damaged_or_missing_season_file_gives_a_new_season_a_copy_and_one_notice(tmp_path, name, gtp, how):
    a_season_on_disk(tmp_path, gtp=gtp)
    names = a_names_file(tmp_path)
    corrupt(data(tmp_path, name), how)
    store = make(tmp_path)
    notices = store.take_notices()
    season = SeasonState()
    loaded = store.load_season(season)
    if name == "footbal1.dat" and how == "missing":                  # no footbal1.dat is a new season, nothing wrong
        assert notices == [] and loaded is False
    else:
        assert notices == [SEASON_DAMAGED] and loaded is False
        if how != "missing":
            copies = [n for n in os.listdir(tmp_path / "data") if n.startswith(name + ".damaged")]
            assert copies == [name + ".damaged1"], os.listdir(tmp_path / "data")
    leftovers = [n for n in os.listdir(tmp_path / "data") if ".damaged" not in n]
    assert leftovers == ["customize"]                                   # every season file is gone
    assert make(tmp_path).player_names().names() == names.names()       # the player's names are not part of a season
    assert make(tmp_path).take_notices() == []                          # the next start is a plain new season


def test_play_off_files_that_do_not_fit_the_week_are_damaged(tmp_path):
    a_season_on_disk(tmp_path, gtp=17)
    store = make(tmp_path)
    store.write_pairings(BASE_PAIRINGS[:3])                                # 4 games are due in week 17
    assert make(tmp_path).take_notices() == [SEASON_DAMAGED]
    a_season_on_disk(tmp_path, gtp=19)
    store = make(tmp_path)
    store.write_pairings([(TeamRef(1, 1), TeamRef(2, 2)), (TeamRef(5, 1), TeamRef(6, 1))])      # the player (3, 2) is in none
    assert make(tmp_path).take_notices() == [SEASON_DAMAGED]


def test_a_damaged_copy_is_kept_beside_the_file_and_three_are_kept(tmp_path):
    for round_ in range(5):
        a_season_on_disk(tmp_path, gtp=3)
        data(tmp_path, "footbal2.dat").write_bytes(b"junk %d" % round_)
        make(tmp_path)
    copies = sorted(n for n in os.listdir(tmp_path / "data") if n.startswith("footbal2.dat.damaged"))
    assert copies == ["footbal2.dat.damaged3", "footbal2.dat.damaged4", "footbal2.dat.damaged5"]
    assert data(tmp_path, copies[-1]).read_bytes() == b"junk 4"


def test_a_copied_original_season_with_singles_and_longs_is_accepted(tmp_path):
    """The values of an original's files are Integer, Long or Single Variants (D-024 item 4): rewrite ours that way."""
    a_season_on_disk(tmp_path, gtp=3)
    values = variant.unpack_numbers(data(tmp_path, "footbal3.dat").read_bytes())
    data(tmp_path, "footbal3.dat").write_bytes(b"".join(variant.pack_single(x) for x in values))
    data(tmp_path, "football.gtp").write_bytes(variant.pack_long(3))
    store = make(tmp_path)
    season = SeasonState()
    assert store.take_notices() == [] and store.load_season(season) and season.gtp == 3
    assert season.records.as_file_values() == records_of(BASE).as_file_values()


# ----- the writes -----

def test_every_write_is_one_whole_file_with_no_temporary_one_left(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=17)
    store.write_gtp(18)
    store.write_pairings([])                                  # the original deletes footbal4.dat first and may write nothing
    assert data(tmp_path, "footbal4.dat").read_bytes() == b""
    assert weekfile.decode(data(tmp_path, "football.gtp").read_bytes()) == 18
    assert not [n for n in os.listdir(tmp_path / "data") if n.endswith(".tmp")]


def test_a_second_write_replaces_the_first_and_shortens_the_file(tmp_path):
    store = make(tmp_path)
    store.write_pairings(BASE_PAIRINGS)
    store.write_pairings(BASE_PAIRINGS[:1])
    assert len(data(tmp_path, "footbal4.dat").read_bytes()) == 16 and pairingsfile.decode(data(tmp_path, "footbal4.dat").read_bytes()) == BASE_PAIRINGS[:1]


def test_the_schedule_is_written_with_the_types_of_the_team_chosen_before_it(tmp_path):
    store = make(tmp_path)
    store.write_coach_and_team(7, 4, "Bo")
    store.write_schedule(make_schedule(GameRandom(random.Random(2)), 7, 4))
    assert len(data(tmp_path, "footbal2.dat").read_bytes()) == 6 * 12 + 10 * 18


def test_the_data_folder_is_made_when_the_first_file_is_written(tmp_path):
    store = make(tmp_path)
    assert not (tmp_path / "data").exists()
    store.write_gtp(1)
    assert (tmp_path / "data" / "football.gtp").is_file()


def test_the_season_end_keeps_the_names_as_previous_replaces_it_next_time_and_is_safe_to_repeat(tmp_path):
    a_season_on_disk(tmp_path, gtp=17)
    first = a_names_file(tmp_path)
    store = make(tmp_path)
    store.delete_season_files()
    assert sorted(os.listdir(tmp_path / "data")) == ["customize"]
    custom = tmp_path / "data" / "customize"
    assert os.listdir(custom) == ["footplay.previous.txt"]
    assert playernames.parse(custom.joinpath("footplay.previous.txt").read_text(encoding="utf-8")).roster.names() == first.names()
    store.delete_season_files()                                          # the exit calls it again: nothing is lost
    assert os.listdir(custom) == ["footplay.previous.txt"]
    second = Roster(*[[f"n{h}{i}" for i in range(c)] for h, c in zip("rdkst", COUNTS)])
    assert store.write_player_names(second)
    store.delete_season_files()
    assert playernames.parse(custom.joinpath("footplay.previous.txt").read_text(encoding="utf-8")).roster.names() == second.names()


def test_a_season_end_clears_what_a_later_load_would_have_returned(tmp_path):
    a_season_on_disk(tmp_path, gtp=3)
    store = make(tmp_path)
    store.delete_season_files()
    assert store.load_season(SeasonState()) is False


# ----- the saved game -----

def test_a_saved_game_is_written_found_at_the_next_start_read_and_deleted(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    saved = a_game()
    assert store.save_game(saved) is True
    again = make(tmp_path)
    assert again.take_notices() == [] and again.has_saved_game() is True
    assert again.take_saved_game() == saved
    assert not data(tmp_path, "football.sav").exists() and again.has_saved_game() is False
    assert again.take_saved_game() is None


def test_a_saved_game_of_the_original_without_the_extra_value_is_accepted(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game(opening=None))
    again = make(tmp_path)
    assert again.has_saved_game() and again.take_saved_game().opening_receiver is None


@pytest.mark.parametrize("how", ["empty", "half", "random", "text", "huge"])
def test_a_saved_game_that_cannot_be_read_is_set_aside_with_one_notice_and_the_season_goes_on(tmp_path, how):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game())
    corrupt(data(tmp_path, "football.sav"), how)
    again = make(tmp_path)
    assert again.take_notices() == [SAVED_DAMAGED] and again.has_saved_game() is False
    assert os.path.exists(data(tmp_path, "football.sav.damaged1")) and not data(tmp_path, "football.sav").exists()
    assert again.load_season(SeasonState())                                  # the season itself is fine


def test_a_saved_game_that_belongs_to_no_season_is_set_aside(tmp_path):
    store = make(tmp_path)
    store.save_game(a_game())
    again = make(tmp_path)
    assert again.take_notices() == [SAVED_DAMAGED] and again.has_saved_game() is False
    assert os.path.exists(data(tmp_path, "football.sav.damaged1"))


def test_a_damaged_season_takes_its_saved_game_with_it_and_says_both(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game())
    corrupt(data(tmp_path, "footbal2.dat"), "half")
    again = make(tmp_path)
    assert again.take_notices() == [SEASON_DAMAGED, SAVED_DAMAGED] and again.has_saved_game() is False


def test_a_saved_game_that_goes_bad_between_the_start_and_the_game_is_handled_too(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game())
    again = make(tmp_path)
    assert again.has_saved_game()
    data(tmp_path, "football.sav").write_bytes(b"cut")
    assert again.take_saved_game() is None and again.take_notices() == [SAVED_DAMAGED]


def test_a_saved_game_that_cannot_be_written_says_so_to_the_caller(tmp_path):
    (tmp_path / "data").write_text("a file where the data folder should be")
    store = make(tmp_path)
    assert store.save_game(a_game()) is False
    assert store.take_notices() == [UNWRITABLE]


# ----- footplay.txt -----

def test_footplay_is_missing_complete_or_partly_wrong(tmp_path):
    store = make(tmp_path)
    assert store.player_names() is None and store.take_notices() == []
    roster = a_names_file(tmp_path)
    again = make(tmp_path)
    got = again.player_names()
    assert got.names() == roster.names() and got.quarterback == "Unitas" and again.take_notices() == []
    path = tmp_path / "data" / "customize" / "footplay.txt"
    path.write_text(path.read_text(encoding="utf-8").replace("r5\n", ""), encoding="utf-8")
    partial = make(tmp_path)
    got = partial.player_names()
    assert got.running_backs == [] and got.receivers == roster.receivers and got.quarterback == "Unitas"
    assert partial.take_notices() == [NAMES_REPAIRED]
    assert os.path.exists(str(path) + ".damaged1")


def test_footplay_that_is_not_text_is_replaced_with_a_copy_and_one_notice(tmp_path):
    path = tmp_path / "data" / "customize" / "footplay.txt"
    path.parent.mkdir(parents=True)
    for number, junk in enumerate((b"\x00\x01\x02 binary", b"", b"hello\nthere\n", b"\xff\xfe\x00\x00"), start=1):
        path.write_bytes(junk)
        store = make(tmp_path)
        assert store.player_names() is None
        assert store.take_notices() == [NAMES_REPLACED], junk


def test_the_quarterback_is_appended_replaced_and_never_doubled(tmp_path):
    roster = a_names_file(tmp_path, Roster(*[[f"{h}{i}" for i in range(c)] for h, c in zip("rdkst", COUNTS)]))
    store = make(tmp_path)
    assert store.player_names().quarterback == ""
    store.append_quarterback("Starr")
    assert make(tmp_path).player_names().quarterback == "Starr"
    store.append_quarterback("Namath")
    assert make(tmp_path).player_names().quarterback == "Namath"
    text = (tmp_path / "data" / "customize" / "footplay.txt").read_text(encoding="utf-8")
    assert text.count("Quarterback:") == 1 and playernames.parse(text).roster.names() == roster.names()


def test_appending_a_quarterback_to_a_missing_file_makes_a_file_with_only_him(tmp_path):
    make(tmp_path).append_quarterback("Starr")
    text = (tmp_path / "data" / "customize" / "footplay.txt").read_text(encoding="utf-8")
    assert text.splitlines() == ["Quarterback:", "Starr"]
    again = make(tmp_path)
    got = again.player_names()
    assert got.quarterback == "Starr" and got.names() == [] and again.take_notices() == [NAMES_REPLACED]


def test_a_footplay_the_player_saved_with_a_windows_code_page_is_read(tmp_path):
    roster = Roster(*[[f"{h}{i}" for i in range(c)] for h, c in zip("rdkst", COUNTS)], quarterback="Unitas")
    roster.running_backs[0] = "Márquez"
    path = tmp_path / "data" / "customize" / "footplay.txt"
    path.parent.mkdir(parents=True)
    path.write_bytes(playernames.format_roster(roster).encode("cp1252"))
    store = make(tmp_path)
    assert store.player_names().running_backs[0] == "Márquez" and store.take_notices() == []


# ----- a folder or file that cannot be used -----

def test_a_folder_that_cannot_be_written_is_told_once_and_the_game_goes_on(tmp_path):
    (tmp_path / "data").write_text("a file where the data folder should be")
    store = make(tmp_path)
    assert store.take_notices() == []
    store.write_gtp(1)
    store.write_records(Records())
    store.write_coach_and_team(1, 1, "Kim")
    assert store.take_notices() == [UNWRITABLE]
    store.write_gtp(2)
    assert store.take_notices() == []                                       # once
    assert store.load_season(SeasonState()) is False and store.player_names() is None


def test_a_read_only_file_is_not_replaced_and_is_told(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    path = data(tmp_path, "football.gtp")
    os.chmod(path, stat.S_IREAD)
    try:
        store.write_gtp(4)
        assert store.take_notices() == [UNWRITABLE]
        assert weekfile.decode(path.read_bytes()) == 3
        assert not [n for n in os.listdir(tmp_path / "data") if n.endswith(".tmp")]
    finally:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


@pytest.mark.skipif(sys.platform != "win32", reason="a sharing violation is a Windows thing")
def test_a_file_held_open_by_another_program_is_not_called_damaged_and_is_not_deleted(tmp_path):
    import ctypes
    from ctypes import wintypes
    a_season_on_disk(tmp_path, gtp=3)
    path = data(tmp_path, "footbal2.dat")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                     wintypes.DWORD, wintypes.HANDLE]
    handle = kernel32.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)      # GENERIC_READ, no sharing
    assert handle not in (None, wintypes.HANDLE(-1).value)
    try:
        store = make(tmp_path)
        assert store.take_notices() == [LOCKED] and store.load_season(SeasonState()) is False
        assert not [n for n in os.listdir(tmp_path / "data") if ".damaged" in n]
        store.write_gtp(9)                                                       # nothing is written this run
        store.write_coach_and_team(1, 1, "New")
        assert weekfile.decode(data(tmp_path, "football.gtp").read_bytes()) == 3
        assert data(tmp_path, "footbal1.dat").exists() and path.exists()      # nothing was removed
    finally:
        kernel32.CloseHandle(handle)
    assert make(tmp_path).load_season(SeasonState()) is True                   # released: the season is there


# ----- the log -----

def test_the_log_goes_to_footballlog_txt_in_the_data_folder(tmp_path):
    store = make(tmp_path)
    store.log_line("not yet open")
    store.open_log(True)
    store.log_line("NFL Football 4")
    store.close()
    assert data(tmp_path, "footballlog.txt").read_bytes() == b"NFL Football 4\r\n"
    store = make(tmp_path)
    store.open_log(False)
    store.log_line("second run")
    store.close()
    assert data(tmp_path, "footballlog.txt").read_bytes() == b"NFL Football 4\r\nsecond run\r\n"


# ----- fuzz -----

def test_a_few_hundred_random_corruptions_never_stop_the_start_and_leave_a_valid_season_or_none(tmp_path_factory):
    rng = random.Random(2026)
    names = ["footbal1.dat", "footbal2.dat", "football.gtp", "footbal3.dat", "footbal4.dat", "footbal5.dat", "football.sav"]
    for round_ in range(150):
        tmp_path = tmp_path_factory.mktemp("fuzz")
        gtp = rng.choice([1, 2, 5, 16, 17, 18, 19, 20])
        store = a_season_on_disk(tmp_path, gtp=gtp)
        store.save_game(a_game())
        names_file = a_names_file(tmp_path)
        for _ in range(rng.randint(1, 3)):
            path = data(tmp_path, rng.choice(names))
            if not path.exists():
                continue
            raw = bytearray(path.read_bytes())
            how = rng.choice(["flip", "cut", "grow", "zero", "delete"])
            if how == "flip" and raw:
                raw[rng.randrange(len(raw))] = rng.randrange(256)
            elif how == "cut" and raw:
                del raw[rng.randrange(len(raw)):]
            elif how == "grow":
                raw += bytes(rng.randrange(256) for _ in range(rng.randrange(1, 9)))
            elif how == "zero":
                raw = bytearray(len(raw))
            if how == "delete":
                path.unlink()
            else:
                path.write_bytes(bytes(raw))
        again = make(tmp_path)
        season = SeasonState()
        if again.load_season(season):
            assert 1 <= season.gtp <= 20 and 1 <= season.tn1 <= 8 and 1 <= season.tn2 <= 4 and len(season.schedule) == 16
            if season.gtp >= 17:
                assert season.playoffs.contains_player(season.own_team)
        else:
            assert not again.has_saved_game()
        again.take_saved_game()
        got = again.player_names()
        if got is not None:
            assert got.names() == names_file.names()                      # the names never go with a damaged season
        else:                                                             # a week of 0 is a season that ended: names kept
            previous = tmp_path / "data" / "customize" / "footplay.previous.txt"
            assert playernames.parse(previous.read_text(encoding="utf-8")).roster.names() == names_file.names()
        notices = again.take_notices()
        assert all(n in (SEASON_DAMAGED, SAVED_DAMAGED) for n in notices) and len(set(notices)) == len(notices)


# ----- what the independent review found (S7.5) -----

def test_a_saved_game_made_at_the_start_of_quarter_3_or_overtime_has_a_play_counter_of_0_and_is_kept(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    saved = a_game()
    saved.counter = 0
    assert store.save_game(saved)
    again = make(tmp_path)
    assert again.take_notices() == [] and again.has_saved_game() and again.take_saved_game().counter == 0


def test_a_season_that_cannot_be_read_for_another_reason_is_not_damage_and_keeps_the_saved_game(tmp_path, monkeypatch):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game())
    names = a_names_file(tmp_path)
    from nfl4.data.files import store as store_module
    real = store_module.read_bytes

    def broken(path, *args, **kwargs):
        if path.endswith("footbal2.dat"):
            raise OSError(5, "a cloud placeholder that cannot be fetched")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(store_module, "read_bytes", broken)
    again = make(tmp_path)
    assert again.take_notices() == [LOCKED] and again.load_season(SeasonState()) is False
    assert again.has_saved_game() is False
    assert data(tmp_path, "football.sav").exists() and data(tmp_path, "footbal1.dat").exists()      # nothing judged or deleted
    assert not [n for n in os.listdir(tmp_path / "data") if ".damaged" in n]
    again.write_coach_and_team(1, 1, "New")                       # nothing is written over the real season this run
    again.delete_season_files()                                   # a "season end" of the temporary season deletes nothing
    assert coachteam_of(tmp_path) == "Kim Lee"
    assert again.write_player_names(names) is False               # and the names file stays as it is
    assert (tmp_path / "data" / "customize" / "footplay.txt").exists()


def coachteam_of(tmp_path):
    from nfl4.data.files import coachteam
    return coachteam.decode(data(tmp_path, "footbal1.dat").read_bytes()).coach


def test_a_names_file_that_cannot_be_opened_is_never_written_over_that_run(tmp_path, monkeypatch):
    names = a_names_file(tmp_path)
    from nfl4.data.files import store as store_module
    from nfl4.data.healing import FileInUse
    path = tmp_path / "data" / "customize" / "footplay.txt"
    before = path.read_bytes()
    monkeypatch.setattr(store_module, "read_player_text", lambda p: (_ for _ in ()).throw(FileInUse("locked")))
    store = make(tmp_path)
    assert store.player_names() is None
    assert store.write_player_names(names) is False
    store.append_quarterback("Starr")
    store.delete_season_files()
    assert path.read_bytes() == before and not (tmp_path / "data" / "customize" / "footplay.previous.txt").exists()


def test_names_that_cannot_be_copied_stay_where_they_are_at_a_season_end(tmp_path, monkeypatch):
    names = a_names_file(tmp_path)
    a_season_on_disk(tmp_path, gtp=3)
    import shutil

    def no_copy(*args, **kwargs):
        raise OSError(28, "no space left on device")

    monkeypatch.setattr(shutil, "copyfile", no_copy)
    store = make(tmp_path)
    store.delete_season_files()
    assert (tmp_path / "data" / "customize" / "footplay.txt").exists()
    assert make(tmp_path).player_names().names() == names.names()
    assert not data(tmp_path, "footbal1.dat").exists()


def test_a_write_that_cannot_be_encoded_is_a_failed_write_not_an_error(tmp_path):
    store = make(tmp_path)
    store.write_gtp(99999)                                        # does not fit an Integer
    assert store.take_notices() == [UNWRITABLE] and not data(tmp_path, "football.gtp").exists()
    bad = Roster(*[["x" * 3] * c for c in COUNTS], quarterback="Unitas")
    bad.running_backs[0] = "Zo\ud800"                              # a lone surrogate cannot be written as UTF-8
    assert store.write_player_names(bad) is False
    store.append_quarterback("Bad\ud800name")                     # nor can this
    assert not (tmp_path / "data" / "customize" / "footplay.txt").exists()
    assert not [n for n in os.listdir(tmp_path / "data" / "customize") if n.endswith(".tmp")] if (tmp_path / "data" / "customize").exists() else True


def test_a_saved_game_that_cannot_be_read_when_taken_is_not_an_error(tmp_path, monkeypatch):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game())
    again = make(tmp_path)
    from nfl4.data.files import store as store_module
    monkeypatch.setattr(store_module, "read_bytes", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("gone")))
    assert again.take_saved_game() is None


def test_a_write_is_flushed_to_the_disk_before_it_replaces_the_file(tmp_path, monkeypatch):
    synced = []
    real = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (synced.append(fd), real(fd))[1])
    make(tmp_path).write_gtp(4)
    assert synced and weekfile.decode(data(tmp_path, "football.gtp").read_bytes()) == 4
