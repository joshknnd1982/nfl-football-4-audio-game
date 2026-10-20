"""The program on the real files: a start from every state (data/files/store.py under game/program.py). This is inspired by Jim Kitchen.

GAME_SPEC 3 steps 6 to 9, D-024 items 1, 4 and 5, D-046 item 2, G-F3 to G-F5, G-S10. The rig of tests/programrig.py runs
Form_Load's flow on the virtual clock with a stand-in for pag; here the store behind it is the real one over a temporary data
folder, and each test starts the program again over the same folder with a new store, the way a second launch does.
"""
from savesrig import read_saved
import os

import pytest

from nfl4.data.files import playernames, savedgame
from nfl4.data.files.store import (NAMES_REPAIRED, SAVED_DAMAGED, SEASON_DAMAGED, UNWRITABLE, FileProgramStore)
from nfl4.game import program_texts as P
from nfl4.game import prompt_texts as T
from nfl4.game import texts
from nfl4.game.pag import GameResult
from nfl4.game.season import SeasonState
from programrig import DOWN, ENTER, Outcome, played, program_rig, said
from test_files_savedgame import a_game
from test_files_store import TEAM, a_names_file, a_season_on_disk, data, make

EXIT_KEYS = [DOWN, DOWN, DOWN, ENTER]
WEEK_1 = " This is week  1 of Josh Kennedy's N. F. L. football "
NEW_SEASON = ["k", "i", "m", ENTER, ENTER, ENTER, ENTER]       # the coach "kim", yes; the first team, yes


def file_rig(tmp_path, answers, store=None, **kwargs):
    store = store or make(tmp_path)
    rig = program_rig(tmp_path / "rig", answers, **kwargs)
    game = rig.game
    game.program_store = rig.store = store
    game.season_store = game.setup_store = store
    game.log_sink = store.log_line
    game.notice_sources = (store,)
    return rig


def run(rig):
    rig.run()
    rig.store.close()
    return rig


def test_a_new_season_writes_footbal1_footbal2_and_football_gtp_and_the_next_start_loads_it(tmp_path):
    rig = run(file_rig(tmp_path, NEW_SEASON + EXIT_KEYS))
    assert said(rig)[1] == T.ENTER_COACH and WEEK_1 in said(rig)
    assert sorted(p.name for p in (tmp_path / "data").iterdir()) == ["footbal1.dat", "footbal2.dat", "football.gtp", "footballlog.txt"]
    again = run(file_rig(tmp_path / "second", EXIT_KEYS, store=make(tmp_path)))
    spoken = said(again)
    assert T.ENTER_COACH not in spoken and spoken[1] == WEEK_1
    assert (again.game.season.coach, again.game.season.tn1, again.game.season.tn2, again.game.season.gtp) == ("kim", 1, 1, 1)
    assert again.game.season.schedule == rig.game.season.schedule and len(again.game.season.schedule) == 16


def test_the_log_is_a_new_file_in_week_1_and_appended_to_later(tmp_path):
    run(file_rig(tmp_path, NEW_SEASON + EXIT_KEYS))
    log = data(tmp_path, "footballlog.txt").read_bytes().decode("utf-8").split("\r\n")
    assert log[:3] == [texts.CAPTION, "", " This is week #1 of Josh Kennedy's N. F. L. football "]
    a_season_on_disk(tmp_path, gtp=4)
    before = data(tmp_path, "footballlog.txt").read_bytes()
    run(file_rig(tmp_path / "later", EXIT_KEYS, store=make(tmp_path)))
    after = data(tmp_path, "footballlog.txt").read_bytes()
    assert after.startswith(before) and len(after) > len(before)
    assert b" This is week #4 of Josh Kennedy's N. F. L. football " in after[len(before):]


def test_a_season_on_disk_in_week_5_is_the_week_the_program_announces(tmp_path):
    a_season_on_disk(tmp_path, gtp=5)
    rig = run(file_rig(tmp_path, EXIT_KEYS))
    assert said(rig)[:2] == [texts.TITLE_SPOKEN, " This is week  5 of Josh Kennedy's N. F. L. football "]
    assert rig.game.season.coach == "Kim Lee" and (rig.game.season.tn1, rig.game.season.tn2) == TEAM
    assert rig.game.season.set_week_opponent() is not None


def test_a_play_off_season_on_disk_announces_its_round_and_finds_the_players_opponent(tmp_path):
    a_season_on_disk(tmp_path, gtp=17)
    rig = run(file_rig(tmp_path, EXIT_KEYS))
    assert said(rig)[1] == " This is the " and rig.game.season.opponent_team.division == 4


