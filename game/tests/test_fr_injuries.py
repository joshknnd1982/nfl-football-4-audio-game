"""Injuries of the Franchise: the rules as plain functions (nfl4 only, rule 0.13; NFL_EXTRA_FEATURES N6.8 INJ-1 to INJ-6, NFL_FRANCHISE_DESIGN 17 SX.8k,
D-071): the statuses, who plays, the lineup and its strength, the week's draws in their order, the limit of a team, the spoken range, the stand-ins, the
league record of format 6, the to-do item, the trades and the computer's games. The game and the program are test_fr_injury_flow.py.
"""
import copy
import json
import random

import pytest
from drrig import SURNAMES, legacy_data

from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import first_names as FN
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import injury_flow as F
from nfl4.extras.franchise import todo
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import OFFSEASON, LeagueError, LeagueRecord, new_league
from nfl4.extras.franchise.strength import LeaguePlace
from nfl4.game.rnd import GameRandom
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import history

F_WORDS = history.Words(lambda team: "Team%d" % team)

TEAM = 5


class FakeRnd:
    """A source that answers `below` and `rnd` from a script (then `default`) and records every draw's size, so a test sees the draws in their order."""

    def __init__(self, script=(), default=None):
        self.script = list(script)
        self.default = default
        self.sizes = []

    def below(self, n):
        self.sizes.append(n)
        if self.script:
            value = self.script.pop(0)
        else:
            value = n - 1 if self.default is None else self.default
        assert 0 <= value < n, (value, n)
        return value

    def __call__(self, n):
        return self.below(n) + 1

    def redraw(self, draw, ok, scan, what):
        value = draw()
        return value if ok(value) else scan()


def fresh(seed=3, team=TEAM):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")
    league.gtp = 1
    return league


def place_of(league, team, position, number=0):
    return D.PLACES_OF[position][number]


def player_at(league, team, position, number=0):
    return league.player_at(team, place_of(league, team, position, number))


def hurt(league, player, games, week=1, kind="IJA", offset=0):
    return I.injure(league, player.id, kind, games, offset, week)


def by_depth(league, team, position):
    return [league.player_at(team, i) for i in D.PLACES_OF[position]]          # the depth order is the place order


# ----- the statuses -----

def test_status_by_the_games_still_to_miss_and_in_the_play_offs():
    league = fresh()
    back = player_at(league, 1, "RB")
    row = hurt(league, back, 3, week=2)                        # back: week 6
    assert row[3] == 6 and I.left(row, 3) == 3
    assert [I.status_of_row(row, w) for w in (3, 4, 5, 6, 7)] == ["out", "doubtful", "questionable", "healthy", "healthy"]
    row[3] = 19                                                # a long injury: every play-off week before 19 is out, never doubtful
    assert [I.status_of_row(row, w) for w in (16, 17, 18, 19)] == ["out", "out", "out", "healthy"]
    row[3] = 18
    assert I.status_of_row(row, 16) == "doubtful" and I.status_of_row(row, 17) == "out"


def test_who_plays_the_staff_rule_and_the_players_own_decision():
    league = fresh()
    own_q, own_d = player_at(league, TEAM, "RB", 0), player_at(league, TEAM, "RB", 1)
    cpu_q, cpu_d = player_at(league, 1, "RB", 0), player_at(league, 1, "RB", 1)
    for p in (own_q, cpu_q):
        hurt(league, p, 1, week=1)                             # questionable at week 2
    for p in (own_d, cpu_d):
        hurt(league, p, 2, week=1)                             # doubtful at week 2
    assert I.plays(league, cpu_q, 2, staff=False) and not I.plays(league, cpu_d, 2, staff=False)       # the computer teams: the staff's rule
    assert I.plays(league, own_q, 2, staff=True) and not I.plays(league, own_d, 2, staff=True)         # the player's team, the staff setting on
    assert not I.plays(league, own_q, 2, staff=False) and not I.plays(league, own_d, 2, staff=False)   # off: nothing is decided for him, he rests
    I.decide(league, own_d.id, 2, True)
    assert I.plays(league, own_d, 2, staff=False) and not I.plays(league, own_d, 3, staff=False)       # the decision is for its week only
    I.decide(league, own_d.id, 2, False)
    assert not I.plays(league, own_d, 2, staff=False)
    assert not I.plays(league, cpu_q, 2, staff=False, out=frozenset({cpu_q.id}))                      # hurt in the game in progress


