"""GitHub issue 14, the tester's answers to the open questions (nfl4 only, rule 0.13; rule 0.41; D-234 to D-236). This is inspired by Jim Kitchen.

Asked on issue 14 (comment 6901661967); Dennisl123 answered on 2026-11-15:
* question 4 "B" (comment 6902013659, Q-087, D-234): "All backups in" also puts in the backup returners; the kicker and the punter stay.
* question 3 "B" (comment 6902011610, Q-086, D-235): packages by formation: the men the player sets for a formation come in for every play called
  in it (the offense's formation as lined up, the defense's package of defensive backs as played); between plays the lineup is the game's again.
* question 2 "B" (comment 6902019767, Q-085, D-236): the computer rests its starters when it leads by a lot late in the game, and sends them back
  when the lead shrinks; one sentence each; Save Game keeps it.
* question 1 "A I think but ask me in a few days" (comment 6902028827, Q-084): U only, as now (nothing to build; asked again later).
Every part changes who holds a place and never a draw: whole games draw and score what they did without them.
"""
import random

import pytest
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from test_se1_franchise_back_targets import franchise_state, real_league_at

from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import subs as S
from nfl4.extras import subs_flow as SF
from nfl4.extras.franchise.injury_flow import game_returners
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C

ENTER, ESCAPE, UP, DOWN, HOME, END = 13, 27, 38, 40, 36, 35
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
BENGALS = 1
SHOTGUN = next(c.id for c in C.BY_ID.values() if c.side == "O" and c.formation == "shotgun")
I_FORM = next(c.id for c in C.BY_ID.values() if c.side == "O" and c.formation == "i_form")
WILDCAT = next(c.id for c in C.BY_ID.values() if c.side == "O" and c.formation == "wildcat")


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def rig_for(tmp_path, answers=(), **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=False, offense_book="classic")
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def names(rig, side=1):
    s = rig.engine.s
    roster = s.rosters[side]
    return roster.running_backs + roster.receivers + roster.defense + roster.special_teams + roster.kickers + [s.quarterbacks[side]]


def real_rig(tmp_path, answers=()):
    rig = rig_for(tmp_path, answers=answers)
    real = R.defaults()
    rig.game.real_names = real
    rig.engine.s.rosters[1] = real.roster(BENGALS, rig.engine.s.rosters[1])
    rig.engine.s.quarterbacks[1] = real.quarterback(BENGALS)
    return rig, real


# ----- Q-087 (D-234): All backups in rests the returners too -----

def test_backups_in_brings_the_teams_next_returners_from_the_real_roles(tmp_path):
    rig, real = real_rig(tmp_path)
    _chart, roles, _squad = real.chart(BENGALS)
    turns = []
    for i in range(max(len(v) for v in roles.values())):
        for role in ("KR", "PR"):
            if i < len(roles.get(role, ())):
                turns.append(real.spoken(roles[role][i]))
    before = names(rig)
    s = rig.engine.s
    s.extras.subs = S.new_record()
    s.extras.subs["backups"] = True
    rig.rules.subs.apply(s, "test")
    after = names(rig)
    expected = []
    for name in turns:
        if name not in before[29:31] and name not in expected:
            expected.append(name)
    assert after[29:31] == expected[:2] and len(expected) >= 2           # the Bengals' KR2 and PR2 (KR1 and PR1 rest)
    assert after[31:33] == before[31:33]                                 # the kicker and the punter stay


def test_backups_in_with_no_roles_known_takes_the_lineups_men_who_may_return():
    table = [S.Man(None, "x") for _ in range(S.PLACE_COUNT)]
    for place, key, position in ((0, "HB1", "HB"), (1, "HB2", "HB"), (6, "W1", "WR"), (7, "W2", "WR"), (8, "W3", "WR"), (10, "W4", "WR"),
                                 (29, "W1", "WR"), (30, "HB1", "HB"), (31, "K1", "K"), (32, "P1", "P"), (33, "Q1", "QB")):
        table[place] = S.Man(key, key, position)
    out = S.backups_in(table, [S.Man("QB2", "QB2", "QB")])
    assert [m.key for m in out[29:33]] == ["W4", "HB2", "K1", "P1"]
    assert out[29].key not in ("W1", "HB1") and out[30].key not in ("W1", "HB1")


