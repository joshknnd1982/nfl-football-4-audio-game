"""The news of the Franchise: which lines a week's results make, the lines they become and the check of the news in league.sav (nfl4
only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 8.3 (SX.8e). The rules are plain functions over the league record (`extras/franchise/news.py`), so a test builds
a league, writes results into it by hand (the weeks are worked out on paper) and reads the events. The week's flow on the program rig is
tests/test_fr_week.py; news.txt is tests/test_fr_news_list.py.
"""
import random

import pytest

from drrig import SURNAMES
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging, news
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise.league import LeagueError, new_league
from nfl4.extras.franchise.news_pools import DEFAULT_POOLS
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, value_for

TEAM = 5                                   # the player's team: the first of the third pair
PAIRS = [(2 * i + 1, 2 * i + 2) for i in range(16)]       # (1, 2), (3, 4) ... (31, 32): the first team of a pair wins by default
WORDS = history.Words(lambda team: "Team%d" % team)
FLAT = D.WEIGHT_SUM * 70


def a_league():
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.sums = [FLAT] * D.TEAMS          # nobody is stronger than anybody: no upsets unless a test says so
    return league


def add_week(league, week, outcomes=None, margin=10):
    """The 16 games of a week as the engine records them: the first team of each pair wins `margin` points unless `outcomes` says
    otherwise: {pair index: (first wins?, winner score, loser score)}."""
    outcomes = outcomes or {}
    for index, (first, second) in enumerate(PAIRS):
        wins_first, ws, ls = outcomes.get(index, (True, 20 + margin, 20))
        winner, loser = (first, second) if wins_first else (second, first)
        league.results.append([0, week, winner, loser, ws, ls])


def events(league, week):
    return {e.pool: e for e in news.week_events(league, week)}


def pools_of(league, week):
    return [e.pool for e in news.week_events(league, week)]


# ----- the biggest win and the closest game -----

def test_the_biggest_win_is_the_largest_margin_and_the_first_of_equal_margins():
    league = a_league()
    add_week(league, 1, {7: (True, 35, 7), 3: (False, 38, 10), 9: (True, 30, 2)})          # three margins of 28
    big = events(league, 1)["NWB"]
    assert big.team == 8 and big.other == 7 and big.n == 28 and big.score == (38, 10)        # pair 3 comes first in the week's order


def test_the_closest_game_is_the_smallest_margin_of_the_games_not_already_told():
    league = a_league()
    add_week(league, 1, {5: (False, 21, 20), 2: (True, 24, 20)})
    close = events(league, 1)["NWC"]
    assert (close.team, close.other, close.n, close.score) == (12, 11, 1, (21, 20))


def test_the_closest_game_skips_the_game_an_upset_already_told():
    league = a_league()
    add_week(league, 1, {5: (True, 21, 20), 2: (True, 24, 20)})                    # pair 5 is the closest (1), pair 2 next (4)
    league.sums[11 - 1], league.sums[12 - 1] = league.sums[11 - 1], league.sums[11 - 1] + T.FR_UPSET_GAP * D.WEIGHT_SUM    # team 11 won as the weaker
    found = events(league, 1)
    assert found["NWU"].team == 11 and found["NWU"].other == 12
    assert found["NWC"].team == 5 and found["NWC"].other == 6 and found["NWC"].n == 4


def test_the_biggest_win_and_the_closest_game_are_never_the_same_game():
    league = a_league()
    add_week(league, 1, {0: (True, 50, 20)})
    found = events(league, 1)
    assert found["NWB"].team == 1 and found["NWC"].team != 1


# ----- the upset -----

def upset_league(gap_points, pair=4, wins_first=True):
    league = a_league()
    add_week(league, 1, {pair: (wins_first, 27, 20)} if pair is not None else None)
    first, second = PAIRS[pair]
    winner, loser = (first, second) if wins_first else (second, first)
    league.sums[loser - 1] = FLAT + gap_points
    return league, winner, loser


def test_an_upset_needs_a_winner_whose_rating_is_the_gap_or_more_under_the_losers():
    league, winner, loser = upset_league(T.FR_UPSET_GAP * D.WEIGHT_SUM)
    found = events(league, 1)["NWU"]
    assert (found.team, found.other) == (winner, loser)
    below, _w, _l = upset_league(T.FR_UPSET_GAP * D.WEIGHT_SUM - 1)
    assert "NWU" not in events(below, 1)


