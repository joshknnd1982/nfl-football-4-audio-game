"""The whole program through app.main(): the title, no voice, a window closed while the game talks, the crash guard
for the five speakers' voices. This is inspired by Jim Kitchen.

The real Win32 window and the real game thread run; speech is a fake so nothing is heard. The window shows for about a
second each time. The player's folders are not touched (NFL4_DATA_DIR in tmp_path). Rule 0.5.1, CLAUDE.md 0.10,
GAP_REGISTER G-F1, G-F8, G-F9, playbook 7.2.1 and 7.4.5.
"""
import os
import threading
import time

import pytest

import nfl4.app as app
import nfl4.audio.engine as audio_engine
import nfl4.ui.window as window_module
from nfl4.audio.engine import NO_SOUND_NOTICE
from nfl4.audio.library import SOUND_FILE_NOTICE
from nfl4.audio.output import OutputError
from nfl4.data.voiceguard import CRASHED_FILE, TRIAL_FILE
from nfl4.game import texts
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager
from nfl4.speech.roles import ANNOUNCER, OPPONENT_PUNTER, OWN_QUARTERBACK
from nfl4.speech.sapi5 import SapiStart

SMOOTH = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\TokenEnums\SmoothTalker\SmoothTalker"


@pytest.fixture(autouse=True)
def sound_on_the_dummy_driver(monkeypatch):
    """The program starts the mixer (S7.2); here on SDL's silent dummy driver, so no test depends on a sound device."""
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True)
def window_stays_in_the_background(monkeypatch):
    """The program's show() brings its window to the front and takes the keyboard; in a test that would interrupt the
    owner's screen reader every run (and a key of the owner could land in it, B-X14). The window exists and gets the
    posted messages either way."""
    monkeypatch.setattr(window_module.GameWindow, "show", lambda self: False)


class Made:
    """A fake create_speech: records what main() asked for and hands back fakes."""

    def __init__(self, ok=True, nvda=None, per_char=0.0):
        self.sapi = FakeBackend(name="SAPI 5", takes_roles=True, seconds_per_char=per_char)
        self.manager = SpeechManager(self.sapi, nvda, "sapi")
        self.started = SapiStart(ok=ok, voice_count=3 if ok else 0, voice_id="first", voice_name="First voice",
                                 error="" if ok else "no SAPI 5 voices installed")
        self.calls = []

    def __call__(self, speech_settings, skip=frozenset(), arm=None, clear=None):
        self.calls.append((dict(speech_settings.voices), skip, arm, clear))
        for role, voice in speech_settings.voices.items():       # the voices SAPI would resolve
            if voice and voice.strip().lower() not in skip:
                self.sapi.role_voices[role] = voice
        return self.manager, self.started


