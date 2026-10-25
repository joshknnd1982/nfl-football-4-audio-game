"""NX-B2b (D-149, the owner 2026-10-24: "it should be using the current 53 man rosters for each team"): the Franchise keeps every team's 53 (nfl4 only,
rule 0.13). A team is its 34 places and a bench (status "reserve", extras/franchise/reserves.py); the design is spec/NFL_EXTRA_FEATURES section 19.1.
"""
import json
import random

import pytest

from drrig import SURNAMES
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import depth as FD
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import reserves
from nfl4.extras.franchise import resign
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.aging import league_order
from nfl4.extras.franchise.league import LeagueRecord, Player, new_league
from nfl4.game.rnd import GameRandom


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def older_names(real):
    """SR.4 (D-161): the real names without their real positions (a format-1 style file), so a new league is made as 0.16 made it (34 places, the
    rest of the 53 on a bench by `real_reserves`): the bench rules of D-149 that the bridge keeps for every league until SR.5 are tested on it."""
    import dataclasses
    rosters = tuple(tuple(dataclasses.replace(p, madden="") for p in roster) for roster in real.rosters)
    return dataclasses.replace(real, rosters=rosters)


def real_league(seed=3, team=1):
    real = older_names(R.defaults())
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000", real=real)
    return league, real


def benched_league(seed=3, team=1):
    league, real = real_league(seed, team)
    reserves.real_reserves(league, real)
    return league, real


# ----- a new franchise of the real 53 -----

def test_a_new_franchise_puts_the_rest_of_every_real_53_on_the_bench_and_the_places_play_as_before():
    league, real = real_league()
    sums = [league.strength_sum(t) for t in range(1, 33)]
    placed = {pid for roster in league.rosters for pid in roster}
    rnd_draws = None
    joined = reserves.real_reserves(league, real)
    assert joined > 500 and league.reserves_on
    assert [league.strength_sum(t) for t in range(1, 33)] == sums                     # the strengths count the 34 places only
    assert {pid for roster in league.rosters for pid in roster} == placed
    names = [p.name.casefold() for p in league.players.values()]
    assert len(names) == len(set(names))                                              # every name once
    for team in range(1, 33):
        bench = league.bench(team)
        assert 15 <= len(bench) <= reserves.MAX, team
        assert len(bench) + sum(1 for p in league.active_of(team) if p) <= D.ROSTER_MAX
        real_names = {real.spoken(p.name) for p in real.active(team) if p.pos != "RET"}
        assert {p.name for p in bench} <= real_names, team                            # only real men of that team
        for p in bench:
            assert p.place == -1 and p.team == team and p.status == "reserve"
            group = [q.rating for q in league.group_of(team, p.pos) if q is not None]
            if group:
                assert p.rating < min(group), (team, p.name)                           # below every place of his group
            assert CT.running(p) and p.salary >= T.FR_MIN_SALARY
        assert any(p.pos == "LS" for p in bench), team                                # the long snapper is kept
        assert sum(1 for p in bench if p.pos == "OL") >= 5, team                       # and the line
    assert sum(1 for t in range(1, 33) if league.bench(t, "QB")) >= 30                 # a backup quarterback almost everywhere (Q-069)
    assert all(p.pos not in D.RESERVE_POSITIONS for roster in league.rosters for pid in roster for p in [league.players[pid]])
    assert reserves.real_reserves(league, real) == 0                                   # once
    league.check()


def test_the_bench_is_made_with_no_draw_and_the_same_league_gives_the_same_bench():
    a, real = real_league(5)
    b, _ = real_league(5)
    reserves.real_reserves(a, real)
    reserves.real_reserves(b, real)
    assert a.to_json() == b.to_json()
    rnd = GameRandom(random.Random(5))
    league = new_league(rnd, SURNAMES, "Kim", 1, "20260101-000000", real=real)
    before = rnd.draws
    reserves.real_reserves(league, real)
    assert rnd.draws == before


def test_the_cap_of_a_league_with_benches_has_the_benchs_share_and_every_team_starts_under_it():
    league, _ = benched_league()
    assert CT.cap_of(league) == T.FR_CAP + T.FR_CAP_RESERVES
    assert all(CT.cap_space(league, t) >= 0 for t in range(1, 33))
    assert all(CT.payroll(league, t) == sum(p.salary for p in CT.team_players(league, t) if CT.running(p)) for t in range(1, 33))
    assert all(any(p.status == "reserve" for p in CT.team_players(league, t)) for t in range(1, 33))     # the bench is paid
    plain, _ = real_league()
    assert CT.cap_of(plain) == T.FR_CAP                                                # a league without benches: as before


