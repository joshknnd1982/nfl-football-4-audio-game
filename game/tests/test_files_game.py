"""The real files and the real game: footplay.txt, the quarterback line and football.sav through pag (data/files/store.py). This is inspired by Jim Kitchen.

GAME_SPEC 4.12, 4.18, 5.5 and 12: pag draws the player's 33 names when footplay.txt does not give them and writes the file
(0x455908 to 0x456f0b), Getqbs appends the quarterback (0x431978 to 0x4319ba), Save Game writes football.sav (0x45f655) and
the next start reads it back and deletes it. S7.5, D-024 items 4 and 5, D-025 d, G-F5.
"""
from savesrig import read_saved
import random

from nfl4.data.files import playernames, savedgame
from nfl4.data.files.store import FileProgramStore
from nfl4.game import program_texts, prompt_texts
from nfl4.game.gamestate import SavedGame
from nfl4.game.rnd import GameRandom
from nfl4.game.schedule import make_schedule
from nfl4.game.setup import COUNTS
from nfl4.game.standings import Records
from pagrig import Draws, engine_rig, make_rig, play, run_steps, texts

ENTER, UP = 13, 38


def make(tmp_path):
    return FileProgramStore(str(tmp_path / "data"), str(tmp_path / "data" / "customize"))


def names_path(tmp_path):
    return tmp_path / "data" / "customize" / "footplay.txt"


def own_asked(spoken):
    """How often the player's own quarterback was asked for (the prompt starts with the coach's name)."""
    return sum(prompt_texts.ENTER_OWN_QUARTERBACK in text for text in spoken)


def a_whole_game(tmp_path, store, seed, own_names=None, **kwargs):
    rig = make_rig(tmp_path / f"rig{seed}", rng=random.Random(seed), fast=True)
    rig.game.setup_store = store
    result = play(rig, quarterback_names=None, own_names=own_names, roster_sink=store.write_player_names, **kwargs)
    return rig, result


def test_the_first_game_of_a_season_draws_the_names_writes_footplay_txt_and_appends_the_quarterback(tmp_path):
    store = make(tmp_path)
    assert store.player_names() is None
    rig, result = a_whole_game(tmp_path, store, 5)
    assert result.scores is not None
    text = names_path(tmp_path).read_text(encoding="utf-8")
    parsed = playernames.parse(text)
    assert parsed.sound and parsed.roster.is_complete() and parsed.roster.quarterback        # all 33 names and the quarterback
    assert len(set(parsed.roster.names())) == 33                                              # drawn without replacement
    lines = text.splitlines()
    assert lines[0] == "Running Backs:" and lines[-2] == "Quarterback:"
    assert [len(names) for _, names in parsed.roster.sections()] == list(COUNTS)
    spoken = texts(rig)
    assert own_asked(spoken) == 1                                                             # the first game asks for him


def test_the_second_game_reads_the_file_keeps_the_names_and_asks_only_for_the_opponents_quarterback(tmp_path):
    store = make(tmp_path)
    a_whole_game(tmp_path, store, 5)
    first = names_path(tmp_path).read_text(encoding="utf-8")
    again = make(tmp_path)
    roster = again.player_names()
    assert roster is not None and again.take_notices() == [] and roster.quarterback
    rig, result = a_whole_game(tmp_path, again, 6, own_names=roster)
    assert result.scores is not None
    assert names_path(tmp_path).read_text(encoding="utf-8") == first                         # nothing was drawn or written
    spoken = texts(rig)
    assert own_asked(spoken) == 0
    assert any(t.startswith(prompt_texts.ENTER_THE_NAME_OF_THE) for t in spoken)


def test_a_player_who_renamed_a_running_back_keeps_the_name_for_the_next_game(tmp_path):
    store = make(tmp_path)
    a_whole_game(tmp_path, store, 7)
    path = names_path(tmp_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1] = "Gale Sayers"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    again = make(tmp_path)
    roster = again.player_names()
    assert roster.running_backs[0] == "Gale Sayers" and again.take_notices() == []
    a_whole_game(tmp_path, again, 8, own_names=roster)
    assert path.read_text(encoding="utf-8").splitlines()[1] == "Gale Sayers"


