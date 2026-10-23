"""The trade window from free agency to the deadline (nfl4 only, rule 0.13; D-130, the owner's answer to Q-063: "Yes, open them"). This is inspired by Jim Kitchen.

Trades are open in the offseason from free agency on: before the draft, after it, after the roster cut and before week 1, as in the NFL; then in the regular
season up to the deadline. Closed while the draft is under way and while the roster cut is decided (the staff's plans of every team are made at the cut's
start). From the draft's first pick to week 1 a trade is player for player: the draft owns its picks, and the first-round picks owed for the next draft join
the table only at the new season.
"""
import random

from drrig import SURNAMES

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import trade_flow
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import OFFSEASON, SEASON, new_league
from nfl4.game.rnd import GameRandom

TEAM, OTHER = 5, 9


def offseason(stage_no, draft=None):
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, stage_no, 0, [8, 8] * 32
    league.draft = draft
    return league


def quarterback(league, team):
    return league.player_at(team, D.PLACES_OF["QB"][0])


class Game:
    play_engine = None


def test_the_window_is_open_from_free_agency_to_week_1_and_closed_during_the_draft_and_the_cut():
    for stage in (D.STAGE_FREE_AGENCY, D.STAGE_DRAFT, D.STAGE_CUT, D.STAGE_NEW_SEASON):
        assert TR.in_window(offseason(stage), 0), stage
    for stage in (D.STAGE_REVIEW, D.STAGE_STAFF, D.STAGE_AGING, D.STAGE_DEVELOPMENT, D.STAGE_CONTRACTS):
        assert not TR.in_window(offseason(stage), 0), stage
    during = offseason(D.STAGE_DRAFT, draft={"picks": []})
    assert not TR.in_window(during, 0) and TR.closed_in_offseason_moves(during)
    after = offseason(D.STAGE_CUT, draft={"picks": []})                       # the draft is over (stage 4 moved on), its record stays until the cut
    assert TR.in_window(after, 0) and not TR.closed_in_offseason_moves(after)
    after.cut_deciding = True
    assert not TR.in_window(after, 0) and TR.closed_in_offseason_moves(after)


def test_draft_picks_are_traded_in_the_season_and_before_the_draft_and_not_from_the_draft_to_week_1():
    assert TR.picks_open(offseason(D.STAGE_FREE_AGENCY)) and TR.picks_open(offseason(D.STAGE_DRAFT))
    assert not TR.picks_open(offseason(D.STAGE_CUT, draft={"picks": []}))
    assert not TR.picks_open(offseason(D.STAGE_NEW_SEASON))
    season = offseason(D.STAGE_FREE_AGENCY)
    season.stage, season.stage_no, season.gtp = SEASON, 0, 1
    assert TR.picks_open(season) and TR.picks_of(season, TEAM)
    assert TR.picks_of(offseason(D.STAGE_NEW_SEASON), TEAM) == []


def test_a_player_for_player_trade_is_made_after_the_draft_and_after_the_cut_and_the_league_stays_whole():
    for stage in (D.STAGE_CUT, D.STAGE_NEW_SEASON):
        league = offseason(stage)
        qa, qb = quarterback(league, TEAM), quarterback(league, OTHER)
        trade = TR.Trade(TEAM, OTHER, qa.id, qb.id)
        assert TR.problems(league, trade, 0) is None, stage
        TR.execute(league, trade, 0, TR.KIND_PLAYER)
        assert quarterback(league, TEAM).id == qb.id and league.trades["log"][-1][0] == 0
        league.check()


def test_a_trade_with_a_pick_is_refused_from_the_draft_to_week_1():
    league = offseason(D.STAGE_NEW_SEASON)
    qa, qb = quarterback(league, TEAM), quarterback(league, OTHER)
    assert TR.problems(league, TR.Trade(TEAM, OTHER, qa.id, qb.id, ((2, TEAM),), ()), 0) == "a pick the team does not own"


def test_the_other_teams_offer_and_answer_without_picks_after_the_draft():
    league = offseason(D.STAGE_NEW_SEASON)
    mine = quarterback(league, TEAM)
    for trade, _gain in TR.block_offers(league, TEAM, mine, league.records, 0):
        assert trade.picks_a == () and trade.picks_b == ()
    theirs = quarterback(league, OTHER)
    answer = TR.ask(league, TEAM, mine, theirs, league.records, 0)
    assert answer is None or (answer.picks_a == () and answer.picks_b == ())


def test_the_player_hears_why_trades_are_closed_and_why_no_picks_are_offered():
    league = offseason(D.STAGE_DRAFT, draft={"picks": []})
    assert trade_flow.closed_reason(Game(), league) == X.text("NXX-37")
    league = offseason(D.STAGE_CUT)
    league.cut_deciding = True
    assert trade_flow.closed_reason(Game(), league) == X.text("NXX-37")
    league.cut_deciding = False
    assert trade_flow.closed_reason(Game(), league) is None
    league = offseason(D.STAGE_AGING)
    assert trade_flow.closed_reason(Game(), league) == X.text("NXX-15", n=TR.last_week(league))
    assert "free agency" in X.text("NXX-15", n=9) and "week 9" in X.text("NXX-15", n=9)


def test_the_cut_flag_is_never_saved():
    league = offseason(D.STAGE_CUT)
    league.cut_deciding = True
    assert "cut_deciding" not in league.to_json()


def test_the_roster_cut_closes_the_trades_while_its_question_waits_and_opens_them_after(tmp_path):
    """On the program rig: the cut asks the player about his own team; trades are closed at that question and open at the stage's end."""
    from drrig import offseason_rig
    from test_fr_cut_flow import cut_league                                    # a whole draft made, the rookies waiting: the cut asks the player
    states = []

    def until(rig):
        league = rig.fstore.league if rig.fstore is not None else None
        if league is not None and league.stage == OFFSEASON:
            states.append((league.stage_no, league.cut_deciding, TR.in_window(league, 0)))
        return league is not None and league.stage == SEASON
    rig = offseason_rig(tmp_path, cut_league(), until=until, picks_told="mine")
    assert rig.fstore.league.stage == SEASON and not rig.fstore.league.cut_deciding
    assert any(deciding for _stage, deciding, _open in states)                    # the rig stood at the cut's own question
    assert all(not open_ for _stage, deciding, open_ in states if deciding)
    assert any(stage == D.STAGE_NEW_SEASON and open_ for stage, _deciding, open_ in states)
