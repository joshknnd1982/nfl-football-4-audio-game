"""The staff on the program rig: stage 1's verdict, the stage "the staff" (stage 2 of 9), the goal at the season's start and F9's job and staff (nfl4 only,
rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8l, D-072). The rules are test_fr_staff.py.
"""
import copy
import json

import pytest

from drrig import at_stage, draft_league, offseason_rig, saved_league
from frrig import DOWN, ENTER, ESC, F9, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import staff as S
from nfl4.extras.franchise import staff_flow as SF
from nfl4.extras.franchise.league import LeagueError, LeagueRecord

TEAM = 5
HEADER = " stage 2 of 9. the staff. "


def staff_league(seed=3, player_approval=70, player_wins=8, mutate=None):
    """A league at the start of the stage of the staff, every coach judged after a season of 8 wins (none of them winning), every coordinator rated 70
    (nobody replaced by the rule); the player's coach with `player_approval` after `player_wins` wins."""
    wins = [8] * 32
    wins[TEAM - 1] = player_wins
    league = draft_league(seed=seed, team=TEAM, stage_no=D.STAGE_STAFF, wins=wins, finish=[0] * 32)
    for team in range(1, 33):
        S.coach_of(league, team).update(approval=70, seasons=3, last=[wins[team - 1], 0, 0, 70])
        for side in S.SIDES:
            S.coordinator_of(league, team, side)["rating"] = 70
    S.coach_of(league, TEAM).update(approval=player_approval)
    if mutate is not None:
        mutate(league)
    return league


def run(tmp_path, league, keys=(), until=None, **kwargs):
    return offseason_rig(tmp_path, league, keys=keys, until=until or at_stage(D.STAGE_AGING), **kwargs)


def past_staff(rig):
    store = rig.fstore
    league = store.league if store is not None else None
    return league is not None and league.stage != "season" and league.stage_no not in (D.STAGE_REVIEW, D.STAGE_STAFF)


def offers_of(league):
    trial = copy.deepcopy(league)
    return S.begin(trial)["offers"]


# ----- stage 1: the verdict -----

def test_stage_one_says_the_owners_goal_met_or_missed_and_the_job_rating_and_keeps_it_after_the_wait(tmp_path):
    league = draft_league(team=TEAM, stage_no=D.STAGE_REVIEW)
    goal = S.coach_of(league, TEAM)["goal"]
    expected = SF.verdict_lines(league, [8] * 32, [0] * 32)
    rig = run(tmp_path, league, until=at_stage(D.STAGE_STAFF))
    text = spoken(rig)
    met = S.goal_met(goal, 8, 0)
    assert expected[0] == X.text("NXV-01" if met else "NXV-02", goal=SF.goal_text(goal)) and all(line in text for line in expected)
    after, _ = S.new_approval(T.FR_APPROVAL_START, goal, 8, 0)
    saved = saved_league(rig)
    coach = S.coach_of(saved, TEAM)
    assert coach["approval"] == after and coach["last"] == [8, 0, int(met), T.FR_APPROVAL_START] and coach["seasons"] == 1
    hired = {row[0] for row in saved.staff["stage"]["hired"]} if saved.staff["stage"] is not None else set()      # stage 9 has begun: its new head coaches
    assert all(S.coach_of(saved, t)["last"] is not None for t in range(1, 33) if t not in hired)                     # have no season judged yet


def test_a_low_job_rating_is_a_warning_and_a_rise_or_a_fall_is_said_with_its_size():
    league = draft_league(team=TEAM, stage_no=D.STAGE_REVIEW)
    S.coach_of(league, TEAM).update(approval=T.FR_FIRE_BELOW + 2, goal=["wins", 12])
    lines = SF.verdict_lines(league, [8] * 32, [0] * 32)
    after = T.FR_FIRE_BELOW + 2 - T.FR_APPROVAL_GOAL[1]
    assert lines == [X.text("NXV-02", goal=X.text("NXV-G01", n=12)), X.text("NXV-04", a=after, d=T.FR_APPROVAL_GOAL[1]), X.text("NXV-06")]
    S.coach_of(league, TEAM).update(approval=70, goal=["playoffs", 0])
    lines = SF.verdict_lines(league, [8] * 32, [D.FINISH_WILD_CARD if t == TEAM - 1 else 0 for t in range(32)])
    up = T.FR_APPROVAL_GOAL[0] + T.FR_APPROVAL_FINISH[1]
    assert lines == [X.text("NXV-01", goal=X.text("NXV-G02")), X.text("NXV-03", a=70 + up, d=up)]
    S.coach_of(league, TEAM).update(approval=100, goal=["wins", 8])
    assert SF.verdict_lines(league, [8] * 32, [0] * 32)[1] == X.text("NXV-05", a=100)


