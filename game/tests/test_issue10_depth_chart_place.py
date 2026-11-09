"""GitHub issue 10 (Dennisl123 on 0.16.21, D-223): "Consider moving deapth Chart to either roster or Franchise. I think this would make more sense."
(nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

The depth chart left F9, Rules (where it was the 17th item) for F9, Franchise: "your depth chart" right after "your roster" while a franchise is played,
"Depth charts" (any of the 32 teams, for single games and classic seasons) as the Franchise menu's last item when none is; and the roster's Enter on a
man has "his place on the depth chart", his position's order with the list on him (U and N move him).
"""
import pytest

from frrig import COACH_AND_TEAM, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken
from programrig import DOWN, ENTER, ESC, said
from test_functions import rig_for
from test_lineup_sr6 import Keys, Speech, franchise, letter, real_league

from nfl4.extras import depth_chart as DC
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras.franchise import roster_flow
from nfl4.game.keys import KEY_END as END

FRANCHISE = [DOWN] * 4 + [ENTER]                 # F9's fifth item with the N. F. L. rules (Speech, Sounds, Customize, Rules, Franchise, About)
DEPTH_OUTSIDE = [END, ENTER]                     # the Franchise menu's last item when no franchise is played
INTO_FRANCHISE = [F9] + FRANCHISE
YOUR_DEPTH_CHART = [DOWN] * 3 + [ENTER]          # to do list, news, your roster, your depth chart
BENGALS = 1


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def menus_seen(monkeypatch):
    """(title, labels) of every SpokenMenu that opens."""
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append((title, [item.label() for item in items]))
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    return seen


def nfl_rig(tmp_path, keys):
    rig = rig_for(tmp_path, [])
    rig.game.options.settings.game.rules = "nfl"
    rig.game.apply_rules_setting()                       # issue 10: the game plays the N. F. L. rules, so F9 shows the Franchise item
    rig.game.real_names = R.defaults()
    rig.keys.answers = keys + [ESC] * 6
    rig.game.functions.run()
    return rig


# ----- the Rules menu has no depth chart any more -----

def test_the_rules_menu_has_seventeen_items_and_no_depth_charts(tmp_path, monkeypatch):
    seen = menus_seen(monkeypatch)
    nfl_rig(tmp_path, [DOWN, DOWN, DOWN, ENTER])
    labels = next(labels for title, labels in seen if title == X.text("NXM-07"))
    assert len(labels) == 17
    assert not any(X.text("NXM-D01") in label for label in labels)
    assert labels[-1] == X.text("NXM-19") and "uarterback" in labels[-2]


# ----- outside a franchise: Depth charts is the Franchise menu's last item -----

def test_outside_a_franchise_the_franchise_menu_ends_with_depth_charts(tmp_path, monkeypatch):
    seen = menus_seen(monkeypatch)
    rig = nfl_rig(tmp_path, FRANCHISE + DEPTH_OUTSIDE)
    labels = next(labels for title, labels in seen if title == X.text("NXF-10"))
    assert labels[-1] == X.text("NXM-D01") and labels[-2] == X.text("NXZ-U01")
    assert X.text("NXM-D02") in " ".join(said(rig)) or any(X.text("NXM-D02").strip() in t for t in said(rig))


def test_outside_a_franchise_enter_on_a_player_makes_him_the_starter_as_before(tmp_path):
    # the Bengals, the halfbacks (the third item after the lineup and the quarterbacks), the second halfback
    rig = nfl_rig(tmp_path, FRANCHISE + DEPTH_OUTSIDE + [ENTER, DOWN, DOWN, ENTER, DOWN, ENTER])
    settings = rig.game.options.settings.game
    assert DC.parse_depth(settings.nx_depth)[BENGALS]["HB"][0] == "Samaje Perine"
    assert X.text("NXM-L68", player="Samaje Perine", position="halfback") in said(rig)


# ----- in a franchise: your depth chart right after your roster -----

