"""The player's choice of a receiver and of a blitzer (nfl4 only, rule 0.13; SY.4, SY.5, D-104, D-105). This is inspired by Jim Kitchen.

R in the offense menu and L in the defense menu open a short list; Enter on a play keeps the original's pace and the random pick. At the snap the
engine still makes its draws and the player's choice takes their place; the model throws to a route that suits the receiver and a blitzer makes a
sack a little likelier. Nothing changes when the player chose nothing.
"""
import random
import types

import pytest

from nfl4.extras import choices as CH
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model as M
from nfl4.game.rules import CLASSIC, MENU_QUIET, MENU_REFRESH
from nfl4.game import phrases as P
from nflrig import RecordingRules, nfl_engine_rig, sim_game
from pagrig import Draws, run_steps

ENTER, ESCAPE, UP, DOWN, HOME, END = 13, 27, 38, 40, 36, 35
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)


def rig_for(tmp_path, answers=(), offense="west", defense_book="classic", **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=False, offense_book=offense, defense_book=defense_book)
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def the_offense_menu(rig):
    return run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)


def the_defense_menu(rig):
    return run_steps(rig, rig.engine.defense_menu, Draws(), until=MENU_UNTIL)


def pass_with_back():
    return next(c for c in C.BY_ID.values() if c.side == "O" and c.kind == "pass" and CH.Choices.has_back_route(c))


def pass_without_back():
    return next(c for c in C.BY_ID.values() if c.side == "O" and c.kind == "pass" and c.params and not CH.Choices.has_back_route(c))


def blitz_call():
    return next(c for c in C.BY_ID.values() if c.side == "D" and getattr(c.params, "blitz", False))


def zone_call():
    return next(c for c in C.BY_ID.values() if c.side == "D" and c.params.coverage != C.PREVENT and not c.params.blitz and c.params.rushers == 4)


# ----- the receiver list -----

def test_r_opens_the_list_with_the_plays_own_pick_first_then_six_receivers_and_two_backs(tmp_path):
    rig = rig_for(tmp_path, answers=["r", ESCAPE, ESCAPE])
    mark = len(rig.said)
    the_offense_menu(rig)
    said = texts(rig, mark)
    assert X.text("NXB-T01", coach="Kim") in said and " 1. %s " % X.text("NXB-T02") in said
    roster = rig.engine.s.rosters[1]
    names = roster.receivers[:6]
    answers = ["r"] + [END, ESCAPE, ESCAPE]
    rig = rig_for(tmp_path / "end", answers=answers)
    mark = len(rig.said)
    the_offense_menu(rig)
    last = [t for t in texts(rig, mark) if t.startswith(" 9. ")]
    assert last and roster.running_backs[1] in last[0] and X.text("NXB-T08") in last[0]          # the second running back is the ninth item
    rig = rig_for(tmp_path / "second", answers=["r", DOWN, ESCAPE, ESCAPE])
    mark = len(rig.said)
    the_offense_menu(rig)
    assert " 2. %s, %s " % (names[0], X.text("NXB-T09")) in texts(rig, mark)        # no real names: no positions


def test_enter_on_a_receiver_names_him_and_keeps_the_choice_for_the_next_snap(tmp_path):
    rig = rig_for(tmp_path, answers=["r", "4", ENTER, ESCAPE])
    mark = len(rig.said)
    the_offense_menu(rig)
    roster = rig.engine.s.rosters[1]
    assert rig.rules.choices.target == 3 and X.text("NXB-T03", player=roster.receivers[2]) in texts(rig, mark)
    rig = rig_for(tmp_path / "again", answers=["r", "9", ENTER, ESCAPE])
    the_offense_menu(rig)
    assert rig.rules.choices.target == 8                                  # the second running back
    rig = rig_for(tmp_path / "none", answers=["r", "3", ENTER, "r", "1", ENTER, ESCAPE])
    mark = len(rig.said)
    the_offense_menu(rig)
    assert rig.rules.choices.target == 0 and X.text("NXB-T04") in texts(rig, mark)
    rig = rig_for(tmp_path / "escape", answers=["r", "3", ENTER, "r", DOWN, ESCAPE, ESCAPE])
    the_offense_menu(rig)
    assert rig.rules.choices.target == 2                                  # Escape leaves the choice as it was