def test_the_upset_told_is_the_largest_gap_and_the_first_of_equal_gaps():
    league = a_league()
    add_week(league, 1)
    big = T.FR_UPSET_GAP * D.WEIGHT_SUM
    league.sums[2 - 1] = FLAT + big               # pair 0: the loser 2 is stronger by the gap
    league.sums[4 - 1] = FLAT + big               # pair 1: the same gap, later in the week
    league.sums[6 - 1] = FLAT + big + 1           # pair 2: the largest gap
    found = events(league, 1)["NWU"]
    assert (found.team, found.other) == (5, 6)
    league.sums[6 - 1] = FLAT + big
    found = events(league, 1)["NWU"]
    assert (found.team, found.other) == (1, 2)


def test_the_stronger_team_winning_is_no_upset_and_a_league_without_strengths_has_none():
    league = a_league()
    add_week(league, 1)
    league.sums[1 - 1] = FLAT + 5 * D.WEIGHT_SUM
    assert "NWU" not in events(league, 1)
    league.sums = []
    assert "NWU" not in events(league, 1)


# ----- the player's streak and the coach's milestone -----

def streak_league(results):
    """The player's team (the first of pair 2) wins or loses in the weeks as `results` says (True: wins)."""
    league = a_league()
    for week, wins in enumerate(results, start=1):
        add_week(league, week, {2: (wins, 27, 20)})
    return league


def test_the_players_winning_streak_is_told_from_the_third_win():
    league = streak_league([True, True, True, True])
    assert "NWY" not in events(league, 2)
    third = events(league, 3)["NWY"]
    assert (third.team, third.n) == (TEAM, 3)
    assert events(league, 4)["NWY"].n == 4


def test_the_players_losing_streak_is_told_and_a_win_breaks_the_streak():
    league = streak_league([False, False, False, True, False, False])
    found = events(league, 3)
    assert found["NWZ"].n == 3 and "NWY" not in found
    assert "NWZ" not in events(league, 4) and "NWZ" not in events(league, 5) and "NWZ" not in events(league, 6)


def test_the_players_streak_comes_first_of_the_lines():
    league = streak_league([True, True, True])
    assert pools_of(league, 3)[0] == "NWY"


def history_with_wins(league, wins):
    team = league.team
    league.history = [{"season": 1, "team": team, "coach": "Kim", "champion": 1, "runner_up": 2,
                       "wins": [wins if t == team - 1 else 8 for t in range(D.TEAMS)], "losses": [16 - 8] * D.TEAMS,
                       "finish": [0] * D.TEAMS, "playoff": [0, 0], "best": 1, "worst": 2, "top_points": None, "big_win": None,
                       "streak": None}]
    league.season = 2


def test_every_tenth_win_as_a_head_coach_is_a_milestone_and_only_in_the_week_it_is_won():
    league = a_league()
    history_with_wins(league, 8)                                 # eight wins in season 1
    for week, wins in enumerate([True, True, False, True], start=1):
        add_week(league, week, {2: (wins, 27, 20)})
    assert "NWM" not in events(league, 1)                         # nine
    milestone = events(league, 2)["NWM"]                          # ten
    assert (milestone.team, milestone.n) == (TEAM, 10)
    assert "NWM" not in events(league, 3)                         # lost: ten is not told again
    assert "NWM" not in events(league, 4)                         # eleven


def test_the_milestone_counts_every_season_and_follows_the_streak_in_the_order():
    league = a_league()
    history_with_wins(league, 17)
    for week in (1, 2, 3):
        add_week(league, week, {2: (True, 27, 20)})
    found = pools_of(league, 3)                                   # twenty wins and three in a row
    assert found[:2] == ["NWY", "NWM"] and events(league, 3)["NWM"].n == 20


def test_no_milestone_for_a_team_with_no_win():
    league = a_league()
    add_week(league, 1, {2: (False, 27, 20)})
    assert "NWM" not in events(league, 1)


# ----- another team's streak -----

