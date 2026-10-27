"""Save Game at the accept-or-decline prompt (nfl4 only, rule 0.13; NFL_EXTRA_FEATURES C10, NFL_EXTRAS_DESIGN 12.3; PX SX.9). This is
inspired by Jim Kitchen.

S at the player's prompt keeps the choice in football.sav when both answers give the team with the ball a new down before the last
second of a half: the board is the declined one, the choice is in the extras record, the game ends saved. Loading asks the choice
again first; the board after the answer is the board the same answer gives without the save. Elsewhere S says NXP-22 and the prompt
goes on. Nothing is drawn by the save or by the resume.
"""
from savesrig import read_saved
import json
import random
import re

import pytest

from nfl4.data.files import savedgame
from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras import penalty_flow as PF
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.saved import rules_for_saved_game
from nfl4.extras.state import ExtrasRecord
from nfl4.game.gamestate import GameState
from nfl4.extras.classic_radio import ClassicRadioRules
from nfl4.game.rules import CLASSIC, NEXT_DOWN
from nflrig import RecordingRules, nfl_engine_rig
from pagrig import make_rig, play
from randsources import ScriptedRandom
from test_nx_penalties import check, defensive_holding, game, play_ended, script, snap

ENTER, DOWN = 13, 40
STATS = savedgame.STATISTICS


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def board(state):
    x = state.extras
    return (state.wisoff, state.half, state.yard_line, state.down, state.to_go,
            tuple(tuple(getattr(state.stats[side], name) for name in STATS) for side in (1, 2)),
            tuple(x.flags), tuple(x.flag_yards))


def saved_at_the_prompt(tmp_path):
    """Defensive holding on an incomplete pass from the Bengals' 30, second and... the player presses S."""
    rig = game(tmp_path, answers=["s"])
    snap(rig)
    rig.engine.s.stats[1].pass_attempts += 1
    play_ended(rig)
    draws = defensive_holding(rig)
    script(rig, draws)
    step = rig.engine.field_play_end()
    check(rig, draws)
    return rig, step


# ----- the save at the prompt -----

def test_s_at_the_prompt_puts_the_declined_board_keeps_the_choice_and_saves(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path)
    s = rig.engine.s
    assert step == rig.engine.save_game
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 30, 2, 10)          # the play stood: second and 10
    assert s.stats[1].pass_attempts == 1 and s.extras.flags == [0, 0]
    pending = s.extras.pending_choice
    assert pending["id"] == "P09" and pending["side"] == 2 and pending["slot"] == 4
    assert pending["stats"][0][STATS.index("pass_attempts")] == 0             # the snap's statistics, for an accepted penalty
    assert rig.rules.penalty.events[-1][1] == "kept in the save"
    kept = []
    rig.engine.save_sink = kept.append
    assert step() is None and rig.engine.result.saved
    saved = savedgame.decode(savedgame.encode(kept[0]))
    assert json.loads(saved.extras)["pending_choice"] == pending
    assert X.text("NXH-47") in rig.rules.extra_help("116")


def load(tmp_path, saved, answers):
    rig = game(tmp_path, answers=answers)
    rig.rnd.source = ScriptedRandom([], strict=True)         # the resume draws nothing (a remark needs comments on)
    rig.engine.s.load(saved)
    return rig


def test_a_loaded_game_asks_the_choice_first_and_accepting_enforces_the_penalty(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path / "a")
    kept = []
    rig.engine.save_sink = kept.append
    step()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    rig2 = load(tmp_path / "b", saved, [ENTER])
    s = rig2.engine.s
    then = rig2.rules.resume_choice(s)
    said = texts(rig2)
    assert said[0] == X.text("NXP-23") and X.text("NXP-01") in said
    assert " defensive holding, on the Jets, ODef4. " in said
    assert " Kim if you accept the penalty, it will be first and 10 on your 35 yard line. " in said
    assert then == NEXT_DOWN and rig2.engine.continuation(then) == rig2.engine.position
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 35, 1, 10)
    assert s.stats[1].pass_attempts == 0 and s.stats[1].first_downs == 1      # erased; a first down by penalty
    assert s.extras.flags == [0, 1] and s.extras.flag_yards == [0, 5] and s.extras.pending_choice is None


