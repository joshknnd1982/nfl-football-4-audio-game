"""A week of the Franchise on the program rig: the news, the to-do list and its deadline, the staff's setting, the F9 items and the
help (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3.4, 8 and 11 (SX.8e). The program is the whole program on the rig of tests/frrig.py (the N. F. L. rules, a
franchise in memory, a stand-in for pag whose scores the test sets, the real season engine). An answer script lists the key of every
wait in order; a regular week's game takes three waits (the menu, the results, the standings). The rules themselves are tested in
tests/test_fr_todo.py and tests/test_fr_news.py.
"""
from drrig import at_stage, draft_league, offseason_rig, saved_league
from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F1, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until,
                   spoken)
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import staff as ST
from nfl4.extras.franchise import todo, weekly
from nfl4.extras.franchise.league import team_index
from nfl4.extras.playbooks import DEFAULT_TABLE
from nfl4.game.keys import GameQuit

GAME = [ENTER, ENTER, ENTER]
TO_FRANCHISE_MENU = [F9] + [DOWN] * 4 + [ENTER]               # F9, down to the Franchise item, into it
ANSWER_LATER = [DOWN, DOWN, DOWN, ENTER]                      # extra work: the two candidates, nobody this week, later
SELECT = " kim select "


def league(rig):
    return rig.fstore.league


def run(tmp_path, keys, nfl=True, setup=None, **kwargs):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy, **kwargs)
    if setup is not None:
        setup(rig)
    return run_until(rig)


def team_points(rig):
    record = league(rig)
    return sum(p.points for p in record.active_of(record.team) if p is not None)


def at(text, sentence, start=0):
    return start + text[start:].index(sentence)


# ----- the order of a week, once -----

def test_a_week_speaks_the_news_then_the_to_do_list_then_the_coachs_select_and_none_of_them_again_on_f1(tmp_path):
    rig = run(tmp_path, GAME + [ENTER, F1, F1])
    text = spoken(rig)
    week2 = at(text, " This is week  2 of Josh Kennedy's N. F. L. football ")
    news = at(text, X.text("NXN-01"), week2)
    listing = at(text, X.text("NXD-02", coach="kim"), news)
    item = at(text, X.text("NXD-05", n=1), listing)
    prompt = at(text, X.text("NXD-10"), item)
    select = at(text, SELECT, prompt)
    assert week2 < news < listing < item < prompt < select
    assert text.count(X.text("NXN-01")) == 1 and text.count(X.text("NXD-10")) == 1 and text.count(X.text("NXD-02", coach="kim")) == 1
    assert text[news + 1:listing] and all(" Games " not in t for t in text[news + 1:listing])        # the lines of the news


def test_week_1_has_no_news_and_no_extra_work_but_says_the_season_line(tmp_path):
    rig = run(tmp_path, [])
    text = spoken(rig)
    assert X.text("NXF-08", n=1) in text and X.text("NXN-01") not in text and X.text("NXD-10") not in text
    assert text.index(X.text("NXF-08", n=1)) < text.index(SELECT)


def test_the_news_lines_are_the_lines_of_the_record_told_once(tmp_path):
    rig = run(tmp_path, GAME + [ENTER, F1])
    text = spoken(rig)
    kept = [e for e in league(rig).news if e["week"] == 1]
    assert 2 <= len(kept) <= T.FR_NEWS_MAX and all(e["told"] == 1 for e in kept)
    for entry in kept:
        assert text.count(entry["markup"]) == 1


# ----- extra work -----

def test_the_first_answer_gives_the_first_candidate_a_point(tmp_path):
    rig = run(tmp_path, GAME + [ENTER])
    record = league(rig)
    assert record.todo == [] and team_points(rig) == 1
    player = next(p for p in record.active_of(record.team) if p.points == 1)
    assert X.text("NXD-11", player=player.name) in spoken(rig)


def test_nobody_this_week_gives_no_point(tmp_path):
    rig = run(tmp_path, GAME + [DOWN, DOWN, ENTER])
    assert league(rig).todo == [] and team_points(rig) == 0
    assert not any(" gets extra work this week. " in t for t in spoken(rig))


def test_later_keeps_the_item_and_the_kick_off_closes_it_without_a_point_and_says_so(tmp_path):
    rig = run(tmp_path, GAME + ANSWER_LATER + [ENTER] + ANSWER_LATER)       # later, play game (asked again), later again
    record = league(rig)
    text = spoken(rig)
    assert X.text("NXD-06", n=1) in text and X.text("NXD-30") in text
    assert text.index(X.text("NXD-06", n=1)) < text.index(X.text("NXD-30"))
    assert record.todo == [] and team_points(rig) == 0                     # nothing was decided for the player


