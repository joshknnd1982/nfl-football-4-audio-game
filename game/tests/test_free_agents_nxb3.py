"""NX-B3 (the owner's bug report of 2026-10-24, D-142, D-145): "it should have all current free agents" (nfl4 only, rule 0.13).

free_agents.txt (customizable, healed like rosters.txt) holds the real free agents researched 2026-10-24 (facts only: position, age, name; no rating).
In the first season of a franchise they are the free agents of F9, Franchise, free agents; made-up veterans only fill a group they leave short.
"""
import os
import random

import pytest
from drrig import SURNAMES
from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken

from nfl4.data import customlists as cl
from nfl4.data.customize import FREE_AGENTS, Customization
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

FREE_AGENTS_MENU = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 6 + [ENTER]     # F9, Franchise, free agents (the 7th item)


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def league(seed=3, team=5):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000")


def test_the_shipped_list_is_the_real_free_agents_of_2026_10_24_and_none_of_them_is_on_a_team():
    real = R.defaults()
    agents = [agent for _ident, agent in real.free_agents]
    assert len(agents) >= 100
    assert "VERSION = season 2026, as of 2026-10-27" in R.shipped_text(R.FREE_AGENTS)     # SR.2: refreshed; D-177: 2026-10-26; D-185: 2026-10-27
    on_teams = {p.name.casefold() for team in range(1, 33) for p in real.rosters[team - 1]}
    assert not [a.name for a in agents if a.name.casefold() in on_teams]
    from nfl4.extras import roster_model as RM
    assert all(R.name_problem(a.name) is None and a.pos in RM.MADDEN for a in agents)          # D-185: the 22 positions of a real roster
    assert any(a.name == "Tyreek Hill" and a.pos == "WR" and a.age == 32 for a in agents)
    groups = {RM.GROUP[a.pos] for a in agents}
    assert {"QB", "RB", "WR", "OL", "DL", "LB", "CB", "S", "K", "P", "LS"} <= groups


def test_in_the_first_season_the_real_free_agents_join_the_pool_once_and_made_up_ones_fill_only_short_groups():
    real = R.defaults()
    record = league()
    made = S.ensure_pool(record, SURNAMES, real)
    pool = S.pool(record)
    from nfl4.extras import roster_model as RM
    real_names = {real.spoken(a.name) for _i, a in real.free_agents if a.pos in S.REAL_GROUP or a.pos in RM.GROUP}     # D-185: the 22 positions
    assert real_names <= {p.name for p in pool}
    for position in D.ROSTER_ORDER:                                                   # SR.5: the 11 families (no RET; the line and the snapper)
        group = S.pool_of(record, position)
        reals = [p for p in group if p.name in real_names]
        assert len(group) == max(T.FR_FA_SEASON_PER_GROUP, len(reals)), position       # made-up ones only up to the group's minimum
    assert S.add_real_free_agents(record, real) == 0                                  # once
    assert S.ensure_pool(record, SURNAMES, real) == 0
    hill = next(p for p in pool if p.name == "Tyreek Hill")
    base, span = T.FR_FA_SEASON_RATING
    assert hill.pos == "WR" and hill.age == 32 and base <= hill.rating < base + span and hill.status == "free" and hill.team == 0
    assert made == len(pool)
    assert [p for p in pool if p.pos == "OL"] and [p for p in pool if p.pos == "LS"]  # SR.5: the line and the snapper are families of the Franchise now
    decker = next(p for p in pool if p.name == "Taylor Decker")                         # D-185: a free agent keeps his real field position
    assert (decker.pos, decker.position) == ("OL", "LT")
    assert {p.position for p in pool if p.pos == "OL"} >= {"LT", "LG", "C", "RG", "RT"}
    assert {p.position for p in pool if p.pos == "DL"} >= {"LEDG", "REDG", "DT"} and {p.position for p in pool if p.pos == "S"} == {"FS", "SS"}


def test_a_later_season_and_a_league_without_real_names_get_no_real_free_agents():
    real = R.defaults()
    record = league()
    record.season = 2
    assert S.add_real_free_agents(record, real) == 0
    other = league()
    assert S.ensure_pool(other, SURNAMES) == 3 * len(D.ROSTER_ORDER)                  # as before: three made-up veterans a family (SR.5: 11 families)


def test_a_tight_end_is_a_receiver_and_a_fullback_a_running_back():
    assert S.REAL_GROUP["TE"] == "WR" and S.REAL_GROUP["FB"] == "RB"
    assert S.REAL_GROUP["OL"] == "OL" and S.REAL_GROUP["LS"] == "LS"                  # SR.5: the line and the snapper join the Franchise's families


def custom(tmp_path):
    return Customization(str(tmp_path), extras=True)


def test_the_player_gets_the_file_and_his_lines_lay_over_the_list(tmp_path):
    c = custom(tmp_path)
    path = tmp_path / "free_agents.txt"
    assert path.is_file() and c.snapshot.statuses[FREE_AGENTS] in (cl.CREATED, cl.OK)
    text = path.read_text(encoding="utf-8")
    first = next(line for line in text.splitlines() if line.startswith("F001 = "))
    text = text.replace(first, "F001 = off") + "F900 = QB 30 My Own Quarterback\nF901 = XX 1 Nobody\n"
    path.write_text(text, encoding="utf-8")
    c.reload()
    names = [a.name for _i, a in c.snapshot.real_names.free_agents]
    assert "My Own Quarterback" in names and first.split(" ", 4)[-1] not in names
    assert c.snapshot.problem_count(FREE_AGENTS) == 1


@pytest.mark.parametrize("damage", [b"", b"\x00\x01\x02" * 50, b"hello, this is not a list\n", b"# NFL Football 4 rosters, format 1.\nT01P01 = QB 9 Joe Burrow\n"])
def test_a_damaged_file_is_copied_aside_and_made_again(tmp_path, damage):
    c = custom(tmp_path)
    (tmp_path / "free_agents.txt").write_bytes(damage)
    notices = c.reload()
    assert c.snapshot.statuses[FREE_AGENTS] == cl.RESET
    assert any("free_agents.txt" in n and "damaged" in n for n in notices)
    assert any(name.startswith("free_agents.txt.damaged") for name in os.listdir(tmp_path))
    assert len(c.snapshot.real_names.free_agents) >= 100


def test_a_new_franchise_lists_the_real_free_agents_in_f9(tmp_path, monkeypatch):
    """The rig reads no customize folder and its start-up keys type the coach's name, so the game has no real names: the pool is made with the shipped ones
    (the flow hands the game's real names to the pool, noted here)."""
    real = R.defaults()
    handed = []
    plain = S.ensure_pool

    def ensure(league_, surnames, given=None):
        handed.append(given)
        return plain(league_, surnames, given if given is not None else real)
    monkeypatch.setattr(S, "ensure_pool", ensure)
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + FREE_AGENTS_MENU + [ENTER, ENTER] + [ESC] * 7, policy=quit_policy)   # sign a free agent, quarterbacks
    run_until(rig)
    league_ = rig.fstore.league
    assert handed and handed[0] is getattr(rig.game, "real_names", None)
    reals = {real.spoken(a.name) for _i, a in real.free_agents}
    qbs = S.pool_of(league_, "QB")
    assert qbs and qbs[0].name in reals                                               # the quarterbacks' list: real free agents
    assert any(qbs[0].name in t for t in spoken(rig))
