"""The practice squads of the Franchise (nfl4 only, rule 0.13; D-136, the owner 2026-10-23: "The practice squad is not added in franchise mode. You
must add this into the game, too."). This is inspired by Jim Kitchen.

Rules (practice.py): the squads formed from the players let go (16 at most, 6 veterans at most, the cap, no draw), dissolved when the season ends,
kept when the offseason drops the players history does not need; a squad player elevated in place of a made-up stand-in, three times a regular
season; the player's own moves; league.sav format 14 and the migration of an older league; the F9 menu on the program rig.
"""
import json
import random

import pytest
from drrig import SURNAMES
from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, enter_until, franchise_rig, quit_policy, run_until, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import practice as P
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.league import SEASON, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5


def season_league(seed=3):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.stage, league.gtp = SEASON, 1
    return league


def let_go(league, count=200, seed=1):
    """Make `count` players of the league free agents of this season, as an offseason's cuts and market leave them (no team, no contract)."""
    rng = random.Random(seed)
    made = 0
    for team in range(1, D.TEAMS + 1):
        for index in range(D.PLACE_COUNT):
            if made >= count:
                return made
            if rng.random() < 0.2:
                player = league.player_at(team, index)
                if player is None:
                    continue
                league.rosters[team - 1][index] = 0
                player.status, player.left, player.team, player.place, player.salary, player.years = "released", league.season, team, -1, 0, 0
                made += 1
    return made


def refill(league):
    """The empty places filled again (the cut's fill), so the season's record is whole."""
    aging.fill_places(league, GameRandom(random.Random(9)), SURNAMES)


def formed(seed=3):
    league = season_league(seed)
    let_go(league)
    refill(league)
    P.form(league)
    return league


# ----- forming the squads -----

def test_every_squad_keeps_the_limits_and_takes_only_players_let_go():
    league = formed()
    for team in range(1, D.TEAMS + 1):
        squad = P.squad(league, team)
        assert len(squad) <= P.SIZE and sum(P.veteran(p) for p in squad) <= P.VETERANS
        assert all(p.place == -1 and p.salary in (P.PRACTICE_SALARY, P.PRACTICE_SALARY_VETERAN) for p in squad)
        assert CT.cap_used(league, team) <= T.FR_CAP
    assert sum(len(P.squad(league, t)) for t in range(1, 33)) > 100
    league.check()
    again = LeagueRecord.from_json(league.to_json())
    assert again.to_json() == league.to_json()


def test_forming_draws_nothing_and_gives_the_same_squads_every_time():
    a, b = formed(4), formed(4)
    assert a.to_json() == b.to_json()


def test_a_team_takes_its_own_cut_players_first():
    league = season_league()
    let_go(league)
    own = [p for p in league.players.values() if p.status == "released" and p.team == 9]
    refill(league)
    P.form(league)
    squad_ids = {p.id for p in P.squad(league, 9)}
    takeable = [p for p in own if p.age <= T.FR_PRACTICE_MAX_AGE]
    assert takeable and squad_ids & {p.id for p in takeable}


def test_the_squads_end_with_the_season_and_survive_the_drop_of_the_offseason():
    league = formed()
    some = P.squad(league, 9)[0]
    aging.drop_the_unkept(league)
    assert some.id in league.players and league.players[some.id].status == P.STATUS
    assert P.dissolve(league) > 0
    assert not any(p.status == P.STATUS for p in league.players.values()) and league.practice == P.empty()


# ----- the elevations -----

def hurt_whole_group(league, team, position, week=2):
    for player in league.group_of(team, position):
        if player is not None:
            I.injure(league, player.id, "IJB", 5, 0, week - 1)


def test_a_squad_player_stands_in_when_his_group_has_nobody_fit_and_counts_an_elevation():
    league = formed()
    team = 9
    qb = next((p for p in P.squad(league, team) if p.pos == "QB"), None)
    if qb is None:                                                      # give the squad a quarterback (a free agent of the season)
        S.ensure_pool(league, SURNAMES)
        qb = next(p for p in S.pool(league) if p.pos == "QB")
        P._join(league, team, qb)
    hurt_whole_group(league, team, "QB")
    I.settle(league, 2, GameRandom(random.Random(5)), SURNAMES)
    row = I.stand_in(league, team, "QB")
    assert row is not None and row[2] == qb.name and row[3] == qb.rating
    assert P.elevations(league, qb) == 1
    league.check()


