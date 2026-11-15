"""GitHub issues 11 and 14, the tester's answers to the follow-up questions (nfl4 only, rule 0.13; rule 0.41; D-240 to D-242). This is inspired by
Jim Kitchen.

Asked on 2026-11-15 and answered by Dennisl123 the same day:
* issue 14, question 1 "B" (comment 6902675397, Q-096, D-240): the computer rests its starters later and less often: only with a lead of 21 or more
  and 5 minutes or less left in the fourth quarter (D-236's "28 at any time of the quarter" is gone); its starters still come back under 14.
* issue 14, question 2 "B" (the same comment, Q-097, D-241): packages for the kicks: the kick-off team, the kick return team, the punt team, the
  punt return team and the field goal team (which kicks the try and a fair catch kick too). They come in at the kick and leave after the play.
* issue 11 "B" (comment 6902689060, Q-095, D-242): in the last two minutes of the second and the fourth quarter a T pressed during a play is kept
  and the time out is called as soon as the play ends (D-233 elsewhere: not kept). The run-out question says so (NXT-18).
None of it draws: a game where the player sets nothing is the very same game.
"""
from pathlib import Path

import pytest
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from randsources import ScriptedRandom

from nfl4.data import debuglog
from nfl4.extras import nx_texts as X
from nfl4.extras import subs as S
from nfl4.extras.nfl_rules import NflRules
from nfl4.game.rules import TIMEOUT_GRANTED, TIMEOUT_KEPT

ENTER, ESCAPE, END, T_KEY = 13, 27, 35, 84
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
OUT = " time out called by the Bengals. "
LATE = X.text("NXT-17")


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


# ----- Q-096 (D-240): the computer rests later and less often -----

@pytest.mark.parametrize("lead,left,due", [(21, 300, True), (21, 301, False), (28, 301, False), (40, 600, False), (20, 10, False),
                                           (35, 0, True)])
def test_the_computer_rests_only_with_21_and_five_minutes_left(lead, left, due):
    assert S.rest_due(False, 4, False, lead, left) is due


def test_the_rest_is_never_before_the_fourth_quarter_or_in_overtime():
    assert not S.rest_due(False, 3, False, 50, 10) and not S.rest_due(False, 4, True, 50, 10) and not S.rest_due(False, 5, False, 50, 10)


def test_its_starters_still_come_back_under_14():
    assert S.rest_due(True, 4, False, 14, 200) and not S.rest_due(True, 4, False, 13, 200)


# ----- Q-097 (D-241): packages for the kicks -----

def test_every_kick_team_is_a_package_with_its_own_spoken_name(tmp_path):
    rig = rig_for(tmp_path)
    flow = rig.rules.subs
    keys = ["K:" + k for k in S.KICK_TEAMS]
    assert all(key in S.PACKAGES for key in keys) and S.PACKAGES[-5:] == tuple(keys)
    words = [flow.package_word(key) for key in keys]
    assert words == [X.text(i) for i in ("NXB-U36", "NXB-U37", "NXB-U38", "NXB-U39", "NXB-U40")]
    assert len(set(flow.package_word(key) for key in S.PACKAGES)) == len(S.PACKAGES)


def test_a_kick_package_is_saved_and_loaded():
    from nfl4.extras.state import ExtrasRecord
    record = ExtrasRecord()
    record.subs = S.new_record()
    S.add_package(record.subs, "K:punt_return", 29, "Back3")
    assert ExtrasRecord.from_json(record.to_json()).subs["packages"] == {"K:punt_return": [[29, "Back3"]]}


def test_a_punt_or_a_field_goal_is_its_teams_formation(tmp_path):
    rig = rig_for(tmp_path)
    flow, s = rig.rules.subs, rig.engine.s
    s.offense_play = 7
    assert flow.formation_of(s) == "K:punt"
    s.offense_play = 6
    assert flow.formation_of(s) == "K:field_goal"
    s.wisoff, s.defense = 2, 1
    assert flow.formation_of(s) is None                                  # the computer's field goal: no block team was asked for
    s.offense_play = 7
    assert flow.formation_of(s) == "K:punt_return"


def test_the_punt_snap_lays_the_punt_package_and_the_next_menu_takes_it_off(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    before = names(rig)
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "K:punt", 12, before[20])              # a linebacker of the coverage in for a defensive lineman
    S.add_package(s.extras.subs, "K:field_goal", 31, before[32])        # the punter kicks field goals (a package of another kick)
    s.offense_play = 7
    rules.before_snap(s, 7, 1)
    assert names(rig)[12] == before[20] and names(rig)[20] == before[12] and names(rig)[31] == before[31]
    rules.subs.ensure(s, "after a play")
    assert names(rig) == before and rules.subs.formation is None


def test_the_kick_off_lays_the_kicking_or_the_return_teams_package(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    rig.rnd.source.strict = False
    before = names(rig)
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "K:kickoff", 13, before[25])
    S.add_package(s.extras.subs, "K:kick_return", 29, before[8])         # a receiver returns kick-offs
    rules.before_kickoff(s, 1)
    assert names(rig)[13] == before[25] and names(rig)[29] == before[29]
    rules.subs.ensure(s, "after a play")
    assert names(rig) == before
    rules.before_kickoff(s, 2)
    assert names(rig)[29] == before[8] and names(rig)[13] == before[13]
    rules.subs.ensure(s, "offense menu")
    assert names(rig) == before


