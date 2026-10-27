"""D-176 (a tester of 0.16.6): "there is no way to get to that backup option except if you start the game and already have a franchise going"
and "try a franchise, save, delete, quit the game with alt+f4, try to restore from backup, this is not working." Every kept copy can be
reached: the start-up menu comes back for anything the player deleted (a franchise, a saved game, a season), the new-game question offers
"restore a deleted franchise", and F9, Franchise has the same item while playing. nfl4 only (rule 0.13). This is inspired by Jim Kitchen.
"""
import copy

from frrig import COACH_AND_TEAM, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until
from programrig import DOWN, ENTER, ESC, preset_season, said
from savesrig import a_saved, menu_rig, run_until_a_key_is_missing

from nfl4.extras.franchise.files import DiskFiles, MemoryFiles
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.extras.state import ExtrasRecord
from nfl4.game import save_texts as S


def a_franchise(tmp_path, files):
    """A franchise of the Bengals, week 1 played (won: week 2, 1 win), with a saved game of its week in its folder."""
    first = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, files=files,
                          policy=enter_until(lambda: first.fstore is not None and first.fstore.league is not None
                                             and first.fstore.league.gtp == 2))
    run_until(first)
    assert first.fstore.save_game(a_saved(own=7, opponent=3, extras=ExtrasRecord().to_json()))
    return first


def start(tmp_path, answers, files, settings, store):
    """One start of the program over the same folder, with the settings the last one left (the settings file) and the same classic files;
    the window closes when the keys are used up (Alt+F4: GameQuit)."""
    rig = franchise_rig(tmp_path, answers, files=files, policy=quit_policy)
    rig.game.options.settings.game = copy.deepcopy(settings)
    rig.game.apply_rules_setting()
    rig.store = rig.game.program_store = store
    rig.game.startup_menu = True
    run_until(rig)
    return rig


def items(rig) -> list:
    return [t for t in said(rig) if t[:4].strip().rstrip(".").isdigit()]


def test_the_testers_path_delete_close_with_alt_f4_start_again_restore_and_play_on(tmp_path):
    files = DiskFiles(str(tmp_path / "franchise"))
    first = a_franchise(tmp_path / "a", files)
    settings, classic = first.game.options.settings.game, first.store
    # the next start: continue the saved game, continue the franchise, start a new game, delete the saved game, delete the franchise:
    # Down x4, Enter, yes; then the window closes at the menu
    second = start(tmp_path / "b", [DOWN] * 4 + [ENTER, "y"], files, settings, classic)
    assert S.WAS_DELETED in said(second) and not files.exists("league.sav") and files.exists("old/league-1.sav")
    # the start after that: nothing in progress, the kept copy brings the menu: start a new game, restore the franchise: Down, Enter;
    # then the menu again: continue the saved game, continue the franchise: Down, Enter
    third = start(tmp_path / "c", [DOWN, ENTER, DOWN, ENTER], files, second.game.options.settings.game, classic)
    spoken = said(third)
    assert " 2. %s " % (S.RESTORE_FRANCHISE_COPY % ("Bengals", 1)) in spoken and S.FRANCHISE_RESTORED_TO % 1 in spoken
    first_item = next(i for i, t in enumerate(spoken) if t.startswith(" 1. "))
    assert S.BACKUP_ONLY in spoken[:first_item]                    # the menu says why it is there and which key reaches the restore
    assert spoken.count(S.BACKUP_ONLY) == 1                        # the second menu (a franchise to continue) does not say it
    assert any("Bengals, season 1, week 2, 1 win and 0 losses. " in t for t in spoken)    # its week and record, said again (not "losss")
    assert third.game.program.mode.kind == "franchise" and third.game.season.gtp == 2
    assert files.exists("league.sav") and files.exists("football.sav") and not files.exists("old/league-1.sav")


def test_a_deleted_franchise_alone_is_offered_at_the_next_start_with_nothing_else_saved(tmp_path):
    files = MemoryFiles()
    first = a_franchise(tmp_path / "a", files)
    store = FranchiseStore(files)
    store.open(True)
    assert store.delete_franchise()
    rig = start(tmp_path / "b", [DOWN, ENTER], files, first.game.options.settings.game, first.store)
    assert S.FRANCHISE_RESTORED_TO % 1 in said(rig) and files.exists("league.sav")


