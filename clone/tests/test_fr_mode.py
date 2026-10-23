"""The program's season frame with a Franchise: the question at a new season, the franchise's seasons and offseason, the switches
between a classic season and a franchise, and Rules = Classic staying the original (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 3 and 13 (H14, H15), SX.8a; B-X48 (a switch asked from F9 at the main menu is heard at once). The program
is the whole program on the rig of tests/frrig.py: the N. F. L. rules, a franchise in memory, a stand-in for pag whose scores the
test sets, and the real season engine, so every result goes through H14 as in play. An answer script lists the key of every wait
in order (a regular week's game takes three: the menu, the results, the standings); when it is used up the rig presses Enter.
"""
import json

import pytest

from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F9, UP, WANT_CLASSIC, WANT_FRANCHISE, enter_until, franchise_rig, run_until,
                   spoken)
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history as fr_history
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import LeagueRecord
from nfl4.game.pag import GameResult
from nfl4.game.setup import Roster
from programrig import Outcome, preset_season

QUESTION = X.text("NXF-01", coach="coach")
GAME = [ENTER, ENTER, ENTER]                  # the main menu's play game, the results, the standings
FRANCHISE_MENU = [F9, DOWN, DOWN, DOWN, DOWN, ENTER]          # F9, down to the Franchise item, into it


def settings_of(rig):
    return rig.game.options.settings.game


def league(rig):
    return rig.fstore.league


def at_week(rig, season, gtp):
    return lambda: rig.fstore is not None and league(rig) is not None and league(rig).season == season and league(rig).gtp == gtp


def a_franchise(tmp_path, until=lambda rig: at_week(rig, 2, 1), **kwargs):
    """A first run that makes a franchise and plays one season, then closes the window at week 1 of the second."""
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: until(rig)()), **kwargs)
    return run_until(rig)


# ----- Rules = Classic is the original (P1) -----

def test_with_rules_classic_nothing_of_the_franchise_is_asked_made_or_opened(tmp_path):
    rig = franchise_rig(tmp_path, COACH_AND_TEAM, nfl=False, policy=enter_until(lambda: rig.game.season.gtp == 3))
    run_until(rig)
    assert rig.game._franchise_store is None and rig.files.data == {} and QUESTION not in spoken(rig)
    assert rig.game.program.mode.kind == "classic" and not rig.game.functions.franchise_shown()
    assert settings_of(rig).nx_season_kind == "classic"


def f9_labels(monkeypatch, rig):
    """The labels of the root of F9 each time it opens (the items are built per opening, design 13)."""
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append((title, [item.label() for item in items]))
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    run_until(rig)
    return seen


def test_with_rules_classic_f9s_list_is_exactly_the_five_items_of_the_original(tmp_path, monkeypatch):
    rig = franchise_rig(tmp_path, [F9, ESC], nfl=False, preset=preset_season(),
                        policy=enter_until(lambda: len(rig.keys.read) >= 1))
    seen = f9_labels(monkeypatch, rig)
    assert seen[0][1] == ["Speech settings.", "Sounds.", "Customize the names and the banter.", "Rules.", "About NFL Football 4."]


def test_with_the_nfl_rules_f9_gets_the_franchise_item_after_rules_and_before_about(tmp_path, monkeypatch):
    rig = franchise_rig(tmp_path, [F9, ESC], preset=preset_season(), policy=enter_until(lambda: len(rig.keys.read) >= 1))
    seen = f9_labels(monkeypatch, rig)
    assert seen[0][1][3:] == ["Rules.", "Franchise", "About NFL Football 4."] and len(seen[0][1]) == 6


# ----- the question at a new season (design 3.2) -----

def test_with_the_nfl_rules_a_new_season_asks_the_question_and_classic_is_the_first_answer(tmp_path):
    rig = franchise_rig(tmp_path, WANT_CLASSIC + COACH_AND_TEAM, policy=enter_until(lambda: rig.game.season.gtp == 2))
    run_until(rig)
    text = spoken(rig)
    assert text[text.index(QUESTION) + 1:text.index(QUESTION) + 2] == [" 1. classic season "]
    assert rig.game.program.mode.kind == "classic" and settings_of(rig).nx_season_kind == "classic"
    assert rig.files.data == {} and rig.game.season.coach == "kim"          # the original's prompts, nothing of the franchise written


