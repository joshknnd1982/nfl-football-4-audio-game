"""The speech stress tests of S8.3 (P8; nfl4 only for the file, the cases are the playbook's 8.3 list). This is inspired by Jim Kitchen.

Playbook 7.4.4, 7.4.5 and the S8.3 line of CLAUDE.md 3: thousands of voices and texts, NVDA absent or closing, JAWS absent or closing,
SAPI failing or slow. The engines are fakes that fail the way the real ones were measured to fail (tests/test_nvda_backend.py's DLL,
tests/test_jaws.py's COM object, speech/fake.py), made hostile: they come and go, raise from every call, answer slowly and take texts and
then raise from the next call. Whatever they do the manager never raises, never hangs, says every text on an engine that works, and never
says a text twice. The real SAPI engine in both bitnesses is tests/test_real_engines.py and `work\\s83\\sapi_stress_s83.py`.
"""
import random
import threading
from types import SimpleNamespace
import time

import pytest

from gamerig import Rig
from nfl4.game.voice_choice import choose_role_voice
from nfl4.speech.fake import FakeBackend
from nfl4.speech.jaws import JawsBackend
from nfl4.speech.manager import SpeechManager
from nfl4.speech.nvda import NvdaBackend
from nfl4.speech.roles import ANNOUNCER, OWN_PUNTER, OWN_QUARTERBACK
from nfl4.speech.voices import VoiceInfo
from pagrig import make_rig, play
from test_jaws import FakeJawsCom
from test_nvda_backend import FakeDll
from test_pag_games import lively_policy


class Chaos(FakeBackend):
    """An engine that fails the way a dying, slow or confused one does: it comes and goes, refuses a text, and every other call may raise
    (a real engine's speak returns True or False and does not raise after it took the text, so that one never does)."""

    def __init__(self, rng, name, p_raise=0.1, p_refuse=0.1, p_gone=0.1, takes_roles=False, **kwargs):
        super().__init__(name=name, takes_roles=takes_roles, **kwargs)
        self.rng, self.p_raise, self.p_refuse, self.p_gone = rng, p_raise, p_refuse, p_gone
        self.spoken_ids: list[str] = []

    def _maybe_raise(self, what):
        if self.rng.random() < self.p_raise:
            raise RuntimeError(f"{self.name} {what} blew up")

    def is_available(self):
        self._maybe_raise("is_available")
        return self.available and self.rng.random() >= self.p_gone

    def speak(self, text, role=None, rate_step=0):
        if self.rng.random() < self.p_refuse:
            return False
        taken = super().speak(text, role, rate_step) if self.takes_roles else super().speak(text)
        self.spoken_ids.append(text)
        return taken

    def stop(self):
        super().stop()
        self._maybe_raise("stop")

    def wait_until_done(self, abort=None):
        self._maybe_raise("wait_until_done")
        super().wait_until_done(abort)

    def is_speaking(self):
        self._maybe_raise("is_speaking")
        return super().is_speaking()

    def queue_length(self):
        self._maybe_raise("queue_length")
        return 0

    def close(self):
        self._maybe_raise("close")


def hostile_manager(seed, mode="sapi", **chances):
    rng = random.Random(seed)
    sapi = Chaos(rng, "SAPI 5", takes_roles=True, **chances)
    nvda = Chaos(rng, "NVDA", **chances)
    jaws = Chaos(rng, "JAWS", **chances)
    return SpeechManager(sapi, nvda, mode, jaws), (sapi, nvda, jaws)


@pytest.mark.parametrize("mode", ["sapi", "nvda", "jaws", "auto"])
def test_thousands_of_calls_on_three_hostile_engines_never_raise_and_never_say_a_text_twice(mode):
    manager, engines = hostile_manager(7, mode)
    rng = random.Random(8)
    sent = 0
    for i in range(6000):
        roll = rng.random()
        if roll < 0.45:
            manager.say_async(f"text {i}", role=rng.choice((ANNOUNCER, OWN_QUARTERBACK, OWN_PUNTER)))
            sent += 1
        elif roll < 0.70:
            manager.say(f"text {i}", role=ANNOUNCER)
            sent += 1
        elif roll < 0.80:
            manager.stop()
        elif roll < 0.85:
            manager.is_speaking()
        elif roll < 0.88:
            manager.screen_reader_message(f"message {i}")
        elif roll < 0.92:
            manager.role_details(ANNOUNCER)
            manager.role_gender(OWN_PUNTER)
            manager.set_rate(rng.choice((None, 1, 5)))
            manager.set_volume(50)
        elif roll < 0.94:
            manager.nvda_running()
            manager.jaws_running()
            manager.active_engine()
        elif roll < 0.96:
            manager.mode = rng.choice(("sapi", "nvda", "jaws", "auto"))
        else:
            manager.say(f"text {i}", abort=threading.Event())
            sent += 1
    manager.close()
    said = [t for e in engines for t in e.spoken_ids if t.startswith("text ")]
    assert sent > 3000 and len(said) == len(set(said)), "a text was said twice"


