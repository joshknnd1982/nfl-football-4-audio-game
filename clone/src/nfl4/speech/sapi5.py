"""SAPI 5 speech backend: several voices, one queue. This is inspired by Jim Kitchen.

The start-up voice (GAME_SPEC 3 step 3): the first voice in SAPI's list, its default rate kept as the base rate.
One dedicated thread owns every SpVoice COM object in a single-threaded apartment, as the original VB6 form did; other
threads send it commands. That keeps odd third-party engines happy and lets any thread speak or stop speech.

Speakers with their own voices (nfl4 S7.1, D-031 items 1 and 3, GAP_REGISTER G-S1 and G-S6). NFL Football 4 has five
speakers (speech/roles.py), each with a voice and a volume. The original loaded a voice on one SpVoice object whenever
the speaker changed; the clone keeps ONE SpVoice object per distinct voice, made the first time a speaker with that
voice talks (B-S21: five objects at once work in both bitnesses), and every text goes through ONE first-in-first-out
queue: a text is made or spoken only after the one before it has been heard to its end, whatever voice either has, so
nothing is ever cut by a voice change (the original cut the tail of an unguarded " Hike! ", Q52, not reproduced). Two
speakers with the same voice share the object and keep their own volumes (D-022 item 5): the volume and the rate are set
on the object just before each text. A text may ask for a rate step (banter line 113 is one step faster, Q38).

The original's say (Speak flags 0) is done here as an async Speak plus a wait for the end of speech: SAPI parses the
same text the same way (flags 0 and 1 differ only in waiting), and the wait can be broken when the window closes.

Rendered mode (Brain, DECISIONS 2026-10-13, speech latency). With SAPI's own audio output, stopping speech (purge)
blocked the speech thread for up to 700 ms on some voices, so a key pressed while a voice was talking waited for the old
speech before the new speech began. In rendered mode SAPI makes each text into memory (10 to 60 ms for a menu item,
about 30 times faster than real time), and the thread plays it through waveout.WaveOut, which stops at once. Long
texts are made and played sentence by sentence so they start quickly. If no audio device opens, every voice speaks in
the direct mode (SAPI's own output), one text after the other.

Two things were tried and rejected (Brain, DECISIONS 2026-10-13, speech skipping words): playing the memory stream
while the engine is still writing it (the stream's contents change after they are read, so words were skipped), and
rendering with engines that make speech no faster than they speak it (Orpheus, Prose 2000, neural voices: the player
would wait the length of the text). Instead each voice gets a speed probe when it is opened or chosen: if it cannot make
a short text within PROBE_LIMIT_SECONDS, that voice speaks in the direct mode, as the original did. A direct text starts
only when the player has played everything before it, and the next text waits for it, so the order stays one queue.

Crash guard (playbook 7.4.5, data/voiceguard.py): `on_voice_trial(voice_id)` is called before a voice is opened or
chosen again, and `on_voice_proven(voice_id)` once that voice has made or spoken a text to the end. The first voice of
SAPI's list is reported as "" (it is the fallback and is never set aside).
"""
from __future__ import annotations

import collections
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
ORIGINAL_VOLUME = 90  # GAME_SPEC 3 step 3: the first voice at volume 90 until a speaker's own volume is applied
WAIT_SLICE_MS = 5     # how long the speech thread waits inside SAPI per pass while a voice speaks directly
SAFT_44KHZ_16BIT_MONO = 34  # SpeechAudioFormatType; matches WaveOut's fixed format
RENDER_RATE = 44100
CHUNK_FROM_CHARS = 60  # longer texts are made and played sentence by sentence
CHUNK_MIN_CHARS = 25   # a sentence shorter than this is joined to the next one
MAX_CHUNK_CHARS = 300   # a piece longer than this is cut at spaces (S8.3)
MAX_WORD_CHARS = 100    # no word is longer than this in a piece made into memory (S8.3)
PROBE_TEXT = "Select. no panning"   # Brain's calibration text for the 0.25 s limit (any short text works)
PROBE_LIMIT_SECONDS = 0.25  # a voice slower than this for the probe text is spoken directly, not rendered
STALL_SECONDS = 8.0   # no progress this long while speaking = deadlock with another program
DEFAULT_ROLE = "main"   # the one speaker when no roles are given (the kit's single-voice use)


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
        return [_tidy(text)] if _LONE_STOP.search(text) else [text]
    # a single capital letter and a full stop is an initial ("N. F. L."), not the end of a sentence: the welcome sentence of
    # rule 0.16 must not be cut after "N." into two pieces with a gap between them
    pieces = [p for p in re.split(r"(?<=[.!?:;])(?<!\b[A-Z]\.)\s+|\n+", text) if p.strip()]
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
    # S8.3 (fixesforgames B-S28): the old emulated engines were measured to die on two kinds of piece: one with a lone full stop or comma in it
    # (SAM, heap corruption on ". 31 items. Press F1 for help." and on "Press F1 for help. , current voice", which the list titles make when a
    # name is empty) and one with a 4,000 letter word (Votrax, stack overrun). A token of only stops says nothing, and no word is longer
    # than MAX_WORD_CHARS.
    cleaned = [_cut_long(_tidy(piece)) for piece in chunks]
    result = [part for group in cleaned for part in group if part.strip()]
    return result or [text]


