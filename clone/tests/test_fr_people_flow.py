"""The people's later items on the program rig (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8n, D-074): the holdout question at camp (asked before the camp's
focus, the staff's recommendation first, every answer a different league (B-X84), written before it is told, a window closed at the question, the staff
setting), a trade demand of the player's team in his to-do list (the staff's recommendation first, "later" trades nothing, the staff setting), the weekly game
goal before the kick-off and its verdict before the next menu, the talk's personality line and F9's roster words. The rules are test_fr_people.py.
"""
import pytest
from drrig import at_stage, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import people as P
from nfl4.extras.franchise import people_flow as PF
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.history import Words
from nfl4.extras.franchise.league import SEASON

TEAM = 5


@pytest.fixture(autouse=True)
def no_target(monkeypatch):
    """The staff's payroll target out of the way (a new league's contracts are all at the market price): the target's branch is test_fr_people.py's."""
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 1.0)


def make_holdout(league, team, age, word="money"):
    player = next(p for p in league.active_of(team) if p is not None and P.personality(p.id) == word)
    player.rating, player.age, player.seasons, player.years = 86, age, 4, 2
    player.salary = CT.market_salary(player.pos, 86) // 2
    return player


def camp_league(age=24, computer=True):
    holder = {}

    def mutate(league):
        holder["own"] = make_holdout(league, TEAM, age)
        if computer:
            holder["other"] = make_holdout(league, 9, 24)
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_DEVELOPMENT, mutate=mutate)
    return league, holder["own"], holder.get("other")


def prompt_of(league, player, words):
    salary, years = P.new_contract(player)
    return X.text("NXU-H01", player=player.name, position=words.position(player.pos), r=player.rating, contract=words.contract(player),
                  ask=words.contract_of(salary, years))


def test_the_holdout_is_asked_first_with_the_staffs_recommendation_and_enter_takes_it(tmp_path):
    league, own, other = camp_league(age=24)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS))
    text = spoken(rig)
    words = rig.fstore.words
    asked = text.index(prompt_of(league, own, words))
    assert text[asked - 1] == X.text("NXU-H06", n=1)                       # the other teams' holdouts are said with the question
    assert text[asked + 1].strip() == "1. %s" % X.text("NXU-H10").strip()   # young and the cap allows: "pay him" is the staff's recommendation
    camp = next(i for i, t in enumerate(text) if t.startswith(" the camp. "))
    assert asked < camp
    final = rig.fstore.league
    assert (final.players[own.id].salary, final.players[own.id].years) == P.new_contract(own)
    assert P.row_of(final, own.id)[3] == P.PAID and P.row_of(final, other.id)[3] == P.PAID


def test_an_older_holdouts_recommendation_is_to_let_him_wait(tmp_path):
    league, own, _other = camp_league(age=T.FR_HOLDOUT_PAY_AGE + 3, computer=False)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS))
    text = spoken(rig)
    asked = text.index(prompt_of(league, own, rig.fstore.words))
    assert text[asked + 1].strip() == "1. %s" % X.text("NXU-H11").strip()
    final = rig.fstore.league
    assert P.row_of(final, own.id)[3] == P.WAITED and P.morale(final, own.id) == -T.FR_MORALE_MAX and final.players[own.id].salary == own.salary


@pytest.mark.parametrize("keys, outcome", [([ENTER], P.PAID), ([DOWN, ENTER], P.WAITED), ([DOWN, DOWN, ENTER], P.ON_BLOCK)])
def test_every_answer_makes_another_league(tmp_path, keys, outcome):
    league, own, _other = camp_league(age=24, computer=False)
    rig = offseason_rig(tmp_path, league, keys=keys, until=at_stage(D.STAGE_CONTRACTS))
    final = rig.fstore.league
    assert P.row_of(final, own.id)[3] == outcome
    paid = (final.players[own.id].salary, final.players[own.id].years) == P.new_contract(own)
    assert paid == (outcome == P.PAID)
    assert (P.morale(final, own.id) == -T.FR_MORALE_MAX) == (outcome != P.PAID)
    told = {P.PAID: "NXU-H20", P.WAITED: "NXU-H21", P.ON_BLOCK: "NXU-H22"}[outcome]
    assert X.text(told, player=own.name, contract=rig.fstore.words.contract(final.players[own.id])) in spoken(rig)


