"""SR.7 (phase PR, Q-078, D-167): the real players' real ages and years in the league (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

rosters.txt gives a man's age on the file's date and his NFL seasons before this one ("T17P01 = QB 18 Caleb Williams; age 24; seasons 2"), from
nflverse's roster table (birth date, rookie year), written by game\\tools\\update_rosters.py. A new franchise gives every real man his real age (within the
game's 21 to 40) and his seasons; a man the file gives no age keeps the hashed age as before; a practice squad keeps at most six veterans (the accrued
seasons the real rule counts are not in the data, so the six most experienced men are its veterans). The 20-season soaks with real ages (work\\sr7) held
every band of the drawn ages.
"""
import random

import pytest

from drrig import SURNAMES
from nfl4.data import customize
from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import practice as PR
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

BEARS, STEELERS = 17, 4


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def league_of(seed=3, team=BEARS):
    return new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000", real=R.defaults())


def man(league, name):
    found = [p for p in league.players.values() if p.name == name]
    assert len(found) == 1, name
    return found[0]


# ----- the file -----

def test_a_line_with_an_age_and_seasons_reads_and_writes_back_the_same():
    text = RF.HEADER + "VERSION = season 2026, as of 2026-10-25\nT17P01 = QB 18 Caleb Williams; age 24; seasons 2\nT17P02 = PS QB 16 Miller Moss; age 24; seasons 0\nT17P03 = QB 6 No Age Man\n"
    version, teams, problems = RF.parse(text)
    assert problems == []
    men = teams[BEARS].men
    assert (men[0].name, men[0].age, men[0].seasons) == ("Caleb Williams", 24, 2)
    assert (men[1].status, men[1].name, men[1].age, men[1].seasons) == ("PS", "Miller Moss", 24, 0)
    assert (men[2].name, men[2].age, men[2].seasons) == ("No Age Man", None, None)
    rendered = RF.render(version, teams)
    assert "T17P01 = QB 18 Caleb Williams; age 24; seasons 2\n" in rendered and "T17P02 = QB 6 No Age Man\n" in rendered   # actives first
    assert "T17P03 = PS QB 16 Miller Moss; age 24; seasons 0\n" in rendered
    assert sorted(RF.parse(rendered)[1][BEARS].men, key=lambda m: m.name) == sorted(men, key=lambda m: m.name)


def test_a_bad_age_part_is_a_problem_and_an_impossible_age_fails_the_check():
    _, _, problems = RF.parse("VERSION = x\nT17P01 = QB 18 Caleb Williams; aged 24\n")
    assert problems
    _, teams, problems = RF.parse("VERSION = x\nT17P01 = QB 18 Caleb Williams; age 12; seasons 2\n")
    assert problems == []
    fail, _warn = RF.check(teams)
    assert any("age" in f for f in fail)
    _, teams, _ = RF.parse("VERSION = x\nT17P01 = QB 18 Caleb Williams; age 24; seasons 9\n")
    assert any("seasons" in f for f in RF.check(teams)[0])


def test_the_shipped_file_gives_almost_every_man_an_age_and_passes_its_checks():
    _, teams, problems = RF.parse(R.shipped_text(R.ROSTERS))
    assert problems == []
    fail, _ = RF.check(teams)
    assert fail == []
    men = [m for team in teams.values() for m in team.men]
    with_age = [m for m in men if m.age is not None]
    assert len(with_age) >= 0.99 * len(men)
    bears = {m.name: m for m in teams[BEARS].men}
    assert (bears["Caleb Williams"].age, bears["Caleb Williams"].seasons) == (24, 2)
    assert (bears["Colston Loveland"].age, bears["Colston Loveland"].seasons) == (22, 1)


def test_the_game_reads_the_ages_and_the_spoken_names_have_no_age_part():
    real = R.defaults()
    caleb = [p for p in real.rosters[BEARS - 1] if p.name == "Caleb Williams"]
    assert caleb and (caleb[0].age, caleb[0].seasons) == (24, 2)
    assert all(";" not in p.name for roster in real.rosters for p in roster)


# ----- a new franchise -----

