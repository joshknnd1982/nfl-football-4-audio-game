"""The computer's calling over the catalog in whole games (nfl4 only, rule 0.13; NX-P1 to NX-P5, NX-R7 G26-10; NFL_PLAYS_DESIGN 7 and
8; PX SX.10e, D-095). This is inspired by Jim Kitchen.

Whole seeded games with both sides by the computer and both teams on their own team playbooks (a new player's game since SX.10e):
every scrimmage call is a call over the whole catalog that the outcome models play, the computer kneels, spikes, throws the Hail Mary and
goes for two by its rules, fakes a kick now and then, and the sample comes out near the league's numbers (the 10,000-game bands are
work/sx10e). Classic, and a game whose player plays the Classic books, call nothing over the catalog and draw nothing for it.
"""
import random

import pytest

import nflrig
from nfl4.extras import nx_texts as X
from nfl4.extras import offense_flow as OF
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.playbook_data import TEAM_STYLES
from nfl4.extras.plays import calling as K
from nfl4.extras.plays import catalog as C
from nfl4.game import outcome as O
from nfl4.game.rules import CLASSIC


class Recording(nflrig.RecordingRules):
    """RecordingRules that also keeps (offense, kind, catalog play, quarterback run, a try, the score) of every play."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = []

    def after_outcome(self, state, outcome):
        done = super().after_outcome(state, outcome)       # the rules name the catalog play in the record (OffenseFlow.finish)
        self.outcomes.append((outcome.offense, outcome.kind, outcome.catalog, outcome.qb_run, outcome.two_point_try, outcome.score))
        return done


def team_game(tmp_path, seed, forced=None):
    rules = Recording(qb_on=True, penalties_on=True, challenges_on=True, onside_on=True, playbooks_on=True)
    rules.forced = forced or (TEAM_STYLES[(seed + 5) % 32], TEAM_STYLES[seed % 32])
    rig, engine, rules, result = nflrig.sim_game(tmp_path / str(seed), seed, rules=rules)
    return rig, engine, rules, result


@pytest.mark.parametrize("seed", range(41, 47))
def test_whole_games_of_two_team_playbooks_call_over_the_catalog_and_end_with_the_scores_the_statistics_hold(tmp_path, seed):
    rig, engine, rules, result = team_game(tmp_path, seed)
    s = engine.s
    assert result.scores == (s.score(1), s.score(2)) and engine.noise_net == 0 and rig.rnd.fallbacks == 0
    s.extras.check()
    calls = rules.books.calls
    offense = [c for c in calls if c[1] == "O"]
    defense = [c for c in calls if c[1] == "D"]
    assert {1, 2} <= {c[0] for c in offense} and {1, 2} <= {c[0] for c in defense} and len(offense) > 80
    assert all(C.BY_ID[p].side == "O" or p == "K026" for _s, _r, p, *_x in offense)
    assert all(C.BY_ID[p].side == "D" for _s, _r, p, *_x in defense)
    played = rules.offense.events
    assert len(played) > 80 and all(p in C.BY_ID and call.startswith("D") for p, call, *_x in played)
    # every scrimmage play was the model's (no play of the original's tables), but a fake kick, which runs with no call, and a play a
    # review corrected (told again without its call)
    scrimmage = [o for o in rules.outcomes if o[1] in (O.RUN, O.PASS_COMPLETE, O.PASS_INCOMPLETE, O.SACK, O.INTERCEPTION)]
    fakes = sum(1 for e in rules.kicks.events if e[0] == "fake")
    assert scrimmage and len([o for o in scrimmage if not o[2]]) <= fakes + len(rules.review.events)
    assert rules.offense.result is None


def test_a_sample_of_games_comes_out_near_the_leagues_numbers(tmp_path):
    outcomes, calls, qb, tds = [], [], [], 0
    games = 24
    for seed in range(200, 200 + games):
        _rig, _engine, rules, _result = team_game(tmp_path, seed)
        outcomes += rules.outcomes
        calls += rules.books.calls
        qb += rules.qb.events
    kinds = [o[1] for o in outcomes]
    scrambles = sum(1 for o in outcomes if o[3] == "scramble")
    spikes = sum(1 for o in outcomes if o[2] == K.SPIKE)
    dropbacks = (kinds.count(O.PASS_COMPLETE) + kinds.count(O.PASS_INCOMPLETE) + kinds.count(O.SACK) + kinds.count(O.INTERCEPTION)
                 + scrambles - spikes)
    assert 4.5 <= 100 * kinds.count(O.SACK) / dropbacks <= 8.5                  # the league 6.5 (SACK_SCALE)
    assert 3.5 <= 100 * scrambles / dropbacks <= 7.5                             # 5.4
    designed = [e for e in qb if e[2] != "scramble"]
    assert 0.8 <= len(designed) / (2 * games) <= 2.0                             # 1.29 to 1.37 a team-game
    first = [C.BY_ID[p] for _s, r, p, d, *_x in calls if r == "O" and d == 1 and C.BY_ID[p].kind not in K.CLOCK_KINDS]
    assert 42 <= 100 * sum(map(K.pass_class, first)) / len(first) <= 60         # the league's first downs 49.8 percent drop-backs
    tds = sum(1 for o in outcomes if o[5] in ("touchdown", "return touchdown"))
    tries = sum(1 for o in outcomes if o[4])
    assert tds > 50 and 2 <= 100 * tries / tds <= 22                             # 9.8 percent of touchdowns


def test_the_computer_kneels_spikes_and_throws_the_hail_mary_by_its_rules(tmp_path):
    called = []
    for seed in range(300, 316):
        called += [p for _s, r, p, *_x in team_game(tmp_path, seed)[2].books.calls if r == "O"]
    assert K.KNEEL in called
    assert K.HAIL_MARY in called or K.SPIKE in called


def test_the_computers_two_point_try_is_said_played_and_scored(tmp_path, monkeypatch):
    monkeypatch.setattr(K, "TWO_POINT_EARLY", 10000)            # every touchdown before the chart's time: a try for two
    sides, plays, sentences = set(), [], 0
    for seed in range(70, 76):
        rig, engine, rules, result = team_game(tmp_path, seed)
        tries = [o for o in rules.outcomes if o[4]]
        sides |= {o[0] for o in tries}
        plays += [o[2] for o in tries]
        said = [t for t, _, _ in rig.said]
        sentences += sum(said.count(X.text("NXB-H16", team=team)) for team in engine.s.teams.values())
        assert result.scores == (engine.s.score(1), engine.s.score(2))
    # one sentence a try, but a try played again after a foul (TRY_AGAIN) is not announced again
    assert sides == {1, 2} and len(plays) > 4 and len(plays) - 3 <= sentences <= len(plays)
    # the try's plays are the catalog's, played by the models (a try a review corrected or a fake has none)
    assert sum(1 for p in plays if p in C.BY_ID) >= len(plays) - 1


def test_the_computer_fakes_a_kick_on_a_short_fourth_down(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "COMPUTER_FAKE_PUNT", 10000)
    monkeypatch.setattr(T, "COMPUTER_FAKE_FIELD_GOAL", 10000)
    fakes = []
    for seed in range(90, 96):
        fakes += [e for e in team_game(tmp_path, seed)[2].kicks.events if e[0] == "fake"]
    assert fakes and {c for _w, _s, c, _k, _n in fakes} <= {"K015", "K016", "K022", "K023"}


def test_the_same_seed_is_the_same_game(tmp_path):
    first = team_game(tmp_path / "a", 55)
    second = team_game(tmp_path / "b", 55)
    assert first[3].scores == second[3].scores and first[2].books.calls == second[2].books.calls


def test_a_game_whose_player_plays_the_classic_books_calls_nothing_over_the_catalog(tmp_path):
    rig, engine, rules, result = team_game(tmp_path, 61, forced=(("classic", "classic"), ("west", "pressure")))
    assert rules.books.calls == [] and not rules.kicks.on(engine.s)
    assert all(not o[4] or o[0] == 1 for o in rules.outcomes)    # the computer never goes for two there
    assert rules.offense.events == []


def test_classic_answers_the_try_hook_no_with_no_draw():
    class State:
        wisoff = 2
    assert CLASSIC.computer_goes_for_two(State()) is False


def test_the_nfl_rules_ask_the_chart_only_in_a_game_that_plays_the_catalog(tmp_path):
    rig = nflrig.nfl_engine_rig(tmp_path, rules=NflRules(offense_book="classic", defense_book="classic", playbooks_on=True))
    s = rig.engine.s
    s.wisoff, s.defense = 2, 1
    assert rig.rules.computer_goes_for_two(s) is False          # the player's books are Classic: the kick, no draw (strict source)
    rig = nflrig.nfl_engine_rig(tmp_path / "team", rules=NflRules(offense_book="team", defense_book="team", playbooks_on=True))
    s = rig.engine.s
    s.wisoff, s.defense, s.quarter = 2, 1, 5
    s.stats[2].score, s.stats[1].score = 11, 21                 # behind by 10 after the touchdown: the chart says two, no draw (D-175:
    #                                                             behind by 8 the league's coaches kick)
    rig.rules.books.resolve(rig.game, s)
    assert rig.rules.computer_goes_for_two(s) is True


def test_a_game_that_plays_the_catalog_uses_its_own_foul_scale_and_ruling_rates_and_a_classic_one_sx3_and_sx6s(tmp_path):
    from nfl4.extras import review
    team = nflrig.nfl_engine_rig(tmp_path / "team", rules=NflRules(offense_book="team", defense_book="team", playbooks_on=True))
    plain = nflrig.nfl_engine_rig(tmp_path / "plain", rules=NflRules(offense_book="classic", defense_book="classic", playbooks_on=True))
    assert team.rules.penalty.rate_scale() == T.PENALTY_RATE_SCALE_CATALOG
    assert plain.rules.penalty.rate_scale() == T.PENALTY_RATE_SCALE
    assert review.ruling_rates(team.engine.s)["goal"] == T.RULING_RATES_CATALOG["goal"]
    assert review.ruling_rates(team.engine.s)["fumble"] == T.RULING_RATES["fumble"]
    assert review.ruling_rates(plain.engine.s) is T.RULING_RATES


def test_a_sneak_of_the_catalog_never_slides(tmp_path):
    # SX.5's rule (design 7.3); the original's sneak rows never gain 8 yards, the model's sneak can (SX.10e, B-X115)
    games = [team_game(tmp_path / "g", seed)[2] for seed in range(80, 86)]
    assert not [e for rules in games for e in rules.qb.events if e[2] == "sneak" and e[4]]


def test_the_returners_rating_moves_a_2026_kick_off_return_and_nothing_outside_a_franchise():
    # SX.8o's door (FR_RETURN_STEP) for the 2026 kick-off (the Franchise's check WL2 found that no return moved)
    from types import SimpleNamespace
    from nfl4.extras.kick_flow import KickFlow
    from nfl4.extras.plays import model as M
    state = SimpleNamespace(wisoff=1, returner=2)
    rated = KickFlow(SimpleNamespace(modifiers=SimpleNamespace(return_shortest=lambda side, returner: 15)))
    assert rated.returner_door(state, M.KickResult("returned", 30, 22)) == M.KickResult("returned", 33, 25)
    assert rated.returner_door(state, M.KickResult("returned", 98, 40)).touchdown
    assert rated.returner_door(state, M.KickResult("touchback", 35)) == M.KickResult("touchback", 35)
    plain = KickFlow(SimpleNamespace(modifiers=SimpleNamespace(return_shortest=lambda side, returner: 12)))
    result = M.KickResult("returned", 30, 22)
    assert plain.returner_door(state, result) is result


def test_the_engine_family_of_every_call_is_a_play_the_engine_knows():
    for concept in C.OFFENSE:
        assert OF.engine_family(concept) in (1, 2, 3, 4, 5, 8, 9, 10)
    assert OF.engine_family(C.BY_ID["K026"]) == 2