# ----- the stage of the staff -----

def test_a_fired_player_hears_why_chooses_among_other_teams_and_the_job_is_written_before_it_is_told(tmp_path):
    league = staff_league(player_approval=20, player_wins=4)
    offers = offers_of(league)
    assert TEAM not in offers and len(offers) == T.FR_OFFERS
    rig = run(tmp_path, league, keys=[DOWN, ENTER], keep=True)            # the second offer
    text = spoken(rig)
    words = rig.fstore.words
    assert HEADER in text and X.text("NXV-10", a=20, w=4, l=12) in text and X.text("NXV-11", coach="Kim") in text
    told = text.index(X.text("NXV-12", team=words.team_name(offers[1])))
    saved = saved_league(rig)
    assert saved.team == offers[1] and S.coach_of(saved, TEAM)["name"] != "Kim" and S.coach_of(saved, offers[1])["approval"] == T.FR_APPROVAL_START
    first_move = next(said for _stage, _pick, _count, raw, said in rig.saves if raw is not None and json.loads(raw)["team"] == offers[1])
    assert first_move <= told                                              # B-X53: written before it is told
    from nfl4.extras.franchise.league import team_ref
    assert (rig.game.season.tn1, rig.game.season.tn2) == team_ref(offers[1])        # the season's own team follows at once
    for number, t in enumerate(offers[:2], start=1):                      # the first item is said with the question, the second after Down
        assert " %d. %s " % (number, X.text("NXV-A01", team=words.team_name(t), r=league.strength(t), k=league.rank_of(t)).strip()) in text


def test_the_player_who_keeps_his_job_keeps_or_replaces_his_coordinators_and_picks_the_new_one_among_three(tmp_path):
    league = staff_league()
    keys = [DOWN, ENTER, DOWN, DOWN, ENTER]                               # replace the offensive coordinator; the third candidate
    rig = run(tmp_path, league, keys=keys, keep=True)
    text = spoken(rig)
    assert X.text("NXV-22", coach="Kim") in text and X.text("NXV-23") in text and X.text("NXV-24") not in text
    pick = next(json.loads(raw) for _s, _p, _c, raw, _n in rig.saves if raw is not None and json.loads(raw)["staff"]["stage"] is not None
                and json.loads(raw)["staff"]["stage"]["step"] == S.STEP_PICK)
    candidates = pick["staff"]["stage"]["candidates"]["%d:0" % TEAM]
    saved = saved_league(rig)
    assert S.coordinator_of(saved, TEAM, 0) == candidates[2] and [c["rating"] for c in candidates] == sorted((c["rating"] for c in candidates), reverse=True)
    assert S.coordinator_of(saved, TEAM, 1) == S.coordinator_of(league, TEAM, 1)
    assert X.text("NXV-25", name=candidates[2]["name"]) in text


def test_keep_them_changes_nothing_of_the_players_staff_and_asks_for_no_candidate(tmp_path):
    league = staff_league()
    rig = run(tmp_path, league)                                           # Enter: the staff's recommendation, keep them (every coordinator rated 70)
    saved = saved_league(rig)
    assert saved.staff["coordinators"][TEAM - 1] == league.staff["coordinators"][TEAM - 1]
    assert X.text("NXV-23") not in spoken(rig) and X.text("NXV-24") not in spoken(rig)


def test_the_staffs_recommendation_is_the_first_answer_when_the_rule_would_replace_a_coordinator(tmp_path):
    league = staff_league(mutate=lambda lg: S.coordinator_of(lg, TEAM, 1).update(rating=T.FR_COORD_KEEP - 1))
    rig = run(tmp_path, league)
    text = spoken(rig)
    at = text.index(X.text("NXV-22", coach="Kim"))
    assert text[at + 1] == " 1. %s " % X.text("NXV-A04").strip() and X.text("NXV-24") in text


