"""The fouls of an onside kick, the kick made again, the statistics, the help, the remarks, the settings, the saved record and
whole simulated games with onside kicks (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 8.3, 9, 12 and 15; PX SX.4). This is
inspired by Jim Kitchen.
"""
import tempfile
from pathlib import Path

import pytest

from nfl4.data import customlists as cl
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras import remarks as RM
from nfl4.extras.nfl_rules import NflRules, is_nfl, rules_from_settings
from nfl4.extras.state import ExtrasRecord
from nfl4.game import outcome as O
from nfl4.game import phrases as P
from nfl4.game.rules import KICK_AGAIN, NORMAL_KICKOFF
from nflrig import RecordingRules, sim_game
from pagrig import Draws, sounds_played
from test_nx_onside import ENTER, DOWN, QUESTION, game, kick_draws, script, check, texts
from test_nx_penalties import rows, value_of

HANDS = " the Jets send in their hands team. "


def computer_kicks(tmp_path, answers=(), penalties=True, **state):
    """The Jets (side 2, the computer) kick onside in the fourth quarter, trailing 10 to 17 with 100 seconds left: the draw
    `rnd(10) = 9` declares (9 in 10); the Bengals (the player) receive."""
    defaults = dict(wisoff=1, defense=2, half=2, scores=(17, 10), left=100)
    defaults.update(state)
    rig = game(tmp_path, answers=answers, penalties=penalties, **defaults)
    rig.rules.penalty.take_kickoff(rig.engine.s)             # the draws' rows need the down (before_kickoff does it again)
    return rig


def kick_off_and_kick(rig, draws):
    """Declare (the computer's draw first), then play the kick with `draws`; returns the engine's step after the kick."""
    script(rig, Draws().rnd(10, 9))
    step = rig.engine.kick_off()
    check(rig, Draws().rnd(10, 9))
    assert step.__name__ == "onside_kick"
    script(rig, draws)
    step = step()
    check(rig, draws)
    return step


# ----- the fouls of the kick (P24 offside, P33 illegal touching): design 8.3 and 9 -----

def test_the_players_offside_on_a_kick_the_receivers_recovered_gives_them_five_more_yards(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], penalties=True)
    s = rig.engine.s
    step = rig.engine.kick_off()
    value = value_of(rig, rows(rig, O.ONSIDE_KICK, after=False), "P24")
    # 8 yards, not recovered, roll 50 (the receivers fall on it), their player 1, then the foul: P24 by Def6, no second foul
    draws = kick_draws(distance=8, recovered=False, returner=1).below(10000, value).rnd(17, 6).rnd(40, 2).below(3, 0)
    script(rig, draws)
    step = step()
    check(rig, draws)
    said = texts(rig)
    i = said.index(" and ORet1 falls on the ball. ")
    assert said[i + 1:i + 4] == [X.text("NXP-01"), " off sides on the kick off, on the Bengals, Def6. ",
                                 " the Jets accept the penalty. "]
    assert step == rig.engine.position and s.text == P.ITS
    assert (s.half, s.yard_line, s.wisoff, s.down, s.to_go) == (2, 38, 2, 1, 10)       # 5 yards from the 43 toward the goal
    assert s.extras.flags == [1, 0] and s.extras.flag_yards == [5, 0] and s.extras.onside_recovered == [0, 0]
    assert rig.rules.penalty.events == [(4, "accepted", "P24", 1, 5, False)]


