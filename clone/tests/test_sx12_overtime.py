"""SX.12 (nfl4 only, rule 0.13): the 2026 overtime of the N. F. L. rules mode (Rule 16 of the 2026 book, D-096). This is inspired by Jim Kitchen.

The possession rule as plain logic (extras/overtime.py), the hooks H22 in both modes (Classic keeps sudden death exactly), the engine at the end
of regulation and at the end of the regular season's one period (the tie), the play-offs' periods that go on, whole seeded games, and the tie
in the season: the records, footbal6.dat, the standings, the play-off ranking, the week's result, and the Franchise (league.sav format 11).
"""
import json
from dataclasses import dataclass, field

import pytest

from nfl4.data.files import tiesfile
from nfl4.extras import overtime as OT
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.state import ExtrasRecord
from nfl4.game.league import League
from nfl4.game.playoffs import TeamRef, end_of_regular_season
from nfl4.game.rules import CLASSIC, OT_COIN_TOSS, OT_KICK_OFF, OT_SAME_BALL
from nfl4.game.standings import Records, standings_speech
from nflrig import RecordingRules, nfl_engine_rig, sim_game
from seasonrig import ENTER, records_of, run, season_rig, texts as season_texts

A, B = 1, 2


@dataclass
class Board:
    """The few values of GameState the overtime reads."""
    quarter: int = 5
    overtime: int = 1
    wisoff: int = 1
    points: dict = field(default_factory=lambda: {1: 17, 2: 17})

    def score(self, side):
        return self.points[side]


def started(receiver=A, postseason=False, base=17):
    x = ExtrasRecord(postseason=postseason)
    board = Board(wisoff=receiver, points={1: base, 2: base})
    OT.at_kickoff(x, board, 3 - receiver)
    return x, board


def score(x, board, side, points, touchdown=False):
    board.points[side] += points
    return OT.after_points(x, board, side if touchdown else None)


# ----- the possession rule (16-1-3, 16-1-4, 16-1-5) -----

def test_the_first_kick_off_of_overtime_starts_the_rule_with_its_receivers_first():
    x, board = started(receiver=B)
    assert (x.ot_phase, x.ot_first, x.ot_receiver, x.ot_base) == (OT.FIRST, B, B, 17)
    assert not OT.decided(x, board)


def test_a_first_drive_touchdown_no_longer_ends_the_game_the_try_is_played():
    x, board = started()
    assert score(x, board, A, 6, touchdown=True) is False          # 16-1-3 (a): the second team gets its possession
    assert score(x, board, A, 1) is False                           # the extra point; A kicks off next
    assert x.ot_phase == OT.FIRST


def test_a_safety_on_the_first_possession_wins_for_the_kicking_team():
    x, board = started()
    assert score(x, board, B, 2) is True                            # 16-1-3 (a)


def test_a_defensive_touchdown_on_the_first_possession_wins_at_once_with_no_try():
    x, board = started()
    assert score(x, board, B, 6, touchdown=True) is True


def test_the_second_team_answers_a_field_goal_with_a_touchdown_and_wins_with_no_try():
    x, board = started()
    assert score(x, board, A, 3) is False
    OT.at_kickoff(x, board, A)                                      # A kicks off: B's opportunity (16-1-5 (c))
    board.wisoff = B
    assert OT.at_possession(x, board) is False and x.ot_phase == OT.SECOND
    assert score(x, board, B, 6, touchdown=True) is True            # ahead after both possessions (16-1-3 (b))


def test_a_touchdown_answered_by_a_touchdown_and_extra_point_turns_into_sudden_death():
    x, board = started()
    score(x, board, A, 6, touchdown=True)
    score(x, board, A, 1)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    assert score(x, board, B, 6, touchdown=True) is False           # tied or behind: the try is played
    assert score(x, board, B, 1) is False
    assert x.ot_phase == OT.SUDDEN                                  # 16-1-3 (c): the next score wins
    assert OT.sudden_news(x, board) is True and OT.sudden_news(x, board) is False      # said once
    board.wisoff = A
    assert score(x, board, A, 3) is True


