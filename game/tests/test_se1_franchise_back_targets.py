"""Passes to running backs in a Franchise game (nfl4 only, rule 0.13; P8 S-E1, Q-048, D-162, D-174, D-194). This is inspired by Jim Kitchen.

R in the offense menu offers the first two running backs in a Franchise game as it does in a quick game: the pass to a back counts with his own
rating as a back (not a receiver's neutral 70), and a catch can hurt him (his own place, not a receiver's or a defender's); a catch is not a carry of
the workload rule. The receivers of a Franchise game are said by each man's real position in the league. S-E1 also found R failing on the eight RPO
plays (their routes are their second parameter, the first is the gap of the give): fixed in every game, and an RPO given to the back the player chose
is run by that back.
"""
import random
import types

import pytest
from drrig import SURNAMES
from frratings import rated_roster, state_with, use_design_values
from nflrig import RecordingRules, SimEngine
from pagrig import make_rig
from test_fr_injury_flow import OPP, TEAM, WORDS, Rigged, league_at

from nfl4.extras import choices as CH
from nfl4.extras import nfl_surnames
from nfl4.extras import real_names as RN
from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import injury_flow as F
from nfl4.extras.franchise.league import new_league
from nfl4.extras.franchise import ratings as R
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model as M
from nfl4.extras.state import ExtrasRecord
from nfl4.extras import tuning as T
from nfl4.game import outcome as O
from nfl4.game.outcome import PlayOutcome
from nfl4.game.rnd import GameRandom
from nfl4.game.rules import MENU_QUIET

WORD = {"WR": "NXB-T06", "TE": "NXB-T07", "HB": "NXB-T08", "FB": "NXB-T08"}


def pass_with_back():
    return next(c for c in C.BY_ID.values() if c.side == "O" and c.kind == "pass" and CH.Choices.has_back_route(c))


def back_route_plays():
    return [c.id for c in C.BY_ID.values() if c.side == "O" and c.kind in CH.PASS_KINDS and CH.Choices.has_back_route(c)]


def rpos():
    return [c for c in C.BY_ID.values() if c.side == "O" and c.kind == "rpo"]


def real_league_at(week, seed=3):
    """A league made from the shipped rosters.txt, as a player's new franchise is (SR.4): real positions, tight ends among the receivers."""
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", TEAM, "20260101-000000", real=RN.defaults())
    league.gtp = week
    return league


def franchise_state(league, rnd=None):
    """A GameInjuries of the player's team TEAM (side 1) against OPP in week 3, bound to a state whose rosters are the week's lineups."""
    game = F.GameInjuries(league, TEAM, OPP, 3, False, rnd or GameRandom(random.Random(1)), SURNAMES, WORDS, say=lambda text, plain: None)

    class State:
        rosters = {1: league.roster_for_game(TEAM), 2: league.roster_for_game(OPP)}
        quarterbacks = {}
        extras = ExtrasRecord()
        defense, returner = 2, 1
    state = State()
    game.quarterbacks(state)
    return game, state


def menu_rows(rules, state, concept):
    """The rows R's list would offer for `concept` (the list itself is stubbed: it returns no choice)."""
    seen = []
    rules.choices.choose = lambda state, prompt, none, rows, current: seen.append(list(rows)) or None
    assert rules.choices.receiver_menu(state, types.SimpleNamespace(action=("pm:call", concept.id))) == MENU_QUIET
    return seen[-1]


# ----- the target's place -----

def test_the_target_codes_are_the_lists_codes_and_name_the_backs_places():
    assert D.BACK_TARGETS == CH.BACK_CODES == (7, 8)
    for n in range(1, 7):
        assert D.target_key(n) == ("Receivers:", n) and D.target_place(n) == D.PLACES_OF["WR"][n - 1]
    assert D.target_key(7) == ("Running Backs:", 1) and D.target_key(8) == ("Running Backs:", 2)
    assert D.target_place(7) == D.PLACES_OF["RB"][0] and D.target_place(8) == D.PLACES_OF["RB"][1]
    for n in range(1, 9):
        assert D.PLACES[D.target_place(n)][:2] == D.target_key(n)


# ----- the rating -----

def test_a_pass_to_a_back_counts_with_the_backs_own_rating(monkeypatch):
    use_design_values(monkeypatch)
    own, opponent = rated_roster("", 70, rb1=95, rb2=46, wr1=70), rated_roster("O", 70)
    m = R.FranchiseModifiers()
    s = state_with(own, opponent, carrier=7, offense_play=4)
    m.bind(s)
    assert m.gap(R.PASS) == (2 * 70 + 95 + 1) // 3 - 70 == 8                # before S-E1 a code 7 read a receiver's place 7: the neutral 70, gap 0
    s.carrier = 8
    assert m.gap(R.PASS) == (2 * 70 + 46 + 1) // 3 - 70 == -8
    s.carrier = 1
    assert m.gap(R.PASS) == 0                                                # a receiver as before
    s.carrier, s.offense_play = 1, 1
    assert m.gap(R.RUN) == 95 - 70                                           # a run of back 1 as before


