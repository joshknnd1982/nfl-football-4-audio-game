"""The ratings' bounded effect in a game the player plays (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 5.1, SX.8b). This is inspired
by Jim Kitchen.

Every expected number is worked out by hand from the rule next to it (B-X38): step(x, per, cap) = sign(x) * min(cap, |x| // per);
the offense's rating (a run: the carrier's, a pass: (2 quarterback + receiver + 1) // 3, a designed quarterback run: the
quarterback's), the defense's (the two tacklers' mean, rounded up), d = offense - defense, and the Mod ylo = yhi = step(d, 12, 1),
sack = -step(d, 6, 3), comp = step(d, 6, 3), fum = step(d, 8, 3), added to the playbook's Mod and clamped to the playbooks' bounds.
"""
import pytest

from frratings import rated_roster, state_with, use_design_values
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps

from nfl4.extras import playbook_data as PD
from nfl4.extras import playbooks as PB
from nfl4.extras import tuning as T
from nfl4.extras.franchise import ratings as R
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.playbooks import PlaybookModifiers
from nfl4.extras.qb_runs import make_entry
from nfl4.game.playtables import NEUTRAL, PASSES, RUNS, PassEntry, QBRunEntry, RunEntry
from test_nx_qb_plays import after_play
from test_pag_scrimmage import first_handoff, quiet_snap_count, snap_draws


@pytest.fixture(autouse=True)
def design_values(monkeypatch):
    """The hand-worked numbers below are the design's start values with no team edge (frratings.DESIGN_VALUES); the tests of the
    calibrated values say so in their name and set their own."""
    use_design_values(monkeypatch)


# the values SX.8b calibrated (extras/tuning.py has their history, D-057); a later move of one fails the tests named "calibrated"
CALIBRATED = dict(FR_YARD_STEP=(4, 1), FR_SACK_STEP=(2, 3), FR_COMP_STEP=(2, 3), FR_FUM_STEP=(3, 3), FR_TEAM_EDGE=(5, 2),
                  FR_KICK_STEP=(5, 5), FR_PUNT_STEP=(8, 3), FR_SHIFT_MAX=10, FR_SHIFT_PER_SD=5, FR_SPREAD_FLOOR=78,
                  FR_PLAYOFF_PER_SD=150, FR_TEAM_LEVEL_LOW=-2, FR_TEAM_LEVEL_SPAN=5)


@pytest.fixture
def calibrated(monkeypatch):
    for name, value in CALIBRATED.items():
        monkeypatch.setattr(T, name, value)


def bound(carrier=1, d1=1, d2=2, own=None, opponent=None, offense_play=1, wisoff=1, mod=None):
    """FranchiseModifiers bound to a state: the Bengals (side 1) have the ball."""
    own = own if own is not None else rated_roster("")
    opponent = opponent if opponent is not None else rated_roster("O")
    modifiers = R.FranchiseModifiers()
    modifiers.bind(state_with(own, opponent, wisoff, carrier, d1, d2, offense_play))
    modifiers.arm(mod)
    return modifiers


# ----- step and the Mod -----

def test_step_is_zero_under_its_size_whole_numbers_and_the_same_size_up_and_down():
    assert [R.step(x, 12, 1) for x in (0, 1, 11, 12, 23, 24, 59)] == [0, 0, 0, 1, 1, 1, 1]
    assert [R.step(x, 6, 3) for x in (5, 6, 11, 12, 17, 18, 35, 59)] == [0, 1, 1, 2, 2, 3, 3, 3]
    assert [R.step(x, 8, 3) for x in (7, 8, 15, 16, 24, 25)] == [0, 1, 1, 2, 3, 3]
    for per, cap in ((12, 1), (6, 3), (8, 3), (5, 5)):
        for x in range(-70, 71):
            assert R.step(-x, per, cap) == -R.step(x, per, cap)          # Python's // floors a negative number: not used on one


