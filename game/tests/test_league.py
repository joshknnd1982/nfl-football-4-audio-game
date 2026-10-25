"""The 32 teams and 8 divisions in memory, checked against the spec and the string table. This is inspired by Jim Kitchen.

GAME_SPEC 11 and 5.2 (GetTeams p_4321d0, SayStand's division array), CUSTOMIZABLE_CONTENT 3 and 4 (IDs T01 to T32, D1 to D8).
"""
import re

import pytest

from nfl4.game.league import DEFAULT_DIVISION_NAMES, DEFAULT_TEAM_NAMES, DIVISIONS, ORIGINAL_T24_NAME, PLACES, TEAM_COUNT, League
from specfiles import LIFT, need, original_strings, spec_team_lists, strings_of_class

# Q-026 (the owner, 2026-10-22): the one default that is not the original's. The spec and the string table keep the original's "Redskins"; the game says
# "Commanders" for T24, and nothing else differs.
RENAMED = {ORIGINAL_T24_NAME: "Commanders"}


def renamed(name):
    return RENAMED.get(name, name)


def test_there_are_32_teams_and_8_divisions_of_4_places():
    assert (DIVISIONS, PLACES, TEAM_COUNT) == (8, 4, 32)
    assert len(DEFAULT_TEAM_NAMES) == 32 and len(set(DEFAULT_TEAM_NAMES)) == 32
    assert len(DEFAULT_DIVISION_NAMES) == 8 and len(set(DEFAULT_DIVISION_NAMES)) == 8


def test_the_teams_are_in_the_order_of_the_specs_list():
    lists = spec_team_lists()
    assert len(lists) == 8 and all(len(names) == 4 for _, names in lists)
    league = League()
    for division, (label, names) in enumerate(lists, start=1):
        assert [league.team(division, place) for place in range(1, 5)] == [renamed(name) for name in names]


def test_the_division_names_are_the_specs_in_the_specs_order():
    labels = [label for label, _ in spec_team_lists()]
    assert labels == ["AFC North", "AFC East", "AFC West", "AFC South", "NFC North", "NFC East", "NFC West", "NFC South"]
    for label, name in zip(labels, DEFAULT_DIVISION_NAMES):
        conference, direction = label.split()
        assert name == ". ".join(conference) + ". " + direction + "."


def test_every_team_and_division_text_is_a_string_of_the_original():
    strings = original_strings()
    teams = set(strings_of_class("TEAM-NAME"))
    originals = [ORIGINAL_T24_NAME if name == RENAMED[ORIGINAL_T24_NAME] else name for name in DEFAULT_TEAM_NAMES]
    assert set(originals) <= teams
    for name in originals:
        assert name in strings
    spoken = set(strings_of_class("DIVISION-NAME"))
    league = League()
    assert {league.division_text(d) for d in range(1, 9)} == spoken
    assert "Forty Niners" in DEFAULT_TEAM_NAMES and "Sea hawks" in DEFAULT_TEAM_NAMES      # the speech spellings


def test_the_division_text_has_the_spaces_the_original_speaks_it_with():
    league = League()
    assert league.division_text(1) == " A. F. C. North. "
    assert league.division_text(8) == " N. F. C. South. "


def test_team_ids_run_from_t01_to_t32_in_the_originals_order():
    league = League()
    assert league.team_id(1, 1) == "T01"
    assert league.team_id(6, 4) == "T24" and league.team(6, 4) == "Commanders"     # Q-026: the owner renamed the original's "Redskins" (2026-10-22)
    assert league.team_id(8, 4) == "T32" and league.team(8, 4) == "Saints"
    ids = [league.team_id(d, p) for d in range(1, 9) for p in range(1, 5)]
    assert ids == ["T%02d" % n for n in range(1, 33)]


def test_the_cut_is_the_originals_array_index_division_plus_9_times_place():
    """GetTeams stores each name at byte offset 4 * (division + 9 * place) (GAME_SPEC 11); the lifted text shows 40 for
    Bengals (division 1, place 1) and 176 for Saints (division 8, place 4)."""
    lifted = need(LIFT / "p_4321d0_GetTeams.vb.txt").read_text(encoding="utf-8")
    league = League()
    found = 0
    for offset, name in re.findall(r'Me\.m294\(@(\d+)\) = "([^"]+)"', lifted):
        index = int(offset) // 4
        place, division = divmod(index, 9)
        assert 1 <= division <= 8 and 1 <= place <= 4, (offset, name)
        assert league.team(division, place) == renamed(name)
        found += 1
    assert found == 32


def test_a_league_needs_exactly_32_and_8_names_and_asks_for_real_teams():
    with pytest.raises(ValueError):
        League(team_names=DEFAULT_TEAM_NAMES[:31])
    with pytest.raises(ValueError):
        League(division_names=DEFAULT_DIVISION_NAMES[:7])
    league = League()
    for division, place in ((0, 1), (9, 1), (1, 0), (1, 5)):
        with pytest.raises(ValueError):
            league.team(division, place)
    with pytest.raises(ValueError):
        league.division_text(9)


def test_a_player_league_keeps_the_places_and_adds_the_spaces():
    names = ["Team %d" % n for n in range(1, 33)]
    divisions = ["North Group.", "B.", "C.", "D.", "E.", "F.", "G.", "H."]
    league = League(names, divisions)
    assert league.team(2, 3) == "Team 7" and league.division_text(1) == " North Group. "
