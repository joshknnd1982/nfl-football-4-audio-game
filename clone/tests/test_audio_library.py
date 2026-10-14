"""Sound library: the resolution chain and the pool. This is inspired by Jim Kitchen."""
import os
import shutil

import pytest

from nfl4.audio.library import SoundLibrary, shipped_sounds_dir, sound_id
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
from wavmaker import sine, write

DATA = os.path.join(os.path.dirname(__file__), "data")


def make_library(tmp_path, shipped_count=3):
    shipped = tmp_path / "shipped"
    player = tmp_path / "player"
    shipped.mkdir(parents=True, exist_ok=True)
    for number in range(1, shipped_count + 1):
        write(shipped / f"brain{number}.wav", sine(200 * number, 0.02, 11025), rate=11025)
    return SoundLibrary(str(shipped), str(player)), shipped, player


def peak(pick):
    return pick.sound.peak / 32768.0


def test_real_shipped_set_has_42_sounds_and_matches_the_files():
    lib = SoundLibrary(shipped_sounds_dir(), None)
    assert lib.pool_size() == 42
    for number in range(1, 43):
        pick = lib.pick_number(number)
        assert pick.source == "original" and pick.sound is not None
        assert pick.size == os.path.getsize(pick.path) and pick.sound_id == sound_id(number)
    assert lib.pick("brain36").rate == 5564 and lib.pick("BRAIN08").rate == 44100


def test_ids_accept_both_spellings():
    lib = SoundLibrary(shipped_sounds_dir(), None)
    assert lib.pick("brain5") is lib.pick("brain05") is lib.pick_number(5)