def test_the_new_game_question_offers_to_restore_a_deleted_franchise(tmp_path):
    files = MemoryFiles()
    first = a_franchise(tmp_path / "a", files)
    store = FranchiseStore(files)
    store.open(True)
    assert store.delete_franchise()
    # start a new game (item 1): a new season, a new franchise, restore a deleted franchise: Down Down Enter; the list: Enter
    rig = start(tmp_path / "b", [ENTER, DOWN, DOWN, ENTER, ENTER], files, first.game.options.settings.game, first.store)
    spoken = said(rig)
    assert " 3. %s " % S.RESTORE_A_FRANCHISE in spoken and S.WHICH_FRANCHISE_RESTORE in spoken
    assert " 1. %s " % (S.RESTORE_FRANCHISE_COPY % ("Bengals", 1)) in spoken and S.FRANCHISE_RESTORED_TO % 1 in spoken
    assert files.exists("league.sav")


def test_a_deleted_saved_game_alone_brings_the_menu_back(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, ENTER], preset=None)          # nothing in progress; the backup holds the game the player deleted
    shelf = rig.store.shelf
    shelf.write_slot(1, a_saved())
    shelf.delete(shelf.slots[1])
    run_until_a_key_is_missing(rig)
    spoken = said(rig)
    assert " 2. %s " % S.RESTORE_GAME in spoken and S.WAS_RESTORED % 1 in spoken


def test_a_deleted_season_alone_brings_the_menu_back(tmp_path):
    rig = menu_rig(tmp_path, [DOWN, ENTER], preset=None)
    rig.store.backup_preset = preset_season()                    # the season the player deleted
    run_until_a_key_is_missing(rig)
    spoken = said(rig)
    assert " 2. %s " % S.RESTORE_SEASON in spoken and S.SEASON_RESTORED in spoken


def test_nothing_deleted_and_nothing_saved_still_asks_nothing(tmp_path):
    rig = menu_rig(tmp_path, [], preset=None, outcomes=())
    run_until_a_key_is_missing(rig)
    assert S.MENU_PROMPT not in said(rig)


def test_f9_franchise_restores_a_deleted_franchise_while_a_classic_season_is_played_and_switches_to_it(tmp_path):
    files = MemoryFiles()
    a_franchise(tmp_path / "a", files)
    store = FranchiseStore(files)
    store.open(True)
    assert store.delete_franchise()
    # a classic season is played; at its week menu: F9, Franchise (the 5th item), restore a deleted franchise (the 2nd), the copy (Enter),
    # Enter to play it now; then F9 is closed
    keys = [F9] + [DOWN] * 4 + [ENTER, DOWN, ENTER, ENTER, ENTER, ESC]
    rig = franchise_rig(tmp_path / "b", keys, files=files, kind="classic", preset=preset_season(), policy=quit_policy)
    run_until(rig)
    spoken = said(rig)
    assert S.RESTORE_A_FRANCHISE in spoken and S.FRANCHISE_RESTORED_PLAY_NOW % 1 in spoken
    assert files.exists("league.sav") and not files.exists("old/league-1.sav")
    assert rig.game.program.mode.kind == "franchise" and rig.game.season.gtp == 2


def test_f9_restores_into_another_slot_while_a_franchise_is_played_and_says_when_it_can_be_played(tmp_path):
    files = MemoryFiles()
    first = a_franchise(tmp_path / "a", files)
    files.data["old/league-1.sav"] = files.data["league.sav"]    # the franchise a new one replaced in slot 1
    keys = [F9] + [DOWN] * 4 + [ENTER]                           # F9, Franchise; then the restore item, found by its words below
    rig = franchise_rig(tmp_path / "b", keys, files=files, kind="franchise", policy=quit_policy)
    rig.game.options.settings.game = copy.deepcopy(first.game.options.settings.game)
    rig.game.apply_rules_setting()
    menu_items = []

    from nfl4.extras.franchise import kept
    from nfl4.game import spoken_menu

    real_run = spoken_menu.SpokenMenu._run

    def watched(self):
        if self.title == "Franchise":
            menu_items.extend(item.label() for item in self.items)
            index = next(i for i, item in enumerate(self.items) if item.label() == S.RESTORE_A_FRANCHISE)
            self.keys.answers[:0] = [DOWN] * index + [ENTER, ENTER, ESC, ESC]
        return real_run(self)

    spoken_menu.SpokenMenu._run = watched
    try:
        run_until(rig)
    finally:
        spoken_menu.SpokenMenu._run = real_run
    assert S.RESTORE_A_FRANCHISE in menu_items
    assert (S.FRANCHISE_RESTORED_NEXT_START.strip() % 2) in said(rig)
    assert rig.slot_files[2].exists("league.sav") and files.exists("league.sav") and rig.game.program.mode.kind == "franchise"
    assert kept.kept(rig.game) == []
