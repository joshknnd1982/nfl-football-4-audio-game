"""The excited voice of the radio calls and their ten ways per kind of play result (nfl4 only, rule 0.13; XV, D-198). This is inspired by Jim Kitchen.

The owner, 2026-10-27, asked for "an enthusiastic 1990s NFL radio play-by-play announcer": short punchy fragments and exclamations on the big
plays, a color commentator chiming in after the call, "a randomized list of 10+ broadcast templates per play result type so it never feels
repetitive", and the voice faster and louder as the play gets bigger, which "user should be able to turn it on or off".

What is tested: every kind of play result has at least ten calls, written in normal case (capitals were measured to make voices spell the
word, speech/lift.py); every call has a level from 1 (routine) to 5 (the touchdown); with F9, Rules, Excited voice on (the default) the
level reaches the game's own voices (higher pitch through SAPI's XML, more rate steps, a louder volume, capped at 100) and NVDA (SSML
prosody in percent), never JAWS; off, nothing is lifted; the setting is saved in settings.txt, read at every call, in the menu right after
Play calls with Enter, Left and Right, and named in F6; the lift never changes a game (the same draws and score on or off); the analyst still
speaks after the plays.
"""
import random
import re
from types import SimpleNamespace

import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras import radio_calls as RC
from nfl4.extras import rules_menu as RM
from nfl4.extras.nfl_rules import rules_from_settings
from nfl4.speech import lift as L
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager
from nfl4.speech.nvda import NvdaBackend
from nfl4.speech.roles import ANNOUNCER
from nflrig import QUARTERBACKS, RecordingRules, SimEngine
from pagrig import make_rig
from programrig import DOWN, ENTER, ESC, said
from test_functions import rig_for
from test_nvda_backend import FakeDll
from test_sapi_roles import Rig as SapiRig

LEFT, RIGHT = 37, 39


def caller(excited=True):
    settings = Settings.defaults()
    settings.game.nx_play_calls = "radio"
    settings.game.nx_excited_voice = excited
    b = SimpleNamespace(state=SimpleNamespace(teams={1: "Bengals", 2: "Jets"}, wisoff=1), play_calls="radio")
    c = RC.RadioCalls(b)
    c.attach(SimpleNamespace(options=SimpleNamespace(settings=settings), rnd=None))
    return c, settings


# ----- the calls -----

def test_every_kind_of_play_result_has_at_least_ten_calls():
    assert RC.MIN_RESULT_VARIANTS >= 10
    for key in RC.RESULT_CALLS:
        assert len(RC.CALLS[key]) >= RC.MIN_RESULT_VARIANTS, key
    # the owner's kinds: a routine gain, a first down, a big play, a turnover, a touchdown, and the sack, the incompletion and the kicks
    for kind in ("gain", "first_gained", "gain_big", "pick", "fumble", "touchdown", "sack", "no_gain_incomplete", "fg_good", "fg_miss"):
        assert kind in RC.RESULT_CALLS


def test_calls_are_in_normal_case_because_capitals_make_voices_spell_words():
    """MEASURED (work/xv_1027/sapi.txt): "GOT IT" is "got I T" on Microsoft Zira, BeSTspeech says "WOW" in four times the time."""
    for variants in RC.CALLS.values():
        for text in variants:
            plain = re.sub(r"\{\w+\}", "", text)
            assert not re.search(r"\b[A-Z]{2,}\b", plain), text


def test_no_call_says_one_sentence_twice_in_a_row():
    """Rule 0.28 (3); the listening test found "Fumble! Loose ball! Loose ball!" (now "Loose ball, loose ball!")."""
    split = re.compile(r"(?<=[.!?])\s+")
    for key, variants in RC.CALLS.items():
        for text in variants:
            parts = [p.strip().lower() for p in split.split(text)]
            assert all(a != b for a, b in zip(parts, parts[1:])), (key, text)


