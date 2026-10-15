"""The player's names and banter in the game, and the F9 Customize menu on the virtual-clock rig (S7.7). This is inspired by Jim Kitchen.

D-032 item 11, D-048, G-K2. What was written down before the code: a changed name is what every later sentence speaks (the
schedule, the standings, the score, the choice of the team, the roster draws); a season and a saved game hold numbers, so a
rename never breaks them; Reload applies the files at once (a game in progress keeps the roster it drew); the Customize menu has
five items in this order: open the folder, reload, check, reset one list, reset all; reset all asks for one Enter.
"""
import os
import random

from nfl4.data import customlists as cl
from nfl4.data.customize import Customization
from nfl4.game import extra_texts as words
from nfl4.game.banter_markup import Speak
from nfl4.game.banter_pool import DEFAULT_MARKUP
from nfl4.game.names import load_surnames
from programrig import DOWN, ENTER, ESC, F1, UP, preset_season, program_rig, said

TOP = "Customize. 5 items. Press F1 for help. "
END, HOME = 35, 36


class Folders:
    def __init__(self, ok=True):
        self.opened, self.ok = [], ok

    def __call__(self, path):
        self.opened.append(path)
        return self.ok


def rig_for(tmp_path, answers, with_files=True):
    rig = program_rig(tmp_path, answers, preset=preset_season())
    rig.folder = tmp_path / "customize"
    if with_files:
        rig.custom = Customization(str(rig.folder))
        rig.game.customization = rig.custom
        rig.game.apply_customization()
    rig.folders = rig.game.functions.open_folder = Folders()
    return rig


def edit(rig, name, old, new):
    path = rig.folder / name
    path.write_bytes(path.read_bytes().decode("utf-8").replace(old, new, 1).encode("utf-8"))


def customize(rig, keys):
    """F9, down to the third item, Enter, then `keys` in the Customize menu, then two Escapes."""
    rig.keys.answers = [DOWN, DOWN, ENTER] + keys + [ESC, ESC]
    rig.game.functions.run()
    return said(rig)[3:]                                     # after the F9 menu's opening and its two moves


# ----- the names in the game -----

