"""sounds.txt: reading and healing. This is inspired by Jim Kitchen."""
import os

import pytest

from nfl4.audio import soundsconfig
from nfl4.audio.ids import SOUND_IDS, canonical_id, describe, file_stems, foot_number, is_known
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME, load_or_heal, parse
from nfl4.data.healing import save_damaged_copy


def read_back(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def test_the_27_ids_and_their_spellings():
    """SOUND_DESIGN 6: snd_foot0 to snd_foot25 and beep_exit; the original's file names name the same sounds."""
    assert len(SOUND_IDS) == 27 and SOUND_IDS[0] == "snd_foot0" and SOUND_IDS[25] == "snd_foot25"
    assert SOUND_IDS[-1] == "beep_exit"
    for name in ("snd_foot7", "SND_FOOT7", "foot7", "Foot07", " foot7 "):
        assert canonical_id(name) == "snd_foot7" and is_known(name)
    assert not is_known("foot26") and not is_known("brain5") and not is_known("snd_foot")
    assert foot_number("beep_exit") is None and foot_number("foot25") == 25
    assert file_stems("snd_foot7") == ("foot7", "snd_foot7") and file_stems("beep_exit") == ("beep_exit",)
    assert describe("snd_foot7") == "foot7, kick" and describe("foot25") == "foot25, Super Bowl"


def test_default_text_parses_changes_nothing_and_names_every_sound():
    config = parse(DEFAULT_TEXT)
    assert config.entries == {} and config.problems == []
    assert DEFAULT_TEXT.startswith("# NFL Football 4 sounds, format 1.")
    for number in range(26):
        assert f"#   foot{number}: " in DEFAULT_TEXT
    assert "foot7: kick" in DEFAULT_TEXT and "foot13: bleep" in DEFAULT_TEXT


def test_entries_file_volume_off():
    config = parse(DEFAULT_TEXT + "snd_foot7 = file=my kick.wav; volume=80\nFOOT13 = off\nbeep_exit = volume=50%\n")
    assert config.get("snd_foot7").file == "my kick.wav"
    assert config.get("foot7").volume == pytest.approx(0.8)
    assert config.get("snd_foot13").off is True
    assert config.get("beep_exit").volume == pytest.approx(0.5)
    assert config.problems == []


def test_bad_lines_are_skipped_and_counted():
    text = DEFAULT_TEXT + "\n".join([
        "snd_foot5 = volume=abc", "snd_foot6 = volume=500", "snd_foot7 = colour=red",
        "what is this", "unknownsound = off", "foot26 = off", "snd_foot8 = off"]) + "\n"
    config = parse(text)
    assert len(config.problems) == 6
    assert config.get("snd_foot8").off
    assert config.get("snd_foot5").volume == 1.0       # the bad setting is ignored, the line itself stays


def test_unusable_texts_raise_valueerror():
    for bad in ("", "   \n\n", "# NFL Football 4 sounds, format 9\n", "random words\nmore words\n"):
        with pytest.raises(ValueError):
            parse(bad)


def test_comments_only_file_without_header_is_fine():
    assert parse("# I commented everything out\n").entries == {}


def test_missing_folder_and_file_are_recreated(tmp_path):
    folder = tmp_path / "per user" / "sounds"
    config, notices = load_or_heal(str(folder))
    assert read_back(folder / FILE_NAME) == DEFAULT_TEXT
    assert notices == [] and config.entries == {}


@pytest.mark.parametrize("content", [b"", b"\n  \n", b"\x00\x01\x02garbage\xff" * 50,
                                     b"# NFL Football 4 sounds, format 7\nsnd_foot5 = off\n",
                                     b"just some random text\n"])
def test_damaged_file_is_saved_aside_and_reset(tmp_path, content):
    path = tmp_path / FILE_NAME
    path.write_bytes(content)
    config, notices = load_or_heal(str(tmp_path))
    assert config.entries == {}
    assert len(notices) == 1 and "damaged" in notices[0] and "copy was saved" in notices[0]
    assert (tmp_path / (FILE_NAME + ".damaged1")).read_bytes() == content
    assert read_back(path) == DEFAULT_TEXT
    assert load_or_heal(str(tmp_path))[1] == []              # second start: healthy, silent


def test_windows_code_page_file_is_accepted(tmp_path):
    (tmp_path / FILE_NAME).write_bytes("# NFL Football 4 sounds, format 1\nfoot5 = file=caf\xe9.wav\n".encode("cp1252"))
    config, notices = load_or_heal(str(tmp_path))
    assert config.get("snd_foot5").file == "caf\xe9.wav" and notices == []


def test_partly_bad_file_is_kept_and_reported(tmp_path):
    (tmp_path / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot5 = volume=abc\nsnd_foot6 = off\n", encoding="utf-8")
    config, notices = load_or_heal(str(tmp_path))
    assert notices == ["1 problem found in sounds.txt, details are in the log."]
    assert config.get("snd_foot6").off
    assert not (tmp_path / (FILE_NAME + ".damaged1")).exists()


def test_only_the_latest_three_damaged_copies_are_kept(tmp_path):
    path = tmp_path / "file.txt"
    for i in range(6):
        path.write_text(f"version {i}")
        save_damaged_copy(str(path))
    names = sorted(n for n in os.listdir(tmp_path) if "damaged" in n)
    assert names == ["file.txt.damaged4", "file.txt.damaged5", "file.txt.damaged6"]
    assert (tmp_path / "file.txt.damaged6").read_text() == "version 5"


def test_unwritable_location_does_not_raise(tmp_path):
    blocker = tmp_path / "sounds"
    blocker.write_text("a file where the folder should be")
    config, notices = load_or_heal(str(blocker))
    assert config.entries == {}
    assert notices == [soundsconfig.UNWRITABLE_NOTICE] and "NFL Football 4" in notices[0]


def test_format_constants():
    assert soundsconfig.FORMAT_VERSION == 1
