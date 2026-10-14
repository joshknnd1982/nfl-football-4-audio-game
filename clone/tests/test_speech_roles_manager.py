"""The manager's speaker calls: SAPI 5 gets the speaker, NVDA and JAWS only the text (nfl4 S7.1). Inspired by Jim Kitchen.

GAP_REGISTER G-S1, G-S4, G-S6, G-S7; D-031 items 1 and 3; GAME_SPEC 9.1 and 9.2.
"""
import threading

from nfl4.data.settings import SpeechSettings
from nfl4.speech import speaker_voices
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager
from nfl4.speech.roles import (ANNOUNCER, F11_NAMES, F12_NAMES, OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER,
                               OWN_QUARTERBACK, ROLES, VOLUME_ORDER, player_role, pronoun)


def engines(sapi_ok=True, nvda_ok=True, jaws_ok=True, mode="sapi"):
    sapi = FakeBackend("SAPI 5", available=sapi_ok, takes_roles=True)
    nvda = FakeBackend("NVDA", available=nvda_ok)
    jaws = FakeBackend("JAWS", available=jaws_ok)
    return SpeechManager(sapi, nvda, mode, jaws), sapi, nvda, jaws


def test_sapi_gets_the_speaker_and_the_rate_step_of_every_text():
    manager, sapi, nvda, jaws = engines()
    manager.say_async(" Hike! ", role=OWN_QUARTERBACK)
    manager.say(" red leather yellow leather ", role=ANNOUNCER, rate_step=1)
    manager.say_async("plain")
    assert sapi.said == [(" Hike! ", OWN_QUARTERBACK, 0), (" red leather yellow leather ", ANNOUNCER, 1),
                         ("plain", None, 0)]
    assert nvda.said == [] and jaws.said == []


def test_nvda_and_jaws_get_only_the_text_and_ignore_speakers_and_rate_steps():
    for mode, chosen in (("nvda", 1), ("jaws", 2), ("auto", 1)):
        manager, sapi, nvda, jaws = engines(mode=mode)
        manager.say_async(" Hike! ", role=OWN_QUARTERBACK, rate_step=1)
        engine = (sapi, nvda, jaws)[chosen]
        assert engine.said == [(" Hike! ", None, 0)] and sapi.said == []


def test_the_default_mode_is_the_sapi_voices_and_falls_back_when_sapi_is_missing():
    manager = SpeechManager(None, None)
    assert manager.mode == "sapi"                                   # G-S7
    manager, sapi, nvda, jaws = engines(sapi_ok=False)
    manager.say_async("title", role=ANNOUNCER)
    assert nvda.said == [("title", None, 0)] and sapi.said == []


def test_the_rate_counter_reaches_only_sapi():
    manager, sapi, nvda, jaws = engines(mode="nvda")
    manager.set_rate(4)                                             # G-S4: the screen reader's own rate is untouched
    assert ("rate", 4) in sapi.events
    assert all(kind != "rate" for kind, _ in nvda.events + jaws.events)


def test_speaker_voices_and_volumes_reach_only_sapi():
    manager, sapi, nvda, jaws = engines()
    manager.set_role_voice(OPPONENT_PUNTER, "token-9")
    manager.set_role_volume(OWN_PUNTER, 40)
    assert ("role_voice", "opponent_punter=token-9") in sapi.events and ("role_volume", "own_punter=40") in sapi.events
    assert all(kind not in ("role_voice", "role_volume") for kind, _ in nvda.events + jaws.events)


def test_the_gender_comes_from_the_sapi_voice_only_while_sapi_speaks():
    manager, sapi, nvda, jaws = engines()
    sapi.genders = {OPPONENT_QUARTERBACK: "Female"}
    assert manager.role_gender(OPPONENT_QUARTERBACK) == "Female"
    assert pronoun(manager.role_gender(OPPONENT_QUARTERBACK)) == " She "
    assert pronoun(manager.role_gender(OWN_QUARTERBACK)) == " He "        # no Gender attribute: " He "
    manager.mode = "nvda"
    assert manager.role_gender(OPPONENT_QUARTERBACK) == ""                # G-S6: always " He " with NVDA or JAWS
    manager, sapi, nvda, jaws = engines(sapi_ok=False)
    sapi.genders = {OWN_PUNTER: "Female"}
    assert manager.role_gender(OWN_PUNTER) == ""                          # SAPI not speaking now
    assert SpeechManager(None, None).role_gender(OWN_PUNTER) == ""


