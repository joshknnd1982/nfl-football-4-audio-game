"""SR.4 (phase PR, NX-L3, NX-L4, NX-L5, NX-L7, NX-L11 data; D-159, D-160, D-161; NFL_FRANCHISE_DESIGN 21.3 to 21.6 and 21.13): the real roster as the
team (nfl4 only, rule 0.13). A team is its depth chart on Madden NFL's 22 positions; the engine's 34 places are a view made from it; a new franchise is
exactly the men of rosters.txt; an older league is converted once; the player chooses who starts at every position.
"""
import json
import random

import pytest

from drrig import SURNAMES
from nfl4.extras import depth_chart as DC
from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF
from nfl4.extras import roster_model as RM
from nfl4.extras import tuning as T
from nfl4.extras import usage
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import reserves
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import LeagueRecord, new_league
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.rnd import GameRandom

BEARS, DOLPHINS = 17, 6


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def shipped_teams():
    _, teams, problems = RF.parse(R.shipped_text(R.ROSTERS))
    assert problems == []
    return teams


def real_league(seed=3, team=BEARS):
    real = R.defaults()
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", team, "20260101-000000", real=real)
    league.reserves_on = True
    return league, real


def older_names(real):
    import dataclasses
    return dataclasses.replace(real, rosters=tuple(tuple(dataclasses.replace(p, madden="") for p in roster) for roster in real.rosters))


# ----- the rules of the model -----

def test_the_conversion_table_maps_every_older_word_into_its_own_family():
    assert RM.convert_word("RB", {}) == "HB" and RM.convert_word("FB", {}) == "FB" and RM.convert_word("RET", {}) == "WR"
    assert RM.convert_word("QB", {}) == "QB" and RM.convert_word("LS", {}) == "LS" and RM.convert_word("TE", {}) == "TE"
    assert RM.convert_word("DL", {}) == "LEDG"                                         # ties: the first of the 22's order
    assert RM.convert_word("DL", {"LEDG": 2, "REDG": 2, "DT": 1}) == "DT"             # the position the team is shortest of against the league
    assert RM.convert_word("OL", {"LT": 1, "LG": 1, "C": 0, "RG": 1, "RT": 1}) == "C"
    assert RM.convert_word("LB", {"SAM": 0, "MIKE": 1, "WILL": 1}) == "SAM"
    assert RM.convert_word("S", {"FS": 2, "SS": 1}) == "SS" and RM.convert_word("RET", {"WR": 6, "CB": 1}) == "CB"
    for word, positions in RM.WORD_POSITIONS.items():
        if word != "RET":                                                              # a returner of an older league: a receiver or a corner
            assert all(RM.FAMILY[p] == RM.FAMILY[positions[0]] for p in positions), word
    assert RM.convert_word("XX", {}) == ""


def test_a_starter_comes_from_his_position_or_its_other_side_never_another_family():
    assert RM.may_start_at("LT", "RT") and RM.may_start_at("MIKE", "WILL") and RM.may_start_at("FS", "SS") and RM.may_start_at("HB", "FB")
    assert not RM.may_start_at("WR", "QB") and not RM.may_start_at("C", "LG") and not RM.may_start_at("CB", "FS") and not RM.may_start_at("TE", "WR")
    assert RM.put_first(["a", "b", "c"], "c") == ["c", "b", "a"]                      # a swap: the starter takes the chosen man's place
    assert RM.put_first(["a", "b", "c"], "c", 1) == ["a", "c", "b"]
    assert RM.put_first(["a", "b"], "x") == ["x", "a", "b"]                          # a man from the other side joins at the slot


