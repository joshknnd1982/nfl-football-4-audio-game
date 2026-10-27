"""NX-D3 and NX-D4 (the owner's second report of 2026-10-24, D-147, CLAUDE.md 0.30): set your starters, and your players for the key downs and moments
(nfl4 only, rule 0.13). F9, Rules, Depth charts: any team outside a franchise (the settings nx_depth and nx_key_players), the player's own team in a
franchise (league.sav format 16). The named man of a key situation takes CHOSEN_PLAYER_SHARE of his group's draw there.
"""
import json
import random
from types import SimpleNamespace

import pytest
from drrig import SURNAMES
from programrig import DOWN, ENTER, ESC, said
from test_functions import rig_for

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import depth_chart as DC
from nfl4.extras import nx_texts as X
from nfl4.extras import quarterbacks as Q
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import aging
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import depth as FD
from nfl4.extras.franchise.league import LeagueError, new_league
from nfl4.game.rnd import GameRandom
from nfl4.game.setup import Roster

RULES = [DOWN, DOWN, DOWN, ENTER]                        # F9's fourth item
DEPTH = [DOWN] * 14 + [ENTER]                            # the Rules menu's fifteenth item, after Quarterbacks (S-D: How much the crew talks is 11)
BENGALS, BILLS = 1, 5


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def real():
    return R.defaults()


# ----- the settings and the order laid over the names -----

def test_the_settings_read_and_write_by_name_and_skip_what_is_not_a_choice():
    text = "T05 RB=Ray Davis; T05 WR=Khalil Shakir,DJ Moore; T40 RB=Nobody; T05 XX=Ray Davis; nonsense"
    assert DC.parse_depth(text) == {5: {"RB": ["Ray Davis"], "WR": ["Khalil Shakir", "DJ Moore"]}}
    assert DC.clean_depth(text) == "T05 RB=Ray Davis; T05 WR=Khalil Shakir,DJ Moore"
    keys = "T05 redzone receiver=Dalton Kincaid; T05 down back=James Cook III; T05 nowhere back=X"
    assert DC.parse_keys(keys) == {5: {("redzone", "receiver"): "Dalton Kincaid", ("down", "back"): "James Cook III"}}
    assert DC.clean_keys(keys) == "T05 down back=James Cook III; T05 redzone receiver=Dalton Kincaid"


def test_the_settings_file_keeps_both(tmp_path):
    s = Settings.defaults()
    s.game.nx_depth, s.game.nx_key_players = "T05 RB=Ray Davis", "T05 redzone receiver=Dalton Kincaid"
    text = settingsfile.render(s)
    assert "nx_depth = T05 RB=Ray Davis\n" in text and "nx_key_players = T05 redzone receiver=Dalton Kincaid\n" in text
    again, problems = settingsfile.parse(text)
    assert again.game.nx_depth == "T05 RB=Ray Davis" and again.game.nx_key_players == "T05 redzone receiver=Dalton Kincaid" and problems == []
    bad, problems = settingsfile.parse(settingsfile.HEADER + "nx_depth = whoever\n")
    assert problems and bad.game.nx_depth == ""


def test_a_chosen_order_reaches_the_set_up():
    names = real()
    moved = DC.with_depth(names, {BILLS: {"RB": ["Ray Davis"], "WR": ["Khalil Shakir"], "RET": ["James Cook III"]}})
    roster = moved.roster(BILLS, None)
    assert roster.running_backs[0] == "Ray Davis" and roster.running_backs[1] == names.spoken("James Cook III")
    assert roster.receivers[0] == "Khalil Shakir"
    assert roster.special_teams[0] == names.spoken("James Cook III")         # SR.4 (D-161): a returner may also hold his back place in a game
    assert DC.with_depth(names, {}) is names
    assert DC.group_players(moved, BILLS, "RB")[0].name == "Ray Davis"


def test_put_first_keeps_an_earlier_choice_behind_the_new_one():
    depth = DC.put_first({}, BILLS, "WR", "Khalil Shakir", ["DJ Moore", "Khalil Shakir", "Keon Coleman"])
    depth = DC.put_first(depth, BILLS, "WR", "Keon Coleman", depth[BILLS]["WR"])
    assert depth[BILLS]["WR"][:3] == ["Keon Coleman", "Khalil Shakir", "DJ Moore"]
    assert DC.reset_team(depth, BILLS) == {}