def test_the_second_answer_is_franchise_when_none_exists_and_it_makes_the_league(tmp_path):
    rig = a_franchise(tmp_path, until=lambda r: (lambda: r.game.season.gtp == 2 and r.game.program.mode.kind == "franchise"))
    text = spoken(rig)
    assert text[text.index(QUESTION):text.index(QUESTION) + 3] == [QUESTION, " 1. classic season ", " 2. franchise "]
    prompts = [text.index(" Enter the name of your coach "), text.index(X.text("NXF-07")), text.index(X.text("NXF-08", n=1))]
    assert prompts == sorted(prompts)
    assert text[prompts[2] - 1].startswith(" Today's game is") and text[prompts[2] + 1] == X.text("NXX-30", n=9) and text[prompts[2] + 2] == " kim select "       # design 3.4 (SZ.8: and where trades and free agents are)
    assert settings_of(rig).nx_season_kind == "franchise" and rig.game.program.mode.kind == "franchise"
    assert sorted(rig.files.data) == ["history.txt", "league.previous.sav", "league.sav"]
    made = league(rig)
    assert made.coach == "kim" and made.team == 1 and made.season == 1 and len(made.players) == 1088
    assert len(made.schedule) == 16 and made.told == [1, 1] and made.stage == "season"


def test_the_franchise_teams_names_come_from_footplay_txt_when_it_is_whole(tmp_path):
    names = Roster(["rb%d" % i for i in range(6)], ["wr%d" % i for i in range(6)], ["df%d" % i for i in range(17)],
                   ["st%d" % i for i in range(2)], ["kk%d" % i for i in range(2)], quarterback="Quarterman")
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, classic_names=names,
                        policy=enter_until(lambda: rig.game.season.gtp == 2))
    run_until(rig)
    assert [p.name for p in league(rig).active_of(1)] == names.names() + ["Quarterman"]


def test_the_franchise_team_plays_with_the_leagues_players_and_the_leagues_quarterback(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + GAME, policy=enter_until(lambda: rig.game.season.gtp == 2))
    run_until(rig)
    own = rig.plays[0]["own_names"]
    assert own.is_complete() and own.quarterback == league(rig).player_at(1, 33).name and len(own.ratings) == 34
    assert rig.plays[0]["save_sink"] == rig.fstore.save_game and rig.plays[0]["roster_sink"] == rig.fstore.write_player_names


def test_with_a_franchise_the_question_has_three_answers_and_the_first_resumes_it(tmp_path):
    first = a_franchise(tmp_path / "one")
    second = franchise_rig(tmp_path / "two", [DOWN, DOWN, UP, ENTER], files=first.files, kind="classic",
                           policy=enter_until(lambda: rig2.game.season.gtp == 2))
    rig2 = second
    run_until(second)
    text = spoken(second)
    at = text.index(QUESTION)
    team = second.game.league.team(1, 1)
    assert text[at:at + 2] == [QUESTION, " 1. classic season "]
    assert " 2. your franchise with the Bengals " in text and " 3. a new franchise " in text
    assert X.text("NXF-05", team=team) in text and second.game.program.mode.kind == "franchise"
    assert settings_of(second).nx_season_kind == "franchise" and league(second).season == 2


def test_a_new_franchise_asks_first_whether_the_old_one_may_be_kept_as_a_copy(tmp_path):
    first = a_franchise(tmp_path / "one")
    old = first.files.data["league.sav"]
    # A new franchise: Down, Down, Enter; the yes/no starts at no (Enter: back to the question); again, Up for yes, Enter
    script = [DOWN, DOWN, ENTER, ENTER, DOWN, DOWN, ENTER, UP, ENTER] + COACH_AND_TEAM
    second = franchise_rig(tmp_path / "two", script, files=first.files, kind="classic",
                           policy=enter_until(lambda: second.game.season.gtp == 2 and second.game.program.mode.kind == "franchise"))
    run_until(second)
    text = spoken(second)
    team = second.game.league.team(1, 1)
    asked = X.text("NXF-02", team=team)
    assert text.count(asked) == 2 and text.count(QUESTION) == 2 and text[text.index(asked) + 1] == " no "
    assert first.files.data["old/league-1.sav"] == old and "old/history-1.txt" in first.files.data
    assert league(second).league_id and league(second).season == 1 and not league(second).history


# ----- a franchise year: the season, the offseason and the history -----

