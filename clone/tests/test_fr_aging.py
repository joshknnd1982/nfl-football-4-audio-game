"""Aging, retirement, progression and regression of the Franchise's players (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 6 and 8.2, SX.8c (F2). The rules are tested as plain functions of numbers (the formulas with the design's start
values through a fixture, B-X52, so a later calibration moves no hand-worked number; the calibrated values have a test of their own),
then on a league with a STRICT script of draws (a draw the test did not plan fails the test), then as the spoken stages 2 and 3 on
the program rig of tests/frrig.py, and last as the properties over many offseasons.
"""
import copy
import random

import pytest

from frrig import enter_until, franchise_rig, run_until, spoken
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging, resign
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import offseason
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import OFFSEASON, LeagueRecord, new_league, team_ref
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.names import load_surnames
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, below_value

SURNAMES = load_surnames()

# The design's start values (NFL_FRANCHISE_DESIGN 6.2, 6.3): the formulas are tested with these.
DESIGN_AGING = dict(FR_RETIRE_PER_YEAR=110, FR_RETIRE_PER_POINT=6, FR_GROWTH=(5, 3, 1), FR_IN_WINDOW=(1, 0, 0),
                    FR_DECLINE=(2, 3, 4, 5, 6, 6), FR_PROGRESS_NOISE=(5, -2),
                    FR_PEAK={"RB": (24, 27), "WR": (25, 29), "QB": (26, 32), "DL": (25, 29), "LB": (25, 29), "CB": (25, 28),
                             "S": (25, 29), "RET": (24, 27), "K": (26, 34), "P": (26, 34)})


@pytest.fixture
def design(monkeypatch):
    for name, value in DESIGN_AGING.items():
        monkeypatch.setattr(T, name, value)


def made(seed=1, team=5):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def scripted(*values):
    """A GameRandom over a strict script of below() draws, (n, k) pairs; a draw not planned fails the test."""
    source = ScriptedRandom([below_value(n, k) for n, k in values], strict=True)
    return GameRandom(source), source


def with_all_aged(league, age):
    for player in league.players.values():
        player.age = age
    return league


def retire(league, team, place, peak=None):
    """The player of a place retired (as the offseason leaves him)."""
    player = league.player_at(team, place)
    player.status, player.place, player.left = "retired", -1, league.season
    if peak is not None:
        player.peak = peak
    league.rosters[team - 1][place] = 0
    return player


# ----- the rules as functions of numbers -----

def test_nobody_under_thirty_can_retire(design):
    assert all(aging.retire_chance(age, rating) == 0 for age in range(21, 30) for rating in range(40, 100))


def test_the_chance_rises_with_age_at_every_rating(design):
    for rating in range(40, 100):
        chances = [aging.retire_chance(age, rating) for age in range(30, 41)]
        assert chances == sorted(chances), rating
        assert chances[0] < chances[-1] == 1000


def test_the_chance_falls_with_rating_at_every_age(design):
    for age in range(30, 40):
        chances = [aging.retire_chance(age, rating) for rating in range(40, 100)]
        assert chances == sorted(chances, reverse=True), age
        assert chances[0] > chances[-1] or chances[0] == 1000 == chances[-1] or chances[-1] == 0


def test_the_chance_is_the_designs_formula_clamped_to_zero_and_a_thousand(design):
    assert aging.retire_chance(30, 70) == 110
    assert aging.retire_chance(33, 70) == 440
    assert aging.retire_chance(33, 80) == 440 - 60
    assert aging.retire_chance(33, 60) == 440 + 60
    assert aging.retire_chance(35, 40) == 660 + 180
    assert aging.retire_chance(30, 89) == 0                  # 110 - 114: clamped at zero
    assert aging.retire_chance(39, 70) == 1000               # 1100: clamped at a thousand


def test_at_the_oldest_age_the_chance_is_a_thousand_whatever_the_rating(design):
    assert all(aging.retire_chance(D.AGE_MAX, rating) == 1000 for rating in range(40, 100))


