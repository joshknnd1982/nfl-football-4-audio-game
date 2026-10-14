"""SAPI 5 speech backend. This is inspired by Jim Kitchen's Brain.

Brain's own voice (GAME_SPEC 3.1, 9): the first voice in SAPI's list, volume 90, the voice's
own rate kept as the base rate. One dedicated thread owns the SpVoice COM object in a
single-threaded apartment, as the original VB6 form did; other threads send it commands.
That keeps odd third-party engines happy and lets any thread speak or stop speech.

The original's say (Speak flags 0) is done here as an async Speak plus a wait for the end of
speech: SAPI parses the same text the same way (flags 0 and 1 differ only in waiting), and the
wait can be broken when the window closes.

Rendered mode (DECISIONS 2026-10-13, speech latency). With SAPI's own audio output, stopping
speech (purge) blocked the speech thread for up to 700 ms on some voices, so a key pressed
while a voice was talking waited for the old speech before the new speech began. In rendered
mode SAPI makes each text into memory (10 to 60 ms for a menu item, about 30 times faster than
real time), and the thread plays it through waveout.WaveOut, which stops at once. Long texts are
made and played sentence by sentence so they start quickly. If no audio device opens, the
backend falls back to the direct mode above.

Two things were tried and rejected (DECISIONS 2026-10-13, speech skipping words): playing the
memory stream while the engine is still writing it (the stream's contents change after they are
read, so words were skipped), and rendering with engines that make speech no faster than they
speak it (Orpheus, Prose 2000, neural voices: the player would wait the length of the text).
Instead each voice gets a speed probe when it is chosen: if it cannot make a short text within
PROBE_LIMIT_SECONDS, that voice speaks in the direct mode above, as the original did.
"""
from __future__ import annotations

import logging
import queue
import re
import threading
import time
import unicodedata
from dataclasses import dataclass
from xml.sax.saxutils import escape

from .backend import SpeechBackend
from .waveout import trim_silence

log = logging.getLogger(__name__)

# SpeechVoiceSpeakFlags (SAPI 5 documentation)
SVSF_ASYNC = 1
SVSF_PURGE_BEFORE_SPEAK = 2
SVSF_IS_XML = 8

RATE_MIN, RATE_MAX = -10, 10
VOLUME_MIN, VOLUME_MAX = 0, 100
PITCH_MIN, PITCH_MAX = -10, 10
ORIGINAL_VOLUME = 90  # GAME_SPEC 3.1 step 5
WAIT_SLICE_MS = 5     # how long the speech thread waits inside SAPI per pass while speaking
SAFT_44KHZ_16BIT_MONO = 34  # SpeechAudioFormatType; matches WaveOut's fixed format
RENDER_RATE = 44100
CHUNK_FROM_CHARS = 60  # longer texts are made and played sentence by sentence
CHUNK_MIN_CHARS = 25   # a sentence shorter than this is joined to the next one
PROBE_TEXT = "Select. no panning"
PROBE_LIMIT_SECONDS = 0.25  # a voice slower than this for the probe text is spoken directly, not rendered
STALL_SECONDS = 8.0   # no progress this long while speaking = deadlock with another program


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def apply_pitch(text: str, pitch: int) -> tuple[str, int]:
    """Return (text, extra flags). Pitch 0 sends the text untouched, exactly as the original did."""
    if not pitch:
        return text, 0
    return f'<pitch absmiddle="{pitch}">{escape(text)}</pitch>', SVSF_IS_XML


def split_chunks(text: str) -> list[str]:
    """Pieces of text to make and play one after the other. Short texts stay whole (rendered mode)."""
    if len(text) <= CHUNK_FROM_CHARS:
        return [text]
    pieces = [p for p in re.split(r"(?<=[.!?:;])\s+|\n+", text) if p.strip()]
    chunks: list[str] = []
    carry = ""
    for piece in pieces:
        piece = (carry + " " + piece).strip() if carry else piece
        if len(piece) < CHUNK_MIN_CHARS:
            carry = piece
        else:
            chunks.append(piece)
            carry = ""
    if carry:
        if chunks:
            chunks[-1] = chunks[-1] + " " + carry
        else:
            chunks.append(carry)
    return chunks or [text]


_DIGIT_WORDS = "zero one two three four five six seven eight nine".split()


_FOLD = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                       "ß": "ss", "æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O",
                       "đ": "d", "ł": "l", "Ł": "L"})