def test_three_whole_seasons_with_their_history_right_after_each(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(at_week_lambda(lambda: rig, 4, 1)))
    seen = []
    real = fr_history.build_entry

    def spy(record):
        seen.append(len(record.results))
        return real(record)
    fr_history.build_entry = spy
    from nfl4.extras.franchise.store import FranchiseStore
    start = {}
    real_create = FranchiseStore.create

    def create(self, new_league):
        for pid in (1, 2, 3):
            new_league.players[pid].points = 3                                  # points given before the first offseason
        start.update({pid: (p.age, p.seasons) for pid, p in new_league.players.items()})
        return real_create(self, new_league)
    FranchiseStore.create = create
    try:
        run_until(rig)
    finally:
        fr_history.build_entry = real
        FranchiseStore.create = real_create
    made = league(rig)
    assert made.season == 4 and made.gtp == 1 and made.stage == "season" and len(made.history) == 3
    assert seen == [256 + 11] * 3                                              # every game of the season came through H14
    assert [e["season"] for e in made.history] == [1, 2, 3]
    for entry in made.history:
        assert sum(entry["wins"]) == sum(entry["losses"]) == 256               # every regular game has one winner and one loser
        assert entry["finish"].count(D.FINISH_CHAMPION) == 1 and entry["finish"].count(D.FINISH_SUPER_BOWL) == 1
        assert entry["champion"] - 1 == entry["finish"].index(D.FINISH_CHAMPION)
    career = fr_history.career(made)
    assert career.seasons == 3 and career.wins + career.losses == 48
    text = spoken(rig)
    assert text.count(X.text("NXE-01")) == 3 and text.count(QUESTION) == 1      # the question only at the first new season
    assert [text.count(X.text("NXF-08", n=n)) for n in (1, 2, 3, 4)] == [1, 1, 1, 0]       # season 4's week 1 is not reached yet
    assert text.count(X.text("NXE-03")) == 27                                 # every stage of the offseason ends with the wait (design 3.3)
    for number, name in ((1, "the season in review"), (2, "the staff"), (3, "retirements"), (4, "player development"), (5, "expiring contracts"),
                         (6, "free agency"), (7, "the draft"), (8, "the roster cut"), (9, "the new season")):     # (the staff since SX.8l)
        assert text.count(" stage %d of 9. %s. " % (number, name)) == 3
    history_txt = rig.files.data["history.txt"].decode("utf-8")
    assert "after season 3." in history_txt and history_txt.count("\nSeason ") == 3
    for pid, (age, seasons) in start.items():                                 # whoever played all three years is exactly three years older
        player = made.players.get(pid)
        if player is not None and player.status == "active" and player.drafted is None and pid <= 1088:
            assert (player.age, player.seasons) == (age + 3, seasons + 3), pid
    assert all(player.points == 0 for player in made.players.values())      # the points of the first three players are gone
    assert sum(1 for player in made.players.values() if player.status == "retired") >= 1
    assert sum(1 for pid in start if made.players.get(pid) is not None and made.players[pid].status == "active") > 600
    assert made.results == [] and made.sums and made.records == [0] * 64


def at_week_lambda(get_rig, season, gtp):
    def predicate():
        rig = get_rig()
        return rig.fstore is not None and rig.fstore.league is not None and rig.fstore.league.season == season \
            and rig.fstore.league.gtp == gtp and rig.fstore.league.stage == "season"
    return predicate


def test_the_short_offseason_says_a_sentence_per_stage_and_asks_for_no_key(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    settings_of(rig).nx_fr_offseason = "short"
    run_until(rig)
    text = spoken(rig)
    start = text.index(X.text("NXE-01"))
    after = text[start:text.index(X.text("NXF-08", n=2))]
    assert [t for t in after if t.startswith(" the ") and "won the Super Bowl" in t]
    assert all("the draft" in t or "the roster cut" in t or "expiring contracts" in t or "free agency" in t or "the staff" in t
               or "player development" in t
               for t in after if " stage " in t)     # the stages that ask still name themselves (the staff asks about the coordinators since SX.8l,
    #                                                  the player development the camp's focus since SX.8m)
    assert any(t.startswith(" camp focus: ") for t in after)
    assert not any("press enter" in t or "best record" in t or " as a head coach: " in t for t in after)
    assert after[-1].startswith(" season 2 begins.") or " season 2 begins. " in after
    assert " the new schedule is made. " not in after


def test_a_window_closed_at_the_wait_of_a_stage_resumes_at_that_stage_and_keeps_one_history_entry(tmp_path):
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM,
                          policy=enter_until(lambda: X.text("NXE-03") in spoken(first)))
    run_until(first)
    saved = LeagueRecord.from_json(first.files.data["league.sav"].decode("utf-8"))
    assert saved.stage == "offseason" and saved.stage_no == 1 and saved.history == [] and len(saved.results) == 267
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise",
                           policy=enter_until(at_week_lambda(lambda: second, 2, 1)))
    run_until(second)
    text = spoken(second)
    assert text.count(X.text("NXE-01")) == 1 and text.index(" stage 1 of 9. the season in review. ") < text.index(" stage 9 of 9. the new season. ")
    assert len(league(second).history) == 1 and league(second).season == 2


