"""The playbooks' modifiers (H8): the bounds, the rows they move and the engine reading them (nfl4 only, rule 0.13;
NFL_EXTRAS_DESIGN 10.3, PX SX.7). This is inspired by Jim Kitchen.

Every expected number is worked out from the rule next to it (B-X38); the engine tests plan their draws on a strict scripted
source in the order of design 15.
"""
import pytest

from nfl4.extras import playbook_data as D
from nfl4.extras import playbooks as PB
from nfl4.extras.nfl_rules import NflRules
from nfl4.game.playtables import NEUTRAL, PASSES, RUNS, PassEntry, QBRunEntry, RunEntry
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from test_nx_qb_plays import after_play
from test_pag_scrimmage import first_handoff, quiet_snap_count
from nxdraws import nfl_snap_draws as snap_draws, tackle_value      # NX-D2: the N. F. L. rules draw by the usage shares

TABLE = PB.DEFAULT_TABLE
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)


def armed(mod):
    m = PB.PlaybookModifiers()
    m.arm(mod)
    return m


# ----- the door -----

def test_unarmed_modifiers_and_a_zero_mod_return_every_row_unchanged_like_neutral():
    run, passing = RUNS[(1, 3)], PASSES[(4, 4)]
    for m in (PB.PlaybookModifiers(), armed(D.ZERO), armed(None)):
        assert m.run(1, 3, run) is run and m.pass_(4, 4, passing) is passing and m.mod is None
        assert m.fumble_odds(1) == NEUTRAL.fumble_odds(1) == 50
        assert m.field_goal_odds(1) == NEUTRAL.field_goal_odds(1) and m.punt(1) == NEUTRAL.punt(1)


def test_a_run_row_moves_by_the_yards_and_keeps_its_sentences():
    m = armed(D.Mod(1, 2, 0, 0, 0))
    row = m.run(1, 3, RUNS[(1, 3)])                                  # plunge against the Long Run call: 0 to 7 (exclusive)
    assert (row.low, row.high) == (1, 9) and (row.key, row.direction, row.sound) == ("plunge_long_run", 3, 3)
    assert m.run(2, 2, RUNS[(2, 2)]) == RunEntry("end_short_run", 4, 3, -4, 2)      # -5 to 0 becomes -4 to 2


def test_a_row_never_has_no_yards_left_to_draw():
    narrow = RunEntry("k", None, 1, 0, 2)                              # 0 and 1 yard
    row = armed(D.Mod(2, -2, 0, 0, 0)).run(2, 1, narrow)              # low +2 and high -2 would cross: 2 to -2
    assert (row.low, row.high) == (2, 3)                              # one yard at least: Int(Rnd * 1) + low
    wide = armed(D.Mod(2, -2, 0, 0, 0)).run(2, 1, RUNS[(2, 1)])        # end run against the goal line: -3 to 3 becomes -1 to 1
    assert (wide.low, wide.high) == (-1, 1)


def test_a_pass_row_moves_by_yards_sack_and_catch_percent_within_zero_and_a_hundred():
    row = armed(D.Mod(0, 2, -3, 4, 0)).pass_(4, 4, PASSES[(4, 4)])    # short pass against the blitz: 5 to 50, sack 50, catch 70
    assert row == PassEntry(5, 52, 47, 74)
    low = armed(D.Mod(0, 0, -5, -5, 0)).pass_(3, 1, PASSES[(3, 1)])   # screen against the goal line: sack 5, catch 90
    assert (low.sack, low.complete) == (0, 85)
    assert armed(D.Mod(0, 0, 5, 5, 0)).pass_(5, 4, PASSES[(5, 4)]).sack == 65        # long pass against the blitz: 60 + 5
    capped = armed(D.Mod(0, 0, 0, 5, 0)).pass_(3, 1, PassEntry(-3, 10, 5, 98))
    assert capped.complete == 100                                    # never above a hundred


def test_the_fumble_denominator_moves_and_stays_a_real_chance():
    assert armed(D.Mod(0, 0, 0, 0, -5)).fumble_odds(1) == 45 and armed(D.Mod(0, 0, 0, 0, 5)).fumble_odds(2) == 55
    qb = QBRunEntry("keeper", 4, 3, -3, 6, 90)
    assert armed(D.Mod(1, -2, 0, 0, -5)).qb_run(qb) == QBRunEntry("keeper", 4, 3, -2, 4, 85)
    assert armed(D.Mod(0, 0, 0, 0, -99)).fumble_odds(1) >= 2         # an out-of-range value is never a zero or a negative draw


