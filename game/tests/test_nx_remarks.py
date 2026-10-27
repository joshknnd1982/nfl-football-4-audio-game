"""The remark pools of the extras and remarks.txt (nfl4 only, rule 0.13; CUSTOMIZABLE_CONTENT 13, CLAUDE.md 0.12, playbook 7.9
and 7.10; PX SX.2: the timeout pool TO). This is inspired by Jim Kitchen.

The defaults are STRINGS_NX's lines; a player's line replaces, `off` switches off, a new number adds; the draw is never one of
the last three spoken; F8 silences the pool before any draw; remarks.txt heals like every list of the customize folder.
"""
import os
import random

import pytest

from filedamage import BYTE_DAMAGES, apply, holding
from nfl4.data import customlists as cl
from nfl4.data.customize import Customization
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.game.banter_markup import Bleep, Pause, Speak, Text
from nflrig import nfl_engine_rig
from randsources import ScriptedRandom, below_value, value_for

GAME = "NFL Football 4"


# ----- the defaults -----

def test_the_timeout_pool_is_the_five_lines_of_strings_nx_with_their_exact_spaces():
    lines = RM.DEFAULT_POOLS.lines("TO")
    assert [r.id for r in lines] == ["TO01", "TO02", "TO03", "TO04", "TO05"] == list(X.REMARK_POOLS["TO"])
    for remark in lines:
        assert remark.builtin and remark.pieces == (Speak((Text(X.TEXTS[remark.id]),)),)
        assert remark.markup == X.TEXTS[remark.id].strip()
    assert RM.POOLS_BUILT == ("TO", "CHS", "CHC", "RVR", "RVC", "ON", "QB", "PN") + RM.BROADCAST_POOLS   # SX.3 added the penalty remarks, SX.4 the
    #                                                             onside remarks, SX.5 the quarterback's lines (play-by-play:
    #                                                             F8 never silences them), SX.6 the four pools of the replay
    assert [r.id for r in RM.DEFAULT_POOLS.lines("PN")] == list(X.REMARK_POOLS["PN"]) == ["PN01", "PN02", "PN03", "PN04"]


def test_the_file_of_the_defaults_lists_every_default_line(tmp_path):
    entries = RM.default_entries()
    assert entries == [(r.id, r.markup) for pool in RM.POOLS_BUILT for r in RM.DEFAULT_POOLS.lines(pool)]
    text = Customization(str(tmp_path / "customize")).default_text("remarks")
    assert text.startswith("# NFL Football 4 remarks, format 1.\n")
    parsed = cl.parse_list(text, GAME, "remarks")
    assert [(e.id, e.value) for e in parsed.entries] == entries and parsed.bad_lines == []


@pytest.mark.parametrize("entry_id, parsed", [("TO03", ("TO", 3)), ("to3", ("TO", 3)), ("To0003", ("TO", 3)),
                                              ("TO06", ("TO", 6)), ("TO9999", ("TO", 9999)), ("TO0", None),
                                              ("TO10000", None), ("PN01", ("PN", 1)), ("CHS01", ("CHS", 1)),
                                              ("rvc03", ("RVC", 3)), ("B001", None), ("TOX", None)])
def test_remark_ids(entry_id, parsed):
    assert RM.parse_id(entry_id) == parsed


# ----- the player's lines -----

def entries_of(text):
    return cl.parse_list(cl.render_list(GAME, "remarks", RM.NOTES, []) + text, GAME, "remarks").entries


def pools_of(text):
    problems = cl.Problems("remarks.txt")
    return RM.build_pools(RM.overrides_of(entries_of(text), problems), problems), problems


def test_a_line_is_changed_switched_off_added_or_kept_when_it_is_bad():
    pools, problems = pools_of("TO02 = what a call [bleep]\nTO03 = off\nTO06 = [pause] <team> stop it\n"
                               "TO04 = [unclosed\nTO07 = [sound ../x.wav]\nto05 = " + X.TEXTS["TO05"].strip() + "\n")
    lines = {r.id: r for r in pools.lines("TO")}
    assert sorted(lines) == ["TO01", "TO02", "TO04", "TO05", "TO06"]
    assert lines["TO02"].pieces == (Speak((Text("what a call"),)), Bleep()) and not lines["TO02"].builtin
    assert lines["TO06"].pieces == (Pause(), Speak((Text("<team> stop it"),)))
    assert lines["TO04"].builtin and lines["TO05"].builtin                 # bad: the original; exactly the original: builtin
    assert problems.count == 2                                              # TO04 and TO07


