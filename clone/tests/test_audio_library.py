"""Sound library: the resolution chain for the 27 IDs and the sound-file notice. This is inspired by Jim Kitchen.

Playbook 7.7, SOUND_DESIGN 5 and 6, GAP_REGISTER G-A6, D-001 (the shipped files are the originals, proven by hash).
"""
import hashlib
import os
import shutil

import pytest

from nfl4.audio.ids import SOUND_IDS
from nfl4.audio.library import (KIT_SKIPPED_TEXT, ORIGINAL_CORRUPT_TEXT, SOUND_FILE_NOTICE, SoundLibrary,
                                shipped_sounds_dir)
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
from nfl4.data import paths
from wavmaker import sine, write

DATA = os.path.join(os.path.dirname(__file__), "data")
SPEC_HASHES = os.path.join(os.path.dirname(paths.program_dir()), "spec", "ORIGINAL_SHA256.txt")

# WAV_EVENT_MAP 2: channels, bits, rate and length in ms of every original file (measured in S1.1 and S2.3)
SHIPPED_FORMATS = {
    0: (1, 8, 22050, 3405), 1: (2, 16, 22050, 4870), 2: (2, 16, 22050, 2000), 3: (2, 16, 22050, 3081),
    4: (2, 16, 22050, 4300), 5: (2, 16, 22050, 3100), 6: (2, 16, 22050, 2930), 7: (2, 16, 22050, 600),
    8: (2, 16, 22050, 1400), 9: (2, 16, 22050, 1500), 10: (1, 8, 10989, 2162), 11: (2, 16, 22050, 1950),
    12: (2, 16, 22050, 400), 13: (1, 16, 11025, 366), 14: (2, 16, 22050, 2200), 15: (1, 16, 44100, 127),
    16: (1, 16, 44100, 189), 17: (1, 8, 11000, 594), 18: (1, 8, 11025, 339), 19: (1, 8, 8363, 237),
    20: (1, 8, 11000, 201), 21: (1, 16, 44100, 87), 22: (1, 16, 44100, 121), 23: (1, 8, 11025, 250),
    24: (1, 8, 11025, 202), 25: (1, 8, 11025, 11453),
}


def make_library(tmp_path, numbers=(7, 12, 13)):
    """A library over a small shipped folder: foot<n>.wav for each number, 20 ms tones."""
    shipped = tmp_path / "shipped"
    player = tmp_path / "player"
    shipped.mkdir(parents=True, exist_ok=True)
    for number in numbers:
        write(shipped / f"foot{number}.wav", sine(200 + 50 * number, 0.02, 11025), rate=11025)
    return SoundLibrary(str(shipped), str(player)), shipped, player


# ----- the shipped set -----

def test_the_shipped_files_are_the_originals_byte_for_byte():
    """D-001: the 26 wavs in assets\\sounds are the original's, proven by SHA-256 against spec\\ORIGINAL_SHA256.txt."""
    if not os.path.isfile(SPEC_HASHES):
        pytest.skip("the spec folder is not beside this copy of the clone")
    expected = {}
    with open(SPEC_HASHES, encoding="utf-8") as handle:
        for line in handle:
            digest, name = line.split()
            if name.lstrip("*").endswith(".wav"):
                expected[name.lstrip("*")] = digest
    folder = shipped_sounds_dir()
    assert sorted(os.listdir(folder)) == sorted(expected)
    for name, digest in expected.items():
        with open(os.path.join(folder, name), "rb") as handle:
            assert hashlib.sha256(handle.read()).hexdigest() == digest, name


def test_every_id_resolves_to_its_original_with_the_measured_format():
    lib = SoundLibrary(shipped_sounds_dir(), None)
    for number, (channels, _bits, rate, ms) in SHIPPED_FORMATS.items():
        pick = lib.pick(f"snd_foot{number}")
        assert pick.source == "original" and pick.path.endswith(f"foot{number}.wav"), number
        assert pick.sound.channels == channels and pick.rate == rate, number
        assert pick.sound.seconds * 1000 == pytest.approx(ms, abs=1.5), number
    assert lib.pick("beep_exit").source == "generated"
    assert lib.check_all() == [] and lib.take_notices() == []


