"""The screen reader is found and the player is asked once, not made to pick voices (CLAUDE.md 0.28; SZ.4, D-109). This is inspired by Jim Kitchen.

A player's e-mail (2026-10-22): "Screen reader is not detected automatically. You are still asked to pick the voice. It should say: you are running
NVDA or JAWS, do you want to use this voice?" The default speech output was "sapi" (the five voices are part of the game); it is "auto" now (NVDA or
JAWS when one runs, else the five SAPI voices). When a screen reader runs and the player has not said how the game speaks, the game says which one
it found and asks, in the original's yes or no way, whether it should speak through it: yes asks for no voice, no uses the Windows voices. The answer
is saved and the question is never asked again; F9, Speech settings changes it. F12 and the F9 item for the voices say why they have nothing to choose
when a screen reader speaks. A settings file of the old default (sapi, never chosen) becomes automatic once.
"""
import types

from nfl4.data import settingsfile
from nfl4.data.settings import Settings, SpeechSettings
from nfl4.extras.broadcast import Broadcast
from nfl4.game import extra_texts as words
from nfl4.game import help_texts as H
from nfl4.game import texts
from nfl4.speech.voices import VoiceInfo
from programrig import DOWN, ENTER, ESC, preset_season, program_rig, said
from test_program_start import EXIT_KEYS, WEEK_1, Catalog

VOICES = [VoiceInfo(0, "id0", "Alpha", "EngA"), VoiceInfo(1, "id1", "Beta", "EngA")]
QUESTION = words.SCREEN_READER_QUESTION % "NVDA"


def unchosen(rig, mode="auto"):
    speech = rig.game.options.settings.speech
    speech.mode, speech.mode_chosen = mode, False
    rig.game.speech.mode = mode
    return speech


def started(tmp_path, answers, first=False, nvda_running=True, mode="auto", catalog=True):
    rig = program_rig(tmp_path, answers, first=first, preset=preset_season(), mode=mode, nvda_running=nvda_running)
    rig.game.pause_log = []
    speech = unchosen(rig, mode)
    if catalog:
        rig.game.options.voice_catalog = Catalog(VOICES)
    return rig, speech


# ----- the setting -----

def test_the_default_is_automatic_and_the_choice_is_saved_and_read_back():
    settings = Settings.defaults()
    assert settings.speech.mode == "auto" and settings.speech.mode_chosen is False == SpeechSettings().mode_chosen
    text = settingsfile.render(settings)
    assert "speech_output = auto\nspeech_output_chosen = no\n" in text
    settings.speech.mode_chosen, settings.speech.mode = True, "sapi"
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert (again.speech.mode, again.speech.mode_chosen, problems) == ("sapi", True, [])


def test_a_file_of_the_old_default_becomes_automatic_once_and_a_chosen_sapi_stays():
    text = settingsfile.render(Settings.defaults())
    old = text.replace("speech_output = auto\nspeech_output_chosen = no\n", "speech_output = sapi\n")
    read, problems = settingsfile.parse(old)
    assert (read.speech.mode, read.speech.mode_chosen, problems) == ("auto", False, [])
    chosen = text.replace("speech_output = auto\nspeech_output_chosen = no\n", "speech_output = sapi\nspeech_output_chosen = yes\n")
    read, _ = settingsfile.parse(chosen)
    assert (read.speech.mode, read.speech.mode_chosen) == ("sapi", True)
    nvda = old.replace("speech_output = sapi", "speech_output = nvda")
    assert settingsfile.parse(nvda)[0].speech.mode == "nvda"
    bad, problems = settingsfile.parse(text.replace("speech_output_chosen = no", "speech_output_chosen = maybe"))
    assert bad.speech.mode_chosen is False and any("speech_output_chosen" in p for p in problems)


# ----- the question -----

def test_with_nvda_running_the_first_start_asks_once_and_yes_asks_for_no_voice(tmp_path):
    rig, speech = started(tmp_path, [ENTER] + EXIT_KEYS, first=True)
    rig.run()
    spoken = rig.nvda.spoken()
    assert spoken[:2] == [" ", texts.TITLE_SPOKEN] and QUESTION in spoken
    assert spoken.index(QUESTION) < spoken.index(H.SPECIAL_KEYS)                    # before the key list and before any voice
    assert " yes " in spoken and words.SCREEN_READER_YES % "NVDA" in spoken
    assert [t for t in spoken if t.startswith("Choose the voice")] == [] and rig.said == []
    assert (speech.mode, speech.mode_chosen) == ("auto", True) and rig.game.speech.mode == "auto"