def ascii_fold(text: str) -> str:
    """Letters with marks become plain letters (Francais for Français), curly quotes straight; the rest goes."""
    decomposed = unicodedata.normalize("NFKD", text.translate(_FOLD))
    kept = "".join(c if ord(c) < 128 else " " for c in decomposed if not unicodedata.combining(c))
    return kept


def speech_variants(text: str) -> list[str]:
    """Other ways to write text when a voice made no sound for it (rendered mode only knows that).

    Found on the owner's PC with BestSpeech Fred, which makes no audio at all (so, silent voice names in
    the voice list) for: two numbers with only a space between them ("Infovox230 1.12 American"; with a
    comma it is fine) and any letter outside plain ASCII ("Français", "d’homme"). Tried in order:
    commas between numbers; then also plain ASCII letters; then also every digit spelled as a word."""
    cleaned = re.sub(r"[\ufffd\x00-\x08\x0b-\x1f]", " ", text)
    commas = re.sub(r"(?<=\d)\s+(?=\d)", ", ", cleaned)
    folded = ascii_fold(commas)
    with_points = re.sub(r"(?<=\d)\.(?=\d)", " point ", folded)
    spelled = re.sub(r"\d", lambda m: " " + _DIGIT_WORDS[int(m.group())] + " ", with_points)
    variants: list[str] = []
    for candidate in (commas, folded, spelled):
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if candidate and candidate != text.strip() and candidate not in variants:
            variants.append(candidate)
    return variants


def default_stream_factory():
    """A new SAPI memory stream set to the format WaveOut plays."""
    import win32com.client
    stream = win32com.client.Dispatch("SAPI.SpMemoryStream")
    fmt = win32com.client.Dispatch("SAPI.SpAudioFormat")
    fmt.Type = SAFT_44KHZ_16BIT_MONO
    stream.Format = fmt
    return stream


def default_player_factory():
    from .waveout import WaveOut
    return WaveOut(RENDER_RATE)


def default_voice_factory():
    """Create a real SAPI SpVoice. Called on the speech thread after COM is initialized."""
    import win32com.client
    return win32com.client.Dispatch("SAPI.SpVoice")


def default_token_factory():
    import win32com.client
    return win32com.client.Dispatch("SAPI.SpObjectToken")


@dataclass
class SapiStart:
    """What the speech thread found at startup."""
    ok: bool
    voice_count: int = 0
    voice_id: str = ""
    voice_name: str = ""
    base_rate: int = 0
    error: str = ""


