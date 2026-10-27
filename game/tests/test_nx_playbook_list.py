"""plays.txt, styles.txt and team_styles.txt: the playbooks' files of the customize folder (nfl4 only, rule 0.13;
CUSTOMIZABLE_CONTENT 13 L15, CLAUDE.md 0.12, playbook 7.9 and 7.10, N5.7; PX SX.7). This is inspired by Jim Kitchen.

The defaults are the catalog's names, the styles and the team assignment of extras/playbook_data.py; a player's line renames or
switches off a play, changes a weight or a tilt within the bounds of design 10.3, or reassigns a team; a number past its bound
keeps the default and is a problem; the three files heal like every list and are read only with the N. F. L. rules.
"""
import os
import random

import pytest

from filedamage import BYTE_DAMAGES, apply, holding
from nfl4.data import customlists as cl
from nfl4.data.customize import Customization
from nfl4.extras import nx_texts as X
from nfl4.extras import playbook_data as D
from nfl4.extras import playbook_list as PL
from nfl4.extras import playbooks as PB

GAME = "NFL Football 4"
FILES = {"plays": "plays.txt", "styles": "styles.txt", "teamstyles": "team_styles.txt"}
NOTES = {"plays": PL.PLAYS_NOTES, "styles": PL.STYLES_NOTES, "teamstyles": PL.TEAMS_NOTES}


def read(kind, body):
    text = cl.render_list(GAME, kind, NOTES[kind], []) + body
    return cl.parse_list(text, GAME, kind).entries


def table_of(kind, body, table=PB.DEFAULT_TABLE):
    problems = cl.Problems(FILES[kind])
    apply_it = {"plays": PL.apply_plays, "styles": PL.apply_styles, "teamstyles": PL.apply_teams}[kind]
    return apply_it(table, read(kind, body), problems), problems


def write(folder, kind, body):
    path = os.path.join(folder, "playbooks", FILES[kind])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(cl.render_list(GAME, kind, NOTES[kind], []) + body)
    return path


# ----- the defaults -----

def test_the_defaults_are_the_catalogs_names_the_styles_and_the_team_assignment():
    plays = dict(PL.default_plays())                         # SX.10c: every play of the catalog (282), SX.7's 82 among them
    assert all(plays[p.id] == X.text(p.name_id) for p in D.CATALOG) and len(plays) == 282
    assert PB.DEFAULT_TABLE.name("O017") == "Running Back Screen" and PB.DEFAULT_TABLE.name("D011") == "Cover Zero Blitz"
    teams = dict(PL.default_teams())
    assert len(teams) == 32 and teams["T01"] == "Air Raid; defense Pro Style" and teams["T02"] == "Pressure"
    assert teams["T04"] == "Pro Style; defense Pressure"
    styles = dict(PL.default_styles())
    assert styles["S2O017"].startswith("weight ") and styles["S2OB1"] == "families 3 4; vs 1 2 3; sack -2; comp 3"
    assert styles["S6QB"] == "300" and styles["S1QB"] == "100" and not any(k.startswith("S1O") and "B" in k[2:3] for k in styles)


@pytest.mark.parametrize("kind", ["plays", "styles", "teamstyles"])
def test_each_default_file_reads_back_to_the_built_in_table_with_no_problem(kind):
    entries = {"plays": PL.default_plays, "styles": PL.default_styles, "teamstyles": PL.default_teams}[kind]()
    text = cl.render_list(GAME, kind, NOTES[kind], entries)
    parsed = cl.parse_list(text, GAME, kind)
    assert parsed.bad_lines == []
    problems = cl.Problems(FILES[kind])
    apply_it = {"plays": PL.apply_plays, "styles": PL.apply_styles, "teamstyles": PL.apply_teams}[kind]
    assert apply_it(PB.DEFAULT_TABLE, parsed.entries, problems) == PB.DEFAULT_TABLE and problems.count == 0


# ----- plays.txt -----

def test_a_line_renames_or_switches_off_a_play_for_every_style():
    table, problems = table_of("plays", "O004 = Delayed Draw\nd11 = Zero Blitz; off\nO5 = Dive; on\n")
    assert table.name("O004") == "Delayed Draw" and table.name("D011") == "Zero Blitz" and table.name("O005") == "Dive"
    assert table.disabled == frozenset({"D011"}) and problems.count == 0
    assert all("D011" not in [p.id for p, _w in table.usable(k, "D")] for k in D.STYLE_BY_KEY)
    assert table.name("O001") == "Inside Zone"


