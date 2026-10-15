"""The play-off picture: score table, computer game, division winners, wild cards, seeds, bracket files (GAME_SPEC 5.14 to
5.17, 12; Q43, Q44, Q45). This is inspired by Jim Kitchen.

Records are built by hand and the expected teams worked out from the lifted rules (pog 0x466380 to 0x46f4db: the sorts by
losses and by wins, the player's ties, the wild card replacement).
"""
import random
import re

import pytest

from nfl4.game.league import DIVISIONS, League
from nfl4.game.playoffs import (AFC_DIVISIONS, NFC_DIVISIONS, SCORE_TABLE, PlayoffState, Qualifier, TeamRef,
                                computer_game, division_winners, end_of_regular_season, original_sort, score_of, seeds,
                                wild_cards)
from nfl4.game.rnd import GameRandom
from nfl4.game.standings import standings_order
from randsources import ScriptedRandom, StuckRandom, value_for
from seasonrig import BASE, division_wins, records_of, refs
from specfiles import LIFT, need


# ----- the score table -----

def test_the_score_table_is_the_32_entries_of_pog_and_finplay17():
    assert len(SCORE_TABLE) == 32 and list(SCORE_TABLE) == sorted(SCORE_TABLE)
    for lifted, name, array in ((LIFT / "p_4615b0_pog.vb.txt", "pog", "L1c8"), (LIFT / "p_47d8b0_finplay17.vb.txt", "finplay17", "Ld4")):
        text = need(lifted).read_text(encoding="utf-8")
        found = {int(i): int(v) for i, v in re.findall(r"\b%s\((\d+)\) = (\d+)\s*$" % array, text, flags=re.M)}
        assert [found[i] for i in range(1, 33)] == list(SCORE_TABLE), name
    assert (score_of(1), score_of(17), score_of(32)) == (0, 17, 51)


def test_each_score_has_its_chance_in_the_32_entries():
    counts = {s: SCORE_TABLE.count(s) for s in set(SCORE_TABLE)}
    assert counts[0] == counts[3] == counts[6] == counts[7] == counts[9] == counts[10] == counts[12] == counts[14] == 2
    assert counts[20] == 2 and counts[21] == 3 and counts[17] == counts[24] == counts[51] == 1


# ----- the original's sort -----

def test_the_original_sort_is_stable_and_ascending():
    rng = random.Random(7)
    for _ in range(2000):
        n = rng.choice((4, 16))
        items = [(i, rng.randint(0, 5)) for i in range(n)]
        assert original_sort(items, key=lambda t: t[1]) == sorted(items, key=lambda t: t[1])


def test_the_original_sort_is_the_standings_sort():
    records = records_of(BASE)
    league = League()
    for division in range(1, DIVISIONS + 1):
        teams = [(p, records.wins[division - 1][p - 1], records.losses[division - 1][p - 1]) for p in range(1, 5)]
        by_sort = [league.team(division, t[0]) for t in original_sort(teams, key=lambda t: t[2])]
        assert by_sort == [name for name, _, _ in standings_order(division, league, records)]


# ----- a computer game -----

def test_a_computer_game_draws_the_coin_then_the_winner_then_the_loser_with_their_redraws():
    # coin 2 (the home team wins); winner index 1 (score 0) is drawn again, then 23 (24); loser index 30 (45) is not lower
    # and is drawn again, then 17 (the score 17)
    script = [value_for(2, 2), value_for(32, 1), value_for(32, 23), value_for(32, 30), value_for(32, 17)]
    rnd = GameRandom(ScriptedRandom(script, strict=True))
    rnd.trace = []
    game = computer_game(rnd)
    assert rnd.trace == [2, 32, 32, 32, 32]
    assert (game.first_wins, game.winner_index, game.winner_score, game.loser_index, game.loser_score) == (False, 23, 24, 17, 17)


def test_the_loser_must_score_less_even_when_the_indexes_differ():
    # winner 3 (3 points), loser 2 (0 points) is fine; winner 4 (3), loser 3 (3) is not lower: drawn again
    script = [value_for(2, 1), value_for(32, 4), value_for(32, 3), value_for(32, 1)]
    game = computer_game(GameRandom(ScriptedRandom(script, strict=True)))
    assert (game.winner_score, game.loser_score, game.first_wins) == (3, 0, True)


def test_a_computer_game_ends_on_a_stuck_source_through_the_bounded_redraws():
    rnd = GameRandom(StuckRandom(0.0))                       # coin 1, index 1 (0 points) forever
    game = computer_game(rnd)       # the winner's redraw runs out (index 3, 3 points); index 1 (0 points) is a fine loser
    assert rnd.fallbacks == 1 and (game.winner_score, game.loser_score, game.first_wins) == (3, 0, True)
    rnd = GameRandom(StuckRandom(0.999))                     # index 32 (51) as the winner, then as the loser forever
    game = computer_game(rnd)
    assert rnd.fallbacks == 1 and (game.winner_score, game.loser_score) == (51, 0)