def test_an_item_put_off_stays_waiting_until_the_kick_off(tmp_path):
    rig = run(tmp_path, GAME + ANSWER_LATER)
    assert [item["state"] for item in league(rig).todo] == [D.ITEM_LATER] and team_points(rig) == 0


def test_an_item_asked_again_at_the_kick_off_can_be_answered(tmp_path):
    rig = run(tmp_path, GAME + ANSWER_LATER + [ENTER, ENTER])               # later, play game, the first candidate
    assert league(rig).todo == [] and team_points(rig) == 1
    assert X.text("NXD-30") not in spoken(rig)


def test_with_the_staff_setting_on_every_item_takes_the_recommendation_with_one_sentence(tmp_path):
    def auto(rig):
        rig.game.options.settings.game.nx_fr_auto = True
    rig = run(tmp_path, GAME, setup=auto)
    text = spoken(rig)
    assert X.text("NXD-04", n=1) in text and X.text("NXD-10") not in text and X.text("NXD-02", coach="kim") not in text
    assert league(rig).todo == [] and team_points(rig) == 1


def test_an_item_left_for_later_is_taken_by_the_staff_at_the_kick_off_when_the_setting_was_turned_on_meanwhile(tmp_path):
    turn_on = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 11 + [ENTER, ENTER, ESC, ESC, ESC]       # F9, Franchise, settings (11th since SX.8l), the staff item: on   # D-136: practice squad is the 10th item
    rig = run(tmp_path, GAME + ANSWER_LATER + turn_on + [ENTER])
    text = spoken(rig)
    assert rig.game.options.settings.game.nx_fr_auto is True
    assert X.text("NXD-04", n=1) in text and X.text("NXD-06", n=1) not in text and X.text("NXD-30") not in text
    assert league(rig).todo == [] and team_points(rig) == 1


def test_a_week_prepared_with_the_setting_off_and_met_again_with_it_on_has_the_staff_take_the_item(tmp_path):
    first = run(tmp_path / "one", GAME)                                     # the window closes at the question of week 2
    assert [item["state"] for item in league(first).todo] == [D.ITEM_NEW]

    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise", policy=quit_policy)
    second.game.options.settings.game.nx_fr_auto = True
    run_until(second)
    assert X.text("NXD-10") not in spoken(second) and X.text("NXD-04", n=1) in spoken(second)
    assert league(second).todo == [] and team_points(second) == 1


def test_a_restart_in_the_middle_of_the_questions_asks_the_same_item_and_makes_nothing_twice(tmp_path):
    first = run(tmp_path / "one", GAME)                                     # the window closes at the question of week 2
    record = league(first)
    assert record.told == [1, 2] and [item["state"] for item in record.todo] == [D.ITEM_NEW] and len(record.news) >= 2
    assert sum(p.points for p in record.players.values()) == 0                  # week 1 is no extra-work week: nobody has a point yet
    kept = (list(record.news), list(record.todo), dict(record.news_recent))
    second = franchise_rig(tmp_path / "two", [ENTER], files=first.files, kind="franchise", policy=quit_policy)
    run_until(second)
    again = league(second)
    assert (again.news, again.news_recent) == (kept[0], kept[2])
    assert X.text("NXD-10") in spoken(second) and team_points(second) == 1 and again.todo == []


def test_a_restart_after_the_preparation_does_not_give_the_computer_teams_their_points_again(tmp_path):
    first = run(tmp_path / "one", GAME + [ENTER] + GAME)                    # week 3's preparation gave the points of week 2
    total = sum(p.points for p in league(first).players.values())
    news = list(league(first).news)
    assert league(first).told == [1, 3] and total >= 1 + 20                 # the player's point and most computer teams'
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise", policy=quit_policy)
    run_until(second)
    assert sum(p.points for p in league(second).players.values()) == total and league(second).news == news
    assert X.text("NXN-01") not in spoken(second)                            # the lines of week 2 were told in the first run


# ----- the game plan -----

def with_playbook(offense="pro", defense="classic"):
    def setup(rig):
        settings = rig.game.options.settings.game
        settings.nx_offense_playbook, settings.nx_defense_playbook = offense, defense
        rig.game.apply_rules_setting()                                      # as the F9 Rules menu does: the program's rules follow the settings
    return setup


