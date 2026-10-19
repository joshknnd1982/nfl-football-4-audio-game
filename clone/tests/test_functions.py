"""F9, the added functions, on the virtual-clock rig. This is inspired by Jim Kitchen.

GAP_REGISTER G-K2, G-A4, G-S7, G-S8 and D-018 (F9 is a global key; it ends like every global menu with clk and g = "112"), the
starter kit's menu classes (game/spoken_menu.py). The menus read keys with read_key, so the rig types an answer each time a menu
waits. What a label says was written down from game/extra_texts.py, not from the code under test.
"""
import pytest

from nfl4.audio.restore import REMOVED_FOLDER
from nfl4.data.settings import Settings
from nfl4.game import extra_texts as words
from nfl4.game.keys import GameQuit
from nfl4.game.options import Options
from nfl4.speech.voices import VoiceInfo
from programrig import DOWN, ENTER, ESC, F1, F9, UP, preset_season, program_rig, said
from wavmaker import sine, write

LEFT, RIGHT, END, HOME = 37, 39, 35, 36
TOP = "Added functions. 5 items. Press F1 for help. "
RULES = "Rules."                     # nfl4 only (PX SX.2): the Rules item before About (NFL_EXTRAS_DESIGN 12.2)


class Saves:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1
        return True


class Folders:
    """The program's way to open a folder, recorded instead of opening Explorer."""

    def __init__(self, ok=True, error=None):
        self.opened, self.ok, self.error = [], ok, error

    def __call__(self, path):
        if self.error:
            raise self.error
        self.opened.append(path)
        return self.ok


class Catalog:
    def __init__(self, voices):
        self.list = voices

    def voices(self, timeout=None):
        return list(self.list)


def rig_for(tmp_path, answers, **kwargs):
    rig = program_rig(tmp_path, answers, preset=preset_season(), **kwargs)
    settings = Settings.defaults()
    settings.game.rules = "classic"         # SX.9: the rig's Game plays Classic (a new player's default is the N. F. L. rules)
    settings.audio = rig.sounds.settings
    rig.saves = Saves()
    rig.game.options = Options(settings, rig.speech, save=rig.saves)
    rig.folders = rig.game.functions.open_folder = Folders()
    return rig


def run_f9(rig):
    rig.game.functions.run()
    return said(rig)


# ----- the menu -----

def test_f9_opens_the_menu_with_its_title_its_size_and_the_first_item_and_escape_hands_f1_back(tmp_path):
    rig = rig_for(tmp_path, [ESC])
    assert run_f9(rig) == [TOP + "Speech settings."]
    assert rig.keys.code_text == "112"                                   # clk, then g = "112" like every global menu (D-018)
    assert rig.saves.count == 0


def test_up_and_down_move_through_the_five_items_and_wrap(tmp_path):
    rig = rig_for(tmp_path, [DOWN, DOWN, DOWN, DOWN, DOWN, UP, UP, END, HOME, ESC])
    assert run_f9(rig) == [TOP + "Speech settings.", "Sounds.", words.CUSTOMIZE_ITEM, RULES, "About NFL Football 4.",
                           "Speech settings.", "About NFL Football 4.", RULES, "About NFL Football 4.",
                           "Speech settings."]


def test_f1_in_the_menu_says_its_help(tmp_path):
    rig = rig_for(tmp_path, [F1, ESC])
    assert run_f9(rig)[1] == words.F9_HELP and "F11" in words.F9_HELP and "Control" in words.F9_HELP


def test_the_key_f9_inside_a_wait_runs_the_menu_and_the_wait_ends_with_f1(tmp_path):
    rig = rig_for(tmp_path, [F9, ESC])
    rig.keys.getkey(rig.speech)
    assert rig.keys.code_text == "112" and rig.game.hotkeys.runs == ["120"]
    assert said(rig) == [TOP + "Speech settings."]