def test_a_new_franchise_gives_the_real_men_their_real_ages_and_seasons():
    league = league_of()
    league.check()
    caleb, bagent, moss = man(league, "Caleb Williams"), man(league, "Tyson Bagent"), man(league, "Miller Moss")
    assert (caleb.age, caleb.seasons) == (24, 2) and (bagent.age, bagent.seasons) == (26, 3)
    assert (moss.age, moss.seasons, moss.status) == (24, 0, "practice")
    rodgers = man(league, "Aaron Rodgers")
    assert (rodgers.age, rodgers.seasons) == (D.AGE_MAX, D.AGE_MAX - 21)          # 42 and 21 seasons in reality: the game's oldest age, seasons up to it


def test_a_new_franchise_is_the_same_with_the_player_on_another_team_and_keeps_its_draws():
    a, b = league_of(seed=5, team=BEARS), league_of(seed=5, team=STEELERS)
    assert man(a, "Caleb Williams").age == man(b, "Caleb Williams").age == 24


def test_every_practice_squad_starts_with_at_most_six_veterans():
    league = league_of()
    for team in range(1, D.TEAMS + 1):
        squad = PR.squad(league, team)
        assert sum(1 for p in squad if PR.veteran(p)) <= PR.VETERANS, team


def test_a_man_without_an_age_in_the_file_keeps_the_hashed_age():
    league = league_of()
    _, teams, _ = RF.parse(R.shipped_text(R.ROSTERS))
    missing = [(t, m) for t, team in teams.items() for m in team.men if m.age is None and m.status == ""]
    assert missing
    t, m = missing[0]
    p = man(league, R.defaults().spoken(m.name))
    if p.place < 0:
        assert (p.age, p.seasons) == (RR.bench_age(league, t, p.name)[0], max(0, RR.bench_age(league, t, p.name)[0] - 22))
    assert D.AGE_MIN <= p.age <= D.AGE_MAX


def test_the_mean_age_of_a_new_league_is_the_real_leagues():
    league = league_of()
    ages = [p.age for p in league.players.values() if p.status == "active"]
    assert 25.5 <= sum(ages) / len(ages) <= 26.6                                   # the real 53s: 26.3 (work\sr7\real_ages.py)


# ----- the player's old copy of rosters.txt -----

def test_the_copy_0_16_2_shipped_is_refreshed_once(tmp_path):
    import hashlib
    import subprocess
    from pathlib import Path
    game = Path(customize.__file__).resolve().parents[3]                          # game\src\nfl4\data -> game
    try:
        old = subprocess.run(["git", "show", "4e652d0:game/assets/data/rosters.txt"], capture_output=True, cwd=str(game), check=False).stdout
    except OSError:
        old = b""
    if not old:
        pytest.skip("git history not available")
    digest = hashlib.sha256(old.decode("utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest()
    assert digest in customize.OLD_SHIPPED_ROSTERS
    (tmp_path / "rosters.txt").write_bytes(old)
    assert customize.refresh_old_rosters(str(tmp_path)) == "refreshed"
    assert (tmp_path / "rosters.txt").read_text(encoding="utf-8") == R.shipped_text(R.ROSTERS)


# ----- the maintainer's script -----

def test_the_script_dates_each_man_from_nflverse_then_sleeper_and_leaves_the_undated_without_an_age():
    import importlib.util
    import sys
    from pathlib import Path
    tool = Path(__file__).resolve().parent.parent / "tools" / "update_rosters.py"
    U = sys.modules.get("update_rosters")
    if U is None:
        spec = importlib.util.spec_from_file_location("update_rosters", tool)
        U = importlib.util.module_from_spec(spec)
        sys.modules["update_rosters"] = U                  # a dataclass looks up its module while the class is made (B-T109)
        spec.loader.exec_module(U)
    team = RF.Team([RF.Man("QB", "18", "Caleb Williams"), RF.Man("QB", "6", "Tyson Bagent"), RF.Man("QB", "4", "Nobody Known"),
                    RF.Man("WR", "11", "Old Timer")])
    nv = {BEARS: [{"full_name": "Caleb Williams", "birth_date": "2001-11-18", "rookie_year": "2024"},
                  {"full_name": "Old Timer", "birth_date": "1900-01-01", "rookie_year": "1920"}]}
    sl = {BEARS: [{"full_name": "Tyson Bagent", "birth_date": "2000-06-08", "years_exp": 3}]}
    assert U.add_ages({BEARS: team}, nv, sl, "2026-10-25") == 2
    ages = {m.name: (m.age, m.seasons) for m in team.men}
    assert ages == {"Caleb Williams": (24, 2), "Tyson Bagent": (26, 3), "Nobody Known": (None, None), "Old Timer": (None, None)}