def test_a_missed_try_after_the_answering_touchdown_loses():
    x, board = started()
    score(x, board, A, 7)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    score(x, board, B, 6, touchdown=True)
    assert score(x, board, B, 0) is True                            # the try failed: A is ahead after both possessions


def test_the_second_possession_ending_without_points_ends_the_game():
    x, board = started()
    score(x, board, A, 3)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    OT.at_possession(x, board)
    board.wisoff = A                                                # a punt, a turnover, downs or a missed kick
    assert OT.at_possession(x, board) is True


def test_a_tying_field_goal_by_the_second_team_turns_into_sudden_death():
    x, board = started()
    score(x, board, A, 3)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    assert score(x, board, B, 3) is False and x.ot_phase == OT.SUDDEN


def test_the_kickers_keeping_their_kick_after_their_score_used_the_receivers_opportunity():
    x, board = started()
    score(x, board, A, 3)
    OT.at_kickoff(x, board, A)                                      # an onside kick, or a muff the kickers recover
    board.wisoff = A
    assert OT.at_possession(x, board) is True                       # 16-1-5 (c): B has had its opportunity; A is ahead


def test_a_first_possession_without_points_makes_the_next_score_win():
    x, board = started()
    board.wisoff = B
    assert OT.at_possession(x, board) is False and x.ot_phase == OT.SUDDEN
    assert score(x, board, B, 3) is True


def test_a_muffed_punt_the_kickers_keep_was_the_receivers_chance():
    x, board = started()
    OT.kickers_kept_punt(x, board, A)                               # 16-1-5 (c): the first team punted without points and kept the muff
    assert x.ot_phase == OT.SUDDEN and score(x, board, A, 3) is True
    x, board = started()
    score(x, board, A, 3)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    OT.kickers_kept_punt(x, board, B)                               # SX.13 (Q-038): the second team's punt ended its possession and the
    assert x.ot_phase == OT.OVER                                    # first team's muff was its chance: the side ahead (A) wins
    assert OT.at_possession(x, board) is True


def test_the_defense_running_back_the_first_teams_try_does_not_end_the_game():
    x, board = started()
    score(x, board, A, 6, touchdown=True)
    assert score(x, board, B, 2) is False and x.ot_phase == OT.FIRST


def test_the_first_teams_defense_scoring_on_the_second_possession_ends_it():
    x, board = started()
    score(x, board, A, 3)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    assert score(x, board, A, 6, touchdown=True) is True            # an interception run back: no try


def test_an_overtime_saved_before_sx12_goes_on_as_sudden_death():
    x = ExtrasRecord()
    board = Board()
    assert x.ot_phase == "" and score(x, board, B, 3) is True


def test_nothing_happens_before_overtime():
    x = ExtrasRecord()
    board = Board(quarter=4)
    OT.at_kickoff(x, board, A)
    assert x.ot_phase == "" and score(x, board, A, 7) is False and OT.at_possession(x, board) is False


def test_the_second_team_behind_never_punts_and_kicks_only_a_tying_field_goal():
    x, board = started()
    score(x, board, A, 3)
    OT.at_kickoff(x, board, A)
    board.wisoff = B
    assert OT.second_possession_trailing(x, board, B) == 3
    assert OT.second_possession_trailing(x, board, A) == 0
    rig_rules = NflRules()
    state = type("S", (), {})()
    state.extras, state.quarter, state.wisoff, state.half, state.yard_line = x, 5, B, 2, 30
    state.score = board.score
    assert rig_rules.overtime_fourth_down(state) == "kick"            # the other half, inside the 41: the kick ties
    state.yard_line = 45
    assert rig_rules.overtime_fourth_down(state) == "go"
    board.points[A] += 4                                              # now behind by 7: a field goal does not help
    state.yard_line = 10
    assert rig_rules.overtime_fourth_down(state) == "go"
    x2, board2 = started()
    state.extras, state.score = x2, board2.score
    assert rig_rules.overtime_fourth_down(state) is None              # the first possession: the original's rule