def test_a_switched_off_play_leaves_the_computers_choice_and_the_menus():
    table, _ = table_of("plays", "O001 = Inside Zone; off\n")
    assert "O001" not in [p.id for p, _w in table.usable("pro", "O")] and "O002" in [p.id for p, _w in table.usable("pro", "O")]


def test_bad_play_lines_are_problems_and_keep_the_originals():
    table, problems = table_of("plays", "O400 = Nothing\nX001 = No\nO001 = a, b\nO002 = one two three four five six seven\n"
                                        "O003 = Counter; sometimes\nO003 = again\nO004 = ; off\nO006 =\n")
    assert table.name("O001") == X.text("NXY-01") and table.name("O002") == X.text("NXY-02")
    assert table.name("O003") == "Counter" and "O004" in table.disabled and table.name("O006") == X.text("NXY-06")
    assert problems.count == 7


# ----- styles.txt -----

def test_a_line_changes_removes_or_adds_a_play_of_a_style():
    table, problems = table_of("styles", "S2O017 = weight 9\nS2O018 = off\nS2O009 = weight 5\nS2D001 = weight 0\nS2D004 = on\n")
    west = table.styles["west"]
    assert west.offense["O017"] == 9 and "O018" not in west.offense and west.offense["O009"] == 5
    assert "D001" not in west.defense and west.defense["D004"] > 0 and problems.count == 0
    assert table.styles["pro"] == PB.DEFAULT_TABLE.styles["pro"]       # the other styles are the built-in ones
    assert [p.id for p, _w in table.usable("west", "O")] == sorted(west.offense)


def test_a_weight_past_its_bound_or_for_a_play_that_does_not_exist_is_a_problem():
    table, problems = table_of("styles", "S2O017 = weight 101\nS2O018 = lots\nS2O999 = weight 5\nS8O001 = weight 5\n"
                                         "S2D001 = weight 5\nS2O017 = weight 3\n")
    assert table.styles["west"].offense["O017"] == PB.DEFAULT_TABLE.styles["west"].offense["O017"]
    assert table.styles["west"].offense["O018"] == PB.DEFAULT_TABLE.styles["west"].offense["O018"]
    assert problems.count == 4                                        # S2O017 (101 and the twice: one ID), lots, O999 and S8;
    #                                                                           S2D001 is fine


def test_a_tilt_changes_within_its_bounds_and_a_tilt_past_a_bound_keeps_its_default():
    table, problems = table_of("styles", "S2OB1 = families 3; vs 1 2; sack -1; comp 5; ylo 2\n"
                                         "S2OP1 = families 5; vs 1; comp -6\nS3DB1 = families 5; vs 4; fum -5\n")
    west, air = table.styles["west"], table.styles["air"]
    assert west.tilts["OB1"] == D.Tilt((3,), (1, 2), D.Mod(2, 0, -1, 5, 0))
    assert west.tilts["OP1"] == PB.DEFAULT_TABLE.styles["west"].tilts["OP1"]       # comp -6 is past the bound 5
    assert air.tilts["DB1"] == D.Tilt((5,), (4,), D.Mod(0, 0, 0, 0, -5)) and problems.count == 1


@pytest.mark.parametrize("value", ["families 3; vs 1; yhi 3", "families 3; vs 1; sack -6", "families 3; vs 1; fum 6",
                                   "families 3; vs 1; ylo -3", "families 7; vs 1", "families 3; vs 7", "vs 1", "families 3",
                                   "families 3; vs 1; speed 2", "families; vs 1", "families 3; vs 1; yhi x", "nonsense"])
def test_a_tilt_that_is_not_understood_or_out_of_its_bounds_is_a_problem(value):
    table, problems = table_of("styles", "S2OB1 = %s\n" % value)
    assert table.styles["west"].tilts["OB1"] == PB.DEFAULT_TABLE.styles["west"].tilts["OB1"] and problems.count == 1