def test_a_text_the_engine_took_and_then_raised_about_is_not_said_again_on_the_next_engine():
    """The accounting in the log (queue length) happens after the engine took the text: its failure must not count as a refusal."""
    rng = random.Random(1)
    sapi = Chaos(rng, "SAPI 5", p_raise=0.0, p_refuse=0.0, p_gone=0.0, takes_roles=True)
    nvda = Chaos(rng, "NVDA", p_raise=0.0, p_refuse=0.0, p_gone=0.0)
    sapi.queue_length = lambda: (_ for _ in ()).throw(RuntimeError("queue_length blew up"))
    manager = SpeechManager(sapi, nvda, "sapi")
    manager.say_async("only once", role=ANNOUNCER)
    assert sapi.spoken_ids == ["only once"] and nvda.spoken_ids == []


def test_with_every_engine_down_the_calls_return_and_the_first_engine_back_speaks_again():
    manager, (sapi, nvda, jaws) = hostile_manager(3, "auto", p_raise=0.0, p_refuse=0.0, p_gone=0.0)
    for engine in (sapi, nvda, jaws):
        engine.available = False
    started = time.monotonic()
    for i in range(500):
        manager.say(f"nobody {i}")
        manager.say_async(f"nobody {i}")
        manager.stop()
    assert time.monotonic() - started < 5 and not (sapi.said or nvda.said or jaws.said)
    sapi.p_gone = 0.0
    sapi.available = True
    manager.say("back again", role=ANNOUNCER)
    assert sapi.spoken_ids[-1:] == ["back again"]


def test_a_voice_that_speaks_slowly_does_not_hold_up_the_stop():
    sapi = FakeBackend("SAPI 5", takes_roles=True, seconds_per_char=0.5)
    manager = SpeechManager(sapi, None, "sapi")
    for i in range(50):
        manager.say_async("a very long sentence that takes a very long time to say " * 3, role=ANNOUNCER)
    started = time.monotonic()
    manager.stop()
    assert time.monotonic() - started < 0.5 and not sapi.is_speaking()


def whole_game(tmp_path, seed, setup):
    """A whole Classic game; `setup(rig)` changes the engines inside the rig's own manager (every part of the game holds that object)."""
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=1 + seed % 2)
    engines = setup(rig)
    heard = []                                      # what any engine took, for the key policy that never presses Save Game

    for engine in engines:
        real = engine.speak

        def speak(text, *args, _real=real, **kwargs):
            taken = _real(text, *args, **kwargs)
            if taken:
                heard.append((text, None, 0))
            return taken
        engine.speak = speak
    rig.keys.policy = lively_policy(SimpleNamespace(said=heard), seed + 1000)
    return rig, engines, play(rig)


@pytest.mark.parametrize("seed", range(6))
def test_a_whole_game_on_three_hostile_engines_reaches_its_final_score(tmp_path, seed):
    def hostile(rig):
        rng = random.Random(seed)
        engines = [Chaos(rng, "SAPI 5", takes_roles=True, clock=rig.clock, sleep=rig.clock.sleep, seconds_per_char=0.001),
                   Chaos(rng, "NVDA", clock=rig.clock, sleep=rig.clock.sleep, seconds_per_char=0.001),
                   Chaos(rng, "JAWS", clock=rig.clock, sleep=rig.clock.sleep, seconds_per_char=0.001)]
        rig.speech.sapi, rig.speech.nvda, rig.speech.jaws = engines
        rig.speech._mode = rng.choice(("sapi", "nvda", "auto"))
        return engines
    rig, engines, result = whole_game(tmp_path, seed, hostile)
    assert (result.scores is not None and result.scores[0] != result.scores[1]) or result.saved      # a refused text may hide "Save Game" from the policy
    assert rig.rnd.fallbacks == 0
    assert sum(len(e.spoken_ids) for e in engines) > 30


