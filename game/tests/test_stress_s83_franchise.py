"""The Franchise work of SZ.8 under stress (S8.3 round 2; nfl4 only, rule 0.13; D-121 to D-124). This is inspired by Jim Kitchen.

* Free agents of the season: hundreds of random signings, releases and refusals, week after week, with the cap squeezed: every signing the rules
  allow keeps the league whole (league.check), the cap holds, the record reads back the same, and a refused one changes nothing.
* The real calendar with a saved game in the middle: the program is closed and started again from EVERY league.sav the franchise wrote around the
  player's bye week and from week 17 on, and each restart ends the season with one history entry of 17 games a team and one champion.
"""
import copy
import random

import pytest
from drrig import SURNAMES
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until
from test_fr_resume import RecordingFiles

from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import SEASON, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

TEAM = 5


def season_league(seed):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.stage, league.gtp = SEASON, 1
    return league


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_hundreds_of_random_signings_and_releases_keep_the_league_whole_and_the_cap(seed):
    league = season_league(seed)
    rng = random.Random(seed)
    made = refused = 0
    for step in range(400):
        week = 1 + step // 50                                                     # the signing's week (the record stays at week 1)
        S.ensure_pool(league, SURNAMES)
        pool = S.pool(league)
        player = rng.choice(pool)
        group = S.roster_group(league, league.team, player.pos)
        release = rng.choice(group + [None]) if group else None
        if rng.random() < 0.05:
            release = rng.choice([p for p in league.players.values() if p.status == "active" and p.team != league.team])   # another team's man
        if rng.random() < 0.05:
            player = rng.choice([p for p in league.players.values() if p.status == "active"])                               # not a free agent
        before = league.to_json()
        reason = S.problems(league, player, release, week)
        if reason is not None:
            refused += 1
            assert league.to_json() == before                                       # asking changes nothing
            continue
        S.sign(league, player, release, week)
        made += 1
        assert CT.cap_used(league, league.team) <= CT.cap_of(league)                 # SR.5: the cap is FR_CAP + FR_CAP_ROSTER for every league
        league.check()
        assert LeagueRecord.from_json(league.to_json()).to_json() == league.to_json()
    assert made >= 20 and refused >= 20
    names = [p.name for p in league.players.values() if p.status == "active"]
    assert len(names) == len(set(names))


def test_a_squeezed_cap_refuses_every_signing_that_would_break_it():
    league = season_league(4)
    S.ensure_pool(league, SURNAMES)
    for player in league.players.values():
        if player.team == league.team and player.status == "active":
            player.salary = max(player.salary, CT.cap_of(league) // 40)             # the payroll at the cap (SR.5: contracts.cap_of)
    for player in S.pool(league):
        group = S.roster_group(league, league.team, player.pos)
        for release in group + [None]:
            reason = S.problems(league, player, release, 1)
            if reason is None:
                assert S.cap_after(league, league.team, player, release) <= CT.cap_of(league)     # SR.5: contracts.cap_of


# ----- the real calendar, closed and started again from every save -----

def bengals_bye(league):
    calendar = league.calendar
    return next(w for w, row in enumerate(league.schedule, start=1) if row == [0, 0, 0]) if calendar else None


def test_a_restart_from_every_league_sav_around_the_bye_and_at_the_end_ends_the_18_week_season_whole(tmp_path):
    files = RecordingFiles()
    first = franchise_rig(tmp_path / "one", WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=lambda r: (28, 10), files=files,
                          policy=enter_until(lambda: first.fstore is not None and first.fstore.league is not None and first.fstore.league.season == 2))
    run_until(first)
    records = [LeagueRecord.from_json(raw.decode("utf-8")) for raw in files.snapshots]
    bye = next(bengals_bye(r) for r in records if r.calendar is not None and r.schedule)
    assert bye == 6                                                                 # the rig's player is the Bengals
    states = []
    for raw in files.snapshots:
        record = LeagueRecord.from_json(raw.decode("utf-8"))
        if record.stage == "season" and record.regular_weeks == 18 and (bye - 1 <= record.gtp <= bye + 1 or record.gtp >= 17):
            if raw not in states:
                states.append(raw)
    assert len(states) >= 6
    for number, raw in enumerate(states):
        again_files = MemoryFiles()
        again_files.data["league.sav"] = raw
        again = franchise_rig(tmp_path / ("again%d" % number), [], files=again_files, kind="franchise", real_calendar=True, scores=lambda r: (28, 10),
                              policy=enter_until(lambda: again.fstore is not None and again.fstore.league is not None and again.fstore.league.season == 2))
        run_until(again)
        league = again.fstore.league
        entry = league.history[0]
        assert len(league.history) == 1 and entry["finish"].count(D.FINISH_CHAMPION) == 1, number
        assert sum(entry["wins"]) + sum(entry["losses"]) + 2 * sum(entry.get("ties", [0] * 32)) == 272 * 2, number
        assert all(w + l + t == 17 for w, l, t in zip(entry["wins"], entry["losses"], entry.get("ties", [0] * 32))), number
        league.check()
