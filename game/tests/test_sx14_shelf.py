"""SX.14 (CLAUDE.md 0.23, playbook 7.17, NX-S2 to NX-S4, NX-S6, NX-S8): the file format of a save's summary and resume sections, and the shelf
that keeps the three slots, the automatic save and the backup. This is inspired by Jim Kitchen.

Nothing here plays a game: a `SavedGame` goes through `savedgame.encode`/`decode` and the shelf over `MemoryFiles` (the franchise's in-memory
folder) and over a real folder, and the thing that matters is that a file is never lost: written whole, moved and not removed, named when it is
damaged, and the player's own choice is the only thing that moves one.
"""
import json
import struct

import pytest

from nfl4.data.files import savedgame, shelf, variant
from nfl4.extras.franchise.files import DiskFiles, MemoryFiles
from nfl4.game.gamestate import SavedGame, SideStats

INFO = json.dumps({"v": 1, "week": 5, "kind": "classic", "own": "Bears", "opp": "Packers", "lm": 6, "ls": None})


def a_game(info=INFO, resume=None, extras=None, own=14, opponent=10):
    stats = {1: SideStats(score=own), 2: SideStats(score=opponent)}
    return SavedGame(1, 2, 2, 3, 12, [31, 32, 33, 34, 35], 71.5, stats, 40, 2, 6, "Unitas", 1, extras, extras is not None, info, resume)


def tick():
    """A clock that moves one second each time it is read, so a save made later has a later stamp."""
    state = {"t": 1_800_000_000.0}

    def clock():
        state["t"] += 1.0
        return state["t"]
    return clock


# ----- the file: two sections after the original's values -----

def test_a_save_without_the_new_sections_is_the_bytes_it_always_was():
    assert savedgame.encode(a_game(info=None)) == savedgame.encode(a_game(info=None, resume=None))
    assert variant.unpack_numbers(savedgame.encode(a_game(info=None)))[:2] == [1, 2]
    assert savedgame.decode(savedgame.encode(a_game(info=None))).info is None


def test_the_summary_and_the_resume_sections_come_back_whole_in_either_game_mode():
    for extras in (None, '{"rules_year":2026}'):
        saved = a_game(resume='{"v":1,"state":{}}', extras=extras)
        back = savedgame.decode(savedgame.encode(saved))
        assert back.info == INFO and back.resume == '{"v":1,"state":{}}' and back.extras == extras and back.extras_marked == (extras is not None)


def test_the_new_sections_are_after_the_original_values_so_the_original_still_reads_its_own():
    plain = savedgame.encode(a_game(info=None))
    full = savedgame.encode(a_game(resume="{}"))
    assert full.startswith(plain) and len(full) > len(plain)
    assert variant.unpack_numbers(full[:len(plain)])[:11] == variant.unpack_numbers(plain)[:11]


def test_a_section_with_another_format_or_bad_text_is_dropped_and_the_game_still_loads():
    plain = savedgame.encode(a_game(info=None))
    other_format = plain + variant.pack_string(b"NX-INFO") + variant.pack_integer(7) + variant.pack_string(b"{}")
    back = savedgame.decode(other_format)
    assert back.info is None and back.stats[1].score == 14
    not_text = plain + variant.pack_string(b"NX-INFO") + variant.pack_integer(1) + variant.pack_string(b"\xff\xfe")
    assert savedgame.decode(not_text).info is None


def test_a_file_cut_inside_a_section_loads_the_board_and_loses_only_that_section():
    full = savedgame.encode(a_game(resume='{"v":1}'))
    plain_length = len(savedgame.encode(a_game(info=None)))
    for cut in range(plain_length, len(full)):
        back = savedgame.decode(full[:cut])
        assert back.stats[1].score == 14                      # the board is never lost to a cut in a trailer
        assert back.resume is None                            # the last section is cut in every one of these


