"""settings.txt: format, validation, saving and loading. This is inspired by Jim Kitchen's Brain.

Damage handling of the file in every shape is in test_self_healing.py.
"""
import os

import pytest

from nfl4.data.settings import Settings
from nfl4.data.settingsfile import (FILE_NAME, FORMAT_VERSION, IN_USE_NOTICE, UNWRITABLE_NOTICE,
                                     VOICE_MISSING_NOTICE, SettingsFormatError, SettingsStore, parse, render)


def changed() -> Settings:
    s = Settings.defaults()
    s.speech.voice_id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0"
    s.speech.rate = -3
    s.speech.volume = 70
    s.speech.pitch = 4
    s.speech.mode = "auto"
    s.audio.effects_volume = 40
    s.audio.pitch_spread = 8
    return s


def same(a: Settings, b: Settings) -> bool:
    return a.speech == b.speech and a.audio == b.audio


def test_defaults_render_and_parse_back_to_the_original_values():
    settings, problems = parse(render(Settings.defaults()))
    assert problems == [] and same(settings, Settings.defaults())
    assert settings.speech.rate is None and settings.speech.voice_id is None and settings.speech.volume == 90
    assert settings.audio.effects_volume == 100 and settings.audio.pitch_spread == 20


def test_changed_values_round_trip_with_a_voice_note():
    text = render(changed(), "Microsoft David Desktop")
    assert "# The voice below is: Microsoft David Desktop" in text
    settings, problems = parse(text)
    assert problems == [] and same(settings, changed())


def test_header_carries_the_format_version_and_plain_word_notes():
    text = render(Settings.defaults())
    assert text.startswith(f"# Brain settings, format {FORMAT_VERSION}.")
    assert "original" in text and "Notepad" in text


def test_every_value_is_checked_and_a_bad_one_keeps_the_original():
    text = "\n".join(["# Brain settings, format 1", "speech_volume = loud", "speech_pitch = 99", "speech_rate = fast",
                      "speech_output = telepathy", "sound_volume = -5", "pitch_variation = 21",
                      "colour = red", "no equals sign here", "speech_volume = 55"])
    settings, problems = parse(text)
    assert len(problems) == 8
    assert settings.speech.volume == 55 and settings.speech.pitch == 0 and settings.speech.rate is None
    assert settings.speech.mode == "sapi" and settings.audio.effects_volume == 100 and settings.audio.pitch_spread == 20


def test_notepad_friendly_variations_are_accepted():
    text = "﻿SPEECH_VOLUME=  80 %\n  Speech_Output = Automatic  \nspeech_rate = Original\n\n\tpitch_variation = 4\n"
    settings, problems = parse(text)
    assert settings.speech.volume == 80 and settings.speech.mode == "auto" and settings.speech.rate is None
    assert settings.audio.pitch_spread == 4 and problems == []


def test_a_value_may_contain_equals_signs_and_spaces_in_the_voice():
    settings, _ = parse("speech_voice = HKEY\\Some Voice=3\n")
    assert settings.speech.voice_id == "HKEY\\Some Voice=3"


def test_empty_voice_and_rate_mean_the_originals():
    settings, problems = parse("speech_voice =\nspeech_rate =\n")
    assert problems == [] and settings.speech.voice_id is None and settings.speech.rate is None


@pytest.mark.parametrize("text", ["", "  \n\n", "# Brain settings, format 9\nspeech_volume = 5\n", "just words\nmore words\n",
                                  "speech_volumee = 5\nfoo = bar\n"])
def test_unusable_files_raise(text):
    with pytest.raises(SettingsFormatError):
        parse(text)


def test_comments_only_file_is_fine_and_means_all_original():
    settings, problems = parse("# I commented everything out\n")
    assert problems == [] and same(settings, Settings.defaults())


def test_a_setting_given_twice_uses_the_last_and_reports_it():
    settings, problems = parse("# Brain settings, format 1\nspeech_volume = 10\nspeech_volume = 20\n")
    assert settings.speech.volume == 20 and len(problems) == 1


# ----- the store -----

def test_first_start_creates_the_file_with_the_original_values(tmp_path):
    store = SettingsStore(str(tmp_path / "Brain"))
    settings = store.load()
    assert same(settings, Settings.defaults()) and store.take_notices() == []
    assert os.path.isfile(store.path) and os.path.basename(store.path) == FILE_NAME