def test_a_restart_in_week_1_does_not_tell_the_season_line_again_and_a_restart_in_week_5_goes_on_there(tmp_path):
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: first.game.season.gtp == 1 and
                                                                                               X.text("NXF-08", n=1) in spoken(first)))
    run_until(first)
    assert X.text("NXF-08", n=1) in spoken(first) and league(first).told == [1, 1]
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise",
                           policy=enter_until(lambda: second.game.season.gtp == 5))
    run_until(second)
    text = spoken(second)
    assert X.text("NXF-08", n=1) not in text and QUESTION not in text and X.text("NXF-05", team="Bengals") not in text
    assert text[1:3] and " This is week  1 of Josh Kennedy's N. F. L. football " in text
    third = franchise_rig(tmp_path / "three", [], files=first.files, kind="franchise",
                          policy=enter_until(lambda: third.game.season.gtp == 6))
    run_until(third)
    text = spoken(third)
    assert " This is week  5 of Josh Kennedy's N. F. L. football " in text and " This is week  1 of Josh Kennedy's N. F. L. football " not in text


def test_a_franchise_file_that_is_missing_at_the_start_makes_a_classic_season_with_the_notice(tmp_path):
    rig = franchise_rig(tmp_path, COACH_AND_TEAM, kind="franchise", policy=enter_until(lambda: rig.game.season.gtp == 2))
    run_until(rig)
    text = spoken(rig)
    assert X.text("NXF-37") in text and settings_of(rig).nx_season_kind == "classic" and rig.game.program.mode.kind == "classic"
    assert QUESTION in text                                                     # then a new classic season: the question


def test_a_franchise_file_held_by_another_program_is_not_used_and_no_question_is_asked(tmp_path):
    files = MemoryFiles()
    first = a_franchise(tmp_path / "one")
    files.data.update(first.files.data)
    files.held.add("league.sav")
    rig = franchise_rig(tmp_path / "two", COACH_AND_TEAM, files=files, kind="franchise", policy=enter_until(lambda: rig.game.season.gtp == 2))
    run_until(rig)
    text = spoken(rig)
    assert X.text("NXF-35") in text and QUESTION not in text and rig.game.program.mode.kind == "classic"


# ----- H14: every result, whichever way the play-offs go -----