def test_the_stage_writes_the_holdouts_before_it_speaks_and_a_window_closed_at_the_question_asks_again(tmp_path):
    league, own, other = camp_league(age=24)
    rig = offseason_rig(tmp_path, league, until=lambda r: any(t.startswith(" %s, " % own.name) and "holds out" in t for t in spoken(r)), keep=True)
    saved = saved_league(rig)
    assert saved.people["begun"] == saved.season and saved.people["pending"] == [own.id] and saved.stage_no == D.STAGE_DEVELOPMENT
    assert P.row_of(saved, other.id)[3] == P.PAID and saved.players[other.id].salary == P.new_contract(other)[0]      # the computer team's, settled
    assert saved.players[own.id].salary == own.salary                                           # nothing decided for the player
    paid_once = saved.players[other.id].salary
    again = offseason_rig(tmp_path, None, files=rig.files, until=at_stage(D.STAGE_CONTRACTS))
    final = again.fstore.league
    assert final.players[other.id].salary == paid_once and P.row_of(final, own.id)[3] == P.PAID
    assert P.row_of(final, other.id) == [other.id, 9, final.season, P.PAID]      # the camp was not begun again (its rows are the first write's)
    assert sum(1 for t in spoken(again) if "holds out at camp" in t) == 1


def test_with_the_staff_setting_on_nothing_is_asked_and_the_staff_decides(tmp_path):
    league, own, _other = camp_league(age=24, computer=False)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS), auto=True)
    text = spoken(rig)
    assert not any("holds out at camp" in t for t in text)
    final = rig.fstore.league
    assert P.row_of(final, own.id)[3] == P.PAID
    assert X.text("NXU-H23", player=own.name, contract=rig.fstore.words.contract(final.players[own.id])) in text


# ----- the season: a trade demand, the goal and its verdict -----

def season_league(outcome=P.ON_BLOCK):
    """A new league in week 1 whose last camp put a star of the player's team on the trade block."""
    def mutate(league):
        player = make_holdout(league, TEAM, 27)
        league.people["holdouts"] = [[player.id, TEAM, league.season, outcome]]
        league.people["begun"] = league.season
        P.set_morale(league, player.id, -T.FR_MORALE_MAX)
    league = draft_league(seed=4, team=TEAM, stage_no=0, mutate=mutate)
    league.stage, league.gtp, league.records = SEASON, 1, [0] * 64
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    league.history = []
    return league, league.players[league.people["holdouts"][0][0]]


def at_week(number):
    def predicate(rig):
        store = rig.fstore
        return store is not None and store.league is not None and store.league.stage == SEASON and store.league.gtp >= number
    return predicate


def demand_text(league, player, words):
    return X.text("NXU-D01", player=player.name, position=words.position(player.pos), n="@").split("@")[0]


def test_a_demand_of_the_players_team_is_an_item_with_the_offers_and_enter_takes_the_staffs_recommendation(tmp_path):
    league, star = season_league()
    offers = TR.block_offers(league, TEAM, star, list(league.records), 1)[:T.FR_DEMAND_OFFERS]
    assert offers, "the test league must have offers for the star"
    rig = offseason_rig(tmp_path, league, until=at_week(2))
    text = spoken(rig)
    words = rig.fstore.words
    asked = next(i for i, t in enumerate(text) if t.startswith(demand_text(league, star, words)))
    best = offers[0][0]
    recommended = P.acceptable(league, [star.id, TEAM, 1, P.OPEN], offers[0][1])
    first = text[asked + 1].strip()
    if recommended:
        assert first.startswith("1. the %s" % words.team_name(best.other(TEAM)))
    else:
        assert first == "1. %s" % X.text("NXU-D10").strip()
    final = rig.fstore.league
    assert (final.players[star.id].team != TEAM) == recommended
    if recommended:
        assert final.trades["log"][-1][7] == TR.KIND_DEMAND and P.demand_of(final, star.id)[3] == P.TRADED