def test_the_computers_kick_is_recovered_with_an_offside_and_the_player_chooses_to_have_it_kicked_again(tmp_path):
    rig = computer_kicks(tmp_path, answers=[ENTER])
    s = rig.engine.s
    value = value_of(rig, rows(rig, O.ONSIDE_KICK, after=False), "P24")
    draws = kick_draws(distance=10).below(10000, value).rnd(17, 3).rnd(40, 2)
    step = kick_off_and_kick(rig, draws)
    said = texts(rig)
    assert said[:2] == [" the Jets will try an onside kick. ", X.text("NXO-03", receiving_team="Bengals")]       # SZ.6: said once
    i = said.index(" and the Jets recover it. ")
    assert said[i + 1:i + 7] == [
        X.text("NXP-01"), " off sides on the kick off, on the Jets, ODef3. ",
        " Kim if you accept the penalty, the kick will be made again. ",
        " if you decline it, it will be my ball, first and 10 on my 45 yard line. ", " accept ",
        X.text("NXP-24", yards=5, situation="the kick will be made again")]      # the referee says it; the note is not said again (2026-10-23)
    assert step.__name__ == "kick_off"                                  # KICK_AGAIN
    x = s.extras
    assert x.kick_again is True and x.kick_back == 5 and x.flags == [0, 1] and x.flag_yards == [0, 5]
    assert x.onside_tried == [0, 1] and x.onside_recovered == [0, 0]    # the recovery did not stand
    # the kick is made again: the same kind, no new declaration or question, from five yards back, not a new try
    script(rig, Draws())
    again = step()
    assert again.__name__ == "onside_kick" and x.rekick is True and x.kick_from == 30 and x.kick_again is False
    draws = kick_draws(distance=8, recovered=False, returner=2).below(10000, 9999).below(3, 0)    # no foul this time
    script(rig, draws)
    again()
    check(rig, draws)
    assert (s.half, s.yard_line) == (1, 38) and x.onside_tried == [0, 1] and x.rekick is False    # 30 + 8 from the Jets' goal


def test_illegal_touching_on_a_recovered_kick_gives_the_receivers_the_ball_at_the_spot(tmp_path):
    rig = computer_kicks(tmp_path, answers=[ENTER])
    s = rig.engine.s
    value = value_of(rig, rows(rig, O.ONSIDE_KICK, after=False), "P33")
    assert value == 120                                                 # P24's slice is 1.0 * 100 * 1.2 = 120 of 10,000
    draws = kick_draws(distance=10).below(10000, value).rnd(17, 4).rnd(40, 2)
    step = kick_off_and_kick(rig, draws)
    said = texts(rig)
    i = said.index(" and the Jets recover it. ")
    assert said[i + 2] == " illegal touching of the kick, on the Jets, ODef4. "
    assert said[i + 3:i + 6] == [" Kim if you accept the penalty, it will be first and 10 on my 45 yard line. ",
                                 " if you decline it, it will be my ball, first and 10 on my 45 yard line. ", " accept "]
    assert step == rig.engine.position
    assert (s.half, s.yard_line, s.wisoff, s.down, s.to_go) == (1, 45, 1, 1, 10)       # the Bengals' ball at the Jets' 45
    assert s.extras.onside_recovered == [0, 0] and s.extras.flags == [0, 1] and s.extras.flag_yards == [0, 0]


def test_the_player_may_decline_and_the_kickers_keep_a_recovery(tmp_path):
    rig = computer_kicks(tmp_path, answers=[DOWN, ENTER])
    s = rig.engine.s
    value = value_of(rig, rows(rig, O.ONSIDE_KICK, after=False), "P33")
    draws = kick_draws(distance=10).below(10000, value).rnd(17, 4).rnd(40, 2)
    step = kick_off_and_kick(rig, draws)
    assert texts(rig)[-3:-1] == [" accept ", " decline "] and step == rig.engine.possession
    assert texts(rig)[-1].startswith(" the penalty is declined, ")                       # the referee (2026-10-23)
    assert s.extras.onside_recovered == [0, 1] and s.extras.flags == [0, 0]              # counted: no penalty took it away
    assert rig.rules.penalty.events[-1][1] == "declined"


def test_a_foul_by_the_kicking_team_on_a_return_is_the_original_kick_off_machinery(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], penalties=True)
    step = rig.engine.kick_off()
    assert step.__name__ == "onside_kick"
    rules = rows(rig, O.KICKOFF_RETURN, after=False)
    assert {f.id for f in rules} >= {"P19", "P24", "P25"}                # the kick-off return's rows still apply
    assert {f.id for f in rows(rig, O.ONSIDE_KICK, after=False)} == {"P24", "P33"}


def test_a_kick_made_again_after_offsetting_fouls_keeps_a_normal_kick_normal(tmp_path):
    rig = game(tmp_path, answers=[ENTER], penalties=True)
    s = rig.engine.s
    assert rig.rules.before_kickoff(s, 1) == NORMAL_KICKOFF
    assert rig.rules.penalty.apply(s, None, PEN.Result(PEN.REPLAY_KICK, 2)) == KICK_AGAIN
    assert s.extras.kick_again is True and s.extras.kick_back == 0
    assert rig.rules.before_kickoff(s, 1) == NORMAL_KICKOFF            # no question the second time (the keys are used up)
    assert s.extras.kick_again is False and s.extras.kick_from == 35