def staff_plan(rig):
    """SX.8l: (the offense and the defense the player's coordinators recommend, the opponent's (offense, defense)) for week 1: the opponent plays its
    coordinators' styles, and the staff's plan is `staff.recommended` of each side against the opponent's style on the other side of the ball. SX.8o: the
    styles every team's coordinators play with its week-1 lineup (staff.fitted_styles), the player's own included."""
    lg = league(rig)
    division, place, _flag = lg.schedule[0]
    fitted = ST.fitted_styles(lg, 1)
    theirs = fitted[team_index(division, place) - 1]
    own = fitted[lg.team - 1]
    styles = set(DEFAULT_TABLE.styles)
    return ST.recommended(lg, 0, theirs[1], styles, own[0]), ST.recommended(lg, 1, theirs[0], styles, own[1]), theirs


def test_the_game_plan_is_asked_in_week_1_with_the_opponents_styles_and_the_staffs_recommendation(tmp_path):
    rig = run(tmp_path, [], setup=with_playbook())
    text = spoken(rig)
    prompt = next(t for t in text if t.startswith(" the game plan against the "))
    assert " they play " in prompt and " on offense and " in prompt and " on defense. the staff recommends " in prompt
    ours_o, _ours_d, theirs = staff_plan(rig)
    assert (" they play %s on offense and %s on defense. " % (DEFAULT_TABLE.style_name(theirs[0]), DEFAULT_TABLE.style_name(theirs[1]))) in prompt
    assert prompt.endswith(" the staff recommends %s and %s. " % (DEFAULT_TABLE.style_name(ours_o), DEFAULT_TABLE.style_name("classic")))
    assert [item["state"] for item in league(rig).todo] == [D.ITEM_NEW]


def test_the_staffs_game_plan_is_the_rules_of_that_game_and_the_settings_do_not_change(tmp_path):
    rig = run(tmp_path, [ENTER, ENTER], setup=with_playbook())              # the staff's plan, play game
    rules = rig.plays[0]["rules"]
    assert rules is not None and (rules.offense_book, rules.defense_book) == (staff_plan(rig)[0], "classic")
    assert X.text("NXD-23") in spoken(rig)
    settings = rig.game.options.settings.game
    assert (settings.nx_offense_playbook, settings.nx_defense_playbook) == ("pro", "classic")


def test_the_staffs_plan_covers_the_defense_when_the_player_plays_a_defense_playbook(tmp_path):
    rig = run(tmp_path, [ENTER, ENTER], setup=with_playbook("classic", "air"))
    rules = rig.plays[0]["rules"]
    assert rules.offense_book == "classic" and rules.defense_book == staff_plan(rig)[1]


def test_keep_your_playbooks_leaves_the_game_to_the_programs_rules(tmp_path):
    rig = run(tmp_path, [DOWN, ENTER, ENTER], setup=with_playbook())
    assert rig.plays[0]["rules"] is None and X.text("NXD-23") not in spoken(rig)


def test_a_game_plan_left_for_later_is_not_used_and_the_kick_off_says_so(tmp_path):
    rig = run(tmp_path, [DOWN, DOWN, ENTER, ENTER, DOWN, DOWN, ENTER], setup=with_playbook())     # later, play game, later again
    assert rig.plays[0]["rules"] is None and X.text("NXD-30") in spoken(rig) and league(rig).todo == []


def test_with_the_staff_setting_on_the_game_plan_is_taken_without_a_question(tmp_path):
    def setup(rig):
        with_playbook()(rig)
        rig.game.options.settings.game.nx_fr_auto = True
    rig = run(tmp_path, [ENTER], setup=setup)
    assert rig.plays[0]["rules"].offense_book == staff_plan(rig)[0] and X.text("NXD-04", n=1) in spoken(rig)


def test_no_game_plan_item_when_both_playbooks_are_classic(tmp_path):
    rig = run(tmp_path, [])
    assert not any(t.startswith(" the game plan against the ") for t in spoken(rig)) and league(rig).todo == []


# ----- F9: the to-do list, the news, the setting -----

def test_f9_to_do_list_asks_the_waiting_items_again(tmp_path):
    rig = run(tmp_path, GAME + ANSWER_LATER + TO_FRANCHISE_MENU + [ENTER, ENTER, ESC, ESC])
    record = league(rig)
    assert record.todo == [] and team_points(rig) == 1
    text = spoken(rig)
    player = next(p for p in record.active_of(record.team) if p.points == 1)
    assert X.text("NXD-11", player=player.name) in text and X.text("NXD-07") in text


