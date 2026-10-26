"""The staff of the Franchise: the head coaches' job rating and the owner's goal, the firings, the offers, the coordinators (nfl4 only, rule 0.13;
NFL_FRANCHISE_DESIGN 17 SX.8l, research B8, B9, G, D-072). The rules of `extras/franchise/staff.py`, on strict scripts where they draw. The stage on the
program rig is test_fr_staff_flow.py.
"""
import copy
import json
import random

import pytest
from drrig import SURNAMES, draft_league, legacy_data
from randsources import ScriptedRandom, below_value, value_for

from nfl4.extras import playbook_data as PD
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import first_names as FN
from nfl4.extras.franchise import staff as S
from nfl4.extras.franchise.league import OFFSEASON, LeagueError, LeagueRecord, new_league
from nfl4.extras.playbooks import DEFAULT_TABLE
from nfl4.game.rnd import GameRandom

TEAM = 5


def league_of(seed=3, team=TEAM):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def at_stage(league):
    league.stage, league.stage_no, league.gtp, league.records = OFFSEASON, D.STAGE_STAFF, 0, [8, 8] * 32
    return league


def season_judged(league, approval=70, wins=8):
    """Every coach judged after a season of `wins` (8: no winning season), as stage 1 leaves them."""
    for team in range(1, 33):
        judged(league, team, approval, wins)
    return league


def judged(league, team, approval, wins, seasons=3, finish=0):
    """A coach as stage 1 leaves him: his rating after the season and the season's record kept."""
    coach = S.coach_of(league, team)
    coach.update(approval=approval, seasons=seasons, last=[wins, finish, 0, 60])


# ----- a new league -----

def test_a_new_league_has_a_head_coach_and_two_coordinators_for_every_team_with_the_teams_styles_and_no_draw():
    league = league_of()
    again = league_of()
    assert league.staff == again.staff and league.staff["stage"] is None
    for team in range(1, 33):
        coach = S.coach_of(league, team)
        start = (T.FR_APPROVAL_START, 0) if team == TEAM else S.league_start(team)      # the player is new; the others served a while (SX.8l review 5)
        assert (coach["approval"], coach["seasons"]) == start and coach["last"] is None
        for side in S.SIDES:
            c = S.coordinator_of(league, team, side)
            assert c["style"] == PD.TEAM_STYLES[team - 1][side] and c["rating"] == S.side_rating(league, team, side) and c["seasons"] == 0
    names = [S.coach_of(league, t)["name"] for t in range(1, 33) if t != TEAM] + [c["name"] for pair in league.staff["coordinators"] for c in pair]
    active = {p.name for p in league.players.values() if p.status == "active"}
    assert len(set(names)) == len(names) == 95 and not set(names) & active
    assert S.coach_of(league, TEAM)["name"] == "Kim"


def test_a_new_leagues_draws_are_the_same_with_the_staff(monkeypatch):
    with_staff = GameRandom(random.Random(3))
    with_staff.trace = []
    made = new_league(with_staff, SURNAMES, "Kim", TEAM, "20260101-000000")
    monkeypatch.setattr(S, "new_staff", lambda league, surnames, team_styles=None: None)
    without = GameRandom(random.Random(3))
    without.trace = []
    new_league(without, SURNAMES, "Kim", TEAM, "20260101-000000")
    assert with_staff.trace == without.trace and made.staff is not None      # the staff of a new league draws nothing (SX.8l)


def test_a_coordinator_of_a_new_league_is_rated_by_his_side_of_the_ball():
    league = league_of()
    for index, player in enumerate(league.active_of(2)):
        player.rating = 80 if player.pos in S.OFFENSE_POSITIONS else 61
    assert S.side_rating(league, 2, 0) == 80 and S.side_rating(league, 2, 1) == 61
    league.player_at(2, 0).rating = 81                                 # 13 offense players (RB 6, WR 6, QB): 1041 / 13 = 80.08, rounded 80
    assert S.side_rating(league, 2, 0) == 80


def test_the_styles_given_are_the_coordinators_and_a_style_the_table_does_not_know_is_classic():
    styles = [("air", "zone")] * 31 + [("nonsense", "classic")]
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", TEAM, "20260101-000000", team_styles=styles)
    assert S.team_styles(league)[0] == ("air", "zone") and S.team_styles(league)[31] == ("classic", "classic")


# ----- the owner's goal -----

