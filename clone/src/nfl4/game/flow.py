"""The program flow of NFL Football 4. This is inspired by Jim Kitchen.

GAME_SPEC 3. The original did everything inside Form_Load as one long routine with jumps; here each part will be a
method, in the same order and with the same waits. There is no window, sound card or screen reader code in this
module: it talks to a SpeechManager and a KeyInput, so the tests run it with fakes on a virtual clock
(tests/gamerig.py). App code (app.py) wires the real ones.

P7 S7.1 is the SKELETON: the spoken title once per launch (rule 0.5.1, GAP_REGISTER G-F1), the notices the settings
file and the voice crash guard collected (said once, playbook 7.10), then a key wait that ends the program on Escape.
S7.4 replaces run() with the start-up of GAME_SPEC 3 (intro music, first-run welcome, season set-up, the week loop, the
main menu, the exit sequence with its beeps and sentence); Escape does not end the original from the main menu.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from ..speech.roles import ANNOUNCER
from . import texts
from .keys import KEY_ESCAPE, KeyInput

log = logging.getLogger("nfl4.game")


class Game:
    def __init__(self, speech, keys: KeyInput, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, notice_sources=()):
        self.speech = speech
        self.keys = keys
        self.clock = clock
        self.sleep = sleep
        self.notice_sources = tuple(notice_sources)   # objects with take_notices() (the settings file)

    # ----- the original's speakers: GAME_SPEC 9.1 (S7.3 and S7.4 add say3, say4, say5, say6 and the log) -----

    def say(self, text: str, role: str = ANNOUNCER) -> None:
        """Speak and wait until everything queued is spoken (the original's say: flags 0, a barrier)."""
        if text:
            self.speech.say(text, self.keys.quit, role=role)

    def say2(self, text: str, role: str = ANNOUNCER) -> None:
        """Queue and go on (the original's say2: flags 1)."""
        if text:
            self.speech.say_async(text, role=role)

    def stopspeech(self) -> None:
        self.speech.stop()

    # ----- the flow -----

    def speak_notices(self) -> None:
        """Short sentences about damaged files and voices, each said once (playbook 7.10)."""
        for source in self.notice_sources:
            try:
                notices = source.take_notices()
            except Exception as exc:              # a notice source must never stop the game
                log.warning("notices of %s failed: %s", type(source).__name__, exc)
                continue
            for notice in notices:
                self.say(notice)

    def run(self) -> None:
        self.say(texts.TITLE_SPOKEN)              # once per launch (rule 0.5.1, G-F1)
        self.speak_notices()
        while True:                               # S7.1 skeleton: S7.4 builds the week loop and the main menu here
            self.keys.getkey(self.speech)
            if self.keys.code_text == str(KEY_ESCAPE):
                log.info("skeleton: Escape ends the program")
                return
