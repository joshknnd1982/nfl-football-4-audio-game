"""footplay.txt: the player's 33 names and the quarterback (data/files/playernames.py). This is inspired by Jim Kitchen.

GAME_SPEC 11, D-025 d, Q8 and Q36: the file has five headed sections and a quarterback; the reader keeps every good section,
reports the rest, and never raises; the writer prints what the reader expects.
"""
from pathlib import Path

import pytest

from nfl4.data.files import playernames as pn
from nfl4.game.names import NamePool
from nfl4.game.rnd import GameRandom
from nfl4.game.setup import COUNTS, HEADINGS, Roster, adopt_partial_roster, draw_roster, new_game_setup


def a_roster(prefix="A", quarterback="Unitas"):
    sections = [[f"{prefix}{h}{i}" for i in range(count)] for h, count in zip("rdkst", COUNTS)]
    return Roster(*sections, quarterback=quarterback)


def test_the_file_is_the_originals_layout_with_the_quarterback_last():
    text = pn.format_roster(a_roster())
    lines = text.splitlines()
    assert lines[0] == "Running Backs:" and lines[1] == "Ar0" and lines[7] == "Receivers:" and lines[8] == "Ad0"
    assert lines[-2:] == ["Quarterback:", "Unitas"]
    assert len(lines) == 5 + 33 + 2
    assert [line for line in lines if line.endswith(":")] == list(HEADINGS) + ["Quarterback:"]


def test_a_roster_without_a_quarterback_is_written_without_his_section():
    lines = pn.format_roster(a_roster(quarterback="")).splitlines()
    assert "Quarterback:" not in lines and len(lines) == 5 + 33


def test_what_was_written_reads_back_whole():
    roster = a_roster()
    parsed = pn.parse(pn.format_roster(roster))
    assert parsed.sound and parsed.problems == [] and parsed.usable
    assert parsed.roster.names() == roster.names() and parsed.roster.quarterback == "Unitas"


def test_a_file_without_the_quarterback_is_sound_and_has_none():
    parsed = pn.parse(pn.format_roster(a_roster(quarterback="")))
    assert parsed.sound and parsed.roster.quarterback == ""


def test_reading_is_tolerant_of_blank_lines_spaces_case_and_line_ends():
    text = pn.format_roster(a_roster())
    messy = "\r\n\r\n".join(text.splitlines()).replace("Receivers:", "  receivers:  ").replace("Ar0", "   Ar0  ")
    parsed = pn.parse(messy)
    assert parsed.sound and parsed.roster.running_backs[0] == "Ar0"


def test_the_player_may_rename_a_name_and_the_file_stays_sound():
    text = pn.format_roster(a_roster()).replace("Ar0", "Gale Sayers")
    parsed = pn.parse(text)
    assert parsed.sound and parsed.roster.running_backs[0] == "Gale Sayers"


@pytest.mark.parametrize("what, change", [
    ("a section is short", lambda t: t.replace("Ar5\n", "")),
    ("a section is long", lambda t: t.replace("Ar5\n", "Ar5\nAr6\n")),
    ("a name has a comma", lambda t: t.replace("Ar5", "Sayers, Gale")),
    ("a name has a semicolon", lambda t: t.replace("Ar5", "Gale;Sayers")),
    ("a name is 31 characters", lambda t: t.replace("Ar5", "x" * 31)),
])
def test_one_wrong_section_costs_only_that_section(what, change):
    parsed = pn.parse(change(pn.format_roster(a_roster())))
    assert parsed.problems and not parsed.sound and parsed.usable, what
    kept = [len(names) == count for (_, names), count in zip(parsed.roster.sections(), COUNTS)]
    assert kept.count(False) == 1 and kept.count(True) == 4, what
    assert parsed.roster.quarterback == "Unitas"


def test_a_misspelled_heading_also_spoils_the_section_before_it_when_names_run_on():
    text = pn.format_roster(a_roster()).replace("Receivers:", "Recievers:")
    parsed = pn.parse(text)
    assert len(parsed.roster.running_backs) == 0       # running backs now hold 12 lines, so that section is wrong as well
    assert len(parsed.roster.receivers) == 0 and len(parsed.roster.defense) == 17