def test_a_returner_is_never_a_quarterback_kicker_or_lineman_and_a_lone_returner_stays():
    table = [S.Man(None, "x") for _ in range(S.PLACE_COUNT)]
    for place, key, position in ((29, "R1", "WR"), (30, "R2", "HB"), (31, "K1", "K"), (32, "P1", "P"), (33, "Q1", "QB"), (12, "D1", "DT")):
        table[place] = S.Man(key, key, position)
    out = S.backup_returners(table, [S.Man("QB2", "QB2", "QB"), S.Man("K2", "K2", "K"), S.Man("LT", "LT", "LT")])
    assert [m.key for m in out[29:31]] == ["R1", "R2"]                   # nobody else may return: they stay


def test_a_franchise_game_with_the_backups_in_has_the_next_fit_returners():
    league = real_league_at(3)
    game, state = franchise_state(league)
    before = list(game.identity[1])
    state.extras.subs = S.new_record()
    state.extras.subs["backups"] = True
    game.refresh(1)
    after = game.identity[1]
    team = game.teams[0]
    order = [row[0] for row in game_returners(league, team, game.week, game.staff_of(1), game.out(1), count=8)]
    spares = [pid for pid in order if pid not in before[29:31]]
    assert after[29] != before[29] and after[30] != before[30]
    assert after[29] == spares[0] and after[30] == spares[1]


# ----- Q-086 (D-235): packages by formation -----

def test_a_package_plays_only_in_its_formation_after_the_game_substitutions_and_before_the_next_play_ones():
    base = [S.Man(None, "x") for _ in range(S.PLACE_COUNT)]
    for place, key in ((0, "A"), (1, "B"), (2, "C"), (3, "D")):
        base[place] = S.Man(key, key, "HB")
    record = S.new_record()
    S.add_package(record, "O:shotgun", 0, "D")
    assert S.effective(base, [], record)[0] == base                      # no formation: the base lineup
    assert S.effective(base, [], record, formation="O:i_form")[0] == base
    assert [m.key for m in S.effective(base, [], record, formation="O:shotgun")[0][0:4]] == ["D", "B", "C", "A"]
    S.add(record, "game", 0, "B")                                        # for the game: B at 1; the package then puts D there
    assert [m.key for m in S.effective(base, [], record, formation="O:shotgun")[0][0:4]] == ["D", "A", "C", "B"]
    S.add(record, "play", 0, "C")                                        # the next play's word is the newest: C
    assert S.effective(base, [], record, formation="O:shotgun")[0][0].key == "C"
    S.clear_package(record, "O:shotgun")
    assert "O:shotgun" not in record["packages"]


def test_the_formation_of_the_play_called(tmp_path):
    rig = rig_for(tmp_path)
    flow, s = rig.rules.subs, rig.engine.s
    rig.rules.offense.called = SHOTGUN
    assert flow.formation_of(s) == "O:shotgun"
    rig.rules.offense.called = I_FORM
    assert flow.formation_of(s) == "O:i_form"
    rig.rules.offense.called = WILDCAT
    assert flow.formation_of(s) == "O:other"
    s.extras.play_settings = {"formation": "pistol"}                     # the Formation setting lines every play up in it
    assert flow.formation_of(s) == "O:pistol"
    rig.rules.offense.called = ""
    assert flow.formation_of(s) is None                                  # a play of the original's menus: no formation
    s.wisoff, s.defense = 2, 1
    rig.rules.defense.called = "D003"
    s.extras.play_settings = {"defense_personnel": "dime 4-1-6"}
    assert flow.formation_of(s) == "D:dime"
    s.extras.play_settings = {"defense_personnel": "nickel 4-2-5"}
    assert flow.formation_of(s) == "D:nickel"


def test_the_snap_lays_the_package_over_the_lineup_and_the_next_menu_takes_it_off(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    before = names(rig)
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "O:shotgun", 0, before[3])
    rules.offense.called = I_FORM
    rules.subs.before_snap(s)
    assert names(rig) == before                                          # another formation: nothing changes
    rules.offense.called = SHOTGUN
    rules.subs.before_snap(s)
    assert names(rig)[0] == before[3] and names(rig)[3] == before[0]
    rules.subs.ensure(s, "after a play")
    assert names(rig) == before and rules.subs.formation is None


