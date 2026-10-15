"""A regular week of the season engine, pog before week 17 (GAME_SPEC 5.14, Q41, Q42). This is inspired by Jim Kitchen.

Strict draws written by hand from the lifted pog (0x464434 to 0x465c98: the team and score draws of the 15 other games,
0x462f64 to 0x4642fa the heading and the player's game, 0x4660ce to 0x466379 the wait and its repeat).
"""
import random

from nfl4.game.league import DIVISIONS, PLACES, League
from nfl4.game.playoffs import TeamRef, score_of
from nfl4.game.season_engine import KEY_CODES_OF_REPEAT
from pagrig import Draws
from randsources import StuckRandom
from seasonrig import ENTER, F1, F2, run, season_rig, texts

LEAGUE = League()
ALL = [TeamRef(d, p) for d in range(1, DIVISIONS + 1) for p in range(1, PLACES + 1)]
OWN, OPP = TeamRef(1, 1), TeamRef(2, 3)           # the Bengals and the Jets
OTHERS = [t for t in ALL if t not in (OWN, OPP)]  # 30 teams in division and place order


def name(team):
    return LEAGUE.team(*team)


def team_draws(draws: Draws, team: TeamRef) -> Draws:
    return draws.rnd(8, team.division).rnd(4, team.place)


def standard_games(start=0):
    """The games of OTHERS taken two at a time: (A, ia, B, ib). Even games: A has index 23 (24 points), B index 5 (6) and
    A wins; odd games: A index 3 (3 points), B index 12 (10) and B wins."""
    games = []
    for i in range(start, 15):
        a, b = OTHERS[2 * i], OTHERS[2 * i + 1]
        games.append((a, 23, b, 5) if i % 2 == 0 else (a, 3, b, 12))
    return games


def week_draws(games) -> Draws:
    draws = Draws()
    for a, ia, b, ib in games:
        team_draws(draws, a).rnd(32, ia)
        team_draws(draws, b).rnd(32, ib)
    return draws


def expected_line(a, ia, b, ib):
    """Written from the lifted text: the higher index wins (La0 <= L208: B), "<w> over the <l> by the score of <w>, to <l>. "."""
    if ia <= ib:
        winner, loser, ws, ls = b, a, score_of(ib), score_of(ia)
    else:
        winner, loser, ws, ls = a, b, score_of(ia), score_of(ib)
    return "%s over the %s by the score of %d, to %d. " % (name(winner), name(loser), ws, ls)


def test_a_regular_week_speaks_the_heading_the_players_result_and_the_15_other_games(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5)
    games = standard_games()
    result = run(rig, rig.engine.pog, week_draws(games))
    lines = [" Games of week number 5. ", "Bengals over the Jets by the score of 24, to 17. "]
    lines += [expected_line(*g) for g in games]
    assert texts(rig) == lines and len(lines) == 17
    assert rig.game.replay == lines                      # say2 lines are kept for the replay
    assert rig.log == lines + [""]                       # ptf = 1: every line, then Print #3,
    assert result.gtp == 6 and not result.season_over and rig.game.season.gtp == 6 and rig.game.ptf == 1
    assert rig.keys.waits == 1


def test_the_first_games_are_worked_out_by_hand():
    """OTHERS starts Browns (1,2), Ravens (1,3), Steelers (1,4), Bills (2,1): game 0 has Browns index 23 (24) against Ravens
    index 5 (6): Browns win; game 1 has Steelers index 3 (3) against Bills index 12 (10): the Bills win."""
    games = standard_games()
    assert expected_line(*games[0]) == "Browns over the Ravens by the score of 24, to 6. "
    assert expected_line(*games[1]) == "Bills over the Steelers by the score of 10, to 3. "


def test_every_team_plays_once_and_the_records_add_up(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5)
    run(rig, rig.engine.pog, week_draws(standard_games()))
    records = rig.game.season.records
    wins = sum(sum(row) for row in records.wins)
    losses = sum(sum(row) for row in records.losses)
    assert (wins, losses) == (16, 16)
    for team in ALL:
        assert sum(records.record(*team)) == 1                         # one game for everybody
    assert records.record(1, 1) == (1, 0) and records.record(2, 3) == (0, 1)       # the player's game: Bengals won
    assert records.record(1, 2) == (1, 0) and records.record(1, 3) == (0, 1)       # Browns beat the Ravens
    assert rig.store.events == [("records", records.as_file_values()), ("gtp", 6)]