def test_the_mod_of_a_gap_is_worked_out_from_the_four_steps():
    assert R.rating_mod(0) == PD.ZERO and R.rating_mod(5) == PD.ZERO and R.rating_mod(-5) == PD.ZERO      # under every step's size
    assert R.rating_mod(6) == PD.Mod(0, 0, -1, 1, 0) and R.rating_mod(8) == PD.Mod(0, 0, -1, 1, 1)         # 6 // 6 = 1; 8 // 8 = 1
    assert R.rating_mod(11) == PD.Mod(0, 0, -1, 1, 1)                  # the yards need 12
    assert R.rating_mod(12) == PD.Mod(1, 1, -2, 2, 1)                  # sack 12 // 6 = 2 fewer, catch 2 more, fumble 12 // 8 = 1
    assert R.rating_mod(-12) == PD.Mod(-1, -1, 2, -2, -1)
    assert R.rating_mod(25) == PD.Mod(1, 1, -3, 3, 3)                  # 25 // 6 = 4 is capped at 3; 25 // 8 = 3
    assert R.rating_mod(59) == PD.Mod(1, 1, -3, 3, 3) and R.rating_mod(-59) == PD.Mod(-1, -1, 3, -3, -3)


def test_the_ratings_alone_never_move_a_row_more_than_one_yard_and_three_points():
    for gap in range(-59, 60):
        mod = R.rating_mod(gap)
        assert abs(mod.ylo) <= 1 and mod.ylo == mod.yhi
        assert max(abs(mod.sack), abs(mod.comp), abs(mod.fum)) <= 3
        assert mod.sack == -mod.comp                                    # a better offense is sacked less and catches more
    assert all(a <= b for a, b in zip((R.rating_mod(g).comp for g in range(-59, 59)),
                                      (R.rating_mod(g).comp for g in range(-58, 60))))     # the effect grows with the gap


# ----- which ratings count -----

def test_a_run_reads_the_carrier_and_the_two_tacklers():
    own = rated_roster("", 70, rb3=90)
    opponent = rated_roster("O", 70, d5=60, d9=70)                        # the defense: (60 + 70 + 1) // 2 = 65
    m = bound(carrier=3, d1=5, d2=9, own=own, opponent=opponent, offense_play=1)
    assert m.gap("run") == 25                                              # 90 - 65
    row = m.run(1, 3, RUNS[(1, 3)])                                        # 0 to 7 (exclusive): +1 and +1
    assert (row.low, row.high) == (1, 8) and (row.key, row.direction, row.sound) == ("plunge_long_run", 3, 3)
    assert m.fumble_odds(1) == 53                                          # 50 + 3
    other = bound(carrier=2, d1=5, d2=9, own=own, opponent=opponent, offense_play=1)
    assert other.gap("run") == 5 and other.run(1, 3, RUNS[(1, 3)]) is RUNS[(1, 3)]          # carrier 2 is 70: a gap of 5 is no step


def test_a_pass_reads_two_thirds_quarterback_and_one_third_the_target():
    own = rated_roster("", 70, qb=90, wr2=60)                               # (2 * 90 + 60 + 1) // 3 = 80
    opponent = rated_roster("O", 70, d5=60, d9=70)                          # 65
    m = bound(carrier=2, d1=5, d2=9, own=own, opponent=opponent, offense_play=4)
    assert m.gap("pass") == 15                                              # 80 - 65: yards 1, sack -2, catch +2, fumble 1
    row = m.pass_(4, 4, PASSES[(4, 4)])                                     # 5 to 50, sack 50, catch 70
    assert row == PassEntry(6, 51, 48, 72)
    assert m.fumble_odds(1) == 51                                           # a sack and a completion test the fumble with the pass Mod
    rb_only = bound(carrier=2, d1=5, d2=9, own=rated_roster("", 70, rb2=99), opponent=opponent, offense_play=4)
    assert rb_only.gap("pass") == 5                                         # a running back's rating does not count in a pass