def test_every_call_has_a_level_from_routine_to_touchdown():
    assert set(RC.LEVELS) == {L.GAIN, L.BIG_PLAY, L.TURNOVER, L.TOUCHDOWN}
    assert len(RC.LEVEL_OF) == sum(len(keys) for keys in RC.LEVELS.values())        # no call in two levels
    assert RC.RadioCalls.level("touchdown", "") == L.TOUCHDOWN
    for key in ("pick", "fumble", "sack", "ball_turnover", "ball_downs", "safety"):
        assert RC.RadioCalls.level(key, "") == L.TURNOVER, key
    for key in ("gain_big", "gain_huge", "return_big", "fg_good", "he_is_at"):
        assert RC.RadioCalls.level(key, "") == L.BIG_PLAY, key
    for key in ("first_gained", "gain_good", "catch", "third"):
        assert RC.RadioCalls.level(key, "") == L.GAIN, key
    for key in ("gain_short", "huddle", "snap", "no_gain_incomplete"):
        assert RC.RadioCalls.level(key, "") == L.ROUTINE, key


@pytest.mark.parametrize("text, level", [
    (" There is a gain of 2 yards on the play", 1), (" There is a gain of 14 yards on the play", 2),
    (" There is a gain of 33 yards on the play", 3), (" There is a gain of 61 yards on the play", 3),
    (" and Lewis intercepts the ball", 4), (" and Lewis picks off the pass", 4), (" there is a fumble on the play", 4),
    (" Smith sacks Brady", 4), (" Smith and Jones smother Brady", 4), (" TOUCH DOWN", 5),
    (" the ball is now  mine on your 40 yard line", 4), (" the snap is good", 1),
])
def test_the_level_follows_the_play(text, level):
    c, _settings = caller()
    out, got = c.call(text)
    assert got == level, out


def test_the_sentences_of_one_kind_share_one_pool_and_two_tacklers_fit_every_sack_line():
    c, _settings = caller()
    sacks = {" ".join(c.call(" Smith and Jones smother Brady")[0].split()) for _ in range(40)}
    filled = {v.replace("{q}", "Brady").replace("{y}", "Smith and Jones") for v in RC.CALLS["sack"]}
    assert sacks <= filled and len(sacks) >= 8
    picks = {" ".join(c.call(t)[0].split()) for t in (" and Lewis intercepts the ball", " and Lewis picks off the pass") * 20}
    assert picks <= {v.replace("{y}", "Lewis") for v in RC.CALLS["pick"]} and len(picks) >= 8


def test_the_excited_voice_off_lifts_nothing_and_a_change_applies_at_once(caplog):
    with caplog.at_level("INFO", logger="nfl4.extras"):
        c, settings = caller(excited=False)                 # the log names the setting when the game starts
        assert c.call(" TOUCH DOWN")[1] == 0 and c.call(" Smith sacks Brady")[1] == 0
        settings.game.nx_excited_voice = True
        assert c.call(" TOUCH DOWN")[1] == 5
    assert "excited voice off" in caplog.text and "excited voice on" in caplog.text
    plain, _ = caller()
    plain_settings = _
    plain_settings.game.nx_play_calls = "plain"
    assert plain.call(" TOUCH DOWN") == (" TOUCH DOWN", 0)                 # the plain calls are never lifted


# ----- the engines -----

def engines(mode="sapi", nvda_running=False):
    sapi = FakeBackend("SAPI 5", takes_roles=True, takes_lift=True)
    nvda = FakeBackend("NVDA", available=nvda_running, takes_lift=True)
    jaws = FakeBackend("JAWS", available=True)
    return SpeechManager(sapi, nvda, mode, jaws), sapi, nvda, jaws


def test_the_lift_reaches_sapi_and_nvda_but_never_jaws():
    manager, sapi, _nvda, _jaws = engines()
    manager.say_async(" Touchdown! ", role=ANNOUNCER, lift=5)
    manager.say(" First and 10. ", role=ANNOUNCER)
    assert sapi.lifts == [(" Touchdown! ", 5)] and sapi.said[-1] == (" First and 10. ", ANNOUNCER, 0)
    manager, _sapi, nvda, _jaws = engines(mode="nvda", nvda_running=True)
    manager.say_async(" Touchdown! ", role=ANNOUNCER, lift=5)
    assert nvda.lifts == [(" Touchdown! ", 5)]
    manager, _sapi, _nvda, jaws = engines(mode="jaws")
    manager.say_async(" Touchdown! ", role=ANNOUNCER, lift=5)
    assert jaws.said == [(" Touchdown! ", None, 0)] and jaws.lifts == []


