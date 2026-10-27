"""The settings and files added since the first S8.3, under stress (S8.3 round 2; nfl4 only). This is inspired by Jim Kitchen.

The first S8.3 (2026-10-19) damaged every file of the data folder through the whole program (test_stress_s83_files.py). Since then came: the
commentator's name (`nx_commentator`, SZ.1), the menu hints' count (`nx_menu_hints`, SZ.5), the screen reader question and its saved answer
(`speech_output_chosen`, SZ.4) with the migration of the old default, and the one-time rename of the Washington team in teams.txt (SZ.8, D-120).
Here: hostile values in the settings file (huge, empty, binary, markup, placeholders, accents, other scripts), the settings files of earlier
versions, the screen reader closing between the question and the answer, and teams.txt and its kept copy in every awkward state.
"""
import os

import pytest
import filedamage
from programrig import ENTER
from test_program_start import EXIT_KEYS
from test_sz4_screen_reader import started

from nfl4.data import customize as CU
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import commentators as CO
from nfl4.game import extra_texts as words

# ----- the commentator's name -----

HOSTILE_NAMES = {
    "huge": "Ghip " * 5000,
    "empty": "",
    "control_characters": "Pat\x00\x01\x07Mc\x1bAfee",
    "markup": "<team> <commentator> <n>",
    "placeholder_only": "<commentator>",
    "accents": "José Núñez",
    "other_script": "张伟",
    "symbols_only": "!!! ??? ***",
    "right_to_left": "‮Ghip‬",
    "equals_and_hash": "a = b # c",
}


@pytest.mark.parametrize("role", ["announcer", "analyst", "sideline", "network"])
@pytest.mark.parametrize("kind", sorted(HOSTILE_NAMES))
def test_a_hostile_commentator_name_in_the_settings_file_is_cleaned_or_refused_and_the_file_stays_whole(kind, role):
    # BC.3: every name of the radio crew (and the name the player typed for it) is cleaned the same way
    from nfl4.extras import crew
    hostile = HOSTILE_NAMES[kind].replace("\n", " ")
    text = settingsfile.render(Settings.defaults())
    text = text.replace("nx_%s = %s\n" % (role, crew.DEFAULTS[role]), "nx_%s = %s\n" % (role, hostile))
    text = text.replace("nx_%s_own = \n" % role, "nx_%s_own = %s\n" % (role, hostile))
    assert hostile in text or kind == "empty"
    settings, problems = settingsfile.parse(text)
    name, own = getattr(settings.game, "nx_" + role), getattr(settings.game, "nx_%s_own" % role)
    assert name == CO.clean(name) and 2 <= len(name) <= CO.NAME_MAX                  # stored as it is spoken: safe, short, never empty
    assert own == "" or (own == CO.clean(own) and 2 <= len(own) <= CO.NAME_MAX)
    for value in (name, own):
        assert "<" not in value and ">" not in value and "=" not in value and "#" not in value
    assert crew.name_of(settings.game, role) == name
    again, problems_again = settingsfile.parse(settingsfile.render(settings))       # what the program writes back reads back the same
    assert getattr(again.game, "nx_" + role) == name and getattr(again.game, "nx_%s_own" % role) == own and problems_again == []


def test_an_accented_commentator_name_keeps_its_letters_without_the_accents():
    assert CO.clean("José Núñez") == "Jose Nunez"                       # S8.3 round 2: before, "Jos Nez"
    assert CO.clean("Zoë Müller-Lüdenscheidt") == "Zoe Muller-Ludenscheidt"[:CO.NAME_MAX]
    assert CO.clean("张伟") == ""                                              # no letter a voice is sure to say: the default is kept


def test_the_commentators_name_fills_every_line_that_names_him_and_markup_in_it_never_reaches_the_voice():
    from nfl4.extras import nx_texts as X
    name = CO.clean("<team> Pat")
    lines = [text for text in X.TEXTS.values() if "<commentator>" in text]
    assert lines
    for line in lines:
        said = line.replace("<commentator>", name)
        assert "<commentator>" not in said and "<team>" not in said