def test_the_view_of_every_team_at_full_health_has_the_designs_counts():
    """Design 21.1: 74 back places empty over the league (only where a team has fewer than six backs), the 14 short backer places filled by spare line
    men (an edge man first, then a tackle: design 21.4 (4)) and the one short corner place by a safety; nobody twice in the Franchise's view; the
    Dolphins' squad kicker plays."""
    teams = shipped_teams()
    empty = covered_backers = covered_corners = 0
    for t, team in teams.items():
        active = team.active()
        chart = RM.ordered_positions(list(range(len(active))), lambda k: active[k].pos)
        squad = team.squad()
        squad_chart = RM.ordered_positions([("PS", i) for i in range(len(squad))], lambda k: squad[k[1]].pos)
        view = RM.make_view(chart, {"KR": [], "PR": []}, squad=squad_chart, distinct=True)
        backs = sum(1 for m in active if m.pos in ("HB", "FB"))
        assert [i for i in view.empty] == list(range(min(6, backs), 6)), t
        empty += len(view.empty)
        covered_backers += sum(1 for i, p in view.covered.items() if 18 <= i <= 22 and p in ("LEDG", "REDG", "DT"))
        spare_edges = [m for k, m in enumerate(active) if m.pos in ("LEDG", "REDG") and k not in men_of(view)]
        assert not (spare_edges and any(p == "DT" for i, p in view.covered.items() if 18 <= i <= 22)), t      # an edge man before a tackle
        covered_corners += sum(1 for i in view.covered if 23 <= i <= 26)
        men = view.men()
        assert len(men) == len(set(men)), t
        assert view.places[RM.KICKER] is not None and view.places[RM.PUNTER] is not None, t
    assert (empty, covered_backers, covered_corners) == (74, 14, 1)


def men_of(view):
    return set(view.men())


def test_a_quick_games_names_are_the_view_and_an_empty_back_place_carries_nothing():
    real = R.defaults()
    roster = real.roster(BEARS, None)
    assert roster.running_backs[:3] == ["D'Andre Swift", "Kyle Monangai", "Roschon Johnson"]
    assert roster.running_backs[3:] == ["Roschon Johnson"] * 3                         # the empty places name their cover (the original's draws)
    assert roster.empty == [("Running Backs:", 4), ("Running Backs:", 5), ("Running Backs:", 6)]
    assert roster.special_teams[0] == "Kalif Raymond"                                 # the first kick returner (he is the third receiver too)
    weights = usage.without_empty(usage.shares(usage.RUN), roster.empty, usage.RUNNING_BACKS)
    assert weights == [60, 25, 10, 0, 0, 0]
    rnd = GameRandom(random.Random(7))
    counts = [0] * 6
    for _ in range(20000):
        counts[usage.weighted_place(rnd, weights) - 1] += 1
    assert counts[3:] == [0, 0, 0] and abs(counts[0] / 20000 - 60 / 95) < 0.015
    assert usage.without_empty([60, 25, 10, 5, 0, 0], [], usage.RUNNING_BACKS) == [60, 25, 10, 5, 0, 0]   # no empty place: unchanged
    dolphins = real.roster(DOLPHINS, None)
    assert dolphins.kickers[0] == "Zane Gonzalez" and "Zane Gonzalez" in [p.name for p in real.squad(DOLPHINS)]


# ----- a new franchise is exactly the file (NX-L4) -----

