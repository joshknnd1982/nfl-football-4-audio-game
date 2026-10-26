"""SR.5 (phase PR, NX-L6, NX-L10, NX-L12; D-163, D-164; NFL_FRANCHISE_DESIGN 21.7, 21.15): every Franchise block on the real roster (nfl4 only, rule 0.13).
The chart is the team, the 34 places are its view made in memory (league.sav format 19); the cut to 53 by the family minimums; the draft of the 22 positions;
signings, trades, the practice squads, retirements and injuries on the chart; the cap of a real 53; the real NFL surnames of the made-up players.
"""
import json
import random

import pytest

from drrig import SURNAMES
from nfl4.extras import nfl_surnames
from nfl4.extras import real_names as R
from nfl4.extras import roster_model as RM
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import draft as DR
from nfl4.extras.franchise import first_names as FN
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import people
from nfl4.extras.franchise import practice as PR
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import LeagueRecord, Player, new_league
from nfl4.game.rnd import GameRandom

BEARS, DOLPHINS = 17, 6


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None
    yield
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None


def real_league(seed=3, team=BEARS):
    real = R.defaults()
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=real)
    return league, real


def free_man(league, name, position, rating=70, age=26):
    p = Player(league.next_id, name, RM.GROUP[position], rating, "average", age, age - 22, rating, None, 0, "free", league.season, 0, -1,
               position=position)
    league.players[p.id] = p
    league.next_id += 1
    return p


# ----- the model: the chart is the team, the places its view (format 19) -----

def test_every_man_of_a_new_franchise_is_active_on_his_chart_and_the_view_is_made_from_it():
    league, _ = real_league()
    league.check()
    assert not any(p.status == "reserve" for p in league.players.values())
    for team in range(1, D.TEAMS + 1):
        men = RR.members(league, team)
        chart = league.chart[team - 1]
        assert sorted(pid for position in RM.MADDEN for pid in chart[position]) == sorted(p.id for p in men)
        assert all(p.pos == RM.GROUP[p.position] for p in men)
        placed = [pid for pid in league.rosters[team - 1] if pid]
        assert len(placed) == len(set(placed))
        assert all(league.players[pid].place == i for i, pid in enumerate(league.rosters[team - 1]) if pid)
        assert all(p.place < 0 for p in league.bench(team))
    bears = RR.members(league, BEARS)
    assert len(bears) == 53 and {p.name for p in bears if p.position == "QB"} == {"Caleb Williams", "Tyson Bagent", "Case Keenum"}


def test_league_sav_19_keeps_the_charts_and_no_places_and_reads_back_the_same_places():
    league, _ = real_league()
    text = league.to_json()
    data = json.loads(text)
    assert data["format"] == D.FORMAT == 19 and "rosters" not in data and all(row[13] == -1 for row in data["players"])
    again = LeagueRecord.from_json(text)
    assert again.to_json() == text and again.rosters == league.rosters
    assert [p.place for p in sorted(again.players.values(), key=lambda p: p.id)] == [p.place for p in sorted(league.players.values(), key=lambda p: p.id)]


def as_format_18(league):
    """The file 0.16.2 (SR.4) wrote for the same league: the places stored, the men without a place on the bench (status "reserve")."""
    data = json.loads(league.to_json())
    data["format"] = 18
    data["rosters"] = league.rosters
    for row in data["players"]:
        player = league.players[row[0]]
        row[13] = player.place
        if player.status == "active" and player.place < 0:
            row[10] = "reserve"
    return json.dumps(data)


def test_a_format_18_league_reads_into_the_chart_with_its_bench_men_active():
    league, _ = real_league()
    old = as_format_18(league)
    again = LeagueRecord.from_json(old)
    assert again.loaded_format == 18
    assert not any(p.status == "reserve" for p in again.players.values())
    assert again.rosters == league.rosters and again.chart == league.chart
    again.check()


def test_a_damaged_format_18_place_is_still_refused():
    league, _ = real_league()
    data = json.loads(as_format_18(league))
    data["rosters"][0][0], data["rosters"][0][1] = data["rosters"][0][1], data["rosters"][0][0]
    with pytest.raises(Exception):
        LeagueRecord.from_json(json.dumps(data))


def test_a_drawn_league_without_real_names_still_makes_its_chart_from_its_places():
    league = new_league(GameRandom(random.Random(9)), SURNAMES, "Kim", 4, "x")
    league.check()
    assert all(p.position and p.pos == RM.GROUP[p.position] for p in league.players.values())
    assert not any(p.pos == "RET" for p in league.players.values())
    assert all(not league.has_empty_place() for _ in [0])


# ----- the cut to 53 (design 21.7 (1)) and the fill's last resort -----