# ----- the lineup -----

def test_nobody_hurt_the_lineup_is_the_roster_and_the_sums_are_the_seasons():
    league = fresh()
    for team in range(1, D.TEAMS + 1):
        table = I.lineup(league, team, 3, staff=False)
        roster = league.roster_for_game(team)
        assert [entry[0] for entry in table] == league.rosters[team - 1]
        assert [entry[2] for entry in table] == [league.player_at(team, i).rating for i in range(D.PLACE_COUNT)]
        made = F.lineup_roster(league, team, 3, False)
        assert made.names() == roster.names() and made.ratings == roster.ratings and made.quarterback == roster.quarterback
        assert I.effective_sum(league, team, 3) == league.strength_sum(team)
    assert I.effective_sums(league, 3) == league.sums


def test_an_out_player_is_replaced_by_the_next_man_down_the_depth_order():
    league = fresh()
    depth = by_depth(league, 1, "WR")
    hurt(league, depth[2], 5)                                  # the third receiver is out: the fourth plays his place
    table = I.lineup(league, 1, 2, staff=False)
    assert table[depth[2].place][0] == depth[3].id and table[depth[2].place][2] == min(depth[3].rating, T.FR_INJ_STAND_IN_OTHER)     # replacement level
    assert depth[2].id not in [entry[0] for entry in table]
    hurt(league, depth[-1], 5)                                 # the last one is out too: the nearest one above who plays takes his place
    table = I.lineup(league, 1, 2, staff=False)
    assert table[depth[-1].place][0] == depth[-2].id


def test_the_rating_of_an_injured_player_never_counts():
    league = fresh()
    back = player_at(league, 2, "RB", 3)
    hurt(league, back, 6)
    before = I.effective_sum(league, 2, 3)
    for rating in (40, 99):
        back.rating = rating
        assert I.effective_sum(league, 2, 3) == before          # whatever his rating, the sum is the healthy players'
        assert all(entry[0] != back.id for entry in I.lineup(league, 2, 3, staff=False))


@pytest.mark.parametrize("seed", [3, 8])
def test_an_injury_raises_a_teams_strength_only_from_under_replacement_level(seed):
    """Every player of eight teams hurt one at a time (season 1: the places are in the order they were drawn, not by rating): his place is played at
    replacement level whoever plays it (the next man up, the one above the last man, a returner's cover, a stand-in), every other place as before, so
    the strength rises only when he was rated under replacement level, and by no more than that."""
    league = fresh(seed)
    for team in range(1, 9):
        for index in range(D.PLACE_COUNT):
            league.injuries = I.empty()
            player = league.player_at(team, index)
            I.injure(league, player.id, "IJA", 5, 0, 1)
            I.settle(league, 2, FakeRnd(), SURNAMES)
            replacement = I.stand_in_rating(player.pos)
            assert I.effective_sum(league, team, 2) - league.strength_sum(team) <= D.WEIGHT[player.pos] * max(0, replacement - player.rating), (team, index)
            table = I.lineup(league, team, 2, staff=False)
            assert table[index][2] <= replacement and all(table[i][2] == league.player_at(team, i).rating for i in range(D.PLACE_COUNT) if i != index)


def test_a_player_who_plays_hurt_plays_below_his_rating():
    league = fresh()
    q, d = player_at(league, 1, "RB", 0), player_at(league, 1, "RB", 1)
    hurt(league, q, 1)                                          # questionable at week 2: the computer team plays him
    table = I.lineup(league, 1, 2, staff=False)
    assert table[q.place][0] == q.id and table[q.place][2] == max(D.RATING_MIN, q.rating - T.FR_INJ_HURT_PENALTY["questionable"])
    hurt(league, d, 2)
    I.decide(league, d.id, 2, True)                            # a decision is the player's team's only; the computer team rests a doubtful one
    assert all(entry[0] != d.id for entry in I.lineup(league, 1, 2, staff=False))


