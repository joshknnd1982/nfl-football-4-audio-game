"""The referee's microphone and the whistles of the N. F. L. rules (nfl4 only, rule 0.13; SY.3, D-103). This is inspired by Jim Kitchen.

The referee is a speaker of his own (outside the original's five): his sentences (the flags, the time outs, the reviews) are said in his voice
with a public-address sound when the broadcast is on, and the microphone clicks; the whistles of the game are pea whistles chosen by what
happened. Nothing changes the game: the draws are the stadium's own, the wait of a whistle is the original's 2.5 seconds, and Classic hears
the original's foot11 and the announcer.
"""
import array
import audioop
import math
import os
import types

import pytest

from gamerig import Rig
from nfl4.audio.output import SLOT_TACKLE
from nfl4.extras import nx_texts as X
from nfl4.extras import stadium as ST
from nfl4.extras.nfl_rules import NflRules
from nfl4.speech import pa_effect
from nfl4.speech.roles import ALL_ROLES, EXTRA_ROLES, REFEREE, ROLES
from nfl4.speech.sapi5 import RoleVoice
from nflrig import RecordingRules, sim_game

RATE = 44100


def tone(freq, seconds=0.4, amplitude=8000):
    n = int(RATE * seconds)
    return array.array("h", (int(amplitude * math.sin(2 * math.pi * freq * i / RATE)) for i in range(n))).tobytes()


# ----- the public-address sound -----

def test_the_pa_sound_keeps_the_middle_of_the_voice_and_takes_away_the_bottom_and_the_top():
    middle, low, high = tone(1000), tone(80), tone(12000)
    kept = audioop.rms(pa_effect.band_limit(middle, RATE), 2) / audioop.rms(middle, 2)
    lost_low = audioop.rms(pa_effect.band_limit(low, RATE), 2) / audioop.rms(low, 2)
    lost_high = audioop.rms(pa_effect.band_limit(high, RATE), 2) / audioop.rms(high, 2)
    assert kept > 0.5 and lost_low < 0.45 * kept and lost_high < 0.45 * kept, (kept, lost_low, lost_high)


def test_the_pa_sound_adds_the_tail_of_the_echo_and_never_overflows_and_is_the_same_every_time():
    voice = tone(900, 0.5, 16000)
    out = pa_effect.apply(voice, RATE)
    assert len(out) == len(voice) + 2 * int(RATE * pa_effect.TAIL_SECONDS)
    assert out == pa_effect.apply(voice, RATE)
    assert audioop.max(out, 2) <= 32767
    tail = out[len(voice):]
    assert audioop.rms(tail, 2) > 0 and audioop.rms(tail, 2) < audioop.rms(out[:len(voice)], 2)       # the echo rings and dies
    assert pa_effect.apply(b"", RATE) == b"" and pa_effect.apply(b"ab", RATE) == b"ab"
    assert audioop.rms(pa_effect.apply(bytes(4000), RATE), 2) == 0            # silence stays silence
    for samples in (4, 5, 17, 63, 64, 65, 200):                               # a very short chunk (a word) never breaks the filters
        short = tone(500, samples / RATE)
        assert len(pa_effect.apply(short, RATE)) == len(short) + 2 * int(RATE * pa_effect.TAIL_SECONDS)


# ----- the speaker -----

def test_the_referee_is_a_speaker_outside_the_original_five():
    assert REFEREE == "referee" and REFEREE not in ROLES and EXTRA_ROLES == ("color", "referee") and ALL_ROLES == ROLES + EXTRA_ROLES


def test_the_sapi_engine_gives_the_referee_the_effect_and_nobody_else(tmp_path):
    from test_sapi_render import make, texts
    b, voice, player = make(roles={"announcer": RoleVoice(), "referee": RoleVoice(effect="pa")}, default_role="announcer")
    try:
        text = "the ruling on the field stands"
        b.speak(text, role="announcer")
        b.wait_until_done()
        b.speak(text, role="referee")
        b.wait_until_done()
        plain, processed = player.blocks
        assert plain == text.encode() and processed != plain and len(processed) > len(plain)
        b.set_role_effect("referee", None)
        b.speak(text, role="referee")
        b.wait_until_done()
        assert player.blocks[-1] == text.encode()
        b.set_role_effect("nobody", "pa")                     # an unknown speaker is ignored
    finally:
        b.close()


# ----- the referee's sentences -----

def test_say_referee_waits_is_logged_and_kept_for_f2_in_the_referees_voice(tmp_path):
    rig = Rig([], sounds_dir=tmp_path)
    rig.game.say_referee(" there is a flag on the play. ")
    assert rig.said[-1] == (" there is a flag on the play. ", REFEREE, 0)
    assert rig.game.replay[-1] == " there is a flag on the play. "
    assert [kind for kind, _ in rig.sapi.events if kind in ("speak", "wait")][-2:] == ["speak", "wait"]


def test_ref_says_uses_the_microphone_with_the_broadcast_on_and_the_announcer_without(tmp_path):
    rig = Rig([], sounds_dir=tmp_path)
    rules = NflRules(broadcast_on=True)
    rules.game = rig.game
    rules.ref_says(" the play is dead. ")
    assert rig.said[-1][1] == REFEREE
    rules = NflRules(broadcast_on=False)
    rules.game = rig.game
    rules.ref_says(" the play is dead. ")
    assert rig.said[-1][1] == "announcer"


# ----- the whistles and the clicks of the microphone -----

class Sounds:
    def __init__(self):
        self.calls = []
        self.now = 0.0

    def play_effect(self, path, level=0, slot=None):
        self.calls.append(os.path.basename(path)[:-4])

    def clock(self):
        return self.now


