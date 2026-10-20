"""The T key calls a timeout anywhere in a game until the play is run (nfl4 only, rule 0.13; owner rule 0.22, playbook 7.16, D-084;
PX SX.2b, requirement NX-T). This is inspired by Jim Kitchen.

The tests of playbook 7.16, in this order: T in every play menu and every question, in the snap count and the set-up of a kick (the play
is withdrawn and the menu comes again), during a live play (kept, granted when it ends), the three limits and their sentences, no menu
item on the letter T, F5 (which is "t" in this key model, B-W6) never calling one, T in a typed box, the speech cut at once, the global
and F9 menus that close on T, the log line, Classic unchanged. Every draw is planned on a strict scripted source; the speech is the fake
SAPI's list of (text, speaker, rate step).
"""
from pathlib import Path

import pytest

from nfl4.data import debuglog
from nfl4.extras import fouls_2026 as F
from nfl4.extras import nx_texts as X
from nfl4.extras import penalties as PEN
from nfl4.extras import penalty_flow as PF
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import phrases as P
from nfl4.game.pag import PlayWithdrawn
from nfl4.game.rules import TIMEOUT_GRANTED
from nflrig import nfl_engine_rig
from pagrig import Draws, engine_rig
from randsources import ScriptedRandom

ENTER, ESCAPE, UP, DOWN, F1, F5 = 13, 27, 38, 40, 112, 116
T_KEY = 84
STATE = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10)
OUT = " time out called by the Bengals. "


def script(rig, draws: Draws):
    rig.rnd.source = ScriptedRandom(draws.values, strict=True)
    rig.rnd.trace = []


def check(rig, draws: Draws):
    assert rig.rnd.trace == draws.sizes, (rig.rnd.trace, draws.sizes)
    assert rig.rnd.source.left == 0


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def stops(rig) -> int:
    return sum(1 for kind, _ in rig.sapi.events if kind == "stop")


def called(rig) -> list[int]:
    return list(rig.engine.s.extras.used)


def quiet_snap_count(d: Draws) -> Draws:
    """0x43fe61 to 0x440cb2 with the fewest draws: the line, the huddle broken, " hut 1 ", no " hut 2 ", no call, no extra hut."""
    return d.rnd(4, 1).rnd(10, 1).rady().rnd(7, 1).rnd(5, 3).below(4, 0).rady()


def press_t_at(rig, method: str, nth: int):
    """The player presses T just before the nth call of the engine's `dy` or `rady`: the pause pumps the keys, as the original's do."""
    engine = rig.engine
    original = getattr(engine, method)
    count = {"n": 0}

    def wrapper(*args, **kwargs):
        count["n"] += 1
        if count["n"] == nth:
            rig.keys.post(T_KEY)
            rig.keys.post_char("t")
        return original(*args, **kwargs)
    setattr(engine, method, wrapper)


def drive(engine, step, stop=("play_menu", "offense_menu", "defense_menu")):
    """Run the engine's steps as PlayEngine.run does, with its catch of a withdrawn play. Returns the step that is next when one of
    `stop` comes up and the names of the steps run."""
    names = []
    while step is not None:
        if step.__name__ in stop:
            return step, names
        names.append(step.__name__)
        try:
            step = step()
        except PlayWithdrawn as withdrawal:
            names.append("withdrawn")
            step = engine.withdrawn(withdrawal)
    return None, names


def scene(tmp_path, answers=(), extras=None, rules=None, **state):
    fields = dict(STATE)
    fields.update(state)
    base = dict(left=500, pending=33, running=True)
    base.update(extras or {})
    return nfl_engine_rig(tmp_path, answers=answers, rules=rules, extras=base, **fields)


# ----- NX-T1: the menus and the questions -----

