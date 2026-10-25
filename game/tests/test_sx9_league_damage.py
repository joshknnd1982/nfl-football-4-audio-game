"""league.sav under the damage matrix of playbook 7.10 at every stage of a franchise year (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 10.1,
invariant I10; PX SX.9, the stress tests of S8.3 with the Franchise). This is inspired by Jim Kitchen.

One franchise is played through its first season, the whole offseason (every stage, the staff deciding) and into the second season;
every league.sav it wrote is kept. For the first file of every stage (each of the 16 weeks of the season, the play-off week the season's
files name, each of the nine stages of the offseason; a stage that writes many files, the draft, is met at its first) the file is damaged in each way of the matrix while league.previous.sav holds the file written before it: the store
opens the copy and says so once (NXF-30, NXF-36 for a missing file); with both files damaged it sets the franchise aside and a classic season begins (NXF-31). The
program restarted from a damaged file at every stage of the offseason goes on to the next season with a whole league.
"""
import pytest

import filedamage
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import LeagueRecord
from nfl4.extras.franchise.store import FranchiseStore
from test_fr_resume import RecordingFiles

KINDS = [kind for kind in filedamage.BYTE_DAMAGES if kind != "newer_format"]
NXF30, NXF31 = X.text("NXF-30"), X.text("NXF-31")


def key_of(record):
    return (record.season, record.stage, record.stage_no, record.gtp)


@pytest.fixture(scope="module")
def stages(tmp_path_factory):
    """[(key, the file of that stage, the file written before it)] for the first file of every stage, in order."""
    files = RecordingFiles()
    folder = tmp_path_factory.mktemp("league")
    rig = franchise_rig(folder, WANT_FRANCHISE + COACH_AND_TEAM, files=files,
                        policy=enter_until(lambda: rig.fstore is not None and rig.fstore.league is not None
                                           and rig.fstore.league.season == 2 and rig.fstore.league.gtp >= 3))
    run_until(rig)
    out, seen, before = [], set(), None
    STAGES_FIRST.append(files.snapshots[0])
    for raw in files.snapshots:
        record = LeagueRecord.from_json(raw.decode("utf-8"))
        key = key_of(record)
        if key not in seen and before is not None:
            seen.add(key)
            out.append((key, raw, before))
        before = raw
    return out


STAGES_FIRST = []                                    # the first league.sav the new franchise wrote (no copy before it)


def damaged(tmp_path, raw, kind):
    path = tmp_path / ("d_" + kind)
    path.write_bytes(raw)
    filedamage.apply(kind, path)
    return path.read_bytes()


def open_store(main, previous):
    files = MemoryFiles()
    if main is not None:
        files.data["league.sav"] = main
    if previous is not None:
        files.data["league.previous.sav"] = previous
    store = FranchiseStore(files)
    store.strict = True
    store.open(True)
    return store, files


def test_the_franchise_wrote_a_file_at_every_stage_of_the_year(stages):
    keys = [key for key, _, _ in stages]
    offseason = {key[2] for key in keys if key[1] == "offseason"}
    assert offseason >= set(range(1, 10)), keys                # the nine stages of the offseason
    assert any(key[1] == "season" and key[3] >= 17 for key in keys)          # the play-offs
    assert {key[3] for key in keys if key[1] == "season" and key[0] == 1 and 1 <= key[3] <= 16} >= set(range(2, 17))


@pytest.mark.parametrize("kind", KINDS)
def test_every_damage_of_league_sav_at_every_stage_opens_the_copy_and_says_so_once(tmp_path, stages, kind):
    for key, raw, previous in stages:
        store, files = open_store(damaged(tmp_path, raw, kind), previous)
        assert store.exists, (key, kind)
        assert store.league.to_json() == LeagueRecord.from_json(previous.decode("utf-8")).to_json(), (key, kind)
        store.league.check()
        assert store.take_notices() == [NXF30], (key, kind)


def test_a_missing_league_sav_at_every_stage_opens_the_copy(stages):
    for key, raw, previous in stages:
        store, _ = open_store(None, previous)
        assert store.exists and store.take_notices() == [X.text("NXF-36")], key


@pytest.mark.parametrize("kind", ["empty", "cut_in_half", "random_bytes", "binary_zeros"])
def test_both_files_damaged_at_every_stage_set_the_franchise_aside(tmp_path, stages, kind):
    for key, raw, previous in stages:
        store, files = open_store(damaged(tmp_path, raw, kind), damaged(tmp_path, previous, kind))
        assert not store.exists and store.force_classic and store.take_notices() == [NXF31], (key, kind)


def test_a_restart_from_a_damaged_file_at_every_offseason_stage_reaches_the_next_season_whole(tmp_path, stages):
    done = 0
    for number, (key, raw, previous) in enumerate(stages):
        if key[1] != "offseason":
            continue
        files = MemoryFiles()
        files.data["league.sav"] = damaged(tmp_path, raw, "cut_in_half")
        files.data["league.previous.sav"] = previous
        start = LeagueRecord.from_json(previous.decode("utf-8")).season
        again = franchise_rig(tmp_path / ("again%d" % number), [], files=files, kind="franchise",
                              policy=enter_until(lambda: again.fstore is not None and again.fstore.league is not None
                                                 and again.fstore.league.season == start + 1 and again.fstore.league.gtp >= 2))
        run_until(again)
        league = again.fstore.league
        league.check()
        assert league.season == start + 1 and len(league.history) == start, key
        assert NXF30 in [t for t, _, _ in again.said], key
        done += 1
    assert done >= 9


@pytest.mark.parametrize("kind", ["empty", "cut_in_half", "random_bytes"])
def test_the_first_file_of_a_new_franchise_damaged_with_no_copy_sets_the_franchise_aside(tmp_path, stages, kind):
    first = STAGES_FIRST[0]
    store, files = open_store(damaged(tmp_path, first, kind), None)
    assert not store.exists and store.force_classic and store.take_notices() == [NXF31]