def test_sapi_says_a_lifted_call_higher_faster_and_louder_capped_at_100():
    rig = SapiRig()
    try:
        rig.backend.set_rate(2)
        rig.backend.speak("Gain of 3.", ANNOUNCER)
        rig.backend.speak("Touchdown!", ANNOUNCER, lift=L.TOUCHDOWN)
        rig.backend.speak("A big gain!", ANNOUNCER, lift=L.BIG_PLAY)
        rig.backend.speak("First down!", ANNOUNCER, lift=L.ROUTINE)
        rig.backend.wait_until_done()
        heard = rig.heard()
        td = L.LIFTS[L.TOUCHDOWN]
        assert heard[0][1:] == (95, 2, "Gain of 3.")
        assert heard[1][1:3] == (100, 2 + td.rate) and heard[1][3] == '<pitch absmiddle="%d">Touchdown!</pitch>' % td.pitch
        assert heard[2][1:3] == (100, 2 + L.LIFTS[L.BIG_PLAY].rate) and 'absmiddle="%d"' % L.LIFTS[L.BIG_PLAY].pitch in heard[2][3]
        assert heard[3][1:] == (95, 2, "First down!")                       # routine: the voice as it is
    finally:
        rig.close()


def test_sapi_adds_the_lift_to_the_players_pitch_and_clamps_it():
    rig = SapiRig()
    try:
        rig.backend.set_pitch(9)
        rig.backend.speak("Touchdown!", ANNOUNCER, lift=L.TOUCHDOWN)
        rig.backend.wait_until_done()
        assert 'absmiddle="10"' in rig.heard()[-1][3]
    finally:
        rig.close()


def test_nvda_says_a_lifted_call_with_ssml_prosody_in_percent():
    assert L.nvda_ssml("a & b") == "<speak>a &amp; b</speak>"
    assert L.nvda_ssml("x", L.ROUTINE) == "<speak>x</speak>"
    td = L.LIFTS[L.TOUCHDOWN]
    assert L.nvda_ssml("Touchdown!", L.TOUCHDOWN) == '<speak><prosody pitch="%d%%" rate="%d%%">Touchdown!</prosody></speak>' % (
        td.nvda_pitch, td.nvda_rate)
    dll = FakeDll()
    backend = NvdaBackend(path="fake.dll", loader=lambda path: dll)
    backend.speak("Sacked!", lift=L.TURNOVER)
    backend.speak("A gain of 3.")
    backend.wait_until_done()
    texts = dll.ssml_texts()
    assert texts[0].startswith('<speak><prosody pitch="') and "Sacked!" in texts[0] and texts[1] == "<speak>A gain of 3.</speak>"
    backend.close()


def test_the_amounts_grow_with_the_level_and_stay_small():
    order = [L.LIFTS[level] for level in (L.ROUTINE, L.GAIN, L.BIG_PLAY, L.TURNOVER, L.TOUCHDOWN)]
    for low, high in zip(order, order[1:]):
        assert high.pitch >= low.pitch and high.rate >= low.rate and high.nvda_pitch >= low.nvda_pitch and high.nvda_rate >= low.nvda_rate
    top = L.LIFTS[L.TOUCHDOWN]
    assert top.rate <= 2 and top.pitch <= 3 and top.volume <= 5          # measured: 2 rate steps are 23 % faster, 3 pitch steps up to 50 %
    assert top.nvda_pitch <= 110 and top.nvda_rate <= 112                 # measured on IBM ECI: 110 % pitch is 20 % higher


# ----- the setting -----

@pytest.mark.parametrize("value, wanted", [("on", True), ("off", False), ("yes", True), ("no", False)])
def test_settings_txt_keeps_the_excited_voice(value, wanted):
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_excited_voice = %s\n" % value)
    assert settings.game.nx_excited_voice is wanted and problems == []
    assert ("nx_excited_voice = %s" % ("on" if wanted else "off")) in settingsfile.render(settings)


