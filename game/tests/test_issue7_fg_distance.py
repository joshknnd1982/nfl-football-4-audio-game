"""GitHub issue 7 (a tester, 2026-11-07, on 0.16.20: "have radio announcer tell you the distance of the field goal being attempted. It
should be just like in a radio broadcast."), built in S-O (D-220). This is inspired by Jim Kitchen.

The radio play-by-play (F9, Rules, Play calls: radio, the default) now names the kick's length at its set-up ("Here comes Kim for a
42-yard field goal attempt."), calls a try of 50 yards or more a long one, a little excited, names the fair catch kick's length, and some
of the result calls say it again ("From 42 yards, right through!"). The length is the line of scrimmage to the goal line, plus the hold 7
yards back and the end zone's 10 (the original's help: "add seventeen yards"), the same number the N. F. L. rules' kick uses. The calls
draw only from the caller's own generator: the game, its draws and scores do not change. Plain calls keep the original's words."""
import random
import re
from types import SimpleNamespace

from nfl4.data.settings import Settings
from nfl4.extras import kick_flow as KF
from nfl4.extras import radio_calls as RC
from nfl4.speech.lift import GAIN, ROUTINE
from test_rc_radio_calls import classic_game, nfl_game
from nfl4.extras.classic_radio import ClassicRadioRules

YARDS = re.compile(r"\b(\d+)(?:-yard| yards)")
SET_UP = re.compile(r"field goal (try|attempt)|-yard try|-yarder|-yard attempt|try it from|fair catch kick|it's from \d+ yards", re.IGNORECASE)


def book_game(tmp_path, seed):
    """A game of the N. F. L. rules with a playbook, so the kicks of 2026 are played (kick_flow.kicks_on)."""
    from nflrig import QUARTERBACKS, RecordingRules, SimEngine
    from pagrig import make_rig
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
    rig.game.options.settings.game.nx_play_calls = "radio"
    rig.game.comtog_source = lambda: 0
    rules = RecordingRules(offense_book="west", defense_book="pressure", playbooks_on=True, broadcast_on=True)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, result, rig.said


def caller(yard_line, half, wisoff=1, calls="radio"):
    settings = Settings.defaults()
    settings.game.nx_play_calls = calls
    state = SimpleNamespace(teams={1: "Bengals", 2: "Jets"}, wisoff=wisoff, yard_line=yard_line, half=half)
    c = RC.RadioCalls(SimpleNamespace(state=state, play_calls="radio"))
    c.attach(SimpleNamespace(options=SimpleNamespace(settings=settings), rnd=None))
    return c


def said(c, text):
    out, level = c.call(text)
    return " ".join(out.split()), level


def test_every_set_up_call_has_the_length_and_the_right_article():
    for key in ("fg_in", "fg_in_long", "fck_in"):
        assert all("{d}" in v for v in RC.CALLS[key]), key
    assert sum("{d}" in v for v in RC.CALLS["fg_good"]) >= 3 and sum("{d}" not in v for v in RC.CALLS["fg_good"]) >= RC.MIN_RESULT_VARIANTS
    assert sum("{d}" not in v for v in RC.CALLS["fg_miss"]) >= RC.MIN_RESULT_VARIANTS


def test_the_set_up_names_the_length_in_the_defenses_half():
    # side 1's own half is half 2 (game/gamestate.own_half): on half 1 the ball is in the defense's half, 25 yards from its goal line
    c = caller(25, 1)
    text, level = said(c, " Kim is in for the field goal attempt ")
    assert "42" in text and "Kim" in text and level == ROUTINE
    assert re.search(r"\b42(-yard| yards)", text)


def test_a_long_try_is_called_a_long_one_and_a_little_excited():
    c = caller(40, 1)                                   # 40 + 17 = 57 yards
    text, level = said(c, " Kim is in for the field goal attempt ")
    assert "57" in text and "!" in text and level == GAIN


def test_from_the_own_half_the_length_counts_the_whole_field():
    c = caller(45, 2)                                   # side 1 on its own 45: 55 yards to go, a 72-yard kick
    assert "72" in said(c, " Kim is in for the field goal attempt ")[0]


