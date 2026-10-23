"""The N. F. L.'s 14-team play-offs of a franchise on the real calendar (nfl4 only, rule 0.13; D-129, the owner's answer to Q-061). This is inspired by Jim Kitchen.

7 teams a conference: the four division winners are seeds 1 to 4 (the most wins first), three wild cards seeds 5 to 7; only seed 1 rests in the wild
card round, where 2 hosts 7, 3 hosts 6 and 4 hosts 5; the division round is reseeded (seed 1 hosts the lowest seed left) and the better seed hosts the
conference championship. Classic and a franchise on the original's 16 weeks keep the original's 12 teams (their tests: test_playoffs.py,
test_season_playoffs.py, the golden transcript); a league saved in the play-offs by 0.12.1 finishes the bracket it began.
"""
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import LeagueRecord
from nfl4.game.playoffs import (REAL_BYES, REAL_WILD_CARD_GAMES, TeamRef, end_of_regular_season, real_championship_pairings,
                                real_division_pairings, real_end_of_regular_season)
from nfl4.game.schedule import Calendar
from nfl4.game.season import SeasonState
from nfl4.game.standings import Records


def records_from(wins_of) -> Records:
    """A whole 17-game season: team (division, place) has wins_of(division, place) wins and the rest losses."""
    records = Records()
    for division in range(1, 9):
        for place in range(1, 5):
            wins = wins_of(division, place)
            records.wins[division - 1][place - 1], records.losses[division - 1][place - 1] = wins, 17 - wins
    return records


# In every division place 1 wins it; the A. F. C.'s winners have 13, 12, 11, 10 wins (divisions 1 to 4), the N. F. C.'s 10, 11, 12, 13 (5 to 8);
# the places 2 have 9 + a little, the places 3 and 4 fewer.
WINS = {1: 13, 2: 12, 3: 11, 4: 10, 5: 10, 6: 11, 7: 12, 8: 13}
SECOND = {1: 9, 2: 10, 3: 8, 4: 7, 5: 9, 6: 8, 7: 10, 8: 7}


def standard(division, place):
    if place == 1:
        return WINS[division]
    if place == 2:
        return SECOND[division]
    return 6 if place == 3 else 3


OUTSIDER = TeamRef(4, 4)                 # the player's team in most tests: 3 wins, out


def test_seeds_one_to_four_are_the_division_winners_by_wins_and_five_to_seven_the_wild_cards():
    result = real_end_of_regular_season(records_from(standard), OUTSIDER)
    assert [q.team for q in result.afc_seeds] == [TeamRef(1, 1), TeamRef(2, 1), TeamRef(3, 1), TeamRef(4, 1)]
    assert [q.team for q in result.nfc_seeds] == [TeamRef(8, 1), TeamRef(7, 1), TeamRef(6, 1), TeamRef(5, 1)]
    # the A. F. C.'s places 2: 9, 10, 8, 7 wins: the wild cards are D2 (10), D1 (9), D3 (8), fewest losses first
    assert [q.team for q in result.afc_wild_cards] == [TeamRef(2, 2), TeamRef(1, 2), TeamRef(3, 2)]
    assert [q.team for q in result.nfc_wild_cards] == [TeamRef(7, 2), TeamRef(5, 2), TeamRef(6, 2)]
    seed = result.seed_of
    assert seed[TeamRef(1, 1)] == 1 and seed[TeamRef(4, 1)] == 4 and seed[TeamRef(2, 2)] == 5 and seed[TeamRef(3, 2)] == 7
    assert seed[TeamRef(8, 1)] == 1 and seed[TeamRef(6, 2)] == 7 and len(seed) == 14


def test_the_wild_card_round_has_six_games_two_hosts_seven_three_hosts_six_four_hosts_five_and_only_seed_one_rests():
    result = real_end_of_regular_season(records_from(standard), OUTSIDER)
    assert len(result.pairings) == REAL_WILD_CARD_GAMES and len(result.byes) == REAL_BYES
    assert result.pairings[:3] == [(TeamRef(3, 2), TeamRef(2, 1)), (TeamRef(1, 2), TeamRef(3, 1)), (TeamRef(2, 2), TeamRef(4, 1))]
    assert result.pairings[3:] == [(TeamRef(6, 2), TeamRef(7, 1)), (TeamRef(5, 2), TeamRef(6, 1)), (TeamRef(7, 2), TeamRef(5, 1))]
    assert result.byes == [TeamRef(1, 1), TeamRef(8, 1)]
    assert result.where(TeamRef(1, 1)) == "bye" and result.where(TeamRef(2, 1)) == "wild_card" and result.where(OUTSIDER) == "out"


def test_equal_wins_keep_the_division_order_and_a_tie_is_half_a_win():
    records = records_from(lambda d, p: 12 if p == 1 and d <= 4 else (5 if p == 1 else 4))
    result = real_end_of_regular_season(records, OUTSIDER)
    assert [q.team.division for q in result.afc_seeds] == [1, 2, 3, 4]            # four winners with 12 wins: the division order
    records.wins[2][0], records.losses[2][0], records.ties[2][0] = 12, 4, 1           # D3's winner 12-4-1 beats 12-5
    result = real_end_of_regular_season(records, OUTSIDER)
    assert result.afc_seeds[0].team == TeamRef(3, 1)


def test_the_players_team_with_as_many_wins_as_the_seventh_seed_takes_its_place_q43():
    own = TeamRef(4, 3)
    records = records_from(standard)
    records.wins[3][2], records.losses[3][2] = 8, 9                                   # as many wins as D3's place 2, the third wild card
    result = real_end_of_regular_season(records, own)
    assert result.afc_wild_cards[2].team == own and result.player_in_playoffs
    assert result.pairings[0] == (own, TeamRef(2, 1)) and result.seed_of[own] == 7