def test_the_quarterback_out_is_played_by_the_stand_in_and_a_returner_by_a_running_back():
    league = fresh()
    qb = player_at(league, 3, "QB")
    hurt(league, qb, 4)
    with pytest.raises(LeagueError):
        I.lineup(league, 3, 2, staff=False)                    # a group with nobody to play needs its stand-in (settle makes it)
    done = I.settle(league, 2, FakeRnd([0]), SURNAMES)          # rnd(1708) gives the first name, free: no redraw
    assert len(done.stand_ins) == 1 and done.stand_ins[0][:2] == [3, "QB"] and done.stand_ins[0][3] == T.FR_INJ_STAND_IN["QB"]
    table = I.lineup(league, 3, 2, staff=False)
    assert table[D.PLACES_OF["QB"][0]] == ((I.STAND_IN, "QB"), done.stand_ins[0][2], T.FR_INJ_STAND_IN["QB"])
    ret = player_at(league, 3, "RET", 0)
    hurt(league, ret, 4)
    table = I.lineup(league, 3, 2, staff=False)
    lowest_back = by_depth(league, 3, "RB")[-1]
    assert table[ret.place][0] == lowest_back.id                # the other returner is named with him: a running back covers
    assert table[player_at(league, 3, "RET", 1).place][0] == player_at(league, 3, "RET", 1).id


def test_a_whole_group_out_gets_its_stand_in():
    league = fresh()
    for safety in league.group_of(4, "S"):
        hurt(league, safety, 4)
    I.settle(league, 2, FakeRnd(), SURNAMES)
    table = I.lineup(league, 4, 2, staff=False)
    assert all(table[i][0] == (I.STAND_IN, "S") for i in D.PLACES_OF["S"])
    assert table[D.PLACES_OF["S"][0]][2] == T.FR_INJ_STAND_IN_OTHER


def test_a_stand_in_has_a_name_nobody_active_has():
    league = fresh()
    taken = SURNAMES.index(FN.surname_of(league.league_id, player_at(league, 1, "RB").name)) + 1     # D-131: his drawn surname
    row = I.make_stand_in(league, 9, "QB", FakeRnd([taken - 1]), SURNAMES)
    active = {p.name for p in league.players.values() if p.status == "active"}
    assert row[2] not in active and FN.surname_of(league.league_id, row[2]) not in FN.name_keys(league.league_id, active)


# ----- an injury, its range -----

def test_a_new_injury_of_a_player_already_hurt_keeps_the_later_return():
    league = fresh()
    p = player_at(league, 1, "LB")
    row = hurt(league, p, 5, week=2)
    assert row[3] == 8
    I.injure(league, p.id, "IJB", 2, 0, 3)                     # back 6: earlier, the first stays
    assert row[1] == "IJA" and row[3] == 8
    I.injure(league, p.id, "IJC", 6, 1, 4)                     # back 11: the new one
    assert row[1:4] == ["IJC", 4, 11] and len(league.injuries["hurt"]) == 1


def test_the_spoken_range_narrows_and_always_holds_the_truth():
    for games in range(1, 21):
        width = I.width_for(games)
        assert width <= T.FR_INJ_RANGE_MAX
        for offset in range(width + 1):
            row = [1, "IJA", 2, 3 + games, width, offset, 0]
            ranges = []
            for week in range(3, 3 + games):
                low, high = I.spoken_range(row, week)
                truth = I.left(row, week)
                assert 1 <= low <= truth <= high, (games, offset, week)
                ranges.append((low, high))
            spans = [high - low for low, high in ranges]
            assert all(a >= b for a, b in zip(spans, spans[1:])), (games, offset, spans)       # it narrows
            assert spans[0] <= width and spans[-1] == 0 or games == 1                          # to the exact games at the end


def test_out_for_the_season_only_when_he_misses_the_play_offs_too():
    league = fresh()
    p = player_at(league, 1, "RB")
    row = hurt(league, p, 4, week=13)                          # back in week 18: he plays in the play-offs
    assert I.status_of_row(row, 14) == "out" and "for the season" not in F._status_line(F_WORDS, p, row, 14, None)
    row[3] = 21                                                # back after the Super Bowl
    assert F._status_line(F_WORDS, p, row, 14, None) == X.text("NXI-17", player=p.name, position=F_WORDS.position("RB"))