def test_an_onside_kick_with_penalties_off_draws_no_foul(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], penalties=False)
    step = rig.engine.kick_off()
    draws = kick_draws(distance=9, recovered=False, returner=1).below(3, 1)
    script(rig, draws)
    step()
    check(rig, draws)


def test_the_foul_names_of_the_kick_are_in_the_foul_table_and_the_prompt_says_the_kick_again(tmp_path):
    rig = game(tmp_path, penalties=True)
    result = PEN.Result(PEN.REPLAY_KICK, 1)
    assert PEN.situation(result, 1) == X.text("NXP-S17") == "the kick will be made again"


# ----- the statistics, the help, the remarks -----

def test_the_statistics_add_the_onside_kicks_tried_and_recovered(tmp_path):
    rig = game(tmp_path, extras=dict(onside_tried=[2, 1], onside_recovered=[0, 1]))
    lines = rig.rules.extra_stats_lines(rig.engine.s)
    assert lines == [X.text("NXS-06"), "Bengals 2", "Jets 1", X.text("NXS-07"), "Bengals 0", "Jets 1"]


def test_without_the_switch_the_statistics_and_the_help_say_nothing_of_onside_kicks(tmp_path):
    rig = game(tmp_path, onside=False)
    assert rig.rules.extra_stats_lines(rig.engine.s) == []
    for key in ("116", "117", "118"):
        assert not {X.text(i) for i in ("NXH-14", "NXH-15", "NXH-16", "NXH-17")} & set(rig.rules.extra_help(key))


def test_the_help_of_f5_f6_and_f7_names_the_onside_kick_when_it_is_on(tmp_path):
    rig = game(tmp_path)
    from nflrig import feature_help
    assert X.text("NXH-14") in rig.rules.extra_help("116")
    assert feature_help(rig.rules, "117")[-2:] == [X.text("NXH-15"), X.text("NXH-16")]
    assert feature_help(rig.rules, "118")[-1] == X.text("NXH-17")


def test_the_remark_is_one_in_three_and_comes_after_the_hands_team(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], comments=True)
    step = rig.engine.kick_off()
    # comments on: the chance 1 in 3 hits, the third line of the pool (ON03), the kick (recovered), L = 3
    draws = Draws().rnd(3, 1).rnd(3, 3).extend(kick_draws(distance=9))
    script(rig, draws)
    step()
    check(rig, draws)
    said = texts(rig)
    i = said.index(HANDS)
    assert said[i + 1] == X.TEXTS["ON03"] and said[i + 2] == " Kick1 bounces the ball along the ground. "      # SZ.6: ON03 no longer repeats the hands team


def test_the_remark_chance_missing_says_nothing_and_comments_off_draws_nothing(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], comments=True)
    step = rig.engine.kick_off()
    draws = Draws().rnd(3, 2).extend(kick_draws(distance=9))           # 2: no remark
    script(rig, draws)
    step()
    check(rig, draws)
    assert X.TEXTS["ON03"] not in texts(rig)


def test_the_player_can_change_switch_off_and_add_remarks_of_the_pool(tmp_path):
    rig = game(tmp_path, answers=["y", ENTER], comments=True)
    problems = cl.Problems("remarks.txt")
    pools = RM.build_pools({"ON01": None, "ON04": "<team> try it short, <coach>, with <quarterback> watching."}, problems)
    assert [r.id for r in pools.lines("ON")] == ["ON02", "ON03", "ON04"] and problems.count == 0
    rig.game.remark_pools = pools
    step = rig.engine.kick_off()
    draws = Draws().rnd(3, 1).rnd(3, 3).extend(kick_draws(distance=9))         # the third line on: ON04
    script(rig, draws)
    step()
    check(rig, draws)
    said = texts(rig)
    i = said.index(HANDS)
    assert said[i + 1] == "Bengals try it short, Kim, with Starr watching."


# ----- the settings, the rules object and the saved record -----

def test_the_settings_read_and_write_the_onside_lines():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_onside = off\nnx_onside_question = ALWAYS\n")
    assert problems == [] and settings.game.nx_onside is False and settings.game.nx_onside_question == "always"
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert problems == [] and again.game == settings.game
    defaults = Settings.defaults().game
    assert defaults.nx_onside is True and defaults.nx_onside_question == "always" and defaults.nx_onside_question_chosen is False