def test_a_run_play_has_no_receiver_and_the_backs_are_listed_only_for_plays_with_a_back_route(tmp_path):
    rules = NflRules()
    state = types.SimpleNamespace(rosters={1: types.SimpleNamespace(receivers=list("abcdef"), running_backs=["rb1", "rb2"])})
    seen = []
    g = types.SimpleNamespace(say5=lambda text: seen.append(text))
    rules.game = g
    rules.choices.choose = lambda state, prompt, none, rows, current: seen.append(len(rows)) or None
    for concept, expected in ((pass_with_back(), 8), (pass_without_back(), 6)):
        item = types.SimpleNamespace(action=("pm:call", concept.id))
        assert rules.choices.receiver_menu(state, item) == MENU_QUIET and seen[-1] == expected
    run = next(c for c in C.BY_ID.values() if c.side == "O" and c.kind == "run")
    assert rules.choices.receiver_menu(state, types.SimpleNamespace(action=("pm:call", run.id))) == MENU_QUIET
    assert seen[-1] == X.text("NXB-T21")


# ----- the snap -----

def snap_state(side=1):
    return types.SimpleNamespace(wisoff=side, defense=3 - side, defender1=4, defender2=9)


def test_the_chosen_receiver_replaces_the_drawn_one_only_for_a_pass_of_the_player_and_only_once():
    rules = NflRules()
    rules.offense.called = pass_with_back().id
    rules.choices.target = 5
    assert rules.choices.carrier(snap_state(), 2) == 5 and rules.choices.target == 0 and rules.choices.used_kind == ""
    assert rules.choices.carrier(snap_state(), 2) == 2                      # for one snap only
    rules.choices.target = 5
    assert rules.choices.carrier(snap_state(2), 2) == 2                     # the computer's offense: never
    rules.choices.target = 5
    rules.offense.called = next(c.id for c in C.BY_ID.values() if c.side == "O" and c.kind == "run")
    assert rules.choices.carrier(snap_state(), 2) == 2                      # a run: the drawn carrier


def test_a_back_is_the_target_only_when_the_play_has_a_back_route():
    rules = NflRules()
    rules.offense.called = pass_with_back().id
    rules.choices.target = 7
    assert rules.choices.carrier(snap_state(), 3) == 7 and rules.choices.used_kind == "RB"
    rules.offense.called = pass_without_back().id
    rules.choices.target = 7
    assert rules.choices.carrier(snap_state(), 3) == 3                      # no route for him: the drawn receiver


def test_the_engine_names_a_running_back_who_was_thrown_to(tmp_path):
    rig = rig_for(tmp_path)
    roster = rig.engine.s.rosters[1]
    assert rig.engine.receiver(1, 3) == roster.receivers[2]
    assert rig.engine.receiver(1, 7) == roster.running_backs[0] and rig.engine.receiver(1, 8) == roster.running_backs[1]


# ----- the model -----

def throw(concept, target, seeds=range(300)):
    call = zone_call().params
    routes = set()
    for seed in seeds:
        result = M.play(concept, call, M.Situation(target=target), random.Random(seed) and _Rnd(seed))
        if result.route:
            routes.add(result.route)
    return routes


class _Rnd:
    """The model's random function (`rnd(n)` is 1 to n; `below(n)` is 0 to n - 1), over a seeded generator."""

    def __init__(self, seed):
        self.r = random.Random(seed)

    def __call__(self, n):
        return self.r.randrange(n) + 1

    def below(self, n):
        return self.r.randrange(n)


def test_a_back_as_the_target_runs_back_routes_and_a_wide_receiver_does_not_run_the_backs_swing():
    concept = pass_with_back()
    back_routes = set(M.ROUTE_TARGETS["RB"])
    assert throw(concept, "RB") <= back_routes and throw(concept, "RB")
    free = throw(concept, "")
    assert free - back_routes                                                # the play's own routes include others
    wide = throw(concept, "WR")
    assert wide <= set(M.ROUTE_TARGETS["WR"]) and "swing" not in wide and "angle" not in wide


def test_a_target_with_no_suitable_route_leaves_the_play_as_it_was():
    routes = (("go", 60), ("post", 40))
    assert M.targeted_routes(routes, "RB") == routes and M.targeted_routes(routes, "") == routes
    assert M.targeted_routes((("swing", 50), ("go", 50)), "RB") == (("swing", 50),)


def test_a_blitzer_makes_the_sack_likelier_when_he_is_not_a_lineman_and_only_on_a_blitz():
    concept = pass_with_back()
    blitz, zone = blitz_call().params, zone_call().params
    tags = M.call_tags(blitz)
    base = M.sack_rate(concept, blitz, M.Situation(), tags)
    assert M.sack_rate(concept, blitz, M.Situation(blitzer="DL"), tags) == base
    assert M.sack_rate(concept, blitz, M.Situation(blitzer="LB"), tags) > base
    assert M.sack_rate(concept, blitz, M.Situation(blitzer="DB"), tags) > M.sack_rate(concept, blitz, M.Situation(blitzer="LB"), tags)
    assert M.sack_rate(concept, zone, M.Situation(blitzer="DB"), M.call_tags(zone)) == M.sack_rate(concept, zone, M.Situation(), M.call_tags(zone))


# ----- the blitzer -----

