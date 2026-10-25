"""T24 is the Commanders (nfl4; Q-026, the owner 2026-10-22 after a player's e-mail: "They are the Commanders"). This is inspired by Jim Kitchen.

The built-in default is "Commanders". A teams.txt that an older version wrote names every team, so the default alone would change nothing for a player
who already has the file: `migrate_team_names` changes T24 once, keeps the player's file first (teams.txt.before-commanders) and adds the note that
tells a later T24 = Redskins is the player's own choice. The original's name stays in the code as ORIGINAL_T24_NAME and in STRINGS.md.
"""
import os

from nfl4.data import customize as C
from nfl4.data.customize import TEAMS, Customization, migrate_team_names
from nfl4.game import league as league_module
from nfl4.game.league import League


def folder_of(tmp_path):
    return tmp_path / "customize"


def old_file_text(t24="Redskins"):
    """What a version before the rename wrote: the five notes, the 32 teams with the original's T24."""
    names = list(league_module.DEFAULT_TEAM_NAMES)
    names[23] = t24
    lines = ["# NFL Football 4 teams, format 1."] + ["# " + note for note in C.TEAM_NOTES[:5]] + [""]
    lines += ["T%02d = %s" % (n, name) for n, name in enumerate(names, start=1)]
    return "\r\n".join(lines) + "\r\n"


def put(tmp_path, text):
    os.makedirs(folder_of(tmp_path), exist_ok=True)
    (folder_of(tmp_path) / "teams.txt").write_bytes(text.encode("utf-8"))


def teams_file(tmp_path):
    return (folder_of(tmp_path) / "teams.txt").read_bytes().decode("utf-8")


def test_the_built_in_name_of_t24_is_the_commanders_and_the_original_is_kept_as_a_constant():
    league = League()
    assert league.team(6, 4) == "Commanders" and league.team_id(6, 4) == "T24"
    assert league_module.DEFAULT_TEAM_NAMES[23] == "Commanders" and league_module.ORIGINAL_T24_NAME == "Redskins"
    assert "Redskins" not in league_module.DEFAULT_TEAM_NAMES


def test_a_first_start_writes_the_commanders_and_the_note_and_nothing_to_migrate(tmp_path):
    custom = Customization(str(folder_of(tmp_path)))
    text = teams_file(tmp_path)
    assert "\nT24 = Commanders\n" in text.replace("\r\n", "\n") and "Redskins" in C.TEAM_RENAME_NOTE      # the note names the old name
    assert "# " + C.TEAM_RENAME_NOTE in text and custom.snapshot.team_names[23] == "Commanders"
    assert not (folder_of(tmp_path) / ("teams.txt" + C.TEAMS_BEFORE_RENAME)).exists()
    assert migrate_team_names(str(folder_of(tmp_path))) == ""                                  # a file with the note is never migrated


def test_an_older_teams_file_with_the_original_name_becomes_the_commanders_once_and_the_players_file_is_kept(tmp_path):
    put(tmp_path, old_file_text())
    custom = Customization(str(folder_of(tmp_path)))
    assert custom.snapshot.team_names[23] == "Commanders" and custom.take_notices() == []
    text = teams_file(tmp_path)
    plain = text.replace("\r\n", "\n")
    assert "\nT24 = Commanders\n" in plain and "\nT24 = Redskins" not in plain and "# " + C.TEAM_RENAME_NOTE in plain
    kept = (folder_of(tmp_path) / ("teams.txt" + C.TEAMS_BEFORE_RENAME)).read_bytes().decode("utf-8")
    assert kept == old_file_text()
    assert text.replace("\r\n", "\n") == custom.default_text(TEAMS)                             # an untouched older file is the new default exactly


def test_the_player_who_wants_the_redskins_back_writes_it_and_it_stays(tmp_path):
    put(tmp_path, old_file_text())
    Customization(str(folder_of(tmp_path)))
    path = folder_of(tmp_path) / "teams.txt"
    path.write_bytes(path.read_bytes().replace(b"T24 = Commanders", b"T24 = Redskins"))
    again = Customization(str(folder_of(tmp_path)))
    assert again.snapshot.team_names[23] == "Redskins" and "T24 = Redskins" in teams_file(tmp_path)
    assert migrate_team_names(str(folder_of(tmp_path))) == ""


def test_an_older_file_with_another_name_for_t24_keeps_it_and_gets_the_note_so_a_later_redskins_is_the_players_own(tmp_path):
    put(tmp_path, old_file_text("Washington"))
    assert migrate_team_names(str(folder_of(tmp_path))) == "noted"
    text = teams_file(tmp_path)
    assert "T24 = Washington" in text and "# " + C.TEAM_RENAME_NOTE in text
    assert not (folder_of(tmp_path) / ("teams.txt" + C.TEAMS_BEFORE_RENAME)).exists()           # nothing the player wrote was changed: no copy needed
    path = folder_of(tmp_path) / "teams.txt"
    path.write_bytes(path.read_bytes().replace(b"T24 = Washington", b"T24 = Redskins"))
    assert Customization(str(folder_of(tmp_path))).snapshot.team_names[23] == "Redskins"


def test_other_edits_of_the_older_file_stay_and_only_t24_changes(tmp_path):
    put(tmp_path, old_file_text().replace("T09 = Broncos", "T09 = Mustangs"))
    custom = Customization(str(folder_of(tmp_path)))
    assert custom.snapshot.team_names[8] == "Mustangs" and custom.snapshot.team_names[23] == "Commanders"
    assert "T09 = Mustangs" in teams_file(tmp_path)


def test_a_file_without_the_old_notes_is_not_touched_even_when_it_says_redskins(tmp_path):
    text = "# NFL Football 4 teams, format 1.\r\nT24 = Redskins\r\n"
    put(tmp_path, text)
    assert migrate_team_names(str(folder_of(tmp_path))) == ""
    assert teams_file(tmp_path) == text
    assert Customization(str(folder_of(tmp_path))).snapshot.team_names[23] == "Redskins"


def test_the_migration_never_raises_for_a_missing_folder_or_a_damaged_file(tmp_path):
    assert migrate_team_names(str(folder_of(tmp_path))) == ""                                    # no folder
    os.makedirs(folder_of(tmp_path))
    (folder_of(tmp_path) / "teams.txt").write_bytes(b"\x00\x01binary")
    assert migrate_team_names(str(folder_of(tmp_path))) == ""
    (folder_of(tmp_path) / "teams.txt").unlink()
    os.makedirs(folder_of(tmp_path) / "teams.txt")                                               # a folder where the file should be
    assert migrate_team_names(str(folder_of(tmp_path))) == ""


def test_a_reset_of_the_older_file_after_the_migration_needs_no_second_copy(tmp_path):
    put(tmp_path, old_file_text())
    custom = Customization(str(folder_of(tmp_path)))
    written, kept = custom.files[TEAMS].reset()
    assert written and not kept                                                                  # the migrated file already is the built-in text
