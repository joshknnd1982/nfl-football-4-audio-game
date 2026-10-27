"""Neutral ratings equal Classic (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 5.3 N1 to N3, B-P65, B-P66, SX.8b). This is inspired by
Jim Kitchen.

N1 every row of spec 5.9 and 5.10 read through the Franchise's modifiers with every rating 70 (and with no ratings) is the
original's; N2 a seeded whole game with the N. F. L. rules and franchise rosters of 70s gives the same spoken and sound transcript
and the same trace of draw sizes as the same game with the same rosters handed in without ratings; N3 a seeded whole season of the
season engine with every strength equal (70 or any other value) gives the same draws, sentences, records and bracket as the
classic engine. N4 (the golden Classic transcript, the franchise folder never made with Rules = Classic) is test_pag_golden.py and
test_fr_mode.py: nothing here touches them.
"""
import random

import pytest

from frratings import rated_roster, state_with
from nflrig import sim_game
from pagrig import named_roster, sounds_played, texts
from test_season_games import Season
from test_fr_strength import EVEN, league_store, two_levels

from nfl4.extras.franchise.mode import FranchiseHooks
from nfl4.extras.franchise import ratings as R
from nfl4.extras.playbooks import PlaybookModifiers
from nfl4.extras.qb_runs import make_entry
from nfl4.game.playtables import FIELD_GOAL_ODDS, FUMBLE_ODDS, PASSES, PUNT_ODDS, PUNT_SHORTEST, RUNS, QBRunEntry
from nfl4.game.setup import Roster


# ----- N1 -----

def test_n1_every_row_is_the_originals_with_every_rating_70_for_every_pair_of_slots():
    own, opponent = rated_roster("", 70), rated_roster("O", 70)
    m = R.FranchiseModifiers()
    keeper = QBRunEntry("keeper", 4, 3, -3, 6, 90)
    for offense_play in (1, 2, 3, 4, 5, 8, 9, 10):
        for carrier in range(1, 7):
            for d1 in range(1, 18):
                for d2 in range(1, 18):
                    if d1 == d2:
                        continue
                    m.bind(state_with(own, opponent, 1, carrier, d1, d2, offense_play))
                    assert m.gap("run") == m.gap("pass") == m.gap("qb") == 0
                    assert m.mod_for("run") is None and m.mod_for("pass") is None and m.mod_for("qb") is None
                    assert m.mod_for("fumble") is None
    assert len(RUNS) + len(PASSES) == 30
    for key, entry in RUNS.items():
        assert m.run(*key, entry) is entry
    for key, entry in PASSES.items():
        assert m.pass_(*key, entry) is entry
    assert m.qb_run(keeper) is keeper
    for key in ("sneak", "keeper", "draw"):                                    # and the real quarterback rows of the table
        for call in range(1, 7):
            entry = make_entry(key, call)
            assert m.qb_run(entry) is entry
    assert m.fumble_odds(1) == FUMBLE_ODDS and m.field_goal_odds(1) == FIELD_GOAL_ODDS
    assert m.punt(1) == (PUNT_ODDS, PUNT_SHORTEST) and m.punt(2) == (PUNT_ODDS, PUNT_SHORTEST)


def test_n1_a_roster_with_no_ratings_is_read_as_the_playbooks_object_reads_it():
    own, opponent = named_roster(""), named_roster("O")
    assert not own.ratings and not opponent.ratings
    m, plain = R.FranchiseModifiers(), PlaybookModifiers()
    m.bind(state_with(own, opponent, 1, 3, 5, 9, 4))
    for key, entry in RUNS.items():
        assert m.run(*key, entry) is entry and plain.run(*key, entry) is entry
    for key, entry in PASSES.items():
        assert m.pass_(*key, entry) is entry
    assert (m.fumble_odds(2), m.field_goal_odds(2), m.punt(1)) == (plain.fumble_odds(2), plain.field_goal_odds(2), plain.punt(1))


# ----- N2 -----

def plain_copy(roster: Roster) -> Roster:
    """The same names and quarterback, no ratings: what every game that is not a Franchise game has."""
    copy = Roster(list(roster.running_backs), list(roster.receivers), list(roster.defense), list(roster.special_teams),
                  list(roster.kickers), quarterback=roster.quarterback)
    assert copy.ratings == {}
    return copy


def transcript(tmp_path, seed, own, opponent):
    rig, engine, rules, result = sim_game(tmp_path, seed, own_names=own, opponent_names=opponent, quarterbacks=("QB", "OQB"),
                                          trace=True)
    return texts(rig), sounds_played(rig), list(rig.rnd.trace), result.scores, rig.game.rnd.fallbacks


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_n2_a_game_of_70s_through_the_franchise_seams_equals_the_same_game_without_ratings(tmp_path, seed):
    rated = transcript(tmp_path / "rated", seed, rated_roster("", 70), rated_roster("O", 70))
    plain = transcript(tmp_path / "plain", seed, plain_copy(rated_roster("", 70)), plain_copy(rated_roster("O", 70)))
    assert rated == plain
    assert len(rated[0]) > 300 and len(rated[2]) > 1000 and rated[4] == 0


def test_n2_the_franchise_game_has_the_leagues_players_and_no_drawn_name(tmp_path):
    own, opponent = rated_roster("A", 70), rated_roster("B", 70)
    rig, engine, rules, result = sim_game(tmp_path, 7, own_names=own, opponent_names=opponent, quarterbacks=("Ace", "Bob"))
    s = engine.s
    assert s.rosters[1].names() == own.names() and s.rosters[2].names() == opponent.names()
    assert s.quarterbacks == {1: "Ace", 2: "Bob"}
    assert s.rosters[1].ratings == own.ratings and s.rosters[2].ratings == opponent.ratings        # H7: the ratings come along
    assert s.rosters[1].quarterback == "AQB" and s.rosters[2].quarterback == "BQB"
    assert s.player_names == own.running_backs + own.receivers + own.defense + opponent.running_backs + opponent.receivers + opponent.defense
    said = " ".join(texts(rig))
    assert "Ace" in said and "Bob" in said                                   # the quarterbacks of the league, never asked for


# ----- N3 -----

def season_record(tmp_path, seed, hooks=None):
    rng = random.Random(seed)
    own = (rng.randint(1, 8), rng.randint(1, 4))
    season = Season(tmp_path, seed, "random", own)
    if hooks is not None:
        season.game.season_hooks = hooks
    season.game.rnd.trace = []
    season.regular_season()
    if season.game.season.gtp in (17, 18):
        season.playoffs()
    game, rig = season.game, season.rig
    return (texts(rig), list(rig.store.events), list(game.rnd.trace), game.season.records.as_file_values(), game.season.gtp)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("level", [EVEN, 78 * 50, 0])
def test_n3_a_season_with_every_strength_equal_is_the_classic_season(tmp_path, seed, level):
    classic = season_record(tmp_path / "classic", seed)
    equal = season_record(tmp_path / "equal", seed, FranchiseHooks(league_store([level] * 32)))
    assert classic == equal
    assert len(classic[2]) > 1000


def test_n3_a_season_in_a_league_with_a_spread_differs_from_the_classic_one_and_stays_a_season(tmp_path):
    classic = season_record(tmp_path / "classic", 3)
    leaning = season_record(tmp_path / "leaning", 3, FranchiseHooks(league_store(two_levels())))
    assert classic[0] != leaning[0] and classic[2] != leaning[2]
    records = leaning[3]
    assert sum(records[0::2]) == sum(records[1::2])                     # a win for every loss
    assert all(records[2 * t] + records[2 * t + 1] == 16 for t in range(32))