def test_a_demand_left_for_later_trades_nothing_and_with_the_staff_setting_on_the_staff_answers(tmp_path):
    league, star = season_league()
    offers = TR.block_offers(league, TEAM, star, list(league.records), 1)[:T.FR_DEMAND_OFFERS]
    later = [DOWN] * (len(offers) + 1) + [ENTER]
    rig = offseason_rig(tmp_path, league, keys=later, until=at_week(2))
    final = rig.fstore.league
    assert final.players[star.id].team == TEAM and P.demand_of(final, star.id)[3] == P.OPEN
    assert not any(row[7] == TR.KIND_DEMAND for row in final.trades["log"])
    league2, star2 = season_league()
    rig2 = offseason_rig(tmp_path, league2, until=at_week(2), auto=True)
    recommended = P.acceptable(league2, [star2.id, TEAM, 1, P.OPEN], offers[0][1])
    assert (rig2.fstore.league.players[star2.id].team != TEAM) == recommended


def test_the_goal_is_said_before_the_kick_off_once_and_its_verdict_before_the_next_menu(tmp_path):
    league, _star = season_league(outcome=P.PAID)
    rig = offseason_rig(tmp_path, league, until=at_week(3))
    text = spoken(rig)
    final = rig.fstore.league
    goals = [i for i, t in enumerate(text) if t.startswith(" the goal of this game: ")]
    assert len(goals) == 2                                      # weeks 1 and 2, once each
    verdicts = [i for i, t in enumerate(text) if t in (X.text("NXU-G04"), X.text("NXU-G05"))]
    assert len(verdicts) == 1 and goals[0] < verdicts[0] < goals[1]
    assert final.people["goal"][1] == 2 and final.people["goal"][4] == 1


def test_the_morale_moves_after_a_week_through_the_program_and_reaches_the_games_ratings(tmp_path):
    league, _star = season_league(outcome=P.PAID)
    rig = offseason_rig(tmp_path, league, until=at_week(2))
    final = rig.fstore.league
    assert final.people["morale"], "a week moves the morale"
    from nfl4.extras.franchise.injury_flow import lineup_roster
    roster = lineup_roster(final, TEAM, final.gtp, False)
    for index, (heading, number, _pos) in enumerate(D.PLACES):
        player = final.player_at(TEAM, index)
        assert roster.ratings[(heading, number)] == max(40, min(99, player.rating + P.effect(P.morale(final, player.id))))
    assert any(P.effect(P.morale(final, player.id)) for player in final.active_of(TEAM)), "a morale that moves a rating"


# ----- the talk and the roster -----

def test_the_talk_says_what_the_player_cares_about_most(tmp_path):
    def expire(league):
        league.player_at(TEAM, 33).years = 0
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CONTRACTS, mutate=expire)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_FREE_AGENCY))
    qb = league.player_at(TEAM, 33)
    assert X.text("NXU-P01", trait=X.text(P.TRAIT_TEXT[P.personality(qb.id)])) in spoken(rig)


def test_the_roster_says_the_tag_the_morale_and_the_word():
    league, _o, _x = camp_league()
    words = Words(lambda t: "Team%d" % t)
    for player in [p for p in league.active_of(TEAM) if p is not None][:10]:
        line = PF.roster_words(words, league, player)
        trait = X.text(P.TRAIT_TEXT[P.personality(player.id)])
        tag = P.tag_of(player)
        want = (X.text("NXU-T05", tag=X.text(P.TAG_TEXT[tag]), morale=X.text("NXU-M02"), trait=trait) if tag
                else X.text("NXU-T06", morale=X.text("NXU-M02"), trait=trait))
        assert line == want
    from nfl4.extras.franchise.menus import roster_line
    star = league.player_at(TEAM, 0)
    P.set_morale(league, star.id, T.FR_MORALE_MAX)
    assert roster_line(words, league, star) == words.player_with_contract(star) + PF.roster_words(words, league, star)
    assert X.text("NXU-M01") in PF.roster_words(words, league, star)