@pytest.mark.parametrize("position", D.POSITIONS)
def test_the_curve_has_the_shape_of_the_window_and_the_potential(design, position):
    first, last = DESIGN_AGING["FR_PEAK"][position]
    assert [aging.base_change(position, first - 1, p) for p in D.POTENTIALS] == [5, 3, 1]
    for age in range(first, last + 1):
        assert [aging.base_change(position, age, p) for p in D.POTENTIALS] == [1, 0, 0]
    assert [aging.base_change(position, last + k, "average") for k in range(1, 9)] == [-2, -3, -4, -5, -6, -6, -6, -6]
    for k in range(1, 9):                                      # after the window the potential does not matter
        assert len({aging.base_change(position, last + k, p) for p in D.POTENTIALS}) == 1
    assert {aging.base_change(position, age, "high") for age in range(21, first)} <= {5}      # growth is flat before the window


def test_the_windows_differ_by_position_as_research_says(design):
    # a receiver declines later than a running back; a quarterback and a kicker hold into their thirties
    assert aging.base_change("RB", 28, "average") < 0 <= aging.base_change("WR", 28, "average")
    assert aging.base_change("QB", 31, "average") == 0 and aging.base_change("QB", 33, "average") == -2
    assert aging.base_change("K", 34, "average") == 0 and aging.base_change("P", 35, "average") == -2


def test_a_rating_is_kept_in_forty_to_ninety_nine():
    assert aging.clamp_rating(120) == 99 and aging.clamp_rating(-5) == 40 and aging.clamp_rating(77) == 77


# ----- stage 2 on a strict script -----

def test_a_player_who_will_be_under_thirty_neither_retires_nor_draws(design):
    league = with_all_aged(made(), 28)                         # 29 once aged
    rnd, source = scripted()
    assert aging.plan_retirements(league, rnd) == [] and source.drawn == 0


def test_the_draws_follow_league_order_and_the_oldest_retire_without_a_draw(design):
    league = with_all_aged(made(), 25)
    a, b, c, d = (league.player_at(1, 0), league.player_at(1, 1), league.player_at(2, 5), league.player_at(3, 2))
    a.age, a.rating = 29, 70            # 30 once aged: chance 110, draws first (team 1, place 0)
    b.age, b.rating = 39, 99            # 40 once aged: retires with no draw
    c.age, c.rating = 38, 70            # 39: chance 1000
    d.age, d.rating = 28, 70            # 29: no draw
    rnd, source = scripted((1000, 109), (1000, 999))
    assert aging.plan_retirements(league, rnd) == [a, b, c] and source.left == 0
    rnd, source = scripted((1000, 110), (1000, 999))
    assert aging.plan_retirements(league, rnd) == [b, c] and source.left == 0      # 110 is not below 110


def test_nothing_changes_until_the_plan_is_applied(design):
    league = with_all_aged(made(), 25)
    player = league.player_at(1, 0)
    player.age = 39
    before = league.to_json()
    rnd, _ = scripted()
    assert aging.plan_retirements(league, rnd) == [player]
    assert league.to_json() == before


def test_applying_makes_everybody_a_year_older_and_the_retired_leave_their_places(design):
    league = with_all_aged(made(), 25)
    player = league.player_at(2, 5)
    player.age, player.seasons, player.peak = 39, 17, 91
    other = league.player_at(2, 6)
    other.seasons = 3
    league.season = 7
    aging.apply_aging(league, [player])
    assert player.status == "retired" and player.left == 7 and player.place == -1 and player.team == 2
    assert player.age == 40 and player.seasons == 18 and league.rosters[1][5] == 0
    assert other.age == 26 and other.seasons == 4 and other.status == "active"
    assert all(p.age == 26 for p in league.players.values() if p.id != player.id)
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, 3, 0, [8, 8] * 32
    LeagueRecord.from_json(league.to_json())                   # an empty place is not damage at stage 3


def test_nobody_goes_over_forty_even_when_a_record_has_a_forty_year_old(design):
    league = with_all_aged(made(), 25)
    league.player_at(1, 0).age = 40
    rnd, _ = scripted()
    aging.apply_aging(league, aging.plan_retirements(league, rnd))
    assert league.player_at(1, 0) is None and max(p.age for p in league.players.values()) == 40


# ----- stage 3 on a strict script -----