def test_a_designed_quarterback_run_reads_the_quarterback_and_the_tackles():
    own = rated_roster("", 70, qb=95)
    opponent = rated_roster("O", 70, d1=45, d2=45)                          # a gap of 50
    m = bound(carrier=4, own=own, opponent=opponent, offense_play=9)
    entry = QBRunEntry("keeper", 4, 3, -3, 6, 90)
    assert m.gap("qb") == 50
    assert m.qb_run(entry) == QBRunEntry("keeper", 4, 3, -2, 7, 93)         # yards +1, the fumble 1 in 90 + 3 (the entry's own odds)
    assert m.mod_for("qb") == PD.Mod(1, 1, -3, 3, 3) and m.play_kind() == R.QB


def test_the_defense_sides_ratings_are_the_other_teams_and_the_side_with_the_ball_may_be_either():
    own = rated_roster("", 70, d1=40, d2=40)
    opponent = rated_roster("O", 70, qb=99, rb1=99)                         # the opponent has the ball
    m = bound(carrier=1, d1=1, d2=2, own=own, opponent=opponent, offense_play=1, wisoff=2)
    assert m.gap("run") == 99 - 40
    flipped = bound(carrier=1, d1=1, d2=2, own=own, opponent=opponent, offense_play=1, wisoff=1)
    assert flipped.gap("run") == 70 - 70                                    # the home team's carrier against the opponent's tacklers


# ----- no ratings, every rating 70 -----

def test_a_league_of_70s_reads_every_row_field_goal_and_punt_as_the_original():
    m = bound(own=rated_roster("", 70), opponent=rated_roster("O", 70))
    for key, entry in RUNS.items():
        assert m.run(*key, entry) is entry
    for key, entry in PASSES.items():
        assert m.pass_(*key, entry) is entry
    assert m.fumble_odds(1) == NEUTRAL.fumble_odds(1) == 50
    assert m.field_goal_odds(1) == NEUTRAL.field_goal_odds(1) and m.punt(2) == NEUTRAL.punt(2)


def test_a_game_without_ratings_reads_every_row_as_the_playbooks_object_does():
    plain = PlaybookModifiers()
    unrated = bound(own=rated_roster(""), opponent=rated_roster("O"))
    unrated.state.rosters[1].ratings = {}                                      # the rosters of every game that is not a Franchise game
    unrated.state.rosters[2].ratings = {}
    for key, entry in RUNS.items():
        assert unrated.run(*key, entry) is entry and plain.run(*key, entry) is entry
    assert unrated.gap("run") is None and unrated.gap("pass") is None and unrated.gap("qb") is None
    assert unrated.fumble_odds(1) == NEUTRAL.fumble_odds(1) and unrated.field_goal_odds(1) == NEUTRAL.field_goal_odds(1)
    assert unrated.punt(1) == NEUTRAL.punt(1)
    armed = bound(own=rated_roster(""), opponent=rated_roster("O"), mod=PD.Mod(1, 2, 0, 0, 0))
    armed.state.rosters[1].ratings = {}
    assert armed.run(1, 3, RUNS[(1, 3)]) == plain_armed(PD.Mod(1, 2, 0, 0, 0)).run(1, 3, RUNS[(1, 3)])     # the playbook's Mod alone
    unbound = R.FranchiseModifiers()                                           # never bound to a state
    assert unbound.run(1, 1, RUNS[(1, 1)]) is RUNS[(1, 1)] and unbound.punt(2) == NEUTRAL.punt(2)
    assert unbound.fumble_odds(1) == 50 and unbound.field_goal_odds(2) == 70 and unbound.mod_for("fumble") is None
    assert unbound.pass_(4, 4, PASSES[(4, 4)]) is PASSES[(4, 4)]
    armed = R.FranchiseModifiers()
    armed.arm(PD.Mod(1, 2, 0, 0, 3))                                           # unbound with a playbook's Mod: the playbook's alone
    assert armed.fumble_odds(1) == 53 and armed.run(1, 3, RUNS[(1, 3)]) == plain_armed(PD.Mod(1, 2, 0, 0, 3)).run(1, 3, RUNS[(1, 3)])


def plain_armed(mod):
    m = PlaybookModifiers()
    m.arm(mod)
    return m


def test_a_place_without_a_rating_counts_70():
    own = rated_roster("", 70, rb1=90)
    del own.ratings[("Running Backs:", 1)]
    m = bound(carrier=1, own=own, opponent=rated_roster("O", 70, d1=40, d2=40), offense_play=1)
    assert m.gap("run") == 70 - 40