def test_a_bad_onside_value_is_a_problem_and_keeps_the_default():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_onside = sometimes\nnx_onside_question = when\n")
    assert len(problems) == 2 and settings.game.nx_onside is True and settings.game.nx_onside_question == "always"


def test_the_programs_rules_follow_the_onside_settings():
    settings = Settings.defaults()
    settings.game.rules = "nfl"
    rules = rules_from_settings(settings.game)
    assert is_nfl(rules) and rules.onside_on is True and rules.onside_always is True       # SX.2b, D-085: asked at every kick by default
    settings.game.nx_onside, settings.game.nx_onside_question = False, "sensible"
    rules = rules_from_settings(settings.game)
    assert rules.onside_on is False and rules.onside_always is False
    again = rules.for_game()
    assert again.onside_on is False and again.onside_always is False


def test_a_rules_object_made_by_hand_has_no_onside_kicks():
    assert NflRules().onside_on is False and NflRules().onside_always is False


def test_the_record_keeps_the_onside_values_in_json_and_checks_them():
    x = ExtrasRecord(onside_on=True, onside_always=True, onside_tried=[3, 1], onside_recovered=[0, 1],
                     kick_kind="onside", kick_again=True, rekick=True, kick_back=5, kick_from=30, safety_kick=True)
    again = ExtrasRecord.from_json(x.to_json())
    assert again == x


def test_a_record_saved_before_the_onside_kicks_loads_with_them_off():
    old = ExtrasRecord().to_json()
    import json
    data = json.loads(old)
    for name in ("onside_on", "onside_always", "onside_tried", "onside_recovered", "kick_kind", "kick_again", "rekick",
                 "kick_back", "kick_from", "safety_kick"):
        data.pop(name)
    loaded = ExtrasRecord.from_json(json.dumps(data))
    assert loaded.onside_on is False and loaded.onside_tried == [0, 0] and loaded.kick_from == 35 and loaded.kick_kind == ""


@pytest.mark.parametrize("name, value", [("onside_on", 1), ("kick_kind", "squib"), ("kick_back", -1), ("kick_back", 51),
                                         ("kick_from", 0), ("onside_tried", [1]), ("onside_recovered", [0, -1]),
                                         ("safety_kick", "yes"), ("rekick", None)])
def test_a_damaged_onside_value_in_the_record_is_refused(name, value):
    x = ExtrasRecord()
    setattr(x, name, value)
    with pytest.raises(ValueError):
        x.check()


# ----- whole games: the properties -----

def test_whole_simulated_games_keep_every_onside_property(tmp_path):
    total = 0
    for seed in range(1, 41):
        rules = RecordingRules(penalties_on=True, onside_on=True)
        rig, engine, rules, result = sim_game(tmp_path / ("g%d" % seed), seed, rules=rules)
        x = engine.s.extras
        x.check()
        assert rig.rnd.fallbacks == 0 and result.scores is not None and result.scores[0] != result.scores[1]
        for quarter, kicking, left, lead, answer in rules.onsides:
            assert quarter == 4 and lead < 0 and left <= 600                       # design 8.4: only the team behind, late
            assert answer in ("kept", "lost", "run")
        kicks = len(rules.onsides)
        assert sum(x.onside_tried) <= kicks and sum(x.onside_recovered) <= sum(x.onside_tried)
        assert sum(x.onside_recovered) <= sum(1 for e in rules.onsides if e[4] == "kept")
        total += kicks
    assert total > 0                                                               # the rule fires in 40 seeded games

def test_a_safety_by_penalty_makes_the_next_kick_a_kick_from_the_twenty(tmp_path):
    rig = game(tmp_path, penalties=True)
    s = rig.engine.s
    rig.rules.penalty.take_snap(s)
    flow = rig.rules.penalty
    assert s.extras.safety_kick is False
    assert flow.apply(s, None, PEN.Result(PEN.SAFETY, 2)) == "safety"
    assert s.extras.safety_kick is True
    s.extras.kick_kind = ""
    assert rig.rules.before_kickoff(s, 2) == NORMAL_KICKOFF and s.extras.kick_from == 20 and s.extras.safety_kick is False


# ----- whole games through the menus: the player's question at every kick-off -----

