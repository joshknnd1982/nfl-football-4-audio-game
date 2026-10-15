"""The play-off weeks with the player's team (pog, GAME_SPEC 5.16) and the rounds without it (finplay17, 5.17). This is inspired by Jim Kitchen.

Strict draws written by hand from the lifted code: pog 0x473502 to 0x47d257 (the three weeks, the player's game GoSub
0x477000), finplay17 0x47e033 to 0x484698. The hand-worked season of tests/seasonrig.py gives the wild card pairings; every round
after it is worked out by hand in the comments. Q46 and Q48 are NOT reproduced (D-029): every result is its own sentence with
" The ", the player's own A. F. C. championship result is spoken, a conceded Super Bowl ends the season.
"""
import pytest

from nfl4.game.playoffs import TeamRef
from nfl4.game.season_engine import SeasonStateError
from pagrig import Draws, sounds_played
from seasonrig import BASE_BYES, BASE_PAIRINGS, ENTER, F1, computer_game_draws, refs, run, season_rig, texts

BRONCOS, COLTS, BROWNS, BILLS, CHIEFS = TeamRef(3, 1), TeamRef(4, 1), TeamRef(1, 2), TeamRef(2, 1), TeamRef(3, 3)
LIONS, BEARS, COWBOYS, CARDINALS = TeamRef(5, 2), TeamRef(5, 1), TeamRef(6, 1), TeamRef(7, 1)

DIVISION_PAIRINGS = [(BRONCOS, BROWNS), (BILLS, CHIEFS), (LIONS, BEARS), (COWBOYS, CARDINALS)]
CHAMPIONSHIP_PAIRINGS = [(BRONCOS, BILLS), (BEARS, COWBOYS)]


def playoff_rig(tmp_path, own, opponent, gtp, scores, answers, pairings, byes=None):
    rig = season_rig(tmp_path, answers=answers, own=own, opponent=opponent, gtp=gtp, scores=scores)
    rig.game.season.playoffs.pairings = list(pairings)
    rig.game.season.playoffs.byes = list(byes if byes is not None else BASE_BYES)
    rig.finplay17_calls = []
    rig.engine.finplay17 = lambda: rig.finplay17_calls.append(rig.game.season.gtp)
    return rig


def values(*teams):
    return [v for team in teams for v in team]


# ----- the wild card week -----

WILD_CARD_REST = [(2, 20, 5), (1, 31, 1), (2, 28, 3)]       # games 2 to 4: coin, winner index, loser index


def wild_card_draws():
    draws = Draws()
    for coin, w, l in WILD_CARD_REST:
        computer_game_draws(draws, coin, w, l)
    return draws


WILD_CARD_TEXTS = [" In the A. F. C. wild card games. ",
                   " The Broncos won over the Colts by the score of  24 to 17. ",
                   " The Bills won over the Bengals by the score of  21 to 6. ",
                   " In the N. F. C. wild card games. ",
                   " The Lions won over the Buccaneers by the score of  49 to 0. ",
                   " The Cowboys won over the Eagles by the score of  41 to 3. "]


def test_the_player_wins_the_wild_card_game_every_result_is_its_own_sentence_and_gtp_becomes_18(tmp_path):
    rig = playoff_rig(tmp_path, (3, 1), (4, 1), 17, (24, 17), [ENTER], BASE_PAIRINGS)
    result = run(rig, rig.engine.pog, wild_card_draws())
    assert texts(rig) == WILD_CARD_TEXTS and rig.game.replay == WILD_CARD_TEXTS
    assert rig.game.season.playoffs.pairings == [(BRONCOS, BROWNS), (BILLS, CHIEFS), (LIONS, BEARS), (COWBOYS, CARDINALS)]
    assert rig.store.events == [("pairings", values(BRONCOS, BROWNS, BILLS, CHIEFS, LIONS, BEARS, COWBOYS, CARDINALS)),
                                ("gtp", 18)]
    assert result.gtp == 18 and rig.finplay17_calls == [] and rig.engine.player_won
    assert rig.keys.waits == 1 and rig.game.norep == 0 and rig.game.ptf == 1


def test_the_player_loses_the_wild_card_game_the_rest_of_the_season_is_played_at_once(tmp_path):
    rig = playoff_rig(tmp_path, (3, 1), (4, 1), 17, (10, 20), [ENTER], BASE_PAIRINGS)
    run(rig, rig.engine.pog, wild_card_draws())
    assert texts(rig)[1] == " The Colts won over the Broncos by the score of  20 to 10. "
    assert rig.game.season.playoffs.pairings[0] == (COLTS, BROWNS)           # the winner at the bye team
    assert rig.finplay17_calls == [18] and not rig.engine.player_won
    assert rig.store.events[-1] == ("gtp", 18)


