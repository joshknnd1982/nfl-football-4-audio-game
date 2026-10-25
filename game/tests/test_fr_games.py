"""A franchise game: the league's players and ratings reach the game, the ratings are spoken, the games lean by strength (nfl4 only,
rule 0.13; NFL_FRANCHISE_DESIGN 5.1, 5.3, 13 H7 extended, SX.8b). This is inspired by Jim Kitchen.

* H7 extended: `adopt_roster` keeps the ratings and the quarterback, `new_game_setup` takes the opponent's roster in place of the 33
  draws, `Game.play_game` and `PlayEngine` pass it on;
* `FranchiseSeason.game_arguments` hands the opponent's team and both quarterbacks of the league to the game, so Getqbs asks nothing;
* NXF-09 after a new league and at the start of every season; the ratings and the potential in the roster; the team ratings item;
* whole games with both sides by the computer: the stronger roster wins more often, and a league of 70s plays the original's game.
"""
import random

import pytest

from frratings import rated_roster
from frrig import (COACH_AND_TEAM, DOWN, ENTER, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until, spoken)
from nflrig import sim_game
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import history
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import team_index, team_ref
from nfl4.game.names import NamePool, load_surnames
from nfl4.game.rnd import GameRandom
from nfl4.game.setup import Roster, adopt_opponent, adopt_roster, new_game_setup
from randsources import ScriptedRandom, draws

GAME = [ENTER, ENTER, ENTER]
INTO_FRANCHISE = [F9, DOWN, DOWN, DOWN, DOWN, ENTER]
NAMES = load_surnames()


def league(rig):
    return rig.fstore.league


# ----- H7 extended: the set-up -----

def test_adopt_roster_keeps_the_ratings_and_the_quarterback_in_a_copy():
    given = rated_roster("A", 70, rb2=88, qb=91)
    pool = NamePool(GameRandom(ScriptedRandom([], strict=True)))
    taken = adopt_roster(pool, given, [])
    assert taken.ratings == given.ratings and taken.ratings is not given.ratings and taken.quarterback == "AQB"
    assert taken.names() == given.names() and taken.running_backs is not given.running_backs
    plain = Roster(*[list(x) for x in (given.running_backs, given.receivers, given.defense, given.special_teams, given.kickers)])
    assert adopt_roster(NamePool(GameRandom(ScriptedRandom([], strict=True))), plain, []).ratings == {}     # Classic: none


def test_a_league_roster_blanks_no_name_of_the_pool_and_a_files_roster_still_does():
    def roster_of(names, rated):
        roster = Roster(names[0:6], names[6:12], names[12:29], names[29:31], names[31:33])
        if rated:
            roster.ratings = {(heading, number): 70 for heading, number, _ in D.PLACES}
        return roster
    for rated, blanked in ((True, 0), (False, 33)):
        pool = NamePool(GameRandom(ScriptedRandom([], strict=True)))
        before = pool.available()
        adopt_roster(pool, roster_of(NAMES[0:33], rated), [])
        assert before - pool.available() == blanked                # footplay.txt's 33 names are taken; the league's are not


def test_the_opponent_of_a_franchise_game_is_a_roster_and_nothing_is_drawn_for_it():
    own, opponent = rated_roster("A"), rated_roster("B", 70, d3=55)
    source = ScriptedRandom(draws(*([(8, k) for k in (1, 2, 3, 4, 5)] + [(3, k) for k in (1, 2, 3)])), strict=True)
    rnd = GameRandom(source)
    setup = new_game_setup(rnd, NamePool(rnd), own, opponent)
    assert source.drawn == 8 and source.left == 0                       # the five periods and the three warnings, no names
    assert setup.rosters[2].names() == opponent.names() and setup.rosters[2].ratings == opponent.ratings
    assert setup.rosters[2].ratings is not opponent.ratings and setup.rosters[2].quarterback == "BQB"
    assert setup.rosters[1].names() == own.names() and setup.own_names_drawn is False
    assert setup.banter_names == own.running_backs + own.receivers + own.defense + opponent.running_backs + opponent.receivers + opponent.defense


def test_without_an_opponent_roster_the_set_up_draws_33_names_as_the_original():
    source = ScriptedRandom(draws(*([(1708, k) for k in range(1, 67)] + [(8, 1)] * 5 + [(3, 1)] * 3)), strict=True)
    rnd = GameRandom(source)
    setup = new_game_setup(rnd, NamePool(rnd))
    assert source.drawn == 74 and setup.rosters[1].ratings == {} and setup.rosters[2].ratings == {}


def test_an_opponent_roster_must_be_whole():
    short = Roster(["a"], [], [], [], [])
    with pytest.raises(ValueError):
        adopt_opponent(short, [])


# ----- the game arguments of the program -----