def test_format_17_round_trips_and_an_older_file_loads_with_nobody_on_a_bench():
    league, _ = benched_league()
    text = league.to_json()
    assert json.loads(text)["format"] == D.FORMAT == 18                               # SR.4: the bench of a format-17 league is kept in format 18
    again = LeagueRecord.from_json(text)
    assert sum(1 for p in again.players.values() if p.status == "reserve") == sum(1 for p in league.players.values() if p.status == "reserve")
    plain, _ = real_league()
    data = json.loads(plain.to_json())
    data["format"] = 16
    old = LeagueRecord.from_json(json.dumps(data))
    assert not old.reserves_on and all(p.status != "reserve" for p in old.players.values())
    data["format"] = 19
    with pytest.raises(Exception):
        LeagueRecord.from_json(json.dumps(data))


def test_the_whole_file_check_refuses_a_bench_that_is_too_big_or_a_lineman_in_a_place():
    from nfl4.extras.franchise.league import LeagueError
    league, _ = benched_league()
    man = league.bench(1)[0]
    man.place = 3
    with pytest.raises(LeagueError):
        league.check()
    man.place = -1
    extra = [p for p in league.players.values() if p.status == "reserve" and p.team == 2][:5]
    for p in extra:
        p.team = 1
    if len(league.bench(1)) > reserves.MAX:
        with pytest.raises(LeagueError):
            league.check()
    for p in extra:
        p.team = 2
    league.check()
    lineman = league.bench(1, "OL")[0]
    lineman.status = "active"
    with pytest.raises(LeagueError):
        league.check()


# ----- the year: aging, contracts, the order of the draws -----

def test_the_bench_ages_after_its_team_and_a_league_without_one_keeps_its_order():
    league, _ = benched_league()
    order = [p.id for p in league_order(league)]
    first_bench = [p.id for p in league.bench(1)]
    assert order[34:34 + len(first_bench)] == sorted(first_bench)
    plain, _ = real_league()
    assert [p.id for p in league_order(plain)] == [pid for roster in plain.rosters for pid in roster if pid]


def test_a_bench_mans_contract_runs_out_and_is_settled_in_stage_7():
    league, _ = benched_league()
    man = league.bench(4)[0]
    man.years = 0
    assert man in resign.expiring(league, 4)
    resign.let_go(league, man)
    assert man.status == "free" and man.place == -1 and man not in league.bench(4)
    assert resign.room_after(0, 0, 0, *resign.league_terms(league)) == CT.cap_of(league) - T.FR_RESIGN_RESERVE - T.FR_MIN_SALARY * (D.ROSTER_MAX - 1)
    assert resign.room_after(0, 0, 0) == T.FR_CAP - T.FR_RESIGN_RESERVE - T.FR_MIN_SALARY * 33        # the older rule, unchanged


# ----- the cut keeps 53 -----

def rookies(league, team, count, position="WR", rating=58):
    out = []
    for n in range(count):
        p = Player(league.next_id, "Rookie Number %d" % league.next_id, position, rating - n % 7, "average", 22, 0, rating, None, 0, "active", 0, team, -1,
                   T.FR_MIN_SALARY, 3)
        league.players[p.id] = p
        league.next_id += 1
        out.append(p)
    return out


def test_the_cut_of_a_league_with_benches_keeps_53_and_releases_the_worst():
    league, _ = benched_league()
    team = 6
    added = rookies(league, team, 12)
    waiting = DR.waiting_by_team(league)
    plan = DR.plan_cut(league, team, waiting)
    before = len(league.bench(team)) + len(added)
    assert len(plan) == before - reserves.MAX                                           # over the bench's room
    order = reserves.bench_order(DR.bench_candidates(league, team, waiting)[0], DR.keep_order)
    kept = order[:reserves.MAX]
    assert any(p.pos == "QB" for p in kept) == any(p.pos == "QB" for p in order)       # the backup quarterback is kept first
    assert any(p.pos == "LS" for p in kept)
    DR.apply_cut(league, {team: plan}, waiting)
    assert len(league.bench(team)) == reserves.MAX
    assert sum(1 for p in league.active_of(team) if p) == D.PLACE_COUNT
    assert all(p.status == "released" for p in plan)
    for position in D.ROSTER_ORDER:                                                     # the best of a group holds its places
        places = [p.rating for p in league.group_of(team, position)]
        bench = [p.rating for p in league.bench(team, position)]
        assert not bench or min(places) >= max(bench), position
    league.check()