def test_computer_games_are_a_coin_flip_whatever_the_teams():
    rnd = GameRandom(random.Random(5))
    firsts = sum(computer_game(rnd).first_wins for _ in range(4000))
    assert 1900 < firsts < 2100
    assert rnd.fallbacks == 0


# ----- the division winners -----

def test_the_division_winner_has_the_fewest_losses_and_a_tie_keeps_the_team_order():
    winners, in_playoffs = division_winners(records_of(BASE), TeamRef(2, 3))
    assert [(q.team.division, q.team.place, q.wins, q.losses) for q in winners] == [
        (1, 2, 12, 4), (2, 1, 9, 7), (3, 3, 13, 3), (4, 1, 8, 8),
        (5, 1, 12, 4), (6, 1, 10, 6), (7, 1, 13, 3), (8, 1, 9, 7)]
    assert in_playoffs is False


def test_the_player_wins_a_tie_for_the_division_and_the_spoken_record_is_the_first_team_s_q43():
    records = records_of(division_wins([12, 12, 8, 6]))
    winners, in_playoffs = division_winners(records, TeamRef(1, 2))
    assert winners[0] == Qualifier(TeamRef(1, 2), 12, 4) and in_playoffs
    winners, in_playoffs = division_winners(records, TeamRef(1, 1))                  # the player IS first
    assert winners[0] == Qualifier(TeamRef(1, 1), 12, 4) and in_playoffs
    winners, in_playoffs = division_winners(records, TeamRef(1, 3))                  # fewer wins: no win
    assert winners[0].team == TeamRef(1, 1) and not in_playoffs


def test_a_team_in_another_division_never_takes_a_division_tie():
    records = records_of(division_wins([12, 12, 8, 6], [10, 7, 7, 7]))
    winners, in_playoffs = division_winners(records, TeamRef(2, 2))
    assert winners[0].team == TeamRef(1, 1) and winners[1].team == TeamRef(2, 1) and not in_playoffs


# ----- the seeds -----

def test_the_seeds_run_from_the_fewest_wins_to_the_most_and_a_tie_keeps_the_division_order():
    winners, _ = division_winners(records_of(BASE), TeamRef(2, 3))
    assert [q.team for q in seeds(winners, AFC_DIVISIONS)] == refs((4, 1), (2, 1), (1, 2), (3, 3))     # 8, 9, 12, 13 wins
    assert [q.team for q in seeds(winners, NFC_DIVISIONS)] == refs((8, 1), (6, 1), (5, 1), (7, 1))     # 9, 10, 12, 13
    tied = records_of(division_wins([10, 8, 8, 8], [10, 8, 8, 8], [10, 8, 8, 8], [10, 8, 8, 8]))
    winners, _ = division_winners(tied, TeamRef(1, 1))
    assert [q.team.division for q in seeds(winners, AFC_DIVISIONS)] == [1, 2, 3, 4]


# ----- the wild cards -----

def test_the_wild_cards_are_the_two_non_winners_with_the_fewest_losses_ties_in_division_and_place_order():
    records = records_of(BASE)
    winners, flag = division_winners(records, TeamRef(2, 3))
    afc, flag = wild_cards(records, AFC_DIVISIONS, winners, TeamRef(2, 3), flag)
    assert afc == [Qualifier(TeamRef(3, 1), 11, 5), Qualifier(TeamRef(1, 1), 10, 6)]       # 6 losses: D1p1 before D3p2
    nfc, flag = wild_cards(records, NFC_DIVISIONS, winners, TeamRef(2, 3), flag)
    assert nfc == [Qualifier(TeamRef(5, 2), 11, 5), Qualifier(TeamRef(6, 2), 10, 6)]
    assert flag is False


def test_a_division_winner_is_never_a_wild_card_even_with_few_losses():
    records = records_of(BASE)
    winners, flag = division_winners(records, TeamRef(2, 3))
    afc, _ = wild_cards(records, AFC_DIVISIONS, winners, TeamRef(2, 3), flag)
    assert all(q.team not in [w.team for w in winners] for q in afc)


def test_the_player_who_is_a_wild_card_sets_the_flag():
    records = records_of(BASE)
    own = TeamRef(3, 1)
    winners, flag = division_winners(records, own)
    afc, flag = wild_cards(records, AFC_DIVISIONS, winners, own, flag)
    assert afc[0].team == own and flag
    own = TeamRef(1, 1)                                                                 # the second wild card
    winners, flag = division_winners(records, own)
    afc, flag = wild_cards(records, AFC_DIVISIONS, winners, own, flag)
    assert afc[1].team == own and flag


def test_the_player_with_as_many_wins_as_the_second_wild_card_takes_its_place_q43_afc_and_nfc():
    records = records_of({(1, 1): 11, (5, 1): 11})              # the winners of divisions 1 and 5 have 11, the rest are 8 and 8
    for own, conference in ((TeamRef(1, 4), AFC_DIVISIONS), (TeamRef(5, 4), NFC_DIVISIONS)):
        winners, flag = division_winners(records, own)
        assert not flag
        cards, flag = wild_cards(records, conference, winners, own, flag)
        first_division = conference[0]
        assert [q.team for q in cards] == [TeamRef(first_division, 2), own] and flag     # the second would be place 3
        assert (cards[1].wins, cards[1].losses) == (8, 8)       # the record spoken is the replaced team's