def test_the_report_tells_the_new_injuries_by_name_then_the_older_ones_then_who_is_back():
    league = fresh()
    old, new, back = player_at(league, TEAM, "RB", 0), player_at(league, TEAM, "WR", 0), player_at(league, TEAM, "LB", 0)
    row_old = hurt(league, old, 5, week=1)                     # an older injury: out at week 3
    hurt(league, new, 4, week=2)                               # hurt in week 2's game: told with its kind's name
    lines = F.report_lines(league, 3, [back.id], F_WORDS, None, FakeRnd([0]))
    low, high = I.spoken_range(row_old, 3)
    assert lines[0].strip().startswith(new.name) and "sprained ankle" in lines[0]
    assert X.text("NXI-15", player=old.name, position=F_WORDS.position("RB"), lo=low, hi=high) in lines
    assert lines[-1] == X.text("NXI-20", list=back.name)
    assert F.report_lines(fresh(), 3, [], F_WORDS, None, FakeRnd()) == []          # nothing to tell: no report


def test_the_headline_is_another_teams_best_player_out_never_the_players_own():
    league = fresh()
    own = player_at(league, TEAM, "QB")
    own.rating = 99
    other_qb, other_rb = player_at(league, 2, "QB"), player_at(league, 3, "RB")
    for p, games in ((own, 5), (other_qb, 5), (other_rb, 5)):
        hurt(league, p, games, week=2)
    event = F.headline(league, 3)
    best = max((other_qb, other_rb), key=lambda p: (p.rating, -p.id))
    assert event.pool == "NWJ" and event.player is best and event.team == best.team and event.n == I.spoken_range(I.row_of(league, best.id), 3)[1]
    assert F.headline(league, 4) is None                       # only an injury of last week's game


def test_the_kinds_their_shares_and_the_positions_they_skip():
    kinds = T.FR_INJ_KINDS
    assert [k[0] for k in kinds] == list(D.INJURY_KIND_POOLS) and sum(k[3] for k in kinds) == 100
    assert all(1 <= k[1] <= k[2] for k in kinds)
    assert all(k[0] != "IJH" for k in I.kinds_for("K")) and any(k[0] == "IJH" for k in I.kinds_for("QB"))
    rnd = FakeRnd([0, 0, 0])
    assert I.draw_injury(rnd, "RB") == ("IJA", 1, 0) and rnd.sizes == [100, 3, 2]
    rnd = FakeRnd([99, 3, 3])                                  # the last share is IJM's (1 to 4 games), its last games, the widest offset
    assert I.draw_injury(rnd, "RB", worse=1) == ("IJM", 5, 3)


# ----- the week's draws -----

def test_the_week_draws_in_their_order_and_a_played_game_has_no_game_part():
    league = fresh()
    rnd = FakeRnd(default=9999)                                # no draw hits
    I.after_games(league, 3, rnd, SURNAMES, played=(TEAM, 7))
    practice, game = T.FR_INJ_PRACTICE[0], T.FR_INJ_GAME[0]
    assert rnd.sizes == [10000] * (D.TEAMS * (practice + game) - 2 * game)
    rnd = FakeRnd(default=9999)
    assert I.after_games(league, 16, rnd, SURNAMES).new == [] and rnd.sizes == []        # week 16: no draws (no preparation follows it)
    assert I.after_games(league, 0, rnd, SURNAMES).new == [] and rnd.sizes == []


def test_a_hit_hurts_the_player_who_plays_the_place():
    league = fresh()
    depth = by_depth(league, 1, "RB")
    hurt(league, depth[0], 6)                                  # out: his place is played by the second back
    script = [0]                                               # team 1's first practice draw hits
    script += [depth[0].place]                                 # the place: the hurt back's own place, which the second back plays
    script += [0, 0, 0]                                        # IJA, 1 game, offset 0
    rnd = FakeRnd(script, default=9999)
    done = I.after_games(league, 2, rnd, SURNAMES)
    assert done.new == [(depth[1].id, "IJA", 2)] and I.row_of(league, depth[1].id)[3] == 4