# ----- the injuries -----

def test_a_catch_by_a_back_exposes_his_own_place():
    league = league_at(3)
    game, state = franchise_state(league)
    for carrier, place in ((7, D.PLACES_OF["RB"][0]), (8, D.PLACES_OF["RB"][1]), (3, D.PLACES_OF["WR"][2]), (6, D.PLACES_OF["WR"][5])):
        assert game.exposed_places(PlayOutcome(O.PASS_COMPLETE, 1, 4, 5, carrier=carrier), state) == (1, place, True)
    assert game.exposed_places(PlayOutcome(O.RUN, 1, 1, 1, carrier=2), state) == (1, D.PLACES_OF["RB"][1], True)


def test_a_back_hurt_on_a_catch_is_the_back_and_the_catch_is_not_a_carry():
    league = league_at(3)
    rnd = Rigged([0, 99] + [0] * 10)                         # the play's draw hits, the carrier (not the tackler), then the injury's draws
    game, state = franchise_state(league, rnd)
    back = game.identity[1][D.PLACES_OF["RB"][0]]
    assert isinstance(back, int) and league.players[back].pos == "RB"
    game.after_play(state, PlayOutcome(O.PASS_COMPLETE, 1, 4, 5, yards=6, carrier=7, defender1=3))
    assert [row[0] for row in game.record["hurt"]] == [back]
    assert game.record["carries"] == {}                       # the workload rule counts runs only


# ----- the list -----

def test_r_in_a_franchise_game_offers_the_two_backs_and_says_each_mans_real_position():
    league = real_league_at(3)
    game, state = franchise_state(league)
    rules = NflRules()
    rules.game = types.SimpleNamespace(say5=lambda text: None, game_injuries=game)
    roster = state.rosters[1]
    rows = menu_rows(rules, state, pass_with_back())
    codes = [code for code, _text in rows]
    assert codes[-2:] == [7, 8] and set(codes[:-2]) <= set(range(1, 7))
    for code, text in rows:
        pid = game.identity[1][D.target_place(code)]
        name = roster.receivers[code - 1] if code <= 6 else roster.running_backs[code - 7]
        assert text == X.text("NXB-T05", player=name, position=X.text(WORD[league.players[pid].position]))
    assert rows[-2][1].startswith(roster.running_backs[0] + ",") and rows[-1][1].startswith(roster.running_backs[1] + ",")
    assert any(X.text("NXB-T07") in text for _code, text in rows) and any(X.text("NXB-T06") in text for _code, text in rows)
    no_back = next(c for c in C.BY_ID.values() if c.side == "O" and c.kind == "pass" and c.params and not CH.Choices.has_back_route(c))
    assert all(code <= 6 for code, _text in menu_rows(rules, state, no_back))


def test_a_franchise_targets_kind_is_his_real_position_and_a_stand_in_has_none():
    league = real_league_at(3)
    game, state = franchise_state(league)
    rules = NflRules()
    rules.game = types.SimpleNamespace(game_injuries=game)
    for slot in range(1, 7):
        position = league.players[game.identity[1][D.target_place(slot)]].position
        assert rules.choices.receiver_kind(slot) == CH.KIND_OF_POSITION[position]
    assert rules.choices.receiver_kind(7) == rules.choices.receiver_kind(8) == "RB"
    assert {rules.choices.receiver_kind(slot) for slot in range(1, 7)} == {"WR", "TE"}
    game.identity[1][D.target_place(4)] = ("stand-in", "WR")
    assert rules.choices.receiver_kind(4) == ""


def test_a_back_in_an_empty_place_is_not_offered_and_not_thrown_to():
    rules = NflRules()
    roster = types.SimpleNamespace(receivers=list("abcdef"), running_backs=["rb1", "rb2", "rb3", "rb1", "rb1", "rb1"],
                                   empty=[("Running Backs:", 2)])
    state = types.SimpleNamespace(rosters={1: roster})
    rules.game = types.SimpleNamespace(say5=lambda text: None)
    assert [code for code, _t in menu_rows(rules, state, pass_with_back())] == [1, 2, 3, 4, 5, 6, 7]
    rules.offense.called = pass_with_back().id
    rules.choices.target = 8
    snap = types.SimpleNamespace(wisoff=1, defense=2, rosters={1: roster})
    assert rules.choices.carrier(snap, 4) == 4                                # nobody in that place: the drawn receiver


# ----- the RPO plays (every game) -----

def test_r_on_an_rpo_play_lists_the_receivers_and_the_backs_when_its_throw_has_a_back_route():
    found = rpos()
    assert len(found) == 8
    rules = NflRules()
    rules.game = types.SimpleNamespace(say5=lambda text: None)
    state = types.SimpleNamespace(rosters={1: types.SimpleNamespace(receivers=list("abcdef"), running_backs=["rb1", "rb2"])})
    with_back = 0
    for concept in found:
        assert CH.Choices.routes_of(concept) == concept.params[1]
        rows = menu_rows(rules, state, concept)                               # before S-E1: ValueError (the gap word read as routes)
        if CH.Choices.has_back_route(concept):
            with_back += 1
            assert [code for code, _t in rows][-2:] == [7, 8]
        else:
            assert len(rows) == 6
    assert with_back == 3