def test_no_uses_the_windows_voices_and_the_first_start_then_asks_for_them(tmp_path):
    rig, speech = started(tmp_path, ["n"] + [ESC] * 5 + EXIT_KEYS, first=True)
    rig.run()
    assert QUESTION in rig.nvda.spoken() and words.SCREEN_READER_NO in said(rig) + rig.nvda.spoken()
    assert (speech.mode, speech.mode_chosen) == ("sapi", True) and rig.game.speech.mode == "sapi"
    assert [t.split(".")[0] for t in said(rig) if t.startswith("Choose the voice for")][:2] == [
        "Choose the voice for the announcer", "Choose the voice for your quarterback"]


def test_a_later_start_asks_once_and_never_again(tmp_path):
    rig, speech = started(tmp_path, [ENTER] + EXIT_KEYS)
    rig.run()
    spoken = rig.nvda.spoken()
    assert spoken.index(texts.TITLE_SPOKEN) < spoken.index(QUESTION) < spoken.index(WEEK_1) and speech.mode_chosen is True
    again, _ = started(tmp_path / "again", EXIT_KEYS)
    again.game.options.settings.speech.mode_chosen = True
    again.run()
    assert QUESTION not in again.nvda.spoken() + said(again)


def test_without_a_screen_reader_nothing_is_asked_and_the_voices_are_the_games(tmp_path):
    rig, speech = started(tmp_path, [ESC] * 5 + EXIT_KEYS, first=True, nvda_running=False)
    rig.run()
    assert QUESTION not in said(rig) + rig.nvda.spoken() and rig.nvda.spoken() == []
    assert speech.mode_chosen is False                                                # asked later, when a screen reader runs
    assert len([t for t in said(rig) if t.startswith("Choose the voice for")]) == 5


def test_the_question_is_not_asked_of_a_player_who_chose_sapi_or_already_chose(tmp_path):
    rig, speech = started(tmp_path, EXIT_KEYS)
    speech.mode_chosen = True
    rig.run()
    assert QUESTION not in rig.nvda.spoken() + said(rig)
    rig2, speech2 = started(tmp_path / "sapi", EXIT_KEYS, mode="sapi")
    rig2.run()
    assert QUESTION not in said(rig2) + rig2.nvda.spoken()


def test_jaws_is_named_when_it_is_the_one_that_runs(tmp_path):
    rig = program_rig(tmp_path, [ENTER] + EXIT_KEYS, preset=preset_season(), mode="auto", nvda_running=False)
    rig.jaws = rig.speech.jaws = rig.nvda.__class__("JAWS", available=True, clock=rig.clock, sleep=rig.clock.sleep)
    unchosen(rig)
    rig.run()
    assert words.SCREEN_READER_QUESTION % "JAWS" in rig.jaws.spoken()


# ----- the voices -----

def test_f12_and_the_voices_item_say_why_when_a_screen_reader_speaks(tmp_path):
    rig, _ = started(tmp_path, [])
    rig.game.hotkeys.change_voice()
    assert rig.nvda.spoken()[-1] == words.SCREEN_READER_VOICES and rig.keys.code_text == "112"
    assert [t for t in rig.nvda.spoken() if t.startswith("Choose the voice")] == []
    rig2, _ = started(tmp_path / "sapi", [ESC] * 5, nvda_running=False)
    rig2.game.hotkeys.change_voice()
    assert len([t for t in said(rig2) if t.startswith("Choose the voice for")]) == 5


def test_the_color_commentator_gets_no_saved_voice_while_a_screen_reader_speaks():
    class Catalog2:
        loaded = False
        started = 0

        def load_async(self):
            self.started += 1

    catalog = Catalog2()
    options = types.SimpleNamespace(voice=lambda role: None, voice_catalog=catalog)
    for speaks, expected in ((True, 0), (False, 1)):
        game = types.SimpleNamespace(options=options, speech=types.SimpleNamespace(screen_reader_speaks=lambda s=speaks: s))
        broadcast = Broadcast(None, analyst=True)
        broadcast.game = game
        broadcast._own_voice()
        assert catalog.started == expected
        catalog.started = 0


def test_the_speech_manager_knows_when_a_screen_reader_speaks(tmp_path):
    rig = program_rig(tmp_path, [], mode="auto", nvda_running=True)
    assert rig.speech.screen_reader_speaks() is True
    rig = program_rig(tmp_path / "b", [], mode="auto", nvda_running=False)
    assert rig.speech.screen_reader_speaks() is False
    rig = program_rig(tmp_path / "c", [], mode="sapi", nvda_running=True)
    assert rig.speech.screen_reader_speaks() is False
