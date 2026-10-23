"""The real calendar of a Franchise season (nfl4 only, rule 0.13; SZ.8, D-120). This is inspired by Jim Kitchen.

A player wrote (2026-10-22) that the Franchise did not play the 2026 schedule. The Franchise now plays the league's real calendar: 18 weeks, 17 games for every team, one bye week
(`assets/data/schedule_2026.txt`, `extras/franchise/fixtures.py`). Tested here: the shipped file and the whole check of a calendar, the relabeling of later seasons, the season state and
the engine's bye week and calendar weeks, the schedule the player hears, and whole seasons on the Franchise rig (the byes, the play-offs after week 18, the next season).
The original's 16 weeks are tested where they were (test_season_*.py, the Franchise tests with their 16 random weeks).
"""
import pytest
from frrig import COACH_AND_TEAM, ENTER, WANT_FRANCHISE, enter_until, franchise_rig, run_until, spoken
from seasonrig import Draws, ENTER as KEY_ENTER, season_rig, texts

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import fixtures
from nfl4.extras.franchise.fixtures import CalendarError
from nfl4.game.schedule import BYE, Calendar, ScheduleEntry, team_number, team_pair
from nfl4.game.season import SeasonState

COMMANDERS, PATRIOTS, SEAHAWKS, MIAMI, CINCINNATI = 24, 8, 28, 6, 1


@pytest.fixture(scope="module")
def shipped():
    return fixtures.load_file(fixtures.shipped_path(2026))


def games_of(calendar, team):
    return [game for week in calendar.weeks for game in week if team in game]


# ----- the shipped file -----

def test_the_shipped_2026_calendar_has_18_weeks_272_games_17_games_and_one_bye_for_every_team(shipped):
    assert shipped.length == 18 and sum(len(week) for week in shipped.weeks) == 272
    assert "season 2026" in shipped.label
    for team in range(1, 33):
        assert len(games_of(shipped, team)) == 17
        byes = [week for week in range(1, 19) if shipped.game_of(week, team) is None]
        assert len(byes) == 1 and 5 <= byes[0] <= 14, (team, byes)               # the NFL's byes fall in weeks 5 to 14
    fixtures.check(shipped)


def test_the_shipped_calendar_has_the_facts_of_the_nfls_release_that_were_checked_by_hand(shipped):
    assert shipped.weeks[0][0] == (PATRIOTS, SEAHAWKS)                         # the opener: the Patriots at the Seahawks (Wednesday, September 9, 2026)
    assert shipped.game_of(18, PATRIOTS) == (MIAMI, PATRIOTS)                  # their last game: the Dolphins at New England
    assert shipped.game_of(7, COMMANDERS) is None                             # the Commanders' bye is week 7
    assert shipped.game_of(6, CINCINNATI) is None and shipped.game_of(5, 31) is None   # the Bengals' (week 6) and the Panthers' (week 5)
    assert [len(week) for week in shipped.weeks] == [16, 16, 16, 16, 15, 14, 14, 14, 15, 14, 13, 16, 14, 15, 16, 16, 16, 16]


def test_a_team_visits_every_division_rival_once_and_hosts_it_once(shipped):
    for division in range(1, 9):
        teams = [team_number(division, place) for place in range(1, 5)]
        for visitor in teams:
            for home in teams:
                if visitor != home:
                    assert sum(1 for week in shipped.weeks for game in week if game == (visitor, home)) == 1


def test_the_players_schedule_has_the_opponent_and_the_flag_of_every_week_and_a_bye(shipped):
    entries = shipped.entries_of(COMMANDERS)
    assert len(entries) == 18 and entries[6] == ScheduleEntry(*BYE) and entries[6].is_bye
    assert entries[0] == ScheduleEntry(6, 2, 2)                                 # week 1 at the Eagles (division 6, place 2): away is flag 2
    assert entries[17] == ScheduleEntry(6, 1, 1)                                # week 18 against the Cowboys at home: the opponent first, flag 1
    assert sum(1 for entry in entries if entry.is_bye) == 1 and {entry.flag for entry in entries if not entry.is_bye} == {1, 2}
    for week, entry in enumerate(entries, start=1):
        if not entry.is_bye:
            visitor, home = shipped.game_of(week, COMMANDERS)
            assert team_number(entry.division, entry.team) == (visitor if entry.flag == 1 else home)


