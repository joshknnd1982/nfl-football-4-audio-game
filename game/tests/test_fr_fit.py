"""The computer teams' playbooks follow their best players, and the game's later items never reach a game outside a franchise (nfl4 only, rule 0.13;
NFL_FRANCHISE_DESIGN 17 SX.8o, research B8, D-076). The lean of a lineup (the passing rating against the backs', the front against the backs of the
defense), the styles it fits, the week's styles of a franchise (the player's own are his coordinators'), and the traces of a quick game and of a classic
season (both Rules values) with every new rule made to raise (INJ-1 and design 1.3 for the new items).
"""
import random

import pytest
from drrig import SURNAMES
from frrig import COACH_AND_TEAM, ENTER, franchise_rig, quit_policy, run_until, spoken

from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import honors as H
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import staff as S
from nfl4.extras.franchise import workload as W
from nfl4.extras.franchise.league import new_league
from nfl4.game.rnd import GameRandom

TEAM = 5


def table(qb=70, rb=70, wr=70, front=70, cover=70):
    out = []
    for index, position in enumerate(D.POSITION_OF_PLACE):
        rating = {"QB": qb, "RB": rb, "WR": wr, "DL": front, "LB": front, "CB": cover, "S": cover}.get(position, 70)
        out.append((index + 1, "N", rating))
    return out


def test_an_even_lineup_leans_nowhere_and_keeps_its_coordinators_styles():
    assert S.lean(table()) == (0, 0)
    assert S.fit(table(), "zone", "option") == ("zone", "option")


def test_a_lineup_leans_to_the_pass_at_the_gap_and_not_a_point_under_it():
    gap = T.FR_FIT_GAP
    # passing = (2 x qb + 70) / 3; running = 70: the passing rating is gap over at qb = 70 + 1.5 x gap
    assert gap == 5                                       # the hand-worked points below are for a gap of 5
    assert S.lean(table(qb=77))[0] == 0                   # passing (154 + 70) / 3 = 74.67: 4.67 over the backs, a point under the gap
    assert S.lean(table(qb=78))[0] == 1                   # (156 + 70) / 3 = 75.33: 5.33 over
    assert S.lean(table(rb=70 - gap))[0] == 1 and S.lean(table(rb=70 - gap + 1))[0] == 0
    assert S.lean(table(rb=70 + gap))[0] == -1 and S.lean(table(rb=70 + gap - 1))[0] == 0
    assert S.fit(table(rb=70 - gap), "pro", "pro") == (T.FR_FIT_STYLES["pass"], "pro")
    assert S.fit(table(rb=70 + gap), "air", "pro") == (T.FR_FIT_STYLES["run"], "pro")


def test_a_defense_leans_to_the_rush_or_the_cover_at_the_gap():
    gap = T.FR_FIT_GAP
    assert S.lean(table(front=70 + gap))[1] == 1 and S.lean(table(front=70 + gap - 1))[1] == 0
    assert S.lean(table(cover=70 + gap))[1] == -1 and S.lean(table(cover=70 + gap - 1))[1] == 0
    assert S.fit(table(front=90), "pro", "zone") == ("pro", T.FR_FIT_STYLES["rush"])
    assert S.fit(table(cover=90), "pro", "zone") == ("pro", T.FR_FIT_STYLES["cover"])


def test_the_backs_and_receivers_count_by_their_carry_weights():
    lineup = table()
    for k, index in enumerate(D.PLACES_OF["RB"]):           # one back of 99 among five of 55: his weight lifts the running rating
        lineup[index] = (lineup[index][0], "N", 99 if k == 0 else 55)
    weights = [W.carry_weight(r) for r in [99] + [55] * 5]
    running = (99 * weights[0] + 55 * sum(weights[1:])) / sum(weights)
    plain = (99 + 5 * 55) / 6
    assert running > plain
    assert S.lean(lineup)[0] == (1 if 70 - running >= T.FR_FIT_GAP else -1 if running - 70 >= T.FR_FIT_GAP else 0)


