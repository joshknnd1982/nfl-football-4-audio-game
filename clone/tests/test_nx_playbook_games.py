"""Whole games with the playbooks: the computer on both sides and a seeded player through the two-level menus (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 10; PX SX.7). This is inspired by Jim Kitchen.

The 10,000-game balance test of design 10.3 is work/calibrate_playbooks_sx7.py (its report: work/calibrate_playbooks_sx7_10000.txt);
here a few seeded games per style check the properties in every suite run: a winner, a valid record, every call a play of the
catalog and of the side's own style, the modifiers never left armed, the same seed the same game.
"""
import random

import pytest

from nfl4.extras import playbook_data as D
from nfl4.extras import playbooks as PB
from nfl4.extras.plays import catalog as C
from nflrig import RecordingRules, sim_game
from pagrig import make_rig, play

ENTER, ESCAPE, DOWN, F1, F2, F3, F4, BACKSPACE, LEFT = 13, 27, 40, 112, 113, 114, 115, 8, 37
CLASSIC = ("classic", "classic")


def rules_with(forced):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    rules.forced = forced
    return rules


def games_of(tmp_path, forced, seeds):
    return [sim_game(tmp_path / ("s%d" % seed), seed, rules=rules_with(forced)) for seed in seeds]


@pytest.mark.parametrize("style", D.STYLES, ids=lambda s: s.key)
def test_a_game_of_a_style_against_classic_ends_with_a_winner_and_calls_only_its_own_plays(tmp_path, style):
    for rig, engine, rules, result in games_of(tmp_path, ((style.key, style.key), CLASSIC), range(300, 303)):
        assert result.scores is not None and result.scores[0] != result.scores[1]
        assert rig.rnd.fallbacks == 0 and engine.noise_net == 0
        engine.s.extras.check()
        assert engine.s.extras.offense_book == [style.key, "classic"] and engine.s.extras.defense_book == [style.key, "classic"]
        offense = {i for i, _w in style.offense}
        defense = {i for i, _w in style.defense}
        calls = rules.books.events
        assert len(calls) > 100
        # SX.10e (D-095): side 1 uses a playbook, so the game plays the catalog and side 1 calls over the WHOLE catalog (calling.py), not
        # only its style's SX.7 plays; side 2's Classic book calls nothing, and side 1's defense against side 2's original plays is SX.7's
        fakes = sum(1 for what, side, *_x in rules.kicks.events if what == "fake" and side == 1)   # a fake kick runs with no call
        empty = 0
        for side, off_id, def_id, family, d_family, kind, yards in calls:
            if side == 1:
                if off_id == "" and family <= 5:
                    empty += 1
                    continue
                assert (off_id == "" and family > 5) or (off_id in C.BY_ID and (C.BY_ID[off_id].side == "O" or off_id == "K026")), \
                    (off_id, family)
            else:
                assert off_id == ""                                    # Classic calls no play of a playbook
        assert empty <= fakes, (empty, fakes)
        assert any(off_id not in offense for side, off_id, *_x in calls if side == 1 and off_id)
        by_defender = [(c[0], c[2], c[4]) for c in calls]
        assert all(d == "" or d in defense and D.PLAYS[d].family == fam for side, d, fam in by_defender if side == 2)
        assert all(d == "" for side, d, fam in by_defender if side == 1)
        assert rules.modifiers.mod is None                              # no play's modifiers stay armed after its end


def test_a_game_of_two_styles_calls_over_the_whole_catalog_on_both_sides(tmp_path):
    # SX.10e (D-095): both sides call over the catalog (extras/plays/calling.py) and the outcome models play every call
    forced = (("air", "pressure"), ("power", "west"))
    for rig, engine, rules, result in games_of(tmp_path, forced, range(310, 313)):
        assert result.scores[0] != result.scores[1] and rig.rnd.fallbacks == 0
        fakes = sum(1 for what, *_x in rules.kicks.events if what == "fake")      # a fake kick runs with no call
        events = rules.books.events
        empty = [e for e in events if e[1] == ""]
        assert len(empty) <= fakes, (empty, fakes)
        for side, off_id, def_id, family, d_family, kind, yards in events:
            if off_id == "":
                continue
            assert off_id in C.BY_ID and (C.BY_ID[off_id].side == "O" or off_id == "K026"), (side, off_id)
            assert def_id in C.BY_ID and C.BY_ID[def_id].side == "D", (side, def_id)
        played = rules.offense.events
        assert len(played) > 100 and {p for p, *_x in played} - {i for s in D.STYLES for i, _w in s.offense}


