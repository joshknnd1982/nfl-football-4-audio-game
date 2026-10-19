"""Spoken texts of the clone's added functions (help, settings, sounds, about, notices). This is inspired by Jim Kitchen.

None of these exist in the original; the original's own texts stay in texts.py. The help texts below are still the
starter kit's (Brain's F1 to F4 menus): S7.4 rewrites them for nfl4's F9 menu (GAP_REGISTER G-K2, section 8); the
about text and the names are nfl4's since S7.1.
"""
from __future__ import annotations

import os

from .. import VERSION

# ----- menus in general -----
MENU_HELP = ("Up and Down move through the items. Left and Right change a value. "
             "Enter does the item's action or restores a value to its original. Escape goes back.")
LIST_HELP = ("Up and Down move one item, Page Up and Page Down move ten, Home and End jump to the ends. "
             "Typing letters jumps to a name that begins with them. Enter chooses. Escape goes back.")
PREVIEW_HELP = ("Up and Down move through the sounds, Page Up and Page Down move ten, Home and End jump "
                "to the ends. Enter plays the sound. Escape goes back.")
PAGES_HELP = "Up and Down read the lines one by one. Escape goes back."
GOING_BACK = "Back."
ORIGINAL = "original"


def menu_opening(title: str, count: int) -> str:
    return f"{title}. {count} items. Press F1 for help."


# ----- the added functions (F9): help and about -----
F9_TITLE = "Added functions"
F9_HELP = (MENU_HELP + " The five items are the speech settings, the sounds, the names and the banter, the rules, and the "
           "about text. "
           "The original's own keys work as always: Control sets the speech rate, F11 the volumes, F12 the voices.")
# nfl4 only (SX.9): with the N. F. L. rules the Franchise item is a sixth item, before About
F9_HELP_FRANCHISE = (MENU_HELP + " The six items are the speech settings, the sounds, the names and the banter, the rules, the "
                     "franchise, and the about text. "
                     "The original's own keys work as always: Control sets the speech rate, F11 the volumes, F12 the voices.")
SPEECH_ITEM = "Speech settings."
SOUNDS_ITEM = "Sounds."
ABOUT_ITEM = "About NFL Football 4."
CHOOSE_VOICES_ITEM = "Choose the five voices, the same as F12."
VOICES_DONE = "Back from the voices."

ABOUT_TITLE = "About NFL Football 4"
ABOUT_LINES = (
    f"NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen. Version {VERSION}. "
    "A new version of Jim Kitchen's N. F. L. football version 4.",
    "This is inspired by Jim Kitchen. Jim Kitchen was blind from birth. "
    "He made his games free for the blind community. He died in 2015.",
    "This version is new code, written from a description of how his program behaves. "
    "It plays his original sound files.",
    # nfl4 only (rule 0.13, NFL_EXTRA_FEATURES NX-R6, SX.9): the added rules and the franchise, and the trademark notice. The notice is the
    # only text of the game that names Madden or Electronic Arts (tests/test_sx9_about.py)
    "Added to the original game: the N. F. L. rules, with a real clock and time outs, penalties you may accept or decline, "
    "onside kicks, quarterback runs, replay challenges and playbooks, and a franchise that lasts from season to season. "
    "The Rules item of this menu switches them, or chooses Classic, the game exactly as the original.",
    "The playbooks and the franchise are inspired by the playbooks and franchise ideas of Madden N. F. L. "
    "Madden N. F. L. is a trademark of Electronic Arts. "
    "This project is not made, endorsed or supported by Electronic Arts or the N. F. L.",
)

# ----- settings menu (F2) -----
SETTINGS_TITLE = "Speech settings"
SOUNDS_TITLE = "Sounds"
OUTPUT_NAMES = {"sapi": "SAPI 5 voice only", "nvda": "NVDA only", "jaws": "JAWS only", "auto": "automatic"}
NVDA_NOT_RUNNING = "NVDA is not running now, so the SAPI 5 voice is used."
JAWS_NOT_RUNNING = "JAWS is not running now, so the SAPI 5 voice is used."
NEITHER_RUNNING = "NVDA and JAWS are not running now, so the SAPI 5 voice is used."
PITCH_NOTE = "Not every voice supports it."
SETTINGS_HELP = (MENU_HELP + " On the voice item, Enter lets you choose another voice. "
                 "Speech pitch: " + PITCH_NOTE)