# ----- added to the playbook's Mod and clamped to the same bounds -----

def test_the_ratings_mod_is_added_to_the_playbooks_and_the_sum_is_clamped_to_the_bounds():
    own = rated_roster("", 70, rb1=99)
    opponent = rated_roster("O", 70, d1=40, d2=40)                           # a gap of 59: Mod(1, 1, -3, 3, 3)
    run = RUNS[(1, 3)]
    for armed, expected in ((None, PD.Mod(1, 1, -3, 3, 3)),
                            (PD.Mod(2, 2, 5, 5, 5), PD.Mod(2, 2, 2, 5, 5)),      # 3 and 6 and 8 are clamped to 2 and 5
                            (PD.Mod(-2, -2, -5, -5, -5), PD.Mod(-1, -1, -5, -2, -2)),
                            (PD.Mod(1, 0, 1, -1, 1), PD.Mod(2, 1, -2, 2, 4))):    # inside the bounds: the plain sum
        m = bound(carrier=1, own=own, opponent=opponent, offense_play=1, mod=armed)
        assert m.mod_for("run") == expected, armed
        row = m.run(1, 3, run)
        assert (row.low, row.high) == (run.low + expected.ylo, max(run.high + expected.yhi, run.low + expected.ylo + 1))
        assert m.fumble_odds(1) == 50 + expected.fum


def test_a_pass_row_keeps_its_percents_between_zero_and_a_hundred_with_the_ratings_added():
    own = rated_roster("", 70, qb=99, wr1=99)
    opponent = rated_roster("O", 70, d1=40, d2=40)
    m = bound(carrier=1, own=own, opponent=opponent, offense_play=3, mod=PD.Mod(0, 0, -5, 5, 0))
    row = m.pass_(3, 1, PassEntry(-3, 10, 5, 98))                            # screen against the goal line: sack 5, catch 98
    assert row.sack == 0 and row.complete == 100                              # 5 - 5 - 3 and 98 + 5 + 3 stay in range
    worse = bound(carrier=1, own=rated_roster("", 40), opponent=rated_roster("O", 99), offense_play=3, mod=PD.Mod(0, 0, 5, -5, 0))
    low = worse.pass_(5, 4, PassEntry(15, 100, 60, 40))                      # a gap of -59: sack +3, catch -3; the playbook: +5, -5
    assert low.sack == 65 and low.complete == 35                              # 60 + (5 + 3 clamped to 5), 40 - (5 + 3 clamped to 5)
    thin = worse.pass_(5, 4, PassEntry(15, 100, 60, 3))
    assert thin.complete == 1                                                 # a catch is never below 1 percent


CORNERS = [PD.Mod(a * 2, b * 2, c * 5, d * 5, e * 5) for a in (-1, 1) for b in (-1, 1) for c in (-1, 0, 1) for d in (-1, 0, 1)
           for e in (-1, 0, 1)] + [PD.ZERO]                                  # every corner of the bounds, and no playbook (109)


def unequal_rosters():
    """Ratings 40 to 99 that differ from slot to slot and from one team to the other."""
    own, opponent = rated_roster(""), rated_roster("O")
    for key in own.ratings:
        own.ratings[key] = 40 + (sum(map(ord, key[0])) * 7 + key[1] * 13) % 60
    for key in opponent.ratings:
        opponent.ratings[key] = 40 + (sum(map(ord, key[0])) * 11 + key[1] * 17) % 60
    return own, opponent


def table_row(play, call):
    """The original's row of an offense play 1 to 5 or 8 to 10 against a defense call, and the call that applies it."""
    if play <= 2:
        return RUNS[(play, call)], lambda m, row: m.run(play, call, row)
    if play <= 5:
        return PASSES[(play, call)], lambda m, row: m.pass_(play, call, row)
    return make_entry({8: "sneak", 9: "keeper", 10: "draw"}[play], call), lambda m, row: m.qb_run(row)