def test_the_same_seed_is_the_same_game_with_a_style_on_each_side(tmp_path):
    forced = (("zone", "option"), ("west", "air"))
    first = games_of(tmp_path / "a", forced, [321])[0]
    second = games_of(tmp_path / "b", forced, [321])[0]
    assert first[3].scores == second[3].scores and first[2].books.events == second[2].books.events


def test_a_classic_side_calls_nothing_and_a_game_of_classic_books_draws_nothing_extra(tmp_path):
    games = games_of(tmp_path, (CLASSIC, CLASSIC), [330])
    rules = games[0][2]
    assert all(call[1] == "" and call[2] == "" for call in rules.books.events)
    assert rules.books.in_use(games[0][1].s.extras) is False


def test_the_catalog_names_a_player_changed_are_what_the_menu_says(tmp_path):
    rig = make_rig(tmp_path, rng=random.Random(5), fast=True, vtrnt=2)
    names = dict(PB.DEFAULT_TABLE.names)
    names["O001"] = "Zone Dive"
    rig.game.playbook_table = PB.Table(names, PB.DEFAULT_TABLE.disabled, PB.DEFAULT_TABLE.styles, PB.DEFAULT_TABLE.teams)
    rig.keys.policy = menu_policy(rig, 6)
    program_rules = RecordingRules(offense_book="west", defense_book="pressure", playbooks_on=True, qb_on=True)
    result = play(rig, rules=program_rules)
    assert result.scores is not None
    assert " 1. Zone Dive " in [t for t, _, _ in rig.said]


# ----- a player through the two-level menus -----

def menu_policy(rig, seed):
    """Enter, digits, Right (SX.10c), Down, Backspace, Left, the letters B and T, plus, F1 to F4; Escape answered no; never Save Game."""
    rng = random.Random(seed)

    def policy(keys):
        last = rig.said[-1][0] if rig.said else ""
        if last.endswith("Save Game "):
            return DOWN
        if "concede" in last:
            return "n"
        if last.endswith("Time Out ") and rng.random() < 0.6:
            return ENTER
        roll = rng.random()
        if roll < 0.40:
            return ENTER
        if roll < 0.62:
            return str(rng.randint(1, 9))
        if roll < 0.70:
            return 39               # Right: a family's lists (SX.10c)
        if roll < 0.77:
            return rng.choice((BACKSPACE, LEFT, "b"))
        if roll < 0.80:
            return "t"
        if roll < 0.84:
            return 187              # plus: a favourite (SX.10c)
        if roll < 0.91:
            return DOWN
        if roll < 0.99:
            return rng.choice((F1, F2, F3, F4))
        return ESCAPE
    return policy


@pytest.mark.parametrize("seed", range(6))
def test_a_whole_game_through_the_two_level_menus(tmp_path, seed):
    rig = make_rig(tmp_path, rng=random.Random(700 + seed), fast=True, vtrnt=1 + seed % 2)
    rig.keys.policy = menu_policy(rig, 800 + seed)
    book = ("west", "air", "power", "pressure", "zone", "option")[seed]
    program_rules = RecordingRules(auto_sides=(2,), penalties_on=True, qb_on=True, challenges_on=True, onside_on=True,
                                   offense_book=book, defense_book="pressure" if seed % 2 else "team", playbooks_on=True)
    result = play(rig, rules=program_rules)
    rules = program_rules.used
    assert rules is not None and result.scores is not None and result.scores[0] != result.scores[1]
    assert rig.rnd.fallbacks == 0
    said = [t for t, _, _ in rig.said]
    # a list of plays was opened at least once (its heading, SX.10c, or its Back item); SX.10d's defense has lists, not SX.7's groups
    assert " 1. Line Plunge " in said and any(t.strip().endswith(". Back") or ", list " in t for t in said)
    # SX.10c: the player's offense calls the catalog's plays through its menus, the defense the style's (SX.7, until SX.10d)
    calls = rules.offense.events
    assert len(calls) > 10 and all(play.startswith("O") for play, _call, _kind, _yards, _branch in calls)
    defended = rules.defense.events                                 # SX.10d: the player's defense calls the catalog's calls
    assert defended and all(call.startswith("D") and play.startswith("O") for play, call, _k, _y, _b, _x in defended)
    rules.state.extras.check()
