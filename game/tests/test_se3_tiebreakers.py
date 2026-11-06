"""The N. F. L.'s tie-breakers for the standings and the play-off seeds of a franchise on the real calendar (nfl4 only, rule 0.13; S-E3, D-202,
Q-070). This is inspired by Jim Kitchen.

The procedures of the NFL's page (nfl.com/standings/tie-breaking-procedures, SRC-OFFICIAL): a division tie (two clubs, three or more), a wild
card tie (two clubs of different divisions, three or more with the division's best first and a head-to-head sweep), a step that sets clubs aside
starts the list again for those left, the division winners seeded by the wild card list, a coin toss that is a fixed order (no draw of the game).
"""
from types import SimpleNamespace

from nfl4.extras.franchise import data as D
from nfl4.extras.franchise.league import LeagueRecord, team_index
from nfl4.extras.franchise.mode import FranchiseHooks
from nfl4.game import tiebreak as TB
from nfl4.game.league import League
from nfl4.game.playoffs import TeamRef, real_end_of_regular_season, tiebreak_table
from nfl4.extras import nx_texts as NX
from nfl4.game.season_engine import CLASSIC_SEASON_HOOKS, SeasonEngine
from nfl4.game.standings import Records, standings_speech

R = TB.Ref


def records_of(games) -> Records:
    records = Records()
    for a, b, sa, sb in games:
        if sa == sb:
            records.tie(*a)
            records.tie(*b)
        elif sa > sb:
            records.win(*a)
            records.loss(*b)
        else:
            records.win(*b)
            records.loss(*a)
    return records


def table_of(games, key="k") -> TB.Table:
    return tiebreak_table(records_of(games), games, key)


def beat(a, b, times=1):
    return [(a, b, 24, 10)] * times


A, B, C, Dd, X = R(1, 1), R(1, 2), R(1, 3), R(1, 4), R(2, 1)


def test_two_clubs_of_a_division_head_to_head_first():
    games = beat(B, A) + beat(B, A) + beat(A, X) + beat(A, X) + beat(X, B) + beat(X, B)
    t = table_of(games)
    assert t.pct(A) == t.pct(B)
    assert TB.best_in_division(t, [A, B]) == B
    assert TB.division_order(t, 1)[:2] == [B, A]


def test_split_head_to_head_then_the_division_record():
    games = beat(A, B) + beat(B, A) + beat(A, C) + beat(C, B) + beat(X, A) + beat(B, X)
    t = table_of(games)
    assert t.pct(A) == t.pct(B)
    assert TB.best_in_division(t, [A, B]) == A                  # division: A 2-1, B 1-2


def test_three_clubs_set_aside_by_one_step_and_the_two_left_start_again_at_head_to_head():
    # A, B and C each 4-3; head-to-head among them 2-2 each; division: A 4-2, B 4-2, C 3-3 (C out); A beat B twice, so A, though B is better
    # in the common games (the next step, had the list gone on)
    games = (beat(A, B, 2) + beat(B, C, 2) + beat(C, A, 2) + beat(A, Dd, 2) + beat(B, Dd, 2) + beat(C, Dd) + beat(Dd, C)
             + beat(X, A) + beat(X, B) + beat(C, X))
    t = table_of(games)
    assert t.pct(A) == t.pct(B) == t.pct(C)
    assert TB.division_order(t, 1) == [A, B, C, Dd]
    assert TB.common_games(t, [A, B]) == [B]                     # the step the restart skips would have chosen B


def test_a_wild_card_tie_sets_aside_all_but_each_divisions_best_then_head_to_head():
    E, F = R(2, 2), R(1, 3)
    games = beat(E, R(1, 2)) + beat(R(1, 2), R(3, 1)) + beat(F, R(3, 2)) + beat(R(3, 3), E)
    t = table_of(games)
    rank = {R(1, 2): 1, F: 2, E: 1}
    assert TB.best_for_wild_card(t, [R(1, 2), F, E], rank) == E   # F set aside by its division's order; E beat R(1, 2)


