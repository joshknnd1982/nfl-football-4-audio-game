"""settings.txt: format, validation, saving and loading (nfl4: five voices, five volumes, rate, sound volume, comments).
This is inspired by Jim Kitchen.

GAP_REGISTER G-F8 (the data folder and the kit's settings file, no footbal0.dat or football.vol), GAME_SPEC 4.5 to 4.8
(the original's values: volumes 95, wavol 0, comments on, the voice's own rate).
"""
import os

import pytest

from nfl4.data import paths
from nfl4.data.settings import Settings
from nfl4.data.settingsfile import (FILE_NAME, FORMAT_VERSION, IN_USE_NOTICE, UNWRITABLE_NOTICE,
                                     VOICE_MISSING_NOTICE, SettingsFormatError, SettingsStore, parse, render)
from nfl4.speech.roles import ANNOUNCER, OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER, OWN_QUARTERBACK, ROLES

DAVID = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"


def changed() -> Settings:
    s = Settings.defaults()
    s.speech.voices[ANNOUNCER] = DAVID
    s.speech.voices[OPPONENT_QUARTERBACK] = "HKEY\\Zira"
    s.speech.volumes[OWN_PUNTER] = 70
    s.speech.volumes[OPPONENT_PUNTER] = 0
    s.speech.rate = -3
    s.speech.pitch = 4
    s.speech.mode = "auto"
    s.speech.list_letters = "first"
    s.audio.sound_level = -1200
    s.game.comments = False
    return s


def same(a: Settings, b: Settings) -> bool:
    return a.speech == b.speech and a.audio.sound_level == b.audio.sound_level and a.game == b.game


def test_defaults_are_the_originals_values_and_parse_back():
    s = Settings.defaults()
    assert s.speech.mode == "sapi"                                            # G-S7
    assert s.speech.voices == {role: None for role in ROLES + ("color", "referee")}     # voice 0 for everybody (GAME_SPEC 3 step 4); Ghip and the referee too (SY.1, SY.3)
    assert s.speech.volumes == {role: 95 for role in ROLES + ("color", "referee")}      # volumes 1 to 5 = 95
    assert s.speech.rate is None and s.audio.sound_level == 0 and s.game.comments is True
    settings, problems = parse(render(s))
    assert problems == [] and same(settings, s)


def test_changed_values_round_trip_with_a_voice_note_per_chosen_voice():
    names = {ANNOUNCER: "Microsoft David Desktop", OPPONENT_QUARTERBACK: "Microsoft Zira"}
    text = render(changed(), lambda role: names.get(role, ""))
    assert "# The voice below is: Microsoft David Desktop\nvoice_announcer = " + DAVID in text
    assert "# The voice below is: Microsoft Zira\nvoice_opponent_quarterback = HKEY\\Zira" in text
    assert "voice_own_quarterback = \n" in text
    assert "sound_volume = -12" in text and "comments = off" in text
    settings, problems = parse(text)
    assert problems == [] and same(settings, changed())


def test_header_carries_the_format_version_and_plain_word_notes():
    text = render(Settings.defaults())
    assert text.startswith(f"# NFL Football 4 settings, format {FORMAT_VERSION}.")
    assert "original" in text and "Notepad" in text and "F12" in text and "F11" in text


def test_every_value_is_checked_and_a_bad_one_keeps_the_original():
    text = "\n".join(["# NFL Football 4 settings, format 1", "volume_announcer = loud", "speech_pitch = 99",
                      "speech_rate = fast", "speech_output = telepathy", "sound_volume = 5", "sound_volume = -51",
                      "comments = maybe", "volume_own_punter = 101", "voice_the_referee = x", "colour = red",
                      "no equals sign here", "volume_announcer = 55"])
    settings, problems = parse(text)
    assert len(problems) == 11
    assert settings.speech.volumes[ANNOUNCER] == 55 and settings.speech.volumes[OWN_PUNTER] == 95
    assert settings.speech.pitch == 0 and settings.speech.rate is None and settings.speech.mode == "sapi"
    assert settings.audio.sound_level == 0 and settings.game.comments is True


def test_notepad_friendly_variations_are_accepted():
    text = "\ufeffVOLUME_ANNOUNCER=  80 %\n  Speech_Output = Automatic  \nspeech_rate = Original\n\n\tcomments = OFF\n"
    settings, problems = parse(text)
    assert settings.speech.volumes[ANNOUNCER] == 80 and settings.speech.mode == "auto" and settings.speech.rate is None
    assert settings.game.comments is False and problems == []


