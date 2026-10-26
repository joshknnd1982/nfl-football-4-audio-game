"""The Franchise's non-exclusive franchise tag (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8m, research B3, D-073): the prices (the cap percentage
average from the kept history, 120 percent, the market; the exclusive tag never under it), the offer sheet a computer team makes (an empty place, the room,
both first-round picks, the value of the two picks), keeping him at the offer or letting him go for the two first-round picks, the picks owed for the next
draft, the whole-file check, and stages 7 and 8 on the program rig.
"""
import pytest
from drrig import at_stage, draft_league, offseason_rig
from frrig import DOWN, ENTER, spoken
from test_fr_resign_flow import contract_league

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT, data as D, resign as R, tags, trades
from nfl4.extras.franchise.league import LeagueError, LeagueRecord, team_ref

TEAM = 5
BUYER = 9


# ----- the prices -----

def test_the_history_keeps_the_last_seasons_and_the_cap_average_is_their_mean():
    league = draft_league(seed=3, team=TEAM)
    now = tags.top_average(league, "QB")
    assert tags.cap_average(league, "QB") == now                      # no history yet: the average of now
    league.tags["history"]["QB"] = [100, 110, 120, 130]
    tags.record_history(league)
    assert league.tags["history"]["QB"] == [100, 110, 120, 130, now]
    tags.record_history(league)
    assert league.tags["history"]["QB"] == [110, 120, 130, now, now] and len(league.tags["history"]["QB"]) == T.FR_TAG_HISTORY
    assert tags.cap_average(league, "QB") == (110 + 120 + 130 + 2 * now + 2) // 5


