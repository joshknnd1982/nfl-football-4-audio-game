"""Who carries the ball and how much (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8o, research B2 and B7, INJ-3, D-076): the weighted ball carrier
(H17, equal weights are the original's rnd(6)), the returners' rating (H8's return_shortest), the season's games and carries, and the workload rule in a
game the engine plays and in the week's draws of a game it does not play (one rule, the same expected injuries). Every number is the tuning file's; the
cases are worked by hand.
"""
import random

import pytest
from drrig import SURNAMES
from frratings import rated_roster, state_with
from test_fr_injury_flow import TEAM, OPP, WORDS, Counting, Rigged, exposed, league_at, play

from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import injury_flow as F
from nfl4.extras.franchise import people as P
from nfl4.extras.franchise import ratings as R
from nfl4.extras.franchise import workload as W
from nfl4.extras.franchise.league import LeagueError, LeagueRecord
from nfl4.extras.playbooks import PlaybookModifiers
from nfl4.extras.state import check_game_injuries
from nfl4.game import outcome as O
from nfl4.game.playtables import NEUTRAL, RETURN_SHORTEST
from nfl4.game.rules import CLASSIC


class Script:
    """A strict scripted source: every draw must be the size the script expects (B-X62)."""

    def __init__(self, *steps):
        self.steps = list(steps)
        self.trace = []

    def _take(self, kind, n):
        want_kind, want_n, value = self.steps.pop(0)
        assert (kind, n) == (want_kind, want_n), (kind, n, want_kind, want_n)
        self.trace.append(n)
        return value

    def below(self, n):
        return self._take("below", n)

    def __call__(self, n):
        return self._take("rnd", n)


# ----- the weights and the draw -----

def test_a_carry_weight_is_its_base_and_a_bounded_step_of_the_rating():
    base, per, cap = T.FR_CARRY_WEIGHT
    assert W.carry_weight(70) == base and W.carry_weight(70 + per - 1) == base and W.carry_weight(70 - per + 1) == base
    assert W.carry_weight(70 + per) == base + 1 and W.carry_weight(70 - per) == base - 1
    assert W.carry_weight(99) == base + cap and W.carry_weight(40) == base - cap
    assert all(W.carry_weight(r) >= 1 for r in range(40, 100))


def test_equal_weights_are_the_originals_draw_itself():
    rnd = Script(("rnd", 6, 4))
    assert W.draw(rnd, [5, 5, 5, 5, 5, 5]) == 4 and rnd.trace == [6]


@pytest.mark.parametrize("roll,carrier", [(0, 1), (3, 1), (4, 2), (7, 2), (8, 3), (13, 3), (14, 4), (25, 6)])
def test_unequal_weights_draw_once_below_their_total(roll, carrier):
    rnd = Script(("below", 26, roll))
    assert W.draw(rnd, [4, 4, 6, 4, 4, 4]) == carrier and rnd.trace == [26]


def test_who_carries_by_the_kind_of_play():
    assert [W.kind_of(play) for play in range(0, 11)] == [None, "run", "run", "pass", "pass", "pass", None, None, None, None, None]


def test_the_franchise_object_gives_the_backs_on_a_run_and_the_receivers_on_a_pass_and_nothing_else():
    own, opponent = rated_roster("", 70, rb2=90, wr5=50), rated_roster("O", 70)
    m = R.FranchiseModifiers()
    s = state_with(own, opponent, offense_play=1)
    m.bind(s)
    base = T.FR_CARRY_WEIGHT[0]
    assert m.carrier_weights(s) == [base, W.carry_weight(90), base, base, base, base]
    s.offense_play = 4
    assert m.carrier_weights(s) == [base, base, base, base, W.carry_weight(50), base]
    for play in (0, 6, 7, 8, 9, 10):
        s.offense_play = play
        assert m.carrier_weights(s) is None
    s.wisoff, s.defense, s.offense_play = 2, 1, 2                     # the other side's backs, all 70
    assert m.carrier_weights(s) == [base] * 6