def test_the_goal_follows_the_rank_at_the_seasons_start_and_every_kind_is_judged_by_its_own_number():
    assert [S.goal_for(r) for r in (1, 4, 5, 8, 9, 12, 13, 20, 21, 24, 25, 28, 29, 32)] == [
        ["wins", 11], ["wins", 11], ["playoffs", 0], ["playoffs", 0], ["wins", 9], ["wins", 9], ["wins", 8], ["wins", 8], ["wins", 7], ["wins", 7],
        ["wins", 6], ["wins", 6], ["wins", 5], ["wins", 5]]
    league = league_of()
    for rank, team in enumerate(league.ranking(), start=1):
        assert S.coach_of(league, team)["goal"] == S.goal_for(rank)
    assert S.goal_met(["wins", 9], 9, 0) and not S.goal_met(["wins", 9], 8, 5)
    assert S.goal_met(["playoffs", 0], 0, D.FINISH_WILD_CARD) and not S.goal_met(["playoffs", 0], 16, D.FINISH_MISSED)
    assert S.goal_met(["title_game", 0], 5, D.FINISH_CHAMPIONSHIP) and not S.goal_met(["title_game", 0], 14, D.FINISH_DIVISION)


# ----- the job rating -----

def test_the_job_rating_moves_by_the_goal_the_wins_and_the_finish_and_stays_in_0_to_100():
    met, missed = T.FR_APPROVAL_GOAL
    assert S.new_approval(60, ["wins", 8], 8, 0) == (60 + met, True)
    assert S.new_approval(60, ["wins", 9], 8, 0) == (60 - missed, False)
    assert S.new_approval(60, ["wins", 8], 12, D.FINISH_CHAMPION) == (min(100, 60 + met + 4 * T.FR_APPROVAL_PER_WIN + T.FR_APPROVAL_FINISH[5]), True)
    assert S.new_approval(60, ["wins", 8], 3, 0) == (60 - missed - 5 * T.FR_APPROVAL_PER_WIN, False)
    assert S.new_approval(98, ["wins", 0], 16, 5)[0] == 100 and S.new_approval(5, ["wins", 16], 0, 0)[0] == 0


def test_the_verdicts_change_nothing_and_applying_them_keeps_the_season_for_the_firing_rule():
    league = league_of()
    wins = [8] * 32
    finish = [0] * 32
    wins[TEAM - 1], finish[TEAM - 1] = 3, 0
    before = copy.deepcopy(league.staff)
    found = S.verdicts(league, wins, finish)
    assert league.staff == before
    goal = S.coach_of(league, TEAM)["goal"]
    assert found[TEAM - 1] == (60,) + S.new_approval(60, goal, 3, 0)
    S.apply_verdicts(league, wins, finish)
    coach = S.coach_of(league, TEAM)
    assert coach["approval"] == found[TEAM - 1][1] and coach["seasons"] == 1 and coach["last"] == [3, 0, int(found[TEAM - 1][2]), 60]
    assert all(c["seasons"] == 1 for pair in league.staff["coordinators"] for c in pair)


def test_a_coach_is_never_fired_after_a_winning_season_nor_after_his_first_and_only_under_the_line():
    coach = S.new_coach("X")
    for wins in range(0, 17):
        for approval in range(0, 101, 5):
            for seasons in range(0, 4):
                coach.update(approval=approval, seasons=seasons, last=[wins, 0, 0, 60])
                fired = S.is_fired(coach)
                assert not (fired and S.winning(wins)) and not (fired and seasons <= T.FR_FIRE_GRACE)
                assert fired == (approval < T.FR_FIRE_BELOW and wins <= 8 and seasons > T.FR_FIRE_GRACE)
    coach.update(approval=T.FR_FIRE_BELOW - 1, seasons=2, last=[8, 0, 0, 60])
    assert S.is_fired(coach)
    coach.update(approval=T.FR_FIRE_BELOW)
    assert not S.is_fired(coach)
    coach.update(approval=0, last=[9, 0, 0, 60])
    assert not S.is_fired(coach)
    coach.update(last=None)
    assert not S.is_fired(coach)


# ----- the stage: the firings and the offers -----

