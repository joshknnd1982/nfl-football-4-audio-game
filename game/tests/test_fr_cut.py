"""The Franchise's roster cut and fill (nfl4 only, rule 0.13): the keep value, the staff's releases, the floor of the small groups, the
places, the fill, and the invariants over many offseasons (NFL_FRANCHISE_DESIGN 7.6, 16 SX.8d, I3 to I5). Rules only: the questions are
test_fr_cut_flow.py.
"""
import random

import pytest

from drrig import SURNAMES, draft_league
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging, resign
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise.league import LeagueRecord, Player
from nfl4.game.rnd import GameRandom

TEAM = 5


def rnd_of(seed=1):
    return GameRandom(random.Random(seed))


def rookie(league, pos, rating, age=22, potential="average", team=TEAM, name=None):
    """A drafted rookie waiting for the cut (not in the draft record: the rules read the waiting list they are given)."""
    player = Player(league.next_id, name or "Rookie%d" % league.next_id, pos, rating, potential, age, 0, rating, [league.season, 1, 1], 0,
                    "active", 0, team, -1)
    league.next_id += 1
    league.players[player.id] = player
    return player


def set_group(league, team, pos, ratings, age=28, potential="average"):
    """The ratings of the group's players in place order (as many as there are places; None leaves the place empty)."""
    for index, rating in zip(D.PLACES_OF[pos], ratings):
        player = league.player_at(team, index)
        if rating is None:
            player.status, player.place, player.left = "retired", -1, league.season
            league.rosters[team - 1][index] = 0
        else:
            player.rating, player.age, player.potential = rating, age, potential


def ratings_of(league, team, pos):
    return [league.player_at(team, i).rating if league.player_at(team, i) else None for i in D.PLACES_OF[pos]]


# ----- the keep value (design 7.6) -----

def test_the_keep_value_adds_the_youth_bonus_for_24_or_younger_by_potential():
    league = draft_league()
    at = lambda age, potential: DR.keep_value(rookie(league, "RB", 60, age=age, potential=potential))
    assert [at(24, "high"), at(24, "average"), at(24, "low")] == [64, 62, 60]
    assert [at(25, "high"), at(25, "average"), at(25, "low")] == [60, 60, 60]
    assert at(21, "high") == 64


def test_equal_keep_values_keep_the_younger_then_the_lower_id():
    league = draft_league()
    old = rookie(league, "RB", 60, age=30)
    young = rookie(league, "RB", 60, age=26)
    same_age_low_id = rookie(league, "RB", 60, age=26)
    twin = rookie(league, "RB", 60, age=26)
    order = DR.keep_order([old, twin, same_age_low_id, young])
    assert [p.id for p in order] == [young.id, same_age_low_id.id, twin.id, old.id]
    assert [p.id for p in DR.release_order([old, twin, same_age_low_id, young])] == [old.id, twin.id, same_age_low_id.id, young.id]


# ----- the staff's releases -----

def test_a_group_keeps_its_count_and_the_worst_to_keep_are_released_worst_first():
    league = draft_league()
    set_group(league, TEAM, "RB", [70, 68, 66, 64, 62, 60])
    high = rookie(league, "RB", 61, age=22, potential="high")                    # 61 + 4 = 65 beats the 64
    low = rookie(league, "RB", 55, age=22, potential="low")
    waiting = {TEAM: [high, low]}
    released = DR.plan_cut(league, TEAM, waiting)
    assert [p.rating for p in released if p.pos == "RB"] == [55, 60]
    assert DR.surplus(league, TEAM, waiting) == {"RB": 2}
    assert DR.plan_cut(league, 6, {}) == []


def test_the_releases_come_group_by_group_in_the_roster_menus_order():
    league = draft_league()
    waiting = {TEAM: [rookie(league, "P", 40), rookie(league, "QB", 40), rookie(league, "DL", 40), rookie(league, "RB", 40)]}
    released = DR.plan_cut(league, TEAM, waiting)
    assert [p.pos for p in released] == ["QB", "RB", "DL", "P"]