def test_every_team_of_a_new_franchise_is_its_real_roster_man_for_man():
    league, real = real_league()
    league.check()
    teams = shipped_teams()
    for t, team in teams.items():
        mine = {p.name: p for p in league.players.values() if p.team == t}
        file_men = {real.spoken(m.name): m for m in team.men}
        assert set(mine) == set(file_men), t                                           # nobody left off, nobody made up
        for name, man in file_men.items():
            p = mine[name]
            assert (p.position, p.number) == (man.pos, man.number), (t, name)
            if man.status == "":
                assert p.status in ("active", "reserve") and p.roster_list == "", (t, name)
            elif man.status == RF.SQUAD:
                assert (p.status, p.roster_list) in (("practice", "PS"), ("active", "")), (t, name)      # ("active": the squad kicker the view needs)
            else:
                assert (p.status, p.roster_list) == ("list", man.status), (t, name)
        chart = league.chart[t - 1]
        for position in RM.MADDEN:
            want = [real.spoken(m.name) for m in team.active() if m.pos == position]
            got = [league.players[pid].name for pid in chart[position] if league.players[pid].roster_list == ""]
            assert [n for n in got if n in want] == want, (t, position)              # the file's depth order (an elevated kicker leads his own)
        assert [league.players[pid].name for pid in chart["KR"]] == [real.spoken(n) for n in team.roles["KR"]], t
        on_53 = [p for p in mine.values() if p.status in ("active", "reserve")]
        assert len(on_53) <= D.ROSTER_MAX + D.GAME_DAY_EXTRA, t
    bears = {p.name: p for p in league.players.values() if p.team == BEARS}
    assert [n for n in ("Caleb Williams", "Tyson Bagent", "Case Keenum") if bears[n].status in ("active", "reserve")] == [
        "Caleb Williams", "Tyson Bagent", "Case Keenum"]
    assert league.player_at(BEARS, 33).name == "Caleb Williams" and bears["Miller Moss"].status == "practice"
    assert bears["Colston Loveland"].position == "TE" and bears["Colston Loveland"].pos == "WR"     # the bridge: his group is the receivers'
    assert league.roster_version == real.version


def test_a_new_franchise_makes_the_same_draws_with_or_without_the_real_rosters():
    a, b = GameRandom(random.Random(11)), GameRandom(random.Random(11))
    new_league(a, SURNAMES, "Kim", 5, "x", real=R.defaults())
    new_league(b, SURNAMES, "Kim", 5, "x")
    assert a.draws == b.draws


def test_a_new_franchise_round_trips_in_format_18_and_its_lineup_plays_the_empty_places_as_their_cover():
    league, _ = real_league()
    text = league.to_json()
    data = json.loads(text)
    assert data["format"] == D.FORMAT == 18 and len(data["players"][0]) == 19 and len(data["chart"]) == 32
    again = LeagueRecord.from_json(text)
    again.reserves_on = True
    assert again.to_json() == text
    from nfl4.extras.franchise import injuries as I
    table = I.lineup(league, BEARS, 1, staff=True)
    assert [row[0] for row in table[3:6]] == [I.EMPTY] * 3 and table[3][1] == "Roschon Johnson"
    roster = league.roster_for_game(BEARS)
    assert roster.empty == [("Running Backs:", 4), ("Running Backs:", 5), ("Running Backs:", 6)]
    assert league.strength_sum(BEARS) == league.sums[BEARS - 1] and 40 * 78 <= league.strength_sum(BEARS) <= 99 * 78
    assert not league.has_empty_place() and reserves.room(league, BEARS) == 0           # 53 men: no open spot although back places are empty


# ----- an older league is converted once (NX-L7) -----

def downgraded(league, version):
    data = json.loads(league.to_json())
    data["format"] = version
    for key in ("chart", "roster_version", "roster_offer"):
        del data[key]
    for row in data["players"]:
        del row[16:]
    return json.dumps(data)


def test_a_format_16_league_gets_its_teams_missing_real_men_and_every_real_quarterback_at_once():
    real = R.defaults()
    old = new_league(GameRandom(random.Random(4)), SURNAMES, "Kim", 9, "20260101-000000", real=older_names(real))
    assert sum(1 for p in old.players.values() if p.team == BEARS and p.pos == "QB") == 1          # the tester's report: one quarterback
    league = LeagueRecord.from_json(downgraded(old, 16))
    league.reserves_on = True
    done = RR.convert(league, real)
    assert done["from"] == 16 and done["joined"] > 500 and done["positions"] > 900
    league.check()
    for t, team in shipped_teams().items():
        names = {p.name for p in league.players.values() if p.team == t and p.status in ("active", "reserve")}
        assert {real.spoken(m.name) for m in team.active() if m.pos == "QB"} <= names, t
    bears = {p.name: p for p in league.players.values() if p.team == BEARS}
    assert bears["Tyson Bagent"].status == "reserve" and bears["Tyson Bagent"].position == "QB" and bears["Tyson Bagent"].number == "17"
    assert all(p.position for p in league.players.values())
    again = LeagueRecord.from_json(league.to_json())
    assert again.loaded_format == 18 and again.converted is None


