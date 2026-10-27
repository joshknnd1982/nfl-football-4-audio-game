"""The owner's report of 2026-10-26 (nfl4 only, rule 0.13): "it doesn't have all free agents example is kicker" (D-169) and "it doesn't have the depth
charts right. Example the Giants started J.J Macarthy" (D-170). This is inspired by Jim Kitchen.

D-169: free_agents.txt is the whole real pool (nflverse's players table: on a roster this season or the one before, not retired, on no team; Sleeper
agrees), every position with the kicker, the punter and the long snapper; update_rosters.py makes it.
D-170: the staff's depth order keeps a real starter until a man is clearly better (FR_DEPTH_HOLD; a newcomer FR_DEPTH_HOLD_NEW), so a point or two of the
game's own ratings never gives J.J. McCarthy (traded to the Giants on 2026-09-28, Jameis Winston's backup) the Giants' job.
"""
import importlib.util
import random
import sys
from pathlib import Path

import pytest

from nfl4.data import customize
from nfl4.extras import nfl_surnames
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

TOOL = Path(__file__).resolve().parent.parent / "tools" / "update_rosters.py"
GIANTS = 23


def _tool():
    if "update_rosters" in sys.modules:
        return sys.modules["update_rosters"]
    spec = importlib.util.spec_from_file_location("update_rosters", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["update_rosters"] = module          # a dataclass looks up its module while the class is made
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None
    yield
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None


def real_league(seed=3, team=17):
    return new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=R.defaults())


# ----- D-169: the whole pool of real free agents -----

def test_the_shipped_free_agents_are_the_whole_pool_with_kickers_punters_and_snappers():
    real = R.defaults()
    agents = [agent for _ident, agent in real.free_agents]
    by = {}
    for a in agents:
        by.setdefault(a.pos, []).append(a.name)
    assert len(agents) >= 700
    assert len(by["K"]) >= 10 and len(by["P"]) >= 5 and len(by["LS"]) >= 5 and len(by["OL"]) >= 100 and len(by["QB"]) >= 20
    assert {"Younghoe Koo", "Cade York", "Greg Joseph", "Matt Prater", "Graham Gano", "Justin Tucker"} <= set(by["K"])    # D-172: Tucker, out in 2025
    assert "Taylor Heinicke" in by["QB"] and "Derek Carr" not in by["QB"] and "Tom Brady" not in by["QB"]               # retired men are not free
    assert {"Johnny Hekker", "Thomas Morstead"} <= set(by["P"])
    on_teams = {p.name.casefold() for team in range(1, 33) for p in real.rosters[team - 1]}
    assert not [a.name for a in agents if a.name.casefold() in on_teams]
    assert len({a.name.casefold() for a in agents}) == len(agents)
    assert all(R.name_problem(a.name) is None and a.pos in R.POSITIONS and a.pos != "RET" for a in agents)
    text = R.shipped_text(R.FREE_AGENTS)
    assert "wait for a later version" not in text and "on an NFL roster this season or last season" in text


def test_a_new_franchise_offers_the_real_kickers_and_snappers_and_makes_up_no_kicker():
    real = R.defaults()
    record = real_league()
    S.ensure_pool(record, nfl_surnames.pool(), real)
    names = {real.spoken(a.name) for _i, a in real.free_agents}
    kickers = S.pool_of(record, "K")
    assert len(kickers) >= 10 and all(p.name in names for p in kickers)
    assert "Younghoe Koo" in {p.name for p in kickers}
    snappers = S.pool_of(record, "LS")
    assert len(snappers) >= 5 and all(p.name in names for p in snappers)