def test_a_team_never_has_more_than_its_limit_hurt():
    league = fresh()
    spread = {"RB": 3, "WR": 3, "DL": 3, "LB": 2, "CB": 1}      # twelve, no group left without a player who plays
    players = [p for position, count in spread.items() for p in league.group_of(1, position)[:count]]
    assert len(players) == T.FR_INJ_TEAM_MAX
    for p in players:
        hurt(league, p, 6)
    rnd = FakeRnd(default=0)                                   # every draw hits, the first place, the first kind
    I.after_games(league, 2, rnd, SURNAMES)
    assert I.hurt_count(league, 1, 3) == T.FR_INJ_TEAM_MAX
    for team in range(1, D.TEAMS + 1):
        assert I.hurt_count(league, team, 3) <= T.FR_INJ_TEAM_MAX
    assert not I.at_limit(league, 1, players[0].id, 2)          # a player hurt anyway adds nobody


def test_hurt_worse_after_a_game_played_hurt():
    league = fresh()
    q = player_at(league, 1, "RB", 0)
    hurt(league, q, 1, week=1)                                 # questionable at week 2: the computer team plays him
    script = [0]                                               # the worse draw of team 1's first hurt player: hit
    script += [0, 0, 0]                                        # its kind IJA, 1 game + 1, offset 0
    rnd = FakeRnd(script, default=9999)
    done = I.after_games(league, 2, rnd, SURNAMES)
    assert done.worse == [(q.id, "IJA", 2)] and I.row_of(league, q.id)[3] == 2 + 1 + 2
    assert rnd.sizes[:4] == [1000, 100, 3, 2]


def test_settle_lets_the_healed_go_and_says_who_is_back():
    league = fresh()
    p = player_at(league, 6, "CB")
    hurt(league, p, 2, week=1)                                 # back: week 4
    assert I.settle(league, 3, FakeRnd(), SURNAMES).back == []
    assert I.settle(league, 4, FakeRnd(), SURNAMES).back == [p.id] and I.healthy(league, p.id, 4)
    assert league.injuries["hurt"] == []


def test_end_of_season_clears_everything():
    league = fresh()
    hurt(league, player_at(league, 1, "QB"), 3)
    I.settle(league, 2, FakeRnd(), SURNAMES)
    I.end_of_season(league)
    assert league.injuries == I.empty()


def test_the_kinds_shares_are_whole_rolls_of_a_hundred():
    assert I.draw_kind(FakeRnd([19]), "RB")[0] == "IJA" and I.draw_kind(FakeRnd([20]), "RB")[0] == "IJB"       # IJA's share is 20: rolls 0 to 19
    assert I.draw_kind(FakeRnd([35]), "RB")[0] == "IJB" and I.draw_kind(FakeRnd([36]), "RB")[0] == "IJC"


def test_hurt_worse_is_not_drawn_on_a_team_at_its_limit():
    league = fresh()
    q = player_at(league, 1, "CB", 0)
    hurt(league, q, 1, week=1)                                 # questionable at week 2: the computer team plays him; fit for week 3
    spread = {"RB": 3, "WR": 3, "DL": 3, "LB": 2, "S": 1}
    for p in [p for position, count in spread.items() for p in league.group_of(1, position)[:count]]:
        hurt(league, p, 6, week=1)                             # twelve more, out
    rnd = FakeRnd([0])                                         # the worse draw of the questionable man hits, every other draw misses
    done = I.after_games(league, 2, rnd, SURNAMES)
    assert done.worse == [] and rnd.sizes[0] == 1000 and I.healthy(league, q.id, 3)


# ----- the computer's games -----