def test_without_ratings_the_nfl_rules_draw_by_depth_and_classic_draws_rnd6(tmp_path):
    """Outside the Franchise the N. F. L. rules weigh the six places by depth (T.DEPTH_CARRY_WEIGHT, tester 2026-10-23); Classic keeps rnd(6)."""
    from nflrig import RecordingRules
    from pagrig import named_roster
    from nfl4.extras import tuning as TU
    rules = RecordingRules()
    s = state_with(named_roster(""), named_roster("O"), offense_play=1)
    rules.modifiers.bind(s)
    for value, place in zip(range(1, 7), (1, 1, 2, 2, 3, 4)):
        rnd = Script(("rnd", 6, value))                                       # the same one rnd(6) as ever, read through the depth chart
        assert rules.draw_carrier(s, rnd) == place and rnd.trace == [6]
    assert TU.DEPTH_CARRY_SLOTS == (1, 1, 2, 2, 3, 4)
    rnd = Script(("rnd", 6, 5))
    assert CLASSIC.draw_carrier(s, rnd) == 5 and rnd.trace == [6]


def test_a_franchise_game_draws_its_carrier_by_the_weights(tmp_path):
    from nflrig import RecordingRules
    rules = RecordingRules()
    s = state_with(rated_roster("", 70, rb3=90), rated_roster("O"), offense_play=2)
    rules.modifiers.bind(s)
    weights = W.weights([70, 70, 90, 70, 70, 70])
    assert weights[2] > weights[0]
    rnd = Script(("below", sum(weights), weights[0] + weights[1]))
    assert rules.draw_carrier(s, rnd) == 3 and rnd.trace == [sum(weights)]


# ----- the returners' rating -----

def test_the_shortest_return_is_the_originals_in_classic_without_ratings_and_at_70():
    assert NEUTRAL.return_shortest(1, 2) == RETURN_SHORTEST == 12 and PlaybookModifiers().return_shortest(2, 1) == RETURN_SHORTEST
    m = R.FranchiseModifiers()
    from pagrig import named_roster
    m.bind(state_with(named_roster(""), named_roster("O")))
    assert m.return_shortest(1, 1) == RETURN_SHORTEST
    m.bind(state_with(rated_roster("", 70), rated_roster("O", 70)))
    assert m.return_shortest(1, 1) == m.return_shortest(2, 2) == RETURN_SHORTEST


def test_the_returners_rating_moves_the_shortest_return_by_bounded_steps():
    per, cap = T.FR_RETURN_STEP
    m = R.FranchiseModifiers()
    m.bind(state_with(rated_roster("", 70, ret1=70 + per, ret2=99), rated_roster("O", 70, ret1=70 - 2 * per, ret2=40)))
    assert m.return_shortest(1, 1) == RETURN_SHORTEST + 1 and m.return_shortest(1, 2) == RETURN_SHORTEST + cap
    assert m.return_shortest(2, 1) == RETURN_SHORTEST - 2 and m.return_shortest(2, 2) == RETURN_SHORTEST - cap


# ----- a game the engine does not play: the expected carries and the places of the game part -----

def table_of(ratings_rb, ratings_wr=(70,) * 6, ids=None):
    table = [(1000 + i, "N%d" % i, 70) for i in range(D.PLACE_COUNT)]
    for k, index in enumerate(D.PLACES_OF["RB"]):
        table[index] = (ids[k] if ids else 1000 + index, "B", ratings_rb[k])
    for k, index in enumerate(D.PLACES_OF["WR"]):
        table[index] = (1000 + index, "R", ratings_wr[k])
    return table