def closing_after(seconds):
    real = window_module.GameWindow

    class Closing(real):
        """The player closes the window `seconds` after it opens."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.closed_at = []
            threading.Timer(seconds, self.close_now).start()

        def close_now(self):
            Closing.closed.append(time.monotonic())
            self.close()

    Closing.closed = []
    return Closing


def write_settings(folder, lines):
    (folder / "settings.txt").write_text("# NFL Football 4 settings, format 1\n" + "".join(l + "\n" for l in lines),
                                         encoding="utf-8")


@pytest.mark.window
def test_a_normal_start_says_the_title_and_closes_cleanly(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    window = closing_after(1.0)
    monkeypatch.setattr(window_module, "GameWindow", window)
    assert app.main() == 0
    assert made.sapi.said[0] == (texts.TITLE_SPOKEN, ANNOUNCER, 0)
    assert window.closed and time.monotonic() - window.closed[0] < 2.5
    assert (tmp_path / "settings.txt").is_file() and not (tmp_path / TRIAL_FILE).exists()
    log_text = (tmp_path / "logs" / "nfl4.log").read_text(encoding="utf-8")
    assert "NFL Football 4 clone closed" in log_text
    assert os.path.normcase(os.getcwd()) == os.path.normcase(str(tmp_path))  # left the program folder (7.2.1)


@pytest.mark.window
def test_a_sound_file_that_cannot_be_used_is_reported_once_at_start(tmp_path, monkeypatch):
    """G-A6: every sound is resolved at start, so the notice comes with the start-up notices, once."""
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    (tmp_path / "sounds").mkdir()
    (tmp_path / "sounds" / "foot7.wav").write_bytes(b"RIFF this is not a sound")
    (tmp_path / "sounds" / "foot12.wav").write_bytes(b"")
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken[0] == texts.TITLE_SPOKEN and spoken.count(SOUND_FILE_NOTICE) == 1
    assert (tmp_path / "sounds" / "sounds.txt").is_file()
    log_text = (tmp_path / "logs" / "nfl4.log").read_text(encoding="utf-8")
    assert "foot7.wav cannot be used" in log_text and "foot12.wav cannot be used" in log_text


@pytest.mark.window
def test_no_sound_device_is_said_once_and_the_program_runs_on(tmp_path, monkeypatch):
    """G-A4: the game goes on without sound and says so once."""
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))

    def no_device(*args, **kwargs):
        raise OutputError("no sound device")
    monkeypatch.setattr(audio_engine, "PygameOutput", no_device)
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    assert made.sapi.spoken().count(NO_SOUND_NOTICE) == 1


@pytest.mark.window
def test_no_sapi_voice_shows_the_box_tells_nvda_and_exits_cleanly(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    nvda = FakeBackend(name="NVDA")
    made = Made(ok=False, nvda=nvda)
    monkeypatch.setattr(app, "create_speech", made)
    boxes = []
    monkeypatch.setattr(window_module.GameWindow, "message_box", lambda self, text, title: boxes.append((text, title)))
    assert app.main() == 1                                                    # G-F9: the box, then a clean exit
    assert nvda.spoken() == [texts.NO_VOICES_SPOKEN]                          # the screen reader hears the same words
    assert boxes == [(texts.NO_VOICES + "\n" + texts.NO_VOICES_CONTACT, texts.MESSAGE_TITLE)]
    assert "Jim Kitchen" not in boxes[0][0] and "github.com/joshknnd1982" in boxes[0][0]   # D-008: no contact details
    assert made.sapi.said == []


@pytest.mark.window
def test_closing_the_window_while_the_game_talks_ends_the_program_within_two_seconds(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made(per_char=0.2)                                                 # the title alone would take 11 seconds
    monkeypatch.setattr(app, "create_speech", made)
    window = closing_after(1.0)
    monkeypatch.setattr(window_module, "GameWindow", window)
    assert app.main() == 0
    assert window.closed and time.monotonic() - window.closed[0] < 2.5
    assert made.sapi.spoken()[0] == texts.TITLE_SPOKEN                        # it really was in the middle of the title


@pytest.mark.window
def test_after_a_crash_the_speakers_with_that_voice_use_the_first_voice_and_the_game_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, [f"voice_own_quarterback = {SMOOTH}", f"voice_opponent_punter = {SMOOTH}",
                              "voice_announcer = token-7"])
    (tmp_path / TRIAL_FILE).write_text(SMOOTH + "\n")              # the last run died while this voice was in trial
    made = Made()
    made.sapi.role_voices[ANNOUNCER] = "token-7"
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    voices, skip, arm, clear = made.calls[0]
    assert skip == frozenset({SMOOTH.lower()})                     # not opened for either speaker
    spoken = made.sapi.spoken()
    crashed = [t for t in spoken if "The voice SmoothTalker crashed NFL Football 4 last time" in t]
    assert len(crashed) == 1 and "F12" in crashed[0]               # one notice for the voice, not one per speaker
    assert spoken.index(crashed[0]) > spoken.index(texts.TITLE_SPOKEN)
    text = (tmp_path / "settings.txt").read_text(encoding="utf-8")
    assert f"voice_own_quarterback = {SMOOTH}" in text and f"voice_opponent_punter = {SMOOTH}" in text  # kept
    assert SMOOTH in (tmp_path / CRASHED_FILE).read_text()
    assert not (tmp_path / TRIAL_FILE).exists()                    # closed normally: no new trial left


@pytest.mark.window
def test_the_guard_hooks_arm_a_new_voice_and_clear_only_that_voice(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    trial_seen = []
    real = window_module.GameWindow

    class Probe(real):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            threading.Timer(0.8, self.check).start()

        def check(self):
            _, _, arm, clear = made.calls[0]
            arm("")                                                # the first voice is never armed
            trial_seen.append((tmp_path / TRIAL_FILE).exists())
            arm("token-3")
            trial_seen.append((tmp_path / TRIAL_FILE).read_text().strip())
            clear("token-9")                                       # another voice proven: token-3's trial stays
            trial_seen.append((tmp_path / TRIAL_FILE).exists())
            clear("TOKEN-3")
            trial_seen.append((tmp_path / TRIAL_FILE).exists())
            self.close()

    monkeypatch.setattr(window_module, "GameWindow", Probe)
    assert app.main() == 0
    assert trial_seen == [False, "token-3", True, False]


@pytest.mark.window
def test_a_saved_voice_that_is_not_installed_is_told_once(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, ["voice_own_quarterback = token-gone", "voice_opponent_punter = token-also-gone"])
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)

    def resolve_to_first(role, timeout=3.0):
        from nfl4.speech.sapi5 import VoiceDetails
        return VoiceDetails("first", "First voice", "")

    made.sapi.role_details = resolve_to_first
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken.count("A voice saved in the settings was not found, so the first voice is used for it.") == 1
