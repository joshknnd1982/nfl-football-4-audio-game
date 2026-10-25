"""Start NFL Football 4: window, speech, game thread. This is inspired by Jim Kitchen.

Threads: the main thread runs the window and posts keys and typed characters; the game thread runs the program flow
the way the original's Form_Load did (waits, DoEvents-style key pumping); the SAPI 5 speech thread owns the voices.
Closing the window ends the game thread at its next key pump or speech wait.
Process lifetime (CLAUDE.md 0.10, playbook 7.2.1): the working directory leaves the program folder first thing, the
window's close arms an exit deadline, and the entry points end with finish(main()), so nothing stays behind.
P7 S7.1: speech, window, settings, the voice crash guard and the lifecycle. P7 S7.2: the sound layer (the mixer with
the original's seven slots, every sound resolved once at start so a bad file is reported then, the sound procedures
handed to the game). The game itself (S7.3 to S7.5) comes next. P7 S7.4a: the Options the hot keys change and save. P7 S7.4b: the
start-up, week loop, main menu and exit of game/program.py. P7 S7.5: the player's files (data/files: the season, the saved
game, footplay.txt, footballlog.txt) handed to the Game as its program store, season store, set-up store and log sink; the
first start is the one that made settings.txt.
"""
from __future__ import annotations

import logging
import os
import sys
import threading

from . import VERSION
from .audio import Audio, SoundLibrary
from .data import debuglog, paths, problem_report, sysreport
from .data.customize import Customization
from .data.files.store import FileProgramStore
from .data.lifecycle import arm_exit_deadline, leave_program_folder
from .data.logsetup import install_exception_logging, setup_logging
from .data.settingsfile import SettingsStore
from .data.voiceguard import VoiceGuard, voice_label
from .extras.nfl_rules import is_nfl, rules_from_settings
from .game import texts
from .game.flow import Game
from .game.keys import GameQuit, KeyInput
from .game.options import Options
from .game.rnd import GameRandom
from .game.commercials import Commercials
from .game.sounds import GameSounds
from .speech import create_speech
from .speech.roles import ALL_ROLES
from .speech.voices import VoiceCatalog

log = logging.getLogger("nfl4")