def test_a_tilt_can_be_taken_out_or_added_to_a_style_that_has_none():
    table, problems = table_of("styles", "S2OB1 = off\nS1OB1 = families 1; vs 1 2 3; ylo 1\nS1DB1 = families 4; vs 3; sack 2\n")
    assert "OB1" not in table.styles["west"].tilts and table.styles["pro"].tilts["OB1"] == D.Tilt((1,), (1, 2, 3), D.Mod(1))
    assert table.styles["pro"].tilts["DB1"] == D.Tilt((4,), (3,), D.Mod(0, 0, 2)) and problems.count == 0
    side = PB.StyleBook.tilts_of(table.styles["pro"], "D")
    assert side == [D.Tilt((4,), (3,), D.Mod(0, 0, 2))]


def test_a_defense_tilt_uses_the_defenses_families_and_the_offenses_calls():
    table, problems = table_of("styles", "S1DB1 = families 6; vs 8 9 10; yhi -2\nS1OB1 = families 1; vs 8\n")
    assert table.styles["pro"].tilts["DB1"] == D.Tilt((6,), (8, 9, 10), D.Mod(0, -2))
    assert "OB1" not in table.styles["pro"].tilts and problems.count == 1      # an offense tilt's families are the offense's and
    #                                                                           its calls the defense's: 8 is no defense call


def test_the_computers_quarterback_rate_is_a_percent():
    table, problems = table_of("styles", "S6QB = 500\nS5QB = 1001\nS4QB = x\nS3QB = 0\n")
    assert table.styles["option"].qb_percent == 500 and table.styles["zone"].qb_percent == 100
    assert table.styles["air"].qb_percent == 0 and problems.count == 2


def test_other_lines_of_styles_txt_are_problems_and_a_second_line_for_an_id_is_ignored():
    table, problems = table_of("styles", "WES = x\nS2O017 = weight 4\nS2O017 = weight 8\nS2Q = 1\n")
    assert table.styles["west"].offense["O017"] == 4 and problems.count == 3


# ----- team_styles.txt -----

def test_a_line_assigns_a_teams_offense_and_defense_by_the_styles_name():
    table, problems = table_of("teamstyles", "T01 = Classic\nT02 = zone run; defense OPTION\nt3 = west\nT04 = Power Run\n")
    assert table.teams[0] == ("classic", "classic") and table.teams[1] == ("zone", "option")
    assert table.teams[2] == ("west", "west") and table.teams[3] == ("power", "power") and problems.count == 0
    assert table.teams[4:] == PB.DEFAULT_TABLE.teams[4:]
    assert table.team_style(1, "O") == "zone" and table.team_style(1, "D") == "option" and table.team_style(40, "O") == "classic"


def test_a_bad_team_line_is_a_problem_and_keeps_the_original_assignment():
    table, problems = table_of("teamstyles", "T01 = Wing T\nT33 = Air Raid\nT05 = Air Raid; defence Zone Run\n"
                                             "T06 = Air Raid; defense Wing T\nT02 = Air Raid\nT02 = Zone Run\n")
    assert table.teams[0] == PB.DEFAULT_TABLE.teams[0] and table.teams[5] == PB.DEFAULT_TABLE.teams[5]
    assert table.teams[4] == ("air", "air") and table.teams[1] == ("air", "air") and problems.count == 5


def test_style_names_are_found_whatever_their_case_and_by_their_key():
    for name, key in (("pro style", "pro"), ("WEST COAST", "west"), ("air", "air"), ("Option", "option"), ("classic", "classic")):
        assert PL.style_choice(name, PB.DEFAULT_TABLE) == key
    assert PL.style_choice("", PB.DEFAULT_TABLE) is None and PL.style_choice("Wing T", PB.DEFAULT_TABLE) is None


# ----- the folder, the healing, the game -----

def test_the_three_files_are_made_in_the_playbooks_folder_only_with_the_nfl_rules(tmp_path):
    folder = str(tmp_path / "customize")
    classic = Customization(folder)
    assert not os.path.exists(os.path.join(folder, "playbooks")) and classic.snapshot.playbooks is None
    assert [spec.file_name for spec in classic.specs] == ["teams.txt", "divisions.txt", "surnames.txt"]      # BC.2: no banter.txt
    custom = Customization(folder, extras=True)
    assert [spec.file_name for spec in custom.specs][-6:-3] == ["plays.txt", "styles.txt", "team_styles.txt"]       # news.txt (SX.8e), injuries.txt (SX.8k), favourites.txt (SX.10c) follow
    for name in FILES.values():
        assert os.path.isfile(os.path.join(folder, "playbooks", name)), name
    assert custom.snapshot.playbooks == PB.DEFAULT_TABLE and custom.take_notices() == []