def test_a_tie_goes_to_the_opponent_q41(tmp_path):
    rig = playoff_rig(tmp_path, (3, 1), (4, 1), 17, (14, 14), [ENTER], BASE_PAIRINGS)
    run(rig, rig.engine.pog, wild_card_draws())
    assert texts(rig)[1] == " The Colts won over the Broncos by the score of  14 to 14. "
    assert rig.finplay17_calls == [18]


def test_the_player_as_the_home_team_and_in_the_second_a_f_c_game_is_spoken_in_order_q46_not_reproduced(tmp_path):
    """The Bills host the Bengals (game 2). In the original the first game's result is lost when the player plays the second
    A. F. C. game (the player's sentence is assigned over it); here each result is its own sentence, game 1 included."""
    rig = playoff_rig(tmp_path, (2, 1), (1, 1), 17, (21, 6), [ENTER], BASE_PAIRINGS)
    draws = Draws()
    computer_game_draws(draws, 1, 23, 17)                                    # game 1 first: Broncos at Colts, 24 to 17
    computer_game_draws(draws, 1, 31, 1)                                     # game 3
    computer_game_draws(draws, 2, 28, 3)                                     # game 4
    run(rig, rig.engine.pog, draws)
    assert texts(rig) == WILD_CARD_TEXTS and rig.game.season.playoffs.pairings[1] == (BILLS, CHIEFS)
    assert rig.engine.player_won and rig.finplay17_calls == []


def test_the_third_result_keeps_its_the_q46_not_reproduced(tmp_path):
    """The original drops " The " from the third record of the wild card week (0x475452); the clone speaks all four alike."""
    rig = playoff_rig(tmp_path, (3, 1), (4, 1), 17, (24, 17), [ENTER], BASE_PAIRINGS)
    run(rig, rig.engine.pog, wild_card_draws())
    assert all(t.startswith(" The ") for t in texts(rig) if " won over " in t)


# ----- the division week -----

def test_the_division_week_the_player_wins_and_the_next_round_pairs_the_winners(tmp_path):
    rig = playoff_rig(tmp_path, (3, 1), (1, 2), 18, (20, 13), [ENTER], DIVISION_PAIRINGS)
    draws = Draws()
    computer_game_draws(draws, 1, 23, 17)                                    # Bills at Chiefs: the visitor, 24 to 17
    computer_game_draws(draws, 2, 26, 2)                                     # Lions at Bears: the home team, 35 to 0
    computer_game_draws(draws, 1, 16, 1)                                     # Cowboys at Cardinals: the visitor, 14 to 0
    run(rig, rig.engine.pog, draws)
    assert texts(rig) == [" In the A. F. C. division play off games. ",
                          " The Broncos won over the Browns by the score of  20 to 13. ",
                          " The Bills won over the Chiefs by the score of  24 to 17. ",
                          " In the N. F. C. division play off games. ",
                          " The Bears won over the Lions by the score of  35 to 0. ",
                          " The Cowboys won over the Cardinals by the score of  14 to 0. "]
    assert rig.game.season.playoffs.pairings == [(BRONCOS, BILLS), (BEARS, COWBOYS)]
    assert rig.store.events == [("pairings", values(BRONCOS, BILLS, BEARS, COWBOYS)), ("gtp", 19)]
    assert rig.game.season.gtp == 19 and rig.finplay17_calls == []


def test_the_player_who_hosts_a_division_game_and_loses_hands_the_rest_to_finplay17(tmp_path):
    rig = playoff_rig(tmp_path, (1, 2), (3, 1), 18, (7, 10), [ENTER], DIVISION_PAIRINGS)     # the Browns host the Broncos
    draws = Draws()
    for coin, w, l in ((1, 23, 17), (2, 26, 2), (1, 16, 1)):
        computer_game_draws(draws, coin, w, l)
    run(rig, rig.engine.pog, draws)
    assert texts(rig)[1] == " The Broncos won over the Browns by the score of  10 to 7. "
    assert rig.game.season.playoffs.pairings[0] == (BRONCOS, BILLS)
    assert rig.finplay17_calls == [19] and rig.store.events[-1] == ("gtp", 19)


# ----- the championship week -----

def test_the_championship_week_speaks_the_players_own_a_f_c_result_and_the_two_space_heading(tmp_path):
    rig = playoff_rig(tmp_path, (3, 1), (2, 1), 19, (17, 14), [ENTER], CHAMPIONSHIP_PAIRINGS)
    run(rig, rig.engine.pog, computer_game_draws(Draws(), 2, 30, 29))        # Bears at Cowboys: the home team, 45 to 42
    assert texts(rig) == [" In the A. F. C. championship  game. ",
                          " The Broncos won over the Bills by the score of  17 to 14. ",     # never spoken by the original (Q46c)
                          " In the N. F. C. championship game. ",
                          " The Cowboys won over the Bears by the score of  45 to 42. "]
    assert rig.game.season.playoffs.pairings == [(BRONCOS, COWBOYS)]
    assert rig.store.events == [("pairings", values(BRONCOS, COWBOYS)), ("gtp", 20)]
    assert rig.game.season.gtp == 20 and rig.finplay17_calls == []


