"""The awards and the hall of fame of a Franchise (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8o, research B11, D-076): the season's awards by one rule
over what every team has (ratings, games played, wins, the play-offs), the coach of the year by the rank at the season's start, the hall's candidates, bar
and class, the players kept for good, the whole-file check, and the words (stage 1, the history menu, history.txt). Every case is worked by hand.
"""
import random

import pytest
from drrig import SURNAMES

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import honors as H
from nfl4.extras.franchise import honors_flow as HF
from nfl4.extras.franchise import workload as W
from nfl4.extras.franchise.league import LeagueError, LeagueRecord, OFFSEASON, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5
WORDS = history.Words(lambda team: "Team%d" % team)


def league_of(seed=11):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    return league


def everybody_played(league, games=D.REGULAR_WEEKS):
    for team in range(1, D.TEAMS + 1):
        for player in league.active_of(team):
            league.usage["season"] = league.season
            league.usage["games"][str(player.id)] = games


def at(league, team, position, k=0):
    return league.player_at(team, D.PLACES_OF[position][k])


def flat(league, rating=70):
    for player in league.players.values():
        player.rating = rating
        player.seasons = 3


WINS = [8] * D.TEAMS
FINISH = [D.FINISH_MISSED] * D.TEAMS


def test_a_players_value_is_his_weight_his_rating_over_the_base_his_games_and_his_teams_wins():
    league = league_of()
    qb = at(league, 3, "QB")
    qb.rating = T.FR_AWARD_BASE + 20
    assert H.value(qb, 16, 10) == D.WEIGHT["QB"] * 20 + T.FR_AWARD_WIN * 10
    assert H.value(qb, 8, 0) == D.WEIGHT["QB"] * 20 * 8 // 16
    assert H.value(qb, 16, 0, weighted=False) == D.WEIGHT["RB"] * 20
    qb.rating = T.FR_AWARD_BASE - 5
    assert H.value(qb, 16, 3) == T.FR_AWARD_WIN * 3


def test_the_most_valuable_player_comes_from_a_play_off_team_and_the_others_by_their_sides():
    league = league_of()
    flat(league)
    everybody_played(league)
    finish = list(FINISH)
    finish[8 - 1] = D.FINISH_DIVISION
    best_qb_out = at(league, 2, "QB")
    best_qb_out.rating = 95                                           # a better quarterback of a team that missed the play-offs
    qb = at(league, 8, "QB")
    qb.rating = 80
    rb = at(league, 4, "RB", 2)
    rb.rating = 90
    dl = at(league, 6, "LB", 1)
    dl.rating = 91
    rookie = at(league, 7, "CB")
    rookie.seasons, rookie.rating = 0, 75
    kicker_rookie = at(league, 9, "K")
    kicker_rookie.seasons, kicker_rookie.rating = 0, 99
    rows = H.season_awards(league, WINS, finish)
    got = {row[1]: row for row in rows}
    assert got["mvp"][2] == qb.id and got["opoy"][2] == rb.id and got["dpoy"][2] == dl.id and got["roy"][2] == rookie.id
    assert got["mvp"] == [league.season, "mvp", qb.id, qb.name, "QB", 8]
    assert [row[1] for row in rows] == ["mvp", "opoy", "dpoy", "roy", "coy"]


def test_a_player_who_missed_games_counts_less_and_under_the_least_games_not_at_all():
    league = league_of()
    flat(league)
    everybody_played(league)
    star = at(league, 10, "WR")
    star.rating = 99
    league.usage["games"][str(star.id)] = T.FR_AWARD_MIN_GAMES - 1
    second = at(league, 11, "WR")
    second.rating = 72
    assert H.value(star, T.FR_AWARD_MIN_GAMES - 1, 8, weighted=False) > H.value(second, 16, 8, weighted=False)     # he would win on value alone
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert rows["opoy"][2] == second.id                                # the star played one game too few (the review of SX.8o: a case where it decides)
    league.usage["games"][str(star.id)] = T.FR_AWARD_MIN_GAMES
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert rows["opoy"][2] == star.id                                  # at the least games he counts, by his share of the 16
    third = at(league, 12, "WR")
    third.rating = 90
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert H.value(star, T.FR_AWARD_MIN_GAMES, 8, weighted=False) < H.value(third, 16, 8, weighted=False) and rows["opoy"][2] == third.id