def test_the_longest_streak_of_another_team_of_four_or_more_is_told_the_lower_team_first():
    league = a_league()
    for week in (1, 2, 3):
        add_week(league, week)
    assert "NWS" not in events(league, 3) and "NWL" not in events(league, 3)             # three are not enough
    add_week(league, 4)
    found = events(league, 4)["NWS"]                                                       # teams 1 and 3 won four, 2 and 4 lost four
    assert (found.team, found.n) == (1, 4)


def test_a_losing_streak_is_told_as_such_and_the_equal_streaks_go_to_the_lower_team_and_the_players_team_is_not_another_team():
    league = a_league()
    for week in (1, 2, 3, 4):
        add_week(league, week, {0: (False, 27, 20), 2: (True, 27, 20)})                  # team 2 wins, team 1 loses; the player wins
    found = events(league, 4)
    assert found["NWL"].team == 1 and found["NWL"].n == 4 and "NWS" not in found         # teams 1 (losses) and 2 (wins): the lower
    assert found["NWY"].team == TEAM                                                      # the player's own streak is its own line
    swapped = a_league()
    for week in (1, 2, 3, 4):
        add_week(swapped, week, {0: (True, 27, 20), 2: (False, 27, 20)})                 # the player loses four in a row
    found = events(swapped, 4)
    assert found["NWS"].team == 1 and found["NWZ"].team == TEAM and found["NWZ"].n == 4


def test_a_longer_streak_wins_over_a_shorter_one():
    league = a_league()
    for week in range(1, 6):
        add_week(league, week, {0: (week != 5, 27, 20)})                                   # team 1 wins four, then loses
    found = events(league, 5)
    assert found["NWS"].team == 3 and found["NWS"].n == 5                                 # five wins of team 3 (and 7, 9 ...) and five losses of 4


# ----- the order and the number of lines -----

def test_at_most_four_lines_in_the_order_streak_milestone_biggest_win_upset_league_streak_closest():
    league = a_league()
    history_with_wins(league, 6)
    for week in range(1, 5):
        add_week(league, week, {2: (True, 27, 20), 5: (True, 31, 30)})
    league.sums[8 - 1] = FLAT + T.FR_UPSET_GAP * D.WEIGHT_SUM                            # team 7 beats the stronger team 8
    found = news.week_events(league, 4)
    assert [e.pool for e in found] == ["NWY", "NWM", "NWB", "NWU"]                       # NWS and NWC are cut at four
    assert len(found) == T.FR_NEWS_MAX


def test_a_quiet_week_has_the_biggest_win_and_the_closest_game():
    league = a_league()
    add_week(league, 1, {0: (True, 30, 20), 1: (True, 21, 20)})
    assert pools_of(league, 1) == ["NWB", "NWC"]


def test_no_news_after_week_15_before_the_first_week_or_for_a_week_with_no_games():
    league = a_league()
    for week in (15, 16):
        add_week(league, week)
    assert news.week_events(league, 15) != [] and news.week_events(league, 16) == [] and news.week_events(league, 0) == []
    assert news.week_events(a_league(), 3) == []


def test_play_off_games_do_not_make_news_or_streaks():
    league = a_league()
    add_week(league, 1)
    league.results.append([1, 17, 2, 1, 40, 3])
    assert events(league, 1)["NWB"].n == 10
    assert news.streaks(league, 17)[2] == (-1, 1)                                         # team 2 lost week 1; the play-off win does not count


# ----- the offseason's events -----

def a_change(league, team, index, delta):
    player = league.active_of(team)[index]
    return aging.Change(player, max(40, min(99, player.rating + delta)))


def test_the_improvers_are_the_players_of_the_team_who_gained_five_or_more_the_biggest_first_at_most_two():
    league = a_league()
    for team in (TEAM, 6):
        for p in league.active_of(team):
            p.rating = 60
    changes = [a_change(league, TEAM, 0, 5), a_change(league, TEAM, 1, 9), a_change(league, TEAM, 2, 4), a_change(league, TEAM, 3, 9),
               a_change(league, TEAM, 4, 7), a_change(league, 6, 0, 20)]
    found = news.improver_events(changes, TEAM)
    assert [e.player.id for e in found] == [changes[1].player.id, changes[3].player.id]    # two 9s: the first in league order
    assert [e.rating for e in found] == [69, 69] and all(e.pool == "NWP" and e.team == TEAM for e in found)
    assert news.improver_events(changes[:1] + changes[2:3], TEAM)[0].rating == changes[0].new
    assert news.improver_events(changes[2:3], TEAM) == []