def test_with_the_staff_setting_on_nothing_is_asked_and_the_staff_follows_the_computer_teams_rule(tmp_path):
    league = staff_league(player_approval=20, player_wins=4, mutate=lambda lg: S.coordinator_of(lg, TEAM, 1).update(rating=50))
    offers = offers_of(league)
    rig = run(tmp_path, league, auto=True)
    text = spoken(rig)
    assert X.text("NXV-11", coach="Kim") not in text and X.text("NXV-22", coach="Kim") not in text and X.text("NXV-23") not in text
    saved = saved_league(rig)
    assert saved.team == offers[0]                                        # the best ranked offer
    for side in S.SIDES:                                                  # a new head coach: the rule replaces both, with the best candidate
        assert S.coordinator_of(saved, saved.team, side)["name"] != S.coordinator_of(league, offers[0], side)["name"]


def test_the_menus_first_answers_make_the_league_the_staff_makes(tmp_path):
    league = staff_league(player_approval=20, player_wins=4, mutate=lambda lg: S.coordinator_of(lg, 9, 0).update(rating=95))
    by_menu = run(tmp_path / "menu", copy.deepcopy(league))
    by_staff = run(tmp_path / "staff", copy.deepcopy(league), auto=True)
    assert saved_league(by_menu).to_json() == saved_league(by_staff).to_json()


def test_a_window_closed_at_the_job_question_resumes_there_with_the_same_offers(tmp_path):
    league = staff_league(player_approval=20, player_wins=4)
    offers = offers_of(league)
    first = run(tmp_path / "one", league, until=lambda r: X.text("NXV-11", coach="Kim") in spoken(r))
    saved = saved_league(first)
    assert saved.staff["stage"]["step"] == S.STEP_JOB and saved.staff["stage"]["offers"] == offers and saved.team == TEAM
    second = run(tmp_path / "two", None, files=first.files, keys=[DOWN, DOWN, ENTER])
    final = saved_league(second)
    assert final.team == offers[2] and X.text("NXV-11", coach="Kim") in spoken(second)
    assert final.staff["coaches"][TEAM - 1]["name"] != "Kim"


def test_a_window_closed_at_the_candidates_resumes_with_the_same_candidates(tmp_path):
    league = staff_league()
    first = run(tmp_path / "one", league, keys=[DOWN, ENTER], until=lambda r: X.text("NXV-23") in spoken(r))
    saved = saved_league(first)
    candidates = saved.staff["stage"]["candidates"]["%d:0" % TEAM]
    second = run(tmp_path / "two", None, files=first.files)
    assert S.coordinator_of(saved_league(second), TEAM, 0) == candidates[0] and X.text("NXV-23") in spoken(second)


def test_the_short_offseason_still_asks_and_ends_the_stage_without_a_wait(tmp_path):
    league = staff_league()
    rig = run(tmp_path, league, short=True, until=past_staff)            # the short stages after it wait for nothing: the next wait is the draft's
    text = spoken(rig)
    assert X.text("NXV-22", coach="Kim") in text
    at = text.index(X.text("NXV-22", coach="Kim"))
    assert X.text("NXE-03") not in text[at:]


def test_the_league_lines_name_at_most_three_hires_and_the_players_coordinator_who_left(tmp_path):
    def change(lg):
        for team in (11, 12, 13, 14):
            S.coach_of(lg, team).update(approval=10)
        S.coordinator_of(lg, TEAM, 0).update(rating=99)
    league = staff_league(mutate=change)
    rig = run(tmp_path, league)
    text = spoken(rig)
    words = rig.fstore.words
    name = S.coordinator_of(league, TEAM, 0)["name"]
    assert X.text("NXV-13", n=4) in text and X.text("NXV-17", name=name, team=words.team_name(11)) in text
    assert sum(1 for t in text if " as head coach. " in t) == 3


# ----- the goal at the season's start, F9 -----

def test_the_new_season_says_the_owners_goal(tmp_path):
    league = draft_league(team=TEAM, stage_no=D.STAGE_NEW_SEASON)
    weakest = league.ranking()[-1]
    old_goal = list(S.coach_of(league, weakest)["goal"])
    for player in league.active_of(weakest):                          # the weakest team of season 1 is the strongest of season 2
        player.rating = 95
    rig = offseason_rig(tmp_path, league)
    assert S.coach_of(rig.fstore.league, weakest)["goal"] == S.goal_for(1) != old_goal
    final = rig.fstore.league
    assert SF.goal_line(final) in spoken(rig) and final.season == 2
    for rank, team in enumerate(final.ranking(), start=1):           # the goals were set again by the rank at the new season's start
        assert S.coach_of(final, team)["goal"] == S.goal_for(rank)


