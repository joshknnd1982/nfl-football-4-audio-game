"""Start NFL Football 4: window, speech, game thread. This is inspired by Jim Kitchen.

Threads: the main thread runs the window and posts keys and typed characters; the game thread runs the program flow
the way the original's Form_Load did (waits, DoEvents-style key pumping); the SAPI 5 speech thread owns the voices.
Closing the window ends the game thread at its next key pump or speech wait.
Process lifetime (CLAUDE.md 0.10, playbook 7.2.1): the working directory leaves the program folder first thing, the
window's close arms an exit deadline, and the entry points end with finish(main()), so nothing stays behind.
P7 S7.1: speech, window, settings, the voice crash guard and the lifecycle; the sound (S7.2) and the game (S7.3 to
S7.5) come next.
"""
from __future__ import annotations

import logging
import os
import threading

from . import VERSION
from .data import paths
from .data.lifecycle import arm_exit_deadline, leave_program_folder
from .data.logsetup import install_exception_logging, setup_logging
from .data.settingsfile import SettingsStore
from .data.voiceguard import VoiceGuard, voice_label
from .game import texts
from .game.flow import Game
from .game.keys import GameQuit, KeyInput
from .speech import create_speech
from .speech.roles import ROLES

log = logging.getLogger("nfl4")


def main() -> int:
    log_path = setup_logging(logging.DEBUG if os.environ.get("NFL4_DEBUG") else logging.INFO)
    install_exception_logging()
    log.info("NFL Football 4 clone %s starting; log %s", VERSION, log_path)
    leave_program_folder(paths.program_dir(), paths.user_data_dir())   # never hold the program folder open
    from .ui import window as window_module

    store = SettingsStore()
    settings = store.load()     # creates, reads or heals settings.txt; the original values when anything is wrong
    keys = KeyInput()
    speech_holder: dict = {}
    deadlines: list = []                    # timers that end the process if closing hangs; cancelled when main() returns

    def on_close():
        deadlines.append(arm_exit_deadline())   # an orderly close that hangs must not leave the process behind
        keys.close()
        speech = speech_holder.get("speech")
        if speech is not None:
            speech.stop()

    frame = window_module.GameWindow(keys.post, on_close, on_char=keys.post_char)
    frame.show()

    guard = VoiceGuard(paths.user_data_dir())
    guard.recover()                         # a voice that took the last run down is set aside (data/voiceguard.py)
    crashed = {voice.strip().lower() for voice in guard.crashed()}
    skipped = {}                            # saved voice -> the speakers that use the first voice instead this run
    for role in ROLES:
        saved = settings.speech.voices.get(role)
        if saved and saved.strip().lower() in crashed:
            skipped.setdefault(saved, []).append(role)
    speech, started = create_speech(settings.speech, skip=frozenset(crashed),
                                    arm=lambda voice_id: guard.arm(voice_id) if voice_id else None,
                                    clear=lambda voice_id: guard.clear(voice_id) if voice_id else None)
    speech_holder["speech"] = speech
    if not started.ok:
        guard.clear()                       # no voice at all is not a crash
        for timer in deadlines:
            timer.cancel()
        no_voices(speech, frame, started.error)
        speech.close()
        return 1
    note_voices(store, speech, settings, skipped)
    store.voice_name = lambda role: _voice_name(speech, role)   # the note above each saved voice in settings.txt

    def game_thread():
        try:
            Game(speech, keys, notice_sources=(store,)).run()
        except GameQuit:
            pass
        except Exception:
            log.exception("unexpected error in the game thread")
        finally:
            log.debug("game thread ended")
            frame.close()                   # thread-safe: posts WM_CLOSE to the window

    thread = threading.Thread(target=game_thread, name="game", daemon=True)
    thread.start()
    frame.run()
    log.debug("main loop ended")
    keys.close()
    thread.join(2.0)
    speech.close()
    guard.clear()                           # closed normally: whatever voice was in use did not crash
    for timer in deadlines:
        timer.cancel()                      # main() ends: the entry point ends the process (data/lifecycle.finish)
    log.info("NFL Football 4 clone closed")
    return 0


def _voice_name(speech, role: str) -> str:
    details = speech.role_details(role)
    return details.name if details is not None else ""


def note_voices(store, speech, settings, skipped: dict) -> None:
    """One notice per voice that crashed the program last time, and one if a saved voice is not installed now."""
    for saved, roles in skipped.items():
        store.note_voice_crashed(voice_label(saved), _voice_name(speech, roles[0]))   # the first voice, used instead
    for role in ROLES:
        saved = settings.speech.voices.get(role)
        if not saved or saved in skipped:
            continue
        details = speech.role_details(role)
        if details is not None:
            store.note_voice_fallback(saved, details.voice_id)


def no_voices(speech, frame, error: str) -> None:
    """GAP_REGISTER G-F9: the sentence through a screen reader when one runs, the original's kind of box, the end."""
    log.error("no SAPI 5 voice: %s", error)
    speech.screen_reader_message(texts.NO_VOICES_SPOKEN)
    frame.message_box(texts.NO_VOICES + "\n" + texts.NO_VOICES_CONTACT, texts.MESSAGE_TITLE)
    frame.destroy()