def test_t_calls_the_timeout_in_the_offense_menu_with_no_enter_and_the_menu_comes_again(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER])
    draws = Draws().below(6, 1)                                      # u: 4 of the 33 seconds that would run
    script(rig, draws)
    step = rig.engine.offense_menu()
    check(rig, draws)
    assert step == rig.engine.offense_chosen and rig.engine.s.offense_play == 1
    assert texts(rig) == [" Kim" + P.SELECT_OFFENSE, " 1. Line Plunge ", OUT, " you have 2 time outs left. ",
                          " Kim" + P.SELECT_OFFENSE, " 1. Line Plunge "]
    x = rig.engine.s.extras
    assert (x.timeouts, x.used, x.called) == ([2, 3], [1, 0], [True, False]) and (x.left, x.pending, x.running) == (496, 0, False)


def test_t_calls_the_timeout_in_the_defense_menu(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER], wisoff=2, defense=1, extras=dict(pending=0, running=False))
    script(rig, Draws().rnd(9, 3))                                   # the computer's offense draw, after the choice
    rig.engine.defense_menu()
    assert texts(rig)[:5] == [" Kim" + P.SELECT_DEFENSE, " 1. Goal Line ", OUT, " you have 2 time outs left. ",
                              " Kim" + P.SELECT_DEFENSE]
    assert called(rig) == [1, 0]


def test_t_calls_the_timeout_in_the_two_point_menu_before_the_try(tmp_path):
    """A timeout before a try is allowed and charged (11-3-1); the try's menu comes again with its items 1 to 5."""
    rig = scene(tmp_path, answers=["t", ENTER], two_point=True, yard_line=2, extras=dict(pending=0, running=False))
    script(rig, Draws())
    rig.engine.offense_menu()
    said = texts(rig)
    assert said[:2] == [" Kim" + P.SELECT_OFFENSE, " 1. Line Plunge "] and OUT in said and said[-2:] == [said[0], said[1]]
    assert called(rig) == [1, 0]


def test_the_time_out_item_still_works_by_its_number_and_enter(tmp_path):
    rig = scene(tmp_path, answers=["8", ENTER, ENTER], extras=dict(pending=0, running=False))
    script(rig, Draws())
    rig.engine.offense_menu()
    assert texts(rig)[:4] == [" Kim" + P.SELECT_OFFENSE, " 1. Line Plunge ", " 8. Time Out ", OUT]
    assert called(rig) == [1, 0]


def test_t_in_the_onside_question_calls_the_timeout_and_the_question_is_asked_again(tmp_path):
    rules = NflRules(timeouts_on=True, auto_sides=(2,), onside_on=True, onside_always=True)
    rig = scene(tmp_path, answers=["t", "y", ENTER], rules=rules, wisoff=2, defense=1, half=1, yard_line=0, quarter=1,
                extras=dict(left=900, pending=0, running=False))
    script(rig, Draws())
    assert rig.rules.onside.ask(rig.engine.s) is True
    said = texts(rig)
    question = " Kim do you wish to try an onside kick "
    assert said[:3] == [question, " no ", OUT] and said[4:6] == [question, " no "] and said[-1] == " yes "
    assert called(rig) == [1, 0]


def test_t_in_the_accept_or_decline_question_calls_the_timeout_and_asks_again(tmp_path):
    rules = NflRules(timeouts_on=True, auto_sides=(2,), penalties_on=True)
    rig = scene(tmp_path, answers=["t", ENTER], rules=rules, extras=dict(pending=0, running=False))
    flow = rig.rules.penalty
    flow.down = PEN.Down(1, 30, 1, 10)
    flag = PF.Flag(F.BY_ID["P09"][0], 2, 4)
    accepted = PEN.Result(PEN.NEW_DOWN, 1, 35, new_series=True)
    declined = PEN.Result(PEN.NEW_DOWN, 1, 30, 2, 10)
    assert flow.ask(rig.engine.s, flag, accepted, declined, None, PF.ACCEPT) == PF.ACCEPT
    said = texts(rig)
    assert OUT in said and said.count(X.text("NXP-A01")) == 2 and said.index(OUT) < len(said) - 3
    assert called(rig) == [1, 0]