def test_an_eighteen_and_eighty_yard_kick_take_an():
    for line, half in ((1, 1), (37, 2)):                # 18 yards; 100 - 37 + 17 = 80 yards
        c = caller(line, half)
        for _ in range(12):
            text = said(c, " Kim is in for the field goal attempt ")[0]
            assert not re.search(r"\b[Aa] (18|8\d)-yard", text), text


def test_the_fair_catch_kick_names_its_length():
    c = caller(30, 1)                                   # kicked from the catch: 30 + 10
    text, _level = said(c, " Kim lines up for a fair catch kick ")
    assert "40" in text and "fair catch" in text.lower()


def test_the_result_says_the_same_length_or_none():
    c = caller(25, 1)
    said(c, " Kim is in for the field goal attempt ")
    lengths = set()
    for _ in range(60):
        c.kick_distance = 42
        lengths.update(YARDS.findall(said(c, " is good ")[0]))
        c.kick_distance = 42
        lengths.update(YARDS.findall(said(c, " is wide to the left ")[0]))
    assert lengths == {"42"}
    fresh = caller(25, 1)                               # a result with no set-up heard: no variant that needs a length
    for _ in range(40):
        assert "{d}" not in said(fresh, " is good ")[0]


def test_a_new_play_forgets_the_length():
    c = caller(25, 1)
    said(c, " Kim is in for the field goal attempt ")
    assert c.kick_distance == 42
    said(c, " the Bengals break the huddle ")
    c.call(" Kim is in for the extra point attempt ")
    assert c.kick_distance is None


def test_plain_calls_keep_the_original_words():
    c = caller(25, 1, calls="plain")
    assert c.call(" Kim is in for the field goal attempt ") == (" Kim is in for the field goal attempt ", 0)


def test_nfl_rules_games_say_the_length_the_kick_is_planned_with(tmp_path, monkeypatch):
    planned = []
    real = KF.KickFlow.plan

    def recording(self, state, what):
        plan = real(self, state, what)
        if plan is not None and plan.what in (KF.FIELD_GOAL, KF.FAIR_CATCH_KICK) and not plan.fake:
            planned.append(plan.distance)
        return plan

    monkeypatch.setattr(KF.KickFlow, "plan", recording)
    heard = []
    for seed in (22, 23):
        planned_before = len(planned)
        _rig, _res, sents = book_game(tmp_path / str(seed), seed)
        game_heard = [int(YARDS.findall(t)[0]) for t, _r, _s in sents if SET_UP.search(t) and YARDS.search(t)
                     and "good" not in t]
        # a kick withdrawn by a time out and planned again is not set up twice (SZ.6): every length said is one that was planned
        assert set(game_heard) <= set(planned[planned_before:]), (game_heard, planned[planned_before:])
        heard += game_heard
    assert planned, "no field goal in two games"
    assert len(heard) >= len(set(planned))


def test_the_length_changes_no_game(tmp_path):
    rig_r, res_r, radio = nfl_game(tmp_path / "r", 24)
    rig_p, res_p, plain = nfl_game(tmp_path / "p", 24, "plain")
    assert res_r.scores == res_p.scores and rig_r.rnd.draws == rig_p.rnd.draws
    rig_c, res_c, classic = classic_game(tmp_path / "c", ClassicRadioRules(broadcast_on=True), comments=False)
    rig_b, res_b, bare = classic_game(tmp_path / "b", ClassicRadioRules(broadcast_on=True), "plain", comments=False)
    assert res_c.scores == res_b.scores and rig_c.rnd.draws == rig_b.rnd.draws
    fg_calls = [t for t in classic if SET_UP.search(t) and YARDS.search(t) and "good" not in t]     # not a result call
    fg_plain = [t for t in bare if "is in for the field goal attempt" in t]
    assert fg_plain and len(fg_calls) == len(fg_plain)            # every set-up of the Classic game names its length
    assert not any("is in for the field goal attempt" in t for t in classic)
