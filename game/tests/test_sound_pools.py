"""Numbered sound pools the player can extend (owner rule 0.14, playbook 7.7.1, audio/pools.py, D-068). This is inspired by Jim Kitchen.

With nothing added a pool is the original's list and every draw is the original's; added files named <pool><number> join
the draw; a switched-off original leaves it; an unreadable added file is skipped.
"""
import os

import pytest

from gamerig import Rig
from nfl4.audio.library import SoundLibrary
from nfl4.audio.output import SLOT_AMBIENT, SLOT_ONESHOT
from nfl4.audio.pools import POOLS, next_free_number, scan_added
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
from test_game_sounds import ScriptedRnd, plays, rnd_for
from wavmaker import write


def player_dir(tmp_path):
    folder = tmp_path / "sounds"
    folder.mkdir(parents=True)
    return folder


def listing(*names):
    return {name.lower(): name for name in names}


# ----- the scan -----

def test_the_scan_finds_pool_names_in_any_case_extension_and_zero_padding_in_number_order():
    found, skipped = scan_added(POOLS["celebration"], listing("Celebration10.WAV", "celebration2.ogg", "CELEBRATION003.flac",
                                                              "celebration4.mp3", "celebration5.txt", "celebration.wav",
                                                              "celebrations6.wav", "foot26.wav", "ambient1.wav"))
    assert [number for number, _ in found] == [2, 3, 4, 10] and skipped == []


def test_two_files_with_one_number_count_once_and_the_other_is_reported():
    found, skipped = scan_added(POOLS["ambient"], listing("ambient7.wav", "ambient07.ogg"))
    assert [n for n, _ in found] == [7] and len(skipped) == 1


def test_the_next_free_number_is_one_past_the_highest_added_one():
    assert next_free_number(POOLS["celebration"], []) == 1
    assert next_free_number(POOLS["celebration"], [(2, "a"), (9, "b")]) == 10


def test_the_pools_are_exactly_the_two_draws_of_the_original():
    assert POOLS["ambient"].originals == (8, 9, 10) and POOLS["celebration"].originals == tuple(range(15, 25))


# ----- nothing added: the original's draws, to the last draw -----

def test_with_nothing_added_the_pools_are_the_originals_lists(tmp_path):
    library = SoundLibrary(player_dir=str(player_dir(tmp_path)))
    assert [m.sound_id for m in library.pool_members("celebration")] == [f"snd_foot{n}" for n in range(15, 25)]
    assert [m.sound_id for m in library.pool_members("ambient")] == ["snd_foot8", "snd_foot9", "snd_foot10"]
    assert library.pool_summary("celebration") == (10, 0, 1)


def test_a_celebration_sound_with_nothing_added_draws_two_numbers_and_plays_the_chosen_original(tmp_path):
    rig = Rig(sounds_dir=player_dir(tmp_path), rng=ScriptedRnd([rnd_for(3, 10), rnd_for(30, 40)], seed=1))
    rig.sounds.celebration_sound()
    played = plays(rig, SLOT_ONESHOT)[-1]
    assert played.sound_id == "snd_foot18" and played.volume == -300 and rig.rnd.source.drawn == 2
    assert played.freq == max(8000, 11025 + 100 * 10)                        # k = 30 - 20


def test_an_ambient_sound_with_nothing_added_keeps_the_originals_three_branches(tmp_path):
    rig = Rig(sounds_dir=player_dir(tmp_path), rng=ScriptedRnd([rnd_for(2, 3), rnd_for(20, 30), 0.5], seed=1))
    rig.sounds.play_ran()                                                    # foot10: a pan draw, then the next-time draw
    played = plays(rig, SLOT_AMBIENT)[-1]
    assert played.sound_id == "snd_foot10" and played.pan == 500 and played.volume == -2900 + 500
    assert rig.rnd.source.drawn == 3
    rig2 = Rig(sounds_dir=player_dir(tmp_path / "b"), rng=ScriptedRnd([rnd_for(0, 3), 0.5], seed=1))
    rig2.sounds.play_ran()
    played = plays(rig2, SLOT_AMBIENT)[-1]
    assert played.sound_id == "snd_foot8" and played.volume == -250 and played.pan == 0 and rig2.rnd.source.drawn == 2


# ----- added files -----

def test_added_celebration_files_join_the_draw_after_the_originals_in_number_order(tmp_path):
    folder = player_dir(tmp_path)
    write(folder / "celebration2.wav", [0.2] * 400, rate=8000)
    write(folder / "celebration1.wav", [0.2] * 300, rate=22050)
    library = SoundLibrary(player_dir=str(folder))
    members = library.pool_members("celebration")
    assert len(members) == 12 and [m.number for m in members[10:]] == [1, 2] and all(m.added for m in members[10:])
    assert library.pool_summary("celebration") == (10, 2, 3)


