"""league.sav FORMAT 9 (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 10.1, 17 SX.8n, D-074): the people (the morale, the camp's holdouts with the player's own still
to ask, the trade demands, the goal and its verdict) round-trip through the REAL store, and a format-8 file loads by the migration (nobody has a morale, nobody
held out) at a week of the season, at stage 3 and in a draft, and is saved again as format 9. With the two sources made to differ (B-X74): a migrated file keeps
its own players' values and gets the empty people, never another league's.
"""
import json

import pytest
from drrig import draft_league

from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import people as P
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import SEASON, LeagueError, LeagueRecord
from nfl4.extras.franchise.store import FranchiseStore

TEAM = 5


def through_store(league):
    files = MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True
    store.league = league
    assert store.save()
    again = FranchiseStore(files)
    again.strict = True
    again.open(True)
    return again.league, files


def as_format_8(league):
    data = json.loads(league.to_json())
    data.pop("people")
    data["format"] = 8
    return data


def camp_with_holdout():
    def mutate(league):
        player = next(p for p in league.active_of(TEAM) if p is not None and P.personality(p.id) == "money")
        player.rating, player.age, player.seasons, player.years = 86, 24, 4, 2
        player.salary = CT.market_salary(player.pos, 86) // 2
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_DEVELOPMENT, mutate=mutate)
    P.begin_holdouts(league, False)
    return league


def test_format_9_round_trips_every_people_value_through_the_real_store():
    league = camp_with_holdout()
    assert league.people["pending"]
    ids = [league.rosters[0][i] for i in range(3)]
    for pid, value in zip(ids, (6, -2, 3)):
        P.set_morale(league, pid, value)
    league.people["holdouts"].append([ids[0], 1, league.season, P.WAITED])
    loaded, files = through_store(league)
    assert json.loads(files.data[D.LEAGUE_FILE].decode("utf-8"))["format"] == D.FORMAT == 17
    assert loaded.people == league.people and loaded.to_json() == league.to_json()


def test_the_seasons_values_round_trip():
    league = draft_league(seed=4, team=TEAM, stage_no=0)
    league.stage, league.gtp, league.records = SEASON, 1, [0] * 64     # week 1 before its schedule is made (a valid record, design 20 entry 1.1)
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    star = league.player_at(TEAM, 33)
    league.people.update(demands=[[star.id, TEAM, 2, P.OPEN], [league.player_at(9, 0).id, 9, 1, P.TRADED]], goal=[1, 3, "close", 14, 0],
                         verdict=[1, 2, 1, 1], holdouts=[[star.id, TEAM, 1, P.ON_BLOCK]], begun=1)
    loaded, _files = through_store(league)
    assert loaded.people == league.people


@pytest.mark.parametrize("stage_no", [0, D.STAGE_DEVELOPMENT, D.STAGE_DRAFT])
def test_a_format_8_file_loads_with_nobody_moved_and_is_saved_as_format_9(stage_no):
    league = draft_league(seed=4, team=TEAM, stage_no=stage_no)
    if stage_no == 0:
        league.stage, league.gtp, league.records = SEASON, 1, [0] * 64
    P.set_morale(league, league.rosters[0][0], 4)              # the two sources differ: this league's people are NOT what a format-8 file gets
    data = as_format_8(league)
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.people == P.empty() != league.people
    assert json.loads(loaded.to_json())["format"] == D.FORMAT
    before = set(league.players)                                                     # D-136: the squads formed at the load are new players
    assert [p.to_list() for p in loaded.players.values() if p.id in before and p.status != "practice"] == [
        p.to_list() for p in league.players.values() if loaded.players[p.id].status != "practice"]


def test_a_format_8_file_at_stage_3_starts_its_camp_holdouts_when_the_stage_runs():
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_DEVELOPMENT)
    loaded = LeagueRecord.from_json(json.dumps(as_format_8(league)))
    assert loaded.people["begun"] == 0 != loaded.season                     # people_flow.holdouts begins the camp's holdouts at its next run


def test_a_format_9_file_without_its_people_is_damage():
    data = json.loads(draft_league(seed=4, team=TEAM).to_json())
    del data["people"]
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))
    data = json.loads(draft_league(seed=4, team=TEAM).to_json())
    data["people"] = []
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))