def test_the_champion_the_first_pick_and_the_retiring_stars_make_their_events():
    league = a_league()
    star = league.active_of(3)[0]
    assert news.champion_event(4, 9) == news.Event("NWT", team=9, n=4)
    assert news.first_pick_event(7, star).player is star and news.first_pick_event(7, star).team == 7
    assert [(e.pool, e.team) for e in news.star_events([star])] == [("NWR", 3)]


# ----- the lines -----

def test_placeholders_give_the_team_names_the_score_as_said_the_player_and_the_coach():
    league = a_league()
    player = league.active_of(3)[1]
    values = news.placeholders(news.Event("NWB", team=1, other=2, n=7, score=(27, 20)), league, WORDS)
    assert values == {"<coach>": "Kim", "<n>": "7", "<team>": "Team1", "<other>": "Team2", "<score>": "27 to 20"}
    values = news.placeholders(news.Event("NWP", team=TEAM, player=player, rating=80), league, WORDS)
    assert values["<player>"] == player.name and values["<position>"] == WORDS.position_for(player) and values["<r>"] == "80"  # SR.6: a man is said by his own position
    assert values["<team>"] == "Team%d" % TEAM


def strict(*picks):
    rnd = GameRandom(ScriptedRandom([value_for(n, k) for n, k in picks], strict=True))
    rnd.trace = []
    return rnd


def test_a_line_is_drawn_from_the_pool_filled_and_kept_with_the_history_of_the_pool():
    league = a_league()
    rnd = strict((4, 2))                                                                  # NWB02
    made = news.make_entries(league, [news.Event("NWB", team=1, other=2, n=7, score=(27, 20))], DEFAULT_POOLS, WORDS, rnd, 3)
    assert made == [{"season": 1, "week": 3, "pool": "NWB", "markup": "a big win for the Team1, 27 to 20 over the Team2.",
                     "told": 0}]
    assert league.news == made and league.news_recent["NWB"] == ["NWB02"] and rnd.trace == [4]


def test_a_line_is_never_one_of_the_last_three_of_its_pool():
    league = a_league()
    league.news_recent["NWB"] = ["NWB02", "NWB03", "NWB04"]
    rnd = strict((4, 2), (4, 3), (4, 4), (4, 1))                                          # the first three are refused
    made = news.make_entries(league, [news.Event("NWB", team=1, other=2, n=7, score=(27, 20))], DEFAULT_POOLS, WORDS, rnd, 3)
    assert made[0]["markup"] == "the Team1 beat the Team2 by 7 points." and league.news_recent["NWB"] == ["NWB03", "NWB04", "NWB01"]
    assert rnd.trace == [4, 4, 4, 4]


def test_render_changes_nothing_in_the_league_and_keep_puts_the_lines_in():
    league = a_league()
    rnd = strict((4, 1))
    lines, recent = news.render(league, [news.champion_event(4, 9)], DEFAULT_POOLS, WORDS, rnd)
    assert league.news == [] and league.news_recent == {} and recent == {"NWT": ["NWT01"]}
    assert lines == [("NWT", "the Team9 are the champions of season 4.")]
    made = news.keep(league, lines, recent, D.NEWS_OFFSEASON)
    assert league.news == made and made[0]["week"] == D.NEWS_OFFSEASON and league.news_recent == recent


def test_a_pool_with_every_line_off_makes_no_line_and_draws_nothing():
    from nfl4.extras.franchise.news_pools import NewsPools
    league = a_league()
    pools = NewsPools({pool: () if pool == "NWB" else DEFAULT_POOLS.lines(pool) for pool in D.NEWS_POOLS})
    rnd = strict()
    assert news.make_entries(league, [news.Event("NWB", team=1, other=2, n=7, score=(27, 20))], pools, WORDS, rnd, 3) == []
    assert league.news == [] and rnd.trace == []