# ----- the review's cases (SX.8n) -----

def test_enter_makes_the_demand_trade_when_the_staff_recommends_it(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_DEMAND_GIVE", 10 ** 6)            # every offer is acceptable: the first answer is the best offer
    league, star = season_league()
    rig = offseason_rig(tmp_path, league, until=at_week(2))
    final = rig.fstore.league
    assert final.players[star.id].team != TEAM and P.demand_of(final, star.id)[3] == P.TRADED
    assert any(row[7] == TR.KIND_DEMAND and row[1] == TEAM for row in final.trades["log"]) and P.morale(final, star.id) == 0


def test_a_chosen_offer_that_can_no_longer_be_made_is_told_so():
    from types import SimpleNamespace
    from nfl4.extras.franchise import todo, weekly
    league, star = season_league()
    offers = P.offers_for(league, [star.id, TEAM, 1, P.OPEN], list(league.records), 1)
    item = PF.demand_item(league, 1, [star.id, TEAM, 1, P.OPEN], offers)
    league.people["demands"] = [[star.id, TEAM, 1, P.OPEN]]
    league.todo.append(item)
    choices = PF.demand_choices(league, item)
    index = next(i for i, c in enumerate(choices) if c is not None)
    other = league.players[choices[index].give_b]
    other.status = "retired"                                    # the other team's player is gone: the trade can no longer be made
    store = SimpleNamespace(save=lambda: True, words=Words(lambda t: "Team%d" % t))
    done, text = weekly.finish_item(store, league, item, index, todo.answer_count(league, item))
    assert done and text == X.text("NXU-D13", player=star.name) and star.team == TEAM


def test_the_talk_reads_the_morale_and_the_personality(tmp_path, monkeypatch):
    def expire(league):
        qb = league.player_at(TEAM, 33)
        qb.years, qb.rating = 0, 78
        P.set_morale(league, qb.id, T.FR_MORALE_MAX)
    monkeypatch.setattr(T, "FR_RESIGN_TARGET", 1.0)
    league = draft_league(seed=3, team=TEAM, stage_no=D.STAGE_CONTRACTS, mutate=expire)
    qb = league.player_at(TEAM, 33)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_FREE_AGENCY))
    text = spoken(rig)
    assert any(t.startswith(" %s, " % qb.name) and X.text("NXW-20") + " with the team" in t for t in text)      # content by the record, happy by his morale
    word = P.personality(qb.id)
    if word == "playing_time":
        monkeypatch.setattr(T, "FR_PERSON_STARTER", (-T.FR_MOOD_SLACK["happy"], -T.FR_MOOD_SLACK["happy"]))
    else:
        monkeypatch.setattr(T, "FR_PERSON_TALK", dict(T.FR_PERSON_TALK, **{word: (-T.FR_MOOD_SLACK["happy"],) * 3}))
    again = offseason_rig(tmp_path, league, keys=[DOWN, ENTER], until=at_stage(D.STAGE_FREE_AGENCY))
    assert any(" wants more. " in t for t in spoken(again))     # his word took the happy slack away: the offer for less is countered, not taken


def test_the_answer_is_written_before_it_is_told(tmp_path):
    league, own, _other = camp_league(age=24, computer=False)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS), keep=True)
    text = spoken(rig)
    told = text.index(X.text("NXU-H20", player=own.name, contract=rig.fstore.words.contract(rig.fstore.league.players[own.id])))
    asked = text.index(prompt_of(league, own, rig.fstore.words))
    from nfl4.extras.franchise.league import LeagueRecord
    between = [s for s in rig.saves if asked < s[4] <= told and s[3] is not None]
    assert between and P.row_of(LeagueRecord.from_json(between[-1][3].decode("utf-8")), own.id)[3] == P.PAID


