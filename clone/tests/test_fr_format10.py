"""league.sav FORMAT 10 (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 10.1, 17 SX.8o, D-076): the awards, the hall of fame and the season's games and carries
round-trip through the REAL store, and a format-9 file loads by the migration (no award, nobody in the hall, nothing counted this season) at a week of the
season, at stage 1 and in a draft, and is saved again as format 10. With the two sources made to differ (B-X74): a migrated file keeps its own players and
gets the empty honors and counts, never another league's.
"""
import json

import pytest
from drrig import draft_league
from test_fr_format9 import TEAM, through_store

from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import honors as H
from nfl4.extras.franchise import workload as W
from nfl4.extras.franchise.league import OFFSEASON, SEASON, LeagueError, LeagueRecord


def as_format_9(league):
    data = json.loads(league.to_json())
    data.pop("honors")
    data.pop("usage")
    data["format"] = 9
    return data


def honored(league):
    """The league with awards of the season before, a member of the hall and counts of this season (the two sources of B-X74 made to differ)."""
    p = league.player_at(TEAM, 0)
    gone = league.player_at(9, 0)
    gone.status, gone.left, gone.place = "retired", league.season - 1, -1
    league.rosters[8][0] = 0
    league.honors["awards"] = [[league.season - 1, "mvp", p.id, p.name, p.pos, TEAM], [league.season - 1, "coy", 0, "Smith", "", 3]]
    league.honors["hall"] = [[gone.id, league.season - 1]]
    league.usage = {"season": league.season, "games": {str(p.id): 4}, "carries": {str(p.id): 35}}
    return league


def week_league():
    league = draft_league(seed=4, team=TEAM, stage_no=0)
    league.stage, league.gtp, league.records = SEASON, 1, [0] * 64
    league.sums = [league.strength_sum(t) for t in range(1, 33)]
    league.season = 3
    return league


def test_format_10_round_trips_the_honors_and_the_counts_through_the_real_store():
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_DRAFT)
    league.season = 3
    honored(league)
    loaded, files = through_store(league)
    assert json.loads(files.data[D.LEAGUE_FILE].decode("utf-8"))["format"] == D.FORMAT == 15
    assert loaded.honors == league.honors and loaded.usage == league.usage and loaded.to_json() == league.to_json()


@pytest.mark.parametrize("where", ["week", "review", "draft"])
def test_a_format_9_file_loads_with_no_honors_and_no_counts_and_is_saved_as_format_10(where):
    if where == "week":
        league = week_league()
    else:
        league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_REVIEW if where == "review" else D.STAGE_DRAFT)
        league.season = 3
    data = as_format_9(league)
    honored(league)
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.honors == H.empty() != league.honors and loaded.usage == {"season": 0, "games": {}, "carries": {}} != league.usage
    assert json.loads(loaded.to_json())["format"] == D.FORMAT
    assert W.carries_of(loaded, league.player_at(TEAM, 0).id) == 0 and W.games_of(loaded, league.player_at(TEAM, 0).id) == 0


def test_a_format_10_file_without_its_honors_or_counts_is_damage():
    for key, bad in (("honors", None), ("usage", None), ("honors", []), ("usage", {"season": 1})):
        data = json.loads(week_league().to_json())
        if bad is None:
            del data[key]
        else:
            data[key] = bad
        with pytest.raises(LeagueError):
            LeagueRecord.from_json(json.dumps(data))
