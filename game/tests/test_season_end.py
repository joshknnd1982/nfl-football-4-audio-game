"""The end of the regular season, pog after week 16 (GAME_SPEC 5.15; Q43, Q44, Q51). This is inspired by Jim Kitchen.

The speech is worked out by hand from the lifted pog (0x4698e9 to 0x46f9f9) for the hand-worked season of tests/seasonrig.py
(BASE): the division winners, the wild cards, the pairings written to footbal4.dat, the four bye teams of footbal5.dat, and the
three places the player's team can be (a wild card game, a bye, out). Strict draws; the bye's four simulated games are scripted.
"""
from nfl4.game.playoffs import TeamRef
from pagrig import Draws
from seasonrig import (BASE, BASE_BYES, BASE_PAIRINGS, ENTER, F1, F2, computer_game_draws, division_wins, records_of, run,
                       season_rig, texts)

DIVISION_LINES = [
    " the division winners are. ",
    " A. F. C. North. ", "Browns. at 12 and 4. ", " A. F. C. East. ", "Bills. at 9 and 7. ",
    " A. F. C. West. ", "Chiefs. at 13 and 3. ", " A. F. C. South. ", "Colts. at 8 and 8. ",
    " N. F. C. North. ", "Bears. at 12 and 4. ", " N. F. C. East. ", "Cowboys. at 10 and 6. ",
    " N. F. C. West. ", "Cardinals. at 13 and 3. ", " N. F. C. South. ", "Buccaneers. at 9 and 7. ",
]
WILD_CARD_LINES = [
    " the A. F. C. wild card teams are. ", "Broncos. at 11 and 5. ", "Bengals. at 10 and 6. ",
    " the N. F. C. wild card teams are. ", "Lions. at 11 and 5. ", "Eagles. at 10 and 6. ",
]
BASE_LINES = DIVISION_LINES + WILD_CARD_LINES
PAIRING_VALUES = [3, 1, 4, 1, 1, 1, 2, 1, 5, 2, 8, 1, 6, 2, 6, 1]
BYE_VALUES = [1, 2, 3, 3, 5, 1, 7, 1]


def end_rig(tmp_path, own, answers, records=None):
    rig = season_rig(tmp_path, answers=answers, own=own, opponent=(4, 4), gtp=17)
    rig.game.season.records = records if records is not None else records_of(BASE)
    rig.finplay17_calls = []
    rig.engine.finplay17 = lambda: rig.finplay17_calls.append(rig.game.season.gtp)
    return rig


def test_the_division_winners_and_the_wild_cards_are_spoken_in_the_lifted_order(tmp_path):
    rig = end_rig(tmp_path, (2, 3), [ENTER])
    run(rig, rig.engine._end_of_regular_season)
    assert texts(rig)[:-1] == BASE_LINES
    assert rig.game.ptf == 1 and rig.game.norep == 0
    # Print #3, after the eight division winners and after the N. F. C. wild cards (and after the out sentence)
    assert rig.log == BASE_LINES[:17] + [""] + BASE_LINES[17:] + [""] + [texts(rig)[-1], ""]
    assert rig.game.replay == BASE_LINES + [texts(rig)[-1]]


def test_the_files_of_the_bracket_are_written_before_the_players_place_is_looked_up(tmp_path):
    rig = end_rig(tmp_path, (2, 3), [ENTER])
    run(rig, rig.engine._end_of_regular_season)
    assert rig.store.events == [("pairings", PAIRING_VALUES), ("byes", BYE_VALUES)]
    assert rig.game.season.playoffs.pairings == BASE_PAIRINGS and rig.game.season.playoffs.byes == BASE_BYES


def test_a_team_that_is_out_hears_its_record_waits_and_the_rest_of_the_season_is_played_at_once(tmp_path):
    rig = end_rig(tmp_path, (2, 3), [ENTER])
    run(rig, rig.engine._end_of_regular_season)
    assert texts(rig)[-1] == " The Jets at  7 and  9.  did not make it into the playoffs. "
    assert rig.finplay17_calls == [17] and rig.keys.waits == 1
    assert rig.store.kinds() == ["pairings", "byes"]            # football.gtp is NOT written: the exit deletes the files


def test_a_team_that_is_out_can_hear_the_lines_again_with_f1_or_f2_without_the_introduction(tmp_path):
    rig = end_rig(tmp_path, (2, 3), [F1, F2, ENTER])
    run(rig, rig.engine._end_of_regular_season)
    spoken = texts(rig)
    lines = BASE_LINES + [" The Jets at  7 and  9.  did not make it into the playoffs. "]
    assert spoken == lines + lines + lines and rig.keys.waits == 3
    assert " here's the instant rea play " not in spoken and rig.game.norep == 0


def test_a_wild_card_team_waits_once_gtp_17_is_written_and_the_next_start_plays_the_week(tmp_path):
    rig = end_rig(tmp_path, (3, 1), [ENTER])                     # the Broncos, the first wild card
    run(rig, rig.engine._end_of_regular_season)
    assert texts(rig) == BASE_LINES and rig.finplay17_calls == []
    assert rig.store.events == [("pairings", PAIRING_VALUES), ("byes", BYE_VALUES), ("gtp", 17)]
    assert rig.game.season.gtp == 17


