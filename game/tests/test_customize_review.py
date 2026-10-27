"""What the independent review of the customization layer found (S7.7, fixesforgames B-X31), one test each. This is inspired by Jim Kitchen.

A fresh reviewer read the finished layer after 300 tests were green and found two ways to lose the player's own text (a reset
that replaced a file whose copy could not be made, and a second reset that replaced the only copy with the originals) and a few
smaller faults. Written down before the fixes: a reset never writes unless the copy was made; the copies are three deep; a list
whose file cannot be read now keeps the values it had; a notice is said once and is true; "no problems" is never said of a file
that was not read; a sound named in a line cannot hold the game for more than 30 seconds; a name with nothing visible is refused.
BC.2 (D-180): banter.txt is gone; the findings are tested on the lists in use and the sounds on game/line_player.py, which every
customizable line with a sound uses.
"""
import os

import pytest

from filedamage import holding
from nfl4.audio.library import SOUND_FILE_NOTICE
from nfl4.data import customlists as cl
from nfl4.data.customize import Customization, name_problem
from gamerig import Rig
from nfl4.game.banter_markup import parse_markup
from nfl4.game.line_player import MAX_LINE_SOUND_SECONDS, play_line
from randsources import ScriptedRandom
from wavmaker import sine, write


def make(tmp_path):
    return Customization(str(tmp_path / "customize"))


def line_rig(tmp_path):
    """A rig whose game plays the player's sounds from customize\\sounds (no draws: the lines below have no [name] or [one of:])."""
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=ScriptedRandom([], strict=True))
    folder = tmp_path / "customize" / "sounds"
    os.makedirs(folder, exist_ok=True)
    rig.game.custom_sounds_dir = str(folder)
    return rig


def play(rig, markup):
    parsed = parse_markup(markup)
    assert parsed.pieces is not None, parsed.problems
    play_line(rig.game, parsed.pieces, "", "", [])


def edit(tmp_path, name, old, new):
    path = tmp_path / "customize" / name
    path.write_bytes(path.read_bytes().decode("utf-8").replace(old, new, 1).encode("utf-8"))


# ----- findings 1, 2 and 7 live in test_customlists.py; the menu side -----

def test_a_reset_whose_copy_cannot_be_made_is_reported_as_failed_and_the_edit_is_still_there(tmp_path):
    custom = make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    folder = tmp_path / "customize"
    (folder / "teams.txt.before-reset").write_bytes(b"older")
    (folder / "teams.txt.before-reset2").write_bytes(b"older still")
    os.makedirs(folder / "teams.txt.before-reset3" / "x")                    # the copies cannot be moved on
    result = custom.reset("teams")
    assert result.failed == ["teams.txt"] and result.done == [] and result.kept == []
    assert "Mustangs" in (folder / "teams.txt").read_text(encoding="utf-8")


def test_a_reset_of_an_unchanged_list_says_nothing_was_kept(tmp_path):
    custom = make(tmp_path)
    result = custom.reset("teams")
    assert result.done == ["teams.txt"] and result.kept == [] and not (tmp_path / "customize" / "teams.txt.before-reset").exists()


# ----- finding 4: a list whose file cannot be read now keeps what it had -----

def test_reload_with_the_file_held_by_another_program_keeps_the_names_already_loaded(tmp_path):
    custom = make(tmp_path)
    edit(tmp_path, "teams.txt", "T01 = Bengals", "T01 = MyTeam")
    custom.reload()
    assert custom.snapshot.team_names[0] == "MyTeam"
    with holding(tmp_path / "customize" / "teams.txt"):
        notices = custom.reload()
    assert custom.snapshot.team_names[0] == "MyTeam" and custom.snapshot.kept == {"teams"}
    assert notices == [" The file teams.txt is in use by another program. The team names you already had stay in use. "]
    custom.reload()
    assert custom.snapshot.kept == set() and custom.snapshot.team_names[0] == "MyTeam"


def test_the_first_load_with_a_held_file_uses_the_originals_and_says_so(tmp_path):
    make(tmp_path)
    with holding(tmp_path / "customize" / "teams.txt"):
        custom = make(tmp_path)
    assert custom.snapshot.kept == set()
    assert custom.snapshot.notices[0].endswith("The original team names are used this time. ")


def test_a_list_is_kept_too_when_its_file_is_damaged_and_cannot_be_replaced(tmp_path):
    from filedamage import read_only
    custom = make(tmp_path)
    edit(tmp_path, "divisions.txt", "D1 = A. F. C. North.", "D1 = The North.")
    custom.reload()
    assert custom.snapshot.division_names[0] == "The North."
    (tmp_path / "customize" / "divisions.txt").write_bytes(b"junk")
    with read_only(tmp_path / "customize" / "divisions.txt"):
        custom.reload()
    assert custom.snapshot.division_names[0] == "The North." and custom.snapshot.kept == {"divisions"}


# ----- finding 5: notices said once and true -----