def test_a_team_that_wins_everything_is_the_champion_and_every_game_is_recorded(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, scores=lambda r: (28, 10),
                        policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    seen = []
    real = fr_history.build_entry
    fr_history.build_entry = lambda record: (seen.append(len(record.results)), real(record))[1]
    try:
        run_until(rig)
    finally:
        fr_history.build_entry = real
    entry = league(rig).history[0]
    assert seen == [267] and entry["champion"] == 1 and entry["finish"][0] == D.FINISH_CHAMPION
    assert entry["wins"][0] == 16 and entry["playoff"][1] == 0 and entry["playoff"][0] >= 3
    assert entry["streak"][1] >= 16 + 3 or entry["streak"][0] == 1


def test_a_team_that_loses_the_super_bowl_is_the_runner_up(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM,
                        scores=lambda r: (28, 10) if r.game.season.gtp < 20 else (3, 24),
                        policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    run_until(rig)
    entry = league(rig).history[0]
    assert entry["runner_up"] == 1 and entry["finish"][0] == D.FINISH_SUPER_BOWL and entry["champion"] != 1


def test_a_conceded_super_bowl_is_recorded_as_the_opponents_win(tmp_path):
    def conceded(r):
        if r.game.season.gtp == 20:
            return Outcome(GameResult(scores=(0, 28), conceded=True))
        return Outcome(GameResult(scores=(28, 10)))
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, outcomes=[conceded] * 40,
                        policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    run_until(rig)
    entry = league(rig).history[0]
    assert entry["runner_up"] == 1 and entry["finish"][0] == D.FINISH_SUPER_BOWL and entry["big_win"] is not None


def test_a_team_that_loses_everything_misses_the_play_offs_and_the_rest_is_still_recorded(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, scores=lambda r: (3, 40),
                        policy=enter_until(at_week_lambda(lambda: rig, 2, 1)))
    seen = []
    real = fr_history.build_entry
    fr_history.build_entry = lambda record: (seen.append(len(record.results)), real(record))[1]
    try:
        run_until(rig)
    finally:
        fr_history.build_entry = real
    entry = league(rig).history[0]
    assert seen == [267] and entry["finish"][0] == D.FINISH_MISSED and entry["wins"][0] == 0 and entry["worst"] == 1


# ----- the switches (design 3.1, 3.5) and B-X48 -----

def classic_to_franchise_script():
    return GAME + FRANCHISE_MENU + [ENTER, ENTER, ESC, ESC]       # play a game, F9, Franchise, start now, confirm, close F9


def test_a_franchise_started_from_f9_at_the_main_menu_is_heard_at_once_and_the_classic_season_waits(tmp_path):
    rig = franchise_rig(tmp_path, classic_to_franchise_script() + COACH_AND_TEAM, preset=preset_season(gtp=3),
                        policy=enter_until(lambda: rig.game.program.mode.kind == "franchise" and rig.game.season.gtp == 2))
    run_until(rig)
    text = spoken(rig)
    confirm = text.index(X.text("NXF-27"))
    assert text[confirm + 1:confirm + 4] and " Enter the name of your coach " in text[confirm:]           # B-X48: no play game first
    assert len(rig.plays) == 2 and rig.plays[0]["gtp"] == 3                                                # the classic week 3, the franchise week 1
    assert rig.game.program.mode.kind == "franchise" and rig.game.season_store is rig.fstore
    assert rig.game.parked_classic is not None and rig.game.parked_classic.gtp == 4 and rig.game.parked_classic.coach == "Kim"
    assert settings_of(rig).nx_season_kind == "franchise"


def test_playing_classic_seasons_from_the_franchise_goes_back_to_the_classic_week_it_left(tmp_path):
    back = GAME + FRANCHISE_MENU + [DOWN] * 12 + [ENTER, ENTER, ESC, ESC]      # F9, Franchise, play classic seasons (12th since SX.8l), confirm   # D-136: practice squad is the 10th item
    script = classic_to_franchise_script() + COACH_AND_TEAM + GAME + back
    rig = franchise_rig(tmp_path, script, preset=preset_season(gtp=3), policy=enter_until(lambda: len(rig.plays) == 4))
    run_until(rig)
    text = spoken(rig)
    team = rig.game.league.team(1, 1)
    assert X.text("NXF-06") in text and rig.game.program.mode.kind == "classic" and rig.game.season_store is None      # the rig's classic stores
    assert settings_of(rig).nx_season_kind == "classic" and rig.game.season.coach == "Kim"
    tail = text[text.index(X.text("NXF-06")):]
    assert " This is week  4 of Josh Kennedy's N. F. L. football " in tail                       # the classic season goes on at week 4
    assert [play["gtp"] for play in rig.plays] == [3, 1, 2, 4]
    assert league(rig).gtp == 3 and league(rig).season == 1                              # the franchise waits at its week 3
    assert X.text("NXF-05", team=team) not in text


def test_back_to_the_franchise_continues_it_where_it_stood(tmp_path):
    to_classic = GAME + FRANCHISE_MENU + [DOWN] * 12 + [ENTER, ENTER, ESC, ESC]   # D-136: practice squad is the 10th item
    to_franchise_again = GAME + [F9, DOWN, DOWN, DOWN, DOWN, ENTER, ENTER, ESC]       # classic week 4; F9, Franchise, back to the franchise
    script = classic_to_franchise_script() + COACH_AND_TEAM + GAME + to_classic + to_franchise_again
    rig = franchise_rig(tmp_path, script, preset=preset_season(gtp=3), policy=enter_until(lambda: len(rig.plays) == 6))
    run_until(rig)
    text = spoken(rig)
    team = rig.game.league.team(1, 1)
    assert X.text("NXF-05", team=team) in text and rig.game.program.mode.kind == "franchise"
    assert [play["gtp"] for play in rig.plays] == [3, 1, 2, 4, 3, 4]               # classic 3, franchise 1 and 2, classic 4, franchise 3 and 4
    assert rig.game.parked_classic is not None and rig.game.parked_classic.gtp == 5 and league(rig).gtp == 5


def test_changing_the_rules_to_classic_while_the_franchise_is_in_use_says_it_waits_and_back_resumes_it(tmp_path):
    rules_to_classic = GAME + [F9, DOWN, DOWN, DOWN, ENTER, ENTER, ESC, ESC, ESC]     # F9, Rules, change to Classic, leave
    rules_to_nfl = [F9, DOWN, DOWN, DOWN, ENTER, ENTER, ESC, ESC, ESC]
    script = WANT_FRANCHISE + COACH_AND_TEAM + rules_to_classic + COACH_AND_TEAM + rules_to_nfl
    rig = franchise_rig(tmp_path, script, policy=enter_until(lambda: len(rig.plays) == 2 and rig.game.program.mode.kind == "franchise"
                                                             and rig.game.options.settings.game.rules == "nfl"))
    run_until(rig)
    text = spoken(rig)
    assert any(X.text("NXF-04") in t for t in text) and any(X.text("NXM-26") in t for t in text)
    assert X.text("NXF-06") not in text                                               # the Rules menu told it; the switch adds nothing
    assert X.text("NXF-05", team=rig.game.league.team(1, 1)) in text and rig.game.program.mode.kind == "franchise"
    assert settings_of(rig).nx_season_kind == "franchise"
    assert text.count(QUESTION) == 1                                                  # a classic season in between asked nothing


# ----- Save Game in a franchise (design 10.2) -----

def test_a_game_saved_in_the_franchise_is_loaded_at_the_next_start_of_that_week(tmp_path):
    from test_files_savedgame import a_game
    from nfl4.extras.state import ExtrasRecord

    def save_it(r):
        saved = a_game()
        saved.extras, saved.extras_marked = ExtrasRecord().to_json(), True
        r.plays[-1]["save_sink"](saved)
        return Outcome(GameResult(scores=None, saved=True), stop_beds=False)

    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM + [ENTER], outcomes=[save_it])
    run_until(first) if False else first.run()
    assert first.game.program.ending == "saved" and "football.sav" in first.files.data
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise",
                           policy=enter_until(lambda: len(second.plays) == 1))
    run_until(second)
    assert second.plays[0]["saved"] is not None and second.plays[0]["saved"].quarter == 3
    assert "football.sav" not in second.files.data
    # SX.8b (design 10.2): the loaded game has the same teams as the saved one, with the league's ratings and quarterbacks
    before, after = first.plays[0], second.plays[0]
    assert after["opponent"] == before["opponent"] and after["own_names"].ratings == before["own_names"].ratings
    assert after["opponent_names"].names() == before["opponent_names"].names()
    assert after["opponent_names"].ratings == before["opponent_names"].ratings and len(after["opponent_names"].ratings) == 34
    assert after["quarterback_names"](None) == before["quarterback_names"](None)