def test_declining_after_the_load_leaves_the_play_as_it_stood(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path / "a")
    kept = []
    rig.engine.save_sink = kept.append
    step()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    rig2 = load(tmp_path / "b", saved, [DOWN, ENTER])
    s = rig2.engine.s
    assert rig2.rules.resume_choice(s) == NEXT_DOWN
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 30, 2, 10) and s.stats[1].pass_attempts == 1
    assert s.extras.flags == [0, 0] and rig2.rules.penalty.events[-1][1] == "declined"


def test_s_again_after_the_load_keeps_it_again(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path / "a")
    kept = []
    rig.engine.save_sink = kept.append
    step()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    rig2 = load(tmp_path / "b", saved, ["s"])
    s = rig2.engine.s
    then = rig2.rules.resume_choice(s)
    again = []
    rig2.engine.save_sink = again.append
    assert rig2.engine.continuation(then) == rig2.engine.save_game
    rig2.engine.save_game()
    assert json.loads(again[0].extras)["pending_choice"] == json.loads(kept[0].extras)["pending_choice"]
    assert (s.half, s.yard_line, s.down, s.to_go) == (2, 30, 2, 10)


def test_a_save_that_cannot_be_written_asks_the_choice_again(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path)
    rig.keys.answers.append(ENTER)
    rig.engine.save_sink = lambda record: False
    nxt = step()
    s = rig.engine.s
    assert not rig.engine.result.saved and nxt == rig.engine.position
    assert X.text("NXP-23") in texts(rig) and (s.yard_line, s.down) == (35, 1) and s.extras.flags == [0, 1]


def test_a_classic_program_that_says_no_plays_the_declined_board(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path / "a")
    kept = []
    rig.engine.save_sink = kept.append
    step()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    prog = make_rig(tmp_path / "b")
    prog.keys.answers.extend([DOWN, ENTER])
    assert isinstance(rules_for_saved_game(prog.game, saved), ClassicRadioRules)
    state = GameState()
    state.load(saved)
    assert (state.half, state.yard_line, state.down, state.to_go) == (2, 30, 2, 10)


def test_s_where_the_choice_cannot_be_kept_says_so_and_the_prompt_goes_on(tmp_path):
    rig = game(tmp_path, answers=["s", ENTER])
    flow = rig.rules.penalty
    flow.down = PEN.Down(1, 30, 1, 10)
    flag = PF.Flag(F.BY_ID["P09"][0], 2, 4)
    accepted = PEN.Result(PEN.NEW_DOWN, 1, 35, new_series=True)
    declined = PEN.Result(PEN.NEW_DOWN, 1, 30, 2, 10)
    assert flow.ask(rig.engine.s, flag, accepted, declined, None, PF.ACCEPT, can_save=False) == PF.ACCEPT
    said = texts(rig)
    assert said[-3:] == [X.text("NXP-A01"), X.text("NXP-22"), X.text("NXP-A01")]


@pytest.mark.parametrize("change", ["try", "last second", "turnover on downs", "untimed", "score"])
def test_can_save_only_a_new_down_for_the_team_with_the_ball(tmp_path, change):
    rig = game(tmp_path)
    flow, s = rig.rules.penalty, rig.engine.s
    flow.down = PEN.Down(1, 30, 1, 10)
    accepted = PEN.Result(PEN.NEW_DOWN, 1, 35, new_series=True)
    declined = PEN.Result(PEN.NEW_DOWN, 1, 30, 2, 10)
    assert flow.can_save(s, accepted, declined)
    if change == "try":
        flow.down = PEN.Down(1, 98, two_point=True)
    elif change == "last second":
        s.extras.left = 0
    elif change == "turnover on downs":
        declined = PEN.Result(PEN.NEW_DOWN, 2, 70, new_series=True)
    elif change == "untimed":
        accepted = PEN.Result(PEN.NEW_DOWN, 1, 35, new_series=True, untimed=True)
    else:
        declined = PEN.Result(PEN.TOUCHDOWN, 1, points=(6, 0))
    assert not flow.can_save(s, accepted, declined)


