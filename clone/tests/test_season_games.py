"""Whole seeded seasons: the property checks of GAP_REGISTER G-C1 for the season engine (D-029: a season has 16 games and the
play-offs follow the rules, the seeds and the bracket are consistent). This is inspired by Jim Kitchen.

A season is played on the virtual clock the way the week loop will (S7.4): the schedule from `makes`, each week's opponent from
it, the player's game decided by a seeded score, pog after every game, the play-off opponent from footbal4.dat's data; the
Super Bowl through the presentation (pag's job) or conceded. The checks are the invariants, not the exact text (the
other test files do that with scripted draws).
"""
import random

import pytest

from nfl4.game.league import DIVISIONS, PLACES, League
from nfl4.game.playoffs import AFC_DIVISIONS, PlayoffState, TeamRef
from seasonrig import enter_policy, season_rig, texts

LEAGUE = League()
ALL = [TeamRef(d, p) for d in range(1, DIVISIONS + 1) for p in range(1, PLACES + 1)]


def own_score_pair(rng, policy):
    while True:
        own, opponent = rng.randint(0, 45), rng.randint(0, 45)
        if own == opponent:
            continue
        if policy == "win" and own < opponent or policy == "lose" and own > opponent:
            own, opponent = opponent, own
        return own, opponent


def conference(team: TeamRef):
    return "A" if team.division in AFC_DIVISIONS else "N"


class Season:
    """One whole season of a rig, with the facts the invariants need."""

    def __init__(self, tmp_path, seed, policy, own, concede=False):
        self.rng = random.Random(seed)
        self.rig = season_rig(tmp_path, own=own, gtp=1, rng=random.Random(seed + 1), policy=enter_policy, fast=True)
        self.game = self.rig.game
        self.policy, self.concede = policy, concede
        self.rounds = []                       # (gtp before, pairings before, pairings after, byes) of each play-off pog
        self.reached = None                    # the last week the player's team played

    def regular_season(self):
        game, season = self.game, self.game.season
        game.make_schedule()
        for week in range(1, 17):
            season.gtp = week
            assert season.set_week_opponent() is not None
            game.m414 = own_score_pair(self.rng, "random")
            game.pog()
            assert season.gtp == week + 1 or (week == 16 and season.gtp in (0, 17, 18))

    def playoffs(self):
        game, season, engine = self.game, self.game.season, self.game.season_engine
        while season.gtp != 0:
            week = season.gtp
            assert 17 <= week <= 20
            assert season.set_playoff_opponent(), "the player's team is in no record of the round"
            self.reached = week
            before = list(season.playoffs.pairings)
            byes = list(season.playoffs.byes)
            if week == 20:
                if self.concede:
                    game.m414 = (0, self.rng.randint(1, 20))
                    game.pog()
                else:
                    game.m414 = own_score_pair(self.rng, self.policy)
                    game.superbowl(game.m414)
                    assert season.gtp == 42
                    season.gtp = 0                  # pag
                break
            game.m414 = own_score_pair(self.rng, self.policy)
            mark = len(self.rig.store.events)
            game.pog()
            # the pairings pog itself wrote for the next round (finplay17 writes the later ones after a loss)
            written = next(v for kind, v in self.rig.store.events[mark:] if kind == "pairings")
            self.rounds.append((week, before, PlayoffState.pairings_from_values(written), byes, game.m414))


def play(tmp_path, seed, policy="random", own=None, concede=False):
    rng = random.Random(seed)
    own = own or (rng.randint(1, 8), rng.randint(1, 4))
    season = Season(tmp_path, seed, policy, own, concede)
    season.regular_season()
    return season


def full_season(tmp_path, seed, policy="random", own=None, concede=False):
    season = play(tmp_path, seed, policy, own, concede)
    if season.game.season.gtp in (17, 18):
        season.playoffs()
    return season


def check_regular_season(season):
    records = season.game.season.records
    assert all(sum(records.record(*t)) == 16 for t in ALL)                         # 16 games for every team
    assert sum(map(sum, records.wins)) == sum(map(sum, records.losses)) == 256
    assert season.game.rnd.fallbacks == 0
    assert season.game.replay_longest < 200                                         # the original's list has 501 places