def main(argv=None) -> int:
    args = [str(a) for a in (argv or ())]
    if any(a.lower() == "--problem-report" for a in args):
        return problem_report.run_command(args)             # no window, no game: one zip for the owner (playbook 7.11)
    # the debug log starts first, at the level the command line, the environment or settings.txt names (default: detailed)
    level = (debuglog.level_from_environment(args) or debuglog.level_from_settings_file(paths.user_data_dir())
             or debuglog.DEFAULT_LEVEL)
    last_errors = debuglog.last_launch_errors()
    log_path = setup_logging(level)
    install_exception_logging()
    log.info("NFL Football 4 %s starting; log %s", VERSION, log_path)
    cwd_before = os.getcwd()
    moved = leave_program_folder(paths.program_dir(), paths.user_data_dir())   # never hold the program folder open
    cwd_after = os.getcwd() if moved else ""
    from .ui import window as window_module

    with debuglog.phase("settings"):
        store = SettingsStore()
        settings = store.load()     # creates, reads or heals settings.txt; the original values when anything is wrong
    if debuglog.level_from_environment(args) is None and settings.game.debug_log != debuglog.level_name():
        debuglog.set_level(settings.game.debug_log)         # the file said something other than the quick look at its text did
    first_start = store.created # this start made settings.txt: the original's missing footbal0.dat (the welcome, S7.4b)
    keys = KeyInput()
    speech_holder: dict = {}
    deadlines: list = []                    # timers that end the process if closing hangs; cancelled when main() returns

    def on_close():
        debuglog.set_exit_reason("window closed")
        deadlines.append(arm_exit_deadline())   # an orderly close that hangs must not leave the process behind
        keys.close()
        speech = speech_holder.get("speech")
        if speech is not None:
            speech.stop()

    with debuglog.phase("window"):
        frame = window_module.GameWindow(keys.post, on_close, on_char=keys.post_char)
        shown = frame.show()
    debuglog.event("app", "window_shown", in_front=shown, title=frame.title)

    guard = VoiceGuard(paths.user_data_dir())
    guard.recover()                         # a voice that took the last run down is set aside (data/voiceguard.py)
    crashed = {voice.strip().lower() for voice in guard.crashed()}
    skipped = {}                            # saved voice -> the speakers that use the first voice instead this run
    for role in ALL_ROLES:
        saved = settings.speech.voices.get(role)
        if saved and saved.strip().lower() in crashed:
            skipped.setdefault(saved, []).append(role)
    with debuglog.phase("speech start"):
        speech, started = create_speech(settings.speech, skip=frozenset(crashed),
                                        arm=lambda voice_id: guard.arm(voice_id) if voice_id else None,
                                        clear=lambda voice_id: guard.clear(voice_id) if voice_id else None)
    speech_holder["speech"] = speech
    if getattr(speech, "jaws", None) is not None:
        speech.jaws.key_waiting = keys.key_waiting     # 2026-10-23: a key ends a JAWS wait from its earliest end (speech/jaws.py)
    debuglog.event("speech", "started", ok=started.ok, voices=started.voice_count, voice=started.voice_name,
                   error=started.error or None, crashed_voices_skipped=len(crashed) or None)
    if not started.ok:
        guard.clear()                       # no voice at all is not a crash
        for timer in deadlines:
            timer.cancel()
        no_voices(speech, frame, started.error)
        speech.close()
        return 1
    note_voices(store, speech, settings, skipped)
    store.voice_name = lambda role: _voice_name(speech, role)   # the note above each saved voice in settings.txt
    with debuglog.phase("audio start"):
        audio = start_audio(settings)
    rnd = GameRandom()                      # ONE random function for the game and the sounds (G-D2); its seed is in the log
    sounds = GameSounds(audio, keys, settings.audio, rng=rnd)
    sounds.own_mode = lambda: settings.game.rules == "nfl"          # NX-M1 (D-148): the start's music follows the Rules setting (no music by default)
    sounds.commercials = Commercials(paths.commercials_dir())   # the player's own commercials (rule 0.14): none shipped, off by default
    # what the hot keys change, saved to settings.txt where the original wrote footbal0.dat or football.vol (S7.4a);
    # the voice list for F12 is read the first time F12 is pressed
    options = Options(settings, speech, save=store.save, base_rate=lambda: speech.base_rate,
                      voice_catalog=VoiceCatalog(), voice_guard=guard)

    # the season, the saved game, footplay.txt and the log; every file is checked now, so a damaged one is told with the
    # start-up notices (S7.5, D-024 item 5, G-F5, playbook 7.10)
    with debuglog.phase("program files"):
        files = FileProgramStore(paths.user_data_dir(), paths.customize_dir(), first=first_start)
    # the player's names and banter (teams.txt, divisions.txt, surnames.txt, banter.txt in the same folder, S7.7): read and
    # healed once now, so their notices come with the start-up notices too
    # nfl4 only (rule 0.13, SX.2): the Rules setting chooses Classic or the N. F. L. rules; their files (remarks.txt) are read
    # only with the N. F. L. rules
    rules = rules_from_settings(settings.game)
    try:
        with debuglog.phase("customization files"):
            custom = Customization(paths.customize_dir(), extras=is_nfl(rules))
    except Exception:                       # cannot happen (it never raises); the game plays with the original names
        log.exception("the customization files could not be loaded")
        custom = None
    debuglog.event("app", "rules", rules=settings.game.rules, extras=is_nfl(rules), season_kind=settings.game.nx_season_kind)
    # the startup report is made on its own thread now (the game does not wait for it); the log's writer puts it at the top
    sysreport.build_in_background(args=args, cwd_before=cwd_before, cwd_after=cwd_after, welcome=texts.TITLE_SPOKEN.strip(),
                                  last_errors=last_errors, speech=speech, speech_settings=settings.speech, started=started,
                                  audio=audio, store=store, custom=custom, settings=settings)

    def franchise_factory(classic_store):
        from .extras.franchise import data as franchise_data
        from .extras.franchise.files import DiskFiles
        from .extras.franchise.store import FranchiseStore
        return FranchiseStore(DiskFiles(os.path.join(paths.user_data_dir(), franchise_data.FOLDER)), classic_store)

    def game_thread():
        try:
            sources = tuple(source for source in (store, audio, files, custom) if source is not None)
            game = Game(speech, keys, notice_sources=sources, sounds=sounds, rnd=rnd, options=options,
                        program_store=files, open_folder=paths.open_folder, settings_dir=store.folder,
                        customization=custom, rules=rules)
            game.season_store = game.setup_store = files        # the files the season engine and the prompts write
            game.log_sink = files.log_line                      # footballlog.txt (Print #3, G-S10)
            game.franchise_factory = franchise_factory          # the Franchise's folder (nfl4 only, SX.8a): opened only with the N. F. L. rules
            game.run()
            debuglog.set_exit_reason("the player left the game")
        except GameQuit:
            debuglog.set_exit_reason("window closed")
        except Exception:
            debuglog.set_exit_reason("error in the game thread")
            log.exception("unexpected error in the game thread")
        finally:
            log.debug("game thread ended")
            files.close()
            frame.close()                   # thread-safe: posts WM_CLOSE to the window

    thread = threading.Thread(target=game_thread, name="game", daemon=True)
    thread.start()
    frame.run()
    log.debug("main loop ended")
    keys.close()
    thread.join(2.0)
    if thread.is_alive():
        log.warning("the game thread did not end within 2 s; the process ends anyway")
    audio.close()
    speech.close()
    guard.clear()                           # closed normally: whatever voice was in use did not crash
    for timer in deadlines:
        timer.cancel()                      # main() ends: the entry point ends the process (data/lifecycle.finish)
    log.info("NFL Football 4 closed")
    debuglog.flush()                        # the entry point's finish() writes the last line, `closed`
    return 0