class SapiBackend(SpeechBackend):
    name = "SAPI 5"

    def __init__(self, voice_id: str | None = None, rate: int | None = None,
                 volume: int = ORIGINAL_VOLUME, pitch: int = 0,
                 voice_factory=default_voice_factory, token_factory=default_token_factory,
                 com_init=True, render: bool = False, player_factory=default_player_factory,
                 stream_factory=default_stream_factory):
        self._want_voice_id = voice_id
        self._want_rate = rate
        self._volume = clamp(volume, VOLUME_MIN, VOLUME_MAX)
        self._pitch = clamp(pitch, PITCH_MIN, PITCH_MAX)
        self._voice_factory = voice_factory
        self._token_factory = token_factory
        self._com_init = com_init
        self._render = render
        self._player_factory = player_factory
        self._stream_factory = stream_factory
        self._player = None
        self._direct = True       # speak through SAPI's own output (no player, or a voice too slow to render)
        self.last_start_at = 0.0  # time.monotonic() when speech was last handed to the output (latency tool)
        self._commands: queue.Queue = queue.Queue()
        self._cv = threading.Condition()
        self._queued = 0        # speak commands sent but not yet given to SAPI
        self._busy = False      # SAPI is speaking or has speech queued
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._errors_logged = 0
        self.on_healthy = None    # called once when speech has ended after this was set (the voice guard, data/voiceguard.py)
        self.started = SapiStart(ok=False, error="not started")

    # ----- life cycle -------------------------------------------------------------
    def start(self, timeout: float = 15.0) -> SapiStart:
        """Start the speech thread and wait until the voice is ready (or found missing)."""
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="sapi5-speech", daemon=True)
            self._thread.start()
        if not self._ready.wait(timeout):
            self.started = SapiStart(ok=False, error=f"SAPI 5 did not start within {timeout} s")
            log.error(self.started.error)
        return self.started

    def close(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            self._commands.put(("quit",))
            self._thread.join(3.0)
        with self._cv:
            self._queued = 0
            self._busy = False
            self._cv.notify_all()

    # ----- SpeechBackend -----------------------------------------------------------
    def is_available(self) -> bool:
        return self.started.ok and self._thread is not None and self._thread.is_alive()

    def speak(self, text: str) -> bool:
        if not self.is_available():
            return False
        with self._cv:
            self._queued += 1
        self._commands.put(("speak", text))
        return True

    def stop(self) -> None:
        if self.is_available():
            self._commands.put(("purge",))

    def wait_until_done(self, abort: threading.Event | None = None) -> None:
        with self._cv:
            while (self._queued or self._busy) and self.is_available():
                if abort is not None and abort.is_set():
                    return
                self._cv.wait(0.02)

    def is_speaking(self) -> bool:
        with self._cv:
            return bool(self._queued or self._busy)

    # ----- settings (clone additions, GAME_SPEC 17) -------------------------------------
    @property
    def voice_name(self) -> str:
        return self.started.voice_name

    @property
    def voice_id(self) -> str:
        return self.started.voice_id

    @property
    def base_rate(self) -> int:
        return self.started.base_rate

    def set_rate(self, rate: int | None) -> None:
        """None restores the voice's own base rate (the original's behavior)."""
        self._commands.put(("rate", None if rate is None else clamp(rate, RATE_MIN, RATE_MAX)))

    def set_volume(self, volume: int) -> None:
        self._commands.put(("volume", clamp(volume, VOLUME_MIN, VOLUME_MAX)))

    def set_pitch(self, pitch: int) -> None:
        self._commands.put(("pitch", clamp(pitch, PITCH_MIN, PITCH_MAX)))

    def set_voice(self, voice_id: str | None) -> None:
        """None selects the first voice in SAPI's list (the original's choice)."""
        self._commands.put(("voice", voice_id))

    # ----- speech thread ------------------------------------------------------------
    def _run(self) -> None:
        pythoncom = None
        if self._com_init:
            import pythoncom
            pythoncom.CoInitialize()
        voice = None
        try:
            voice = self._open_voice()
            if voice is None:
                return
            if self._player is not None:
                self._loop_render(voice, pythoncom)
            else:
                self._loop(voice, pythoncom)
        except Exception as exc:  # the speech thread must never take the game down
            log.exception("SAPI 5 speech thread failed: %s", exc)
            self.started = SapiStart(ok=False, error=f"{type(exc).__name__}: {exc}")
        finally:
            self._ready.set()
            if voice is not None:
                try:
                    voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
                except Exception:
                    pass
            voice = None
            if self._player is not None:
                try:
                    self._player.close()
                except Exception:
                    pass
                self._player = None
            with self._cv:
                self._queued = 0
                self._busy = False
                self._cv.notify_all()
            if pythoncom is not None:
                pythoncom.CoUninitialize()

    def _open_voice(self):
        """GAME_SPEC 3.1 steps 3 and 5. Returns the voice, or None after reporting why not."""
        try:
            voice = self._voice_factory()
            tokens = voice.GetVoices("", "")
            count = tokens.Count
        except Exception as exc:
            self.started = SapiStart(ok=False, error=f"SAPI 5 unavailable: {type(exc).__name__}: {exc}")
            log.error(self.started.error)
            self._ready.set()
            return None
        if count == 0:
            self.started = SapiStart(ok=False, voice_count=0, error="no SAPI 5 voices installed")
            log.error(self.started.error)
            self._ready.set()
            return None
        self._select_voice(voice, tokens, self._want_voice_id)
        base_rate = int(voice.Rate)
        # The original reads the rate and writes it back unchanged; the clone may override it.
        voice.Rate = base_rate if self._want_rate is None else clamp(self._want_rate, RATE_MIN, RATE_MAX)
        voice.Volume = self._volume
        token = voice.Voice
        self.started = SapiStart(ok=True, voice_count=count, voice_id=str(token.Id),
                                 voice_name=str(token.GetDescription()), base_rate=base_rate)
        self._base_rate = base_rate
        if self._render:
            try:
                self._player = self._player_factory()
            except Exception as exc:
                log.warning("rendered speech unavailable (%s: %s); SAPI 5 plays through its own output",
                            type(exc).__name__, exc)
            else:
                self._choose_mode(voice)
        log.info("SAPI 5 ready: %d voices, using %r, base rate %d, volume %d",
                 count, self.started.voice_name, base_rate, self._volume)
        self._ready.set()
        return voice

    def _select_voice(self, voice, tokens, voice_id: str | None) -> None:
        """Pick a saved voice by its token ID, else the first voice (GetVoices Item(0))."""
        if voice_id:
            try:  # cheap direct lookup, 2 ms on the owner's PC
                token = self._token_factory()
                token.SetId(voice_id)
                voice.Voice = token
                return
            except Exception:
                pass
            try:  # tokens from token enumerators may not accept SetId: scan the list
                for i in range(tokens.Count):
                    token = tokens.Item(i)
                    if str(token.Id) == voice_id:
                        voice.Voice = token
                        return
            except Exception as exc:
                log.warning("voice list scan failed: %s", exc)
            log.warning("saved voice %r not found, using the first voice", voice_id)
        voice.Voice = tokens.Item(0)

    @property
    def rendered(self) -> bool:
        """True when the current voice is spoken in rendered mode (tools and tests)."""
        return self._player is not None and not self._direct

    def _choose_mode(self, voice) -> None:
        """Probe the current voice: rendered if it makes a short text fast enough, else direct."""
        fast = self._renders_fast(voice)
        self._direct = not fast
        log.info("speech mode for %r: %s", self.started.voice_name,
                 "rendered" if fast else "direct (this voice makes speech too slowly to render)")

    def _renders_fast(self, voice) -> bool:
        """Make PROBE_TEXT into memory; True if it finishes within PROBE_LIMIT_SECONDS. Leaves the
        voice on its default audio output when it did not, so direct speech works afterwards."""
        try:
            voice.AudioOutputStream = self._stream_factory()
            voice.Speak(PROBE_TEXT, SVSF_ASYNC)
            fast = bool(voice.WaitUntilDone(int(PROBE_LIMIT_SECONDS * 1000)))
        except Exception as exc:
            self._log_error("speed probe", exc)
            fast = False
        if not fast:
            try:
                voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)   # still writing to memory: returns at once
                voice.AudioOutput = voice.GetAudioOutputs().Item(0)
            except Exception as exc:
                self._log_error("back to the default output", exc)
        return fast

    def _loop(self, voice, pythoncom) -> None:
        # Stall watchdog (S7.1 test): when two programs speak through SAPI at once, Windows can
        # deadlock them; one waits for the audio device (state "not started") while the other
        # holds it at word 0, forever. Plain SAPI does the same, so the original would freeze or
        # lose speech too. If the voice's status shows no progress for STALL_SECONDS, this copy
        # stops its own speech and goes on; the test showed the other program then continues.
        state = [None, time.monotonic()]    # progress, progress_time
        while True:
            if self._direct_step(voice, pythoncom, state):
                return

    def _direct_step(self, voice, pythoncom, state) -> bool:
        """One pass of the direct loop. Returns True when told to quit."""
        progress, progress_time = state
        try:
            command = self._commands.get_nowait() if self._busy else self._commands.get(timeout=0.05)
        except queue.Empty:
            command = None
        if command is not None:
            if command[0] == "quit":
                return True
            self._handle(voice, command)
        if pythoncom is not None:
            pythoncom.PumpWaitingMessages()
        if self._busy and self._commands.empty():
            try:
                done = bool(voice.WaitUntilDone(WAIT_SLICE_MS))
            except Exception as exc:
                self._log_error("WaitUntilDone", exc)
                done = True
            if not done:
                now = time.monotonic()
                current = self._progress(voice)
                if current != progress:
                    progress, progress_time = current, now
                elif current is not None and now - progress_time > STALL_SECONDS:
                    log.warning("SAPI 5 speech made no progress for %s s (another program "
                                "speaking?); speech stopped", STALL_SECONDS)
                    try:
                        voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
                    except Exception as exc:
                        self._log_error("purge after stall", exc)
                    done = True
            if done:
                log.debug("speech done")
                self._note_healthy()
                progress = None
                with self._cv:
                    self._busy = False
                    self._cv.notify_all()
        state[0], state[1] = progress, progress_time
        return False

    def _loop_render(self, voice, pythoncom) -> None:
        """Rendered mode: SAPI makes each chunk of text into memory, the player plays it."""
        player = self._player
        pending: list = []          # (chunk, other ways to write it or None) not yet made
        current = None              # the entry being made
        stream = None               # the memory stream SAPI is filling, None when not making
        direct_state = [None, time.monotonic()]
        while True:
            if self._direct:
                if self._direct_step(voice, pythoncom, direct_state):
                    return
                continue
            making = stream is not None
            playing = False if making else player.busy()
            wait = 0.05 if not (pending or making or playing) else 0.002
            try:
                command = self._commands.get(timeout=wait)
            except queue.Empty:
                command = None
            if command is not None:
                kind = command[0]
                if kind == "quit":
                    return
                if kind == "speak":
                    chunks = [c for c in split_chunks(command[1]) if c.strip()]
                    with self._cv:
                        pending.extend((c, None) for c in chunks)
                        self._queued -= 1
                        self._busy = self._busy or bool(chunks)
                        self._cv.notify_all()
                elif kind == "purge":
                    pending.clear()
                    if stream is not None:
                        try:  # memory output: returns at once
                            voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
                        except Exception as exc:
                            self._log_error("purge", exc)
                        stream = None
                    player.reset()
                    log.debug("purge")
                else:
                    self._handle(voice, command)
            if pythoncom is not None:
                pythoncom.PumpWaitingMessages()
            if stream is None and pending:
                current = pending.pop(0)
                stream = self._start_chunk(voice, current[0])
            if stream is not None:
                try:
                    done = bool(voice.WaitUntilDone(1))
                except Exception as exc:
                    self._log_error("WaitUntilDone", exc)
                    done = True
                if done:
                    if not self._play_chunk(stream) and current is not None:
                        # the voice made no sound for this text: try the next way of writing it
                        alts = speech_variants(current[0]) if current[1] is None else current[1]
                        if alts:
                            log.debug("no audio for %r, trying %r", current[0], alts[0])
                            pending.insert(0, (alts[0], alts[1:]))
                    stream = None
            idle = stream is None and not pending and not player.busy()
            if idle and self._busy:
                log.debug("speech done")
                self._note_healthy()
                with self._cv:
                    if not self._queued:
                        self._busy = False
                    self._cv.notify_all()

    def _start_chunk(self, voice, text: str):
        """Begin making text into a new memory stream. Returns the stream, or None on failure."""
        try:
            stream = self._stream_factory()
            voice.AudioOutputStream = stream
            text, flags = apply_pitch(text, self._pitch)
            voice.Speak(text, SVSF_ASYNC | flags)
            log.debug("speak %r", text)
            return stream
        except Exception as exc:
            self._log_error("Speak", exc)
            return None

    def _play_chunk(self, stream) -> bool:
        """Give the finished audio to the player. False when the voice made none."""
        try:
            data = bytes(stream.GetData())
            if data:
                data = trim_silence(data, RENDER_RATE)     # voices end with silence that would delay the sounds
            if data and not self._player.write(data):
                log.warning("the audio device refused speech")
            self.last_start_at = time.monotonic()
            return bool(data)
        except Exception as exc:
            self._log_error("play", exc)
            return True      # an error is not "no sound for this text": do not try other texts

    @staticmethod
    def _progress(voice):
        """What changes while speech moves on: (running state, stream, word position). None if unknown."""
        try:
            status = voice.Status
            return (int(status.RunningState), int(status.CurrentStreamNumber),
                    int(status.InputWordPosition))
        except Exception:
            return None

    def _handle(self, voice, command) -> None:
        kind = command[0]
        try:
            if kind == "speak":
                text, flags = apply_pitch(command[1], self._pitch)
                try:
                    voice.Speak(text, SVSF_ASYNC | flags)
                    self.last_start_at = time.monotonic()
                    log.debug("speak %r", command[1])
                    started = True
                except Exception as exc:
                    self._log_error("Speak", exc)
                    started = False
                with self._cv:
                    self._queued -= 1
                    self._busy = self._busy or started
                    self._cv.notify_all()
            elif kind == "purge":
                voice.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
                log.debug("purge")
                with self._cv:
                    self._busy = False
                    self._cv.notify_all()
            elif kind == "rate":
                voice.Rate = self._base_rate if command[1] is None else command[1]
            elif kind == "volume":
                self._volume = command[1]
                voice.Volume = command[1]
            elif kind == "pitch":
                self._pitch = command[1]
            elif kind == "voice":
                rate, volume = int(voice.Rate), int(voice.Volume)
                self._select_voice(voice, voice.GetVoices("", ""), command[1])
                voice.Rate, voice.Volume = rate, volume  # keep the player's settings
                token = voice.Voice
                self.started.voice_id = str(token.Id)
                self.started.voice_name = str(token.GetDescription())
                if self._player is not None:
                    self._choose_mode(voice)
        except Exception as exc:
            self._log_error(kind, exc)

    def _note_healthy(self) -> None:
        hook, self.on_healthy = self.on_healthy, None
        if hook is not None:
            try:
                hook()
            except Exception as exc:
                log.debug("voice health hook failed: %s", exc)

    def _log_error(self, what: str, exc: Exception) -> None:
        if self._errors_logged < 20:  # a broken engine must not flood the log
            self._errors_logged += 1
            log.warning("SAPI 5 %s failed: %s: %s", what, type(exc).__name__, exc)