def test_ids_accept_the_original_file_names():
    lib = SoundLibrary(shipped_sounds_dir(), None)
    assert lib.pick("snd_foot5") is lib.pick("foot5") is lib.pick("FOOT05")


# ----- the chain -----

def test_player_file_overrides_the_original_by_either_name(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    assert lib.pick("snd_foot7").source == "original"
    write(player / "foot7.wav", sine(900, 0.05, 22050), rate=22050)
    write(player / "SND_FOOT12.WAV", sine(900, 0.05, 16000), rate=16000)
    lib.refresh()
    assert lib.pick("snd_foot7").source == "player" and lib.pick("snd_foot7").rate == 22050
    assert lib.pick("snd_foot12").source == "player" and lib.pick("snd_foot12").rate == 16000
    assert lib.pick("snd_foot13").source == "original"                  # others untouched


def test_the_original_file_name_wins_over_the_id_and_wav_over_other_types(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    player.mkdir(parents=True, exist_ok=True)
    write(player / "foot7.wav", sine(500, 0.05, 8000), rate=8000)
    write(player / "snd_foot7.wav", sine(500, 0.05, 16000), rate=16000)
    (player / "foot7.ogg").write_bytes(b"not really audio")
    lib.refresh()
    assert lib.pick("snd_foot7").rate == 8000


def test_a_player_file_for_a_sound_that_ships_none_is_used(tmp_path):
    lib, shipped, player = make_library(tmp_path, numbers=())
    write(player / "foot25.wav", sine(300, 0.05, 11025), rate=11025)
    lib.refresh()
    assert lib.pick("snd_foot25").source == "player"


def test_ogg_flac_mp3_player_files_play_when_the_mixer_is_running(tmp_path, monkeypatch):
    import pygame
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init(44100, -16, 2, 256)
    try:
        for number, ext in ((7, "ogg"), (12, "flac"), (13, "mp3")):
            lib, shipped, player = make_library(tmp_path / ext)
            player.mkdir(parents=True, exist_ok=True)
            shutil.copy(os.path.join(DATA, f"tone.{ext}"), player / f"foot{number}.{ext}")
            lib.refresh()
            pick = lib.pick(f"snd_foot{number}")
            assert pick.source == "player" and pick.rate == 44100, ext
    finally:
        pygame.mixer.quit()


def test_sounds_txt_can_name_another_file_trim_volume_and_switch_off(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    write(player / "my kick.wav", sine(900, 0.05, 22050), rate=22050)
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot7 = file=My Kick.wav; volume=50\nfoot12 = off\n"
                                    "snd_foot13 = volume=25\n", encoding="utf-8")
    lib.refresh()
    kick, contact, bleep = lib.pick("snd_foot7"), lib.pick("snd_foot12"), lib.pick("snd_foot13")
    assert kick.source == "player" and kick.rate == 22050 and kick.volume == 0.5
    assert contact.source == "off" and contact.sound is not None and not any(contact.sound.pcm)
    assert contact.sound.frames == 220                       # keeps its length: the game waits as long
    assert bleep.source == "original" and bleep.volume == 0.25


def test_sounds_txt_naming_a_missing_file_falls_back_and_is_reported_without_a_notice(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot7 = file=nothing.wav\n", encoding="utf-8")
    lib.refresh()
    assert lib.pick("snd_foot7").source == "original"
    assert any("nothing.wav" in p for p in lib.problems)
    assert lib.take_notices() == []                          # a missing file is not a damaged one (G-A6)


@pytest.mark.parametrize("damage", [b"", b"RIFF junk", os.urandom(300)])
def test_damaged_player_file_falls_back_to_the_original_and_speaks_the_notice_once(tmp_path, damage):
    lib, shipped, player = make_library(tmp_path)
    player.mkdir(parents=True, exist_ok=True)
    (player / "foot12.wav").write_bytes(damage)
    lib.refresh()
    pick = lib.pick("snd_foot12")
    assert pick.source == "original"
    assert lib.take_notices() == [SOUND_FILE_NOTICE]
    lib.refresh()
    lib.pick("snd_foot12")
    assert lib.take_notices() == []                       # once per damaged file state
    assert any("foot12.wav" in p for p in lib.problems)   # but still listed for "check files"


def test_the_notice_is_the_authors_unused_sentence_then_the_kits():
    """SOUND_DESIGN 5, GAP_REGISTER 8: the exe's dead string (no spaces around it) and the kit's sentence."""
    assert ORIGINAL_CORRUPT_TEXT == "Sorry but one or more of the wave files seem to be corrupt"
    assert KIT_SKIPPED_TEXT == "A sound file could not be used and was skipped, details are in the log."
    assert SOUND_FILE_NOTICE == ORIGINAL_CORRUPT_TEXT + ". " + KIT_SKIPPED_TEXT


def test_one_notice_per_start_however_many_files_are_bad(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    player.mkdir(parents=True, exist_ok=True)
    for number in (7, 12, 13):
        (player / f"foot{number}.wav").write_bytes(b"junk")
    lib.refresh()
    problems = lib.check_all()
    assert sum("cannot be used" in p for p in problems) == 3
    assert lib.take_notices() == [SOUND_FILE_NOTICE]
    (player / "foot7.wav").write_bytes(b"other junk")         # a new bad state later in the same run
    lib.refresh()
    lib.check_all()
    assert lib.take_notices() == []


def test_a_damaged_shipped_file_or_none_at_all_gives_the_notice_and_silence(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (shipped / "foot7.wav").write_bytes(b"RIFF\x00\x00")
    lib.refresh()
    pick = lib.pick("snd_foot7")
    assert pick.sound is None and pick.source == "none" and pick.rate is None
    assert lib.take_notices() == [SOUND_FILE_NOTICE]
    lib2, *_ = make_library(tmp_path / "second", numbers=(12,))
    assert lib2.pick("snd_foot7").source == "none"           # no file at all: silence, logged, one notice
    assert lib2.take_notices() == [SOUND_FILE_NOTICE]
    assert any("snd_foot7: no usable sound file" in p for p in lib2.problems)


def test_beep_exit_chain_player_file_then_generated(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    generated = lib.pick("beep_exit")
    assert generated.source == "generated"
    assert generated.sound.seconds == pytest.approx(0.080, abs=0.001) and generated.rate == 44100
    write(player / "beep_exit.wav", sine(300, 0.1, 22050), rate=22050)
    lib.refresh()
    assert lib.pick("beep_exit").source == "player"
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "beep_exit = off\n", encoding="utf-8")
    lib.refresh()
    assert lib.pick("beep_exit").source == "off"


def test_unknown_id_is_silent_not_an_error_and_not_a_notice(tmp_path):
    lib, *_ = make_library(tmp_path)
    pick = lib.pick("no_such_sound")
    assert pick.sound is None and pick.source == "none"
    assert lib.take_notices() == []


def test_deleted_folder_and_sounds_txt_come_back_on_refresh(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    shutil.rmtree(player)
    lib.refresh()
    assert (player / FILE_NAME).is_file()
    assert lib.pick("snd_foot7").source == "original"


def test_damaged_sounds_txt_resets_and_tells_the_player(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (player / FILE_NAME).write_bytes(b"\x00\x00\x00 broken")
    lib.refresh()
    notices = lib.take_notices()
    assert any("sounds.txt was damaged" in n for n in notices)
    assert (player / (FILE_NAME + ".damaged1")).exists()


def test_check_all_resolves_all_27_ids(tmp_path):
    lib, shipped, player = make_library(tmp_path, numbers=range(26))
    assert lib.check_all() == []
    assert set(lib._picks) == set(SOUND_IDS)


def test_changed_file_is_decoded_again(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    path = write(player / "foot7.wav", sine(300, 0.02, 11025), rate=11025)
    lib.refresh()
    assert lib.pick("snd_foot7").rate == 11025
    write(player / "foot7.wav", sine(300, 0.03, 8000), rate=8000)
    os.utime(path, (1, 1))                                     # make sure the stamp differs
    lib.refresh()
    assert lib.pick("snd_foot7").rate == 8000
