"""The Franchise's camp focus (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8m, research B6, D-073): the rule (the recommendation by the sides' means,
the candidates in the extra work's order, a point each, the season's limit), and stage 3 on the program rig: the question asked before anything changes, the
staff's recommendation first, the player's own focus, the staff setting, a window closed at the question.
"""
import random

from drrig import SURNAMES, at_stage, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging, camp, data as D
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

TEAM = 5


def league_of(seed=7):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")


def set_side(league, team, side, rating):
    for player in league.active_of(team):
        if player is not None and player.pos in T.FR_CAMP_SIDES[side]:
            player.rating = rating


def test_the_recommendation_is_the_side_furthest_under_the_leagues_mean_else_young_players():
    league = league_of()
    for team in range(1, 33):
        set_side(league, team, "offense", 70)
        set_side(league, team, "defense", 70)
    assert camp.recommend(league, 3) == "young"                       # nobody under the mean
    set_side(league, 3, "offense", 60)
    assert camp.recommend(league, 3) == "offense"
    set_side(league, 3, "defense", 50)
    assert camp.recommend(league, 3) == "defense"                     # further under
    set_side(league, 3, "offense", 49)
    assert camp.recommend(league, 3) == "offense"                     # the offense now further under
    even = league_of()
    for team in range(1, 33):
        set_side(even, team, "offense", 70 if team != 4 else 60)
        set_side(even, team, "defense", 70 if team != 4 else 60)     # both sides equally far under: the offense first
    assert camp.recommend(even, 4) == "offense"


def test_the_candidates_are_the_focus_in_the_extra_works_order_without_the_players_at_the_seasons_limit():
    league = league_of()
    for focus in T.FR_CAMP_FOCI:
        picked = camp.candidates(league, TEAM, focus)
        assert len(picked) == min(T.FR_CAMP_PLAYERS, len([p for p in league.active_of(TEAM) if camp.in_focus(p, focus)]))
        pool = sorted((p for p in league.active_of(TEAM) if camp.in_focus(p, focus)), key=lambda p: (D.POTENTIALS.index(p.potential), p.age, -p.rating, p.id))
        assert picked == pool[:T.FR_CAMP_PLAYERS]
    first = camp.candidates(league, TEAM, "offense")[0]
    first.points = T.FR_EXTRA_WORK_POINTS
    assert first not in camp.candidates(league, TEAM, "offense")
    young = camp.candidates(league, TEAM, "young")
    assert all(p.age <= T.FR_CAMP_YOUNG_AGE for p in young)
    assert all(p.pos in ("QB", "RB", "WR") for p in camp.candidates(league, TEAM, "offense"))


def test_every_teams_camp_gives_its_candidates_one_point_and_nobody_else_and_the_choice_is_kept():
    league = league_of()
    expected = {team: camp.candidates(league, team, "defense" if team == TEAM else camp.recommend(league, team)) for team in range(1, 33)}
    result = camp.apply(league, {TEAM: "defense"})
    assert result[TEAM][0] == "defense"
    given = {p.id for players in expected.values() for p in players}
    assert {team: [p.id for p in players] for team, (_f, players) in result.items()} == {t: [p.id for p in ps] for t, ps in expected.items()}
    for player in league.players.values():
        assert player.points == (1 if player.id in given else 0)


def stage_three(**kwargs):
    return draft_league(seed=3, team=TEAM, stage_no=D.STAGE_DEVELOPMENT, **kwargs)


def points_at_plan(monkeypatch):
    """The development points of every player at the moment stage 3 plans the progression (the camp's points are consumed by it)."""
    seen = {}
    real = aging.plan_development

    def spy(league, rnd):
        seen.update({p.id: p.points for p in league.players.values() if p.status == "active"})
        return real(league, rnd)
    monkeypatch.setattr(aging, "plan_development", spy)
    return seen