def test_the_staffs_cut_keeps_53_with_every_family_minimum_and_at_most_one_kicker():
    league, _ = real_league()
    team = 12
    men = RR.members(league, team)
    extra = [free_man(league, "Extra Kicker", "K", 99), free_man(league, "Extra Punter", "P", 99)]
    extra += [free_man(league, "Extra Man %d" % i, "WR", 41) for i in range(10)]
    for p in extra:
        RR.join(league, team, p)
    assert RR.roster_count(league, team) == len(men) + 12
    released = DR.plan_cut(league, team, {})
    kept = [p for p in RR.members(league, team) if p.id not in {r.id for r in released}]
    assert len(kept) == 53
    have = RR.counts_by_group(kept)
    assert all(have.get(g, 0) >= least for g, least in T.FR_FAMILY_MIN.items())
    assert have["K"] == 1 and have["P"] == 1 and have["LS"] == 1 and have["QB"] <= 3
    assert {p.name for p in kept} >= {"Extra Kicker", "Extra Punter"}                 # rated 99, the best of their families


def test_the_cut_keeps_room_for_a_family_the_fill_must_make_and_the_fill_makes_it_with_a_real_surname():
    league, _ = real_league()
    team = 20
    for p in [p for p in RR.members(league, team) if p.pos == "LS"]:
        RR.leave(league, p, "released")
    for i in range(8):
        RR.join(league, team, free_man(league, "Camp Man %d" % i, "CB", 41))
    released = DR.plan_cut(league, team, {})
    DR.apply_cut(league, {team: released}, {})
    assert RR.roster_count(league, team) == 52                                          # one spot kept for the snapper
    made = RR.fill_needs(league, GameRandom(random.Random(1)), nfl_surnames.pool())
    mine = [p for p in made if p.team == team]
    assert [p.position for p in mine] == ["LS"] and RR.roster_count(league, team) == 53
    surname = FN.surname_of(league.league_id, mine[0].name)
    assert surname is not None and surname in nfl_surnames.shipped()
    league.check()


def test_the_reserve_lists_come_back_at_the_cut_with_a_contract():
    league, _ = real_league()
    listed = [p for p in league.players.values() if p.status == "list"]
    assert listed
    back = RR.return_lists(league)
    assert back == len(listed)
    assert all(p.status == "active" and p.roster_list == "" and CT.running(p) for p in listed)
    league.check()


# ----- the draft of the 22 positions (design 21.7 (2)) -----

def test_a_class_has_prospects_of_the_real_positions_by_the_leagues_mix_and_no_returner():
    league, _ = real_league()
    prospects = DR.make_class(league, GameRandom(random.Random(5)), nfl_surnames.pool())
    positions = {p.position for p in prospects}
    assert "RET" not in {p.pos for p in prospects} and positions <= set(RM.MADDEN)
    assert {"LT", "C", "LS", "TE", "FB", "LEDG", "MIKE", "FS"} & positions
    assert all(p.pos == RM.GROUP[p.position] for p in prospects)
    line = sum(1 for p in prospects if p.pos == "OL")
    assert 20 <= line <= 70                                                              # the league's mix: 293 of 1,686 (17 percent of 260)


def test_a_team_without_linemen_needs_them_and_a_drafted_lineman_gets_a_number_of_his_range():
    league, _ = real_league()
    team = 7
    for p in [p for p in RR.members(league, team) if p.pos == "OL"]:
        RR.leave(league, p, "released")
    league.season, league.stage = 1, "offseason"
    league.stage_no = D.STAGE_DRAFT
    draft = DR.Draft.create(league, GameRandom(random.Random(2)), nfl_surnames.pool())
    needs = draft.needs(team)
    assert needs["OL"][0] is True and needs["OL"][1] is None
    number = DR.free_number(league, team, "LT")
    assert 50 <= int(number) <= 79 and number not in {p.number for p in league.players.values() if p.team == team and p.status in ("active", "practice", "list")}


# ----- signings, trades, the squads, retirements on the chart -----

def test_a_signed_free_agent_joins_his_positions_chart_by_the_staffs_order_and_the_places_follow():
    league, _ = real_league()
    team = league.team
    star = free_man(league, "Star Receiver", "WR", 99)
    RR.leave(league, RR.members(league, team)[-1], "released")
    league.gtp = 1
    assert S.problems(league, star, None, 1) is None
    S.sign(league, star, None, 1)
    assert league.chart[team - 1]["WR"][0] == star.id and star.place == D.PLACES_OF["WR"][0]
    league.check()


def test_a_trade_may_swap_men_of_different_positions_unless_a_team_would_fall_under_a_minimum():
    league, _ = real_league()
    league.gtp = 1
    a, b = 3, 4
    wr = league.players[league.chart[a - 1]["WR"][-1]]
    cb = league.players[league.chart[b - 1]["CB"][-1]]
    trade = TR.Trade(a, b, wr.id, cb.id, (), ())
    assert TR.problems(league, trade, 1) in (None, "over the cap")
    snapper = next(p for p in RR.members(league, a) if p.position == "LS")
    trade = TR.Trade(a, b, snapper.id, cb.id, (), ())
    assert TR.problems(league, trade, 1) == "a team would be short of a position"