def test_two_wild_card_clubs_that_did_not_meet_go_to_the_conference_record():
    E, F = R(1, 2), R(2, 2)
    games = beat(E, R(3, 1)) + beat(R(5, 1), E) + beat(R(3, 3), F) + beat(F, R(6, 1))
    t = table_of(games)
    assert TB.best_for_wild_card(t, [E, F], {E: 1, F: 1}) == E   # E 1-0 in the conference, F 0-0 there


def test_a_head_to_head_sweep_decides_three_wild_card_clubs():
    E, F, G = R(1, 2), R(2, 2), R(3, 2)
    games = (beat(G, E) + beat(G, F) + beat(E, R(4, 1), 3) + beat(F, R(4, 2), 3) + beat(R(4, 3), G) + beat(R(4, 4), G) + beat(G, R(5, 1))
             + beat(R(5, 3), E) + beat(R(5, 4), F))
    t = table_of(games)
    assert t.pct(E) == t.pct(F) == t.pct(G)
    assert TB.best_for_wild_card(t, [E, F, G], {E: 1, F: 1, G: 1}) == G


def test_the_coin_toss_is_a_fixed_order_of_the_league_and_season():
    t = table_of([])
    first = TB.best_in_division(t, [A, B, C, Dd])
    assert TB.best_in_division(table_of([]), [A, B, C, Dd]) == first
    winners = {TB.best_in_division(table_of([], "league:%d" % season), [A, B]) for season in range(1, 40)}
    assert winners == {A, B}                                      # the key changes who wins, now and then
    TB.division_order(t, 1)
    assert any("coin toss" in str(note) for note in t.notes)


def test_combined_ranking_counts_a_shared_place_as_held_alone():
    games = [(A, X, 30, 10), (B, R(2, 2), 30, 20), (C, R(2, 3), 10, 0)]
    t = table_of(games)
    teams = [A, B, C]
    assert t.combined_rank(A, teams) == 1 + 2 and t.combined_rank(B, teams) == 1 + 3 and t.combined_rank(C, teams) == 3 + 1


STANDARD_WINS = {1: 13, 2: 12, 3: 11, 4: 10, 5: 10, 6: 11, 7: 12, 8: 13}
SECOND = {1: 9, 2: 10, 3: 8, 4: 7, 5: 9, 6: 8, 7: 10, 8: 7}


def standard_records() -> Records:
    records = Records()
    for d in range(1, 9):
        for p in range(1, 5):
            wins = STANDARD_WINS[d] if p == 1 else (SECOND[d] if p == 2 else (6 if p == 3 else 3))
            records.wins[d - 1][p - 1], records.losses[d - 1][p - 1] = wins, 17 - wins
    return records


def test_the_players_team_gets_no_favour_on_a_tie_it_loses_q43_is_gone_with_the_tie_breakers():
    own = TeamRef(4, 3)
    records = standard_records()
    records.wins[3][2], records.losses[3][2] = 8, 9                   # as many wins as D3's place 2, the third wild card
    without = real_end_of_regular_season(records, own)                # D-138: Q43 gives the player's team the place
    assert without.afc_wild_cards[2].team == own
    lost = real_end_of_regular_season(records, own, [((3, 2), (4, 3), 20, 17)], "k")
    assert lost.afc_wild_cards[2].team == TeamRef(3, 2) and lost.where(own) == "out" and not lost.player_in_playoffs
    won = real_end_of_regular_season(records, own, [((4, 3), (3, 2), 20, 17)], "k")
    assert won.afc_wild_cards[2].team == own and won.player_in_playoffs and won.seed_of[own] == 7
    assert won.afc_wild_cards[2].wins == 8 and won.afc_wild_cards[2].losses == 9


def test_equal_division_winners_are_seeded_by_the_wild_card_list_not_the_division_order():
    records = standard_records()
    for d in (1, 2):
        records.wins[d - 1][0], records.losses[d - 1][0] = 12, 5
    games = [((2, 1), (1, 1), 31, 3)]
    notes: list = []
    result = real_end_of_regular_season(records, TeamRef(4, 4), games, "k", notes)
    assert [q.team for q in result.afc_seeds][:2] == [TeamRef(2, 1), TeamRef(1, 1)]
    assert result.byes[0] == TeamRef(2, 1) and any("head-to-head" in str(n) for n in notes)
    plain = real_end_of_regular_season(records, TeamRef(4, 4))
    assert plain.afc_seeds[0].team == TeamRef(1, 1)                  # D-138's order without results: the division order


