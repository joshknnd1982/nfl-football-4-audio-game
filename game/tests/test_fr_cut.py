"""The Franchise's roster cut and fill (nfl4 only, rule 0.13): the keep value, the staff's releases, the floor of the small groups, the
places, the fill, and the invariants over many offseasons (NFL_FRANCHISE_DESIGN 7.6, 16 SX.8d, I3 to I5). Rules only: the questions are
test_fr_cut_flow.py.
"""
import random

import pytest

from drrig import SURNAMES, draft_league, full_league
from nfl4.extras import roster_model as RM
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging, resign
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import real_roster as RR
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


# ----- the staff's releases (SR.5, D-164, design 21.7 (1): the cut to 53 by the family minimums, then the keep value) -----

def full(seed=3):
    """A league of the real rosters with every family at its target and 53 men a team (drrig.full_league), at the cut."""
    league = full_league(seed, TEAM)
    league.stage, league.stage_no = "offseason", D.STAGE_CUT
    return league


def rated(league, team, rating=70, age=28):
    for p in RR.members(league, team):
        p.rating, p.age, p.potential = rating, age, "average"


def rookie_of(league, position, rating, **kwargs):
    man = rookie(league, RM.GROUP[position], rating, **kwargs)
    man.position = position
    return man


def test_a_team_keeps_53_and_the_worst_to_keep_are_released_worst_first():
    league = full()
    rated(league, TEAM)
    high = rookie_of(league, "HB", 61, age=22, potential="high")                     # 61 + 4 = 65
    low = rookie_of(league, "HB", 55, age=22, potential="low")
    waiting = {TEAM: [high, low]}
    released = DR.plan_cut(league, TEAM, waiting)
    assert [p.id for p in released] == [low.id, high.id]                            # 55 kept least, then 65: the 53 rated 70 stay
    assert DR.surplus(league, TEAM, waiting)["RB"] == 2
    assert DR.plan_cut(league, 6, {}) == []                                          # a team of 53 releases nobody


def test_the_family_minimums_are_kept_before_the_keep_value_and_a_family_never_passes_its_most():
    league = full()
    rated(league, TEAM, rating=55)                                                    # (over the floor: a one-man family under it would leave a spot for the fill)
    stars = [rookie_of(league, "WR", 90) for _ in range(6)] + [rookie_of(league, "K", 95), rookie_of(league, "QB", 95), rookie_of(league, "QB", 94)]
    waiting = {TEAM: stars}
    released = {p.id for p in DR.plan_cut(league, TEAM, waiting)}
    kept = [p for p in DR.team_candidates(league, TEAM, waiting) if p.id not in released]
    have = RR.counts_by_group(kept)
    assert len(kept) == 53 and all(have.get(g, 0) >= n for g, n in T.FR_FAMILY_MIN.items())
    assert have["K"] == 1 and have["QB"] == 3                                        # the best kicker only, at most three quarterbacks
    assert not any(s.id in released for s in stars)


def test_a_team_under_53_releases_nobody():
    league = full()
    for man in [p for p in RR.members(league, TEAM) if p.pos == "WR"][:3]:
        RR.leave(league, man, "released")
    assert DR.plan_cut(league, TEAM, {}) == []


def test_a_weak_player_of_a_one_man_family_is_released_without_a_surplus_and_a_big_family_keeps_its_weak_ones():
    league = full()
    rated(league, TEAM)
    kicker = next(p for p in RR.members(league, TEAM) if p.pos == "K")
    punter = next(p for p in RR.members(league, TEAM) if p.pos == "P")
    quarterback = next(p for p in RR.members(league, TEAM) if p.pos == "QB")
    kicker.rating, punter.rating, quarterback.rating = 49, 50, 45                    # the floor: the kicker under it goes, the punter at it stays
    released = DR.plan_cut(league, TEAM, {})
    assert [p.id for p in released] == [kicker.id] and T.FR_CUT_FLOOR == 50
    assert DR.FLOOR_GROUPS == ("K", "P", "LS")                                      # SR.5: the quarterbacks are a family of two or three now


def test_the_floor_looks_at_the_players_who_stay_not_at_the_surplus():
    league = full()
    rated(league, TEAM)
    kicker = next(p for p in RR.members(league, TEAM) if p.pos == "K")
    kicker.rating = 45
    better = rookie_of(league, "K", 58)
    released = DR.plan_cut(league, TEAM, {TEAM: [better]})
    assert [p.id for p in released] == [kicker.id]                                   # 58 stays; the 45 goes by the family's most and the floor
    assert DR.floor_releases([kicker], "K") == [kicker] and DR.floor_releases([kicker], "RB") == []


# ----- applying the cut -----