def test_a_new_rating_is_the_base_plus_the_spread_plus_the_points_one_draw_a_player(design):
    league = with_all_aged(made(), 22)
    first, second = league.player_at(1, 0), league.player_at(1, 1)            # two running backs: age 22 is before the window
    first.rating, first.potential, first.points = 60, "high", 2
    second.rating, second.potential, second.points = 60, "low", 0
    values = [(5, 2)] * 1088                                                    # a spread of 0
    values[0], values[1] = (5, 4), (5, 0)                                       # +2 and -2
    rnd, source = scripted(*values)
    plan = aging.plan_development(league, rnd)
    assert source.left == 0 and len(plan) == 1088
    assert (plan[0].player, plan[0].new) == (first, 60 + 5 + 2 + 2)             # high +5, spread +2, two points
    assert (plan[1].player, plan[1].new) == (second, 60 + 1 - 2)                # low +1, spread -2
    assert first.rating == 60 and first.points == 2                              # nothing is changed by the plan
    aging.apply_development(plan)
    assert first.rating == 69 and first.points == 0 and second.rating == 59


def test_the_rating_is_kept_in_range_and_the_peak_follows_it(design):
    league = with_all_aged(made(), 22)
    high, low = league.player_at(1, 0), league.player_at(1, 1)
    high.rating, high.peak, high.potential, high.points = 98, 98, "high", 3
    low.rating, low.peak, low.age = 41, 90, 37                                  # a running back far past his window
    rnd, _ = scripted(*([(5, 4), (5, 0)] + [(5, 2)] * 1086))
    aging.apply_development(aging.plan_development(league, rnd))
    assert high.rating == 99 and high.peak == 99                                # 98 + 5 + 2 + 3 clamped
    assert low.rating == 40 and low.peak == 90                                  # 41 - 6 - 2 clamped, the peak stays


def test_a_retired_player_gets_no_draw_and_no_change(design):
    league = with_all_aged(made(), 25)
    gone = league.player_at(1, 0)
    aging.apply_aging(league, [gone])
    rnd, source = scripted(*([(5, 2)] * 1087))
    plan = aging.plan_development(league, rnd)
    assert gone not in [c.player for c in plan] and source.left == 0


def test_the_summary_counts_the_players_team_and_names_the_first_of_equal_changes(design):
    league = with_all_aged(made(), 22)
    rnd, _ = scripted(*([(5, 2)] * 1088))
    plan = aging.plan_development(league, rnd)                                  # every young player improves by his base
    summary = aging.summarize(plan, league.team)
    assert summary.improved + summary.declined + summary.same == 34
    best = max(c.delta for c in plan if c.player.team == league.team)
    assert summary.best.delta == best
    assert summary.best is next(c for c in plan if c.player.team == league.team and c.delta == best)
    old = with_all_aged(made(), 36)                                             # everybody declines
    rnd, _ = scripted(*([(5, 2)] * 1088))
    plan = aging.plan_development(old, rnd)
    summary = aging.summarize(plan, old.team)
    assert summary.best is None and summary.improved == 0
    assert summary.worst.delta == min(c.delta for c in plan if c.player.team == old.team)


# ----- the places, the stand-in fill and what history keeps -----

def test_the_best_player_of_a_group_takes_its_first_place_and_an_empty_place_goes_last():
    league = made()
    team = 3
    ids = [league.rosters[team - 1][i] for i in D.PLACES_OF["WR"]]
    for rating, pid in zip((50, 90, 70, 90, 60, 80), ids):
        league.players[pid].rating = rating
    league.rosters[team - 1][D.PLACES_OF["WR"][2]] = 0                        # the 70 is gone
    aging.place_by_rating(league, team)
    ratings = [league.player_at(team, i).rating if league.player_at(team, i) else None for i in D.PLACES_OF["WR"]]
    assert ratings == [90, 90, 80, 60, 50, None]
    assert league.player_at(team, D.PLACES_OF["WR"][0]).id == ids[1]            # equal ratings: the lower ID first
    assert all(league.player_at(team, i).place == i for i in D.PLACES_OF["WR"][:5])