def leaning_league():
    league = new_league(GameRandom(random.Random(5)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    league.gtp = 3
    for team in (TEAM, 9):
        league.player_at(team, D.PLACES_OF["QB"][0]).rating = 99
        for index in D.PLACES_OF["RB"]:
            league.player_at(team, index).rating = 60        # with the stand-in (55) passing is (110 + 70) / 3 = 60: no lean
    return league


def test_the_weeks_styles_fit_every_team_the_players_team_playbook_too():
    league = leaning_league()
    base = S.team_styles(league)
    fitted = S.fitted_styles(league, 3)
    # the player's team leans as team 9 does: his coordinators follow his best players too (one rule for every team: the whole-program C-F2, B-P107)
    assert base[TEAM - 1][0] == "option" and fitted[9 - 1][0] == fitted[TEAM - 1][0] == T.FR_FIT_STYLES["pass"]
    for team in range(1, D.TEAMS + 1):
        assert fitted[team - 1] == S.fit(I.lineup(league, team, 3, team != TEAM, hurt_before=3), *base[team - 1])
    league.stage = "offseason"
    assert S.fitted_styles(league, 3) == base


def test_a_hurt_quarterback_takes_the_lean_away_for_his_weeks():
    league = leaning_league()
    qb = league.player_at(9, D.PLACES_OF["QB"][0])
    I.injure(league, qb.id, "IJK", 4, 0, 2)
    I.settle(league, 3, GameRandom(random.Random(1)), SURNAMES)           # the stand-in quarterback (55) plays
    fitted = S.fitted_styles(league, 3)
    assert fitted[9 - 1][0] != T.FR_FIT_STYLES["pass"]


# ----- nothing of the new items outside a franchise -----

def _forbid(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a rule of SX.8o was used outside a franchise")
    for name in ("kind_of", "carry_weight", "weights", "draw", "expected_carries", "place_weights", "count_games", "add_carries", "extra_percent",
                 "carry_chance", "game_chance", "rated_table"):
        monkeypatch.setattr(W, name, refuse)
    for name in ("season_awards", "stage_one", "apply", "hall_class", "keeps"):
        monkeypatch.setattr(H, name, refuse)
    for name in ("fitted_styles", "fit", "lean"):
        monkeypatch.setattr(S, name, refuse)


def test_a_quick_game_with_the_nfl_rules_draws_what_it_drew(tmp_path, monkeypatch):
    from nflrig import sim_game
    plain = sim_game(tmp_path / "a", 6, trace=True)[0]
    _forbid(monkeypatch)
    rig = sim_game(tmp_path / "b", 6, trace=True)[0]
    assert rig.rnd.trace == plain.rnd.trace and len(rig.rnd.trace) > 1000


@pytest.mark.parametrize("nfl", [False, True])
def test_a_classic_season_draws_and_says_what_it_did(tmp_path, monkeypatch, nfl):
    from frrig import WANT_CLASSIC
    keys = (WANT_CLASSIC if nfl else []) + COACH_AND_TEAM + [ENTER, ENTER, ENTER] * 3

    def season(folder):
        rig = franchise_rig(folder, keys, policy=quit_policy, nfl=nfl)
        rig.game.rnd.trace = []
        return run_until(rig)
    plain = season(tmp_path / "a")
    _forbid(monkeypatch)
    rig = season(tmp_path / "b")
    assert rig.game.rnd.trace == plain.game.rnd.trace and len(rig.game.rnd.trace) > 100 and spoken(rig) == spoken(plain)


# ----- SX.8o: the staff's game plan of a coordinator who keeps his own style uses his lineup's fit (the mutation check's survivors) -----

def test_the_game_plan_recommends_the_style_the_players_lineup_fits():
    from types import SimpleNamespace
    from nfl4.extras.franchise import weekly
    from nfl4.extras.franchise.league import team_ref
    league = leaning_league()
    league.stage, league.gtp = "season", 3
    league.staff["coordinators"][TEAM - 1][0]["rating"] = T.FR_COORD_ADAPT - 1      # a coordinator who keeps his own style
    own_style = league.staff["coordinators"][TEAM - 1][0]["style"]
    fitted = S.fitted_styles(league, 3)[TEAM - 1][0]
    assert fitted == T.FR_FIT_STYLES["pass"] != own_style
    settings = SimpleNamespace(nx_offense_playbook="team", nx_defense_playbook="team")
    division, place = team_ref(9)
    p = SimpleNamespace(g=SimpleNamespace(playbook_table=None, options=SimpleNamespace(settings=SimpleNamespace(game=settings))),
                        season=SimpleNamespace(tn3=division, tn4=place))
    item = weekly._game_plan_item(p, league, 3)
    assert item["styles"][2] == fitted                                 # the staff recommends what his coordinator plays with this lineup
