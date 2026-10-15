"""The player's customization files: teams, divisions, surnames, banter (data/customize.py). This is inspired by Jim Kitchen.

D-032 items 7 to 11, D-035, D-048, CUSTOMIZABLE_CONTENT 3 to 6 and 10 to 12. What was written down before the code: with the
files absent or unchanged the originals are used; a player's entry with the same ID replaces the original; a bad entry keeps the
original and is counted once; one spoken summary per file; team names (and division names) always all differ ignoring case: a
later collision goes back to its original name, an original name taken by a player's name becomes "<name> 2"; a missing file or
folder is made again silently; reset keeps the player's file as <name>.before-reset and never touches footplay.txt or the
player's sound files.
"""
import os
import random

import pytest

from nfl4.data import customlists as cl
from nfl4.data.customize import (BANTER, DIVISIONS, SPECS, SURNAMES, TEAMS, Customization, name_problem, unique_variant)
from nfl4.game import league as league_module
from nfl4.game.banter_markup import Sound
from nfl4.game.banter_pool import DEFAULT_LINES, DEFAULT_MARKUP
from nfl4.game.names import POOL_SIZE, load_surnames
from wavmaker import sine, write

DEFAULT_TEAMS = league_module.DEFAULT_TEAM_NAMES
DEFAULT_DIVISIONS = league_module.DEFAULT_DIVISION_NAMES


def folder_of(tmp_path):
    return tmp_path / "customize"


def make(tmp_path):
    return Customization(str(folder_of(tmp_path)))


def text_of(tmp_path, name):
    return (folder_of(tmp_path) / name).read_bytes().decode("utf-8")


def edit(tmp_path, name, old, new):
    path = folder_of(tmp_path) / name
    text = path.read_bytes().decode("utf-8")
    assert old in text, (name, old)
    path.write_bytes(text.replace(old, new, 1).encode("utf-8"))


def append(tmp_path, name, *lines):
    path = folder_of(tmp_path) / name
    path.write_bytes(path.read_bytes() + "".join(line + "\r\n" for line in lines).encode("utf-8"))


# ----- the first start -----

def test_a_first_start_makes_the_four_files_and_the_sounds_folder_and_says_nothing(tmp_path):
    custom = make(tmp_path)
    assert sorted(n for n in os.listdir(folder_of(tmp_path))) == ["banter.txt", "divisions.txt", "sounds", "surnames.txt",
                                                                  "teams.txt"]
    assert custom.take_notices() == [] and custom.snapshot.notices == []
    assert [text_of(tmp_path, spec.file_name).splitlines()[0] for spec in SPECS] == [
        "# NFL Football 4 teams, format 1.", "# NFL Football 4 divisions, format 1.", "# NFL Football 4 surnames, format 1.",
        "# NFL Football 4 banter, format 1."]
    assert custom.snapshot.statuses == {spec.key: cl.CREATED for spec in SPECS}


def test_with_the_files_unchanged_the_values_are_the_originals(tmp_path):
    make(tmp_path)
    custom = make(tmp_path)                          # the second start reads the files the first start wrote
    snap = custom.snapshot
    assert snap.statuses == {spec.key: cl.OK for spec in SPECS} and snap.notices == []
    assert snap.team_names == DEFAULT_TEAMS and snap.division_names == DEFAULT_DIVISIONS
    assert snap.surnames == load_surnames() and len(snap.surnames) == POOL_SIZE
    assert all(a is b for a, b in zip(snap.banter.lines, DEFAULT_LINES)) and snap.banter.size == 142
    assert all(snap.problem_count(spec.key) == 0 for spec in SPECS) and snap.sound_files == []


