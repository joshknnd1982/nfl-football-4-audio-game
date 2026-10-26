"""The 53-man roster of NX-B2b (D-149) as it lives on in SR.5 (D-164): the men of a team's roster without a place in the game day's view (nfl4 only,
rule 0.13). The bench of D-149 was a status of its own ("reserve", extras/franchise/reserves.py); SR.5 retired both: a team is its depth chart, the 34
places a view made from it, and a man without a place is simply an active man (LeagueRecord.bench lists them). The rules of D-149 that still hold are
tested here on a new franchise of the real rosters: such a man is paid and settled like any other, he plays for a hurt starter of his position, the player
may choose him, put him first, swap his quarterbacks and trade him; and a name pool all in use costs one draw.
"""
import random

import pytest

from drrig import SURNAMES
from nfl4.extras import nfl_surnames
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import depth as FD
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import resign
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def real_league(seed=3, team=1):
    real = R.defaults()
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=real)
    return league, real


def test_a_new_franchise_carries_every_real_53_and_the_men_without_a_place_are_active():
    league, _ = real_league()
    for team in range(1, D.TEAMS + 1):
        bench = league.bench(team)
        assert all(p.status == "active" and p.place < 0 and p.team == team for p in bench)
        placed = sum(1 for pid in league.rosters[team - 1] if pid)
        assert placed + len(bench) == RR.roster_count(league, team)
    assert not any(p.status == "reserve" for p in league.players.values())          # SR.5: no status of its own


def test_a_man_without_a_place_is_paid_and_his_contract_runs_out_and_is_settled_in_stage_7():
    league, _ = real_league()
    man = league.bench(4)[0]
    assert CT.running(man) and man in CT.team_players(league, 4)
    man.years = 0
    assert man in resign.expiring(league, 4)
    resign.let_go(league, man)
    assert man.status == "free" and man.place == -1 and man not in league.bench(4) and man.id not in league.chart[3][man.position]
    assert resign.room_after(0, 0, 0, *resign.league_terms(league)) == CT.cap_of(league) - T.FR_RESIGN_RESERVE - T.FR_MIN_SALARY * (D.ROSTER_MAX - 1)
    assert resign.room_after(0, 0, 0) == T.FR_CAP - T.FR_RESIGN_RESERVE - T.FR_MIN_SALARY * 33        # the function's older defaults, unchanged


def test_a_hurt_quarterback_is_played_by_the_backup_never_above_the_starter():
    league, _ = real_league()
    team = next(t for t in range(2, 33) if league.bench(t, "QB"))
    starter = league.group_of(team, "QB")[0]
    backup = league.bench(team, "QB")[0]
    I.injure(league, starter.id, I.KIND_IDS[0], 4, 0, 1)
    table = I.lineup(league, team, 2, staff=True)
    index = D.PLACES_OF["QB"][0]
    assert table[index][0] == backup.id and table[index][2] == min(backup.rating, starter.rating)
    assert I.bench_covers(league, team, "QB", 2)


def test_the_player_may_choose_a_man_without_a_place_for_his_hurt_mans_place():
    league, _ = real_league()
    team = league.team
    hurt = league.group_of(team, "CB")[0]
    I.injure(league, hurt.id, I.KIND_IDS[0], 4, 0, 1)
    bench = league.bench(team, "CB")
    assert bench
    choices = I.cover_choices(league, hurt.id, 2)
    assert set(p.id for p in bench) <= {p.id for p in choices}
    I.choose(league, hurt.id, bench[-1].id)
    table = I.lineup(league, team, 2, staff=False)
    assert table[hurt.place][0] == bench[-1].id


def test_a_man_put_first_takes_the_first_place_and_the_last_man_of_the_places_has_none():
    league, _ = real_league()
    team = league.team
    man = league.bench(team, "S")[-1]
    first = league.players[league.chart[team - 1][man.position][0]]                  # SR.5: the first of his own position's chart
    FD.put_first(league, "S", man.id)
    assert man.place in D.PLACES_OF["S"] and man.status == "active" and league.chart[team - 1][man.position][0] == man.id
    assert first.place < 0 and first in league.bench(team, "S")
    league.check()


def test_a_backup_quarterback_and_the_starter_swap_with_no_release():
    league, _ = real_league()
    team = league.team
    starter, backup = league.group_of(team, "QB")[0], league.bench(team, "QB")[0]
    before = CT.payroll(league, team)
    RR.choose_starter(league, "QB", backup.id)                                       # the Quarterbacks item (D-140, Q-069)
    assert league.group_of(team, "QB")[0].id == backup.id and starter.place < 0 and starter.status == "active"
    assert CT.payroll(league, team) == before
    league.check()


def test_a_name_pool_all_in_use_costs_one_draw_not_ten_thousand():
    from nfl4.extras.franchise.league import draw_name
    rnd = GameRandom(random.Random(1))
    before = rnd.draws
    assert draw_name(rnd, ["Able", "Baker"], {"Able", "Baker"}) in ("Able", "Baker") and rnd.draws == before + 1
    assert rnd.fallbacks == 0
    assert draw_name(rnd, ["Able", "Baker"], {"Able"}) == "Baker"                       # a free surname is still drawn by the old rule


def test_a_man_without_a_place_is_said_with_his_own_position_and_no_bench_words():
    """SR.6 (design 21.8): "on the bench" is gone; every man is said by his own position word (Words.position_for)."""
    from nfl4.extras import nx_texts as X
    from nfl4.extras import roster_file as RF
    from nfl4.extras.franchise.history import Words
    league, _ = real_league()
    words = Words(lambda team: "Team %d" % team)
    man = league.bench(1, "QB")[0] if league.bench(1, "QB") else league.bench(1)[0]
    assert RF.SPOKEN[man.position] in words.player(man) and "on the bench" not in words.player(man)       # SR.6
    placed = league.group_of(1, "QB")[0]
    assert "on the bench" not in words.player(placed)
    assert words.group("OL") == X.text("NXL-50") and words.position("LS") == X.text("NXM-D42")


# SR.5 (D-164): the tests of D-149's bench mechanics are gone with them: real_reserves (a new franchise is exactly rosters.txt now), the bench's size
# limit and its status checks (the chart's checks, test_real_roster_sr5), the cut that kept 34 places and a bench (the cut to 53 by the family minimums,
# test_fr_cut), the bench's top-up of a snapper and five linemen (the fill of a family's minimum), the cap's FR_CAP_RESERVES (FR_CAP_ROSTER, measured
# again), a bench man's trade "into the other's slot" (any man for any man onto the chart, test_real_roster_sr5) and the older league's bench at its first
# cut (real_roster.convert and the cut).
_ = SURNAMES
