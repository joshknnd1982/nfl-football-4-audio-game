"""The Franchise's compensatory picks (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8m, research B4 and F2, D-073): the rule (the offsetting, the net
loss, a team's four, the league's 32, the round by value), the picks in the next offseason's draft at the end of rounds 3 to 7, the end of free agency on the
program rig, the stage 4 sentences, and the whole-file check.
"""
import random

import pytest
from drrig import SURNAMES, at_stage, draft_league, offseason_rig, saved_league
from frrig import spoken
from test_fr_market_flow import END_ROUND, market_league, start_of

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import comp, contracts as CT, data as D, draft as DR, market as M
from nfl4.extras.franchise.league import LeagueError, LeagueRecord
from nfl4.game.rnd import GameRandom

TEAM = 5


def mv(pid, left, joined, salary):
    return [pid, left, joined, salary]


# ----- the rule -----

def test_a_lost_free_agent_is_offset_only_by_a_gained_one_of_an_equal_or_higher_value():
    moves = [mv(1, 1, 2, 80), mv(2, 1, 3, 60), mv(3, 4, 1, 70)]
    assert comp.team_values(1, moves) == [80]                          # lost 2, gained 1: net loss 1; the 70 offsets the 60; the 80 is left
    moves.append(mv(4, 1, 6, 30))
    assert comp.team_values(1, moves) == [80, 30]                      # a third loss: the net loss is 2, the 80 and the 30
    assert comp.team_values(1, [mv(1, 1, 2, 80), mv(2, 3, 1, 50), mv(3, 1, 4, 60)]) == [80]   # the 50 offsets nothing; net loss 1


def test_a_gained_free_agent_of_the_same_value_offsets_a_lost_one():
    assert comp.team_values(1, [mv(1, 1, 2, 60), mv(2, 1, 4, 30), mv(3, 3, 1, 60)]) == [30]      # the gained 60 offsets the lost 60 (equal); the 30 is left


def test_a_compensatory_pick_is_paid_as_the_last_pick_of_its_round():
    assert CT.pick_number(3, 33) == CT.pick_number(3, 40) == 96 and CT.pick_number(4, 1) == 97 and CT.pick_number(1, 5) == 5


def test_the_net_loss_in_number_and_the_teams_four_bound_the_picks():
    moves = [mv(i, 1, 2 + i, 30 + i) for i in range(1, 8)]               # seven lost, none gained
    assert comp.team_values(1, moves) == [37, 36, 35, 34]              # the four highest (FR_COMP_TEAM_MAX)
    assert len(comp.team_values(1, moves + [mv(20, 9, 1, 25), mv(21, 9, 1, 25), mv(22, 9, 1, 25), mv(23, 9, 1, 25)])) == 3      # net loss 3
    assert comp.team_values(1, [mv(1, 1, 2, T.FR_COMP_QUALIFY - 1)]) == []      # under the qualifying salary: no compensatory free agent
    assert comp.team_values(1, [mv(1, 1, 2, T.FR_COMP_QUALIFY)]) == [T.FR_COMP_QUALIFY]
    assert comp.team_values(1, [mv(1, 1, 1, 90)]) == []                # a player who signed again with the team he left is no loss


def test_the_round_of_a_pick_follows_the_value_of_the_player_lost():
    for least, round_no in T.FR_COMP_ROUNDS:
        assert comp.round_of(least) == round_no
    assert comp.round_of(T.FR_COMP_ROUNDS[0][0] + 100) == 3 and comp.round_of(0) == 7