def test_the_file_texts_hold_every_original_value_by_its_id(tmp_path):
    custom = make(tmp_path)
    teams = [l for l in text_of(tmp_path, "teams.txt").splitlines() if l and not l.startswith("#")]
    assert teams == ["T%02d = %s" % (n, name) for n, name in enumerate(DEFAULT_TEAMS, start=1)] and len(teams) == 32
    divisions = [l for l in text_of(tmp_path, "divisions.txt").splitlines() if l and not l.startswith("#")]
    assert divisions[0] == "D1 = A. F. C. North." and divisions[7] == "D8 = N. F. C. South." and len(divisions) == 8
    surnames = [l for l in text_of(tmp_path, "surnames.txt").splitlines() if l and not l.startswith("#")]
    assert len(surnames) == 1708 and surnames[0].startswith("S0001 = ") and surnames[-1].startswith("S1708 = ")
    banter = [l for l in text_of(tmp_path, "banter.txt").splitlines() if l and not l.startswith("#")]
    assert len(banter) == 142 and banter[44] == "B045 = " + DEFAULT_MARKUP[45]
    assert banter[68] == "B069 = Holy [bleep] Ghip!"
    assert custom.default_text(TEAMS).replace("\n", "\r\n") == text_of(tmp_path, "teams.txt")


def test_every_original_value_passes_the_clones_own_limits_so_loading_the_defaults_reports_nothing():
    assert all(name_problem(n) is None for n in DEFAULT_TEAMS + DEFAULT_DIVISIONS)
    assert all(name_problem(n) is None for n in load_surnames())           # Jones" and Maddox) pass (D-026)
    assert len({n.casefold() for n in DEFAULT_TEAMS}) == 32 and len({n.casefold() for n in DEFAULT_DIVISIONS}) == 8


# ----- teams and divisions -----

def test_a_changed_team_name_replaces_the_original_whatever_the_case_of_the_id_and_the_spaces(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "  t09=   Mustangs   ")
    snap = make(tmp_path).snapshot
    assert snap.team_names[8] == "Mustangs" and snap.problem_count(TEAMS) == 0
    assert [n for i, n in enumerate(snap.team_names) if i != 8] == [n for i, n in enumerate(DEFAULT_TEAMS) if i != 8]