def test_the_player_in_the_n_f_c_championship_loses_and_finplay17_plays_the_super_bowl(tmp_path):
    rig = playoff_rig(tmp_path, (5, 1), (6, 1), 19, (3, 17), [ENTER], CHAMPIONSHIP_PAIRINGS)
    run(rig, rig.engine.pog, computer_game_draws(Draws(), 1, 23, 17))        # Broncos at Bills: the visitor, 24 to 17
    assert texts(rig)[-1] == " The Cowboys won over the Bears by the score of  17 to 3. "
    assert rig.game.season.playoffs.pairings == [(BRONCOS, COWBOYS)] and rig.finplay17_calls == [20]


# ----- a conceded Super Bowl (D-029 item 3: Q48 not reproduced) -----

def test_a_conceded_super_bowl_speaks_the_loss_plays_the_celebration_and_ends_the_season(tmp_path):
    rig = playoff_rig(tmp_path, (3, 1), (4, 1), 20, (0, 7), [ENTER], [(BRONCOS, COLTS)])
    rig.game.pause_log = []
    draws = Draws().celebration(9)
    run(rig, rig.engine.pog, draws)
    assert texts(rig) == [" In the Super Bowl. ", " The Colts won over the Broncos by the score of  7 to 0. "]
    assert sounds_played(rig) == ["foot15"] * 9
    assert rig.game.pause_log == [(0x483F1A, 0.2)]
    assert rig.game.season.gtp == 0 and rig.store.events == [("gtp", 0)] and rig.game.norep == 0
    assert rig.finplay17_calls == []


# ----- finplay17: the rounds without the player -----

ROUND_GAMES = [(1, 23, 17), (2, 20, 5), (1, 31, 1), (2, 28, 3),            # wild card: Broncos, Bills, Lions, Cowboys
               (2, 26, 2), (1, 16, 1), (1, 30, 29), (2, 12, 3),            # division: Browns, Bills, Lions, Cardinals
               (1, 24, 4), (2, 32, 31),                                    # championship: Browns, Cardinals
               (2, 19, 7)]                                                 # Super Bowl: the Cardinals


def finplay_texts():
    return [" In the A. F. C. wild card games. ",
            " The Broncos won over the Colts by the score of  24 to 17. ",
            " The Bills won over the Bengals by the score of  21 to 6. ",
            " In the N. F. C. wild card games. ",
            " The Lions won over the Buccaneers by the score of  49 to 0. ",
            " The Cowboys won over the Eagles by the score of  41 to 3. ",
            " In the A. F. C. Division play off games. ",                  # capital D (Q47)
            " The Browns won over the Broncos by the score of  35 to 0. ",
            " The Bills won over the Chiefs by the score of  14 to 0. ",
            " In the N. F. C. division play off games. ",
            " The Lions won over the Bears by the score of  45 to 42. ",
            " The Cardinals won over the Cowboys by the score of  10 to 3. ",
            " In the A. F. C. Championship game. ",
            " The Browns won over the Bills by the score of  28 to 3. ",
            " In the N. F. C. Championship game. ",
            " The Cardinals won over the Lions by the score of  51 to 49. ",
            " In the Super Bowl. ",
            " The Cardinals won over the Browns by the score of  20 to 7. "]


def finplay_draws(first_run=8, second_run=10):
    draws = Draws()
    for coin, w, l in ROUND_GAMES[:10]:
        computer_game_draws(draws, coin, w, l)
    computer_game_draws(draws, *ROUND_GAMES[10])
    draws.celebration(first_run)
    if second_run:
        draws.celebration(second_run)
    return draws


def test_finplay17_plays_every_round_from_the_wild_card_round_to_the_super_bowl(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER, ENTER, ENTER, F1, ENTER], own=(2, 3), opponent=(4, 4), gtp=17)
    rig.game.season.playoffs.pairings = list(BASE_PAIRINGS)
    rig.game.season.playoffs.byes = list(BASE_BYES)
    rig.game.pause_log = []
    run(rig, rig.game.finplay17, finplay_draws())
    spoken = texts(rig)
    assert spoken[:18] == finplay_texts()
    assert spoken[18:] == finplay_texts()[-2:]                               # F1: the replay (norep = 1: no introduction)
    assert rig.game.season.gtp == 0 and rig.game.norep == 0 and rig.game.ptf == 1
    assert rig.game.replay == finplay_texts()[-2:]                           # ilc = 0 before the Super Bowl
    assert rig.keys.waits == 5