def test_f9_to_do_list_says_nothing_is_waiting_when_it_is_so(tmp_path):
    rig = run(tmp_path, TO_FRANCHISE_MENU + [ENTER, ESC, ESC])
    assert X.text("NXD-07") in spoken(rig)


def test_f9_to_do_list_leaves_an_item_that_escape_left(tmp_path):
    rig = run(tmp_path, GAME + ANSWER_LATER + TO_FRANCHISE_MENU + [ENTER, ESC, ESC, ESC])
    assert [item["state"] for item in league(rig).todo] == [D.ITEM_LATER] and team_points(rig) == 0


def test_f9_to_do_list_is_closed_inside_a_game(tmp_path):
    class Engine:                                                           # what F9 sees while a game runs: any engine at all
        rules = None

        def get_sex_of(self):
            return None

    held = {}
    sequence = iter(TO_FRANCHISE_MENU + [ENTER, ESC, ESC])

    def policy(keys):
        held["rig"].game.play_engine = Engine()
        try:
            return next(sequence)
        except StopIteration:
            held["rig"].game.play_engine = None
            raise GameQuit()
    rig = held["rig"] = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + GAME + ANSWER_LATER, policy=policy)
    run_until(rig)
    assert [item["state"] for item in league(rig).todo] == [D.ITEM_LATER] and X.text("NXD-07") in spoken(rig)


def test_f9_news_lists_the_latest_lines_and_the_earlier_ones(tmp_path):
    def auto(rig):
        rig.game.options.settings.game.nx_fr_auto = True
    rig = run(tmp_path, GAME + GAME + TO_FRANCHISE_MENU + [DOWN, ENTER, ENTER, ESC, DOWN, ENTER, ESC, ESC, ESC, ESC], setup=auto)
    text = spoken(rig)
    record = league(rig)
    latest = [e for e in record.news if e["week"] == 2]
    earlier = [e for e in record.news if e["week"] == 1]
    assert latest and earlier
    assert any(t.startswith("this week's news. %d items." % len(latest)) and (" %s" % latest[0]["markup"]) in t for t in text)
    assert any(t.startswith("earlier. %d items." % (len(earlier) + 1)) and X.text("NXN-05", n=1) in t
               for t in text)                                                       # the list opens on the week's heading


def test_f9_news_says_there_is_none_before_the_first_week_has_been_played(tmp_path):
    rig = run(tmp_path, TO_FRANCHISE_MENU + [DOWN, ENTER, ESC, ESC])
    assert X.text("NXN-02") in spoken(rig)


def test_the_staff_setting_is_in_the_franchise_settings_and_kept(tmp_path):
    from nfl4.data import settingsfile
    rig = run(tmp_path, TO_FRANCHISE_MENU + [DOWN] * 11 + [ENTER, ENTER, ESC, ESC, ESC])      # settings: the 11th item since SX.8l   # D-136: practice squad is the 10th item
    assert rig.game.options.settings.game.nx_fr_auto is True and "nx_fr_auto = on" in settingsfile.render(rig.game.options.settings)
    assert any(X.text("NXF-20") + "," + X.text("NXM-20") in t for t in spoken(rig))


# ----- the help -----

def test_the_help_of_a_franchise_has_its_lines_for_f5_f6_and_f7_after_the_rules_lines(tmp_path):
    rig = run(tmp_path, [])
    g = rig.game
    assert g.franchise_help("116") == [X.text("NXH-34")]
    assert g.franchise_help("117") == [X.text("NXH-35"), X.text("NXH-37"), X.text("NXH-39"), X.text("NXH-40"), X.text("NXH-41"),
                                       X.text("NXH-42"), X.text("NXH-43"), X.text("NXH-44"), X.text("NXH-45"),
                                       X.text("NXH-46"), X.text("NXH-72"), X.text("NXH-74"),
                                       X.text("NXH-76"), X.text("NXH-77"), X.text("NXH-78")]       # D-138, D-141, D-140       # D-136: the practice squad; SX.8k: injuries; SX.8l: your job; SX.8m: the market's later items; SX.8n: the people; SX.8o: the game's
    assert g.franchise_help("118") == [X.text("NXH-36"), X.text("NXH-38"), X.text("NXH-73")]
    assert g.franchise_help("119") == [] and all(len(X.text(i)) < 200 for i in ("NXH-34", "NXH-35", "NXH-36", "NXH-37", "NXH-38"))
    before = len(spoken(rig))
    g.hotkeys._extra_help("117")                                              # the hook of F6 says them with the rules' own lines
    assert [t for t in spoken(rig)[before:] if t in (X.text("NXH-35"), X.text("NXH-37"))] == [X.text("NXH-35"), X.text("NXH-37")]