def test_a_renamed_team_and_division_are_spoken_by_the_schedule_the_score_and_the_standings(tmp_path):
    rig = rig_for(tmp_path, [])
    edit(rig, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    edit(rig, "teams.txt", "T10 = Chargers", "T10 = Comets")
    edit(rig, "divisions.txt", "D3 = A. F. C. West.", "D3 = The Big Western Group.")
    rig.custom.reload()
    rig.game.apply_customization()
    game = rig.game
    game.season.choose_team(3, 1)
    game.season.tn3, game.season.tn4 = 3, 2
    assert game.own_team() == "Mustangs" and game.opponent_team() == "Comets"
    game.say_score(7, 3)
    assert "Mustangs" in said(rig)[-1] and "Comets" in said(rig)[-1] and "Broncos" not in said(rig)[-1]
    rig.sapi.said.clear()
    game.season.gtp = 2
    assert game.say_stand() is True
    spoken = " ".join(said(rig))
    assert " The Big Western Group. " in spoken and "Mustangs" in spoken and "Comets" in spoken
    assert "Broncos" not in spoken and "Chargers" not in spoken and "A. F. C. West." not in spoken


def test_the_surnames_the_next_game_draws_come_from_the_players_file(tmp_path):
    rig = rig_for(tmp_path, [])
    lines = ["# NFL Football 4 surnames, format 1."] + ["S%04d = Zed%d" % (n, n) for n in range(1, 1709)]
    (rig.folder / "surnames.txt").write_bytes("\r\n".join(lines).encode("utf-8"))
    rig.custom.reload()
    rig.game.apply_customization()
    setup = rig.game.new_game_setup()
    names = setup.rosters[2].running_backs + setup.rosters[2].defense + setup.banter_names
    assert names and all(name.startswith("Zed") for name in names)


def test_a_reload_keeps_the_names_already_drawn_and_never_draws_them_again(tmp_path):
    rig = rig_for(tmp_path, [])
    first = rig.game.new_game_setup()
    kept = list(first.rosters[2].running_backs)
    drawn = set(first.rosters[2].running_backs + first.rosters[1].running_backs)
    lines = ["# NFL Football 4 surnames, format 1."] + ["S%04d = Zed%d" % (n, n) for n in range(1, 1709)]
    (rig.folder / "surnames.txt").write_bytes("\r\n".join(lines).encode("utf-8"))
    rig.custom.reload()
    rig.game.apply_customization()
    assert first.rosters[2].running_backs == kept and all(not n.startswith("Zed") for n in drawn)   # a game keeps its roster
    used = [i for i, slot in enumerate(rig.game.pool.slots) if slot == ""]
    assert len(used) >= 60                                                    # the slots used before stay used
    second = rig.game.new_game_setup()
    assert all(n.startswith("Zed") for n in second.rosters[2].running_backs)


def test_a_season_and_its_saved_files_hold_numbers_so_a_rename_never_breaks_them(tmp_path):
    from nfl4.data.files.store import FileProgramStore
    from nfl4.game.rnd import GameRandom
    from nfl4.game.schedule import make_schedule
    from nfl4.game.standings import Records
    data, folder = tmp_path / "data", tmp_path / "customize"
    store = FileProgramStore(str(data), str(folder))
    store.write_coach_and_team(3, 1, "Kim Lee")
    store.write_schedule(make_schedule(GameRandom(random.Random(5)), 3, 1))
    store.write_gtp(5)
    store.write_records(Records())
    custom = Customization(str(folder))
    path = folder / "teams.txt"
    path.write_bytes(path.read_bytes().decode("utf-8").replace("T09 = Broncos", "T09 = Mustangs").encode("utf-8"))
    custom.reload()
    rig = program_rig(tmp_path / "rig", [], preset=preset_season())
    rig.game.customization = custom
    rig.game.apply_customization()
    again = FileProgramStore(str(data), str(folder))
    assert again.take_notices() == []                                         # nothing was damaged by the rename
    assert again.load_season(rig.game.season) is True
    assert rig.game.own_team() == "Mustangs" and rig.game.season.gtp == 5


# ----- the menu -----

def test_without_the_player_files_the_item_says_so(tmp_path):
    rig = rig_for(tmp_path, [DOWN, DOWN, ENTER, ESC], with_files=False)
    rig.game.functions.run()
    assert words.CUSTOMIZE_NOT_AVAILABLE in said(rig)


def test_the_customize_menu_names_its_five_items_and_wraps(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = customize(rig, [DOWN, DOWN, DOWN, DOWN, DOWN, UP, END, HOME])
    assert spoken == [TOP + words.CUSTOMIZE_FOLDER_ITEM, words.CUSTOMIZE_RELOAD_ITEM, words.CUSTOMIZE_CHECK_ITEM,
                      words.CUSTOMIZE_RESET_ONE_ITEM, words.CUSTOMIZE_RESET_ALL_ITEM, words.CUSTOMIZE_FOLDER_ITEM,
                      words.CUSTOMIZE_RESET_ALL_ITEM, words.CUSTOMIZE_RESET_ALL_ITEM, words.CUSTOMIZE_FOLDER_ITEM,
                      words.CUSTOMIZE_ITEM]                          # the last: back in the F9 menu, the item again


def test_f1_in_the_customize_menu_says_its_help(tmp_path):
    rig = rig_for(tmp_path, [])
    assert customize(rig, [F1])[1] == words.CUSTOMIZE_HELP


def test_open_the_folder_makes_the_sounds_folder_and_opens_the_customize_folder(tmp_path):
    rig = rig_for(tmp_path, [])
    os.rmdir(rig.folder / "sounds")
    spoken = customize(rig, [ENTER])
    assert spoken[1] == words.CUSTOMIZE_FOLDER_OPENING and rig.folders.opened == [str(rig.folder)]
    assert (rig.folder / "sounds").is_dir()
    rig = rig_for(tmp_path / "b", [])
    rig.folders.ok = False
    assert customize(rig, [ENTER])[1] == words.CUSTOMIZE_FOLDER_FAILED


def test_reload_applies_the_files_at_once_and_says_what_was_wrong(tmp_path):
    rig = rig_for(tmp_path, [])
    edit(rig, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    edit(rig, "teams.txt", "T10 = Chargers", "T10 = no,way")
    for number in range(2, 143):
        edit(rig, "banter.txt", "B%03d = " % number + DEFAULT_MARKUP[number], "B%03d = off" % number)
    with open(rig.folder / "banter.txt", "ab") as handle:
        handle.write(b"B143 = Hello [name]\r\n")
    spoken = customize(rig, [DOWN, ENTER])
    assert spoken[2] == ("The files were read again. 2 banter lines are on. "
                         "1 problem found in teams.txt, details are in the log.")
    assert rig.game.league.team(3, 1) == "Mustangs" and rig.game.league.team(3, 2) == "Chargers"
    assert rig.game.banter_pool.numbers() == [1, 143]


def test_check_reads_the_results_aloud_and_applies_nothing(tmp_path):
    rig = rig_for(tmp_path, [])
    edit(rig, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    spoken = customize(rig, [DOWN, DOWN, ENTER])
    assert spoken[3].startswith("teams.txt: no problems. divisions.txt: no problems.") and spoken[3].endswith("in the log.")
    assert rig.game.league.team(3, 1) == "Broncos"


def test_reset_one_list_asks_which_and_puts_the_original_back_keeping_the_players_file(tmp_path):
    rig = rig_for(tmp_path, [])
    edit(rig, "divisions.txt", "D1 = A. F. C. North.", "D1 = The North.")
    rig.custom.reload()
    rig.game.apply_customization()
    assert rig.game.league.division_names[0] == "The North."
    spoken = customize(rig, [DOWN, DOWN, DOWN, ENTER, DOWN, ENTER, F1])
    assert spoken[4] == "Reset one list. 4 items. Press F1 for help. Team names"
    assert spoken[5:7] == ["Division names", "divisions.txt is back to the original. Your file was kept as "
                                             "divisions.txt.before-reset."]
    assert spoken[7] == words.CUSTOMIZE_RESET_ONE_HELP
    assert rig.game.league.division_names[0] == "A. F. C. North."
    assert "The North." in (rig.folder / "divisions.txt.before-reset").read_text(encoding="utf-8")


def a_renamed_rig(tmp_path):
    rig = rig_for(tmp_path, [])
    edit(rig, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    rig.custom.reload()
    rig.game.apply_customization()
    assert rig.game.league.team(3, 1) == "Mustangs"
    return rig


def test_reset_all_asks_and_one_enter_puts_every_original_back(tmp_path):
    rig = a_renamed_rig(tmp_path)
    spoken = customize(rig, [END, ENTER, ENTER])                              # the last item, Enter, the confirming Enter
    assert words.CUSTOMIZE_CONFIRM_RESET_ALL in spoken
    assert "All lists are back to the original. Your files were kept with the ending before-reset." in spoken
    assert rig.game.league.team(3, 1) == "Broncos" and (rig.folder / "teams.txt.before-reset").exists()


def test_reset_all_is_cancelled_by_any_key_that_is_not_enter(tmp_path):
    rig = a_renamed_rig(tmp_path)
    spoken = customize(rig, [END, ENTER, DOWN])
    assert words.NOTHING_CHANGED in spoken and rig.game.league.team(3, 1) == "Mustangs"
    assert not (rig.folder / "teams.txt.before-reset").exists()


def test_a_menu_that_cannot_work_never_ends_the_game(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.custom.reload = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    spoken = customize(rig, [DOWN, ENTER, DOWN])
    assert spoken[2] == words.FAILED and spoken[3] == words.CUSTOMIZE_CHECK_ITEM      # said, and the menu is still open


def test_the_original_142_lines_are_the_pool_after_a_reload_of_untouched_files(tmp_path):
    rig = rig_for(tmp_path, [])
    customize(rig, [DOWN, ENTER])
    assert rig.game.banter_pool.size == 142 and all(line.builtin for line in rig.game.banter_pool.lines)
    assert all(isinstance(line.pieces[0], Speak) for line in rig.game.banter_pool.lines)
