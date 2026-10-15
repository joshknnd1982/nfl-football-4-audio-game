"""F9, the clone's added functions: speech settings, sounds, about. This is inspired by Jim Kitchen.

GAP_REGISTER G-K2 (F9 is the one function key the original does not use; it gave the invalid-key character "x"), D-018,
D-045. F9 is a global key like F5 to F12: `HotKeys.added["120"]` runs `Functions.run`, which clears the key, stops the speech,
opens one spoken menu with three items and ends like every global menu with clk and g = "112". The menus are the starter kit's
(game/spoken_menu.py) with this game's items; they read keys with `KeyInput.read_key`, so a key typed ahead is never lost.

* Speech settings: the speech output (SAPI 5 voice only, which is nfl4's default, NVDA only, JAWS only, automatic), the speech
  rate (the same value Ctrl changes), the pitch, the letter keys of the lists, the five voices (the same pickers as F12),
  restore, and the settings folder. Volumes are F11's.
* Sounds: the sound volume (the same value as F11's second part, in steps of 5 decibels here), listen to the sounds one by
  one, reload, check, the sounds folder, restore one or all. Nothing to export: the game has no generated sound but the exit
  beep (SOUND_DESIGN 3); a sound-system failure (G-A4) is said as the first item.
* Customize (S7.7, 7.9: the names and the commentary): open the folder, reload, check, reset one list, reset all.
* About: the attribution of rule 0.5 and the note of the original's author.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Callable

from ..audio.ids import SOUND_IDS, canonical_id, describe
from ..audio.output import EXTRA_SLOT
from ..audio.restore import restore_all_sounds, restore_sound
from ..data import paths
from ..data.customize import SPECS
from ..data.settings import SOUND_LEVEL_MAX, SOUND_LEVEL_MIN
from ..speech.manager import MODES
from . import extra_texts as words
from . import prompt_texts as T
from .keys import KEY_ENTER, GameQuit
from .spoken_menu import Item, ListPicker, SpokenMenu, TextPages

log = logging.getLogger("nfl4.game")

KEY_F9 = "120"
RATE_RANGE = (-10, 10)
PITCH_RANGE = (-10, 10)
SOUND_STEP = 500             # Left and Right: 5 decibels (F11 moves 1 decibel at a time)


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


class Functions:
    def __init__(self, game, open_folder: Callable[[str], bool] = paths.open_folder, settings_dir: str | None = None,
                 clock: Callable[[], float] = time.monotonic):
        self.g = game
        self.open_folder = open_folder
        self.settings_dir = settings_dir
        self.clock = clock
        self._speech_original = type(game.options.settings.speech)()     # the original values, for "original" and restore

    # ----- the key -----

    def install(self) -> None:
        self.g.hotkeys.added[KEY_F9] = self.run

    @property
    def speech(self):
        return self.g.speech

    @property
    def keys(self):
        return self.g.keys

    @property
    def options(self):
        return self.g.options

    @property
    def audio(self):
        return self.g.sounds.audio if self.g.sounds is not None else None

    def run(self) -> None:
        """The menu, then the global menus' ending (clk, g = F1). Never raises, except GameQuit."""
        self.keys.clk()
        self.g.stopspeech()
        try:
            items = [Item(lambda: words.SPEECH_ITEM, enter=self._enter(self.speech_menu)),
                     Item(lambda: words.SOUNDS_ITEM, enter=self._enter(self.sounds_menu)),
                     Item(lambda: words.CUSTOMIZE_ITEM, enter=self._enter(self.customize_menu)),
                     Item(lambda: words.ABOUT_ITEM, enter=self._enter(self.about))]
            SpokenMenu(self.speech, self.keys, words.F9_TITLE, items, help_text=words.F9_HELP).run()
        except GameQuit:
            raise
        except Exception:
            log.exception("F9 failed")
            self.speech.stop()
            self.speech.say_async(words.FAILED)
        self.g.hotkeys._hand_back()

    def _enter(self, menu: Callable[[], None]) -> Callable[[], None]:
        def enter() -> None:
            try:
                menu()
            except GameQuit:
                raise
            except Exception:
                log.exception("an F9 menu failed")
                self.speech.stop()
                return words.FAILED
            return None
        return enter

    def about(self) -> None:
        TextPages(self.speech, self.keys, words.ABOUT_TITLE, words.ABOUT_LINES).run()

    # ----- speech settings -----

    def speech_menu(self) -> None:
        options = self.options
        sp, original = options.settings.speech, self._speech_original

        def rate() -> int:
            return options.vr

        def change_rate(step: int) -> None:
            options.set_vr(clamp(rate() + step, *RATE_RANGE))
            options.save()

        def reset_rate() -> None:
            sp.rate = original.rate                   # None: the first voice's own rate again
            self.speech.set_rate(options.vr)
            options.save()

        def change_pitch(step: int) -> None:
            sp.pitch = clamp(sp.pitch + step, *PITCH_RANGE)
            self.speech.set_pitch(sp.pitch)
            options.save()

        def reset_pitch() -> None:
            sp.pitch = original.pitch
            self.speech.set_pitch(sp.pitch)
            options.save()

        def change_mode(step: int) -> None:
            sp.mode = MODES[(MODES.index(sp.mode) + step) % len(MODES)]
            self.speech.mode = sp.mode
            options.save()

        def reset_mode() -> None:
            sp.mode = original.mode
            self.speech.mode = sp.mode
            options.save()

        def change_letters(step: int) -> None:
            modes = words.LETTER_MODES
            sp.list_letters = modes[(modes.index(sp.list_letters) + step) % len(modes)]
            options.save()

        def reset_letters() -> None:
            sp.list_letters = original.list_letters
            options.save()

        def restore_all() -> str:
            reset_rate()
            reset_pitch()
            reset_mode()
            reset_letters()
            return words.SPEECH_RESTORED

        def voices() -> str:
            self.g.hotkeys.change_voice()             # the five pickers of F12 (G-S8), saved, the He and She words
            return words.VOICES_DONE

        def open_settings_folder() -> str:
            folder = self.settings_dir or paths.user_data_dir()
            return words.SETTINGS_FOLDER_OPENING if self.open_folder(folder) else words.SETTINGS_FOLDER_FAILED

        items = [
            Item(lambda: words.output_label(sp.mode, self.speech.nvda_running(), sp.mode == original.mode,
                                            self.speech.jaws_running()),
                 enter=reset_mode, change=change_mode),
            Item(lambda: words.rate_label(rate(), sp.rate is None), enter=reset_rate, change=change_rate),
            Item(lambda: words.pitch_label(sp.pitch, sp.pitch == original.pitch), enter=reset_pitch, change=change_pitch),
            Item(lambda: words.letters_label(sp.list_letters, sp.list_letters == original.list_letters),
                 enter=reset_letters, change=change_letters),
            Item(lambda: words.CHOOSE_VOICES_ITEM, enter=voices),
            Item(lambda: words.RESTORE_SPEECH, enter=restore_all),
            Item(lambda: words.SETTINGS_FOLDER_ITEM, enter=open_settings_folder),
        ]
        SpokenMenu(self.speech, self.keys, words.SETTINGS_TITLE, items, help_text=words.SETTINGS_HELP).run()

    # ----- sounds -----

    def sounds_menu(self) -> None:
        audio, options = self.audio, self.options
        if audio is None:                              # a rig or a program without a sound layer
            self.speech.stop()
            self.speech.say_async(words.NO_SOUND_DEVICE_ITEM)
            return
        library = audio.library

        def change_volume(step: int) -> None:
            options.set_wavol(clamp(options.wavol + step * SOUND_STEP, SOUND_LEVEL_MIN, SOUND_LEVEL_MAX))
            options.save()
            self.sample()

        def reset_volume() -> None:
            options.set_wavol(0)
            options.save()
            self.sample()

        def reload() -> str:
            audio.refresh()
            notices = library.take_notices()
            return " ".join([words.reloaded(len(SOUND_IDS))] + notices)

        def check() -> str:
            problems = library.check_all()
            library.take_notices()                     # the count says it; details are in the log
            for problem in problems:
                log.info("sound check: %s", problem)
            return words.checked(len(problems))

        def open_sounds_folder() -> str:
            library.refresh()                          # makes sure the folder and sounds.txt exist
            return words.opening_folder() if self.open_folder(library.player_dir) else words.FOLDER_FAILED

        def restore_volume() -> str:
            reset_volume()
            return words.SOUNDS_RESTORED

        items = []
        if not audio.ok:
            items.append(Item(lambda: words.NO_SOUND_DEVICE_ITEM))
        items += [
            Item(lambda: words.volume_label(options.wavol, options.wavol == 0), enter=reset_volume, change=change_volume),
            Item(lambda: words.PREVIEW_ITEM, enter=self._enter(self.preview_sounds)),
            Item(lambda: words.RELOAD_ITEM, enter=reload),
            Item(lambda: words.CHECK_ITEM, enter=check),
            Item(lambda: words.FOLDER_ITEM, enter=open_sounds_folder),
            Item(lambda: words.RESTORE_SOUNDS, enter=restore_volume),
            Item(lambda: words.RESTORE_ONE_ITEM, enter=self._enter(self.restore_one_sound)),
            Item(lambda: words.RESTORE_ALL_ITEM, enter=self.restore_all_sounds),
        ]
        SpokenMenu(self.speech, self.keys, words.SOUNDS_TITLE, items).run()

    # ----- customize (S7.7, G-K2, D-048) -----

    def customize_menu(self) -> None:
        """The names and the banter: open the folder, reload, check, reset one list, reset all (playbook 7.9, 7.10). Every
        action ends by applying the files' values to the game, so what is spoken next uses them."""
        custom = self.g.customization
        if custom is None:                             # a rig or a program without the player's files
            self.speech.stop()
            self.speech.say_async(words.CUSTOMIZE_NOT_AVAILABLE)
            return

        def open_customize_folder() -> str:
            try:
                os.makedirs(custom.sounds_dir, exist_ok=True)
            except OSError:
                log.warning("could not make %s", custom.sounds_dir, exc_info=True)
            return words.CUSTOMIZE_FOLDER_OPENING if self.open_folder(custom.folder) else words.CUSTOMIZE_FOLDER_FAILED

        def reload() -> str:
            notices = custom.reload()
            self.g.apply_customization()
            return words.customize_reloaded(custom.snapshot.banter.size, notices)

        def check() -> str:
            return custom.check()

        def list_name(index: int) -> str:
            return SPECS[index].nouns.capitalize()

        def reset_one(index: int) -> str:
            spec = SPECS[index]
            return guarded(lambda: reset_spec(spec))()

        def reset_spec(spec) -> str:
            result = custom.reset(spec.key)
            custom.reload()
            self.g.apply_customization()
            return words.customize_reset_one(spec.file_name, result)

        def reset_one_menu() -> None:
            ListPicker(self.speech, self.keys, words.CUSTOMIZE_RESET_ONE_TITLE, len(SPECS), list_name, on_enter=reset_one,
                       close_on_enter=False, help_text=words.CUSTOMIZE_RESET_ONE_HELP, clock=self.clock).run()

        def reset_all() -> str:
            self.speech.stop()
            self.speech.say_async(words.CUSTOMIZE_CONFIRM_RESET_ALL)
            if self.keys.read_key() != KEY_ENTER:
                return words.NOTHING_CHANGED
            result = custom.reset(None)
            custom.reload()
            self.g.apply_customization()
            return words.customize_reset_all(result)

        def guarded(action: Callable[[], str]) -> Callable[[], str]:
            """An action that fails says so and leaves the menu open (the player's files are never a reason to stop)."""
            def run() -> str:
                try:
                    return action()
                except GameQuit:
                    raise
                except Exception:
                    log.exception("a Customize action failed")
                    self.speech.stop()
                    return words.FAILED
            return run

        items = [
            Item(lambda: words.CUSTOMIZE_FOLDER_ITEM, enter=guarded(open_customize_folder)),
            Item(lambda: words.CUSTOMIZE_RELOAD_ITEM, enter=guarded(reload)),
            Item(lambda: words.CUSTOMIZE_CHECK_ITEM, enter=guarded(check)),
            Item(lambda: words.CUSTOMIZE_RESET_ONE_ITEM, enter=self._enter(reset_one_menu)),
            Item(lambda: words.CUSTOMIZE_RESET_ALL_ITEM, enter=guarded(reset_all)),
        ]
        SpokenMenu(self.speech, self.keys, words.CUSTOMIZE_TITLE, items, help_text=words.CUSTOMIZE_HELP).run()

    def sample(self) -> None:
        """Let the player hear the sound volume: the sound F11 plays as its demo, once, at the new level."""
        audio = self.audio
        audio.stop_preview()
        audio.play(EXTRA_SLOT, canonical_id(T.DEMO_SOUND), self.options.wavol)

    def _sound_name(self, index: int) -> str:
        sound_id = SOUND_IDS[index]
        return words.sound_name(describe(sound_id), self.audio.library.pick(sound_id).source)

    def preview_sounds(self) -> None:
        """The sounds one by one, the exit beep last; Enter plays one at the sound volume the player set."""
        audio = self.audio
        audio.library.refresh()

        def play(index: int) -> None:
            audio.stop_preview()
            sound_id = SOUND_IDS[index]
            if canonical_id(sound_id) == "beep_exit":
                audio.preview(sound_id)
            else:
                audio.play(EXTRA_SLOT, sound_id, self.options.wavol)
            return None

        try:
            ListPicker(self.speech, self.keys, words.PREVIEW_TITLE, len(SOUND_IDS), self._sound_name, on_enter=play,
                       close_on_enter=False, help_text=words.PREVIEW_HELP, clock=self.clock).run()
        finally:
            audio.stop_preview()

    def restore_one_sound(self) -> None:
        """A list of the sounds; Enter puts the chosen one back to the original (playbook 7.7, 7.10)."""
        library = self.audio.library
        library.refresh()

        def restore(index: int) -> str:
            result = restore_sound(library.player_dir, SOUND_IDS[index])
            library.refresh()
            return words.restored_one(describe(SOUND_IDS[index]), result) + " " + self._sound_name(index)

        ListPicker(self.speech, self.keys, words.RESTORE_ONE_TITLE, len(SOUND_IDS), self._sound_name, on_enter=restore,
                   close_on_enter=False, help_text=words.RESTORE_ONE_HELP, clock=self.clock).run()

    def restore_all_sounds(self) -> str:
        """Every sound back to the original, after one confirming Enter (it moves the player's own files)."""
        self.speech.stop()
        self.speech.say_async(words.CONFIRM_RESTORE_ALL)
        if self.keys.read_key() != KEY_ENTER:
            return words.NOTHING_CHANGED
        library = self.audio.library
        result = restore_all_sounds(library.player_dir)
        library.refresh()
        return words.restored_all(result)