def test_nothing_can_be_written_says_the_one_sentence_once_not_twice(tmp_path):
    (tmp_path / "customize").write_text("a file where the folder should be", encoding="utf-8")
    custom = make(tmp_path)
    said = custom.take_notices() + custom.take_notices()
    assert said == [" The game could not write its customization files, so the original names and lines are used. "]


def test_one_unwritable_file_is_said_once_and_the_others_are_not_blamed(tmp_path):
    folder = tmp_path / "customize"
    os.makedirs(folder / "teams.txt.tmp")                                    # the temporary file of teams.txt cannot be made
    custom = make(tmp_path)
    expected = " The file teams.txt could not be made, so the original team names are used. "
    assert custom.take_notices() == [expected]
    assert custom.take_notices() == []
    assert sorted(os.listdir(folder)) == sorted(["divisions.txt", "remarks.txt", "sounds", "surnames.txt", "teams.txt.tmp"])      # BC.3


# ----- finding 6: check never says "no problems" of a file it did not read -----

def test_check_does_not_say_no_problems_of_a_file_it_could_not_read(tmp_path):
    custom = make(tmp_path)
    with holding(tmp_path / "customize" / "divisions.txt"):
        text = custom.check()
    assert "divisions.txt: it could not be read or made, so it was not checked." in text
    assert "divisions.txt: no problems" not in text and "teams.txt: no problems." in text


# ----- finding 10: nothing visible -----

@pytest.mark.parametrize("name", ["​", " ​ ", " ", "​‍"])
def test_a_name_with_nothing_to_see_or_say_is_refused(name):
    assert name_problem(name) is not None


def test_names_in_any_language_and_signs_are_fine():
    for name in ("Márquez", "山田", "O'Brien", "No. 7", "9ers", "?!"):
        assert name_problem(name) is None


# ----- finding 13: a tab inside a value is a space -----

def test_a_tab_in_a_team_name_is_a_space(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Red\tHorses")
    assert make(tmp_path).snapshot.team_names[8] == "Red Horses"


# ----- finding 14: more device names, and only real files are opened -----

@pytest.mark.parametrize("name", ["COM¹.wav", "lpt³", "Com² .wav"])
def test_the_superscript_device_names_are_refused_too(name):
    parsed = parse_markup("[sound %s]" % name)
    assert parsed.pieces is None and any("device" in p for p in parsed.problems)


def test_a_sound_that_is_a_folder_plays_nothing_and_gives_the_notice(tmp_path):
    rig = line_rig(tmp_path)
    os.makedirs(tmp_path / "customize" / "sounds" / "dir.wav")
    play(rig, "a [sound dir.wav] b")
    assert [t for t, _, _ in rig.said] == ["a", "b"] and rig.audio.library.take_notices() == [SOUND_FILE_NOTICE]


# ----- finding 9: the sounds of one line stop at 30 seconds -----

def test_the_sounds_of_one_line_together_are_cut_at_thirty_seconds(tmp_path):
    rig = line_rig(tmp_path)
    write(tmp_path / "customize" / "sounds" / "long.wav", sine(220, 20.0, 8000), rate=8000)
    before = rig.clock()
    play(rig, "[sound long.wav] [sound long.wav] [sound long.wav] end")
    waited = rig.clock() - before
    assert MAX_LINE_SOUND_SECONDS <= waited < MAX_LINE_SOUND_SECONDS + 1.0       # 20 s + the 10 s that are left, then the text
    assert [t for t, _, _ in rig.said] == ["end"]


def test_a_second_sound_after_the_limit_is_skipped(tmp_path):
    rig = line_rig(tmp_path)
    write(tmp_path / "customize" / "sounds" / "long.wav", sine(220, 20.0, 8000), rate=8000)
    write(tmp_path / "customize" / "sounds" / "short.wav", sine(220, 1.0, 8000), rate=8000)
    play(rig, "[sound long.wav] [sound long.wav] [sound short.wav] [sound short.wav] end")
    played = [e for e in rig.slot_log if e.action == "play" and e.source == "player"]
    assert [e.sound_id for e in played] == ["file long.wav", "file long.wav"]           # the short ones came after the 30 seconds


# ----- finding 3: the reset says what the reload found -----

def test_reset_one_also_says_what_the_reload_healed(tmp_path):
    from programrig import DOWN, ENTER, ESC, preset_season, program_rig, said
    rig = program_rig(tmp_path / "rig", [], preset=preset_season())
    rig.custom = Customization(str(tmp_path / "customize"))
    rig.game.customization = rig.custom
    rig.game.apply_customization()
    (tmp_path / "customize" / "divisions.txt").write_bytes(b"junk")
    rig.keys.answers = [DOWN, DOWN, ENTER, DOWN, DOWN, DOWN, ENTER, ENTER, ESC, ESC, ESC]
    rig.game.functions.run()
    spoken = said(rig)
    assert any("Team names" in s for s in spoken)
    healed = [s for s in spoken if s.startswith("teams.txt is back to the original")]
    assert healed and "The file divisions.txt was damaged and has been reset" in healed[0]