def test_f9_has_your_job_and_staff_with_the_goal_the_job_rating_and_the_coordinators(tmp_path, monkeypatch):
    from nfl4.extras.franchise import menus
    lists = []
    real = menus._lines_picker

    def picker(speech, keys, title, lines):
        lists.append((title, list(lines)))
        real(speech, keys, title, lines)
    monkeypatch.setattr(menus, "_lines_picker", picker)
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 9 + [ENTER, ESC, ESC, ESC, ESC]       # F9, Franchise, your job and staff (the 10th item)
    rig = offseason_rig(tmp_path, staff_league(), keys=keys, until=lambda r: bool(lists))
    league = rig.fstore.league
    coach = S.coach_of(league, TEAM)
    oc, dc = S.coordinator_of(league, TEAM, 0), S.coordinator_of(league, TEAM, 1)
    assert lists[0] == (X.text("NXF-45"), [X.text("NXV-30", goal=SF.goal_text(coach["goal"])), X.text("NXV-31", a=coach["approval"]),
                                           X.text("NXV-20", name=oc["name"], style=SF.style_name(oc["style"]), r=oc["rating"]),
                                           X.text("NXV-21", name=dc["name"], style=SF.style_name(dc["style"]), r=dc["rating"])])


def test_a_league_saved_in_the_stage_loads_with_its_stage_record():
    league = staff_league(player_approval=20, player_wins=4)
    S.begin(league)
    assert LeagueRecord.from_json(league.to_json()).staff == league.staff


def test_the_pick_and_the_answer_about_the_coordinators_are_written_before_they_are_told(tmp_path):
    league = staff_league()
    rig = run(tmp_path, league, keys=[DOWN, ENTER, DOWN, ENTER], keep=True)          # replace the offensive coordinator; the second candidate
    text = spoken(rig)
    files = [(json.loads(raw), said) for _s, _p, _c, raw, said in rig.saves if raw is not None]
    assert any(data["staff"]["stage"] is not None and data["staff"]["stage"]["step"] == S.STEP_DRAW for data, _said in files)    # the answer, before the draws
    hired = S.coordinator_of(saved_league(rig), TEAM, 0)
    told = text.index(X.text("NXV-25", name=hired["name"]))
    assert any(data["staff"]["coordinators"][TEAM - 1][0] == hired and said <= told for data, said in files)


def test_with_one_coordinator_hired_away_and_the_other_under_the_line_the_first_answer_is_replace_him(tmp_path):
    def change(lg):
        S.coach_of(lg, 11).update(approval=10)                        # team 11 fires its coach and takes the best coordinator: the player's offense
        S.coordinator_of(lg, TEAM, 0).update(rating=99)
        S.coordinator_of(lg, TEAM, 1).update(rating=T.FR_COORD_KEEP - 1)
    rig = run(tmp_path, staff_league(mutate=change))
    text = spoken(rig)
    at = text.index(X.text("NXV-22", coach="Kim"))
    assert text[at + 1] == " 1. %s " % X.text("NXV-A07").strip()
    assert X.text("NXV-23") in text and X.text("NXV-24") in text       # both places get candidates: the open one and the one he replaced


def test_a_fired_player_who_moves_hears_no_your_coordinator_left_about_his_new_team_and_no_warning_after_a_winning_season(tmp_path):
    league = staff_league(player_approval=20, player_wins=4, mutate=lambda lg: S.coordinator_of(lg, 1, 0).update(rating=99))
    rig = run(tmp_path, league, keys=[ENTER])
    assert not any(" your offensive coordinator " in t and " left to be head coach " in t for t in spoken(rig))
    review = draft_league(team=TEAM, stage_no=D.STAGE_REVIEW)
    S.coach_of(review, TEAM).update(approval=T.FR_FIRE_BELOW, goal=["wins", 16])
    wins = [8] * 32
    wins[TEAM - 1] = 9
    assert X.text("NXV-06") not in SF.verdict_lines(review, wins, [0] * 32)
    wins[TEAM - 1] = 8
    assert X.text("NXV-06") in SF.verdict_lines(review, wins, [0] * 32)


def test_a_season_of_one_win_is_said_in_the_singular(tmp_path):
    rig = run(tmp_path, staff_league(player_approval=20, player_wins=1), keys=[ENTER])
    assert X.text("NXV-09", a=20, l=15) in spoken(rig)


