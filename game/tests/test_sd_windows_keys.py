"""S-D (2026-11-06, D-205, fixesforgames B-W43): the volume, mute, media and browser keys belong to Windows, never to the game.
This is inspired by Jim Kitchen.

The owner's log of 0.16.12 (2026-11-06 10:55): in the defense menu he pressed volume up seven times and volume down once; each key cut
the speech, the key echo said "¯" or "®" (chr 175 and 174) and the menu began again. Windows changes the volume itself whatever the
window does (MEASURED with real input in work\\sd_1106\\appcommand_real_input_mute.py), so the game only has to leave the keys alone.
Posted keys never reach Windows' volume handling (MEASURED: no WM_APPCOMMAND, work\\sd_1106\\appcommand_probe.py), so the window
test below changes nothing on the PC.
"""
import threading
import time

import pytest

from nfl4.data import debuglog
from nfl4.game import key_list as K
from nfl4.game.keys import WINDOWS_KEYS, KeyInput
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager

VOLUME_UP, VOLUME_DOWN, MUTE = 175, 174, 173


def test_the_keys_windows_keeps_are_the_browser_volume_media_and_launch_keys():
    assert WINDOWS_KEYS == frozenset(range(166, 184))
    assert {VOLUME_UP, VOLUME_DOWN, MUTE, 179} <= WINDOWS_KEYS          # 179: play and pause
    every_game_key = {13, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 8, 9, 16, 17, 18, 187, 189, 107, 109}
    every_game_key |= set(range(48, 58)) | set(range(65, 91)) | set(range(96, 106)) | set(range(112, 124))
    assert not WINDOWS_KEYS & every_game_key


def test_a_key_of_windows_is_never_a_key_of_the_game():
    keys = KeyInput()
    for code in sorted(WINDOWS_KEYS):
        keys.post(code)
    assert not keys.key_waiting()
    keys.pump()
    assert (keys.code_text, keys.char) == ("", "")
    keys.post(VOLUME_UP)
    keys.post(40)                                                        # Down after it is the next key the game reads
    assert keys.read_key() == 40 and keys.code_text == "40"


def test_volume_up_while_the_announcer_speaks_neither_cuts_the_speech_nor_echoes_a_character():
    """wait_speech is the original's `Loop While g = "" And speaking`: before the fix the volume key ended it (g = "175") and the key
    echo then said chr(175). Now the wait runs to the end of the speech and nothing is said for the key."""
    clock = [0.0]
    backend = FakeBackend("SAPI 5", takes_roles=True, seconds_per_char=0.01, clock=lambda: clock[0],
                          sleep=lambda s: clock.__setitem__(0, clock[0] + s))
    speech = SpeechManager(backend, FakeBackend("NVDA", available=False), "sapi")
    keys = KeyInput(clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s))
    speech.say_async(" Nick Sirianni select the play for your dee fence ", role="announcer")
    keys.post(VOLUME_UP)
    keys.post(VOLUME_DOWN)
    keys.wait_speech(speech)
    assert keys.code_text == "" and not speech.is_speaking()
    assert [text for text, *_ in backend.said] == [" Nick Sirianni select the play for your dee fence "]


def test_the_log_says_the_key_was_left_to_windows(monkeypatch):
    seen = []
    monkeypatch.setattr(debuglog, "event", lambda *args, **fields: seen.append((args, fields)))
    KeyInput().post(VOLUME_UP)
    assert seen and seen[0][0][:2] == ("key", "ignored") and seen[0][1]["vk"] == VOLUME_UP


def test_the_master_key_list_documents_the_keys_of_windows_in_both_modes():
    row = K.BY_ID["windows_keys"]
    assert row.modes == "all" and row.f5 and "volume" in row.f5
    assert row.f5 in K.help_lines(K.KEY_F5, "classic") and row.f5 in K.help_lines(K.KEY_F5, "nfl")
    assert any(line.startswith(" The volume, mute and media keys. Anywhere.") for line in K.help_lines(K.KEY_F6, "classic"))
    assert "**The volume, mute and media keys**" in K.readme_text()


win32api = pytest.importorskip("win32api")
win32con = pytest.importorskip("win32con")

from nfl4.ui import window as window_module  # noqa: E402


def test_the_log_names_the_keys_of_windows():
    assert [window_module.key_name(code) for code in (VOLUME_UP, VOLUME_DOWN, MUTE, 179)] == \
           ["VolumeUp", "VolumeDown", "VolumeMute", "MediaPlayPause"]
    assert all(not window_module.key_name(code).startswith("vk") for code in WINDOWS_KEYS)


@pytest.mark.window
def test_the_window_hands_the_keys_of_windows_back_to_windows_and_the_game_never_gets_them(monkeypatch):
    real = window_module.user32.DefWindowProcW
    handed = []

    def recording(hwnd, msg, wparam, lparam):
        if msg in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
            handed.append(int(wparam))
        return real(hwnd, msg, wparam, lparam)

    monkeypatch.setattr(window_module.user32, "DefWindowProcW", recording)
    logged = []
    real_event = debuglog.event
    monkeypatch.setattr(debuglog, "event", lambda *args, **fields: (logged.append((args, fields)), real_event(*args, **fields)))
    got = []
    window = window_module.GameWindow(got.append, lambda: None)

    def send():
        time.sleep(0.05)
        for code in (VOLUME_UP, 40, VOLUME_DOWN, MUTE, 13):
            win32api.PostMessage(window.handle, win32con.WM_KEYDOWN, code, 0)
        time.sleep(0.3)
        window.close()

    threading.Thread(target=send, daemon=True).start()
    safety = threading.Timer(5.0, window.close)
    safety.start()
    window.run()
    safety.cancel()
    assert got == [40, 13]
    assert handed == [VOLUME_UP, VOLUME_DOWN, MUTE]
    downs = [fields for args, fields in logged if args[:2] == ("key", "down")]
    assert [(f["name"], f.get("to")) for f in downs] == [("VolumeUp", "windows"), ("Down", None), ("VolumeDown", "windows"),
                                                        ("VolumeMute", "windows"), ("Enter", None)]