def inside_the_bounds(original, row):
    """The row is the original's moved by at most the bounds of design 10.3, and is still a row."""
    assert abs(row.low - original.low) <= PD.BOUNDS.ylo and abs(row.high - original.high) <= PD.BOUNDS.yhi and row.high > row.low
    if isinstance(original, PassEntry):
        assert abs(row.sack - original.sack) <= PD.BOUNDS.sack and abs(row.complete - original.complete) <= PD.BOUNDS.comp
        assert row.complete >= 1 and 0 <= row.sack <= 100
    if isinstance(original, QBRunEntry):
        assert row.fumble >= 2 and abs(row.fumble - original.fumble) <= PD.BOUNDS.fum


@pytest.mark.parametrize("values", ["design", "calibrated"])
def test_every_row_stays_inside_the_bounds_for_every_carrier_every_tackler_and_every_playbook_corner(monkeypatch, values):
    """Property, on the rows and not on the Mod: every play of the original's tables and the quarterback runs, every carrier and
    every first tackler (the second is the next one), every corner of the playbooks' Mod, both ways round."""
    if values == "calibrated":
        for name, value in CALIBRATED.items():
            monkeypatch.setattr(T, name, value)
    own, opponent = unequal_rosters()
    checked = 0
    for play in (1, 2, 3, 4, 5, 8, 9, 10):
        for carrier in range(1, 7):
            for d1 in range(1, 18):
                call = 1 + (carrier + d1) % 6
                original, apply = table_row(play, call)
                for first, second in ((own, opponent), (opponent, own)):
                    m = bound(carrier=carrier, d1=d1, d2=d1 % 17 + 1, own=first, opponent=second, offense_play=play)
                    for armed in CORNERS:
                        m.arm(armed)
                        inside_the_bounds(original, apply(m, original))
                        if play <= 5:
                            assert 2 <= m.fumble_odds(1) and abs(m.fumble_odds(1) - 50) <= PD.BOUNDS.fum
                        checked += 1
    assert checked > 150000


@pytest.mark.parametrize("values", ["design", "calibrated"])
def test_every_pair_of_tacklers_with_the_extreme_ratings_keeps_the_rows_inside_the_bounds(monkeypatch, values):
    """Every ordered pair of two different defensive players for every carrier, the best team against the worst, a run, a pass and
    a keeper, with the corners of the bounds that push the other way and the same way."""
    if values == "calibrated":
        for name, value in CALIBRATED.items():
            monkeypatch.setattr(T, name, value)
    best, worst = rated_roster("", 99), rated_roster("O", 40)
    seen = set()
    for play in (1, 4, 9):
        for carrier in range(1, 7):
            for d1 in range(1, 18):
                for d2 in range(1, 18):
                    if d1 == d2:
                        continue
                    call = 1 + (d1 + d2) % 6
                    original, apply = table_row(play, call)
                    for first, second in ((best, worst), (worst, best)):
                        m = bound(carrier=carrier, d1=d1, d2=d2, own=first, opponent=second, offense_play=play)
                        for armed in (CORNERS[0], CORNERS[54], CORNERS[-2], CORNERS[-1]):
                            m.arm(armed)
                            inside_the_bounds(original, apply(m, original))
                            seen.add((play, carrier, d1, d2))
    assert len(seen) == 3 * 6 * 17 * 16


