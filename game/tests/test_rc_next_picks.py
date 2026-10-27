"""The picks of the draft after the coming one are tradeable: in a franchise's first season the 2028 draft (nfl4 only, rule 0.13; RC, D-197). This is
inspired by Jim Kitchen.

The owner on 0.16.9: "Add the following year 2028 nfl draft picks and make them tradeable as well. you must implement this into the game before making
the new installer." A franchise's first season is 2026: its coming draft is the 2027 draft, and the one after it the 2028 draft. Such a pick is
(round, the team whose pick it is, NEXT); its owner lives in `future_picks` ([season + 1, round, team, owner], the exceptions only), it is worth
FR_TRADE_NEXT_SHARE percent of the same round's pick of the coming draft, it is offered after the coming draft's picks, saves and loads, passes the
whole-file checks, is said with its year, and at the new season joins the coming draft's table for its owner.
"""
import random

import pytest
from drrig import SURNAMES

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import tags
from nfl4.extras.franchise import trade_flow as TF
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.history import Words
from nfl4.extras.franchise.league import SEASON, LeagueError, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5
A, B = 4, 9


def league_in_season(seed=3):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")
    for p in league.players.values():
        p.rating = p.peak = 60
        p.age, p.potential = 25, "average"
        p.salary, p.years = CT.market_salary(p.pos, 60), 2
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    league.stage, league.gtp = SEASON, 1
    return league


def quarterback(league, team):
    return league.player_at(team, D.PLACES_OF["QB"][0])


def test_a_team_owns_its_seven_picks_of_the_next_draft_after_the_coming_ones():
    league = league_in_season()
    picks = TR.picks_of(league, A)
    assert picks[:7] == [(r, A) for r in range(1, 8)]
    assert picks[7:] == [(r, A, TR.NEXT) for r in range(1, 8)]
    assert TR.value_of((1, A, TR.NEXT), "middle") == T.FR_TRADE_PICK_VALUE[0] * T.FR_TRADE_NEXT_SHARE // 100
    assert TR.value_of((1, A, TR.NEXT), "middle") < TR.value_of((1, A), "middle")


def test_a_next_pick_moves_with_a_trade_saves_loads_and_passes_the_checks():
    league = league_in_season()
    a, b = quarterback(league, A), quarterback(league, B)
    trade = TR.Trade(A, B, a.id, b.id, ((2, A, TR.NEXT),), ((1, B),))
    assert TR.problems(league, trade, 5) is None                           # the team owns it: nothing stops the trade
    TR.execute(league, trade, 5, TR.KIND_COMPUTER)
    assert TR.owner_next(league, 2, A) == B and TR.owner(league, 1, B) == A
    assert league.future_picks == [[league.season + 1, 2, A, B]]
    assert (2, A, TR.NEXT) in TR.picks_of(league, B) and (2, A, TR.NEXT) not in TR.picks_of(league, A)
    assert league.trades["log"][-1][5] == [[2, A, TR.NEXT]]
    league.check()
    again = LeagueRecord.from_json(league.to_json())
    assert again.future_picks == league.future_picks and again.trades == league.trades
    again.check()
    TR.move_pick(league, (2, A, TR.NEXT), A)                                # traded back: the row leaves the table
    assert league.future_picks == [] and TR.owner_next(league, 2, A) == A


def test_a_damaged_next_pick_is_refused_by_the_check():
    league = league_in_season()
    league.future_picks = [[league.season + 1, 8, A, B]]                    # a round the draft has not
    with pytest.raises(LeagueError):
        league.check()
    league.future_picks = []
    league.trades["log"].append([5, A, B, quarterback(league, A).id, quarterback(league, B).id, [[1, A, 2]], [], TR.KIND_COMPUTER])
    with pytest.raises(LeagueError):
        league.check()


def test_at_the_new_season_a_next_pick_joins_the_coming_drafts_table_for_its_owner():
    league = league_in_season()
    TR.move_pick(league, (3, A, TR.NEXT), B)
    league.season += 1                                                      # stage 6: the new season, then the picks owed join its draft
    tags.move_future(league)
    assert league.future_picks == [] and TR.owner(league, 3, A) == B
    assert (3, A) in TR.picks_of(league, B) and (3, A) not in TR.picks_of(league, A)


def test_the_coming_drafts_picks_come_first_and_a_next_pick_covers_what_they_cannot():
    gap = TR.value_of((1, A, TR.NEXT), "middle")
    assert TR.cover(gap, [(2, A), (1, A, TR.NEXT)], "middle") == ((2, A),)                 # the computer's calibrated trades keep their picks
    assert TR.cover(gap, [(7, A), (1, A, TR.NEXT)], "middle") == ((1, A, TR.NEXT),)        # a seventh cannot: the next draft's first can
    assert TR.cover(gap, [(7, A)], "middle", limit=1) is None


def test_a_next_pick_is_said_with_its_year():
    league = league_in_season()
    words = Words(lambda t: {A: "Bears", B: "Lions"}.get(t, "Team%d" % t), lambda: league)
    assert TF.pick_text(words, (2, A, TR.NEXT), A, A) == X.text("NXX-P08", round=2, year=2028)
    assert "2028" in TF.pick_text(words, (2, A, TR.NEXT), A, A)
    assert TF.pick_text(words, (3, B, TR.NEXT), B, A) == X.text("NXX-P09", round=3, year=2028)
    assert TF.pick_text(words, (1, B, TR.NEXT), A, TEAM) == X.text("NXX-P07", round=1, year=2028, team="Lions")
    assert TF.pick_text(words, (2, A), A, A) == X.text("NXX-P04", round=2)          # the coming draft's picks are said as before
    league.season = 3                                                               # the 2028 season: the draft after the coming one is 2030
    assert "2030" in TF.pick_text(words, (2, A, TR.NEXT), A, A)


def test_the_tag_rule_still_sees_a_first_round_pick_owed_a_year_ahead():
    league = league_in_season()
    assert tags.owns_both_firsts(league, A)
    TR.move_pick(league, (1, A, TR.NEXT), B)
    assert not tags.owns_both_firsts(league, A)
