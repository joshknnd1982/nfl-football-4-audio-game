"""Free agents the player signs in the regular season, and the trade deadline (nfl4 only, rule 0.13; SZ.8, D-120). This is inspired by Jim Kitchen.

A player wrote (2026-10-22): "You can't sign free agents or do trades." In the season F9's free agents item said "the market is closed" and trades closed at the deadline with
nothing said before it. Now: the rules of `signings.py` (the pool, a signing with a release, the cap), the menu on the program rig, and the trade window (the deadline of the
calendar, free agency of the offseason, the sentences about the deadline in the news). The offseason's market is test_fr_market*.py, the trades test_fr_trades.py and test_fr_trade_flow.py.
"""
import copy
import random

import pytest
from drrig import SURNAMES, at_stage, draft_league, full_league, offseason_rig
from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until, spoken)

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import market as M
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import OFFSEASON, SEASON, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5
FREE_AGENTS = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 6 + [ENTER]          # F9, Franchise, free agents (the 7th item)
TRADES = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 7 + [ENTER]               # and trades (the 8th)


def fresh(seed=3, team=TEAM):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")
    league.stage, league.gtp = SEASON, 1
    return league


def full(seed=3, team=TEAM):
    """SR.5: a league of full teams (53 men, drrig.full_league) in week 1: a signing needs a release, as the season's whole places did."""
    league = full_league(seed, team)
    league.stage, league.gtp = SEASON, 1
    return league


def quarterback(league, team=TEAM):
    return league.player_at(team, D.PLACES_OF["QB"][0])


# ----- the pool -----

def test_the_pool_is_three_veterans_for_every_group_made_from_the_league_and_not_from_the_games_draws():
    league = fresh()
    assert S.pool(league) == []
    made = S.ensure_pool(league, SURNAMES)
    assert made == 3 * len(D.ROSTER_ORDER) == len(S.pool(league))                 # SR.5: the 11 families (the line and the snapper too)
    for position in D.ROSTER_ORDER:
        assert len(S.pool_of(league, position)) == 3
    for p in S.pool(league):
        assert p.status == "free" and p.team == 0 and p.left == 0 and p.place == -1 and p.salary == p.years == 0
        assert 58 <= p.rating <= 69 and 27 <= p.age <= 33 and p.potential == "low"
    assert S.ensure_pool(league, SURNAMES) == 0                                      # whole: nothing more is made
    names = [p.name for p in league.players.values()]
    assert len(names) == len(set(names))                                             # a veteran never has the name of a player of the league
    again = fresh()
    S.ensure_pool(again, SURNAMES)
    assert [(p.name, p.pos, p.rating, p.age) for p in S.pool(again)] == [(p.name, p.pos, p.rating, p.age) for p in S.pool(league)]   # the same men each time
    league.check()                                                                   # a whole record


def test_the_pool_is_the_best_first_and_is_no_part_of_the_offseasons_market_or_of_next_year(monkeypatch):
    league = fresh()
    S.ensure_pool(league, SURNAMES)
    ratings = [(-S.R.value(p)[0]) for p in S.pool(league)]
    assert ratings == sorted(ratings, reverse=True)
    league.stage, league.stage_no = OFFSEASON, D.STAGE_FREE_AGENCY
    assert M.pool(league) == []                                                      # the veterans have left = 0: no market sees them
    kept = aging.drop_the_unkept(league)
    assert kept == 3 * len(D.ROSTER_ORDER) and S.pool(league) == []                 # SR.5: the 11 families                     # stage 6 drops them like the released


def test_a_player_the_player_released_is_a_free_agent_of_the_season_and_of_the_offseason_market():
    league = fresh()
    S.ensure_pool(league, SURNAMES)
    old = quarterback(league)
    new = S.pool_of(league, "QB")[0]
    S.sign(league, new, old, 1)
    assert old in S.pool(league) and old.status == "free" and old.left == league.season and old.team == 0
    league.stage, league.stage_no = OFFSEASON, D.STAGE_FREE_AGENCY
    assert old in M.pool(league)                                                     # he is on the market of this offseason too


# ----- a signing -----

