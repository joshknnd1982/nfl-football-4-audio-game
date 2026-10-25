"""Test setup shared by all test files. This is inspired by Jim Kitchen.

A new game (made from the starter kit) has no shipped sound files yet: the tests that need them are skipped until
assets\\sounds holds wav files, so a fresh game starts with a green test run (fixesforgames.md B-X, section C).
nfl4 S7.2 copied the 26 original wavs (D-001), so nothing is skipped here any more; the lists name nfl4's tests.
"""
import os

import pytest

from nfl4.data import debuglog, paths

# whole files, and single tests of other files, that read the shipped wav files
NEEDS_SHIPPED_FILES = {"test_audio_engine.py", "test_audio_mixer.py", "test_audio_realdevice.py",
                       "test_game_sounds.py", "test_conformance.py", "test_game_real_sounds.py"}
NEEDS_SHIPPED_TESTS = {
    "test_the_shipped_files_are_the_originals_byte_for_byte",
    "test_every_id_resolves_to_its_original_with_the_measured_format",
    "test_ids_accept_the_original_file_names",
    "test_real_lengths_at_the_pitch_extremes_match_the_spec",
    "test_every_shipped_wav_renders_at_both_extremes_without_gaining_level",
    "test_every_shipped_wav_loads_and_matches_the_standard_reader",
}


def _have_shipped_sounds() -> bool:
    folder = os.path.join(paths.program_dir(), "assets", "sounds")
    return os.path.isdir(folder) and any(name.lower().endswith(".wav") for name in os.listdir(folder))


def pytest_collection_modifyitems(config, items):
    if _have_shipped_sounds():
        return
    skip = pytest.mark.skip(reason="no shipped sounds in assets\\sounds yet (a new game has none)")
    for item in items:
        if os.path.basename(str(item.fspath)) in NEEDS_SHIPPED_FILES or item.name.split("[")[0] in NEEDS_SHIPPED_TESTS:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def close_the_debug_log():
    """A test that starts the whole program (app.main) leaves its debug log open, as the entry point's finish() closes it
    in real life. Closing it after the test keeps its files and thread out of the next test (data/debuglog.py)."""
    yield
    debuglog.shutdown_quietly()


@pytest.fixture(autouse=True)
def no_player_calendars(monkeypatch):
    """D-128: the Franchise reads the player's own schedule_<year>.txt from his customize folder first. A test never reads the real player's folder
    (a calendar the owner downloaded would change what a later season plays); a test of the download points it at its own folder."""
    from nfl4.extras.franchise import fixtures
    monkeypatch.setattr(fixtures, "player_folder", lambda: os.path.join(os.sep, "nfl4-tests-no-player-calendars"))
    yield


@pytest.fixture(autouse=True)
def keep_the_working_directory():
    """The program moves its own working directory out of its folder (data/lifecycle.py); a test that starts the whole
    program must not move the next tests' working directory."""
    here = os.getcwd()
    yield
    try:
        os.chdir(here)
    except OSError:
        pass