def test_t_in_the_choice_of_the_extra_point_is_a_timeout_before_the_try_and_the_choice_is_asked_again(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER], extras=dict(pending=0, running=False))
    script(rig, Draws())
    step = rig.engine.extra_point_choice()
    assert step == rig.engine.extra_point and rig.engine.t_back == rig.engine.extra_point_choice
    said = texts(rig)
    assert said[:2] == [" Kim" + P.SELECT, P.KICK_FOR_EXTRA_POINT] and OUT in said and said[-2:] == [said[0], said[1]]
    assert called(rig) == [1, 0]


def test_a_time_out_called_by_t_during_the_run_out_question_is_kept_because_the_ball_is_live(tmp_path):
    rig = scene(tmp_path, answers=["t", ENTER], returner=1, extras=dict(pending=0, running=False))
    rig.engine.t_live = True
    script(rig, Draws())
    assert rig.engine.run_it_out() == rig.engine.kick_return
    said = texts(rig)
    assert X.text("NXT-15") in said and OUT not in said and called(rig) == [0, 0] and rig.rules.timeout_kept


# ----- NX-T2: the snap count and the set-up of a kick: the play is withdrawn -----

COUNT_POINTS = [("dy", 1, Draws().rnd(4, 1).rnd(10, 1)),                       # the huddle is said, the pause before " hut 1 "
                ("rady", 1, Draws().rnd(4, 1).rnd(10, 1).rady()),              # after " hut 1 "
                ("rady", 2, quiet_snap_count(Draws()))]                        # the last pause, just before " Hike! "


@pytest.mark.parametrize("method,nth,before", COUNT_POINTS)
def test_t_in_the_snap_count_withdraws_the_play_and_the_menu_comes_again(tmp_path, method, nth, before):
    """Nothing is drawn for the play (no ball carrier, no defenders, no snap phrase), the runoff the snap took is given back, the speech
    stops, the timeout is called and the play menu is spoken again from its top."""
    rig = scene(tmp_path, offense_play=1, defense_play=1)
    draws = Draws().extend(before).below(6, 1)
    script(rig, draws)
    press_t_at(rig, method, nth)
    engine = rig.engine
    with pytest.raises(PlayWithdrawn) as caught:
        engine.snap()
    check(rig, draws)
    assert engine.withdrawn(caught.value) == engine.play_menu
    said = texts(rig)
    assert P.HIKE not in said and said[-2:] == [OUT, " you have 2 time outs left. "]
    x = engine.s.extras
    assert (x.timeouts, x.used, x.called) == ([2, 3], [1, 0], [True, False])
    assert (x.left, x.pending, x.running) == (496, 0, False)         # the 33 seconds the snap took were given back, then u = 4 ran
    assert not engine.t_live and engine.t_back is None


def test_t_in_the_snap_count_does_not_count_a_repeat_of_the_computers_choice(tmp_path):
    rig = scene(tmp_path, offense_play=2)
    engine, s = rig.engine, rig.engine.s
    s.previous_play, s.repeats = 2, 0
    script(rig, Draws().rnd(6, 3).rnd(2, 2))                         # the defense; the same play twice: matched with 1 in 2 (not here)
    assert engine.offense_chosen() == engine.snap
    assert (s.previous_play, s.repeats) == (2, 1)
    script(rig, Draws().rnd(4, 1).rnd(10, 1).below(6, 0))
    press_t_at(rig, "dy", 1)
    with pytest.raises(PlayWithdrawn) as caught:
        engine.snap()
    engine.withdrawn(caught.value)
    assert (s.previous_play, s.repeats) == (2, 0)                    # as before the choice


def test_the_whole_run_goes_back_to_the_menu_and_the_next_snap_is_a_new_one(tmp_path):
    rig = scene(tmp_path, answers=[ENTER], offense_play=1, defense_play=1)
    engine = rig.engine
    draws = Draws().rnd(4, 1).rnd(10, 1).below(6, 1)
    script(rig, draws)
    press_t_at(rig, "dy", 1)
    step, names = drive(engine, engine.snap)
    assert names == ["snap", "withdrawn"] and step == engine.play_menu
    check(rig, draws)


