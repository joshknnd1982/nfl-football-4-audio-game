"""The set-up of a game: the rosters, the banter names, the periods, the warnings. This is inspired by Jim Kitchen.

GAME_SPEC 5.5 "Set-up" and 11 (CODE (lifted) pag's GoSub 0x453eac): the order of the draws is the original's. A scripted
source plays it draw by draw.
"""
import random

import pytest

from gamerig import Rig
from nfl4.game.names import NamePool, load_surnames
from nfl4.game.rnd import GameRandom
from nfl4.game.setup import (COUNTS, DEFENSE_ITEMS, HEADINGS, OFFENSE_ITEMS, PERIODS, QUARTERBACK_HEADING, RUN_DIRECTIONS,
                             SNAP_WORDS, GameSetup, Roster, adopt_roster, draw_roster, new_game_setup)
from randsources import ScriptedRandom, draws
from specfiles import original_strings, strings_of_class

NAMES = load_surnames()


def full_script(own_slots, opponent_slots, plays=(1, 2, 3, 4, 5), warnings=(1, 2, 3)):
    """Rnd values: 33 slot draws for each side (rnd(1708) = slot), five rnd(8)+29 plays draws, three rnd(3) warnings."""
    pairs = [(1708, slot) for slot in own_slots] + [(1708, slot) for slot in opponent_slots]
    pairs += [(8, k) for k in plays] + [(3, k) for k in warnings]
    return draws(*pairs)


def test_the_headings_counts_and_texts_are_the_files_and_the_originals():
    assert HEADINGS == ("Running Backs:", "Receivers:", "Defensive Players:", "Special Teams Players:", "Kickers:")
    assert COUNTS == (6, 6, 17, 2, 2) and sum(COUNTS) == 33 and PERIODS == 5
    assert QUARTERBACK_HEADING == "Quarterback:"
    strings = original_strings()
    for text in HEADINGS + (QUARTERBACK_HEADING,) + SNAP_WORDS + RUN_DIRECTIONS + OFFENSE_ITEMS + DEFENSE_ITEMS:
        assert text in strings, text
    assert set(HEADINGS) <= set(strings_of_class("ROSTER-HEADING"))
    assert len(SNAP_WORDS) == 10 and len(RUN_DIRECTIONS) == 7 and len(OFFENSE_ITEMS) == 8 and len(DEFENSE_ITEMS) == 7


def test_the_draws_go_in_the_originals_order_own_team_then_the_opponent_then_periods_then_warnings():
    own = list(range(1, 34))                       # slots 1 to 33
    opponent = list(range(101, 134))               # slots 101 to 133
    source = ScriptedRandom(full_script(own, opponent, plays=(1, 8, 4, 5, 2), warnings=(1, 2, 3)), strict=True)
    setup = new_game_setup(GameRandom(source), NamePool(GameRandom(source)))
    assert source.left == 0 and source.drawn == 33 + 33 + 5 + 3          # 74 draws, no more, no fewer
    one, two = setup.rosters[1], setup.rosters[2]
    assert one.running_backs == NAMES[0:6] and one.receivers == NAMES[6:12] and one.defense == NAMES[12:29]
    assert one.special_teams == NAMES[29:31] and one.kickers == NAMES[31:33]            # kicker 1 first, then kicker 2
    assert two.running_backs == NAMES[100:106] and two.kickers == NAMES[131:133]
    assert setup.plays_per_period == [30, 37, 33, 34, 31]                                # Int(Rnd * 8) + 30
    assert setup.warnings == (5, 6, 7) and setup.own_names_drawn is True                # Int(Rnd * 3) + 5
    assert (setup.quarter, setup.countdown, setup.play_counter) == (1, 100, 1)
    assert setup.plays_in(1) == 30 and setup.plays_in(2) == 37 and setup.plays_in(5) == 31 and setup.plays_in(9) == 31