def check_bracket(season):
    """After week 16: 12 teams, 6 per conference, the byes are the two best division winners; every later round is made of
    the winners of the round before in the fixed order (Q44)."""
    pog = season.game.season.playoffs
    assert season.rounds or season.game.season.gtp == 0
    for week, before, after, byes, scores in season.rounds:
        teams = [t for pairing in before for t in pairing]
        assert len(teams) == len(set(teams))
        if week == 17:                                                              # wild card round: 4 games, 4 byes
            assert len(before) == 4 and len(byes) == 4 and len(after) == 4
            assert [conference(v) for v, _ in before] == ["A", "A", "N", "N"]
            assert [conference(h) for _, h in before] == ["A", "A", "N", "N"]
            assert not set(teams) & set(byes)
            for index, (visitor, bye) in enumerate(after):
                assert visitor in before[index] and bye == byes[index]
        elif week == 18:                                                            # division round
            assert len(before) == 4 and len(after) == 2
            for index, (first, second) in enumerate(after):
                assert first in before[2 * index] and second in before[2 * index + 1]
                assert conference(first) == conference(second) == ("A" if index == 0 else "N")
        elif week == 19:                                                            # championship games
            assert len(before) == 2 and len(after) == 1
            visitor, home = after[0]
            assert visitor in before[0] and home in before[1] and conference(visitor) == "A" and conference(home) == "N"


@pytest.mark.parametrize("seed", range(12))
def test_a_season_of_a_random_team_ends_in_the_season_over_state_with_a_consistent_bracket(tmp_path, seed):
    season = full_season(tmp_path, seed)
    check_regular_season(season)
    check_bracket(season)
    assert season.game.season.gtp == 0
    assert season.game.rnd.fallbacks == 0


@pytest.mark.parametrize("seed", range(8))
def test_a_season_the_player_wins_every_play_off_game_reaches_the_super_bowl_when_in_the_play_offs(tmp_path, seed):
    season = full_season(tmp_path, 100 + seed, policy="win")
    check_regular_season(season)
    check_bracket(season)
    if season.rounds:
        assert season.reached in (17, 18, 19, 20)
    spoken = texts(season.rig)
    if season.reached == 20:                                       # a winning team's Super Bowl: the presentation, once
        assert sum(" have Won the super Bowl! " in t for t in spoken) == 1


@pytest.mark.parametrize("seed", range(8))
def test_a_season_the_player_loses_every_play_off_game_ends_after_its_first_play_off_game(tmp_path, seed):
    season = full_season(tmp_path, 200 + seed, policy="lose")
    check_regular_season(season)
    check_bracket(season)
    assert season.game.season.gtp == 0
    assert len(season.rounds) <= 1                                 # one play-off game at most, the rest at once
    assert all(scores[0] < scores[1] for _, _, _, _, scores in season.rounds)       # the player lost the game it played


def test_a_conceded_super_bowl_ends_the_season_with_the_opponents_win(tmp_path):
    reached = 0
    for seed in range(300, 340):
        season = full_season(tmp_path / str(seed), seed, policy="win", concede=True)
        if season.reached == 20:
            reached += 1
            spoken = texts(season.rig)
            assert " In the Super Bowl. " in spoken
            assert season.game.season.gtp == 0
            assert not any(" have Won the super Bowl! " in t for t in spoken)
    assert reached >= 1                                            # at least one of the 40 teams-and-seeds got there


def test_every_team_can_be_the_player_and_the_engine_never_raises_a_state_error(tmp_path):
    for index, team in enumerate(ALL):
        season = full_season(tmp_path / str(index), 400 + index, policy="random", own=(team.division, team.place))
        check_regular_season(season)
        assert season.game.season.gtp == 0


def test_the_record_of_the_player_team_is_in_the_play_offs_exactly_when_the_engine_says_so(tmp_path):
    """The three places of the end of week 16 (a wild card game, a bye, out) are told by gtp 17, 18 and 0."""
    seen = set()
    for seed in range(600, 680):
        season = play(tmp_path / str(seed), seed)
        seen.add(season.game.season.gtp)
    assert seen == {0, 17, 18}
