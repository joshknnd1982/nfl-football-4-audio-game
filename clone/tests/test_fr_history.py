"""History and records of a Franchise: the entry of a season worked by hand, the coach's career, the league records, the spoken
lines and history.txt (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

NFL_FRANCHISE_DESIGN 9, SX.8a. The season is small on purpose (a few regular games and the four play-off rounds) so every number
can be worked out here; the numbers of the entry are the ones the code must give.
"""
import random

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise.league import LeagueRecord, new_league
from nfl4.game.names import load_surnames
from nfl4.game.rnd import GameRandom

WORDS = history.Words(lambda team: "T%02d" % team)


def league_with(team=5):
    league = new_league(GameRandom(random.Random(1)), load_surnames(), "Kim", team, "L1")
    league.schedule = [[2, 1, 1]] * 16
    return league


def worked_season(league, wins_of_5=14):
    """Records: team 5 has `wins_of_5` wins, team 2 the fewest, the rest 8 and 8; the games below are the season's results."""
    values = [8, 8] * 32
    values[8], values[9] = wins_of_5, 16 - wins_of_5                    # team 5
    values[2], values[3] = 2, 14                                        # team 2
    values[0], values[1] = 12, 4                                        # team 1
    league.records = values
    league.gtp = 0
    league.results = [[0, 1, 5, 2, 31, 10], [0, 2, 5, 3, 28, 14], [0, 3, 5, 2, 17, 14], [0, 4, 6, 5, 21, 20],
                      [1, 17, 1, 9, 24, 20], [2, 18, 5, 1, 31, 17], [3, 19, 5, 7, 20, 17], [4, 20, 5, 12, 35, 10]]
    return league


def test_the_entry_of_a_season_is_worked_out_from_the_results_and_the_records():
    entry = history.build_entry(worked_season(league_with()))
    assert entry["season"] == 1 and entry["team"] == 5 and entry["coach"] == "Kim"
    assert entry["champion"] == 5 and entry["runner_up"] == 12
    assert entry["wins"][4] == 14 and entry["losses"][4] == 2 and entry["wins"][1] == 2
    finish = entry["finish"]
    assert finish[4] == D.FINISH_CHAMPION and finish[11] == D.FINISH_SUPER_BOWL and finish[6] == D.FINISH_CHAMPIONSHIP
    assert finish[0] == D.FINISH_DIVISION and finish[8] == D.FINISH_WILD_CARD
    assert all(finish[t] == D.FINISH_MISSED for t in range(32) if t not in (4, 11, 6, 0, 8))
    assert entry["playoff"] == [3, 0]
    assert entry["best"] == 5 and entry["worst"] == 2                   # 14 wins; team 2 has only 2
    assert entry["top_points"] == [5, 12, 35, 10] and entry["big_win"] == [5, 12, 35, 10]
    assert entry["streak"] == [5, 3]                                    # three wins in a row, first reached in week 3


def test_ties_for_the_best_and_the_worst_record_go_to_the_lower_team_number():
    league = worked_season(league_with(), wins_of_5=12)                 # team 1 and team 5 both 12 and 4
    entry = history.build_entry(league)
    assert entry["best"] == 1 and entry["worst"] == 2


def test_a_season_with_no_recorded_super_bowl_still_has_a_champion():
    league = worked_season(league_with())
    league.results = []
    entry = history.build_entry(league)
    assert entry["champion"] == 5 and entry["runner_up"] == 1


def test_the_entry_passes_the_whole_file_check_and_a_bad_one_does_not():
    league = worked_season(league_with())
    league.history.append(history.build_entry(league))
    league.results = []
    league.stage, league.stage_no = "offseason", 1
    LeagueRecord.from_json(league.to_json())
    league.history[0]["finish"][0] = 9
    try:
        LeagueRecord.from_json(league.to_json())
    except ValueError:
        pass
    else:
        raise AssertionError("an entry with a finish of 9 was accepted")


def two_seasons():
    league = worked_season(league_with(team=5))
    league.history.append(history.build_entry(league))
    league.season = 2
    league = worked_season(league, wins_of_5=9)
    league.results = [[0, 1, 5, 2, 20, 10], [0, 2, 3, 5, 45, 7], [1, 17, 2, 5, 17, 14]]    # team 5 lost the wild card game
    entry = history.build_entry(league)
    league.history.append(entry)
    return league, entry