@pytest.mark.parametrize("seed", range(3))
def test_a_whole_game_with_no_engine_at_all_is_played_in_silence_to_its_final_score(tmp_path, seed):
    def none(rig):
        rig.speech.sapi = rig.speech.nvda = rig.speech.jaws = None
        return []
    rig, _, result = whole_game(tmp_path, seed, none)
    assert (result.scores is not None and result.scores[0] != result.scores[1]) or result.saved     # nothing is heard, so Save Game may be picked


@pytest.mark.parametrize("seed", range(3))
def test_nvda_and_jaws_closing_in_the_middle_of_a_game_hand_the_speech_to_sapi_and_it_reaches_the_end(tmp_path, seed):
    def closing(rig):
        rig.nvda.available = True
        jaws = FakeBackend("JAWS", clock=rig.clock, sleep=rig.clock.sleep, seconds_per_char=0.001)
        manager = rig.speech
        manager.jaws, manager._mode = jaws, "auto"
        calls = {"n": 0}
        real = manager._send

        def send(text, role, rate_step):
            calls["n"] += 1
            if calls["n"] == 40:
                rig.nvda.available = False                       # NVDA is closed by the player
            if calls["n"] == 90:
                jaws.available = False                           # JAWS too
            return real(text, role, rate_step)
        manager._send = send
        return [rig.sapi, rig.nvda, jaws]
    rig, engines, result = whole_game(tmp_path, seed, closing)
    sapi, nvda, jaws = engines
    assert result.scores is not None and result.scores[0] != result.scores[1]
    assert len(nvda.said) >= 30 and len(sapi.said) > 50                  # NVDA spoke until it closed, SAPI after it


# ----- the real NVDA and JAWS backends on hostile controllers -----