def test_an_unknown_placeholder_is_counted_and_spoken_as_written():
    pools, problems = pools_of("TO06 = <score> and <team>\n")
    assert [r.id for r in pools.lines("TO")][-1] == "TO06"
    assert problems.count == 1 and "<score>" in problems.messages[0]


def test_ids_that_are_not_remarks_twice_or_empty_are_problems():
    pools, problems = pools_of("B001 = no\nXY01 = no\nTO02 = first\nTO02 = second\nTO03 =\n")
    assert {r.id: r for r in pools.lines("TO")}["TO02"].pieces == (Speak((Text("first"),)),)
    assert problems.count == 4


def test_the_example_of_the_players_guide_works_as_written():
    from pathlib import Path
    guide = (Path(__file__).resolve().parent.parent / "CUSTOMIZE.md").read_text(encoding="utf-8")
    example = next(line.strip() for line in guide.splitlines() if line.strip().startswith("TO06 = "))
    pools, problems = pools_of(example + "\n")
    assert problems.count == 0
    assert pools.lines("TO")[-1].pieces == (Speak((Text("the <team> stop the clock."),)), Bleep())


def test_every_line_off_means_silence():
    pools, _ = pools_of("".join("TO%02d = off\n" % n for n in range(1, 6)))
    assert pools.lines("TO") == ()


# ----- the draw and the line -----

def strict_game(tmp_path, values, comments=True):
    rig = nfl_engine_rig(tmp_path, comments=comments)
    rig.rnd.source = ScriptedRandom(values, strict=True)
    rig.rnd.trace = []
    return rig


def test_a_line_is_never_one_of_the_last_three_spoken_when_the_pool_has_more(tmp_path):
    rig = strict_game(tmp_path, [value_for(5, 2), value_for(5, 4), value_for(5, 1)])
    record = rig.engine.s.extras
    record.recent["TO"] = ["TO02", "TO04", "TO05"]
    remark = RM.say_remark(rig.game, rig.engine.s, record, "TO", {})
    assert remark.id == "TO01" and rig.rnd.trace == [5, 5, 5]
    assert record.recent["TO"] == ["TO04", "TO05", "TO01"]
    assert [t for t, _, _ in rig.said] == [X.TEXTS["TO01"]]


def test_a_pool_of_three_or_fewer_draws_once_whatever_was_said(tmp_path):
    pools, _ = pools_of("TO04 = off\nTO05 = off\n")
    rig = strict_game(tmp_path, [value_for(3, 2)])
    rig.game.remark_pools = pools
    record = rig.engine.s.extras
    record.recent["TO"] = ["TO02"]
    assert RM.say_remark(rig.game, rig.engine.s, record, "TO", {}).id == "TO02"
    assert rig.rnd.trace == [3]


def test_comments_off_silence_the_pool_before_any_draw(tmp_path):
    rig = strict_game(tmp_path, [], comments=False)
    assert RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "TO", {}) is None
    assert rig.said == [] and rig.rnd.trace == []


def test_placeholders_a_name_and_choices_are_filled_with_their_draws_in_line_order(tmp_path):
    pools, _ = pools_of("".join("TO%02d = off\n" % n for n in range(1, 6))
                        + "TO06 = <team> called it, [name] [one of: smiles | frowns], says <coach>\n")
    rig = strict_game(tmp_path, [value_for(1, 1), value_for(58, 3), value_for(2, 2)])
    rig.game.remark_pools = pools
    RM.say_remark(rig.game, rig.engine.s, rig.engine.s.extras, "TO", {"<team>": "Jets", "<coach>": "Kim",
                                                                        "<quarterback>": "Unitas"})
    assert rig.rnd.trace == [1, 58, 2]
    name = rig.engine.s.player_names[2]
    assert [t for t, _, _ in rig.said] == ["Jets called it, %s frowns, says Kim" % name]