# ----- the record -----

def kept_choice(tmp_path):
    rig, step = saved_at_the_prompt(tmp_path)
    return rig.engine.s.extras.pending_choice


def test_the_kept_choice_goes_to_json_and_back_whole(tmp_path):
    pending = kept_choice(tmp_path)
    record = ExtrasRecord(penalties_on=True, pending_choice=pending)
    back = ExtrasRecord.from_json(record.to_json())
    assert back.pending_choice == pending and back == record
    assert "pending_choice" not in ExtrasRecord(penalties_on=True).to_json()


@pytest.mark.parametrize("damage", [
    lambda p: p.pop("qb"), lambda p: p.update(foul=999), lambda p: p.update(id="P01"), lambda p: p.update(side=3),
    lambda p: p.update(slot=18), lambda p: p.update(spot="x"), lambda p: p["down"].update(two_point=True),
    lambda p: p["down"].update(down=5), lambda p: p["accepted"].update(kind="touchdown"), lambda p: p["declined"].update(ball=2),
    lambda p: p["accepted"].update(untimed=True), lambda p: p["accepted"].update(points=[6, 0]),
    lambda p: p["accepted"].update(notes=["a\x07b"]), lambda p: p["stats"][0].pop(), lambda p: p["qb"][0].append(1),
    lambda p: p["stats"][1].__setitem__(3, "x"), lambda p: p["stats"][0].__setitem__(0, 10 ** 7),
    lambda p: p["accepted"].update(keeps_play=1), lambda p: p.update(extra=1),
])
def test_a_damaged_kept_choice_refuses_the_record(tmp_path, damage):
    pending = json.loads(json.dumps(kept_choice(tmp_path)))
    damage(pending)
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(ExtrasRecord(penalties_on=True, pending_choice=pending).to_json())


def test_a_kept_choice_without_penalties_is_refused(tmp_path):
    with pytest.raises(ValueError):
        ExtrasRecord.from_json(ExtrasRecord(penalties_on=False, pending_choice=kept_choice(tmp_path)).to_json())


# ----- whole games: the board after the answer is the same with and without the save -----

NXP04 = re.compile(r"^ \S.* if you accept the penalty, ")
ANSWERS = (X.text("NXP-A01"), X.text("NXP-A02"))


