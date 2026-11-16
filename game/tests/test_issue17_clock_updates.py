"""GitHub issue 17 (nfl4 only, rule 0.13; D-244): F9, Rules, Clock updates. This is inspired by Jim Kitchen.

The tester: (1) "Even after a player is pushed out of bounds the clock still continues to run"; (2) "You have no way to know when the clock has
started to wind"; (3) "You have no way to get the current time remaining as the clock winds down". The game follows the N. F. L. rule (4-3-2 (a)):
out of bounds stops the clock until the snap only in the last 2:00 of the first half and the last 5:00 of the second; before them it starts again
on the ready signal. With Clock updates on (the default) the game says so after every play, F4 says the time as it winds while the player
chooses (the runoff drawn as before, never more), and a time out stops it where F4 said. Off, everything is as before. No draw changes.
"""
from pathlib import Path

import pytest
from test_issue11_14_followups import scene

from nfl4.data import debuglog, settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import clock as C
from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.state import ExtrasRecord
from nfl4.game.gamestate import GameState
from nfl4.game.key_list import ROWS
from nfl4.game.rnd import GameRandom
from randsources import ScriptedRandom, below_value

RUNNING, STOPPED, READY, HELD = X.text("NXC-01"), X.text("NXC-02"), X.text("NXC-44"), X.text("NXC-45")


class Time:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class FakeGame:
    """What the clock reads of the game: its settings, its clock, say_clock."""

    def __init__(self, news):
        self.clock = Time()
        self.said = []
        settings = type("G", (), {"nx_clock_news": news})()
        self.options = type("O", (), {"settings": type("S", (), {"game": settings})()})()

    def say_clock(self, text):
        self.said.append(text)


def strict(*pairs):
    rnd = GameRandom(ScriptedRandom([below_value(n, k) for n, k in pairs], strict=True))
    rnd.trace = []
    return rnd


def make(news, quarter=1, left=600, **extras):
    state = GameState()
    state.quarter = quarter
    state.extras = ExtrasRecord(left=left, period=min(quarter, 5), **extras)
    game = FakeGame(news)
    return C.NflPeriodClock(game, state), state, game


# ----- the clock itself -----

def test_off_f4_says_the_time_at_the_end_of_the_last_play_as_before():
    clock, state, game = make(False)
    clock.runoff(strict((11, 5)), True, False, 0)                       # 35 seconds pending
    game.clock.now += 20
    clock.speak()
    assert game.said == [" 10 minutes  0 seconds remaining in the first quarter. "] or game.said[0].startswith(" 10 minutes")
    assert RUNNING not in game.said[0] and clock.wound() == 0


def test_on_f4_says_the_time_as_it_runs_down_and_never_past_the_runoff():
    clock, state, game = make(True)
    clock.runoff(strict((11, 5)), True, False, 0)
    assert state.extras.pending == 35
    game.clock.now += 12.7
    clock.speak()
    assert game.said[-1].startswith(" 9 minutes  48 seconds remaining") and game.said[-1].endswith(RUNNING)
    game.clock.now += 100                                               # the player waits long: the clock stops at the snap's time
    assert clock.wound() == 35 and clock.time_now() == 565
    assert clock.before_snap() is False and state.extras.left == 565    # the snap applies the whole runoff, as before


def test_the_snap_applies_the_same_runoff_on_and_off():
    for news in (False, True):
        clock, state, game = make(news)
        clock.runoff(strict((11, 3)), True, False, 0)
        game.clock.now += 5                                             # a quick player
        clock.before_snap()
        assert state.extras.left == 600 - (T.RUNOFF_NORMAL[0] + 3)


def test_after_out_of_bounds_early_the_clock_waits_for_the_ready_signal_then_winds():
    clock, state, game = make(True, quarter=1, left=300)
    rnd = strict((11, 10), (4, 3))                                      # 40 drawn, the ready signal cuts 3 + its low end
    pending = clock.runoff(rnd, True, True, 0)
    cut = T.READY_SIGNAL_CUT[0] + 3
    assert pending == 40 - cut and clock.ready_cut == cut and rnd.trace == [11, 4]
    assert clock.waiting_for_ready() and clock.state_text() == READY and clock.wound() == 0
    game.clock.now += cut + 5
    assert not clock.waiting_for_ready() and clock.state_text() == RUNNING and clock.wound() == 5


def test_a_stopped_clock_says_stopped_and_does_not_wind():
    clock, state, game = make(True)
    clock.runoff(strict(), False, False, 0)
    game.clock.now += 30
    clock.speak()
    assert game.said[-1].endswith(STOPPED) and clock.time_now() == 600


def test_a_time_out_stops_the_clock_where_f4_said_with_the_same_draw():
    clock, state, game = make(True, quarter=4, left=100, pending=30, running=True)
    clock.wind_from = game.clock.now
    game.clock.now += 20
    rnd = strict((6, 2))                                                # the signal's u is drawn as before
    assert clock.stop_for_timeout(rnd) == 20 and state.extras.left == 80 and rnd.trace == [6]
    clock, state, game = make(True, quarter=4, left=100, pending=30, running=True)
    clock.wind_from = game.clock.now
    game.clock.now += 1                                                 # a quick T: the signal's seconds, as before
    assert clock.stop_for_timeout(strict((6, 2))) == T.TIMEOUT_SIGNAL[0] + 2