def test_a_group_with_fewer_players_than_places_releases_nobody():
    league = draft_league()
    set_group(league, TEAM, "WR", [70, 70, 70, None, None, None])
    assert DR.plan_cut(league, TEAM, {}) == []


def test_a_weak_player_of_a_small_group_is_released_without_a_surplus_and_a_big_group_keeps_its_weak_ones():
    league = draft_league()
    set_group(league, TEAM, "RET", [57, 42])
    set_group(league, TEAM, "QB", [49])
    set_group(league, TEAM, "K", [50])                                             # exactly the floor: kept
    set_group(league, TEAM, "S", [70, 49])
    set_group(league, TEAM, "DL", [45, 70, 70, 70, 70, 70])                           # six places: a big group, nobody is released for a rating
    released = DR.plan_cut(league, TEAM, {})
    assert sorted((p.pos, p.rating) for p in released) == [("QB", 49), ("RET", 42), ("S", 49)]
    assert T.FR_CUT_FLOOR == 50 and D.CUT_FLOOR_GROUP_MAX == 2


def test_the_floor_looks_at_the_players_who_stay_not_at_the_surplus():
    league = draft_league()
    set_group(league, TEAM, "RET", [45, 44])
    waiting = {TEAM: [rookie(league, "RET", 58)]}
    released = DR.plan_cut(league, TEAM, waiting)
    assert sorted(p.rating for p in released) == [44, 45]                             # 58 stays; the two under 50 go (one by the count, one by the floor)
    assert [p.rating for p in DR.floor_releases([league.player_at(TEAM, i) for i in D.PLACES_OF["RET"]], "RET")] == [44, 45]
    assert DR.floor_releases([league.player_at(TEAM, i) for i in D.PLACES_OF["RB"]], "RB") == []


# ----- applying the cut -----

def test_applying_the_cut_releases_places_the_rest_by_rating_and_keeps_empty_places_last():
    league = draft_league()
    set_group(league, TEAM, "RB", [60, 70, 62, 68, 64, 66])
    high = rookie(league, "RB", 61, age=22, potential="high")
    low = rookie(league, "RB", 55, age=22, potential="low")
    set_group(league, TEAM, "WR", [70, 69, None, 67, None, 65])
    waiting = {TEAM: [high, low]}
    plans = {t: DR.plan_cut(league, t, waiting) for t in range(1, 33)}
    gone = {p.id for p in plans[TEAM]}
    count = DR.apply_cut(league, plans, waiting)
    assert count == len(gone) == 2
    assert ratings_of(league, TEAM, "RB") == [70, 68, 66, 64, 62, 61]                  # the rookie is placed by rating; the 60 is out
    assert ratings_of(league, TEAM, "WR") == [70, 69, 67, 65, None, None]
    for p in plans[TEAM]:
        assert (p.status, p.left, p.place, p.points) == ("released", league.season, -1, 0)
    assert low.status == "released" and high.status == "active" and high.place == D.PLACES_OF["RB"][-1] and high.team == TEAM
    assert all(league.players[pid].place == i for i, pid in enumerate(league.rosters[TEAM - 1]) if pid)


def test_a_cut_that_leaves_a_group_over_its_places_is_refused():
    league = draft_league()
    waiting = {TEAM: [rookie(league, "QB", 80)]}
    with pytest.raises(ValueError):
        DR.apply_cut(league, {}, waiting)


def test_the_players_own_choice_replaces_the_staffs_for_his_team():
    league = draft_league()
    set_group(league, TEAM, "RB", [70, 68, 66, 64, 62, 60])
    best = rookie(league, "RB", 90)
    waiting = {TEAM: [best]}
    plans = {t: DR.plan_cut(league, t, waiting) for t in range(1, 33)}
    plans[TEAM] = [league.player_at(TEAM, D.PLACES_OF["RB"][0])]                      # the player releases his best old back, not the worst
    DR.apply_cut(league, plans, waiting)
    assert ratings_of(league, TEAM, "RB") == [90, 68, 66, 64, 62, 60]


# ----- the fill (design 7.6, 12 item 6) -----