def test_a_trade_moves_each_man_onto_the_other_teams_chart():
    league, _ = real_league()
    league.gtp = 1
    a, b = 3, 4
    pa = next(p for p in RR.members(league, a) if p.position == "WR")
    pb = next(p for p in RR.members(league, b) if p.position == "WR")
    TR.execute(league, TR.Trade(a, b, pa.id, pb.id, (), ()), 1, 0)
    assert pa.team == b and pa.id in league.chart[b - 1]["WR"] and pa.id not in league.chart[a - 1]["WR"]
    assert pb.team == a and pb.id in league.chart[a - 1]["WR"]
    league.check()


def test_a_promoted_squad_man_joins_the_chart():
    league, _ = real_league()
    team = league.team
    man = PR.squad(league, team)[0]
    RR.leave(league, RR.members(league, team)[-1], "released")
    league.gtp, league.practice["season"] = 1, league.season
    assert PR.promote_problem(league, man, None, 1) is None
    PR.promote(league, man, None)
    assert man.status == "active" and man.id in league.chart[team - 1][man.position] and man.roster_list == ""
    league.check()


def test_a_retired_starter_leaves_his_chart_and_the_next_man_plays_his_place():
    league, _ = real_league()
    qb = league.player_at(BEARS, D.PLACES_OF["QB"][0])
    second = league.chart[BEARS - 1]["QB"][1]
    aging.apply_aging(league, [qb])
    assert qb.status == "retired" and qb.id not in league.chart[BEARS - 1]["QB"]
    assert league.rosters[BEARS - 1][D.PLACES_OF["QB"][0]] == second


def test_a_starter_is_the_first_of_his_positions_chart():
    league, _ = real_league()
    chart = league.chart[BEARS - 1]
    assert people.is_starter(league, league.players[chart["QB"][0]]) and not people.is_starter(league, league.players[chart["QB"][1]])
    assert all(people.is_starter(league, league.players[pid]) for pid in chart["WR"][:3])


def test_a_hurt_starters_place_goes_to_the_next_man_of_his_chart_at_the_replacement_level():
    league, _ = real_league()
    league.gtp = 2
    qb = league.player_at(BEARS, D.PLACES_OF["QB"][0])
    I.injure(league, qb.id, I.KIND_IDS[0], 4, 0, 1)
    table = I.lineup(league, BEARS, 2, staff=True)
    backup = league.players[league.chart[BEARS - 1]["QB"][1]]
    assert table[D.PLACES_OF["QB"][0]][0] == backup.id
    assert table[D.PLACES_OF["QB"][0]][2] <= min(backup.rating, qb.rating)


# ----- the cap of a real 53 (design 21.7 (10)) -----

def test_the_cap_is_the_measured_cap_of_a_real_53_and_a_new_league_starts_under_it():
    league, _ = real_league()
    assert CT.cap_of(league) == T.FR_CAP + T.FR_CAP_ROSTER == 1932 + 510
    assert all(CT.cap_space(league, t) >= 0 for t in range(1, D.TEAMS + 1))


# ----- NX-L12: the real NFL surnames of the made-up players -----

def test_twenty_draft_classes_take_only_real_nfl_surnames_and_no_real_players_full_name():
    league, real = real_league()
    pool = nfl_surnames.pool()
    keys = {s.casefold() for s in pool}
    real_full = real.real_full_names()
    rnd = GameRandom(random.Random(20))
    for season in range(20):
        league.league_id = "L%02d" % season
        for prospect in DR.make_class(league, rnd, pool):
            surname = FN.surname_of(league.league_id, prospect.name)
            assert surname is not None and surname.casefold() in keys, prospect.name
            assert prospect.name.casefold() not in real_full, prospect.name
    assert len(pool) > 9000


def test_a_made_up_first_name_never_makes_a_real_players_full_name():
    real = R.defaults()
    full = real.real_full_names()
    assert "josh allen" in full
    league_id = next("L%d" % n for n in range(100000) if FN.FIRST_NAMES[__import__("zlib").crc32(("L%d|Allen" % n).encode()) % len(FN.FIRST_NAMES)] == "Josh")
    name = FN.full_name(league_id, "Allen")
    assert name != "Josh Allen" and name.endswith(" Allen") and FN.surname_of(league_id, name) == "Allen"


def test_the_surnames_file_is_a_customizable_list_of_real_nfl_last_names():
    text = R.shipped_text(R.NFL_SURNAMES)
    assert text.startswith("# NFL Football 4 nflsurnames, format 1.")
    names = R.defaults().surname_pool()
    assert len(names) == len(set(n.casefold() for n in names)) > 9000
    assert {"Smith", "Allen", "St. Brown", "Kelce"} <= set(names)
    assert all(2 <= len(n) <= 30 and "," not in n and ";" not in n for n in names)


def test_a_quick_games_last_resort_name_is_a_real_surname_from_the_drawn_one():
    real = R.defaults()
    name = real.last_resort("Acerbis")
    assert name != "Acerbis" and name.split(" ", 1)[1] in real.surname_pool() and name == real.last_resort("Acerbis")