def test_off_a_time_out_uses_only_the_signal_as_before():
    clock, state, game = make(False, quarter=4, left=100, pending=30, running=True)
    clock.wind_from = game.clock.now
    game.clock.now += 20
    assert clock.stop_for_timeout(strict((6, 2))) == T.TIMEOUT_SIGNAL[0] + 2


def test_a_game_with_no_settings_has_it_off():
    state = GameState()
    state.extras = ExtrasRecord(left=600, period=1)
    assert C.NflPeriodClock(object(), state).news_on() is False


# ----- after the play (H10) -----

def after_play(tmp_path, news, quarter, left, oob=False, kind="run", logs=None):
    rig = scene(tmp_path, quarter=quarter, extras=dict(plays=1, handled=0, last_offense=1, last_kind=kind, running=True, pending=0,
                                                       left=left, period=quarter, out_of_bounds=oob, timeouts_on=False))
    rig.game.options.settings.game.nx_clock_news = news
    rig.rnd.source = ScriptedRandom([], seed=3, strict=False)
    rig.rules.after_play = True
    rig.rules.between_plays(rig.engine.s)
    return rig, [t for t, _, _ in rig.said]


def test_an_out_of_bounds_run_early_in_a_game_says_the_clock_starts_again_on_the_signal(tmp_path):
    rig, said = after_play(tmp_path, True, 1, 500, oob=True)
    assert READY in said and rig.engine.s.extras.running


def test_an_out_of_bounds_run_in_the_last_five_minutes_says_stopped_until_the_snap(tmp_path):
    rig, said = after_play(tmp_path, True, 4, 200, oob=True)
    assert HELD in said and not rig.engine.s.extras.running


def test_a_run_in_bounds_says_running_and_an_incomplete_pass_says_stopped(tmp_path):
    _, said = after_play(tmp_path / "a", True, 1, 500)
    assert RUNNING in said
    _, said = after_play(tmp_path / "b", True, 1, 500, kind="pass incomplete")
    assert STOPPED in said


def test_off_nothing_is_said_and_the_draws_are_the_same(tmp_path):
    on, said_on = after_play(tmp_path / "on", True, 1, 500, oob=True)
    off, said_off = after_play(tmp_path / "off", False, 1, 500, oob=True)
    assert not {READY, HELD, RUNNING, STOPPED} & set(said_off)
    assert on.engine.s.extras.pending == off.engine.s.extras.pending
    assert [t for t in said_on if t != READY] == said_off


def test_the_log_says_why_the_clock_runs_after_every_play(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    after_play(tmp_path / "rig", False, 1, 500, oob=True)
    debuglog.flush(30)
    lines = [line for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines() if "clock_after_play" in line]
    assert len(lines) == 1 and "restarts on the ready signal" in lines[0] and "out_of_bounds=true" in lines[0].lower(), lines


# ----- the setting, the help, the key -----

def test_the_setting_is_on_by_default_and_saved_as_on_or_off():
    assert Settings.defaults().game.nx_clock_news is True
    for value, wanted in (("off", False), ("on", True)):
        settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_clock_news = %s\n" % value)
        assert settings.game.nx_clock_news is wanted and problems == []
        assert ("nx_clock_news = %s" % value) in settingsfile.render(settings)
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_clock_news = maybe\n")
    assert settings.game.nx_clock_news is True and len(problems) == 1


def test_f6_explains_the_out_of_bounds_rule_and_the_setting_and_f4_names_it(tmp_path):
    rig = scene(tmp_path)
    lines = rig.rules.extra_help("117")                                # F6
    assert X.text("NXH-88") in lines and X.text("NXH-89") in lines
    f4 = next(row for row in ROWS if row.id == "f4")
    assert "Clock updates" in f4.what and "referee's signal" in f4.what


@pytest.mark.parametrize("text_id", ["NXM-77", "NXM-78", "NXM-79", "NXC-44", "NXC-45", "NXH-88", "NXH-89"])
def test_the_new_texts_fit(text_id):
    assert 0 < len(X.text(text_id)) <= 200


@pytest.mark.parametrize("seed", [17, 18])
def test_a_whole_game_with_clock_updates_draws_and_scores_what_it_did_without_them(tmp_path, seed, monkeypatch):
    from nflrig import RecordingRules, sim_game

    def rules():
        return RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True)
    plain, _e, _r, plain_result = sim_game(tmp_path / "off", seed, rules=rules(), trace=True)
    monkeypatch.setattr(C.NflPeriodClock, "news_on", lambda self: True)
    rig, _e, _r, result = sim_game(tmp_path / "on", seed, rules=rules(), trace=True)
    assert rig.rnd.trace == plain.rnd.trace and len(rig.rnd.trace) > 1000
    assert result.scores == plain_result.scores
    said = [t for t, _, _ in rig.said]
    assert said.count(RUNNING) + said.count(STOPPED) + said.count(READY) + said.count(HELD) > 50