@pytest.mark.parametrize("values", ["design", "calibrated"])
def test_every_row_stays_inside_the_bounds_for_every_style_and_every_pair_of_its_plays_with_the_extreme_ratings(monkeypatch, values):
    """Property: the row of every (offense family, defense call) with the Mod of every style's offense play against every one of its
    defense plays (design 10.3), the ratings of the best team against the worst and the other way round: never more than the bounds
    from the original's row."""
    if values == "calibrated":
        for name, value in CALIBRATED.items():
            monkeypatch.setattr(T, name, value)
    table = PB.DEFAULT_TABLE
    best, worst = rated_roster("", 99), rated_roster("O", 40)
    checked = quarterback_rows = 0
    for style in table.styles:
        offense_plays = [play for play, _ in table.usable(style, "O")]            # the quarterback runs (families 8 to 10) too
        defense_plays = [play for play, _ in table.usable(style, "D")]
        for offense in offense_plays:
            assert offense.family in (1, 2, 3, 4, 5, 8, 9, 10)
            for defense in defense_plays:
                mod = PB.combined(table, style, offense, style, defense, offense.family, defense.family)
                original, apply = table_row(offense.family, defense.family)
                for own, opponent in ((best, worst), (worst, best)):
                    m = bound(own=own, opponent=opponent, offense_play=offense.family, mod=mod)
                    inside_the_bounds(original, apply(m, original))
                    if offense.family <= 5:
                        assert 2 <= m.fumble_odds(1) and abs(m.fumble_odds(1) - 50) <= PD.BOUNDS.fum
                    checked += 1
                    quarterback_rows += offense.family >= 8
    assert len(table.styles) == 7 and checked > 5000 and quarterback_rows > 1000


def test_every_row_moves_by_at_most_the_bounds_whatever_the_ratings():
    own = rated_roster("", 99)
    opponent = rated_roster("O", 40)
    m = bound(own=own, opponent=opponent, offense_play=1, mod=PD.Mod(2, 2, 5, 5, 5))
    for key, entry in RUNS.items():
        row = m.run(*key, entry)
        assert abs(row.low - entry.low) <= 2 and abs(row.high - entry.high) <= 2 and row.high > row.low
    for key, entry in PASSES.items():
        row = m.pass_(*key, entry)
        assert abs(row.low - entry.low) <= 2 and abs(row.high - entry.high) <= 2 and row.high > row.low
        assert abs(row.sack - entry.sack) <= 5 and abs(row.complete - entry.complete) <= 5 and row.complete >= 1


# ----- the kicks -----

def test_the_kicker_and_the_punter_move_the_field_goal_and_the_punt_around_the_originals_numbers():
    def kick(**places):
        m = bound(own=rated_roster("", 70, **places))
        return m.field_goal_odds(1), m.punt(1)
    assert kick() == (70, (35, 25))                                             # 70s: the original's
    assert kick(k=99, p=99) == (75, (35, 28))                                   # (99 - 70) // 5 = 5; (99 - 70) // 8 = 3
    assert kick(k=40, p=40) == (65, (35, 22))                                   # -30 // 5 = -6 is capped at -5; -30 // 8 = -3
    assert kick(k=74, p=77) == (70, (35, 25))                                   # under one step
    assert kick(k=75, p=78) == (71, (35, 26))
    assert kick(k=65, p=62) == (69, (35, 24))                                   # 5 // 5 = 1 below; 8 // 8 = 1 below
    side2 = bound(own=rated_roster("", 70), opponent=rated_roster("O", 70, k=90, p=50))
    assert side2.field_goal_odds(2) == 74 and side2.punt(2) == (35, 23)          # 20 // 5 = 4 and -20 // 8 = -2 (the kicking side's own)
    assert side2.field_goal_odds(1) == 70 and side2.punt(1) == (35, 25)


# ----- the engine reads them -----

def rated_engine(tmp_path, own, opponent, **fields):
    fields = dict(dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1), **fields)
    rig = nfl_engine_rig(tmp_path, answers=[13] * 3, rules=NflRules(timeouts_on=False), **fields)
    rig.engine.s.rosters = {1: own, 2: opponent}
    return rig


def test_the_rules_object_gives_the_engine_the_ratings_modifiers_bound_to_the_games_state(tmp_path):
    rig = rated_engine(tmp_path, rated_roster(""), rated_roster("O"), offense_play=1, defense_play=3)
    assert isinstance(rig.rules.modifiers, R.FranchiseModifiers) and rig.rules.modifiers.state is rig.engine.s
    assert rig.rules.books.modifiers is rig.rules.modifiers