def test_a_draw_that_lands_on_an_added_celebration_file_plays_it_with_the_random_pitch(tmp_path):
    folder = player_dir(tmp_path)
    write(folder / "celebration1.wav", [0.2] * 400, rate=22050)
    write(folder / "celebration2.wav", [0.2] * 400, rate=22050)
    rig = Rig(sounds_dir=folder, rng=ScriptedRnd([rnd_for(11, 12), rnd_for(25, 40)], seed=1))
    rig.sounds.celebration_sound()
    played = plays(rig, SLOT_ONESHOT)[-1]
    assert played.sound_id == "file celebration2.wav" and played.source == "player" and played.volume == -300
    assert played.freq == 22050 + 500 and rig.rnd.source.drawn == 2
    rig2 = Rig(sounds_dir=player_dir(tmp_path / "b"), rng=ScriptedRnd([rnd_for(0, 12)], seed=1))
    assert [m.sound_id for m in rig2.audio.library.pool_members("celebration")][0] == "snd_foot15"


def test_a_gap_in_the_numbers_is_fine_and_the_draw_range_is_the_member_count(tmp_path):
    folder = player_dir(tmp_path)
    write(folder / "celebration9.wav", [0.2] * 400, rate=11025)
    rig = Rig(sounds_dir=folder, rng=ScriptedRnd([rnd_for(10, 11), rnd_for(30, 40)], seed=1))
    rig.sounds.celebration_sound()
    assert plays(rig, SLOT_ONESHOT)[-1].sound_id == "file celebration9.wav"


def test_an_added_ambient_sound_plays_at_foot9s_level_centered(tmp_path):
    folder = player_dir(tmp_path)
    write(folder / "ambient1.wav", [0.2] * 400, rate=11025)
    rig = Rig(sounds_dir=folder, rng=ScriptedRnd([rnd_for(3, 4), 0.5], seed=1), sound_level=-300)
    rig.sounds.play_ran()
    played = plays(rig, SLOT_AMBIENT)[-1]
    assert played.sound_id == "file ambient1.wav" and played.volume == -1200 - 300 and played.pan == 0
    assert rig.rnd.source.drawn == 2


def test_a_file_dropped_in_later_joins_after_the_sounds_menus_reload(tmp_path):
    folder = player_dir(tmp_path)
    library = SoundLibrary(player_dir=str(folder))
    assert len(library.pool_members("ambient")) == 3
    write(folder / "ambient4.wav", [0.2] * 400, rate=11025)
    assert len(library.pool_members("ambient")) == 3                          # not before the reload
    library.refresh()
    assert len(library.pool_members("ambient")) == 4


# ----- switched off, damaged, replaced -----

def test_an_original_switched_off_in_sounds_txt_leaves_the_draw(tmp_path):
    folder = player_dir(tmp_path)
    (folder / FILE_NAME).write_text(DEFAULT_TEXT + "foot15 = off\n", encoding="utf-8")
    rig = Rig(sounds_dir=folder, rng=ScriptedRnd([rnd_for(0, 9), rnd_for(30, 40)], seed=1))
    assert len(rig.audio.library.pool_members("celebration")) == 9
    rig.sounds.celebration_sound()
    assert plays(rig, SLOT_ONESHOT)[-1].sound_id == "snd_foot16" and rig.rnd.source.drawn == 2


def test_a_pool_with_every_member_off_plays_nothing_and_still_costs_its_draw(tmp_path):
    folder = player_dir(tmp_path)
    off = "".join(f"foot{n} = off\n" for n in range(15, 25))
    (folder / FILE_NAME).write_text(DEFAULT_TEXT + off, encoding="utf-8")
    rig = Rig(sounds_dir=folder, rng=ScriptedRnd([0.5], seed=1))
    t0 = rig.clock()
    rig.sounds.celebration_sound()
    assert not plays(rig, SLOT_ONESHOT) and rig.rnd.source.drawn == 1 and rig.clock() - t0 < 0.002


def test_an_added_file_that_cannot_be_read_is_skipped_and_reported(tmp_path):
    folder = player_dir(tmp_path)
    (folder / "celebration1.wav").write_bytes(os.urandom(300))
    write(folder / "celebration2.wav", [0.2] * 400, rate=11025)
    library = SoundLibrary(player_dir=str(folder))
    members = library.pool_members("celebration")
    assert len(members) == 11 and members[-1].number == 2
    assert any("celebration1.wav" in problem for problem in library.problems)
    assert library.take_notices() and library.check_all() is not None


def test_a_player_file_with_an_original_members_name_replaces_it_and_adds_no_member(tmp_path):
    folder = player_dir(tmp_path)
    write(folder / "foot16.wav", [0.2] * 400, rate=11025)
    library = SoundLibrary(player_dir=str(folder))
    assert len(library.pool_members("celebration")) == 10
    assert library.pick("snd_foot16").source == "player"


def test_numbers_of_the_originals_that_are_not_pools_take_no_added_files(tmp_path):
    folder = player_dir(tmp_path)
    write(folder / "foot26.wav", [0.2] * 400, rate=11025)
    write(folder / "hit5.wav", [0.2] * 400, rate=11025)
    library = SoundLibrary(player_dir=str(folder))
    assert len(library.pool_members("celebration")) == 10 and len(library.pool_members("ambient")) == 3


def test_a_folder_of_thousands_of_names_scans_fast(tmp_path):
    import time
    folder = player_dir(tmp_path)
    for number in range(1, 2001):
        (folder / f"celebration{number}.wav").write_bytes(b"")
    started = time.perf_counter()
    library = SoundLibrary(player_dir=str(folder))
    assert time.perf_counter() - started < 5.0
    assert library._added["celebration"][-1][0] == 2000