def test_player_file_overrides_the_original(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    original = lib.pick_number(2)
    assert original.source == "original"
    write(player / "brain2.wav", sine(900, 0.05, 22050), rate=22050)
    lib.refresh()
    mine = lib.pick_number(2)
    assert mine.source == "player" and mine.rate == 22050 and mine.sound.frames == 1102
    assert lib.pick_number(1).source == "original"          # others untouched


def test_player_file_names_padded_and_any_case_and_other_formats(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    write(player / "BRAIN03.WAV", sine(900, 0.05, 22050), rate=22050)
    write(player / "Brain1.Wav", sine(500, 0.05, 8000), rate=8000)
    lib.refresh()
    assert lib.pick_number(3).source == "player" and lib.pick_number(3).rate == 22050
    assert lib.pick_number(1).source == "player" and lib.pick_number(1).rate == 8000


def test_unpadded_name_wins_over_padded_and_wav_over_other_types(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    write(player / "brain1.wav", sine(500, 0.05, 8000), rate=8000)
    write(player / "brain01.wav", sine(500, 0.05, 16000), rate=16000)
    lib.refresh()
    assert lib.pick_number(1).rate == 8000


def test_ogg_flac_mp3_player_files_play_when_the_mixer_is_running(tmp_path, monkeypatch):
    import pygame
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.mixer.init(44100, -16, 2, 256)
    try:
        for number, ext in ((1, "ogg"), (2, "flac"), (3, "mp3")):
            lib, shipped, player = make_library(tmp_path / ext)
            player.mkdir(parents=True, exist_ok=True)
            shutil.copy(os.path.join(DATA, f"tone.{ext}"), player / f"brain{number}.{ext}")
            lib.refresh()
            pick = lib.pick_number(number)
            assert pick.source == "player" and pick.rate == 44100, ext
    finally:
        pygame.mixer.quit()


def test_sounds_txt_can_name_another_file_trim_volume_and_switch_off(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    write(player / "my best bell.wav", sine(900, 0.05, 22050), rate=22050)
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "brain1 = file=My Best Bell.wav; volume=50\nbrain2 = off\nbrain3 = volume=25\n",
                                    encoding="utf-8")
    lib.refresh()
    one, two, three = lib.pick_number(1), lib.pick_number(2), lib.pick_number(3)
    assert one.source == "player" and one.rate == 22050 and one.volume == 0.5
    assert two.source == "off" and two.sound is not None and not any(two.sound.pcm)
    assert two.sound.frames == 220 and two.size == os.path.getsize(shipped / "brain2.wav")   # keeps its place and length
    assert three.source == "original" and three.volume == 0.25


def test_sounds_txt_naming_a_missing_file_falls_back_and_is_reported(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "brain1 = file=nothing.wav\n", encoding="utf-8")
    lib.refresh()
    assert lib.pick_number(1).source == "original"
    assert any("nothing.wav" in p for p in lib.problems)


@pytest.mark.parametrize("damage", [b"", b"RIFF junk", os.urandom(300)])
def test_damaged_player_file_falls_back_to_the_original_and_speaks_once(tmp_path, damage):
    lib, shipped, player = make_library(tmp_path)
    player.mkdir(parents=True, exist_ok=True)
    (player / "brain2.wav").write_bytes(damage)
    lib.refresh()
    pick = lib.pick_number(2)
    assert pick.source == "original" and pick.size == os.path.getsize(shipped / "brain2.wav")
    notices = lib.take_notices()
    assert len(notices) == 1 and "skipped" in notices[0]
    lib.refresh()
    lib.pick_number(2)
    assert lib.take_notices() == []                       # once per damaged file state
    assert any("brain2.wav" in p for p in lib.problems)   # but still listed for "check files"


def test_nothing_playable_gives_the_originals_failure_path_facts(tmp_path):
    """GAME_SPEC 5.4: an unloadable file still has a size (FileLen worked); a missing one has none."""
    lib, shipped, player = make_library(tmp_path, shipped_count=0)
    player.mkdir(parents=True, exist_ok=True)
    (player / "brain1.wav").write_bytes(b"x" * 77)           # exists, cannot load
    lib.refresh()
    bad, absent = lib.pick_number(1), lib.pick_number(2)
    assert bad.sound is None and bad.size == 77 and bad.source == "none" and bad.rate is None
    assert absent.sound is None and absent.size is None and absent.source == "none"


def test_pool_is_the_highest_consecutive_number(tmp_path):
    lib, shipped, player = make_library(tmp_path, shipped_count=3)
    assert lib.pool_size() == 3
    write(player / "brain4.wav", sine(300, 0.02, 11025), rate=11025)
    lib.refresh()                                              # adding a wav is noticed at the next start
    assert lib.pool_size() == 4
    write(player / "brain6.wav", sine(300, 0.02, 11025), rate=11025)      # gap at 5
    lib.refresh()
    assert lib.pool_size() == 4
    assert any("brain5 is missing" in p and "brain6" in p for p in lib.problems)
    write(player / "brain5.wav", sine(300, 0.02, 11025), rate=11025)
    lib.refresh()
    assert lib.pool_size() == 6
    assert not any("is missing" in p for p in lib.problems)


def test_pool_with_original_style_and_padded_names_and_other_types(tmp_path):
    lib, shipped, player = make_library(tmp_path, shipped_count=2)
    write(player / "brain03.wav", sine(300, 0.02, 11025), rate=11025)
    player.joinpath("brain4.ogg").write_bytes(b"not really audio")      # present even if unusable
    lib.refresh()
    assert lib.pool_size() == 4


def test_empty_pool_is_zero_and_the_logic_uses_one(tmp_path):
    lib, shipped, player = make_library(tmp_path, shipped_count=0)
    assert lib.pool_size() == 0


def test_a_switched_off_sound_still_counts_for_the_pool(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "brain2 = off\n", encoding="utf-8")
    lib.refresh()
    assert lib.pool_size() == 3


def test_beep_exit_chain_player_file_then_generated(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    generated = lib.pick("beep_exit")
    assert generated.source == "generated" and generated.size is None
    assert generated.sound.seconds == pytest.approx(0.080, abs=0.001) and generated.rate == 44100
    write(player / "beep_exit.wav", sine(300, 0.1, 22050), rate=22050)
    lib.refresh()
    assert lib.pick("beep_exit").source == "player"
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "beep_exit = off\n", encoding="utf-8")
    lib.refresh()
    assert lib.pick("beep_exit").source == "off"


def test_unknown_id_is_silent_not_an_error(tmp_path):
    lib, *_ = make_library(tmp_path)
    pick = lib.pick("no_such_sound")
    assert pick.sound is None and pick.source == "none"


def test_deleted_folder_and_sounds_txt_come_back_on_refresh(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    shutil.rmtree(player)
    lib.refresh()
    assert (player / FILE_NAME).is_file()
    assert lib.pool_size() == 3


def test_damaged_sounds_txt_resets_and_tells_the_player(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (player / FILE_NAME).write_bytes(b"\x00\x00\x00 broken")
    lib.refresh()
    notices = lib.take_notices()
    assert any("sounds.txt was damaged" in n for n in notices)
    assert (player / (FILE_NAME + ".damaged1")).exists()


def test_check_all_lists_every_problem(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    (player / "brain2.wav").write_bytes(b"junk")
    lib.refresh()
    problems = lib.check_all()
    assert any("brain2.wav" in p for p in problems)


def test_changed_file_is_decoded_again(tmp_path):
    lib, shipped, player = make_library(tmp_path)
    path = write(player / "brain1.wav", sine(300, 0.02, 11025), rate=11025)
    lib.refresh()
    assert lib.pick_number(1).rate == 11025
    write(player / "brain1.wav", sine(300, 0.03, 8000), rate=8000)
    os.utime(path, (1, 1))                                     # make sure the stamp differs
    lib.refresh()
    assert lib.pick_number(1).rate == 8000