def test_the_stand_in_fill_gives_every_empty_place_an_undrafted_rookie_by_the_designs_rules(design):
    league = with_all_aged(made(), 25)
    retire(league, 5, D.PLACES_OF["QB"][0])                                     # a group of one place
    retire(league, 11, D.PLACES_OF["RB"][2])                                    # a group of six
    active = {p.name for p in league.players.values() if p.status == "active"}
    free = [i for i, name in enumerate(SURNAMES, start=1) if name not in active]
    # a name is rnd(1708) = below(1708) + 1; the rating below(11); the potential below(100); team 5 comes before team 11
    rnd, source = scripted((len(SURNAMES), free[0] - 1), (11, 3), (100, 10), (len(SURNAMES), free[1] - 1), (11, 4), (100, 80))
    assert aging.fill_places(league, rnd, SURNAMES) == 2 and source.left == 0
    qb = league.player_at(5, D.PLACES_OF["QB"][0])
    rb = [p for p in league.group_of(11, "RB") if p.age == 22]
    assert qb.name == SURNAMES[free[0] - 1] and qb.rating == 50 + 3 and qb.potential == "high" and qb.age == 22 and qb.seasons == 0
    assert len(rb) == 1 and rb[0].name == SURNAMES[free[1] - 1] and rb[0].rating == 45 + 4 and rb[0].potential == "low"
    assert qb.peak == qb.rating and qb.drafted is None and qb.id >= 1089 and qb.team == 5
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, 6, 0, [8, 8] * 32
    LeagueRecord.from_json(league.to_json())                                    # whole again: stage 6 is valid


def test_history_keeps_the_players_team_and_the_stars_and_drops_the_rest():
    league = made(team=5)
    kept = {key: retire(league, team, place, peak).id for key, (team, place, peak) in
            {"other": (1, 0, 70), "star": (1, 1, 91), "own": (5, 0, 70), "own_star": (5, 1, 90)}.items()}
    assert aging.drop_the_unkept(league) == 1
    assert kept["other"] not in league.players
    assert all(kept[key] in league.players for key in ("star", "own", "own_star"))


# ----- the calibrated values have a test of their own -----

CALIBRATED = dict(FR_RETIRE_PER_YEAR=110, FR_RETIRE_PER_POINT=6, FR_GROWTH=(4, 2, 1), FR_IN_WINDOW=(1, 0, 0),
                  FR_DECLINE=(2, 3, 4, 5, 6, 6), FR_PROGRESS_NOISE=(5, -2),
                  FR_PEAK={"RB": (24, 28), "WR": (25, 29), "QB": (24, 30), "DL": (25, 29), "LB": (25, 29), "CB": (25, 28),
                           "S": (25, 29), "RET": (24, 28), "K": (24, 34), "P": (24, 34)})        # the quarterback's end, K and P: D-061 (SX.8f)


def test_the_tuning_file_holds_the_values_the_calibration_settled_on():
    for name, value in CALIBRATED.items():
        assert getattr(T, name) == value, name


def test_the_shipped_windows_keep_the_researchs_shape_where_it_matters():
    # the calibration moved some windows (D-058, D-061); a quarterback holds to thirty, a kicker into his mid thirties, a receiver still
    # declines later than a running back, and nothing grows after its window
    assert aging.base_change("QB", 30, "average") == 0 and aging.base_change("QB", 30, "high") == 1
    assert aging.base_change("QB", 31, "average") == -2 and aging.base_change("QB", 33, "high") == -4
    assert aging.base_change("K", 34, "average") == 0 and aging.base_change("P", 35, "average") == -2
    assert aging.base_change("RB", 29, "average") < 0 <= aging.base_change("WR", 29, "average")
    for position in D.POSITIONS:
        last = T.FR_PEAK[position][1]
        assert all(aging.base_change(position, age, p) <= 0 for age in range(last + 1, 41) for p in D.POTENTIALS)


def test_the_tables_are_whole_numbers_and_cover_every_position():
    assert all(isinstance(x, int) and x > 0 for x in T.FR_DECLINE) and len(T.FR_DECLINE) >= 1
    assert all(len(w) == 2 and w[0] <= w[1] for w in T.FR_PEAK.values()) and set(T.FR_PEAK) == set(D.POSITIONS)
    assert len(T.FR_GROWTH) == 3 == len(T.FR_IN_WINDOW)


# ----- the properties over many offseasons -----

def test_twenty_offseasons_keep_every_place_filled_every_value_in_range_and_nobody_young_retires():
    rnd = GameRandom(random.Random(7))
    league = new_league(rnd, SURNAMES, "Kim", 9, "20260101-000000")
    for _ in range(20):
        retiring = aging.plan_retirements(league, rnd)
        assert all(aging.aged(p) >= 30 for p in retiring)
        aging.apply_aging(league, retiring)
        aging.apply_development(aging.plan_development(league, rnd))
        resign.run_teams(league)
        aging.fill_places(league, rnd, SURNAMES)
        aging.drop_the_unkept(league)
        league.season += 1
        league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, 6, 0, [8, 8] * 32
        league = LeagueRecord.from_json(league.to_json())                       # the whole-file check, every season
        assert all(pid for roster in league.rosters for pid in roster)
        assert all(40 <= p.rating <= 99 and 21 <= p.age <= 40 for p in league.players.values() if p.status == "active")
        names = [p.name for p in league.players.values() if p.status == "active"]
        assert len(names) == len(set(names)) == 1088