def test_after_three_elevations_the_next_squad_player_or_a_made_up_one_stands_in():
    league = formed()
    team = 9
    S.ensure_pool(league, SURNAMES)
    qbs = [p for p in S.pool(league) if p.pos == "QB"][:2]
    for p in qbs:
        P._join(league, team, p)
    hurt_whole_group(league, team, "QB", week=2)
    rnd = GameRandom(random.Random(5))
    I.settle(league, 2, rnd, SURNAMES)
    first = I.stand_in(league, team, "QB")[2]
    for week in (3, 4):
        P.count_week(league, week)
    row = I.stand_in(league, team, "QB")
    assert row[2] != first or P.elevations(league, next(p for p in qbs if p.name == first)) < P.ELEVATIONS


# ----- the player's own moves -----

def test_promoting_a_squad_player_puts_him_on_the_roster_for_the_minimum():
    league = formed()
    squad = P.squad(league, TEAM)
    assert squad
    player = squad[0]
    release = None if S.open_place(league, TEAM, player.pos) else S.releasable(league, TEAM, player.pos, 1)[0]
    assert P.promote_problem(league, player, release, 1) is None
    P.promote(league, player, release)
    assert player.status == "active" and player.team == TEAM and player.place >= 0 and player.salary == CT.min_salary(player.seasons)
    league.check()


def test_adding_and_releasing_squad_players_keep_the_limits():
    league = formed()
    S.ensure_pool(league, SURNAMES)
    while len(P.squad(league, TEAM)) < P.SIZE:
        candidate = next((p for p in S.pool(league) if P.sign_problem(league, p) is None), None)
        if candidate is None:
            break
        P.sign_to_squad(league, candidate)
    extra = next((p for p in S.pool(league)), None)
    if extra is not None and len(P.squad(league, TEAM)) >= P.SIZE:
        assert P.sign_problem(league, extra) == "the practice squad is full"
    out = P.squad(league, TEAM)[-1]
    P.release_from_squad(league, out)
    assert out.status == "free" and out in S.pool(league)
    league.check()


# ----- the file -----

def test_an_older_league_in_its_season_gets_its_squads_when_it_is_opened():
    league = season_league()
    let_go(league)
    refill(league)
    data = json.loads(league.to_json())
    data["format"] = 13
    del data["practice"]
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert any(p.status == P.STATUS for p in loaded.players.values())
    assert json.loads(loaded.to_json())["format"] == D.FORMAT == 17


@pytest.mark.parametrize("bad", [None, [], {"season": 1}, {"season": -1, "elevations": {}}, {"season": 1, "elevations": {"x": 1}},
                                 {"season": 1, "elevations": {"1": -2}}])
def test_a_damaged_practice_record_is_damage(bad):
    from nfl4.extras.franchise.league import LeagueError
    data = json.loads(formed().to_json())
    data["practice"] = bad
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


# ----- F9 on the program rig -----

PRACTICE = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 9 + [ENTER]          # F9, Franchise, practice squad (the 10th item)


def test_f9_practice_squad_in_a_new_franchise_opens_and_hears_the_squad(tmp_path):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + PRACTICE + [ENTER, ESC, ESC, ESC, ESC], practice=True, policy=quit_policy)
    run_until(rig)
    text = spoken(rig)
    assert any(X.text("NXJ-P02", n=16).strip() in t for t in text), text[-12:]                       # a new franchise has full squads from week 1
    league = rig.fstore.league
    assert all(len(P.squad(league, t)) == P.SIZE for t in range(1, 33))
    assert all(not P.veteran(p) for t in range(1, 33) for p in P.squad(league, t))
    league.check()


def test_top_up_draws_nothing_and_a_reloaded_league_has_the_same_players():
    a, b = season_league(6), season_league(6)
    P.top_up(a, SURNAMES)
    P.top_up(b, SURNAMES)
    assert a.to_json() == b.to_json() and P.top_up(a, SURNAMES) == 0
