"""The customization list format and its healing, for any list (data/customlists.py). This is inspired by Jim Kitchen.

Playbook 7.9 and 7.10, D-032 item 7, D-048. The format was chosen once here: a header with the format version on the first line,
`#` notes, one `ID = value` per line. What was written down before the code: a file is unusable when it is empty, binary,
undecodable, far too large, has no header, has another list's or game's header, or another format version (copied to
.damagedN, written again, one notice); a bad line is only a bad line; a locked or unwritable file is not damage.
"""
import os
import sys

import pytest

from filedamage import BYTE_DAMAGES, apply, holding, read_only
from nfl4.data import customlists as cl

GAME, KIND = "Test Game", "things"
ENTRIES = [("A1", "one"), ("A2", "two"), ("A3", "three")]


def default_text():
    return cl.render_list(GAME, KIND, ["A note.", "Another note."], ENTRIES)


def a_file(tmp_path, name="things.txt"):
    return cl.ListFile(str(tmp_path / "customize"), name, GAME, KIND, default_text)


# ----- parse -----

def test_parse_reads_the_header_the_entries_and_skips_notes_and_blank_lines():
    parsed = cl.parse_list(default_text(), GAME, KIND)
    assert parsed.version == 1 and parsed.bad_lines == []
    assert [(e.id, e.value) for e in parsed.entries] == ENTRIES
    assert [e.line for e in parsed.entries] == [5, 6, 7]


def test_the_id_is_not_case_sensitive_and_spaces_around_it_and_the_value_are_ignored():
    parsed = cl.parse_list("#   test game   THINGS , format  1\n  a1=  x y  \nA2 =z = w\n", GAME, KIND)
    assert [(e.id, e.value) for e in parsed.entries] == [("A1", "x y"), ("A2", "z = w")]


def test_blank_lines_before_the_header_are_fine_and_lf_or_crlf_do_not_matter():
    for text in ("\n\n# Test Game things, format 1.\nA1 = one\n", "\r\n# Test Game things, format 1.\r\nA1 = one\r\n"):
        assert [e.id for e in cl.parse_list(text, GAME, KIND).entries] == ["A1"]


def test_a_line_that_is_not_an_entry_is_a_bad_line_not_an_error():
    parsed = cl.parse_list("# Test Game things, format 1.\nA1 = one\nno equals here\n= no id\n12 = digit first\nA2 = two\n",
                           GAME, KIND)
    assert [e.id for e in parsed.entries] == ["A1", "A2"]
    assert [number for number, _ in parsed.bad_lines] == [3, 4, 5]


@pytest.mark.parametrize("text", ["", "   \n\n  \r\n", "A1 = one\n", "# just a note\nA1 = one\n",
                                  "# Other Game things, format 1.\nA1 = one\n", "# Test Game other, format 1.\nA1 = one\n",
                                  "# Test Game things, format 2.\nA1 = one\n", "# Test Game things, format 0.\nA1 = one\n",
                                  "# Test Game things.\nA1 = one\n"])
def test_a_text_that_is_not_a_list_of_this_kind_is_unusable(text):
    with pytest.raises(cl.ListFormatError):
        cl.parse_list(text, GAME, KIND)


def test_render_then_parse_gives_the_entries_back_and_the_first_line_is_the_header():
    text = default_text()
    assert text.splitlines()[0] == "# Test Game things, format 1."
    assert text.endswith("A3 = three\n") and "\r" not in text


# ----- the notices -----

def test_the_problem_summary_says_how_many_in_plain_words_and_counts_entries_not_messages():
    problems = cl.Problems("teams.txt")
    problems.add("T01", "first thing")
    problems.add("T01", "second thing about the same entry")
    problems.add("line 9", "another")
    assert problems.count == 2 and problems.messages[0] == "T01: first thing"
    assert cl.problems_notice("teams.txt", 1) == " 1 problem found in teams.txt, details are in the log. "
    assert cl.problems_notice("teams.txt", 2) == " 2 problems found in teams.txt, details are in the log. "


# ----- the file -----

def test_a_missing_file_and_a_missing_folder_are_made_silently_from_the_built_in_text(tmp_path):
    file = a_file(tmp_path)
    load = file.load()
    assert load.status == cl.CREATED and load.parsed is None
    assert open(file.path, "rb").read().decode("utf-8") == default_text().replace("\n", "\r\n")     # written with CRLF
    again = file.load()
    assert again.status == cl.OK and [(e.id, e.value) for e in again.parsed.entries] == ENTRIES