def test_pronoun_is_the_originals_case_sensitive_test():
    assert pronoun("Female") == " She " and pronoun(" Female ") == " She "
    assert pronoun("female") == " He " and pronoun("Male") == " He " and pronoun("") == " He "


def test_the_last_speaker_is_kept_for_say6():
    manager, sapi, nvda, jaws = engines()
    manager.say_async("one", role=OWN_PUNTER)
    assert manager.last_role == OWN_PUNTER
    manager.say_async("again", role=manager.last_role)                   # say6: the voice that spoke last
    assert sapi.said[-1] == ("again", OWN_PUNTER, 0)


def test_an_engine_that_raises_is_skipped_and_logged_never_raised(caplog):
    manager, sapi, nvda, jaws = engines()

    def broken(*args, **kwargs):
        raise RuntimeError("COM died")

    sapi.speak = broken
    sapi.set_role_voice = broken
    sapi.role_details = broken
    manager.say("still heard", role=ANNOUNCER)
    manager.set_role_voice(ANNOUNCER, "x")
    assert manager.role_gender(ANNOUNCER) == ""
    assert nvda.said == [("still heard", None, 0)]
    assert any("speak failed" in r.message for r in caplog.records)


def test_is_speaking_asks_the_engine_in_use():
    manager, sapi, nvda, jaws = engines()
    sapi.seconds_per_char = 1.0
    manager.say_async("long", role=ANNOUNCER)
    assert manager.is_speaking()
    manager.stop()
    assert not manager.is_speaking()


def test_the_crash_guard_hooks_reach_the_sapi_engine():
    manager, sapi, nvda, jaws = engines()
    sapi.on_voice_trial = sapi.on_voice_proven = None
    arm, clear = (lambda v: None), (lambda v: None)
    manager.watch_voice_trials(arm, clear)
    assert sapi.on_voice_trial is arm and sapi.on_voice_proven is clear
    SpeechManager(None, None).watch_voice_trials(arm, clear)            # no SAPI: nothing to do, no error


def test_a_synchronous_say_waits_for_everything_queued_before_it():
    manager, sapi, nvda, jaws = engines()
    sapi.seconds_per_char = 0.002
    done = threading.Event()
    manager.say_async("x" * 50, role=ANNOUNCER)                          # 0.1 s
    t = threading.Thread(target=lambda: (manager.say(" ", role=ANNOUNCER), done.set()))
    t.start()
    assert not done.wait(0.05)
    assert done.wait(1.0)


def test_the_five_speakers_and_their_orders():
    assert ROLES == (ANNOUNCER, OWN_QUARTERBACK, OPPONENT_QUARTERBACK, OWN_PUNTER, OPPONENT_PUNTER)   # F12, 4.7
    assert VOLUME_ORDER == (ANNOUNCER, OWN_QUARTERBACK, OWN_PUNTER, OPPONENT_QUARTERBACK, OPPONENT_PUNTER)  # F11
    assert set(F11_NAMES) == set(F12_NAMES) == set(ROLES)
    assert F12_NAMES[OPPONENT_QUARTERBACK] == "your opponent's quarter back"
    assert F11_NAMES[OPPONENT_QUARTERBACK] == "your opponents quarterback"
    # say3: qorp = 1 the quarterback, else the punter, of side wisoff (GAME_SPEC 9.1)
    assert player_role(1) == OWN_QUARTERBACK and player_role(2) == OPPONENT_QUARTERBACK
    assert player_role(1, punter=True) == OWN_PUNTER and player_role(2, punter=True) == OPPONENT_PUNTER


def test_speaker_voices_come_from_the_settings_and_skip_a_voice_that_crashed():
    settings = SpeechSettings()
    assert all(v.voice_id is None and v.volume == 95 for v in speaker_voices(settings).values())
    settings.voices[OWN_QUARTERBACK] = "HKEY\\SmoothTalker"
    settings.voices[ANNOUNCER] = "HKEY\\David"
    settings.volumes[OPPONENT_PUNTER] = 20
    voices = speaker_voices(settings, skip=frozenset({"hkey\\smoothtalker"}))
    assert voices[OWN_QUARTERBACK].voice_id is None                       # the first voice until chosen again
    assert voices[ANNOUNCER].voice_id == "HKEY\\David" and voices[OPPONENT_PUNTER].volume == 20
    assert settings.voices[OWN_QUARTERBACK] == "HKEY\\SmoothTalker"       # the saved choice is kept