def test_a_hurt_team_moves_down_its_league_and_the_others_do_not():
    league = fresh()
    healthy = LeaguePlace(league.sums)
    assert LeaguePlace(league.sums, league.sums).d == healthy.d
    qb = player_at(league, 2, "QB")
    hurt(league, qb, 6)
    I.settle(league, 2, FakeRnd(), SURNAMES)
    effective = I.effective_sums(league, 2)
    assert effective[1] < league.sums[1] and [s for i, s in enumerate(effective) if i != 1] == [s for i, s in enumerate(league.sums) if i != 1]
    place = LeaguePlace(league.sums, effective)
    assert place.spread_sq == healthy.spread_sq and place.shift(2) <= healthy.shift(2)
    assert all(place.shift(t) >= healthy.shift(t) for t in range(1, 33) if t != 2)      # the week's mean fell: the others are a little higher in it
    everyone = LeaguePlace(league.sums, [s - 78 for s in league.sums])                   # every team one rating point down: nobody moves
    assert everyone.d == healthy.d


def test_the_computers_games_of_a_week_do_not_see_the_injuries_of_that_weeks_game():
    league = fresh()
    league.gtp = 5
    qb = player_at(league, 2, "QB")
    I.injure(league, qb.id, "IJA", 4, 0, 5)                    # hurt in the player's game of week 5, committed before the week's computer games
    I.settle(league, 6, FakeRnd(), SURNAMES)
    assert I.effective_sums(league, 5) == league.sums
    assert I.effective_sums(league, 6)[1] < league.sums[1]     # from the next week he counts
    rb = player_at(league, 2, "RB")
    I.injure(league, rb.id, "IJA", 6, 0, 3)                    # an older injury of the same team: it counts in week 5, the fresh one does not
    with_old = I.effective_sums(league, 5)[1]
    assert with_old < league.sums[1]
    league.injuries["hurt"] = [row for row in league.injuries["hurt"] if row[0] != qb.id]
    I.settle(league, 5, FakeRnd(), SURNAMES)
    assert I.effective_sums(league, 5)[1] == with_old


