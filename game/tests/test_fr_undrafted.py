"""The Franchise's undrafted free agents (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8m, research B4, B12, F2, D-073): the rule (the draft's need and
value, the best prospects first, a team's limit, the market's tie rule), the camp's contract and the free release at the cut, the whole-file check, and stage 4's
question on the program rig: the staff's offers, the player's own, nobody, the staff setting (nothing decided for him when it is off).
"""
import random

import pytest
from drrig import SURNAMES, at_stage, draft_league, offseason_rig
from frrig import DOWN, ENTER, UP, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT, data as D, draft as DR, undrafted as UD
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise.league import LeagueError, LeagueRecord
from nfl4.game.rnd import GameRandom

TEAM = 5


def weak(league):
    """Weak running backs and receivers on every odd team and the player's, so the market has buyers."""
    for t in list(range(1, 33, 2)) + [TEAM]:
        for i in list(range(0, 3)) + list(range(6, 9)):
            league.players[league.rosters[t - 1][i]].rating = 41


def drafted(seed=6, mutate=weak):
    """A league whose draft is complete (every pick the computer's rule), before the undrafted market."""
    league = draft_league(seed=seed, team=TEAM, mutate=mutate)
    draft = DR.Draft.create(league, GameRandom(random.Random(seed)), SURNAMES)
    while not draft.done:
        _, _, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    return league, draft


# ----- the rule -----

def test_a_team_offers_only_the_prospects_it_wants_the_most_valuable_first_at_most_its_chase():
    league, draft = drafted()
    for team in range(1, 33):
        offers = UD.team_offers(draft, team)
        needs = draft.needs(team)
        assert len(offers) <= T.FR_UDFA_CHASE
        prospects = [draft.prospects[o.prospect] for o in offers]
        assert all(UD.wanted(draft, team, p, needs) for p in prospects)
        values = [draft.value(p, needs) for p in prospects]
        assert values == sorted(values, reverse=True)
        others = [p for p in UD.pool(draft) if p not in prospects and UD.wanted(draft, team, p, needs)]
        assert not prospects or all(draft.value(p, needs) <= values[-1] for p in others)


def test_the_market_signs_the_best_prospects_first_each_with_the_team_that_values_him_most_within_the_limit():
    league, draft = drafted()
    result = UD.run(draft)
    assert result.signed, "the weak teams sign undrafted free agents"
    per = {}
    for prospect, team, player in result.signed:
        per[team] = per.get(team, 0) + 1
        assert (player.status, player.place, player.drafted, player.team) == ("active", -1, None, team)
        assert (player.salary, player.years) == (CT.min_salary(0), T.FR_FILL_YEARS)
        assert (player.name, player.pos, player.rating, player.potential, player.age) == (prospect.name, prospect.pos, prospect.true, prospect.potential, prospect.age)
        assert [team, prospect.index, player.id] in draft.data["undrafted"]
    assert max(per.values()) <= T.FR_UDFA_MAX
    order = [p.index for p, _t, _pl in result.signed]
    base = {p.index: draft.board.base[p.index] for p, _t, _pl in result.signed}
    assert order == sorted(order, key=lambda i: (-base[i], i))
    league.check()                                                     # waiting for the cut, in the draft record
    assert set(pl.id for _p, t, pl in result.signed if t == TEAM) <= {r.id for r in league.waiting_rookies(TEAM)}


def test_a_team_that_has_signed_its_limit_offers_nobody(monkeypatch):
    league, draft = drafted()
    monkeypatch.setattr(T, "FR_UDFA_MAX", 0)
    assert all(UD.team_offers(draft, team) == [] for team in range(1, 33))
    assert UD.run(draft).signed == []


def test_equal_values_go_by_the_markets_tie_rule_not_by_the_team_number():
    league, draft = drafted()
    prospect = UD.pool(draft)[0]
    offers = [UD.Offer(t, prospect.index) for t in (3, 11)]
    for t in (3, 11):
        league.players[league.rosters[t - 1][0]].rating = 41
    v3, v11 = draft.value(prospect, draft.needs(3)), draft.value(prospect, draft.needs(11))
    result = UD.resolve(draft, offers)
    if v3 == v11 and UD.wanted(draft, 3, prospect) and UD.wanted(draft, 11, prospect):
        from nfl4.extras.franchise.market import tie_key
        assert result.signed[0][1] == min((3, 11), key=lambda t: tie_key(t, prospect.index + 1))