def test_a_format_17_league_keeps_its_bench_and_gets_the_positions_by_name():
    real = R.defaults()
    old = new_league(GameRandom(random.Random(4)), SURNAMES, "Kim", 9, "20260101-000000", real=older_names(real))
    reserves.real_reserves(old, older_names(real))
    league = LeagueRecord.from_json(downgraded(old, 17))
    league.reserves_on = True
    done = RR.convert(league, real)
    assert done["joined"] == 0 and done["from"] == 17
    loveland = next(p for p in league.players.values() if p.name == "Colston Loveland")
    assert loveland.position == "TE" and loveland.pos == "WR"
    league.check()


def test_the_store_keeps_the_older_file_and_converts_the_league_when_it_opens_it():
    real = R.defaults()
    old = new_league(GameRandom(random.Random(4)), SURNAMES, "Kim", 9, "20260101-000000", real=older_names(real))
    old.schedule = [[2, 1, 1]] * 16
    files = MemoryFiles()
    files.data["league.sav"] = downgraded(old, 16).encode("utf-8")
    store = FranchiseStore(files)
    store.real_names_of = lambda: real
    store.open(True)
    assert store.league is not None and store.league.converted["from"] == 16
    assert files.data["league.sav.before-format-18"] == downgraded(old, 16).encode("utf-8")
    assert store.save() and json.loads(files.data["league.sav"])["format"] == 18


# ----- who starts (NX-L11 data) -----

FIRST_PLACE = {"HB": 0, "WR": 6, "TE": 9, "LEDG": 12, "REDG": 13, "DT": 14, "SAM": 18, "MIKE": 19, "WILL": 20, "CB": 23, "FS": 27, "SS": 28,
               "K": 31, "P": 32, "QB": 33}


def test_in_a_franchise_the_player_chooses_the_starter_at_every_position_and_the_places_follow():
    league, _ = real_league()
    chart = league.chart[BEARS - 1]
    for position in RM.MADDEN + RM.ROLES:
        men = chart[position] if position in RM.ROLES else [pid for pid in chart[position]]
        if position in RM.ROLES:
            men = [p.id for p in league.team_men(BEARS) if p.status == "reserve" and p.position in ("WR", "CB", "HB")]
        if len(men) < 2:
            continue
        pick = men[1]
        order = RR.choose_starter(league, position, pick)
        assert order[0] == pick and league.chart[BEARS - 1][position][0] == pick, position
        if position in FIRST_PLACE:
            assert league.rosters[BEARS - 1][FIRST_PLACE[position]] == pick, position
        if position == "KR":
            assert league.rosters[BEARS - 1][29] == pick
    league.check()
    tackle = league.chart[BEARS - 1]["RT"][0]
    RR.choose_starter(league, "LT", tackle)                                             # the other side of his family: he moves to left tackle
    assert league.players[tackle].position == "LT" and league.chart[BEARS - 1]["LT"][0] == tackle
    quarterback = league.chart[BEARS - 1]["QB"][1]
    with pytest.raises(Exception):
        RR.choose_starter(league, "WR", quarterback)                                    # a backup quarterback never starts at receiver
    text = league.to_json()
    again = LeagueRecord.from_json(text)
    assert again.chart[BEARS - 1]["LT"][0] == tackle and again.chart[BEARS - 1]["HB"][0] == league.chart[BEARS - 1]["HB"][0]


def test_a_chosen_halfback_gets_the_starters_share_of_20000_draws():
    league, _ = real_league()
    second = league.chart[BEARS - 1]["HB"][1]
    RR.choose_starter(league, "HB", second)
    roster = league.roster_for_game(BEARS)
    assert roster.running_backs[0] == league.players[second].name
    weights = usage.without_empty(usage.shares(usage.RUN), roster.empty, usage.RUNNING_BACKS)
    rnd = GameRandom(random.Random(9))
    hits = sum(1 for _ in range(20000) if usage.weighted_place(rnd, weights) == 1)
    assert abs(hits / 20000 - weights[0] / sum(weights)) < 0.015 and weights[0] == T.USAGE_RUN[0]