def voice_label(name: str) -> str:
    return f"Voice: {name or 'unknown'}."      # short: it is spoken at every arrow key (the hint is in the help)


def rate_label(rate: int, original: bool) -> str:
    return f"Speech rate: {rate}{', original' if original else ''}."


def percent_label(what: str, value: int, original: bool) -> str:
    return f"{what}: {value} percent{', original' if original else ''}."


def pitch_label(pitch: int, original: bool) -> str:
    return f"Speech pitch: {pitch}{', original' if original else ''}."


def output_label(mode: str, nvda_running: bool, original: bool, jaws_running: bool = False) -> str:
    text = f"Speech output: {OUTPUT_NAMES.get(mode, mode)}{', original' if original else ''}."
    if mode == "nvda" and not nvda_running:
        text += " " + NVDA_NOT_RUNNING
    elif mode == "jaws" and not jaws_running:
        text += " " + JAWS_NOT_RUNNING
    elif mode == "auto" and not (nvda_running or jaws_running):
        text += " " + NEITHER_RUNNING
    return text


# the debug log (owner rule 0.15, playbook 7.11): the level, and the problem report
DEBUG_LOG_NAMES = {"detailed": "detailed, the log that lets a bug on this computer be fixed",
                   "trace": "trace, even more detail, only when you are asked for it",
                   "normal": "normal, only problems and the main events",
                   "off": "off, no log at all, so a bug on this computer cannot be fixed"}
DEBUG_LOG_LEVELS = ("detailed", "trace", "normal", "off")


def debug_log_label(level: str) -> str:
    return f"Debug log: {DEBUG_LOG_NAMES.get(level, level)}{', the default' if level == 'detailed' else ''}."


PROBLEM_REPORT_ITEM = "Save a problem report."
PROBLEM_REPORT_TITLE = "Problem report"
PROBLEM_REPORT_HELP = (MENU_HELP + " Enter on the first item makes one file with what the game wrote down about this computer. "
                       "It never leaves your computer by itself: you send it.")
PROBLEM_REPORT_PLAIN = "Save the report without my saved games."
PROBLEM_REPORT_WITH_SAVES = "Save the report with my saved games and season files."
PROBLEM_REPORT_OPEN = "Open the folder with the last report."
PROBLEM_REPORT_SAVING = "Saving the problem report."
PROBLEM_REPORT_NONE_YET = "No report has been saved yet."


def problem_report_saved(path: str) -> str:
    folder = os.path.basename(os.path.dirname(path)) or "its folder"
    return (f"The problem report was saved in the {folder} folder as {os.path.basename(path)}. Send that file to the owner: "
            "the readme says how. Choose the next item to open the folder.")


def problem_report_failed(why: str) -> str:
    return f"The problem report could not be saved: {why}"


RESTORE_SPEECH = "Restore the original speech settings."
SETTINGS_FOLDER_ITEM = "Open the folder with the settings file."
SETTINGS_FOLDER_OPENING = "Opening the folder. The file is settings.txt."
SETTINGS_FOLDER_FAILED = "The settings folder could not be opened. Its place is in the readme."
SPEECH_RESTORED = "The original speech settings are back."

# letter keys in lists (settings item, list help)
LETTER_MODES = ("type", "first")
LETTER_NAMES = {"type": "type letters to search for a name",
                "first": "a letter jumps to the next name with that first letter"}
LIST_HELP_FIRST = ("Up and Down move one item, Page Up and Page Down move ten, Home and End jump to the ends. "
                   "Pressing a letter jumps to the next name that starts with it; press it again for the one after. "
                   "Enter chooses. Escape goes back.")


def letters_label(mode: str, original: bool) -> str:
    return f"Letter keys in lists: {LETTER_NAMES.get(mode, mode)}{', original' if original else ''}."


def list_help(mode: str) -> str:
    return LIST_HELP_FIRST if mode == "first" else LIST_HELP


# engine list and voice list
ENGINE_TITLE = "Choose a speech engine"
ENGINE_HELP = ("Each item is a speech engine and how many voices it has. The first item lists all the voices of all "
               "engines. Enter opens the voices of the engine. Escape goes back. " + LIST_HELP)