@pytest.mark.parametrize("period, phase, expected", [
    (2, OT.SUDDEN, OT.SAME_BALL), (3, OT.SUDDEN, OT.KICK_OFF), (3, OT.FIRST, OT.SAME_BALL), (3, OT.SECOND, OT.SAME_BALL),
    (4, OT.SUDDEN, OT.SAME_BALL), (5, OT.SUDDEN, OT.COIN_TOSS), (6, OT.SUDDEN, OT.SAME_BALL), (7, OT.SUDDEN, OT.KICK_OFF),
    (9, OT.SUDDEN, OT.COIN_TOSS)])
def test_play_off_periods_go_on_with_the_ball_a_kick_off_or_a_new_toss(period, phase, expected):
    x, board = started(postseason=True)
    x.ot_phase = phase
    board.overtime = period - 1
    assert OT.period_end(x, board) == expected
    assert x.ot_toss is (expected == OT.COIN_TOSS)


def test_the_regular_season_has_one_period():
    x, board = started()
    assert OT.period_end(x, board) is None


def test_a_save_without_a_toss_loser_gives_the_third_period_as_sx12_did():
    """SX.13: the toss's loser chooses (test_sx13_rules_audit); a record saved before SX.13 has none and keeps SX.12's reading."""
    x, board = started(receiver=B, postseason=True)
    assert x.ot_toss_loser == 0
    assert OT.third_period_receiver(x) == A
    x.ot_toss = True                                                  # the fifth period's toss: A receives its kick-off
    board.quarter = 5
    OT.at_kickoff(x, board, B)
    assert x.ot_receiver == A and x.ot_toss is False and OT.third_period_receiver(x) == B


@pytest.mark.parametrize("name, value", [("ot_phase", "late"), ("ot_first", 3), ("ot_receiver", -1), ("ot_base", -1),
                                         ("ot_kicked", 1), ("ot_told", "yes"), ("ot_toss", None), ("ot_toss_loser", 3)])
def test_a_saved_overtime_value_out_of_range_refuses_the_record(name, value):
    x, _ = started()
    x.check()
    setattr(x, name, value)
    with pytest.raises(ValueError):
        x.check()


def test_the_overtime_values_go_through_a_save():
    x, board = started(receiver=B)
    score(x, board, B, 3)
    x.ot_kicked = True
    assert ExtrasRecord.from_json(x.to_json()) == x


# ----- the hooks: Classic keeps sudden death -----

def test_classic_answers_the_overtime_hooks_with_the_originals_sudden_death():
    board = Board()
    assert CLASSIC.overtime_follows(board) is True and CLASSIC.overtime_toss(board) is False
    assert CLASSIC.points_end_game(board) is True and CLASSIC.points_end_game(board, 1) is False     # every score, the try first
    board.quarter = 4
    assert CLASSIC.points_end_game(board) is False
    assert CLASSIC.possession_ends_game(board) is False and CLASSIC.period_end_step(board) is None
    assert CLASSIC.overtime_fourth_down(board) is None
    assert CLASSIC.overtime_lines(board) == [] and CLASSIC.game_over_lines(board) == []


def test_the_nfl_rules_say_the_overtime_at_its_start_and_the_tie_at_the_end(tmp_path):
    rig = nfl_engine_rig(tmp_path, quarter=4)
    s = rig.engine.s
    assert rig.rules.overtime_follows(s) is True
    assert rig.rules.overtime_lines(s) == [X.text("NXC-06"), X.text("NXC-07")]
    s.extras.postseason = True
    assert rig.rules.overtime_lines(s) == [X.text("NXC-06"), X.text("NXC-08")]
    s.quarter = 5
    assert rig.rules.overtime_follows(s) is False
    assert rig.rules.game_over_lines(s) == [" The game ends in a tie. "]