def test_nfl_rules_before_snap_calls_the_package(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    before = names(rig)
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "O:shotgun", 0, before[2])
    rules.offense.called = SHOTGUN
    rules.before_snap(s, 1, 1)
    assert names(rig)[0] == before[2]


def test_the_packages_item_sets_a_man_for_a_formation_and_starters_back_in_keeps_it(tmp_path):
    # the top list: 1 All backups in, 2 to 8 the groups (no returners, kickers in a game without real names? the list says what is there),
    # End: Packages by formation; its list: 1 under center, 2 shotgun; the package: 1 quarterback, 2 running backs; place 1; who: 2 is Back3
    rig = rig_for(tmp_path, answers=["u", END, ENTER, "2", ENTER, "2", ENTER, ENTER, "2", ENTER, ESCAPE, ESCAPE, ESCAPE, ESCAPE, ESCAPE])
    before = names(rig)
    mark = len(rig.said)
    run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)
    said = texts(rig, mark)
    record = rig.engine.s.extras.subs
    assert record["packages"] == {"O:shotgun": [[0, "Back3"]]}
    shotgun = rig.rules.subs.package_word("O:shotgun")
    assert X.text("NXB-U35", player="Back3", old="Back1", formation=shotgun) in said
    assert any(X.text("NXB-U20", n=0) in t for t in said) and X.text("NXB-U31") in said
    assert " 2. %s " % X.text("NXB-U28", formation=shotgun) in said      # the formations' list said shotgun with none set
    assert names(rig) == before                                          # between plays the game's lineup plays
    record["backups"] = True
    record["game"] = [[1, "Back4"]]
    rig.keys.answers[:] = ["u", "2", ENTER, ESCAPE, ESCAPE]              # backups in: 1 is "Starters back in" (All backups in is gone)
    rig.keys.answers[:] = ["u", ENTER, ESCAPE, ESCAPE]
    run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)
    assert record["backups"] is False and record["game"] == [] and record["packages"] == {"O:shotgun": [[0, "Back3"]]}


def test_clear_this_package(tmp_path):
    rig = rig_for(tmp_path, answers=["u", END, ENTER, "2", ENTER, ENTER, ESCAPE, ESCAPE, ESCAPE, ESCAPE])
    s = rig.engine.s
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "O:shotgun", 0, "Back3")
    mark = len(rig.said)
    run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)
    assert "O:shotgun" not in s.extras.subs["packages"]
    assert X.text("NXB-U34", formation=rig.rules.subs.package_word("O:shotgun")) in texts(rig, mark)


def test_every_package_has_a_spoken_name():
    flow = SF.SubsFlow(NflRules())
    words = [flow.package_word(key) for key in S.PACKAGES]
    assert all(w.strip() for w in words) and len(set(words)) == len(words)


# ----- Q-085 (D-236): the computer rests its starters -----

@pytest.mark.parametrize("resting,quarter,overtime,lead,left,due", [
    (False, 4, False, 21, 600, True), (False, 4, False, 21, 601, False), (False, 4, False, 28, 900, True), (False, 3, False, 35, 100, False),
    (False, 4, True, 30, 100, False), (False, 4, False, 20, 100, False), (True, 4, False, 14, 100, True), (True, 4, False, 13, 100, False),
    (False, 4, False, -30, 100, False)])
def test_when_the_computer_rests(resting, quarter, overtime, lead, left, due):
    assert S.rest_due(resting, quarter, overtime, lead, left) is due


def lead_by(rig, points, quarter=4, left=500):
    s = rig.engine.s
    s.quarter = quarter
    s.extras.left = left
    s.stats[2].score = 30
    s.stats[1].score = 30 - points


def test_the_computer_rests_its_starters_says_so_and_brings_them_back(tmp_path):
    rig = rig_for(tmp_path)
    s, flow = rig.engine.s, rig.rules.subs
    before = names(rig, 2)
    lead_by(rig, 24)
    mark = len(rig.said)
    flow.rest(s, "test")
    after = names(rig, 2)
    assert s.extras.computer_rest is True and X.text("NXB-U29", team="Jets") in texts(rig, mark)
    assert after[0:6] == before[1:6] + before[0:1] and after[31:33] == before[31:33]
    assert names(rig, 1)[0] == rig.engine.s.rosters[1].running_backs[0]
    mark = len(rig.said)
    flow.rest(s, "test")                                                 # still resting: nothing said again
    assert texts(rig, mark) == []
    lead_by(rig, 13)
    flow.rest(s, "test")
    assert s.extras.computer_rest is None and X.text("NXB-U30", team="Jets") in texts(rig, mark) and names(rig, 2) == before