def stadium_with(on=True, seed=3, rules=True):
    import random

    from nfl4.game.rnd import GameRandom
    st = ST.Stadium(NflRules(), on=on)
    game = types.SimpleNamespace(sounds=Sounds(), rnd=GameRandom(random.Random(seed)),
                                 play_engine=types.SimpleNamespace(rules=st.rules if rules else object()))      # no engine of its own: another game
    game.rnd.seed = seed
    st.attach(game, None)
    return st, game


def test_the_whistle_is_chosen_by_what_happened_and_is_a_file_of_the_pea_whistles():
    st, game = stadium_with()
    for context, name in ST.CONTEXT_WHISTLES.items():
        assert os.path.basename(st.whistle(context)) == name + ".wav"
    seen = {st.whistle(None) for _ in range(60)}
    assert None not in seen and {os.path.basename(p) for p in seen} == {"whistle_short.wav", "whistle_double.wav"}    # never foot11 (2026-10-23)
    assert st.whistle("nonesuch") is None


def test_a_classic_game_after_an_nfl_game_hears_the_original_whistle():
    st, game = stadium_with(rules=False)
    assert st.whistle("timeout") is None and st.whistle(None) is None


def test_the_hook_is_installed_at_the_start_and_the_microphone_effect_is_set(tmp_path):
    rig = Rig([], sounds_dir=tmp_path)
    st = ST.Stadium(NflRules(), on=True)
    st.attach(rig.game, None)
    assert rig.game.sounds.whistle_hook == st.whistle
    assert ("role_effect", "referee=pa") in rig.sapi.events
    off = ST.Stadium(NflRules(), on=False)
    rig.game.sounds.whistle_hook = None
    off.attach(rig.game, None)
    assert rig.game.sounds.whistle_hook is None and ("role_effect", "referee=") in rig.sapi.events


def test_play_tackle_8_plays_the_named_pea_whistle_waits_as_ever_and_forgets_the_context(tmp_path):
    rig = Rig([], sounds_dir=tmp_path)
    sounds = rig.game.sounds
    asked = []
    path = os.path.join(ST.shipped_folder(), "whistle_short.wav")
    sounds.whistle_hook = lambda context: asked.append(context) or path
    sounds.whistle_context = "timeout"
    before = len(rig.slot_log)
    sounds.play_tackle(8)
    assert asked == ["timeout"] and sounds.whistle_context is None
    played = [e for e in rig.slot_log[before:] if e.action == "play" and e.slot == SLOT_TACKLE]
    assert len(played) == 1 and played[0].sound_id != "snd_foot11"
    sounds.whistle_hook = lambda context: None                      # the hook answers None: the original's foot11
    sounds.play_tackle(8)
    assert [e.sound_id for e in rig.slot_log if e.action == "play" and e.slot == SLOT_TACKLE][-1] == "snd_foot11"
    sounds.whistle_hook = None
    sounds.play_tackle(3)                                           # another tackle never asks
    assert [e.sound_id for e in rig.slot_log if e.action == "play" and e.slot == SLOT_TACKLE][-1] == "snd_foot6"


def test_the_microphone_clicks_once_per_burst_and_closes_at_the_end():
    st, game = stadium_with()
    st.mic(True)
    game.sounds.now = 1.0
    st.mic(True)                                  # within three seconds: the same burst, no second click
    st.mic(False)
    game.sounds.now = 9.0
    st.mic(True)
    assert game.sounds.calls == ["mic_on", "mic_off", "mic_on"]


def test_every_shipped_stadium_file_is_a_known_sound():
    names = set(ST.ALL_NAMES)
    files = {f[:-4] for f in os.listdir(ST.shipped_folder()) if f.endswith(".wav")}
    assert files == names, files ^ names


# ----- a whole game -----

def whole_game(tmp_path, seed, on):
    said = []
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=on,
                           stadium_on=on)
    from nfl4.game import flow
    real = flow.Game.say_referee
    flow.Game.say_referee = lambda self, text: said.append(text) or real(self, text)
    try:
        rig, engine, rules, result = sim_game(tmp_path, seed, rules=rules, trace=True)
    finally:
        flow.Game.say_referee = real
    return rig, said, result


def test_the_referee_and_the_whistles_do_not_move_a_draw_and_the_flags_are_the_referees(tmp_path):
    rig_on, said_on, result_on = whole_game(tmp_path / "on", 21, True)
    rig_off, said_off, result_off = whole_game(tmp_path / "off", 21, False)
    assert said_off == [] and len(said_on) > 5
    assert any(X.text("NXP-01").strip() == t.strip() for t in said_on)                     # the flags are the referee's
    assert any("time out called by" in t for t in said_on) or any("review" in t for t in said_on) or len(said_on) > 10
    assert rig_on.rnd.trace == rig_off.rnd.trace and rig_on.rnd.draws == rig_off.rnd.draws and result_on.scores == result_off.scores
    whistles = [e.sound_id for e in rig_on.slot_log if e.action == "play" and e.slot == SLOT_TACKLE]
    assert {"file whistle_short.wav", "file whistle_long.wav", "file whistle_double.wav"} <= set(whistles)        # by what happened
    assert "snd_foot11" not in whistles                       # a tester, 2026-10-23: every whistle of these rules is the official's
    rig_classic = sim_game(tmp_path / "classic", 21, rules=RecordingRules(penalties_on=True, qb_on=True, playbooks_on=True))[0]
    assert not [e for e in rig_classic.slot_log if e.action == "play" and "whistle_" in str(e.sound_id)]    # the original's rules hear no pea whistle
