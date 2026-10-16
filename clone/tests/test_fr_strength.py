"""A team's place in its league and its effect on the computer's games (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 5.2, 13, SX.8b).
This is inspired by Jim Kitchen.

The league's 32 exact strength sums give z = (sum - mean) / max(sd, floor); a regular week's score index moves by
sign(z) * min(6, round_half_up(|z| * 3)) and the play-off coin leans by 60 per mille per standard deviation of the gap, 250 to 750.
The module computes them with whole numbers; these tests check it against a 60-digit decimal calculation of the same formula, by
hand-worked leagues, and through the season engine's hooks on strict scripts.
"""
import random
from decimal import Decimal, getcontext

import pytest

from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import SEASON, new_league
from nfl4.extras.franchise.mode import FranchiseHooks
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.strength import LeaguePlace
from nfl4.game.names import load_surnames
from nfl4.game.playoffs import ComputerGame, TeamRef, computer_game, score_of
from nfl4.game.rnd import GameRandom
from nfl4.game.season_engine import ClassicSeasonHooks, playoff_result
from frratings import use_design_values
from pagrig import Draws
from randsources import ScriptedRandom
from seasonrig import ENTER, run, season_rig, texts
from test_season_week import OTHERS, name, standard_games, team_draws, week_draws

getcontext().prec = 60
SURNAMES = load_surnames()
EVEN = 78 * 70                                    # the weighted sum of a team of 70s


@pytest.fixture(autouse=True)
def design_values(monkeypatch):
    """The hand-worked leagues below use the design's start values (3 places a standard deviation, 6 at most, 60 per mille); the
    calibrated values (5, 10, 150) have the tests named "calibrated" at the end."""
    use_design_values(monkeypatch)


def two_levels(plus=78 * 4, minus=78 * 4):
    """Sixteen teams at EVEN + plus and sixteen at EVEN - minus."""
    return [EVEN + plus] * 16 + [EVEN - minus] * 16


def exact(sums, team, per_sd):
    """round_half_up(|z| * per_sd) with the sign, from a 60-digit calculation of the formula of design 5.2."""
    n = len(sums)
    mean = Decimal(sum(sums)) / n
    var = sum((Decimal(s) - mean) ** 2 for s in sums) / n
    sd = max(var.sqrt(), Decimal(T.FR_SPREAD_FLOOR))
    z = (Decimal(sums[team - 1]) - mean) / sd
    value = abs(z) * per_sd
    magnitude = int((value + Decimal("0.5")).to_integral_value(rounding="ROUND_FLOOR"))
    return magnitude if z >= 0 else -magnitude


# ----- hand-worked leagues -----

def test_sixteen_teams_four_points_above_and_sixteen_below_are_one_standard_deviation_out():
    sums = two_levels()                                       # sd = 312 = 78 * 4, the mean is EVEN: z = +1 and -1
    place = LeaguePlace(sums)
    assert place.shift(1) == 3 and place.shift(17) == -3        # one standard deviation x 3 places
    assert all(place.shift(t) == 3 for t in range(1, 17)) and all(place.shift(t) == -3 for t in range(17, 33))
    assert place.playoff_per_mille(1, 17) == 500 + 120          # a gap of two standard deviations x 60 per mille
    assert place.playoff_per_mille(17, 1) == 500 - 120
    assert place.playoff_per_mille(1, 2) == 500                 # equal teams: the original's coin


def test_the_spread_floor_keeps_a_nearly_even_league_from_exaggerating_one_teams_lead():
    sums = [EVEN] * 31 + [EVEN + 78]                            # one team a rating point above the rest: the sd is only 13.6 sums
    place = LeaguePlace(sums)
    # without the floor z = 5.57 and the shift would be the cap 6; with it z = 2418 / 2496 = 0.969 (2418 is 32 times the team's
    # distance from the mean, 2496 is 32 times the floor of 78): three places, and the others (z = -0.031) stay where they are
    assert place.shift(32) == 3 and all(place.shift(t) == 0 for t in range(1, 32))
    assert place.shift(32) < T.FR_SHIFT_MAX


def test_the_shift_is_capped_and_a_league_of_equal_teams_has_none():
    sums = [EVEN] * 31 + [EVEN + 78 * 40]
    assert LeaguePlace(sums).shift(32) == T.FR_SHIFT_MAX == 6     # z = 5.57: 17 places is capped to 6
    for value in (0, 1, EVEN, 78 * 99, 12345):
        place = LeaguePlace([value] * 32)                         # every sum equal at any value: z = 0 for every team
        assert all(place.shift(t) == 0 for t in range(1, 33))
        assert place.playoff_per_mille(1, 2) == 500 and place.playoff_per_mille(31, 4) == 500
    assert LeaguePlace([EVEN] * 32).index(5, 17) == 17