def test_saved_settings_come_back_at_the_next_start(tmp_path):
    store = SettingsStore(str(tmp_path))
    store.load()
    store.settings.speech.volume = 30
    store.settings.speech.mode = "nvda"
    store.settings.audio.pitch_spread = 6
    assert store.save() is True
    again = SettingsStore(str(tmp_path))
    assert again.load().speech.volume == 30 and again.settings.speech.mode == "nvda"
    assert again.settings.audio.pitch_spread == 6 and again.take_notices() == []


def test_save_writes_the_voice_name_note_when_a_voice_is_chosen(tmp_path):
    store = SettingsStore(str(tmp_path), voice_name=lambda: "Zira")
    store.load()
    store.settings.speech.voice_id = "token-7"
    store.save()
    with open(store.path, encoding="utf-8") as handle:
        text = handle.read()
    assert "# The voice below is: Zira" in text and "speech_voice = token-7" in text


def test_a_failing_voice_name_never_stops_saving(tmp_path):
    def boom():
        raise RuntimeError("voice list not ready")

    store = SettingsStore(str(tmp_path), voice_name=boom)
    store.load()
    store.settings.speech.voice_id = "token-7"
    assert store.save() is True


def test_partly_bad_file_is_kept_reported_once_and_values_still_used(tmp_path):
    (tmp_path / FILE_NAME).write_text("# Brain settings, format 1\nspeech_volume = 55\nspeech_pitch = banana\n", encoding="utf-8")
    store = SettingsStore(str(tmp_path))
    settings = store.load()
    assert settings.speech.volume == 55 and settings.speech.pitch == 0
    assert store.take_notices() == ["1 problem found in settings.txt, details are in the log."]
    assert store.take_notices() == [] and len(store.problems) == 1
    assert not (tmp_path / (FILE_NAME + ".damaged1")).exists()


def test_unwritable_folder_runs_from_memory_and_says_so_once(tmp_path):
    blocker = tmp_path / "Brain"
    blocker.write_text("a file where the folder should be")
    store = SettingsStore(str(blocker))
    settings = store.load()
    assert same(settings, Settings.defaults())
    assert store.take_notices() == [UNWRITABLE_NOTICE]
    settings.speech.volume = 10
    assert store.save() is False and store.save() is False
    assert store.take_notices() == []                       # once per run
    assert "Roaming" in UNWRITABLE_NOTICE and "Kitchensinc Revival" in UNWRITABLE_NOTICE


def test_saving_works_again_when_the_folder_becomes_writable(tmp_path):
    blocker = tmp_path / "Brain"
    blocker.write_text("in the way")
    store = SettingsStore(str(blocker))
    store.load()
    store.take_notices()
    blocker.unlink()
    assert store.save() is True and (blocker / FILE_NAME).is_file()


def test_voice_fallback_notice_only_when_a_saved_voice_is_not_the_one_in_use(tmp_path):
    store = SettingsStore(str(tmp_path))
    store.note_voice_fallback(None, "token-0")
    store.note_voice_fallback("TOKEN-3", "token-3")
    assert store.take_notices() == []
    store.note_voice_fallback("token-9", "token-0")
    assert store.take_notices() == [VOICE_MISSING_NOTICE]


def test_voice_that_vanished_keeps_the_saved_choice_in_the_file(tmp_path):
    s = Settings.defaults()
    s.speech.voice_id = "token-9"
    (tmp_path / FILE_NAME).write_text(render(s), encoding="utf-8")
    store = SettingsStore(str(tmp_path))
    store.load()
    store.settings.speech.volume = 80
    store.save()
    with open(store.path, encoding="utf-8") as handle:
        assert "speech_voice = token-9" in handle.read()       # reinstalling the voice brings it back


def test_notice_texts_are_short_plain_sentences():
    for text in (IN_USE_NOTICE, UNWRITABLE_NOTICE, VOICE_MISSING_NOTICE):
        assert text.endswith(".") and len(text) < 220


def test_a_file_or_folder_that_vanishes_mid_game_is_recreated_at_the_next_save(tmp_path):
    import shutil
    store = SettingsStore(str(tmp_path / "a" / "Brain"))
    store.load()
    store.settings.speech.volume = 45
    shutil.rmtree(tmp_path / "a")
    assert store.save() is True and store.take_notices() == []
    assert SettingsStore(str(tmp_path / "a" / "Brain")).load().speech.volume == 45     # from the copy kept in memory