def test_the_help_of_a_classic_season_has_no_franchise_line(tmp_path):
    rig = franchise_rig(tmp_path, [ENTER] + COACH_AND_TEAM, policy=quit_policy)
    run_until(rig)
    assert rig.game.program.mode.kind == "classic"
    assert all(rig.game.franchise_help(key) == [] for key in ("116", "117", "118"))


# ----- a whole season and its offseason -----

def test_a_whole_season_has_the_news_of_weeks_1_to_15_and_extra_work_in_four_weeks_only(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: at_stage(1)(rig)))
    run_until(rig)
    text = spoken(rig)
    assert text.count(X.text("NXN-01")) == 15                               # told at the menus of weeks 2 to 16, never in the play-offs
    assert 1 <= text.count(X.text("NXD-10")) <= len(T.FR_EXTRA_WORK_WEEKS)
    record = league(rig)
    assert {e["week"] for e in record.news} == set(range(1, 16))
    assert all(sum(1 for e in record.news if e["week"] == w) <= T.FR_NEWS_MAX for w in range(1, 16))
    assert record.todo == [] or all(item["week"] <= 16 for item in record.todo)
    points = sum(p.points for p in record.players.values())
    assert points >= 4 * 20                                                   # the computer teams' four weeks (most have two candidates)


def test_the_regular_season_is_weeks_1_to_16_of_a_league_in_its_season_stage():
    from nfl4.extras.franchise.league import OFFSEASON
    record = draft_league(stage_no=D.STAGE_REVIEW)
    record.stage = "season"
    for week, wanted in ((0, False), (1, True), (16, True), (17, False), (20, False)):
        record.gtp = week
        assert weekly.in_regular_season(record) is wanted, week
    record.stage, record.gtp = OFFSEASON, 5
    assert weekly.in_regular_season(record) is False and weekly.in_regular_season(None) is False


def test_the_offseason_makes_the_champion_and_first_pick_news_and_keeps_it_for_the_new_season(tmp_path):
    def weekly_news(record):
        record.news.append({"season": 1, "week": 5, "pool": "NWB", "markup": "an old line", "told": 1})
    league0 = draft_league(stage_no=D.STAGE_REVIEW, mutate=weekly_news)
    rig = offseason_rig(tmp_path, league0)
    final = saved_league(rig)
    pools = {e["pool"] for e in final.news if e["week"] == D.NEWS_OFFSEASON}
    assert {"NWT", "NWD"} <= pools and all(e["season"] == 1 for e in final.news) and final.season == 2
    assert not any(e["week"] < D.NEWS_OFFSEASON for e in final.news)
    champion_lines = [e["markup"] for e in final.news if e["pool"] == "NWT"]
    assert len(champion_lines) == 1 and champion_lines[0] in spoken(rig)


def test_the_short_offseason_makes_the_same_news_and_does_not_say_it(tmp_path):
    rig = offseason_rig(tmp_path, draft_league(stage_no=D.STAGE_REVIEW), short=True)
    final = saved_league(rig)
    kept = [e["markup"] for e in final.news if e["week"] == D.NEWS_OFFSEASON]
    assert {e["pool"] for e in final.news} >= {"NWT", "NWD"}
    assert not any(line in spoken(rig) for line in kept)


# ----- the review's findings (SX.8e) -----

def test_an_item_answered_in_f9_while_the_flows_question_is_open_is_not_answered_again(tmp_path):
    rig = run(tmp_path, GAME + TO_FRANCHISE_MENU + [ENTER, ENTER, ESC, ESC, ENTER])     # F9 gives the point, then Enter at the open question
    assert league(rig).todo == [] and team_points(rig) == 1
    assert spoken(rig).count(X.text("NXD-11", player=next(p.name for p in league(rig).active_of(league(rig).team) if p.points == 1))) == 1


def test_a_game_plan_kept_in_f9_while_the_flows_question_is_open_is_not_set_by_the_flows_answer(tmp_path):
    keys = TO_FRANCHISE_MENU + [ENTER, DOWN, ENTER, ESC, ESC, ENTER, ENTER]            # F9, to do list, keep your playbooks; the open question; play game
    rig = run(tmp_path, keys, setup=with_playbook())
    assert league(rig).todo == [] and rig.plays[0]["rules"] is None and X.text("NXD-23") not in spoken(rig)