class Spy(RecordingRules):
    """Records the board at the first H10 after the player's prompt number `target` (the next down's board), and for a loaded game
    after its first prompt."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.armed = False
        self.boards = []
        self.prompts = 0
        self.target = 0

    def for_game(self):
        used = super().for_game()
        used.target, used.boards = self.target, self.boards
        return used

    def between_plays(self, state):
        if self.armed:
            self.armed = False
            self.boards.append(board(state))
        return super().between_plays(state)


def policy(rig, plan):
    """Menus by a seeded draw (never Save Game, never conceding); at the player's prompt number plan["at"] the key plan["key"] (S: when
    the prompt says NXP-22 the choice cannot be kept and the next prompt is tried); every other prompt Enter."""
    rng = random.Random(plan["seed"])

    def choose(keys):
        said = [t for t, _, _ in rig.said]
        last = said[-1] if said else ""
        if last.endswith("Save Game "):
            return DOWN
        if "concede" in last:
            return "n"
        if last in ANSWERS:
            n = sum(1 for t in said if NXP04.match(t))
            if n != plan["at"] or plan["done"]:
                return ENTER
            if len(said) > 1 and said[-2] == X.text("NXP-22"):
                plan["at"] += 1                       # this one cannot be kept: the next prompt
                return ENTER
            if plan["key"] == "s":
                return "s"
            plan["done"] = True
            plan["armed"]()
            return {"accept": "a", "decline": "d"}[plan["key"]]
        if last in (X.text("NXP-A01"), X.text("NXP-A02")) or last == X.text("NXP-22"):
            return ENTER
        roll = rng.random()
        if roll < 0.5:
            return ENTER
        if roll < 0.9:
            return str(rng.randint(1, 6))
        return DOWN
    return choose


def one_game(path, seed, plan, saved=None, sink=None):
    rig = make_rig(path, rng=random.Random(seed), fast=True, vtrnt=2)
    rules = Spy(auto_sides=(2,), penalties_on=True)
    rig.keys.policy = policy(rig, plan)

    def arm():
        rules.used.armed = True
    plan["armed"] = arm
    result = play(rig, rules=rules, saved=saved, save_sink=sink)
    return rig, rules, result


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("answer", ["accept", "decline"])
def test_a_whole_game_saved_at_a_prompt_and_loaded_gives_the_board_the_answer_gives_without_the_save(tmp_path, seed, answer):
    from nfl4.data.files.store import FileProgramStore
    store = FileProgramStore(str(tmp_path / "data"), str(tmp_path / "data" / "customize"))
    plan = {"seed": 40 + seed, "at": 1, "key": "s", "done": False}
    rig, rules, result = one_game(tmp_path / "a", 900 + seed, plan, sink=store.save_game)
    assert result.saved and rules.used.state.extras.pending_choice is not None
    at = plan["at"]
    saved = read_saved(store)
    assert json.loads(saved.extras)["pending_choice"] == rules.used.state.extras.pending_choice
    # the same game without the save: the same keys up to that prompt, then the answer
    base = {"seed": 40 + seed, "at": at, "key": answer, "done": False}
    rig_b, rules_b, result_b = one_game(tmp_path / "b", 900 + seed, base)
    assert result_b.scores is not None and len(rules_b.boards) == 1
    # the saved game loaded, the answer given at its first prompt
    loaded = {"seed": 5, "at": 1, "key": answer, "done": False}
    rig_c, rules_c, result_c = one_game(tmp_path / "c", 77, loaded, saved=saved)
    said = [t for t, _, _ in rig_c.said]
    assert X.text("NXP-23") in said and not any(NXP04.match(t) for t in said[:said.index(X.text("NXP-23"))])
    assert result_c.scores is not None and rules_c.boards[:1] == rules_b.boards


# ----- the review of SX.9: a kick-off's choice, a franchise game, every switch on and later prompts -----

def kicked(tmp_path, answers):
    """A kick-off return to the 28 with a foul by the kicking team (P24): the receivers (the player) choose."""
    from nfl4.game import outcome as O
    rig = game(tmp_path, answers=answers, wisoff=1, defense=2, half=2, yard_line=28)
    s = rig.engine.s
    flow = rig.rules.penalty
    flow.take_kickoff(s)
    flow.flags = [PF.Flag(F.BY_ID["P24"][0], 2, 3)]
    facts = PEN.PlayFacts(O.KICKOFF_RETURN, 28, offense_play=0, defense_play=0)
    return rig, flow.settle(s, None, facts)


@pytest.mark.parametrize("answer", ["accept", "decline"])
def test_a_kick_off_choice_is_kept_read_back_and_gives_the_board_of_the_answer(tmp_path, answer):
    keys = [ENTER] if answer == "accept" else [DOWN, ENTER]
    rig_a, then = kicked(tmp_path / "a", ["s"])
    kept = []
    rig_a.engine.save_sink = kept.append
    rig_a.engine.save_game()
    saved = savedgame.decode(savedgame.encode(kept[0]))
    record = ExtrasRecord.from_json(saved.extras)                 # a kick-off's down starts at the goal line (los 0): read back whole
    assert record.pending_choice["down"]["los"] == 0
    rig_c = load(tmp_path / "c", saved, keys)
    rig_c.rules.resume_choice(rig_c.engine.s)
    rig_b, then_b = kicked(tmp_path / "b", keys)
    if then_b is None:                                # the play stands: the engine counts the return's first down after the end point (Q19)
        rig_b.engine.s.stats[1].first_downs += 1
        rig_b.engine.s.down, rig_b.engine.s.to_go = 1, 10
    assert board(rig_c.engine.s) == board(rig_b.engine.s)


def test_a_franchise_game_saved_at_the_prompt_keeps_its_mark_and_its_choice(tmp_path):
    import random as _random
    from nfl4.extras.franchise.files import MemoryFiles
    from nfl4.extras.franchise.league import new_league
    from nfl4.extras.franchise.store import FranchiseStore
    from nfl4.game.names import load_surnames
    from nfl4.game.rnd import GameRandom
    rig, step = saved_at_the_prompt(tmp_path)
    kept = []
    rig.engine.save_sink = kept.append
    step()
    files = MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True
    store.league = new_league(GameRandom(_random.Random(3)), load_surnames(), "Kim", 4, "L3")
    store.league.schedule = [[2, 1, 1]] * 16
    store.league.gtp = 1
    store.save()
    assert store.save_game(kept[0])
    again = FranchiseStore(files)
    again.open(True)
    assert again.has_saved_game() and again.take_notices() == []
    saved = read_saved(again)
    record = ExtrasRecord.from_json(saved.extras)
    assert record.franchise is not None and record.pending_choice == rig.engine.s.extras.pending_choice


def wide_board(state):
    x = state.extras
    return board(state) + (state.quarter, x.left, x.running, x.pending, x.foul_clock, tuple(x.timeouts), tuple(x.used), x.warning_given,
                           x.warning_due, x.plays - x.handled, x.last_kind, x.last_offense, x.out_of_bounds, tuple(x.qb_runs),
                           tuple(x.qb_yards), x.unit, tuple(x.called), tuple(x.onside_tried), tuple(x.onside_recovered), x.extension,
                           x.no_snap, x.foul_by_offense)


class WideSpy(Spy):
    def between_plays(self, state):
        if self.armed:
            self.armed = False
            self.boards.append(wide_board(state))
        return RecordingRules.between_plays(self, state)


def every_switch_game(path, seed, plan, saved=None, sink=None):
    rig = make_rig(path, rng=random.Random(seed), fast=True, vtrnt=2)
    rules = WideSpy(auto_sides=(2,), penalties_on=True, onside_on=True, qb_on=True, challenges_on=True)
    rig.keys.policy = policy(rig, plan)

    def arm():
        rules.used.armed = True
    plan["armed"] = arm
    result = play(rig, rules=rules, saved=saved, save_sink=sink)
    return rig, rules, result


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("first", [2, 5])
@pytest.mark.parametrize("answer", ["accept", "decline"])
def test_every_switch_on_and_a_later_prompt_the_whole_record_after_the_answer_is_the_same_with_and_without_the_save(tmp_path, seed,
                                                                                                                   first, answer):
    from nfl4.data.files.store import FileProgramStore
    store = FileProgramStore(str(tmp_path / "data"), str(tmp_path / "data" / "customize"))
    plan = {"seed": 140 + seed, "at": first, "key": "s", "done": False}
    rig, rules, result = every_switch_game(tmp_path / "a", 1900 + seed, plan, sink=store.save_game)
    if not result.saved:
        pytest.skip("no prompt from this one on could be kept in this game")
    saved = read_saved(store)
    base = {"seed": 140 + seed, "at": plan["at"], "key": answer, "done": False}
    rig_b, rules_b, result_b = every_switch_game(tmp_path / "b", 1900 + seed, base)
    assert len(rules_b.boards) == 1
    loaded = {"seed": 5, "at": 1, "key": answer, "done": False}
    rig_c, rules_c, result_c = every_switch_game(tmp_path / "c", 77, loaded, saved=saved)
    assert X.text("NXP-23") in [t for t, _, _ in rig_c.said]
    assert rules_c.boards[:1] == rules_b.boards and result_c.scores is not None