# ----- the spoken stages on the program rig -----

def stage_rig(tmp_path, mutate, short=False, until=None, keys=(), waits=None, source=None, files=None, **kwargs):
    """A franchise record at the start of stage 2 (the season just reviewed), `mutate(league)` applied, resumed on the rig until
    the next season's week 1 (or `until(rig)`). `rig.kept[stage]` is the file as each stage wrote it, `rig.start` the record at the
    start; `keys` are the first keys the waits get; `waits` (a list) gets (lines, the league's players as they are) at every stage
    wait; `source` replaces the program's random source (a ScriptedRandom)."""
    league = made(seed=3, team=5)
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, 2, 0, [8, 8] * 32
    mutate(league)
    if files is None:
        files = MemoryFiles()
        files.data["league.sav"] = league.to_json().encode("utf-8")

    def next_week_1():
        fstore = rig.fstore
        return fstore is not None and fstore.league is not None and fstore.league.stage == "season" and fstore.league.season == 2

    rig = franchise_rig(tmp_path, list(keys), files=files, kind="franchise", **kwargs,
                        policy=enter_until(lambda: (until or (lambda r: next_week_1()))(rig)))
    if short:
        rig.game.options.settings.game.nx_fr_offseason = "short"
    if source is not None:
        rig.game.rnd.source = source
    kept = {}
    real = FranchiseStore.save
    real_wait = offseason.wait_for_enter

    def save(self):
        ok = real(self)
        if self.league.stage == "offseason" and self.league.stage_no not in kept:
            kept[self.league.stage_no] = self.files.data["league.sav"]
        return ok

    def spy(game, lines):
        if waits is not None:
            waits.append((list(lines), {pid: (p.age, p.rating, p.status) for pid, p in rig.fstore.league.players.items()}))
        real_wait(game, lines)
    FranchiseStore.save = save
    offseason.wait_for_enter = spy
    try:
        run_until(rig)
    finally:
        FranchiseStore.save = real
        offseason.wait_for_enter = real_wait
    rig.kept = {number: LeagueRecord.from_json(raw.decode("utf-8")) for number, raw in kept.items()}
    rig.start = league
    return rig


class Veterans:
    """Three players of the player's team and a star of another team who will be 40: they retire whatever the draws say. Every
    other player of the player's team is young, so nothing else of it retires."""

    def __init__(self):
        self.own = []                                          # (name, position word, rating, seasons played once aged)
        self.star = None

    def __call__(self, league):
        for player in league.players.values():
            if player.team == league.team:
                player.age = 22
        words = {0: "running back", 7: "receiver", 33: "quarterback"}
        for place in (0, 7, 33):
            player = league.player_at(league.team, place)
            player.age, player.seasons = 39, 16 + place
            self.own.append((player.name, words[place], player.rating, player.seasons + 1))
        self.star = league.player_at(2, 12)
        self.star.age, self.star.peak, self.star.rating, self.star.seasons = 39, 93, 88, 17


def test_stage_two_names_the_players_of_your_team_who_retire_and_the_league_count_and_the_stars(tmp_path):
    veterans = Veterans()
    rig = stage_rig(tmp_path, veterans)
    text = spoken(rig)
    after = text[text.index(" stage 2 of 8. retirements. "):]
    assert after[1] == X.text("NXE-30")
    for name, position, rating, seasons in veterans.own:
        assert X.text("NXE-31", player=name, position=position, a=40, r=rating, n=seasons) in after
    saved = rig.kept[3]
    retired = [p for p in saved.players.values() if p.status == "retired"]
    own = [p for p in retired if p.team == 5]
    assert len(own) == 3 and len([t for t in after if ", retires. seasons played: " in t and " of the " not in t]) == 3
    count = X.text("NXE-33", n=len(retired))
    star = X.text("NXE-35", player=veterans.star.name, team=rig.game.league.team(*team_ref(2)), position="defensive lineman", n=18)
    assert star in after and after.index(count) < after.index(star) < after.index(X.text("NXE-03"))
    assert all(p.left == 1 and p.status == "retired" and p.age >= 30 for p in retired)