def test_a_season_counted_from_a_later_week_scales_the_least_games_and_the_share():
    league = league_of()
    flat(league)
    everybody_played(league, games=8)                                   # a league migrated from format 9 after week 8: 8 weeks counted
    star = at(league, 10, "WR")
    star.rating = 90
    least = H.least_games(8)
    assert least == -(-T.FR_AWARD_MIN_GAMES * 8 // 16) and H.weeks_counted(league) == 8
    league.usage["games"][str(star.id)] = least
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert rows["opoy"][2] == star.id and set(rows) == {"opoy", "dpoy", "coy"}     # the players' awards too, not only the coach (no play-off team
    #                                                                     and no rookie in this hand-made league)
    league.usage["games"][str(star.id)] = least - 1
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert rows["opoy"][2] != star.id
    assert H.value(star, 8, 0, weighted=False, weeks=8) == H.value(star, 16, 0, weighted=False)    # every game of the weeks counted is a whole share


def test_equal_values_go_to_the_higher_rating_then_the_lower_id():
    league = league_of()
    flat(league)
    everybody_played(league)
    a, b = at(league, 12, "S"), at(league, 13, "S")
    a.rating = b.rating = 88
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert rows["dpoy"][2] == min(a.id, b.id)
    wins = list(WINS)
    wins[max(a, b, key=lambda p: p.id).team - 1] = 9                   # one more win: the value decides first
    rows = {row[1]: row for row in H.season_awards(league, wins, FINISH)}
    assert rows["dpoy"][2] == max(a.id, b.id)


def test_nobody_qualifies_no_award_but_the_coach():
    league = league_of()
    rows = H.season_awards(league, WINS, FINISH)                        # nobody counted a game
    assert [row[1] for row in rows] == ["coy"]


def test_the_coach_of_the_year_won_the_most_over_his_ranks_expectation():
    league = league_of()
    league.sums = [78 * (60 + t) for t in range(D.TEAMS)]               # team 32 is the best, team 1 the weakest
    wins = [8] * D.TEAMS
    wins[1 - 1] = 9                                                     # the weakest team wins 9: 90 against an expectation of the last band
    wins[32 - 1] = 15                                                   # the best wins 15: 150 against the first band
    team = H.coach_of_the_year(league, wins)
    assert team == 1 if 90 - T.FR_COACH_EXPECT[-1] > 150 - T.FR_COACH_EXPECT[0] else team == 32
    rows = H.season_awards(league, wins, FINISH)
    assert rows[-1] == [league.season, "coy", 0, league.staff["coaches"][team - 1]["name"], "", team]
    wins = [8] * D.TEAMS
    wins[TEAM - 1] = 16
    rows = H.season_awards(league, wins, FINISH)
    assert rows[-1][3] == "Kim" and rows[-1][5] == TEAM                 # the player himself


def test_the_expectation_is_by_bands_of_four_ranks():
    assert [H.expected_wins(rank) for rank in (1, 4, 5, 8, 29, 32)] == [T.FR_COACH_EXPECT[0]] * 2 + [T.FR_COACH_EXPECT[1]] * 2 + [T.FR_COACH_EXPECT[7]] * 2
    assert list(T.FR_COACH_EXPECT) == sorted(T.FR_COACH_EXPECT, reverse=True) and len(T.FR_COACH_EXPECT) == 8


# ----- the hall of fame -----

def retire(league, player, season):
    player.status, player.left, player.place = "retired", season, -1
    roster = league.rosters[player.team - 1]
    roster[roster.index(player.id)] = 0


def test_a_candidate_has_left_long_enough_is_a_star_or_won_an_award_and_is_not_in_the_hall():
    league = league_of()
    league.season = 10
    star, plain, awarded, recent = at(league, 1, "QB"), at(league, 2, "QB"), at(league, 3, "QB"), at(league, 4, "QB")
    for p, peak in ((star, 90), (plain, 84), (awarded, 84), (recent, 95)):
        p.peak = peak
    for p in (star, plain, awarded):
        retire(league, p, 10 - T.FR_HOF_WAIT)
    retire(league, recent, 10 - T.FR_HOF_WAIT + 1)
    league.honors["awards"].append([3, "roy", awarded.id, awarded.name, "QB", 3])
    assert set(p.id for p in H.hall_candidates(league)) == {star.id, awarded.id}
    league.honors["hall"].append([star.id, 9])
    assert [p.id for p in H.hall_candidates(league)] == [awarded.id]


def test_the_class_is_the_candidates_over_the_bar_best_first_at_most_the_classs_size():
    league = league_of()
    league.season = 20
    group = [at(league, t, "WR") for t in range(1, 8)]
    for k, p in enumerate(group):
        p.peak, p.seasons = 86 + k, 10
        retire(league, p, 5)
    group[0].peak = 85                                                 # 85 + 10 = 95: under the bar (FR_HOF_BAR)
    chosen = H.hall_class(league)
    ranked = sorted((p for p in group if H.hall_value(league, p) >= T.FR_HOF_BAR), key=lambda p: -H.hall_value(league, p))
    assert chosen == ranked[:T.FR_HOF_CLASS] and len(chosen) == min(T.FR_HOF_CLASS, len(ranked))
    assert H.hall_value(league, group[3]) == group[3].peak + group[3].seasons
    league.honors["awards"].append([4, "mvp", group[0].id, group[0].name, "WR", 1])
    assert H.hall_value(league, group[0]) == 85 + 10 + T.FR_HOF_AWARD_POINTS["mvp"]


def test_stage_one_changes_nothing_and_apply_keeps_the_awards_and_the_class():
    league = league_of()
    flat(league)
    everybody_played(league)
    league.season = 9
    old = at(league, 20, "LB")
    old.peak, old.seasons = 99, 14
    retire(league, old, 2)
    before = league.to_json()
    awards, inducted = H.stage_one(league, WINS, FINISH)
    assert league.to_json() == before and inducted == [old]
    H.apply(league, awards, inducted)
    assert league.honors["hall"] == [[old.id, 9]] and len(league.honors["awards"]) == len(awards) >= 1


def test_award_winners_and_members_of_the_hall_are_kept_for_good():
    league = league_of()
    winner, member, other = at(league, 1, "RB"), at(league, 2, "RB"), at(league, 3, "RB")
    for p in (winner, member, other):
        p.peak = 80
        retire(league, p, 1)
    league.honors["awards"].append([1, "opoy", winner.id, winner.name, "RB", 1])
    league.honors["hall"].append([member.id, 7])
    aging.drop_the_unkept(league)
    assert winner.id in league.players and member.id in league.players and other.id not in league.players
    assert H.keeps(league) == {winner.id, member.id}


# ----- the whole-file check -----

def _whole(value, low, high, what):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise LeagueError("%s is %r" % (what, value))


def honored_league():
    league = league_of()
    league.stage = OFFSEASON
    league.stage_no = D.STAGE_REVIEW
    p = at(league, 1, "QB")
    league.honors["awards"] = [[1, "mvp", p.id, p.name, "QB", 1], [1, "coy", 0, "Smith", "", 4]]
    gone = at(league, 2, "QB")
    retire(league, gone, 1)
    league.honors["hall"] = [[gone.id, 1]]
    return league


@pytest.mark.parametrize("damage", [
    lambda h: h.update(awards=None), lambda h: h.update(extra=1), lambda h: h["awards"].append([1, "mvp", 1, "x", "QB", 1]),
    lambda h: h["awards"].append([1, "best", 1, "x", "QB", 1]), lambda h: h["awards"][1].__setitem__(2, 5),
    lambda h: h["awards"][0].__setitem__(4, "XX"), lambda h: h["awards"][0].__setitem__(2, 999999),
    lambda h: h["awards"][0].__setitem__(3, "a\tb"), lambda h: h["awards"][0].__setitem__(5, 33),
    lambda h: h["awards"][0].__setitem__(0, 2), lambda h: h["hall"].append(h["hall"][0]), lambda h: h["hall"].append([1, 1]),
    lambda h: h["hall"].__setitem__(0, [1]), lambda h: h["hall"][0].__setitem__(1, 0),
    lambda h: h["awards"][1].__setitem__(2, False), lambda h: h["awards"][1].__setitem__(2, 0.0)])
def test_the_check_refuses_damaged_honors(damage):
    league = honored_league()
    H.check_honors(league, _whole)
    damage(league.honors)
    with pytest.raises(LeagueError):
        H.check_honors(league, _whole)


@pytest.mark.parametrize("damage", [
    lambda u: u.update(season=-1), lambda u: u.update(more={}), lambda u: u["games"].__setitem__("1", 19),
    lambda u: u["games"].__setitem__("x", 1), lambda u: u["carries"].__setitem__("999999", 3), lambda u: u["carries"].__setitem__("1", 0),
    lambda u: u.update(carries=[])])
def test_the_check_refuses_damaged_usage(damage):
    league = league_of()
    league.usage = {"season": 1, "games": {"1": 3}, "carries": {"1": 25}}
    W.check_usage(league, _whole)
    damage(league.usage)
    with pytest.raises(LeagueError):
        W.check_usage(league, _whole)


def test_an_award_of_the_season_in_progress_is_damage_until_its_stage_1():
    league = honored_league()
    league.stage = "season"
    league.season = 1
    with pytest.raises(LeagueError):
        H.check_honors(league, _whole)
    league.season = 2
    H.check_honors(league, _whole)


# ----- the words -----

def test_stage_ones_lines_name_the_players_own_and_the_others():
    league = league_of()
    own = at(league, TEAM, "RB")
    other = at(league, 9, "QB")
    rows = [[1, "mvp", other.id, other.name, "QB", 9], [1, "opoy", own.id, own.name, "RB", TEAM], [1, "coy", 0, "Kim", "", TEAM],
            [1, "coy", 0, "Smith", "", 3]]
    lines = HF.stage_lines(league, WORDS, rows, [])
    assert lines[0] == X.text("NXG-B01")
    assert lines[1] == X.text("NXG-B02", award=X.text("NXG-A01"), player=other.name, position=WORDS.position("QB"), team="Team9")
    assert lines[2] == X.text("NXG-B03", award=X.text("NXG-A02"), player=own.name, position=WORDS.position("RB"))
    assert lines[3] == X.text("NXG-B05", award=X.text("NXG-A05"), coach="Kim")
    assert lines[4] == X.text("NXG-B04", award=X.text("NXG-A05"), name="Smith", team="Team3")
    member = at(league, 4, "LB")
    lines = HF.stage_lines(league, WORDS, [], [member])
    assert lines == [X.text("NXG-B06"), X.text("NXG-B07", player=member.name, position=WORDS.position("LB"), team="Team4", n=member.seasons,
                                                   r=member.peak)]
    assert HF.short_lines(league, WORDS, rows, [member]) == [X.text("NXG-B02", award=X.text("NXG-A01"), player=other.name,
                                                                     position=WORDS.position("QB"), team="Team9"), X.text("NXG-B09")]
    assert HF.short_lines(league, WORDS, [], [member, other]) == [X.text("NXG-B08", n=2)] and "members" in X.text("NXG-B08", n=2)
    assert "member." in X.text("NXG-B09") and "members" not in X.text("NXG-B09")          # one new member (the review of SX.8o)


def test_the_history_lists_and_history_txt_have_the_awards_and_the_hall_newest_first():
    league = honored_league()
    league.honors["awards"].append([2, "dpoy", league.honors["awards"][0][2], league.honors["awards"][0][3], "QB", 1])
    lines = HF.award_lines(league, WORDS)
    assert lines[0].startswith(" season 2, ") and len(lines) == 3 and X.text("NXG-A05") in lines[2]
    members = HF.hall_lines(league, WORDS)
    gone = league.players[league.honors["hall"][0][0]]
    assert members == [X.text("NXG-22", player=gone.name, position=WORDS.position("QB"), team="Team2", n=gone.seasons, r=gone.peak, s=1)]
    text = history.history_text(league, WORDS)
    assert "\nAwards\n" in text and "\nHall of fame\n" in text
    award_part = text[text.index("\nAwards\n"):text.index("\nHall of fame\n")].strip().split("\n")[1:]
    assert len(award_part) == 3 and not any(line.startswith("Season ") for line in award_part)      # the seasons' parts of history.txt keep their count
    assert "Coach of the year, season 1: Smith, the Team4." in text


def test_the_hall_lists_the_newest_class_first_and_a_class_in_the_order_it_entered():
    league = honored_league()
    first = league.honors["hall"][0][0]
    members = []
    for team, peak in ((5, 95), (6, 94), (7, 93)):
        p = at(league, team, "QB")
        p.peak = peak
        retire(league, p, 1)
        members.append(p.id)
    league.honors["hall"] += [[pid, 9] for pid in members]               # entered in season 9 in this order (the highest hall value first)
    assert [p.id for p, _season in H.hall_members(league)] == members + [first]


# ----- SX.8o: the mutation check's survivors -----

def test_the_rookie_award_is_a_first_seasons_player_not_a_second_seasons():
    league = league_of()
    flat(league)
    everybody_played(league)
    rookie, second = at(league, 14, "LB"), at(league, 15, "LB")
    rookie.seasons, rookie.rating = 0, 72
    second.seasons, second.rating = 1, 95                              # far better, but in his second season
    rows = {row[1]: row for row in H.season_awards(league, WINS, FINISH)}
    assert rows["roy"][2] == rookie.id


def test_the_players_own_team_names_him_not_the_staffs_record():
    league = league_of()
    league.staff["coaches"][TEAM - 1]["name"] = "Somebody"
    wins = [8] * D.TEAMS
    wins[TEAM - 1] = 16
    assert H.season_awards(league, wins, FINISH)[-1][3] == "Kim" and H.coach_name(league, TEAM) == "Kim"


def test_a_class_is_never_bigger_than_its_size():
    league = league_of()
    league.season = 20
    group = [at(league, t, "WR") for t in range(1, 8)]
    for k, p in enumerate(group):
        p.peak, p.seasons = 90 + k, 20                                 # every hall value 110 or more: all seven are over the bar
        retire(league, p, 5)
    assert all(H.hall_value(league, p) >= T.FR_HOF_BAR for p in group)
    chosen = H.hall_class(league)
    assert len(chosen) == T.FR_HOF_CLASS < len(group) and chosen == sorted(group, key=lambda p: -p.peak)[:T.FR_HOF_CLASS]