def test_a_signing_needs_a_release_when_the_group_is_full_and_makes_dead_money_and_a_whole_record():
    league = full()                                                                  # SR.5: a team of 53 has no room
    S.ensure_pool(league, SURNAMES)
    old, new = quarterback(league), S.pool_of(league, "QB")[0]
    assert not S.open_place(league, TEAM, "QB") and S.problems(league, new, None, 1) == "no place and no release"
    assert S.problems(league, new, old, 1) is None
    before = CT.cap_used(league, TEAM)
    salary, years = S.price(new)
    dead = CT.dead_money(old)
    expected = before - old.salary + dead + salary
    assert dead > 0 and S.cap_after(league, TEAM, new, old) == expected
    paid = S.sign(league, new, old, 1)
    assert paid == (salary, years, dead) and league.dead[TEAM - 1] == dead
    assert new.status == "active" and new.team == TEAM and (new.salary, new.years) == (salary, years)
    assert new.id in league.chart[TEAM - 1][new.position] and RR.roster_count(league, TEAM) == D.ROSTER_MAX      # SR.5: he joins the chart, the 53 stay 53
    assert quarterback(league) is max((p for p in RR.members(league, TEAM) if p.pos == "QB"), key=lambda p: (p.rating, -p.id))   # the best plays
    assert old.status == "free" and old.place == -1 and old.salary == old.years == 0
    assert CT.cap_used(league, TEAM) == expected
    league.check()


def test_a_signing_into_an_open_place_releases_nobody(monkeypatch):
    league = full()
    S.ensure_pool(league, SURNAMES)
    runner = [p for p in RR.members(league, TEAM) if p.pos == "RB"][-1]               # (a back place may be empty: the men, not the places)
    RR.leave(league, runner, "free")                                                 # SR.5: a spot free on the 53 (the chart's next man takes the place)
    runner.left, runner.salary, runner.years, runner.team = 0, 0, 0, 0
    new = S.pool_of(league, "RB")[0]
    assert S.open_place(league, TEAM, "RB") and S.problems(league, new, None, 1) is None
    assert S.problems(league, new, league.player_at(TEAM, D.PLACES_OF["RB"][0]), 1) == "a release with an open place"
    S.sign(league, new, None, 1)
    assert new.status == "active" and league.dead[TEAM - 1] == 0 and not S.open_place(league, TEAM, "RB")


def test_a_signing_that_breaks_a_rule_is_refused_with_the_reason():
    league = full()                                                                  # SR.5: a full 53, so a release is asked for
    S.ensure_pool(league, SURNAMES)
    old, new = quarterback(league), S.pool_of(league, "QB")[0]
    assert S.problems(league, new, old, 20) == "outside the regular season"          # the play-offs (week 19 and on)
    league.stage = OFFSEASON
    assert S.problems(league, new, old, 1) == "outside the regular season"
    league.stage = SEASON
    assert S.problems(league, old, old, 1) == "a player who is not a free agent"
    other = next(p for p in league.group_of(TEAM, "WR") if p is not None)
    assert S.problems(league, new, other, 1) == "a release who is not a player of the group"
    wrong = S.pool_of(league, "WR")[0]
    assert S.problems(league, wrong, old, 1) == "a release who is not a player of the group"


def test_a_hurt_player_cannot_be_released_and_the_cap_holds(monkeypatch):
    from nfl4.extras.franchise import injuries
    league = full()                                                                  # SR.5: a full 53, so a release is asked for
    S.ensure_pool(league, SURNAMES)
    old, new = quarterback(league), S.pool_of(league, "QB")[0]
    kind = next(iter(injuries.KIND_IDS))
    injuries.injure(league, old.id, kind, 3, 0, 1)
    releasable = S.releasable(league, TEAM, "QB", 1)
    assert S.problems(league, new, old, 1) == "a release who is hurt" and old not in releasable
    assert releasable == [p for p in RR.members(league, TEAM) if p.pos == "QB" and p is not old]      # SR.5: the team has two quarterbacks; the fit one may go
    league.injuries["hurt"].clear()
    limit = CT.cap_used(league, TEAM) + S.price(new)[0] - old.salary + CT.dead_money(old) - 1                                 # one tenth over
    monkeypatch.setattr(T, "FR_CAP", limit - T.FR_CAP_ROSTER)                        # SR.5: the cap is FR_CAP + FR_CAP_ROSTER (contracts.cap_of)
    assert S.problems(league, new, old, 1) == "over the cap"
    monkeypatch.setattr(T, "FR_CAP", T.FR_CAP + 1)
    assert S.problems(league, new, old, 1) is None