def test_a_footplay_with_one_wrong_section_is_repaired_by_the_game_and_the_rest_stays(tmp_path):
    store = make(tmp_path)
    a_whole_game(tmp_path, store, 9)
    path = names_path(tmp_path)
    good = playernames.parse(path.read_text(encoding="utf-8")).roster
    path.write_text(path.read_text(encoding="utf-8").replace(good.receivers[-1] + "\n", "", 1), encoding="utf-8")
    again = make(tmp_path)
    partial = again.player_names()
    assert partial.receivers == [] and partial.running_backs == good.running_backs
    assert len(again.take_notices()) == 1
    a_whole_game(tmp_path, again, 10, own_names=partial)
    repaired = playernames.parse(path.read_text(encoding="utf-8"))
    assert repaired.sound and repaired.roster.is_complete()
    assert repaired.roster.running_backs == good.running_backs and repaired.roster.defense == good.defense
    assert repaired.roster.quarterback == good.quarterback
    assert repaired.roster.receivers != good.receivers and len(repaired.roster.receivers) == 6
    assert make(tmp_path).take_notices() == [] and make(tmp_path).player_names().names() == repaired.roster.names()


def test_a_footplay_without_the_quarterback_asks_for_him_again_and_appends_him(tmp_path):
    store = make(tmp_path)
    a_whole_game(tmp_path, store, 11)
    path = names_path(tmp_path)
    path.write_text(path.read_text(encoding="utf-8").split("Quarterback:")[0], encoding="utf-8")
    again = make(tmp_path)
    roster = again.player_names()
    assert roster.quarterback == "" and roster.is_complete()
    rig, _ = a_whole_game(tmp_path, again, 12, own_names=roster)
    assert own_asked(texts(rig)) == 1
    assert make(tmp_path).player_names().quarterback


# ----- Save Game -----

def saving_rig(tmp_path, sink):
    rig = engine_rig(tmp_path, [UP, ENTER], wisoff=1, defense=2, half=2, yard_line=22, down=1, to_go=10, quarter=3, counter=12)
    rig.engine.save_sink = sink
    return rig


def test_save_game_writes_football_sav_and_the_next_start_loads_and_deletes_it(tmp_path):
    store = make(tmp_path)
    store.write_gtp(3)                                          # a season for the saved game to belong to
    rig = saving_rig(tmp_path, store.save_game)
    rig.engine.s.stats[2].score = 14
    rig.engine.s.opening_receiver = 2
    assert run_steps(rig, rig.engine.offense_menu, Draws(), until=("never",)) is None
    assert texts(rig)[-1] == " Game Saved "
    assert (tmp_path / "data" / "football.sav").is_file()
    record = savedgame.decode((tmp_path / "data" / "football.sav").read_bytes())
    assert (record.wisoff, record.quarter, record.counter, record.yard_line, record.opening_receiver) == (1, 3, 12, 22, 2)
    assert record.stats[2].score == 14 and record.opponent_quarterback == "Unitas"


def test_a_save_that_cannot_be_written_says_so_and_the_game_goes_on(tmp_path):
    rig = saving_rig(tmp_path, lambda record: False)
    assert run_steps(rig, rig.engine.offense_menu, Draws(), until=("play_menu",)) == "play_menu"
    assert texts(rig)[-1] == program_texts.SAVE_FAILED
    assert " Game Saved " not in texts(rig) and rig.engine.result.saved is False
    assert not [e for e in rig.slot_log if e.action == "stop" and e.slot in (1, 2)]


def test_a_sink_that_returns_nothing_is_a_save_as_before(tmp_path):
    saved = []
    rig = saving_rig(tmp_path, saved.append)
    assert run_steps(rig, rig.engine.offense_menu, Draws(), until=("never",)) is None
    assert texts(rig)[-1] == " Game Saved " and len(saved) == 1 and rig.engine.result.saved


def test_a_whole_saved_game_survives_the_file_and_is_loaded_by_pag(tmp_path):
    store = make(tmp_path)
    store.write_coach_and_team(1, 1, "Kim")                     # a saved game belongs to a season
    store.write_schedule(make_schedule(GameRandom(random.Random(5)), 1, 1))
    store.write_gtp(3)
    store.write_records(Records())
    stats_game = SavedGame(2, 1, 1, 3, 12, [31, 32, 33, 34, 35], 71.5, {}, 40, 2, 6, "Namath", 1)
    from nfl4.game.gamestate import SideStats
    stats_game.stats = {1: SideStats(score=10), 2: SideStats(score=3)}
    assert store.save_game(stats_game)
    again = make(tmp_path)
    saved = read_saved(again)
    assert saved == stats_game
    rig = make_rig(tmp_path / "rig", answers=["7", ENTER])
    result = play(rig, saved=saved, quarterback_names=lambda s: ("Starr", s.quarterbacks[2]))
    assert result.saved and texts(rig)[0] == " getting saved game "