_LONE_STOP = re.compile(r"(?<!\S)[.,;:]+(?!\S)")


def _tidy(piece: str) -> str:
    """The piece without a token that is only full stops, commas, semicolons or colons (an empty list title followed by ". 31 items" makes
    one): it says nothing, and SAM died on it (fixesforgames B-S28). Spaces stay as they were."""
    return _LONE_STOP.sub("", piece)


def _cut_long(piece: str) -> list[str]:
    """A piece over MAX_CHUNK_CHARS is cut at spaces; a word over MAX_WORD_CHARS is cut into pieces of that size."""
    if len(piece) <= MAX_CHUNK_CHARS and len(max(piece.split(), key=len, default="")) <= MAX_WORD_CHARS:
        return [piece]
    words: list[str] = []
    for word in piece.split():
        words += [word[i:i + MAX_WORD_CHARS] for i in range(0, len(word), MAX_WORD_CHARS)]
    parts, line = [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > MAX_CHUNK_CHARS:
            parts.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        parts.append(line)
    return parts


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
    cleaned = re.sub(r"[�\x00-\x08\x0b-\x1f]", " ", text)
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


@dataclass
class RoleVoice:
    """The voice and the volume of one speaker."""
    voice_id: str | None = None      # None or "" = the first voice in SAPI's list (the original's voice 0)
    volume: int = ORIGINAL_VOLUME


@dataclass(frozen=True)
class VoiceDetails:
    """What a speaker's voice is, read from its voice token without opening the voice."""
    voice_id: str
    name: str
    gender: str          # the token's Gender attribute ("Female", "Male"; "" when it has none)


class _Voice:
    """One SpVoice object for one voice token (speech thread only)."""

    def __init__(self, com, token_id: str, name: str):
        self.com = com
        self.token_id = token_id
        self.name = name
        self.direct = True       # spoken through SAPI's own output (no player, or too slow to render)
        self.rate = None         # what was last set on the object
        self.volume = None
        self.proven = False      # has made or spoken a text to the end (the crash guard's all clear)


@dataclass
class _Entry:
    """One text waiting in the queue."""
    role: str
    text: str
    rate_step: int = 0
    chunked: bool = False        # already one sentence of a longer text (rendered mode)
    alts: list | None = None     # other ways to write it still to try; None = not tried yet


class _Work:
    """The text being made (render) or spoken (direct) now."""

    def __init__(self, kind: str, entry: _Entry, voice: _Voice, stream=None):
        self.kind = kind
        self.entry = entry
        self.voice = voice
        self.stream = stream
        self.progress = None
        self.progress_time = time.monotonic()


class SapiBackend(SpeechBackend):
    name = "SAPI 5"
    takes_roles = True        # the manager passes role and rate_step to speak()

    def __init__(self, voice_id: str | None = None, rate: int | None = None,
                 volume: int = ORIGINAL_VOLUME, pitch: int = 0,
                 voice_factory=default_voice_factory, token_factory=default_token_factory,
                 com_init=True, render: bool = False, player_factory=default_player_factory,
                 stream_factory=default_stream_factory, roles: dict[str, RoleVoice] | None = None,
                 default_role: str | None = None):
        if roles:
            self._roles = {name: RoleVoice(r.voice_id or None, clamp(r.volume, VOLUME_MIN, VOLUME_MAX))
                           for name, r in roles.items()}
            self._default_role = default_role if default_role in self._roles else next(iter(self._roles))
        else:
            self._roles = {DEFAULT_ROLE: RoleVoice(voice_id or None, clamp(volume, VOLUME_MIN, VOLUME_MAX))}
            self._default_role = DEFAULT_ROLE
        self._role_lock = threading.Lock()
        self._want_rate = rate
        self._rate = 0                 # vr: the rate every voice speaks at (set at start)
        self._base_rate = 0
        self._pitch = clamp(pitch, PITCH_MIN, PITCH_MAX)
        self._voice_factory = voice_factory
        self._token_factory = token_factory
        self._com_init = com_init
        self._render = render
        self._player_factory = player_factory
        self._stream_factory = stream_factory
        self._player = None
        self._tokens = None            # SAPI's voice list (GetVoices), read once at start
        self._resolved: dict[str, object] = {}     # wanted voice id (lower case) -> its token
        self._voices: dict[str, _Voice] = {}       # token id (lower case) -> the voice object
        self._reprobe: set[str] = set()            # voices chosen again: probe them when nothing is speaking
        self._last_voice: _Voice | None = None     # the voice that spoke last (a stop with nothing in hand purges it)
        self.last_start_at = 0.0  # time.monotonic() when speech was last handed to the output (latency tool)
        self._first_request = 0.0
        self.first_utterance = ""   # the startup report's "time of the first test utterance": request to hand-over, in ms
        self._commands: queue.Queue = queue.Queue()
        self._cv = threading.Condition()
        self._queued = 0        # speak commands sent but not yet taken by the speech thread
        self._busy = False      # something is being made, spoken or played, or waits in the queue
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._errors_logged = 0
        self.on_healthy = None        # called once when speech has ended after this was set (the kit's voice guard hook)
        self.on_voice_trial = None    # called with a voice id before that voice is opened (data/voiceguard.py arm)
        self.on_voice_proven = None   # called with a voice id when that voice has made its first text (guard clear)
        self.started = SapiStart(ok=False, error="not started")

    # ----- life cycle -------------------------------------------------------------
    def start(self, timeout: float = 15.0) -> SapiStart:
        """Start the speech thread and wait until the start-up voice is ready (or found missing)."""
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

    def speak(self, text: str, role: str | None = None, rate_step: int = 0) -> bool:
        """Queue text for the speaker `role` (None: the default speaker), rate_step steps faster than the rate."""
        if not self.is_available():
            return False
        if not self._first_request:
            self._first_request = time.monotonic()
        with self._cv:
            self._queued += 1
        self._commands.put(("speak", text, role if role in self._roles else self._default_role, int(rate_step)))
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

    def queue_length(self) -> int:
        """Texts sent to the speech thread and not yet taken (the debug log writes it with every request)."""
        return self._queued

    # ----- speakers ---------------------------------------------------------------------
    @property
    def roles(self) -> tuple[str, ...]:
        return tuple(self._roles)

    @property
    def default_role(self) -> str:
        return self._default_role

    def role_voice(self, role: str) -> RoleVoice:
        """The voice and volume wanted for a speaker (a copy)."""
        with self._role_lock:
            wanted = self._roles.get(role) or self._roles[self._default_role]
            return RoleVoice(wanted.voice_id, wanted.volume)

    def set_role_voice(self, role: str, voice_id: str | None) -> None:
        """Choose a speaker's voice (None: the first voice). The voice is opened and probed by the speech thread."""
        if role not in self._roles:
            return
        with self._role_lock:
            self._roles[role].voice_id = voice_id or None
        self._commands.put(("role_voice", role))

    def set_role_volume(self, role: str, volume: int) -> None:
        if role not in self._roles:
            return
        with self._role_lock:
            self._roles[role].volume = clamp(volume, VOLUME_MIN, VOLUME_MAX)

    def role_details(self, role: str, timeout: float = 3.0) -> VoiceDetails | None:
        """The id, name and Gender attribute of a speaker's voice, read from its token by the speech thread (the voice
        itself is not opened, so a voice that would crash cannot crash here). None when SAPI is not running."""
        if not self.is_available():
            return None
        answer: list = []
        done = threading.Event()
        self._commands.put(("details", role, answer, done))
        done.wait(timeout)
        return answer[0] if answer else None

    # ----- settings (clone additions) -------------------------------------------------
    @property
    def voice_name(self) -> str:
        return self.started.voice_name

    @property
    def voice_id(self) -> str:
        return self.started.voice_id

    @property
    def base_rate(self) -> int:
        return self.started.base_rate

    @property
    def rate(self) -> int:
        """vr: the rate every voice speaks at now."""
        return self._rate

    def set_rate(self, rate: int | None) -> None:
        """None restores the first voice's own base rate (the original's start value of vr)."""
        self._commands.put(("rate", None if rate is None else clamp(rate, RATE_MIN, RATE_MAX)))

    def set_volume(self, volume: int) -> None:
        """The default speaker's volume (the kit's single-voice setting)."""
        self.set_role_volume(self._default_role, volume)

    def set_pitch(self, pitch: int) -> None:
        self._commands.put(("pitch", clamp(pitch, PITCH_MIN, PITCH_MAX)))

    def set_voice(self, voice_id: str | None) -> None:
        """The default speaker's voice; None selects the first voice in SAPI's list (the original's choice)."""
        self.set_role_voice(self._default_role, voice_id)

    @property
    def rendered(self) -> bool:
        """True when the default speaker's voice is spoken in rendered mode (tools and tests)."""
        voice = self._voices.get(self.started.voice_id.lower()) if self.started.voice_id else None
        return self._player is not None and voice is not None and not voice.direct

    # ----- speech thread ------------------------------------------------------------
    def _run(self) -> None:
        pythoncom = None
        if self._com_init:
            import pythoncom
            pythoncom.CoInitialize()
        try:
            if self._open():
                self._loop(pythoncom)
        except Exception as exc:  # the speech thread must never take the game down
            log.exception("SAPI 5 speech thread failed: %s", exc)
            self.started = SapiStart(ok=False, error=f"{type(exc).__name__}: {exc}")
        finally:
            self._ready.set()
            for voice in list(self._voices.values()):
                try:
                    voice.com.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
                except Exception as exc:
                    log.debug("purging %s at the end failed: %s", voice.name, exc)
            self._voices.clear()
            self._resolved.clear()
            self._tokens = None
            self._last_voice = None
            if self._player is not None:
                try:
                    self._player.close()
                except Exception as exc:
                    log.warning("the speech player did not close cleanly: %s", exc, exc_info=exc)
                self._player = None
            with self._cv:
                self._queued = 0
                self._busy = False
                self._cv.notify_all()
            if pythoncom is not None:
                pythoncom.CoUninitialize()

    def _open(self) -> bool:
        """GAME_SPEC 3 steps 3 and 4: SAPI's voice list, the first voice's rate as vr, the default speaker's voice."""
        try:
            com = self._voice_factory()
            tokens = com.GetVoices("", "")
            count = tokens.Count
        except Exception as exc:
            self.started = SapiStart(ok=False, error=f"SAPI 5 unavailable: {type(exc).__name__}: {exc}")
            log.error(self.started.error)
            self._ready.set()
            return False
        if count == 0:
            self.started = SapiStart(ok=False, voice_count=0, error="no SAPI 5 voices installed")
            log.error(self.started.error)
            self._ready.set()
            return False
        self._tokens = tokens
        base_rate = int(com.Rate)        # the original reads the rate and keeps it in vr
        self._base_rate = base_rate
        self._rate = base_rate if self._want_rate is None else clamp(self._want_rate, RATE_MIN, RATE_MAX)
        if self._render:
            try:
                self._player = self._player_factory()
            except Exception as exc:
                log.warning("rendered speech unavailable (%s: %s); SAPI 5 plays through its own output",
                            type(exc).__name__, exc)
        role = self.role_voice(self._default_role)
        voice = self._adopt(com, self._resolve(role.voice_id), role.voice_id)
        com.Rate = self._rate            # a voice load sets Rate = vr and the speaker's volume (GAME_SPEC 9.1)
        com.Volume = role.volume
        voice.rate, voice.volume = self._rate, role.volume
        self._last_voice = voice
        self.started = SapiStart(ok=True, voice_count=count, voice_id=voice.token_id, voice_name=voice.name,
                                 base_rate=base_rate)
        log.info("SAPI 5 ready: %d voices, %r for the %s, rate %d (base %d), %d speakers",
                 count, voice.name, self._default_role, self._rate, base_rate, len(self._roles))
        self._ready.set()
        return True

    # ----- voices: tokens, objects, probes ----------------------------------------------
    def _first_token(self):
        return self._tokens.Item(0)

    def _resolve(self, voice_id: str | None):
        """The token of a wanted voice; the first voice when it is None or not installed (logged once)."""
        if not voice_id:
            return self._first_token()
        key = voice_id.strip().lower()
        if key in self._resolved:
            return self._resolved[key]
        token = None
        try:  # cheap direct lookup, 2 ms on the owner's PC
            candidate = self._token_factory()
            candidate.SetId(voice_id)
            token = candidate
        except Exception as exc:
            log.debug("direct lookup of voice %s failed (%s); searching SAPI's list", voice_id, exc)
            pass
        if token is None:
            try:  # tokens from token enumerators may not accept SetId: scan the list
                for i in range(self._tokens.Count):
                    candidate = self._tokens.Item(i)
                    if str(candidate.Id).strip().lower() == key:
                        token = candidate
                        break
            except Exception as exc:
                log.warning("voice list scan failed: %s", exc)
        if token is None:
            log.warning("saved voice %r not found, using the first voice", voice_id)
            token = self._first_token()
        self._resolved[key] = token
        return token

    def _token_name(self, token) -> tuple[str, str]:
        token_id = str(token.Id)
        try:
            name = str(token.GetDescription())
        except Exception as exc:
            log.debug("voice %s has no description (%s)", token_id, exc)
            name = token_id.rsplit("\\", 1)[-1]
        return token_id, name

    def _is_first(self, token_id: str) -> bool:
        try:
            return token_id.lower() == str(self._first_token().Id).lower()
        except Exception:
            return False

    def _trial(self, token_id: str) -> None:
        hook = self.on_voice_trial
        if hook is not None:
            try:
                hook("" if self._is_first(token_id) else token_id)
            except Exception as exc:
                log.debug("voice trial hook failed: %s", exc)

    def _adopt(self, com, token, wanted_id: str | None) -> _Voice:
        """Put a voice token on a SpVoice object and probe it. Falls back to the first voice if the token is refused."""
        token_id, name = self._token_name(token)
        self._trial(token_id)
        try:
            com.Voice = token
        except Exception as exc:
            self._log_error(f"select voice {name!r}", exc)
            token = self._first_token()
            token_id, name = self._token_name(token)
            try:
                com.Voice = token
            except Exception as exc2:
                self._log_error("select the first voice", exc2)
        voice = _Voice(com, token_id, name)
        self._voices[token_id.lower()] = voice
        self._probe(voice)
        return voice

    def _probe(self, voice: _Voice) -> None:
        """Rendered if the voice makes a short text fast enough, else direct (there is no player: direct)."""
        if self._player is None:
            voice.direct = True
            return
        fast = self._renders_fast(voice.com)
        voice.direct = not fast
        if fast:
            self._prove(voice)
        log.info("speech mode for %r: %s", voice.name,
                 "rendered" if fast else "direct (this voice makes speech too slowly to render)")

    def _renders_fast(self, com) -> bool:
        """Make PROBE_TEXT into memory; True if it finishes within PROBE_LIMIT_SECONDS. Leaves the
        voice on its default audio output when it did not, so direct speech works afterwards."""
        try:
            com.AudioOutputStream = self._stream_factory()
            com.Speak(PROBE_TEXT, SVSF_ASYNC)
            fast = bool(com.WaitUntilDone(int(PROBE_LIMIT_SECONDS * 1000)))
        except Exception as exc:
            self._log_error("speed probe", exc)
            fast = False
        if not fast:
            try:
                com.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)   # still writing to memory: returns at once
                com.AudioOutput = com.GetAudioOutputs().Item(0)
            except Exception as exc:
                self._log_error("back to the default output", exc)
        return fast

    def _voice_for(self, role: str) -> _Voice | None:
        """The voice object of a speaker, opened the first time a speaker with that voice talks."""
        wanted = self.role_voice(role)
        token = self._resolve(wanted.voice_id)
        token_id, _name = self._token_name(token)
        voice = self._voices.get(token_id.lower())
        if voice is not None:
            return voice
        try:
            com = self._voice_factory()
        except Exception as exc:
            self._log_error("open another voice", exc)
            return self._voices.get(self.started.voice_id.lower())
        return self._adopt(com, token, wanted.voice_id)

    def _choose_again(self, role: str) -> None:
        """A speaker's voice was chosen (role_voice command): open it now, or probe it again when it is open."""
        wanted = self.role_voice(role)
        token = self._resolve(wanted.voice_id)
        token_id, name = self._token_name(token)
        voice = self._voices.get(token_id.lower())
        if voice is None:
            try:
                voice = self._adopt(self._voice_factory(), token, wanted.voice_id)
            except Exception as exc:
                self._log_error("open the chosen voice", exc)
        else:
            self._reprobe.add(token_id.lower())        # probed when nothing is speaking (see _loop)
        if role == self._default_role and voice is not None:
            self.started.voice_id = voice.token_id
            self.started.voice_name = voice.name

    def _details(self, role: str) -> VoiceDetails:
        token = self._resolve(self.role_voice(role).voice_id)
        token_id, name = self._token_name(token)
        try:
            gender = str(token.GetAttribute("Gender") or "")
        except Exception:
            gender = ""                          # no Gender attribute: the original says " He "
        return VoiceDetails(token_id, name, gender)

    def _prove(self, voice: _Voice) -> None:
        if voice.proven:
            return
        voice.proven = True
        hook = self.on_voice_proven
        if hook is not None:
            try:
                hook("" if self._is_first(voice.token_id) else voice.token_id)
            except Exception as exc:
                log.debug("voice proven hook failed: %s", exc)

    # ----- the queue -----------------------------------------------------------------------
    def _loop(self, pythoncom) -> None:
        pending: collections.deque[_Entry] = collections.deque()
        work: _Work | None = None
        while True:
            playing = self._player is not None and work is None and self._player.busy()
            active = bool(pending) or work is not None or playing
            try:
                command = self._commands.get(timeout=0.002 if active else 0.05)
            except queue.Empty:
                command = None
            if command is not None:
                kind = command[0]
                if kind == "quit":
                    self._purge(work, pending)
                    return
                if kind == "speak":
                    _kind, text, role, step = command
                    with self._cv:
                        self._queued -= 1
                        if text.strip():         # the original's Speak " " is only a barrier: say() waits for the queue
                            pending.append(_Entry(role, text, step))
                            self._busy = True
                        self._cv.notify_all()
                elif kind == "purge":
                    work = self._purge(work, pending)
                else:
                    self._handle(command)
            if pythoncom is not None:
                pythoncom.PumpWaitingMessages()
            if work is None:
                for key in list(self._reprobe):
                    self._reprobe.discard(key)
                    voice = self._voices.get(key)
                    if voice is not None:
                        self._trial(voice.token_id)
                        self._probe(voice)
                if pending:
                    work = self._start_next(pending)
            if work is not None and self._step(work, pending):
                work = None
            if self._busy and work is None and not pending and not (self._player is not None and self._player.busy()):
                log.debug("speech done")
                self._note_healthy()
                with self._cv:
                    if not self._queued:
                        self._busy = False
                    self._cv.notify_all()

    def _apply(self, voice: _Voice, entry: _Entry) -> None:
        """The speaker's volume and the rate (plus the text's rate step) on the voice object, just before its text."""
        volume = self.role_voice(entry.role).volume
        rate = clamp(self._rate + entry.rate_step, RATE_MIN, RATE_MAX)
        try:
            if voice.volume != volume:
                voice.com.Volume = volume
                voice.volume = volume
            if voice.rate != rate:
                voice.com.Rate = rate
                voice.rate = rate
        except Exception as exc:
            self._log_error("rate or volume", exc)

    def _start_next(self, pending) -> _Work | None:
        """Begin the next text: make it into memory (rendered voice) or speak it (direct voice, only when the player
        has played everything before it). None when it must wait or there was nothing to do."""
        entry = pending[0]
        voice = self._voice_for(entry.role)
        if voice is None:
            pending.popleft()
            log.warning("no voice could say %r", entry.text)
            return None
        if voice.direct or self._player is None:
            if self._player is not None and self._player.busy():
                return None                          # rendered speech before it is still playing: keep the order
            pending.popleft()
            self._apply(voice, entry)
            text, flags = apply_pitch(entry.text, self._pitch)
            try:
                voice.com.Speak(text, SVSF_ASYNC | flags)
            except Exception as exc:
                self._log_error("Speak", exc)
                return None
            self.last_start_at = time.monotonic()
            self._note_first_start()
            self._last_voice = voice
            log.debug("speak %r (%s, direct)", entry.text, entry.role)
            return _Work("direct", entry, voice)
        pending.popleft()
        if not entry.chunked:
            chunks = [c for c in split_chunks(entry.text) if c.strip()]
            if not chunks:
                return None
            for chunk in reversed(chunks[1:]):
                pending.appendleft(_Entry(entry.role, chunk, entry.rate_step, True))
            entry = _Entry(entry.role, chunks[0], entry.rate_step, True)
        try:
            stream = self._stream_factory()
            voice.com.AudioOutputStream = stream
            self._apply(voice, entry)
            text, flags = apply_pitch(entry.text, self._pitch)
            voice.com.Speak(text, SVSF_ASYNC | flags)
        except Exception as exc:
            self._log_error("Speak", exc)
            return None
        self._last_voice = voice
        log.debug("speak %r (%s)", entry.text, entry.role)
        return _Work("render", entry, voice, stream)

    def _step(self, work: _Work, pending) -> bool:
        """One pass on the current text. True when it is finished (made and handed to the player, or spoken)."""
        com = work.voice.com
        if work.kind == "render":
            try:
                done = bool(com.WaitUntilDone(1))
            except Exception as exc:
                self._log_error("WaitUntilDone", exc)
                done = True
            if not done:
                return False
            if self._play_chunk(work.stream):
                self._prove(work.voice)
            else:
                # the voice made no sound for this text: try the next way of writing it
                entry = work.entry
                alts = speech_variants(entry.text) if entry.alts is None else entry.alts
                if alts:
                    log.debug("no audio for %r, trying %r", entry.text, alts[0])
                    pending.appendleft(_Entry(entry.role, alts[0], entry.rate_step, True, alts[1:]))
            return True
        try:
            done = bool(com.WaitUntilDone(WAIT_SLICE_MS))
        except Exception as exc:
            self._log_error("WaitUntilDone", exc)
            done = True
        if done:
            self._prove(work.voice)
            return True
        # Stall watchdog (Brain S7.1 test): when two programs speak through SAPI at once, Windows can deadlock them;
        # one waits for the audio device (state "not started") while the other holds it at word 0, forever. If the
        # voice's status shows no progress for STALL_SECONDS, this copy stops its own speech and goes on.
        now = time.monotonic()
        current = self._progress(com)
        if current != work.progress:
            work.progress, work.progress_time = current, now
        elif current is not None and now - work.progress_time > STALL_SECONDS:
            log.warning("SAPI 5 speech made no progress for %s s (another program speaking?); speech stopped",
                        STALL_SECONDS)
            try:
                com.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
            except Exception as exc:
                self._log_error("purge after stall", exc)
            return True
        return False

    def _purge(self, work: _Work | None, pending) -> None:
        """Stop at once: drop the queue, cut the text being made or spoken, silence the player."""
        pending.clear()
        voice = work.voice if work is not None else (self._last_voice if self._player is None else None)
        if voice is not None:
            try:  # memory output returns at once; a direct voice may take longer (B-S1)
                voice.com.Speak("", SVSF_ASYNC | SVSF_PURGE_BEFORE_SPEAK)
            except Exception as exc:
                self._log_error("purge", exc)
        if self._player is not None:
            self._player.reset()
        log.debug("purge")
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
            self._note_first_start()
            return bool(data)
        except Exception as exc:
            self._log_error("play", exc)
            return True      # an error is not "no sound for this text": do not try other texts

    @staticmethod
    def _progress(com):
        """What changes while speech moves on: (running state, stream, word position). None if unknown."""
        try:
            status = com.Status
            return (int(status.RunningState), int(status.CurrentStreamNumber),
                    int(status.InputWordPosition))
        except Exception:
            return None

    def _handle(self, command) -> None:
        kind = command[0]
        try:
            if kind == "rate":
                self._rate = self._base_rate if command[1] is None else command[1]
            elif kind == "pitch":
                self._pitch = command[1]
            elif kind == "role_voice":
                self._choose_again(command[1])
            elif kind == "details":
                _kind, role, answer, done = command
                try:
                    answer.append(self._details(role))
                finally:
                    done.set()
        except Exception as exc:
            self._log_error(kind, exc)

    def _note_first_start(self) -> None:
        if not self.first_utterance and self._first_request:
            self.first_utterance = "%d ms from the request to the hand-over to the output" % round(
                (self.last_start_at - self._first_request) * 1000)

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
            log.warning("SAPI 5 %s failed: %s: %s", what, type(exc).__name__, exc, exc_info=exc)