def test_the_injuries_move_a_team_at_most_the_bound():
    league = fresh()
    healthy = LeaguePlace(league.sums)
    effective = list(league.sums)
    effective[3] -= 78 * 30                                    # a team that lost 30 rating points of strength
    place = LeaguePlace(league.sums, effective)
    n = D.TEAMS
    num, den = T.FR_INJ_SD_MAX
    from math import isqrt
    limit = isqrt(num * num * healthy.spread_sq // (n * den * den))
    assert place.d[3] == healthy.d[3] - limit and 0 < limit < 78 * 30 * n


# ----- the trades -----

def test_a_hurt_player_is_not_traded():
    league = fresh()
    a, b = player_at(league, 1, "WR", 0), player_at(league, 2, "WR", 0)
    trade = TR.Trade(1, 2, a.id, b.id, [], [])
    league.gtp = 5
    before = TR.problems(league, trade, 5)
    hurt(league, a, 3, week=4)
    assert TR.problems(league, trade, 5) == "a player who is hurt" and before != "a player who is hurt"


# ----- the to-do item -----

def test_the_items_ask_about_the_players_who_matter_the_biggest_gap_first():
    league = fresh()
    qb = player_at(league, TEAM, "QB")
    hurt(league, qb, 1, week=1)                                # questionable; the stand-in plays 55: a big gap
    weak = by_depth(league, TEAM, "WR")[-1]
    weak.rating = T.FR_INJ_STAND_IN_OTHER + T.FR_INJ_ASK_GAP - 1      # a receiver just over replacement level: resting him costs too little to ask
    hurt(league, weak, 2, week=1)
    I.settle(league, 2, FakeRnd(), SURNAMES)
    asked = I.to_ask(league, 2)
    assert asked[0] == qb.id and weak.id not in asked
    assert I.ask_gap(league, TEAM, qb.id, 2) == qb.rating - T.FR_INJ_STAND_IN["QB"]
    assert I.to_ask(league, 17) == []


def test_the_list_asks_at_a_gap_of_exactly_the_mark():
    league = fresh()
    weak = by_depth(league, TEAM, "WR")[-1]
    weak.rating = T.FR_INJ_STAND_IN_OTHER + T.FR_INJ_ASK_GAP          # resting him costs exactly the mark: asked
    hurt(league, weak, 1, week=1)
    assert I.ask_gap(league, TEAM, weak.id, 2) == T.FR_INJ_ASK_GAP and I.to_ask(league, 2) == [weak.id]
    weak.rating -= 1
    assert I.to_ask(league, 2) == []


def test_the_list_asks_the_biggest_gaps_first_at_most_its_limit():
    league = fresh()
    backs = league.group_of(TEAM, "RB")
    for back, rating in zip(backs[:3], (60, 80, 70)):
        back.rating = rating
        hurt(league, back, 1, week=1)                          # questionable, the gaps 10, 30 and 20 against replacement level 50
    asked = I.to_ask(league, 2)
    assert asked == [backs[1].id, backs[2].id] and len(asked) == T.FR_INJ_ASK_MAX


def test_the_kick_off_writes_who_plays_hurt_by_the_staff_setting():
    league = fresh()
    q, d = player_at(league, TEAM, "RB", 0), player_at(league, TEAM, "RB", 1)
    hurt(league, q, 1, week=1)
    hurt(league, d, 2, week=1)
    I.lineup_decided(league, TEAM, 2, staff=False)
    assert I.row_of(league, q.id)[6] == 0 and I.row_of(league, d.id)[6] == 0        # the setting off: nothing is decided for him
    F.GameInjuries(league, TEAM, 9, 2, True, FakeRnd(), SURNAMES, F_WORDS)          # the kick-off of a game with the setting on
    assert I.row_of(league, q.id)[6] == 2 and I.row_of(league, d.id)[6] == 0        # the staff's rule: the questionable man plays


def test_the_item_answers_and_the_do_nothing_answer_rests_him():
    league = fresh()
    q, d = player_at(league, TEAM, "RB", 0), player_at(league, TEAM, "RB", 1)
    hurt(league, q, 1, week=1)
    hurt(league, d, 2, week=1)
    item_q, item_d = F.item(league, 2, q.id), F.item(league, 2, d.id)
    league.todo.extend([item_q, item_d])
    todo.check_items(league, _whole)
    assert F.answers_order(league, item_q) == (True, False) and F.answers_order(league, item_d) == (False, True)
    assert todo.apply_answer(league, item_q, 0) is True and I.row_of(league, q.id)[6] == 2      # the staff's: play the questionable one
    assert todo.close_unanswered(league) == 1 and I.row_of(league, d.id)[6] == 0              # left for later: he rests
    item_d2 = F.item(league, 2, d.id)
    league.todo.append(item_d2)
    assert todo.apply_answer(league, item_d2, 1) is True and I.row_of(league, d.id)[6] == 2    # the second answer of a doubtful one: play him


def _whole(value, low, high, what):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise LeagueError("%s is %r" % (what, value))


def test_an_answer_outside_the_two_rests_him():
    league = fresh()
    q = player_at(league, TEAM, "RB", 0)
    hurt(league, q, 1, week=1)
    item = F.item(league, 2, q.id)
    league.todo.append(item)
    assert todo.apply_answer(league, item, 2) is False and I.row_of(league, q.id)[6] == 0


def test_two_items_for_one_player_or_a_bad_item_are_damage():
    league = fresh()
    p = player_at(league, TEAM, "RB", 0)
    league.todo[:] = [F.item(league, 2, p.id), F.item(league, 2, p.id)]
    with pytest.raises(LeagueError):
        todo.check_items(league, _whole)
    for bad in ({"kind": "injury", "season": 1, "week": 2, "state": 0, "player": 0},
                {"kind": "injury", "season": 1, "week": 2, "state": D.ITEM_SET, "player": p.id},
                {"kind": "extra_work", "season": 1, "week": 2, "state": 0, "player": p.id},
                {"kind": "injury", "season": 1, "week": 2, "state": 0, "players": [p.id]}):
        league.todo[:] = [bad]
        with pytest.raises(LeagueError):
            todo.check_items(league, _whole)


# ----- league.sav format 6 -----

def test_format_6_round_trips_with_injuries_and_stand_ins():
    league = fresh()
    hurt(league, player_at(league, 1, "QB"), 3, week=1)
    hurt(league, player_at(league, 2, "RB"), 1, week=1, kind="IJE", offset=1)
    I.settle(league, 2, FakeRnd(), SURNAMES)
    league.injuries["report"] = {"season": 1, "week": 2, "lines": [" the line. "], "told": 0}
    text = league.to_json()
    assert json.loads(text)["format"] == 19 == D.FORMAT     # (12 since SZ.8: the injuries are format 6's; SR.5: 19, no places stored)
    again = LeagueRecord.from_json(text)
    assert again.injuries == league.injuries and again.to_json() == text


def test_a_format_5_file_loads_with_nobody_hurt():
    league = fresh()
    data = legacy_data(league)
    data["format"] = 5
    del data["injuries"]
    again = LeagueRecord.from_json(json.dumps(data))
    assert again.injuries == I.empty() and json.loads(again.to_json())["format"] == D.FORMAT


@pytest.mark.parametrize("damage", [
    lambda inj, league: inj.update(hurt="x"),
    lambda inj, league: inj.__setitem__("extra", 1),
    lambda inj, league: inj["hurt"].append([1, "IJA", 1, 3, 1, 0]),
    lambda inj, league: inj["hurt"].append([10 ** 8, "IJA", 1, 3, 1, 0, 0]),
    lambda inj, league: inj["hurt"].append([1, "XXX", 1, 3, 1, 0, 0]),
    lambda inj, league: inj["hurt"].append([1, "IJA", 18, 20, 1, 0, 0]),
    lambda inj, league: inj["hurt"].append([1, "IJA", 2, 2, 1, 0, 0]),
    lambda inj, league: inj["hurt"].append([1, "IJA", 2, 4, 1, 2, 0]),
    lambda inj, league: inj["hurt"].append([1, "IJA", 2, 4, 4, 0, 0]),
    lambda inj, league: inj["hurt"].append([1, "IJA", 2, 4, 1, 0, 2]),
    lambda inj, league: inj["hurt"].extend([[1, "IJA", 2, 4, 1, 0, 0], [1, "IJB", 2, 4, 1, 0, 0]]),
    lambda inj, league: inj["stand_ins"].append([1, "QB", "", 55]),
    lambda inj, league: inj["stand_ins"].append([1, "XX", "Smith", 55]),
    lambda inj, league: inj["stand_ins"].extend([[1, "QB", "Smith", 55], [1, "QB", "Jones", 55]]),
    lambda inj, league: inj["stand_ins"].append([33, "QB", "Smith", 55]),
    lambda inj, league: inj["stand_ins"].append([1, "QB", "Smith", 30]),
    lambda inj, league: inj.update(report={"season": 1, "week": 2, "lines": [], "told": 2}),
    lambda inj, league: inj.update(report={"season": 1, "week": 2, "lines": ["a\x01b"], "told": 0}),
    lambda inj, league: inj.update(report={"season": 1, "week": 2, "lines": []}),
])
def test_a_damaged_injury_record_is_refused(damage):
    league = fresh()
    damage(league.injuries, league)
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_injuries_outside_the_season_are_damage():
    league = fresh()
    hurt(league, player_at(league, 1, "RB"), 3)
    league.stage, league.stage_no = OFFSEASON, D.STAGE_REVIEW
    league.gtp = 0
    league.records = [8, 8] * 32
    with pytest.raises(LeagueError):
        league.check()
    league.injuries = I.empty()
    league.check()


def test_the_shipped_values():
    """The values of SX.8k (D-071): the target band from the NFL's injury reports, the draws calibrated to it (work/sim_league_sx8k.py, the 10,000-season run)."""
    assert T.FR_INJ_TARGET == (31.3, 38.0)
    assert T.FR_INJ_PRACTICE == (4, 1303) and T.FR_INJ_GAME == (16, 1310) and T.FR_INJ_PLAY == 441 and T.FR_INJ_TACKLER == 50
    assert T.FR_INJ_SD_MAX == (1, 2)
    assert T.FR_INJ_LAST_WEEK == 15 and T.FR_INJ_TEAM_MAX == 12
    weights = T.FR_INJ_GAME_WEIGHT
    assert weights["K"] == weights["P"] == 0 and sum(weights[D.POSITION_OF_PLACE[i]] for i in range(D.PLACE_COUNT)) == 4762
