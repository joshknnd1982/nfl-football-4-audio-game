"""Test setup shared by all test files. This is inspired by Jim Kitchen.

A new clone (made from the starter kit) has no shipped sound files yet: the tests that need them are skipped until
assets\\sounds holds wav files, so a fresh clone starts with a green test run (fixesforgames.md B-X, section C).
"""
import os

import pytest

from nfl4.data import paths

# whole files, and single tests of other files, that read the shipped wav files
NEEDS_SHIPPED_FILES = {"test_audio_engine.py", "test_audio_mixer.py", "test_conformance.py", "test_game_real_sounds.py"}
NEEDS_SHIPPED_TESTS = {
    "test_real_shipped_set_has_42_sounds_and_matches_the_files",
    "test_ogg_flac_mp3_player_files_play_when_the_mixer_is_running",
    "test_real_lengths_at_the_pitch_extremes_match_the_spec",
    "test_every_shipped_wav_renders_at_both_extremes_without_gaining_level",
    "test_every_shipped_wav_loads_and_matches_the_standard_reader",
    "test_ogg_flac_mp3_need_the_mixer_and_decode_with_it",
    "test_twenty_virtual_seconds_on_nine_slots_with_the_real_sounds",
}


def _have_shipped_sounds() -> bool:
    folder = os.path.join(paths.program_dir(), "assets", "sounds")
    return os.path.isdir(folder) and any(name.lower().endswith(".wav") for name in os.listdir(folder))


def pytest_collection_modifyitems(config, items):
    if _have_shipped_sounds():
        return
    skip = pytest.mark.skip(reason="no shipped sounds in assets\\sounds yet (a new clone has none)")
    for item in items:
        if os.path.basename(str(item.fspath)) in NEEDS_SHIPPED_FILES or item.name.split("[")[0] in NEEDS_SHIPPED_TESTS:
            item.add_marker(skip)


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