def test_in_a_quick_game_the_player_chooses_the_starter_at_every_position_from_the_current_rosters():
    real = R.defaults()
    depth: dict = {}
    chart, _roles, _squad = real.chart(BEARS)
    chosen = {}
    for position in RM.MADDEN:
        if len(chart[position]) < 2:
            continue
        name = chart[position][1]
        depth = DC.choose_starter(depth, real, BEARS, position, name)
        chosen[position] = name
    bench_receiver = chart["WR"][-1]
    depth = DC.choose_starter(depth, real, BEARS, "KR", bench_receiver)
    moved = DC.with_depth(real, depth)
    after, roles, _ = moved.chart(BEARS)
    for position, name in chosen.items():
        assert after[position][0] == name, position
    assert roles["KR"][0] == bench_receiver
    view = moved.view(BEARS)
    for position, index in FIRST_PLACE.items():
        if position in chosen:
            assert view.places[index] == chosen[position], position
    text = DC.render_depth(depth)
    assert DC.parse_depth(text) == depth and "T17 LT=" in text and "T17 KR=" in text
    tackle = chart["RT"][0]
    moved = DC.with_depth(real, DC.choose_starter({}, real, BEARS, "LT", tackle))
    assert moved.chart(BEARS)[0]["LT"][0] == tackle and tackle not in moved.chart(BEARS)[0]["RT"]
    with pytest.raises(ValueError):
        DC.choose_starter({}, real, BEARS, "WR", chart["QB"][1])


def test_an_older_depth_setting_by_group_is_read_through_the_conversion_table():
    real = R.defaults()
    chart, _r, _s = real.chart(BEARS)
    tackle = chart["DT"][1]
    old = {BEARS: {"DL": [tackle], "RB": [chart["HB"][1]], "RET": [chart["WR"][4]], "LT": [chart["LT"][0]]}}
    new = DC.migrate_depth(old, real)
    assert new == {BEARS: {"LT": [chart["LT"][0]], "DT": [tackle], "HB": [chart["HB"][1]], "KR": [chart["WR"][4]]}}
    assert DC.with_depth(real, old).chart(BEARS)[0]["DT"][0] == tackle                # the older form still works until SR.6's menus write the new one


# ----- a whole game on the view (design 21.11) -----

def test_a_whole_quick_game_of_the_real_rosters_never_gives_an_empty_back_place_the_ball(tmp_path, monkeypatch):
    from pagrig import make_rig
    from programrig import said
    from nfl4.extras import nfl_rules
    drawn = []
    original = nfl_rules.NflRules.draw_carrier

    def spy(self, state, rnd):
        result = original(self, state, rnd)
        roster = state.rosters.get(state.wisoff)
        drawn.append((usage.kind_of(state.offense_play), result, list(getattr(roster, "empty", ()))))
        return result

    monkeypatch.setattr(nfl_rules.NflRules, "draw_carrier", spy)
    rig = make_rig(tmp_path, fast=True)
    game = rig.game
    game.season.choose_team(5, 1)                                  # the Bears (T17) at home against the Eagles (T22)
    game.season.tn3, game.season.tn4 = 6, 2
    game.options.settings.game.rules = "nfl"
    game.apply_rules_setting()
    game.real_names = R.defaults()
    game.play_game()
    runs = [(place, empty) for kind, place, empty in drawn if kind == usage.RUN]
    assert len(runs) > 20 and all(("Running Backs:", place) not in empty for place, empty in runs)
    assert any(empty for _place, empty in runs)                   # both teams have empty back places (three and two backs)
    spoken = " ".join(said(rig))
    assert "Caleb Williams" in spoken                              # the real men of both teams play
    assert any(name in spoken for name in ("D'Andre Swift", "Kyle Monangai", "Roschon Johnson"))