def test_an_rpo_given_to_the_chosen_back_is_run_by_him_and_nothing_else_moves():
    rules = NflRules()
    rules.offense.called = "O135"
    give, throw, keep = M.Result("run", 4, gap="guard"), M.Result("complete", 7, "drag", 1, 3), M.Result("run", 3, gap="qb")
    for carrier, result, side, after in ((7, give, 1, 1), (8, give, 1, 2), (3, give, 1, 3), (7, throw, 1, 7), (7, keep, 1, 7), (8, give, 2, 8)):
        state = types.SimpleNamespace(wisoff=side, carrier=carrier)
        rules.choices.handed_off(state, result)
        assert state.carrier == after, (carrier, result.kind, side)


# ----- whole Franchise games -----

def franchise_game(tmp_path, monkeypatch, seed, target):
    """A whole game of week 3 with the Franchise's injuries and ratings (both sides by the computer); every snap of the player's runs and passes
    calls a catalog pass with a back route and throws to `target`. Returns the rig, the engine, the GameInjuries, the snaps' carriers and the
    places exposed on the player's catches."""
    league = real_league_at(3)
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=3)
    rules = RecordingRules(penalties_on=True, qb_on=True)
    own, opponent = F.lineup_roster(league, TEAM, 3, False), F.lineup_roster(league, OPP, 3, True)
    game = F.GameInjuries(league, TEAM, OPP, 3, False, rig.game.rnd, SURNAMES, WORDS, say=lambda text, plain: rig.game.say2(text))
    plays, carriers, catches = back_route_plays(), [], []
    real_draw, real_exposed = NflRules.draw_carrier, F.GameInjuries.exposed_places

    def draw_carrier(self, state, rnd):
        mine = state.wisoff == 1 and 1 <= state.offense_play <= 5
        if mine:
            self.choices.target = target
            self.offense.called = plays[len(carriers) % len(plays)]
        value = real_draw(self, state, rnd)
        if mine:
            carriers.append(value)
        return value

    def exposed_places(self, outcome, state=None):
        found = real_exposed(self, outcome, state)
        if found is not None and outcome.offense == 1 and outcome.kind == O.PASS_COMPLETE:
            catches.append((outcome.carrier, found[1], self.identity[1][found[1]]))
        return found
    monkeypatch.setattr(NflRules, "draw_carrier", draw_carrier)
    monkeypatch.setattr(F.GameInjuries, "exposed_places", exposed_places)
    engine = SimEngine(rig.game, rules, quarterback_names=game.quarterbacks, own_names=own, opponent_names=opponent)
    rig.game.play_engine, rig.game.game_injuries = engine, game
    try:
        engine.run()
    finally:
        rig.game.play_engine = rig.game.game_injuries = None
    return rig, engine, game, league, carriers, catches


@pytest.mark.parametrize("seed,target", [(21, 7), (22, 8)])
def test_a_franchise_game_where_every_pass_goes_to_a_back_ends_and_names_him(tmp_path, monkeypatch, seed, target):
    rig, engine, game, league, carriers, catches = franchise_game(tmp_path, monkeypatch, seed, target)
    assert rig.game.rnd.fallbacks == 0 and engine.outcomes
    assert carriers and set(carriers) == {target}
    assert catches and all(carrier == target and place == D.target_place(target) for carrier, place, _who in catches)
    name = engine.s.rosters[1].running_backs[target - 7]
    said = " ".join(t for t, _, _ in rig.said)
    assert name in said
    runs = [o for o in engine.outcomes if o.offense == 1 and o.kind == O.RUN and not o.qb_run and o.catalog in ("O131", "O135", "O136")]
    assert all(o.carrier == target - 6 for o in runs)                      # an RPO's give: the chosen back runs it


def test_a_made_up_leagues_receivers_are_wide_receivers():
    league = league_at(3)
    game, _state = franchise_state(league)
    rules = NflRules()
    rules.game = types.SimpleNamespace(game_injuries=game)
    assert [rules.choices.receiver_kind(slot) for slot in range(1, 9)] == ["WR"] * 6 + ["RB"] * 2


def test_in_a_franchise_game_where_every_play_hurts_the_catches_hurt_only_backs(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_INJ_PLAY", 10000)
    monkeypatch.setattr(T, "FR_INJ_TACKLER", 0)
    rig, engine, game, league, carriers, catches = franchise_game(tmp_path, monkeypatch, 23, 7)
    assert catches
    hurt = {row[0] for row in game.record["hurt"]}
    caught_by = {who for _c, _p, who in catches if isinstance(who, int)}
    assert caught_by & hurt and all(league.players[pid].pos == "RB" for pid in caught_by)
