"""D-173 (the owner 2026-10-26): "the backups fail to restore. The user must have the ability to save three different franchise games, load
them, and restore from backups." Three franchise slots, each a folder of its own (slot 1 the folder of every earlier version); the start-up
menu continues, starts, deletes and restores any of them; every kept copy can be restored, into its own slot when that is empty, else into the
first empty one. nfl4 only (rule 0.13). This is inspired by Jim Kitchen.
"""
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game import save_texts as S
from programrig import DOWN, ENTER, said


def a_franchise(tmp_path, weeks=1):
    files = MemoryFiles()
    first = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, files=files,
                          policy=enter_until(lambda: first.fstore is not None and first.fstore.league is not None
                                             and first.fstore.league.gtp == 1 + weeks))
    run_until(first)
    assert files.exists("league.sav")
    return files


def copy_of(files):
    other = MemoryFiles()
    other.data = dict(files.data)
    other.times = dict(files.times)
    return other


def menu(tmp_path, answers, files, more=None):
    rig = franchise_rig(tmp_path, answers, files=files, kind="franchise", policy=quit_policy)
    rig.game.startup_menu = True
    for slot, other in (more or {}).items():
        rig.slot_files[slot] = other
    run_until(rig)
    return rig


def test_the_folder_of_each_slot_and_the_setting_read_and_written():
    assert [D.folder_of(s) for s in (1, 2, 3)] == ["franchise", "franchise2", "franchise3"]
    settings = Settings.defaults()
    assert settings.game.nx_franchise_slot == 1
    settings.game.nx_franchise_slot = 3
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert again.game.nx_franchise_slot == 3 and not problems
    _bad, problems = settingsfile.parse(settingsfile.HEADER + "nx_franchise_slot = 4\n")
    assert problems


def test_two_franchises_are_two_items_and_the_second_is_continued_in_its_own_slot(tmp_path):
    one = a_franchise(tmp_path / "make")
    two = copy_of(one)
    rig = menu(tmp_path / "menu", [DOWN, ENTER], one, {2: two})
    spoken = said(rig)
    assert " 1. %s " % (S.CONTINUE_FRANCHISE_N % (1, "Bengals")) in spoken and " 2. %s " % (S.CONTINUE_FRANCHISE_N % (2, "Bengals")) in spoken
    assert any(t.startswith(" Franchise 2: You have a franchise in progress") for t in spoken)
    assert rig.game.franchise_slot == 2 and rig.game.options.settings.game.nx_franchise_slot == 2
    assert rig.game.franchise().files is two and rig.game.program.mode.kind == "franchise"


def test_a_new_franchise_goes_to_the_first_empty_slot_and_the_first_one_is_untouched(tmp_path):
    one = a_franchise(tmp_path / "make")
    before = one.data["league.sav"]
    # continue the franchise, start a new game: Down, Enter; the kind (a franchise, the last kind): Enter; the slot (starts on 2, empty): Enter
    rig = menu(tmp_path / "menu", [DOWN, ENTER, ENTER, ENTER] + COACH_AND_TEAM, one)
    spoken = said(rig)
    assert S.WHICH_FRANCHISE_SLOT in spoken and " 2. %s " % (S.FRANCHISE_SLOT_EMPTY % 2) in spoken     # it starts on the empty slot
    assert rig.slot_files[2].exists("league.sav") and one.data["league.sav"] == before and not one.exists("old/league-1.sav")


def test_a_kept_copy_is_restored_into_an_empty_slot_while_its_own_slot_has_a_franchise(tmp_path):
    one = a_franchise(tmp_path / "make")
    one.data["old/league-1.sav"] = one.data["league.sav"]          # the franchise a new one replaced in slot 1
    # continue the franchise, start a new game, delete the franchise, restore the deleted franchise of the Bengals: Down x3, Enter
    rig = menu(tmp_path / "menu", [DOWN, DOWN, DOWN, ENTER], one)
    spoken = said(rig)
    assert " 4. %s " % (S.RESTORE_FRANCHISE_COPY % ("Bengals", 1)) in spoken
    assert S.FRANCHISE_RESTORED_TO % 2 in spoken
    assert rig.slot_files[2].exists("league.sav") and one.exists("league.sav") and not one.exists("old/league-1.sav")


def test_with_three_franchises_a_kept_copy_waits_and_nothing_moves(tmp_path):
    one = a_franchise(tmp_path / "make")
    one.data["old/league-1.sav"] = one.data["league.sav"]
    two, three = copy_of(one), copy_of(one)
    for other in (two, three):
        other.data.pop("old/league-1.sav")
    # continue 1, 2, 3, start a new game, delete a franchise, restore: Down x5, Enter
    rig = menu(tmp_path / "menu", [DOWN] * 5 + [ENTER], one, {2: two, 3: three})
    assert S.EVERY_FRANCHISE_FULL in said(rig) and one.exists("old/league-1.sav")


def test_the_store_restores_an_older_copy_into_another_slot_and_the_copies_after_it_move_up(tmp_path):
    one = a_franchise(tmp_path / "make")
    league = one.data["league.sav"]
    source_files = MemoryFiles()
    source_files.data.update({"old/league-1.sav": league, "old/league-2.sav": league, "old/league-3.sav": league,
                              "old/history-2.txt": b"history two\r\n"})
    source, target = FranchiseStore(source_files), FranchiseStore(MemoryFiles())
    source.slot, target.slot = 1, 3
    source.open(False)
    assert source.backup_numbers() == [1, 2, 3] and source.peek_backup(2) is not None
    assert source.restore_backup(2, target) and target.league is not None
    assert target.files.data["history.txt"] == b"history two\r\n"
    assert source.backup_numbers() == [1, 2] and not source_files.exists("old/league-3.sav")
    assert not source.restore_backup(1, target)                      # a slot that holds a franchise takes no copy


def test_a_deleted_franchise_still_comes_back_into_its_own_slot(tmp_path):
    one = a_franchise(tmp_path / "make")
    before = one.data["league.sav"]
    store = FranchiseStore(one)
    store.open(True)
    assert store.delete_franchise() and not one.exists("league.sav")
    assert store.restore_deleted() and one.data["league.sav"] == before


def test_a_franchise_deleted_at_one_start_can_be_restored_at_the_next(tmp_path):
    one = a_franchise(tmp_path / "make")
    before = one.data["league.sav"]
    store = FranchiseStore(one)
    store.open(True)
    assert store.delete_franchise() and not one.exists("league.sav")
    # the next start: nothing but the kept copy; the menu is there: start a new game, restore the deleted franchise: Down, Enter
    rig = franchise_rig(tmp_path / "next", [DOWN, ENTER], files=one, kind="classic", policy=quit_policy)
    rig.game.startup_menu = True
    run_until(rig)
    spoken = said(rig)
    assert " 2. %s " % (S.RESTORE_FRANCHISE_COPY % ("Bengals", 1)) in spoken and S.FRANCHISE_RESTORED_TO % 1 in spoken
    assert one.data["league.sav"] == before