# ----- H14 in the engine, a season that ended and was not begun, history.txt -----

def test_every_result_of_a_regular_week_goes_through_h14_once_with_both_teams_and_the_scores(tmp_path):
    from nfl4.game.season_engine import CLASSIC_SEASON_HOOKS, ClassicSeasonHooks

    class Recorder(ClassicSeasonHooks):                 # the hooks object has three calls since SX.8b; this one records the first
        def __init__(self):
            self.calls = []

        def game_played(self, *args):
            self.calls.append(args)

    rig = franchise_rig(tmp_path, GAME, preset=preset_season(gtp=1), policy=enter_until(lambda: rig.game.season.gtp == 2))
    assert rig.game.season_hooks is CLASSIC_SEASON_HOOKS and CLASSIC_SEASON_HOOKS.game_played("regular", 1, None, None, 0, 0) is None
    rig.game.season_hooks = recorder = Recorder()
    run_until(rig)
    assert len(recorder.calls) == 16 and {call[0] for call in recorder.calls} == {"regular"} and {call[1] for call in recorder.calls} == {1}
    teams = [team for call in recorder.calls for team in (call[2], call[3])]
    assert len(set(teams)) == 32                                              # every team plays once in a week
    opponent = rig.plays[0]["opponent"]
    assert recorder.calls[0][2:] == (rig.game.season.own_team, type(rig.game.season.own_team)(*opponent), 24, 17)    # the player's game first