def test_the_staff_setting_turned_on_at_the_first_question_decides_the_second(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_HOLDOUT_TEAM_MAX", 2)
    holder = {}

    def mutate(league):
        holder["a"] = make_holdout(league, TEAM, 24)
        holder["b"] = make_holdout(league, TEAM, 24, word="winning")
        P.set_morale(league, holder["b"].id, T.FR_HOLDOUT_MORALE)
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_DEVELOPMENT, mutate=mutate)
    seen = []

    def until(r):
        prompts = [t for t in spoken(r) if "holds out at camp" in t]
        if prompts and not seen:
            seen.append(1)
            r.game.options.settings.game.nx_fr_auto = True     # turned on (as F9 would) while the first question waits; Enter answers it
        return at_stage(D.STAGE_CONTRACTS)(r)
    rig = offseason_rig(tmp_path, league, until=until)
    final = rig.fstore.league
    assert sum(1 for t in spoken(rig) if "holds out at camp" in t) == 1
    assert final.people["pending"] == [] and all(P.row_of(final, p.id)[3] != P.PENDING for p in (holder["a"], holder["b"]))
    assert any(t.startswith(" the staff paid ") or t.endswith(" and the staff let him wait. ") for t in spoken(rig))


def test_the_verdict_is_said_once_also_across_a_restart(tmp_path):
    league, _star = season_league(outcome=P.PAID)
    verdicts = (X.text("NXU-G04"), X.text("NXU-G05"))
    first = offseason_rig(tmp_path, league, until=lambda r: any(t in verdicts for t in spoken(r)))
    assert sum(1 for t in spoken(first) if t in verdicts) == 1
    again = offseason_rig(tmp_path, None, files=first.files, until=at_week(4))
    assert sum(1 for t in spoken(again) if t in verdicts) == 1                    # week 2's (said in week 3), never week 1's again


def test_a_demand_of_week_one_is_news_at_once(tmp_path):
    def mutate(league):
        player = make_holdout(league, 9, 30)
        league.people["holdouts"] = [[player.id, 9, league.season, P.ON_BLOCK]]
        league.people["begun"] = league.season
        P.set_morale(league, player.id, -T.FR_MORALE_MAX)
    league = draft_league(seed=4, team=TEAM, stage_no=0, mutate=mutate)
    league.stage, league.gtp, league.records = SEASON, 1, [0] * 64
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    league.history = []
    player = league.players[league.people["holdouts"][0][0]]
    rig = offseason_rig(tmp_path, league, until=at_week(2))
    news = [e for e in rig.fstore.league.news if e["pool"] == "NWH"]
    assert len(news) == 1 and player.name in news[0]["markup"] and news[0]["week"] == 1
    text = spoken(rig)
    assert text.index(X.text("NXN-01")) < next(i for i, t in enumerate(text) if player.name in t and "trade" in t)


def fake_program(league):
    from types import SimpleNamespace
    said = []
    p = SimpleNamespace(store=SimpleNamespace(league=league, save=lambda: True), g=SimpleNamespace(say2=said.append))
    return p, said


def test_the_goal_is_said_once_however_often_the_kick_off_is_reached():
    league, _star = season_league(outcome=P.PAID)
    P.set_goal(league, 1, 9)
    p, said = fake_program(league)
    PF.say_goal(p)
    PF.say_goal(p)
    assert said == [PF.goal_text(league)]


@pytest.mark.parametrize("met, text_id", [(1, "NXU-G04"), (0, "NXU-G05")])
def test_the_verdict_says_met_or_missed(met, text_id):
    league, _star = season_league(outcome=P.PAID)
    league.people["verdict"] = [league.season, 1, met, 0]
    p, said = fake_program(league)
    PF.say_verdict(p)
    PF.say_verdict(p)
    assert said == [X.text(text_id)]