def test_the_nvda_backend_survives_the_screen_reader_closing_and_coming_back_under_three_talking_threads():
    dll = FakeDll(speech_seconds=0.002)
    backend = NvdaBackend(path="fake.dll", loader=lambda path: dll)
    stop = threading.Event()
    errors = []

    def talker(n):
        try:
            for i in range(400):
                backend.speak(f"t{n}-{i}")
                if i % 37 == 0:
                    backend.stop()
                if i % 53 == 0:
                    backend.wait_until_done()
        except Exception as exc:                                      # noqa: BLE001  any exception out of the backend is a finding
            errors.append(repr(exc))

    def flapper():
        rng = random.Random(5)
        while not stop.is_set():
            dll.running = rng.random() < 0.6
            dll.ssml_code = 0 if dll.running else 1753
            time.sleep(0.003)
    flap = threading.Thread(target=flapper, daemon=True)
    flap.start()
    threads = [threading.Thread(target=talker, args=(n,)) for n in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(60)
    stop.set()
    flap.join(5)
    assert not any(thread.is_alive() for thread in threads) and not errors
    dll.running, dll.ssml_code = True, 0
    done = threading.Event()
    threading.Thread(target=lambda: (backend.stop(), backend.wait_until_done(), done.set()), daemon=True).start()
    assert done.wait(10)
    backend.close()
    assert not backend.speak("after the close")


def test_the_jaws_backend_survives_a_com_object_that_raises_and_a_screen_reader_that_comes_and_goes():
    com = FakeJawsCom()
    rng = random.Random(11)
    real_say, real_stop = com.SayString, com.StopSpeech

    def say(text, flush):
        if rng.random() < 0.2:
            raise OSError("RPC server is unavailable")
        com.running = rng.random() < 0.7
        return real_say(text, flush)

    def stop():
        if rng.random() < 0.2:
            raise OSError("RPC server is unavailable")
        return real_stop()
    com.SayString, com.StopSpeech = say, stop
    backend = JawsBackend(factory=lambda: com, window_open=lambda: rng.random() < 0.5)
    errors = []

    def talker(n):
        try:
            for i in range(600):
                backend.is_available()
                backend.speak(f"j{n}-{i}")
                if i % 41 == 0:
                    backend.stop()
                if i % 97 == 0:
                    backend.wait_until_done(threading.Event())
        except Exception as exc:                                      # noqa: BLE001
            errors.append(repr(exc))
    threads = [threading.Thread(target=talker, args=(n,)) for n in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(60)
    assert not any(thread.is_alive() for thread in threads) and not errors
    backend.close()


# ----- thousands of voices -----

def thousands_of_voices(count=5000, engines=60):
    voices = []
    for i in range(count):
        name = {0: "", 1: " ", 2: "x" * 4000, 3: "Françoise ‘quoted’ – dash", 4: "123"}.get(i, f"Voice {i % 997:03d} of engine {i % engines}")
        voices.append(VoiceInfo(i, f"HKEY\\Speech\\Voices\\TokenEnums\\Engine{i % engines}\\Voice{i}", name, f"Engine {i % engines}"))
    return voices


KEY_END, KEY_HOME, KEY_PAGE_DOWN, KEY_PAGE_UP, ENTER, ESC, DOWN = 35, 36, 34, 33, 13, 27, 40


def pick(answers, voices, current=None):
    rig = Rig(answers=answers)
    started = time.monotonic()
    chosen = choose_role_voice(rig.speech, rig.keys, voices, ANNOUNCER, current)
    return chosen, rig, time.monotonic() - started


def test_five_thousand_voices_of_sixty_engines_all_voices_end_enter_picks_the_last_one_quickly():
    voices = thousands_of_voices()
    chosen, rig, seconds = pick([KEY_HOME, ENTER, KEY_END, ENTER], voices)
    assert chosen == voices[-1] and seconds < 10
    assert any("5000" in t for t, _, _ in rig.said)                 # the count of the list is spoken


def test_five_thousand_voices_page_keys_type_ahead_and_escape_never_raise_and_each_key_speaks():
    voices = thousands_of_voices()
    rng = random.Random(4)
    keys = [KEY_HOME, ENTER]                                          # into "All voices"; Enter or Escape would end the picker, so only the moving keys
    for _ in range(600):
        keys.append(rng.choice((DOWN, DOWN, KEY_PAGE_DOWN, KEY_PAGE_UP, KEY_END, KEY_HOME, 38, "v", "o", "1", "f", "z", 112)))
    keys += [ESC, ESC]
    rig = Rig(answers=keys)
    started = time.monotonic()
    assert choose_role_voice(rig.speech, rig.keys, voices, ANNOUNCER, voices[2500].voice_id) is None
    assert len(rig.said) > 300 and time.monotonic() - started < 30


def test_voices_with_an_empty_blank_enormous_or_accented_name_are_listed_and_can_be_picked():
    voices = thousands_of_voices(8, engines=1)
    for index in range(5):
        chosen, rig, _ = pick([ENTER] + [DOWN] * index + [ENTER], voices)
        assert chosen == voices[index]


def test_one_voice_and_no_voice_at_all_do_not_break_the_picker():
    voices = thousands_of_voices(1, engines=1)
    chosen, _, _ = pick([ENTER, ENTER], voices)
    assert chosen == voices[0]
    chosen, _, _ = pick([ESC], voices)
    assert chosen is None


# ----- the pieces handed to a voice (B-S28: SAM died on a lone full stop, Votrax on a 4,000 letter word) -----

def test_split_chunks_removes_a_token_of_only_stops_and_keeps_the_numbers_and_initials():
    from nfl4.speech.sapi5 import split_chunks
    assert split_chunks(" the other teams' quarterback, the best first. . 31 items. Press F1 for help.  Clay of the Ravens, rating 80, age 24, 20.9 million for 3 years.") == [
        " the other teams' quarterback, the best first.", " 31 items. Press F1 for help.", "Clay of the Ravens, rating 80, age 24, 20.9 million for 3 years."]
    assert split_chunks(". 31 items.") == [" 31 items."]
    assert split_chunks("Press F1 for help. , current voice, with a name that is long enough to be split") == [
        "Press F1 for help.  current voice, with a name that is long enough to be split"]
    assert split_chunks(" 1. play game ") == [" 1. play game "] and split_chunks(" and .5 of a yard, 3.5 and N. F. L. ") == [" and .5 of a yard, 3.5 and N. F. L. "]


def test_split_chunks_never_hands_a_voice_a_lone_stop_a_word_over_100_letters_or_a_piece_over_300():
    from nfl4.speech.sapi5 import split_chunks
    rng = random.Random(9)
    vocabulary = ["the", "Ravens", "31", "items.", ".", ",", ";", "..", ":", "N.", "F.", "L.", "3.5", "x" * 400, "y" * 99, "end!", "a?", "\n"]
    for _ in range(4000):
        text = " ".join(rng.choice(vocabulary) for _ in range(rng.randint(1, 120)))
        for chunk in split_chunks(text):
            assert len(chunk) <= 300 + 1, len(chunk)
            for word in chunk.split():
                assert len(word) <= 100 and (word.strip(".,;:") != "" or word in ("N.", "F.", "L.")), (word, chunk)
        # nothing that is said is lost: the words of the text without its lone stops, as pieces of at most 100 letters, in order
        said = "".join(w for c in split_chunks(text) for w in c.split())
        wanted = "".join(w for w in text.split() if w.strip(".,;:") != "" or w in ("N.", "F.", "L."))
        assert said == wanted
