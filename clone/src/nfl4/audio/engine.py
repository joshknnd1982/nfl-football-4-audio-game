"""The audio layer the game logic uses: the original's DirectSound calls on seven slots. This is inspired by Jim Kitchen.

WAV_EVENT_MAP 1, 3 and 4: every original buffer is a slot (output.py); on a slot the original did SetCurrentPosition(0),
SetVolume (hundredths of a decibel, wavol already added by the caller), SetPan, SetFrequency, Play (once or looping),
GetStatus, GetVolume and Stop. Here `play` does the first five at once, `busy` is GetStatus = playing, `volume` and
`set_volume` are GetVolume and SetVolume (the crowd ramps change a playing loop's level), `stop` is Stop. The +1 Hz the
original adds to most sounds is not reproduced (D-023): freq None plays a file at its own rate.

The logic never sees pygame or file names; it names a sound by its ID (audio/ids.py). Nothing here raises into the
game: a failure to play is logged and the slot stays silent. `slot_log` (a list) receives one SlotEvent per call that
changes a slot, with the time, for the tests' slot log (GAP_REGISTER G-A1).
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from ..data import debuglog
from ..data.settings import AudioSettings
from .ids import BEEP_EXIT
from .library import Pick, SoundLibrary
from .output import CHANNELS, EXTRA_SLOT, SLOT_COUNT, SLOT_NAMES, Output, OutputError, PygameOutput, TimedOutput
from .render import MIX_RATE, frames_of, level_gain, render_stereo, usable_frequency
from .tonegen import generated

log = logging.getLogger("nfl4.audio")

_RENDER_BUDGET = 64 * 1024 * 1024    # bytes of rendered sound kept for the next start of the same sound

# GAP_REGISTER G-A4 (draft wording, section 8; CLONE text): said once when no sound device could be opened.
NO_SOUND_NOTICE = " The sound system could not be started. The game goes on without sounds. "
# S8.3 (CLONE text, GAP_REGISTER section 8): said once, at the next notices, when the device that worked stops working in the middle of a run
DEVICE_LOST_NOTICE = " The sound system stopped working. The game goes on without sounds. "
# plays in a row that the mixer refused before the device is called lost (one refusal can be a single bad sound)
DEVICE_LOST_AFTER = 3


class Beeper(Protocol):
    def beep(self) -> bool: ...


class SystemBeeper:
    """The Windows default sound, MessageBeep(MB_OK = 0): what VB's Beep did (SOUND_DESIGN 2, fixesforgames B-A11)."""

    def beep(self) -> bool:
        try:
            import winsound
            winsound.MessageBeep(0)
            return True
        except Exception:
            log.exception("system beep not available")
            return False


@dataclass(frozen=True)
class SlotEvent:
    time: float
    slot: int
    action: str             # "play", "volume" or "stop"
    sound_id: str = ""
    volume: int = 0         # hundredths of a decibel
    freq: int = 0           # Hz the sound plays at
    pan: int = 0
    loop: bool = False
    source: str = ""        # the Pick's source: "player", "original", "generated", "off", "none"