# ----- the check of a calendar -----

def tweak(calendar, week, new_games):
    weeks = list(calendar.weeks)
    weeks[week - 1] = tuple(new_games)
    return Calendar(calendar.label, tuple(weeks))


def test_a_calendar_that_breaks_a_rule_is_refused_with_the_reason(shipped):
    with pytest.raises(CalendarError, match="17 weeks|weeks"):
        fixtures.check(Calendar("x", shipped.weeks[:17]))
    with pytest.raises(CalendarError, match="twice in week 1"):
        fixtures.check(tweak(shipped, 1, [shipped.weeks[0][0], (PATRIOTS, 27)] + list(shipped.weeks[0][2:])))
    with pytest.raises(CalendarError, match="plays 16 games"):
        fixtures.check(tweak(shipped, 1, shipped.weeks[0][1:]))
    with pytest.raises(CalendarError, match="plays itself"):
        fixtures.check(tweak(shipped, 5, [(31, 31)] + list(shipped.weeks[4])))
    with pytest.raises(CalendarError):
        fixtures.parse("# NFL Football 4 schedule, format 1.\nVERSION = x\nW01G01 = T01 T02 2026-09-13\n")


def test_a_file_that_is_not_a_schedule_is_refused():
    for text in ("", "nothing", "# NFL Football 4 rosters, format 1.\n", "# NFL Football 4 schedule, format 2.\n"):
        with pytest.raises(CalendarError):
            fixtures.parse(text)


# ----- the later seasons -----

def test_season_1_is_the_2026_calendar_and_a_later_season_is_the_same_calendar_with_the_divisions_rotated(shipped):
    assert fixtures.year_of(1) == 2026 and fixtures.year_of(5) == 2030
    assert fixtures.for_season(1).weeks == shipped.weeks
    for season in range(2, 41):
        rotated = fixtures.for_season(season)
        fixtures.check(rotated)                                                  # every rule holds again
        assert [len(week) for week in rotated.weeks] == [len(week) for week in shipped.weeks]    # the same weeks, byes and games
        assert f"season {2026 + season - 1}" in rotated.label
    assert fixtures.for_season(2).weeks != shipped.weeks
    opponents = [{(game[0] if game[1] == COMMANDERS else game[1]) for game in games_of(fixtures.for_season(n), COMMANDERS)} for n in (1, 2, 3, 4)]
    assert len({frozenset(o) for o in opponents}) == 4                          # a team meets other teams every season


def test_a_rotated_season_keeps_a_teams_division_rivals_in_its_division(shipped):
    for season in (2, 3, 4, 9):
        calendar = fixtures.for_season(season)
        for team in range(1, 33):
            rivals = [g for g in games_of(calendar, team) if team_pair(g[0])[0] == team_pair(g[1])[0]]
            assert len(rivals) == 6


# ----- the season state -----

def test_the_season_state_knows_the_length_of_the_regular_season_and_the_play_off_weeks(shipped):
    season = SeasonState()
    assert season.regular_weeks == 16 and season.first_playoff_week == 17 and season.playoff_week(4) == 20
    season.calendar = shipped
    season.choose_team(*team_pair(COMMANDERS))
    season.schedule = shipped.entries_of(COMMANDERS)
    assert season.regular_weeks == 18 and season.first_playoff_week == 19 and season.playoff_week(1) == 19 and season.playoff_week(4) == 22
    season.gtp = 18
    assert season.in_regular_season and not season.in_playoffs and season.classic_gtp() == 18
    season.gtp = 19
    assert season.in_playoffs and not season.in_regular_season and season.classic_gtp() == 17          # the original's numbering for the texts keyed by it
    assert season.classic_gtp(22) == 20 and season.classic_gtp(7) == 7
    season.gtp = 7
    assert season.on_bye and season.set_week_opponent() is None
    season.gtp = 8
    assert not season.on_bye and season.set_week_opponent() is not None
    season.reset_for_new_season()
    assert season.calendar is None and season.regular_weeks == 16 and not season.on_bye


