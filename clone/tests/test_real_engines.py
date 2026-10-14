"""Real SAPI 5 (volume 0, silent) and the real NVDA DLL (never speaks). This is inspired by Jim Kitchen's Brain.

Run in both builds: 64-bit and 32-bit Python. Skips itself where SAPI or the DLL is missing.
"""
import os
import struct
import time

import pytest

from nfl4.speech.nvda import NvdaBackend, dll_path
from nfl4.speech.sapi5 import SapiBackend
from nfl4.speech.voices import VoiceCatalog

win32com = pytest.importorskip("win32com.client")


@pytest.fixture
def silent_sapi():
    backend = SapiBackend(volume=0)
    started = backend.start()
    if not started.ok:
        pytest.skip(f"SAPI 5 not usable here: {started.error}")
    yield backend, started
    backend.close()


@pytest.mark.sapi
def test_first_voice_is_sapi_item_0(silent_sapi):
    _, started = silent_sapi
    first = win32com.Dispatch("SAPI.SpVoice").GetVoices("", "").Item(0)
    assert started.voice_id == first.Id and started.voice_name == first.GetDescription()


@pytest.mark.sapi
def test_speak_waits_for_real_end_of_speech(silent_sapi):
    backend, _ = silent_sapi
    start = time.monotonic()
    backend.speak("My Brain by Josh Kennedy, inspired by Jim Kitchen.")
    assert time.monotonic() - start < 0.1
    backend.wait_until_done()
    took = time.monotonic() - start
    assert 0.3 < took < 10, took


@pytest.mark.sapi
def test_stop_cuts_speech_at_once(silent_sapi):
    backend, _ = silent_sapi
    backend.speak("This is a long sentence that would take several seconds to speak in full. " * 3)
    time.sleep(0.2)
    start = time.monotonic()
    backend.stop()
    backend.wait_until_done()
    assert time.monotonic() - start < 0.3


@pytest.mark.sapi
def test_pitch_markup_is_accepted(silent_sapi):
    backend, _ = silent_sapi
    backend.set_pitch(5)
    start = time.monotonic()
    backend.speak("pitch test & <markup>")
    backend.wait_until_done()
    assert time.monotonic() - start > 0.2   # spoken, not rejected as bad XML


@pytest.mark.sapi
def test_voice_list_matches_sapi_count():
    catalog = VoiceCatalog()
    voices = catalog.voices(timeout=30)
    count = win32com.Dispatch("SAPI.SpVoice").GetVoices("", "").Count
    assert len(voices) + catalog.broken == count
    assert voices and voices[0].index == 0


@pytest.mark.sapi
def test_switch_to_last_voice_by_id(silent_sapi):
    backend, _ = silent_sapi
    voices = VoiceCatalog().voices(timeout=30)
    last = voices[-1]
    backend.set_voice(last.voice_id)
    backend.speak("x")
    backend.wait_until_done()
    assert backend.started.voice_id == last.voice_id


@pytest.mark.nvda
def test_nvda_dll_for_this_bitness_loads_without_speaking():
    path = dll_path()
    assert os.path.exists(path)
    assert ("x64" if struct.calcsize("P") == 8 else "x86") in path
    backend = NvdaBackend()
    running = backend.is_available()          # only asks whether NVDA runs
    assert backend._dll is not None
    assert running in (True, False)


@pytest.mark.sapi
def test_a_voice_saved_in_settings_txt_comes_back_and_a_missing_one_falls_back(silent_sapi, tmp_path):
    from nfl4.data.settingsfile import VOICE_MISSING_NOTICE, SettingsStore
    _, first = silent_sapi
    voices = VoiceCatalog()
    voices.load_async()
    listed = voices.voices(timeout=20)
    other = next((v for v in listed if v.voice_id != first.voice_id), None)
    if other is None:
        pytest.skip("only one voice installed")
    store = SettingsStore(str(tmp_path))
    store.load()
    store.settings.speech.voice_id = other.voice_id
    store.save()
    again = SettingsStore(str(tmp_path))
    saved = again.load().speech.voice_id
    backend = SapiBackend(voice_id=saved, volume=0)
    started = backend.start()
    try:
        assert started.ok and started.voice_id == other.voice_id and started.voice_name == other.name
        again.note_voice_fallback(saved, started.voice_id)
        assert again.take_notices() == []
    finally:
        backend.close()
    missing = SapiBackend(voice_id=r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\NoSuchVoice", volume=0)
    started = missing.start()
    try:
        assert started.ok and started.voice_id == first.voice_id           # the first voice, never silence
        again.note_voice_fallback(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\NoSuchVoice", started.voice_id)
        assert again.take_notices() == [VOICE_MISSING_NOTICE]
    finally:
        missing.close()


@pytest.fixture
def silent_rendered_sapi():
    backend = SapiBackend(volume=0, render=True)
    started = backend.start()
    if not started.ok:
        pytest.skip(f"SAPI 5 not usable here: {started.error}")
    yield backend
    backend.close()


@pytest.mark.sapi
def test_rendered_speech_waits_for_the_real_end_of_speech(silent_rendered_sapi):
    backend = silent_rendered_sapi
    if backend._player is None:
        pytest.skip("no audio device for rendered speech here")
    start = time.monotonic()
    backend.speak("My Brain by Josh Kennedy, inspired by Jim Kitchen.")
    assert time.monotonic() - start < 0.1
    backend.wait_until_done()
    assert 0.3 < time.monotonic() - start < 10


@pytest.mark.sapi
def test_rendered_stop_and_next_item_start_fast(silent_rendered_sapi):
    """The arrow-key case: stop plus the next item must start within 250 ms, whatever the voice does."""
    backend = silent_rendered_sapi
    if backend._player is None:
        pytest.skip("no audio device for rendered speech here")
    backend.speak("Speech settings. Seven items. Voice.")
    time.sleep(0.15)
    worst = 0.0
    for text in ("Speech rate", "Speech volume", "Speech pitch", "Speech output", "Restore", "Folder") * 2:
        before = backend.last_start_at
        t0 = time.monotonic()
        backend.stop()
        backend.speak(text)
        while backend.last_start_at == before and time.monotonic() - t0 < 2:
            time.sleep(0.001)
        assert backend.last_start_at != before, f"{text!r} never started"
        worst = max(worst, backend.last_start_at - t0)
        time.sleep(0.08)
    backend.stop()
    assert worst < 0.25, worst


@pytest.mark.sapi
def test_every_real_voice_has_an_engine_and_the_engine_list_covers_them_all():
    from nfl4.speech.voices import enumerate_voices, group_by_engine
    voices, broken = enumerate_voices()
    if not voices:
        pytest.skip("no SAPI 5 voices here")
    assert all(v.engine for v in voices)
    groups = group_by_engine(voices)
    assert sum(len(vs) for _, vs in groups) == len(voices)
    assert len({e for e, _ in groups}) == len(groups)