def test_nobody_from_your_team_retires_is_said_when_nobody_does(tmp_path):
    def mutate(league):
        for p in league.players.values():
            if p.team == league.team:
                p.age = 22
    text = spoken(stage_rig(tmp_path, mutate))
    assert X.text("NXE-32") in text and X.text("NXE-30") not in text


def test_at_most_three_stars_of_other_teams_are_named_the_highest_peak_first_and_your_own_are_not_named_twice(tmp_path):
    def mutate(league):
        for p in league.players.values():
            if p.team == 5:
                p.age = 22
        for i, team in enumerate((1, 2, 3, 4, 6)):
            star = league.player_at(team, 12)
            star.age, star.peak, star.rating = 39, 86 + i, 80
        own = league.player_at(5, 12)
        own.age, own.peak = 39, 99                                             # the player's own star: in "from your team"
    rig = stage_rig(tmp_path, mutate)
    text = spoken(rig)
    named = [t for t in text if " of the " in t and ", retires. seasons played: " in t]
    stars = sorted((p for p in rig.kept[3].players.values() if p.status == "retired" and p.team != 5 and p.peak >= 85),
                   key=lambda p: (-p.peak, p.id))
    assert len(stars) >= 5 and len(named) == 3
    assert [t.split(" of the ")[0].strip() for t in named] == [p.name for p in stars[:3]]
    stage_two = text[text.index(" stage 2 of 8. retirements. "):]
    stage_two = stage_two[:stage_two.index(X.text("NXE-03"))]          # the later stages may name a rookie with the retired star's surname
    assert sum(1 for t in stage_two if rig.start.player_at(5, 12).name + "," in t) == 1


def test_stars_of_equal_peak_are_named_in_league_order_not_by_their_ids(tmp_path):
    def mutate(league):
        for p in league.players.values():
            if p.team == 5:
                p.age = 22
        for team in (9, 3, 7, 1):                                              # four stars with the same peak
            star = league.player_at(team, 12)
            star.age, star.peak, star.rating = 39, 90, 80
    rig = stage_rig(tmp_path, mutate)
    named = [t.split(" of the ")[0].strip() for t in spoken(rig) if " of the " in t and ", retires. seasons played: " in t]
    expected = [rig.start.player_at(team, 12).name for team in (1, 3, 7)]          # league order: team 1, 3, 7 (and 9 is the fourth)
    assert named == expected


def test_the_short_offseason_says_one_sentence_for_each_of_the_two_stages(tmp_path):
    waits = []
    rig = stage_rig(tmp_path, Veterans(), short=True, waits=waits)
    text = spoken(rig)
    retired = [p for p in rig.kept[3].players.values() if p.status == "retired"]
    own = [p for p in retired if p.team == 5]
    assert X.text("NXE-71", n=len(retired), m=len(own)) in text
    before, after = rig.kept[3], rig.kept[7]
    mine = [p for p in before.players.values() if p.status == "active" and p.team == 5]
    deltas = [after.players[p.id].rating - p.rating for p in mine]
    assert X.text("NXE-72", n=sum(1 for d in deltas if d > 0), m=sum(1 for d in deltas if d < 0)) in text
    assert not any("retirements" in t or "player development" in t or "retires. seasons" in t for t in text)
    assert X.text("NXE-03") not in text and not [w for w in waits if any("retirements" in line for line in w[0])]


def test_stage_three_counts_the_players_team_and_names_its_best_and_its_biggest_drop(tmp_path):
    rig = stage_rig(tmp_path, lambda league: None)
    text = spoken(rig)
    before, after = rig.kept[3], rig.kept[7]
    own = [p for p in before.players.values() if p.status == "active" and p.team == 5]
    deltas = {p.id: after.players[p.id].rating - p.rating for p in own}
    improved = sum(1 for d in deltas.values() if d > 0)
    declined = sum(1 for d in deltas.values() if d < 0)
    assert X.text("NXE-40", n=improved, m=declined, k=len(own) - improved - declined) in text
    best = max(deltas.values())
    best_lines = [t for t in text if t.startswith(" most improved: ")]
    assert len(best_lines) == (1 if best > 0 else 0)
    if best > 0:
        assert any(" most improved: %s, " % after.players[pid].name in best_lines[0] and " up %d to " % best in best_lines[0]
                   for pid, d in deltas.items() if d == best)
    assert len([t for t in text if t.startswith(" the biggest drop: ")]) == (1 if min(deltas.values()) < 0 else 0)
    assert X.text("NXE-43") in text