def test_a_better_carrier_against_two_weak_tacklers_reads_a_moved_row_and_a_larger_fumble_denominator(tmp_path):
    own = rated_roster("", 70, rb3=90)
    opponent = rated_roster("O", 70, d5=60, d9=70)
    rig = rated_engine(tmp_path, own, opponent, offense_play=1, defense_play=3)
    d = quiet_snap_count(Draws())
    # SX.8o: the carrier is drawn by the backs' carry weights (the back rated 90 weighs more), so back 3 is the roll just past the first two weights
    from nfl4.extras.franchise import workload
    weights = workload.weights([70, 70, 90, 70, 70, 70])
    d.below(sum(weights), weights[0] + weights[1]).rnd(17, 5).rnd(17, 9).rnd(13, 1).rady()
    first_handoff(d, group=1, phrase=1)
    d.rnd(3, 1).rnd(53, 1).below(7, 0)                  # the direction; the fumble 1 in 50 + 3; the row is 1 to 8: width 7, 1 yard
    after_play(d, oob=99)
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert rig.engine.s.yard_line == 31 and rig.engine.s.stats[1].running_yards == 1


def test_the_same_play_with_every_rating_70_draws_the_originals_fumble_test_and_row(tmp_path):
    rig = rated_engine(tmp_path, rated_roster(""), rated_roster("O"), offense_play=1, defense_play=3)
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=3, d1=5, d2=9)
    first_handoff(d, group=1, phrase=1)
    d.rnd(3, 1).rnd(50, 1).below(7, 0)                  # the original's 1 in 50 and the row 0 to 7: 0 yards
    after_play(d, oob=99)
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert rig.engine.s.yard_line == 30


def test_a_scramble_gets_no_ratings_mod_and_a_designed_run_does(tmp_path):
    own = rated_roster("", 70, qb=99)
    opponent = rated_roster("O", 70, d1=40, d2=40)
    rig = rated_engine(tmp_path, own, opponent, offense_play=9, defense_play=3, carrier=1, defender1=1, defender2=2)
    rules, s = rig.rules, rig.engine.s
    scramble = rules.qb_entry(s, scramble=True)
    assert scramble == make_entry("scramble", s.defense_play)                  # handed over unchanged (design 5.1)
    designed = rules.qb_entry(s)
    plain = rules.qb.entry(s)
    assert designed.low == plain.low + 1 and designed.high == plain.high + 1 and designed.fumble == plain.fumble + 3


def test_the_calibrated_values_in_the_tuning_file_are_the_ones_recorded_in_d057(monkeypatch):
    monkeypatch.undo()                                                          # the file's own values, not the design's
    for name, value in CALIBRATED.items():
        assert getattr(T, name) == value, name


def test_the_calibrated_steps_keep_the_designs_caps_one_yard_and_three_points(calibrated):
    for gap in range(-80, 81):                                                  # the caps are read from the behavior of the steps
        mod = R.rating_mod(gap)
        assert abs(mod.ylo) <= 1 and mod.ylo == mod.yhi and max(abs(mod.sack), abs(mod.comp), abs(mod.fum)) <= 3
        assert mod.sack == -mod.comp
    assert R.rating_mod(3) == PD.Mod(0, 0, -1, 1, 1) and R.rating_mod(4) == PD.Mod(1, 1, -2, 2, 1)
    assert R.rating_mod(6) == PD.Mod(1, 1, -3, 3, 2) and R.rating_mod(12) == PD.Mod(1, 1, -3, 3, 3)


# ----- the team edge -----