ALL_VOICES_TITLE = "All voices of all engines"


def all_voices_item(count: int) -> str:
    return f"All voices of all engines, {count} voices"


def engine_item(name: str, count: int) -> str:
    return f"{name}, {count} voice{'' if count == 1 else 's'}"


def engine_voices_title(name: str) -> str:
    return f"Voices of {name}"


VOICE_TITLE = "Choose a voice"
NO_VOICES_LISTED = "No voices were found."
VOICE_LIST_LOADING = "The voice list is not ready yet. Try again in a moment."
CURRENT_VOICE = "current voice"


def voice_chosen(name: str) -> str:
    return f"Voice set to {name}."


VOICE_SAMPLE = "This is how this voice will speak in N. F. L. football."


# ----- sounds menu (F3) -----
def volume_label(level: int, original: bool) -> str:
    """The sound volume wavol (hundredths of a decibel, 0 to -5000): "Sound volume: full" or "minus 12 decibels"."""
    decibels = -level // 100
    text = "Sound volume: full" if decibels <= 0 else f"Sound volume: minus {decibels} decibel{'' if decibels == 1 else 's'}"
    return f"{text}{', original' if original else ''}."


# numbered sound pools and commercials (owner rule 0.14, playbook 7.7.1)
POOLS_ITEM = "Sound pools you can add your own sounds to."
POOLS_TITLE = "Sound pools"
POOLS_HELP = ("Up and Down move through the pools. Enter plays the next sound of the pool. To add a sound, put the file in "
              "the sounds folder and name it with the pool's name and a new number, the name is spoken with the pool. "
              "Then reload the sounds. Escape goes back.")
COMMERCIAL_CUE = "Commercial. Any key skips it."
COMMERCIALS_FOLDER_ITEM = "Open the commercials folder."
COMMERCIALS_FOLDER_OPENING = "Opening the commercials folder."
COMMERCIALS_FOLDER_FAILED = "The commercials folder could not be opened. Its place is in the readme."
_COMMERCIAL_WORDS = {"off": "off", "every": "at every break", "second": "at every second break",
                     "third": "at every third break"}


def commercials_label(value: str, found: int) -> str:
    """Spoken: "Commercials: off." or "Commercials: at every break, 3 files found." The files are the player's own."""
    words_ = _COMMERCIAL_WORDS.get(value, "off")
    if value == "off":
        return "Commercials: off."
    return f"Commercials: {words_}, {found} file{'' if found == 1 else 's'} found."


def pool_name(label: str, base: str, original: int, added: int, next_number: int) -> str:
    """Spoken: "Celebration sounds, 10 original, 2 added. A new file is named celebration3." """
    added_text = f"{added} added" if added else "none added"
    return f"{label.capitalize()}, {original} original, {added_text}. A new file is named {base}{next_number}."


def pool_played(position: int, count: int, source: str) -> str:
    kind = "your file" if source == "player" else "original"
    return f"Sound {position} of {count}, {kind}."


NO_SOUND_DEVICE_ITEM = "The sound system could not be started, so the game runs without sounds. Details are in the log."

PREVIEW_ITEM = "Listen to the sounds one by one."
RELOAD_ITEM = "Reload the sounds from the folder."
CHECK_ITEM = "Check the sound files."
FOLDER_ITEM = "Open the sounds folder."
RESTORE_SOUNDS = "Restore the original sound settings."
SOUNDS_RESTORED = "The original sound settings are back."
RESTORE_ONE_ITEM = "Restore one sound to the original."
RESTORE_ALL_ITEM = "Restore all sounds to the original."
RESTORE_ONE_TITLE = "Restore one sound"
RESTORE_ONE_HELP = ("Up and Down move through the sounds, Page Up and Page Down move ten, Home and End jump "
                    "to the ends. Enter puts the original sound back. Escape goes back.")
CONFIRM_RESTORE_ALL = ("This puts every sound back to the original. Your own sound files are moved to the removed "
                       "sounds folder, and sounds.txt starts again. Press Enter to do it, or any other key to cancel.")
NOTHING_CHANGED = "Nothing was changed."
PREVIEW_TITLE = "Listen to the sounds"
EXIT_BEEP_NAME = "exit beep"