def start_audio(settings) -> Audio:
    """The mixer (or silent running when no device opens, G-A4) and every sound resolved once, so a sound file that
    cannot be used is reported among the start-up notices (G-A6). Never raises."""
    audio = Audio(SoundLibrary(), settings.audio)
    try:
        problems = audio.library.check_all()
        if problems:
            log.warning("sound problems at start: %s", "; ".join(problems))
    except Exception:
        log.exception("checking the sound files failed; each sound is tried again when it plays")
    return audio


def _voice_name(speech, role: str) -> str:
    details = speech.role_details(role)
    return details.name if details is not None else ""


def note_voices(store, speech, settings, skipped: dict) -> None:
    """One notice per voice that crashed the program last time, and one if a saved voice is not installed now."""
    for saved, roles in skipped.items():
        store.note_voice_crashed(voice_label(saved), _voice_name(speech, roles[0]))   # the first voice, used instead
    for role in ALL_ROLES:
        saved = settings.speech.voices.get(role)
        if not saved or saved in skipped:
            continue
        details = speech.role_details(role)
        if details is not None:
            store.note_voice_fallback(saved, details.voice_id)


def no_voices(speech, frame, error: str) -> None:
    """GAP_REGISTER G-F9: the sentence through a screen reader when one runs, the original's kind of box, the end."""
    debuglog.set_exit_reason("no SAPI 5 voice")
    log.error("no SAPI 5 voice: %s", error)
    speech.screen_reader_message(texts.NO_VOICES_SPOKEN)
    frame.message_box(texts.NO_VOICES + "\n" + texts.NO_VOICES_CONTACT, texts.MESSAGE_TITLE)
    frame.destroy()