def test_finplay17_writes_each_rounds_pairings_and_never_football_gtp(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER, ENTER, ENTER, ENTER], own=(2, 3), opponent=(4, 4), gtp=17)
    rig.game.season.playoffs.pairings = list(BASE_PAIRINGS)
    rig.game.season.playoffs.byes = list(BASE_BYES)
    run(rig, rig.game.finplay17, finplay_draws(8, 0))
    assert rig.store.events == [
        ("pairings", values(BRONCOS, BROWNS, BILLS, CHIEFS, LIONS, BEARS, COWBOYS, CARDINALS)),
        ("pairings", values(BROWNS, BILLS, LIONS, CARDINALS)),
        ("pairings", values(BROWNS, CARDINALS))]
    assert rig.game.season.playoffs.pairings == [(BROWNS, CARDINALS)]


def test_the_pauses_and_the_celebration_sounds_of_finplay17(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER, ENTER, ENTER, F1, ENTER], own=(2, 3), opponent=(4, 4), gtp=17)
    rig.game.season.playoffs.pairings = list(BASE_PAIRINGS)
    rig.game.season.playoffs.byes = list(BASE_BYES)
    rig.game.pause_log = []
    run(rig, rig.game.finplay17, finplay_draws(8, 10))
    # 0.2 s at the start, 0.2 s before the first celebration, inrep's own 0.2 s after F1, then 5 s before the second
    assert rig.game.pause_log == [(0x47DF85, 0.2), (0x483F1A, 0.2), (0x4867C9, 0.2), (0x483F1A, 5.0)]
    assert sounds_played(rig) == ["foot15"] * 18                             # 8 then 10 celebration sounds, nothing else
    plays = [e for e in rig.slot_log if e.action == "play"]
    assert len(plays) == 18 and all(e.sound_id == "snd_foot15" for e in plays)


@pytest.mark.parametrize("gtp, rounds", [(17, [1, 2, 3, 4]), (18, [2, 3, 4]), (19, [3, 4]), (20, [4]),
                                         (0, [1, 2, 3, 4]), (16, [1, 2, 3, 4]), (21, [1, 2, 3, 4]), (37, [1, 2, 3, 4])])
def test_finplay17_starts_at_round_gtp_minus_16_and_a_value_outside_1_to_4_starts_at_the_wild_card_round(tmp_path, gtp, rounds):
    rig = season_rig(tmp_path, answers=[], gtp=gtp)
    called = []
    rig.engine._fin_wild_card_round = lambda: called.append(1)
    rig.engine._fin_division_round = lambda: called.append(2)
    rig.engine._fin_championship_round = lambda: called.append(3)
    rig.engine._fin_super_bowl = lambda: called.append(4)
    run(rig, rig.engine.finplay17)
    assert called == rounds


def test_finplay17_from_the_championship_round_uses_the_pairings_of_the_state(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER, ENTER], own=(2, 3), opponent=(4, 4), gtp=19)
    rig.game.season.playoffs.pairings = list(CHAMPIONSHIP_PAIRINGS)
    draws = Draws()
    computer_game_draws(draws, 1, 23, 17)                                    # Broncos at Bills: the visitor, 24 to 17
    computer_game_draws(draws, 1, 26, 2)                                     # Bears at Cowboys: the visitor, 35 to 0
    computer_game_draws(draws, 1, 20, 5)                                     # Broncos at Bears: 21 to 6
    draws.celebration(8)
    run(rig, rig.game.finplay17, draws)
    assert texts(rig) == [" In the A. F. C. Championship game. ", " The Broncos won over the Bills by the score of  24 to 17. ",
                          " In the N. F. C. Championship game. ", " The Bears won over the Cowboys by the score of  35 to 0. ",
                          " In the Super Bowl. ", " The Broncos won over the Bears by the score of  21 to 6. "]
    assert rig.game.season.gtp == 0


# ----- a state that does not fit the week -----

def test_missing_pairings_or_byes_raise_the_season_state_error_that_the_week_loop_turns_into_a_restart(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=17)
    with pytest.raises(SeasonStateError):
        rig.engine.pog()
    rig = season_rig(tmp_path / "b", answers=[ENTER], gtp=18)
    rig.game.season.playoffs.pairings = DIVISION_PAIRINGS[:3]
    with pytest.raises(SeasonStateError):
        rig.engine.pog()
    rig = season_rig(tmp_path / "c", answers=[ENTER], gtp=17)
    rig.game.season.playoffs.pairings = list(BASE_PAIRINGS)
    rig.game.season.playoffs.byes = refs((1, 2))
    with pytest.raises(SeasonStateError):
        rig.engine.pog()