def test_no_replacement_with_fewer_wins_in_another_conference_or_when_already_in():
    records = records_of({(1, 4): 7})
    winners, flag = division_winners(records, TeamRef(1, 4))
    cards, flag = wild_cards(records, AFC_DIVISIONS, winners, TeamRef(1, 4), flag)
    assert TeamRef(1, 4) not in [q.team for q in cards] and not flag
    records = records_of({(1, 1): 11})
    winners, flag = division_winners(records, TeamRef(1, 4))
    assert not flag
    cards, flag = wild_cards(records, NFC_DIVISIONS, winners, TeamRef(1, 4), flag)       # an A. F. C. team, N. F. C. cards
    assert TeamRef(1, 4) not in [q.team for q in cards] and not flag
    records = records_of({})
    own = TeamRef(1, 1)                                                                 # a division winner: no replacement
    winners, flag = division_winners(records, own)
    assert flag
    cards, flag = wild_cards(records, AFC_DIVISIONS, winners, own, flag)
    assert own not in [q.team for q in cards]


# ----- the bracket -----

def test_the_wild_card_pairings_and_the_byes_of_the_hand_worked_season():
    result = end_of_regular_season(records_of(BASE), TeamRef(2, 3))
    assert result.pairings == [(TeamRef(3, 1), TeamRef(4, 1)), (TeamRef(1, 1), TeamRef(2, 1)),
                               (TeamRef(5, 2), TeamRef(8, 1)), (TeamRef(6, 2), TeamRef(6, 1))]
    assert result.byes == refs((1, 2), (3, 3), (5, 1), (7, 1))
    assert result.where(TeamRef(2, 3)) == "out"
    assert result.where(TeamRef(3, 1)) == "wild_card" and result.where(TeamRef(4, 1)) == "wild_card"
    assert result.where(TeamRef(1, 2)) == "bye" and result.where(TeamRef(7, 1)) == "bye"
    assert result.player_in_playoffs is False


def test_twelve_teams_make_it_whoever_plays_and_where_agrees_with_the_flag():
    rng = random.Random(11)
    for _ in range(300):
        wins = {(d, p): rng.randint(0, 16) for d in range(1, 9) for p in range(1, 5)}
        own = TeamRef(rng.randint(1, 8), rng.randint(1, 4))
        result = end_of_regular_season(records_of(wins), own)
        teams = [t for pairing in result.pairings for t in pairing] + result.byes
        assert len(teams) == len(set(teams)) == 12
        assert (result.where(own) != "out") == result.player_in_playoffs
        for conference in (AFC_DIVISIONS, NFC_DIVISIONS):
            assert sum(t.division in conference for t in teams) == 6
        assert [d.division for d in (q.team for q in result.winners)] == list(range(1, 9))


def test_the_bye_teams_have_the_most_wins_of_their_conference_s_division_winners():
    rng = random.Random(3)
    for _ in range(200):
        wins = {(d, p): rng.randint(0, 16) for d in range(1, 9) for p in range(1, 5)}
        result = end_of_regular_season(records_of(wins), TeamRef(1, 1))
        for seeds_, byes in ((result.afc_seeds, result.byes[:2]), (result.nfc_seeds, result.byes[2:])):
            assert [q.team for q in seeds_[2:]] == byes
            assert seeds_[0].wins <= seeds_[1].wins <= seeds_[2].wins <= seeds_[3].wins


# ----- the files in memory -----

def test_the_playoff_files_round_trip_and_the_opponent_is_found_as_form_load_does():
    state = PlayoffState(pairings=[(TeamRef(3, 1), TeamRef(4, 1)), (TeamRef(1, 1), TeamRef(2, 1))],
                         byes=refs((1, 2), (3, 3)))
    assert state.pairing_values() == [3, 1, 4, 1, 1, 1, 2, 1] and state.bye_values() == [1, 2, 3, 3]
    assert PlayoffState.pairings_from_values(state.pairing_values()) == state.pairings
    assert PlayoffState.byes_from_values(state.bye_values()) == state.byes
    assert state.opponent_of(TeamRef(3, 1)) == (TeamRef(4, 1), 2)          # the first team is the visitor: vtrnt = 2
    assert state.opponent_of(TeamRef(2, 1)) == (TeamRef(1, 1), 1)          # the second is the home team: vtrnt = 1
    assert state.opponent_of(TeamRef(8, 4)) is None and state.contains_player(TeamRef(4, 1))
    with pytest.raises(ValueError):
        PlayoffState.pairings_from_values([1, 2, 3])
    with pytest.raises(ValueError):
        PlayoffState.byes_from_values([1, 2, 3])