def test_the_kicked_try_is_the_field_goal_teams(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    before = names(rig)
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "K:field_goal", 31, before[32])
    rules.special_kick(s, "extra point")
    assert names(rig)[31] == before[32]
    rules.subs.ensure(s, "kick-off")
    s.wisoff, s.defense = 2, 1
    rules.special_kick(s, "extra point")                                 # the computer's try: none of the player's packages
    assert names(rig) == before


def test_nothing_changes_with_no_package_set(tmp_path):
    rig = rig_for(tmp_path)
    s, rules = rig.engine.s, rig.rules
    rig.rnd.source.strict = False
    before = names(rig)
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "O:shotgun", 0, before[3])
    rules.before_kickoff(s, 1)
    s.offense_play = 7
    rules.before_snap(s, 7, 1)
    rules.special_kick(s, "extra point")
    assert names(rig) == before


def test_the_packages_list_ends_with_the_kicks_and_sets_a_field_goal_team_man(tmp_path):
    # the top list, End: Formation and kick packages; its list, End: the field goal team; its groups: 2 the running backs; place 1; who: 2
    rig = rig_for(tmp_path, answers=["u", END, ENTER, END, ENTER, "2", ENTER, ENTER, "2", ENTER, ESCAPE, ESCAPE, ESCAPE, ESCAPE, ESCAPE])
    mark = len(rig.said)
    run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)
    said = texts(rig, mark)
    record = rig.engine.s.extras.subs
    assert record["packages"] == {"K:field_goal": [[0, "Back3"]]}
    field_goal = rig.rules.subs.package_word("K:field_goal")
    assert X.text("NXB-U31") in said and any(X.text("NXB-U20", n=0) in t for t in said)
    assert " %d. %s " % (len(S.PACKAGES), X.text("NXB-U28", formation=field_goal)) in said
    assert X.text("NXB-U35", player="Back3", old="Back1", formation=field_goal) in said


def test_the_kick_package_log_line(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = rig_for(tmp_path / "rig")
    s = rig.engine.s
    s.extras.subs = S.new_record()
    S.add_package(s.extras.subs, "K:field_goal", 31, names(rig)[32])
    rig.rules.special_kick(s, "extra point")
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if " package " in line]
    assert any("K:field_goal" in line for line in lines), lines


# ----- Q-095 (D-242): a T during a play late in a half is kept -----

def scene(tmp_path, answers=(), extras=None, **state):
    fields = dict(START)
    fields.update(state)
    base = dict(left=500, pending=0, running=False)
    base.update(extras or {})
    return nfl_engine_rig(tmp_path, answers=answers, extras=base, **fields)


def end_of_play(tmp_path, quarter, left, seed=7):
    """A running play of the player's offense ends (H10, between_plays) after a T pressed while it was live."""
    rig = scene(tmp_path, quarter=quarter, extras=dict(plays=1, handled=0, last_offense=1, last_kind="run", running=True, pending=0, left=left))
    rig.rnd.source = ScriptedRandom([], seed=seed, strict=False)
    engine, rules = rig.engine, rig.rules
    engine.go_live()
    rig.keys.post(T_KEY)
    rig.keys.pump()
    rules.after_play = True
    rules.between_plays(engine.s)
    return rig


@pytest.mark.parametrize("quarter,left", [(2, 120), (4, 45), (4, 1)])
def test_in_the_last_two_minutes_of_a_half_the_time_out_is_called_when_the_play_ends(tmp_path, quarter, left):
    rig = end_of_play(tmp_path, quarter, left)
    said = [t for t, _, _ in rig.said]
    assert OUT in said and LATE not in said and list(rig.engine.s.extras.used) == [1, 0]


@pytest.mark.parametrize("quarter,left", [(2, 121), (4, 500), (1, 60), (3, 30), (5, 60)])
def test_elsewhere_a_t_during_a_play_is_still_not_kept(tmp_path, quarter, left):
    rig = end_of_play(tmp_path, quarter, left)
    said = [t for t, _, _ in rig.said]
    assert OUT not in said and said.count(LATE) == 1 and list(rig.engine.s.extras.used) == [0, 0]


def test_the_run_out_question_late_in_a_half_says_the_time_out_comes_when_the_play_ends(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER], returner=1, quarter=4, extras=dict(left=90))
    rig.engine.t_live = True
    rig.rnd.source = ScriptedRandom([], seed=5, strict=False)
    assert rig.engine.run_it_out() == rig.engine.kick_return
    said = [t for t, _, _ in rig.said]
    assert said.count(X.text("NXT-18")) == 1 and X.text("NXT-15") not in said
    assert rig.rules.timeout_kept and not rig.rules.timeout_late
    assert rig.rules.grant_kept_timeout(rig.engine.s) == TIMEOUT_GRANTED and list(rig.engine.s.extras.used) == [1, 0]


def test_the_late_in_half_key_logs_why(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig", quarter=2, extras=dict(left=100))
    assert rig.rules.timeout_key(rig.engine.s, True) == TIMEOUT_KEPT and not rig.rules.timeout_late
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if "timeout_key" in line]
    assert len(lines) == 1 and "last two minutes" in lines[0] and "kept" in lines[0], lines


def test_the_sentence_and_the_key_help():
    from nfl4.game import key_list
    assert X.text("NXT-18").strip() == "the ball is live. you will have the time out when the play ends."
    row = [r for r in key_list.ROWS if r.id == "timeout"][0]
    assert "last two minutes of the second and fourth quarters" in row.what and "is not kept for after the play" in row.what