def test_begin_fires_by_the_rule_alone_and_a_fired_player_is_offered_jobs_of_other_teams_only():
    league = season_judged(at_stage(league_of()))
    judged(league, TEAM, 20, 4)
    judged(league, 9, 20, 6)
    judged(league, 12, 20, 12)                               # a winning season: never fired
    judged(league, 14, 20, 5, seasons=1)                     # his first season: never fired
    state = S.begin(league)
    assert state["fired"] == [TEAM, 9] and state["step"] == S.STEP_JOB and state["old_team"] == TEAM and state["approval"] == 20
    assert S.coach_of(league, TEAM) is None and S.coach_of(league, 9) is None and S.coach_of(league, 12) is not None
    offers = state["offers"]
    assert TEAM not in offers and len(offers) == T.FR_OFFERS and 9 in offers
    ranks = {t: n for n, t in enumerate(league.ranking(), start=1)}
    assert offers == sorted(offers, key=lambda t: ranks[t])
    others = [t for t in offers if t != 9]
    assert all(not S.winning(S.coach_of(league, t)["last"][0]) for t in others)


def test_the_offers_take_the_open_places_first_then_the_lowest_rated_coaches_without_a_winning_season():
    league = at_stage(league_of())
    for team in range(1, 33):
        judged(league, team, 70, 10)                         # everybody won ...
    for team, approval in ((20, 61), (21, 58), (22, 66), (23, 57)):
        judged(league, team, approval, 7)                    # ... but these four, who keep their jobs
    league.staff["coaches"][30] = None                        # team 31's place is open
    got = S.offers(league, TEAM)
    assert sorted(got) == [21, 23, 31] and TEAM not in got
    league.staff["coaches"][29] = league.staff["coaches"][28] = None
    assert sorted(S.offers(league, TEAM)) == [29, 30, 31]
    assert TEAM not in S.offers(league, TEAM) and 29 not in S.offers(league, 29)


def test_taking_a_job_moves_the_player_and_a_coach_still_in_the_place_is_let_go():
    league = season_judged(at_stage(league_of()))
    judged(league, TEAM, 20, 4)
    state = S.begin(league)
    with pytest.raises(LeagueError):
        S.take_job(league, TEAM)                             # never the team that fired him
    target = next(t for t in state["offers"] if S.coach_of(league, t) is not None)
    S.take_job(league, target)
    assert league.team == target and state["let_go"] == target and state["step"] == S.STEP_COACHES
    assert S.coach_of(league, target) == S.new_coach("Kim") and S.coach_of(league, TEAM) is None


# ----- the head coaches hired and the coordinators -----

def test_an_open_place_takes_the_best_rated_coordinator_and_a_new_head_coach_brings_his_own_coordinators():
    league = at_stage(league_of())
    for team in range(1, 33):
        for side in S.SIDES:
            S.coordinator_of(league, team, side)["rating"] = 70
    S.coordinator_of(league, 7, 1)["rating"] = 88
    S.coordinator_of(league, 3, 0)["rating"] = 88                     # equal: the first in team order
    S.coordinator_of(league, 11, 0)["rating"] = 59                    # under FR_COORD_KEEP: a computer team replaces him
    S.coordinator_of(league, TEAM, 1)["rating"] = 50                  # the player's own: kept while the staff does not handle it
    judged(league, 20, 10, 2)
    judged(league, 21, 10, 2)
    state = S.begin(league)
    name3, name7 = S.coordinator_of(league, 3, 0)["name"], S.coordinator_of(league, 7, 1)["name"]
    S.hire_head_coaches(league, staff=False)
    assert state["hired"] == [[20, 3, 0, name3], [21, 7, 1, name7]]
    assert S.coach_of(league, 20)["name"] == name3 and S.coach_of(league, 20)["approval"] == T.FR_APPROVAL_START
    assert S.coordinator_of(league, 3, 0) is None and S.coordinator_of(league, 7, 1) is None
    assert S.coordinator_of(league, 20, 0) is None and S.coordinator_of(league, 20, 1) is None      # the new head coach brings his own
    assert S.coordinator_of(league, 11, 0) is None and S.coordinator_of(league, 11, 1) is not None
    assert S.coordinator_of(league, TEAM, 1) is not None and state["step"] == S.STEP_OWN


def test_the_staff_handles_the_players_coordinators_by_the_computer_teams_rule_and_his_lost_coordinator_is_told():
    league = at_stage(league_of())
    S.coordinator_of(league, TEAM, 0)["rating"] = 95
    S.coordinator_of(league, TEAM, 1)["rating"] = 50
    judged(league, 20, 10, 2)
    state = S.begin(league)
    name = S.coordinator_of(league, TEAM, 0)["name"]
    S.hire_head_coaches(league, staff=True)
    assert state["lost"] == [[0, name, 20]] and S.coordinator_of(league, TEAM, 1) is None and state["step"] == S.STEP_DRAW