def test_the_award_keeps_the_leagues_32_highest_and_writes_them_for_the_next_draft():
    league = draft_league(seed=4)
    league.comp = [[league.season, 5, 3, 40]]                         # a row of this season's draft stays
    moves = [mv(100 * t + i, t, 1 + (t % 32), 40 + 3 * t + i) for t in range(1, 33) for i in range(4)]      # every team loses four, gains four
    moves += [mv(9000 + t, t, 1 + (t + 5) % 32, 30) for t in range(1, 33)]
    rows = comp.award(league, [m for m in moves if m[1] != m[2]])
    assert len(rows) <= T.FR_COMP_TOTAL
    assert all(r[0] == league.season + 1 for r in rows)
    assert [league.season, 5, 3, 40] in league.comp and all(r in league.comp for r in rows)
    assert rows == sorted(rows, key=lambda r: (r[1], -r[3], comp.tie(r[2], league.season + 1)))
    big = [mv(i, 1 + i % 16, 17 + i % 16, 40 + i) for i in range(1, 200)]
    rows = comp.award(league, big)
    assert len(rows) == T.FR_COMP_TOTAL
    values = sorted((v, t) for t in range(1, 33) for v in comp.team_values(t, big))
    assert min(r[3] for r in rows) >= sorted(v for v, _ in values)[-T.FR_COMP_TOTAL]     # the highest 32 values were kept


def test_the_draft_of_the_next_offseason_puts_the_picks_at_the_end_of_their_rounds_by_value():
    league = draft_league(seed=4, team=TEAM)
    league.comp = [[league.season, 3, 7, 80], [league.season, 3, 9, 90], [league.season, 7, TEAM, 40], [league.season + 1, 4, 2, 60]]
    draft = DR.Draft.create(league, GameRandom(random.Random(4)), SURNAMES)
    assert draft.data["comp"] == [[3, 9], [3, 7], [7, TEAM]]
    assert league.comp == [[league.season + 1, 4, 2, 60]]              # this draft's rows are the draft's now; next year's stay
    assert len(draft.data["class"]) == T.FR_CLASS_SIZE + 3 and draft.total == D.DRAFT_PICKS + 3
    assert draft.slot(96) == (3, 32, draft.order[31]) and draft.slot(97) == (3, 33, 9) and draft.slot(98) == (3, 34, 7) and draft.slot(99) == (4, 1, draft.order[0])
    assert draft.slot(draft.total) == (7, 33, TEAM)
    assert (7, 33) in draft.picks_of(TEAM) and draft.comp_picks_of(TEAM) == [(7, 33)] and draft.own_picks_only(TEAM)      # (the compensatory picks are told apart)
    while not draft.done:
        _, _, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    league.stage_no = D.STAGE_DRAFT
    league.check()
    by_pick = {tuple(p.drafted[1:]): p for p in league.players.values() if p.drafted and p.drafted[0] == league.season}
    assert by_pick[(3, 33)].team == 9 and by_pick[(7, 33)].team == TEAM
    assert by_pick[(3, 33)].salary == CT.rookie_salary(96) and by_pick[(4, 1)].salary == CT.rookie_salary(97)      # paid by the regular pick number


def test_the_draft_check_refuses_a_compensatory_pick_in_round_2_a_fifth_for_a_team_and_a_wrong_class():
    league = draft_league(seed=4, team=TEAM)
    league.comp = [[league.season, 3, 7, 80]]
    DR.Draft.create(league, GameRandom(random.Random(4)), SURNAMES)
    league.check()
    good = LeagueRecord.from_json(league.to_json())
    for change in (lambda lg: lg.draft["comp"].__setitem__(0, [2, 7]),
                   lambda lg: lg.draft["comp"].extend([[4, 7], [5, 7], [6, 7], [7, 7]]),
                   lambda lg: lg.draft["class"].pop()):
        bad = LeagueRecord.from_json(good.to_json())
        change(bad)
        with pytest.raises(LeagueError):
            bad.check()


def test_the_leagues_rows_are_checked_whole():
    league = draft_league(seed=4)
    league.stage, league.stage_no = "season", 0
    league.gtp, league.records = 1, [0] * 64
    league.comp = [[league.season, 3, 7, 80], [league.season + 1, 7, 2, 20]]
    league.check()
    for rows in ([[league.season + 2, 3, 7, 80]], [[league.season, 2, 7, 80]], [[league.season, 3, 33, 80]], [[league.season, 3, 7, 80]] * 5,
                 [[league.season, 3, 7]]):
        league.comp = rows
        with pytest.raises(LeagueError):
            league.check()


