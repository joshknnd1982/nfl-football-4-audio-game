"""league.sav FORMAT 8 (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 10.1, 17 SX.8m, D-073): the compensatory picks awarded, the picks owed, the tags and their
history, the market's moves and the draft's compensatory picks and undrafted signings round-trip through the REAL store, and a format-7 file (with a market
and with a draft in progress) loads by the migration and is saved again as format 8. With the two sources made to differ (B-X74): a migrated draft keeps its
own picks and a migrated market its own offers.
"""
import json
import random

import pytest
from drrig import SURNAMES, draft_league

from nfl4.extras.franchise import data as D, draft as DR, market as M, undrafted as UD
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import LeagueError, LeagueRecord
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.rnd import GameRandom

TEAM = 5


def through_store(league):
    """Save the league with the real store and open the file again."""
    files = MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True
    store.league = league
    assert store.save()
    again = FranchiseStore(files)
    again.strict = True
    again.open(True)
    return again.league, files


def as_format_7(league, drop=()):
    data = json.loads(league.to_json())
    for key in ("comp", "future_picks", "tags") + tuple(drop):
        data.pop(key, None)
    data["format"] = 7
    return data


def test_format_8_round_trips_every_new_value_through_the_real_store():
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_FREE_AGENCY)
    league.comp = [[league.season + 1, 3, 7, 80], [league.season + 1, 6, 2, 33]]
    league.future_picks = [[league.season + 1, 1, 9, TEAM]]
    league.tags["history"] = {"QB": [200, 210], "K": [30]}
    league.market = M.begin()
    league.market["moves"] = [[1, 2, 3, 50]]
    loaded, files = through_store(league)
    assert json.loads(files.data[D.LEAGUE_FILE].decode("utf-8"))["format"] == D.FORMAT == 15          # (12 since SZ.8: the values are format 8's)
    assert (loaded.comp, loaded.future_picks, loaded.tags, loaded.market) == (league.comp, league.future_picks, league.tags, league.market)
    assert loaded.to_json() == league.to_json()


def test_a_draft_with_compensatory_picks_and_undrafted_signings_round_trips():
    league = draft_league(seed=6, team=TEAM)
    league.comp = [[league.season, 4, 3, 60]]
    draft = DR.Draft.create(league, GameRandom(random.Random(6)), SURNAMES)
    while not draft.done:
        _, _, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    UD.run(draft)
    league.stage_no = D.STAGE_CUT
    loaded, _files = through_store(league)
    assert loaded.draft == league.draft and loaded.to_json() == league.to_json()


def test_a_format_7_file_loads_by_the_migration_and_is_saved_as_format_8():
    league = draft_league(seed=4, team=TEAM)
    data = as_format_7(league)
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.comp == [] and loaded.future_picks == [] and loaded.tags == {"history": {}, "open": None, "sheet": None}
    assert json.loads(loaded.to_json())["format"] == D.FORMAT       # (9 since SX.8n)


def test_a_format_7_market_in_progress_keeps_its_offers_and_gets_no_moves():
    league = draft_league(seed=4, team=TEAM, stage_no=D.STAGE_FREE_AGENCY)
    free = league.player_at(9, 3)
    from nfl4.extras.franchise import resign
    resign.let_go(league, free)
    league.market = M.begin()
    league.market["offers"] = [[free.id, 50]]
    data = as_format_7(league)
    del data["market"]["moves"]
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.market["moves"] == [] and loaded.market["offers"] == [[free.id, 50]]


def test_a_format_7_draft_in_progress_gets_no_compensatory_picks_and_no_undrafted_and_keeps_its_picks():
    league = draft_league(seed=6, team=TEAM)
    draft = DR.Draft.create(league, GameRandom(random.Random(6)), SURNAMES)
    for _ in range(40):
        _, _, team = draft.next_slot()
        draft.make_pick(team, draft.best_for(team))
    data = as_format_7(league)
    del data["draft"]["comp"]
    del data["draft"]["undrafted"]
    picks = [list(p) for p in data["draft"]["picks"]]
    loaded = LeagueRecord.from_json(json.dumps(data))
    assert loaded.draft["comp"] == [] and loaded.draft["undrafted"] == [] and loaded.draft["picks"] == picks
    resumed = DR.Draft(loaded)
    assert resumed.total == D.DRAFT_PICKS and len(resumed.picks) == 40


def test_a_format_8_file_without_its_new_values_is_damage():
    league = draft_league(seed=4, team=TEAM)
    for key in ("comp", "future_picks", "tags"):
        data = json.loads(league.to_json())
        del data[key]
        with pytest.raises(LeagueError):
            LeagueRecord.from_json(json.dumps(data))