def test_the_player_with_both_coordinators_gone_is_not_asked_about_keeping_them():
    league = at_stage(league_of())
    S.coordinator_of(league, TEAM, 0)["rating"] = 95
    S.coordinator_of(league, TEAM, 1)["rating"] = 94
    judged(league, 20, 10, 2)
    judged(league, 21, 10, 2)
    S.begin(league)
    S.hire_head_coaches(league, staff=False)
    assert league.staff["stage"]["step"] == S.STEP_DRAW


def test_the_candidates_are_drawn_in_team_order_the_computer_takes_the_best_and_the_player_waits():
    league = at_stage(league_of())
    for team in range(1, 33):
        for side in S.SIDES:
            S.coordinator_of(league, team, side)["rating"] = 70
    S.begin(league)
    S.hire_head_coaches(league, staff=False)
    league.staff["coordinators"][1][1] = None                         # team 2's defense is open
    S.own_sides(league, [0])                                          # the player replaces his offensive coordinator
    free = [n for n, name in enumerate(SURNAMES, start=1) if name not in FN.name_keys(league.league_id, (p.name for p in league.players.values()))
            and all(name != c["name"] for pair in league.staff["coordinators"] for c in pair if c is not None)
            and all(c is None or name != c["name"] for c in league.staff["coaches"]) and name != "Kim"]
    source = ScriptedRandom(strict=True)
    names = []
    for start in (0, 3):
        for k, (style, a, b) in enumerate(((1, 0, 0), (2, 20, 20), (3, 10, 10)) if start == 0 else ((4, 5, 5), (5, 6, 6), (6, 5, 6))):
            names.append(SURNAMES[free[start + k] - 1])
            source.values += [value_for(len(SURNAMES), free[start + k]), below_value(7, style), below_value(21, a), below_value(21, b)]
    S.draw_candidates(league, GameRandom(source), SURNAMES, staff=False)
    assert source.left == 0
    state = league.staff["stage"]
    two = state["candidates"]["2:1"]
    assert [c["rating"] for c in two] == [90, 70, 50] and [c["style"] for c in two] == [S.STYLE_KEYS[2], S.STYLE_KEYS[3], S.STYLE_KEYS[1]]
    assert S.coordinator_of(league, 2, 1) == two[0]                  # the computer took the best
    mine = state["candidates"]["%d:0" % TEAM]
    assert [c["rating"] for c in mine] == [62, 61, 60] and [c["name"] for c in mine] == [names[4], names[5], names[3]]       # the best rated first
    assert [c["style"] for c in mine] == [S.STYLE_KEYS[5], S.STYLE_KEYS[6], S.STYLE_KEYS[4]]                                   # the seventh style too
    assert S.coordinator_of(league, TEAM, 0) is None and S.waiting_sides(league) == [0] and state["step"] == S.STEP_PICK
    chosen = S.hire(league, TEAM, 0, 2)
    assert chosen == mine[2] and S.coordinator_of(league, TEAM, 0) == mine[2] and S.waiting_sides(league) == []
    with pytest.raises(LeagueError):
        S.hire(league, TEAM, 0, 0)
    S.finish(league)
    assert league.staff["stage"] is None


def test_finish_refuses_an_open_place():
    league = at_stage(league_of())
    S.begin(league)
    league.staff["coordinators"][3][0] = None
    with pytest.raises(LeagueError):
        S.finish(league)


def test_settle_is_the_programs_steps_with_the_staffs_answers():
    def made():
        league = at_stage(league_of(seed=4))
        for team in (TEAM, 8, 17):
            judged(league, team, 10, 3)
        return league
    one, two = made(), made()
    S.settle(one, GameRandom(random.Random(9)), SURNAMES)
    state = S.begin(two)
    S.take_job(two, state["offers"][0])
    S.hire_head_coaches(two, staff=True)
    S.draw_candidates(two, GameRandom(random.Random(9)), SURNAMES, staff=True)
    S.finish(two)
    assert one.to_json() == two.to_json() and one.team == state["offers"][0] != TEAM


# ----- the games -----