def test_a_damaged_season_is_said_after_the_title_then_a_new_season_is_set_up(tmp_path):
    a_season_on_disk(tmp_path, gtp=3)
    data(tmp_path, "footbal2.dat").write_bytes(b"cut")
    rig = run(file_rig(tmp_path, NEW_SEASON + EXIT_KEYS))
    spoken = said(rig)
    assert spoken[:3] == [texts.TITLE_SPOKEN, SEASON_DAMAGED, T.ENTER_COACH] and WEEK_1 in spoken
    names = sorted(p.name for p in (tmp_path / "data").iterdir())
    assert [n for n in names if ".damaged" not in n] == ["footbal1.dat", "footbal2.dat", "football.gtp", "footballlog.txt"]
    assert "footbal2.dat.damaged1" in names and "footbal1.dat.damaged1" in names      # every old season file kept as a copy
    assert rig.game.season.gtp == 1 and rig.game.season.coach == "kim"


def test_a_saved_game_skips_the_menu_goes_to_pag_and_is_deleted(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    saved = a_game()
    store.save_game(saved)
    rig = run(file_rig(tmp_path, [ENTER] + EXIT_KEYS, store=make(tmp_path), outcomes=[played()]))   # a key ends the standings
    assert rig.plays[0]["saved"] == saved
    assert not data(tmp_path, "football.sav").exists()
    assert [t for t in said(rig) if t.startswith(" 1. play game")] != []


def test_save_game_inside_the_program_writes_football_sav_and_ends_the_program(tmp_path):
    a_season_on_disk(tmp_path, gtp=3)

    def save(rig):
        assert rig.plays[-1]["save_sink"](a_game()) is True
        return Outcome(GameResult(scores=None, saved=True), stop_beds=False)

    rig = run(file_rig(tmp_path, [ENTER], store=make(tmp_path), outcomes=[save]))
    assert rig.game.program.ending == "saved"
    assert savedgame.decode(data(tmp_path, "football.sav").read_bytes()) == a_game()
    again = make(tmp_path)
    assert again.take_notices() == [] and again.has_saved_game()


def test_a_damaged_saved_game_is_not_loaded_and_not_set_aside_and_the_season_goes_on(tmp_path):
    store = a_season_on_disk(tmp_path, gtp=3)
    store.save_game(a_game())
    data(tmp_path, "football.sav").write_bytes(b"cut")
    rig = run(file_rig(tmp_path, EXIT_KEYS, store=make(tmp_path)))
    spoken = said(rig)
    assert spoken[:2] == [texts.TITLE_SPOKEN, " This is week  3 of Josh Kennedy's N. F. L. football "]      # SX.14: the start-up menu names it; the store does not
    assert (tmp_path / "data" / "football.sav").exists() and not (tmp_path / "data" / "football.sav.damaged1").exists() and rig.plays == []


def test_a_season_that_ends_keeps_the_names_as_previous_and_starts_the_next_season(tmp_path):
    names = a_names_file(tmp_path)
    a_season_on_disk(tmp_path, gtp=20)
    final = Outcome(GameResult(scores=(24, 17)), gtp=0)
    rig = run(file_rig(tmp_path, [ENTER] + NEW_SEASON + EXIT_KEYS, store=make(tmp_path), outcomes=[final]))
    assert P.SEASON_OVER in said(rig)
    custom = tmp_path / "data" / "customize"
    assert [p.name for p in custom.iterdir()] == ["footplay.previous.txt"]
    kept = playernames.parse((custom / "footplay.previous.txt").read_text(encoding="utf-8"))
    assert kept.roster.names() == names.names() and kept.roster.quarterback == "Unitas"
    assert sorted(p.name for p in (tmp_path / "data").iterdir() if p.is_file()) == [
        "footbal1.dat", "footbal2.dat", "football.gtp", "footballlog.txt"]
    assert make(tmp_path).load_season(SeasonState())                      # the new season is on disk, week 1


def test_a_footplay_with_a_problem_is_said_before_the_game_and_the_game_gets_the_good_part(tmp_path):
    names = a_names_file(tmp_path)
    a_season_on_disk(tmp_path, gtp=3)
    path = tmp_path / "data" / "customize" / "footplay.txt"
    path.write_text(path.read_text(encoding="utf-8").replace("r5\n", "", 1), encoding="utf-8")
    rig = run(file_rig(tmp_path, [ENTER, ENTER] + EXIT_KEYS, store=make(tmp_path), outcomes=[played()]))   # play, a key ends the standings
    spoken = said(rig)
    assert NAMES_REPAIRED in spoken and spoken.index(NAMES_REPAIRED) > spoken.index(" 1. play game ")
    roster = rig.plays[0]["own_names"]
    assert roster.running_backs == [] and roster.receivers == names.receivers and roster.quarterback == "Unitas"
    assert rig.plays[0]["roster_sink"] == rig.store.write_player_names


def test_a_data_folder_that_cannot_be_written_is_said_once_and_the_game_plays_on(tmp_path):
    (tmp_path / "data").write_text("a file where the data folder should be")
    rig = run(file_rig(tmp_path, NEW_SEASON + EXIT_KEYS))
    spoken = said(rig)
    assert spoken.count(UNWRITABLE) == 1 and spoken.index(UNWRITABLE) < spoken.index(WEEK_1)
    assert rig.game.season.gtp == 1 and rig.game.season.coach == "kim"