def test_a_bad_value_is_a_problem_and_an_old_file_gets_the_excited_voice():
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_excited_voice = loud\n")
    assert settings.game.nx_excited_voice is True and len(problems) == 1
    settings, problems = settingsfile.parse(settingsfile.HEADER + "nx_play_calls = radio\n")       # a file of 0.16.10
    assert settings.game.nx_excited_voice is True and problems == []
    assert "F9, Rules, Excited voice" in settingsfile.HEADER


@pytest.mark.parametrize("rules", ["nfl", "classic"])
def test_f6_says_how_to_turn_it_on_and_off_in_both_modes(rules):
    settings = Settings.defaults()
    settings.game.rules = rules
    help_text = X.text("NXH-85")
    assert "F9, Rules, Excited voice" in help_text and "Enter" in help_text and "on by default" in help_text
    assert help_text in rules_from_settings(settings.game).extra_help("117")


def rules_menu(rig, keys):
    """F9, Rules, down to the thirteenth item (Excited voice: Rules, then twelve Downs), then the keys."""
    rig.keys.answers = [DOWN, DOWN, DOWN, ENTER] + [DOWN] * 12 + keys + [ESC, ESC]
    rig.game.functions.run()
    return said(rig)[4 + 12:]


def test_the_item_comes_after_play_calls_switches_saves_at_once_and_says_it_applies_now(tmp_path):
    rig = rig_for(tmp_path, [])
    game = rig.game.options.settings.game
    spoken = rules_menu(rig, [ENTER, LEFT, RIGHT])
    now = X.text("NXM-69")
    on = "Excited voice: on, the big plays are said higher, faster and a little louder"
    off = "Excited voice: off, every call in the voice as it is"
    assert spoken[0] == on
    assert spoken[1] == off + "," + now
    assert spoken[2:4] == [on, off]
    assert game.nx_excited_voice is False and rig.saves.count == 3
    assert "nx_excited_voice = off" in settingsfile.render(rig.game.options.settings)


def test_the_item_says_jaws_says_the_words_only_while_jaws_speaks():
    jaws = SimpleNamespace(active_engine=lambda: SimpleNamespace(name="JAWS"))
    nvda = SimpleNamespace(active_engine=lambda: SimpleNamespace(name="NVDA"))
    settings = Settings.defaults().game
    assert RM.excited_label(settings, jaws).endswith(X.text("NXM-76"))
    assert X.text("NXM-76") not in RM.excited_label(settings, nvda)
    assert "Reset" not in RM.excited_label(settings)


# ----- whole games -----

def nfl_game(tmp_path, seed, excited=True):
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=2, gtp=1)
    rig.sapi.takes_lift = True
    rig.game.options.settings.game.nx_play_calls = "radio"
    rig.game.options.settings.game.nx_excited_voice = excited
    rig.game.comtog_source = lambda: 0
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=True)
    engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS)
    rig.game.play_engine = engine
    try:
        result = engine.run()
    finally:
        rig.game.play_engine = None
    return rig, result


def test_the_excited_voice_changes_no_game_and_lifts_the_big_moments(tmp_path):
    rig_on, res_on = nfl_game(tmp_path / "on", 22)
    rig_off, res_off = nfl_game(tmp_path / "off", 22, excited=False)
    assert res_on.scores == res_off.scores and rig_on.rnd.draws == rig_off.rnd.draws
    assert [t for t, _r, _s in rig_on.said] == [t for t, _r, _s in rig_off.said]     # the same words, only the voice differs
    assert rig_off.sapi.lifts == []
    levels = [lift for _t, lift in rig_on.sapi.lifts]
    assert set(levels) >= {L.ROUTINE, L.GAIN, L.BIG_PLAY}
    touchdowns = [t for t, lift in rig_on.sapi.lifts if lift == L.TOUCHDOWN]
    assert all("touchdown" in t.lower() or "end zone" in t.lower() for t in touchdowns)
    if max(res_on.scores) >= 6:
        assert touchdowns


def test_the_analyst_still_chimes_in_after_the_calls(tmp_path):
    rig, _res = nfl_game(tmp_path, 22)
    roles = [r for _t, r, _s in rig.said]
    assert roles.count("color") >= 10                                   # Gus after the plays, in his own voice