def test_the_team_edge_is_a_part_of_the_teams_strength_gap_rounded_half_up_and_the_same_size_up_and_down(monkeypatch):
    def edge(own, numerator=5, denominator=2):
        monkeypatch.setattr(T, "FR_TEAM_EDGE", (numerator, denominator))
        m = bound(own=own, opponent=rated_roster("O"))
        return m.team_edge(1, 2), m.team_edge(2, 1)

    # the difference of the weighted sums (design 4.4: weights QB 12, K 4, RB WR DL LB CB S P 2, RET 1) over 78, times 5 / 2, half up
    assert edge(rated_roster("", 70, rb1=90, rb2=90)) == (3, -3)                 # +80: 1.03 points x 2.5 = 2.56
    assert edge(rated_roster("", 80)) == (25, -25)                                # +780: 10 points x 2.5
    assert edge(rated_roster("", 70, rb1=75, wr1=75, wr2=75)) == (1, -1)         # +30: 0.38 x 2.5 = 0.96
    assert edge(rated_roster("", 70, qb=73)) == (1, -1)                          # +36: 0.46 x 2.5 = 1.15
    assert edge(rated_roster("", 70, rb1=71)) == (0, 0)                          # +2: 0.06
    assert edge(rated_roster("", 70, rb1=40)) == (-2, 2)                         # -60: -1.92
    assert edge(rated_roster("", 70, qb=76, k=71), 1, 1) == (1, -1)              # +76 / 78 = 0.97
    assert edge(rated_roster("", 70, rb1=71, rb2=71), 1, 1) == (0, 0)            # +4: 0.05
    assert edge(rated_roster("", 70, qb=79, k=72, ret1=71), 1, 1) == (2, -2)     # +117 = 1.5 points: half up, and -1.5 is -2 too
    assert edge(rated_roster("", 80), 0, 1) == (0, 0)                             # off: no edge at all
    assert edge(rated_roster("", 70)) == (0, 0)
    monkeypatch.setattr(T, "FR_TEAM_EDGE", (5, 2))
    assert bound(own=rated_roster("", 55), opponent=rated_roster("O", 55)).team_edge(1, 2) == 0       # equal teams, whatever the level


def test_the_edge_is_added_to_every_plays_gap_and_moves_the_rows_like_a_gap(calibrated):
    stronger = rated_roster("", 80)                                               # a team 10 points better in every place
    even = rated_roster("O")
    m = bound(carrier=3, d1=5, d2=9, own=stronger, opponent=even, offense_play=1)
    assert m.gap("run") == 10 + 25                                                # the carrier's 80 against the two tacklers' 70, plus 2.5 x 10
    assert m.mod_for("run") == PD.Mod(1, 1, -3, 3, 3)                             # saturated at the caps
    behind = bound(carrier=3, d1=5, d2=9, own=even, opponent=stronger, offense_play=1)
    assert behind.gap("run") == -10 - 25 and behind.mod_for("run") == PD.Mod(-1, -1, 3, -3, -3)
    flat = bound(carrier=3, d1=5, d2=9, own=rated_roster("", 70), opponent=rated_roster("O", 70))
    assert flat.gap("run") == 0 and flat.mod_for("run") is None                  # neutral ratings are the original's


def test_the_player_in_the_play_still_counts_with_the_edge(calibrated):
    """A weak carrier of a team that is weaker only by him: his rating is what the play is about, the edge a little more."""
    own = rated_roster("", 70, rb1=40)                                           # the weighted sum is 60 lower: an edge of 2.5 x -0.77 = -2
    m = bound(carrier=1, d1=1, d2=2, own=own, opponent=rated_roster("O"), offense_play=1)
    assert m.team_edge(1, 2) == -2 and m.gap("run") == (40 - 70) - 2
    other = bound(carrier=2, d1=1, d2=2, own=own, opponent=rated_roster("O"), offense_play=1)
    assert other.gap("run") == -2                                                 # another back of the same team: only the edge


# ----- SX.8o: the kick-off return reads the receiving side's returner through H8 (the mutation check's survivors) -----

def test_the_kick_off_return_asks_h8_for_the_receiving_sides_returner(tmp_path):
    rig = rated_engine(tmp_path, rated_roster("", 70), rated_roster("O", 70), offense_play=0, defense_play=1)
    asked = []

    def shortest(side, returner):
        asked.append((side, returner))
        return 200                                                     # far past any return of the original: the engine adds what H8 gives
    rig.rules.modifiers.return_shortest = shortest
    from randsources import ScriptedRandom
    rig.rnd.source = ScriptedRandom(seed=7)                          # the return's own draws from a seeded source (their values do not matter here)
    s = rig.engine.s
    s.wisoff, s.defense, s.returner = 2, 1, 2                          # the receivers are side 2, their second returner runs it back
    rig.engine.kick_return()
    assert asked == [(2, 2)] and s.yards >= 200