def test_stage_three_asks_the_focus_first_with_the_staffs_recommendation_and_enter_takes_it(tmp_path, monkeypatch):
    league = stage_three()
    recommended = camp.recommend(league, TEAM)
    seen = points_at_plan(monkeypatch)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS))
    text = spoken(rig)
    assert X.text("NXU-01", focus=X.text(camp.FOCUS_TEXT[recommended])) in text
    picked = camp.candidates(league, TEAM, recommended)
    assert X.text("NXU-02", focus=X.text(camp.FOCUS_TEXT[recommended]), list=", ".join(p.name for p in picked)) in text
    assert all(seen[p.id] == 1 for p in picked)


def test_the_player_may_choose_another_focus(tmp_path, monkeypatch):
    league = stage_three()
    recommended = camp.recommend(league, TEAM)
    second = [f for f in camp.FOCUS_TEXT if f != recommended][0]
    seen = points_at_plan(monkeypatch)
    rig = offseason_rig(tmp_path, league, keys=[DOWN, ENTER], until=at_stage(D.STAGE_CONTRACTS))
    picked = camp.candidates(league, TEAM, second)
    assert all(seen[p.id] == 1 for p in picked)
    assert X.text("NXU-02", focus=X.text(camp.FOCUS_TEXT[second]), list=", ".join(p.name for p in picked)) in spoken(rig)
    others = {p.id for p in camp.candidates(league, TEAM, recommended)} - {p.id for p in picked}
    assert all(seen[pid] == 0 for pid in others)


def test_with_the_staff_setting_on_nothing_is_asked_and_the_staffs_focus_is_taken(tmp_path, monkeypatch):
    league = stage_three()
    recommended = camp.recommend(league, TEAM)
    seen = points_at_plan(monkeypatch)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS), auto=True)
    assert not any(t.startswith(" the camp. ") for t in spoken(rig))
    assert all(seen[p.id] == 1 for p in camp.candidates(league, TEAM, recommended))


def test_a_window_closed_at_the_question_leaves_the_file_as_the_stage_found_it(tmp_path):
    league = stage_three()
    rig = offseason_rig(tmp_path, league, until=lambda r: any(t.startswith(" the camp. ") for t in spoken(r)))
    saved = saved_league(rig)
    assert saved.stage_no == D.STAGE_DEVELOPMENT
    assert all(p.points == 0 for p in saved.players.values())
    assert saved.to_json() == league.to_json()


def test_the_short_offseason_still_asks_and_says_the_camp(tmp_path):
    league = stage_three()
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS), short=True)
    text = spoken(rig)
    assert any(t.startswith(" the camp. ") for t in text) and any(t.startswith(" camp focus: ") for t in text)


def weak_defense(league):
    for player in league.active_of(TEAM):
        if player is not None and player.pos in T.FR_CAMP_SIDES["defense"]:
            player.rating = 41


def test_the_recommendation_is_the_first_answer_also_when_it_is_not_the_first_focus_of_the_list(tmp_path):
    league = stage_three(mutate=weak_defense)
    assert camp.recommend(league, TEAM) == "defense" and T.FR_CAMP_FOCI[0] != "defense"
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CONTRACTS))
    assert any(t.strip() == "1. %s" % X.text(camp.FOCUS_TEXT["defense"]).strip() for t in spoken(rig))
    picked = camp.candidates(league, TEAM, "defense")
    assert X.text("NXU-02", focus=X.text(camp.FOCUS_TEXT["defense"]), list=", ".join(p.name for p in picked)) in spoken(rig)


def test_young_players_are_only_the_young():
    league = league_of()
    for player in league.active_of(TEAM):
        player.age = T.FR_CAMP_YOUNG_AGE + 1
    assert camp.candidates(league, TEAM, "young") == []
    league.player_at(TEAM, 3).age = T.FR_CAMP_YOUNG_AGE
    assert camp.candidates(league, TEAM, "young") == [league.player_at(TEAM, 3)]