def test_a_section_twice_or_an_unknown_record_after_the_game_is_a_damaged_file():
    plain = savedgame.encode(a_game(info=None))
    twice = plain + (variant.pack_string(b"NX-INFO") + variant.pack_integer(1) + variant.pack_string(b"{}")) * 2
    with pytest.raises(variant.FileDamaged):
        savedgame.decode(twice)
    with pytest.raises(variant.FileDamaged):
        savedgame.decode(plain + variant.pack_integer(3))


# ----- the shelf: slots, the automatic save, the backup -----

def new_shelf(files=None):
    files = files if files is not None else MemoryFiles()
    return shelf.SaveShelf(files, clock=tick()), files


def test_a_slot_and_the_automatic_save_are_written_whole_through_a_temporary_file():
    s, files = new_shelf()
    assert s.write_slot(2, a_game()) and s.write_auto(a_game(own=21))
    assert files.steps == [("tmp", "football2.sav"), ("commit", "football2.sav"), ("tmp", "autosave.sav"), ("commit", "autosave.sav")]
    entries = s.scan()
    assert [(e.kind, e.slot, e.status) for e in entries] == [("game", 2, "ok"), ("auto", None, "ok")]
    assert entries[0].info["slot"] == 2 and entries[0].info["auto"] is False and entries[1].info["auto"] is True
    assert entries[0].info["week"] == 5 and entries[0].stamp > 0 and entries[1].stamp > entries[0].stamp      # the shelf stamps the date


def test_a_write_that_fails_leaves_the_save_that_was_there():
    s, files = new_shelf()
    s.write_slot(1, a_game(own=7))
    files.unwritable = True
    assert not s.write_slot(1, a_game(own=99))
    files.unwritable = False
    assert s.scan()[0].saved.stats[1].score == 7


def test_a_damaged_save_is_named_not_loaded_and_not_removed():
    s, files = new_shelf()
    s.write_slot(1, a_game())
    files.data["football.sav"] = files.data["football.sav"][:50]
    files.data["football3.sav"] = b"not a save at all"
    entries = s.scan()
    assert [(e.slot, e.status) for e in entries] == [(1, "damaged"), (3, "damaged")]
    assert entries[0].reason and entries[0].saved is None and "football.sav" in files.data and "football3.sav" in files.data


def test_a_save_another_program_holds_is_named_held_and_stays():
    s, files = new_shelf()
    s.write_slot(1, a_game())
    files.held.add("football.sav")
    entry = s.scan()[0]
    assert entry.status == "held" and "football.sav" in files.data and not entry.playable


def test_the_owners_check_can_say_a_save_is_old_or_belongs_to_no_season():
    s, _files = new_shelf()
    s.write_slot(1, a_game())
    s.write_slot(2, a_game())
    seen = []

    def classify(entry):
        seen.append(entry.slot)
        return ("stale", "week 4") if entry.slot == 1 else ("ok", "")
    entries = s.scan(classify)
    assert seen == [1, 2] and [e.status for e in entries] == ["stale", "ok"] and [e.playable for e in entries] == [False, True]


def test_a_save_made_by_the_original_has_no_summary_and_takes_the_files_date():
    files = MemoryFiles()
    files.data["football.sav"] = savedgame.encode(a_game(info=None))
    files.times["football.sav"] = 1_700_000_000.0
    entry = shelf.SaveShelf(files).scan()[0]
    assert entry.info == {} and entry.stamp == 1_700_000_000.0 and entry.playable


# ----- delete and restore (NX-S2): a move, one level, never a removal -----

def test_delete_moves_the_file_to_the_backup_and_restore_brings_it_back_to_its_slot():
    s, files = new_shelf()
    s.write_slot(2, a_game(own=3))
    entry = s.scan()[0]
    assert s.delete(entry) and "football2.sav" not in files.data and shelf.DELETED_FILE in files.data
    assert s.deleted().saved.stats[1].score == 3
    assert s.restore() == 2 and "football2.sav" in files.data and shelf.DELETED_FILE not in files.data