# ----- the key downs and moments -----

def state(down=1, yard_line=50, quarter=1, left=900, wisoff=1, half=1):
    roster = Roster(["Back%d" % n for n in range(1, 7)], ["Rec%d" % n for n in range(1, 7)], ["D%d" % n for n in range(17)], ["R1", "R2"],
                    ["K", "P"])
    return SimpleNamespace(down=down, yard_line=yard_line, quarter=quarter, wisoff=wisoff, half=half, rosters={1: roster},
                           extras=SimpleNamespace(left=left), qb_run="")


@pytest.mark.parametrize("values, want", [(dict(down=3), "down"), (dict(down=4), "down"), (dict(quarter=2, left=100), "twominute"),
                                          (dict(quarter=1, left=100), None), (dict(), None)])
def test_the_key_situations(values, want):
    s = state(**values)
    assert DC.situation_of(s, 60, s.extras.left) == want
    assert DC.situation_of(state(), 15, 900) == "redzone"


def test_the_player_named_for_a_key_situation_gets_his_share():
    game = SimpleNamespace(franchise_in_use=False, real_names=real(), season=SimpleNamespace(tn1=1, tn2=1),
                           options=SimpleNamespace(settings=SimpleNamespace(game=SimpleNamespace(nx_key_players="T01 down receiver=Rec4"))))
    real_spoken = game.real_names.spoken
    game.real_names = SimpleNamespace(spoken=lambda n: real_spoken(n))
    from nfl4.extras.usage import PASS, RUN
    assert DC.key_place_for(game, state(down=3), PASS) == 4
    assert DC.key_place_for(game, state(down=1), PASS) is None                  # not a key situation
    assert DC.key_place_for(game, state(down=3), RUN) is None                   # no back named
    assert DC.key_place_for(game, state(down=3, wisoff=2), PASS) is None        # the other team's offense


# ----- F9, Rules, Depth charts outside a franchise -----

def nfl_rig(tmp_path, keys):
    rig = rig_for(tmp_path, [])
    rig.game.options.settings.game.rules = "nfl"
    rig.game.real_names = real()
    rig.keys.answers = RULES + DEPTH + keys + [ESC, ESC, ESC, ESC]
    rig.game.functions.run()
    return rig


def test_enter_on_a_player_makes_him_the_starter_and_the_next_game_uses_him(tmp_path):
    # SR.6: the menu is the starting lineup, then the 22 positions (QB first, HB second): the Bengals, the halfbacks, the second halfback
    rig = nfl_rig(tmp_path, [ENTER, DOWN, DOWN, ENTER, DOWN, ENTER])
    settings = rig.game.options.settings.game
    group = DC.parse_depth(settings.nx_depth)[BENGALS]["HB"]
    assert group[0] == "Samaje Perine" and rig.saves.count == 1
    assert rig.game.real_names.roster(BENGALS, None).running_backs[0] == "Samaje Perine"
    assert X.text("NXM-L68", player="Samaje Perine", position="halfback") in said(rig)       # SR.6: the choice is said with the position (NXM-L68)


def test_key_downs_and_moments_set_and_clear(tmp_path):
    # SR.6: key downs and moments follow the lineup and the 24 positions and roles (item 25)
    rig = nfl_rig(tmp_path, [ENTER] + [DOWN] * 25 + [ENTER, DOWN, ENTER, DOWN, ENTER])   # the Bengals, key downs, third down the receiver, the first receiver
    settings = rig.game.options.settings.game
    chosen = DC.parse_keys(settings.nx_key_players)[BENGALS]
    assert list(chosen) == [("down", "receiver")]
    assert any(X.text("NXM-K10", situation=X.text("NXM-K05"), player=rig.game.real_names.spoken(chosen[("down", "receiver")])) == t for t in said(rig))