class Audio:
    SLOTS = SLOT_COUNT

    def __init__(self, library: SoundLibrary, settings: AudioSettings, output: Output | None = None,
                 beeper: Beeper | None = None, buffer: int = 256, clock: Callable[[], float] = time.monotonic,
                 slot_log: list | None = None):
        self.library = library
        self.settings = settings
        self.beeper = beeper if beeper is not None else SystemBeeper()
        self.clock = clock
        self.slot_log = slot_log
        self.error: str | None = None
        self._device_notice_given = False
        if output is None:
            try:
                output = PygameOutput(buffer)
            except OutputError as exc:
                self.error = str(exc)
                log.error("%s; running without sound", exc)
                output = TimedOutput(clock, keep=False)
            except Exception as exc:
                self.error = f"{type(exc).__name__}: {exc}"
                log.exception("sound system failed to start; running without sound")
                output = TimedOutput(clock, keep=False)
        self.output = output
        self._device_lost = False
        self._refused_plays = 0
        self._volumes = [0] * CHANNELS          # GetVolume: DirectSound's default level is 0 (full)
        self._renders: dict[tuple, tuple[Pick, bytes]] = {}
        self._render_bytes = 0
        self._warned_frequency: set[int] = set()

    @property
    def ok(self) -> bool:
        """False when no sound device could be opened (the game then runs silently, G-A4)."""
        return self.error is None

    def take_notices(self) -> list[str]:
        """Sentences worth speaking once: no sound device (G-A4), then the library's (sounds.txt, G-A6)."""
        notices = []
        if self.error is not None and not self._device_notice_given:
            self._device_notice_given = True
            notices.append(DEVICE_LOST_NOTICE if self._device_lost else NO_SOUND_NOTICE)
        return notices + self.library.take_notices()

    def refresh(self) -> None:
        """Sounds menu reload: rescan the sound files."""
        self.library.refresh()
        self._renders.clear()
        self._render_bytes = 0

    def rate(self, sound_id: str) -> int | None:
        """The sound's own sample rate (GetFrequency of a freshly loaded buffer); None when nothing is playable."""
        return self.library.pick(sound_id).rate

    # ----- the original's DirectSound calls -----

    def play(self, slot: int, sound_id: str, volume: int = 0, pan: int = 0, freq: int | None = None,
             loop: bool = False) -> float:
        """Stop the slot, then start the sound at volume (hundredths of a dB, 0 = full), pan and freq (Hz), once or
        looping. freq None, or outside DirectSound's 100 to 200,000 Hz, plays the file at its own rate.
        Returns the seconds one pass of the sound takes (0 when nothing plays)."""
        return self._start(slot, self.library.pick(sound_id), volume, pan, freq, loop, "id")

    def play_member(self, slot: int, member, volume: int = 0, pan: int = 0, freq: int | None = None) -> float:
        """A numbered pool's member (audio/pools.py): an original by its ID, exactly the call the original's draw made, an
        added file of the player's by its place, once. Returns the seconds one pass takes (0 when nothing plays)."""
        if member.sound_id is not None:
            return self.play(slot, member.sound_id, volume, pan, freq)
        return self._start(slot, self.library.pick_file(member.path), volume, pan, freq, False,
                           "pool member %s added by the player" % member.number)

    def member_rate(self, member) -> int | None:
        """The member's own sample rate (GetFrequency of its buffer); None when nothing is playable."""
        return self.library.pick_for(member).rate

    def play_file(self, slot: int, path: str, volume: int = 0, pan: int = 0, loop: bool = False) -> float:
        """The same for a sound file of the player's named by its place (the banter's [sound file.wav], D-048): once (or looping: the music
        slot's file at the start, NX-M1), at the file's own rate. A file that cannot be used plays nothing (the library logs it and speaks its one
        notice)."""
        return self._start(slot, self.library.pick_file(path), volume, pan, None, loop, "file named in a line")

    def _start(self, slot: int, pick: Pick, volume: int, pan: int, freq: int | None, loop: bool, via: str = "id") -> float:
        self.stop(slot, log_it=False)
        sound = pick.sound
        self._volumes[slot] = int(volume)
        if sound is None:
            self._log(slot, "play", pick, volume, 0, pan, loop)
            debuglog.event("sound", "play", slot=SLOT_NAMES[slot], id=pick.sound_id, chain=pick.source, via=via, file=None,
                           result="silence: nothing playable", volume=int(volume), pan=int(pan), loop=loop)
            return 0.0
        if freq is None or not usable_frequency(freq):
            if freq is not None and freq not in self._warned_frequency:
                self._warned_frequency.add(freq)
                log.warning("frequency %s Hz is outside DirectSound's range; playing %s at its own rate",
                            freq, pick.sound_id)
            freq = sound.rate
        began = time.perf_counter()
        try:
            pcm = self._render(pick, freq, pan)
        except Exception:
            log.exception("could not prepare %s", pick.sound_id)
            return 0.0
        self._log(slot, "play", pick, volume, freq, pan, loop)
        try:
            self.output.play(slot, pcm, level_gain(volume), loop)
            self._refused_plays = 0
        except Exception as exc:
            if not self._mixer_refused(pick.sound_id, exc):
                return 0.0
            try:
                self.output.play(slot, pcm, level_gain(volume), loop)       # the silent output keeps the game's waits as long as the sound
            except Exception:
                log.exception("the silent output could not play %s", pick.sound_id)
                return 0.0
        seconds = frames_of(pcm) / MIX_RATE
        debuglog.event("sound", "play", slot=SLOT_NAMES[slot], id=pick.sound_id, chain=pick.source, via=via,
                       file=os.path.basename(pick.path) if pick.path else None, volume=int(volume), pan=int(pan), freq=int(freq),
                       loop=loop or None, seconds=round(seconds, 3), result="ok", prepare_ms=round((time.perf_counter() - began) * 1000, 2))
        return seconds

    def _mixer_refused(self, sound_id: str, exc: Exception) -> bool:
        """The mixer raised while playing. One refusal may be one bad sound: logged with its traceback the first time, a warning after that.
        After DEVICE_LOST_AFTER in a row the device is called lost (unplugged, taken by another program): the silent output takes over, as at
        start-up with no device, so the waits that the game makes for its sounds keep their length, one notice is queued and the log says
        so (S8.3, G-A4). True when the play should be tried again on the silent output."""
        self._refused_plays += 1
        if self._refused_plays == 1:
            log.exception("the mixer could not play %s", sound_id)
        else:
            log.warning("the mixer could not play %s (%d in a row): %s", sound_id, self._refused_plays, exc)
        if self._refused_plays < DEVICE_LOST_AFTER or self._device_lost:
            return False
        self._device_lost = True
        self.error = f"the sound device stopped working: {type(exc).__name__}: {exc}"
        log.error("%s; running without sound from now on", self.error)
        debuglog.event("sound", "device lost", reason=self.error, result="silent output from now on")
        try:
            self.output.close()
        except Exception as close_exc:
            log.debug("the lost mixer did not close cleanly: %s", close_exc)
        self.output = TimedOutput(self.clock, keep=False)
        return True

    def set_volume(self, slot: int, volume: int) -> None:
        """SetVolume on the slot's buffer, playing or not (the next play sets its own)."""
        self._volumes[slot] = int(volume)
        debuglog.trace("sound", "volume", slot=SLOT_NAMES[slot], volume=int(volume))     # 43 percent of all lines otherwise
        if self.slot_log is not None:
            self.slot_log.append(SlotEvent(self.clock(), slot, "volume", volume=int(volume)))
        try:
            self.output.set_gain(slot, level_gain(volume))
        except Exception:
            log.exception("the mixer could not change the level of slot %d", slot)

    def volume(self, slot: int) -> int:
        """GetVolume: the level last set on the slot, in hundredths of a decibel."""
        return self._volumes[slot]

    def busy(self, slot: int) -> bool:
        """The original's GetStatus = playing. A failing mixer counts as stopped."""
        try:
            return bool(self.output.busy(slot))
        except Exception:
            log.exception("the mixer could not report slot %d", slot)
            return False

    def stop(self, slot: int, log_it: bool = True) -> None:
        if log_it:
            debuglog.trace("sound", "stop", slot=SLOT_NAMES[slot])
        if log_it and self.slot_log is not None:
            self.slot_log.append(SlotEvent(self.clock(), slot, "stop"))
        try:
            self.output.stop(slot)
        except Exception:
            log.exception("the mixer could not stop slot %d", slot)

    def stop_all(self) -> None:
        """Every slot and the extra channel (the exit, SOUND_DESIGN 4 step 1)."""
        for slot in range(CHANNELS):
            self.stop(slot)

    # ----- the sounds menu and the exit (not original slots) -----

    def preview(self, sound_id: str) -> str:
        """Sounds menu: play one sound once at its own rate, full level, centered, on the extra channel.

        Returns what was played: the Pick's source ("player", "original", "generated", "off", "none")."""
        if sound_id == BEEP_EXIT:
            self.beep_exit()
            return self.library.pick(sound_id).source
        self.play(EXTRA_SLOT, sound_id)
        return self.library.pick(sound_id).source

    def stop_preview(self) -> None:
        self.stop(EXTRA_SLOT)

    def beep_exit(self) -> bool:
        """One exit beep (SOUND_DESIGN 4 step 3; the flow plays two, 0.1 s apart).

        Chain: the player's beep_exit file, then the Windows default sound, then the generated blip."""
        pick = self.library.pick(BEEP_EXIT)
        if pick.source in ("player", "off"):
            self.play(EXTRA_SLOT, BEEP_EXIT)
            return True
        if self.beeper.beep():
            debuglog.event("sound", "play", id=BEEP_EXIT, chain="system", via="Windows default sound", result="ok")
            if self.slot_log is not None:
                self.slot_log.append(SlotEvent(self.clock(), EXTRA_SLOT, "play", BEEP_EXIT, source="system"))
            return True
        blip = generated(BEEP_EXIT)
        if blip is None:
            return False
        self._play_pick(EXTRA_SLOT, Pick(BEEP_EXIT, blip, "generated"))
        return True

    def _play_pick(self, slot: int, pick: Pick) -> None:
        self.stop(slot, log_it=False)
        pcm = render_stereo(pick.sound, pick.sound.rate, 0, pick.volume)
        self._volumes[slot] = 0
        self._log(slot, "play", pick, 0, pick.sound.rate, 0, False)
        debuglog.event("sound", "play", slot=SLOT_NAMES[slot], id=pick.sound_id, chain=pick.source, via="generated", result="ok")
        try:
            self.output.play(slot, pcm, 1.0, False)
        except Exception:
            log.exception("the mixer could not play %s", pick.sound_id)

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

    # ----- inside -----

    def _render(self, pick: Pick, freq: int, pan: int) -> bytes:
        """The sound at freq and pan with the player's trim, 16-bit stereo; kept for the next start of the same sound
        (the crowd beds, the tackles and the hike come back often)."""
        key = (id(pick), int(freq), int(pan))
        cached = self._renders.get(key)
        if cached is not None and cached[0] is pick:
            return cached[1]
        pcm = render_stereo(pick.sound, freq, pan, pick.volume)
        if self._render_bytes + len(pcm) > _RENDER_BUDGET:
            self._renders.clear()
            self._render_bytes = 0
        self._renders[key] = (pick, pcm)
        self._render_bytes += len(pcm)
        return pcm

    def _log(self, slot, action, pick: Pick, volume, freq, pan, loop) -> None:
        if self.slot_log is not None:
            self.slot_log.append(SlotEvent(self.clock(), slot, action, pick.sound_id, int(volume), int(freq),
                                           int(pan), bool(loop), pick.source))


def wait_until(predicate: Callable[[], bool], timeout: float, step: float = 0.001) -> bool:
    """Small helper for tests and tools: poll until predicate is true or timeout passes."""
    end = time.perf_counter() + timeout
    while time.perf_counter() < end:
        if predicate():
            return True
        time.sleep(step)
    return predicate()