def test_an_undrafted_rookie_released_at_his_first_cut_costs_no_dead_money_and_the_cap_rule_knows_it():
    league, draft = drafted()
    result = UD.run(draft)
    _prospect, team, player = result.signed[0]
    assert CT.released_free(player) and CT.release_cost(player) == 0
    waiting = DR.waiting_by_team(league)
    left = len(DR.group_players(league, team, player.pos, waiting)) - 1
    fill = T.FR_MIN_SALARY if left < D.GROUP_SIZE[player.pos] else 0
    assert CT.cap_after_cut(league, team, waiting, [player]) == CT.cap_after_cut(league, team, waiting, []) - player.salary + fill   # no dead money
    dead = league.dead[team - 1]
    plans = {t: DR.staff_cut(league, t, waiting) for t in range(1, 33)}
    if player not in plans[team]:
        plans[team] = plans[team] + [player]
    expected = sum(CT.release_cost(p) for p in plans[team]) + dead
    DR.apply_cut(league, plans, waiting)
    assert league.dead[team - 1] == expected
    assert player.status == "released" and (player.salary, player.years) == (0, 0)


def test_the_draft_record_check_refuses_a_bad_undrafted_signing():
    league, draft = drafted()
    UD.run(draft)
    good = LeagueRecord.from_json(league.to_json())
    row = good.draft["undrafted"][0]
    picked = good.draft["picks"][0][1]
    cases = [lambda lg: lg.draft["undrafted"].append(list(lg.draft["undrafted"][0])),                 # twice
             lambda lg: lg.draft["undrafted"][0].__setitem__(1, picked),                              # a drafted prospect
             lambda lg: setattr(lg.players[row[2]], "name", "Somebody"),                              # not his prospect
             lambda lg: setattr(lg.players[row[2]], "drafted", [lg.season, 7, 1])]                    # a drafted rookie
    for change in cases:
        bad = LeagueRecord.from_json(good.to_json())
        change(bad)
        with pytest.raises(LeagueError):
            bad.check()
    early = draft_league(seed=6, team=TEAM, mutate=weak)
    d = DR.Draft.create(early, GameRandom(random.Random(6)), SURNAMES)
    d.make_pick(d.next_slot()[2], d.best_for(d.next_slot()[2]))
    UD.sign(d, 3, UD.pool(d)[0])
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(early.to_json())                           # signed before the draft is over


# ----- stage 4 on the program rig -----

def replayed(rig, skip):
    """The undrafted market the stage must have made: the class the stage saved, the computer's rule for every pick (the player's Enter takes the staff's
    first, the same prospect), then `undrafted.run` with `skip`."""
    league = LeagueRecord.from_json(rig.class_raw.decode("utf-8"))
    draft = DR.Draft(league)
    while not draft.done:
        _, _, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    return draft


def signed_of(league):
    return sorted([t, i] for t, i, _pid in league.draft["undrafted"])


def wanting(league):
    """`weak` and the player's team weak in every group but the quarterback, so it wants undrafted prospects (the review of SX.8m: in `weak` alone the staff
    offered nobody for it, and the tests of the question could not fail)."""
    weak(league)
    for i in range(33):
        league.players[league.rosters[TEAM - 1][i]].rating = 41


def test_after_the_last_pick_the_player_is_asked_and_enter_makes_the_staffs_offers(tmp_path):
    league = draft_league(seed=6, team=TEAM, mutate=wanting)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine")
    draft = replayed(rig, ())
    staff = UD.team_offers(draft, TEAM)
    assert staff, "the player's team wants undrafted prospects in this league"
    expected = UD.run(draft, staff, skip=(TEAM,))
    after = LeagueRecord.from_json(rig.kept[D.STAGE_CUT].decode("utf-8"))
    assert signed_of(after) == sorted([t, p.index] for p, t, _pl in expected.signed)
    assert any(t == TEAM for t, _i in signed_of(after))                    # the staff's offers signed somebody for him
    names = {p.index: p.name for p in draft.prospects}
    text = spoken(rig)
    assert any(t.startswith(" undrafted free agents. ") for t in text)
    assert X.text("NXU-25", list=", ".join(names[o.prospect] for o in staff)) in text