def test_l_opens_the_list_of_the_seventeen_defenders_and_the_choice_is_for_a_blitz_of_the_players_defense(tmp_path):
    rig = rig_for(tmp_path, answers=["l", END, ENTER, ESCAPE], wisoff=2, defense=1, offense="classic", defense_book="west")
    mark = len(rig.said)
    run_steps(rig, rig.engine.defense_menu, Draws(), until=MENU_UNTIL)
    said = texts(rig, mark)
    roster = rig.engine.s.rosters[1]
    assert X.text("NXB-T11", coach="Kim") in said and rig.rules.choices.blitzer == 17
    assert X.text("NXB-T13", player=roster.defense[16]) in said


def test_the_chosen_blitzer_is_named_on_the_sack_only_when_the_call_is_a_blitz():
    rules = NflRules()
    state = snap_state(2)
    state.defense = 1
    rules.choices.blitzer = 8
    rules.defense.called = blitz_call().id
    assert rules.sack_defenders(state) == (8, 9)
    state.defender2 = 8
    assert rules.sack_defenders(state) == (8, 4)                             # the second name is the one the draw gave first
    rules.defense.called = zone_call().id
    assert rules.sack_defenders(state) == (state.defender1, state.defender2)
    rules.defense.called = blitz_call().id
    state.defense = 2
    assert rules.sack_defenders(state) == (state.defender1, state.defender2)  # the computer's defense never has the player's blitzer
    assert rules.choices.blitzer_kind(snap_state(1)) == "" and CLASSIC.sack_defenders(state) == (4, 8)


def test_the_kind_of_the_blitzer_by_his_place_and_the_choices_are_cleared_after_a_play():
    rules = NflRules()
    state = snap_state(2)
    state.defense = 1
    rules.defense.called = blitz_call().id
    for place, kind in ((1, "DL"), (6, "DL"), (7, "LB"), (11, "LB"), (12, "DB"), (17, "DB")):
        rules.choices.blitzer = place
        assert rules.choices.blitzer_kind(state) == kind
    rules.choices.target = 3
    rules.choices.clear()
    assert (rules.choices.target, rules.choices.blitzer, rules.choices.used_kind) == (0, 0, "")


# ----- whole games -----

def test_a_game_where_the_player_chooses_every_target_throws_to_him_and_ends(tmp_path):
    chosen = []
    real = NflRules.draw_carrier

    def draw_carrier(self, state, rnd):
        if state.wisoff == 1:
            self.choices.target = 2
            self.offense.called = pass_with_back().id               # the player's call (the simulated game calls none of its own)
        value = real(self, state, rnd)
        called = C.BY_ID.get(self.offense.called)
        if state.wisoff == 1 and called is not None and called.kind in CH.PASS_KINDS:
            chosen.append(value)
        return value

    NflRules.draw_carrier = draw_carrier
    try:
        rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
        rig, engine, rules, result = sim_game(tmp_path, 41, rules=rules)
    finally:
        NflRules.draw_carrier = real
    assert result.scores is not None and rig.rnd.fallbacks == 0
    assert chosen and set(chosen) == {2}                                    # every pass of the player went to the second receiver


def test_a_game_where_the_player_chooses_nothing_is_the_game_it_was(tmp_path):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    rig, engine, rules, result = sim_game(tmp_path / "a", 42, rules=rules, trace=True)
    rules2 = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    rig2, engine2, rules2, result2 = sim_game(tmp_path / "b", 42, rules=rules2, trace=True)
    assert rig.rnd.trace == rig2.rnd.trace and result.scores == result2.scores


# ----- T works in the lists too (rule 0.22) -----

def test_t_in_the_receiver_list_and_in_the_blitzer_list_calls_the_timeout_and_leaves_the_list(tmp_path):
    from randsources import ScriptedRandom
    out = " time out called by the Bengals. "
    for menu, letter, extra in (("offense_menu", "r", {}), ("defense_menu", "l", dict(wisoff=2, defense=1))):
        rules = NflRules(timeouts_on=True, offense_book="west", defense_book="west")
        fields = dict(START)
        fields.update(extra)
        rig = nfl_engine_rig(tmp_path / menu, answers=[letter, "t", ENTER], rules=rules, extras=dict(left=500, pending=33, running=True), **fields)
        draws = Draws().below(6, 1) if menu == "offense_menu" else Draws().rnd(9, 3)
        rig.rnd.source = ScriptedRandom(draws.values, strict=False)          # the Enter after the time out picks a play: its draws are free
        rig.rnd.trace = []
        getattr(rig.engine, menu)()
        assert out in texts(rig) and rig.rules.choices.target == 0 and rig.rules.choices.blitzer == 0
        assert rig.rnd.trace[0] == 6                                          # the time out's own draw is the first of the game