def test_stage_six_drops_the_rows_of_a_draft_that_is_over():
    league = draft_league(seed=4)
    league.comp = [[league.season, 3, 7, 80], [league.season + 1, 4, 2, 60]]
    league.season += 1
    comp.drop_past(league)
    assert league.comp == [[league.season, 4, 2, 60]]


# ----- on the program rig -----

def test_free_agency_awards_next_years_compensatory_picks_from_the_signings_of_its_rounds(tmp_path):
    league = market_league()
    copy_of = start_of(league)
    rounds = M.run_market(copy_of, skip=(TEAM,))                       # the player ends every round without an offer: his team is skipped
    expected = comp.award(copy_of, [m for r in rounds for m in r.moves])
    rig = offseason_rig(tmp_path, league, keys=END_ROUND * T.FR_FA_ROUNDS, until=at_stage(D.STAGE_DRAFT), picks_told="mine")
    after = LeagueRecord.from_json(rig.kept[D.STAGE_DRAFT].decode("utf-8"))
    assert [r for r in after.comp if r[0] == league.season + 1] == expected
    if len(expected) > 1:
        assert X.text("NXU-60", n=len(expected)) in spoken(rig)
    own = sorted(r[1] for r in expected if r[2] == TEAM)
    if own:
        assert any(t.startswith(" your team gets") for t in spoken(rig))


def test_the_market_records_every_signing_with_the_team_he_left():
    league = market_league()
    before = {p.id: p.team for p in M.pool(league)}
    rounds = M.run_market(league, skip=(TEAM,))
    moves = [m for r in rounds for m in r.moves]
    signed = [p for r in rounds for p, _bid in r.signed]
    assert len(moves) == len(signed) and moves
    for (pid, left, joined, salary), player in zip(moves, signed):
        assert pid == player.id and left == before[pid] and joined == player.team and salary == player.salary


def test_the_draft_stage_tells_the_compensatory_picks_and_the_players_own(tmp_path):
    league = draft_league(seed=4, team=TEAM)
    league.comp = [[league.season, 3, 9, 90], [league.season, 5, TEAM, 45]]
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine")
    text = spoken(rig)
    assert X.text("NXU-10", n=2) in text
    assert X.text("NXU-12", list=X.text("NXK-15", round=5, pick=33)) in text
    after = LeagueRecord.from_json(rig.kept[D.STAGE_CUT].decode("utf-8"))
    assert len(after.draft["picks"]) == D.DRAFT_PICKS + 2 and after.comp == []
    assert any(p.drafted == [league.season, 5, 33] and p.team == TEAM for p in after.players.values())


def test_a_free_agent_who_leaves_for_another_team_earns_his_old_team_a_pick_next_year(tmp_path):
    """Team 2 cannot pay its own quarterback again (it is broke); team 7's quarterback place is empty: he signs with team 7 (or another team with the
    room), and team 2 gets a compensatory pick for next year's draft, written at the end of the stage and told."""
    def open_quarterback(league):
        from nfl4.extras.franchise import resign
        resign.let_go(league, league.player_at(7, 33))                    # team 7's place is empty (its own quarterback a free agent too)
        for player in league.players.values():
            if player.status == "free" and player.pos == "QB":
                player.seasons = max(player.seasons, 8)                     # veterans: they ask the market price (a young one asks the minimum)
    league = market_league(others=((2, 33, 84),), broke=(2,), mutate=open_quarterback)
    copy_of = start_of(league)
    rounds = M.run_market(copy_of, skip=(TEAM,))
    moves = [m for r in rounds for m in r.moves]
    expected = comp.award(copy_of, moves)
    assert any(m[1] == 2 and m[2] != 2 for m in moves) and any(r[2] == 2 for r in expected), (moves, expected)
    rig = offseason_rig(tmp_path, league, keys=END_ROUND * T.FR_FA_ROUNDS, until=at_stage(D.STAGE_DRAFT), picks_told="mine")
    after = LeagueRecord.from_json(rig.kept[D.STAGE_DRAFT].decode("utf-8"))
    assert [r for r in after.comp if r[0] == league.season + 1] == expected
    assert (X.text("NXU-60", n=len(expected)) if len(expected) > 1 else X.text("NXU-64")) in spoken(rig)
