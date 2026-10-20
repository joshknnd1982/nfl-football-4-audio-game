"""SX.14 (CLAUDE.md 0.23, playbook 7.17, NX-S1 to NX-S8): the program, the real engine and the franchise together. This is inspired by Jim Kitchen.

* a whole game played by the program with the real engine and killed at a play, then a second program over the same files: it offers "the game
  that was not finished", Enter continues it, the game ends as a game does, and its saves move to the backup;
* the program hands the engine the save questions and the automatic save only when the start-up choice is on;
* the franchise in the menu (N. F. L. rules): its sentence, "continue the franchise", the kind in use follows the choice, and deleting it moves it
  to the backup with its saved games and brings it back.
"""
import pytest

from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.game import save_texts as S
from nfl4.game.keys import GameQuit
from nfl4.game.save_menu import SaveUi
from programrig import ENTER, DOWN, UP, enter_policy, played, preset_season, program_rig, said
from savesrig import EXIT, a_saved, games, menu_rig


# ----- a crash in a game played by the program, and the next start -----

def real_engine(rig):
    """The program plays the real pag (the rig's stand-in is taken away)."""
    del rig.game.play_game
    return rig


def test_a_game_killed_at_a_play_is_offered_at_the_next_start_and_ends_as_a_game_ends(tmp_path):
    first = real_engine(menu_rig(tmp_path / "one", [], policy=enter_policy, fast=True))
    real_autosave = first.store.autosave
    count = []

    def dying(record):
        real_autosave(record)
        count.append(1)
        if len(count) == 6:
            raise GameQuit()                                           # the window closes (or the power goes) right after the sixth play's save
        return True
    first.store.autosave = dying
    first.keys.answers[:0] = [ENTER]                                    # the start-up question: continue the season
    with pytest.raises(GameQuit):
        first.run()
    shelf = first.store.shelf
    assert shelf.auto is not None and shelf.slots == {}                 # the crash left the automatic save and nothing else lost
    assert shelf.auto.saved.resume and shelf.auto.info["auto"] is True

    def until_the_game_is_over(keys):
        if shelf.auto is None and " getting saved game " in said(second):
            raise GameQuit()                                           # the resumed game ended (its automatic save went): stop before the next week
        return ENTER
    second = real_engine(menu_rig(tmp_path / "two", [ENTER], policy=until_the_game_is_over, fast=True))
    second.store.shelf = shelf
    second.store.preset = first.store.preset
    with pytest.raises(GameQuit):
        second.run()
    spoken = said(second)
    assert any(t.startswith(" You have a game that was not finished: ") for t in spoken)
    assert " 1. %s " % S.CONTINUE_AUTO in spoken
    assert " getting saved game " in spoken                              # Enter continued it
    assert shelf.auto is None and shelf.slots == {}                      # the game ended: the automatic save is gone


def test_the_program_gives_the_engine_the_save_questions_and_the_automatic_save_only_with_the_choice_on(tmp_path):
    on = menu_rig(tmp_path / "on", [ENTER, ENTER, ENTER] + EXIT, outcomes=[played()])
    on.run()
    assert isinstance(on.plays[0]["save_ui"], SaveUi) and on.plays[0]["autosave_sink"] == on.store.autosave
    off = program_rig(tmp_path / "off", [ENTER, ENTER] + EXIT, preset=preset_season(), outcomes=[played()])
    off.run()
    assert off.plays[0]["save_ui"] is None and off.plays[0]["autosave_sink"] is None


def test_save_game_inside_the_program_asks_the_place_and_ends_or_goes_on(tmp_path):
    from nfl4.game.pag import GameResult
    rig = menu_rig(tmp_path, [ENTER, ENTER] + EXIT)

    def saves_then_ends(rig_):
        ui = rig_.plays[-1]["save_ui"]
        engine = type("E", (), {})()
        slot = ui.choose_slot(engine, None)                            # Enter takes the first place
        rig_.store.save_game(a_saved(), slot)
        from programrig import Outcome
        return Outcome(GameResult(scores=None, saved=True), stop_beds=False)
    rig.outcomes = [saves_then_ends]
    rig.run()
    assert S.SLOT_QUESTION in said(rig) and games(rig) == [(1, 14)] and rig.game.program.ending == "saved"