def test_offer_nobody_signs_nobody_for_the_player_where_the_staffs_offers_would_have(tmp_path):
    league = draft_league(seed=6, team=TEAM, mutate=wanting)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine", keys=[ENTER] * 7 + [DOWN, DOWN, ENTER])
    after = LeagueRecord.from_json(rig.kept[D.STAGE_CUT].decode("utf-8"))
    other = replayed(rig, ())
    staffs = UD.run(other, UD.team_offers(other, TEAM), skip=(TEAM,))
    assert any(t == TEAM for _p, t, _pl in staffs.signed)                  # the staff's offers would have signed somebody: "nobody" differs
    draft = replayed(rig, (TEAM,))
    expected = UD.run(draft, [], skip=(TEAM,))
    assert all(t != TEAM for t, _i in signed_of(after))
    assert signed_of(after) == sorted([t, p.index] for p, t, _pl in expected.signed)


def test_choose_yourself_offers_the_prospect_he_picks_and_he_signs_or_is_told_why_not(tmp_path):
    league = draft_league(seed=6, team=TEAM, mutate=wanting)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine",
                        keys=[ENTER] * 7 + [DOWN, ENTER, DOWN, ENTER, UP, ENTER])   # choose yourself; down to the first of his list and offer him; up to "done"
    after = LeagueRecord.from_json(rig.kept[D.STAGE_CUT].decode("utf-8"))
    draft = replayed(rig, (TEAM,))
    first = sorted(UD.pool(draft), key=lambda p: (-draft.value(p, draft.needs(TEAM)), p.index))[0]
    expected = UD.run(draft, [UD.Offer(TEAM, first.index)], skip=(TEAM,), own=(TEAM,))
    assert signed_of(after) == sorted([t, p.index] for p, t, _pl in expected.signed)
    text = spoken(rig)
    assert X.text("NXU-28", player=first.name) in text
    winner = {p.index: t for p, t, _pl in expected.signed}.get(first.index)
    if winner == TEAM:
        assert [TEAM, first.index] in signed_of(after)
    else:
        assert any(t.startswith(" %s " % first.name) and ("signed with the" in t or "did not sign with you" in t) for t in text)


def test_the_players_own_offer_is_not_held_to_the_computers_need_rule():
    league, draft = drafted()
    unwanted = [p for p in UD.pool(draft) if not UD.wanted(draft, TEAM, p)
                and not any(UD.wanted(draft, t, p) for t in range(1, 33) if t != TEAM)]
    assert unwanted, "a prospect nobody wants by the rule"
    result = UD.run(draft, [UD.Offer(TEAM, unwanted[0].index)], skip=(TEAM,), own=(TEAM,))
    assert any(p.index == unwanted[0].index and t == TEAM for p, t, _pl in result.signed)
    assert not any(p.index == unwanted[0].index for p, _t, _pl in UD.run(drafted()[1], [UD.Offer(TEAM, unwanted[0].index)], skip=(TEAM,)).signed)


def test_a_team_never_signs_more_than_its_limit_even_when_it_offers_more(monkeypatch):
    league, draft = drafted()
    monkeypatch.setattr(T, "FR_UDFA_MAX", 1)
    offers = UD.computer_offers(draft)
    assert any(sum(1 for o in offers if o.team == t) > 1 for t in range(1, 33))
    result = UD.run(draft)
    per = {}
    for _p, t, _pl in result.signed:
        per[t] = per.get(t, 0) + 1
    assert per and max(per.values()) == 1


def test_a_drafted_rookie_released_at_the_cut_still_costs_dead_money():
    league, draft = drafted()
    rookie = league.players[draft.picks[0][2]]
    assert not CT.released_free(rookie) and CT.release_cost(rookie) == CT.dead_money(rookie) > 0