def test_a_voice_may_contain_equals_signs_and_spaces_and_empty_means_the_first_voice():
    settings, problems = parse("voice_own_punter = HKEY\\Some Voice=3\nvoice_announcer =\nspeech_rate =\n")
    assert problems == [] and settings.speech.voices[OWN_PUNTER] == "HKEY\\Some Voice=3"
    assert settings.speech.voices[ANNOUNCER] is None and settings.speech.rate is None


def test_sound_volume_is_whole_decibels_down_to_minus_fifty():
    for word, level in (("0", 0), ("-1", -100), ("-50", -5000)):
        settings, problems = parse(f"sound_volume = {word}\n")
        assert problems == [] and settings.audio.sound_level == level


@pytest.mark.parametrize("text", ["", "  \n\n", "# NFL Football 4 settings, format 9\nvolume_announcer = 5\n",
                                  "just words\nmore words\n", "volume_annoucer = 5\nfoo = bar\n"])
def test_unusable_files_raise(text):
    with pytest.raises(SettingsFormatError):
        parse(text)


def test_brains_settings_file_is_not_understood_as_this_games():
    with pytest.raises(SettingsFormatError):
        parse("# Brain settings, format 1\nspeech_volume = 55\nsound_start = early\n")


def test_comments_only_file_is_fine_and_means_all_original():
    settings, problems = parse("# I commented everything out\n")
    assert problems == [] and same(settings, Settings.defaults())


def test_a_setting_given_twice_uses_the_last_and_reports_it():
    settings, problems = parse("# NFL Football 4 settings, format 1\nvolume_announcer = 10\nvolume_announcer = 20\n")
    assert settings.speech.volumes[ANNOUNCER] == 20 and len(problems) == 1


# ----- the store -----

def test_the_data_folder_is_the_games_own_folder_in_appdata(monkeypatch):
    monkeypatch.delenv("NFL4_DATA_DIR", raising=False)
    monkeypatch.setenv("APPDATA", r"C:\Users\someone\AppData\Roaming")
    assert paths.user_data_dir() == r"C:\Users\someone\AppData\Roaming\Kitchensinc Revival\NFL Football 4"
    assert paths.customize_dir().endswith(r"NFL Football 4\customize")
    assert "kitchensinc" not in paths.user_data_dir().lower().replace("kitchensinc revival", "")   # never Documents\kitchensinc
    monkeypatch.setenv("NFL4_DATA_DIR", r"D:\portable")
    assert paths.user_data_dir() == r"D:\portable"


def test_first_start_creates_the_file_with_the_original_values(tmp_path):
    store = SettingsStore(str(tmp_path / "NFL Football 4"))
    settings = store.load()
    assert same(settings, Settings.defaults()) and store.take_notices() == []
    assert os.path.isfile(store.path) and os.path.basename(store.path) == FILE_NAME
    assert not os.path.exists(os.path.join(store.folder, "footbal0.dat"))    # G-F8: not the original's files
    assert not os.path.exists(os.path.join(store.folder, "football.vol"))


def test_saved_settings_come_back_at_the_next_start(tmp_path):
    store = SettingsStore(str(tmp_path))
    store.load()
    store.settings.speech.volumes[OWN_QUARTERBACK] = 30
    store.settings.speech.mode = "nvda"
    store.settings.audio.sound_level = -300
    store.settings.game.comments = False
    assert store.save() is True
    again = SettingsStore(str(tmp_path))
    assert again.load().speech.volumes[OWN_QUARTERBACK] == 30 and again.settings.speech.mode == "nvda"
    assert again.settings.audio.sound_level == -300 and again.settings.game.comments is False
    assert again.take_notices() == []


def test_a_failing_voice_name_never_stops_saving(tmp_path):
    def boom(role):
        raise RuntimeError("voice list not ready")

    store = SettingsStore(str(tmp_path), voice_name=boom)
    store.load()
    store.settings.speech.voices[ANNOUNCER] = "token-7"
    assert store.save() is True
    with open(store.path, encoding="utf-8") as handle:
        assert "voice_announcer = token-7" in handle.read()