def first_game(tmp_path, nfl=True, kind=None, keys=None):
    rig = franchise_rig(tmp_path, (keys if keys is not None else WANT_FRANCHISE + COACH_AND_TEAM) + GAME, nfl=nfl, kind=kind,
                        policy=enter_until(lambda: len(rig.plays) == 1 and rig.game.season.gtp == 2))
    return run_until(rig)


def test_a_franchise_game_gets_the_opponent_team_and_the_two_quarterbacks_of_the_league(tmp_path):
    rig = first_game(tmp_path)
    play, record = rig.plays[0], league(rig)
    opponent_team = team_index(*play["opponent"])
    expected = record.roster_for_game(opponent_team)
    assert play["opponent_names"].names() == expected.names() and play["opponent_names"].ratings == expected.ratings
    assert len(play["opponent_names"].ratings) == 34 and play["opponent_names"].is_complete()
    own = play["own_names"]
    assert own.names() == record.roster_for_game(record.team).names()
    quarterbacks = play["quarterback_names"](None)
    assert quarterbacks == (own.quarterback, expected.quarterback)
    assert quarterbacks == (record.player_at(record.team, 33).name, record.player_at(opponent_team, 33).name)
    assert opponent_team != record.team


def test_a_classic_season_and_the_original_get_no_opponent_roster_and_no_quarterback_names(tmp_path):
    classic_kind = first_game(tmp_path / "a", keys=[ENTER] + COACH_AND_TEAM)                    # the N. F. L. rules, a classic season
    original = first_game(tmp_path / "b", nfl=False, keys=COACH_AND_TEAM)                          # Rules = Classic: no question
    for rig in (classic_kind, original):
        assert rig.plays[0]["opponent_names"] is None and rig.plays[0]["quarterback_names"] is None
    assert classic_kind.game.program.mode.kind == "classic" and original.game.program.mode.kind == "classic"


# ----- the team's rating is spoken -----

def test_the_new_league_says_the_teams_rating_and_its_number_right_after_it_is_ready(tmp_path):
    rig = first_game(tmp_path)
    text, record = spoken(rig), league(rig)
    said = X.text("NXF-09", r=record.strength(record.team), k=record.rank_of(record.team))
    assert text.index(said) == text.index(X.text("NXF-07")) + 1
    assert 1 <= record.rank_of(record.team) <= 32 and 40 <= record.strength(record.team) <= 99


def season_two(tmp_path, short):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM,
                        policy=enter_until(lambda: league(rig).season == 2 and league(rig).stage == "season"))
    if short:
        rig.game.options.settings.game.nx_fr_offseason = "short"
    return run_until(rig)


@pytest.mark.parametrize("short", [False, True])
def test_every_new_season_says_season_n_begins_and_then_the_teams_rating(tmp_path, short):
    rig = season_two(tmp_path, short)
    text, record = spoken(rig), league(rig)
    said = X.text("NXF-09", r=record.strength(record.team), k=record.rank_of(record.team))
    begins = text.index(X.text("NXE-60", n=2))
    assert text[begins + 1] == said
    assert record.sums == [record.strength_sum(t) for t in range(1, 33)]


@pytest.mark.parametrize("short", [False, True])
def test_the_new_seasons_sums_and_rating_follow_the_ratings_at_the_end_of_the_offseason(tmp_path, monkeypatch, short):
    """No rating changes in the offseason yet (SX.8c brings that): a rating is raised at stage 6 here, so that the sums kept for
    the season and the spoken rating are seen to be taken then and not copied from the season before."""
    from nfl4.extras.franchise import offseason
    seen = {}
    real = offseason.RUNNERS[D.STAGE_NEW_SEASON]

    def raise_the_players_ratings(p, n, m, short_mode):
        record = p.store.league
        seen["before"] = list(record.sums)
        for player in record.active_of(record.team):
            player.rating = min(D.RATING_MAX, player.rating + 6)
        return real(p, n, m, short_mode)

    monkeypatch.setitem(offseason.RUNNERS, D.STAGE_NEW_SEASON, raise_the_players_ratings)
    rig = season_two(tmp_path, short)
    text, record = spoken(rig), league(rig)
    own = record.team
    assert record.sums[own - 1] > seen["before"][own - 1]                                   # the own team's sum is the new one
    assert record.sums == [record.strength_sum(t) for t in range(1, 33)]
    assert X.text("NXF-09", r=record.strength(own), k=record.rank_of(own)) == text[text.index(X.text("NXE-60", n=2)) + 1]


# ----- the roster and the team ratings in F9 -----

def test_a_group_of_the_roster_speaks_the_rating_the_age_and_the_potential_of_each_player(tmp_path):
    rig = run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + INTO_FRANCHISE + [DOWN, DOWN, ENTER, DOWN, DOWN, ENTER, DOWN],
                                  policy=quit_policy))
    text, record = spoken(rig), league(rig)
    words = history.Words(lambda t: "")
    for player in record.group_of(1, "WR")[:2]:                                                  # the second group of the menu
        line = X.text("NXL-33", player=player.name, position="receiver", r=player.rating, a=player.age,
                      potential=words.potential(player.potential), contract=words.contract(player))     # SX.8g: and the contract
        assert any(line in t for t in text), line