def test_f9_in_the_main_menu_repeats_the_menu_from_the_top_with_the_choice_kept(tmp_path):
    rig = rig_for(tmp_path, [DOWN, F9, ESC, DOWN, DOWN, ENTER])
    rig.run()
    spoken = said(rig)
    at = spoken.index(TOP + "Speech settings.")
    assert spoken[at + 1].startswith(" Today's game is") and spoken[at + 2:at + 4] == [" Kim select ", " 2. see schedule "]


def test_f9_while_a_name_is_typed_runs_the_menu_and_the_name_starts_again(tmp_path):
    rig = rig_for(tmp_path, ["a", F9, ESC, "b", "c", ENTER])
    assert rig.game.getter(" Type ") == "bc"
    assert said(rig) == [" Type ", "a", TOP + "Speech settings.", " Type ", "b", "c"]


def test_closing_the_window_in_the_menu_unwinds_the_game(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.keys.close()
    with pytest.raises(GameQuit):
        rig.game.functions.run()


# ----- about -----

def test_about_reads_the_attribution_and_the_note_about_the_author(tmp_path):
    rig = rig_for(tmp_path, [DOWN, DOWN, DOWN, DOWN, ENTER, ESC, ESC])
    spoken = run_f9(rig)
    assert spoken[:5] == [TOP + "Speech settings.", "Sounds.", words.CUSTOMIZE_ITEM, RULES, "About NFL Football 4."]
    text = " ".join(spoken[5:])
    assert "About NFL Football 4." in spoken and "inspired by Jim Kitchen" in text and "He died in 2015" in text
    assert spoken[-1] == "About NFL Football 4."                         # back in the menu: the item again


# ----- speech settings -----

def speech_menu(rig, keys):
    rig.keys.answers = [ENTER] + keys + [ESC, ESC]
    return run_f9(rig)


def test_the_speech_menu_names_its_nine_items_and_starts_with_the_original_values(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = speech_menu(rig, [DOWN] * 9)
    assert spoken[1:11] == ["Speech settings. 9 items. Press F1 for help. Speech output: SAPI 5 voice only, original.",
                            "Speech rate: 0, original.", "Speech pitch: 0, original.",
                            "Letter keys in lists: type letters to search for a name, original.",
                            words.CHOOSE_VOICES_ITEM, words.RESTORE_SPEECH, words.SETTINGS_FOLDER_ITEM,
                            words.debug_log_label("detailed"), words.PROBLEM_REPORT_ITEM,
                            "Speech output: SAPI 5 voice only, original."]


def test_right_changes_the_speech_output_and_saves_it_enter_goes_back_to_the_original(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = speech_menu(rig, [RIGHT, RIGHT, RIGHT, RIGHT, LEFT, ENTER])
    assert spoken[2:8] == ["Speech output: NVDA only. " + words.NVDA_NOT_RUNNING,
                           "Speech output: JAWS only. " + words.JAWS_NOT_RUNNING,
                           "Speech output: automatic. " + words.NEITHER_RUNNING,
                           "Speech output: SAPI 5 voice only, original.",
                           "Speech output: automatic. " + words.NEITHER_RUNNING,
                           "Speech output: SAPI 5 voice only, original."]
    assert rig.speech.mode == "sapi" and rig.game.options.settings.speech.mode == "sapi" and rig.saves.count == 6


def test_the_speech_output_follows_the_running_screen_reader(tmp_path):
    rig = rig_for(tmp_path, [], nvda_running=True)
    spoken = speech_menu(rig, [RIGHT])
    assert rig.nvda.spoken()[0] == "Speech output: NVDA only." and rig.speech.mode == "nvda"     # now NVDA speaks


def test_left_and_right_change_the_speech_rate_in_the_range_of_the_ctrl_menu(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = speech_menu(rig, [DOWN, RIGHT, RIGHT, LEFT, ENTER])
    assert spoken[2:7] == ["Speech rate: 0, original.", "Speech rate: 1.", "Speech rate: 2.", "Speech rate: 1.",
                           "Speech rate: 0, original."]
    assert rig.game.options.settings.speech.rate is None and rig.saves.count == 4


def test_the_speech_rate_stops_at_ten_and_minus_ten(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = speech_menu(rig, [DOWN] + [RIGHT] * 12)
    assert spoken[-2] == "Speech rate: 10." and spoken[-3] == "Speech rate: 10."
    assert rig.game.options.vr == 10
    rig = rig_for(tmp_path, [])
    spoken = speech_menu(rig, [DOWN] + [LEFT] * 12)
    assert spoken[-2] == "Speech rate: -10." and rig.game.options.vr == -10


def test_the_pitch_and_the_letter_keys_change_and_return(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = speech_menu(rig, [DOWN, DOWN, RIGHT, ENTER, DOWN, RIGHT, ENTER])
    assert spoken[3:9] == ["Speech pitch: 0, original.", "Speech pitch: 1.", "Speech pitch: 0, original.",
                           "Letter keys in lists: type letters to search for a name, original.",
                           "Letter keys in lists: a letter jumps to the next name with that first letter.",
                           "Letter keys in lists: type letters to search for a name, original."]
    assert rig.game.options.settings.speech.pitch == 0 and rig.game.options.settings.speech.list_letters == "type"


def test_restore_puts_the_original_speech_settings_back(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.options.set_vr(4)
    rig.game.options.settings.speech.pitch = 3
    rig.game.options.settings.speech.list_letters = "first"
    rig.speech.mode = rig.game.options.settings.speech.mode = "auto"
    spoken = speech_menu(rig, [DOWN] * 5 + [ENTER])
    assert spoken[-2] == words.SPEECH_RESTORED
    speech = rig.game.options.settings.speech
    assert (speech.mode, speech.rate, speech.pitch, speech.list_letters) == ("sapi", None, 0, "type") and rig.speech.mode == "sapi"


def test_the_voices_item_runs_the_five_pickers_of_f12_and_says_it_is_done(tmp_path):
    voices = [VoiceInfo(0, "id0", "Alpha", "EngA"), VoiceInfo(1, "id1", "Beta", "EngA")]
    rig = rig_for(tmp_path, [])
    rig.game.options.voice_catalog = Catalog(voices)
    spoken = speech_menu(rig, [DOWN] * 4 + [ENTER] + [ESC] * 5)
    titles = [t.split(".")[0] for t in spoken if t.startswith("Choose the voice for")]
    assert len(titles) == 5 and titles[0] == "Choose the voice for the announcer"
    assert words.VOICES_DONE in spoken


def test_the_settings_folder_item_opens_the_folder_of_settings_txt(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.functions.settings_dir = str(tmp_path)
    spoken = speech_menu(rig, [DOWN] * 6 + [ENTER])
    assert rig.folders.opened == [str(tmp_path)] and spoken[-2] == words.SETTINGS_FOLDER_OPENING


def test_a_folder_that_cannot_be_opened_is_said(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.folders.ok = False
    spoken = speech_menu(rig, [DOWN] * 6 + [ENTER])
    assert spoken[-2] == words.SETTINGS_FOLDER_FAILED


def test_a_menu_that_fails_says_so_and_the_game_goes_on(tmp_path, caplog):
    rig = rig_for(tmp_path, [])
    rig.folders.error = RuntimeError("explorer is gone")
    rig.keys.answers = [ENTER] + [DOWN] * 6 + [ENTER, ESC]
    spoken = run_f9(rig)
    assert spoken[-1] == words.FAILED and rig.keys.answers == []
    assert any("an F9 menu failed" in r.message for r in caplog.records)


# ----- sounds -----

def sounds_menu(rig, keys):
    rig.keys.answers = [DOWN, ENTER] + keys + [ESC, ESC]
    return run_f9(rig)


def extra_plays(rig):
    return [(e.sound_id, e.volume) for e in rig.slot_log if e.slot == 7 and e.action == "play"]


def test_the_sounds_menu_lists_its_nine_items(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN] * 8)
    assert spoken[2:11] == ["Sounds. 9 items. Press F1 for help. Sound volume: full, original.",
                            words.PREVIEW_ITEM, words.RELOAD_ITEM, words.CHECK_ITEM, words.FOLDER_ITEM,
                            words.RESTORE_SOUNDS, words.RESTORE_ONE_ITEM, words.RESTORE_ALL_ITEM, words.POOLS_ITEM]


def test_with_the_players_commercials_folder_the_menu_has_the_commercials_items_and_the_setting_cycles_and_is_saved(tmp_path):
    from nfl4.game.commercials import Commercials
    rig = rig_for(tmp_path, [])
    rig.sounds.commercials = Commercials(str(tmp_path / "commercials"))
    spoken = sounds_menu(rig, [DOWN] * 9 + [ENTER, RIGHT, LEFT, LEFT, DOWN])
    assert spoken[2].startswith("Sounds. 11 items.")
    assert spoken[10] == words.POOLS_ITEM
    assert spoken[11:16] == ["Commercials: off.", "Commercials: at every break, 0 files found.",
                             "Commercials: at every second break, 0 files found.",
                             "Commercials: at every break, 0 files found.", "Commercials: off."]
    assert spoken[16] == words.COMMERCIALS_FOLDER_ITEM
    assert rig.game.options.settings.audio.commercials == "off" and rig.saves.count == 4


def test_the_sound_pools_item_tells_each_pool_its_counts_and_the_next_name_and_plays_its_sounds_in_turn(tmp_path):
    from wavmaker import write
    folder = tmp_path / "sounds"
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / "celebration2.wav", [0.2] * 400, rate=11025)
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN] * 8 + [ENTER, ENTER, ENTER, DOWN, ENTER, ESC])
    ambient = "Ambient sounds while a key is awaited, 3 original, none added. A new file is named ambient1."
    celebration = "Celebration sounds, 10 original, 1 added. A new file is named celebration3."
    assert any(line.endswith(ambient) and line.startswith("Sound pools. 2 items.") for line in spoken)
    assert "Sound 1 of 3, original." in spoken and "Sound 2 of 3, original." in spoken
    assert celebration in spoken and "Sound 1 of 11, original." in spoken
    assert [pid for pid, _ in extra_plays(rig)][-3:] == ["snd_foot8", "snd_foot9", "snd_foot15"]


def test_left_lowers_the_sound_volume_by_five_decibels_saves_it_and_plays_a_sample(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [LEFT, LEFT, RIGHT])
    assert spoken[3:6] == ["Sound volume: minus 5 decibels.", "Sound volume: minus 10 decibels.", "Sound volume: minus 5 decibels."]
    assert rig.game.options.wavol == -500 and rig.sounds.wavol == -500           # the game's sounds read the same value
    assert extra_plays(rig) == [("snd_foot0", -500), ("snd_foot0", -1000), ("snd_foot0", -500)]   # F11's own demo sound
    assert rig.saves.count == 3


def test_the_sound_volume_stops_at_full_and_at_minus_fifty_decibels_and_enter_restores_it(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [RIGHT] + [LEFT] * 12 + [ENTER])
    assert spoken[3] == "Sound volume: full, original."                          # Right at full changes nothing
    assert spoken[-3] == "Sound volume: minus 50 decibels." and spoken[-2] == "Sound volume: full, original."
    assert rig.game.options.wavol == 0


def test_restore_the_original_sound_settings_resets_the_volume(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.options.set_wavol(-1500)
    spoken = sounds_menu(rig, [DOWN] * 5 + [ENTER])
    assert spoken[-2] == words.SOUNDS_RESTORED and rig.game.options.wavol == 0


def test_listen_to_the_sounds_one_by_one_plays_each_at_the_players_volume(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.options.set_wavol(-300)
    spoken = sounds_menu(rig, [DOWN, ENTER, ENTER, DOWN, ENTER, DOWN, ENTER, ESC])
    assert spoken[4:7] == ["Listen to the sounds. 27 items. Press F1 for help. foot0, intro music", "foot1, crowd bed 1",
                           "foot2, crowd bed 2"]
    assert extra_plays(rig) == [("snd_foot0", -300), ("snd_foot1", -300), ("snd_foot2", -300)]
    assert rig.keys.answers == []


def test_the_exit_beep_is_the_last_sound_and_plays_through_its_chain(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN, ENTER, END, ENTER, ESC])
    assert "beep_exit, the exit beep" in spoken and rig.beeper.calls == 1


def test_a_players_file_is_named_in_the_list(tmp_path):
    rig = rig_for(tmp_path, [])
    write(tmp_path / "sounds" / "foot7.wav", sine(400, 0.02, 11025), rate=11025)
    rig.audio.refresh()
    spoken = sounds_menu(rig, [DOWN, ENTER] + [DOWN] * 7 + [ESC])
    assert "foot7, kick, your file" in spoken


def test_reload_says_how_many_sounds_it_found(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN, DOWN, ENTER])
    assert spoken[3:6] == [words.PREVIEW_ITEM, words.RELOAD_ITEM, "27 sounds found."]


def test_check_counts_the_problems_and_the_details_go_to_the_log(tmp_path, caplog):
    rig = rig_for(tmp_path, [])
    caplog.set_level("INFO", logger="nfl4.game")
    assert sounds_menu(rig, [DOWN, DOWN, DOWN, ENTER])[6] == words.checked(0)
    rig = rig_for(tmp_path, [])
    (tmp_path / "sounds" / "foot12.wav").write_bytes(b"RIFF not a sound")
    rig.audio.refresh()
    assert sounds_menu(rig, [DOWN, DOWN, DOWN, ENTER])[6] == words.checked(1)
    assert any("foot12.wav" in r.message for r in caplog.records)


def test_the_sounds_folder_item_opens_the_players_sounds_folder(tmp_path):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN, DOWN, DOWN, DOWN, ENTER])
    assert rig.folders.opened == [str(tmp_path / "sounds")] and spoken[-2] == words.opening_folder()


def test_restore_one_sound_moves_the_players_file_aside_and_says_so(tmp_path):
    rig = rig_for(tmp_path, [])
    write(tmp_path / "sounds" / "foot7.wav", sine(400, 0.02, 11025), rate=11025)
    rig.audio.refresh()
    spoken = sounds_menu(rig, [DOWN] * 6 + [ENTER] + [DOWN] * 7 + [ENTER, ESC])
    assert "foot7, kick is back to the original. Your file was moved to the removed sounds folder. foot7, kick" in spoken
    assert not (tmp_path / "sounds" / "foot7.wav").exists()
    assert (tmp_path / "sounds" / REMOVED_FOLDER / "foot7.wav").exists()


def test_restore_all_needs_one_enter_any_other_key_cancels(tmp_path):
    rig = rig_for(tmp_path, [])
    write(tmp_path / "sounds" / "foot7.wav", sine(400, 0.02, 11025), rate=11025)
    spoken = sounds_menu(rig, [DOWN] * 7 + [ENTER, "x"])
    assert words.CONFIRM_RESTORE_ALL in spoken and words.NOTHING_CHANGED in spoken
    assert (tmp_path / "sounds" / "foot7.wav").exists()
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN] * 7 + [ENTER, ENTER])
    assert words.CONFIRM_RESTORE_ALL in spoken and any(t.startswith("All sounds are back to the original") for t in spoken)
    assert not (tmp_path / "sounds" / "foot7.wav").exists()


def test_a_sound_system_that_did_not_start_is_the_first_item(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.audio.error = "no device"
    spoken = sounds_menu(rig, [])
    assert spoken[2] == ("Sounds. 10 items. Press F1 for help. " + words.NO_SOUND_DEVICE_ITEM)


def test_without_a_sound_layer_the_sounds_item_says_so(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.sounds = None
    spoken = sounds_menu(rig, [])
    assert spoken[2] == words.NO_SOUND_DEVICE_ITEM