def test_the_nonexclusive_price_is_the_highest_of_the_cap_average_120_percent_and_the_market_and_the_exclusive_is_never_under_it():
    league = draft_league(seed=3, team=TEAM)
    qb = league.player_at(TEAM, 33)
    league.tags["history"]["QB"] = [270] * 5
    raised = (qb.salary * T.FR_TAG_RAISE + 50) // 100
    assert tags.nonexclusive_salary(league, qb) == min(T.FR_MAX_SALARY, max(270, raised, CT.market_salary("QB", qb.rating)))
    assert R.tag_salary(league, qb) >= tags.nonexclusive_salary(league, qb)
    league.tags["history"]["QB"] = [10] * 5
    qb.salary = 200
    assert tags.nonexclusive_salary(league, qb) == max((200 * T.FR_TAG_RAISE + 50) // 100, CT.market_salary("QB", qb.rating))
    assert tags.nonexclusive_salary(league, qb) <= T.FR_MAX_SALARY


def test_stage_seven_keeps_the_history_once_when_it_begins():
    league = contract_league()
    before = {pos: list(v) for pos, v in league.tags["history"].items()}
    R.begin(league, False)
    assert all(len(league.tags["history"][pos]) == len(before.get(pos, [])) + 1 for pos in D.POSITIONS)


# ----- the offer sheet -----

def tagged_league(rating=78, buyer_open=True, mutate=None):
    """A league at the start of free agency with the player's quarterback under the non-exclusive tag and team BUYER's quarterback place empty.
    SR.5: the full teams of the real rosters (drrig.full_league, 53 men each), so only a team that let a man go has a spot for him (a drawn league of 34
    places has room on every 53)."""
    def change(league):
        qb = league.player_at(TEAM, 33)
        qb.rating = qb.peak = rating
        CT.sign(qb, tags.nonexclusive_salary(league, qb), 1)
        league.tags["open"] = [qb.id, league.season]
        if buyer_open:
            R.let_go(league, league.player_at(BUYER, 33))
            for player in league.active_of(BUYER):                      # the buyer has the room for an offer at the tag's price
                if player is not None:
                    player.salary = T.FR_MIN_SALARY
        if mutate is not None:
            mutate(league)
    return draft_league(seed=3, team=TEAM, stage_no=D.STAGE_FREE_AGENCY, wins=[8] * 32, finish=[D.FINISH_MISSED] * 32, mutate=change, real=True)


def test_a_team_with_an_empty_place_room_and_both_first_round_picks_makes_the_sheet_at_the_market_price_or_his_tag():
    league = tagged_league()
    qb = tags.tagged(league)
    price, years = CT.market_contract(qb)
    assert tags.offer_sheet(league) == (BUYER, max(price, qb.salary), years)


def test_no_sheet_without_an_empty_place_the_room_a_first_round_pick_or_enough_value():
    assert tags.offer_sheet(tagged_league(buyer_open=False)) is None
    poor = tagged_league(mutate=lambda lg: [setattr(p, "salary", T.FR_MAX_SALARY // 2) for p in lg.active_of(BUYER) if p is not None])
    assert tags.offer_sheet(poor) is None
    traded = tagged_league(mutate=lambda lg: trades.move_pick(lg, (1, BUYER), 20))
    assert tags.offer_sheet(traded) is None
    owed = tagged_league(mutate=lambda lg: lg.future_picks.append([lg.season + 1, 1, BUYER, 20]))
    assert tags.offer_sheet(owed) is None
    assert tags.offer_sheet(tagged_league(rating=58)) is None          # a quarterback worth less than two first-round picks


def test_of_two_teams_the_one_that_values_him_most_makes_the_sheet():
    def second_buyer(lg):
        R.let_go(lg, lg.player_at(12, 33))
        for player in lg.active_of(12):
            if player is not None:
                player.salary = T.FR_MIN_SALARY
    league = tagged_league(mutate=second_buyer)
    qb = tags.tagged(league)
    price, years = CT.market_contract(qb)
    salary = max(price, qb.salary)
    values = {t: tags.sheet_value(qb, salary, years, trades.situation(league.records, t)) for t in (BUYER, 12)}
    from nfl4.extras.franchise.market import tie_key
    best = min((BUYER, 12), key=lambda t: (-values[t], tie_key(t, qb.id)))
    assert tags.offer_sheet(league)[0] == best


def test_letting_him_go_moves_him_and_gives_the_two_first_round_picks():
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    tags.let_go(league, qb, team, salary, years)
    tags.close(league)
    assert (qb.team, qb.salary, qb.years) == (BUYER, salary, years) and league.player_at(BUYER, 33) is qb
    assert qb.id in league.chart[BUYER - 1]["QB"] and qb.id not in league.chart[TEAM - 1]["QB"]      # SR.5: his team's next quarterback takes the place
    assert trades.owner(league, 1, BUYER) == TEAM
    assert league.future_picks == [[league.season + 1, 1, BUYER, TEAM]]
    league.check()
    league.season += 1                                                 # stage 6: the pick owed joins the coming draft's table
    tags.move_future(league)
    assert league.future_picks == [] and [1, BUYER, TEAM] in league.trades["picks"]


def test_the_staff_matches_when_he_can_and_he_is_worth_the_picks():
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    assert tags.can_match(league, qb, salary)
    assert tags.should_match(league, qb, salary, years) == (tags.sheet_value(qb, salary, years, trades.situation(league.records, TEAM))
                                                            >= tags.picks_value(trades.situation(league.records, TEAM)))
    assert not tags.can_match(league, qb, T.FR_CAP)


def test_the_tags_are_checked_whole():
    league = tagged_league()
    league.check()
    good = LeagueRecord.from_json(league.to_json())
    qb_id = good.tags["open"][0]
    for change in (lambda lg: lg.tags.__setitem__("open", [qb_id, lg.season - 1]),
                   lambda lg: lg.tags.__setitem__("sheet", [TEAM, 100, 2]),
                   lambda lg: lg.tags["history"].__setitem__("QB", [1] * 6),
                   lambda lg: lg.future_picks.append([lg.season + 2, 1, 3, 4]),
                   lambda lg: lg.future_picks.append([lg.season + 1, 1, 3, 3]),
                   lambda lg: setattr(lg, "stage_no", D.STAGE_DRAFT)):
        bad = LeagueRecord.from_json(good.to_json())
        change(bad)
        with pytest.raises(LeagueError):
            bad.check()


# ----- stages 7 and 8 on the program rig -----

def test_the_talk_offers_the_nonexclusive_tag_and_taking_it_leaves_him_for_the_other_teams(tmp_path):
    league = contract_league()
    start = LeagueRecord.from_json(league.to_json())
    R.begin(start, False)                                              # (the talk's room as the stage will have it)
    qb = start.player_at(TEAM, 33)
    talk = R.Talk.start(qb, R.mood(start, TEAM))
    space = R.room(start, TEAM)
    kinds = [k for k, ok in (("sign", talk.ask <= space), ("less", R.lower_offer(talk.ask, talk.least) < talk.ask and R.lower_offer(talk.ask, talk.least) <= space),
                             ("tag", R.tag_salary(start, qb) <= space), ("open", tags.nonexclusive_salary(start, qb) <= space)) if ok]
    assert "open" in kinds
    price = tags.nonexclusive_salary(start, qb)
    rig = offseason_rig(tmp_path, league, keys=[DOWN] * kinds.index("open") + [ENTER], until=at_stage(D.STAGE_FREE_AGENCY), picks_told="mine")
    after = LeagueRecord.from_json(rig.kept[D.STAGE_FREE_AGENCY].decode("utf-8"))
    tagged = after.players[qb.id]
    assert after.tags["open"] == [qb.id, after.season] and (tagged.salary, tagged.years) == (price, 1)
    words_contract = X.text("NXA-11", salary=X.text("NXA-20", money=CT.millions(price)), y=1)
    assert X.text("NXU-57", player=qb.name, contract=words_contract) in spoken(rig)


def run_stage_eight(tmp_path, league, keys=(), **kwargs):
    return offseason_rig(tmp_path, league, keys=keys, until=at_stage(D.STAGE_DRAFT), picks_told="mine", **kwargs)


def answers(league):
    """The keys that choose "keep him" and "let him go" at the sheet's question (the staff's recommendation is the first answer)."""
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    keep_first = tags.should_match(league, qb, salary, years)
    return ([ENTER], [DOWN, ENTER]) if keep_first else ([DOWN, ENTER], [ENTER])


def after_stage(rig):
    return LeagueRecord.from_json(rig.kept[D.STAGE_DRAFT].decode("utf-8"))


def test_letting_him_go_at_the_sheet_gives_his_team_the_picks(tmp_path):
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    _keep, go = answers(league)
    rig = run_stage_eight(tmp_path, league, keys=go)
    after = after_stage(rig)
    moved = after.players[qb.id]
    assert moved.team == BUYER and (moved.salary, moved.years) == (salary, years)
    assert [1, BUYER, TEAM] in after.trades["picks"] and after.future_picks == [[after.season + 1, 1, BUYER, TEAM]]
    assert after.tags["open"] is None and after.tags["sheet"] is None
    assert any(t.startswith(" the ") and " make an offer for " in t for t in spoken(rig))
    assert X.text("NXU-54", player=qb.name, team=rig.game.league.team(*team_ref(BUYER))) in spoken(rig)


def test_keeping_him_at_the_sheet_pays_the_offer(tmp_path):
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    keep, _go = answers(league)
    rig = run_stage_eight(tmp_path, league, keys=keep)
    kept = after_stage(rig).players[qb.id]
    assert kept.team == TEAM and (kept.salary, kept.years) == (salary, years)
    assert after_stage(rig).future_picks == []


def test_with_the_staff_setting_on_the_staff_answers_the_sheet_by_its_recommendation(tmp_path):
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    keep = tags.should_match(league, qb, salary, years)
    rig = run_stage_eight(tmp_path, league, auto=True)
    moved = after_stage(rig).players[qb.id]
    assert moved.team == (TEAM if keep else BUYER)
    assert X.text("NXU-56", player=qb.name) in spoken(rig)


def test_when_no_team_makes_a_sheet_he_stays_on_the_tag(tmp_path):
    league = tagged_league(buyer_open=False)
    qb = tags.tagged(league)
    rig = run_stage_eight(tmp_path, league)
    after = after_stage(rig)
    assert after.players[qb.id].team == TEAM and after.players[qb.id].years == 1 and after.tags["open"] is None
    assert X.text("NXU-55", player=qb.name) in spoken(rig)


def test_stage_six_moves_the_pick_owed_into_the_coming_drafts_table(tmp_path):
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_NEW_SEASON)
    league.future_picks = [[league.season + 1, 1, BUYER, TEAM]]
    rig = offseason_rig(tmp_path, league)
    final = rig.fstore.league
    assert final.future_picks == [] and [1, BUYER, TEAM] in final.trades["picks"] and trades.owner(final, 1, BUYER) == TEAM


def test_an_offer_sheet_pays_at_least_his_tag_and_matching_what_costs_no_more_is_never_refused():
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    assert salary >= qb.salary
    for player in league.active_of(TEAM):
        if player is not None and player is not qb:
            player.salary = T.FR_MAX_SALARY                                  # his team is far over the cap
    assert tags.can_match(league, qb, qb.salary) and not tags.can_match(league, qb, qb.salary + 1)


def test_the_team_that_values_him_most_makes_the_sheet_whatever_its_number(monkeypatch):
    def second_buyer(lg):
        R.let_go(lg, lg.player_at(12, 33))
        for player in lg.active_of(12):
            if player is not None:
                player.salary = T.FR_MIN_SALARY
    league = tagged_league(mutate=second_buyer)
    how = {BUYER: "rebuild", 12: "contend"}
    monkeypatch.setattr(trades, "situation", lambda records, team: how.get(team, "middle"))
    monkeypatch.setattr(tags, "sheet_value", lambda player, salary, years, situation: {"rebuild": 500, "contend": 900}.get(situation, 0))
    assert tags.offer_sheet(league)[0] == 12
    how.update({BUYER: "contend", 12: "rebuild"})
    assert tags.offer_sheet(league)[0] == BUYER


def test_the_sheets_question_offers_the_staffs_recommendation_first(tmp_path):
    league = tagged_league()
    qb = tags.tagged(league)
    team, salary, years = tags.offer_sheet(league)
    keep = tags.should_match(league, qb, salary, years)
    rig = run_stage_eight(tmp_path, league, keys=[ENTER])
    first = X.text("NXU-A08") if keep else X.text("NXU-A09")
    assert any(t.strip() == "1. %s" % first for t in spoken(rig)), [t for t in spoken(rig) if t.strip().startswith("1.")][:3]
    moved = after_stage(rig).players[qb.id]
    assert moved.team == (TEAM if keep else BUYER)


def test_the_sheets_question_puts_letting_him_go_first_when_the_staff_would_let_him_go(tmp_path, monkeypatch):
    monkeypatch.setattr(tags, "should_match", lambda league, player, salary, years: False)
    league = tagged_league()
    qb = tags.tagged(league)
    rig = run_stage_eight(tmp_path, league, keys=[ENTER])
    assert any(t.strip() == "1. %s" % X.text("NXU-A09") for t in spoken(rig))
    assert after_stage(rig).players[qb.id].team == BUYER