# ----- the engine: a bye week and a calendar week -----

def calendar_rig(tmp_path, shipped, gtp, **kwargs):
    rig = season_rig(tmp_path, answers=[KEY_ENTER] * 4, own=team_pair(COMMANDERS), opponent=(6, 2), gtp=gtp, **kwargs)
    rig.finplay17_calls = []
    rig.engine.finplay17 = lambda: rig.finplay17_calls.append(rig.game.season.gtp)        # the rounds without the player are not these tests'
    season = rig.game.season
    season.calendar = shipped
    season.schedule = shipped.entries_of(COMMANDERS)
    return rig


def scripted(count):
    """Two draws for each of `count` computer games: the visitor's index 17 (17 points) against the home team's index 1 (0): the visitor wins."""
    draws = Draws()
    for _ in range(count):
        draws.rnd(32, 17).rnd(32, 1)
    return draws


def test_the_bye_week_tells_the_other_games_in_the_calendars_order_and_no_game_of_the_players(tmp_path, shipped):
    from seasonrig import run
    rig = calendar_rig(tmp_path, shipped, gtp=7)
    assert rig.game.season.on_bye
    result = run(rig, rig.engine.bye_week, scripted(14))
    lines = texts(rig)
    assert lines[0] == " Games of week number 7. " and lines[1] == X.text("NXC-24") and len(lines) == 2 + 14
    assert result.gtp == 8 and rig.game.season.gtp == 8
    records = rig.game.season.records
    assert records.record(*team_pair(COMMANDERS)) == (0, 0)                      # no game, no record
    assert sum(sum(r) for r in records.wins) == 14 and sum(sum(r) for r in records.losses) == 14
    visitor, home = shipped.weeks[6][0]
    names = rig.game.league
    assert lines[2] == "%s over the %s by the score of 17, to 0. " % (names.team(*team_pair(visitor)), names.team(*team_pair(home)))
    assert [kind for kind, _ in rig.store.events] == ["records", "gtp"] and rig.store.events[-1] == ("gtp", 8)


def test_a_calendar_week_tells_the_players_result_and_the_games_without_his_own(tmp_path, shipped):
    from seasonrig import run
    rig = calendar_rig(tmp_path, shipped, gtp=1, scores=(24, 17))
    run(rig, rig.engine.pog, scripted(15))
    lines = texts(rig)
    assert lines[0] == " Games of week number 1. " and len(lines) == 2 + 15                  # the week has 16 games, one of them the player's
    own = rig.game.league.team(*team_pair(COMMANDERS))
    assert lines[1].startswith(own + " over the ") or own in lines[1]
    records = rig.game.season.records
    assert records.record(*team_pair(COMMANDERS)) == (1, 0) and sum(sum(r) for r in records.wins) == 16
    assert rig.game.season.gtp == 2


def test_the_last_regular_week_of_a_calendar_ends_the_regular_season_at_week_19(tmp_path, shipped):
    from seasonrig import run
    rig = calendar_rig(tmp_path, shipped, gtp=18, scores=(24, 17))
    records = rig.game.season.records
    for team in range(1, 33):                                                    # 17 games each before the last: a hand-made, whole season
        division, place = team_pair(team)
        wins = 2 if team == COMMANDERS else 8 + (team % 5)
        records.wins[division - 1][place - 1], records.losses[division - 1][place - 1] = wins, 16 - wins
    run(rig, rig.engine.pog, scripted(15))
    season = rig.game.season
    assert season.gtp == 19 and season.in_playoffs and season.records.record(*team_pair(COMMANDERS)) == (3, 14)       # the 17th game was won: out of the play-offs
    kinds = [kind for kind, _ in rig.store.events]
    assert kinds[-2:] == ["pairings", "byes"]                                    # football.gtp is not written for a team that is out
    assert rig.finplay17_calls == [19]                                           # the rounds without him start at the wild card week, week 19
    assert len(season.playoffs.pairings) == 4 and len(season.playoffs.byes) == 4
    assert texts(rig)[-1].endswith("did not make it into the playoffs. ")