def test_applying_the_cut_releases_the_plan_ends_the_draft_and_the_rookies_who_stay_join_their_charts():
    league = full()
    rated(league, TEAM, rating=65)
    high = rookie_of(league, "HB", 90, age=22, potential="high")
    low = rookie_of(league, "HB", 55, age=22, potential="low")
    waiting = {TEAM: [high, low]}
    plans = {t: DR.plan_cut(league, t, waiting) for t in range(1, 33)}
    count = DR.apply_cut(league, plans, waiting)
    assert count == sum(len(v) for v in plans.values()) and low in plans[TEAM]
    for p in plans[TEAM]:
        assert (p.status, p.left, p.place, p.points) == ("released", league.season, -1, 0)
    assert high.status == "active" and high.team == TEAM and league.chart[TEAM - 1]["HB"][0] == high.id
    assert high.place == D.PLACES_OF["RB"][0] and league.draft is None and league.pick_no == 0
    assert all(league.players[pid].place == i for i, pid in enumerate(league.rosters[TEAM - 1]) if pid)
    assert RR.roster_count(league, TEAM) == 53


def test_the_players_own_choice_replaces_the_staffs_for_his_team():
    league = full()
    rated(league, TEAM)
    best = rookie_of(league, "HB", 90)
    waiting = {TEAM: [best]}
    plans = {t: DR.plan_cut(league, t, waiting) for t in range(1, 33)}
    old_best = league.players[league.chart[TEAM - 1]["HB"][0]]
    plans[TEAM] = [old_best]                                                          # the player releases his best old back, not the worst
    DR.apply_cut(league, plans, waiting)
    assert old_best.status == "released" and league.chart[TEAM - 1]["HB"][0] == best.id


# ----- the fill: the cut's last resort (design 21.3, real_roster.fill_needs) -----

def test_the_fill_makes_an_undrafted_rookie_for_every_man_a_family_lacks_by_the_rules_of_its_size():
    league = full()
    for group, keep in (("RB", 1), ("K", 0), ("LS", 0)):
        for man in [p for p in RR.members(league, TEAM) if p.pos == group][keep:]:
            RR.leave(league, man, "retired")
    before = {p.name for p in league.players.values() if p.status == "active"}
    first = league.next_id
    filled = aging.fill_places(league, rnd_of(), SURNAMES)
    assert filled == 2 + 1 + 1
    for group, count, low, high in (("RB", 2, 45, 55), ("K", 1, 50, 60), ("LS", 1, 50, 60)):
        new = [p for p in league.players.values() if p.id >= first and p.pos == group]
        assert len(new) == count and all(low <= p.rating <= high and p.age == 22 and p.seasons == 0 and p.drafted is None for p in new)
        assert all(p.name not in before and p.team == TEAM and p.id in league.chart[TEAM - 1][p.position] for p in new)
    assert not RR.short_groups(league, TEAM)


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


def test_twenty_offseasons_keep_every_place_filled_every_family_whole_and_no_one_man_family_under_the_floor():
    rnd = rnd_of(11)
    league = full_league(11, 9)
    league.stage, league.stage_no = "offseason", 1
    for season in range(1, 21):
        league.history = [{"season": league.season, "wins": [8] * 32, "finish": [0] * 32}]
        league.sums = [league.strength_sum(t) for t in range(1, 33)]
        offseason_by_rules(league, rnd, None)
        league.stage_no, league.gtp, league.records, league.history = D.STAGE_NEW_SEASON, 0, [8, 8] * 32, []
        league = LeagueRecord.from_json(league.to_json())                              # the whole-file check, every season
        for team in range(1, 33):
            roster = league.rosters[team - 1]
            assert all(pid for i, pid in enumerate(roster) if i not in D.BACK_PLACES), (season, team)       # I3 (a back place may be empty)
            assert RR.roster_count(league, team) <= D.ROSTER_MAX and not RR.short_groups(league, team), (season, team)
            for group in DR.FLOOR_GROUPS:                                                                     # I5
                assert all(p.rating >= T.FR_CUT_FLOOR or p.drafted for p in RR.members(league, team) if p.pos == group), (season, team, group)
            for pos in ("RB", "WR", "DL", "LB", "CB", "S"):
                ratings = [league.players[roster[i]].rating for i in D.PLACES_OF[pos] if roster[i]]
                assert sum(ratings) / len(ratings) >= 50, (season, team, pos, ratings)
        active = [p for p in league.players.values() if p.status == "active"]
        assert len({p.id for p in active}) == len(active)
        assert all(40 <= p.rating <= 99 and 21 <= p.age <= 40 for p in active)             # I4
        assert 60 <= sum(p.rating for p in active) / len(active) <= 76 and 24 <= sum(p.age for p in active) / len(active) <= 29
        league.stage_no = 1


def test_the_released_and_the_retired_are_dropped_at_the_end_except_the_players_team_and_the_stars():
    league = full_league(12, 9)
    league.stage, league.stage_no = "offseason", 1
    league.history = [{"season": league.season, "wins": [8] * 32, "finish": [0] * 32}]
    offseason_by_rules(league, rnd_of(12), None)
    leaving = [p for p in league.players.values() if p.status not in ("active", "practice", "list")]
    assert all(p.team == 9 or p.peak >= D.STAR_PEAK for p in leaving)
    assert {"retired", "released"} <= {p.status for p in leaving if p.team == 9} <= {"retired", "released", "free"}          # the player's team keeps every kind for its history