def test_the_teams_styles_are_the_coordinators_and_none_while_a_place_is_open():
    league = league_of()
    S.coordinator_of(league, 3, 1)["style"] = "pressure"
    assert S.team_styles(league)[2][1] == "pressure"
    league.staff["coordinators"][3][1] = None
    assert S.team_styles(league) is None


def test_the_staffs_game_plan_is_a_good_coordinators_answer_to_the_opponent_and_a_lesser_ones_own_style():
    league = league_of()
    styles = set(DEFAULT_TABLE.styles)
    oc, dc = S.coordinator_of(league, TEAM, 0), S.coordinator_of(league, TEAM, 1)
    oc.update(rating=T.FR_COORD_ADAPT, style="power")
    dc.update(rating=T.FR_COORD_ADAPT - 1, style="zone")
    assert S.recommended(league, 0, "pressure", styles) == T.FR_GAME_PLAN["offense"]["pressure"]
    assert S.recommended(league, 1, "air", styles) == "zone"
    assert S.recommended(league, 1, "air", styles - {"zone"}) == "classic"


def test_a_game_outside_a_franchise_has_no_franchise_styles():
    class Game:
        pass
    game = Game()
    assert S.game_team_styles(game) is None
    game.franchise_styles = lambda: (("air", "air"),) * 32
    assert S.game_team_styles(game)[0] == ("air", "air")


# ----- the file -----

def test_format_7_round_trips_with_a_stage_in_progress():
    league = at_stage(league_of())
    judged(league, TEAM, 20, 4)
    S.begin(league)
    text = league.to_json()
    assert json.loads(text)["format"] == D.FORMAT == 19          # (12 since SZ.8; SR.5: 19, no places stored)
    again = LeagueRecord.from_json(text)
    assert again.staff == league.staff and again.to_json() == text


def test_a_format_6_file_gets_a_new_leagues_staff_by_the_migration_with_no_draw():
    league = league_of()
    data = legacy_data(league)
    del data["staff"]
    data["format"] = 6
    loaded = LeagueRecord.from_json(json.dumps(data))
    fresh = league_of()
    assert loaded.staff == fresh.staff and json.loads(loaded.to_json())["format"] == D.FORMAT == 19      # SR.5: format 19


def test_a_format_7_file_without_its_staff_is_damage():
    data = json.loads(league_of().to_json())
    del data["staff"]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


@pytest.mark.parametrize("mutate", [
    lambda s: s.update(extra=1), lambda s: s.update(coaches=s["coaches"][:31]), lambda s: s["coaches"].__setitem__(3, None),
    lambda s: s["coordinators"][3].__setitem__(0, None), lambda s: s["coaches"][2].update(approval=101), lambda s: s["coaches"][2].update(approval=-1),
    lambda s: s["coaches"][2].update(goal=["points", 3]), lambda s: s["coaches"][2].update(goal=["wins", 19]), lambda s: s["coaches"][2].update(name=""),
    lambda s: s["coaches"][2].update(last=[19, 0, 0, 60]), lambda s: s["coaches"][2].update(last=[8, 6, 0, 60]), lambda s: s["coaches"][2].update(last=[8, 0, 2, 60]),
    lambda s: s["coaches"][2].update(last=[8, 0]), lambda s: s["coaches"][2].pop("seasons"), lambda s: s["coordinators"][2][1].update(style="nonsense"),
    lambda s: s["coordinators"][2][1].update(rating=100), lambda s: s["coordinators"][2][1].update(rating=39), lambda s: s["coordinators"][2].append(None),
    lambda s: s["coordinators"][2][0].update(name="a\x01b"), lambda s: s.update(stage={"step": "draw"})])
def test_a_damaged_staff_is_refused(mutate):
    league = league_of()
    mutate(league.staff)
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


@pytest.mark.parametrize("mutate", [
    lambda st: st.update(step="nonsense"), lambda st: st.update(fired=[33]), lambda st: st.update(offers=[TEAM]), lambda st: st.update(offers=[1, 2, 3, 4]),
    lambda st: st.update(hired=[[1, 2, 0]]), lambda st: st["candidates"].update({"40:0": []}), lambda st: st["candidates"].update({"3:2": []}),
    lambda st: st["candidates"].update({"3:0": [S.new_coordinator("A", "air", 70)] * 4}), lambda st: st.update(approval=101), lambda st: st.pop("new"),
    lambda st: st.update(step=S.STEP_JOB, offers=[]), lambda st: st["candidates"].update({"3:0": [S.new_coordinator("A", "air", 30)]})])