def test_t_in_the_set_up_of_a_field_goal_withdraws_the_kick(tmp_path):
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20)
    draws = Draws().rady().below(6, 1)                               # the first pause of the set-up, then u
    script(rig, draws)
    press_t_at(rig, "rady", 1)
    engine = rig.engine
    step, names = drive(engine, engine.snap)
    check(rig, draws)
    assert names == ["snap", "field_goal", "withdrawn"] and step == engine.play_menu and called(rig) == [1, 0]
    assert P.KICK_HUT_1 not in texts(rig)
    assert (rig.game.qorp, rig.game.ptf) == (1, 0)                    # the punter's voice and the speech log's flag do not stay on


def test_t_in_the_set_up_of_the_extra_point_goes_back_to_the_choice(tmp_path):
    rig = scene(tmp_path, answers=[ENTER], extras=dict(pending=0, running=False))
    engine = rig.engine
    script(rig, Draws())
    assert engine.extra_point_choice() == engine.extra_point
    draws = Draws().rady()
    script(rig, draws)
    press_t_at(rig, "rady", 1)
    with pytest.raises(PlayWithdrawn) as caught:
        engine.extra_point()
    assert caught.value.back == engine.extra_point_choice and called(rig) == [1, 0]


def test_t_in_the_set_up_of_a_kick_off_calls_the_timeout_and_the_kick_off_goes_on(tmp_path):
    """No play is called before a kick-off, so nothing is withdrawn: the speech is cut, the timeout is called, and the kick-off goes on."""
    rig = scene(tmp_path, wisoff=1, defense=2, half=1, yard_line=0, extras=dict(pending=0, running=False))
    engine = rig.engine
    press_t_at(rig, "dy", 1)
    draws = Draws().rnd(2, 1).rnd(7, 3).rady().rady()
    script(rig, draws)
    step = engine.kick_off()
    check(rig, draws)
    assert step == engine.run_it_out and called(rig) == [1, 0]
    said = texts(rig)
    assert said.index(OUT) < said.index(P.KICKOFF_UP)


# ----- NX-T3: the live play, the limits, the keys that are not T -----

def test_t_during_a_live_play_is_kept_and_granted_when_the_play_ends_not_before(tmp_path):
    rig = scene(tmp_path, extras=dict(pending=0, running=False, plays=1, handled=0, last_offense=1), quarter=2)
    engine, rules = rig.engine, rig.rules
    before = stops(rig)
    engine.go_live()
    rig.keys.post(T_KEY)
    assert stops(rig) == before                                      # a live play is not cut
    rig.keys.pump()
    assert rules.timeout_kept and called(rig) == [0, 0] and texts(rig) == []
    rules.after_play = True
    rules.between_plays(engine.s)                                    # the play ended: H10 grants it before the next prompt
    assert not rules.timeout_kept and called(rig) == [1, 0] and OUT in texts(rig)
    assert rig.engine.s.extras.timeouts == [2, 3]