# ----- the settings files of earlier versions -----

def older_settings(version):
    """The settings file as version 0.9.0, 0.10.0 or 0.11.0 wrote it: the lines that came later are not in it, and its speech output is the old
    default (sapi) where that version had it."""
    text = settingsfile.render(Settings.defaults())
    crew_lines = tuple("nx_" + role + own for role in ("announcer", "analyst", "sideline", "network") for own in ("", "_own"))   # BC.3
    later = {"0.9.0": ("speech_output_chosen", "nx_menu_hints", "nx_broadcast") + crew_lines,
             "0.10.0": ("speech_output_chosen", "nx_menu_hints") + crew_lines,
             "0.11.0": crew_lines}[version]
    lines = [line for line in text.splitlines() if not line.split("=", 1)[0].strip() in later]
    text = "\n".join(lines) + "\n"
    if version != "0.11.0":
        text = text.replace("speech_output = auto", "speech_output = sapi")
    return text


@pytest.mark.parametrize("version", ["0.9.0", "0.10.0", "0.11.0"])
def test_a_settings_file_of_an_earlier_version_is_read_without_a_problem_and_gets_the_new_defaults(version):
    settings, problems = settingsfile.parse(older_settings(version))
    assert problems == []
    assert settings.speech.mode == "auto" and settings.speech.mode_chosen is False      # the old default sapi, never chosen: automatic, once
    from nfl4.extras import crew
    assert crew.names(settings.game) == crew.DEFAULTS
    again, _ = settingsfile.parse(settingsfile.render(settings))
    assert "speech_output_chosen = no" in settingsfile.render(settings) and again.speech.mode == "auto"


@pytest.mark.parametrize("line, value", [("speech_output_chosen", "maybe"), ("speech_output_chosen", ""), ("nx_menu_hints", "-1"),
                                         ("nx_menu_hints", "100"), ("nx_menu_hints", "999999999999"), ("nx_menu_hints", "three"),
                                         ("speech_output", "screen reader")])
def test_a_damaged_value_of_a_new_setting_is_one_plain_problem_and_the_default(line, value):
    text = settingsfile.render(Settings.defaults())
    lines = [f"{line} = {value}" if raw.split("=", 1)[0].strip() == line else raw for raw in text.splitlines()]
    settings, problems = settingsfile.parse("\n".join(lines) + "\n")
    assert len(problems) == 1 and line in problems[0]
    defaults = Settings.defaults()
    assert settings.speech.mode == defaults.speech.mode and settings.game.nx_menu_hints == defaults.game.nx_menu_hints


# ----- the screen reader question under stress -----

def test_nvda_closing_right_after_yes_at_the_first_start_still_asks_for_no_voice(tmp_path):
    """Rule 0.28 (1): yes means the program never asks the player to choose a voice, even when the screen reader closes a moment later."""
    rig, speech = started(tmp_path, [ENTER] + EXIT_KEYS, first=True)
    real = rig.game.prompts._confirm

    def answer_then_close(*args, **kwargs):
        result = real(*args, **kwargs)
        rig.nvda.available = False                                                     # NVDA closes as the answer is given
        return result

    rig.game.prompts._confirm = answer_then_close
    rig.run()
    everything = rig.nvda.spoken() + [text for text, *_ in rig.said]
    assert words.SCREEN_READER_QUESTION % "NVDA" in everything
    assert [t for t in everything if t.startswith("Choose the voice")] == []
    assert (speech.mode, speech.mode_chosen) == ("auto", True)