def test_a_team_may_take_the_name_of_another_when_that_one_is_renamed_too(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T01 = Bengals", "T01 = Browns")
    edit(tmp_path, "teams.txt", "T02 = Browns", "T02 = Bengals")
    snap = make(tmp_path).snapshot
    assert snap.team_names[:2] == ("Browns", "Bengals") and snap.problem_count(TEAMS) == 0


@pytest.mark.parametrize("value,reason", [("", "1 to 30"), ("x" * 31, "1 to 30"), ("a,b", "comma"), ("a;b", "semicolon"),
                                          ("tab\there", "control")])
def test_a_team_name_the_rules_refuse_keeps_the_original_and_is_counted(tmp_path, value, reason):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T05 = Bills", "T05 = " + value)
    custom = make(tmp_path)
    snap = custom.snapshot
    assert snap.team_names == DEFAULT_TEAMS and snap.problem_count(TEAMS) == 1
    assert reason in snap.problems[TEAMS].messages[0]
    assert snap.notices == [" 1 problem found in teams.txt, details are in the log. "]
    assert custom.take_notices() == snap.notices and custom.take_notices() == []        # said once


def test_a_name_of_exactly_one_and_thirty_characters_is_fine(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T05 = Bills", "T05 = x")
    edit(tmp_path, "teams.txt", "T06 = Dolphins", "T06 = " + "y" * 30)
    snap = make(tmp_path).snapshot
    assert snap.team_names[4] == "x" and snap.team_names[5] == "y" * 30 and snap.problem_count(TEAMS) == 0


def test_an_unknown_id_a_repeated_id_and_a_bad_line_are_problems_and_the_rest_still_applies(tmp_path):
    make(tmp_path)
    append(tmp_path, "teams.txt", "T99 = Nowhere", "T00 = Zero", "T09 = Second Mustangs", "what is this", "X1 = nope")
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    snap = make(tmp_path).snapshot
    assert snap.team_names[8] == "Mustangs"                          # the first line of the ID wins
    assert snap.problem_count(TEAMS) == 5
    assert snap.notices == [" 5 problems found in teams.txt, details are in the log. "]


def test_a_collision_sends_the_later_entry_back_to_its_original_name(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T01 = Bengals", "T01 = Mustangs")
    edit(tmp_path, "teams.txt", "T02 = Browns", "T02 = MUSTANGS")
    snap = make(tmp_path).snapshot
    assert snap.team_names[:2] == ("Mustangs", "Browns") and snap.problem_count(TEAMS) == 1


def test_an_original_name_taken_by_a_new_name_becomes_that_name_with_a_number(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T01 = Bengals", "T01 = Browns")                  # T02's original name
    snap = make(tmp_path).snapshot
    assert snap.team_names[:2] == ("Browns", "Browns 2") and snap.problem_count(TEAMS) == 1
    edit(tmp_path, "teams.txt", "T03 = Ravens", "T03 = Browns 2")
    snap = make(tmp_path).snapshot
    assert snap.team_names[:3] == ("Browns", "Browns 3", "Browns 2")


def test_unique_variant_stays_within_thirty_characters():
    long = "x" * 30
    assert unique_variant(long, set()) == "x" * 28 + " 2" and len(unique_variant(long, {("x" * 28 + " 2").casefold()})) == 30
    assert unique_variant("Browns", {"browns 2"}) == "Browns 3"


def test_random_edits_always_leave_32_different_team_names_and_8_different_division_names(tmp_path):
    rng = random.Random(77)
    pool = list(DEFAULT_TEAMS) + ["Mustangs", "MUSTANGS", "mustangs", "A", "a", "Browns 2", "browns", "", "x,y", "z" * 40]
    for round_ in range(120):
        folder = tmp_path / ("r%d" % round_)
        custom = Customization(str(folder / "customize"))
        path = folder / "customize" / "teams.txt"
        lines = ["# NFL Football 4 teams, format 1."] + ["T%02d = %s" % (n, rng.choice(pool))
                                                         for n in rng.sample(range(1, 33), rng.randint(1, 32))]
        path.write_bytes("\r\n".join(lines).encode("utf-8"))
        dpath = folder / "customize" / "divisions.txt"
        dlines = ["# NFL Football 4 divisions, format 1."] + ["D%d = %s" % (n, rng.choice(["A", "a", "North", "A. F. C. East."]))
                                                             for n in rng.sample(range(1, 9), rng.randint(1, 8))]
        dpath.write_bytes("\r\n".join(dlines).encode("utf-8"))
        custom.reload()
        snap = custom.snapshot
        assert len({n.casefold() for n in snap.team_names}) == 32 and len({n.casefold() for n in snap.division_names}) == 8
        assert all(name_problem(n) is None for n in snap.team_names + snap.division_names)


def test_division_names_are_replaced_the_same_way_and_the_program_adds_the_spaces(tmp_path):
    make(tmp_path)
    edit(tmp_path, "divisions.txt", "D3 = A. F. C. West.", "D3 = The Big Western Group.")
    snap = make(tmp_path).snapshot
    assert snap.division_names[2] == "The Big Western Group." and snap.problem_count(DIVISIONS) == 0
    league = league_module.League()
    league.rename(snap.team_names, snap.division_names)
    assert league.division_text(3) == " The Big Western Group. " and league.team(1, 1) == "Bengals"
    edit(tmp_path, "divisions.txt", "D4 = A. F. C. South.", "D4 = the big western group.")
    snap = make(tmp_path).snapshot
    assert snap.division_names[3] == "A. F. C. South." and snap.problem_count(DIVISIONS) == 1     # same name ignoring case


# ----- surnames -----

def test_a_changed_surname_replaces_its_slot_and_a_duplicate_surname_is_allowed(tmp_path):
    make(tmp_path)
    edit(tmp_path, "surnames.txt", "S0001 = ", "S0001 = Zed ")
    original = load_surnames()
    edit(tmp_path, "surnames.txt", "S0002 = " + original[1], "S0002 = Zed")
    snap = make(tmp_path).snapshot
    assert snap.surnames[0].startswith("Zed") and snap.surnames[1] == "Zed" and len(snap.surnames) == POOL_SIZE
    assert snap.surnames[2:] == original[2:] and snap.problem_count(SURNAMES) == 0


def test_surname_problems_keep_the_original_name_and_the_count_of_slots_never_changes(tmp_path):
    make(tmp_path)
    original = load_surnames()
    append(tmp_path, "surnames.txt", "S1709 = Extra", "S0000 = Zero", "S0003 = a,b")
    edit(tmp_path, "surnames.txt", "S0004 = " + original[3], "S0004 = ")
    snap = make(tmp_path).snapshot
    assert snap.surnames == original and snap.problem_count(SURNAMES) == 4


def test_the_surname_pool_takes_the_renamed_names_and_keeps_used_slots_used(tmp_path):
    from nfl4.game.names import NamePool
    from nfl4.game.rnd import GameRandom
    pool = NamePool(GameRandom(random.Random(1)))
    pool.slots[4] = ""                                              # a name already drawn
    new = list(load_surnames())
    new[4], new[5] = "Renamed Five", "Renamed Six"
    pool.replace_names(new)
    assert pool.slots[4] == "" and pool.slots[5] == "Renamed Six" and pool.original[4] == "Renamed Five"
    with pytest.raises(ValueError):
        pool.replace_names(new[:100])


# ----- banter -----

def test_the_banter_file_replaces_switches_off_and_adds_lines(tmp_path):
    make(tmp_path)
    edit(tmp_path, "banter.txt", "B002 = " + DEFAULT_MARKUP[2], "B002 = Well, [name], that was something")
    edit(tmp_path, "banter.txt", "B003 = " + DEFAULT_MARKUP[3], "B003 = OFF")
    append(tmp_path, "banter.txt", "B143 = What a hit! [sound crunch.wav] Ghip, did you see that?", "b150 = [sound a.wav]",
           "B151 = off")
    custom = make(tmp_path)
    snap = custom.snapshot
    by_number = {line.number: line for line in snap.banter.lines}
    assert snap.problem_count(BANTER) == 0 and snap.banter.off == (3,)             # a new ID that is off is just not there
    assert by_number[2].builtin is False and 3 not in by_number and 143 in by_number and 150 in by_number
    assert snap.banter.size == 142 - 1 + 2 and snap.sound_files == ["a.wav", "crunch.wav"]
    assert by_number[1] is DEFAULT_LINES[0]                                       # untouched lines stay the originals


def test_a_banter_line_that_is_exactly_the_original_markup_is_the_original(tmp_path):
    make(tmp_path)
    snap = make(tmp_path).snapshot
    assert all(a is b for a, b in zip(snap.banter.lines, DEFAULT_LINES))
    edit(tmp_path, "banter.txt", "B069 = Holy [bleep] Ghip!", "B069 = Holy [BLEEP] Ghip!")       # same meaning, other spelling
    snap = make(tmp_path).snapshot
    line = {l.number: l for l in snap.banter.lines}[69]
    assert line.builtin is False and line.markup == "Holy [bleep] Ghip!"


def test_banter_problems_are_counted_once_per_line_with_the_original_kept(tmp_path):
    make(tmp_path)
    edit(tmp_path, "banter.txt", "B010 = " + DEFAULT_MARKUP[10], "B010 = an [unclosed")
    append(tmp_path, "banter.txt", "B160 = a [laugh] b", "B161 = [sound a/b.wav]", "B162 =", "XX = nope", "B143 = ok", "B143 = dup")
    custom = make(tmp_path)
    snap = custom.snapshot
    numbers = [l.number for l in snap.banter.lines]
    assert 10 in numbers and 160 in numbers and 161 not in numbers and 143 in numbers
    assert snap.problem_count(BANTER) == 6                       # B010, B160, B161, B162, line XX, B143 twice
    assert snap.notices == [" 6 problems found in banter.txt, details are in the log. "]


def test_a_new_banter_id_may_be_any_number_up_to_9999(tmp_path):
    make(tmp_path)
    append(tmp_path, "banter.txt", "B9999 = last", "B10000 = too big", "B0 = zero")
    snap = make(tmp_path).snapshot
    assert 9999 in [l.number for l in snap.banter.lines] and snap.problem_count(BANTER) == 2


# ----- the notices of damage -----

def test_a_damaged_file_is_reset_with_one_sentence_and_the_others_are_not_touched(tmp_path):
    make(tmp_path)
    (folder_of(tmp_path) / "teams.txt").write_bytes(b"")
    custom = make(tmp_path)
    assert custom.snapshot.notices == [" The file teams.txt was damaged and has been reset to the original team names. "
                                       "A copy was saved. "]
    assert (folder_of(tmp_path) / "teams.txt.damaged1").exists() and custom.snapshot.team_names == DEFAULT_TEAMS
    assert make(tmp_path).snapshot.notices == []                                           # fixed: said once


def test_a_locked_file_uses_the_originals_this_time_and_says_so(tmp_path):
    from filedamage import holding
    make(tmp_path)
    edit(tmp_path, "banter.txt", "B002 = " + DEFAULT_MARKUP[2], "B002 = mine")
    with holding(folder_of(tmp_path) / "banter.txt"):
        snap = make(tmp_path).snapshot
    assert snap.statuses[BANTER] == cl.LOCKED and snap.banter.size == 142 and snap.banter.lines[1] is DEFAULT_LINES[1]
    assert snap.notices == [" The file banter.txt is in use by another program. The original banter lines are used this time. "]
    assert "mine" in text_of(tmp_path, "banter.txt")                                       # nothing was overwritten
    assert {l.number: l for l in make(tmp_path).snapshot.banter.lines}[2].builtin is False


def test_an_unwritable_folder_says_one_sentence_for_all_the_files(tmp_path):
    (tmp_path / "customize").write_text("a file where the folder should be", encoding="utf-8")
    custom = make(tmp_path)
    assert custom.snapshot.notices == [" The game could not write its customization files, so the original names and lines "
                                       "are used. "]
    assert custom.snapshot.team_names == DEFAULT_TEAMS and custom.snapshot.banter.size == 142


# ----- reload, tend -----

def test_reload_reads_the_files_again_and_returns_the_sentences(tmp_path):
    custom = make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    assert custom.snapshot.team_names[8] == "Broncos"
    assert custom.reload() == [] and custom.snapshot.team_names[8] == "Mustangs"
    edit(tmp_path, "teams.txt", "T10 = Chargers", "T10 = bad,name")
    assert custom.reload() == [" 1 problem found in teams.txt, details are in the log. "]


def test_a_file_that_vanishes_is_made_again_at_the_next_safe_moment_and_the_loaded_names_stay(tmp_path):
    make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    custom = make(tmp_path)
    os.remove(folder_of(tmp_path) / "teams.txt")
    assert custom.take_notices() == []                                  # silent
    assert os.path.exists(folder_of(tmp_path) / "teams.txt") and custom.snapshot.team_names[8] == "Mustangs"
    assert "T09 = Broncos" in text_of(tmp_path, "teams.txt")
    custom.reload()
    assert custom.snapshot.team_names[8] == "Broncos"


def test_a_missing_folder_and_a_missing_sounds_folder_are_made_again(tmp_path):
    import shutil
    custom = make(tmp_path)
    shutil.rmtree(folder_of(tmp_path))
    assert custom.take_notices() == []
    assert sorted(os.listdir(folder_of(tmp_path))) == ["banter.txt", "divisions.txt", "sounds", "surnames.txt", "teams.txt"]
    shutil.rmtree(folder_of(tmp_path) / "sounds")
    custom.reload()
    assert (folder_of(tmp_path) / "sounds").is_dir()


# ----- reset -----

def test_reset_one_list_keeps_the_players_file_and_the_other_lists_alone(tmp_path):
    custom = make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    edit(tmp_path, "divisions.txt", "D1 = A. F. C. North.", "D1 = The North.")
    custom.reload()
    result = custom.reset(TEAMS)
    assert result.done == ["teams.txt"] and result.kept == ["teams.txt"] and result.failed == []
    assert "Mustangs" in (folder_of(tmp_path) / "teams.txt.before-reset").read_text(encoding="utf-8")
    custom.reload()
    assert custom.snapshot.team_names == DEFAULT_TEAMS and custom.snapshot.division_names[0] == "The North."


def test_reset_all_writes_the_four_lists_and_never_touches_footplay_or_the_sound_files(tmp_path):
    custom = make(tmp_path)
    for name, old, new in (("teams.txt", "T09 = Broncos", "T09 = Mustangs"), ("divisions.txt", "D1 = A. F. C. North.", "D1 = N."),
                           ("banter.txt", "B002 = " + DEFAULT_MARKUP[2], "B002 = off")):
        edit(tmp_path, name, old, new)
    (folder_of(tmp_path) / "footplay.txt").write_bytes(b"Running Backs:\r\nA\r\n")
    write(folder_of(tmp_path) / "sounds" / "mine.wav", sine(440, 0.1, 11025), rate=11025)
    footplay = (folder_of(tmp_path) / "footplay.txt").read_bytes()
    sound = (folder_of(tmp_path) / "sounds" / "mine.wav").read_bytes()
    result = custom.reset(None)
    assert result.done == ["teams.txt", "divisions.txt", "surnames.txt", "banter.txt"] and result.failed == []
    assert result.kept == result.done                                     # all four files existed
    custom.reload()
    assert custom.snapshot.team_names == DEFAULT_TEAMS and custom.snapshot.banter.size == 142
    assert (folder_of(tmp_path) / "footplay.txt").read_bytes() == footplay
    assert (folder_of(tmp_path) / "sounds" / "mine.wav").read_bytes() == sound


def test_a_reset_that_cannot_write_says_which_list_failed_and_changes_nothing(tmp_path):
    from filedamage import read_only
    custom = make(tmp_path)
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = Mustangs")
    with read_only(folder_of(tmp_path) / "teams.txt"):
        result = custom.reset(TEAMS)
    assert result.failed == ["teams.txt"] and result.done == []
    assert "Mustangs" in text_of(tmp_path, "teams.txt")


# ----- check -----

def test_check_reads_every_file_and_says_what_it_found_without_applying_anything(tmp_path):
    custom = make(tmp_path)
    assert custom.check() == ("teams.txt: no problems. divisions.txt: no problems. surnames.txt: no problems. "
                              "banter.txt: no problems. Details of every problem are in the log.")
    edit(tmp_path, "teams.txt", "T09 = Broncos", "T09 = a,b")
    edit(tmp_path, "teams.txt", "T10 = Chargers", "T10 = ")
    text = custom.check()
    assert "teams.txt: 2 problems." in text and "banter.txt: no problems." in text
    assert custom.snapshot.team_names == DEFAULT_TEAMS                        # nothing applied


def test_check_names_the_sound_files_and_says_how_many_cannot_be_used(tmp_path):
    custom = make(tmp_path)
    append(tmp_path, "banter.txt", "B143 = a [sound good.wav] b", "B144 = [sound missing.wav]", "B145 = [sound bad.wav]")
    write(folder_of(tmp_path) / "sounds" / "good.wav", sine(440, 0.1, 11025), rate=11025)
    (folder_of(tmp_path) / "sounds" / "bad.wav").write_bytes(b"not a wav file at all")
    assert "The banter names 3 sound files, 2 cannot be used." in custom.check()
    custom.reload()
    assert custom.snapshot.sound_files == ["bad.wav", "good.wav", "missing.wav"]


def test_check_looks_at_footplay_without_changing_it(tmp_path):
    from nfl4.data.files.playernames import format_roster
    from nfl4.game.setup import Roster
    custom = make(tmp_path)
    assert "footplay" not in custom.check()                                   # no such file yet
    names = [("N%d" % n) for n in range(1, 40)]
    roster = Roster(names[:6], names[6:12], names[12:29], names[29:31], names[31:33])
    good = format_roster(roster)
    (folder_of(tmp_path) / "footplay.txt").write_bytes(good.encode("utf-8"))
    assert "footplay.txt: no problems." in custom.check()
    broken = good.replace("Receivers:\n", "Receivers:\nextra\n")
    (folder_of(tmp_path) / "footplay.txt").write_bytes(broken.encode("utf-8"))
    assert "footplay.txt: 1 problem. The game repairs it" in custom.check()
    assert (folder_of(tmp_path) / "footplay.txt").read_bytes() == broken.encode("utf-8")
    (folder_of(tmp_path) / "footplay.txt").write_bytes(b"\x00\x01\x02")
    assert "footplay.txt: it cannot be read now" in custom.check()


def test_check_reports_a_damaged_file_it_healed(tmp_path):
    custom = make(tmp_path)
    (folder_of(tmp_path) / "divisions.txt").write_bytes(b"junk")
    text = custom.check()
    assert text.startswith("The file divisions.txt was damaged and has been reset to the original division names.")
    assert (folder_of(tmp_path) / "divisions.txt.damaged1").exists()


def test_a_sound_name_in_a_line_is_found_in_the_pieces(tmp_path):
    custom = make(tmp_path)
    append(tmp_path, "banter.txt", "B143 = [sound a.wav] [sound b.wav] x")
    custom.reload()
    line = {l.number: l for l in custom.snapshot.banter.lines}[143]
    assert [p.file for p in line.pieces if isinstance(p, Sound)] == ["a.wav", "b.wav"]