def test_the_flows_other_items_are_still_asked_after_one_was_answered_in_f9(tmp_path):
    rig = run(tmp_path, [ENTER] * 0 + GAME + [ENTER], setup=with_playbook())            # a plan in week 1 and extra work in week 2
    assert league(rig).todo == [] or all(item["week"] == 2 for item in league(rig).todo)


def test_a_league_sav_of_an_earlier_session_in_the_middle_of_a_week_is_prepared_when_it_is_next_started(tmp_path):
    import json
    first = run(tmp_path / "one", GAME)                                                 # the window closes at the question of week 2
    raw = json.loads(first.files.data["league.sav"].decode("utf-8"))
    assert raw["prepared"] == [1, 2]
    del raw["prepared"]                                                                 # what SX.8d wrote: told but never prepared
    raw["todo"], raw["news"], raw["news_recent"] = [], [], {}
    first.files.data["league.sav"] = json.dumps(raw).encode("utf-8")
    second = franchise_rig(tmp_path / "two", [ENTER], files=first.files, kind="franchise", policy=quit_policy)
    run_until(second)
    text = spoken(second)
    assert X.text("NXN-01") in text and X.text("NXD-10") in text and team_points(second) == 1
    assert X.text("NXF-08", n=1) not in text and league(second).prepared == [1, 2]


def test_f8_comments_off_do_not_silence_the_news(tmp_path):
    def comments_off(rig):
        rig.game.options.set_comtog(1)
    rig = run(tmp_path, GAME, setup=comments_off)
    assert X.text("NXN-01") in spoken(rig) and rig.game.comtog == 1


def test_a_loaded_games_waiting_items_are_closed_without_a_question_and_a_plan_that_was_taken_stays(tmp_path):
    rig = run(tmp_path, GAME + ANSWER_LATER)
    p = rig.game.program
    p.saved_game = True                                                                 # the game of this week was loaded from a save
    before = len(spoken(rig))
    weekly.before_game(p)
    assert X.text("NXD-30") in spoken(rig)[before:] and X.text("NXD-06", n=1) not in spoken(rig)[before:]
    assert league(rig).todo == [] and team_points(rig) == 0


def test_the_plan_is_applied_only_to_the_sides_the_player_plays_a_playbook_on_when_the_game_is_made(tmp_path):
    rig = run(tmp_path, [ENTER], setup=with_playbook("pro", "classic"))                 # the plan is taken: the coordinators' offense, Classic defense
    p, settings = rig.game.program, rig.game.options.settings.game
    plan = staff_plan(rig)[0]
    assert weekly.game_rules(p).offense_book == plan and weekly.game_rules(p).defense_book == "classic"
    settings.nx_defense_playbook = "air"                                                # the defense setting changes after the plan
    rig.game.apply_rules_setting()
    rules = weekly.game_rules(p)
    assert (rules.offense_book, rules.defense_book) == (plan, "air")
    settings.nx_offense_playbook = "classic"
    rig.game.apply_rules_setting()
    rules = weekly.game_rules(p)
    assert (rules.offense_book, rules.defense_book) == ("classic", "air")


def test_extra_work_comes_in_the_weeks_of_the_tuning_and_in_no_other(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: at_stage(1)(rig)))
    run_until(rig)
    weeks, current = [], None
    for line in spoken(rig):
        if line.startswith(" This is week "):
            current = int(line.split()[3])
        elif line == X.text("NXD-10"):
            weeks.append(current)
    assert weeks and set(weeks) <= set(T.FR_EXTRA_WORK_WEEKS) and len(weeks) == len(set(weeks))
    assert max(T.FR_EXTRA_WORK_WEEKS) <= D.NEWS_LAST_WEEK            # a week's computer points are given at the next week's preparation


def test_the_staffs_defense_plan_is_the_defensive_coordinators_against_the_opponents_offense_style(tmp_path):
    rig = run(tmp_path, [ENTER, ENTER], setup=with_playbook("classic", "air"))
    item = next(i for i in league(rig).todo if i["kind"] == D.TODO_GAME_PLAN)
    lg = league(rig)
    assert item["styles"][3] == ST.recommended(lg, 1, item["styles"][0], set(DEFAULT_TABLE.styles)) and rig.plays[0]["rules"].defense_book == item["styles"][3]