# ----- the plays' own tilts and the styles' (plays and styles made here, so a retune of the data does not move these) -----

def own_play(play_id="O900", family=1, rules=()):
    return D.Play(play_id, family, family, tuple(rules))


def own_book(tilts=None, key="mine"):
    return PB.StyleBook(key, "MIN", "NXM-28", {}, {}, dict(tilts or {}))


def test_a_plays_tilt_applies_only_against_the_calls_it_names():
    play = own_play(rules=[D.Rule((1, 2, 3), D.Mod(1, 1)), D.Rule((4, 5, 6), D.Mod(0, -2)), D.Rule((6,), D.Mod(0, 0, 3))])
    assert PB.play_mod(play, 3) == D.Mod(1, 1) and PB.play_mod(play, 5) == D.Mod(0, -2)
    assert PB.play_mod(play, 6) == D.Mod(0, -2, 3)                    # two rules that name the same call add
    assert PB.play_mod(own_play(), 1) == D.ZERO


def test_a_styles_tilt_adds_to_the_plays_for_its_families_and_calls_and_both_are_bounded():
    book = own_book({"OB1": D.Tilt((1,), (1, 2, 3), D.Mod(1, 1)), "OP1": D.Tilt((2,), (4,), D.Mod(0, 0, 2)),
                     "DB1": D.Tilt((4,), (1,), D.Mod(0, 0, 0, -3))})
    play = own_play(rules=[D.Rule((3,), D.Mod(1, 0))])
    assert PB.style_mod(book, "O", 1, 3) == D.Mod(1, 1)
    assert PB.style_mod(book, "O", 2, 3) == D.ZERO and PB.style_mod(book, "O", 1, 4) == D.ZERO     # another family, another call
    assert PB.style_mod(book, "O", 2, 4) == D.Mod(0, 0, 2)
    assert PB.style_mod(book, "D", 4, 1) == D.Mod(0, 0, 0, -3) and PB.style_mod(book, "O", 4, 1) == D.ZERO   # the sides are apart
    assert PB.side_mod(book, play, 3) == D.Mod(2, 1)                  # +1 of the play and +1 of the style, +1 yards high of the style
    heavy = own_play(rules=[D.Rule((3,), D.Mod(2, 2))])
    assert PB.side_mod(book, heavy, 3) == D.Mod(2, 2)                 # 3 and 3 are clamped to the bound 2
    assert PB.clamp(D.Mod(3, 3, 7, 7, 7)) == D.Mod(2, 2, 5, 5, 5) and PB.clamp(D.Mod(-3, -3, -7, -7, -7)) == D.Mod(-2, -2, -5, -5, -5)
    assert PB.style_mod(None, "O", 1, 3) == D.ZERO and PB.side_mod(book, None, 3) == D.ZERO


def test_the_two_plays_of_a_snap_add_and_the_sum_is_bounded_again():
    books = {"mine": own_book(), "theirs": own_book(key="theirs")}
    table = PB.Table({}, frozenset(), books, tuple(("classic", "classic") for _ in range(32)))
    offense = own_play("O900", 1, [D.Rule((1,), D.Mod(2, 2, -3, 3, 4))])                # a play the defense answers
    defense = own_play("D900", 1, [D.Rule((1,), D.Mod(-1, -1, 4, -5, -3))])             # a defense play: negative helps the defense
    assert PB.combined(table, "mine", offense, "theirs", defense, 1, 1) == D.Mod(1, 1, 1, -2, 1)       # each against the other's family
    assert PB.combined(table, "mine", offense, "classic", None, 1, 1) == D.Mod(2, 2, -3, 3, 4)
    assert PB.combined(table, "classic", None, "theirs", defense, 1, 1) == D.Mod(-1, -1, 4, -5, -3)
    assert PB.combined(table, "classic", None, "classic", None, 1, 1) == D.ZERO
    big = own_play("O901", 1, [D.Rule((1,), D.Mod(2, 2, 5, 5, 5))])
    big_defense = own_play("D901", 1, [D.Rule((1,), D.Mod(0, 0, 5, 0, 0))])
    assert PB.combined(table, "mine", big, "theirs", big_defense, 1, 1) == D.Mod(2, 2, 5, 5, 5)      # the sum 10 is clamped to 5
    assert PB.combined(table, "mine", offense, "theirs", defense, 2, 2) == D.ZERO                    # neither names the families 2 and 2


