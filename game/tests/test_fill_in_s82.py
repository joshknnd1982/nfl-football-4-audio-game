"""S8.2 (an e-mail report of 2026-10-26 the owner made his own: "at some positions it has no one starting. Go through a depth chart and you'll see what
I mean."; B-P189): every place of every team's lineup and depth chart names the man who plays there, in a quick game and in a franchise. A 3-4 team has
no strong-side linebacker, many teams have no fullback, a team's only kicker can be on the practice squad: a spare man of the family fills in, said as
such, and the chart keeps every man at his own position (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.
"""
import random
from types import SimpleNamespace

import pytest

from nfl4.extras import depth_flow
from nfl4.extras import lineup as L
from nfl4.extras import nfl_surnames
from nfl4.extras import quarterbacks as Q
from nfl4.extras import real_names as R
from nfl4.extras import roster_model as RM
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

ALL = range(1, 33)


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None
    yield
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None


def quick_game():
    settings = SimpleNamespace(nx_depth="", nx_qb_starters="", nx_key_players="")
    game = SimpleNamespace(options=SimpleNamespace(settings=SimpleNamespace(game=settings), save=lambda: None), customization=None, real_names=None,
                           play_engine=None)
    game.real_names = R.defaults()
    Q.apply(game)
    return game


def franchise_backend(team):
    league = new_league(GameRandom(random.Random(3)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=R.defaults())
    store = SimpleNamespace(league=league, saves=0, save=lambda: None, words=SimpleNamespace(team_name=lambda t: str(t)))
    return L.FranchiseBackend(SimpleNamespace(play_engine=None), store)


def backends():
    game = quick_game()
    for team in ALL:
        yield "quick", team, L.QuickBackend(game, team, str(team))
    for team in ALL:
        yield "franchise", team, franchise_backend(team)


def test_no_lineup_line_and_no_depth_chart_item_says_nobody_on_any_team():
    empty = []
    for mode, team, backend in backends():
        for key, slot in backend.slots():
            line = L.lineup_line(backend, key, slot)
            if "nobody" in line:
                empty.append((mode, team, line.strip()))
        for key in L.KEYS:
            item = depth_flow._first_label(backend, key)
            if "nobody" in item:
                empty.append((mode, team, item))
    assert empty == []


def test_a_man_who_fills_in_plays_one_place_and_keeps_his_own_position():
    for mode, team, backend in backends():
        seen = {}
        for key, slot in L.LINEUP:
            if key in RM.ROLES:
                continue
            found = backend.starters(key)
            man = found[slot] if slot < len(found) else None
            how = ""
            if man is None:
                fill = backend.fill(key, slot)
                assert fill is not None, (mode, team, key, slot)
                man, own, how = fill
                assert own == man.position                       # the chart is not changed
                if how in ("family", "cover"):
                    assert own != key
                if how == "family":
                    assert RM.family_of(own) == RM.family_of(key)  # never another family on offense
            if how != "kicker":
                assert man.key not in seen, (mode, team, key, seen.get(man.key))
                seen[man.key] = key


def test_a_three_four_team_says_who_plays_strong_side_linebacker():
    game = quick_game()
    teams = [t for t in ALL if not L.QuickBackend(game, t, "").starters("SAM")]
    assert len(teams) >= 10                                     # 19 teams on the rosters of 2026-10-25
    for team in teams:
        backend = L.QuickBackend(game, team, "")
        line = L.lineup_line(backend, "SAM", 0)
        assert "filling in from" in line and ("linebacker" in line.split("filling in from")[1] or "edge" in line.split("filling in from")[1])


def test_a_kicker_only_on_the_practice_squad_is_said_as_brought_up_for_game_day():
    game = quick_game()
    teams = [t for t in ALL if not L.QuickBackend(game, t, "").starters("K") and L.QuickBackend(game, t, "").squad_men("K")]
    for team in teams:
        backend = L.QuickBackend(game, team, "")
        squad_kicker = backend.squad_men("K")[0]
        assert squad_kicker.name in L.lineup_line(backend, "K", 0)
        assert "practice squad for game day" in L.lineup_line(backend, "K", 0)
        assert "practice squad" in depth_flow._first_label(backend, "K")


def test_fill_ins_rules_without_the_rosters():
    chart = {p: [] for p in RM.MADDEN}
    chart.update({"MIKE": ["m1"], "WILL": ["w1"], "LEDG": ["l1", "l2"], "REDG": ["r1"], "HB": ["h1", "h2"], "P": ["p1"]})
    places = [("FB", 0), ("SAM", 0), ("MIKE", 0), ("K", 0), ("P", 0)]
    got = RM.fill_ins(chart, {}, places)
    assert got[("FB", 0)] == ("h2", "HB", "family")              # the second halfback, never the starter
    assert got[("SAM", 0)] == ("l2", "LEDG", "cover")            # no spare backer: a spare edge man, as the game's places do
    assert ("MIKE", 0) not in got
    assert got[("K", 0)] == ("p1", "P", "kicker")                # the punter kicks
    assert RM.fill_ins(chart, {"K": ["k9"]}, places)[("K", 0)] == ("k9", "K", "squad")
    assert chart["HB"] == ["h1", "h2"]                           # the chart is not changed
    alone = {p: [] for p in RM.MADDEN}
    alone["QB"] = ["q1"]
    assert RM.fill_ins(alone, {}, [("HB", 0), ("LT", 0)]) == {}  # nobody fits: nobody, never a quarterback at halfback


def test_choosing_the_man_who_fills_in_makes_him_the_starter_there():
    game = quick_game()
    team = next(t for t in ALL if not L.QuickBackend(game, t, "").starters("SAM"))
    backend = L.QuickBackend(game, team, "")
    man, own, _how = backend.fill("SAM", 0)
    text = backend.choose("SAM", man, 0)
    assert man.name in text
    after = L.lineup_line(backend, "SAM", 0)
    assert man.name in after and "filling in" not in after