def test_a_home_team_of_the_wild_card_round_is_in_a_wild_card_game_too(tmp_path):
    rig = end_rig(tmp_path, (4, 1), [ENTER])                     # the Colts host the Broncos
    run(rig, rig.engine._end_of_regular_season)
    assert rig.store.kinds()[-1] == "gtp" and rig.game.season.gtp == 17


def test_f1_replays_the_results_without_the_introduction_before_the_wild_card_game(tmp_path):
    rig = end_rig(tmp_path, (3, 1), [F1, ENTER])
    run(rig, rig.engine._end_of_regular_season)
    assert texts(rig) == BASE_LINES * 2 and rig.game.norep == 0


def test_a_team_with_a_bye_hears_the_four_wild_card_games_then_gtp_becomes_18(tmp_path):
    rig = end_rig(tmp_path, (1, 2), [ENTER, ENTER])              # the Browns have a bye
    draws = Draws()
    computer_game_draws(draws, 1, 23, 17)                        # Broncos at Colts: the visitor wins 24 to 17
    computer_game_draws(draws, 2, 20, 5)                         # Bengals at Bills: the home team wins 21 to 6
    computer_game_draws(draws, 1, 31, 1)                         # Lions at Buccaneers: the visitor wins 49 to 0
    computer_game_draws(draws, 2, 28, 3)                         # Eagles at Cowboys: the home team wins 41 to 3
    run(rig, rig.engine._end_of_regular_season, draws)
    games = [" In the A. F. C. wild card games. ",
             " The Broncos won over the Colts by the score of  24 to 17. ",
             " The Bills won over the Bengals by the score of  21 to 6. ",
             " In the N. F. C. wild card games. ",
             " The Lions won over the Buccaneers by the score of  49 to 0. ",
             " The Cowboys won over the Eagles by the score of  41 to 3. "]
    assert texts(rig) == BASE_LINES + games and rig.keys.waits == 2
    assert rig.game.season.playoffs.pairings == [
        (TeamRef(3, 1), TeamRef(1, 2)), (TeamRef(2, 1), TeamRef(3, 3)), (TeamRef(5, 2), TeamRef(5, 1)),
        (TeamRef(6, 1), TeamRef(7, 1))]                          # winner n at bye n
    assert rig.store.events == [("pairings", PAIRING_VALUES), ("byes", BYE_VALUES),
                                ("pairings", [3, 1, 1, 2, 2, 1, 3, 3, 5, 2, 5, 1, 6, 1, 7, 1]), ("gtp", 18)]
    assert rig.game.season.gtp == 18 and rig.game.replay == games      # ilc = 0 before the games
    assert rig.finplay17_calls == []


def test_a_player_who_takes_the_second_wild_card_by_wins_is_in_the_game_with_the_replaced_teams_record(tmp_path):
    records = records_of({(1, 1): 11, (5, 1): 11})               # everybody else 8 and 8
    rig = end_rig(tmp_path, (1, 4), [ENTER], records)            # the Steelers are 8 and 8
    run(rig, rig.engine._end_of_regular_season)
    spoken = texts(rig)
    assert spoken[spoken.index(" the A. F. C. wild card teams are. ") + 1:][:2] == ["Browns. at 8 and 8. ",
                                                                                      "Steelers. at 8 and 8. "]
    # seeds by wins, fewest first, ties in division order: D2 Bills, D3 Broncos, D4 Colts (8 wins), D1 Bengals (11)
    assert rig.store.events[0] == ("pairings", [1, 2, 2, 1, 1, 4, 3, 1, 5, 2, 6, 1, 5, 3, 7, 1])
    assert rig.store.events[1] == ("byes", [4, 1, 1, 1, 8, 1, 5, 1])
    assert rig.store.kinds()[-1] == "gtp"                        # the Steelers are in a wild card game


def test_the_player_who_wins_a_tie_for_the_division_is_the_winner_with_the_first_teams_record(tmp_path):
    records = records_of(division_wins([12, 12, 8, 6]))          # the Bengals and the Browns, 12 and 4
    rig = end_rig(tmp_path, (1, 2), [ENTER], records)
    byes = []
    rig.engine._wild_card_games_without_the_player = lambda: byes.append(rig.keys.waits)
    run(rig, rig.engine._end_of_regular_season)
    assert texts(rig)[1:3] == [" A. F. C. North. ", "Browns. at 12 and 4. "]
    # the Browns are the best division winner of the A. F. C. (12 wins against 8): the D4 seed has a bye
    assert rig.game.season.playoffs.byes[1] == TeamRef(1, 2) and byes == [1]


def test_the_standings_after_week_16_are_the_games_not_this_engine_q51(tmp_path):
    """Q51: SayStand is silent above 17 (the week loop's call, S7.4); the engine only leaves gtp at 17, 18 or 0."""
    rig = end_rig(tmp_path, (2, 3), [ENTER])
    run(rig, rig.engine._end_of_regular_season)
    assert rig.game.season.gtp == 17