def test_the_computer_does_not_rest_in_overtime_or_earlier_and_never_the_players_side(tmp_path):
    rig = rig_for(tmp_path)
    s, flow = rig.engine.s, rig.rules.subs
    before = names(rig, 1), names(rig, 2)
    lead_by(rig, 35, quarter=3)
    flow.rest(s, "test")
    s.stats[1].score, s.stats[2].score = 60, 0                           # the player leads by 60: his side is his own to rest (U)
    s.quarter = 4
    flow.rest(s, "test")
    lead_by(rig, 35, quarter=5)
    s.extras.period = 5
    flow.rest(s, "test")
    assert (names(rig, 1), names(rig, 2)) == before and s.extras.computer_rest is None


def test_the_rest_is_saved_and_loaded(tmp_path):
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord()
    assert "computer_rest" not in record.to_json()
    record.computer_rest = True
    assert ExtrasRecord.from_json(record.to_json()).computer_rest is True
    record.computer_rest = False
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(record.to_json())


def test_a_franchise_computer_team_rests_with_its_own_backups():
    league = real_league_at(3)
    game, state = franchise_state(league)
    before = list(game.identity[2])
    state.extras.computer_rest = True
    game.refresh(2)
    after = game.identity[2]
    assert after[S.QUARTERBACK] != before[S.QUARTERBACK] and after[31:33] == before[31:33]
    field = [after[p] for p in S.FIELD if isinstance(after[p], int)]
    assert len(set(field)) == len(field)                                 # one man, one place
    state.extras.computer_rest = None
    game.refresh(2)
    assert game.identity[2] == before


def test_between_plays_rests_the_computer(tmp_path):
    rig = rig_for(tmp_path)
    s = rig.engine.s
    lead_by(rig, 28, left=300)
    s.extras.plays, s.extras.handled, s.extras.last_offense, s.extras.pending, s.extras.running = 1, 0, 2, 0, False
    s.wisoff, s.defense = 2, 1
    rig.rnd.source.strict = False
    rig.rules.between_plays(s)
    assert s.extras.computer_rest is True


# ----- whole games: no draw moves -----

@pytest.mark.parametrize("seed", [41, 42])
def test_whole_games_with_packages_and_the_computer_resting_draw_and_score_what_they_did(tmp_path, seed, monkeypatch):
    from nflrig import RecordingRules, sim_game
    plain_rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    plain, _engine, _rules, plain_result = sim_game(tmp_path / "plain", seed, rules=plain_rules, trace=True)
    applied = []
    cycle = list(S.PACKAGES) + [None, None]

    class Rules(RecordingRules):
        def between_plays(self, state):
            x = state.extras
            if x.handled != x.plays and x.plays == 2:
                record = state.extras.subs = S.new_record()
                roster = state.rosters[1]
                for key in S.PACKAGES:
                    S.add_package(record, key, 0, roster.running_backs[2])
                    S.add_package(record, key, 6, roster.receivers[4])
            return super().between_plays(state)

    rules = Rules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    original_apply = rules.subs.apply

    def formation_of(state):
        return cycle[state.extras.plays % len(cycle)]

    def apply(state, why, side=1):
        applied.append((side, why))
        return original_apply(state, why, side)
    rules.subs.formation_of = formation_of
    rules.subs.apply = apply
    monkeypatch.setattr(S, "rest_due", lambda resting, quarter, overtime, lead, left: quarter in (2, 3))    # the computer rests in the middle quarters
    rig, engine, _r, result = sim_game(tmp_path / "subs", seed, rules=rules, trace=True)
    assert rig.rnd.trace == plain.rnd.trace and len(rig.rnd.trace) > 1000
    assert result.scores == plain_result.scores
    assert any(why == "package" for side, why in applied) and any(side == 2 for side, why in applied)
    said = texts(rig)
    assert any(X.text("NXB-U29", team=engine.s.teams[2]) == t for t in said)