# ----- remarks.txt in the customize folder (7.10) -----

def write(folder, text):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "remarks.txt"), "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(cl.header_line(GAME, "remarks") + "\n" + text)


def test_the_players_remarks_txt_is_read_and_its_problems_said_once(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "TO02 = off\nTO09 = <team> again\nTO04 = [oops\n")
    custom = Customization(folder, extras=True)
    assert [r.id for r in custom.snapshot.remarks.lines("TO")] == ["TO01", "TO03", "TO04", "TO05", "TO09"]
    assert custom.take_notices() == [" 1 problem found in remarks.txt, details are in the log. "]
    assert custom.take_notices() == []


@pytest.mark.parametrize("kind", BYTE_DAMAGES)
def test_a_damaged_remarks_txt_is_copied_aside_and_made_again_or_read_in_part(tmp_path, kind):
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "remarks.txt")
    original = open(path, "rb").read()
    apply(kind, path)
    damaged = open(path, "rb").read()
    custom = Customization(folder, extras=True)
    notices = custom.take_notices()
    pools = custom.snapshot.remarks
    if kind in ("cut_in_half", "bad_line_in_the_middle"):
        assert not os.path.exists(path + ".damaged1")
        assert [r.id for r in pools.lines("TO")] == ["TO01", "TO02", "TO03", "TO04", "TO05"]
    else:
        assert open(path + ".damaged1", "rb").read() == damaged
        assert open(path, "rb").read() == original
        assert notices == [" The file remarks.txt was damaged and has been reset to the original remarks. A copy was saved. "]
        assert pools.lines("TO") == RM.DEFAULT_POOLS.lines("TO")
        assert Customization(folder, extras=True).take_notices() == []    # the next start says nothing more
    if kind == "bad_line_in_the_middle":                                  # the file is kept: its count is said each start
        assert notices == [" 2 problems found in remarks.txt, details are in the log. "]


def test_a_remarks_txt_held_by_another_program_is_not_damage(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "TO01 = mine\n")
    custom = Customization(folder, extras=True)
    with holding(os.path.join(folder, "remarks.txt")):
        notices = custom.reload()
    assert any("remarks.txt is in use by another program. The remarks you already had stay in use." in n
               for n in notices)
    assert custom.snapshot.remarks.lines("TO")[0].pieces == (Speak((Text("mine"),)),)


def test_reset_of_one_list_offers_remarks_only_with_the_nfl_rules_and_keeps_the_players_file(tmp_path):
    folder = str(tmp_path / "customize")
    write(folder, "TO01 = mine\n")
    classic = Customization(folder)
    assert "remarks" not in [spec.key for spec in classic.specs]
    assert classic.reset(None).done == ["teams.txt", "divisions.txt", "surnames.txt"]      # BC.2: no banter.txt
    assert "mine" in open(os.path.join(folder, "remarks.txt"), encoding="utf-8").read()
    custom = Customization(folder, extras=True)
    result = custom.reset("remarks")
    assert result.done == ["remarks.txt"] and result.kept == ["remarks.txt"]
    assert "mine" in open(os.path.join(folder, "remarks.txt.before-reset"), encoding="utf-8").read()


def test_a_fuzz_of_damaged_remarks_files_never_raises_and_always_leaves_a_usable_pool(tmp_path):
    rng = random.Random(23)
    folder = str(tmp_path / "customize")
    Customization(folder, extras=True)
    path = os.path.join(folder, "remarks.txt")
    good = open(path, "rb").read()
    for case in range(60):
        raw = bytearray(good)
        for _ in range(rng.randint(1, 20)):
            raw[rng.randrange(len(raw))] = rng.randrange(256)
        with open(path, "wb") as handle:
            handle.write(bytes(raw[:rng.randint(0, len(raw))]))
        custom = Customization(folder, extras=True)
        assert isinstance(custom.snapshot.remarks, RM.RemarkPools)
        for remark in custom.snapshot.remarks.lines("TO"):
            assert remark.pieces