# ----- whole seasons on the Franchise rig -----

def play_until(tmp_path, target, scores=None, seasons=None, **kwargs):
    extra = {} if scores is None else {"scores": scores}
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, policy=enter_until(lambda: rig.game.season.gtp == target), **extra, **kwargs)
    return run_until(rig)


def test_a_franchise_plays_the_real_calendar_with_a_bye_week_and_17_games(tmp_path):
    rig = play_until(tmp_path, 19, scores=lambda r: (28, 10))
    league, season = rig.fstore.league, rig.game.season
    assert season.calendar is not None and league.calendar is not None and league.regular_weeks == 18 and season.gtp == 19
    team = league.team                                                         # the Bengals: the rig's player takes the first team
    played = [play["gtp"] for play in rig.plays if play["gtp"] <= 18]
    assert played == [week for week in range(1, 19) if week != 6]              # no game in the Bengals' bye week, 17 games in all
    regular = [row for row in league.results if row[0] == 0]
    assert len(regular) == 272
    for t in range(1, 33):
        assert sum(1 for row in regular if t in (row[2], row[3])) == 17
    text = spoken(rig)
    assert X.text("NXC-23") in text and X.text("NXC-22") in text and X.text("NXC-24") in text      # today's game, the menu's first choice, the results
    assert any(line.startswith(" This is week  6 of ") for line in text)


def test_the_play_offs_follow_week_18_and_the_next_season_has_its_own_calendar(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=lambda r: (28, 10),
                        policy=enter_until(lambda: rig.fstore.league is not None and rig.fstore.league.season == 2 and rig.game.season.gtp == 2))
    run_until(rig)
    league, season = rig.fstore.league, rig.game.season
    assert league.season == 2 and season.calendar is not None and season.regular_weeks == 18
    assert "season 2027" in season.calendar.label and league.calendar["weeks"] != fixtures.for_season(1).to_rows()
    weeks = [play["gtp"] for play in rig.plays]
    first = weeks[:weeks.index(1, 1)]
    assert first[-3:] == [20, 21, 22]                                            # the division round, the conference final and the Super Bowl (week 19, the wild card round, was his bye)
    assert first[:17] == [week for week in range(1, 19) if week != 6]
    entry = league.history[-1]
    assert entry["champion"] == league.team                                      # the player won every game
    assert sum(entry["wins"]) + sum(entry["losses"]) >= 272 * 2 - 1              # the history keeps the 17-game season


def test_a_franchise_without_the_real_calendar_plays_the_originals_16_weeks(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: rig.game.season.gtp == 17))
    run_until(rig)
    assert rig.game.season.calendar is None and rig.fstore.league.calendar is None and rig.fstore.league.regular_weeks == 16
    assert [play["gtp"] for play in rig.plays] == list(range(1, 17))


def test_the_league_file_keeps_the_calendar(tmp_path):
    from nfl4.extras.franchise.league import LeagueRecord
    rig = play_until(tmp_path, 5)
    league = rig.fstore.league
    again = LeagueRecord.from_json(league.to_json())
    assert again.calendar == league.calendar and again.regular_weeks == 18 and again.schedule == league.schedule
    assert any(entry == [0, 0, 0] for entry in again.schedule) and again.games_before(5) == 16 + 16 + 16 + 16


def test_a_league_file_of_format_11_is_the_originals_16_weeks_and_its_offseason_news_moves_to_the_new_week(tmp_path):
    import json
    from nfl4.extras.franchise.league import LeagueRecord
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM, policy=enter_until(lambda: rig.game.season.gtp == 4))
    run_until(rig)
    league = rig.fstore.league
    league.news.append({"season": 1, "week": 16, "pool": "NWD", "markup": "The first pick.", "told": 1})        # an offseason line as format 11 kept it
    data = json.loads(league.to_json())
    data["format"] = 11
    del data["calendar"]
    again = LeagueRecord.from_json(json.dumps(data))
    assert again.calendar is None and again.regular_weeks == 16 and again.last_prepared_week == 15
    assert [line["week"] for line in again.news if line["markup"] == "The first pick."] == [99]


# ----- the schedule the player hears, the summaries and the standings -----