def test_the_division_round_is_reseeded_seed_one_hosts_the_lowest_seed_left():
    result = real_end_of_regular_season(records_from(standard), OUTSIDER)
    seed = result.seed_of
    afc = {s: t for t, s in seed.items() if t.division <= 4}
    nfc = {s: t for t, s in seed.items() if t.division >= 5}
    # the A. F. C.: 2, 6 and 5 win (the home team of the first game, the visitors of the other two); the N. F. C.: 7, 3 and 4
    winners = [afc[2], afc[6], afc[5], nfc[7], nfc[3], nfc[4]]
    pairings = real_division_pairings(winners, result.byes, seed)
    assert pairings == [(afc[6], afc[1]), (afc[5], afc[2]), (nfc[7], nfc[1]), (nfc[4], nfc[3])]
    champions = real_championship_pairings([afc[5], afc[1], nfc[3], nfc[7]], seed)
    assert champions == [(afc[5], afc[1]), (nfc[7], nfc[3])]                      # the better seed hosts


def test_classic_and_a_franchise_on_the_originals_16_weeks_keep_the_originals_twelve_teams():
    records = Records()
    old = end_of_regular_season(records, TeamRef(1, 1))
    assert len(old.pairings) == 4 and len(old.byes) == 4 and old.seed_of == {}
    season = SeasonState()
    assert not season.real_playoffs                                                  # no calendar: the original's bracket
    season.calendar = Calendar("test", ((),) * 18)
    assert season.real_playoffs
    season.playoffs.byes = [TeamRef(1, 1), TeamRef(2, 1), TeamRef(5, 1), TeamRef(6, 1)]
    assert not season.real_playoffs                                                  # a bracket begun by 0.12.1 with four byes is finished as it began
    season.playoffs.byes = [TeamRef(1, 1), TeamRef(5, 1)]
    assert season.real_playoffs


def test_the_league_file_check_accepts_the_real_bracket_and_the_old_one_on_a_calendar():
    league = LeagueRecord()
    league.calendar = {"label": "x", "weeks": []}
    league.byes = [1, 1, 5, 1]
    assert league.real_bracket()
    league.byes = [1, 1, 2, 1, 5, 1, 6, 1]
    assert not league.real_bracket()
    league.calendar = None
    league.byes = []
    assert not league.real_bracket()


# ----- whole seasons on the Franchise rig -----

def whole_season(tmp_path, scores):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=scores,
                        policy=enter_until(lambda: rig.fstore.league is not None and rig.fstore.league.season == 2))
    return run_until(rig)


def test_a_season_on_the_real_calendar_sends_fourteen_teams_to_the_play_offs_and_plays_thirteen_play_off_games(tmp_path):
    rig = whole_season(tmp_path, lambda r: (10, 28))                                 # the player loses every game: the rest is played without him
    league = rig.fstore.league
    entry = league.history[-1]
    assert sum(1 for finish in entry["finish"] if finish >= D.FINISH_WILD_CARD) == 14
    assert entry["finish"][league.team - 1] == D.FINISH_MISSED
    text = spoken(rig)
    assert sum(1 for line in text if line.startswith(" the top seeds, the ")) == 1
    assert sum(1 for line in text if " won over the " in line) >= 13                 # 6 wild card games, 4, 2 and the Super Bowl


def test_the_two_teams_with_a_bye_play_first_in_the_division_round(tmp_path):
    rig = whole_season(tmp_path, lambda r: (10, 28))
    entry = rig.fstore.league.history[-1]
    # 14 teams: 6 lose in the wild card round, 4 in the division round, 2 in the championships, 1 in the Super Bowl and 1 is the champion
    finishes = [f for f in entry["finish"] if f >= D.FINISH_WILD_CARD]
    assert finishes.count(D.FINISH_WILD_CARD) == 6 and finishes.count(D.FINISH_DIVISION) == 4
    assert finishes.count(D.FINISH_CHAMPIONSHIP) == 2 and finishes.count(D.FINISH_SUPER_BOWL) == 1 and finishes.count(D.FINISH_CHAMPION) == 1


def test_the_league_saved_in_each_play_off_round_of_the_real_bracket_is_whole_and_can_be_resumed(tmp_path):
    seen = {}

    def note():
        league = rig.fstore.league if rig.fstore is not None else None
        if league is not None and league.season == 1 and league.gtp > 18 and rig.fstore.engine_consistent():
            seen.setdefault(league.gtp, (len(league.pairings) // 4, len(league.byes) // 2, league.to_json()))
        return league is not None and league.season == 2

    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=lambda r: (28, 10), policy=enter_until(note))
    run_until(rig)
    assert seen[20][:2] == (4, 2) and seen[21][:2] == (2, 2) and seen[22][:2] == (1, 2)    # the division round, the championships, the Super Bowl
    for _games, _byes, text in seen.values():
        LeagueRecord.from_json(text).check()                                         # the file's whole check passes in every round


def test_the_player_who_wins_every_game_is_seed_one_rests_in_the_wild_card_round_and_wins_the_super_bowl(tmp_path):
    rig = whole_season(tmp_path, lambda r: (28, 10))
    league = rig.fstore.league
    weeks = [play["gtp"] for play in rig.plays]                                      # the rig stops before the second season's first game
    assert 19 not in weeks and weeks[-3:] == [20, 21, 22]                           # the bye in week 19, then three games to the title
    assert league.history[-1]["champion"] == league.team
    own = rig.game.league.team(*TeamRef(1, 1))                                       # the rig's player takes the first team, the Bengals
    assert any(line.startswith(" the top seeds, the %s and the " % own) for line in spoken(rig))     # the A. F. C.'s seed 1 is named first