def test_a_damaged_stage_of_the_staff_is_refused(mutate):
    league = at_stage(league_of())
    judged(league, TEAM, 20, 4)
    S.begin(league)
    LeagueRecord.from_json(league.to_json())
    mutate(league.staff["stage"])
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_an_open_place_or_a_stage_record_outside_the_stage_is_damage():
    league = at_stage(league_of())
    judged(league, TEAM, 20, 4)
    S.begin(league)
    league.stage_no = D.STAGE_AGING
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_the_stage_list_has_the_staff_right_after_the_season_in_review():
    numbers = [n for n, _ in D.STAGES]
    assert numbers.index(D.STAGE_STAFF) == numbers.index(D.STAGE_REVIEW) + 1 and dict(D.STAGES)[D.STAGE_STAFF] == "NXE-19"


def test_draft_league_of_the_rig_still_loads_at_the_staff_stage():
    league = draft_league(stage_no=D.STAGE_STAFF)
    assert LeagueRecord.from_json(league.to_json()).stage_no == D.STAGE_STAFF


def test_a_new_leagues_computer_coaches_are_past_their_grace_with_a_spread_of_ratings_and_the_player_is_new():
    league = league_of()
    ratings = [S.coach_of(league, t)["approval"] for t in range(1, 33) if t != TEAM]
    base, span, _stride = T.FR_APPROVAL_LEAGUE_START
    assert min(ratings) >= base and max(ratings) < base + span and len(set(ratings)) >= 25
    assert all(S.coach_of(league, t)["seasons"] > T.FR_FIRE_GRACE for t in range(1, 33) if t != TEAM)
    assert S.coach_of(league, TEAM)["seasons"] == 0 and S.coach_of(league, TEAM)["approval"] == T.FR_APPROVAL_START


def test_the_offers_let_a_coach_in_his_grace_go_only_when_no_other_is_left():
    league = at_stage(league_of())
    for team in range(1, 33):
        judged(league, team, 70, 10)                         # everybody won ...
    judged(league, 17, 30, 8, seasons=1)                     # ... but team 17, whose new coach is in his grace (the lowest rating of all)
    for team in (20, 21, 22):
        judged(league, team, 90, 8)                          # and three teams past their grace, rated 90
    assert sorted(S.offers(league, TEAM)) == [20, 21, 22]
    judged(league, 22, 90, 9)
    assert sorted(S.offers(league, TEAM)) == [17, 20, 21]    # only two others are left: the coach in his grace is the third


def test_a_candidate_never_takes_a_name_of_the_staff():
    league = at_stage(league_of())
    S.begin(league)
    S.hire_head_coaches(league, staff=True)
    league.staff["coordinators"][1][1] = None                         # team 2's defense is open
    taken = S.coach_of(league, 9)["name"]
    other = S.coordinator_of(league, 4, 0)["name"]
    used = FN.name_keys(league.league_id, (p.name for p in league.players.values())) | {"Kim"} | {c["name"] for c in league.staff["coaches"] if c is not None}         | {c["name"] for pair in league.staff["coordinators"] for c in pair if c is not None}
    free = [n for n, name in enumerate(SURNAMES, start=1) if name not in used]
    source = ScriptedRandom(strict=True)
    source.values += [value_for(len(SURNAMES), SURNAMES.index(taken) + 1), value_for(len(SURNAMES), SURNAMES.index(other) + 1),
                      value_for(len(SURNAMES), free[0])]                  # a head coach's name, a coordinator's name, then a free one
    source.values += [below_value(7, 0), below_value(21, 0), below_value(21, 0)]
    for k in (1, 2):
        source.values += [value_for(len(SURNAMES), free[k]), below_value(7, 0), below_value(21, 0), below_value(21, 0)]
    S.draw_candidates(league, GameRandom(source), SURNAMES, staff=True)
    assert source.left == 0
    names = [c["name"] for c in league.staff["stage"]["candidates"]["2:1"]]
    assert taken not in names and other not in names and SURNAMES[free[0] - 1] in names


