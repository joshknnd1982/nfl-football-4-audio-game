"""The audio layer the game logic uses. This is inspired by Jim Kitchen's Brain.

Mirrors what the original did with DirectSound (GAME_SPEC 5.4): start a sound in a slot at a
chosen frequency and pan, ask whether a slot is still playing, stop a slot. The logic never sees
numpy, pygame or file names; it asks the library for a Pick and hands it to `play`.

Slots are 0..8 here (the spec's slots 1..9). Nothing in this module raises into the game: a
failure to play is logged and the slot stays silent, as the original's Resume Next did.
"""
from __future__ import annotations

import logging
import time
from typing import Callable, Protocol

from ..data.settings import AudioSettings
from .library import Pick, SoundLibrary
from .output import BEEP_SLOT, SLOT_COUNT, Output, OutputError, PygameOutput, TimedOutput
from .render import MIX_RATE, frames_of, render_stereo, usable_frequency
from .tonegen import generated

log = logging.getLogger("nfl4.audio")


class Beeper(Protocol):
    def beep(self) -> bool: ...


class SystemBeeper:
    """The Windows default sound, MessageBeep(MB_OK = 0): what VB's Beep did (SOUND_DESIGN.md)."""

    def beep(self) -> bool:
        try:
            import winsound
            winsound.MessageBeep(0)
            return True
        except Exception:
            log.exception("system beep not available")
            return False


class Audio:
    SLOTS = SLOT_COUNT

    def __init__(self, library: SoundLibrary, settings: AudioSettings, output: Output | None = None,
                 beeper: Beeper | None = None, buffer: int = 256):
        self.library = library
        self.settings = settings
        self.beeper = beeper if beeper is not None else SystemBeeper()
        self.error: str | None = None
        if output is None:
            try:
                output = PygameOutput(buffer)
            except OutputError as exc:
                self.error = str(exc)
                log.error("%s; running without sound", exc)
                output = TimedOutput()
            except Exception as exc:
                self.error = f"{type(exc).__name__}: {exc}"
                log.exception("sound system failed to start; running without sound")
                output = TimedOutput()
        self.output = output
        self._warned_frequency: set[int] = set()

    @property
    def ok(self) -> bool:
        """False when no sound device could be opened (the game then runs silently)."""
        return self.error is None

    def refresh(self) -> None:
        """Playback start / Sounds menu reload: rescan the sound files (DECISIONS P5)."""
        self.library.refresh()

    # ----- the original's DirectSound calls -----

    def play(self, slot: int, pick: Pick, freq: int | None = None, pan: int = 0) -> float:
        """Stop the slot, then start the pick at freq (Hz) and pan (hundredths of a dB).

        freq None or outside DirectSound's 100..200000 Hz range plays at the file's own rate
        (the original's failed SetFrequency changed nothing, GAME_SPEC 5.3). Returns the seconds the
        sound takes (0 when nothing plays)."""
        log.debug("play slot %d %s freq %s pan %s", slot + 1, pick.sound_id, freq, pan)   # NFL4_DEBUG=1: timing tools read this
        self.stop(slot)
        sound = pick.sound
        if sound is None:
            return 0.0
        if freq is None or not usable_frequency(freq):
            if freq is not None and freq not in self._warned_frequency:
                self._warned_frequency.add(freq)
                log.warning("frequency %s Hz is outside DirectSound's range; playing %s at its own rate",
                            freq, pick.sound_id)
            freq = sound.rate
        gain = (self.settings.effects_volume / 100.0) * pick.volume
        try:
            pcm = render_stereo(sound, freq, pan, gain)
        except Exception:
            log.exception("could not prepare %s", pick.sound_id)
            return 0.0
        try:
            self.output.play(slot, pcm)
        except Exception:
            log.exception("the mixer could not play %s", pick.sound_id)
            return 0.0
        return frames_of(pcm) / MIX_RATE

    def busy(self, slot: int) -> bool:
        """The original's GetStatus = playing. A failing mixer counts as stopped (the slot starts its next sound)."""
        try:
            return bool(self.output.busy(slot))
        except Exception:
            log.exception("the mixer could not report slot %d", slot)
            return False

    def stop(self, slot: int) -> None:
        try:
            self.output.stop(slot)
        except Exception:
            log.exception("the mixer could not stop slot %d", slot)

    def stop_all(self) -> None:
        """Main menu: stop the nine slots (GAME_SPEC 3.2 step 1)."""
        for slot in range(SLOT_COUNT):
            self.stop(slot)

    def preview(self, sound_id: str) -> str:
        """Sounds menu: play one sound once at its own rate, centered (the tenth channel).

        Returns what was played: the Pick's source ("player", "original", "generated", "off", "none")."""
        if sound_id == "beep_exit":
            self.beep_exit()
            return self.library.pick(sound_id).source
        pick = self.library.pick(sound_id)
        self.play(BEEP_SLOT, pick)
        return pick.source

    def stop_preview(self) -> None:
        self.stop(BEEP_SLOT)

    # ----- exit beep -----

    def beep_exit(self) -> bool:
        """One exit beep (GAME_SPEC 3.5; the logic plays two, 0.1 s apart).

        Chain: the player's beep_exit file, then the Windows default sound, then the generated blip."""
        pick = self.library.pick("beep_exit")
        if pick.source in ("player", "off"):
            self.play(BEEP_SLOT, pick)
            return True
        if self.beeper.beep():
            return True
        blip = generated("beep_exit")
        if blip is None:
            return False
        self.play(BEEP_SLOT, Pick("beep_exit", blip, None, "generated"))
        return True

    def close(self) -> None:
        try:
            self.output.stop_all()
        except Exception:
            log.exception("the mixer could not stop at close")
        finally:
            try:
                self.output.close()
            except Exception:
                log.exception("the mixer did not close cleanly")


def wait_until(predicate: Callable[[], bool], timeout: float, step: float = 0.001) -> bool:
    """Small helper for tests and tools: poll until predicate is true or timeout passes."""
    end = time.perf_counter() + timeout
    while time.perf_counter() < end:
        if predicate():
            return True
        time.sleep(step)
    return predicate()