def test_the_draws_of_stage_three_come_in_leagues_order_and_the_points_count_exactly_once(tmp_path, design):
    """A strict script of the whole of stages 2 and 3: nothing draws in stage 2 (everybody is young or retires at 40), stage 3 draws
    below(5) = 2 (a spread of 0) for every active player and nothing else (the empty place waits for the roster cut; the draft that
    follows draws from the source's real generator once the script is used up)."""
    def mutate(league):
        with_all_aged(league, 21)                                              # 22 at stage 3: before every window
        for place in range(34):
            league.player_at(5, place).points = 3
        league.player_at(5, 0).age = 39                                        # the running back retires at 40, with no draw
    values = [below_value(5, 2)] * 1087
    source = ScriptedRandom(values, strict=False)
    rig = stage_rig(tmp_path, mutate, source=source)
    before, after = rig.kept[3], rig.kept[7]
    assert source.drawn >= len(values)
    survivors = [p for p in before.players.values() if p.status == "active"]
    assert len(survivors) == 1087
    for p in survivors:
        points = 3 if p.team == 5 else 0
        expected = aging.clamp_rating(p.rating + aging.base_change(p.pos, p.age, p.potential) + points)
        assert after.players[p.id].rating == expected and after.players[p.id].points == 0, p.id
    assert sum(1 for pid in after.rosters[4] if pid == 0) == 1 and after.rosters[4][0] == 0        # the retired back place waits for the cut
    assert after.stage_no == 7 and after.draft is None                                           # and the draft class is not made yet


def test_the_roster_and_the_ratings_at_a_stages_wait_are_what_the_stage_just_said(tmp_path):
    waits = []
    rig = stage_rig(tmp_path, Veterans(), waits=waits)
    stage_two = next(w for w in waits if any("retirements" in line for line in w[0]))
    stage_three = next(w for w in waits if any("player development" in line for line in w[0]))
    assert {pid: (p.age, p.rating, p.status) for pid, p in rig.kept[3].players.items()} == stage_two[1]
    assert {pid: (p.age, p.rating, p.status) for pid, p in rig.kept[7].players.items()} == stage_three[1]
    assert not any("retires. seasons" in line for line in stage_three[0])


def test_the_roster_of_f9_counts_the_players_it_has_while_places_are_empty(tmp_path, monkeypatch):
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append((title, [item.label() for item in items]))
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    from frrig import DOWN, ENTER, ESC, F9
    stage_rig(tmp_path, Veterans(), keys=[F9, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, DOWN, ENTER, ESC, ESC, ESC])
    roster = [labels for title, labels in seen if title == "your roster"][0]
    assert roster[:3] == [" quarterback: 0 ", " running backs: 5 ", " receivers: 5 "] and roster[3] == " defensive linemen: 6 "


def test_the_development_points_are_not_counted_in_a_retired_players_file(tmp_path):
    def mutate(league):
        Veterans()(league)
        for place in (0, 7, 33):
            league.player_at(5, place).points = 3
    rig = stage_rig(tmp_path, mutate)
    assert all(p.points == 0 for p in rig.kept[3].players.values() if p.status == "retired")


def test_the_file_after_stage_two_has_empty_places_and_the_file_after_stage_three_none(tmp_path):
    rig = stage_rig(tmp_path, Veterans())
    assert any(pid == 0 for roster in rig.kept[3].rosters for pid in roster)         # stage 3's file: written when stage 2 ended
    assert any(pid == 0 for roster in rig.kept[7].rosters for pid in roster)         # stage 7's: written when stage 3 ended
    assert rig.kept[6].stage_no == 6 and all(pid for roster in rig.kept[6].rosters for pid in roster)     # stage 6's: after the cut and the fill
    final = rig.fstore.league
    assert final.stage == "season" and final.season == 2 and all(pid for roster in final.rosters for pid in roster)
    assert len(final.sums) == 32 and final.sums == [final.strength_sum(t) for t in range(1, 33)]
    assert all(p.points == 0 for p in final.players.values())