def test_the_real_order_again(tmp_path):
    rig = rig_for(tmp_path, [])
    rig.game.options.settings.game.rules = "nfl"
    rig.game.options.settings.game.nx_depth = "T01 HB=Samaje Perine"                    # SR.6: keyed by position
    rig.game.options.settings.game.nx_key_players = "T01 down back=Samaje Perine"
    Q.apply(rig.game) if rig.game.real_names is not None else None
    rig.game.real_names = DC.with_depth(real(), DC.parse_depth("T01 HB=Samaje Perine"))
    rig.keys.answers = RULES + DEPTH + [ENTER] + [DOWN] * 26 + [ENTER, ESC, ESC, ESC, ESC]
    rig.game.functions.run()
    assert rig.game.options.settings.game.nx_depth == "" and rig.game.options.settings.game.nx_key_players == ""
    assert X.text("NXM-D11", team=rig.game.league.team(1, 1)) in said(rig)


# ----- in a franchise -----

def league():
    return new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", BILLS, "20260101-000000", real=real())


def test_a_new_franchise_gives_each_groups_best_rating_to_its_real_starter():
    # SR.5 (D-164): the order is the chart's, by POSITION (a group of places such as DL mixes edges and tackles, each in its own chart's order)
    from nfl4.extras.roster_model import MADDEN
    record = league()
    for team in (1, 5, 17):
        for position in MADDEN:
            ratings = [record.players[pid].rating for pid in record.chart[team - 1].get(position, ())]
            assert ratings == sorted(ratings, reverse=True), (team, position)
    assert record.player_at(BILLS, D.PLACES_OF["RB"][0]).name == real().spoken("James Cook III")
    assert record.players[record.chart[BILLS - 1]["HB"][0]].name == real().spoken("James Cook III")


def test_the_players_order_holds_through_the_staffs_sort():
    # SR.5 (D-164): the player's order is kept by POSITION (the running backs' item puts a halfback first of the HB chart)
    record = league()
    halfbacks = list(record.chart[BILLS - 1]["HB"])
    assert len(halfbacks) >= 3
    FD.put_first(record, "RB", halfbacks[2])
    assert FD.group_of(record, "RB")[0].id == halfbacks[2] and record.depth["order"]["HB"][0] == halfbacks[2]
    assert record.chart[BILLS - 1]["HB"][0] == halfbacks[2]
    aging.place_by_rating(record, BILLS)
    assert FD.group_of(record, "RB")[0].id == halfbacks[2]                     # the staff's sort keeps the player's order
    aging.place_by_rating(record, 1)                                           # another team: the best first
    FD.reset(record)
    assert record.depth == {"order": {}, "key": {}} and FD.group_of(record, "RB")[0].id == halfbacks[0]
    with pytest.raises(LeagueError):
        FD.put_first(record, "RB", record.player_at(1, 0).id)


def test_the_league_file_keeps_the_depth_chart_and_checks_it():
    record = league()
    FD.set_key(record, "redzone", "receiver", record.player_at(BILLS, D.PLACES_OF["WR"][3]).id)
    FD.put_first(record, "WR", record.player_at(BILLS, D.PLACES_OF["WR"][2]).id)
    data = json.loads(record.to_json())
    assert data["format"] == 19 == D.FORMAT and data["depth"]["key"]["redzone"]["receiver"] == record.player_at(BILLS, D.PLACES_OF["WR"][3]).id      # SR.5: format 19
    whole = lambda value, lo, hi, what: None if isinstance(value, int) and lo <= value <= hi else (_ for _ in ()).throw(LeagueError(what))  # noqa: E731
    FD.check(record, whole)
    record.depth["key"]["nowhere"] = {}
    with pytest.raises(LeagueError):
        FD.check(record, whole)
    FD.set_key(record, "redzone", "receiver", None)
    assert "redzone" not in record.depth["key"]


def test_in_a_franchise_the_menu_orders_the_players_own_team_and_saves_it(tmp_path):
    from frrig import COACH_AND_TEAM, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + [F9] + RULES + DEPTH + [DOWN, DOWN, ENTER, DOWN, ENTER, ESC, ESC, ESC, ESC],
                        policy=quit_policy)
    run_until(rig)
    record = rig.fstore.league
    first = FD.group_of(record, "RB")[0]
    assert record.depth["order"][first.position][0] == first.id              # SR.5 (D-164): the order is kept by position (HB)
    assert X.text("NXM-L68", player=first.name, position="halfback") in spoken(rig)         # SR.6: NXM-L68 names the position
    from nfl4.extras.franchise.league import LeagueRecord
    saved = LeagueRecord.from_json(rig.files.data["league.sav"].decode("utf-8"))
    assert saved.depth == record.depth