def test_the_quarterback_section_needs_exactly_one_usable_name():
    base = pn.format_roster(a_roster(quarterback=""))
    assert pn.parse(base + "Quarterback:\nStarr\n").roster.quarterback == "Starr"
    for tail in ("Quarterback:\n", "Quarterback:\nA\nB\n", "Quarterback:\na,b\n"):
        parsed = pn.parse(base + tail)
        assert parsed.roster.quarterback == "" and parsed.problems and not parsed.sound


def test_junk_before_the_first_heading_and_a_repeated_heading_are_reported_and_ignored():
    text = "notes by the player\n" + pn.format_roster(a_roster()) + "Kickers:\nZz1\nZz2\n"
    parsed = pn.parse(text)
    assert "line 1 comes before any heading" in parsed.problems[0] and any("twice" in p for p in parsed.problems)
    assert len(parsed.problems) == 4                      # the notes line, the repeated heading and its two names
    assert parsed.roster.kickers == ["At0", "At1"]            # the first section of a heading is used


def test_nothing_usable_in_an_empty_or_foreign_text():
    for text in ("", "\n\n", "hello world\nthis is not a roster\n", "Quarterback:\nUnitas\n"):
        parsed = pn.parse(text)
        assert not parsed.usable and not parsed.sound
    assert pn.parse("Quarterback:\nUnitas\n").roster.quarterback == "Unitas"


def test_a_quarterback_is_appended_or_replaced():
    text = pn.format_roster(a_roster(quarterback=""))
    once = pn.with_quarterback(text, "Starr")
    assert once.splitlines()[-2:] == ["Quarterback:", "Starr"] and once.count("Quarterback:") == 1
    again = pn.with_quarterback(once, "Namath")
    assert again.splitlines()[-2:] == ["Quarterback:", "Namath"] and again.count("Quarterback:") == 1
    assert pn.with_quarterback("", "Starr") == "Quarterback:\nStarr\n"
    assert pn.with_quarterback(text + "Quarterback:\n", "Starr").count("Quarterback:") == 1


def test_every_surname_of_the_pool_is_a_name_the_file_accepts():
    pool = NamePool(GameRandom())
    bad = [pool.name(i) for i in range(1, 1709) if not pn.valid_name(pool.name(i))]
    assert bad == []


def test_a_whole_drawn_roster_survives_the_file():
    roster = draw_roster(NamePool(GameRandom()), None)
    roster.quarterback = "Zoo lynn ski"
    parsed = pn.parse(pn.format_roster(roster))
    assert parsed.sound and parsed.roster.names() == roster.names() and parsed.roster.quarterback == "Zoo lynn ski"


# ----- the set-up with a partly good file (setup.adopt_partial_roster) -----

def test_the_good_sections_are_kept_the_broken_ones_are_drawn_and_the_quarterback_stays():
    text = pn.format_roster(a_roster()).replace("Ar5\n", "")
    parsed = pn.parse(text)
    rnd = GameRandom()
    setup = new_game_setup(rnd, NamePool(rnd), parsed.roster)
    own = setup.rosters[1]
    assert setup.own_names_drawn is True and own.is_complete() and own.quarterback == "Unitas"
    assert own.receivers == a_roster().receivers and own.defense == a_roster().defense      # the good ones are the player's
    assert own.running_backs != a_roster().running_backs and len(own.running_backs) == 6   # the broken one is new
    assert setup.player_names[:29] == own.running_backs + own.receivers + own.defense


def test_a_complete_file_draws_nothing_and_needs_no_new_file():
    rnd = GameRandom()
    setup = new_game_setup(rnd, NamePool(rnd), pn.parse(pn.format_roster(a_roster())).roster)
    assert setup.own_names_drawn is False and setup.rosters[1].names() == a_roster().names()


def test_the_partial_names_blank_the_pool_so_the_opponent_cannot_draw_them():
    pool = NamePool(GameRandom())
    taken = pool.name(41)
    roster = Roster(["Ar%d" % i for i in range(6)], [], ["Ad%d" % i for i in range(17)], [], [taken, "Ak1"])
    adopt_partial_roster(pool, roster, None)
    assert pool.name(41) == ""


def test_the_files_text_decoding_reads_a_windows_code_page_file(tmp_path):
    from nfl4.data.healing import read_player_text
    roster = a_roster()
    roster.running_backs[0] = "Zoë"
    Path(tmp_path / "f.txt").write_bytes(pn.format_roster(roster).encode("cp1252"))
    parsed = pn.parse(read_player_text(str(tmp_path / "f.txt")))
    assert parsed.sound and parsed.roster.running_backs[0] == "Zoë"