def game_plan_rig(tmp_path, monkeypatch, keys):
    """A new franchise whose every coordinator plays the style after his team's in team_styles.txt (so the coordinators and the file never agree), the
    player's playbooks his team's: week 1's game plan item and game."""
    from frrig import COACH_AND_TEAM, WANT_FRANCHISE, franchise_rig, run_until
    from frrig import quit_policy
    from nfl4.extras import playbook_data as PD
    real = S.new_staff

    def shifted(league, surnames, team_styles=PD.TEAM_STYLES):
        real(league, surnames, team_styles)
        keys_ = S.STYLE_KEYS
        for team in range(1, 33):
            for side in S.SIDES:
                c = S.coordinator_of(league, team, side)
                c["style"] = keys_[(keys_.index(PD.TEAM_STYLES[team - 1][side]) + 1) % len(keys_)]
    monkeypatch.setattr(S, "new_staff", shifted)
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy)
    settings = rig.game.options.settings.game
    settings.nx_offense_playbook = settings.nx_defense_playbook = "team"
    rig.game.apply_rules_setting()
    return run_until(rig)


def test_the_game_plan_names_the_opponents_coordinators_styles_not_the_files(tmp_path, monkeypatch):
    from nfl4.extras import playbook_data as PD
    from nfl4.extras.franchise.league import team_index
    from nfl4.extras.playbooks import DEFAULT_TABLE
    rig = game_plan_rig(tmp_path, monkeypatch, [])
    league = rig.fstore.league
    division, place, _flag = league.schedule[0]
    opponent = team_index(division, place)
    keys_ = S.STYLE_KEYS
    theirs = [keys_[(keys_.index(PD.TEAM_STYLES[opponent - 1][side]) + 1) % len(keys_)] for side in S.SIDES]
    assert tuple(theirs) != PD.TEAM_STYLES[opponent - 1]
    prompt = next(t for t in spoken(rig) if t.startswith(" the game plan against the "))
    assert " they play %s on offense and %s on defense. " % (DEFAULT_TABLE.style_name(theirs[0]), DEFAULT_TABLE.style_name(theirs[1])) in prompt


def test_leaving_the_franchise_clears_its_styles_and_a_classic_season_plays_the_files(tmp_path):
    from frrig import COACH_AND_TEAM, WANT_FRANCHISE, franchise_rig, quit_policy, run_until
    rig = run_until(franchise_rig(tmp_path / "in", WANT_FRANCHISE + COACH_AND_TEAM, policy=quit_policy))
    assert rig.game.franchise_styles is not None and rig.game.franchise_styles() == S.team_styles(rig.fstore.league)
    keys = WANT_FRANCHISE + COACH_AND_TEAM + [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 11 + [ENTER, ENTER, ESC]     # play classic seasons (12th)
    rig = run_until(franchise_rig(tmp_path / "out", keys, policy=quit_policy))
    assert rig.game.program.mode.kind == "classic" and rig.game.franchise_styles is None
    assert S.game_team_styles(rig.game) is None


def test_a_new_franchise_says_the_owners_goal_of_season_one(tmp_path):
    from frrig import COACH_AND_TEAM, WANT_FRANCHISE, franchise_rig, quit_policy, run_until
    rig = run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=quit_policy))
    league = rig.fstore.league
    assert league.season == 1 and SF.goal_line(league) in spoken(rig)


def test_an_empty_roster_place_at_the_stage_of_the_staff_is_damage():
    league = staff_league()
    gone = league.player_at(4, 0)
    league.rosters[3][0] = 0
    gone.status, gone.team, gone.place, gone.left, gone.salary, gone.years = "retired", 0, -1, league.season, 0, 0
    league.stage_no = D.STAGE_AGING                                      # stage 2 may have empty places: the file loads ...
    LeagueRecord.from_json(league.to_json())
    league.stage_no = D.STAGE_STAFF                                      # ... stage 9 (before the retirements) may not
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(league.to_json())


def test_f9_your_job_and_staff_says_he_was_fired_while_the_job_question_waits(tmp_path, monkeypatch):
    from nfl4.extras.franchise import menus
    lists = []
    real = menus._lines_picker

    def picker(speech, keys, title, lines):
        lists.append((title, list(lines)))
        real(speech, keys, title, lines)
    monkeypatch.setattr(menus, "_lines_picker", picker)
    keys = [F9, DOWN, DOWN, DOWN, DOWN, ENTER] + [DOWN] * 9 + [ENTER, ESC, ESC, ESC, ESC]       # at the job question: F9, Franchise, your job and staff
    run(tmp_path, staff_league(player_approval=20, player_wins=4), keys=keys, until=lambda r: bool(lists))
    assert lists[0] == (X.text("NXF-45"), [X.text("NXV-32")])