def test_the_computer_that_wins_the_toss_kicks_off_with_the_leagues_share():
    rules = NflRules()

    class Game:
        class rnd:
            values = []

            @classmethod
            def below(cls, n):
                return cls.values.pop(0)

    rules.game = Game
    Game.rnd.values = [T.OT_KICK_FIRST_PER_MILLE - 1, T.OT_KICK_FIRST_PER_MILLE]
    assert rules.overtime_kicks_first(None) is True
    assert rules.overtime_kicks_first(None) is False


# ----- the engine -----

def test_a_tie_after_regulation_says_the_overtime_and_goes_to_its_coin_toss(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=[ENTER, ENTER], quarter=4)
    s, engine = rig.engine.s, rig.engine
    s.stats[1].score = s.stats[2].score = 20
    step = engine.game_end()
    said = [t for t, _, _ in rig.said]
    assert " We are going into over time number  1" in said or any("over time number" in t for t in said)
    assert X.text("NXC-06") in said and X.text("NXC-07") in said
    assert s.quarter == 5 and s.overtime == 1 and s.extras.period == 5 and s.extras.left == 600
    assert step == engine.overtime_coin_toss


def test_the_regular_seasons_overtime_ends_tied_at_the_end_of_its_one_period(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=[ENTER, ENTER, ENTER], quarter=5, overtime=1,
                         extras=dict(period=5, left=0, ot_phase="sudden", ot_first=1, ot_receiver=1, ot_base=20, unit="OT1"))
    s, engine = rig.engine.s, rig.engine
    s.stats[1].score = s.stats[2].score = 20
    step = engine.period_checks()
    assert step == engine.game_end
    step = engine.game_end()
    said = [t for t, _, _ in rig.said]
    assert " The game ends in a tie. " in said
    assert engine.result.scores == (20, 20) and s.finished


def test_a_play_off_period_ends_and_the_next_goes_on_with_the_ball(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=[ENTER, ENTER], quarter=5, overtime=1, gtp=17, down=3, to_go=4, yard_line=30, wisoff=2,
                         extras=dict(period=5, left=0, postseason=True, ot_phase="sudden", ot_first=1, ot_receiver=1, ot_base=20,
                                     unit="OTP1"))
    s, engine = rig.engine.s, rig.engine
    s.stats[1].score = s.stats[2].score = 20
    step = engine.period_checks()
    assert s.overtime == 2 and s.extras.period == 6 and s.extras.left == 900 and s.extras.unit == "OTP1"
    assert (s.down, s.to_go, s.yard_line, s.wisoff) == (3, 4, 30, 2)
    assert step == engine.play_menu


def test_classic_overtime_is_unchanged_the_side_with_the_ball_receives(tmp_path):
    from pagrig import engine_rig
    rig = engine_rig(tmp_path, answers=[ENTER, ENTER], quarter=4, wisoff=2)
    s, engine = rig.engine.s, rig.engine
    s.stats[1].score = s.stats[2].score = 14
    step = engine.game_end()
    assert step == engine.kick_off and s.quarter == 5 and s.defense == 1


# ----- whole seeded games -----

def _games(tmp_path, seeds, gtp):
    out = []
    for seed in seeds:
        rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
        rig, engine, rules, result = sim_game(tmp_path / ("g%d" % seed), seed, rules=rules, gtp=gtp)
        out.append((seed, rig, engine, rules, result))
    return out


