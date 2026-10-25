"""penalties.txt: the fouls' names, switches and weights (nfl4 only, rule 0.13; CUSTOMIZABLE_CONTENT 13 L14, CLAUDE.md 0.12,
playbook 7.9 and 7.10; PX SX.3). This is inspired by Jim Kitchen.

The defaults are STRINGS_NX's foul names; a player's line renames, `; off` switches a foul off, `; weight N` changes its
chance; the yards are never in the file; it heals like every list of the customize folder and is read only with the
N. F. L. rules.
"""
import os
import random

import pytest

from filedamage import BYTE_DAMAGES, apply, holding
from nfl4.data import customlists as cl
from nfl4.data.customize import Customization
from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import penalty_list as PL

GAME = "NFL Football 4"


def write(folder, body):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "penalties.txt"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(cl.render_list(GAME, "penalties", PL.NOTES, []) + body)


def table_of(body):
    problems = cl.Problems("penalties.txt")
    text = cl.render_list(GAME, "penalties", PL.NOTES, []) + body
    return PL.table_of(cl.parse_list(text, GAME, "penalties").entries, problems), problems


def test_the_defaults_are_the_foul_names_of_strings_nx_and_the_file_lists_them():
    assert PL.default_entries() == [(i, X.text(F.name_id(i))) for i in F.IDS]
    assert PL.DEFAULT_TABLE.name("P03") == "off sides" and PL.DEFAULT_TABLE.percent("P08") == 100
    text = Customization.__new__(Customization).default_text("penalties")
    assert text.startswith("# NFL Football 4 penalties, format 1.\n")
    parsed = cl.parse_list(text, GAME, "penalties")
    assert [(e.id, e.value) for e in parsed.entries] == PL.default_entries() and parsed.bad_lines == []


def test_a_line_renames_switches_off_or_weighs_a_foul():
    table, problems = table_of("P08 = hold on the line\nP1 = early jump; off\np12 = interference; weight 50\n"
                               "P13 = offensive pass interference; weight 200; on\n")
    assert table.name("P08") == "hold on the line" and table.percent("P08") == 100
    assert table.name("P01") == "early jump" and table.percent("P01") == 0
    assert table.percent("P12") == 50 and table.percent("P13") == 200 and problems.count == 0
    assert table.name("P09") == X.text("NXP-F09")


def test_bad_lines_are_problems_and_keep_the_originals():
    table, problems = table_of("P27 = new foul\nP08 = holding; weight 300\nP08 = again\nP09 = a, b\nP10 = ; off\n"
                               "P11 = contact; sometimes\n")
    assert table.percent("P08") == 100 and table.name("P09") == X.text("NXP-F09")
    assert table.percent("P10") == 0 and table.name("P10") == X.text("NXP-F10")     # the off still counts
    assert table.name("P11") == "contact" and table.percent("P11") == 100
    assert problems.count == 5                                        # counted per entry: P08's two faults are one


def test_the_yards_are_not_in_the_file_and_cannot_be_given_there():
    assert all(not any(c.isdigit() for c in name) for _, name in PL.default_entries())
    table, problems = table_of("P08 = holding; yards 5\n")
    assert table.percent("P08") == 100 and problems.count == 1


def test_penalties_txt_is_read_only_with_the_nfl_rules_and_its_problems_said_once(tmp_path):
    folder = str(tmp_path / "customize")
    classic = Customization(folder)
    assert not os.path.exists(os.path.join(folder, "penalties.txt")) and classic.snapshot.fouls is None
    write(folder, "P08 = grab; off\nP99 = nothing\n")
    custom = Customization(folder, extras=True)
    assert custom.snapshot.fouls.percent("P08") == 0 and custom.snapshot.fouls.name("P08") == "grab"
    assert " 1 problem found in penalties.txt, details are in the log. " in custom.take_notices()
    assert custom.take_notices() == []
    custom.use_extras(False)
    assert custom.snapshot.fouls is None
    custom.use_extras(True)
    assert custom.snapshot.fouls.name("P08") == "grab"


def test_the_game_takes_the_table_when_the_rules_are_switched_on(tmp_path):
    from pagrig import make_rig
    rig = make_rig(tmp_path)
    folder = str(tmp_path / "customize")
    write(folder, "P01 = jumped early\n")
    rig.game.customization = Customization(folder)
    rig.game.apply_customization()
    assert rig.game.foul_table is None
    rig.game.options.settings.game.rules = "nfl"
    rig.game.apply_rules_setting()
    assert rig.game.foul_table.name("P01") == "jumped early"


@pytest.mark.parametrize("kind", BYTE_DAMAGES)
def test_a_damaged_penalties_txt_is_copied_aside_and_made_again_or_read_in_part(tmp_path, kind):
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "penalties.txt")
    original = open(path, "rb").read()
    apply(kind, path)
    damaged = open(path, "rb").read()
    custom = Customization(folder, extras=True)
    notices = custom.take_notices()
    table = custom.snapshot.fouls
    assert isinstance(table, PL.FoulTable)
    if kind in ("cut_in_half", "bad_line_in_the_middle"):
        assert not os.path.exists(path + ".damaged1")
        assert all(table.percent(i) == 100 for i in F.IDS)
    else:
        assert open(path + ".damaged1", "rb").read() == damaged
        assert open(path, "rb").read() == original
        assert (" The file penalties.txt was damaged and has been reset to the original penalty names. A copy was saved. "
                in notices)
        assert table == PL.DEFAULT_TABLE


def test_a_penalties_txt_held_by_another_program_keeps_the_loaded_table(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "P08 = mine\n")
    custom = Customization(folder, extras=True)
    with holding(os.path.join(folder, "penalties.txt")):
        notices = custom.reload()
    assert any("penalties.txt is in use by another program. The penalty names you already had stay in use." in n
               for n in notices)
    assert custom.snapshot.fouls.name("P08") == "mine"


def test_reset_keeps_the_players_penalties_txt(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "P08 = mine\n")
    custom = Customization(folder, extras=True)
    result = custom.reset("penalties")
    assert result.done == ["penalties.txt"] and result.kept == ["penalties.txt"]
    assert "mine" in open(os.path.join(folder, "penalties.txt.before-reset"), encoding="utf-8").read()
    assert "penalties.txt: no problems." in custom.check()


def test_a_fuzz_of_damaged_penalties_files_never_raises_and_always_leaves_a_usable_table(tmp_path):
    rng = random.Random(31)
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "penalties.txt")
    good = open(path, "rb").read()
    for case in range(60):
        raw = bytearray(good)
        for _ in range(rng.randint(1, 20)):
            raw[rng.randrange(len(raw))] = rng.randrange(256)
        with open(path, "wb") as handle:
            handle.write(bytes(raw[:rng.randint(0, len(raw))]))
        table = Customization(folder, extras=True).snapshot.fouls
        assert isinstance(table, PL.FoulTable)
        assert all(0 <= table.percent(i) <= 200 and 1 <= len(table.name(i)) <= 30 for i in F.IDS)