def test_a_good_file_is_read_whatever_its_encoding(tmp_path):
    file = a_file(tmp_path)
    os.makedirs(file.folder)
    for raw in (default_text().encode("utf-8"), b"\xef\xbb\xbf" + default_text().encode("utf-8"),
                default_text().encode("utf-16"), default_text().replace("one", "né").encode("cp1252")):
        open(file.path, "wb").write(raw)
        load = file.load()
        assert load.status == cl.OK and len(load.parsed.entries) == 3, raw[:10]


@pytest.mark.parametrize("kind", BYTE_DAMAGES)
def test_every_unusable_file_is_copied_aside_written_again_and_told_once(tmp_path, kind):
    file = a_file(tmp_path)
    file.load()
    apply(kind, file.path)
    damaged = open(file.path, "rb").read()
    load = file.load()
    if kind in ("cut_in_half", "bad_line_in_the_middle"):             # the header is fine: only entries are missing or bad
        assert load.status == cl.OK and load.parsed is not None
        assert not os.path.exists(file.path + ".damaged1")
        return
    assert load.status == cl.RESET and load.parsed is None and load.why
    assert open(file.path + ".damaged1", "rb").read() == damaged       # nothing the player wrote is lost
    assert cl.parse_list(open(file.path, "rb").read().decode("utf-8"), GAME, KIND).entries    # the file is whole again
    assert file.load().status == cl.OK


def test_three_damaged_copies_are_kept(tmp_path):
    file = a_file(tmp_path)
    file.load()
    for number in range(5):
        open(file.path, "wb").write(b"junk %d" % number)
        assert file.load().status == cl.RESET
    names = sorted(n for n in os.listdir(file.folder) if ".damaged" in n)
    assert names == ["things.txt.damaged3", "things.txt.damaged4", "things.txt.damaged5"]
    assert open(file.path + ".damaged5", "rb").read() == b"junk 4"


def test_a_file_that_is_a_folder_is_left_alone_and_the_built_in_values_are_used(tmp_path):
    file = a_file(tmp_path)
    os.makedirs(file.path)
    load = file.load()
    assert load.status == cl.KEPT_DAMAGED and load.parsed is None and os.path.isdir(file.path)


@pytest.mark.skipif(sys.platform != "win32", reason="a sharing violation is a Windows thing")
def test_a_file_another_program_holds_is_not_damaged_and_nothing_is_written(tmp_path):
    file = a_file(tmp_path)
    file.load()
    before = open(file.path, "rb").read()
    with holding(file.path):
        load = file.load()
        assert load.status == cl.LOCKED and load.parsed is None
        assert not [n for n in os.listdir(file.folder) if ".damaged" in n or n.endswith(".tmp")]
    assert open(file.path, "rb").read() == before
    assert file.load().status == cl.OK


def test_a_read_only_damaged_file_cannot_be_replaced_so_the_built_in_values_are_used(tmp_path):
    file = a_file(tmp_path)
    file.load()
    open(file.path, "wb").write(b"junk")
    with read_only(file.path):
        load = file.load()
        assert load.status == cl.KEPT_DAMAGED and load.parsed is None
        assert open(file.path, "rb").read() == b"junk" and os.path.exists(file.path + ".damaged1")
        assert not [n for n in os.listdir(file.folder) if n.endswith(".tmp")]


def test_a_folder_that_cannot_be_made_gives_unwritable_not_an_error(tmp_path):
    blocker = tmp_path / "customize"
    blocker.write_text("this is a file where the folder should be", encoding="utf-8")
    load = a_file(tmp_path).load()
    assert load.status == cl.UNWRITABLE and load.parsed is None


def test_load_never_raises_even_when_the_built_in_text_cannot_be_made(tmp_path):
    def broken():
        raise RuntimeError("no built-in text")
    file = cl.ListFile(str(tmp_path / "c"), "x.txt", GAME, KIND, broken)
    assert file.load().status == cl.UNWRITABLE


def test_reset_keeps_the_players_file_as_before_reset_and_writes_the_built_in_text(tmp_path):
    file = a_file(tmp_path)
    file.load()
    open(file.path, "wb").write(default_text().replace("two", "TWO").encode("utf-8"))
    assert file.reset() is True
    assert open(file.path + ".before-reset", "rb").read().decode("utf-8").count("TWO") == 1
    assert "TWO" not in open(file.path, "rb").read().decode("utf-8")
    assert file.reset() is True                                           # a second reset replaces the one copy
    assert "TWO" not in open(file.path + ".before-reset", "rb").read().decode("utf-8")


def test_reset_of_a_missing_file_just_writes_it(tmp_path):
    file = a_file(tmp_path)
    assert file.reset() is True and os.path.exists(file.path) and not os.path.exists(file.path + ".before-reset")
