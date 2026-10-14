"""Spoken texts of the clone's added functions (help, settings, sounds, about, notices). This is inspired by Jim Kitchen.

None of these exist in the original; the original's own texts stay in texts.py. The help texts below are still the
starter kit's (Brain's F1 to F4 menus): S7.4 rewrites them for nfl4's F9 menu (GAP_REGISTER G-K2, section 8); the
about text and the names are nfl4's since S7.1.
"""
from __future__ import annotations

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


# ----- help (F1) and about (F4) -----
HELP_TITLE = "Help"
HELP_LINES = (
    "In the main menu, press a number from 1 to 9 to choose how many sounds play at once. "
    "Then press Up or Down to choose a panning style, and Enter to start. "
    "Any key stops the sounds and returns to the main menu. Escape leaves the program.",
    "F1 is this help. F2 opens the settings for speech. F3 opens the sounds menu. F4 tells about this program. "
    "They work in the main menu and in the panning menu.",
    "In a menu, Up and Down move, Left and Right change a value, Enter chooses or restores the original value, "
    "and Escape goes back.",
)

ABOUT_TITLE = "About NFL Football 4"
ABOUT_LINES = (
    f"NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen. Version {VERSION}. "
    "A new version of Jim Kitchen's N. F. L. football version 4.",
    "This is inspired by Jim Kitchen. Jim Kitchen was blind from birth. "
    "He made his games free for the blind community. He died in 2015.",
    "This version is new code, written from a description of how his program behaves. "
    "It plays his original sound files.",
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


RESTORE_SPEECH = "Restore the original speech settings."
SETTINGS_FOLDER_ITEM = "Open the folder with the settings file."
SETTINGS_FOLDER_OPENING = "Opening the folder. The file is settings.txt."
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
def volume_label(value: int, original: bool) -> str:
    return percent_label("Sound volume", value, original)


def spread_label(spread: int, original: bool) -> str:
    base = f"Pitch variation: {spread} of 20" if spread else "Pitch variation: none, every sound plays at its own pitch"
    return f"{base}{', original' if original else ''}."


def start_label(early: bool, original: bool) -> str:
    base = "Sounds start: right away, while the prompt is spoken" if early else "Sounds start: after the spoken prompt"
    return f"{base}{', original' if original else ''}."


PREVIEW_ITEM = "Listen to the sounds one by one."
RELOAD_ITEM = "Reload the sounds from the folder."
CHECK_ITEM = "Check the sound files."
FOLDER_ITEM = "Open the sounds folder."
EXPORT_ITEM = "Save the generated sounds as wav files."
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


def sound_name(number: int | None, source: str) -> str:
    base = "Exit beep" if number is None else f"Sound {number}"
    extra = {"player": ", your file", "off": ", switched off", "none": ", no usable file"}.get(source, "")
    return base + extra


def reloaded(count: int) -> str:
    return f"{count} sound{'s' if count != 1 else ''} found."


def checked(problems: int) -> str:
    if not problems:
        return "No problems found in the sound files."
    return f"{problems} problem{'s' if problems != 1 else ''} found, details are in the log."


def opening_folder() -> str:
    return "Opening the sounds folder."


FOLDER_FAILED = "The sounds folder could not be opened. Its place is in the readme."


def exported(count: int) -> str:
    return (f"{count} generated sound{'s' if count != 1 else ''} saved as wav files, "
            "in the exported sounds folder next to the sounds folder.")


EXPORT_FAILED = "The generated sounds could not be saved, details are in the log."

def restored_one(number: int | None, result) -> str:
    name = "The exit beep" if number is None else f"Sound {number}"
    if result.failed:
        return f"{name} could not be fully restored, details are in the log."
    if not result.changed:
        return f"{name} was already the original."
    text = f"{name} is back to the original."
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


FAILED = "Something went wrong, details are in the log."
FAILED_BACK_TO_MENU = "Something went wrong, details are in the log. Back to the main menu."
GIVING_UP = "The game keeps running into the same problem and has to close. Details are in the log."

# ----- notices at startup and at playback -----
NO_SOUND_DEVICE = "No sound device was found, so the game will run without sound."
