"""The people's rules of the Franchise (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8n, research B2, B9, B10, D-074): the personality (a rule of the ID, its
talk and morale rules), the morale (the week's change, the pull toward zero, the bounds, its effect on a game's ratings and on the computer's games), the game
goal, the player tags, the holdouts (every branch of the rule decides somewhere, B-X62), the staff's pay rule, the trade demands and stage 6. Every number is
the tuning file's; the cases are worked by hand.
"""
import random

import pytest
from drrig import SURNAMES, draft_league

from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import injuries as INJ
from nfl4.extras.franchise import people as P
from nfl4.extras.franchise import resign
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import LeagueError, new_league
from nfl4.extras.franchise.strength import LeaguePlace
from nfl4.game.rnd import GameRandom

TEAM = 5


def league_of(seed=7, team=TEAM):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def first_with(league, team, word):
    return next(p for p in league.active_of(team) if p is not None and P.personality(p.id) == word)


# ----- the personality -----

def test_every_thousand_consecutive_ids_have_the_shares_exactly_and_no_word_is_left_out():
    for start in (1, 1000, 4321):
        counts = {}
        for pid in range(start, start + 1000):
            counts[P.personality(pid)] = counts.get(P.personality(pid), 0) + 1
        assert counts == {word: share * 10 for word, share in T.FR_PERSON_SHARES}
    assert set(P.PERSONALITIES) == {word for word, _ in T.FR_PERSON_SHARES} == set(T.FR_PERSON_MORALE)


def test_the_personality_is_spread_over_the_positions_of_a_new_league():
    league = league_of()
    for position in D.POSITIONS:
        players = [p for p in league.players.values() if p.pos == position]
        if len(players) < 60:
            continue
        for word, share in T.FR_PERSON_SHARES:
            got = sum(P.personality(p.id) == word for p in players) / len(players)
            assert abs(got - share / 100) < 0.12, (position, word, got)


def test_a_new_league_draws_nothing_for_the_people():
    source = GameRandom(random.Random(3))
    source.trace = []
    first = new_league(source, SURNAMES, "Kim", TEAM, "20260101-000000")
    assert first.people == P.empty()
    for pid in list(first.players)[:50]:                       # asking a player's word draws nothing
        P.personality(pid)
        P.tag_of(first.players[pid])
    count = len(source.trace)
    P.begin_holdouts(first, True)
    P.after_week(first, 2, [[0, 2, 3, 9, 21, 7]])
    P.week_sums(first, 3)
    assert len(source.trace) == count


def test_each_words_rule_in_the_talk():
    league = league_of()
    for word, (happy, content, unhappy) in T.FR_PERSON_TALK.items():
        player = first_with(league, TEAM, word)
        assert [P.slack_change(league, player, how) for how in ("happy", "content", "unhappy")] == [happy, content, unhappy]
    starter = next(p for p in league.players.values() if P.personality(p.id) == "playing_time" and p.place == D.PLACES_OF[p.pos][0])
    bench = next(p for p in league.players.values() if P.personality(p.id) == "playing_time" and p.place != D.PLACES_OF[p.pos][0])
    assert P.slack_change(league, starter, "content") == T.FR_PERSON_STARTER[0] and P.slack_change(league, bench, "content") == T.FR_PERSON_STARTER[1]


def test_the_slack_is_added_to_the_moods_and_never_under_zero():
    assert resign.floor_salary(1000, "content", 9, 0) == 1000 * (100 - T.FR_MOOD_SLACK["content"]) // 100
    assert resign.floor_salary(1000, "content", 9, 4) == 1000 * (100 - T.FR_MOOD_SLACK["content"] - 4) // 100
    assert resign.floor_salary(1000, "unhappy", 9, -4) == 1000                 # no slack under 0
    assert resign.Talk.start(league_of().player_at(TEAM, 0), "happy", -T.FR_MOOD_SLACK["happy"]).floor == resign.asking(league_of().player_at(TEAM, 0))[0]


