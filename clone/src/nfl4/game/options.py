"""The values the original's hot keys change, and where they are saved. This is inspired by Jim Kitchen.

The original kept the rate counter vr and the five voice numbers in footbal0.dat (written by Ctrl and F12) and the five
voice volumes, the sound volume wavol and the comments flag comtog in football.vol (written by F8 and F11); GAME_SPEC 12.
The clone keeps them in its settings.txt (data/settingsfile.py, GAP_REGISTER G-F8): `Options` is the one object the
menus of game/hotkeys.py read and change, and `save()` writes the file where the original wrote one of its two files.

* vr (GAME_SPEC 4.8, D-022 item 3): the saved speech_rate, -10 to 10; "original" (None) is the first voice's own rate,
  the value the original keeps in vr at start (GAME_SPEC 3 step 3). With NVDA or JAWS it only changes the pauses and the
  spoken number (G-S4): the manager passes the rate to SAPI 5 alone.
* comtog (4.5): 1 = the announcer's comments are OFF (settings comments = off), 0 = on.
* the five voice volumes (4.6): 0 to 100, 95 by default; applied to the speaker at once.
* wavol (4.6 part 2): 0 down to -5000 hundredths of a decibel, the AudioSettings the sound procedures read.
* the five voices (4.7, G-S8): voice ids, None = the first voice of SAPI's list (the original's voice 0).
"""
from __future__ import annotations

import logging
from typing import Callable

from ..data.settings import SOUND_LEVEL_MAX, SOUND_LEVEL_MIN, Settings

log = logging.getLogger("nfl4.game")

RATE_MIN, RATE_MAX = -10, 10          # D-022 item 3: the SAPI range; the original's counter had no limit
VOLUME_MIN, VOLUME_MAX = 0, 100


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


class Options:
    def __init__(self, settings: Settings | None, speech, save: Callable[[], object] | None = None,
                 base_rate: Callable[[], int] | None = None, voice_catalog=None, voice_guard=None):
        self.settings = settings if settings is not None else Settings.defaults()
        self.speech = speech
        self._save = save
        # the first voice's own rate, the original's start value of vr (None: 0, as the tests' fakes have no rate)
        self._base_rate = base_rate if base_rate is not None else (lambda: 0)
        self.voice_catalog = voice_catalog          # speech.voices.VoiceCatalog for F12 (None: no voice list)
        self.voice_guard = voice_guard              # data.voiceguard.VoiceGuard (None in the tests)

    def save(self) -> None:
        """Where the original wrote footbal0.dat or football.vol: settings.txt is written (a failure is logged by the
        store and never stops the game)."""
        if self._save is not None:
            try:
                self._save()
            except Exception as exc:
                log.warning("saving the settings failed: %s", exc)

    # ----- vr: the speech rate counter (Ctrl) -----

    @property
    def vr(self) -> int:
        rate = self.settings.speech.rate
        if rate is not None:
            return clamp(rate, RATE_MIN, RATE_MAX)
        try:
            return clamp(self._base_rate(), RATE_MIN, RATE_MAX)
        except Exception as exc:
            log.warning("the voice's own rate could not be read: %s", exc)
            return 0

    def set_vr(self, value: int) -> int:
        """`vr = value` and `Voice.Rate = vr` (kept in -10 to 10); returns the value kept."""
        value = clamp(value, RATE_MIN, RATE_MAX)
        self.settings.speech.rate = value
        self.speech.set_rate(value)
        return value

    # ----- comtog: the comments toggle (F8) -----

    @property
    def comtog(self) -> int:
        return 0 if self.settings.game.comments else 1

    def set_comtog(self, value: int) -> None:
        self.settings.game.comments = int(value) == 0

    # ----- the voice volumes (F11 part 1) -----

    def volume(self, role: str) -> int:
        return int(self.settings.speech.volumes.get(role, 95))

    def set_volume(self, role: str, value: int) -> int:
        value = clamp(value, VOLUME_MIN, VOLUME_MAX)
        self.settings.speech.volumes[role] = value
        self.speech.set_role_volume(role, value)
        return value

    # ----- wavol: the sound volume (F11 part 2) -----

    @property
    def wavol(self) -> int:
        return int(self.settings.audio.sound_level)

    def set_wavol(self, value: int) -> int:
        value = clamp(value, SOUND_LEVEL_MIN, SOUND_LEVEL_MAX)
        self.settings.audio.sound_level = value
        return value

    # ----- the voices (F12) -----

    def voice(self, role: str) -> str | None:
        return self.settings.speech.voices.get(role)

    def set_voice(self, role: str, voice_id: str | None) -> None:
        self.settings.speech.voices[role] = voice_id
        if self.voice_guard is not None and voice_id:
            self.voice_guard.forget(voice_id)      # choosing a set-aside voice again is asking for another try
        self.speech.set_role_voice(role, voice_id)