@pytest.mark.parametrize("gtp, seeds", [(1, range(1, 121)), (17, range(1001, 1121))])
def test_seeded_games_follow_rule_16(tmp_path, gtp, seeds):
    overtimes = 0
    for seed, rig, engine, rules, result in _games(tmp_path, seeds, gtp):
        s, x = engine.s, engine.s.extras
        x.check()
        own, opp = result.scores
        if gtp >= 17 or not s.overtime:
            assert own != opp, seed                                   # only the regular season's overtime can end tied
        if not s.overtime:
            continue
        overtimes += 1
        if gtp < 17:
            assert s.overtime == 1, seed                              # one period (16-1-3 (d))
        if own == opp:
            assert x.left == 0 and x.ot_phase != OT.OVER, seed       # the period ran out
        else:
            assert x.ot_phase == OT.OVER or x.left == 0, seed
        coach = [e for e in rules.review.events if e[1] == "coach" and e[0] >= 5]
        assert coach == [], seed                                      # no coach's challenge in overtime (16-1-5 (d))
        unit_timeouts = {}
        for quarter, side, _left, _held, unit in rules.timeouts:
            if quarter >= 5:
                unit_timeouts[(unit, side)] = unit_timeouts.get((unit, side), 0) + 1
        limit = 3 if gtp >= 17 else 2
        assert all(n <= limit for n in unit_timeouts.values()), (seed, unit_timeouts)
    assert overtimes >= 1


# ----- the season: ties in the records, the files and the standings -----

def test_the_ties_file_holds_32_values_and_refuses_junk():
    records = Records()
    records.tie(2, 3)
    records.tie(2, 3)
    values = tiesfile.decode(tiesfile.encode(records))
    assert len(values) == 32 and values[4 + 2] == 2 and sum(values) == 2
    with pytest.raises(Exception):
        tiesfile.decode(tiesfile.encode(records)[:-2])


def test_the_store_writes_footbal6_only_while_a_team_has_a_tie(tmp_path):
    import os
    from nfl4.data.files.store import FileProgramStore
    store = FileProgramStore(str(tmp_path), str(tmp_path / "customize"))
    os.makedirs(os.path.dirname(store.path("footbal3.dat")), exist_ok=True)
    records = Records()
    store.write_records(records)
    assert os.path.exists(store.path("footbal3.dat")) and not os.path.exists(store.path("footbal6.dat"))
    records.tie(1, 1)
    store.write_records(records)
    assert os.path.exists(store.path("footbal6.dat"))
    records.reset()
    store.write_records(records)
    assert not os.path.exists(store.path("footbal6.dat"))


def test_a_tie_counts_half_a_loss_in_the_standings_and_is_said_after_the_losses():
    records = records_of({}, default=8)
    records.wins[0][:] = [9, 9, 8, 6]
    records.losses[0][:] = [7, 6, 8, 10]
    records.ties[0][:] = [0, 1, 0, 0]
    speech = standings_speech(League(), records, 17)
    lines = speech.divisions[0][1]
    assert lines[0].endswith(" 9, and 6, and 1 tie. ")              # 9-6-1 before 9-7
    assert lines[1].endswith(" 9, and 7. ")
    plain = standings_speech(League(), records_of({}, default=8), 17)
    assert all(", and 8. " in line for _, lines in plain.divisions for line in lines)


def test_the_play_off_ranking_counts_a_tie_as_half_a_win_and_half_a_loss():
    records = records_of({}, default=8)
    records.wins[1][:] = [10, 10, 3, 3]                              # division 2: 10-6 and 10-5-1
    records.losses[1][:] = [6, 5, 13, 13]
    records.ties[1][:] = [0, 1, 0, 0]
    end = end_of_regular_season(records, TeamRef(1, 1))
    winner = end.winners[1]
    assert winner.team == TeamRef(2, 2) and (winner.wins, winner.losses, winner.ties) == (10, 5, 1)


def test_classic_seasons_rank_exactly_as_before_with_no_ties():
    records = records_of({(1, 2): 12, (3, 3): 13}, default=8)
    before = end_of_regular_season(records, TeamRef(1, 1))
    assert all(q.ties == 0 for q in before.winners)