def sound_name(described: str, source: str) -> str:
    """"foot7, kick, your file": the sound as audio.ids.describe words it, and where the game takes it from."""
    extra = {"player": ", your file", "off": ", switched off", "none": ", no usable file"}.get(source, "")
    return described + extra


def reloaded(count: int) -> str:
    return f"{count} sound{'s' if count != 1 else ''} found."


def checked(problems: int) -> str:
    if not problems:
        return "No problems found in the sound files."
    return f"{problems} problem{'s' if problems != 1 else ''} found, details are in the log."


def opening_folder() -> str:
    return "Opening the sounds folder."


FOLDER_FAILED = "The sounds folder could not be opened. Its place is in the readme."


def restored_one(described: str, result) -> str:
    if result.failed:
        return f"{described} could not be fully restored, details are in the log."
    if not result.changed:
        return f"{described} was already the original."
    text = f"{described} is back to the original."
    if result.moved:
        text += " Your file was moved to the removed sounds folder."
    return text


def restored_all(result) -> str:
    if result.failed:
        return "The sounds could not all be restored, details are in the log."
    text = "All sounds are back to the original. The old sounds.txt was kept as sounds.txt.before-reset."
    if result.moved:
        text += f" {len(result.moved)} of your sound file{'s were' if len(result.moved) != 1 else ' was'} moved to the removed sounds folder."
    return text



# ----- customize menu (S7.7, G-K2, D-048) -----
CUSTOMIZE_ITEM = "Customize the names and the banter."
CUSTOMIZE_TITLE = "Customize"
CUSTOMIZE_HELP = (MENU_HELP + " The files are plain text. Open the folder, change a file in any text editor, save it, "
                  "then choose Reload. A game in progress keeps the players it already has.")
CUSTOMIZE_NOT_AVAILABLE = "The customization files are not available."
CUSTOMIZE_FOLDER_ITEM = "Open the folder with the names and banter files."
CUSTOMIZE_FOLDER_OPENING = ("Opening the folder. The files are teams.txt, divisions.txt, surnames.txt and banter.txt. "
                            "Your own sound files for the banter go in the sounds folder inside it.")
CUSTOMIZE_FOLDER_FAILED = "The customization folder could not be opened. Its place is in the readme."
CUSTOMIZE_RELOAD_ITEM = "Reload the names and the banter from the files."
CUSTOMIZE_CHECK_ITEM = "Check the customization files."
CUSTOMIZE_RESET_ONE_ITEM = "Reset one list to the original."
CUSTOMIZE_RESET_ALL_ITEM = "Reset all lists to the original."
CUSTOMIZE_RESET_ONE_TITLE = "Reset one list"
CUSTOMIZE_RESET_ONE_HELP = ("Up and Down move through the lists. Enter puts the original back. Your file is kept with the "
                            "ending before-reset. Escape goes back.")
CUSTOMIZE_CONFIRM_RESET_ALL = ("This puts the original team names, division names, surnames and banter lines back. Your files "
                               "are kept with the ending before-reset. Your sound files and footplay.txt are not touched. "
                               "Press Enter to do it, or any other key to cancel.")


def customize_reloaded(banter_lines: int, notices: list[str]) -> str:
    text = f"The files were read again. {banter_lines} banter line{'s are' if banter_lines != 1 else ' is'} on."
    return " ".join([text] + [notice.strip() for notice in notices])


def customize_reset_one(file_name: str, result) -> str:
    if result.failed:
        return f"{file_name} could not be reset, details are in the log."
    text = f"{file_name} is back to the original."
    if result.kept:
        text += f" Your file was kept as {file_name}.before-reset."
    return text


def customize_reset_all(result) -> str:
    if result.failed:
        return "Not every list could be reset, details are in the log."
    text = "All lists are back to the original."
    if result.kept:
        text += " Your files were kept with the ending before-reset."
    return text

FAILED = "Something went wrong, details are in the log."
FAILED_BACK_TO_MENU = "Something went wrong, details are in the log. Back to the main menu."
GIVING_UP = "The game keeps running into the same problem and has to close. Details are in the log."

# ----- notices at startup and at playback -----
NO_SOUND_DEVICE = "No sound device was found, so the game will run without sound."
