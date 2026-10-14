"""Reset one sound or all to the original (playbook 7.7, 7.10): files moved aside, never deleted.
This is inspired by Jim Kitchen."""
from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.audio.restore import REMOVED_FOLDER, restore_all_sounds, restore_sound
from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
from wavmaker import sine, write


def player_files(folder):
    return sorted(p.name for p in folder.iterdir() if p.is_file())


def test_restore_one_sound_moves_its_own_named_files_and_drops_its_line(tmp_path):
    lib = SoundLibrary(shipped_sounds_dir(), str(tmp_path))
    for name in ("foot7.wav", "SND_FOOT7.ogg", "foot07.wav", "foot12.wav", "my kick.wav"):
        write(tmp_path / name, sine(400, 0.02, 11025), rate=11025)
    (tmp_path / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot7 = file=my kick.wav\nfoot12 = off\n", encoding="utf-8")
    result = restore_sound(str(tmp_path), "foot7")
    assert sorted(result.moved) == ["SND_FOOT7.ogg", "foot7.wav"] and result.entry_removed and not result.failed
    assert player_files(tmp_path) == ["foot07.wav", "foot12.wav", "my kick.wav", FILE_NAME]   # foot07 is no name of it
    assert sorted(p.name for p in (tmp_path / REMOVED_FOLDER).iterdir()) == ["SND_FOOT7.ogg", "foot7.wav"]
    lib.refresh()
    assert lib.pick("snd_foot7").source == "original" and lib.pick("snd_foot12").source == "off"


def test_restore_all_sounds_keeps_a_copy_of_sounds_txt_and_moves_every_own_named_file(tmp_path):
    lib = SoundLibrary(shipped_sounds_dir(), str(tmp_path))
    for name in ("foot0.wav", "snd_foot25.wav", "beep_exit.wav", "crowd loop.wav"):
        write(tmp_path / name, sine(400, 0.02, 11025), rate=11025)
    (tmp_path / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot1 = file=crowd loop.wav\n", encoding="utf-8")
    result = restore_all_sounds(str(tmp_path))
    assert sorted(result.moved) == ["beep_exit.wav", "foot0.wav", "snd_foot25.wav"]
    assert (tmp_path / (FILE_NAME + ".before-reset")).read_text(encoding="utf-8").endswith("crowd loop.wav\n")
    assert (tmp_path / FILE_NAME).read_text(encoding="utf-8") == DEFAULT_TEXT
    lib.refresh()
    assert all(lib.pick(f"snd_foot{n}").source == "original" for n in (0, 1, 25))
    assert lib.pick("beep_exit").source == "generated"