def test_the_players_lines_are_read_and_their_problems_said_once_per_file(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "plays", "O004 = Delayed Draw\nO999 = x\n")
    write(folder, "styles", "S2O017 = weight 9\n")
    write(folder, "teamstyles", "T01 = Classic\nT33 = x\n")
    custom = Customization(folder, extras=True)
    table = custom.snapshot.playbooks
    assert table.name("O004") == "Delayed Draw" and table.styles["west"].offense["O017"] == 9 and table.teams[0][0] == "classic"
    notices = custom.take_notices()
    assert " 1 problem found in plays.txt, details are in the log. " in notices
    assert " 1 problem found in team_styles.txt, details are in the log. " in notices
    assert not any("styles.txt" in n and "team" not in n for n in notices) and custom.take_notices() == []
    custom.use_extras(False)
    assert custom.snapshot.playbooks is None
    custom.use_extras(True)
    assert custom.snapshot.playbooks.name("O004") == "Delayed Draw"


def test_the_game_takes_the_table_when_the_rules_are_switched_on(tmp_path):
    from pagrig import make_rig
    rig = make_rig(tmp_path)
    folder = str(tmp_path / "customize")
    write(folder, "plays", "O001 = Zone Left\n")
    rig.game.customization = Customization(folder)
    rig.game.apply_customization()
    assert rig.game.playbook_table is None
    rig.game.options.settings.game.rules = "nfl"
    rig.game.apply_rules_setting()
    assert rig.game.playbook_table.name("O001") == "Zone Left"
    rig.game.options.settings.game.rules = "classic"
    rig.game.apply_rules_setting()
    assert rig.game.playbook_table is None


@pytest.mark.parametrize("kind", ["plays", "styles", "teamstyles"])
@pytest.mark.parametrize("damage", BYTE_DAMAGES)
def test_a_damaged_file_is_copied_aside_and_made_again_or_read_in_part(tmp_path, kind, damage):
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "playbooks", FILES[kind])
    original = open(path, "rb").read()
    apply(damage, path)
    damaged = open(path, "rb").read()
    custom = Customization(folder, extras=True)
    notices = custom.take_notices()
    table = custom.snapshot.playbooks
    assert isinstance(table, PB.Table)
    if damage in ("cut_in_half", "bad_line_in_the_middle"):
        assert not os.path.exists(path + ".damaged1")
    else:
        assert open(path + ".damaged1", "rb").read() == damaged and open(path, "rb").read() == original
        nouns = {"plays": "play names", "styles": "styles", "teamstyles": "team styles"}[kind]
        assert " The file %s was damaged and has been reset to the original %s. A copy was saved. " % (FILES[kind], nouns) in notices
        assert table == PB.DEFAULT_TABLE


@pytest.mark.parametrize("kind", ["plays", "styles", "teamstyles"])
def test_a_file_held_by_another_program_keeps_the_loaded_part_of_the_table(tmp_path, kind):
    folder = str(tmp_path / "customize")
    write(folder, "plays", "O004 = Mine\n")
    write(folder, "styles", "S2O017 = weight 9\n")
    write(folder, "teamstyles", "T01 = Classic\n")
    custom = Customization(folder, extras=True)
    with holding(os.path.join(folder, "playbooks", FILES[kind])):
        notices = custom.reload()
    nouns = {"plays": "play names", "styles": "styles", "teamstyles": "team styles"}[kind]
    assert any("%s is in use by another program. The %s you already had stay in use." % (FILES[kind], nouns) in n
               for n in notices)
    table = custom.snapshot.playbooks
    assert table.name("O004") == "Mine" and table.styles["west"].offense["O017"] == 9 and table.teams[0][0] == "classic"


def test_reset_keeps_the_players_files_and_check_names_each_one(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "plays", "O004 = Mine\n")
    custom = Customization(folder, extras=True)
    result = custom.reset("plays")
    assert result.done == ["plays.txt"] and result.kept == ["plays.txt"]
    assert "Mine" in open(os.path.join(folder, "playbooks", "plays.txt.before-reset"), encoding="utf-8").read()
    checked = custom.check()
    assert "plays.txt: no problems." in checked and "styles.txt: no problems." in checked
    assert "team_styles.txt: no problems." in checked
    custom.reset()                                                    # every list: the three files are made again from the data
    assert dict(PL.default_plays())["O004"] in open(os.path.join(folder, "playbooks", "plays.txt"), encoding="utf-8").read()