def test_a_window_closed_at_the_wait_of_stage_two_resumes_at_stage_three_with_the_year_done_once(tmp_path):
    first = stage_rig(tmp_path / "one", lambda league: with_all_aged(league, 25), until=lambda r: X.text("NXE-32") in spoken(r))
    saved = LeagueRecord.from_json(first.files.data["league.sav"].decode("utf-8"))
    assert saved.stage == "offseason" and saved.stage_no == 3                          # stage 2 was changed and saved before its wait
    assert all(p.age == 26 for p in saved.players.values())
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise",
                           policy=enter_until(lambda: second.fstore is not None and second.fstore.league is not None
                                              and second.fstore.league.stage == "season" and second.fstore.league.season == 2))
    run_until(second)
    text = spoken(second)
    assert " stage 2 of 8. retirements. " not in text and any(" stage 3 of 8. player development. " in t for t in text)
    assert all(p.age == 26 for p in second.fstore.league.players.values() if p.status == "active" and p.drafted is None and p.id <= 1088)      # once


def test_a_window_closed_at_the_wait_of_stage_three_resumes_at_the_expiring_contracts_with_the_development_done_once(tmp_path):
    first = stage_rig(tmp_path / "one", Veterans(), until=lambda r: X.text("NXE-43") in spoken(r))
    saved = LeagueRecord.from_json(first.files.data["league.sav"].decode("utf-8"))
    assert saved.stage == "offseason" and saved.stage_no == 7 and saved.draft is None and saved.has_empty_place()
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise",
                           policy=enter_until(lambda: second.fstore is not None and second.fstore.league is not None
                                              and second.fstore.league.stage == "season" and second.fstore.league.season == 2))
    run_until(second)
    final = second.fstore.league
    assert all(final.players[pid].rating == p.rating and final.players[pid].age == p.age for pid, p in saved.players.items()
               if pid in final.players and p.status == "active")                       # no second development, no second year


def test_play_classic_seasons_asked_at_a_stages_wait_leaves_the_stage_done_once(tmp_path):
    from frrig import DOWN, ENTER, ESC, F9, quit_policy
    from programrig import preset_season
    league = made(seed=3, team=5)
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, 2, 0, [8, 8] * 32
    with_all_aged(league, 25)
    files = MemoryFiles()
    files.data["league.sav"] = league.to_json().encode("utf-8")
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 9 + [ENTER, ENTER, ESC, ENTER]    # F9, Franchise, classic (the 10th item since SX.8j), confirm
    rig = franchise_rig(tmp_path / "one", keys, files=files, kind="franchise", preset=preset_season(gtp=3), policy=quit_policy)
    run_until(rig)
    saved = LeagueRecord.from_json(files.data["league.sav"].decode("utf-8"))
    assert rig.game.program.mode.kind == "classic" and saved.stage_no == 3 and all(p.age == 26 for p in saved.players.values())
    again = franchise_rig(tmp_path / "two", [], files=files, kind="franchise",
                          policy=enter_until(lambda: again.fstore is not None and again.fstore.league is not None
                                             and again.fstore.league.stage == "season" and again.fstore.league.season == 2))
    run_until(again)
    assert all(p.age == 26 for p in again.fstore.league.players.values() if p.status == "active" and p.drafted is None and p.id <= 1088)


def test_stage_three_leaves_the_empty_places_to_the_roster_cut_which_fills_them(tmp_path):
    """SX.8c filled the places at the end of stage 3 with a stand-in until the draft existed (B-X54); with the draft stage in the list
    the places stay empty through stage 3 and the draft, and stage 5 fills them."""
    rig = stage_rig(tmp_path, Veterans())
    empty = lambda league: sum(1 for roster in league.rosters for pid in roster if pid == 0)
    retired = sum(1 for player in rig.kept[3].players.values() if player.status == "retired")
    assert empty(rig.kept[7]) == retired >= 4                                    # stage 3's file: the retired players' places
    assert empty(rig.kept[4]) >= retired and empty(rig.kept[5]) == empty(rig.kept[4])      # stage 7 lets some go (SX.8h); the draft changes no place
    assert empty(rig.kept[6]) == 0


def test_the_offseason_news_lines_are_sx8es_and_nothing_is_said_for_them_yet(tmp_path):
    text = spoken(stage_rig(tmp_path, Veterans()))
    assert not any("has worked hard" in t or "says goodbye" in t or "who retires" in t for t in text)