def test_a_tied_week_in_the_nfl_rules_is_a_tie_for_both_teams(tmp_path):
    from seasonrig import computer_game_draws  # noqa: F401  (the rig's draws are the week's 15 games)
    from test_season_week import standard_games, week_draws
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5, scores=(20, 20))
    rig.game.rules = NflRules()
    played = []
    rig.game.season_hooks = type("H", (), {"game_played": lambda self, *a: played.append(a),
                                           "computer_index": lambda self, team, i: i,
                                           "playoff_first_wins": lambda self, rnd, v, h: rnd(2) == 1})()
    run(rig, rig.engine.pog, week_draws(standard_games()))
    said = season_texts(rig)
    assert said[1] == "Bengals and the Jets tied at 20. "
    records = rig.game.season.records
    assert records.ties_of(1, 1) == 1 and records.ties_of(2, 3) == 1 and records.record(1, 1) == (0, 0)
    assert played[0][1:] == (5, TeamRef(1, 1), TeamRef(2, 3), 20, 20)


def test_a_tied_score_in_classic_still_goes_to_the_opponent_q41(tmp_path):
    from test_season_week import standard_games, week_draws
    rig = season_rig(tmp_path, answers=[ENTER], gtp=5, scores=(20, 20))
    run(rig, rig.engine.pog, week_draws(standard_games()))
    assert season_texts(rig)[1] == "Jets over the Bengals by the score of 20, to 20. "
    assert rig.game.season.records.ties_of(1, 1) == 0


# ----- the Franchise -----

def _league_with_a_tie():
    from test_fr_league import season_league
    league = season_league()
    return league


def test_league_sav_format_11_keeps_the_ties_and_format_10_has_none():
    from nfl4.extras.franchise import data as D
    from nfl4.extras.franchise.league import LeagueRecord
    league = _league_with_a_tie()
    assert D.FORMAT == 15
    data = json.loads(league.to_json())
    assert data["ties"] == [0] * 32
    data["format"] = 10
    del data["ties"]
    old = LeagueRecord.from_json(json.dumps(data))
    assert old.ties == [0] * 32


def test_the_history_counts_a_tie_breaks_streaks_and_says_it_after_the_losses():
    from nfl4.extras.franchise import history
    from nfl4.extras.franchise.league import LeagueRecord
    league = LeagueRecord()
    league.team = 1
    league.records = [8, 7] + [8, 8] * 31
    league.ties = [1] + [0] * 31
    league.results = [[0, 1, 1, 2, 24, 10], [0, 2, 1, 3, 20, 20], [0, 3, 1, 4, 17, 14]]
    entry = history.build_entry(league)
    assert entry["ties"][0] == 1 and entry["streak"] == [1, 1]           # the tie ended the first streak
    assert history.losses_and_ties(7, 1) == "7 and 1 tie" and history.losses_and_ties(7, 0) == "7"
    assert history.losses_and_ties(6, 2) == "6 and 2 ties"
    assert "ties" not in history.build_entry(LeagueRecord())             # a season without a tie: the entry as before


def test_the_news_never_tells_a_tie_as_a_win():
    from nfl4.extras.franchise import news
    from nfl4.extras.franchise.league import LeagueRecord
    league = LeagueRecord()
    league.results = [[0, 1, 5, 6, 20, 20], [0, 1, 7, 8, 30, 3], [0, 2, 5, 9, 14, 10]]
    assert news.week_games(league, 1) == [(7, 8, 30, 3)]
    table = news.streaks(league, 1)
    assert table[5] == (0, 0) and table[6] == (0, 0) and table[7] == (1, 1)


def test_a_tie_moves_no_morale_by_its_result():
    from nfl4.extras.franchise import people
    assert people.goal_met("win", 0, 20, 20) is False


def test_the_draft_order_counts_a_tie_as_half_a_win():
    from nfl4.extras.franchise import data as D
    from nfl4.extras.franchise import draft
    from nfl4.extras.franchise.league import LeagueRecord
    league = LeagueRecord()
    league.season = 3
    league.history = [{"season": 3, "wins": [6, 6] + [8] * 30, "finish": [D.FINISH_MISSED] * 32, "ties": [1, 0] + [0] * 30}]
    league.sums = [100] * 32
    order = draft.order_of(league)
    assert order.index(2) < order.index(1)                          # 6-10 picks before 6-9-1