def test_the_banter_name_list_is_58_names_runningbacks_receivers_defense_of_each_side_in_order():
    source = ScriptedRandom(full_script(list(range(1, 34)), list(range(101, 134))), strict=True)
    setup = new_game_setup(GameRandom(source), NamePool(GameRandom(source)))
    assert len(setup.player_names) == 58
    assert setup.player_names[:29] == NAMES[0:29]                       # the player's 6 + 6 + 17
    assert setup.player_names[29:] == NAMES[100:129]                    # the opponent's 6 + 6 + 17
    assert not set(NAMES[29:33]) & set(setup.player_names)              # special teams players and kickers are not in it


def test_a_slot_that_was_used_is_drawn_again_so_no_name_is_on_both_teams():
    own = list(range(1, 34))
    # the opponent's draws 5, 6, 7 hit the player's used slots: each is drawn again, then slots 101 to 133 (33 names)
    opponent_script = [(1708, 5), (1708, 6), (1708, 7)] + [(1708, s) for s in range(101, 134)]
    pairs = [(1708, s) for s in own] + opponent_script + [(8, 1)] * 5 + [(3, 1)] * 3
    source = ScriptedRandom(draws(*pairs), strict=True)
    setup = new_game_setup(GameRandom(source), NamePool(GameRandom(source)))
    assert setup.rosters[2].running_backs == NAMES[100:106]
    assert not set(setup.rosters[1].names()) & set(setup.rosters[2].names())
    assert source.left == 0


def test_names_from_footplay_txt_replace_the_draws_blank_the_pool_and_need_no_new_file():
    own = Roster(["Aa%d" % i for i in range(6)], ["Bb%d" % i for i in range(6)], ["Cc%d" % i for i in range(17)],
                 ["Dd0", "Dd1"], ["Ee0", NAMES[40]])
    # one of the player's names is a real pool name (slot 41: kicker 2): the opponent's first draw of it is drawn again
    script = draws(*([(1708, 41)] + [(1708, s) for s in range(101, 134)] + [(8, 1)] * 5 + [(3, 1)] * 3))
    source = ScriptedRandom(script, strict=True)
    pool = NamePool(GameRandom(source))
    setup = new_game_setup(GameRandom(source), pool, own)
    assert setup.own_names_drawn is False
    assert setup.rosters[1].names() == own.names() and setup.rosters[1] is not own
    assert setup.player_names[:29] == own.running_backs + own.receivers + own.defense     # the typed ones too
    assert setup.rosters[2].running_backs == NAMES[100:106]                             # slot 41 was blank: drawn again
    assert pool.name(41) == ""
    assert len(setup.player_names) == 58


def test_an_incomplete_names_object_is_refused():
    with pytest.raises(ValueError):
        adopt_roster(NamePool(GameRandom()), Roster(["a"], ["b"], ["c"], ["d"], ["e"]), None)


def test_sections_come_in_the_files_order_with_their_headings():
    roster = draw_roster(NamePool(GameRandom(random.Random(1))), None)
    assert roster.is_complete()
    assert [heading for heading, _ in roster.sections()] == list(HEADINGS)
    assert [len(names) for _, names in roster.sections()] == list(COUNTS)
    assert len(roster.names()) == 33


def test_seeded_games_never_repeat_a_name_inside_a_game_and_keep_the_ranges():
    for seed in range(300):
        rnd = GameRandom(random.Random(seed))
        setup = new_game_setup(rnd, NamePool(rnd))
        names = setup.rosters[1].names() + setup.rosters[2].names()
        assert len(names) == 66 and len(set(names)) == 66
        assert all(30 <= n <= 37 for n in setup.plays_per_period) and len(setup.plays_per_period) == 5
        assert all(5 <= w <= 7 for w in setup.warnings)
        assert len(setup.player_names) == 58 and rnd.fallbacks == 0


def test_the_game_hands_the_warning_lengths_to_the_clock_and_resets_the_countdown():
    rig = Rig(rng=random.Random(8))
    rig.game.quarter_clock.countdown = 170
    setup = rig.game.new_game_setup()
    clock = rig.game.quarter_clock
    assert (clock.m2w, clock.m4w, clock.m5w) == setup.warnings and clock.countdown == 100
    assert isinstance(setup, GameSetup)