def test_a_season_that_ended_but_whose_offseason_had_not_begun_starts_the_offseason_at_the_next_start(tmp_path, monkeypatch):
    # the player wins until the conference championship and loses it: the engine writes the week 0 (football.gtp = 0) and the
    # offseason begins at once, so the file as it was at that moment is the one a crash there would leave
    from nfl4.extras.franchise.store import FranchiseStore
    kept = {}
    real = FranchiseStore.save

    def save(self):
        ok = real(self)
        if self.league.stage == "season" and self.league.gtp == 0 and "league.sav" not in kept:
            kept["league.sav"] = self.files.data["league.sav"]
        return ok
    monkeypatch.setattr(FranchiseStore, "save", save)
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM,
                          scores=lambda r: (28, 10) if r.game.season.gtp < 19 else (3, 40),
                          policy=enter_until(lambda: X.text("NXE-03") in spoken(first)))
    run_until(first)
    saved = LeagueRecord.from_json(kept["league.sav"].decode("utf-8"))
    assert saved.stage == "season" and saved.gtp == 0 and len(saved.results) == 267 and saved.history == []
    files = MemoryFiles()
    files.data["league.sav"] = kept["league.sav"]
    second = franchise_rig(tmp_path / "two", [], files=files, kind="franchise",
                           policy=enter_until(at_week_lambda(lambda: second, 2, 1)))
    run_until(second)
    assert len(league(second).history) == 1 and spoken(second).count(X.text("NXE-01")) == 1
    assert league(second).history[0]["season"] == 1 and league(second).season == 2


def test_history_txt_is_written_again_from_the_record_when_it_was_deleted(tmp_path):
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(at_week_lambda(lambda: first, 2, 1)))
    run_until(first)
    assert "history.txt" in first.files.data
    del first.files.data["history.txt"]
    second = franchise_rig(tmp_path / "two", [], files=first.files, kind="franchise", policy=enter_until(at_week_lambda(lambda: second, 3, 1)))
    run_until(second)
    text = "\n".join(first.files.data["history.txt"].decode("utf-8").splitlines()) + "\n"
    assert "after season 2." in text and "\nSeason 1\n" in text and "\nSeason 2\n" in text


def test_a_file_written_at_each_stage_of_the_offseason_loads_and_the_offseason_goes_on_from_it(tmp_path, monkeypatch):
    from nfl4.extras.franchise.store import FranchiseStore
    kept = {}
    real = FranchiseStore.save

    def save(self):
        ok = real(self)
        if self.league.stage == "offseason" and self.league.stage_no not in kept:
            kept[self.league.stage_no] = self.files.data["league.sav"]
        return ok
    monkeypatch.setattr(FranchiseStore, "save", save)
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(at_week_lambda(lambda: first, 2, 1)))
    run_until(first)
    assert sorted(kept) == [1, 2, 3, 4, 5, 6, 7, 8, 9]                        # the stages this version has: written when each begins (9 the staff, SX.8l)
    monkeypatch.undo()
    for number, raw in sorted(kept.items()):
        files = MemoryFiles()
        files.data["league.sav"] = raw
        again = franchise_rig(tmp_path / ("again%d" % number), [], files=files, kind="franchise",
                              policy=enter_until(at_week_lambda(lambda: again, 2, 1)))
        run_until(again)
        assert league(again).season == 2 and len(league(again).history) == 1, number


def test_the_franchise_folder_on_disk_is_never_made_by_a_classic_season_with_either_rules(tmp_path):
    from nfl4.extras.franchise.files import DiskFiles
    from nfl4.extras.franchise.store import FranchiseStore
    for name, nfl, answers in (("classic", False, COACH_AND_TEAM), ("nfl", True, WANT_CLASSIC + COACH_AND_TEAM)):
        folder = tmp_path / name / "franchise"
        rig = franchise_rig(tmp_path / name, answers, nfl=nfl, policy=enter_until(lambda: rig.game.season.gtp == 3))
        rig.game.franchise_factory = lambda classic, folder=folder: FranchiseStore(DiskFiles(str(folder)), classic)
        run_until(rig)
        assert rig.game.season.gtp == 3 and not folder.exists(), name       # two weeks were played; reading a missing folder makes nothing