def test_releasing_a_man_ends_his_open_trade_demand_and_the_question_about_him():
    from nfl4.extras.franchise import people
    league = fresh()
    S.ensure_pool(league, SURNAMES)
    old, new = quarterback(league), S.pool_of(league, "QB")[0]
    league.people["demands"].append([old.id, TEAM, 1, people.OPEN])
    league.todo.append({"kind": D.TODO_DEMAND, "season": 1, "week": 1, "state": 0, "demand": [old.id, []]})
    S.sign(league, new, old, 1)
    assert league.people["demands"][0][3] == people.ENDED and not league.todo
    league.check()


# ----- the menu on the program rig -----

def test_f9_free_agents_in_the_season_signs_a_quarterback_and_writes_before_it_tells(tmp_path):
    # SR.5: the rig's new franchise is a drawn league of 34 men a team, so the team has room on its 53: no release is asked (sign, the group, the man, Enter)
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + FREE_AGENTS + [ENTER] * 4, policy=quit_policy)
    run_until(rig)
    league = rig.fstore.league
    text = spoken(rig)
    assert any(t.startswith(" free agents. you can sign a player any week") for t in text)
    signed = [t for t in text if t.startswith(" you signed ")]
    assert len(signed) == 1 and not [t for t in text if t.startswith(" you released ")]
    new = next(p for p in RR.members(league, league.team) if p.salary > 0 and " you signed %s, " % p.name in signed[0])
    assert new.pos == "QB" and new.status == "active" and new.id in league.chart[league.team - 1]["QB"]
    assert league.dead[league.team - 1] == 0
    assert league.trades["log"] == [] and S.pool_of(league, "QB") and rig.fstore.files.data["league.sav"]                                # written


def quarterback_of(league):
    return league.player_at(league.team, D.PLACES_OF["QB"][0])


def test_the_confirmation_says_no_to_a_signing_with_escape_and_changes_nothing(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + FREE_AGENTS + [ENTER] * 3 + [ESC], policy=quit_policy)    # SR.5: no release asked (room on the 53)
    run_until(rig)
    league = rig.fstore.league
    before = quarterback_of(league)
    assert before.status == "active" and not [p for p in league.players.values() if p.status == "free" and p.team == league.team]
    assert any(t.startswith(" you did not sign ") for t in spoken(rig))


def test_f9_free_agents_in_the_offseason_says_the_market_is_closed_and_in_the_stage_it_lists_the_market(tmp_path):
    league = draft_league(stage_no=D.STAGE_DRAFT, team=TEAM)
    rig = offseason_rig(tmp_path, league, keys=FREE_AGENTS + [ESC] * 4, until=lambda r: X.text("NXJ-H01") in spoken(r), picks_told="mine")
    assert X.text("NXJ-H01") in spoken(rig)
    assert "sign free agents again in the regular season" in X.text("NXJ-H01")


def test_the_free_agents_cannot_be_signed_in_the_play_offs_inside_a_game_or_in_the_offseason():
    from nfl4.extras.franchise import signings_flow

    class Idle:
        play_engine = None

    class Busy:
        play_engine = object()
    league = fresh()
    league.prepared = [league.season, league.gtp]                                        # the week is prepared
    assert signings_flow.closed_reason(Idle(), league) is None
    assert signings_flow.closed_reason(Busy(), league) == X.text("NXJ-S13")
    league.gtp = 17                                                                  # the original's wild card week
    assert signings_flow.closed_reason(Idle(), league) == X.text("NXJ-S12")
    league.stage = OFFSEASON
    assert signings_flow.closed_reason(Idle(), league) == X.text("NXJ-H01")


# ----- the trade window -----

def test_the_deadline_is_the_kick_off_of_week_9_of_the_originals_16_weeks_and_of_week_10_of_the_calendar():
    league = fresh()
    assert TR.last_week(league) == 9
    assert TR.in_window(league, 9) and not TR.in_window(league, 10)
    league.calendar = {"label": "x", "weeks": [[] for _ in range(18)]}
    assert TR.last_week(league) == 10 and TR.in_window(league, 10) and not TR.in_window(league, 11) and not TR.in_window(league, 0)


