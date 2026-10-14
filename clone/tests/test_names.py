"""The surname pool and the two ways the original blanks names. This is inspired by Jim Kitchen.

GAME_SPEC 11, 5.5 and 4.12 (SetPlayerNames, pag's set-up, Getqbs), D-026 (the data stays as the original has it),
GAP_REGISTER G-D1 (bounded redraws).
"""
import logging
import random

import pytest

from nfl4.game.names import POOL_SIZE, NamePool, load_surnames, shipped_surnames_path
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, StuckRandom, draws
from specfiles import surnames_table


def pool_with(*values, names=None):
    return NamePool(GameRandom(ScriptedRandom(draws(*values) if values else [], strict=bool(values))), names)


def test_the_shipped_asset_is_the_spec_table_name_for_name():
    names = load_surnames()
    assert len(names) == POOL_SIZE == 1708
    assert names == surnames_table()
    assert shipped_surnames_path().endswith("surnames.txt")


def test_the_asset_keeps_the_originals_odd_names():
    names = load_surnames()
    assert 'Jones"' in names and "Maddox)" in names                 # D-026: kept as in the original data
    assert "Martínez" in names and "Márquez" in names               # the two Latin-1 letters, now UTF-8
    assert "Zoo lynn ski" in names                                  # a phonetic spelling for the speech engine
    assert len({name.lower() for name in names}) == 1708            # no duplicate ignoring case
    assert all(name == name.strip(" ") and name for name in names)


def test_a_pool_needs_exactly_1708_names():
    with pytest.raises(ValueError):
        NamePool(GameRandom(), ["a"] * 1707)


def test_a_draw_is_int_rnd_times_1708_plus_one_and_take_blanks_the_slot():
    pool = pool_with((1708, 1), (1708, 1708))
    names = load_surnames()
    assert pool.take() == names[0] and pool.name(1) == ""
    assert pool.take() == names[1707] and pool.name(1708) == ""
    assert pool.available() == 1706


def test_a_draw_that_hits_a_blank_slot_is_drawn_again_in_the_same_order():
    pool = pool_with((1708, 5), (1708, 5), (1708, 6))
    names = load_surnames()
    assert pool.take() == names[4]
    assert pool.take() == names[5]           # the second draw met the blank slot 5, the third gave slot 6
    assert pool.rnd.source.left == 0


def test_draw_slot_does_not_blank_the_slot_getqbs_blanks_it_only_when_the_name_is_accepted():
    pool = pool_with((1708, 9))
    slot = pool.draw_slot()
    assert slot == 9 and pool.name(9) == load_surnames()[8]


def test_names_read_from_footplay_txt_blank_the_first_equal_slot_with_exact_case():
    names = load_surnames()
    pool = pool_with()
    assert pool.blank_exact(names[10]) is True and pool.name(11) == ""
    assert pool.blank_exact(names[10]) is False                       # already blank: nothing left to blank
    assert pool.blank_exact(names[20].upper()) is False               # another case is another name
    assert pool.name(21) == names[20]
    assert pool.blank_exact("Typed Name") is False and pool.available() == 1707   # a typed name blanks nothing


def test_a_duplicate_pool_entry_is_blanked_one_at_a_time_for_the_file_names():
    names = ["Smith", "Smith"] + ["Name%d" % n for n in range(2, 1708)]
    pool = pool_with(names=names)
    assert pool.blank_exact("Smith") and pool.name(1) == "" and pool.name(2) == "Smith"


def test_a_quarterback_name_blanks_every_slot_that_equals_it_ignoring_case():
    names = ["Smith", "SMITH", "smith", "Jones"] + ["N%d" % n for n in range(4, 1708)]
    pool = pool_with(names=names)
    assert pool.blank_matching("sMiTh") == 3
    assert [pool.name(n) for n in (1, 2, 3, 4)] == ["", "", "", "Jones"]
    assert pool.blank_matching("nobody") == 0


def test_a_used_name_is_never_drawn_again_in_70_draws_of_a_game():
    for seed in range(40):
        pool = NamePool(GameRandom(random.Random(seed)))
        taken = [pool.take() for _ in range(70)]
        assert len(set(taken)) == 70
        assert pool.available() == 1708 - 70


def test_the_redraw_is_bounded_when_the_source_is_stuck_on_a_blank_slot(caplog):
    stuck = StuckRandom(0.0)                    # always slot 1
    pool = NamePool(GameRandom(stuck))
    names = load_surnames()
    assert pool.take() == names[0]
    with caplog.at_level(logging.WARNING, logger="nfl4.game"):
        assert pool.take() == names[1]          # slot 1 is blank for ever: the first free slot after 10,000 tries
    assert stuck.drawn == 1 + 10_000
    assert pool.rnd.fallbacks == 1


def test_a_pool_that_is_used_up_is_filled_again_with_a_warning(caplog):
    pool = NamePool(GameRandom(StuckRandom(0.0)))
    pool.slots = [""] * POOL_SIZE
    with caplog.at_level(logging.WARNING, logger="nfl4.game"):
        assert pool.take() == load_surnames()[0]
    assert any("filled again" in record.message for record in caplog.records)
    assert pool.available() == 1707