def test_a_missing_file_or_folder_is_made_again_silently(tmp_path):
    folder = str(tmp_path / "customize")
    custom = Customization(folder, extras=True)
    custom.take_notices()
    import shutil
    shutil.rmtree(os.path.join(folder, "playbooks"))
    assert custom.take_notices() == []
    assert all(os.path.isfile(os.path.join(folder, "playbooks", name)) for name in FILES.values())


@pytest.mark.parametrize("kind", ["plays", "styles", "teamstyles"])
def test_a_fuzz_of_damaged_files_never_raises_and_always_leaves_a_usable_table(tmp_path, kind):
    rng = random.Random(41)
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "playbooks", FILES[kind])
    good = open(path, "rb").read()
    for case in range(60):
        raw = bytearray(good)
        for _ in range(rng.randint(1, 20)):
            raw[rng.randrange(len(raw))] = rng.randrange(256)
        with open(path, "wb") as handle:
            handle.write(bytes(raw[:rng.randint(0, len(raw))]))
        table = Customization(folder, extras=True).snapshot.playbooks
        assert isinstance(table, PB.Table) and len(table.teams) == 32
        assert all(1 <= len(table.name(i)) <= 200 for i in D.PLAYS)
        for key, book in table.styles.items():
            assert all(0 < w <= 100 for w in list(book.offense.values()) + list(book.defense.values()))
            assert all(all(abs(v) <= b for v, b in zip(t.mod, D.BOUNDS)) for t in book.tilts.values())
        assert all(a in D.BOOK_KEYS and b in D.BOOK_KEYS for a, b in table.teams)


# ----- what the review of SX.7 found -----

@pytest.mark.parametrize("value", ["families 3; vs 1; sack +-3", "families 3 --4; vs 1", "families 3; vs 1; comp ²",
                                   "families 3; vs 1; comp ٣", "families 3; vs 1; ylo 1e0", "families 3; vs 1; yhi ++1"])
def test_a_number_str_isdigit_accepts_and_int_refuses_is_a_problem_not_a_lost_file(value):
    table, problems = table_of("styles", "S2OB1 = %s\n" % value)
    assert table.styles["west"].tilts["OB1"] == PB.DEFAULT_TABLE.styles["west"].tilts["OB1"] and problems.count == 1


def test_one_bad_number_never_costs_the_rest_of_the_file():
    table, problems = table_of("styles", "S1QB = 500\nS2OB1 = families 3; vs 1; sack +-3\nS2O017 = weight ²\nS3QB = ³\n"
                                         "S4QB = 77\nS5QB = %s\nS6O001 = weight %s\n" % ("9" * 5000, "9" * 5000))
    assert table.styles["pro"].qb_percent == 500 and table.styles["power"].qb_percent == 77
    assert table.styles["zone"].qb_percent == PB.DEFAULT_TABLE.styles["zone"].qb_percent
    assert table.styles["air"].qb_percent == PB.DEFAULT_TABLE.styles["air"].qb_percent
    assert problems.count == 5                                          # the five bad lines, one problem each
    assert table.styles["west"].offense == PB.DEFAULT_TABLE.styles["west"].offense


def test_a_style_with_no_quarterback_runs_for_the_computer_plays_a_whole_game(tmp_path):
    from dataclasses import replace
    from nflrig import QUARTERBACKS, RecordingRules, SimEngine
    from pagrig import make_rig
    book = replace(PB.DEFAULT_TABLE.styles["option"], qb_percent=0)
    rules = RecordingRules(penalties_on=True, qb_on=True, playbooks_on=True)
    rules.forced = (("option", "option"), ("classic", "classic"))
    rig = make_rig(tmp_path, rng=random.Random(11), fast=True, vtrnt=2)
    rig.game.playbook_table = PB.Table(PB.DEFAULT_TABLE.names, PB.DEFAULT_TABLE.disabled,
                                       dict(PB.DEFAULT_TABLE.styles, option=book), PB.DEFAULT_TABLE.teams)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    result = engine.run()
    assert result.scores[0] != result.scores[1]
    designed = [e for e in rules.qb.events if e[2] in ("keeper", "draw") and e[1] == 1]
    assert designed == []                                               # side 1 played Option with 0 percent: no keeper or draw