def test_the_fill_gives_every_empty_place_an_undrafted_rookie_by_the_rules_of_its_group_size():
    league = draft_league()
    set_group(league, TEAM, "RB", [70, 68, None, None, None, None])
    set_group(league, TEAM, "QB", [None])
    set_group(league, TEAM, "RET", [None, 60])
    before = {p.name for p in league.players.values() if p.status == "active"}
    filled = aging.fill_places(league, rnd_of(), SURNAMES)
    assert filled == 4 + 1 + 1
    for pos, count, low, high in (("RB", 4, 45, 55), ("QB", 1, 50, 60), ("RET", 1, 50, 60)):
        new = [p for p in league.players.values() if p.id >= 1089 and p.pos == pos]
        assert len(new) == count and all(low <= p.rating <= high and p.age == 22 and p.seasons == 0 and p.drafted is None for p in new)
        assert all(p.name not in before for p in new)
    assert all(pid for roster in league.rosters for pid in roster)
    assert ratings_of(league, TEAM, "RB")[:2] == [70, 68]


# ----- the invariants over many offseasons (I3, I4, I5 and the names) -----

def offseason_by_rules(league, rnd, wins):
    """One whole offseason with the real rules: retirements, development, draft by the computer's rule, the staff's cut, the fill."""
    retiring = aging.plan_retirements(league, rnd)
    aging.apply_aging(league, retiring)
    aging.apply_development(aging.plan_development(league, rnd))
    resign.run_teams(league)
    draft = DR.Draft.create(league, rnd, SURNAMES)
    while not draft.done:
        _, _, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    waiting = DR.waiting_by_team(league)
    DR.apply_cut(league, {t: DR.plan_cut(league, t, waiting) for t in range(1, D.TEAMS + 1)}, waiting)
    aging.fill_places(league, rnd, SURNAMES)
    league.draft, league.pick_no = None, 0
    aging.drop_the_unkept(league)
    league.season += 1


def test_twenty_offseasons_keep_every_place_filled_every_group_whole_and_no_group_under_the_floor():
    rnd = rnd_of(11)
    league = draft_league(seed=11, team=9)
    league.stage, league.stage_no = "offseason", 1
    for season in range(1, 21):
        league.history = [{"season": league.season, "wins": [8] * 32, "finish": [0] * 32}]
        league.sums = [league.strength_sum(t) for t in range(1, 33)]
        offseason_by_rules(league, rnd, None)
        league.stage_no, league.gtp, league.records, league.history = D.STAGE_NEW_SEASON, 0, [8, 8] * 32, []
        league = LeagueRecord.from_json(league.to_json())                              # the whole-file check, every season
        assert all(pid for roster in league.rosters for pid in roster)                 # I3: every place is filled
        for team in range(1, 33):
            roster = league.rosters[team - 1]
            for pos in D.POSITIONS:                                                      # (D-149: OL and LS have no places)
                places = D.PLACES_OF[pos]
                ratings = [league.players[roster[i]].rating for i in places]
                assert sum(ratings) / len(ratings) >= 50, (season, team, pos, ratings)   # I5
                assert all(league.players[roster[i]].pos == pos for i in places)
        active = [p for p in league.players.values() if p.status == "active"]
        assert len(active) == 1088 and len({p.name for p in active}) == 1088             # nobody twice
        assert all(40 <= p.rating <= 99 and 21 <= p.age <= 40 for p in active)             # I4
        assert 66 <= sum(p.rating for p in active) / 1088 <= 74 and 24 <= sum(p.age for p in active) / 1088 <= 29
        league.stage_no = 1


def test_the_released_and_the_retired_are_dropped_at_the_end_except_the_players_team_and_the_stars():
    league = draft_league(seed=12, team=9)
    offseason_by_rules(league, rnd_of(12), None)
    leaving = [p for p in league.players.values() if p.status != "active"]
    assert all(p.team == 9 or p.peak >= D.STAR_PEAK for p in leaving)
    assert {"retired", "released"} <= {p.status for p in leaving if p.team == 9} <= {"retired", "released", "free"}          # the player's team keeps every kind for its history