def test_the_script_takes_the_real_pool_and_leaves_out_the_retired_the_signed_and_the_long_gone():
    U = _tool()
    csv_text = ("gsis_id,display_name,position,status,last_season,latest_team,birth_date\n"
                "1,Free Kicker,K,CUT,2026,NYG,1994-08-03\n"
                "2,Old Kicker,K,ACT,2023,BUF,1984-08-10\n"
                "3,Retired Punter,P,RET,2025,ARI,1990-01-01\n"
                "4,Signed Snapper,LS,CUT,2026,NO,1998-07-09\n"
                "5,Free Snapper,LS,DEV,2025,PHI,1990-05-16\n"
                "6,Free Tackle,OT,CUT,2025,DET,1996-04-04\n"
                "7,Free Back,DB,CUT,2025,DAL,1999-02-02\n"
                "8,Ghost Man,WR,CUT,2025,DAL,1999-02-02\n")
    sl_free = [{"full_name": n, "birth_date": b, "position": pos} for n, b, pos in (
        ("Free Kicker", "1994-08-03", "K"), ("Old Kicker", "1984-08-10", "K"), ("Retired Punter", "1990-01-01", "P"),
        ("Free Snapper", "1990-05-16", "LS"), ("Free Tackle", "1996-04-04", "OL"), ("Free Back", "1999-02-02", "S"))]
    on_team = U.Matcher(["Signed Snapper"])
    pool = U.free_agent_pool(csv_text.encode("utf-8"), on_team, sl_free, "2026-10-25")
    assert [(p, n) for p, _a, n in pool] == [("OL", "Free Tackle"), ("S", "Free Back"), ("K", "Free Kicker"), ("LS", "Free Snapper")]
    assert dict((n, a) for _p, a, n in pool)["Free Kicker"] == "32"
    assert U.free_agent_pool(None, on_team, sl_free, "2026-10-25") == []


def test_a_man_out_a_whole_season_is_free_only_while_he_is_in_the_news_and_a_settled_retiree_never():
    U = _tool()
    csv_text = ("gsis_id,display_name,position,status,last_season,latest_team,birth_date\n"
                "1,Quiet Kicker,K,ACT,2024,BAL,1989-11-21\n"
                "2,News Kicker,K,ACT,2024,BAL,1989-11-21\n"
                "3,Derek Carr,QB,ACT,2024,NO,1991-03-28\n"
                "4,Gone Long,K,ACT,2023,BAL,1989-11-21\n")
    recent, old = 1792519541008, 1701970258455                        # 2026-10 and 2023-12, in Sleeper's milliseconds
    sl_free = [{"full_name": "Quiet Kicker", "news_updated": old}, {"full_name": "News Kicker", "news_updated": recent},
               {"full_name": "Derek Carr", "news_updated": recent}, {"full_name": "Gone Long", "news_updated": recent}]
    pool = U.free_agent_pool(csv_text.encode("utf-8"), U.Matcher([]), sl_free, "2026-10-25")
    assert [n for _p, _a, n in pool] == ["News Kicker"]
    assert U.name_key("Derek Carr") in U.read_fa_settlements(U.FA_SETTLEMENTS.read_bytes().decode("utf-8"))


def test_the_refresh_adds_the_pool_after_the_old_ids_and_writes_the_new_header():
    U = _tool()
    import nfl4.extras.roster_file as RF
    csv_text = "gsis_id,display_name,position,status,last_season,latest_team,birth_date\n1,Free Kicker,K,CUT,2026,NYG,1994-08-03\n"
    old = "# old header: OL and LS players wait for a later version.\nVERSION = season 2026, as of 2026-10-24\nF001 = WR 32 Tyreek Hill\n"
    sl_free = [{"full_name": "Free Kicker", "birth_date": "1994-08-03"}, {"full_name": "Tyreek Hill", "birth_date": "1994-03-01"}]
    text, removed, added = U.refresh_free_agents(old, {}, {3: RF.Team(men=[])}, sl_free, {}, "2026-10-25", csv_text.encode("utf-8"))
    assert removed == [] and added == ["Free Kicker"]
    assert "F001 = WR 32 Tyreek Hill" in text and "F002 = K 32 Free Kicker" in text
    assert "wait for a later version" not in text and text.startswith(U.FA_HEADER[0])