def test_the_morale_moves_the_talks_mood_a_step_at_the_edges_only():
    league = league_of()
    player = league.player_at(TEAM, 0)
    for value, how, want in ((T.FR_MORALE_TALK, "content", "happy"), (T.FR_MORALE_TALK - 1, "content", "content"), (-T.FR_MORALE_TALK, "content", "unhappy"),
                             (T.FR_MORALE_TALK, "happy", "happy"), (-T.FR_MORALE_TALK, "unhappy", "unhappy"), (0, "unhappy", "unhappy")):
        P.set_morale(league, player.id, value)
        assert P.talk_mood(league, player, how) == want, (value, how)


# ----- the morale -----

def test_the_pull_the_bounds_the_effect_and_the_words():
    assert [P.toward_zero(v) for v in (5, 2, 1, 0, -1, -3)] == [5 - T.FR_MORALE_DECAY, max(0, 2 - T.FR_MORALE_DECAY), 0, 0, 0, -3 + T.FR_MORALE_DECAY]
    assert P.clamp(99) == T.FR_MORALE_MAX and P.clamp(-99) == -T.FR_MORALE_MAX
    per, cap = T.FR_MORALE_STEP
    assert [P.effect(v) for v in (0, per - 1, per, 2 * per, 6, -per, -6)] == [0, 0, 1, min(cap, 2), min(cap, 6 // per), -1, -min(cap, 6 // per)]
    assert max(abs(P.effect(v)) for v in range(-T.FR_MORALE_MAX, T.FR_MORALE_MAX + 1)) <= 2      # at most 2 rating points (research B10)
    assert (P.word(T.FR_MORALE_WORD), P.word(T.FR_MORALE_WORD - 1), P.word(-T.FR_MORALE_WORD)) == ("high", "good", "low")
    league = league_of()
    P.set_morale(league, 3, 0)
    assert "3" not in league.people["morale"]                  # a 0 is not kept


def week_league():
    league = league_of()
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    return league


def expected_change(pid, won, met, played=True):
    up, down, sat = T.FR_PERSON_MORALE[P.personality(pid)]
    return (up if won else -down) + (T.FR_GOAL_MORALE if met else -T.FR_GOAL_MORALE) - (0 if played else sat)


def test_a_week_moves_the_morale_of_both_teams_by_the_result_the_goal_and_the_personality():
    league = week_league()
    a, b = 3, 9
    kind_a, n_a = P.goal_for(league.sums, a, b)
    kind_b, n_b = P.goal_for(league.sums, b, a)
    P.set_morale(league, league.rosters[a - 1][0], 4)          # a player who had a morale: the pull first, then the change
    out = P.after_week(league, 2, [[0, 2, a, b, 31, 3]])
    assert out[a] == (True, P.goal_met(kind_a, n_a, 31, 3)) and out[b] == (False, P.goal_met(kind_b, n_b, 3, 31))
    for team, (won, met) in out.items():
        for index, pid in enumerate(league.rosters[team - 1]):
            start = 4 if (team, index) == (a, 0) else 0
            assert P.morale(league, pid) == P.clamp(P.toward_zero(start) + expected_change(pid, won, met)), (team, index)
    others = [pid for t in range(1, 33) if t not in (a, b) for pid in league.rosters[t - 1]]
    assert all(P.morale(league, pid) == 0 for pid in others)  # teams without a result move nothing
    assert league.people["verdict"] is None                    # the player's team did not play


def test_a_player_who_did_not_play_loses_his_words_weight_and_one_hurt_in_that_weeks_game_did_play():
    league = week_league()
    a, b = 3, 9
    costly = [p for p in league.active_of(a) if p is not None and T.FR_PERSON_MORALE[P.personality(p.id)][2] > 0]
    sitting, in_game = costly[0], costly[1]                      # words whose week out costs something, so "played" decides
    INJ.injure(league, sitting.id, "IJA", 4, 0, 1)             # hurt in week 1's game: out for week 2
    INJ.injure(league, in_game.id, "IJA", 4, 0, 2)             # hurt in week 2's own game: he played it
    P.after_week(league, 2, [[0, 2, a, b, 24, 21]])
    kind, n = P.goal_for(league.sums, a, b)
    met = P.goal_met(kind, n, 24, 21)
    assert P.morale(league, sitting.id) == P.clamp(expected_change(sitting.id, True, met, played=False))
    assert P.morale(league, in_game.id) == P.clamp(expected_change(in_game.id, True, met, played=True))


def test_weeks_after_the_last_move_nothing_and_the_play_offs_move_nothing():
    league = week_league()
    assert P.after_week(league, T.FR_MORALE_LAST_WEEK + 1, [[0, T.FR_MORALE_LAST_WEEK + 1, 3, 9, 30, 0]]) == {}
    assert P.after_week(league, 5, [[1, 5, 3, 9, 30, 0]]) == {}
    assert league.people["morale"] == {}


def test_the_players_teams_verdict_is_kept_for_the_next_menu():
    league = week_league()
    P.after_week(league, 3, [[0, 3, 9, TEAM, 40, 0]])
    kind, n = P.goal_for(league.sums, TEAM, 9)
    assert league.people["verdict"] == [league.season, 3, int(P.goal_met(kind, n, 0, 40)), 0]


def test_the_morale_reaches_a_played_games_ratings_only_through_the_players_own_places():
    league = week_league()
    team = 4
    table = P.plain_table(league, team)
    star = league.player_at(team, 0)
    P.set_morale(league, star.id, T.FR_MORALE_MAX)
    moved = P.with_morale(league, team, table)
    assert moved[0][2] == min(99, star.rating + P.effect(T.FR_MORALE_MAX)) and moved[1:] == table[1:]
    sub = list(table)
    other = league.player_at(team, 1)
    P.set_morale(league, other.id, T.FR_MORALE_MAX)               # the substitute has a morale of his own: still none on the place he covers
    sub[0] = (other.id, "sub", 50)                               # the place played by another man: his replacement level stays
    assert P.with_morale(league, team, sub)[0] == sub[0]
    star.rating = 99
    assert P.with_morale(league, team, P.plain_table(league, team))[0][2] == 99      # never over the scale
    P.set_morale(league, star.id, -T.FR_MORALE_MAX)
    star.rating = 40
    assert P.with_morale(league, team, P.plain_table(league, team))[0][2] == 40


def test_the_weeks_sums_are_the_injuries_with_no_morale_and_add_the_weighted_effect_with_it():
    league = week_league()
    assert P.week_sums(league, 3) == INJ.effective_sums(league, 3) == league.sums
    team = 6
    for index, pid in enumerate(league.rosters[team - 1]):
        P.set_morale(league, pid, T.FR_MORALE_MAX)
    gain = sum(D.WEIGHT[D.POSITION_OF_PLACE[i]] * (min(99, league.player_at(team, i).rating + P.effect(T.FR_MORALE_MAX)) - league.player_at(team, i).rating)
               for i in range(D.PLACE_COUNT))
    sums = P.week_sums(league, 3)
    assert sums[team - 1] == league.sums[team - 1] + gain > league.sums[team - 1]
    assert [s for t, s in enumerate(sums, start=1) if t != team] == [s for t, s in enumerate(league.sums, start=1) if t != team]
    place = LeaguePlace(league.sums, sums)
    assert place.shift(team) >= LeaguePlace(league.sums).shift(team)


def test_a_hurt_teams_morale_counts_only_where_its_own_players_play():
    league = week_league()
    team = 6
    hurt = league.player_at(team, 0)                             # a running back, hurt in week 2's game: out for week 3 (the next man plays his place)
    INJ.injure(league, hurt.id, "IJA", 4, 0, 2)
    for pid in league.rosters[team - 1]:
        P.set_morale(league, pid, T.FR_MORALE_MAX)
    table = INJ.lineup(league, team, 3, True, hurt_before=3)
    want = INJ.effective_sums(league, 3)[team - 1] + P.gain_of(league, team, table)
    assert P.week_sums(league, 3)[team - 1] == want
    assert P.gain_of(league, team, table) != P.gain_of(league, team, P.plain_table(league, team))     # the hurt man's morale does not count


def test_the_effect_of_a_team_in_the_computers_games_is_bounded_with_the_injuries():
    league = week_league()
    team = 6
    for pid in league.rosters[team - 1]:
        P.set_morale(league, pid, T.FR_MORALE_MAX)
    sums = P.week_sums(league, 3)
    healthy = LeaguePlace(league.sums)
    moved = LeaguePlace(league.sums, sums)
    num, den = T.FR_INJ_SD_MAX
    limit = (num * num * healthy.spread_sq // (healthy.n * den * den)) ** 0.5
    assert 0 < moved.d[team - 1] - healthy.d[team - 1] <= limit + 1        # the bound of the week's changes (strength.LeaguePlace) holds the morale too
    huge = list(league.sums)
    huge[team - 1] += 78 * 30
    assert LeaguePlace(league.sums, huge).d[team - 1] - healthy.d[team - 1] <= limit + 1


# ----- the game goal -----

def test_the_goal_follows_the_gap_of_the_two_teams_and_its_verdict_the_score():
    sums = [70 * 78] * 32
    sums[0] += T.FR_GAME_GOAL_GAP * 78
    assert P.goal_for(sums, 1, 2) == ("margin", T.FR_GAME_GOAL_MARGIN)
    assert P.goal_for(sums, 2, 1) == ("close", T.FR_GAME_GOAL_CLOSE)
    sums[0] -= 1
    assert P.goal_for(sums, 1, 2) == ("win", 0) == P.goal_for(sums, 2, 1)
    assert P.goal_for([], 1, 2) == ("win", 0)
    n = T.FR_GAME_GOAL_MARGIN
    assert P.goal_met("margin", n, 21 + n, 21) and not P.goal_met("margin", n, 20 + n, 21)
    assert P.goal_met("close", n, 21, 21 + n) and not P.goal_met("close", n, 20, 21 + n) and P.goal_met("close", n, 30, 10)
    assert P.goal_met("win", 0, 14, 13) and not P.goal_met("win", 0, 13, 13)


def test_the_players_team_is_judged_by_the_goal_he_heard_even_when_a_trade_changed_the_strengths():
    league = week_league()
    P.set_goal(league, 3, 9)
    league.people["goal"][2:4] = ["win", 0]                      # what he heard: win the game
    league.sums[TEAM - 1] = league.sums[8] + T.FR_GAME_GOAL_GAP * 78 * 3      # a trade since: by the sums alone his goal would be a margin of 14
    assert P.goal_for(league.sums, TEAM, 9)[0] == "margin"
    P.after_week(league, 3, [[0, 3, TEAM, 9, 24, 20]])
    assert league.people["verdict"] == [league.season, 3, 1, 0]   # a win of 4 meets "win"


def test_a_game_the_engine_plays_has_the_engines_points():
    sums = [70 * 78] * 32
    sums[0] += T.FR_GAME_GOAL_GAP * 78
    margin, close = T.FR_GAME_GOAL_PLAYED
    assert P.goal_for(sums, 1, 2, played=True) == ("margin", margin) and P.goal_for(sums, 2, 1, played=True) == ("close", close)
    assert (margin, close) != (T.FR_GAME_GOAL_MARGIN, T.FR_GAME_GOAL_CLOSE)
    league = week_league()
    league.sums = list(sums)
    league.team = 1
    assert P.set_goal(league, 3, 2)[2:4] == ["margin", margin]
    league.people["goal"] = None
    P.after_week(league, 3, [[0, 3, 1, 2, 20 + margin, 20], [0, 3, 3, 4, 20 + margin, 20]])
    assert league.people["verdict"][2] == 1                       # the player's game by the engine's points (no goal heard: the rule's)
    out = P.after_week(week_league(), 3, [[0, 3, 2, 1, 21, 20]])
    assert out[2] == (True, P.goal_met(*P.goal_for(week_league().sums, 2, 1), 21, 20))     # another team's game: the score table's points


def test_the_players_goal_is_set_for_a_regular_week_against_his_opponent():
    league = week_league()
    goal = P.set_goal(league, 4, 9)
    assert goal == [league.season, 4] + list(P.goal_for(league.sums, TEAM, 9, played=True)) + [0]
    assert P.set_goal(league, 17, 9) is None and league.people["goal"] is None
    assert P.set_goal(league, T.FR_MORALE_LAST_WEEK, 9) is not None
    assert P.set_goal(league, T.FR_MORALE_LAST_WEEK + 1, 9) is None          # a week whose result moves nothing has no goal (it would get no verdict)
    assert P.set_goal(league, 4, TEAM) is None


# ----- the player tags -----

def test_the_tags_from_rating_age_and_potential():
    player = league_of().player_at(TEAM, 0)
    player.rating, player.age, player.potential = T.FR_PTAG_STAR, 22, "high"
    assert P.tag_of(player) == "star"
    player.rating = T.FR_PTAG_STAR - 1
    assert P.tag_of(player) == "rising"
    player.potential = "average"
    assert P.tag_of(player) is None
    player.age = T.FR_PTAG_VETERAN
    assert P.tag_of(player) == "veteran"
    player.age, player.potential = T.FR_PTAG_YOUNG + 1, "high"
    assert P.tag_of(player) is None


# ----- the holdouts -----

def holdout_league(word="money", age=24, team=TEAM, seed=4):
    """A league at the start of stage 3 with one player of `team` who holds out (rated 86, paid half his market price, two years left, four seasons)."""
    league = draft_league(seed=seed, team=TEAM, stage_no=D.STAGE_DEVELOPMENT)
    player = first_with(league, team, word)
    player.rating, player.age, player.seasons, player.years = 86, age, 4, 2
    player.salary = CT.market_salary(player.pos, 86) // 2
    if word != "money":
        P.set_morale(league, player.id, T.FR_HOLDOUT_MORALE)
    return league, player


def test_every_branch_of_the_holdout_rule_decides():
    league, player = holdout_league("money")
    player.salary = T.FR_MIN_SALARY                               # underpaid at every rating: each branch below decides alone
    assert P.holds_out(league, player)
    for attribute, value in (("years", 0), ("seasons", T.FR_HOLDOUT_SEASONS - 1), ("rating", T.FR_HOLDOUT_RATING - 1), ("place", -1)):
        keep = getattr(player, attribute)
        setattr(player, attribute, value)
        assert not P.holds_out(league, player), attribute
        setattr(player, attribute, keep)
    player.salary = CT.market_salary(player.pos, player.rating) // 2
    keep = player.salary
    player.salary = (CT.market_salary(player.pos, player.rating) * T.FR_HOLDOUT_UNDERPAID + 99) // 100
    assert not P.holds_out(league, player)                     # paid at the line: not underpaid
    player.salary = keep
    other, someone = holdout_league("winning")
    assert P.holds_out(other, someone)
    P.set_morale(other, someone.id, T.FR_HOLDOUT_MORALE + 1)
    assert not P.holds_out(other, someone)                     # a word that is not money needs a low morale
    P.set_morale(league, player.id, T.FR_MORALE_MAX)
    assert P.holds_out(league, player)                         # money holds out whatever his morale
    loyal, man = holdout_league("loyalty")
    P.set_morale(loyal, man.id, -T.FR_MORALE_MAX)
    assert not P.holds_out(loyal, man)                         # loyalty never


def test_the_holdout_rules_edges():
    league, player = holdout_league("money")
    player.rating = T.FR_HOLDOUT_RATING
    player.salary = CT.market_salary(player.pos, player.rating) // 2
    assert P.holds_out(league, player)
    player.seasons = T.FR_HOLDOUT_SEASONS
    assert P.holds_out(league, player)
    player.years = 1
    assert P.holds_out(league, player)
    other, man = holdout_league("winning")
    P.set_morale(other, man.id, T.FR_HOLDOUT_MORALE)
    assert P.holds_out(other, man)


def test_a_team_has_one_holdout_at_most_the_most_valuable():
    league, player = holdout_league("money")
    second = next(p for p in league.active_of(TEAM) if p is not None and p.id != player.id and P.personality(p.id) == "money")
    second.rating, second.seasons, second.years = 80, 4, 2
    second.salary = CT.market_salary(second.pos, 80) // 2
    assert P.holds_out(league, second)
    assert P.holdout_of(league, TEAM) == sorted([player, second], key=resign.value)[:T.FR_HOLDOUT_TEAM_MAX]


@pytest.fixture
def no_target(monkeypatch):
    """The staff's payroll target out of the way (a new league's contracts are all at the market price and over it): the target's branch has its own case."""
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 1.0)


def test_the_staff_pays_a_young_holdout_who_fits_and_lets_an_older_one_or_one_over_the_target_wait(no_target):
    league, player = holdout_league("money", age=T.FR_HOLDOUT_PAY_AGE)
    assert P.staff_pays(league, TEAM, player)
    player.age = T.FR_HOLDOUT_PAY_AGE + 1
    assert not P.staff_pays(league, TEAM, player)
    player.age = T.FR_HOLDOUT_PAY_AGE
    keep = T.FR_RESIGN_TARGET
    try:
        T.FR_RESIGN_TARGET = 0.0                                # the payroll target is met already: he waits
        assert not P.staff_pays(league, TEAM, player)
    finally:
        T.FR_RESIGN_TARGET = keep
    league.dead[TEAM - 1] = T.FR_CAP                            # no room under the cap
    assert not P.staff_pays(league, TEAM, player) and not P.can_pay(league, TEAM, player, P.new_contract(player)[0])


def test_the_cap_alone_can_stop_the_staff_paying(no_target, monkeypatch):
    league, player = holdout_league("money", age=T.FR_HOLDOUT_PAY_AGE)
    assert P.staff_pays(league, TEAM, player)
    monkeypatch.setattr(T, "FR_RESIGN_RESERVE", T.FR_CAP)         # the room of stage 7's rule is gone; the payroll target (1.0 of the cap) still allows it
    assert not P.can_pay(league, TEAM, player, P.new_contract(player)[0]) and not P.staff_pays(league, TEAM, player)


def test_begin_settles_the_computer_teams_and_leaves_the_players_own_for_him(no_target):
    league, own = holdout_league("money", team=TEAM)
    other = first_with(league, 9, "money")
    other.rating, other.age, other.seasons, other.years = 86, 30, 4, 2
    other.salary = CT.market_salary(other.pos, 86) // 2
    young = first_with(league, 12, "money")
    young.rating, young.age, young.seasons, young.years = 86, 24, 4, 2
    young.salary = CT.market_salary(young.pos, 86) // 2
    rows = P.begin_holdouts(league, False)
    assert sorted(rows) == sorted([[own.id, TEAM, league.season, P.PENDING], [other.id, 9, league.season, P.WAITED], [young.id, 12, league.season, P.PAID]])
    assert league.people["pending"] == [own.id] and league.people["begun"] == league.season
    assert P.morale(league, other.id) == -T.FR_MORALE_MAX
    assert (young.salary, young.years) == P.new_contract(young) == (max(CT.market_contract(young)[0], young.salary), CT.market_contract(young)[1])
    assert own.salary == CT.market_salary(own.pos, 86) // 2    # nothing decided for the player
    with_staff, mine = holdout_league("money")
    P.begin_holdouts(with_staff, True)
    assert with_staff.people["pending"] == [] and P.row_of(with_staff, mine.id)[3] == P.PAID


def test_a_new_leagues_teams_over_the_target_let_a_young_holdout_wait():
    league, player = holdout_league("money", age=T.FR_HOLDOUT_PAY_AGE)
    assert resign.running_payroll(league, TEAM) - player.salary + P.new_contract(player)[0] + league.dead[TEAM - 1] > resign.target_payroll()
    assert not P.staff_pays(league, TEAM, player)


def test_the_players_answers():
    for outcome in (P.PAID, P.WAITED, P.ON_BLOCK):
        league, player = holdout_league("money")
        P.begin_holdouts(league, False)
        before = player.salary
        P.answer_holdout(league, player.id, outcome)
        assert league.people["pending"] == [] and P.row_of(league, player.id)[3] == outcome
        assert (player.salary != before) == (outcome == P.PAID)
        assert (P.morale(league, player.id) == -T.FR_MORALE_MAX) == (outcome != P.PAID)


# ----- the trade demands -----

def season_league_with(outcome, team=9, word="money"):
    """A league in week 1 of the season whose last camp left a player of `team` with `outcome`."""
    league, player = holdout_league(word, team=team, age=30)
    league.stage, league.stage_no, league.gtp = "season", 0, 1
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    league.people["holdouts"] = [[player.id, team, league.season, outcome]]
    league.people["begun"] = league.season
    P.set_morale(league, player.id, -T.FR_MORALE_MAX)
    return league, player


def test_a_player_on_the_block_asks_at_once_and_one_who_waited_from_the_demand_week_while_his_morale_is_low():
    league, player = season_league_with(P.ON_BLOCK)
    assert [r[0] for r in P.file_demands(league, 1)] == [player.id]
    assert P.file_demands(league, 2) == []                     # once a season
    waited, man = season_league_with(P.WAITED)
    if T.FR_DEMAND_WEEK > 1:
        assert P.file_demands(waited, T.FR_DEMAND_WEEK - 1) == []
    P.set_morale(waited, man.id, T.FR_DEMAND_MORALE + 1)
    assert P.file_demands(waited, T.FR_DEMAND_WEEK) == []      # his morale came back
    P.set_morale(waited, man.id, T.FR_DEMAND_MORALE)
    assert [r[0] for r in P.file_demands(waited, T.FR_DEMAND_WEEK)] == [man.id]
    paid, someone = season_league_with(P.PAID)
    assert P.file_demands(paid, 5) == []
    late, other = season_league_with(P.ON_BLOCK)
    assert P.file_demands(late, T.FR_TRADE_LAST_WEEK + 1) == []  # outside the window


def test_a_computer_team_takes_the_best_offer_it_can_accept_and_the_trade_is_a_demands():
    league, player = season_league_with(P.ON_BLOCK)
    records = list(league.records)
    offers = TR.block_offers(league, 9, player, records, 1)
    made, own, filed = P.demands_week(league, 1, records)
    assert own == [] and [r[0] for r in filed] == [player.id]
    if offers and P.acceptable(league, filed[0], offers[0][1]):
        assert made == [offers[0][0]] and league.trades["log"][-1][7] == TR.KIND_DEMAND
        assert player.team != 9 and P.demand_of(league, player.id)[3] == P.TRADED and P.morale(league, player.id) == 0
    else:
        assert made == [] and P.demand_of(league, player.id)[3] == P.OPEN


def test_a_computer_team_makes_the_demand_trade_when_the_offer_is_acceptable(monkeypatch):
    monkeypatch.setattr(T, "FR_DEMAND_GIVE", 10 ** 6)            # every offer is acceptable
    league, player = season_league_with(P.ON_BLOCK)
    records = list(league.records)
    offers = P.offers_for(league, [player.id, 9, 1, P.OPEN], records, 1)
    assert offers
    made, _own, _filed = P.demands_week(league, 1, records)
    assert made == [offers[0][0]] and player.team == offers[0][0].b
    assert league.trades["log"][-1][7] == TR.KIND_DEMAND and P.demand_of(league, player.id)[3] == P.TRADED and P.morale(league, player.id) == 0


def test_a_computer_teams_demand_never_takes_an_offer_of_the_players_team(monkeypatch):
    monkeypatch.setattr(T, "FR_DEMAND_GIVE", 10 ** 6)
    league, player = season_league_with(P.ON_BLOCK)
    theirs = league.group_of(TEAM, player.pos)[0]
    real = TR.block_offers
    monkeypatch.setattr(TR, "block_offers", lambda *a, **k: [(TR.Trade(9, TEAM, player.id, theirs.id), 10 ** 5)] + real(*a, **k))    # his team's offer first
    records = list(league.records)
    assert any(TEAM in (t.a, t.b) for t, _g in TR.block_offers(league, 9, player, records, 1))
    assert all(TEAM not in (t.a, t.b) for t, _g in P.offers_for(league, [player.id, 9, 1, P.OPEN], records, 1))
    keep = {p.id: p.team for p in league.players.values() if p.team == TEAM}
    P.demands_week(league, 1, records)
    assert {p.id: p.team for p in league.players.values() if p.id in keep} == keep


def test_the_computer_teams_rule_refuses_an_offer_that_costs_too_much():
    league, player = season_league_with(P.ON_BLOCK)
    row = [player.id, 9, 1, P.OPEN]
    line = -T.FR_DEMAND_GIVE * D.WEIGHT[player.pos]
    assert P.acceptable(league, row, line) and not P.acceptable(league, row, line - 1)
    keep = T.FR_DEMAND_GIVE
    try:
        T.FR_DEMAND_GIVE = -10 ** 6                             # nothing is acceptable: the demand waits
        made, _own, _filed = P.demands_week(league, 1, list(league.records))
        assert made == [] and P.demand_of(league, player.id)[3] == P.OPEN and player.team == 9
    finally:
        T.FR_DEMAND_GIVE = keep


def test_a_demand_of_the_players_team_waits_for_his_answer_and_the_deadline_ends_every_demand():
    league, player = season_league_with(P.ON_BLOCK, team=TEAM)
    made, own, _filed = P.demands_week(league, 1, list(league.records))
    assert made == [] and player.team == TEAM
    assert all(row[0] == player.id for row, _offers in own)
    P.demands_week(league, T.FR_TRADE_LAST_WEEK + 1, list(league.records))
    assert P.demand_of(league, player.id)[3] == P.ENDED


def test_the_recommendation_is_the_first_answer_of_a_demand():
    league, player = season_league_with(P.ON_BLOCK, team=TEAM)
    row = [player.id, TEAM, 1, P.OPEN]
    good = [("t1", 0), ("t2", -10 ** 6)]
    bad = [("t1", -10 ** 6), ("t2", -10 ** 7)]
    assert P.demand_answers(league, row, good) == ["t1", "t2", None]
    assert P.demand_answers(league, row, bad) == [None, "t1", "t2"]


# ----- stage 6 and the whole-file check -----

def test_the_new_season_halves_the_morale_toward_zero_and_ends_the_seasons_demands():
    league = week_league()
    ids = [league.rosters[0][i] for i in range(4)]
    for pid, value in zip(ids, (6, 5, -5, 1)):
        P.set_morale(league, pid, value)
    league.people["demands"] = [[ids[0], 1, 3, P.OPEN]]
    league.people["goal"] = [1, 3, "win", 0, 1]
    P.new_season(league)
    assert [P.morale(league, pid) for pid in ids] == [3, 2, -2, 0]
    assert league.people["demands"] == [] and league.people["goal"] is None and league.people["verdict"] is None


@pytest.mark.parametrize("break_it", [
    lambda lg, pid: lg.people["morale"].update({"999999": 3}),
    lambda lg, pid: lg.people["morale"].update({str(pid): 0}),
    lambda lg, pid: lg.people["morale"].update({str(pid): T.FR_MORALE_MAX + 1}),
    lambda lg, pid: lg.people.update(pending=[pid]),
    lambda lg, pid: lg.people.update(holdouts=[[pid, 5, 1, P.PENDING]], pending=[pid]),
    lambda lg, pid: lg.people.update(holdouts=[[pid, 5, 1, 7]]),
    lambda lg, pid: lg.people.update(holdouts=[[pid, 5, 1, 1], [pid, 5, 1, 2]]),
    lambda lg, pid: lg.people.update(demands=[[pid, 5, 3, 0], [pid, 5, 4, 0]]),
    lambda lg, pid: lg.people.update(demands=[[pid, 5, T.FR_TRADE_LAST_WEEK + 1, 0]]),
    lambda lg, pid: lg.people.update(goal=[1, 3, "lose", 0, 0]),
    lambda lg, pid: lg.people.update(verdict=[1, 3, 2, 0]),
    lambda lg, pid: lg.people.update(extra=1),
    lambda lg, pid: lg.people.pop("goal"),
    lambda lg, pid: lg.people["morale"].update({"0" + str(pid): 3}),
    lambda lg, pid: lg.people["morale"].update({"\u00b2": 3}),
    lambda lg, pid: lg.people["morale"].update({"\uff11": 3}),
    lambda lg, pid: lg.people.update(pending=["x", pid]),
])
def test_the_whole_file_check_refuses_damage(break_it):
    league = league_of()
    pid = league.rosters[TEAM - 1][0]
    break_it(league, pid)
    with pytest.raises(LeagueError):
        league.check()


def test_the_programs_computer_games_read_the_morale():
    from types import SimpleNamespace
    from nfl4.extras.franchise.mode import FranchiseHooks
    league = week_league()
    league.gtp = 3
    hooks = FranchiseHooks(SimpleNamespace(league=league))
    plain = hooks.place()
    assert plain.d == LeaguePlace(league.sums).d
    for pid in league.rosters[5]:
        P.set_morale(league, pid, T.FR_MORALE_MAX)
    moved = FranchiseHooks(SimpleNamespace(league=league)).place()
    assert moved.d == LeaguePlace(league.sums, P.week_sums(league, 3)).d and moved.d[5] > plain.d[5]


def test_a_holdout_to_ask_is_whole_at_stage_three():
    league, player = holdout_league("money")
    P.begin_holdouts(league, False)
    league.check()
    league.stage_no = D.STAGE_CONTRACTS
    with pytest.raises(LeagueError):
        league.check()