def test_the_cut_without_benches_is_the_old_one():
    league, _ = real_league()
    team = 6
    rookies(league, team, 4)
    waiting = DR.waiting_by_team(league)
    plan = DR.plan_cut(league, team, waiting)
    assert len(plan) == 4 and all(p.pos == "WR" for p in plan)


def test_an_older_league_fills_its_bench_at_its_first_cut():
    league, _ = real_league()
    league.reserves_on = True                                                           # (the store sets it on a league it opens)
    team = 9
    added = rookies(league, team, 8)
    waiting = DR.waiting_by_team(league)
    plan = DR.plan_cut(league, team, waiting)
    assert plan == []                                                                   # 8 men fit on an empty bench
    DR.apply_cut(league, {team: plan}, waiting)
    assert sorted(p.id for p in league.bench(team)) == sorted(p.id for p in added if p.place == -1)
    league.check()


# ----- an injury: the bench man plays -----

def test_a_hurt_quarterback_is_played_by_the_backup_of_the_bench_never_above_the_starter():
    league, _ = benched_league()
    team = next(t for t in range(2, 33) if league.bench(t, "QB"))
    starter = league.group_of(team, "QB")[0]
    backup = league.bench(team, "QB")[0]
    I.injure(league, starter.id, I.KIND_IDS[0], 4, 0, 1)
    table = I.lineup(league, team, 2, staff=True)
    index = D.PLACES_OF["QB"][0]
    assert table[index][0] == backup.id and table[index][2] == min(backup.rating, starter.rating)
    assert I.bench_covers(league, team, "QB", 2)


def test_the_player_may_choose_a_bench_man_for_his_hurt_mans_place():
    league, _ = benched_league()
    team = league.team
    group = [p for p in league.group_of(team, "DL")]
    hurt = group[0]
    I.injure(league, hurt.id, I.KIND_IDS[0], 4, 0, 1)
    bench = league.bench(team, "DL")
    choices = I.cover_choices(league, hurt.id, 2)
    assert set(p.id for p in bench) <= {p.id for p in choices}
    I.choose(league, hurt.id, bench[-1].id)
    table = I.lineup(league, team, 2, staff=False)
    assert table[hurt.place][0] == bench[-1].id


# ----- the player's own moves -----

def test_a_bench_man_put_first_takes_the_first_place_and_the_last_man_goes_to_the_bench():
    league, _ = benched_league()
    team = league.team
    last = league.group_of(team, "S")[-1]
    man = league.bench(team, "S")[-1]
    FD.put_first(league, "S", man.id)
    assert league.group_of(team, "S")[0].id == man.id and man.status == "active"
    assert last.status == "reserve" and last in league.bench(team, "S")
    league.check()


def test_a_backup_quarterback_and_the_starter_swap_places_with_no_release():
    league, _ = benched_league()
    team = next(t for t in range(1, 33) if league.bench(t, "QB"))
    starter, backup = league.group_of(team, "QB")[0], league.bench(team, "QB")[0]
    before = CT.payroll(league, team)
    reserves.swap(league, starter, backup)
    assert league.group_of(team, "QB")[0].id == backup.id and starter.status == "reserve"
    assert CT.payroll(league, team) == before
    league.check()


def test_a_free_agent_signs_to_the_bench_when_it_has_room_and_a_bench_man_may_be_released():
    league, _ = benched_league()
    team = league.team
    while reserves.room(league, team) == 0:
        man = league.bench(team)[-1]
        man.status, man.team, man.salary, man.years, man.left = "free", 0, 0, 0, league.season
    agent = Player(league.next_id, "Free Agent Here", "LB", 61, "average", 28, 6, 61, None, 0, "free", 0, 0, -1, 0, 0)
    league.players[agent.id] = agent
    league.next_id += 1
    assert S.open_place(league, team, "LB")
    assert S.problems(league, agent, None, 3) is None
    S.sign(league, agent, None, 3)
    assert agent.status == "reserve" and agent.team == team
    league.check()
    other = Player(league.next_id, "Second Free Agent", "LB", 62, "average", 28, 6, 62, None, 0, "free", 0, 0, -1, 0, 0)
    league.players[other.id] = other
    league.next_id += 1
    while reserves.room(league, team):
        filler = Player(league.next_id, "Filler %d" % league.next_id, "OL", 55, "low", 26, 4, 55, None, 0, "reserve", 0, team, -1, T.FR_MIN_SALARY, 1)
        league.players[filler.id] = filler
        league.next_id += 1
    assert S.problems(league, other, None, 3) == "no place and no release"
    assert S.problems(league, other, agent, 3) is None                                  # a man of the bench may be released for him
    S.sign(league, other, agent, 3)
    assert other.status == "reserve" and agent.status == "free"
    league.check()