def test_trades_are_open_from_free_agency_to_week_1_and_closed_in_the_earlier_stages_of_the_offseason():
    """D-130 (the owner's answer to Q-063): open in free agency, before the draft, after it, after the roster cut and before week 1; closed while the
    draft runs and while the cut is decided (test_trades_window_d130.py has the rest)."""
    league = fresh()
    league.stage = OFFSEASON
    for stage in (D.STAGE_REVIEW, D.STAGE_STAFF, D.STAGE_AGING, D.STAGE_DEVELOPMENT, D.STAGE_CONTRACTS):
        league.stage_no = stage
        assert not TR.in_window(league, 0), stage
    for stage in (D.STAGE_FREE_AGENCY, D.STAGE_DRAFT, D.STAGE_CUT, D.STAGE_NEW_SEASON):
        league.stage_no = stage
        assert TR.in_window(league, 0) and not TR.in_window(league, 1), stage
    league.stage_no = D.STAGE_DRAFT
    league.draft = {"x": 1}
    assert not TR.in_window(league, 0)                                                # the draft has begun: its picks are the draft's


def test_a_trade_of_the_offseason_is_made_and_logged_as_week_0_and_the_log_passes_the_check():
    league = fresh()
    league.stage, league.stage_no = OFFSEASON, D.STAGE_FREE_AGENCY
    a, b = TEAM, 9
    qa, qb = quarterback(league, a), quarterback(league, b)
    qa.rating = qa.peak = 70
    qb.rating = qb.peak = 70
    trade = TR.Trade(a, b, qa.id, qb.id, (), ())
    assert TR.problems(league, trade, 0) is None
    TR.execute(league, trade, 0, TR.KIND_PLAYER)
    assert quarterback(league, a).id == qb.id and quarterback(league, b).id == qa.id and league.trades["log"][0][0] == 0
    league.check()


def test_the_news_says_where_trades_and_free_agents_are_at_week_1_and_the_deadline_in_the_weeks_around_it():
    league = fresh()
    assert TR.notice_id(league, 1) == "NXX-30" and TR.notice_id(league, 2) is None
    assert [TR.notice_id(league, w) for w in (7, 8, 9, 10, 11)] == [None, "NXX-31", "NXX-32", "NXX-33", None]          # the original's 16 weeks: the deadline is week 9
    league.calendar = {"label": "x", "weeks": [[] for _ in range(18)]}
    assert [TR.notice_id(league, w) for w in (8, 9, 10, 11, 12)] == [None, "NXX-31", "NXX-32", "NXX-33", None]


def test_the_notices_are_told_once_in_their_week_with_the_news_and_not_again_on_f1(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: rig.game.season.gtp == 11))
    run_until(rig)
    text = spoken(rig)
    assert text.count(X.text("NXX-30", n=9)) == 1                                     # week 1: where trades and free agents are, and the deadline (week 9 of the original's 16)
    assert text.count(X.text("NXX-31")) == 1 and text.count(X.text("NXX-32")) == 1 and text.count(X.text("NXX-33")) == 1
    order = [text.index(X.text(i)) for i in ("NXX-31", "NXX-32", "NXX-33")]
    assert order == sorted(order)                                                     # next week, the last week, passed
    def week_line(n):
        return next(i for i, t in enumerate(text) if t.startswith(" This is week  %d of " % n))
    assert week_line(8) < order[0] < week_line(9) < order[1] < week_line(10) < order[2]


# ----- what the independent review of SZ.8 found -----

def test_a_released_player_has_no_team_so_the_market_that_signs_him_earns_nobody_a_compensatory_pick():
    from nfl4.extras.franchise import comp
    league = fresh()
    S.ensure_pool(league, SURNAMES)
    old, new = quarterback(league), S.pool_of(league, "QB")[0]
    S.sign(league, new, old, 1)
    assert old.team == 0 and old in S.pool(league)
    league.stage, league.stage_no, league.market = OFFSEASON, D.STAGE_FREE_AGENCY, M.begin()
    league.stage_no = D.STAGE_FREE_AGENCY
    assert old in M.pool(league)
    gone = quarterback(league, 9)                                                       # team 9 has an open place at quarterback
    league.rosters[8][gone.place] = 0
    gone.status, gone.place, gone.left, gone.salary, gone.years = "free", -1, league.season, 0, 0
    bid = M.make_bid(league, 9, old, M.price(old, 1)[0], M.price(old, 1)[1])
    result = M.resolve(league, [bid], 1)
    assert result.signed and result.moves == []                                         # nobody lost him: no move, no pick
    league.market = None
    assert comp.award(league, result.moves) == []
    league.market = M.begin()
    league.market["moves"] = result.moves
    league.check()


