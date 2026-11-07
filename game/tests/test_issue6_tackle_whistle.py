"""GitHub issue 6 (a tester, 2026-11-07, on 0.16.19: "two whistles appear to be used still"), fixed in 0.16.20 (D-219, rule 0.40 (4)).
This is inspired by Jim Kitchen.

The cause, found in the tester's problem report and measured in the shipped wavs: the original's three tackle sounds (foot4, foot5, foot6,
PlayTackle(1), (2) and (3)) END IN A REFEREE WHISTLE OF THEIR OWN, a steady tone of 3.4 to 3.9 kHz as loud as the hit. 0.16.18 (D-215) made
every PlayTackle(8) the one made whistle, and its test called the tackle sounds "not whistles", so every tackle still blew the original's
whistle and every other dead ball the made one. Now, in the owner's mode, the shipped tackle sound is played only up to the moment its own
whistle begins (HIT_ENDS, the last 40 ms faded) and the one whistle follows at that moment, in the same 2.5 s; Classic plays the files whole.

The whistle detector here is plain Python (the game's environment has no numpy, rule 0.11): the share of a 20 ms window's energy in the
DFT bins of 3,200 to 4,200 Hz (Goertzel, bins 50 Hz apart). A whistle puts most of its energy there; a hit, a crowd or a pad puts little."""
import math
import os
import wave
from array import array

import pytest

from nfl4.audio.library import shipped_sounds_dir
from nfl4.audio.output import SLOT_NOISE, SLOT_TACKLE, STEREO_FRAME
from nfl4.audio.render import MIX_RATE, cut_with_fade
from nfl4.audio.wavdata import load_sound_file
from nfl4.extras import stadium as ST
from nfl4.game import sounds as S

BAND = (3200, 4200)
WHISTLE_SHARE = 0.45        # a window this whistle-like is a whistle: the original's whistles reach 0.6 to 0.9 (work\i6_1107)
HIT_SHARE = 0.30            # the hits before HIT_ENDS stay far under this (measured: at most about 0.1)


def band_shares(samples, rate):
    """The whistle-band share of every 20 ms window (non-overlapping) of a mono 16-bit signal."""
    n = int(rate / 50)                             # bins 50 Hz apart
    first, last = int(BAND[0] / 50), int(BAND[1] / 50)
    coeffs = [2.0 * math.cos(2.0 * math.pi * k / n) for k in range(first, last + 1)]
    shares = []
    for start in range(0, len(samples) - n + 1, n):
        x = samples[start:start + n]
        energy = sum(v * v for v in x)
        if energy <= 0:
            shares.append(0.0)
            continue
        band = 0.0
        for c in coeffs:
            s1 = s2 = 0.0
            for v in x:
                s1, s2 = v + c * s1 - s2, s1
            band += s1 * s1 + s2 * s2 - c * s1 * s2
        shares.append(min(1.0, 2.0 * band / (n * energy)))
    return shares