def test_nvda_closing_while_the_question_waits_and_no_answers_it_with_the_windows_voices(tmp_path):
    from programrig import DOWN
    rig, speech = started(tmp_path, [DOWN, ENTER] + EXIT_KEYS, first=False)
    real = rig.game.prompts._confirm

    def close_then_answer(*args, **kwargs):
        rig.nvda.available = False
        return real(*args, **kwargs)

    rig.game.prompts._confirm = close_then_answer
    rig.run()
    assert (speech.mode, speech.mode_chosen) == ("sapi", True)
    assert any(text == words.SCREEN_READER_NO for text, *_ in rig.said)               # the answer is said by the Windows voices


def test_the_answer_is_kept_for_this_run_when_the_settings_file_cannot_be_written(tmp_path, monkeypatch):
    rig, speech = started(tmp_path, [ENTER] + EXIT_KEYS, first=False)
    monkeypatch.setattr(rig.game.options, "save", lambda *a, **k: False)
    rig.run()
    assert (speech.mode, speech.mode_chosen) == ("auto", True)
    assert rig.nvda.spoken().count(words.SCREEN_READER_QUESTION % "NVDA") == 1          # asked once in the run, however often the week returns


# ----- teams.txt and the Commanders -----

def old_teams_file(folder):
    """teams.txt as 0.11.0 wrote it: every team, the old notes, T24 = Redskins."""
    text = CU.Customization.default_text_for(CU.TEAMS) if hasattr(CU.Customization, "default_text_for") else None
    path = os.path.join(folder, "teams.txt")
    if text is None:
        CU.Customization(str(folder))                                                 # writes the current file
        text = open(path, encoding="utf-8-sig").read()
    text = text.replace("# " + CU.TEAM_RENAME_NOTE + "\n", "").replace("# " + CU.TEAM_RENAME_NOTE + "\r\n", "")
    text = text.replace("= Commanders", "= Redskins")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


@pytest.mark.parametrize("junk", [bytes(range(256)) * 40, "T24 = Redskins\n".encode("utf-16"), b"\x00" * 300])
def test_a_teams_file_of_junk_is_left_to_the_healing_with_no_error_in_the_log(tmp_path, junk, caplog):
    """Found by the built exe's smoke test (exe_smoke.py teams_junk): the migration logged an ERROR with a traceback for a binary teams.txt."""
    import logging
    (tmp_path / "teams.txt").write_bytes(junk)
    with caplog.at_level(logging.INFO):
        assert CU.migrate_team_names(str(tmp_path)) == ""
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING and "migrated" in r.getMessage()]
    assert (tmp_path / "teams.txt").read_bytes() == junk                               # left for the loader, which heals it


@pytest.mark.parametrize("state", ["read_only", "held_open", "copy_is_a_folder", "copy_is_read_only", "copy_exists", "already_migrated_twice"])
def test_the_commanders_migration_in_every_awkward_state_never_raises_and_never_loses_the_players_file(tmp_path, state):
    path = old_teams_file(tmp_path)
    before = open(path, "rb").read()
    copy = path + CU.TEAMS_BEFORE_RENAME
    context = None
    if state == "read_only":
        context = filedamage.read_only(path)
    elif state == "held_open":
        context = filedamage.holding(path)
    elif state == "copy_is_a_folder":
        os.mkdir(copy)
    elif state == "copy_is_read_only":
        open(copy, "wb").write(b"an older copy")
        context = filedamage.read_only(copy)
    elif state == "copy_exists":
        open(copy, "wb").write(b"an older copy")
    if context is not None:
        with context:
            result = CU.migrate_team_names(str(tmp_path))
    else:
        result = CU.migrate_team_names(str(tmp_path))
        if state == "already_migrated_twice":
            assert result == "renamed"
            result = CU.migrate_team_names(str(tmp_path))
            assert result == ""
    after = open(path, "rb").read()
    if result == "renamed" or state == "already_migrated_twice":
        assert b"Commanders" in after and open(copy, "rb").read() == before            # the player's file is kept, whole
    else:
        assert after == before                                                         # nothing could be done: the file is left as it was
    CU.Customization(str(tmp_path))                                                     # the loader reads whatever is there without raising