def test_a_style_that_is_not_in_the_table_moves_nothing():
    table = PB.DEFAULT_TABLE
    play = own_play(rules=[D.Rule((1,), D.Mod(1, 1))])
    assert PB.combined(table, "nonesuch", play, "nonesuch", None, 1, 1) == D.Mod(1, 1)               # the play's own tilt remains
    assert PB.combined(table, "nonesuch", None, "nonesuch", None, 1, 1) == D.ZERO


# ----- the engine reads the rows through the door -----

def book_rig(tmp_path, offense_book, defense_book, **kwargs):
    fields = dict(START)
    fields.update(kwargs)
    rules = NflRules(timeouts_on=False, offense_book=offense_book, defense_book=defense_book)
    return nfl_engine_rig(tmp_path, answers=[13] * 3, rules=rules, **fields)


def test_a_called_play_moves_the_row_the_engine_draws_its_yards_from(tmp_path, monkeypatch):
    play = own_play("O002", 1, [D.Rule((3,), D.Mod(1, 1))])           # +1 and +1 against the Long Run call
    book = PB.StyleBook("power", "POW", "NXM-31", {"O002": 5}, {}, {"OB1": D.Tilt((1,), (1, 2, 3), D.Mod(1, 1))})
    monkeypatch.setitem(D.PLAYS, "O002", play)
    rig = book_rig(tmp_path, "power", "classic", offense_play=1, defense_play=3)
    rig.game.playbook_table = PB.Table({}, frozenset(), {"power": book}, PB.DEFAULT_TABLE.teams)
    rig.rules.books.offense_id = "O002"                              # against the Long Run call: row 0 to 7, play and style +1 +1 each
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=1, d1=1, d2=2)
    first_handoff(d, group=1, phrase=1)
    d.rnd(3, 1).rnd(50, 1).below(7, 0)                                # the row is 2 to 9 (exclusive): width 7, draw 0 is 2 yards
    after_play(d, oob=99)
    assert run_steps(rig, rig.engine.snap, d) == "next_play"
    assert rig.engine.s.yard_line == 32 and rig.engine.s.stats[1].running_yards == 2
    assert rig.rules.modifiers.mod is None                            # the play is over: nothing stays armed


def test_the_fumble_chance_of_a_called_play_is_its_own_denominator(tmp_path, monkeypatch):
    play = own_play("O011", 2, [D.Rule((4,), D.Mod(0, 2, 0, 0, -2))])  # +2 yards high against the blitz, fumble 1 in 50 - 2 = 48
    book = PB.StyleBook("pro", "PRO", "NXM-28", {"O011": 5}, {}, {})
    monkeypatch.setitem(D.PLAYS, "O011", play)
    rig = book_rig(tmp_path, "pro", "classic", offense_play=2, defense_play=4)
    rig.game.playbook_table = PB.Table({}, frozenset(), {"pro": book}, PB.DEFAULT_TABLE.teams)
    rig.rules.books.offense_id = "O011"
    d = quiet_snap_count(Draws())
    snap_draws(d, carrier=1, d1=1, d2=2)
    first_handoff(d, group=1, phrase=1)
    d.below(4, 0).rnd(48, 13)                                         # the end run against the blitz: direction, then 13 of 48
    d.below(6, 0).below(40, 0)                                        # L of a turnover (5 to 10 seconds), the turnover spot
    run_steps(rig, rig.engine.snap, d)
    assert rig.engine.s.stats[1].fumbles_lost == 1


def test_the_ruling_reads_the_row_the_play_used_not_the_originals(tmp_path):
    from nfl4.extras.qb_runs import make_entry
    from nfl4.game import outcome as O
    rig = book_rig(tmp_path, "classic", "classic")
    review, modifiers = rig.rules.review, rig.rules.modifiers
    run = O.PlayOutcome(O.RUN, 1, 1, 3)
    assert review.row(rig.engine.s, run) == RUNS[(1, 3)]                      # nothing armed: the original's row
    modifiers.arm(D.Mod(1, 2, 0, 0, 0))
    assert review.row(rig.engine.s, run) == RUNS[(1, 3)]._replace(low=1, high=9)
    keeper = O.PlayOutcome(O.RUN, 1, 9, 5)
    entry = make_entry("keeper", 5)
    assert review.row(rig.engine.s, keeper) == entry._replace(low=entry.low + 1, high=entry.high + 2)
    passing = O.PlayOutcome(O.PASS_COMPLETE, 1, 4, 4)
    assert review.row(rig.engine.s, passing) == PASSES[(4, 4)]._replace(low=6, high=52)
    modifiers.arm(None)