def test_the_play_off_lean_is_capped_at_250_and_750_per_mille():
    sums = [EVEN] * 30 + [EVEN + 78 * 30, EVEN - 78 * 30]
    place = LeaguePlace(sums)
    assert place.playoff_per_mille(31, 32) == D.PLAYOFF_CHANCE_MAX == 750      # a gap of about 8 standard deviations
    assert place.playoff_per_mille(32, 31) == D.PLAYOFF_CHANCE_MIN == 250
    assert place.playoff_per_mille(1, 2) == 500


def test_a_league_needs_32_sums():
    with pytest.raises(ValueError):
        LeaguePlace([EVEN] * 31)


def test_the_index_stays_inside_the_table():
    place = LeaguePlace([EVEN] * 31 + [EVEN + 78 * 40])
    assert place.index(32, 31) == 32 and place.index(32, 1) == 7 and place.index(32, 26) == 32
    low = LeaguePlace([EVEN] * 31 + [EVEN - 78 * 40])
    assert low.index(32, 2) == 1 and low.index(32, 7) == 1 and low.index(32, 8) == 2 and low.index(32, 32) == 26


# ----- the whole-number arithmetic against the decimal calculation, and the symmetry -----

def random_league(rng, spread):
    return [max(78 * 40, min(78 * 99, EVEN + int(rng.gauss(0, spread)))) for _ in range(32)]


def test_the_integer_shift_and_lean_equal_the_decimal_calculation_in_many_leagues():
    check_against_the_decimal_calculation()


def test_the_calibrated_values_equal_the_decimal_calculation_in_many_leagues(monkeypatch):
    for name, value in dict(FR_SHIFT_PER_SD=5, FR_SHIFT_MAX=10, FR_PLAYOFF_PER_SD=150, FR_SPREAD_FLOOR=78).items():
        monkeypatch.setattr(T, name, value)
    check_against_the_decimal_calculation()
    place = LeaguePlace(two_levels())                          # one standard deviation out: five places, 150 per mille a deviation
    assert place.shift(1) == 5 and place.shift(32) == -5
    assert place.playoff_per_mille(1, 17) == 750 and place.playoff_per_mille(17, 1) == 250     # a gap of 2: 300, capped at 250
    assert LeaguePlace([EVEN] * 31 + [EVEN + 78 * 40]).shift(32) == 10


def check_against_the_decimal_calculation():
    rng = random.Random(7)
    checked = 0
    for spread in (3, 20, 78, 150, 312, 700, 1500):
        for _ in range(30):
            sums = random_league(rng, spread)
            place = LeaguePlace(sums)
            for team in range(1, 33):
                expected = max(-T.FR_SHIFT_MAX, min(T.FR_SHIFT_MAX, exact(sums, team, T.FR_SHIFT_PER_SD)))
                assert place.shift(team) == expected, (sums, team)
                checked += 1
            mean = Decimal(sum(sums)) / 32
            sd = max((sum((Decimal(s) - mean) ** 2 for s in sums) / 32).sqrt(), Decimal(T.FR_SPREAD_FLOOR))
            for _ in range(8):
                v, h = rng.sample(range(1, 33), 2)
                # the lean is rounded once, from the gap of the two teams' z, not from each team's
                gap = (Decimal(sums[v - 1]) - Decimal(sums[h - 1])) / sd * T.FR_PLAYOFF_PER_SD
                rounded = int((abs(gap) + Decimal("0.5")).to_integral_value(rounding="ROUND_FLOOR"))
                rounded = rounded if gap >= 0 else -rounded
                assert place.playoff_per_mille(v, h) == max(250, min(750, 500 + rounded)), (sums, v, h)
                assert place.playoff_per_mille(v, h) + place.playoff_per_mille(h, v) == 1000
                checked += 1
    assert checked > 7000


def test_a_mirrored_league_gives_exactly_the_negative_shift_and_the_mirrored_lean():
    rng = random.Random(11)
    for spread in (30, 200, 900):
        for _ in range(40):
            sums = random_league(rng, spread)
            mirror = [2 * EVEN - s for s in sums]               # the same distances on the other side of the middle
            a, b = LeaguePlace(sums), LeaguePlace(mirror)
            assert sum(sums) + sum(mirror) == 64 * EVEN
            assert [a.shift(t) for t in range(1, 33)] == [-b.shift(t) for t in range(1, 33)]


def test_the_shift_rises_with_the_sum_and_is_zero_for_the_mean_team_in_every_league():
    rng = random.Random(3)
    for _ in range(50):
        place = LeaguePlace(random_league(rng, 200))
        order = sorted(range(1, 33), key=lambda t: place.d[t - 1])
        shifts = [place.shift(t) for t in order]
        assert shifts == sorted(shifts)
        assert -T.FR_SHIFT_MAX <= min(shifts) and max(shifts) <= T.FR_SHIFT_MAX