def test_restore_takes_the_first_free_slot_when_its_own_is_taken_and_refuses_when_all_are_taken():
    s, files = new_shelf()
    s.write_slot(1, a_game(own=1))
    s.delete(s.scan()[0])
    s.write_slot(1, a_game(own=2))
    assert s.restore() == 2 and s.scan()[1].saved.stats[1].score == 1
    s.delete(s.scan()[1])
    for slot in (1, 2, 3):
        s.write_slot(slot, a_game(own=40 + slot))
    assert s.restore() is None and shelf.DELETED_FILE in files.data           # nothing was overwritten, the backup stays
    assert [e.saved.stats[1].score for e in s.scan()] == [41, 42, 43]


def test_a_second_delete_replaces_the_backup_one_level_and_a_failed_move_loses_nothing():
    s, files = new_shelf()
    s.write_slot(1, a_game(own=1))
    s.write_slot(2, a_game(own=2))
    first, second = s.scan()
    s.delete(first)
    s.delete(second)
    assert s.deleted().saved.stats[1].score == 2
    s.write_slot(3, a_game(own=3))
    files.unwritable = True
    assert not s.delete(s.scan()[0]) and "football3.sav" in files.data


def test_a_damaged_save_can_be_deleted_to_the_backup_too():
    s, files = new_shelf()
    files.data["football.sav"] = b"junk"
    assert s.delete(s.scan()[0]) and shelf.DELETED_FILE in files.data and "football.sav" not in files.data


def test_the_saves_of_an_ended_game_move_to_the_backup_three_deep_and_the_automatic_save_goes():
    s, files = new_shelf()
    for number in range(1, 5):
        s.write_slot(1, a_game(own=number))
        s.write_auto(a_game(own=number))
        assert s.retire(s.scan(), "the game ended") == 1
        assert "autosave.sav" not in files.data and "football.sav" not in files.data
    held = sorted(name for name in files.data if name.startswith("backup/finished-"))
    assert held == ["backup/finished-1.sav", "backup/finished-2.sav", "backup/finished-3.sav"]
    assert savedgame.decode(files.data["backup/finished-1.sav"]).stats[1].score == 4
    assert savedgame.decode(files.data["backup/finished-3.sav"]).stats[1].score == 2


def test_the_shelf_over_a_real_folder_is_atomic_and_keeps_its_backup(tmp_path):
    files = DiskFiles(str(tmp_path))
    s = shelf.SaveShelf(files, clock=tick())
    assert s.write_slot(1, a_game()) and s.write_auto(a_game(own=2))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["autosave.sav", "football.sav"]          # no temporary file is left
    entry = s.scan()[0]
    assert s.delete(entry) and (tmp_path / "backup" / "deleted-game.sav").exists() and not (tmp_path / "football.sav").exists()
    assert s.restore() == 1 and (tmp_path / "football.sav").exists()
    assert struct.unpack_from("<H", (tmp_path / "football.sav").read_bytes(), 0)[0] == 2        # still a Variant file the original reads


# ----- the debug log (rule 0.15): every save, load, delete, restore and retirement -----

def test_every_save_delete_restore_and_retirement_is_in_the_debug_log(monkeypatch):
    from nfl4.data import debuglog
    seen = []
    real = debuglog.event
    monkeypatch.setattr(debuglog, "event", lambda area, name, *args, **fields: (seen.append((area, name, fields.get("file"))), real(area, name, *args, **fields))[1])
    s, _files = new_shelf()
    s.write_slot(1, a_game())
    s.write_auto(a_game())
    s.delete(s.scan()[0])
    s.restore()
    s.retire(s.scan(), "the game ended")
    names = [name for area, name, _ in seen if area == "save"]
    assert names.count("write") == 2 and {"delete", "restore", "retire", "auto_removed", "scan"} <= set(names)
    assert ("save", "write", "football.sav") in seen and ("save", "delete", "football.sav") in seen