def test_a_bench_man_may_be_traded_and_each_man_takes_the_others_slot():
    from nfl4.extras.franchise.league import SEASON
    league, _ = benched_league()
    assert league.stage == SEASON
    a, b = 1, 2
    position = next(pos for pos in ("DL", "LB", "CB", "S", "WR") if league.bench(a, pos))
    mine = league.bench(a, position)[0]
    theirs = league.group_of(b, position)[-1]
    index = theirs.place
    trade = TR.Trade(a, b, mine.id, theirs.id)
    if TR.problems(league, trade, 3) not in (None, "outside the trade window"):
        pytest.fail(TR.problems(league, trade, 3))
    TR.execute(league, trade, 3, 0)
    assert mine.team == b and mine.status == "active" and theirs.team == a and theirs.status == "reserve"
    assert league.rosters[b - 1][mine.place] == mine.id and mine.place in D.PLACES_OF[position] and index in D.PLACES_OF[position]
    league.check()


def test_a_lineman_let_go_from_a_bench_never_joins_a_practice_squad():
    """The soak of 2026-10-25 found it: practice.form took a released lineman, and the whole-file check refused a squad lineman."""
    from nfl4.extras.franchise import practice as P
    league, _ = benched_league()
    lineman = league.bench(3, "OL")[0]
    lineman.status, lineman.team, lineman.left, lineman.salary, lineman.years = "released", 0, league.season, 0, 0
    assert lineman not in P.candidates(league)
    lineman.status, lineman.left = "free", 0
    assert P.sign_problem(league, lineman) in ("not a position of the squad", "not a free agent")
    league.check()


def test_the_cut_tops_a_bench_up_to_a_snapper_and_five_linemen_with_no_draw():
    league, _ = benched_league()
    team = 7
    for man in league.bench(team, "OL") + league.bench(team, "LS"):
        man.status, man.team, man.left, man.salary, man.years = "released", 0, league.season, 0, 0
    before = league.to_json()
    made = reserves.fill_line(league, SURNAMES)
    assert made >= 6 and len(league.bench(team, "LS")) == 1 and len(league.bench(team, "OL")) == 5
    again = LeagueRecord.from_json(before)
    again.reserves_on = True
    assert reserves.fill_line(again, SURNAMES) == made and again.to_json() == league.to_json()       # the same men from the same league
    league.check()
    plain, _ = real_league()
    assert reserves.fill_line(plain, SURNAMES) == 0                                    # nothing in a league without benches


def test_the_cut_keeps_room_for_the_snapper_and_the_linemen_a_bench_lacks():
    """The soak of 2026-10-25: benches filled with rookies left no room for the made-up linemen, and the linemen died out."""
    league, _ = benched_league()
    team = 8
    for man in league.bench(team, "OL") + league.bench(team, "LS"):
        man.status, man.team, man.left, man.salary, man.years = "released", 0, league.season, 0, 0
    rookies(league, team, 30)
    waiting = DR.waiting_by_team(league)
    plan = DR.plan_cut(league, team, waiting)
    DR.apply_cut(league, {team: plan}, waiting)
    assert len(league.bench(team)) == reserves.MAX - 6
    assert reserves.fill_line(league, SURNAMES) >= 6 and len(league.bench(team)) == reserves.MAX
    assert len(league.bench(team, "OL")) == 5 and len(league.bench(team, "LS")) == 1
    league.check()


def test_a_name_pool_all_in_use_costs_one_draw_not_ten_thousand():
    from nfl4.extras.franchise.league import draw_name
    rnd = GameRandom(random.Random(1))
    before = rnd.draws
    assert draw_name(rnd, ["Able", "Baker"], {"Able", "Baker"}) in ("Able", "Baker") and rnd.draws == before + 1
    assert rnd.fallbacks == 0
    assert draw_name(rnd, ["Able", "Baker"], {"Able"}) == "Baker"                       # a free surname is still drawn by the old rule


# ----- the texts -----

def test_a_bench_man_is_said_with_his_position_on_the_bench():
    from nfl4.extras import nx_texts as X
    from nfl4.extras.franchise.history import Words
    league, _ = benched_league()
    words = Words(lambda team: "Team %d" % team)
    man = league.bench(1, "QB")[0] if league.bench(1, "QB") else league.bench(1)[0]
    assert X.text("NXL-52", position=words.position(man.pos)) in words.player(man)
    placed = league.group_of(1, "QB")[0]
    assert "on the bench" not in words.player(placed)
    assert words.group("OL") == X.text("NXL-50") and words.position("LS") == X.text("NXM-D42")