def test_a_team_that_has_played_and_equal_scores_are_drawn_again(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5)
    draws = Draws()
    team_draws(draws, OWN)                                   # the player's own team has played: drawn again (division AND place)
    team_draws(draws, TeamRef(1, 2)).rnd(32, 5)              # the Browns, index 5 (6 points)
    team_draws(draws, TeamRef(1, 2))                         # the same team again: it has played now
    team_draws(draws, TeamRef(1, 3)).rnd(32, 6)              # the Ravens, index 6 has the same 6 points: drawn again
    draws.rnd(32, 17)                                        # index 17: 17 points; 5 <= 17: the Ravens win
    games = standard_games(start=1)
    # the first game used OTHERS[0], OTHERS[1] = Browns, Ravens; the remaining 14 games are OTHERS[2:] two at a time
    rest = week_draws(standard_games(start=1))
    draws.extend(rest)
    run(rig, rig.engine.pog, draws)
    line = texts(rig)[2]
    assert line == "Ravens over the Browns by the score of 17, to 6. "
    assert rig.game.rnd.fallbacks == 0


def test_the_player_loses_and_a_tie_goes_to_the_opponent_q41(tmp_path):
    for scores, line in (((10, 24), "Jets over the Bengals by the score of 24, to 10. "),
                         ((17, 17), "Jets over the Bengals by the score of 17, to 17. ")):
        rig = season_rig(tmp_path / str(scores[0]), answers=[ENTER], gtp=2, scores=scores)
        run(rig, rig.engine.pog, week_draws(standard_games()))
        assert texts(rig)[1] == line
        assert rig.game.season.records.record(2, 3) == (1, 0) and rig.game.season.records.record(1, 1) == (0, 1)


def test_f1_and_f2_speak_the_17_lines_again_with_say2_and_wait_again(tmp_path):
    rig = season_rig(tmp_path, answers=[F1, F2, ENTER], gtp=5)
    games = standard_games()
    run(rig, rig.engine.pog, week_draws(games))
    first = [" Games of week number 5. ", "Bengals over the Jets by the score of 24, to 17. "]
    first += [expected_line(*g) for g in games]
    assert texts(rig) == first * 3 and rig.keys.waits == 3
    assert rig.game.replay == first                      # emptied at each repeat, then the 17 lines again
    assert rig.game.norep == 0                           # this wait does not use inrep
    assert rig.store.kinds() == ["records", "gtp"]


def test_the_wait_ends_on_any_other_key_and_stops_the_speech_still_running(tmp_path):
    rig = season_rig(tmp_path, answers=[27], gtp=5, speech_per_char=0.001)
    run(rig, rig.engine.pog, week_draws(standard_games()))
    kinds = [kind for kind, _ in rig.sapi.events]
    assert rig.keys.waits == 1 and kinds.index("stop") > max(i for i, k in enumerate(kinds) if k == "speak")


def test_week_16_goes_on_to_the_end_of_the_season_and_writes_no_gtp_of_its_own(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=16)
    reached = []
    rig.engine._end_of_regular_season = lambda: reached.append(rig.game.season.gtp)
    result = run(rig, rig.engine.pog, week_draws(standard_games()))
    assert reached == [17] and result.gtp == 17
    assert rig.store.kinds() == ["records"]                  # the end of the season writes what it has to, not this call


def test_a_source_that_never_gives_a_free_team_still_ends_through_the_bounded_redraws(tmp_path):
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5, rng=StuckRandom(0.0))
    rig.engine.pog()
    records = rig.game.season.records
    assert (sum(map(sum, records.wins)), sum(map(sum, records.losses))) == (16, 16)
    assert rig.game.rnd.fallbacks >= 15                      # every team draw after the first fell back to the scan
    assert len(texts(rig)) == 17


def test_seeded_weeks_every_team_once_no_tie_and_no_fallback(tmp_path):
    rig = season_rig(tmp_path, gtp=5, rng=random.Random(2024))
    for week in range(200):
        rig.game.season.records.reset()
        rig.game.season.gtp = 5
        rig.keys.answers.append(ENTER)
        before = len(rig.said)
        rig.engine.pog()
        lines = texts(rig, before)
        assert len(lines) == 17 and lines[0] == " Games of week number 5. "
        records = rig.game.season.records
        assert all(sum(records.record(*t)) == 1 for t in ALL)
        assert sum(map(sum, records.wins)) == 16
        for line in lines[2:]:
            winner, loser = line.split(" over the ")[0], line.split(" over the ")[1].split(" by the score of ")[0]
            w, l = line.split(" by the score of ")[1].rstrip(". ").split(", to ")
            assert winner != loser and int(w) > int(l)       # never tied, the winner has more
    assert rig.game.rnd.fallbacks == 0
    assert max(len(rig.game.replay), rig.game.replay_longest) == 17


def test_the_repeat_keys_are_f1_and_f2_only():
    assert KEY_CODES_OF_REPEAT == (str(F1), str(F2))