# ----- the franchise in the menu -----

def a_franchise_on_disk(tmp_path, weeks=2):
    files = MemoryFiles()
    first = franchise_rig(tmp_path / "make", WANT_FRANCHISE + COACH_AND_TEAM, files=files,
                          policy=enter_until(lambda: first.fstore is not None and first.fstore.league is not None
                                             and first.fstore.league.gtp == 1 + weeks))
    run_until(first)
    assert files.exists("league.sav")
    return files


def test_the_franchise_is_a_sentence_and_an_item_and_continuing_it_puts_it_in_use(tmp_path):
    files = a_franchise_on_disk(tmp_path)
    rig = franchise_rig(tmp_path / "again", [ENTER], files=files, kind="franchise", policy=quit_policy)
    rig.game.startup_menu = True
    run_until(rig)
    spoken = said(rig)
    assert any(t.startswith(" You have a franchise in progress: coach kim of the Bengals, season 1, week 3") for t in spoken)
    assert " 1. %s " % S.CONTINUE_FRANCHISE in spoken and rig.game.program.mode.kind == "franchise"
    assert any(t.startswith(" This is week") for t in spoken)                 # Enter went on into the franchise's season


def test_a_classic_program_never_touches_the_franchise_folder(tmp_path):
    files = a_franchise_on_disk(tmp_path)
    steps = len(files.steps)
    rig = franchise_rig(tmp_path / "classic", [ENTER], files=files, nfl=False, policy=quit_policy, preset=preset_season())
    rig.game.startup_menu = True
    run_until(rig)
    assert not any(t.startswith(" You have a franchise") for t in said(rig)) and len(files.steps) == steps


def test_deleting_the_franchise_asks_again_moves_it_to_the_backup_and_restoring_brings_it_back(tmp_path):
    files = a_franchise_on_disk(tmp_path)
    before = files.data["league.sav"]
    # items: continue the franchise, new game, delete the franchise. Down, Down, Enter, no (Enter): nothing; Down, Down, Enter, yes: moved;
    # the menu stays with: new game, restore the franchise: Down, Enter: back
    answers = [DOWN, DOWN, ENTER, ENTER] + [DOWN, DOWN, ENTER, "y"] + [DOWN, ENTER]
    rig = franchise_rig(tmp_path / "del", answers, files=files, kind="franchise", policy=quit_policy)
    rig.game.startup_menu = True
    run_until(rig)
    spoken = said(rig)
    assert spoken.count(S.DELETE_QUESTION_FRANCHISE) == 2 and S.WAS_DELETED in spoken and S.FRANCHISE_RESTORED in spoken
    assert files.data["league.sav"] == before and not files.exists("old/league-1.sav")
    assert " 2. %s " % S.RESTORE_FRANCHISE in spoken


def test_a_new_franchise_is_started_from_the_menu_with_the_last_kind_first_and_the_classic_season_is_kept(tmp_path):
    files = MemoryFiles()
    rig = franchise_rig(tmp_path, [DOWN, ENTER, DOWN, ENTER] + COACH_AND_TEAM, files=files, kind="classic", policy=quit_policy,
                        preset=preset_season())
    rig.game.startup_menu = True
    run_until(rig)
    spoken = said(rig)
    assert S.NEW_KIND_QUESTION in spoken and " 1. %s " % S.NEW_SEASON in spoken            # the last kind (a classic season) was first
    assert files.exists("league.sav") and rig.store.preset is not None and rig.store.backup_preset is None
    assert rig.game.program.mode.kind == "franchise"


def test_the_new_game_question_starts_on_the_last_kind_a_franchise(tmp_path):
    files = a_franchise_on_disk(tmp_path)
    rig = franchise_rig(tmp_path / "again", [DOWN, ENTER], files=files, kind="franchise", policy=quit_policy)
    rig.game.startup_menu = True
    run_until(rig)
    assert " 2. %s " % S.NEW_FRANCHISE in said(rig)                                         # the question opened on the franchise