def test_partly_bad_file_is_kept_reported_once_and_values_still_used(tmp_path):
    (tmp_path / FILE_NAME).write_text("# NFL Football 4 settings, format 1\nvolume_announcer = 55\nspeech_pitch = banana\n",
                                      encoding="utf-8")
    store = SettingsStore(str(tmp_path))
    settings = store.load()
    assert settings.speech.volumes[ANNOUNCER] == 55 and settings.speech.pitch == 0
    assert store.take_notices() == ["1 problem found in settings.txt, details are in the log."]
    assert store.take_notices() == [] and len(store.problems) == 1
    assert not (tmp_path / (FILE_NAME + ".damaged1")).exists()


def test_an_unusable_file_is_copied_aside_and_reset(tmp_path):
    (tmp_path / FILE_NAME).write_bytes(b"\x00\x01binary junk\x00")
    store = SettingsStore(str(tmp_path))
    settings = store.load()
    assert same(settings, Settings.defaults())
    assert (tmp_path / (FILE_NAME + ".damaged1")).exists()
    assert store.take_notices() == ["settings.txt was damaged and has been reset to the original settings. A copy was saved."]
    assert parse((tmp_path / FILE_NAME).read_text(encoding="utf-8"))[1] == []


def test_unwritable_folder_runs_from_memory_and_says_so_once(tmp_path):
    blocker = tmp_path / "NFL Football 4"
    blocker.write_text("a file where the folder should be")
    store = SettingsStore(str(blocker))
    settings = store.load()
    assert same(settings, Settings.defaults())
    assert store.take_notices() == [UNWRITABLE_NOTICE]
    settings.speech.volumes[ANNOUNCER] = 10
    assert store.save() is False and store.save() is False
    assert store.take_notices() == []                       # once per run
    assert "Roaming" in UNWRITABLE_NOTICE and "Kitchensinc Revival" in UNWRITABLE_NOTICE
    assert "NFL Football 4" in UNWRITABLE_NOTICE


def test_saving_works_again_when_the_folder_becomes_writable(tmp_path):
    blocker = tmp_path / "NFL Football 4"
    blocker.write_text("in the way")
    store = SettingsStore(str(blocker))
    store.load()
    store.take_notices()
    blocker.unlink()
    assert store.save() is True and (blocker / FILE_NAME).is_file()


def test_voice_fallback_notice_only_when_a_saved_voice_is_not_the_one_in_use_and_only_once(tmp_path):
    store = SettingsStore(str(tmp_path))
    store.note_voice_fallback(None, "token-0")
    store.note_voice_fallback("TOKEN-3", "token-3")
    assert store.take_notices() == []
    store.note_voice_fallback("token-9", "token-0")
    store.note_voice_fallback("token-8", "token-0")         # a second missing speaker voice: still one sentence
    assert store.take_notices() == [VOICE_MISSING_NOTICE]


def test_crashed_voice_notice_names_the_game_and_f12(tmp_path):
    store = SettingsStore(str(tmp_path))
    store.note_voice_crashed("SmoothTalker", "FlexVoice2 Bill")
    notice = store.take_notices()[0]
    assert "SmoothTalker" in notice and "NFL Football 4" in notice and "F12" in notice and "Brain" not in notice


def test_voice_that_vanished_keeps_the_saved_choice_in_the_file(tmp_path):
    s = Settings.defaults()
    s.speech.voices[OWN_PUNTER] = "token-9"
    (tmp_path / FILE_NAME).write_text(render(s), encoding="utf-8")
    store = SettingsStore(str(tmp_path))
    store.load()
    store.settings.speech.volumes[ANNOUNCER] = 80
    store.save()
    with open(store.path, encoding="utf-8") as handle:
        assert "voice_own_punter = token-9" in handle.read()       # reinstalling the voice brings it back


def test_notice_texts_are_short_plain_sentences():
    for text in (IN_USE_NOTICE, UNWRITABLE_NOTICE, VOICE_MISSING_NOTICE):
        assert text.endswith(".") and len(text) < 220 and "Brain" not in text


def test_a_file_or_folder_that_vanishes_mid_game_is_recreated_at_the_next_save(tmp_path):
    import shutil
    store = SettingsStore(str(tmp_path / "a" / "NFL Football 4"))
    store.load()
    store.settings.speech.volumes[ANNOUNCER] = 45
    shutil.rmtree(tmp_path / "a")
    assert store.save() is True and store.take_notices() == []
    assert SettingsStore(str(tmp_path / "a" / "NFL Football 4")).load().speech.volumes[ANNOUNCER] == 45