def test_a_players_copy_of_the_older_shipped_list_is_refreshed():
    assert "48b1300b1a6c8b3b08134af599c73e3adc53d2a9025d9aa4b272d86225ca9304" in customize.OLD_SHIPPED_FREE_AGENTS     # 0.16.2 to 0.16.4
    assert "d44f6dd5f1c63fa74819cd551ceb5a1f8f68574dbbbb970b13875f75567f68fa" in customize.OLD_SHIPPED_FREE_AGENTS     # 0.16.5
    assert "94aae97409bbf27e44177d4b82714b5a4dc53b316a06d555f681383f9d42ec0a" in customize.OLD_SHIPPED_FREE_AGENTS     # 0.16.6 (D-177)
    assert "1ce8a093c45f139b2df35c190d92d1816aba61dea496dea022618651cb51c4ed" in customize.OLD_SHIPPED_ROSTERS         # 0.16.3 to 0.16.6


# ----- D-170: the staff keeps a real starter until a man is clearly better -----

def test_the_giants_start_jj_mccarthy_and_a_few_points_never_give_winston_the_job():
    """D-177 (the tester, 2026-10-26: "Winston is not the Giants starter at QB"): the file of 2026-10-26 starts McCarthy, named the starter on
    2026-10-21; D-170's hold keeps him."""
    record = real_league()
    chart = record.chart[GIANTS - 1]
    mccarthy, winston = (record.players[pid] for pid in chart["QB"][:2])
    assert (mccarthy.name, winston.name) == ("J.J. McCarthy", "Jameis Winston")
    assert record.player_at(GIANTS, D.PLACES_OF["QB"][0]) is mccarthy
    winston.rating = mccarthy.rating + T.FR_DEPTH_HOLD["QB"] - 1
    RR.refresh_view(record, GIANTS)
    assert record.chart[GIANTS - 1]["QB"][0] == mccarthy.id and record.player_at(GIANTS, D.PLACES_OF["QB"][0]) is mccarthy
    winston.rating = mccarthy.rating + T.FR_DEPTH_HOLD["QB"]
    RR.refresh_view(record, GIANTS)
    assert record.chart[GIANTS - 1]["QB"][0] == winston.id            # clearly better: the staff starts him


def test_every_position_keeps_its_order_within_the_hold_and_a_newcomer_needs_his_own_margin():
    record = real_league()
    team = 5
    chart = record.chart[team - 1]
    first, second = (record.players[pid] for pid in chart["WR"][:2])
    second.rating = first.rating + T.FR_DEPTH_HOLD["*"] - 1
    assert RR.order_position(record, team, "WR", list(chart["WR"]))[0] == first.id
    second.rating = first.rating + T.FR_DEPTH_HOLD["*"]
    assert RR.order_position(record, team, "WR", list(chart["WR"]))[0] == second.id
    second.rating = first.rating + T.FR_DEPTH_HOLD_NEW
    ids = [i for i in chart["WR"] if i != second.id] + [second.id]       # he joins the chart now, at its end
    assert RR.order_position(record, team, "WR", ids, new={second.id})[0] == second.id
    second.rating = first.rating + T.FR_DEPTH_HOLD_NEW - 1
    assert RR.order_position(record, team, "WR", ids, new={second.id})[0] == first.id
    assert 1 < T.FR_DEPTH_HOLD_NEW < T.FR_DEPTH_HOLD["*"] < T.FR_DEPTH_HOLD["QB"]


def test_a_new_franchise_starts_every_real_starter_of_the_file_and_a_refresh_changes_nobody():
    record = real_league()
    before = [{pos: list(ids) for pos, ids in record.chart[t - 1].items()} for t in range(1, D.TEAMS + 1)]
    RR.refresh_all(record)
    after = [{pos: list(ids) for pos, ids in record.chart[t - 1].items()} for t in range(1, D.TEAMS + 1)]
    assert before == after