class KickOffsRecorded:
    """RecordingRules whose game's rules record (kicking side, kind) of every kick-off, so the test counts the player's kick-offs (the seeded
    games' scores, and so the number of kick-offs, changed with NX-D2's usage draws)."""

    def __new__(cls, **kwargs):
        rules = RecordingRules(**kwargs)
        made = rules.for_game

        def for_game():
            used = made()
            before = used.before_kickoff
            used.kick_offs = []

            def before_kickoff(state, side):
                kind = before(state, side)
                used.kick_offs.append((side, kind))
                return kind
            used.before_kickoff = before_kickoff
            return used
        rules.for_game = for_game
        return rules

def test_whole_games_through_the_menus_ask_the_player_at_every_kick_off_and_keep_the_statistics(tmp_path):
    import random
    from pagrig import make_rig, play
    from test_nx_onside import NO, YES, QUESTION
    tried = 0
    for seed in range(4):
        rig = make_rig(tmp_path / str(seed), rng=random.Random(900 + seed), fast=True, vtrnt=1 + seed % 2)
        rng = random.Random(950 + seed)

        def policy(keys, rig=rig, rng=rng):
            last = rig.said[-1][0] if rig.said else ""
            if last.endswith("Save Game "):
                return DOWN
            if "concede" in last:
                return "n"
            if last in (YES, NO):
                return rng.choice((ENTER, ENTER, "y", "n", DOWN, 112, 114, 97))
            roll = rng.random()
            if roll < 0.45:
                return ENTER
            if roll < 0.80:
                return str(rng.randint(1, 6))
            if roll < 0.90:
                return DOWN
            return rng.choice((112, 113, 114, 115))
        rig.keys.policy = policy
        program_rules = KickOffsRecorded(auto_sides=(2,), penalties_on=True, onside_on=True, onside_always=True)
        result = play(rig, rules=program_rules)
        rules = program_rules.used
        assert result.scores is not None and result.scores[0] != result.scores[1] and rig.rnd.fallbacks == 0
        said = [t for t, _, _ in rig.said]
        mine_kicks = [k for k in rules.kick_offs if k[0] == 1 and k[1] != "period over"]
        assert mine_kicks and said.count(QUESTION) >= len(mine_kicks)        # "always": at every kick-off the player makes
        x = rules.state.extras
        x.check()
        mine = [e for e in rules.onsides if e[1] == 1]
        assert x.onside_tried[0] <= len(mine) and x.onside_tried[1] <= len(rules.onsides) - len(mine)
        tried += x.onside_tried[0]
        assert X.text("NXS-06") in said and X.text("NXS-07") in said     # the statistics of every quarter
    assert tried > 0                                                      # the keys said yes at least once


def test_a_recovered_kick_takes_no_time_so_its_offside_with_3_seconds_left_still_asks_the_player(tmp_path):
    """SX.13 (RB26 4-3-1 (b)): the clock does not start when the kicking team recovers its free kick, so a recovered onside kick never
    runs out a half (SX.4's case of 0:00 after the kick, where the choice was not offered, cannot arise any more): the player is asked."""
    rig = computer_kicks(tmp_path, answers=[ENTER], left=3)
    s = rig.engine.s
    value = value_of(rig, rows(rig, O.ONSIDE_KICK, after=False), "P24")
    draws = kick_draws(distance=10).below(10000, value).rnd(17, 3).rnd(40, 2)
    step = kick_off_and_kick(rig, draws)
    assert " accept " in texts(rig) and step.__name__ == "kick_off" and s.extras.left == 3


def test_the_same_foul_with_time_left_still_asks_the_player(tmp_path):
    rig = computer_kicks(tmp_path, answers=[ENTER], left=100)
    value = value_of(rig, rows(rig, O.ONSIDE_KICK, after=False), "P24")
    draws = kick_draws(distance=10).below(10000, value).rnd(17, 3).rnd(40, 2)
    step = kick_off_and_kick(rig, draws)
    assert " accept " in texts(rig) and step.__name__ == "kick_off"


def test_the_statistics_constants_and_the_foul_yards_agree_with_the_rules_table():
    from nfl4.extras import fouls_2026 as F
    from nfl4.extras import rules_2026 as R
    assert R.ONSIDE_FOUL_YARDS == F.BY_ID["P24"][0].yards == F.BY_ID["P33"][0].yards == 5
    assert (R.KICKOFF_SPOT, R.SAFETY_KICK_SPOT, R.ONSIDE_ANY_TIME) == (35, 20, True)