def test_the_kept_lines_are_listed_newest_first_and_the_untold_ones_are_found():
    league = a_league()
    for season, week in ((1, 3), (1, 16), (2, 1), (1, 5)):
        league.news.append({"season": season, "week": week, "pool": "NWB", "markup": "x", "told": 0})
    league.news[1]["told"] = 1
    assert [(e["season"], e["week"]) for e in news.newest_first(league)] == [(2, 1), (1, 16), (1, 5), (1, 3)]
    assert len(news.untold(league)) == 3
    league.news.append({"season": 1, "week": 5, "pool": "NWC", "markup": "y", "told": 0})
    same_week = [e["markup"] for e in news.newest_first(league) if e["week"] == 5]
    assert same_week == ["x", "y"]                                        # the lines of one week keep the order they were made in


def test_a_new_season_drops_the_weekly_news_and_the_offseason_news_before_the_one_just_over():
    league = a_league()
    league.season = 3
    for season, week in ((3, 4), (3, D.NEWS_OFFSEASON), (2, D.NEWS_OFFSEASON), (2, 5)):
        league.news.append({"season": season, "week": week, "pool": "NWB", "markup": "x", "told": 1})
    news.drop_for_new_season(league)
    assert [(e["season"], e["week"]) for e in league.news] == [(3, D.NEWS_OFFSEASON)]


# ----- the check of the news in league.sav -----

def whole(value, low, high, what):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise LeagueError("%s is %r" % (what, value))


def a_line():
    return {"season": 1, "week": 3, "pool": "NWB", "markup": "a big win [pause]", "told": 0}


def test_well_formed_news_passes_the_check():
    league = a_league()
    league.news = [a_line(), dict(a_line(), week=D.NEWS_OFFSEASON, told=1)]
    league.news_recent = {"NWB": ["NWB01", "NWB02"], "NWT": []}
    news.check_entries(league, whole)


@pytest.mark.parametrize("change", [
    lambda e: e.update(pool="TO"), lambda e: e.update(week=0), lambda e: e.update(week=100), lambda e: e.update(season=0),
    lambda e: e.update(told=2), lambda e: e.update(markup=""), lambda e: e.update(markup="x" * 2001), lambda e: e.update(markup="a\x00b"),
    lambda e: e.update(markup=5), lambda e: e.update(extra=1), lambda e: e.pop("pool"),
])
def test_a_damaged_news_line_is_refused(change):
    league = a_league()
    line = a_line()
    change(line)
    league.news = [line]
    with pytest.raises(LeagueError):
        news.check_entries(league, whole)


@pytest.mark.parametrize("recent", [{"XX": []}, {"NWB": "NWB01"}, {"NWB": ["a", "b"]}, {"NWB": ["NWB01"] * 4}, {"NWB": [5]}, [],
                                    {pool: [] for pool in D.NEWS_POOLS} | {"NWB2": []}])
def test_a_damaged_news_history_is_refused(recent):
    league = a_league()
    league.news_recent = recent
    with pytest.raises(LeagueError):
        news.check_entries(league, whole)


def test_too_many_lines_are_refused_and_the_texts_of_the_pools_exist():
    league = a_league()
    league.news = [a_line() for _ in range(D.MAX_NEWS + 1)]
    with pytest.raises(LeagueError):
        news.check_entries(league, whole)
    assert all(len(DEFAULT_POOLS.lines(pool)) == 4 for pool in D.NEWS_POOLS) and X.REMARK_POOLS["NWB"][0] == "NWB01"


def test_the_tuning_file_holds_the_values_the_calibration_settled_on():
    assert (T.FR_NEWS_MAX, T.FR_STREAK_OWN, T.FR_STREAK_LEAGUE, T.FR_MILESTONE) == (4, 3, 4, 10)
    assert T.FR_UPSET_GAP == 3                                   # the design's 4 told an upset in 8 percent of the weeks, 3 in 26 (D-060)
    assert (T.FR_EXTRA_WORK_WEEKS, T.FR_EXTRA_WORK_AGE, T.FR_EXTRA_WORK_CANDIDATES, T.FR_EXTRA_WORK_POINTS) == ((2, 6, 10, 14), 24, 2, 3)