def test_the_potential_words_are_high_average_and_low():
    words = history.Words(lambda t: "")
    assert [words.potential(p) for p in D.POTENTIALS] == ["high", "average", "low"]
    assert [X.text(i) for i in ("NXK-20", "NXK-21", "NXK-22")] == ["high", "average", "low"]


def test_the_team_ratings_item_lists_the_32_teams_best_first_and_names_the_players_rank(tmp_path):
    rig = run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + INTO_FRANCHISE + [DOWN] * 4 + [ENTER, DOWN],
                                  policy=quit_policy))
    text, record = spoken(rig), league(rig)
    first = history.team_rating_lines(record, history.Words(lambda t: "team%d" % t))
    assert len(first) == 32
    ranking = record.ranking()
    assert first[0] == X.text("NXL-40", k=1, team="team%d" % ranking[0], r=record.strength(ranking[0]))
    assert first[31] == X.text("NXL-40", k=32, team="team%d" % ranking[31], r=record.strength(ranking[31]))
    title = "your team is number %d of 32. 32 items." % record.rank_of(record.team)
    assert any(title in t for t in text)
    # what is SPOKEN (the first item when the list opens, the second after Down), worked out from the players alone: the weighted
    # sum of each team's 34 active players (design 4.4), highest first, ties by team number, the rating the sum over 78 rounded up
    sums = {t: sum(D.WEIGHT[p.pos] * p.rating for p in record.players.values() if p.status == "active" and p.team == t)
            for t in range(1, 33)}
    order = sorted(sums, key=lambda t: (-sums[t], t))
    for rank in (1, 2):
        team = order[rank - 1]
        line = X.text("NXL-40", k=rank, team=rig.game.league.team(*team_ref(team)), r=(sums[team] + 39) // 78)
        assert any(line in t for t in text), line


def test_the_strength_of_a_team_is_the_weighted_mean_of_its_34_ratings_and_the_rank_goes_by_the_exact_sum(tmp_path):
    rig = first_game(tmp_path)
    record = league(rig)
    for team in (1, 9, 32):
        players = record.active_of(team)
        total = sum(D.WEIGHT[p.pos] * p.rating for p in players)
        assert record.strength_sum(team) == total and record.strength(team) == (total + 39) // 78
    ranking = record.ranking()
    sums = [record.strength_sum(t) for t in ranking]
    assert sums == sorted(sums, reverse=True) and sorted(ranking) == list(range(1, 33))


# ----- whole games -----

def league_roster_pair(seed=1):
    """Teams 1 and 2 of a new league as design 4.5 makes them (their names, their drawn ratings, their quarterbacks)."""
    from nfl4.extras.franchise.league import new_league
    league_record = new_league(GameRandom(random.Random(seed)), NAMES, "Kim", 1, "20260101-000000")
    return league_record.roster_for_game(1), league_record.roster_for_game(2), league_record


def test_a_game_between_two_drawn_league_rosters_is_played_whole_and_the_ratings_change_its_draws(tmp_path):
    from test_fr_neutral import plain_copy
    own, opponent, record = league_roster_pair()
    quarterbacks = (own.quarterback, opponent.quarterback)
    rig, engine, rules, result = sim_game(tmp_path / "rated", 11, own_names=own, opponent_names=opponent, quarterbacks=quarterbacks,
                                          trace=True)
    assert result.scores is not None and rig.game.rnd.fallbacks == 0
    assert engine.s.rosters[1].ratings == own.ratings and engine.s.rosters[2].ratings == opponent.ratings
    plain, _, _, plain_result = sim_game(tmp_path / "plain", 11, own_names=plain_copy(own), opponent_names=plain_copy(opponent),
                                         quarterbacks=quarterbacks, trace=True)
    assert plain_result.scores is not None
    assert list(rig.rnd.trace) != list(plain.rnd.trace)          # the same seed and the same names: only the ratings differ
    assert rules.modifiers.state is engine.s                      # and the game's own rules object was bound to the game's state


def test_a_much_stronger_roster_wins_more_games_than_it_loses_in_a_small_sample(tmp_path):
    strong = rated_roster("S", 85)
    weak = rated_roster("W", 55)
    wins = 0
    games = 24
    for k in range(games):
        own, opponent = (strong, weak) if k % 2 == 0 else (weak, strong)
        rig, engine, rules, result = sim_game(tmp_path / str(k), 100 + k, own_names=own, opponent_names=opponent,
                                              quarterbacks=("QS", "QW"))
        a, b = result.scores
        wins += (a > b) if k % 2 == 0 else (b > a)
    assert wins >= 15                                       # a gap of 30 rating points is the whole bounded effect, every play