def test_the_coach_s_career_adds_the_seasons_up():
    league, entry = two_seasons()
    assert entry["finish"][4] == D.FINISH_WILD_CARD and entry["playoff"] == [0, 1]
    career = history.career(league)
    assert career.seasons == 2 and career.wins == 14 + 9 and career.losses == 2 + 7
    assert career.playoff_wins == 3 and career.playoff_losses == 1
    assert career.playoff_seasons == 2 and career.super_bowls == 1


def test_the_league_records_keep_the_first_of_equal_values_and_name_the_season():
    league, _ = two_seasons()
    records = history.league_records(league)
    assert records.most_wins == (5, 14, 1)
    assert records.most_points == (3, 5, 45, 2)                         # 45 points beat 35
    assert records.biggest_win == (3, 5, 45, 7, 2)                      # a margin of 38 beats 25
    assert records.longest_streak == (5, 3, 1)


def test_the_spoken_lines_are_the_texts_of_the_table_newest_season_first():
    league, _ = two_seasons()
    champions = history.champions_lines(league, WORDS)
    assert champions[1] == " season 1: the T05 over the T12. " and champions[0].startswith(" season 2: the T")
    assert history.record_line(league) == " seasons: 2. wins: 23. losses: 9. play off seasons: 2. Super Bowls won: 1. "
    seasons = history.season_lines(league, WORDS)
    assert seasons[1] == (" season 1: you were 14 and 2, and won the Super Bowl. champion: the T05. the best record: the T05."
                          " the worst: the T02. ")
    assert seasons[0].startswith(" season 2: you were 9 and 7, and lost in the wild card round. ")
    records = history.record_lines(league, WORDS)
    assert records[0] == " most wins in a season: the T05, 14, season 1. "
    assert records[1] == " most points in a game: the T03, 45 against the T05, season 2. "
    assert records[2] == " the biggest win: the T03 over the T05, 45 to 7, season 2. "
    assert records[3] == " the longest winning streak: the T05, 3 games, season 1. "


def test_nothing_is_said_when_there_is_nothing_yet():
    league = league_with()
    assert history.champions_lines(league, WORDS) == [] and history.season_lines(league, WORDS) == []
    assert history.record_lines(league, WORDS) == [] and history.retired_lines(league, WORDS) == []


def test_retired_stars_are_the_kept_retired_players_with_a_peak_of_85_newest_first():
    league = league_with()
    stars = [(10, 90, 3), (11, 85, 3), (12, 84, 4), (13, 99, 2)]
    for pid, peak, left in stars:
        player = league.players[pid]
        player.status, player.peak, player.left, player.team, player.place = "retired", peak, left, 7, -1
    for pid in (10, 11, 12, 13):
        for team in league.rosters:
            if pid in team:
                team[team.index(pid)] = 0
    found = history.retired_stars(league)
    assert [p.id for p in found] == [10, 11, 13]                        # 84 is not a star; season 3 before season 2; 90 before 85
    line = history.retired_lines(league, WORDS)[0]
    assert line.startswith(" %s, " % league.players[10].name) and ", the T07. seasons played: " in line and "retired after season 3. " in line


def test_history_txt_is_plain_lines_in_the_layout_of_the_design():
    league, _ = two_seasons()
    text = history.history_text(league, WORDS)
    lines = text.split("\n")
    assert lines[0] == "Franchise history: coach Kim, the T05."
    assert lines[1] == "Written by NFL Football 4 after season 2." and lines[2] == "" and lines[3] == "Your record"
    assert lines[4] == "2 seasons, 23 wins and 9 losses. Play-offs 2 times. Super Bowls won: 1."
    season_2 = lines.index("Season 2")
    assert lines[season_2 - 1] == "" and lines[season_2 + 1].startswith("Champion: T")
    assert lines[season_2 + 2] == "Your team: 9 and 7, and lost in the wild card round."
    assert "Season 1" in lines and lines.index("Season 1") > season_2
    assert "League records" in lines and "Most wins in a season: T05, 14, season 1." in lines
    assert "Retired stars" not in lines and text.endswith(".\n")
    assert "\\" not in text and "<" not in text


def test_history_txt_has_no_retired_stars_part_until_there_is_one():
    league = league_with()
    text = history.history_text(league, WORDS)
    assert text.splitlines()[:4] == ["Franchise history: coach Kim, the T05.", "Written by NFL Football 4 before the first season.", "",
                                     "Your record"]
    assert "League records" not in text and X.text("NXG-18").strip() not in text