def test_a_damaged_row_of_the_stage_or_an_open_place_that_does_not_fit_the_step_is_refused():
    def at_pick():
        league = at_stage(league_of())
        S.begin(league)
        S.hire_head_coaches(league, staff=False)
        S.own_sides(league, [0])
        S.draw_candidates(league, GameRandom(random.Random(1)), SURNAMES, staff=False)
        LeagueRecord.from_json(league.to_json())
        return league
    for mutate in (lambda st, lg: st.update(hired=[["a", "b", "c", "d"]]), lambda st, lg: st.update(hired=[[1, 2, 7, "X"]]),
                   lambda st, lg: st.update(lost=[[5, "X", 3]]), lambda st, lg: st.update(hired=[[[1], 4, 0, "x"]]),
                   lambda st, lg: st.update(new=[[3, 0, ""]]), lambda st, lg: st.update(replaced=[[0, 0, "X"]]),
                   lambda st, lg: lg.staff["coaches"].__setitem__(8, None), lambda st, lg: lg.staff["coordinators"][8].__setitem__(1, None),
                   lambda st, lg: st["candidates"].pop("%d:0" % TEAM)):
        league = at_pick()
        mutate(league.staff["stage"], league)
        with pytest.raises(LeagueError):
            LeagueRecord.from_json(league.to_json())
    league = at_stage(league_of())
    S.begin(league)
    league.staff["coaches"][TEAM - 1] = None                          # the player's place open while he does not wait for an offer
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_the_coordinators_not_team_styles_choose_the_books_of_a_franchise_game_and_the_file_outside_it():
    from nfl4.extras.nfl_rules import NflRules
    from nfl4.extras.playbook_flow import PlaybookFlow
    from nfl4.extras.state import ExtrasRecord

    class Season:
        tn1, tn2, tn3, tn4 = 2, 1, 5, 3                                # team 5 against team 19

    class Game:
        playbook_table = None
        season = Season()

    rules = NflRules(offense_book="team", defense_book="team", playbooks_on=True)
    styles = tuple(("option", "zone") if t == 4 else ("power", "pressure") if t == 18 else ("pro", "pro") for t in range(32))
    assert PD.TEAM_STYLES[4] != ("option", "zone") and PD.TEAM_STYLES[18] != ("power", "pressure")

    class State:
        extras = ExtrasRecord()

    game = Game()
    game.franchise_styles = lambda: styles
    flow = PlaybookFlow(rules)
    state = State()
    flow.resolve(game, state)
    assert state.extras.offense_book == ["option", "power"] and state.extras.defense_book == ["zone", "pressure"]
    game.franchise_styles = None                                       # outside the franchise: team_styles.txt's assignment
    flow.resolve(game, state)
    assert state.extras.offense_book == [PD.TEAM_STYLES[4][0], PD.TEAM_STYLES[18][0]]
    assert state.extras.defense_book == [PD.TEAM_STYLES[4][1], PD.TEAM_STYLES[18][1]]


def test_the_offers_are_at_most_three_and_listed_by_rank():
    league = season_judged(at_stage(league_of()))
    ranks = {t: n for n, t in enumerate(league.ranking(), start=1)}
    open_places = [t for t in sorted(range(1, 33), key=lambda t: ranks[t], reverse=True) if t != TEAM][:5]       # the five weakest: open
    for team in open_places:
        league.staff["coaches"][team - 1] = None
    got = S.offers(league, TEAM)
    assert got == sorted(open_places, key=lambda t: ranks[t])[:T.FR_OFFERS]
    league = season_judged(at_stage(league_of()))
    order = sorted((t for t in range(1, 33) if t != TEAM), key=lambda t: ranks[t])
    for n, team in enumerate(reversed(order)):                         # the weakest has the lowest job rating: let go first, but listed by rank
        judged(league, team, 20 + n, 8)
    got = S.offers(league, TEAM)
    assert sorted(got) == sorted(list(reversed(order))[:3]) and got == sorted(got, key=lambda t: ranks[t]) and got != list(reversed(order))[:3]


def test_a_coordinator_rated_at_the_keep_line_is_kept():
    league = at_stage(league_of())
    for team in range(1, 33):
        for side in S.SIDES:
            S.coordinator_of(league, team, side)["rating"] = 70
    S.coordinator_of(league, 7, 0)["rating"] = T.FR_COORD_KEEP
    S.coordinator_of(league, 8, 0)["rating"] = T.FR_COORD_KEEP - 1
    S.begin(league)
    S.hire_head_coaches(league, staff=True)
    assert S.coordinator_of(league, 7, 0) is not None and S.coordinator_of(league, 8, 0) is None