# ----- chance_first -----

def test_chance_first_at_500_is_exactly_the_originals_coin_for_every_number():
    source = random.Random(5)
    numbers = [source.random() for _ in range(100_000)] + [0.0, 0.4999, 0.49999999999999994, 0.5, 0.5000000000000001, 0.9999999999999999]
    first, second = GameRandom(ScriptedRandom(list(numbers))), GameRandom(ScriptedRandom(list(numbers)))
    for _ in numbers:
        assert second.chance_first(500) == (first(2) == 1)


def test_chance_first_draws_one_number_traced_as_two_and_leans_by_the_chance_it_is_given():
    rnd = GameRandom(ScriptedRandom([0.7499, 0.7501, 0.2499, 0.2501, 0.0, 0.999]))
    rnd.trace = []
    assert [rnd.chance_first(750), rnd.chance_first(750), rnd.chance_first(250), rnd.chance_first(250),
            rnd.chance_first(0), rnd.chance_first(1000)] == [True, False, True, False, False, True]
    assert rnd.trace == [2] * 6


def test_a_whole_run_of_numbers_gives_the_chance_asked_for():
    rnd = GameRandom(random.Random(1))
    for per_mille in (250, 620, 750):
        share = sum(rnd.chance_first(per_mille) for _ in range(40_000)) / 40_000
        assert abs(share - per_mille / 1000) < 0.01


# ----- the engine's hooks -----

class Shifts(ClassicSeasonHooks):
    """H14 with a given shift for some teams (a hand-made league for the engine's tests)."""

    def __init__(self, shifts):
        self.shifts = shifts
        self.asked = []

    def computer_index(self, team, index):
        self.asked.append((team, index))
        return max(1, min(32, index + self.shifts.get(team, 0)))


def first_game_draws(a, ia, b, *ib):
    draws = Draws()
    team_draws(draws, a).rnd(32, ia)
    team_draws(draws, b)
    for raw in ib:
        draws.rnd(32, raw)
    return draws


def test_classic_hooks_leave_the_index_and_the_play_off_coin_alone():
    hooks = ClassicSeasonHooks()
    assert hooks.computer_index(TeamRef(1, 1), 17) == 17
    rnd = GameRandom(ScriptedRandom([0.49, 0.5, 0.0, 0.99]))
    rnd.trace = []
    assert [hooks.playoff_first_wins(rnd, TeamRef(1, 1), TeamRef(2, 2)) for _ in range(4)] == [True, False, True, False]
    assert rnd.trace == [2, 2, 2, 2]                          # exactly the original's rnd(2)


def test_a_stronger_team_draws_its_score_higher_in_the_table_and_the_redraw_compares_the_shifted_scores(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5)
    browns, ravens = OTHERS[0], OTHERS[1]
    rig.game.season_hooks = hooks = Shifts({browns: 3, ravens: 3})
    draws = first_game_draws(browns, 2, ravens, 2, 7)         # Browns 2 + 3 = 5 (6 points); Ravens 2 + 3 = 5: the same 6: again; 7 + 3 = 10 (9 points)
    draws.extend(week_draws(standard_games(start=1)))
    run(rig, rig.engine.pog, draws)
    assert (score_of(5), score_of(10)) == (6, 9)
    assert texts(rig)[2] == "Ravens over the Browns by the score of 9, to 6. "
    assert hooks.asked[:4] == [(browns, 2), (ravens, 2), (ravens, 7), (ravens, 7)]    # A; B's two tries; B's index once more
    assert rig.game.rnd.fallbacks == 0


def test_the_index_is_clamped_to_the_ends_of_the_table(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5)
    browns, ravens = OTHERS[0], OTHERS[1]
    rig.game.season_hooks = Shifts({browns: 6, ravens: -6})
    draws = first_game_draws(browns, 31, ravens, 3)           # Browns 31 + 6 = 37 -> 32 (51 points); Ravens 3 - 6 = -3 -> 1 (0 points)
    draws.extend(week_draws(standard_games(start=1)))
    run(rig, rig.engine.pog, draws)
    assert texts(rig)[2] == "Browns over the Ravens by the score of 51, to 0. "


def test_the_redraws_bounded_scan_reads_the_shifted_scores_too(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5)
    browns, ravens = OTHERS[0], OTHERS[1]
    rig.game.season_hooks = Shifts({browns: 3, ravens: 3})
    rig.game.rnd.redraw_limit = 3                              # three tries, then the first valid candidate by scanning
    draws = first_game_draws(browns, 2, ravens, 2, 2, 2)      # all three tries are 5 (6 points) against the Browns' 6 points
    draws.extend(week_draws(standard_games(start=1)))
    run(rig, rig.engine.pog, draws)
    # the scan: raw 1 + 3 = 4 (3 points) is the first index whose shifted score differs from 6: the Browns win 6 to 3
    assert texts(rig)[2] == "Browns over the Ravens by the score of 6, to 3. "
    assert rig.game.rnd.fallbacks == 1