def test_see_schedule_tells_18_weeks_with_one_bye_week_and_does_not_ask_whether_the_player_likes_it(tmp_path):
    from frrig import DOWN, quit_policy
    from nfl4.game import prompt_texts as PT
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + [DOWN, ENTER], real_calendar=True, policy=quit_policy)
    run_until(rig)
    text = spoken(rig)
    assert [t for t in text if t.startswith(" week ")] == [X.text("NXC-20", n=n) for n in range(1, 19)]
    assert text.count(X.text("NXC-21")) == 1 and text.index(X.text("NXC-21")) == text.index(X.text("NXC-20", n=6)) + 1       # the Bengals' bye is week 6
    assert not any("do you like this schedual" in t for t in text)
    first = text.index(X.text("NXC-20", n=1)) + 1
    assert text[first] == " Bengals verses the Buccaneers" or "verses the" in text[first]               # a game: the opponent first when the team is at home, as the original orders it


def test_the_summaries_and_the_standings_know_the_length_of_the_season(shipped):
    from nfl4.game import save_summary as SS
    from nfl4.game import save_texts as S
    from nfl4.game.league import League
    from nfl4.game.standings import Records, standings_speech
    assert SS.week_words(17, 18) == S.THE_WEEK % 17 and SS.week_words(18, 18) == S.THE_WEEK % 18
    assert SS.week_words(19, 18) == S.THE_PLAYOFF_WEEK % "Wild card play off week" and SS.week_words(22, 18) == S.THE_PLAYOFF_WEEK % "super bowl week"
    assert SS.week_words(17) == S.THE_PLAYOFF_WEEK % "Wild card play off week"                      # the original's 16 weeks
    assert "Wild card play off week" in SS.franchise_sentence("kim", "Bengals", 1, True, 19, 12, 5, 18)
    assert "week 17" in SS.franchise_sentence("kim", "Bengals", 1, True, 17, 12, 4, 18) and "Wild card" in SS.franchise_sentence("kim", "Bengals", 1, True, 17, 12, 4)
    league, records = League(), Records()
    assert standings_speech(league, records, 19, 18).heading.endswith("18")                        # after week 18, spoken
    assert standings_speech(league, records, 20, 18) is None and standings_speech(league, records, 0, 18) is None
    assert standings_speech(league, records, 17).heading.endswith("16") and standings_speech(league, records, 18) is None          # the original's 16 weeks, unchanged


def test_a_team_on_its_bye_plays_no_game_gets_no_game_injury_and_is_not_asked_about_a_hurt_player(shipped):
    import random
    from drrig import SURNAMES
    from nfl4.extras import tuning as T
    from nfl4.extras.franchise import injuries, workload
    from nfl4.extras.franchise.league import SEASON, new_league
    from nfl4.game.rnd import GameRandom

    def league_with(calendar):
        league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", COMMANDERS, "20260101-000000")
        league.stage, league.gtp = SEASON, 7
        if calendar:
            league.calendar = {"label": "x", "weeks": shipped.to_rows()}
        return league

    def draws_of(league):
        counted = []
        source = random.Random(5)

        class Counting:
            def random(self):
                counted.append(1)
                return source.random()
        injuries.after_games(league, 7, GameRandom(Counting()), SURNAMES, played=())
        return len(counted)
    with_bye, without = league_with(True), league_with(False)
    assert with_bye.has_bye(COMMANDERS, 7) and not without.has_bye(COMMANDERS, 7) and not with_bye.has_bye(COMMANDERS, 8)
    assert draws_of(without) - draws_of(with_bye) >= T.FR_INJ_GAME[0] * 3          # four teams are on their bye in week 7 (the Commanders, the Bills, the Jaguars and the Chargers): no game draws
    assert injuries.to_ask(with_bye, 7) == [] == injuries.to_ask(without, 99)
    workload.count_games(with_bye, 7, True)
    assert not any(with_bye.usage["games"].get(str(p.id)) for p in with_bye.active_of(COMMANDERS) if p is not None)         # a team on its bye played no game
    assert any(with_bye.usage["games"].get(str(p.id)) for p in with_bye.active_of(1) if p is not None)