def test_equal_weights_share_the_runs_evenly_and_the_game_part_keeps_its_table():
    table = table_of((70,) * 6)
    carries = W.expected_carries(table)
    assert set(carries.values()) == {(2 * T.FR_WORKLOAD_RUNS + 6) // 12} and len(carries) == 6
    assert W.place_weights(table) == [T.FR_INJ_GAME_WEIGHT[D.POSITION_OF_PLACE[i]] for i in range(D.PLACE_COUNT)]


def test_the_runs_follow_the_carry_weights_and_a_man_who_plays_two_places_gets_both():
    table = table_of((90, 70, 70, 70, 70, 50), ids=[1, 2, 3, 4, 5, 2])
    carries = W.expected_carries(table)
    weights = [W.carry_weight(r) for r in (90, 70, 70, 70, 70, 50)]
    total = sum(weights)
    share = lambda w: (2 * T.FR_WORKLOAD_RUNS * w + total) // (2 * total)       # noqa: E731
    assert carries[1] == share(weights[0]) and carries[2] == share(weights[1]) + share(weights[5]) and carries[5] == share(weights[4])
    places = W.place_weights(table)
    rb = [places[i] for i in D.PLACES_OF["RB"]]
    assert rb[0] > rb[1] > rb[5] and abs(sum(rb) - 6 * T.FR_INJ_GAME_WEIGHT["RB"]) <= 6


def test_a_stand_in_carries_but_is_not_counted():
    table = table_of((70,) * 6)
    index = D.PLACES_OF["RB"][2]
    table[index] = ((I.STAND_IN, "RB"), "Stand", 50)
    carries = W.expected_carries(table)
    assert len(carries) == 5


# ----- the season's counts -----

def test_the_games_count_who_played_his_own_place_and_a_hurt_man_does_not():
    league = league_at(3)
    hurt = league.player_at(TEAM, D.PLACES_OF["RB"][0])
    I.injure(league, hurt.id, "IJA", 3, 0, 1)
    W.count_games(league, 2, staff=False)                      # the week-2 game: he was hurt in week 1 (the next man up plays his place)
    W.count_games(league, 3, staff=False)
    assert W.games_of(league, hurt.id) == 0
    other = league.player_at(TEAM, D.PLACES_OF["QB"][0])
    assert W.games_of(league, other.id) == 2
    assert W.games_of(league, league.player_at(OPP, 0).id) == 2
    W.count_games(league, 0)
    W.count_games(league, 17)
    assert W.games_of(league, other.id) == 2                  # only the regular season counts


def test_the_counts_are_the_seasons_and_stage_6_ends_them():
    league = league_at(3)
    pid = league.player_at(TEAM, 0).id
    W.add_carries(league, pid, 25)
    W.add_carries(league, pid, 0)
    assert W.carries_of(league, pid) == 25 and league.usage["season"] == league.season
    league.season += 1
    assert W.carries_of(league, pid) == 0 and W.games_of(league, pid) == 0     # a count of another season is not this season's
    W.new_season(league)
    assert league.usage == W.empty(league.season)


# ----- the workload rule -----

def back_of(league, team=TEAM, k=0):
    return league.player_at(team, D.PLACES_OF["RB"][k])


def test_the_extra_percent_starts_after_the_free_carries_rises_by_steps_and_stops_at_its_most():
    league = league_at(5)
    back = back_of(league)
    assert W.extra_percent(league, back.id) == 0
    W.add_carries(league, back.id, T.FR_WORKLOAD_FREE + T.FR_WORKLOAD_PER - 1)
    assert W.extra_percent(league, back.id) == 0
    W.add_carries(league, back.id, 1)
    assert W.extra_percent(league, back.id) == T.FR_WORKLOAD_PCT
    W.add_carries(league, back.id, T.FR_WORKLOAD_PER)
    assert W.extra_percent(league, back.id) == 2 * T.FR_WORKLOAD_PCT
    W.add_carries(league, back.id, 100 * T.FR_WORKLOAD_PER)
    assert W.extra_percent(league, back.id) == T.FR_WORKLOAD_MAX
    receiver = league.player_at(TEAM, D.PLACES_OF["WR"][0])
    W.add_carries(league, receiver.id, 5000)
    assert W.extra_percent(league, receiver.id) == 0                     # the rule is a running back's


def test_a_games_chance_is_its_carries_times_one_carrys_chance():
    for extra in (10, 50, 100):
        assert W.carry_chance(extra) == T.FR_INJ_PLAY * (100 - T.FR_INJ_TACKLER) * extra // 10000
        assert W.game_chance(10, extra) == W.carry_chance(extra)
        assert abs(W.game_chance(60, extra) - 6 * W.carry_chance(extra)) <= 6
    assert W.game_chance(10 ** 6, 100) == 9999


def test_the_weeks_draws_add_the_expected_carries_of_the_teams_the_engine_did_not_play():
    league = league_at(3)
    I.after_games(league, 2, GameRandomFromSeed(4), SURNAMES, played=(TEAM, OPP))
    assert all(W.carries_of(league, back_of(league, team).id) == 0 for team in (TEAM, OPP))
    total = sum(W.carries_of(league, p.id) for p in league.group_of(1, "RB"))
    assert abs(total - T.FR_WORKLOAD_RUNS) <= 6


def GameRandomFromSeed(seed):
    from nfl4.game.rnd import GameRandom
    return GameRandom(random.Random(seed))


def test_a_back_past_his_free_carries_draws_once_more_in_the_weeks_draws_and_nobody_else_does(monkeypatch):
    league = league_at(3)
    monkeypatch.setattr(T, "FR_INJ_PRACTICE", (0, 0))
    monkeypatch.setattr(T, "FR_INJ_GAME", (0, 0))
    heavy = back_of(league, 1)
    W.add_carries(league, heavy.id, T.FR_WORKLOAD_FREE + 4 * T.FR_WORKLOAD_PER)
    sizes = []

    class Source:
        def below(self, n):
            sizes.append(n)
            return 0                                                  # every draw hits

        def __call__(self, n):
            return self.below(n) + 1
    done = I.after_games(league, 2, Source(), SURNAMES)
    assert sizes[0] == 10000 and done.workload == [heavy.id] and I.row_of(league, heavy.id) is not None
    assert sizes.count(10000) == 1                                   # one back past his carries, one workload draw in the league


def test_with_the_rules_percent_at_zero_the_weeks_draws_are_the_old_ones(monkeypatch):
    league_a, league_b = league_at(3), league_at(3)
    for league in (league_a, league_b):
        W.add_carries(league, back_of(league, 2).id, 5000)
    monkeypatch.setattr(T, "FR_CARRY_WEIGHT", (4, 4, 0))
    asked = []
    monkeypatch.setattr(W, "game_chance", lambda tenths, extra: asked.append((tenths, extra)) or 0)    # drawn, never a hit
    a = Counting(GameRandomFromSeed(9))
    I.after_games(league_a, 2, a, SURNAMES)
    assert asked == [((2 * T.FR_WORKLOAD_RUNS + 6) // 12, T.FR_WORKLOAD_MAX)]      # one back past his carries: one draw in the league
    monkeypatch.setattr(T, "FR_WORKLOAD_PCT", 0)
    b = Counting(GameRandomFromSeed(9))
    I.after_games(league_b, 2, b, SURNAMES)
    first = next(i for i, (x, y) in enumerate(zip(a.sizes, b.sizes)) if x != y)
    assert a.sizes[:first] == b.sizes[:first] and a.sizes[first] == 10000 and len(asked) == 1      # the same draws up to the one more draw


# ----- a game the engine plays -----

def test_every_rush_of_a_back_counts_and_joins_the_season_with_the_result(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 0)
    league = league_at(3)
    rig, engine, game = play(tmp_path, 21, league, 3)
    rushes = {}
    for outcome in engine.outcomes:
        if outcome.kind == O.RUN and not outcome.qb_run and outcome.then is None and not outcome.two_point_try:
            team = TEAM if outcome.offense == 1 else OPP
            pid = league.player_at(team, D.PLACES_OF["RB"][outcome.carrier - 1]).id
            rushes[pid] = rushes.get(pid, 0) + 10
    assert game.record["carries"] == {str(k): v for k, v in rushes.items()} and sum(rushes.values()) > 100
    game.commit()
    assert all(W.carries_of(league, pid) == n for pid, n in rushes.items()) and game.record["carries"] == {}


def test_a_heavy_backs_rush_draws_once_more_when_the_play_hurt_nobody(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 0)
    league = league_at(3)
    for team in (TEAM, OPP):
        for k in range(6):
            W.add_carries(league, back_of(league, team, k).id, T.FR_WORKLOAD_FREE + T.FR_WORKLOAD_PER)
    rig, engine, game = play(tmp_path, 21, league, 3)
    rushes = sum(1 for o in engine.outcomes if o.kind == O.RUN and not o.qb_run and o.then is None and not o.two_point_try)
    assert game.rnd.sizes.count(10000) == exposed(game, engine) + rushes and rushes > 10


def heavy_league():
    league = league_at(3)
    for team in (TEAM, OPP):
        for k in range(6):
            W.add_carries(league, back_of(league, team, k).id, T.FR_WORKLOAD_FREE + T.FR_WORKLOAD_PER)
    return league


def test_a_play_that_hurt_somebody_draws_no_workload_draw(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 10000)                   # every exposed play hurts somebody (until a team's limit)
    rig, engine, game = play(tmp_path, 23, heavy_league(), 3)
    assert game.rnd.sizes.count(10000) == exposed(game, engine)     # one draw a play: the workload's draw comes only after a play that hurt nobody


def test_the_workload_draw_hurts_the_heavy_back_who_carried(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 0)                       # the play's own draw never hurts ...
    monkeypatch.setattr(W, "carry_chance", lambda extra: 10000)     # ... the workload's always does
    league = heavy_league()
    rig, engine, game = play(tmp_path, 21, league, 3)
    hurt = [league.players[row[0]] for row in game.record["hurt"]]
    assert hurt and all(p.pos == "RB" for p in hurt)                # only backs who carried, hurt as the ball carrier


def test_a_played_games_rosters_keep_the_morale_at_the_kick_off_and_after_an_injury():
    from nfl4.extras.state import ExtrasRecord
    from nfl4.game.gamestate import GameState
    league = league_at(3)
    back = back_of(league)
    P.set_morale(league, back.id, T.FR_MORALE_MAX)
    game = F.GameInjuries(league, TEAM, OPP, 3, False, Counting(GameRandomFromSeed(1)), SURNAMES, WORDS)
    s = GameState()
    s.extras = ExtrasRecord()
    s.rosters = {1: F.lineup_roster(league, TEAM, 3, False), 2: F.lineup_roster(league, OPP, 3, True)}
    key = ("Running Backs:", 1)
    want = F.lineup_roster(league, TEAM, 3, False).ratings[key]
    assert want == min(D.RATING_MAX, back.rating + P.effect(T.FR_MORALE_MAX)) != back.rating
    game.quarterbacks(s)                                            # Getqbs at the kick-off rewrites the rosters (the review of SX.8o)
    assert s.rosters[1].ratings[key] == want
    game.refresh(1)                                                 # as after an injury
    assert s.rosters[1].ratings[key] == want


def test_the_games_of_the_players_team_follow_the_staff_setting():
    league = league_at(3)
    back = back_of(league, TEAM, 1)
    I.injure(league, back.id, "IJA", 1, 0, 2)                       # questionable for week 3, and the player decided nothing
    other = league_at(3)
    I.injure(other, back.id, "IJA", 1, 0, 2)
    W.count_games(league, 3, staff=False)                           # nothing decided for him: the questionable man rests
    W.count_games(other, 3, staff=True)                             # the staff plays a questionable man
    assert W.games_of(league, back.id) == 0 and W.games_of(other, back.id) == 1


# ----- SX.8o: the game part's place draw follows the carry shares (the mutation check's survivors) -----

def test_the_game_parts_place_draw_is_over_the_carry_weighted_places(monkeypatch):
    league = league_at(3)
    monkeypatch.setattr(T, "FR_INJ_PRACTICE", (0, 0))
    monkeypatch.setattr(T, "FR_INJ_GAME", (1, 10000))                 # one draw of the game part, always a hit
    for k, rating in enumerate((99, 70, 70, 70, 70, 40)):
        back_of(league, 1, k).rating = rating
    rated = W.rated_table(league, 1, I.week_table(league, 1, 2))
    want = sum(W.place_weights(rated))
    flat = sum(T.FR_INJ_GAME_WEIGHT[D.POSITION_OF_PLACE[i]] for i in range(D.PLACE_COUNT))
    sizes = []
    real = I._place_by_weight

    def spy(rnd, weights=None):
        sizes.append(sum(weights) if weights is not None else flat)
        return real(rnd, weights)
    monkeypatch.setattr(I, "_place_by_weight", spy)
    I.after_games(league, 2, GameRandomFromSeed(5), SURNAMES)
    assert sizes[0] == want != flat