class Coin(ClassicSeasonHooks):
    def __init__(self, answer):
        self.answer, self.asked = answer, []

    def playoff_first_wins(self, rnd, visitor, home):
        self.asked.append((visitor, home))
        return self.answer


def test_a_play_off_computer_game_asks_the_hook_for_the_coin_and_draws_the_scores_as_the_original(tmp_path):
    rig = season_rig(tmp_path)
    visitor, home = TeamRef(3, 1), TeamRef(4, 1)
    for answer, winner in ((True, visitor), (False, home)):
        rig.game.season_hooks = hooks = Coin(answer)
        draws = Draws().rnd(32, 23).rnd(32, 5)                  # no rnd(2): the hook answers; then the winner's 24 and the loser's 6
        result = run(rig, lambda: rig.engine._computer_game((visitor, home)), draws)
        loser = home if winner == visitor else visitor
        assert result == (winner, playoff_result(name(winner), name(loser), 24, 6)) and hooks.asked == [(visitor, home)]


def test_the_original_coin_draws_rnd_2_and_the_visitor_wins_on_a_1(tmp_path):
    rig = season_rig(tmp_path)
    visitor, home = TeamRef(3, 1), TeamRef(4, 1)
    for coin, winner in ((1, visitor), (2, home)):
        draws = Draws().rnd(2, coin).rnd(32, 23).rnd(32, 5)
        assert run(rig, lambda: rig.engine._computer_game((visitor, home)), draws)[0] == winner
    source = ScriptedRandom(Draws().rnd(2, 1).rnd(32, 23).rnd(32, 5).values, strict=True)
    game = computer_game(GameRandom(source))
    assert game == ComputerGame(True, 23, 5)


# ----- the Franchise's hooks over a league record -----

def league_store(sums=None, stage=SEASON):
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 5, "20260101-000000")
    if sums is not None:
        league.sums = list(sums)
    league.stage = stage
    store = FranchiseStore(MemoryFiles())
    store.league = league
    return store


def test_the_franchise_hooks_shift_by_the_leagues_sums_of_the_season():
    sums = two_levels()
    hooks = FranchiseHooks(league_store(sums))
    assert hooks.computer_index(TeamRef(1, 1), 10) == 13           # team 1: z = +1: three places up
    assert hooks.computer_index(TeamRef(5, 1), 10) == 7            # team 17: z = -1
    assert hooks.computer_index(TeamRef(1, 1), 31) == 32           # clamped
    assert hooks.place().shift(1) == 3


def test_the_franchise_hooks_lean_the_coin_and_keep_the_originals_draw_for_equal_teams():
    even = FranchiseHooks(league_store([EVEN] * 32))
    first, second = GameRandom(ScriptedRandom([0.49, 0.51])), GameRandom(ScriptedRandom([0.49, 0.51]))
    assert [even.playoff_first_wins(first, TeamRef(1, 1), TeamRef(5, 1)) for _ in range(2)] == [True, False]
    assert [second(2) == 1 for _ in range(2)] == [True, False]
    leaning = FranchiseHooks(league_store(two_levels()))
    rnd = GameRandom(ScriptedRandom([0.60, 0.63, 0.37, 0.40]))
    rnd.trace = []
    assert [leaning.playoff_first_wins(rnd, TeamRef(1, 1), TeamRef(5, 1)) for _ in range(2)] == [True, False]      # 620 per mille
    assert [leaning.playoff_first_wins(rnd, TeamRef(5, 1), TeamRef(1, 1)) for _ in range(2)] == [True, False]      # 380 per mille
    assert rnd.trace == [2, 2, 2, 2]


def test_the_franchise_hooks_do_nothing_without_the_sums_of_a_season():
    for store in (league_store([]), league_store(two_levels(), stage="offseason"), league_store([EVEN] * 31)):
        hooks = FranchiseHooks(store)
        assert hooks.place() is None and hooks.computer_index(TeamRef(1, 1), 10) == 10
        rnd = GameRandom(ScriptedRandom([0.49]))
        assert hooks.playoff_first_wins(rnd, TeamRef(1, 1), TeamRef(2, 1)) is True
    assert FranchiseHooks(FranchiseStore(MemoryFiles())).place() is None         # no league at all


def test_the_hooks_follow_a_new_set_of_sums():
    store = league_store(two_levels())
    hooks = FranchiseHooks(store)
    assert hooks.computer_index(TeamRef(1, 1), 10) == 13
    store.league.sums = [EVEN] * 32
    assert hooks.computer_index(TeamRef(1, 1), 10) == 10