def test_in_a_franchise_your_depth_chart_is_the_item_after_your_roster(tmp_path, monkeypatch):
    seen = menus_seen(monkeypatch)
    rig = run_until(franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + INTO_FRANCHISE + YOUR_DEPTH_CHART, policy=quit_policy))
    labels = next(labels for title, labels in seen if title == X.text("NXF-10"))
    assert labels[2:5] == [X.text("NXF-13"), X.text("NXF-57"), X.text("NXF-14")]
    assert X.text("NXM-D01") not in labels                         # the 32 teams' item is only outside a franchise
    league = rig.fstore.league
    title = X.text("NXM-D03", team=rig.fstore.words.team_name(league.team)).strip()
    assert any(title in t for t in spoken(rig))


def test_in_a_franchise_your_depth_chart_opens_a_positions_list_as_before(tmp_path):
    # the lineup is the first item, the quarterbacks the second: Enter lists who may start at quarterback, with the move keys said
    keys = WANT_FRANCHISE + COACH_AND_TEAM + INTO_FRANCHISE + YOUR_DEPTH_CHART + [DOWN, ENTER]
    rig = run_until(franchise_rig(tmp_path, keys, policy=quit_policy))
    title = (X.text("NXM-L37", position="quarterback") + X.text("NXM-R01")).strip()
    assert any(t.strip().startswith(title) for t in spoken(rig))


# ----- the roster: his place on the depth chart -----

def test_the_roster_offers_his_place_on_the_depth_chart_before_his_name():
    league = real_league()
    game, store = franchise(league)
    speech = Speech()
    qb = league.players[league.chart[league.team - 1]["QB"][1]]
    section = next(s for s in roster_flow.sections_of(game, store) if s.key == "QB")
    roster_flow.man_items(game, speech, Keys(DOWN, DOWN, ESC), store, section, qb)
    assert X.text("NXM-L92").strip() in speech.said[1]
    assert X.text("NXM-L29").strip() in speech.said[2]


def test_his_place_opens_his_positions_order_on_him_and_u_moves_him_up():
    league = real_league()
    game, store = franchise(league)
    speech = Speech()
    chart = league.chart[league.team - 1]
    starter = league.players[chart["QB"][0]]
    third = league.players[chart["QB"][2]]
    second = league.players[chart["QB"][1]]
    section = next(s for s in roster_flow.sections_of(game, store) if s.key == "QB")
    roster_flow.man_items(game, speech, Keys(DOWN, ENTER, letter("u"), ESC), store, section, third)
    opened = speech.said[2]
    first_line = opened.split("Press F1 for help.")[-1]
    assert X.text("NXM-R01").strip() in opened and third.name in first_line and starter.name not in first_line     # the list starts on him
    chart = league.chart[league.team - 1]                     # the move writes a new chart
    assert chart["QB"][:3] == [starter.id, third.id, second.id]
    assert store.saves == 1
    assert X.text("NXM-R07", player=third.name, n=2, position="quarterback", other=second.name) in speech.said


def test_his_place_is_refused_during_a_game():
    league = real_league()
    game, store = franchise(league, playing=True)
    speech = Speech()
    before = list(league.chart[league.team - 1]["QB"])
    qb = league.players[before[1]]
    section = next(s for s in roster_flow.sections_of(game, store) if s.key == "QB")
    result = roster_flow.man_items(game, speech, Keys(DOWN, ENTER), store, section, qb)
    assert result == X.text("NXI-54")
    assert league.chart[league.team - 1]["QB"] == before


# ----- the help and the documents name the new place -----

def test_the_help_and_the_documents_name_f9_franchise_not_f9_rules():
    from pathlib import Path
    from nfl4.game import key_list
    assert "F9, Franchise" in X.text("NXH-79") and "Rules" not in X.text("NXH-79")
    assert "your depth chart" in X.text("NXH-34") and "your depth chart" in X.text("NXH-82")
    rows = [row for row in key_list.ROWS if row.id in ("lineup", "describe_position", "depth_move")]
    assert len(rows) == 3 and all("F9, Franchise" in row.where and "Rules" not in row.where for row in rows)
    game = Path(__file__).resolve().parents[1]
    for name in ("README_keys.md", "README_nfl_rules_and_franchise.md", "CUSTOMIZE.md", "PLAYS_GUIDE.md"):
        assert "F9, Rules, Depth charts" not in (game / name).read_text(encoding="utf-8"), name