def test_the_standings_speech_follows_the_orders_given():
    league = League()
    records = standard_records()
    plain = standings_speech(league, records, 5, 18)
    turned = standings_speech(league, records, 5, 18, {d: [4, 3, 2, 1] for d in range(1, 9)})
    assert turned.divisions[0][1] == list(reversed(plain.divisions[0][1]))


def test_the_franchise_gives_its_regular_season_results_and_classic_none():
    assert CLASSIC_SEASON_HOOKS.tiebreak_games() is None
    league = LeagueRecord(league_id="abc", season=3)
    league.results = [[D.STAGE_CODE["regular"], 1, team_index(1, 1), team_index(5, 2), 20, 10],
                      [D.STAGE_CODE["wild_card"], 19, team_index(1, 1), team_index(1, 2), 14, 7]]
    games, key = FranchiseHooks(SimpleNamespace(league=league)).tiebreak_games()
    assert games == [((1, 1), (5, 2), 20, 10)] and key == "abc:3"


def spoken(notes, own):
    fake = SimpleNamespace(name=lambda team: "team %d %d" % team, STEP_TEXT=SeasonEngine.STEP_TEXT, TIE_TEXT=SeasonEngine.TIE_TEXT)
    return SeasonEngine._tiebreak_lines(fake, notes, own)


def test_the_player_hears_when_a_tie_breaker_decided_his_last_wild_card_place():
    own = TeamRef(4, 3)
    records = standard_records()
    records.wins[3][2], records.losses[3][2] = 8, 9
    notes: list = []
    real_end_of_regular_season(records, own, [((3, 2), (4, 3), 20, 17)], "k", notes)
    assert spoken(notes, own) == [NX.text("NXC-29", other="team 3 2", step="the games between the teams")]
    notes = []
    real_end_of_regular_season(records, own, [((4, 3), (3, 2), 20, 17)], "k", notes)
    assert spoken(notes, own) == [NX.text("NXC-28", other="team 3 2", step="the games between the teams")]
    assert spoken(notes, TeamRef(8, 4)) == []                          # another conference's tie says nothing to this player


def test_the_player_hears_when_a_tie_breaker_decided_his_division_title_and_nothing_for_a_seed_inside_the_bracket():
    records = standard_records()
    records.wins[0][1], records.losses[0][1] = 13, 4                   # D1's place 2 as good as its place 1
    notes: list = []
    result = real_end_of_regular_season(records, TeamRef(1, 2), [((1, 1), (1, 2), 27, 20), ((1, 2), (1, 1), 10, 9),
                                                                 ((1, 1), (1, 3), 30, 0), ((1, 3), (1, 2), 14, 13)], "k", notes)
    assert result.winners[0].team == TeamRef(1, 1)                     # split head-to-head; the division record 2-1 against 1-2
    assert spoken(notes, TeamRef(1, 2)) == [NX.text("NXC-27", other="team 1 1", step="the record in division games")]
    assert spoken(notes, TeamRef(1, 1)) == [NX.text("NXC-26", other="team 1 2", step="the record in division games")]
    records = standard_records()
    for d in (1, 2):
        records.wins[d - 1][0], records.losses[d - 1][0] = 12, 5
    notes = []
    real_end_of_regular_season(records, TeamRef(1, 1), [((2, 1), (1, 1), 31, 3)], "k", notes)
    assert notes and spoken(notes, TeamRef(1, 1)) == []                # only the seeds 1 and 2: no sentence


def test_every_step_has_its_words_and_every_text_is_short():
    steps = {name for name, _ in TB.DIVISION_STEPS + TB.WILD_TWO_STEPS + TB.WILD_THREE_STEPS} | {"division order"}
    assert steps == set(SeasonEngine.STEP_TEXT)
    for text_id in list(SeasonEngine.STEP_TEXT.values()) + list(SeasonEngine.TIE_TEXT.values()) + ["NXH-87"]:
        assert 0 < len(NX.text(text_id)) <= 200