def test_a_request_kept_during_a_play_is_granted_at_the_start_of_the_next_menu(tmp_path):
    rig = scene(tmp_path, answers=[ENTER], extras=dict(pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    engine.go_live()
    rig.keys.post(T_KEY)
    rig.keys.pump()
    engine.t_live = False                                            # the end point of the play
    engine.offense_menu()
    assert texts(rig)[:3] == [OUT, " you have 2 time outs left. ", " Kim" + P.SELECT_OFFENSE]


def test_a_timeout_between_the_end_of_a_play_and_the_next_menu_stops_the_whole_runoff(tmp_path):
    """T while the result is told (the play is over, H10 has not run): granted at once, and no runoff is drawn for the play."""
    rig = scene(tmp_path, extras=dict(pending=0, running=False, plays=1, handled=0, last_offense=1))
    engine, rules = rig.engine, rig.rules
    rules.after_play = True
    rig.keys.post(T_KEY)
    rig.keys.pump()
    assert called(rig) == [1, 0] and rules.review.clock_held


@pytest.mark.parametrize("extras,sentence", [(dict(timeouts=[0, 3]), "NXT-04"), (dict(called=[True, False]), "NXT-05")])
def test_a_refused_t_says_one_sentence_and_the_snap_count_goes_on(tmp_path, extras, sentence):
    """Also the second T of one dead-ball period: the snap's own bookkeeping ends that period, but the snap count is still in it."""
    rig = scene(tmp_path, offense_play=1, defense_play=1, extras=dict(pending=0, running=False, **extras))
    draws = Draws().extend(quiet_snap_count(Draws())).rnd(6, 1).rnd(17, 1).rnd(17, 2)
    script(rig, draws)
    press_t_at(rig, "dy", 1)
    engine = rig.engine
    assert engine.snap() == engine.snap_phrase
    check(rig, draws)
    said = texts(rig)
    assert X.text(sentence) in said and said.index(X.text(sentence)) < said.index(P.HIKE) and OUT not in said
    assert called(rig) == [0, 0] and engine.t_live


def test_t_with_no_time_left_says_so_and_the_menu_goes_on(tmp_path):
    """The two-point try is untimed: at 0:00 it is still played, but no timeout can be granted then."""
    rig = scene(tmp_path, answers=["t", ENTER], two_point=True, yard_line=2, extras=dict(left=0, pending=0, running=False))
    script(rig, Draws())
    rig.engine.offense_menu()
    said = texts(rig)
    assert said[:4] == [" Kim" + P.SELECT_OFFENSE, " 1. Line Plunge ", X.text("NXT-16"), " Kim" + P.SELECT_OFFENSE]
    assert called(rig) == [0, 0]


def test_t_is_never_the_letter_of_an_item_in_any_play_menu(tmp_path):
    for kwargs in (dict(), dict(qb_on=True), dict(challenges_on=True), dict(penalties_on=True), dict(timeouts_on=False)):
        rig = scene(tmp_path / ("m%d" % len(kwargs)), rules=NflRules(**kwargs))
        for items in (rig.rules.offense_menu(rig.engine.s, False), rig.rules.offense_menu(rig.engine.s, True),
                      rig.rules.defense_menu(rig.engine.s)):
            assert all(item.letter != "t" for item in items)


def test_f5_is_not_the_t_key_it_looks_like_in_this_key_model(tmp_path):
    """F5 (code 116) is "t" in a VB6 port's character field (B-W6): the help runs, no timeout is called."""
    rig = scene(tmp_path, answers=[F5, ("end",), ENTER], extras=dict(pending=0, running=False))
    script(rig, Draws())
    rig.engine.offense_menu()
    assert called(rig) == [0, 0] and OUT not in texts(rig) and rig.keys.char != "t"


def test_t_in_a_typed_box_is_a_letter(tmp_path, monkeypatch):
    rig = scene(tmp_path)
    monkeypatch.setattr(debuglog, "typing_now", lambda: True)
    assert not rig.engine.t_armed
    rig.keys.post(T_KEY)
    assert rig.keys.timeout_posts == 0                               # no timeout key: the speech is not cut, the key stays a plain key
    rig.keys.pump()
    assert called(rig) == [0, 0] and rig.keys.code_text == "84"


def test_t_before_the_game_is_in_play_is_a_plain_key(tmp_path):
    rig = scene(tmp_path)
    rig.engine.game_on = False
    rig.keys.post(T_KEY)
    assert rig.keys.timeout_posts == 0
    rig.keys.pump()
    assert called(rig) == [0, 0]


# ----- quickly: the speech is cut at the moment the key is pressed -----

def test_the_speech_is_cut_the_moment_t_is_posted_by_the_window_thread(tmp_path):
    rig = scene(tmp_path, extras=dict(pending=0, running=False))
    before = stops(rig)
    rig.keys.post(T_KEY)                                              # the window thread; the game thread has not pumped yet
    assert stops(rig) == before + 1 and rig.keys.timeout_posts == 1
    rig.keys.pump()
    assert rig.keys.timeout_posts == 0


def test_a_text_is_not_started_while_a_t_key_waits_to_be_taken(tmp_path):
    """The window posted T while the game thread was inside a long text: the next text is not said before the key is taken."""
    rig = scene(tmp_path, extras=dict(pending=0, running=False))
    rig.keys.post(T_KEY)
    rig.game.say5(" a sentence after the key ")
    assert texts(rig)[0] == OUT and texts(rig)[-1] == " a sentence after the key "


# ----- the menus that read their own keys, and the global menus -----

def test_t_closes_the_help_menu_and_calls_the_timeout(tmp_path):
    rig = scene(tmp_path, extras=dict(pending=0, running=False))
    hot = rig.game.hotkeys
    rig.keys.post(T_KEY)
    rig.keys.code_text = "116"
    hot.dispatch("116")                                               # F5 starts; T is waiting; its wait takes the key and closes the menu
    assert called(rig) == [1, 0] and rig.keys.code_text == "112" and hot.depth == 0
    assert rig.keys.resumed == TIMEOUT_GRANTED


def test_t_closes_f9_during_a_game_and_calls_the_timeout(tmp_path):
    rig = scene(tmp_path, answers=["t"], extras=dict(pending=0, running=False))
    rig.game.functions.run()
    assert called(rig) == [1, 0] and OUT in texts(rig) and rig.keys.code_text == "112"


# ----- the log -----

def test_the_log_names_the_moment_the_result_and_the_reason(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    rig = scene(tmp_path / "rig", answers=["t", "t", ENTER], extras=dict(pending=0, running=False))
    script(rig, Draws())
    rig.engine.offense_menu()
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if "timeout_key" in line]
    assert len(lines) == 2
    assert "dead ball" in lines[0] and "granted" in lines[0]
    assert "refused" in lines[1] and "called" in lines[1]


# ----- Classic is the original -----

def test_classic_keeps_the_key_of_the_original(tmp_path):
    rig = engine_rig(tmp_path, answers=["t", ENTER], **STATE)
    rig.rnd.source = ScriptedRandom([], strict=True)
    rig.keys.post(T_KEY)
    assert rig.keys.timeout_posts == 0 and not rig.engine.t_armed
    rig.keys.pump()
    assert rig.keys.code_text == "84"                                 # an unknown key of the original's menus
    rig.engine.offense_menu()
    said = [t for t, _, _ in rig.said]
    assert "t" in said and not any("time out" in t for t in said)


def test_the_resumed_marker_of_a_wait_is_cleared_by_the_next_wait(tmp_path):
    rig = scene(tmp_path)
    rig.keys.hand_back(TIMEOUT_GRANTED)
    assert rig.keys.resumed == TIMEOUT_GRANTED
    rig.keys.clk()
    assert rig.keys.resumed == "" and rig.keys.take_resumed() == ""


def test_t_at_a_press_any_key_screen_is_that_key_and_the_timeout_comes_at_the_next_menu(tmp_path):
    """After a score or at the end of a period the game waits for any key: T is that key (nothing is repeated, nothing is replayed),
    and the timeout is called at the first menu or question that follows."""
    rig = scene(tmp_path, answers=["t", ENTER], extras=dict(pending=0, running=False))
    script(rig, Draws())
    engine = rig.engine
    engine.key_wait()
    assert rig.rules.timeout_kept and called(rig) == [0, 0] and texts(rig) == []
    engine.offense_menu()
    assert called(rig) == [1, 0] and texts(rig)[:3] == [OUT, " you have 2 time outs left. ", " Kim" + P.SELECT_OFFENSE]


# ----- what the first mutation check found untested (SX.2b) -----

def test_t_in_the_set_up_of_a_kick_after_the_punter_calls_the_snap_resets_his_voice_and_the_speech_log_flag(tmp_path):
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20)
    draws = Draws().rady().rady().below(6, 1)                       # the first pause, the pause after " hut 1 ", then u
    script(rig, draws)
    press_t_at(rig, "rady", 2)
    engine = rig.engine
    step, names = drive(engine, engine.snap)
    assert names == ["snap", "field_goal", "withdrawn"] and step == engine.play_menu
    assert (rig.game.qorp, rig.game.ptf) == (1, 0) and called(rig) == [1, 0]


class Stop(Exception):
    pass


def stop_at(rig, method: str, nth: int):
    engine = rig.engine
    original = getattr(engine, method)
    count = {"n": 0}

    def wrapper(*args, **kwargs):
        count["n"] += 1
        if count["n"] == nth:
            raise Stop()
        return original(*args, **kwargs)
    setattr(engine, method, wrapper)


def test_t_after_the_kick_is_snapped_is_kept_not_granted_the_kick_is_live(tmp_path):
    """The field goal: the pauses after the punter's " Hike! " belong to a live kick; T there waits for the end of the play."""
    rig = scene(tmp_path, offense_play=6, defense_play=1, yard_line=20, extras=dict(pending=0, running=False))
    draws = Draws().rady().rady().rnd(3, 2).rnd(3, 1).rnd(3, 1).rady().rady().rady()   # set-up; hut 1; no hut 2/3; one hut (its draw); 3 pauses
    script(rig, draws)
    press_t_at(rig, "rady", 5)                                              # the pause after the kick is snapped
    stop_at(rig, "rady", 6)
    engine = rig.engine
    with pytest.raises(Stop):
        drive(engine, engine.snap)
    assert rig.rules.timeout_kept and called(rig) == [0, 0] and engine.t_live


def test_t_after_the_kick_off_is_made_is_kept(tmp_path):
    rig = scene(tmp_path, wisoff=1, defense=2, half=1, yard_line=0, extras=dict(pending=0, running=False))
    script(rig, Draws().rnd(2, 1).rnd(7, 3).rady().rady())
    press_t_at(rig, "rady", 1)                                              # the first pause after the kick
    assert rig.engine.kick_off() == rig.engine.run_it_out
    assert rig.rules.timeout_kept and called(rig) == [0, 0]


def test_t_after_the_onside_kick_is_made_is_kept(tmp_path):
    from nfl4.extras import tuning as T
    rules = NflRules(timeouts_on=True, auto_sides=(2,), onside_on=True, onside_always=True)
    rig = scene(tmp_path, rules=rules, wisoff=2, defense=1, half=1, yard_line=0, quarter=4,
                extras=dict(left=400, pending=0, running=False, kick_from=35))
    low, high = T.ONSIDE_DISTANCE
    script(rig, Draws().rady(0).below(high - low + 1, 2).below(100, 5))     # the pause, the distance, the kicking team recovers
    original = rig.game.rady

    def rady(site=None):
        rig.keys.post(T_KEY)
        rig.keys.post_char("t")
        original(site)
    rig.game.rady = rady
    rig.rules.onside_kick(rig.engine.s)
    assert rig.rules.timeout_kept and called(rig) == [0, 0]


def test_the_final_whistle_ends_the_t_key(tmp_path):
    rig = scene(tmp_path, answers=[ENTER] * 6, quarter=4, extras=dict(left=0, pending=0, running=False))
    s = rig.engine.s
    s.stats[1].score, s.stats[2].score = 21, 10
    assert rig.engine.t_armed
    step = rig.engine.game_end()
    assert not rig.engine.game_on and step is not None


def test_the_timeout_cuts_what_is_being_said_by_itself_too(tmp_path):
    """Not only the window thread's cut: the rules stop the speech when they take the key (a test or another host without the thread)."""
    rig = scene(tmp_path, extras=dict(pending=0, running=False))
    before = stops(rig)
    rig.rules.timeout_key(rig.engine.s, False)
    assert stops(rig) > before