def mono_of_rendered(pcm):
    """The left channel of rendered 16-bit stereo sound (the tackle slot is centered)."""
    every = array("h")
    every.frombytes(pcm[:len(pcm) // STEREO_FRAME * STEREO_FRAME])
    return every[0::2]


def shipped(n):
    return load_sound_file(os.path.join(shipped_sounds_dir(), "foot%d.wav" % (n + 3)))


def write_wav(path, seconds, freq=200, rate=22050):
    """A plain low tone of the player's (no whistle in it), mono 16-bit."""
    frames = int(seconds * rate)
    data = array("h", (int(8000 * math.sin(2 * math.pi * freq * i / rate)) for i in range(frames)))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data.tobytes())


# ----- the evidence: the original's tackle sounds hold a whistle, after HIT_ENDS and not before -----

@pytest.mark.parametrize("n", [1, 2, 3])
def test_the_originals_tackle_sounds_end_in_a_whistle_of_their_own_and_hit_ends_is_before_it(n):
    sound = shipped(n)
    shares = band_shares(sound.samples(0), sound.rate)
    window = 0.02
    end = min(S.HIT_ENDS[n], S.TACKLE_WAIT)
    before = [s for i, s in enumerate(shares) if (i + 1) * window <= end]
    after = [s for i, s in enumerate(shares) if i * window >= S.HIT_ENDS[n]]
    assert sum(1 for s in after if s >= WHISTLE_SHARE) >= 10, (n, max(after))       # half a second and more of whistle in the file
    assert max(before) < HIT_SHARE, (n, max(before))                                # and none in what the owner's mode plays


def test_foot11_is_a_whistle_by_the_same_measure_and_the_made_whistle_too():
    for path in (os.path.join(shipped_sounds_dir(), "foot11.wav"), os.path.join(ST.shipped_folder(), "whistle.wav")):
        sound = load_sound_file(path)
        assert sum(1 for s in band_shares(sound.samples(0), sound.rate) if s >= WHISTLE_SHARE) >= 5, path


# ----- the cut -----

def test_cut_with_fade_keeps_the_head_and_fades_to_silence():
    frames = MIX_RATE                                                     # one second of a loud square-ish signal
    pcm = array("h", [12000, 12000, -12000, -12000] * (frames // 2)).tobytes()
    cut = cut_with_fade(pcm, 0.5)
    assert len(cut) == int(0.5 * MIX_RATE) * STEREO_FRAME
    assert cut[:1000] == pcm[:1000]
    tail = array("h")
    tail.frombytes(cut[-64:])
    assert max(abs(v) for v in tail) < 1500                              # the last steps of the fade are near silence: no click
    assert cut_with_fade(pcm, 2.0) == pcm and cut_with_fade(pcm, 1.0) == pcm


# ----- PlayTackle on the rig: the real audio layer on the shipped wavs, a virtual clock -----

def rig_sounds(tmp_path):
    from gamerig import Rig
    rig = Rig([], sounds_dir=tmp_path)
    sounds = rig.game.sounds
    sounds.whistle_hook = None
    return rig, sounds


def tackle_events(rig, before):
    return [e for e in rig.slot_log[before:] if e.action == "play" and e.slot == SLOT_TACKLE]


@pytest.mark.parametrize("n", [1, 2, 3])
def test_the_owners_mode_plays_the_hit_without_its_whistle_then_the_one_whistle_in_the_same_wait(tmp_path, n):
    rig, sounds = rig_sounds(tmp_path)
    sounds.own_mode = lambda: True
    before, start, played = len(rig.slot_log), rig.clock(), len(rig.output.played)
    sounds.play_tackle(n)
    events = tackle_events(rig, before)
    assert [e.sound_id for e in events] == ["snd_foot%d" % (n + 3), "file whistle.wav"]
    hit, whistle = events
    end = min(S.HIT_ENDS[n], S.TACKLE_WAIT)
    assert hit.cut == pytest.approx(end) and whistle.cut == 0.0
    assert whistle.time - hit.time == pytest.approx(end, abs=0.01)        # the one whistle where the original's began
    assert rig.clock() - start == pytest.approx(S.TACKLE_WAIT, abs=0.01)    # PlayTackle's 2.5 s, as before
    assert any(e.action == "stop" and e.slot == SLOT_NOISE for e in rig.slot_log[before:])
    pcm = [p for slot, p, _gain, _loop in rig.output.played[played:] if slot == SLOT_TACKLE][0]
    assert len(pcm) // STEREO_FRAME == int(end * MIX_RATE)
    shares = band_shares(mono_of_rendered(pcm), MIX_RATE)
    assert max(shares) < HIT_SHARE, max(shares)                          # what is heard of the hit has no whistle in it


@pytest.mark.parametrize("n", [1, 2, 3])
def test_classic_plays_the_originals_tackle_whole_with_its_own_whistle(tmp_path, n):
    rig, sounds = rig_sounds(tmp_path)
    sounds.own_mode = lambda: False
    before, start = len(rig.slot_log), rig.clock()
    sounds.play_tackle(n)
    events = tackle_events(rig, before)
    assert [e.sound_id for e in events] == ["snd_foot%d" % (n + 3)] and events[0].cut == 0.0
    assert rig.clock() - start == pytest.approx(S.TACKLE_WAIT, abs=0.01)


def test_a_players_own_tackle_file_plays_whole_then_the_one_whistle(tmp_path):
    write_wav(str(tmp_path / "foot6.wav"), seconds=0.8)
    rig, sounds = rig_sounds(tmp_path)
    sounds.own_mode = lambda: True
    before = len(rig.slot_log)
    sounds.play_tackle(3)
    hit, whistle = tackle_events(rig, before)
    assert hit.source == "player" and hit.cut == 0.0 and whistle.sound_id == "file whistle.wav"
    assert whistle.time - hit.time == pytest.approx(0.8, abs=0.01)


def test_the_players_whistle_follows_the_tackle_too(tmp_path, monkeypatch):
    write_wav(str(tmp_path / "whistle.wav"), seconds=0.3)
    monkeypatch.setattr(ST, "player_folder", lambda: str(tmp_path))
    rig, sounds = rig_sounds(tmp_path)
    sounds.own_mode = lambda: True
    before = len(rig.slot_log)
    sounds.play_tackle(2)
    hit, whistle = tackle_events(rig, before)
    assert hit.sound_id == "snd_foot5" and whistle.sound_id == "file whistle.wav" and whistle.source == "player"


def test_with_no_whistle_file_at_all_the_tackle_plays_whole_rather_than_none(tmp_path, monkeypatch):
    rig, sounds = rig_sounds(tmp_path)
    sounds.own_mode = lambda: True
    monkeypatch.setattr(S.GameSounds, "slot_files", lambda self, name: [])
    before = len(rig.slot_log)
    sounds.play_tackle(3)
    events = tackle_events(rig, before)
    assert [e.sound_id for e in events] == ["snd_foot6"] and events[0].cut == 0.0


def test_the_tackle_says_in_the_log_what_was_cut_and_which_whistle_followed(tmp_path, caplog):
    import logging
    from nfl4.data import debuglog
    rig, sounds = rig_sounds(tmp_path)
    sounds.own_mode = lambda: True
    old = debuglog._threshold
    debuglog._threshold = logging.DEBUG
    try:
        with caplog.at_level(logging.DEBUG, logger="nfl4"):
            sounds.play_tackle(3)
    finally:
        debuglog._threshold = old
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "tackle n=3 hit=snd_foot6" in text and "cut at 1.36 s" in text and "whistle=whistle.wav" in text, text
    assert "cut=1.36" in text                                            # the sound line of the hit itself


# ----- whole games in the owner's mode: every tackle is cut, every whistle is the one whistle, no draw moves -----

def test_whole_owners_mode_games_play_no_tackle_whole_and_change_no_draw(tmp_path, monkeypatch):
    import test_sy3_referee as T
    real = S.GameSounds.play_tackle
    mode = {"own": True}

    def blown(self, n):
        # sim_game builds no flow.Game, so its N. F. L. rules game is told the owner's mode here (test_issue4_one_whistle does the same)
        self.own_mode = lambda: mode["own"]
        real(self, n)

    monkeypatch.setattr(S.GameSounds, "play_tackle", blown)
    for seed in (3, 21):
        mode["own"] = True
        rig, _said, result = T.whole_game(tmp_path / ("own%d" % seed), seed, True)
        tackle = [e for e in rig.slot_log if e.action == "play" and e.slot == SLOT_TACKLE]
        hits = [e for e in tackle if e.sound_id in ("snd_foot4", "snd_foot5", "snd_foot6")]
        assert len(hits) > 20, seed
        whole = [e for e in hits if not e.cut]
        assert whole == [], (seed, whole[:3])                                 # no tackle with the original's whistle in it
        for i, e in enumerate(tackle):
            if e.sound_id in ("snd_foot4", "snd_foot5", "snd_foot6"):
                assert tackle[i + 1].sound_id == "file whistle.wav", (seed, i)   # each hit is ended by the one whistle
        assert {e.sound_id for e in tackle} - {"snd_foot4", "snd_foot5", "snd_foot6"} == {"file whistle.wav"}
        mode["own"] = False
        rig_classic_sounds, _said2, result2 = T.whole_game(tmp_path / ("cls%d" % seed), seed, True)
        assert rig.rnd.trace == rig_classic_sounds.rnd.trace and rig.rnd.draws == rig_classic_sounds.rnd.draws, seed
        assert result.scores == result2.scores, seed