def test_the_start_up_menu_cannot_write_the_default_season_over_the_league(tmp_path):
    from nfl4.extras.franchise.store import FranchiseStore
    from nfl4.extras.franchise.files import MemoryFiles
    from nfl4.game.season import SeasonState
    league = fresh()
    league.team, league.gtp = 24, 1
    store = FranchiseStore(MemoryFiles())
    store.league = league
    season = SeasonState()                                                              # the defaults the Game holds before a season is loaded: team 1, week 1, nothing played
    store.bind(season)
    store.sync()
    assert league.team == 24                                                            # an F9 save at the start-up menu changes nothing
    store.write_gtp(1)                                                                  # the engine wrote: its state is the season now
    assert league.team == 1 and store.season_current
    store.unbind()
    assert not store.season_current


def test_free_agents_wait_until_the_week_is_prepared_so_the_results_of_the_week_before_do_not_let_an_unsettled_injury_through():
    from nfl4.extras.franchise import signings_flow

    class Idle:
        play_engine = None
    league = fresh()
    league.prepared = [league.season, league.gtp]
    assert signings_flow.closed_reason(Idle(), league) is None
    league.gtp = 2                                                                      # the week counter moved on; the preparation of week 2 has not run
    assert signings_flow.closed_reason(Idle(), league) == X.text("NXJ-S19")
    league.prepared = [league.season, 2]
    assert signings_flow.closed_reason(Idle(), league) is None


def test_the_tagged_player_cannot_be_traded_while_his_offer_sheet_waits():
    league = fresh()
    league.stage, league.stage_no = OFFSEASON, D.STAGE_FREE_AGENCY
    a, b = TEAM, 9
    qa, qb = quarterback(league, a), quarterback(league, b)
    qa.rating = qa.peak = qb.rating = qb.peak = 70
    trade = TR.Trade(a, b, qa.id, qb.id, (), ())
    assert TR.problems(league, trade, 0) is None
    league.tags["open"] = [qa.id, 50, 1]
    assert TR.problems(league, trade, 0) == "a player under the non-exclusive tag"


def test_in_the_offseason_only_the_offseasons_own_trades_stop_a_second_trade_of_the_same_player():
    league = fresh()
    a, b = TEAM, 9
    qa, qb = quarterback(league, a), quarterback(league, b)
    league.trades["log"].append([5, a, b, qa.id, qb.id, [], [], TR.KIND_PLAYER])        # a trade of the finished regular season
    assert TR.traded_this_season(league) == {qa.id, qb.id}
    league.stage, league.stage_no = OFFSEASON, D.STAGE_FREE_AGENCY
    assert TR.traded_this_season(league) == set()                                       # the season's log is history in the offseason's window
    league.trades["log"].append([0, a, b, qa.id, qb.id, [], [], TR.KIND_PLAYER])
    assert TR.traded_this_season(league) == {qa.id, qb.id}


def test_the_injury_report_of_a_bye_week_names_no_stand_in_because_nobody_plays(shipped_calendar):
    from nfl4.extras.franchise import injury_flow, injuries
    from nfl4.extras.franchise.history import Words
    league = fresh(team=1)                                                              # the Bengals: their bye is week 6
    league.calendar = {"label": "x", "weeks": shipped_calendar.to_rows()}
    qb = quarterback(league, 1)
    injuries.injure(league, qb.id, next(iter(injuries.KIND_IDS)), 4, 0, 5)
    injuries.settle(league, 6, GameRandom(random.Random(2)), SURNAMES)                  # the group has nobody fit: a stand-in is made
    words = Words(lambda team: "team %d" % team)
    league.gtp = 6
    on_bye = injury_flow.report_lines(league, 6, [], words, None, GameRandom(random.Random(3)))
    league.calendar = None
    played = injury_flow.report_lines(league, 6, [], words, None, GameRandom(random.Random(3)))
    assert len(played) == len(on_bye) + 1 and any("fills in" in line for line in played) and not any("fills in" in line for line in on_bye)


@pytest.fixture(scope="module")
def shipped_calendar():
    from nfl4.extras.franchise import fixtures
    return fixtures.load_file(fixtures.shipped_path(2026))