def test_with_the_staff_setting_on_nothing_is_asked_and_his_team_follows_the_computer_teams_rule(tmp_path):
    league = draft_league(seed=6, team=TEAM, mutate=weak)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine", auto=True)
    after = LeagueRecord.from_json(rig.kept[D.STAGE_CUT].decode("utf-8"))
    draft = replayed(rig, ())
    expected = UD.run(draft)
    assert signed_of(after) == sorted([t, p.index] for p, t, _pl in expected.signed)
    assert not any(t.startswith(" undrafted free agents. ") for t in spoken(rig))


def test_of_two_teams_that_want_him_the_one_that_values_him_more_signs_him():
    # SR.5: a need is by family (fewer than FR_ROSTER_TARGET, or a starter under FR_DRAFT_WEAK), so both teams have the need bonus and the values differ by
    # the "better" one: the player's team is short of backs but its two starters are better than him, the other team's backs are all weak
    league, draft = drafted()
    prospect = next(p for p in UD.pool(draft) if p.pos == "RB")
    other = 20 if TEAM != 20 else 21
    rookies = sum(1 for r in draft.rookies.get(TEAM, ()) if r.pos == "RB")
    backs = sorted((p for p in RR.members(league, TEAM) if p.pos == "RB"), key=lambda p: (-p.rating, p.id))
    keep = T.FR_ROSTER_TARGET["RB"] - 1 - rookies
    assert keep >= T.FR_GROUP_STARTERS["RB"], "the player's team drafted too many backs for this case"
    for man in backs[:keep]:
        man.rating = man.peak = 70
    for man in backs[keep:]:
        man.left = league.season
        RR.leave(league, man, "released")
    for man in RR.members(league, other):
        if man.pos == "RB":
            man.rating = man.peak = 41
    RR.refresh_view(league, other)
    draft = DR.Draft(league)
    values = {t: draft.value(prospect, draft.needs(t)) for t in (TEAM, other)}
    assert UD.wanted(draft, TEAM, prospect) and UD.wanted(draft, other, prospect) and values[other] > values[TEAM]
    result = UD.resolve(draft, [UD.Offer(TEAM, prospect.index), UD.Offer(other, prospect.index)])
    assert any(p.index == prospect.index and t == other for p, t, _pl in result.signed)


def test_his_own_choice_signs_a_prospect_the_rule_would_not_want_and_an_offer_that_signs_nobody_is_told(tmp_path, monkeypatch):
    real = UD.wanted
    monkeypatch.setattr(UD, "wanted", lambda draft, team, prospect, needs=None: team != TEAM and real(draft, team, prospect, needs))
    monkeypatch.setattr(T, "FR_UDFA_MAX", 1)
    league = draft_league(seed=6, team=TEAM, mutate=wanting)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine",
                        keys=[ENTER] * 7 + [DOWN, ENTER] + [DOWN, ENTER] * 3 + [UP, UP, UP, ENTER])   # choose yourself; offer the first three; up to "done"
    after = LeagueRecord.from_json(rig.kept[D.STAGE_CUT].decode("utf-8"))
    draft = replayed(rig, (TEAM,))
    ranked = sorted(UD.pool(draft), key=lambda p: (-draft.value(p, draft.needs(TEAM)), p.index))[:3]
    expected = UD.run(draft, [UD.Offer(TEAM, p.index) for p in ranked], skip=(TEAM,), own=(TEAM,))
    assert signed_of(after) == sorted([t, p.index] for p, t, _pl in expected.signed)
    mine = [t for t, _i in signed_of(after) if t == TEAM]
    assert len(mine) == 1                                                 # his choice signed although the rule wanted nobody for him; his limit is one
    winners = {p.index: t for p, t, _pl in expected.signed}
    text = spoken(rig)
    nobody = [p for p in ranked if p.index not in winners]
    assert nobody, "one of his three offers signed nobody"
    for p in nobody:
        assert X.text("NXU-31", player=p.name) in text
